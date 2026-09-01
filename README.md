# Indian Railroad Ticketing

A teaching project for learning Python development with an AI workflow harness
([`attune-ai`](https://pypi.org/project/attune-ai/)) in the loop.

> **Status: two experiment cycles concluded, third opened.** What began as a
> scaffold is now a systems experiment on the IRCTC Tatkal booking spike: a
> calibrated, seeded discrete-event simulator (`src/tatkal_sim`), two
> pre-registered experiment cycles with graded results, and a decisions-ledger
> workflow throughout.
>
> **Start here → [What survives contact with a Tatkal-scale spike: a v1–v2
> synthesis](docs/v1-v2-synthesis.md)** — the claims, their evidence, their
> transfer limits, and what the third cycle (v3) still owes. The full graded
> records live in [docs/specs/tatkal-spike-prototype/RESULTS.md](docs/specs/tatkal-spike-prototype/RESULTS.md)
> and [docs/specs/tatkal-v2/RESULTS.md](docs/specs/tatkal-v2/RESULTS.md); the
> live v3 ledger is [docs/specs/tatkal-v3/decisions.md](docs/specs/tatkal-v3/decisions.md).

---

## Prerequisites

- **Python 3.10 or newer.** `attune-ai` requires it. Check with `python3 --version`.
  If you use [pyenv](https://github.com/pyenv/pyenv), the pinned version is in
  `.python-version` and pyenv will pick it up automatically.
- **git** and a GitHub account.
- **An Anthropic API key** — see [API key](#api-key) below. This one costs money;
  read that section before running anything.

## Setup

```bash
git clone <your-copy-of-this-repo>
cd IndianRailroadTicketing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verify it worked:

```bash
python -c "import attune; print(attune.__version__)"
```

You should see `11.5.0`. Note the import name is **`attune`**, not `attune_ai` —
the PyPI package and the Python module are named differently, which trips
everyone up once.

The CLI is `attune`:

```bash
attune version
```

(It's `attune version`, not `attune --version`. The latter errors.)

## API key

`attune-ai` calls the Anthropic API. **Charges land on whoever owns the key**, so
use your own — never someone else's.

1. Create a key at <https://console.anthropic.com/>.
2. Put it in a `.env` file in the project root:

   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

`.env` is in `.gitignore` and must stay there. **Never commit an API key.** If you
ever do — even in a commit you immediately amend away — treat it as public,
revoke it in the console, and issue a new one. Deleting the commit is not enough;
it stays in the reflog and in anyone's existing clone.

Some `attune-ai` workflows fan out across multiple model calls and can spend more
than you expect. Set a spend limit in the Anthropic console before you start
experimenting, not after.

## Databases for calibration (optional — only for re-running R2/W4)

The calibration harness measures a real HTTP endpoint against a real
database. Two engines are involved, both run as **throwaway local
instances** (data dir outside the repo, no service registered):

- **PostgreSQL** — the primary v1 anchor (`tools/calibrate_r2.py`
  header shows the recipe; Homebrew `postgresql@17`).
- **MariaDB** — the v3 second anchor (decisions.md D11; Homebrew
  `mariadb`, driver `PyMySQL` pinned in `requirements.txt`). Recorded
  here per the no-ad-hoc-installs rule: the project now deliberately
  depends on a local MariaDB for the W4 anchor run.

You do not need either engine to run the simulator or its tests —
only to re-run the calibration measurements.

## Redis (optional)

`attune-ai` has memory features backed by Redis. **You do not need Redis for this
project.** Without it, the package degrades gracefully — memory-backed features
go quiet rather than crashing.

If you see log lines about Redis being unavailable, that is expected and safe to
ignore. Don't go installing Redis to chase those warnings unless we've explicitly
decided you need it.

## Layout

```
.
├── .gitignore
├── .python-version      # pyenv pin
├── README.md
└── requirements.txt     # attune-ai, pinned
```

`.venv/` is deliberately **not** committed — it's ~388 MB of platform-specific
binaries and would be useless on another machine. Everyone builds their own from
`requirements.txt`. Same for `.attune/`, which holds a local session database
that can contain the text of your prompts.

## Working on this

Dependencies are pinned (`attune-ai==11.5.0`) so everyone gets an identical
environment. If you need to add one, add it to `requirements.txt` with an exact
version rather than installing ad hoc — otherwise your machine and mine drift
apart and bugs stop reproducing.
