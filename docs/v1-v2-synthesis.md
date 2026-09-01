# What survives contact with a Tatkal-scale spike: a v1–v2 synthesis

**Status:** draft (2026-09-01, per decision D6 in
`specs/tatkal-v3/decisions.md`; audience per D7: practitioners judging
transfer, not students reproducing — reproduction is Appendix A).

## The one-paragraph version

We simulated India's IRCTC Tatkal booking spike — demand over supply
by roughly 20–50×, released at a known clock instant — with a seeded
discrete-event simulator calibrated against a real HTTP + Postgres
`SELECT FOR UPDATE` endpoint, and ran two pre-registered experiment
cycles over it: v1 ablated six classical engineering mechanisms; v2
ablated three allocation mechanisms against v1's best engineering.
The transferable result is a hierarchy: **bounded admission recovers
almost everything that engineering can recover; every classical
mechanism above it is marginal, corner-dependent, or actively
harmful; and fairness — who gets a seat — never moved until the
*allocation rule* changed.** A lottery over a qualification window
delivered bot/human parity that no engineering rung approached, and
the celebrated virtual waiting room failed to survive the costing of
its own notification channel. Two deliberate negatives (adaptive
concurrency limiting, paced drain) are reported as findings, not
buried. Every claim below carries its evidence and its transfer
limit; the threats-to-validity section is load-bearing, not
boilerplate.

## How the evidence was produced (compressed)

- **Instrument:** single-process, seeded, deterministic DES
  (`src/tatkal_sim`). Ten fidelity toggles — open-loop arrivals,
  retry amplification, bounded capacity, atomic inventory, sub-second
  T0 concentration, wasted work, heavy-tailed service, Zipf demand, a
  bot cohort, per-user identity — all ON in every evidentiary run.
  Each exists because turning it off produces a *flattering lie* (a
  mechanism that only looks good because the simulation was
  unfaithful).
- **Calibration:** the server model is fitted to a 2026-08-11
  measurement of a real ~150-line HTTP endpoint doing genuine
  row-locked seat decrements against Postgres
  (`specs/tatkal-spike-prototype/calibration/2026-08-11-postgres-http.csv`,
  fit record `fit-2026-08-11.json`). The fit is faithful on
  throughput and tail *direction* and conservative ~0.6–0.7× on tail
  *magnitude*; all arms run on the same conservative model, so
  *comparisons* stand even where absolute numbers understate pain.
  An earlier SQLite measurement is **withdrawn provenance** — it
  informed early threshold drafting and is not an anchor.
- **Discipline:** thresholds and constants pre-registered before any
  run; misses reported, never adjusted (two are on the record —
  v1's winners bar, v2's degenerate burst floor). Paired per-seed
  statistics, 20 seeds per cell (reduced cells labelled), bootstrap
  CIs; v2 adds Holm correction over its 22 inventoried comparisons.
  Chair-ruled append-only decision ledgers gate every phase.
- **Scale:** v1 operating point ~13× overall / ~40× hot-pool
  oversubscription, 200 seats; v2 ran 780 registered runs (39 cells
  × 20 seeds).

## Claims, with evidence and transfer limits

**C1 — Bounded admission recovers the collapse; it is most of the
achievable engineering gain.** One mechanism — a bounded worker pool
with FIFO queueing — took the naive arm from 47% hard errors, 335
seats/s and 1.72 s rejected-p99 to zero hard errors, 1733 seats/s
and 53 ms (v1 §2, F1). Nothing above it on the ladder came close to
that delta. *Transfer:* the direction is textbook and robust; the
magnitudes are model-specific. If you run a sale, a drop, or a quota
release and have no admission bound, this is the only finding you
need.

**C2 — Above the strong baseline (bounded + FIFO + fast-fail),
classical engineering is marginal and corner-dependent.** Sharding
by hot key: +36 seats/s, real but an order of magnitude smaller than
C1 (v1 §3). The virtual waiting room: the largest goodput gain above
baseline (+338/s, distinguishable) but its latency advantage was
*not* statistically distinguishable, held in only 2 of 8 sensitivity
cells, and **reversed catastrophically under a
congestion-collapsing backend** — its own status-polling stream
strangled the drain it was protecting (8.5 s resolutions at 23
seats/s, worse than doing nothing clever; v1 §4). *Transfer:* before
deploying a waiting room, know your backend's overload shape; on a
collapsing backend, fast-fail beats a room.

**C3 — The waiting room does not survive costing its own
notification channel.** v1 modelled push delivery as free and the
room looked strong. v2 charged for it: at a push cost of just **one
quarter of one status check**, the room is significantly *worse*
than plain fast-fail, and even at zero cost its advantage is
indistinguishable under the v2 population (v2 §3). *Transfer:* this
is the synthesis's sharpest practitioner warning, and it
generalizes: **any mechanism whose benefit case leaves its own
infrastructure uncosted is unevaluated.** v1 made exactly this
mistake, caught it in limitations, and v2 closed it — which is the
process working, but only because the question was forced.

**C4 — Adaptive concurrency limiting lost to the hand-tuned
constant it was meant to replace.** The AIMD swap regressed rejected
p99 from 41 ms to 258 ms and goodput from 2079 to 666 seats/s
(v1 F3). It was stable across knee variants; it was also strictly
worse at the operating point. *Transfer:* narrow — one controller,
one target — but a useful counterweight to the assumption that
adaptive always beats static. The tuning cost you save reappears as
regret at the operating point you actually run at.

**C5 — Fairness never moved until the allocation rule changed; then
it moved to parity.** Through every classical rung, the bot cohort's
seat advantage stayed ~5.2× — engineering *ordered* the latency
contest without changing who wins it (v1 §9). Under a lottery over a
qualification window (M2) and a pre-registration window (M1), bot
advantage went to ~1.0× — parity — while engineering baselines left
~3.9× on the v2 population, and every allocation-vs-engineering
comparison was Holm-distinguishable (v2 §1). *Transfer, with the
honest caveat attached:* parity at zero abuse is close to
**true-by-construction** — a draw over registered identities is
timing-blind by design, and the simulator partly re-derives the
mechanism's definition. The claim that carries information is not
"lotteries are fair" but the pair of results around it: engineering
*cannot* get there while the contest is a race (C1–C2 bound how much
it can do), and the lottery's fairness is *durable under abuse*
(C6) — which is not true by construction at all.

**C6 — Identity abuse pays linearly at low prevalence, self-dilutes
at scale, and never returns the advantage to bot-like levels.** An
abuser holding m = 5 identities gains ≈ m× at low abuse prevalence;
as prevalence grows, abusers crowd each other out (controller
advantage 4.46 → 3.46 across the prevalence grid) while staying
under the super-linearity guard. Honest-user fairness still degrades
monotonically with prevalence — self-dilution is not mitigation
(v2 §2). *Transfer:* multi-identity abuse is the lottery's real
attack surface; pricing identities is the v3 question
(three arms are ledgered: verification-cost, deposit,
registration-bound — D5/D9).

**C7 — Deliberately paced drain backfired on both of its own
goals.** M3 concentrated the entire bot advantage into the early
tranches (camp bots re-arrive within 50 ms of every tranche open),
made whole-run fairness *worse* than engineering (+1.4 vs
baselines), and starved inventory — 125 of 200 seats sold, because
rejected users leave and late tranches open onto campers (v2 §4).
*Transfer:* pacing a scarce drop without a retry/return model is a
gift to whoever can afford to camp. Whether rejected-demand
re-entry rescues it is registered v3 work (D2), not assumed.

**C8 — Timing-based bot classification works exactly where it can't
matter most.** The equal-effort classifier halved the bot advantage
against machine-shaped automation *including a held-out family it
never trained on* — and slightly worsened fairness against
human-mimicking bots, breaching its pre-registered guard: it pays
its false-positive cost without finding the bots (v1 §5). Deeper
structural finding (F5): at a ~100 ms sell-out, timing features are
blind — everyone present is "early," nobody has a second request
yet, and classification degenerates to FIFO. **Classification needs
the contest to outlast the population's arrival spread; mechanisms
that lengthen the contest are therefore prerequisites for, not
alternatives to, behavioural detection.** *Transfer:* strong, and
adversarially eroding — bots converge on human shapes.

## Threats to validity — read before reusing any number

1. **One calibration anchor, one machine.** The server model rests
   on a single Postgres/HTTP measurement lineage on one laptop
   (SQLite withdrawn). Seed-level sampling error is tightly
   controlled (paired stats, 10k bootstraps, Holm in v2);
   **structural model error is not, and it is the dominant risk.**
   A second, independent anchor — different engine or different
   hardware — is ruled in but not yet chosen (D8/D10, OQ4). Until
   it lands, the flat-median / exploding-tail server shape is a
   one-lineage observation.
2. **Tail magnitudes are conservative ~0.6–0.7×.** Comparisons
   between arms stand (same model under every arm); absolute
   latencies understate real pain.
3. **The headline is knee-shape-dependent, and honestly so.** Under
   the plateau server the waiting-room story is clean; under the
   fitted server it is inconclusive; under the cliff server it
   reverses catastrophically. v1's own draft once claimed otherwise
   and was corrected at review — the correction is on the record.
4. **Fairness results ride on population assumptions.** Cohort
   sizes, the 60/30/30/30 strategy mix, m = 5 identities, bot
   repertoires: fixed by ledger (D13/D3), never fitted to data. The
   *comparisons* across mechanisms share the population, but how
   much of any absolute fairness number is population-encoded is
   unknown. No real-world behavioural trace validates the cohorts.
5. **Parity is partly definitional** (see C5's caveat). The
   informative results are the abuse economics and the negatives,
   not the parity headline.
6. **v1's ~20 comparisons carry no multiplicity correction** (v2's
   22 do). Isolated marginal v1 results deserve suspicion; the
   ladder's big effects (C1, C4) dwarf that concern.
7. **The review loop is closed.** Chair, seats, and executors are
   one person plus the models he prompts. Pre-registration guards
   thresholds, not blind spots. This document exists partly to open
   that loop; external review has not yet happened.
8. **Simulated mechanisms carry no policy authority.** Nothing here
   contacted IRCTC or its users; mechanism results inform a
   discussion, not a deployment. The registration-surface finding
   (v2 §6: the pre-window absorbed its load trivially) is
   scale-dependent and was probed at one population/window regime
   only.

## Claim → evidence → v3 gap

| # | Claim | Evidence | What v3 owes it |
|---|---|---|---|
| C1 | Bounded admission recovers the collapse | v1 F1, §2–3 | Nothing — settled at this fidelity |
| C2 | Above the strong baseline, engineering is marginal/corner-dependent | v1 §3–4 | Nothing new; cliff-variant reporting carries (v2 §7) |
| C3 | Waiting room fails costed push | v2 §3 (break-even ≤ 0.25×) | Extend costing to M1/M2 bursts — the un-run D14.2 grid (D2.2) |
| C4 | Adaptive limiting regressed | v1 F3 | None (one controller tested; wider claim needs new arms) |
| C5 | Only allocation moves fairness; parity delivered | v1 §9, v2 §1 | Costed-pool gateway modelling so the parity isn't infrastructure-subsidized (D9) |
| C6 | Abuse pays ≈ m, self-dilutes, degrades honest fairness | v2 §2 | The three identity-pricing arms: which currency reclaims parity (D5, D9) |
| C7 | Paced drain backfires; inventory starves | v2 §4 | p_retry_after_reject sweep: does re-entry rescue M3? (D2.3) |
| C8 | Classification needs a long contest; mimics defeat timing | v1 §5, F5 | Nothing registered; adversarial co-evolution stays deferred |
| — | Server model rests on one anchor lineage | v1 §10, v2 §7 | Second anchor per D8/D10 — engine or hardware, chair to rule (OQ4) |

## Appendix A — reproduction (demoted per D7)

Everything is committed and seeded; no cloud resources are involved.

- Simulator: `src/tatkal_sim` (Python; `requirements.txt` pins).
- v1 pipeline: `tools/calibrate_r2.py` + `tools/r2_server.py`
  (measurement; needs local Postgres), `tools/fit_calibration.py`
  (fit), phase reports under `specs/tatkal-spike-prototype/reports/`,
  evaluation via `tools/p9_evaluation.py` →
  `reports/p9-evaluation-data.json`.
- v2 pipeline: `tools/v2_floors.py`, `tools/v5_baselines.py`,
  `tools/v6_sweeps.py` (39 cells × 20 seeds),
  `tools/v7_grading.py` → `specs/tatkal-v2/reports/*-data.json`.
- Graded records: `specs/tatkal-spike-prototype/RESULTS.md`,
  `specs/tatkal-v2/RESULTS.md`. Decision ledgers: `decisions.md` in
  each spec directory (v2 sealed at D19; tag `tatkal-v2-sealed`).
- Identical seeds reproduce byte-identical simulator results (v1 R1
  acceptance).

## Provenance

Commissioned by D6 (`specs/tatkal-v3/decisions.md`), from round-table
thread `q-project-critical-review-001` (2026-09-01, 3/3 seats
convergent). Audience ruling D7; anchor rulings D8/D10; gateway
ruling D9. Sources: the two graded RESULTS records and the sealed
ledgers; nothing in this document introduces new measurements.
