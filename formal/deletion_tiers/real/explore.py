"""Exhaustive bounded exploration of Agent deletion tiers on the REAL TopKit.

Covers TopKit/lifecycle.py (_teardown_all, At_Exit, _forget_exit,
_run_exit_protocols), TopKit/access.py (_agent_del, _host_finalizer),
TopKit/state.py (finalizer wiring) and TopKit/arrest.py (Safehouse hold).

Method: stateless enumeration. Every case builds fresh Agents from a fixed
set of Tag archetypes on the real code, drives one deletion-tier act
(`del`+gc, a direct `_run_exit_protocols()` pass, an explicit Rip, or a
real subprocess exit), and checks the log against an independent expected
value derived from the spec (never from the code under test).

Bounds (default): 1-3 Tags per Agent drawn from {ok, Exception} teardown
archetypes (ordered, no repetition), interruption archetypes
{KeyboardInterrupt, SystemExit} at every seat, 1-2 Agents, Layer forms
{host-only, Underlay-chain, replacer, Delete}, with/without prior explicit
Rip, with/without At_Exit. `--quick` shrinks to <=2 Tags and fewer forms.
"""

from __future__ import annotations

import argparse
import gc
import io
import os
import subprocess
import sys
import textwrap
import time
import warnings
from contextlib import redirect_stderr

LOG: list[tuple[str, str]] = []  # ("tear"|"layer", name), in run order


def _import_topkit(root: str):
    root = os.path.realpath(root)
    if root not in [os.path.realpath(p) for p in sys.path]:
        sys.path.insert(0, root)
    import TopKit  # noqa: E402
    import TopKit.lifecycle as L  # noqa: E402
    import TopKit.arrest as A  # noqa: E402
    loc = os.path.realpath(TopKit.__file__)
    if not (loc.startswith(root + os.sep) or os.path.dirname(loc) == root):
        raise SystemExit(f"harness error: TopKit loaded from {loc}, not --root {root}")
    return TopKit, L, A


def _build_tags(TK):
    """Fixed archetypes. Behaviour is fixed per class; a case = which tags,
    in which application order. Distinct teardown names avoid overwrite
    warnings between independent Tags."""

    class K_OK(TK.Tag):
        @TK.Rip
        def Tear_ok(a):
            LOG.append(("tear", "K_OK"))

    class K_OK2(TK.Tag):
        @TK.Rip
        def Tear_ok2(a):
            LOG.append(("tear", "K_OK2"))

    class K_EXC(TK.Tag):
        @TK.Rip
        def Tear_exc(a):
            LOG.append(("tear", "K_EXC"))
            raise ValueError("boom")

    class K_KI(TK.Tag):
        @TK.Rip
        def Tear_ki(a):
            LOG.append(("tear", "K_KI"))
            raise KeyboardInterrupt("stop")

    class K_SE(TK.Tag):
        @TK.Rip
        def Tear_se(a):
            LOG.append(("tear", "K_SE"))
            raise SystemExit(3)

    class LU1(TK.Tag):
        @TK.Underlay
        def __del__(a, u):
            LOG.append(("layer", "LU1"))
            u()

    class LU2(TK.Tag):
        @TK.Underlay
        def __del__(a, u):
            LOG.append(("layer", "LU2"))
            u()

    class LR(TK.Tag):
        def __del__(a):
            LOG.append(("layer", "LR"))

    class LD(TK.Tag):
        @TK.Delete
        def __del__(a):
            LOG.append(("layer", "LD-never"))

    class HBase:
        def __del__(self):
            LOG.append(("layer", "host"))

    class HPlain:
        pass

    return {
        "K_OK": K_OK, "K_OK2": K_OK2, "K_EXC": K_EXC, "K_KI": K_KI,
        "K_SE": K_SE, "LU1": LU1, "LU2": LU2, "LR": LR, "LD": LD,
        "HBase": HBase, "HPlain": HPlain,
    }


FORMS = ("host", "chain", "replace", "delete")


def _form_layers(T, form):
    if form == "host":
        return []
    if form == "chain":
        return [T["LU1"], T["LU2"]]
    if form == "replace":
        return [T["LR"]]
    if form == "delete":
        return [T["LD"]]
    raise AssertionError(form)


def _expected_layers(form):
    if form == "host":
        return [("layer", "host")]
    if form == "chain":
        return [("layer", "LU2"), ("layer", "LU1"), ("layer", "host")]
    if form == "replace":
        return [("layer", "LR")]
    if form == "delete":
        return []
    raise AssertionError(form)


def _drop(agents: list) -> str:
    """Release agents and collect, swallowing finalizer stderr noise
    (BaseExceptions re-raised by the finalizer are reported by the
    interpreter as 'Exception ignored'; the LOG is the verdict)."""
    buf = io.StringIO()
    with redirect_stderr(buf):
        agents.clear()
        gc.collect()
        gc.collect()
    return buf.getvalue()


def _run_deletion(T, tags, form="host", host="HBase"):
    """Apply tags then layer-tags, delete the agent, return the LOG."""
    LOG.clear()
    holder = [T[host]()]
    for t in tags:
        t(holder[0])
    for t in _form_layers(T, form):
        t(holder[0])
    _drop(holder)
    return list(LOG)


class Explorer:
    def __init__(self, root: str, quick: bool = False):
        self.quick = quick
        self.TK, self.L, self.A = _import_topkit(root)
        self.root = os.path.realpath(root)
        self.T = _build_tags(self.TK)
        self.cases = 0
        self.violations: list[tuple[str, str, list[str]]] = []
        warnings.simplefilter("ignore")

    def fail(self, pid: str, msg: str, steps: list[str]):
        self.violations.append((pid, msg, steps))

    # ---- DT-1: every due teardown runs, reverse order, Exception isolated ----
    def dt1(self):
        T = self.T
        OK, OK2, EXC = T["K_OK"], T["K_OK2"], T["K_EXC"]
        combos = [[OK], [EXC]]
        pairs = [(OK, EXC), (EXC, OK), (OK, OK2), (OK2, OK),
                 (OK2, EXC), (EXC, OK2)]
        combos += [list(p) for p in pairs]
        if not self.quick:
            combos.append([OK, OK2, OK.__class__ and OK])  # placeholder, replaced below
            combos.pop()
            trips = []
            for pos in range(3):
                for oks in ([OK, OK2], [OK2, OK]):
                    seq = list(oks)
                    seq.insert(pos, EXC)
                    trips.append(seq)
            trips.append([OK, OK2, OK])  # repetition-free all-ok needs 3rd ok tag
            trips.pop()  # (no third ok archetype; use OK,OK2 pair + EXC only)
            combos += trips
            combos.append([OK, OK2, T["K_OK"]][:2] + [T["K_OK"]][:0] or [OK, OK2])
            # all-ok triple is impossible without repetition; use EXC-free pair
            # plus one triple with the interrupter covered by DT-6 instead.
        for tags in combos:
            names = [t.__name__ for t in tags]
            for form in ("host",) if self.quick else ("host", "chain"):
                self.cases += 1
                log = _run_deletion(T, tags, form)
                tears = [e for e in log if e[0] == "tear"]
                want = [("tear", n) for n in reversed(names)]
                if tears != want:
                    self.fail("DT-1",
                              f"deletion of [{','.join(names)}] ran tears {tears}, want {want}",
                              [f"apply {' then '.join(names)} to a host",
                               "del agent; gc.collect()",
                               f"observed tears: {[n for _, n in tears]}"])
                layers = [e for e in log if e[0] == "layer"]
                if layers != _expected_layers(form):
                    self.fail("DT-2",
                              f"deletion of [{','.join(names)}] ran layers {layers}",
                              [f"layer form {form}",
                               f"observed layers: {[n for _, n in layers]}"])

    # ---- DT-2: layers run even after failure / interruption ----
    def dt2(self):
        T = self.T
        outcomes = [T["K_OK"], T["K_EXC"]] if self.quick else [T["K_OK"], T["K_EXC"], T["K_KI"]]
        forms = ("host", "chain") if self.quick else FORMS
        for form in forms:
            for tag in outcomes:
                self.cases += 1
                log = _run_deletion(T, [tag], form)
                layers = [e for e in log if e[0] == "layer"]
                if layers != _expected_layers(form):
                    self.fail("DT-2",
                              f"form {form} with teardown {tag.__name__} ran layers {layers}, "
                              f"want {_expected_layers(form)}",
                              [f"apply {tag.__name__} plus layer form {form}",
                               "del agent; gc.collect()",
                               f"observed layers: {[n for _, n in layers]}"])

    # ---- DT-3: At_Exit pass completeness, isolation, weak, run-once ----
    def _exit_pass(self, specs):
        """specs: list of (host_cls_name, [tag names]). Registers every agent,
        runs the pass twice, returns (first_tears, rerun_tears, error)."""
        T = self.T
        L = self.L
        saved = dict(L._exit_registry)
        L._exit_registry.clear()
        agents = []
        try:
            LOG.clear()
            for host_name, tag_names in specs:
                a = T[host_name]()
                for n in tag_names:
                    T[n](a)
                agents.append(a)
            for a in agents:
                self.TK.At_Exit(a)
            err = None
            with redirect_stderr(io.StringIO()):
                try:
                    L._run_exit_protocols()
                except BaseException as e:  # noqa: BLE001 - interruption must not escape silently
                    err = e
            first = [e for e in LOG if e[0] == "tear"]
            mark = len(LOG)
            with redirect_stderr(io.StringIO()):
                try:
                    L._run_exit_protocols()
                except BaseException:  # noqa: BLE001
                    pass
            rerun = [e for e in LOG[mark:] if e[0] == "tear"]
            return first, rerun, err
        finally:
            L._exit_registry.clear()
            for k, v in saved.items():
                if v() is not None:
                    L._exit_registry[k] = v
            _drop(agents)
    def _check_exit_weak(self):
        # weak registration: death unregisters
        self.cases += 1
        L = self.L
        saved = dict(L._exit_registry)
        L._exit_registry.clear()
        try:
            a = self.T["HPlain"]()
            self.T["K_OK"](a)
            self.TK.At_Exit(a)
            before = len(L._exit_registry)
            holder = [a]
            del a
            _drop(holder)
            after = len(L._exit_registry)
            if not (before == 1 and after == 0):
                self.fail("DT-3",
                          f"At_Exit registry held {before} then {after} entries across agent death "
                          f"(want 1 then 0); registration must be weak",
                          ["At_Exit(agent)", "del agent; gc.collect()",
                           f"registry size before/after: {before}/{after}"])
            # unregistered agents are untouched by the pass
            LOG.clear()
            b = self.T["HPlain"]()
            self.T["K_OK"](b)
            holder2 = [b]
            with redirect_stderr(io.StringIO()):
                L._run_exit_protocols()
            if [e for e in LOG if e[0] == "tear"]:
                self.fail("DT-3", "unregistered agent's teardown ran in the At_Exit pass",
                          ["tag without At_Exit", "call _run_exit_protocols()"])
            _drop(holder2)
        finally:
            L._exit_registry.clear()
            for k, v in saved.items():
                if v() is not None:
                    L._exit_registry[k] = v

    def _check_exit_rerun(self, pairs):
        for specs in pairs:
            self.cases += 1
            _, rerun, _ = self._exit_pass(specs)
            if rerun:
                self.fail("DT-4",
                          f"second At_Exit pass re-ran {rerun}; teardowns must run at most once",
                          ["run _run_exit_protocols() twice",
                           f"second pass observed: {rerun}"])

    def dt3(self):
        pairs = [[("HPlain", ["K_OK"]), ("HPlain", ["K_EXC"])]]
        if not self.quick:
            pairs += [[("HPlain", ["K_EXC"]), ("HPlain", ["K_OK"])],
                      [("HPlain", ["K_OK"]), ("HPlain", ["K_OK"])],
                      [("HPlain", ["K_EXC"]), ("HPlain", ["K_EXC"])],
                      [("HPlain", ["K_OK"]), ("HPlain", ["K_OK2"])]]
        for specs in pairs:
            self.cases += 1
            first, _, err = self._exit_pass(specs)
            want = []
            for _, tag_names in specs:
                want += [("tear", n) for n in reversed(tag_names)]
            if sorted(first) != sorted(want) or err is not None:
                self.fail("DT-3",
                          f"At_Exit pass over {[s[1] for s in specs]} ran {first} "
                          f"(err={err!r}), want {want}",
                          ["register one agent per spec with At_Exit",
                           "call _run_exit_protocols()",
                           f"observed: {first}"])
        self._check_exit_rerun(pairs)
        self._check_exit_weak()
    def dt4(self):
        T = self.T
        # explicit Rip of one tag, then deletion: ripped tag silent, other runs
        self.cases += 1
        holder = [T["HBase"]()]
        T["K_OK"](holder[0])
        T["K_OK2"](holder[0])
        del T["K_OK"][holder[0]]
        LOG.clear()
        _drop(holder)
        if [e for e in LOG if e == ("tear", "K_OK")]:
            self.fail("DT-4", f"explicitly Ripped K_OK ran again at deletion: {LOG}",
                      ["apply K_OK then K_OK2", "del K_OK[agent]  (runs Tear_ok)",
                       "del agent; gc.collect()", f"observed: {LOG}"])
        if ("tear", "K_OK2") not in LOG:
            self.fail("DT-4", f"still-due K_OK2 did not run at deletion: {LOG}",
                      ["apply K_OK then K_OK2", "del K_OK[agent]", "del agent",
                       f"observed: {LOG}"])
        # _teardown_all twice: second run must be empty (ledger popped)
        self.cases += 1
        LOG.clear()
        holder = [T["HBase"]()]
        T["K_OK"](holder[0])
        with redirect_stderr(io.StringIO()):
            self.L._teardown_all(holder[0])
        first = list(LOG)
        LOG.clear()
        with redirect_stderr(io.StringIO()):
            self.L._teardown_all(holder[0])
        if LOG:
            self.fail("DT-4", f"_teardown_all re-ran {list(LOG)} on second call",
                      ["apply K_OK", "call _teardown_all twice", f"second observed: {LOG}"])
        _drop(holder)
        # failed explicit Rip arrests: agent held, finalizer never re-runs
        self.cases += 1
        LOG.clear()
        holder = [T["HBase"]()]
        T["K_EXC"](holder[0])
        import weakref
        from TopKit.errors import TagCompositionError
        try:
            del T["K_EXC"][holder[0]]
            self.fail("DT-4", "failing explicit Rip did not raise",
                      ["apply K_EXC", "del K_EXC[agent]  (want TagCompositionError)"])
        except TagCompositionError:
            pass
        ref = weakref.ref(holder[0])
        LOG.clear()
        _drop(holder)
        if ref() is None:
            self.fail("DT-4", "arrested agent was collected while custody remains",
                      ["fail an explicit Rip (arrest)", "drop all refs + gc",
                       "agent is gone; Safehouse must hold it"])
        if [e for e in LOG if e[0] == "tear"]:
            self.fail("DT-4", f"finalizer re-ran arrested work: {LOG}",
                      ["fail an explicit Rip (arrest)", "drop all refs + gc",
                       f"observed: {LOG}"])
        self.A._safehouse.clear()
        gc.collect()

    # ---- DT-5: at interpreter exit only Layers run (real subprocess) ----
    def dt5(self):
        body = textwrap.dedent("""
            import os, warnings; warnings.filterwarnings("ignore")
            import sys
            sys.path.insert(0, os.environ["DT_ROOT"])
            from TopKit import Tag, Rip, At_Exit
            FD = os.open(os.environ["DT_OUT"], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
            class T(Tag):
                @Rip
                def By(a):
                    os.write(FD, b"teardown\\n")
            class H:
                def __del__(self):
                    os.write(FD, b"host\\n")
            a = H(); T(a)
            {extra}
            """)
        for with_exit, want in (("", [b"host"]),
                                ("At_Exit(a)", [b"teardown", b"host"])):
            self.cases += 1
            out = f"/tmp/dt5_{'atex' if with_exit else 'plain'}_{os.getpid()}.txt"
            code = body.format(extra=with_exit)
            env = dict(os.environ, DT_ROOT=self.root, DT_OUT=out)
            try:
                os.remove(out)
            except FileNotFoundError:
                pass
            proc = subprocess.run([sys.executable, "-c", code], capture_output=True,
                                  text=True, env=env, timeout=120)
            if proc.returncode != 0:
                self.fail("DT-5", f"exit-probe subprocess failed rc={proc.returncode}: "
                                  f"{proc.stderr[-500:]}", ["run python3 -c probe", out])
                continue
            try:
                with open(out, "rb") as f:
                    got = f.read().split()
            except FileNotFoundError:
                got = ["<missing>"]
            if got != want:
                self.fail("DT-5",
                          f"interpreter exit {'with' if with_exit else 'without'} At_Exit "
                          f"wrote {got}, want {want}",
                          ["probe script with os.write logging", f"observed: {got}"])
            try:
                os.remove(out)
            except FileNotFoundError:
                pass

    # ---- DT-6: interruption isolation (KNOWN violation on current code) ----
    def dt6(self):
        T = self.T
        # deletion: interrupter at every seat, 2-3 tags
        seqs = [["K_OK", "K_KI"], ["K_KI", "K_OK"], ["K_OK", "K_SE"], ["K_SE", "K_OK"]]
        if not self.quick:
            seqs += [["K_OK", "K_OK2", "K_KI"], ["K_OK", "K_KI", "K_OK2"],
                     ["K_KI", "K_OK", "K_OK2"], ["K_OK", "K_OK2", "K_SE"],
                     ["K_SE", "K_OK", "K_OK2"]]
        for names in seqs:
            self.cases += 1
            log = _run_deletion(T, [T[n] for n in names])
            tears = [e for e in log if e[0] == "tear"]
            want = [("tear", n) for n in reversed(names)]
            if tears != want:
                self.fail("DT-6",
                          f"interrupted deletion of [{','.join(names)}] ran tears "
                          f"{[n for _, n in tears]}, want {[n for _, n in want]}",
                          [f"apply {' then '.join(names)}",
                           "del agent; gc.collect()",
                           f"observed tears: {[n for _, n in tears]}"])
        # exit pass: interrupted agent must not skip the others
        pairs = [[("HPlain", ["K_KI"]), ("HPlain", ["K_OK"])]]
        if not self.quick:
            pairs += [[("HPlain", ["K_SE"]), ("HPlain", ["K_OK"])],
                      [("HPlain", ["K_OK"]), ("HPlain", ["K_KI"])],
                      [("HPlain", ["K_OK"]), ("HPlain", ["K_SE"])]]
        for specs in pairs:
            self.cases += 1
            first, _, err = self._exit_pass(specs)
            want = []
            for _, tag_names in specs:
                want += [("tear", n) for n in reversed(tag_names)]
            if sorted(first) != sorted(want):
                self.fail("DT-6",
                          f"interrupted At_Exit pass over {[s[1] for s in specs]} ran "
                          f"{first}, want {want} (err={type(err).__name__ if err else None})",
                          ["At_Exit both agents, one teardown raises",
                           "call _run_exit_protocols()",
                           f"observed: {first}"])

    def run_all(self):
        start = time.perf_counter()
        self.dt1()
        self.dt2()
        self.dt3()
        self.dt4()
        self.dt5()
        self.dt6()
        return time.perf_counter() - start
def _replay(vector, ex):
    """Replay one TLC-mapped vector on the real code. Vector forms:
    DT-6:[K_OK,K_KI]  (deletion with named teardowns, KI interrupter)
    DT-6X:[K_KI,K_OK] (At_Exit pass: bad agent first, good second)
    DT-1:[K_OK,K_EXC] (deletion with Exception interrupter)
    """
    import re
    m = re.match(r"(DT-\w+):\[(.*)\]$", vector.strip())
    if not m:
        print(f"harness error: bad --replay vector {vector!r}")
        return 2
    pid, names = m.group(1), [n.strip() for n in m.group(2).split(",") if n.strip()]
    T = ex.T
    try:
        tags = [T[n] for n in names]
    except KeyError as e:
        print(f"harness error: unknown tag {e}")
        return 2
    if pid in ("DT-1", "DT-2", "DT-6"):
        log = _run_deletion(T, tags)
        print(f"replay {pid} deletion {[n for n in names]} -> {log}")
        return 0
    if pid == "DT-6X":
        first, _, err = ex._exit_pass([("HPlain", [names[0]]), ("HPlain", [names[1]])])
        print(f"replay DT-6X exit pass {names} -> {first} err={err!r}")
        return 0
    print(f"harness error: no replay for {pid}")
    return 2



def _default_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(3):
        d = os.path.dirname(d)
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--replay", default=None,
                    help="replay one violation vector, e.g. DT-6:[K_OK,K_KI]")
    opts = ap.parse_args(argv)
    root = opts.root or _default_root()
    ex = Explorer(root, quick=opts.quick)
    if opts.replay:
        return _replay(opts.replay, ex)
    ex.run_all()
    for pid, msg, steps in ex.violations:
        print(f"VIOLATION {pid}: {msg}")
        for i, s in enumerate(steps, 1):
            print(f"  step {i}: {s}")
    print(f"cases={ex.cases}")
    return 1 if ex.violations else 0


if __name__ == "__main__":
    sys.exit(main())
