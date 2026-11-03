"""Mutation self-test for the rip_cleanup explorer (moved from the old skill dir).

Proves the checker (scripts/explore.py) can fail: each mutant below breaks
one load-bearing line of the real kit, and the self-test requires the
explorer to report the expected property id for it. Also runs the explorer
on an unmodified copy and requires exit 0 (baseline).

Each mutant is data: name, edits (file under the scratch root, exact old
text, replacement text), expected property ids, plain-words description.
A mutant whose old text does not occur EXACTLY once fails loudly
("mutant <name> no longer applies: <file>").

Mutant catalogue (M1-M10 per the design contract, M11-M12 per lead):
 M1  cursor_before_invoke  rip_runs._run_saved: `run.cursor += 1` moved
     before `invoke(...)`, so a failed step is skipped on retry. P1 or P2.
 M2  no_running_guard      rip_runs._run_saved: re-entry guard deleted. P1.
 M3  finish_clears_all     rip_runs._finish_run: pop-one -> clear-all. P2/P3.
 M4  door_not_agent_bound  arrest._may_act: agent binding dropped. P3.
 M5  del_ignores_saved_run lifecycle._rip: saved run lookup forced None. P4.
 M6  no_upfront_revoke     lifecycle._rip_field: revoke-everyone-first loop
     deleted. P5.
 M7  field_rip_continues   lifecycle._rip_field: per-member `_run_one` wrapped
     in try/except Exception: continue. P6.
 M8  running_stays_set     rip_runs._run_saved: `run.running = False` removed
     from `finally`. P2.
 M9  retry_restarts        rip_runs._run_saved: `run.cursor = 0` on failure. P1.
 M10 act_not_gated         arrest._require_available: return immediately. P3.
 M11 revoke_every_retry    _run_saved revokes on every retry AND _revoke loses
     its `if run.revoked: return` early return AND `fresh` forced False, so a
     retry ends a fresh re-Tagging. P4.
 M12 no_retry_older        lifecycle._rip: the `retry_older` block after the
     run is deleted. PROBE, expected uncaught: the HEAL/act path still drains
     older work, so this is equivalent-for-our-properties. Reported only.

Usage (plain python3 from the repo root, stdlib only, deterministic):
  python3 .claude/skills/verify-rip-cleanup/scripts/self_test.py [--quick] \
      [--mutants M1,M4] [--timeout S]

Exit 0 only if the baseline passes and every non-probe mutant is caught.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # formal/rip_cleanup/real/ -> repo root
EXPLORE = SCRIPT_DIR / "explore.py"
TOPKIT_SRC = REPO_ROOT / "TopKit"

MUTANTS = [
    dict(
        name="M1",
        title="cursor_before_invoke",
        expected=["P1", "P2"],
        why="cursor advances before the step runs, so a failed step is "
            "skipped on retry instead of re-run (order broken / owed step lost).",
        edits=[("TopKit/rip_runs.py",
"""            while run.cursor < len(run.teardowns):
                name, teardown = run.teardowns[run.cursor]

                try:
                    invoke(run, name, teardown)
                except Exception as error:
                    raise TagCompositionError(
                            f"{_tag_name(run.tag)} teardown failed in:"
                            f" {str.__str__(name)};"
                            " the Agent is arrested"
                            ) from error

                run.cursor += 1
""",
"""            while run.cursor < len(run.teardowns):
                name, teardown = run.teardowns[run.cursor]
                run.cursor += 1

                try:
                    invoke(run, name, teardown)
                except Exception as error:
                    raise TagCompositionError(
                            f"{_tag_name(run.tag)} teardown failed in:"
                            f" {str.__str__(name)};"
                            " the Agent is arrested"
                            ) from error
""")],
    ),
    dict(
        name="M2",
        title="no_running_guard",
        expected=["P1"],
        why="the re-entry guard is gone, so a step can run twice at once via "
            "a nested retry (replay).",
        edits=[("TopKit/rip_runs.py",
"""    if run.running:
        raise TagCompositionError(
                f"{_tag_name(run.tag)} teardown is already running"
                )
""",
"""    # MUTANT M2 no_running_guard: re-entry guard deleted.
""")],
    ),
    dict(
        name="M3",
        title="finish_clears_all",
        expected=["P2", "P3"],
        why="finishing one run drops every run in custody, so owed cleanup "
            "vanishes and the Agent walks free with unfinished work.",
        edits=[("TopKit/rip_runs.py",
"""            arrest.runs.pop(index)
""",
"""            arrest.runs.clear()  # MUTANT M3 finish_clears_all.
""")],
    ),
    dict(
        name="M4",
        title="door_not_agent_bound",
        expected=["P3"],
        why="any open Rip door authorises any arrested Agent, so another "
            "Agent's cleanup lets this Agent act (arrest no longer holds).",
        edits=[("TopKit/arrest.py",
"""            door.active and door.agent is agent
""",
"""            door.active  # MUTANT M4 door_not_agent_bound.
""")],
    ),
    dict(
        name="M5",
        title="del_ignores_saved_run",
        expected=["P4"],
        why="`del T[x]` never selects the saved old application, so it starts "
            "fresh work that ends (revokes) the fresh re-Tagging instead of "
            "the owed cleanup.",
        edits=[("TopKit/lifecycle.py",
"""    pending = _pending_run(agent, tag) if _safehouse else None
""",
"""    pending = None  # MUTANT M5 del_ignores_saved_run.
""")],
    ),
    dict(
        name="M6",
        title="no_upfront_revoke",
        expected=["P5"],
        why="field Rip runs each member's first step while that member is "
            "still seated, instead of revoking every starting member first.",
        edits=[("TopKit/lifecycle.py",
"""    # Publish every original application before any revocation can fail.
    for agent, state, run in pending:
        _revoke(agent, state, run)
""",
"""    # MUTANT M6 no_upfront_revoke: starting Field is NOT revoked up front.
""")],
    ),
    dict(
        name="M7",
        title="field_rip_continues",
        expected=["P6"],
        why="field Rip swallows a member's failure and keeps running later "
            "members' steps directly instead of stopping.",
        edits=[("TopKit/lifecycle.py",
"""    for agent, state, run in pending:
        _run_one(agent, state, run)
        if _arrest_of(agent) is not None and not _may_act(agent):
            _retry_arrested(agent)
""",
"""    for agent, state, run in pending:
        try:
            _run_one(agent, state, run)
        except Exception:
            continue
        if _arrest_of(agent) is not None and not _may_act(agent):
            _retry_arrested(agent)
""")],
    ),
    dict(
        name="M8",
        title="running_stays_set",
        expected=["P2"],
        why="a failed run keeps `running` set, so no retry can ever finish it "
            "(stuck custody / stuck `running` flag).",
        edits=[("TopKit/rip_runs.py",
"""        run.running = False
""",
"""        pass  # MUTANT M8 running_stays_set: flag never cleared.
""")],
    ),
    dict(
        name="M9",
        title="retry_restarts",
        expected=["P1"],
        why="a failed run restarts at step 0, so steps that already returned "
            "normally run again (replay).",
        edits=[("TopKit/rip_runs.py",
"""                try:
                    invoke(run, name, teardown)
                except Exception as error:
                    raise TagCompositionError(
""",
"""                try:
                    invoke(run, name, teardown)
                except Exception as error:
                    run.cursor = 0  # MUTANT M9 retry_restarts.
                    raise TagCompositionError(
""")],
    ),
    dict(
        name="M10",
        title="act_not_gated",
        expected=["P3"],
        why="acts on an arrested Agent skip both the retry and the refusal, "
            "so custody no longer gates ordinary acts.",
        edits=[("TopKit/arrest.py",
"""    if _may_act(agent):
        return
""",
"""    return  # MUTANT M10 act_not_gated: no retry, no refusal.
""")],
    ),
    dict(
        name="M11",
        title="revoke_every_retry",
        expected=["P4"],
        why="revoke runs on every retry with no revoked early-return and no "
            "fresh-seat preservation, so finishing old cleanup ends a fresh "
            "re-Tagging of the same Tag.",
        edits=[
            ("TopKit/rip_runs.py",
"""            if not run.revoked:
                revoke(run)
                run.revoked = True
""",
"""            revoke(run)  # MUTANT M11: revoke on every retry, no guard.
            run.revoked = True
"""),
            ("TopKit/lifecycle.py",
"""    if run.revoked:
        return
""",
"""    # MUTANT M11: revoked early-return removed; revoke always proceeds.
"""),
            ("TopKit/lifecycle.py",
"""    fresh = member is not None and member is not run.member
""",
"""    fresh = False  # MUTANT M11: a fresh re-Tagging is never preserved.
"""),
        ],
    ),
    dict(
        name="M12",
        title="no_retry_older",
        expected=[],
        why="PROBE (expected uncaught): deleting the post-run retry of older "
            "saved work changes no checked property, because the HEAL/act "
            "path still drains older work before the final checks.",
        edits=[("TopKit/lifecycle.py",
"""    _run_one(agent, state, pending)

    if retry_older and _safehouse and _arrest_of(agent) is not None and not _may_act(agent):
        _retry_arrested(agent)

    return agent
""",
"""    _run_one(agent, state, pending)

    # MUTANT M12: older saved work is NOT retried after the run.
    return agent
""")],
    ),
]

VIOLATION_RE = re.compile(r"^VIOLATION ([A-Za-z0-9_]+):", re.MULTILINE)


def apply_mutant(scratch: Path, mutant: dict) -> None:
    """Apply one mutant's edits to the scratch tree; fail loudly on drift."""
    for rel, old, new in mutant["edits"]:
        target = scratch / rel
        text = target.read_text()
        found = text.count(old)
        if found != 1:
            raise SystemExit(
                f"mutant {mutant['name']} no longer applies: {rel} "
                f"(old text found {found} times, want exactly 1)")
        target.write_text(text.replace(old, new, 1))


def fresh_scratch() -> Path:
    """Copy the CURRENT TopKit tree to a new scratch dir under /tmp."""
    tmp = Path(tempfile.mkdtemp(prefix="rip_verify_"))
    shutil.copytree(TOPKIT_SRC, tmp / "TopKit", symlinks=False)
    return tmp


def run_python(args: list, cwd: Path, env_extra: dict, timeout: float):
    import os
    env = dict(os.environ)
    env.update(env_extra)
    return subprocess.run(
        args, cwd=str(cwd), env=env, capture_output=True, text=True,
        timeout=timeout)


def check_imports(scratch: Path, timeout: float) -> None:
    proc = run_python(
        [sys.executable, "-c", "import TopKit"], scratch,
        {"PYTHONPATH": str(scratch)}, timeout)
    if proc.returncode != 0:
        raise SystemExit(
            f"mutated tree at {scratch} does not import:\n{proc.stderr[-2000:]}")


def run_explorer(scratch: Path, extra: list, timeout: float):
    started = time.perf_counter()
    try:
        proc = run_python(
            [sys.executable, str(EXPLORE), "--root", str(scratch)] + extra,
            REPO_ROOT, {}, timeout)
    except subprocess.TimeoutExpired:
        return None, None, time.perf_counter() - started
    elapsed = time.perf_counter() - started
    found = VIOLATION_RE.findall(proc.stdout or "")
    return proc.returncode, found, elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true",
                        help="pass --quick to the explorer (fast sanity)")
    parser.add_argument("--mutants", default="",
                        help="comma list like M1,M4 (default: all)")
    parser.add_argument("--timeout", type=float, default=300.0,
                        help="seconds per explorer run (default 300)")
    parser.add_argument("--keep", action="store_true",
                        help="keep scratch dirs for inspection")
    opts = parser.parse_args()

    if not EXPLORE.is_file():
        print(f"error: explorer not found at {EXPLORE}", file=sys.stderr)
        return 2
    if not TOPKIT_SRC.is_dir():
        print(f"error: TopKit tree not found at {TOPKIT_SRC}", file=sys.stderr)
        return 2

    wanted = None
    if opts.mutants.strip():
        wanted = {m.strip().upper() for m in opts.mutants.split(",")}
    mutants = [m for m in MUTANTS
               if wanted is None or m["name"].upper() in wanted]
    if wanted:
        unknown = wanted - {m["name"].upper() for m in MUTANTS}
        if unknown:
            print(f"error: unknown mutants: {sorted(unknown)}", file=sys.stderr)
            return 2

    extra = ["--quick"] if opts.quick else []
    failures = []
    scratches = []

    def cleanup():
        if not opts.keep:
            for tmp in scratches:
                shutil.rmtree(tmp, ignore_errors=True)

    # Baseline: unmodified copy must exit 0.
    base = fresh_scratch()
    scratches.append(base)
    check_imports(base, opts.timeout)
    code, found, elapsed = run_explorer(base, extra, opts.timeout)
    if code is None:
        print(f"baseline: TIMEOUT after {elapsed:.1f}s (explorer hung)")
        failures.append("baseline TIMEOUT")
    elif code == 0:
        print(f"baseline: clean ({elapsed:.1f}s)")
    else:
        print(f"baseline: UNEXPECTED exit={code} ids={found} ({elapsed:.1f}s)")
        failures.append(f"baseline exit={code} ids={found}")

    for mutant in mutants:
        label = f"{mutant['name']} {mutant['title']}"
        tmp = fresh_scratch()
        scratches.append(tmp)
        try:
            apply_mutant(tmp, mutant)
        except SystemExit as failure:
            print(f"mutant {label}: ERROR {failure}")
            failures.append(f"{mutant['name']} does not apply")
            continue
        check_imports(tmp, opts.timeout)
        code, found, elapsed = run_explorer(tmp, extra, opts.timeout)
        probe = not mutant["expected"]
        if code is None:
            print(f"mutant {label}: TIMEOUT after {elapsed:.1f}s (explorer hung)")
            failures.append(f"{mutant['name']} TIMEOUT")
            continue
        hit = next((p for p in mutant["expected"] if p in (found or [])), None)
        if probe:
            if code == 0:
                print(f"mutant {label}: probe clean as expected ({elapsed:.1f}s)")
            else:
                print(f"mutant {label}: probe CAUGHT by {found} "
                      f"(exit={code}, {elapsed:.1f}s); why: {mutant['why']}")
        elif code == 1 and hit is not None:
            print(f"mutant {label}: caught by {hit} ({elapsed:.1f}s)")
        else:
            print(f"mutant {label}: MISSED (exit={code} ids={found}, "
                  f"{elapsed:.1f}s); want one of {mutant['expected']}")
            failures.append(f"{mutant['name']} MISSED")

    cleanup()
    if failures:
        print(f"SELF-TEST FAILED: {'; '.join(failures)}")
        return 1
    print(f"SELF-TEST PASSED: baseline clean, "
          f"{len([m for m in mutants if m['expected']])} mutants caught, "
          f"{len([m for m in mutants if not m['expected']])} probes reported.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
