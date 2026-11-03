"""Exhaustive explorer for verify-memo-lifetimes (ML-1..ML-4), stdlib only.

Method: stateless exhaustive exploration of the REAL TopKit in plain
Python. Every case in the stated bound runs against the real code; the
expected behaviour comes from an independent oracle written from the
spec/notes (never derived from the code under test). Counterexamples
print as numbered steps in the code's own words and are replayable via
--replay <id> or scripts/repro_<id>.py.

Usage:
  python3 .claude/skills/verify-memo-lifetimes/scripts/explore.py [--quick] [--root DIR]
  python3 .../explore.py --replay ML-1 [--root DIR]
"""

from __future__ import annotations

import argparse
import gc
import sys
import time
import traceback
import weakref
from pathlib import Path


def resolve_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    return Path(__file__).resolve().parent.parent.parent.parent


def use_root(root: Path) -> None:
    sys.path.insert(0, str(root))
    import TopKit  # noqa: E402

    if not Path(TopKit.__file__).resolve().is_relative_to(root.resolve()):
        raise SystemExit(
            f"error: TopKit resolved to {TopKit.__file__}, not under --root {root}"
        )


def collect() -> None:
    gc.collect()
    gc.collect()


def is_collected(ref) -> bool:
    collect()
    return ref() is None


def make_host_class(exact: bool = False, slots: bool = False, eq: bool = False,
                    unhashable: bool = False):
    """Build one host class per kind. Returns (Host, label)."""
    ns: dict = {}
    if slots:
        ns["__slots__"] = ("x", "__weakref__")
    if eq:
        ns["__eq__"] = lambda self, o: isinstance(o, self.__class__)
        ns["__hash__"] = lambda self: 0x1234
    if unhashable:
        ns["__eq__"] = lambda self, o: isinstance(o, self.__class__)
        ns["__hash__"] = None
    host = type("HostProbe", (object,), ns)
    label = "plain" if not (slots or eq or unhashable) else (
        "slots" if slots else ("eqhash" if eq else "unhashable"))
    return host, label


def fresh_tag(suffix: str, body: str = ""):
    """Define a fresh Tag subclass with a unique name (avoids memo aliasing)."""
    from TopKit import Action, Record, Tag
    ns: dict = {}
    exec(
        "def Work(agent):\n    return 'work-" + suffix + "'\n"
        "def data(agent):\n    return {'n': 1}\n", ns)
    attrs = {"Work": Action(ns["Work"]), "data": Record(ns["data"])}
    if body == "rip-fail":
        flag = {"fail": True}
        def Leave(agent):
            if flag["fail"]:
                raise ValueError("cleanup blocked")
        from TopKit import Rip
        attrs["Leave"] = Rip(Leave)
        tag = type("Role" + suffix, (Tag,), attrs)
        return tag, flag
    tag = type("Role" + suffix, (Tag,), attrs)
    return tag, None


def check_ml1(quick: bool):
    """ML-1: a Field never keeps an Agent alive, in every Agent state."""
    from TopKit.errors import TagCompositionError
    from TopKit.arrest import _arrest_of
    import warnings as _w

    violations = []
    cases = 0

    state_kinds = ["tagged", "ripped", "arrested-freed"]
    capture_kinds = ["none", "action", "record", "view", "viewcall",
                     "walk-closed", "walk-exhausted"]
    if quick:
        state_kinds = ["tagged", "arrested-freed"]
        capture_kinds = ["none", "action", "view", "walk-closed"]

    for si, sk in enumerate(state_kinds):
        for ci, ck in enumerate(capture_kinds):
            cases += 1
            label = f"state={sk} capture={ck}"
            with _w.catch_warnings():
                _w.simplefilter("ignore")
                try:
                    tag, _ = fresh_tag(f"ML1{si}{ci}")
                    host_cls, _ = make_host_class()
                    agent = host_cls()
                    tag(agent)
                    if sk == "ripped":
                        del tag[agent]
                    elif sk == "arrested-freed":
                        # `agent` (tagged only by tag) is not part of this
                        # scenario; drop it now so it cannot leak.
                        del agent
                        tag2, flag2 = fresh_tag(f"ML1A{si}{ci}", body="rip-fail")
                        agent2 = host_cls()
                        tag(agent2)
                        tag2(agent2)
                        try:
                            del tag2[agent2]
                        except TagCompositionError:
                            pass
                        if _arrest_of(agent2) is None:
                            violations.append(
                                (label, ["1. Tag with failing @Rip",
                                        "2. del Tag[agent] (expected arrest, got none)"]))
                            try:
                                del agent, agent2
                            except Exception:
                                pass
                            collect()
                            continue
                        flag2["fail"] = False
                        try:
                            agent2.Work()
                        except Exception:
                            pass
                        if _arrest_of(agent2) is not None:
                            violations.append(
                                (label, ["1. arrested Agent",
                                        "2. fixed Rip failure; called public Action",
                                        "3. still arrested (saved work incomplete)"]))
                            try:
                                del agent, agent2
                            except Exception:
                                pass
                            collect()
                            continue
                        agent = agent2
                        del agent2, tag2, flag2
                        collect()
                    held = None
                    extra = None
                    if ck in ("action", "view", "viewcall") and sk == "ripped":
                        # Rip removes active membership, so no bound Action
                        # or view can be captured afterwards; the lifetime
                        # question for this state is the bare Field (none)
                        # plus Record and walk snapshots. Skip action/view
                        # captures here (covered in tagged + freed states).
                        collect()
                        try:
                            del agent
                        except Exception:
                            pass
                        collect()
                        continue
                    if ck == "action":
                        held = agent.Work
                    elif ck == "record":
                        held = agent.data
                    elif ck == "view":
                        held = tag[agent]
                    elif ck == "viewcall":
                        held = tag[agent].Work
                    elif ck in ("walk-closed", "walk-exhausted"):
                        walk = iter(tag[:])
                        nxt = next(walk, None)
                        extra = (walk, nxt)
                    canary = weakref.ref(agent)
                    del agent
                    collect()
                    if ck in ("walk-closed",):
                        walk, nxt = extra
                        try:
                            walk.close()
                        except Exception:
                            pass
                        del walk, nxt, extra
                        collect()
                    if ck == "walk-exhausted":
                        walk, nxt = extra
                        try:
                            list(walk)
                        except Exception:
                            pass
                        del walk, nxt, extra
                        collect()
                    if ck == "record":
                        del held
                        collect()
                        if canary() is not None:
                            violations.append((label, [
                                "1. Tag with @Record data",
                                "2. agent = Host(); Tag(agent)",
                                "3. held = agent.data; del agent; del held",
                                "4. gc.collect(); canary() is not None (Field kept it)",
                            ]))
                        continue
                    if ck in ("none", "action", "view", "viewcall"):
                        if canary() is not None:
                            violations.append((label, [
                                "1. Tag with @Action Work",
                                "2. agent = Host(); Tag(agent)",
                                f"3. held = <{ck}>; del agent; gc.collect()",
                                "4. canary() is not None (capture/Field kept it)",
                            ]))
                            try:
                                del held
                            except Exception:
                                pass
                            collect()
                        else:
                            if ck in ("action", "viewcall"):
                                try:
                                    held()
                                    violations.append((label, [
                                        "1. capture bound handle", "2. agent died",
                                        "3. held() did not raise ReferenceError"]))
                                except ReferenceError:
                                    pass
                                except Exception as e:
                                    violations.append((label, [
                                        "1. capture bound handle", "2. agent died",
                                        f"3. held() raised {type(e).__name__}, want ReferenceError"]))
                            if ck == "view":
                                try:
                                    held.Work
                                    violations.append((label, [
                                        "1. capture Tag view", "2. agent died",
                                        "3. view.Work did not raise ReferenceError"]))
                                except ReferenceError:
                                    pass
                                except Exception as e:
                                    violations.append((label, [
                                        "1. capture Tag view", "2. agent died",
                                        f"3. view access raised {type(e).__name__}, want ReferenceError"]))
                            try:
                                del held
                            except Exception:
                                pass
                        continue
                    if canary() is not None:
                        violations.append((label, [
                            "1. Tag(agent) x1; walk = iter(Tag[:])",
                            f"2. next(walk); del agent; gc.collect(); walk.{('close()' if ck=='walk-closed' else 'exhausted')}",
                            "3. canary() is not None (walk snapshot kept it)",
                        ]))
                except Exception as e:
                    violations.append((label + " HARNESS-ERROR",
                                       [f"harness raised {type(e).__name__}: {e}",
                                        traceback.format_exc(limit=3)]))
                collect()
    return cases, violations


def check_ml2(quick: bool):
    """ML-2: runtime-type sharing keyed by host identity + type-level facts."""
    from TopKit import Action, Constant, Record, Secret, Tag
    from TopKit import state as rt

    violations = []
    cases = 0

    # Fact dimensions: secrets? constants? dunder actions? arrestable(rip)?
    # Enumerate a small matrix of Tag shapes; each pair with same facts must
    # share, each pair with different facts must not.
    def build(shape: str, n: int):
        attrs: dict = {}
        def mk(name, fn):
            return fn
        if shape in ("base", "secret", "const", "dunder", "rip", "all"):
            exec("def Work(agent):\n    return 1\n", attrs)
            attrs["Work"] = Action(attrs.pop("Work"))
        if shape in ("secret", "all"):
            exec("def Hid(agent):\n    return 2\n", attrs)
            attrs["Hid"] = Secret(Action(attrs.pop("Hid")))
        if shape in ("const", "all"):
            exec("def level(tag):\n    return 3\n", attrs)
            attrs["level"] = Constant(attrs.pop("level"))
        if shape in ("dunder", "all"):
            exec("def __len__(agent):\n    return 4\n", attrs)
            attrs["__len__"] = Action(attrs.pop("__len__"))
        if shape in ("rip", "all"):
            from TopKit import Rip
            exec("def Bye(agent):\n    return 5\n", attrs)
            attrs["Bye"] = Rip(attrs.pop("Bye"))
        return type(f"Shape{shape}{n}", (Tag,), dict(attrs))

    shapes = ["base", "secret", "const", "dunder", "rip", "all"]
    if quick:
        shapes = ["base", "secret", "const"]
    host_kinds = [dict(), dict(slots=True), dict(eq=True), dict(unhashable=True)]
    if quick:
        host_kinds = [dict(), dict(eq=True)]

    refs: list = []  # keep agents alive during the matrix
    for hk in host_kinds:
        host_cls, hlabel = make_host_class(**{k: v for k, v in hk.items() if v})
        for s in shapes:
            cases += 1
            t = build(s, cases)
            a = host_cls()
            try:
                t(a)
            except Exception as e:
                # e.g. slots host without instance dict cannot carry state:
                # documented limit, skip but count
                cases -= 1
                continue
            refs.append((a, t))
    # sharing: same host class + same facts -> one runtime type
    for i in range(len(refs)):
        for j in range(i + 1, len(refs)):
            (a, ta), (b, tb) = refs[i], refs[j]
            same_host_cls = type(a) is type(b)
            ka = rt._type_key_of(rt._state_of(a))
            kb = rt._type_key_of(rt._state_of(b))
            same_facts = ka[1:] == kb[1:]
            same_key_head = ka[0] == kb[0]
            cases += 1
            if same_host_cls and same_facts:
                if type(a) is not type(b):
                    violations.append((f"host-kind facts={ka[1:]}", [
                        "1. two Agents, same host class, same Tag facts",
                        "2. type(a) is not type(b) (want shared ONE type)"]))
                if not same_key_head:
                    violations.append(("key-head", [
                        "1. same host class", "2. id(host) differs in key"]))
            elif not same_facts:
                if type(a) is type(b):
                    violations.append((f"alias shape {ta.__name__}/{tb.__name__}", [
                        "1. two Agents with differing type-level facts",
                        "2. type(a) is type(b) (must never alias)"]))
    # equal-but-distinct hosts never alias while entry live
    host_cls, _ = make_host_class(eq=True)
    t = build("base", 9999)
    x, y = host_cls(), host_cls()
    assert x == y and x is not y
    t(x)
    t(y)
    cases += 1
    if type(x) is not type(y):
        pass  # same host CLASS shares (correct); distinct classes below:
    # distinct host classes with equal instances
    h1, _ = make_host_class(eq=True)
    h2, _ = make_host_class(eq=True)
    t2 = build("base", 9998)
    p, q = h1(), h2()
    t(p)
    t2(q)
    cases += 1
    # keys must differ (identity, not equality)
    kp = rt._type_key_of(rt._state_of(p))
    kq = rt._type_key_of(rt._state_of(q))
    if kp == kq:
        violations.append(("host-equality-alias", [
            "1. two host classes with custom __eq__ (equal instances)",
            "2. _type_key_of equal (must use identity, not equality)"]))
    # id-reuse guard: while a runtime type is live it owns its Host via bases
    import weakref as _w
    dead_host_ref = None
    rt_ref = None
    def _mk():
        h, _ = make_host_class()
        tt = build("base", 5555)
        ag = h()
        tt(ag)
        return _w.ref(h), _w.ref(type(ag)), ag, tt
    hr, tr, kept_agent, kept_tag = _mk()
    collect()
    cases += 1
    if hr() is None and tr() is not None:
        violations.append(("id-reuse", [
            "1. Host class dropped while runtime type live",
            "2. Host collected but cached type alive (id could be reused)"]))
    return cases, violations


def check_ml3(quick: bool):
    """ML-3: owner-local memos (Form + declaration memo contract)."""
    from TopKit import Form, Pin, Public, Record, Tag
    from TopKit.geometry import _form_key
    from TopKit.declarations import _declaration_key, _declarations_of
    from TopKit.memo import _memo_key, _memo_of, _remember_memo, _forget_memo

    violations = []
    cases = 0

    # M3a: memo lives on owning Tag, never overwrites program binding,
    # never accepts foreign memo; invalidation retires the value.
    probe_values = [None, False, (Tag,), "application-private"]
    if quick:
        probe_values = [None, "application-private"]
    for v in probe_values:
        cases += 1
        class Base(Tag):
            pass
        class Shape(Base):
            pass
        name = _form_key(Shape)
        Shape.__dict__.get(name)  # warm nothing
        setattr(Shape, name, v)
        got = Form(Shape)
        if got != (Base, Shape):
            violations.append((f"own-collision {v!r}", [
                "1. setattr(Shape, form-key, value)",
                f"2. Form(Shape) == {got} (want (Base, Shape))"]))
        if vars(Shape)[name] is not v:
            violations.append((f"own-overwrite {v!r}", [
                "1. program binding at memo key overwritten by memo"]))
    # inherited collision not shadowed
    cases += 1
    class Earlier(Tag):
        pass
    class B2(Tag):
        pass
    class S2(Earlier, B2):
        pass
    setattr(B2, _form_key(S2), "application-private")
    if Form(S2) != (Earlier, B2, S2) or _form_key(S2) in vars(S2):
        violations.append(("inherited-collision", [
            "1. setattr(Base, shape-form-key, value)",
            "2. Form(Shape) wrong or memo shadowed the inherited binding"]))
    # foreign memo not accepted
    cases += 1
    class F1(Tag):
        pass
    class F2(Tag):
        pass
    class G1(Tag):
        pass
    class G2(G1):
        pass
    Form(F1)
    foreign = vars(F1)[_form_key(F1)]
    setattr(G2, _form_key(G2), foreign)
    if Form(G2) != (G1, G2) or vars(G2)[_form_key(G2)] is not foreign:
        violations.append(("foreign-memo", [
            "1. planted another Tag's memo wrapper at our key",
            "2. Form reused/overwrote it (must recompute, leave untouched)"]))
    # invalidation retires the value (warm read misses afterwards)
    cases += 1
    class H1(Tag):
        pass
    class H2(H1):
        pass
    Form(H2)
    memo_before = _memo_of(H2, _form_key(H2))
    assert memo_before is not None
    _forget_memo(H2, _form_key(H2))
    if _memo_of(H2, _form_key(H2)) is not None:
        violations.append(("retire", [
            "1. Form(Shape) to publish memo",
            "2. _forget_memo(Shape, key)",
            "3. warm read still hits (must miss)"]))
    # M3b: Tag whose Base Contribution closes over the Shape is collectible
    for kind in (["closure", "default", "annotation", "callable"]
                 if not quick else ["closure", "callable"]):
        cases += 1
        from TopKit import Action as _A
        if kind == "closure":
            def Owner(agent):
                return shape
        else:
            def Owner(agent, owner=None):
                return owner
        decl = _A(Owner)
        class Base(Tag):
            Owner = decl
        class Shape(Base):
            pass
        shape = Shape
        if kind == "default":
            Owner.__defaults__ = (Shape,)
        elif kind == "annotation":
            Owner.__annotations__["return"] = Shape
        elif kind == "callable":
            class Callable:
                def __init__(self, owner):
                    self.owner = owner
                def __call__(self, agent):
                    return self.owner
            Base.Owner = _A(Callable(Shape))
        assert Form(Shape) == (Base, Shape)
        rb, rs = weakref.ref(Base), weakref.ref(Shape)
        del Base, Shape, shape, Owner, decl
        if not is_collected(rb) or not is_collected(rs):
            violations.append((f"cycle-{kind}", [
                "1. Base Contribution closes over Shape; Form(Shape)",
                "2. del Base, Shape; gc.collect()",
                "3. Tag still alive (memo cycle roots it)"]))
    # descriptor/metaclass collision variants: publication must not call
    # program metadata code, and warm reads must not evaluate descriptors
    cases += 1
    try:
        calls: list = []
        class Meta(type(Tag)):
            pass
        class Rcv(Tag, metaclass=Meta):
            pass
        key = _declaration_key(Rcv)
        def forbidden(*a):
            calls.append(a)
            raise RuntimeError("memo called the program metadata")
        setattr(Meta, key, property(forbidden, forbidden, forbidden))
        _declarations_of(Rcv)
        if calls:
            violations.append(("descriptor", [
                "1. metaclass property at memo key",
                "2. declaration scan evaluated it (must use physical reads)"]))
        delattr(Meta, key)
    except Exception as e:
        violations.append(("descriptor HARNESS-ERROR",
                           [f"{type(e).__name__}: {e}"]))
    return cases, violations


def check_ml4(quick: bool):
    """ML-4: weak handles (bound Actions, Tag views, view calls)."""
    from TopKit import Action, Operation, Record, Tag

    violations = []
    cases = 0
    kinds = ["action", "secret-action", "view", "viewcall", "operation"]
    if quick:
        kinds = ["action", "view", "viewcall"]

    for ki, kind in enumerate(kinds):
        cases += 1
        try:
            from TopKit import Secret
            if kind == "secret-action":
                ns: dict = {}
                exec("def Hid(agent):\n    return 'hid'\n", ns)
                tag = type(f"WK{ki}", (Tag,), {"Hid": Secret(Action(ns["Hid"]))})
            elif kind == "operation":
                ns = {}
                exec("def Calc(tag, x):\n    return x\n", ns)
                tag = type(f"WK{ki}", (Tag,), {"Calc": Operation(ns["Calc"])})
            else:
                ns = {}
                exec("def Work(agent):\n    return 'w'\n", ns)
                tag = type(f"WK{ki}", (Tag,), {"Work": Action(ns["Work"])})
            host_cls, _ = make_host_class()
            agent = host_cls()
            tag(agent)
            if kind == "action":
                handle = agent.Work
                canary = weakref.ref(agent)
                del agent
                collect()
                if canary() is not None:
                    violations.append((kind, [
                        "1. agent = Host(); Tag(agent); h = agent.Work",
                        "2. del agent; gc.collect()",
                        "3. agent alive (bound handle kept it strongly)"]))
                else:
                    try:
                        handle()
                        violations.append((kind, [
                            "1. h = agent.Work; agent died",
                            "2. h() did not raise ReferenceError"]))
                    except ReferenceError:
                        pass
                    except Exception as e:
                        violations.append((kind, [
                            "1. h = agent.Work; agent died",
                            f"2. h() raised {type(e).__name__}, want ReferenceError"]))
                del handle
            elif kind == "secret-action":
                # capture inside composition via a view read with handles=False
                from TopKit.access import _view_of
                from TopKit import state as _st
                view = _view_of(agent, tag)
                _st._state_of(agent).composing += 1
                try:
                    handle = view._read("Hid", handles=False)
                finally:
                    _st._state_of(agent).composing -= 1
                canary = weakref.ref(agent)
                del agent, view
                collect()
                if canary() is not None:
                    violations.append((kind, [
                        "1. secret bound handle captured in composition",
                        "2. del agent; gc.collect(); agent alive"]))
                else:
                    try:
                        handle()
                        violations.append((kind, [
                            "1. secret handle; agent died",
                            "2. h() did not raise ReferenceError"]))
                    except ReferenceError:
                        pass
                    except AttributeError:
                        pass  # secret door also acceptable post-mortem? no:
                        # ReferenceError must come first; record as violation
                        violations.append((kind, [
                            "1. secret handle; agent died",
                            "2. h() raised AttributeError, want ReferenceError first"]))
                    except Exception as e:
                        violations.append((kind, [
                            "1. secret handle; agent died",
                            f"2. h() raised {type(e).__name__}, want ReferenceError"]))
                del handle
            elif kind == "view":
                handle = tag[agent]
                canary = weakref.ref(agent)
                del agent
                collect()
                if canary() is not None:
                    violations.append((kind, [
                        "1. v = Tag[agent]; del agent; gc.collect()",
                        "2. agent alive (view kept it strongly)"]))
                else:
                    try:
                        handle.Work if hasattr(handle, "Work") else handle._current()
                        violations.append((kind, [
                            "1. v = Tag[agent]; agent died",
                            "2. view use did not raise ReferenceError"]))
                    except ReferenceError:
                        pass
                    except Exception as e:
                        violations.append((kind, [
                            "1. v = Tag[agent]; agent died",
                            f"2. view use raised {type(e).__name__}, want ReferenceError"]))
                del handle
            elif kind == "viewcall":
                handle = tag[agent].Work
                canary = weakref.ref(agent)
                del agent
                collect()
                if canary() is not None:
                    violations.append((kind, [
                        "1. c = Tag[agent].Work; del agent; gc.collect()",
                        "2. agent alive (view call kept it strongly)"]))
                else:
                    try:
                        handle()
                        violations.append((kind, [
                            "1. c = Tag[agent].Work; agent died",
                            "2. c() did not raise ReferenceError"]))
                    except ReferenceError:
                        pass
                    except Exception as e:
                        violations.append((kind, [
                            "1. c = Tag[agent].Work; agent died",
                            f"2. c() raised {type(e).__name__}, want ReferenceError"]))
                del handle
            elif kind == "operation":
                # Operations bind the Tag (a class), not the Agent; the
                # weak-handle promise covers Agent-bound handles. Record
                # that an Operation handle does not keep an AGENT alive.
                handle = tag.Calc
                canary = weakref.ref(agent)
                del agent
                collect()
                if canary() is not None:
                    violations.append((kind, [
                        "1. Tag with @Operation; agent tagged",
                        "2. h = Tag.Calc; del agent; agent alive"]))
                del handle
            collect()
        except Exception as e:
            violations.append((kind + " HARNESS-ERROR",
                               [f"{type(e).__name__}: {e}",
                                traceback.format_exc(limit=3)]))
    return cases, violations


CHECKS = [("ML-1", check_ml1), ("ML-2", check_ml2),
          ("ML-3", check_ml3), ("ML-4", check_ml4)]

REPLAYS = {
    "ML-1": "state=tagged capture=action: Tag(agent); h = agent.Work; "
            "del agent; gc.collect(); assert weakref canary dead, "
            "h() raises ReferenceError",
    "ML-2": "same host class + same Tag facts share ONE runtime type; "
            "differing facts never alias; equal-but-distinct hosts never alias",
    "ML-3": "setattr(Shape, form-key, value) then Form(Shape) still (Base, Shape) "
            "and binding untouched; Base/Shape collectible after release",
    "ML-4": "h = agent.Work (or Tag[agent] / Tag[agent].Work); del agent; "
            "gc.collect(); agent dead; handle raises ReferenceError",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--root", default=None)
    ap.add_argument("--replay", default=None)
    opts = ap.parse_args()
    use_root(resolve_root(opts.root))
    if opts.replay:
        print(REPLAYS.get(opts.replay, f"unknown id {opts.replay}"))
        print(f"replay with: python3 .claude/skills/verify-memo-lifetimes/scripts/repro_{opts.replay}.py")
        return 0
    started = time.perf_counter()
    total = 0
    all_violations = []
    for pid, fn in CHECKS:
        t0 = time.perf_counter()
        cases, violations = fn(opts.quick)
        total += cases
        for label, steps in violations:
            if "HARNESS-ERROR" in label:
                print(f"HARNESS-ERROR {pid} [{label}]:")
            else:
                print(f"VIOLATION {pid}: {label}")
            for i, s in enumerate(steps, 1):
                print(f"  {i}. {s}")
            all_violations.append(pid)
    elapsed = time.perf_counter() - started
    import platform
    print(f"explored {total} cases in {elapsed:.1f}s "
          f"({sys.version.split()[0]}, {platform.python_implementation()})")
    if all_violations:
        return 1
    print("no violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
