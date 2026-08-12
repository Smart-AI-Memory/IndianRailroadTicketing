"""Client state machine — the design's outcome matrix (R3.2; task P2.2).

Each intent runs `submit -> await response | timeout -> retry?` against a
`Service`. The outcome matrix from design.md "Client model" is implemented
here verbatim:

    booked                      -> stop (definitive)
    sold out (clean)            -> stop (definitive)*
    not open (pre-T0 only)      -> poll until T0, real attempt at T0
    mechanism reject w/ answer  -> stop (definitive)*
    queue position (rung 4)     -> poll at interval, no retry
    timeout / hard error        -> retry w/ backoff (R3.2 feedback loop)

    * unless a `p_retry_after_reject` draw says the user re-tries anyway.

Timeouts are client-side: the engine schedules its own timeout event; a
late server response finds the attempt closed and is dropped here (the
server keeping the slot busy is R3.6's wasted work — P3's concern).

Toggles consulted: `retries_enabled` (off: a failed attempt ends the
intent unanswered — it abandons), `open_loop_arrivals` (off: closed-loop
gating — at most K intents active, the next starts when one finishes; the
R3.1 flattering lie, kept only for its direction test).

The engine emits a raw event log (event-log-then-derive, design
"Measurement"); the small helpers at the bottom serve P2.3's direction
tests until P5.1's full metrics land.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Callable, Protocol

from tatkal_sim.config import FidelityConfig
from tatkal_sim.core import Clock, EventQueue, RngStreams
from tatkal_sim.model.workload import Intent, Pool, WorkloadConfig


class Outcome(enum.Enum):
    BOOKED = "booked"
    SOLD_OUT = "sold_out"
    NOT_OPEN = "not_open"
    MECH_REJECT = "mech_reject"  # mechanism rejection carrying an answer
    QUEUE_POSITION = "queue_position"  # waiting-room token (rung 4)
    HARD_ERROR = "hard_error"


#: Outcomes that end the intent with a definitive answer (subject only to
#: the p_retry_after_reject draw for the rejection-shaped ones).
DEFINITIVE = {Outcome.BOOKED, Outcome.SOLD_OUT, Outcome.MECH_REJECT}
RETRYABLE_REJECTS = {Outcome.SOLD_OUT, Outcome.MECH_REJECT}


class Service(Protocol):
    """Server-side interface. P2 tests stub it; P3's server implements it."""

    def submit(self, user_id: int, pool: Pool, respond: Callable[[Outcome], None]) -> None: ...


@dataclass(frozen=True)
class ClientConfig:
    timeout_s: float = 2.0
    max_attempts: int = 4
    backoff_base: float = 0.5
    backoff_mult: float = 2.0
    patience_mean: float = 8.0  # seconds; per-user draw around this
    p_retry_after_reject: float = 0.0  # sensitivity knob (design matrix)
    poll_interval: float = 1.0  # queue-position status polls (rung 4)
    bot_speedup: float = 0.5  # bots: timeout & backoff scaled by this (R3.9)
    closed_loop_users: int = 32  # K when open_loop_arrivals is OFF


@dataclass
class _IntentState:
    intent: Intent
    attempts: int = 0  # post-T0 attempts (pre-T0 polls don't count)
    t_first: float | None = None
    patience: float = 0.0
    open_attempt: int | None = None  # token guarding stale responses
    attempt_counter: int = 0
    t_token: float | None = None  # first queue-position answer (rung 4)
    done: bool = False


LogEntry = tuple  # (kind, t, user_id, *extra) — JSON-able


class ClientEngine:
    def __init__(
        self,
        clock: Clock,
        queue: EventQueue,
        streams: RngStreams,
        fidelity: FidelityConfig,
        client_cfg: ClientConfig,
        workload_cfg: WorkloadConfig,
        service: Service,
        log: list[LogEntry] | None = None,
    ) -> None:
        self.clock = clock
        self.queue = queue
        self.fidelity = fidelity
        self.cfg = client_cfg
        self.wcfg = workload_cfg
        self.service = service
        self.retry_rng = streams.get("retry")
        self.abandon_rng = streams.get("abandon")
        self.log: list[LogEntry] = log if log is not None else []
        self._active = 0
        self._waitlist: list[_IntentState] = []
        self._states: list[_IntentState] = []
        self._by_uid: dict[int, _IntentState] = {}

    # -- lifecycle -----------------------------------------------------------
    def start(self, intents: list[Intent]) -> None:
        for intent in intents:
            st = _IntentState(intent)
            self._states.append(st)
            self._by_uid[intent.user_id] = st
            self.queue.schedule_at(intent.t_arrival, lambda st=st: self._on_arrival(st))

    def push_definitive(self, user_id: int, outcome: Outcome) -> None:
        """Server-push delivery (rung 4): the waiting room resolves tokens
        server-side — booked when a token's turn completes, sold-out on
        eviction — and pushes the definitive answer (the SMS/notification
        channel real waiting rooms have). Cancels any open attempt; the
        client stops polling because the intent is done."""
        st = self._by_uid.get(user_id)
        if st is None or st.done:
            return
        st.open_attempt = None  # any in-flight response is now stale
        if st.t_first is None:  # pushed before the client ever began (rare)
            st.t_first = self.clock.now()
            self._active += 1  # keep _finish's slot bookkeeping balanced
        self._definitive(st, outcome)

    def _on_arrival(self, st: _IntentState) -> None:
        if self.fidelity.open_loop_arrivals or self._active < self.cfg.closed_loop_users:
            self._begin(st)
        else:
            self._waitlist.append(st)  # closed loop: wait for a slot

    def _begin(self, st: _IntentState) -> None:
        self._active += 1
        st.t_first = self.clock.now()
        st.patience = self.abandon_rng.uniform(0.5, 1.5) * self.cfg.patience_mean
        self._submit(st)

    def _finish(self, st: _IntentState) -> None:
        st.done = True
        self._active -= 1
        if not self.fidelity.open_loop_arrivals and self._waitlist:
            nxt = self._waitlist.pop(0)
            self._begin(nxt)

    # -- one attempt ---------------------------------------------------------
    def _speed(self, st: _IntentState) -> float:
        return self.cfg.bot_speedup if st.intent.cohort == "bots" else 1.0

    def _submit(self, st: _IntentState, *, is_poll: bool = False) -> None:
        if st.done:
            return
        st.attempt_counter += 1
        token = st.attempt_counter
        st.open_attempt = token
        if not is_poll and self.clock.now() >= self.wcfg.t0:
            st.attempts += 1
        self.log.append(("request", self.clock.now(), st.intent.user_id, st.attempt_counter))

        def respond(outcome: Outcome, token: int = token) -> None:
            if st.open_attempt == token and not st.done:
                st.open_attempt = None
                self.log.append(("response", self.clock.now(), st.intent.user_id, outcome.value))
                self._on_outcome(st, outcome)
            else:
                # late answer to a closed attempt: dropped here, but LOGGED —
                # wasted-work attribution (R3.6 metric) pairs these with the
                # server's "served" entries at the same (t, uid)
                self.log.append(("stale_response", self.clock.now(), st.intent.user_id))

        self.service.submit(st.intent.user_id, st.intent.pool, respond)
        timeout = self.cfg.timeout_s * self._speed(st)
        self.queue.schedule_in(timeout, lambda: self._on_timeout(st, token))

    def _on_timeout(self, st: _IntentState, token: int) -> None:
        if st.open_attempt == token and not st.done:
            st.open_attempt = None
            self.log.append(("timeout", self.clock.now(), st.intent.user_id, st.attempt_counter))
            self._retry_or_abandon(st)

    # -- the outcome matrix --------------------------------------------------
    def _on_outcome(self, st: _IntentState, outcome: Outcome) -> None:
        now = self.clock.now()
        if outcome is Outcome.NOT_OPEN:
            if now < self.wcfg.t0:  # pre-T0: poll, then real attempt at T0
                nxt = min(now + self.wcfg.pre_fire_poll, self.wcfg.t0)
                self.queue.schedule_at(nxt, lambda: self._submit(st, is_poll=nxt < self.wcfg.t0))
            else:  # post-T0 "not open" is a server bug shape; treat as hard error
                self._retry_or_abandon(st)
            return
        if outcome is Outcome.QUEUE_POSITION:
            # a queue position is a PROGRESS signal: patience for the polling
            # loop runs from token issuance, not from the first request —
            # otherwise pre-fire campers quit the moment they get queued
            if st.t_token is None:
                st.t_token = now
            if now - st.t_token > st.patience:
                self._abandon(st)
            else:  # poll status; polling is not a retry. Bots poll at their
                # faster cadence (R3.9) — the signal P8's classifier reads.
                self.queue.schedule_in(
                    self.cfg.poll_interval * self._speed(st),
                    lambda: self._submit(st, is_poll=True),
                )
            return
        if outcome in DEFINITIVE:
            if (
                outcome in RETRYABLE_REJECTS
                and self.retry_rng.random() < self.cfg.p_retry_after_reject
            ):
                self._retry_or_abandon(st)
            else:
                self._definitive(st, outcome)
            return
        # HARD_ERROR
        self._retry_or_abandon(st)

    def _retry_or_abandon(self, st: _IntentState) -> None:
        now = self.clock.now()
        exhausted = (
            not self.fidelity.retries_enabled
            or st.attempts >= self.cfg.max_attempts
            or (st.t_first is not None and now - st.t_first > st.patience)
        )
        if exhausted:
            self._abandon(st)
            return
        backoff = (
            self.cfg.backoff_base
            * (self.cfg.backoff_mult ** max(0, st.attempts - 1))
            * self._speed(st)
        )
        self.queue.schedule_in(backoff, lambda: self._submit(st))

    def _definitive(self, st: _IntentState, outcome: Outcome) -> None:
        ttda = self.clock.now() - (st.t_first if st.t_first is not None else self.clock.now())
        self.log.append(
            ("definitive", self.clock.now(), st.intent.user_id, outcome.value, repr(ttda))
        )
        self._finish(st)

    def _abandon(self, st: _IntentState) -> None:
        self.log.append(("abandon", self.clock.now(), st.intent.user_id))
        self._finish(st)


# -- P2.3 helpers over the raw log (superseded by P5.1's metrics) ------------
def total_requests(log: list[LogEntry]) -> int:
    return sum(1 for e in log if e[0] == "request")


def requests_in_window(log: list[LogEntry], a: float, b: float) -> int:
    return sum(1 for e in log if e[0] == "request" and a <= e[1] < b)


def peak_in_flight(log: list[LogEntry]) -> int:
    """Max concurrent open attempts — the D10/S5 offered-concurrency gauge."""
    delta = {"request": +1, "response": -1, "timeout": -1}
    inflight = peak = 0
    for e in sorted(log, key=lambda e: e[1]):
        inflight += delta.get(e[0], 0)
        peak = max(peak, inflight)
    return peak


def peak_rate(log: list[LogEntry], bin_s: float = 0.5) -> float:
    """Max requests/second over fixed bins — 'peak offered load'."""
    bins: dict[int, int] = {}
    for e in log:
        if e[0] == "request":
            bins[int(e[1] // bin_s)] = bins.get(int(e[1] // bin_s), 0) + 1
    return max(bins.values()) / bin_s if bins else 0.0


def retry_amplification(log: list[LogEntry], n_users: int, identity_on: bool) -> float:
    """total requests / unique intents; identity OFF hides it (R3.10)."""
    reqs = total_requests(log)
    unique = n_users if identity_on else reqs
    return reqs / unique if unique else 0.0


def winners_by_cohort(log: list[LogEntry], intents: list[Intent]) -> dict[str, int]:
    cohort_of = {i.user_id: i.cohort for i in intents}
    wins: dict[str, int] = {}
    for e in log:
        if e[0] == "definitive" and e[3] == Outcome.BOOKED.value:
            wins[cohort_of[e[2]]] = wins.get(cohort_of[e[2]], 0) + 1
    return wins
