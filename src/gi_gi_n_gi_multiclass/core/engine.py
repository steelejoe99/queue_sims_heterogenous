"""Event loop for the conventional single-class GI/GI/N(+GI) simulator."""

from __future__ import annotations

from typing import Optional
from .types import SimConfig, SimResult, CustomerRecord
from .events import Event, EventQueue
from .state import SystemState
from .rng import RNGStreams
from .validate import validate_config

def _log_append(event_log: Optional[list[dict]], **row) -> None:
    """Append a structured event row only when event logging is enabled."""
    if event_log is not None:
        event_log.append(row)

def run_sim(cfg: SimConfig) -> SimResult:
    """Run an event-driven GI/GI/N(+GI) simulation.

    - If cfg.patience is None, this is GI/GI/N with no abandonment.
    - Time horizon: [0, warmup_time + run_time]. Metrics should be computed post-warmup.
    """
    validate_config(cfg)
    rng = RNGStreams(cfg.seed)
    eq = EventQueue()
    state = SystemState(n_servers=cfg.n_servers)
    event_log = [] if cfg.collect_event_log else None
    customers: list[CustomerRecord] = []

    horizon_end = cfg.warmup_time + cfg.run_time

    # schedule first arrival
    t0 = float(cfg.interarrival.sample(rng.arrivals))
    eq.push(Event(time=t0, priority=0, etype="ARRIVAL", customer_id=0))

    next_cid = 0

    def try_start_services(now: float) -> None:
        """Fill every currently idle server according to the configured policy."""
        while state.idle_servers > 0 and state.waiting:
            chosen = cfg.policy.select_customer(state, now)
            if chosen is None:
                return
            # Start service
            rec = customers[chosen]
            if rec.service_start is not None:
                # already started (shouldn't happen)
                state.waiting.discard(chosen)
                continue
            state.start_service(chosen)
            rec.service_start = now
            rec.service_end = now + rec.service_time
            rec.outcome = "SERVED"
            # schedule service end
            eq.push(Event(time=rec.service_end, priority=1, etype="SERVICE_END", customer_id=chosen))
            _log_append(event_log, time=now, etype="SERVICE_START", customer_id=chosen)

    while len(eq) > 0:
        ev = eq.pop()
        if ev.time > horizon_end:
            state.now = horizon_end
            break

        state.now = ev.time

        if ev.etype == "ARRIVAL":
            cid = ev.customer_id
            # create customer record
            st = float(cfg.service.sample(rng.service))
            pt = float(cfg.patience.sample(rng.patience)) if cfg.patience is not None else None
            abandon_time = (state.now + pt) if pt is not None else None
            rec = CustomerRecord(
                customer_id=cid,
                arrival_time=state.now,
                service_time=st,
                patience_time=pt,
                abandon_time=abandon_time
            )
            customers.append(rec)

            state.add_waiting(cid, state.now)
            _log_append(event_log, time=state.now, etype="ARRIVAL", customer_id=cid)

            # schedule abandonment (lazy cancellation via state.active)
            if abandon_time is not None:
                eq.push(Event(time=abandon_time, priority=2, etype="ABANDON", customer_id=cid))

            # schedule next arrival
            next_cid = cid + 1
            tnext = state.now + float(cfg.interarrival.sample(rng.arrivals))
            eq.push(Event(time=tnext, priority=0, etype="ARRIVAL", customer_id=next_cid))

            # attempt to start service immediately if capacity
            try_start_services(state.now)

        elif ev.etype == "ABANDON":
            cid = ev.customer_id
            # abandon only if still active and waiting
            if state.active.get(cid, False) and (cid in state.waiting):
                state.abandon(cid)
                rec = customers[cid]
                rec.outcome = "ABANDONED"
                rec.service_start = None
                rec.service_end = None
                _log_append(event_log, time=state.now, etype="ABANDON", customer_id=cid)
                # freeing capacity isn't needed since they were waiting

        elif ev.etype == "SERVICE_END":
            cid = ev.customer_id
            # if service end fires, customer must be in service
            state.end_service(cid)
            _log_append(event_log, time=state.now, etype="SERVICE_END", customer_id=cid)
            # immediately start next if available
            try_start_services(state.now)

    # finalize outcomes for customers still waiting or in service at end
    end_time = state.now
    for rec in customers:
        if rec.outcome is None:
            # still in system at horizon end
            rec.outcome = "IN_SYSTEM_END"

    return SimResult(config=cfg, customers=customers, end_time=end_time, event_log=event_log)
