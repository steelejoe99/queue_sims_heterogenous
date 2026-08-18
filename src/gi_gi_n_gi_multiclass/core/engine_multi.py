from __future__ import annotations

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
    "INITIAL_QUEUE",
    "BATCH_ARRIVAL",
    "ELIGIBILITY",
    "HOUSING_RELEASE",
]


EventEntry = tuple[float, int, int, EventType, int, int]


class MultiEventQueue:
    def __init__(self) -> None:
        # Raw tuples let ``heapq`` compare and store events in C without
        # allocating a Python event object for every insertion.
        self._heap: list[EventEntry] = []
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
            (time, priority, self._seq, etype, customer_id, class_id),
        )

    def pop(self) -> EventEntry:
        return heapq.heappop(self._heap)

    def __len__(self) -> int:
        return len(self._heap)


def run_sim_multi(cfg: MultiSimConfig) -> MultiSimResult:
    """Run the multiclass simulation.

    The default path is the original reusable-server queue. Setting
    ``housing_mode=True`` switches to consumable housing releases. Housing
    arrivals can be periodic batches or renewal arrivals, selected by
    ``housing_arrival_mode``. In that mode a housing unit is permanently
    consumed when allocated and no service-completion event is scheduled.
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
        if cfg.initial_queue_counts is not None:
            eq.push(time=0.0, priority=0, etype="INITIAL_QUEUE")
        if cfg.housing_arrival_mode == "batch":
            eq.push(time=cfg.first_batch_time, priority=2, etype="BATCH_ARRIVAL")
        else:
            arrival_cutoff = cfg.last_arrival_time
            if arrival_cutoff is None:
                arrival_cutoff = end_time
            for cls_id, cls in enumerate(cfg.classes):
                ia = float(cls.interarrival.sample(streams.arrivals[cls_id]))
                if ia <= arrival_cutoff and ia <= end_time:
                    eq.push(time=ia, priority=0, etype="ARRIVAL", class_id=cls_id)
        eq.push(time=cfg.first_housing_release, priority=1, etype="HOUSING_RELEASE")
    else:
        # Original schedule: first renewal arrival for each class.
        for cls_id, cls in enumerate(cfg.classes):
            ia = float(cls.interarrival.sample(streams.arrivals[cls_id]))
            eq.push(time=ia, priority=0, etype="ARRIVAL", class_id=cls_id)

    def log(ev: EventEntry, note: str = "") -> None:
        if event_log is None:
            return
        event_log.append(
            {
                "time": ev[0],
                "etype": ev[3],
                "customer_id": ev[4],
                "class_id": ev[5],
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
        # Housing allocations are immediate and permanent, so a service-time
        # draw cannot affect the simulation in this mode.
        service_time = 0.0 if cfg.housing_mode else float(cls.service.sample(streams.service[true_cls_id]))
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
            # A person who abandons strictly before eligibility can never be
            # allocated housing. Avoid creating an event that will only be
            # canceled later. Equality retains the existing event ordering:
            # eligibility is processed before abandonment at the same time.
            if abandon_time is None or abandon_time >= eligibility_time:
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
        event_time, _, _, event_type, event_customer_id, event_class_id = ev
        now = float(event_time)
        if now > end_time:
            break
        state.now = now

        if event_type == "INITIAL_QUEUE":
            counts = cfg.initial_queue_counts
            assert counts is not None
            for true_cls_id, count in enumerate(counts):
                for _ in range(int(count)):
                    add_customer(true_cls_id, now)

            log(ev, note=f"initial_queue total={sum(int(x) for x in counts)}")
            try_start_services(now)

        elif event_type == "BATCH_ARRIVAL":
            counts = cfg.batch_arrival_counts
            assert counts is not None
            for true_cls_id, count in enumerate(counts):
                for _ in range(int(count)):
                    add_customer(true_cls_id, now)

            log(ev, note=f"batch_arrival total={sum(int(x) for x in counts)}")
            try_start_services(now)

            next_t = now + cfg.batch_interval
            within_last_batch = (
                cfg.last_batch_time is None
                or next_t <= cfg.last_batch_time + 1e-12
            )
            if next_t <= end_time and within_last_batch:
                eq.push(time=next_t, priority=2, etype="BATCH_ARRIVAL")

        elif event_type == "ELIGIBILITY":
            cid = event_customer_id
            if 0 <= cid < len(customers) and state.make_eligible(cid):
                log(ev, note="eligible")
                try_start_services(now)
            else:
                log(ev, note="eligibility_canceled")

        elif event_type == "HOUSING_RELEASE":
            state.add_capacity(cfg.n_servers)
            log(ev, note=f"housing_release added={cfg.n_servers}")
            try_start_services(now)

            next_t = now + cfg.housing_release_interval
            if next_t <= end_time:
                eq.push(time=next_t, priority=1, etype="HOUSING_RELEASE")

        elif event_type == "ARRIVAL":
            true_cls_id = event_class_id
            add_customer(true_cls_id, now)

            cls = cfg.classes[true_cls_id]
            ia = float(cls.interarrival.sample(streams.arrivals[true_cls_id]))
            next_t = now + ia
            if cfg.housing_mode and cfg.housing_arrival_mode == "renewal":
                arrival_cutoff = cfg.last_arrival_time
                if arrival_cutoff is None:
                    arrival_cutoff = end_time
                if next_t <= arrival_cutoff and next_t <= end_time:
                    eq.push(time=next_t, priority=0, etype="ARRIVAL", class_id=true_cls_id)
            else:
                eq.push(time=next_t, priority=0, etype="ARRIVAL", class_id=true_cls_id)

            log(ev, note="housing_renewal_arrival" if cfg.housing_mode else "arrival")
            try_start_services(now)

        elif event_type == "SERVICE_END":
            cid = event_customer_id
            if cid < 0 or cid >= len(customers):
                continue
            rec = customers[cid]
            if rec.outcome is not None:
                continue
            rec.outcome = "SERVED"
            state.end_service(cid)
            log(ev, note="service_end")
            try_start_services(now)

        elif event_type == "ABANDON":
            cid = event_customer_id
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
