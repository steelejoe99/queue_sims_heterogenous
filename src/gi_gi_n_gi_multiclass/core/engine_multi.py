from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Literal
import heapq

from gi_gi_n_gi_multiclass.core.types_multi import MultiSimConfig, MultiSimResult, MultiCustomerRecord
from gi_gi_n_gi_multiclass.core.multi_state import MultiSystemState
from gi_gi_n_gi_multiclass.core.rng_multi import make_multi_rng_streams, make_label_rng
from gi_gi_n_gi_multiclass.core.validate_multi import validate_multi_config

EventType = Literal[
    "ARRIVAL",
    "SERVICE_END",
    "ABANDON",
    "BATCH_ARRIVAL",
    "ELIGIBILITY",
    "HOUSING_RELEASE",
]


@dataclass(order=True)
class MultiEvent:
    time: float
    priority: int
    seq: int
    etype: EventType = field(compare=False)
    customer_id: int = field(compare=False, default=-1)
    class_id: int = field(compare=False, default=-1)


class MultiEventQueue:
    def __init__(self) -> None:
        self._heap: list[MultiEvent] = []
        self._seq = 0

    def push(
        self,
        time: float,
        priority: int,
        etype: EventType,
        customer_id: int = -1,
        class_id: int = -1,
    ) -> None:
        self._seq += 1
        heapq.heappush(
            self._heap,
            MultiEvent(
                time=time,
                priority=priority,
                seq=self._seq,
                etype=etype,
                customer_id=customer_id,
                class_id=class_id,
            ),
        )

    def pop(self) -> MultiEvent:
        return heapq.heappop(self._heap)

    def __len__(self) -> int:
        return len(self._heap)


def run_sim_multi(cfg: MultiSimConfig) -> MultiSimResult:
    """Run the multiclass simulation.

    The default path is the original reusable-server queue. Setting
    ``housing_mode=True`` switches to annual or otherwise periodic batch
    arrivals and consumable housing releases. In that mode a housing unit is
    permanently consumed when allocated and no service-completion event is
    scheduled.
    """

    validate_multi_config(cfg)

    n_classes = len(cfg.classes)
    streams = make_multi_rng_streams(cfg.seed, n_classes)
    label_rng = make_label_rng(cfg.seed)

    initial_capacity = cfg.initial_housing_stock if cfg.housing_mode else cfg.n_servers
    state = MultiSystemState(n_servers=initial_capacity, n_classes=n_classes)
    eq = MultiEventQueue()

    customers: list[MultiCustomerRecord] = []
    event_log: Optional[list[dict]] = [] if cfg.collect_event_log else None

    end_time = cfg.warmup_time + cfg.run_time

    if cfg.housing_mode:
        eq.push(time=cfg.first_batch_time, priority=2, etype="BATCH_ARRIVAL")
        eq.push(time=cfg.first_housing_release, priority=1, etype="HOUSING_RELEASE")
    else:
        # Original schedule: first renewal arrival for each class.
        for cls_id, cls in enumerate(cfg.classes):
            ia = float(cls.interarrival.sample(streams.arrivals[cls_id]))
            eq.push(time=ia, priority=0, etype="ARRIVAL", class_id=cls_id)

    def log(ev: MultiEvent, note: str = "") -> None:
        if event_log is None:
            return
        event_log.append(
            {
                "time": ev.time,
                "etype": ev.etype,
                "customer_id": ev.customer_id,
                "class_id": ev.class_id,
                "note": note,
                "idle_servers": state.idle_servers,
                "available_housing": state.idle_servers if cfg.housing_mode else None,
            }
        )

    def add_customer(true_cls_id: int, now: float) -> int:
        cls = cfg.classes[true_cls_id]

        if cfg.classifier is None:
            assigned_cls_id = true_cls_id
        else:
            assigned_cls_id = int(cfg.classifier.assign(true_cls_id, label_rng))

        cid = len(customers)
        service_time = float(cls.service.sample(streams.service[true_cls_id]))
        patience_time = None
        abandon_time = None
        if cls.patience is not None:
            patience_time = float(cls.patience.sample(streams.patience[true_cls_id]))
            abandon_time = now + patience_time

        eligibility_time = now + cfg.eligibility_delay if cfg.housing_mode else now

        rec = MultiCustomerRecord(
            customer_id=cid,
            class_id=assigned_cls_id,
            true_class_id=true_cls_id,
            assigned_class_id=assigned_cls_id,
            arrival_time=now,
            service_time=service_time,
            patience_time=patience_time,
            abandon_time=abandon_time,
            eligibility_time=eligibility_time,
        )
        customers.append(rec)

        if cfg.housing_mode and eligibility_time > now:
            state.add_ineligible(cid, assigned_cls_id, now, eligibility_time)
            eq.push(
                time=eligibility_time,
                priority=0,
                etype="ELIGIBILITY",
                customer_id=cid,
                class_id=assigned_cls_id,
            )
        else:
            state.add_waiting(cid, assigned_cls_id, now)

        if abandon_time is not None:
            eq.push(
                time=abandon_time,
                priority=3 if cfg.housing_mode else 2,
                etype="ABANDON",
                customer_id=cid,
                class_id=assigned_cls_id,
            )

        return cid

    def try_start_services(now: float) -> None:
        """Start reusable services or permanently allocate available housing."""
        state.now = now
        while state.idle_servers > 0 and state.has_waiting():
            cid = cfg.policy.select_customer(state, now)
            if cid is None:
                break

            rec = customers[cid]
            if rec.outcome is not None:
                state.abandon(cid)
                continue

            state.start_service(cid)
            rec.service_start = now

            if cfg.housing_mode:
                # Housing is consumed permanently. Keeping the historical
                # outcome name SERVED preserves all existing metrics.
                rec.service_end = now
                rec.outcome = "SERVED"
            else:
                rec.service_end = now + rec.service_time
                eq.push(
                    time=rec.service_end,
                    priority=1,
                    etype="SERVICE_END",
                    customer_id=cid,
                    class_id=rec.assigned_class_id,
                )

    while len(eq) > 0:
        ev = eq.pop()
        now = float(ev.time)
        if now > end_time:
            break
        state.now = now

        if ev.etype == "BATCH_ARRIVAL":
            counts = cfg.batch_arrival_counts
            assert counts is not None
            for true_cls_id, count in enumerate(counts):
                for _ in range(int(count)):
                    add_customer(true_cls_id, now)

            log(ev, note=f"batch_arrival total={sum(int(x) for x in counts)}")
            try_start_services(now)

            next_t = now + cfg.batch_interval
            within_last_batch = cfg.last_batch_time is None or next_t <= cfg.last_batch_time
            if next_t <= end_time and within_last_batch:
                eq.push(time=next_t, priority=2, etype="BATCH_ARRIVAL")

        elif ev.etype == "ELIGIBILITY":
            cid = ev.customer_id
            if 0 <= cid < len(customers) and state.make_eligible(cid):
                log(ev, note="eligible")
                try_start_services(now)
            else:
                log(ev, note="eligibility_canceled")

        elif ev.etype == "HOUSING_RELEASE":
            state.add_capacity(cfg.n_servers)
            log(ev, note=f"housing_release added={cfg.n_servers}")
            try_start_services(now)

            next_t = now + cfg.housing_release_interval
            if next_t <= end_time:
                eq.push(time=next_t, priority=1, etype="HOUSING_RELEASE")

        elif ev.etype == "ARRIVAL":
            true_cls_id = ev.class_id
            add_customer(true_cls_id, now)

            cls = cfg.classes[true_cls_id]
            ia = float(cls.interarrival.sample(streams.arrivals[true_cls_id]))
            next_t = now + ia
            eq.push(time=next_t, priority=0, etype="ARRIVAL", class_id=true_cls_id)

            log(ev, note="arrival")
            try_start_services(now)

        elif ev.etype == "SERVICE_END":
            cid = ev.customer_id
            if cid < 0 or cid >= len(customers):
                continue
            rec = customers[cid]
            if rec.outcome is not None:
                continue
            rec.outcome = "SERVED"
            state.end_service(cid)
            log(ev, note="service_end")
            try_start_services(now)

        elif ev.etype == "ABANDON":
            cid = ev.customer_id
            if cid < 0 or cid >= len(customers):
                continue
            if state.active_waiting.get(cid, False):
                rec = customers[cid]
                if rec.outcome is None:
                    rec.outcome = "ABANDONED"
                state.abandon(cid)
                log(ev, note="abandon")
                try_start_services(now)
            else:
                log(ev, note="abandon_canceled")

    for rec in customers:
        if rec.outcome is None:
            rec.outcome = "IN_SYSTEM_END"

    return MultiSimResult(
        config=cfg,
        customers=customers,
        end_time=float(end_time),
        event_log=event_log,
    )
