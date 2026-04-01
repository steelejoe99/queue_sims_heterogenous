from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Literal
import heapq

import numpy as np

from gi_gi_n_gi_multiclass.core.types_multi import MultiSimConfig, MultiSimResult, MultiCustomerRecord
from gi_gi_n_gi_multiclass.core.multi_state import MultiSystemState
from gi_gi_n_gi_multiclass.core.rng_multi import make_multi_rng_streams, make_label_rng
from gi_gi_n_gi_multiclass.core.validate_multi import validate_multi_config

EventType = Literal["ARRIVAL", "SERVICE_END", "ABANDON"]

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

    def push(self, time: float, priority: int, etype: EventType, customer_id: int = -1, class_id: int = -1) -> None:
        self._seq += 1
        heapq.heappush(self._heap, MultiEvent(time=time, priority=priority, seq=self._seq, etype=etype, customer_id=customer_id, class_id=class_id))

    def pop(self) -> MultiEvent:
        return heapq.heappop(self._heap)

    def __len__(self) -> int:
        return len(self._heap)

def run_sim_multi(cfg: MultiSimConfig) -> MultiSimResult:
    validate_multi_config(cfg)

    n_classes = len(cfg.classes)
    streams = make_multi_rng_streams(cfg.seed, n_classes)
    label_rng = make_label_rng(cfg.seed)

    state = MultiSystemState(n_servers=cfg.n_servers, n_classes=n_classes)
    eq = MultiEventQueue()

    customers: list[MultiCustomerRecord] = []
    event_log: Optional[list[dict]] = [] if cfg.collect_event_log else None

    end_time = cfg.warmup_time + cfg.run_time

    # schedule first arrival for each class
    for cls_id, cls in enumerate(cfg.classes):
        ia = float(cls.interarrival.sample(streams.arrivals[cls_id]))
        eq.push(time=ia, priority=0, etype="ARRIVAL", class_id=cls_id)

    def log(ev: MultiEvent, note: str = "") -> None:
        if event_log is None:
            return
        event_log.append({
            "time": ev.time,
            "etype": ev.etype,
            "customer_id": ev.customer_id,
            "class_id": ev.class_id,
            "note": note,
            "idle_servers": state.idle_servers,
        })

    def try_start_services(now: float) -> None:
        # Start as many services as possible at current time
        state.now = now
        while state.idle_servers > 0 and state.has_waiting():
            cid = cfg.policy.select_customer(state, now)
            if cid is None:
                break
            # start service
            rec = customers[cid]
            if rec.outcome is not None:
                # should not happen
                state.abandon(cid)
                continue
            state.start_service(cid)
            rec.service_start = now
            rec.service_end = now + rec.service_time
            eq.push(
                time=rec.service_end,
                priority=1,
                etype="SERVICE_END",
                customer_id=cid,
                class_id=rec.assigned_class_id,
            )

    # main loop
    while len(eq) > 0:
        ev = eq.pop()
        now = float(ev.time)
        if now > end_time:
            break
        state.now = now

        if ev.etype == "ARRIVAL":
            true_cls_id = ev.class_id
            cls = cfg.classes[true_cls_id]

            if cfg.classifier is None:
                assigned_cls_id = true_cls_id
            else:
                assigned_cls_id = int(cfg.classifier.assign(true_cls_id, label_rng))

            # create customer
            cid = len(customers)
            service_time = float(cls.service.sample(streams.service[true_cls_id]))
            patience_time = None
            abandon_time = None
            if cls.patience is not None:
                patience_time = float(cls.patience.sample(streams.patience[true_cls_id]))
                abandon_time = now + patience_time

            rec = MultiCustomerRecord(
                customer_id=cid,
                class_id=assigned_cls_id,          # keep for backward compatibility if still present
                true_class_id=true_cls_id,
                assigned_class_id=assigned_cls_id,
                arrival_time=now,
                service_time=service_time,
                patience_time=patience_time,
                abandon_time=abandon_time,
            )
            customers.append(rec)

            # queue by assigned class
            state.add_waiting(cid, assigned_cls_id, now)

            # schedule abandonment if applicable
            if abandon_time is not None:
                eq.push(
                    time=abandon_time,
                    priority=2,
                    etype="ABANDON",
                    customer_id=cid,
                    class_id=assigned_cls_id,
                )

            # schedule next arrival for this true class stream
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
            # complete service
            rec.outcome = "SERVED"
            state.end_service(cid)
            log(ev, note="service_end")
            try_start_services(now)

        elif ev.etype == "ABANDON":
            cid = ev.customer_id
            if cid < 0 or cid >= len(customers):
                continue
            # abandon only if still waiting
            if state.active_waiting.get(cid, False):
                rec = customers[cid]
                if rec.outcome is None:
                    rec.outcome = "ABANDONED"
                state.abandon(cid)
                log(ev, note="abandon")
                try_start_services(now)
            else:
                log(ev, note="abandon_canceled")

    # mark customers still in system at end
    for rec in customers:
        if rec.outcome is None:
            rec.outcome = "IN_SYSTEM_END"

    return MultiSimResult(config=cfg, customers=customers, end_time=float(end_time), event_log=event_log)
