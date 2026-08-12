"""P0.3 acceptance — the wall-clock lint.

R1 requires byte-identical results from identical seeds; any wall-clock
read inside `src/` is a nondeterminism hole. This walks every source AST
and flags:

- `import time` / `from time import ...` (the whole module is banned —
  sim time comes from the virtual clock only);
- calls shaped `datetime.now/utcnow/today(...)` or `date.today(...)`.

The attribute check is deliberately narrow (receiver named `datetime` or
`date`) so the virtual clock's own `clock.now()` never false-positives.
Best-effort by design: the hard ban on the `time` module is the load-
bearing rule; the datetime patterns catch the common aliases-free case.
"""

import ast
import pathlib

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "tatkal_sim"

_BANNED_ATTRS = {"now", "utcnow", "today"}
_BANNED_RECEIVERS = {"datetime", "date"}


def wallclock_violations(source: str, filename: str = "<mem>") -> list[str]:
    out = []
    for node in ast.walk(ast.parse(source, filename=filename)):
        if isinstance(node, ast.Import):
            if any(a.name == "time" or a.name.startswith("time.") for a in node.names):
                out.append(f"{filename}:{node.lineno} imports time")
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == "time" or node.module.startswith("time.")):
                out.append(f"{filename}:{node.lineno} imports from time")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            func = node.func
            if (
                func.attr in _BANNED_ATTRS
                and isinstance(func.value, ast.Name)
                and func.value.id in _BANNED_RECEIVERS
            ):
                out.append(f"{filename}:{node.lineno} calls {func.value.id}.{func.attr}()")
    return out


def test_src_tree_is_wallclock_free():
    assert SRC.is_dir(), f"missing source tree: {SRC}"
    all_violations = []
    for path in sorted(SRC.rglob("*.py")):
        all_violations += wallclock_violations(path.read_text(), str(path))
    assert not all_violations, "wall-clock usage in src/:\n" + "\n".join(all_violations)


def test_checker_detects_planted_time_import():
    assert wallclock_violations("import time\n")
    assert wallclock_violations("from time import sleep\n")
    assert wallclock_violations("import time as t\n")


def test_checker_detects_planted_datetime_now():
    planted = "from datetime import datetime\nx = datetime.now()\n"
    assert wallclock_violations(planted)
    assert wallclock_violations("from datetime import date\nd = date.today()\n")


def test_checker_allows_virtual_clock():
    # the sim's own clock.now() must NOT trip the lint
    assert not wallclock_violations("t = clock.now()\n")
    assert not wallclock_violations("import datetime\n")  # module import alone is fine
