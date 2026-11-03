"""Exhaustive Tagging-admission explorer: TA-1 failure-boundary oracle + TA-2 FieldAdding atomicity.

TA-1: for every injected failure point in user protocols during a Tagging
of Base+Shape (+ independent Tag + Tag with Pre/Post), the resulting state
must equal the spec's outcome table (spec/SPECIFICATION.md:219-246):
Gate refusal -> nothing of that Tag; Gainings/Imprints failure (Exception
or KeyboardInterrupt) -> acquired non-Post Gains stay, provisional Posts
discarded, no membership/history of that Tag, earlier completed turns stay;
Post failure -> membership stays (defective); host refusal at preparation
-> class/dict/slots restored, no membership/Field entry. Retry starts fresh
(spec:239-241). The oracle below is written from that table, not from the code.

TA-2: KeyboardInterrupt injected at EVERY executed line event inside
transactions._enter_field (sys.settrace, deterministic) plus on the return
event of fields._Field._Add, for first Tagging and for reTagging; afterwards
(agent in Tag[:]) == (Tag in state.active) == isinstance-history, every
Field member can be Ripped with `del Tag[agent]`, and `del Tag[:]` does not
fail for other members.

Findings (stable ids): TA-1* = oracle mismatch at a user-protocol failure
point; TA-2* = FieldAdding split (phantom member).
"""

from __future__ import annotations

import inspect
import sys

import TopKit.fields as _fields
import TopKit.state as _S
import TopKit.transactions as _T
from TopKit import Tags


def _snapshot(agent, turns):
    st = _S._state_of(agent)
    snap = dict(
        state_none=st is None,
        cls=type(agent).__name__,
        active=tuple(t.__name__ for t in st.active) if st else (),
        ever=tuple(sorted(t.__name__ for t in st.ever)) if st else (),
        records=tuple(sorted(st.records)) if st else (),
        actions=tuple(sorted(st.actions)) if st else (),
        posts=tuple(sorted(st.postconditions)) if st else (),
        layers={k: len(v) for k, v in st.post_layers.items()} if st else {},
        field={t.__name__: agent in t[:] for t in turns},
        sound={t.__name__: agent in t for t in turns},
        isinst={t.__name__: isinstance(agent, t) for t in turns},
        tags=tuple(t.__name__ for t in Tags(agent)),
    )
    return snap


def check_ta1(make_case):
    """Run the TA-1 oracle over every failure-point case.

    make_case(mode) -> (HostClass, Base, Shape, Indep, WithPP): fresh classes
    per mode so Field state never leaks between cases. Returns a list of
    (case, observed, expected_desc) mismatches.
    """
    from TopKit import Tag, Action, Record, Post, Pre, Imprint

    failures = []

    def note(case, observed, expected):
        failures.append((case, observed, expected))

    MODES = (
        "base_gate", "shape_gate", "shape_gain", "shape_imprint",
        "shape_interrupt", "post", "ok", "indep_then_fail",
        "withpp_gain", "withpp_imprint", "host_refuse",
    )

    def build(mode):
        class Host:
            def __init__(self):
                self.kept = "host"

        class Base(Tag):
            @Record
            def base_value(agent):
                return "base"

            @Action
            def Read(agent):
                return agent.base_value

        class Shape(Base):
            @Record
            def shape_value(agent):
                if mode == "shape_gain":
                    raise ValueError("gain boom")
                return "shape"

            @Record
            def after(agent):
                return "after"

            @Imprint
            def Train(agent):
                if mode == "shape_imprint":
                    raise ValueError("imprint boom")
                if mode == "shape_interrupt":
                    raise KeyboardInterrupt("int")

            @Post
            def Ok(agent):
                return mode != "post"

        if mode == "shape_gate":
            class Shape(Base):  # noqa: F811
                @Pre
                def Allowed(agent):
                    return False

                @Record
                def shape_value(agent):
                    return "shape"

                @Imprint
                def Train(agent):
                    pass

        if mode == "base_gate":
            class Base(Tag):  # noqa: F811
                @Pre
                def Allowed(agent):
                    return False

                @Record
                def base_value(agent):
                    return "base"

            class Shape(Base):  # noqa: F811
                @Record
                def shape_value(agent):
                    return "shape"

        class Indep(Tag):
            @Record
            def indep(agent):
                return "i"

        class WithPP(Tag):
            @Pre
            def Allowed(agent):
                return True

            @Record
            def wv(agent):
                if mode == "withpp_gain":
                    raise ValueError("gain boom")
                return "w"

            @Imprint
            def Train(agent):
                if mode == "withpp_imprint":
                    raise ValueError("imprint boom")

            @Post
            def Ok(agent):
                return True

        return Host, Base, Shape, Indep, WithPP

    for mode in MODES:
        Host, Base, Shape, Indep, WithPP = build(mode)
        turns = (Base, Shape)
        if mode == "host_refuse":
            class RefuseHost:
                def __init__(self):
                    self.kept = "x"

                def __setattr__(self, k, v):
                    if k == "__class__":
                        raise RuntimeError("no class change")
                    object.__setattr__(self, k, v)

            agent = RefuseHost()
            err = None
            try:
                Base(agent)
            except BaseException as e:
                err = type(e).__name__
            if not (err == "TagCompositionError"
                    and type(agent) is RefuseHost
                    and sorted(vars(agent)) == ["kept"]
                    and agent not in Base[:]):
                note("host_refuse",
                     f"err={err} cls={type(agent).__name__} field={agent in Base[:]}",
                     "TagCompositionError, host class/dict restored, no Field entry")
            continue
        if mode in ("withpp_gain", "withpp_imprint"):
            agent = Host()
            err = None
            try:
                WithPP(agent)
            except BaseException as e:
                err = type(e).__name__
            snap = _snapshot(agent, (WithPP,))
            # Gain failure raises TagCompositionError; Imprint failure raises
            # the TagImprintError subclass named after the Imprint.
            if not (err is not None
                    and snap["active"] == ()
                    and snap["ever"] == ()
                    and not snap["field"]["WithPP"]
                    and snap["posts"] == ()
                    and snap["layers"] == {}
                    and (snap["records"] == ("wv",) if mode == "withpp_imprint"
                         else snap["records"] == ())):
                note(mode, f"err={err} {snap!r}",
                     "no membership/history; acquired Records stay; provisional Posts discarded")
            continue
        if mode == "indep_then_fail":
            agent = Host()
            Indep(agent)
            # force the Shape gain to fail via a fresh failing Shape
            class FailShape(Base):
                @Record
                def shape_value(agent):
                    raise ValueError("boom")
            err = None
            try:
                FailShape(agent)
            except BaseException as e:
                err = type(e).__name__
            snap = _snapshot(agent, (Base, FailShape, Indep))
            if not (snap["active"] == ("Indep", "Base",)
                    and snap["field"]["Base"] and not snap["field"]["FailShape"]
                    and snap["isinst"]["Base"] and not snap["isinst"]["FailShape"]):
                note("indep_then_fail", repr(snap),
                     "Indep+Base admitted stay; FailShape: gains kept, no membership")
            continue

        agent = Host()
        err = None
        try:
            Shape(agent)
        except BaseException as e:
            err = type(e).__name__
        snap = _snapshot(agent, turns)

        if mode == "base_gate":
            if not (snap["state_none"] and not snap["field"]["Base"]
                    and not snap["field"]["Shape"]):
                note(mode, repr(snap), "Gate refusal: nothing of Base/Shape, no state")
        elif mode == "shape_gate":
            if not (snap["active"] == ("Base",) and snap["ever"] == ("Base",)
                    and snap["field"]["Base"] and not snap["field"]["Shape"]
                    and snap["isinst"]["Base"] and not snap["isinst"]["Shape"]
                    and "Allowed" in err):
                note(mode, f"err={err} {snap!r}",
                     "Base admitted stays; Shape unstarted")
        elif mode in ("shape_gain", "shape_imprint", "shape_interrupt"):
            if not (snap["active"] == ("Base",) and snap["ever"] == ("Base",)
                    and snap["field"]["Base"] and not snap["field"]["Shape"]
                    and snap["isinst"]["Base"] and not snap["isinst"]["Shape"]
                    and snap["posts"] == ()
                    and (err == "KeyboardInterrupt" if mode == "shape_interrupt"
                         else err is not None)):
                note(mode, f"err={err} {snap!r}",
                     "Base stays; Shape gains kept, provisional Posts discarded, no membership")
            # acquired non-Post Gains stay: shape_value present even on failure
            # (gain failure keeps gains acquired before the failing one)
            if mode == "shape_imprint" and "shape_value" not in snap["records"]:
                note(mode + "+gains", repr(snap), "acquired Shape Records stay")
        elif mode == "post":
            if not (snap["active"] == ("Base", "Shape")
                    and snap["ever"] == ("Base", "Shape")
                    and snap["field"]["Shape"] and snap["isinst"]["Shape"]
                    and snap["posts"] == ("Ok",)
                    and not snap["sound"]["Shape"]):
                note(mode, f"err={err} {snap!r}",
                     "Post failure: membership stays, defective")
        elif mode == "ok":
            if not (err is None and snap["active"] == ("Base", "Shape")
                    and snap["field"]["Shape"] and snap["sound"]["Shape"]):
                note(mode, f"err={err} {snap!r}", "clean Tagging admits both")

        # retry starts fresh (spec:239-241): Tag again, same expectation class
        if mode in ("shape_gain", "shape_imprint", "shape_interrupt"):
            err2 = None
            try:
                Shape(agent)
            except BaseException as e:
                err2 = type(e).__name__
            snap2 = _snapshot(agent, turns)
            if not (snap2["active"] == ("Base",)
                    and not snap2["field"]["Shape"]):
                note(mode + "+retry", f"err={err2} {snap2!r}",
                     "retry starts fresh, still Base-only")

    return failures


def _enter_field_lines():
    """Line events _enter_field actually executes (plain Record tag)."""
    from TopKit import Tag, Record

    class Host:
        pass

    class Probe(Tag):
        @Record
        def v(agent):
            return 1

    seen = []

    def trace(frame, event, arg):
        if frame.f_code is _T._enter_field.__code__ and event == "line":
            seen.append(frame.f_lineno)
        return trace

    agent = Host()
    old = sys.gettrace()
    sys.settrace(trace)
    try:
        Probe(agent)
    finally:
        sys.settrace(old)
    out = []
    for line in seen:
        if line not in out:
            out.append(line)
    return out


def check_ta2(quick=False):
    """TA-2: interrupt at every executed _enter_field line + _Add return.

    For first Tagging and for reTagging. Returns a list of dicts, one per
    violating injection point: point, field, active, ever, isinst, rip,
    whole_rip, detail.
    """
    from TopKit import Tag, Record

    violations = []

    def fresh_classes(suffix):
        class Host:
            pass

        Host.__name__ = f"Host{suffix}"

        class T(Tag):
            @Record
            def val(agent):
                return 1

        T.__name__ = f"T{suffix}"
        T.__qualname__ = f"T{suffix}"
        return Host, T

    lines = _enter_field_lines()
    if quick:
        # keep the boundary lines that can split the triple
        keep = set()
        src = inspect.getsource(_T._enter_field).splitlines()
        first = _T._enter_field.__code__.co_firstlineno
        for i, text in enumerate(src):
            s = text.strip()
            if s.startswith(("field._Add", "state.active.append",
                             "state.words =", "state.ever.add")):
                keep.add(first + i)
        lines = [ln for ln in lines if ln in keep]
        if not lines:
            lines = _enter_field_lines()

    points = [("add-return", None)] + [("line", ln) for ln in lines]

    counter = [0]

    def inject(point):
        kind, lineno = point
        if kind == "add-return":
            def trace(frame, event, arg):
                if event == "return" and frame.f_code is _fields._Field._Add.__code__:
                    raise KeyboardInterrupt("ta2-window")
                return trace
            return trace

        def trace(frame, event, arg):
            if (event == "line" and frame.f_code is _T._enter_field.__code__
                    and frame.f_lineno == lineno):
                raise KeyboardInterrupt("ta2-window")
            return trace
        return trace

    for kind in ("first", "retag"):
        for point in points:
            counter[0] += 1
            Host, T = fresh_classes(f"{kind}{counter[0]}")
            agent = Host()
            if kind == "retag":
                # admit, Rip (keeps history), then reTag under injection
                T(agent)
                del T[agent]
            old = sys.gettrace()
            sys.settrace(inject(point))
            try:
                T(agent)
                raised = None
            except BaseException as e:
                raised = type(e).__name__
            finally:
                sys.settrace(old)
            st = _S._state_of(agent)
            in_field = agent in T[:]
            active = (T in st.active) if st else False
            ever = (T in st.ever) if st else False
            isinst = isinstance(agent, T)
            sound = agent in T

            problems = []
            # The promise: Field entry, active membership and history are
            # established together. For a first Tagging the baseline is
            # (False, False, False); for a reTagging after Rip the baseline
            # is ever=True already, so only the *change* must be atomic:
            # in_field and active must move together, and a Field member
            # must carry history.
            if kind == "first":
                if in_field != active or active != ever or (in_field and not isinst):
                    problems.append(
                        f"split: field={in_field} active={active} "
                        f"ever={ever} isinst={isinst}")
            elif in_field != active or (in_field and not (ever and isinst)):
                problems.append(
                    f"split: field={in_field} active={active} "
                    f"ever={ever} isinst={isinst}")
            # every Field member must be rippable
            if in_field:
                try:
                    del T[agent]
                    rip = "ok"
                except BaseException as e:
                    rip = f"{type(e).__name__}: {e}"
                    problems.append(f"unrippable: {rip}")
                else:
                    if agent in T[:]:
                        problems.append("rip did not remove Field entry")
            else:
                rip = "n/a"
            # whole-Field Rip must not fail for other members
            good = Host()
            try:
                T(good)
            except BaseException:
                good = None
            whole = "n/a"
            if good is not None and in_field:
                try:
                    del T[:]
                    whole = "ok"
                    if good in T[:]:
                        problems.append("whole-Field Rip left the healthy member")
                except BaseException as e:
                    whole = f"{type(e).__name__}: {e}"
                    problems.append(f"whole-Field Rip poisoned: {whole}")
            if problems:
                violations.append(dict(
                    kind=kind, point=point, raised=raised,
                    field=in_field, active=active, ever=ever,
                    isinst=isinst, sound=sound, rip=rip,
                    whole_rip=whole, detail="; ".join(problems)))
            # best-effort cleanup so one phantom cannot poison later points
            try:
                if good is not None and good in T[:]:
                    # healthy member may sit in saved custody after a
                    # poisoned whole-Field Rip; retry once
                    try:
                        del T[good]
                    except BaseException:
                        pass
            except BaseException:
                pass
            import gc as _gc
            del agent
            try:
                del good
            except NameError:
                pass
            _gc.collect()

    return violations
