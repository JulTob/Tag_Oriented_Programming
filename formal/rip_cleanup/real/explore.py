"""Bounded exhaustive explorer for TopKit saved-Rip cleanup (formal/rip_cleanup).

What it verifies: properties P1..P6 plus P7 (ordinary Posts follow
membership) of `del Tag[agent]` / `del Tag[:]` saved runs, checked against
the REAL TopKit code under an adversary that controls everything user code
can do inside a `@Rip` step. Method: stateless DFS, re-executing the
scenario from scratch for each choice path; iterative deepening on the op
budget so the first violation reported uses the fewest ops. Deterministic,
stdlib only, single process, no randomness, no threads.

Bounds (defaults): 2 agents (ada, bob); Wizard (2 Rip steps + Ready Post +
Ping Action) and Fighter (1 Rip step); op budget OPS=3 top-level AND nested;
`rip_field` only for Wizard (trim, see below). --quick uses OPS=2.

Trims vs the design doc (all explicitly allowed there, reported here):
  - Fighter has 1 step by default (doc: "e.g. Fighter 1 step").
  - `rip_field` only for Wizard (doc: "`rip_field` only for Wizard").
  - --steps N overrides both tags; agents/tags/terminals never dropped.
  - No --jobs flag (single process; results deterministic).

Assumptions: interrupts only inside user steps (harness Boom/Interrupt);
revocation treated as atomic between observation points; single thread and
single context (no async); this world has no Posts except Wizard.Ready;
Tag classes are built once per process and worlds (agents) rebuilt per path.

Covers (kit code relied on; each read/check carries a comment at the site):
  TopKit/lifecycle.py: _rip, _rip_field, _revoke, _run_one, _retry_arrested,
    _call_teardown, _teardown_all, _new_run
  TopKit/rip_runs.py: _RipRun (tag/teardowns/cursor/running/revoked/member),
    _save_run, _pending_run, _finish_run, _run_saved, _retry_arrested
  TopKit/arrest.py: _safehouse, _arrest_of, _may_act, _require_available,
    _rip_door/_Rip_Door
  TopKit/fields.py: _field_of, _Field._members (seat identity)
  TopKit/state.py: _state_of, _State.postconditions
  TopKit/tags.py: MetaTag.__delitem__ (del T[x] / del T[:])
  TopKit/access.py: _agent_bool (bool(agent))
  TopKit/errors.py: TagCompositionError, TagResolutionError (covers
    TagArrestedAccessError and TagRogueAccessError subclasses)
P7 read choice: Contract.Status(agent) was probed to work on arrested Agents
but it EVALUATES user Post code (contracts._status_of runs each check, with
side effects in general); the harness instead reads the keys of
_state_of(agent).postconditions -- the same mapping _status_of iterates --
so the visibility verdict has zero user-code evaluation and zero side
effects, and was probed reliable (Ready present iff Wizard seated).

CLI: exit 0 = no violation in bounds, 1 = violation, 2 = harness/usage error.
Property ids `P1`..`P7` and `KIT_FAULT` start the violation line, e.g.
`VIOLATION P3: ...`, so `--replay` reproduces the printed choice vector.
"""

from __future__ import annotations

import argparse
import gc
import operator
import sys
import time
import traceback
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
# formal/rip_cleanup/real/explore.py -> repo root is 3 levels up.
DEFAULT_ROOT = SCRIPT_DIR.parent.parent.parent

AGENT_POOL = ("ada", "bob", "cyd", "dan", "eli", "fay")
PROMISES = {
    "P1": "A cleanup step that returned normally never runs again, steps "
          "run in order, and a step is never running twice at once.",
    "P2": "An application whose membership ended owes every step: custody "
          "ends only when all its steps returned normally, and retrying "
          "with working steps finishes everything and frees the Agent.",
    "P3": "While cleanup is unfinished, an outside act either finishes all "
          "owed cleanup first or is refused with TagArrestedAccessError; "
          "inside its own cleanup the act is allowed; bool(agent) is False "
          "exactly while its ledger is non-empty.",
    "P4": "A fresh Tagging made while an older application has unfinished "
          "cleanup survives the old cleanup; only an explicit Rip that "
          "targets the active membership ends it.",
    "P5": "del Tag[:] ends the membership of every starting member before "
          "any step callback runs.",
    "P6": "After a step run directly by del Tag[:] fails or is interrupted, "
          "that del Tag[:] runs no further step directly.",
    "P7": "An ordinary Post is a membership-bound Gain: Ready is visible "
          "exactly while the Wizard membership is active.",
    "KIT_FAULT": "Only documented refusals (TagCompositionError, "
                 "TagResolutionError incl. TagArrestedAccessError) or the "
                 "harness's own Boom/Interrupt escape a user-level op.",
}


# Harness control flow. BaseException so the kit's `except Exception`
# wrappers (rip_runs._run_saved, arrest._require_available) never wrap them:
# a violation or an exhausted choice vector must reach the driver intact.
class _Violation(BaseException):
    def __init__(self, prop, detail):
        super().__init__(detail)
        self.prop = prop
        self.detail = detail
        self.vector = None
        self.log = []


class _NeedMore(BaseException):
    def __init__(self, n):
        super().__init__("need more choices")
        self.n = n


class _PathTooLong(BaseException):
    pass


# Harness adversary faults (user code's two terminal choices).
class Boom(Exception):
    """A step raising an ordinary failure (kit: wrapped by _run_saved)."""


class Interrupt(KeyboardInterrupt):
    """A step interrupted (kit: propagates through `except Exception`)."""


class _Adversary:
    """Anchor the step bodies call; the current Run is installed per path."""

    def __init__(self):
        self.run = None

    def step(self, agent, tagname, idx):
        run = self.run
        # kit: lifecycle._teardown_all runs teardowns at GC without a ledger;
        # closed mode does nothing so a dying path cannot poison the next.
        if run is None or run.mode == "closed":
            return True
        if run.mode == "heal":
            return run.heal_step(agent, tagname, idx)
        return run.explore_step(agent, tagname, idx)


ADV = _Adversary()

# Filled by build_tags(); module-level so step closures resolve at call time.
Wizard = None
Fighter = None
TAGS = ()
FIELD_TAGS = ()
N_STEPS = {}


def build_tags(n_wizard, n_fighter):
    """Create Wizard/Fighter once per process with unique step names in rip
    order (kit: overlay stores state.rips in declaration order)."""
    from TopKit import Action, Post, Rip, Tag

    global Wizard, Fighter, TAGS, FIELD_TAGS, N_STEPS

    def ping(agent):
        return "pong"

    namespace = {"Ping": Action(ping)}

    def ready(agent):
        return True

    ready.__name__ = "Ready"
    namespace["Ready"] = Post(ready)
    for i in range(n_wizard):
        def step(agent, _i=i):
            return ADV.step(agent, "Wizard", _i)

        step.__name__ = "WStep%d" % i
        namespace[step.__name__] = Rip(step)
    Wizard = type("Wizard", (Tag,), namespace)

    namespace = {}
    for i in range(n_fighter):
        def step(agent, _i=i):
            return ADV.step(agent, "Fighter", _i)

        step.__name__ = "FStep%d" % i
        namespace[step.__name__] = Rip(step)
    Fighter = type("Fighter", (Tag,), namespace)

    TAGS = (Wizard, Fighter)
    FIELD_TAGS = (Wizard,)
    N_STEPS = {"Wizard": n_wizard, "Fighter": n_fighter}


class Run:
    """One path execution: world, choice driver, and harness bookkeeping."""

    def __init__(self, vector, ops_budget, max_choices=5000):
        from TopKit.arrest import _arrest_of, _safehouse
        from TopKit.fields import _field_of
        from TopKit.state import _state_of

        self._arrest_of = _arrest_of  # kit: arrest._arrest_of
        self._safehouse = _safehouse  # kit: arrest._safehouse
        self._field_of = _field_of  # kit: fields._field_of
        self._state_of = _state_of  # kit: state._state_of
        self.vector = list(vector)
        self.pos = 0
        self.n_choices = 0
        self.max_choices = max_choices
        self.ops_used = 0
        self.ops_budget = ops_budget
        self.mode = "explore"
        self.agents = []
        self.agent_index = {}
        self.log = []  # (indent, text)
        self.ok = {}  # (agent_idx, app) -> {step idx returned normally}
        self.frames = set()  # (agent_idx, app, idx) active callback frames
        self.cbstack = []  # callback frames (innermost last)
        self.opstack = []  # op frames (innermost last)
        self.protected = {}  # app -> (agent_idx, tag, seat): fresh seats
        self.seat_refs = []  # strong refs so seat ids are never reused
        self.ever_current = set()  # app ids once observed as current seats
        self.app_tag = {}  # app id -> tag name (for P2 step counts)
        self.app_agent = {}  # app id -> agent index
        self.current = {}  # (agent_idx, tag) -> current seat or None

    # -- small helpers -------------------------------------------------
    def _keep(self, seat):
        self.seat_refs.append(seat)
        return id(seat)

    def _seat(self, tag, agent):
        # kit: fields._field_of(tag)._members maps id(agent) -> weak seat.
        seat = self._field_of(tag)._members.get(id(agent))
        return seat if seat is not None and seat() is agent else None

    @staticmethod
    def _tagname(tag):
        return "Wizard" if tag is Wizard else "Fighter"

    @staticmethod
    def _aname(aidx):
        return AGENT_POOL[aidx]

    def _op_text(self, op):
        kind = op[0]
        if kind == "rip":
            return "del %s[%s]" % (
                    self._tagname(op[1]), self._aname(op[2]))
        if kind == "field":
            return "del %s[:]" % self._tagname(op[1])
        if kind == "tag":
            return "%s(%s)" % (self._tagname(op[1]), self._aname(op[2]))
        if kind == "act":
            return "%s.Ping()" % self._aname(op[1])
        if kind == "heal-act":
            return "%s.Ping()  [heal]" % self._aname(op[1])
        return op[0]

    def _step_text(self, tagname, idx, agent):
        return "%s step %d of %d runs for %s" % (
                tagname, idx + 1, N_STEPS[tagname],
                self._aname(self.agent_index[id(agent)]))

    # -- choices -------------------------------------------------------
    def next(self, n):
        self.n_choices += 1
        if self.n_choices > self.max_choices:
            raise _PathTooLong("path exceeded %d choices" % self.max_choices)
        if self.pos >= len(self.vector):
            raise _NeedMore(n)
        choice = self.vector[self.pos]
        self.pos += 1
        if not 0 <= choice < n:
            raise _PathTooLong("replay choice %d out of menu range %d"
                               % (choice, n))
        return choice

    def _base_ops(self):
        menu = []
        for tag in TAGS:
            for a in range(len(self.agents)):
                menu.append(("rip", tag, a))
        for tag in FIELD_TAGS:
            menu.append(("field", tag))
        for tag in TAGS:
            for a in range(len(self.agents)):
                menu.append(("tag", tag, a))
        for a in range(len(self.agents)):
            menu.append(("act", a))
        return menu

    def _top_menu(self):
        if self.ops_used >= self.ops_budget:
            return [("stop",)]
        return self._base_ops() + [("stop",)]

    def _inner_menu(self):
        if self.ops_used < self.ops_budget:
            return self._base_ops() + [("ok",), ("raise",), ("interrupt",)]
        return [("ok",), ("raise",), ("interrupt",)]

    def _refresh_seats(self):
        for aidx, agent in enumerate(self.agents):
            for tag in TAGS:
                seat = self._seat(tag, agent)
                if seat is not None:
                    app = self._keep(seat)
                    self.ever_current.add(app)
                    self.app_tag.setdefault(app, self._tagname(tag))
                    self.app_agent.setdefault(app, aidx)
                self.current[(aidx, tag)] = seat

    # -- observation points --------------------------------------------
    def _observe(self, where):
        self._refresh_seats()
        # P3 bool half: bool(agent) is False exactly while its ledger is
        # non-empty. kit: access._agent_bool vs arrest._arrest_of. No Posts
        # here except Wizard.Ready (always True), so equality must hold.
        for aidx, agent in enumerate(self.agents):
            if bool(agent) != (self._arrest_of(agent) is None):
                raise _Violation(
                        "P3", "bool(%s) is %s at %s but its ledger is %s "
                        "(truth must be False exactly while custody holds "
                        "runs)." % (
                                self._aname(aidx), bool(agent), where,
                                "non-empty" if self._arrest_of(agent) is not
                                None else "empty"))
        # P4: every protected fresh seat is still the current seat.
        for app, (aidx, tag, seat) in self.protected.items():
            if self._seat(tag, self.agents[aidx]) is not seat:
                raise _Violation(
                        "P4", "fresh %s seat of %s ended at %s while its old "
                        "application's cleanup was still owed (only an "
                        "explicit Rip targeting the active membership may "
                        "end it)." % (
                                self._tagname(tag), self._aname(aidx), where))
        # P7: Ready is visible iff the Wizard membership is active.
        # Reads _state_of(agent).postconditions keys (see module docstring
        # for why Status is not used); kit: state._state_of.
        for aidx, agent in enumerate(self.agents):
            state = self._state_of(agent)
            visible = set(state.postconditions) if state is not None else set()
            seated = self._seat(Wizard, agent) is not None
            if ("Ready" in visible) != seated:
                raise _Violation(
                        "P7", "Ready is %s on %s at %s but its Wizard "
                        "membership is %s (an ordinary Post follows its "
                        "membership)." % (
                                "visible" if "Ready" in visible else "absent",
                                self._aname(aidx), where,
                                "active" if seated else "ended"))

    def _check_top_boundary(self, where):
        # P2 stuck-custody part: outside any callback no run may be flagged
        # running. kit: rip_runs._RipRun.running, cleared in `finally`.
        for aidx, agent in enumerate(self.agents):
            arrest = self._arrest_of(agent)
            if arrest is not None:
                for run in arrest.runs:
                    if run.running:
                        raise _Violation(
                                "P2", "%s has run %s still flagged running at "
                                "%s with no callback active (stuck "
                                "custody)." % (
                                        self._aname(aidx),
                                        run.tag.__name__, where))

    # -- op frames -----------------------------------------------------
    def _release_protected(self, aidx, tag):
        # A protected seat is released only when it is the CURRENT seat:
        # then the op targets the active membership (contract P4).
        agent = self.agents[aidx]
        for app in [app for app, (pa, ptag, seat) in self.protected.items()
                    if pa == aidx and ptag is tag
                    and self._seat(tag, agent) is seat]:
            del self.protected[app]

    def _op_begin(self, op):
        kind = op[0]
        frame = {"kind": kind, "op": op, "failed": False, "starting": None,
                 "indent": len(self.opstack) + len(self.cbstack)}
        if kind == "rip":
            _, tag, aidx = op
            agent = self.agents[aidx]
            arrest = self._arrest_of(agent)
            # P4 release: del T[x] issued with no saved run of T targets the
            # active membership (kit: lifecycle._rip picks a pending run else
            # starts fresh work), so it legitimately ends a fresh seat.
            if arrest is None or all(r.tag is not tag for r in arrest.runs):
                self._release_protected(aidx, tag)
        elif kind == "field":
            _, tag = op
            starting = set()
            for aidx, agent in enumerate(self.agents):
                seat = self._seat(tag, agent)
                if seat is not None:
                    starting.add((aidx, self._keep(seat)))
            frame["starting"] = (tag, starting)
            # P4 release: del T[:] that started with the seat as a member
            # targets it (kit: lifecycle._rip_field snapshots members
            # first). Members only: release exactly the starting seats.
            started = set(starting)
            for app in [app for app, (pa, ptag, seat) in self.protected.items()
                        if ptag is tag and (pa, id(seat)) in started]:
                del self.protected[app]
        self.opstack.append(frame)
        return frame

    def _op_after_tag(self, tag, aidx, seat_before):
        agent = self.agents[aidx]
        seat_after = self._seat(tag, agent)
        if seat_after is not None and seat_after is not seat_before:
            arrest = self._arrest_of(agent)
            has_run = arrest is not None and any(
                    r.tag is tag for r in arrest.runs)
            framed = any(f["tag"] is tag and f["agent"] == aidx
                         for f in self.cbstack)
            # P4 mark: fresh seat created while an older application of the
            # same Tag still holds a ledger run, or from inside that Tag's
            # own step (kit: rip_runs ledger + harness callback frames).
            if has_run or framed:
                self.protected[self._keep(seat_after)] = (
                        aidx, tag, seat_after)

    # -- performing ops ------------------------------------------------
    def _perform(self, op):
        kind = op[0]
        if kind == "rip":
            _, tag, aidx = op
            operator.delitem(tag, self.agents[aidx])  # kit: tags.__delitem__
        elif kind == "field":
            _, tag = op
            operator.delitem(tag, slice(None))  # kit: lifecycle._rip_field
        elif kind == "tag":
            _, tag, aidx = op
            tag(self.agents[aidx])
        elif kind in ("act", "heal-act"):
            self.agents[op[1]].Ping()  # kit: gated by arrest._require_available
        elif kind == "stop":
            pass
        else:  # pragma: no cover - harness bug if reached
            raise AssertionError("unknown op %r" % (op,))

    @staticmethod
    def _allowed(error):
        from TopKit.errors import TagCompositionError, TagResolutionError
        return isinstance(
                error,
                (TagCompositionError, TagResolutionError, Boom, Interrupt))

    def _exec_top(self, op):
        frame = self._op_begin(op)
        text = self._op_text(op)
        if op[0] != "stop":
            self.ops_used += 1
        seat_before = None
        if op[0] == "tag":
            seat_before = self._seat(op[1], self.agents[op[2]])
        try:
            self._perform(op)
        except (_Violation, _NeedMore, _PathTooLong):
            raise
        except BaseException as error:
            self._after_op_error(op, error)
            outcome = type(error).__name__
        else:
            self._after_op_success(op)
            if op[0] == "tag":
                self._op_after_tag(op[1], op[2], seat_before)
            outcome = "ok"
        self.opstack.pop()
        self.log.append((frame["indent"], "%s -> %s" % (text, outcome)))
        self._observe("after %s" % text)
        self._check_top_boundary("after %s" % text)

    def _exec_nested(self, op):
        frame = self._op_begin(op)
        self.ops_used += 1
        text = self._op_text(op)
        seat_before = None
        if op[0] == "tag":
            seat_before = self._seat(op[1], self.agents[op[2]])
        try:
            self._perform(op)
        except (_Violation, _NeedMore, _PathTooLong):
            raise
        except BaseException as error:
            # Nested op exceptions are swallowed by the callback and logged;
            # to propagate one, the adversary chooses `raise` next.
            self._after_op_error(op, error)
            outcome = type(error).__name__
        else:
            self._after_op_success(op)
            if op[0] == "tag":
                self._op_after_tag(op[1], op[2], seat_before)
            outcome = "ok"
        self.opstack.pop()
        self.log.append((frame["indent"], "inside it: %s -> %s"
                         % (text, outcome)))
        self._observe("after nested %s" % text)

    def _after_op_error(self, op, error):
        kind = op[0]
        if kind in ("act", "heal-act"):
            agent = self.agents[op[1]]
            has_frame = any(f["agent"] == op[1] for f in self.cbstack)
            if isinstance(error, Interrupt) and not has_frame:
                # Act on an agent with no open door of its own (top level,
                # or another agent's cleanup): its heal-retry is user code
                # interrupted by Ctrl-C. The kit lets it propagate (kit:
                # rip_runs._run_saved catches only `except Exception`;
                # arrest._require_available re-raises non-Exceptions), so
                # an escaping Interrupt is allowed here; custody staying
                # behind is that Ctrl-C's doing, not a P3 break.
                return
            from TopKit.errors import TagArrestedAccessError
            if isinstance(error, TagArrestedAccessError):
                return  # the documented refusal: arrest holds.
            if self._allowed(error):
                raise _Violation(
                        "P3", "%s.Ping() raised %s but custody remains "
                        "without the documented TagArrestedAccessError "
                        "refusal." % (
                                self._aname(op[1]),
                                type(error).__name__))
            raise _Violation(
                    "KIT_FAULT", "%s.Ping() raised %s: %s\n%s" % (
                            self._aname(op[1]), type(error).__name__, error,
                            "".join(traceback.format_exception(error))))
        if self._allowed(error):
            return
        raise _Violation(
                "KIT_FAULT", "%s raised %s: %s\n%s" % (
                        self._op_text(op), type(error).__name__, error,
                        "".join(traceback.format_exception(error))))

    def _after_op_success(self, op):
        kind = op[0]
        if kind in ("act", "heal-act"):
            agent = self.agents[op[1]]
            has_frame = any(f["agent"] == op[1] for f in self.cbstack)
            if has_frame:
                return
            # P3 arrest holds: outside cleanup, success is only acceptable
            # with an empty ledger afterwards (kit: arrest._arrest_of).
            if self._arrest_of(agent) is not None:
                raise _Violation(
                        "P3", "%s.Ping() succeeded outside cleanup but its "
                        "ledger still holds runs %s (arrest must hold)." % (
                                self._aname(op[1]),
                                [(r.tag.__name__, r.cursor)
                                 for r in self._arrest_of(agent).runs]))

    # -- steps ---------------------------------------------------------
    def _find_run(self, agent, tag):
        # kit: the kit always runs steps through the ledger here
        # (rip_runs._run_saved sets run.running around invoke). The
        # entering step belongs to the most recently saved running run:
        # an outer step's frame is still active while a nested op runs a
        # fresh application's steps, so the FIRST running run would
        # misattribute the nested step to the outer application (false P1
        # "running twice at once"; the kit is really running the fresh
        # run's step). Ledger order is creation order (rip_runs._save_run
        # appends) and nested work is created later, so scan last-first.
        arrest = self._arrest_of(agent)
        if arrest is not None:
            for run in reversed(arrest.runs):
                if run.tag is tag and run.running:
                    return run
        return None

    def explore_step(self, agent, tagname, idx):
        tag = Wizard if tagname == "Wizard" else Fighter
        aidx = self.agent_index[id(agent)]
        run = self._find_run(agent, tag)
        if run is None:
            raise _Violation(
                    "P2", "%s for %s ran with no saved run in its ledger "
                    "(steps must run through custody)." % (
                            self._step_text(tagname, idx, agent),
                            self._aname(aidx)))
        # kit: rip_runs._RipRun.member identifies the application this run
        # belongs to; harness ok-sets are keyed per application.
        member = run.member
        app = id(member) if member is not None else ("nomem", tagname, aidx)
        if member is not None:
            self._keep(member)
        key = (aidx, app)
        if (aidx, app, idx) in self.frames:
            raise _Violation(
                    "P1", "%s is running twice at once (re-entered before "
                    "returning)." % self._step_text(tagname, idx, agent))
        # P1 order: a step runs only after all earlier steps of that
        # application returned normally (harness-owned ok-set, independent
        # of the kit's cursor).
        if self.ok.get(key, set()) != set(range(idx)):
            raise _Violation(
                    "P1", "%s ran although steps %s (not 0..%d) had returned "
                    "normally for that application." % (
                            self._step_text(tagname, idx, agent),
                            sorted(self.ok.get(key, set())), idx - 1))
        parent = self.opstack[-1] if self.opstack else None
        # P6: no step directly under an already-failed field Rip.
        if parent is not None and parent["kind"] == "field" \
                and parent["failed"]:
            raise _Violation(
                    "P6", "%s ran directly under %s after that field Rip "
                    "already failed (it must stop)." % (
                            self._step_text(tagname, idx, agent),
                            self._op_text(parent["op"])))
        # P5: while a field-Rip frame is on the stack, every starting seat
        # must already be gone (kit: lifecycle._rip_field revokes all
        # starting members before invoking any step).
        for frame in self.opstack:
            if frame["kind"] == "field":
                ftag, starting = frame["starting"]
                for (saidx, sseat) in starting:
                    seat = self._seat(ftag, self.agents[saidx])
                    if seat is not None and id(seat) == sseat:
                        raise _Violation(
                                "P5", "%s ran while starting member %s still "
                                "holds its %s membership (field Rip must "
                                "revoke everyone first)." % (
                                        self._step_text(
                                                tagname, idx, agent),
                                        self._aname(saidx),
                                        self._tagname(ftag)))
        frame = {"agent": aidx, "tag": tag, "tagname": tagname, "idx": idx,
                 "app": app, "parent": parent,
                 "indent": len(self.opstack) + len(self.cbstack)}
        self.cbstack.append(frame)
        self.frames.add((aidx, app, idx))
        step_text = self._step_text(tagname, idx, agent)
        self.log.append((frame["indent"] - 1, "%s -> enters" % step_text))
        self._observe("entry of %s" % step_text)
        while True:
            menu = self._inner_menu()
            choice = self.next(len(menu))
            item = menu[choice]
            if item[0] in ("ok", "raise", "interrupt"):
                return self._finish_step(frame, step_text, item[0])
            self._exec_nested(item)

    def _finish_step(self, frame, step_text, terminal):
        aidx, app, idx = frame["agent"], frame["app"], frame["idx"]
        key = (aidx, app)
        parent = frame["parent"]
        if terminal == "ok":
            # P1 no replay: a step that returned normally never runs again.
            if idx in self.ok.get(key, set()):
                self.cbstack.pop()
                self.frames.discard((aidx, app, idx))
                raise _Violation(
                        "P1", "%s returned normally twice for the same "
                        "application (cleanup replayed)." % step_text)
            self.ok.setdefault(key, set()).add(idx)
            self.cbstack.pop()
            self.frames.discard((aidx, app, idx))
            self.log.append((frame["indent"], "%s -> returns normally"
                             % step_text))
            self._observe("exit of %s" % step_text)
            return True
        self.cbstack.pop()
        self.frames.discard((aidx, app, idx))
        if parent is not None and parent["kind"] == "field":
            parent["failed"] = True
        if terminal == "raise":
            self.log.append((frame["indent"], "%s -> raises Boom"
                             % step_text))
            raise Boom("boom")
        self.log.append((frame["indent"], "%s -> interrupted" % step_text))
        raise Interrupt("interrupted")

    def heal_step(self, agent, tagname, idx):
        # HEAL mode: every step returns normally, no nested ops. Ledger and
        # P1/P7 checks still apply (parent is never a field frame here, so
        # P5/P6 trivially pass).
        tag = Wizard if tagname == "Wizard" else Fighter
        aidx = self.agent_index[id(agent)]
        run = self._find_run(agent, tag)
        if run is None:
            raise _Violation(
                    "P2", "%s for %s ran with no saved run during heal." % (
                            self._step_text(tagname, idx, agent),
                            self._aname(aidx)))
        member = run.member
        app = id(member) if member is not None else ("nomem", tagname, aidx)
        if member is not None:
            self._keep(member)
        key = (aidx, app)
        if (aidx, app, idx) in self.frames:
            raise _Violation(
                    "P1", "%s is running twice at once during heal."
                    % self._step_text(tagname, idx, agent))
        if self.ok.get(key, set()) != set(range(idx)):
            raise _Violation(
                    "P1", "%s ran during heal although steps %s had returned "
                    "normally." % (
                            self._step_text(tagname, idx, agent),
                            sorted(self.ok.get(key, set()))))
        frame = {"agent": aidx, "tag": tag, "tagname": tagname, "idx": idx,
                 "app": app, "parent": None,
                 "indent": len(self.opstack) + len(self.cbstack)}
        self.cbstack.append(frame)
        self.frames.add((aidx, app, idx))
        step_text = self._step_text(tagname, idx, agent)
        self.log.append((frame["indent"] - 1, "%s -> enters [heal]"
                         % step_text))
        self._observe("heal entry of %s" % step_text)
        if idx in self.ok.get(key, set()):
            self.cbstack.pop()
            self.frames.discard((aidx, app, idx))
            raise _Violation(
                    "P1", "%s returned normally twice during heal."
                    % step_text)
        self.ok.setdefault(key, set()).add(idx)
        self.cbstack.pop()
        self.frames.discard((aidx, app, idx))
        self.log.append((frame["indent"], "%s -> returns normally [heal]"
                         % step_text))
        self._observe("heal exit of %s" % step_text)
        return True

    # -- heal ----------------------------------------------------------
    def heal(self):
        from TopKit.errors import TagArrestedAccessError, TagCompositionError
        self.mode = "heal"
        for aidx in range(len(self.agents)):
            op = ("heal-act", aidx)
            frame = self._op_begin(op)
            text = self._op_text(op)
            try:
                self._perform(op)
            except (_Violation, _NeedMore, _PathTooLong):
                raise
            except BaseException as error:
                self.opstack.pop()
                if isinstance(error, (TagArrestedAccessError,
                                      TagCompositionError)):
                    # P2 completion: retrying with working steps must finish
                    # all owed steps and free the Agent (kit: arrest.
                    # _require_available retries before refusing).
                    raise _Violation(
                            "P2", "heal %s raised %s: %s owes cleanup that "
                            "working steps cannot finish (stuck custody)." % (
                                    text, type(error).__name__,
                                    self._aname(aidx)))
                raise _Violation(
                        "KIT_FAULT", "heal %s raised %s: %s\n%s" % (
                                text, type(error).__name__, error,
                                "".join(traceback.format_exception(error))))
            self.opstack.pop()
            self.log.append((0, "%s -> ok" % text))
            self._observe("heal %s" % text)
            self._check_top_boundary("heal %s" % text)
        self._check_heal_end()

    def _check_heal_end(self):
        # P2 no loss / no stuck custody at HEAL end.
        if dict(self._safehouse):
            detail = []
            for key, arrest in self._safehouse.items():
                name = self.app_agent.get(
                        id(arrest.agent), None)
                detail.append("%s: [%s]" % (
                        self._aname(name)
                        if name is not None and
                        name < len(self.agents) and
                        self.agents[name] is arrest.agent
                        else hex(key),
                        ", ".join("%s@%d%s" % (
                                r.tag.__name__, r.cursor,
                                " running" if r.running else "")
                                for r in arrest.runs)))
            raise _Violation(
                    "P2", "custody not empty after heal with working steps "
                    "(safehouse holds %s)." % "; ".join(detail))
        for aidx, agent in enumerate(self.agents):
            if self._arrest_of(agent) is not None:
                raise _Violation(
                        "P2", "%s still arrested after heal with working "
                        "steps." % self._aname(aidx))
            if not bool(agent):
                raise _Violation(
                        "P2", "%s is falsy after heal although its ledger is "
                        "empty." % self._aname(aidx))
        current_ids = set()
        for seat in self.current.values():
            if seat is not None:
                current_ids.add(id(seat))
        for app in self.ever_current:
            if app in current_ids:
                continue
            tagname = self.app_tag.get(app)
            full = set(range(N_STEPS.get(tagname, 0)))
            got = set()
            for (aa, aa_app), steps in self.ok.items():
                if aa_app == app:
                    got = set(steps)
                    break
            if got != full:
                raise _Violation(
                        "P2", "ended %s application (seat %s) owes steps %s "
                        "but only %s returned normally (cleanup lost)." % (
                                tagname, hex(app), sorted(full),
                                sorted(got)))


def make_world(n_agents):
    """Fresh agents, each tagged Wizard then Fighter (fixed preamble, not a
    choice; tagging runs no Rip steps)."""

    class Character:
        pass

    agents = [Character() for _ in range(n_agents)]
    for agent in agents:
        Wizard(agent)
        Fighter(agent)
    return agents


def run_vector(vector, ops_budget, n_agents):
    """Execute exactly the path named by vector; return the Run on success."""
    run = Run(vector, ops_budget)
    ADV.run = run
    try:
        run.agents = make_world(n_agents)
        run.agent_index = {id(a): i for i, a in enumerate(run.agents)}
        run._refresh_seats()
        run._observe("start")
        while True:
            menu = run._top_menu()
            choice = run.next(len(menu))
            op = menu[choice]
            if op[0] == "stop":
                run.log.append((0, "stop"))
                break
            run._exec_top(op)
        run.heal()
        return run
    except _Violation as violation:
        violation.vector = list(vector)
        violation.log = list(run.log)
        raise
    finally:
        # Closed adversary before agents die: the finalizer
        # (kit: lifecycle._teardown_all) must not touch harness state.
        run.mode = "closed"
        ADV.run = None
        run.agents = []
        run.agent_index = {}
        run._safehouse.clear()
        for tag in TAGS:
            try:
                members = run._field_of(tag)._members
            except Exception:
                continue
            for key, seat in list(members.items()):
                try:
                    if seat() is None:
                        members.pop(key, None)
                except Exception:
                    pass
        gc.collect()


def explore(ops, n_agents, deadline=None, start=None):
    """Iterative deepening on OPS; first violation has the fewest ops."""
    counts = []
    total_paths = 0
    for depth in range(ops + 1):
        level_paths = 0
        stack = [[]]
        while stack:
            if deadline is not None and start is not None \
                    and time.perf_counter() - start > deadline:
                return (None, counts, total_paths, True)
            prefix = stack.pop()
            try:
                run_vector(prefix, depth, n_agents)
            except _NeedMore as need:
                for i in reversed(range(need.n)):
                    stack.append(prefix + [i])
                continue
            except _Violation as violation:
                return (violation, counts, total_paths, False)
            level_paths += 1
            total_paths += 1
        counts.append((depth, level_paths))
    return (None, counts, total_paths, False)


def format_report(violation):
    lines = ["VIOLATION %s: %s" % (violation.prop, PROMISES[violation.prop])]
    for number, (indent, text) in enumerate(violation.log, 1):
        lines.append("  %d. %s%s" % (number, "  " * indent, text))
    lines.append("  failing check: %s" % violation.detail)
    lines.append("  replay: --replay %s" % ",".join(
            str(c) for c in violation.vector))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
            description="Bounded exhaustive explorer for TopKit saved-Rip "
                        "cleanup (properties P1-P7 + KIT_FAULT).")
    parser.add_argument("--root", default=str(DEFAULT_ROOT),
                        help="directory containing the TopKit package")
    parser.add_argument("--ops", type=int, default=3,
                        help="shared op budget (default 3)")
    parser.add_argument("--agents", type=int, default=2,
                        help="number of agents (default 2)")
    parser.add_argument("--steps", type=int, default=None,
                        help="Rip steps per tag (default: Wizard 2, "
                             "Fighter 1)")
    parser.add_argument("--quick", action="store_true",
                        help="fast preset (OPS=2)")
    parser.add_argument("--replay", default=None,
                        help="run exactly one choice vector, e.g. 3,0,5")
    parser.add_argument("--max-seconds", type=float, default=None,
                        help="stop starting new paths after S seconds")
    opts = parser.parse_args(argv)

    ops = 2 if opts.quick else opts.ops
    n_agents = opts.agents
    if not 1 <= n_agents <= len(AGENT_POOL):
        print("error: --agents must be 1..%d" % len(AGENT_POOL),
              file=sys.stderr)
        return 2
    if opts.steps is None:
        n_wizard, n_fighter = 2, 1
    else:
        if opts.steps < 1:
            print("error: --steps must be >= 1", file=sys.stderr)
            return 2
        n_wizard = n_fighter = opts.steps

    root = Path(opts.root).resolve()
    sys.path.insert(0, str(root))
    try:
        import TopKit
    except ImportError as error:
        print("error: cannot import TopKit from --root %s: %s"
              % (root, error), file=sys.stderr)
        return 2
    topkit_file = getattr(TopKit, "__file__", "") or ""
    try:
        inside = Path(topkit_file).resolve().is_relative_to(root)
    except AttributeError:  # Python < 3.9 fallback (needs >= 3.12 anyway)
        inside = str(Path(topkit_file).resolve()).startswith(str(root))
    if not inside:
        print("error: TopKit imported from %s, not --root %s"
              % (topkit_file, root), file=sys.stderr)
        return 2

    build_tags(n_wizard, n_fighter)

    if opts.replay is not None:
        try:
            vector = [int(p) for p in opts.replay.split(",") if p != ""]
        except ValueError:
            print("error: --replay must be comma-separated ints",
                  file=sys.stderr)
            return 2
        start = time.perf_counter()
        try:
            run = run_vector(vector, ops, n_agents)
        except _NeedMore as need:
            print("error: replay vector ended mid-path with menu of size "
                  "%d; append more choices" % need.n, file=sys.stderr)
            return 2
        except _Violation as violation:
            print(format_report(violation))
            return 1
        except _PathTooLong as error:
            print("error: %s" % error, file=sys.stderr)
            return 2
        print("replay log (%d events, %.1fs):" % (
                len(run.log), time.perf_counter() - start))
        for number, (indent, text) in enumerate(run.log, 1):
            print("  %d. %s%s" % (number, "  " * indent, text))
        print("no violation on this path")
        return 0

    start = time.perf_counter()
    try:
        violation, counts, total, timed_out = explore(
                ops, n_agents, opts.max_seconds, start)
    except _PathTooLong as error:
        print("error: %s" % error, file=sys.stderr)
        return 2
    elapsed = time.perf_counter() - start
    if violation is not None:
        print(format_report(violation))
        return 1
    print("bounds: agents=%d (%s), Wizard=%d steps+Ready/Ping, Fighter=%d "
          "step(s), ops<=%d, rip_field=[Wizard]" % (
                  n_agents, ",".join(AGENT_POOL[:n_agents]),
                  n_wizard, n_fighter, ops))
    print("menu: top: rip/tag per tag+agent, del Wizard[:], act per agent, "
          "stop; inside a step: same nested ops + ok/raise/interrupt")
    print("trim: Fighter 1 step by default and rip_field Wizard-only "
          "(both explicitly allowed by the design doc)")
    for depth, npaths in counts:
        print("paths explored at OPS<=%d: %d" % (depth, npaths))
    print("paths explored total: %d" % total)
    print("elapsed: %.1fs" % elapsed)
    if timed_out:
        print("TIME BUDGET EXCEEDED after %.1fs (bounds partial)" % elapsed)
    print("NO VIOLATION within these bounds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
