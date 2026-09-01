"""v3 priced entry — identity-pricing policies over the M2 draw path.

The one new v3 simulator concept (tatkal-v3 design §Shape, D13):
an identity's admission to a draw pool can carry a cost in work,
stake, or eligibility. Policies compose onto `LotteryPool` via
`PricedLotteryPool`; the draw itself is untouched, so every v3/v2
fairness delta is attributable to the pricing (design §Shape).

With `policy=None` the pool defers to the parent on every path and is
bit-identical to v2 M2 (W1.1 acceptance; guarded by test).

Policies (D5 arms, D9 costed-pool ruling, DC1–DC3 as amended by D17):

- `VerificationPolicy` (A1, work-priced): entry costs a verification
  work item at `c_verify` (× app service time) on the SHARED worker
  pool; an identity joins the draw only if verification completes
  before the draw instant; the rest resolve as clean `verify-missed`
  rejections in the burst — never lost intents (W1.2).
- `DepositPolicy` (A2, money-priced): entry stakes `d` (V = 1).
  Abuser controllers enter k* identities per the D17-corrected DC2
  rule: k* maximizes P(>=1 win | k) · V − E[(wins − 1)+ | k] · d.
  At the draw, losers are refunded; one winning identity per
  controller redeems (bond returned, D17); excess winning identities
  forfeit and their bookings are never submitted. At d = 0 the
  policy MUST NOT be used — pass policy=None (pass-through), which
  is the registered continuity cell (W1.3).
- `RegistrationBoundPolicy` (A3, enrollment-priced): only identities
  with a registration instant may enter; unregistered attempts log
  an `ineligible` outcome and contest only post-draw leftovers.

Log events added (v1 tuple convention):
    ("verify_start", t, user_id)
    ("verify_done", t, user_id)          # wait = done − start
    ("verify_missed", t_draw, user_id)   # distinct from lottery-loss
    ("stake_in", t, user_id, d)
    ("stake_refund", t_draw, user_id, d)     # losers
    ("stake_return", t_draw, user_id, d)     # the redeemed identity
    ("stake_forfeit", t_draw, user_id, d)    # excess winning identities
    ("ineligible", t, user_id)

IMPLEMENTATION CONSTANT FLAGGED FOR CHAIR ENTRY (D1 discipline): DC4
registers the human deadline profile; abuser (identity-split)
registration timing in A3 is implemented as uniform over W (the
patient-abuser reading of D5) and camp bots carry their first-5%
rule. Needs a ratifying entry at the W2 gate.
"""

from __future__ import annotations

from tatkal_sim.model.users import Outcome
from tatkal_sim.model.workload_v2 import V2WorkloadConfig
from tatkal_sim.strategies.allocation import LotteryPool

#: DC1 grid (× app service time), registered by D13.
C_VERIFY_GRID = (0.25, 1.0, 4.0)
#: DC3 grid (× ticket value V = 1), registered by D13.
D_GRID = (0.1, 0.5, 2.0)


def expected_pool_identities(wcfg: V2WorkloadConfig) -> int:
    """The pool-size expectation an abuser forms from the registered
    population (DC2: all constants public inside the model). Every
    T0-cohort identity arrives within Q >> sigma_t0, so the expected
    pool is all humans + all bot identities."""
    n_split = round(wcfg.abuse_p * wcfg.n_bots)
    return wcfg.n_t0_humans + wcfg.n_bots + (wcfg.m_identities - 1) * n_split


def deposit_k_star(d: float, m: int, p_win: float, value: float = 1.0) -> int:
    """DC2 as amended by D17: k* = argmax over k in 0..m of
    P(>=1 win | k)·V − E[(wins−1)+ | k]·d, wins ~ Binomial(k, p_win).
    E[(wins−1)+] = k·p − (1 − (1−p)^k)."""
    best_k, best_v = 0, 0.0
    for k in range(m + 1):
        p_any = 1.0 - (1.0 - p_win) ** k
        excess = k * p_win - p_any
        v = p_any * value - excess * d
        if v > best_v + 1e-12:
            best_k, best_v = k, v
    return best_k


class VerificationPolicy:
    """A1 (R2.1, DC1). Verification work on the shared pool; join the
    draw iff verified before the draw instant."""

    def __init__(self, c_verify: float, *, retry_backoff: float = 0.05) -> None:
        self.c_verify = c_verify
        self.retry_backoff = retry_backoff
        self.pending: set[int] = set()

    def enter(self, pool: "PricedLotteryPool", uid: int) -> None:
        self.pending.add(uid)
        pool.log.append(("verify_start", pool.clock.now(), uid))
        self._work(pool, uid)

    def _work(self, pool: "PricedLotteryPool", uid: int) -> None:
        def done(o: Outcome) -> None:
            if o is Outcome.HARD_ERROR:  # pool saturated: retry, like push
                pool.queue.schedule_in(self.retry_backoff, lambda: self._work(pool, uid))
                return
            pool.log.append(("verify_done", pool.clock.now(), uid))
            if uid in self.pending:
                self.pending.discard(uid)
                if not pool.drawn:
                    pool.entries.append(uid)
                # verified after the draw: uid was already resolved as
                # verify-missed at the draw instant; nothing to do

        pool.server.submit_light_at(uid, Outcome.QUEUE_POSITION, done, self.c_verify)

    def before_draw(self, pool: "PricedLotteryPool") -> None:
        now = pool.clock.now()
        for uid in sorted(self.pending):
            pool.log.append(("verify_missed", now, uid))
            pool.resolved.add(uid)
            pool.push.deliver(uid, Outcome.SOLD_OUT)

    def after_draw(self, pool: "PricedLotteryPool") -> None:
        pool.default_winner_submission()


class DepositPolicy:
    """A2 (R2.2, DC2/DC3 as amended by D17). d = 0 is served by
    policy=None (pass-through continuity cell), enforced here."""

    def __init__(self, d: float, wcfg: V2WorkloadConfig, seats_total: int) -> None:
        if d <= 0.0:
            raise ValueError("d = 0 is the pass-through cell: use policy=None")
        self.d = d
        p_win = min(1.0, seats_total / expected_pool_identities(wcfg))
        self.k_star = deposit_k_star(d, wcfg.m_identities, p_win)
        self._entered_per_controller: dict[int, int] = {}
        self.staked: set[int] = set()

    def enter(self, pool: "PricedLotteryPool", uid: int) -> None:
        intent = pool.by_uid[uid]
        if intent.strategy == "identity_split":
            n = self._entered_per_controller.get(intent.controller_id, 0)
            if n >= self.k_star:
                return  # abuser declines to stake this identity
            self._entered_per_controller[intent.controller_id] = n + 1
        self.staked.add(uid)
        pool.log.append(("stake_in", pool.clock.now(), uid, self.d))
        pool.entries.append(uid)

    def before_draw(self, pool: "PricedLotteryPool") -> None:
        pass

    def after_draw(self, pool: "PricedLotteryPool") -> None:
        now = pool.clock.now()
        # every staked non-winner is refunded at the draw — including
        # identities whose client went inactive before it: the bond
        # follows the stake, not the session (D17 finding 2)
        for uid in sorted(self.staked - pool.winners):
            pool.log.append(("stake_refund", now, uid, self.d))
        # winners: one redemption per controller (lowest uid),
        # bond returned; excess winning identities forfeit and never book
        by_controller: dict[int, list[int]] = {}
        for uid in sorted(pool.winners):
            by_controller.setdefault(pool.by_uid[uid].controller_id, []).append(uid)
        for _, uids in sorted(by_controller.items()):
            redeemer, excess = uids[0], uids[1:]
            if redeemer in self.staked:
                pool.log.append(("stake_return", now, redeemer, self.d))
            p = pool.by_uid[redeemer].pool
            pool.inner.submit(redeemer, p, lambda o, u=redeemer: pool.push.deliver(u, o))
            for uid in excess:
                if uid in self.staked:
                    pool.log.append(("stake_forfeit", now, uid, self.d))
                pool.resolved.add(uid)
                pool.push.deliver(uid, Outcome.SOLD_OUT)


class RegistrationBoundPolicy:
    """A3 (R2.3, DC4). Eligibility = a registration instant on the
    intent; ineligible entries are logged and contest only post-draw
    leftovers through the serving layer."""

    def __init__(self) -> None:
        self._logged: set[int] = set()

    def enter(self, pool: "PricedLotteryPool", uid: int) -> None:
        if pool.by_uid[uid].t_register is None:
            if uid not in self._logged:
                self._logged.add(uid)
                pool.log.append(("ineligible", pool.clock.now(), uid))
            return  # not entered; post-draw fall-through still applies
        pool.entries.append(uid)

    def before_draw(self, pool: "PricedLotteryPool") -> None:
        pass

    def after_draw(self, pool: "PricedLotteryPool") -> None:
        pool.default_winner_submission()


class PricedLotteryPool(LotteryPool):
    """M2 with a priced-entry policy. policy=None defers to the parent
    on every code path (bit-identity with v2 M2 — W1.1)."""

    def __init__(self, *args, policy=None, **kw) -> None:
        super().__init__(*args, **kw)
        self.policy = policy

    def default_winner_submission(self) -> None:
        # the parent's post-draw winner forwarding, verbatim semantics
        for uid in sorted(self.winners):
            pool = self.by_uid[uid].pool
            self.inner.submit(uid, pool, lambda o, u=uid: self.push.deliver(u, o))

    def _draw(self) -> None:
        if self.policy is None:
            super()._draw()
            return
        self.policy.before_draw(self)
        self._draw_pools(self.entries)
        self.policy.after_draw(self)

    def submit(self, user_id: int, pool, respond) -> None:
        if self.policy is None:
            super().submit(user_id, pool, respond)
            return
        now = self.clock.now()
        if now < self.wcfg.t0:
            self.inner.submit(user_id, pool, respond)
            return
        if not self.drawn:
            if user_id not in self._entered:
                self._entered.add(user_id)
                self.policy.enter(self, user_id)
            self.server.submit_light(user_id, Outcome.QUEUE_POSITION, respond)
            return
        if user_id in self.winners or user_id in self.resolved:
            self.server.submit_light(user_id, Outcome.QUEUE_POSITION, respond)
            return
        self.inner.submit(user_id, pool, respond)
