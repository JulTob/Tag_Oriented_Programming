"""Links: a Tag of one's own (STEP-SPEC-22).

A two-place statement, *Charlie knows Ruth*, is a family of one-place
statements, one for each Agent in the first place. So a Tag may grant
each of its Agents a Tag of its own, a **Link**::

    class Social(Tag):

        @Link
        class Knows(Tag):                         # the Relation: a template

            @Record
            def since(agent, contact, *, since=None):
                return since


    Social(charlie)
    charlie.Knows(ruth, since=2010)               # Ruth is Charlie's Contact
    ruth in charlie.Knows                         # True; ruth in bob.Knows is not
    charlie.Knows[ruth].since                     # 2010: the Pair's Record

How the kit builds it, from parts it already has:

- **The Link** is a real Tag, built for one Agent at the Parts of the
  declaring Tag. Its Field holds the Contacts, so membership, history,
  the algebra and Rip are the kit's own. It holds only the Relation's
  Tag-scope members (Reports and Operations) and the lines the Relation
  publishes onto Contacts (``@Public``).
- **The Pair** is a hidden Agent. It is tagged with the Relation's *Pair
  Tag*: the Relation's Actions, Records, conditions, Imprints and
  teardowns, each adapted to the two seats ``(agent, contact)``. So the
  Pair's gate, Parts, Write, Quality, Underlays, secrets and contract
  truth are the kit's own too.
- **Nothing lands on the Contact** but membership and what the Relation
  publishes. Her own Tags, Outline and contract never name a Link.
"""

from __future__ import annotations

from functools import partial
from inspect import CO_ITERABLE_COROUTINE
from inspect import isasyncgenfunction
from inspect import iscoroutinefunction
from inspect import isgeneratorfunction
from inspect import signature
from itertools import count
from types import coroutine
from typing import Any
from typing import Callable
from weakref import WeakKeyDictionary
import weakref

from . import tags as tags_module
from .declarations import KIND
from .declarations import STATE
from .declarations import Report
from .declarations import _CONDITION_KINDS
from .declarations import _FLAG
from .declarations import _LINK
from .declarations import _MISSING
from .declarations import _PAIR_TAG
from .declarations import _PUBLIC
from .declarations import _RELATION
from .declarations import _RIP
from .declarations import _SECRET
from .declarations import _UNDERLAY
from .declarations import _has_flag
from .declarations import _invalidate_declarations
from .declarations import _is_dunder
from .declarations import _is_link
from .declarations import _is_pin
from .declarations import _is_private
from .declarations import _is_relation
from .declarations import _relation_homes
from .declarations import _kind_of
from .declarations import _mark_flag
from .declarations import _parameters_of
from .errors import TagCompositionError
from .errors import TagDeclarationError
from .errors import TagResolutionError
from .errors import TagRogueAccessError
from .geometry import _form_of
from .geometry import _is_tag
from .geometry import _requiring_shapes
from .lifecycle import _rip
from .overlay import _require_membership
from .state import _Async_Door
from .state import _Bound
from .state import _Line
from .state import _State
from .state import _async_doors
from .state import _is_composing
from .state import _namespace_of
from .state import _reopen_async_doors
from .state import _set_runtime_type
from .state import _shut_async_doors
from .state import _state_of
from .tags import MetaTag
from .tags import Tag
from .transactions import _Call_Boundary
from .transactions import _Undo_Step
from .transactions import _apply_form
from .transactions import _capture
from .transactions import _close
from .transactions import _current_boundary
from .transactions import _gate_form
from .transactions import _hand_over
from .transactions import _open_boundary
from .transactions import _imprint
from .transactions import _inspect
from .transactions import _rollback_to
from .transactions import _undo_refused_linking


Function = Callable[..., Any]

_PAIR_ENDS = "_TOPKIT_PAIR"   # in a Pair's dictionary: who it joins, out of public reach
_LATER = "_topkit_later"      # on a Relation's function that runs later: "generator" or "coroutine"

_CLASS_MACHINERY = frozenset((
        "__module__",
        "__qualname__",
        "__doc__",
        "__dict__",
        "__weakref__",
        "__firstlineno__",
        "__static_attributes__",
        "__classcell__",
        "__annotations__",
        "__annotate__",
        "__orig_bases__",
        "__type_params__",
        ))

_TAKES_INPUTS = frozenset((
        "record",
        "precondition",
        "postcondition",
        "condition",
        "imprint",
        ))


# ------------------------------------------------------------------
# Declaring a Relation
# ------------------------------------------------------------------


def Link(
        relation: type,
        ) -> type:
    """Mark a Tag declared in another Tag's body as a **Relation**: every
    Agent of the declaring Tag receives a Link of its own, a Tag held
    under the declaration's name. Its functions take the Link's Agent and
    the Contact, in that order::

        class Social(Tag):

            @Link
            class Knows(Tag):

                @Pre
                def Not_Oneself(agent, contact):
                    return contact is not agent
    """

    _check_relation(relation)

    for name, member in relation.__dict__.items():
        _check_seats(
                relation,
                name,
                member,
                )

    for name, member in relation.__dict__.items():
        _mark_code_that_runs_later(
                name,
                member,
                )   # once the whole body passed: the builders ask the function, not the language, at every Link

    type.__setattr__(
            relation,
            _RELATION,
            True,
            )
    type.__setattr__(
            relation,
            KIND,
            "relation",
            )

    return relation


def _check_relation(
        relation: Any,
        ) -> None:
    """A Relation is a Tag whose Bases are Relations, and never a Pin
    (STEP-SPEC-22 rules 2.5 and 2.8)."""

    if not _is_tag(relation):
        raise TagDeclarationError(
                "@Link marks a Tag class declared in another Tag's body:"
                " @Link class Knows(Tag)"
                )

    if _is_pin(relation):
        raise TagDeclarationError(
                f"{relation.__name__} is a Pin; a Relation never is: Links"
                " between Tags need their own receiver rule (§1.9)"
                )

    for base in relation.__bases__:
        if _is_tag(base) and not _is_relation(base):
            raise TagDeclarationError(
                    f"{relation.__name__}: its Base {base.__name__} is an"
                    " ordinary Tag, which would be written on every Contact"
                    " without a word; a Relation's Bases are Relations, and a"
                    f" Link that Tags its Contact says so in an Imprint,"
                    f" {base.__name__}(contact)"
                    )


def _is_pair_member(
        name: str,
        member: Any,
        ) -> bool:
    """What a Relation declares for the Pair: everything callable that is
    not Tag scope (Reports, Operations) and not class machinery."""

    if _is_private(name) or name in _CLASS_MACHINERY:
        return False

    if isinstance(member, (Report, classmethod, staticmethod, type)):
        return False

    return callable(member)


def _function_of(
        name: str,
        member: Any,
        ) -> Function | None:
    """The function behind a Relation's member, when it is a Link's
    function. A static method is plain Python, a private helper is the
    Relation's own, and the language's machinery and plain values are
    neither: none of them is a Link's function."""

    if _is_private(name) or name in _CLASS_MACHINERY or isinstance(member, staticmethod):
        return None

    if isinstance(member, Report):
        function = member.builder
    else:
        function = getattr(
                member,
                "__func__",
                member,
                )

    if not callable(function):
        return None

    return function


def _later_of(
        function: Function,
        ) -> str | None:
    """How a function's body runs later, when it is iterated or awaited, or
    ``None`` for an ordinary function."""

    if isasyncgenfunction(function):
        return "async generator"

    if _is_generator_based_coroutine(function):
        return "generator-based coroutine"

    if iscoroutinefunction(function):
        return "coroutine"

    if isgeneratorfunction(function):
        return "generator"

    return None


def _refuse_code_that_runs_later(
        relation: type,
        name: str,
        member: Any,
        ) -> None:
    """A generator or a coroutine runs its body later, one step at a time,
    when it is iterated or awaited. The kit steps one behind the Link's
    doors (rule 3.6) where it hands the result to the caller: a Pair
    Action, an Operation or another class method. It refuses the rest.
    An async generator: the event loop closes it itself, outside the code
    that holds it, so its cleanup would run outside the doors. A Record,
    a condition, an Imprint, a teardown and a Report builder: the kit runs
    them itself and never iterates or awaits what they return."""

    function = _function_of(
            name,
            member,
            )

    if function is None:
        return

    later = _later_of(function)

    if later is None:
        return

    if later == "async generator":
        raise TagDeclarationError(
                f"{relation.__name__}.{name}: an async generator function is"
                " refused; the event loop closes an async generator itself,"
                " at its collection and at loop.shutdown_asyncgens, outside"
                " the code that holds it, so its cleanup would run outside"
                " the Link's doors; write a generator function or a"
                " coroutine function"
                )

    if later == "generator-based coroutine":
        raise TagDeclarationError(
                f"{relation.__name__}.{name}: a generator-based coroutine"
                " (@types.coroutine) is refused; write it as async def, or"
                " as a generator function"
                )

    if not _is_stepped_by_the_kit(member):
        raise TagDeclarationError(
                f"{relation.__name__}.{name}: a generator or a coroutine"
                " function is a Pair Action, an Operation or another class"
                " method; the kit runs a Record, a condition, an Imprint, a"
                " teardown and a Report builder itself and never iterates"
                " or awaits what they return"
                )


def _mark_code_that_runs_later(
        name: str,
        member: Any,
        ) -> None:
    """Note on a function, once, that it is a generator or a coroutine
    function, so that no Link's creation or call asks the language again.
    Only the two kinds the kit steps get here; the rest was refused."""

    function = _function_of(
            name,
            member,
            )

    if function is None:
        return

    later = _later_of(function)

    if later is not None:
        setattr(
                function,
                _LATER,
                later,
                )


def _is_generator_based_coroutine(
        function: Function,
        ) -> bool:
    code = getattr(
            function,
            "__code__",
            None,
            )

    return code is not None and bool(code.co_flags & CO_ITERABLE_COROUTINE)


def _is_stepped_by_the_kit(
        member: Any,
        ) -> bool:
    """A Pair Action, an Operation or another class method hands what it
    returns to its caller, so the kit can step it behind the doors
    (``_stepper_of``). A Record, a condition, an Imprint, a teardown (an
    Action marked @Rip) and a Report builder it runs itself."""

    if isinstance(member, classmethod):
        return True

    if isinstance(member, Report) or _has_flag(member, _RIP):
        return False

    return _kind_of(member) in (None, "action")


def _check_seats(
        relation: type,
        name: str,
        member: Any,
        ) -> None:
    """Both seats, always (STEP-SPEC-22 rule 3.3): the Agent and the
    Contact, by position, the Contact without a default."""

    if isinstance(member, type) and not _is_private(name) and name not in _CLASS_MACHINERY:
        raise TagDeclarationError(
                f"{relation.__name__}.{name}: a class in a Relation's body has"
                " no seat; declare Relations in the declaring Tag's body"
                )

    if isinstance(member, staticmethod) and (_has_flag(member, _SECRET) or getattr(member, _SECRET, False)):
        raise TagDeclarationError(
                f"{relation.__name__}.{name}: a static method is plain Python,"
                " which the kit never wraps, so @Secret on it would promise"
                " nothing; an @Operation takes the Link, and its @Secret keeps"
                " it in-house"
                )

    _refuse_code_that_runs_later(
            relation,
            name,
            member,
            )

    if not _is_pair_member(name, member) or _kind_of(member) == "delete":
        return

    if _has_flag(member, _PUBLIC) and _kind_of(member) in (*_CONDITION_KINDS, "imprint"):
        raise TagDeclarationError(
                f"{relation.__name__}.{name}: a @Public Pair member is a line"
                " the Contact calls or reads; a condition or an Imprint is the"
                " kit's to run, so it is never a line"
                )

    if _is_dunder(name):
        raise TagDeclarationError(
                f"{relation.__name__}.{name}: a Pair's members have ordinary"
                " names; a Pair has no special methods, and its teardown is"
                " @Rip def Forget(agent, contact)"
                )

    function = getattr(
            member,
            "__func__",
            member,
            )

    try:
        spec = _parameters_of(function)
    except (TypeError, ValueError) as error:
        raise TagDeclarationError(
                f"{relation.__name__}.{name}: a Link's function for the Pair"
                " takes the Agent and the Contact, in that order:"
                f" def {name}(agent, contact)"
                ) from error
    underlay = _has_flag(function, _UNDERLAY)
    needed = 3 if underlay else 2
    contact_has_default = len(spec.named) >= 2 and spec.named[1][1]

    if spec.positional < needed or contact_has_default:
        seats = "agent, contact, underlay" if underlay else "agent, contact"

        raise TagDeclarationError(
                f"{relation.__name__}.{name}: a Link's function for the Pair"
                " takes the Agent and the Contact, in that order, the Contact"
                f" without a default: def {name}({seats})"
                )


# ------------------------------------------------------------------
# The Pair Tag of a Relation
# ------------------------------------------------------------------


_pair_tags: "WeakKeyDictionary[type, type]" = WeakKeyDictionary()


def _pair_tag(
        relation: type,
        ) -> type:
    """The Tag a Pair receives from ``relation``: the Relation's Pair-scope
    declarations, each adapted to the two seats, with the Pair Tags of
    the Relation's own Bases as its Bases. One per Relation, shared by
    every Agent's Link: the Pair carries who it joins."""

    cached = _pair_tags.get(relation)

    if cached is not None:
        return cached

    bases = tuple(
            _pair_tag(base)
            for base in relation.__bases__
            if _is_relation(base)
            ) or (Tag,)
    namespace: dict[str, Any] = {
            "__module__": relation.__module__,
            "__qualname__": relation.__qualname__,
            "__doc__": relation.__doc__,
            _PAIR_TAG: True,   # the kit's own: reached only through a Link (rule 7.1)
            KIND: "pair",
            }

    for name, member in relation.__dict__.items():
        if not _is_pair_member(name, member):
            continue

        if _kind_of(member) == "delete":
            namespace[name] = member
        else:
            namespace[name] = _two_seats(member)

    pair_tag = MetaTag(
            relation.__name__,
            bases,
            namespace,
            )
    words = relation.__dict__.get(_FLAG)

    if words is not None:
        _mark_flag(
                pair_tag,
                words,
                )   # a Flag Link answers its words on the Pair, never on the Contact

    _pair_tags[relation] = pair_tag

    return pair_tag


def _two_seats(
        member: Any,
) -> Function:
    """Adapt ``def f(agent, contact, ...)`` to the kit's one receiver, the
    Pair. The adapted function shows the kit the seats after the Contact
    (a stored value or an Underlay, then inputs by name), and calls ``f``
    with the Link's Agent and the Contact. It runs inside the Agent's
    composition door (rule 3.6); the Pair's door is the kit's. A generator
    or a coroutine function takes each of its steps inside them."""

    function = getattr(
            member,
            "__func__",
            member,
            )
    parameters = list(signature(function).parameters.values())
    seats = {
            parameters[0].name,
            parameters[1].name,
            }
    kind = _kind_of(function)
    spec = _parameters_of(function)

    if spec.positional >= 3 and (kind == "record" or _has_flag(function, _UNDERLAY)):
        seats.add(parameters[2].name)   # the stored value, or the Underlay

    stepper = _stepper_of(function)

    if stepper is None:
        Two_Seats = _plain_seats(function)
    else:
        Two_Seats = _stepped_seats(stepper)

    Two_Seats.__signature__ = signature(function).replace(
            parameters=[parameters[0], *parameters[2:]],
            )
    Two_Seats.__name__ = function.__name__
    Two_Seats.__qualname__ = function.__qualname__
    Two_Seats.__doc__ = function.__doc__
    Two_Seats.__module__ = function.__module__

    for key, value in vars(function).items():
        if key.startswith("__topkit_"):
            setattr(
                    Two_Seats,
                    key,
                    value,
                    )   # the declaration's marks: kind, Underlay, Secret, Constant, Tool

    Two_Seats._topkit_seats = frozenset(seats)

    return Two_Seats


def _plain_seats(
        function: Function,
        ) -> Function:
    """The Pair's receiver for an ordinary function: it runs inside the
    doors for as long as it runs."""

    def Two_Seats(
            pair: object,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        agent, contact = _ends_of(pair)
        contacts = (contact,)
        entered = _enter_doors(
                agent,
                contacts,
                )   # her door stays shut on every path; the Link is the Agent's code (rule 3.6)

        try:
            return function(
                    agent,
                    contact,
                    *args,
                    **kwargs,
                    )
        finally:
            _leave_doors(entered)

    return Two_Seats


def _stepped_seats(
        stepper: Function,
        ) -> Function:
    """The Pair's receiver for a generator or a coroutine function: what it
    returns takes each of its steps inside the doors (rule 3.6)."""

    def Two_Seats(
            pair: object,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        agent, contact = _ends_of(pair)
        doors = _Doors(
                agent,
                pair,
                (contact,),
                )

        return stepper(
                doors,
                (agent, contact, *args),
                kwargs,
                )

    return Two_Seats


def _door_shut_operation(
        member: classmethod,
        ) -> classmethod:
    """A Relation's Operation, on one Agent's Link. Called with one of the
    Link's Contacts after the Link (as a published Operation is), it runs
    with her door shut, as a line does (rule 3.6); a generator or a
    coroutine function takes each of its steps that way."""

    function = member.__func__
    secret = _has_flag(function, _SECRET)
    stepper = _stepper_of(function)

    def Operation(
            link: type,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        if secret:
            _require_agents_door(
                    link,
                    function.__name__,
                    "Operation",
                    )

        record = link.__dict__.get(_RECORD)
        agent = None if record is None else record.agent()
        contacts = tuple(
                value
                for value in (*args, *kwargs.values())
                if _is_contact_of(link, value)
                )   # the Contacts it is called with, by position or by name: their doors stay shut (rule 3.6)

        if stepper is not None:
            doors = _Doors(
                    agent,
                    None,
                    contacts,
                    )

            return stepper(
                    doors,
                    (link, *args),
                    kwargs,
                    )

        return _run_behind(
                agent,
                contacts,
                function,
                link,
                *args,
                **kwargs,
                )

    Operation.__signature__ = signature(function)
    Operation.__name__ = function.__name__
    Operation.__qualname__ = function.__qualname__
    Operation.__doc__ = function.__doc__
    Operation.__module__ = function.__module__

    for key, value in vars(function).items():
        if key.startswith("__topkit_"):
            setattr(
                    Operation,
                    key,
                    value,
                    )   # its marks: kind, Public, Secret, Constant

    return classmethod(Operation)


def _require_agents_door(
        link: type,
        name: str,
        kind: str,
        ) -> None:
    """A ``@Secret`` member of the Link belongs to its Agent alone (rule
    2.7): it answers only inside the Agent's own code, the Link's
    functions included."""

    record = link.__dict__.get(_RECORD)
    agent = None if record is None else record.agent()
    state = None if agent is None else _state_of(agent)

    if state is None or not _is_composing(state):
        raise AttributeError(
                f"{name!r} is a secret {kind} of {link.__name__}; it answers"
                " only inside its Agent's own code"
                )


class _Secret_Link_Report(Report):
    """A Relation's ``@Secret`` Report, on one Agent's Link: read only
    inside the Agent's own code (rule 2.7)."""

    def __get__(
            report,
            instance: object,
            owner: type | None = None,
            ) -> Any:
        if owner is None:
            owner = type(instance)

        if _RECORD in owner.__dict__:
            _require_agents_door(
                    owner,
                    report._name,
                    "Report",
                    )

        return super().__get__(
                instance,
                owner,
                )


def _door_shut_builder(
        builder: Function,
        ) -> Function:
    """A Relation's Report builder, on one Agent's Link. A built Report is
    kept and served to everyone who reads it, so it is built with every
    Contact's door shut, whoever's code first read it (rule 3.6)."""

    def Build(
            link: type,
            *args: Any,
            ) -> Any:
        record = link.__dict__.get(_RECORD)
        agent = None if record is None else record.agent()

        return _run_behind(
                agent,
                _every_contact(link),
                builder,
                link,
                *args,
                )

    Build.__signature__ = signature(builder)
    Build.__name__ = builder.__name__
    Build.__qualname__ = builder.__qualname__
    Build.__doc__ = builder.__doc__
    Build.__module__ = builder.__module__

    for key, value in vars(builder).items():
        if key.startswith("__topkit_"):
            setattr(
                    Build,
                    key,
                    value,
                    )   # its marks: Public, Secret, Constant

    return Build


def _every_contact(
        link: type,
        ) -> list[object]:
    """Every Contact of the Link's family, now."""

    record = link.__dict__.get(_RECORD)

    if record is None:
        return []

    contacts: list[object] = []

    for member in record.family.Links():
        contacts.extend(member.__dict__["_topkit_field"])

    return contacts


def _enter_doors(
        agent: object | None,
        contacts: Any,
        ) -> tuple[_State | None, list[tuple[_State, int]] | None]:
    """Enter the doors a Link's code runs behind (rule 3.6): every Contact
    it is about has her door shut, and the Link's Agent has his open,
    since the Link's code is its Agent's code. Return what
    ``_leave_doors`` needs to put every door back as it was."""

    saved: list[tuple[_State, int]] | None = None

    for contact in contacts:
        if contact is agent:
            continue   # a self-link: she is the Agent, whose door opens

        state = _state_of(contact)

        if state is not None and state.composing:
            if saved is None:
                saved = []

            saved.append(
                    (
                        state,
                        state.composing,
                        )
                    )
            state.composing = 0   # her door stays shut

    agent_state = None if agent is None else _state_of(agent)

    if agent_state is not None:
        agent_state.composing += 1   # his door opens

    return (
            agent_state,
            saved,
            )


def _leave_doors(
        entered: tuple[_State | None, list[tuple[_State, int]] | None],
        ) -> None:
    agent_state, saved = entered

    if agent_state is not None:
        agent_state.composing -= 1

    if saved is None:
        return

    for state, opened in saved:
        state.composing = opened


def _run_behind(
        agent: object | None,
        contacts: Any,
        function: Function,
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    """Call a Link's function behind its doors, for as long as it runs."""

    entered = _enter_doors(
            agent,
            contacts,
            )

    try:
        return function(
                *args,
                **kwargs,
                )
    finally:
        _leave_doors(entered)


# ------------------------------------------------------------------
# Code that runs later: a generator or a coroutine of a Link
# ------------------------------------------------------------------


def _stepper_of(
        function: Function,
        ) -> Function | None:
    """How a Link's function that runs later is started, or ``None`` for an
    ordinary one. Its body runs when it is iterated or awaited, long after
    the call returned, so each of its steps runs behind the doors (rule
    3.6); between steps every door is as the caller left it. Only a
    function the Link's author wrote as a generator or a coroutine is
    stepped: what an ordinary function hands back was made elsewhere, and
    runs under the doors of whoever runs it."""

    later = getattr(
            function,
            _LATER,
            None,
            )

    if later == "coroutine":
        return partial(
                _start,
                _coroutine_behind,
                function,
                signature(function),
                )

    if later == "generator":
        return partial(
                _start,
                _steps_behind,
                function,
                signature(function),
                )

    return None


class _Doors:
    """The doors a Link's code keeps at every step of a generator or a
    coroutine (rule 3.6): the Agent's and the Pair's open, every Contact's
    shut, her async door included. Held weakly: a Link never keeps its
    Agent, its Pair or a Contact alive, and each step finds them again."""

    __slots__ = (
            "agent",
            "pair",
            "contacts",
            "held",
            )

    def __init__(
            doors,
            agent: object | None,
            pair: object | None,
            contacts: Any,
            ) -> None:
        doors.agent = None if agent is None else weakref.ref(agent)
        doors.pair = None if pair is None else weakref.ref(pair)
        doors.contacts = [weakref.ref(contact) for contact in contacts]
        doors.held = None   # the async doors held when the Link's code started, once it has

    def Alive(
            doors,
            ) -> tuple[object | None, object | None, list[object]]:
        """Whoever of them is still there."""

        agent = None if doors.agent is None else doors.agent()
        pair = None if doors.pair is None else doors.pair()
        contacts = [
                contact
                for reference in doors.contacts
                if (contact := reference()) is not None
                ]

        return (
                agent,
                pair,
                contacts,
                )

    def Enter(
            doors,
            ) -> tuple[Any, Any, list[_Async_Door]]:
        """Open and shut the doors for one step; ``Leave`` puts them back."""

        agent, pair, contacts = doors.Alive()
        states = [
                state
                for contact in contacts
                if contact is not agent and (state := _state_of(contact)) is not None
                ]
        agent_doors = _enter_doors(
                agent,
                contacts,
                )   # hers shut, his open
        pair_doors = _enter_doors(
                pair,
                (),
                )   # the Pair's open

        if doors.held is None:
            doors.held = _async_doors.get()   # a hook the Link's own code enters later is hers to use

        async_doors = _shut_async_doors(
                states,
                doors.held,
                )   # and hers, if she opened one before the Link's code began

        return (
                agent_doors,
                pair_doors,
                async_doors,
                )

    def Leave(
            doors,
            entered: tuple[Any, Any, list[_Async_Door]],
            ) -> None:
        agent_doors, pair_doors, async_doors = entered
        _reopen_async_doors(async_doors)
        _leave_doors(pair_doors)
        _leave_doors(agent_doors)


def _call_behind(
        doors: _Doors,
        function: Function,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        ) -> Any:
    """Call a Link's function behind the doors, as an ordinary one is. For
    a generator or a coroutine function the call makes the object and runs
    none of its body; every step after it takes the doors again."""

    entered = doors.Enter()

    try:
        return function(
                *args,
                **kwargs,
                )
    finally:
        doors.Leave(entered)


def _start(
        behind: Function,
        function: Function,
        declared: Any,
        doors: _Doors,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        ) -> Any:
    """Start a Link's generator or coroutine function. The call is checked
    now, as Python checks it, so a wrong call fails at the call. The Link's
    own generator or coroutine is made when the first step is asked for: one
    that never starts, because its task was cancelled first, leaves no
    coroutine "never awaited", and the object the caller holds is the older
    of the two, so a collector that finds both closes it first."""

    try:
        declared.bind(
                *args,
                **kwargs,
                )
    except TypeError as error:
        raise TypeError(f"{function.__qualname__}(): {error}") from None

    stepping = behind(
            doors,
            function,
            args,
            kwargs,
            )
    stepping.__name__ = function.__name__
    stepping.__qualname__ = function.__qualname__

    return stepping


def _steps_behind(
        doors: _Doors,
        function: Function,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        ) -> Any:
    """A Link's generator, or the awaiting of its coroutine, taken one step
    at a time, each step behind the doors. What is sent or thrown in, a
    close() included, goes to the Link's code at its next step; what it
    returns, raises or yields comes out. So its ``finally`` runs inside the
    doors, and what it returns on ``GeneratorExit`` is what ``close()``
    returns (Python 3.13)."""

    steps = _call_behind(
            doors,
            function,
            args,
            kwargs,
            )
    del args, kwargs   # the body holds them now; this generator keeps nobody alive

    sent: Any = None
    thrown: BaseException | None = None

    while True:
        entered = doors.Enter()

        try:
            if thrown is None:
                step = steps.send(sent)
            else:
                step = steps.throw(thrown)
        except StopIteration as stop:
            return stop.value
        finally:
            thrown = None   # an exception comes out, or is handled: never kept in this frame
            doors.Leave(entered)

        try:
            sent = yield step
        except BaseException as error:
            thrown = error   # GeneratorExit too: a close() and a throw() reach the Link's code as they would reach any generator's
            sent = None


@coroutine
def _suspend(
        step: Any,
        ) -> Any:
    """Hand what the Link's coroutine yielded to whoever drives it, and give
    back what that one sends in, or raise what it throws in."""

    return (yield step)


async def _coroutine_behind(
        doors: _Doors,
        function: Function,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        ) -> Any:
    """A coroutine of a Link, as a coroutine: awaitable, and accepted by
    ``asyncio.run`` and by tasks, each of its steps behind the doors. The
    loop is the coroutine itself, never an ``await`` of the Link's own, so
    that ``close()`` gives back what the body returns when it is closed."""

    steps = _call_behind(
            doors,
            function,
            args,
            kwargs,
            )
    del args, kwargs   # the body holds them now; this coroutine keeps nobody alive

    sent: Any = None
    thrown: BaseException | None = None

    while True:
        entered = doors.Enter()

        try:
            if thrown is None:
                step = steps.send(sent)
            else:
                step = steps.throw(thrown)
        except StopIteration as stop:
            return stop.value
        finally:
            thrown = None   # an exception comes out, or is handled: never kept in this frame
            doors.Leave(entered)

        try:
            sent = await _suspend(step)
        except BaseException as error:
            thrown = error   # GeneratorExit too, as for a generator
            sent = None


def _is_contact_of(
        link: type,
        candidate: object,
        ) -> bool:
    state = _state_of(candidate)

    return (
            state is not None
            and link in state.active
            )


# ------------------------------------------------------------------
# The Pair
# ------------------------------------------------------------------


class Pair:
    """One Agent and one Contact, linked: what a Link gives, held for the
    Link's Agent and read through the Link, ``charlie.Knows[ruth]``.

    Nothing public on a Pair names the Agent: its functions receive the
    Agent in their first seat, and that is the Link's own code."""

    def __repr__(
            pair,
            ) -> str:
        ends = object.__getattribute__(pair, "__dict__").get(_PAIR_ENDS)
        name = ends.name if ends is not None else "Link"

        return f"<{name} Pair>"


class _Ends:
    """Who a Pair joins, held weakly: a Link never keeps its Agent alive,
    and a Field never keeps a Contact alive."""

    __slots__ = (
            "agent",
            "contact",
            "family",
            "name",
            "held",
            "ended",
            )

    def __init__(
            ends,
            agent: object,
            contact: object,
            family: "_Family",
            name: str,
            forget: Callable[..., None],
            ) -> None:
        ends.agent = weakref.ref(agent)
        ends.contact = weakref.ref(contact, forget)
        ends.family = family
        ends.name = name
        ends.held = None   # both ends, held strongly only while teardowns run
        ends.ended = False   # set when the Pair ends: a Pair held by a name answers no more


def _ends_of(
        pair: object,
        ) -> tuple[object, object]:
    ends: _Ends = object.__getattribute__(pair, "__dict__")[_PAIR_ENDS]

    if ends.held is not None:
        return ends.held

    if ends.ended:
        raise TagResolutionError(
                f"this {ends.name} Pair has ended: its Contact was unlinked;"
                " reach a Pair through its Link, agent.Link[contact]"
                )

    agent = ends.agent()
    contact = ends.contact()

    if agent is None:
        agent = ends.family.dying   # the finalizer of the Link's Agent fills the first seat

    if agent is None or contact is None:
        raise TagResolutionError(
                f"this {ends.name} Pair's Agent or Contact no longer exists"
                )

    return agent, contact


class _Family:
    """The Links of one Agent that share Pairs: a Link and its Base Links
    hold one Pair for each Contact (rule 5.3). Independent Links of one
    Agent are separate families."""

    __slots__ = (
            "pairs",
            "links",
            "dying",
            "busy",
            "__weakref__",
            )

    def __init__(
            family,
            ) -> None:
        family.pairs: dict[int, Pair] = {}
        family.links: list[weakref.ref] = []
        family.dying: object | None = None
        family.busy = 0   # linkings and extensions under way: no Layer is added meanwhile

    def Pair_Of(
            family,
            contact: object,
            leaving: bool = False,
            ) -> Pair | None:
        """The Pair of a live Contact. ``leaving`` is her own teardown,
        inside her finalizer: in a reference cycle the language has
        already cleared her weak references, but she is still in hand and
        her identity is still hers, so her Pair is still found (rule 7.4)."""

        pair = family.pairs.get(id(contact))

        if pair is None:
            return None

        ends = object.__getattribute__(pair, "__dict__")[_PAIR_ENDS]
        live = ends.contact()

        if live is contact:
            return pair

        if ends.held is not None and ends.held[1] is contact:
            return pair

        if leaving and live is None:
            return pair

        return None

    def New_Pair(
            family,
            agent: object,
            contact: object,
            name: str,
            ) -> Pair:
        pair = Pair()
        key = id(contact)
        forget = partial(
                _forget_pair,
                weakref.ref(family),
                key,
                )
        object.__getattribute__(pair, "__dict__")[_PAIR_ENDS] = _Ends(
                agent,
                contact,
                family,
                name,
                forget,
                )
        family.pairs[key] = pair

        return pair

    def End(
            family,
            contact: object,
            ) -> None:
        pair = family.Pair_Of(
                contact,
                leaving=True,
                )

        if pair is None:
            return

        del family.pairs[id(contact)]
        object.__getattribute__(pair, "__dict__")[_PAIR_ENDS].ended = True
        state = _state_of(pair)

        if state is not None:
            state.rips.clear()   # its teardowns ran, or end silently; never again at collection (rule 8.5)

    def Links(
            family,
            ) -> list[type]:
        return [
                link
                for reference in family.links
                if (link := reference()) is not None
                ]


def _forget_pair(
        family_reference: weakref.ref,
        key: int,
        expired: weakref.ref,
        ) -> None:
    """A Contact's weak reference is cleared. Her Pair stays until her
    finalizer's teardown ends it, even in a reference cycle, where the
    language clears weak references before any finalizer runs (rule
    7.4). Her identity cannot be reused before that teardown: an object
    is freed only after its finalizer. At interpreter exit no finalizer
    runs, and nothing reads the Pair again."""

    return None


# ------------------------------------------------------------------
# One Agent's Link
# ------------------------------------------------------------------


class _Link_Record:
    """What the kit keeps about one Agent's Link, out of public reach."""

    __slots__ = (
            "name",
            "agent",
            "layers",
            "gained",
            "family",
            "hook",
            "ending",
            "ended",
            "pair_form",
            )

    def __init__(
            record,
            name: str,
            agent: object,
            layers: list[type],
            family: _Family,
            ) -> None:
        record.name = name
        record.agent = weakref.ref(agent)
        record.layers = layers
        record.gained = {
                relation: next(_gaining)
                for relation in layers
                }   # when the Agent gained each Layer: the order every Pair is overlaid in
        record.family = family
        record.hook = None
        record.ending = False
        record.ended = False
        record.pair_form = None   # the Pair Tags a linking gives, once computed


_RECORD = "_topkit_link_record"   # on the Link class itself: read on every Pair lookup
_gaining = count(1)   # numbers the Layers in the order Agents gain them


def _record_of(
        link: type,
        ) -> _Link_Record:
    return link.__dict__[_RECORD]


def _grant(
        agent: object,
        state: _State,
        declarations: Any,
        ) -> None:
    """At the Parts of a declaring Tag (rule 4.1): build each Link the
    Agent does not hold yet, or extend a held one with a new Layer (rule
    4.6). The Link is stored under the Relation's name, read-only."""

    namespace = _namespace_of(agent)

    for name, _relation in declarations.links:
        link, layers = state.links[name]

        if link is None:
            link = _new_link(
                    agent,
                    state,
                    name,
                    layers,
                    )
            state.links[name] = (
                    link,
                    layers,
                    )
        else:
            record = _record_of(link)
            added = [
                    relation
                    for relation in layers
                    if relation not in record.layers
                    ]

            if added:
                _extend(
                        link,
                        record,
                        added,
                        )

        namespace[name] = link


def _new_link(
        agent: object,
        state: _State,
        name: str,
        layers: tuple[type, ...],
        ) -> type:
    """A distinct Tag for this Agent (rule 4.2), with this Agent's own
    Links as its Bases (rule 2.4)."""

    _refuse_mixed_layers(
            list(layers),
            name,
            TagCompositionError,
            )
    bases = _base_links(
            state,
            layers,
            )
    namespace: dict[str, Any] = {
            "__module__": layers[0].__module__,
            "__qualname__": layers[0].__qualname__,
            "__doc__": layers[0].__doc__,
            _LINK: True,
            KIND: "link",
            }

    for relation in layers:
        namespace.update(_tag_scope_of(relation))

    tags_module._making_link += 1

    try:
        link = MetaTag(
                name,
                tuple(bases) or (Tag,),
                namespace,
                )
    finally:
        tags_module._making_link -= 1

    family = _family_for(
            bases,
            agent,
            )
    record = _Link_Record(
            name,
            agent,
            list(layers),
            family,
            )
    type.__setattr__(
            link,
            _RECORD,
            record,
            )   # the record holds its Agent weakly, so the Link never keeps it alive
    reference = weakref.ref(link)
    family.links.append(reference)
    boundary = _open_boundary()

    if boundary is not None:
        boundary.undo.append(_Undo_Step(
                (agent,),
                partial(
                        _forget_link,
                        record,
                        reference,
                        ),
                ))   # a call on the Agent that rolls back leaves no trace in the family (§0.6)

    for relation in layers:
        _publish_lines(
                link,
                relation,
                )

    return link


def _forget_link(
        record: _Link_Record,
        reference: weakref.ref,
        ) -> None:
    family = record.family

    if reference in family.links:
        family.links.remove(reference)

    _forget_pair_forms(family)


def _base_links(
        state: _State,
        layers: tuple[type, ...],
        ) -> list[type]:
    """The Agent's own Links for the Relations its Relations extend under
    other names: Charlie's Trusts is a Shape of Charlie's Knows."""

    bases: list[type] = []

    for relation in layers:
        for base in relation.__bases__:
            if not _is_relation(base) or base in layers:
                continue

            held = _link_holding(
                    state,
                    base,
                    )

            if held is None:
                raise TagCompositionError(
                        f"{relation.__name__} extends {base.__name__}, a Link"
                        " this Agent does not hold"
                        )

            if held not in bases:
                bases.append(held)

    return [
            base
            for base in bases
            if not any(
                    other is not base and issubclass(other, base)
                    for other in bases
                    )
            ]   # only the leaves: a consistent order for the language


def _link_holding(
        state: _State,
        relation: type,
        ) -> type | None:
    for link, layers in state.links.values():
        if link is not None and relation in layers:
            return link

    return None


def _family_for(
        bases: list[type],
        agent: object,
        ) -> _Family:
    """A Link joins the family of its Base Links; a Link with none starts
    its own. Base Links from separate families are joined into one, after
    checking that no Contact holds a Pair in two of them. The join is
    undone with the call if it rolls back (§0.6)."""

    families: list[_Family] = []

    for base in bases:
        for member in _form_of(base):
            family = _record_of(member).family

            if family not in families:
                families.append(family)

    if not families:
        return _Family()

    if len(families) > 1:
        for family in families:
            _refuse_while_busy(
                    family,
                    "its Links are not joined with another family's",
                    )

    _refuse_shared_contacts(families)
    kept = families[0]
    joins = [
            _join(
                    kept,
                    other,
                    )
            for other in families[1:]
            ]
    boundary = _open_boundary()

    if joins and boundary is not None:
        boundary.undo.append(_Undo_Step(
                (agent,),
                partial(
                        _split,
                        kept,
                        joins,
                        ),
                ))

    return kept


def _refuse_while_busy(
        family: "_Family",
        what: str,
        ) -> None:
    """While a linking or an extension of a family is under way, from a
    Pair's gate to the Contact's entry, nothing adds a Layer to its Pairs:
    the Pair in flight would hold a Layer its linking did not give it, and
    undoing one would take back the other's work."""

    if family.busy:
        raise TagCompositionError(
                f"a linking or an extension is under way in this Link's"
                f" family, so {what} until it is done; give the Agent the"
                " Shape before or after it, or from the Pair's Imprint,"
                " which runs after her entry"
                )


def _refuse_shared_contacts(
        families: list[_Family],
        ) -> None:
    """Two families joined would give one Contact two Pairs: refused,
    before anything is joined."""

    seen: set[int] = set()

    for family in families:
        if seen & family.pairs.keys():
            raise TagCompositionError(
                    "this Link would join Links that hold separate Pairs for"
                    " one Contact; unlink her from one of them first"
                    )

        seen.update(family.pairs)


def _join(
        kept: _Family,
        other: _Family,
        ) -> tuple[_Family, dict[int, Pair], list[type], list[weakref.ref]]:
    """Move ``other``'s Pairs and Links into ``kept``. Returns what
    ``_split`` needs to move them back."""

    moved_pairs = dict(other.pairs)
    moved_links = other.Links()
    added: list[weakref.ref] = []

    for pair in moved_pairs.values():
        object.__getattribute__(pair, "__dict__")[_PAIR_ENDS].family = kept

    kept.pairs.update(moved_pairs)
    other.pairs.clear()

    for link in moved_links:
        _record_of(link).family = kept
        reference = weakref.ref(link)
        kept.links.append(reference)
        added.append(reference)

    return (
            other,
            moved_pairs,
            moved_links,
            added,
            )


def _split(
        kept: _Family,
        joins: list[tuple[_Family, dict[int, Pair], list[type], list[weakref.ref]]],
        ) -> None:
    """Undo ``_join``, latest first: each family gets back its own Pairs
    and Links."""

    for other, moved_pairs, moved_links, added in reversed(joins):
        for key, pair in moved_pairs.items():
            if kept.pairs.get(key) is pair:
                del kept.pairs[key]
                other.pairs[key] = pair
                object.__getattribute__(pair, "__dict__")[_PAIR_ENDS].family = other

        for link in moved_links:
            _record_of(link).family = other
            _record_of(link).pair_form = None

        for reference in added:
            if reference in kept.links:
                kept.links.remove(reference)

    _forget_pair_forms(kept)


def _tag_scope_of(
        relation: type,
        ) -> dict[str, Any]:
    """What the Relation declares for the Link itself, one Link per Agent
    (rule 2.3): its Reports (``def capacity(link)``), its Operations and
    other class methods, its static methods and its plain values
    (``capacity = 150``), as an ordinary Tag keeps them on the class.
    Everything else callable is the Pair's."""

    members: dict[str, Any] = {}

    for name, member in relation.__dict__.items():
        if not _is_tag_scope_member(name, member):
            continue

        if isinstance(member, Report):
            if _has_flag(member.builder, _SECRET):
                copy = _Secret_Link_Report(_door_shut_builder(member.builder))
            else:
                copy = Report(_door_shut_builder(member.builder))   # one Report per Link: each builds for its own Link

            copy.public = member.public
            members[name] = copy
        elif isinstance(member, classmethod):
            members[name] = _door_shut_operation(member)   # an Operation, or another class method
        else:
            members[name] = member   # a static method, or a plain value: capacity = 150

    return members


def _is_tag_scope_member(
        name: str,
        member: Any,
        ) -> bool:
    """What a Relation declares for the Link itself (rule 2.3): Reports,
    Operations and other class methods, static methods, plain values.
    The kit's marks and the language's machinery stay on the Relation."""

    if _is_private(name) or name in _CLASS_MACHINERY:
        return False

    if isinstance(member, Report):
        return True

    if isinstance(member, classmethod) and _kind_of(member) == "operation":
        return True

    if _is_dunder(name):
        return False

    return isinstance(member, (classmethod, staticmethod)) or not callable(member)


def _layer_names(
        layer: type,
        ) -> tuple[set[str], set[str]]:
    """A Relation's line names (its ``@Public`` Pair members) and the
    names it declares for the Link itself."""

    lines = set(_published_names(layer))
    members = {
            member_name
            for member_name, member in layer.__dict__.items()
            if _is_tag_scope_member(member_name, member)
            }

    return (
            lines,
            members,
            )


def _extension_chain(
        inherited: type,
        name: str,
        ) -> list[type]:
    """The Layers of one Link an extension joins: the Relation it extends,
    and the Relations that one extends in turn under the same name. A
    Relation Base under another name is a Shape Relation's Base: another
    Link, whose lines stay on its own class."""

    chain: list[type] = []
    layer: type | None = inherited

    while layer is not None:
        chain.append(layer)
        relation_bases = [
                base
                for base in layer.__bases__
                if _is_relation(base)
                ]
        layer = None

        if len(relation_bases) == 1:
            home = _relation_homes.get(relation_bases[0])

            if home is not None and home[1] == name:
                layer = relation_bases[0]

    return chain


def _refuse_a_name_both_ways(
        tag: type,
        name: str,
        extension: type,
        inherited: type,
        ) -> None:
    """One Link holds the lines and the Tag-scope members of all its Layers
    in one class. So across a Relation and its extensions, a name is a line
    or a Tag-scope member, never both: one would silently replace the
    other on every Agent's Link. Checked when the extending Shape is made;
    extensions declared side by side meet only on an Agent, and are
    checked there (``_refuse_mixed_layers``)."""

    _refuse_mixed_layers(
            [*reversed(_extension_chain(inherited, name)), extension],
            f"{tag.__name__}.{name}",
            TagDeclarationError,
            )


def _refuse_mixed_layers(
        layers: list[type],
        where: str,
        failure: type,
        ) -> None:
    """No name is a line in one Layer of a Link and a member of the Link in
    another."""

    lines: dict[str, type] = {}
    members: dict[str, type] = {}

    for layer in layers:
        layer_lines, layer_members = _layer_names(layer)

        for line_name in layer_lines:
            lines.setdefault(line_name, layer)

        for member_name in layer_members:
            members.setdefault(member_name, layer)

    clashes = sorted(set(lines) & set(members))

    if not clashes:
        return

    clash = clashes[0]

    raise failure(
            f"{where}.{clash}: {lines[clash].__qualname__} publishes"
            f" '{clash}' as a line onto its Contacts, and"
            f" {members[clash].__qualname__} declares it for the Link itself;"
            " one Link holds both side by side, so give one of them another"
            " name"
            )


def _publish_lines(
        link: type,
        relation: type,
        ) -> None:
    """``@Public`` Pair members are seen by the Contact (rule 2.7): each
    becomes a line on the Link, which the Contact receives at linking.
    ``ruth.Greet()`` runs the Pair's ``Greet(charlie, ruth)``."""

    for name, member in relation.__dict__.items():
        if not _is_pair_member(name, member) or not _has_flag(member, _PUBLIC):
            continue

        if _kind_of(member) == "record":
            line: Any = _Pair_Record_Line(
                    link,
                    name,
                    )
            type.__setattr__(link, name, line)
            line.__set_name__(link, name)
        else:
            type.__setattr__(
                    link,
                    name,
                    _line_action(
                            link,
                            name,
                            ),
                    )

    _invalidate_declarations(link)


def _line_action(
        link: type,
        name: str,
        ) -> Function:
    link_reference = weakref.ref(link)

    def Line(
            contact: object,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        pair = _line_pair(
                link_reference,
                contact,
                name,
                "Pair Action",
                )
        state = _state_of(contact)
        opened = state.composing
        state.composing = 0   # the Contact's door stays shut on every path (rule 3.6)

        try:
            return getattr(pair, name)(
                    *args,
                    **kwargs,
                    )
        finally:
            state.composing = opened

    Line.__name__ = name
    Line.__qualname__ = f"{link.__qualname__}.{name}"
    Line.__doc__ = f"A line from a {link.__name__} Pair: its {name}."

    return Line


def _line_pair(
        link_reference: weakref.ref,
        contact: object,
        name: str,
        kind: str,
        ) -> Pair:
    """The Pair a line reaches. A published member answers members only
    (§1.5): once unlinked, the line raises a Rogue Access Failure."""

    link = link_reference()

    if link is None:
        raise TagRogueAccessError(
                f"{name!r} was published by a Link that no longer exists"
                )

    _require_membership(
            contact,
            link,
            name,
            kind,
            )
    pair = _record_of(link).family.Pair_Of(contact)

    if pair is None:
        raise TagRogueAccessError(
                f"{name!r} is a published {kind} of {link.__name__}; this"
                " Contact holds no Pair of it"
                )

    return pair


def _no_builder(
        link: type,
        ) -> None:
    return None


class _Pair_Record_Line(Report, _Line):
    """A ``@Public`` Pair Record, read on the Contact: read-only there,
    and read live from her Pair."""

    def __init__(
            line,
            link: type,
            name: str,
            ) -> None:
        Report.__init__(
                line,
                _no_builder,
                )
        line.public = True
        line.__name__ = name
        line._link = weakref.ref(link)
        line._member = name

    def __get__(
            line,
            instance: object,
            owner: type | None = None,
            ) -> Any:
        return line   # on the Link itself it is a line, not a value

    def Read(
            line,
            contact: object,
            ) -> Any:
        pair = _line_pair(
                line._link,
                contact,
                line._member,
                "Pair Record",
                )

        return getattr(
                pair,
                line._member,
                )

    def __repr__(
            line,
            ) -> str:
        return (
                f"<Pair Record {line._member}: read it on a Pair,"
                f" agent.Link[contact].{line._member}>"
                )


# ------------------------------------------------------------------
# Extending a held Link (rule 4.6)
# ------------------------------------------------------------------


def _extend(
        link: type,
        record: _Link_Record,
        added: list[type],
        ) -> None:
    """A Shape of the declaring Tag extends a held Link with new Layers.

    Inside the Agent's call, as a tagging of every Pair the Link holds:
    every Pair's gate and Parts now (one refusal refuses the whole call,
    nothing changed); their Imprints and promises after the Agent's
    Commit. Linkings made after that get every Layer."""

    _refuse_while_busy(
            record.family,
            f"{link.__name__} gains no Layer",
            )
    _refuse_mixed_layers(
            [*record.layers, *added],
            link.__name__,
            TagCompositionError,
            )
    boundary = _open_boundary()
    field = link.__dict__["_topkit_field"]
    pairs = [
            pair
            for contact in field
            if (pair := record.family.Pair_Of(contact)) is not None
            ]
    form = _pair_tags_of(added)
    entries = [
            (
                pair,
                _capture(pair),
                )
            for pair in pairs
            ]
    previous_layers = list(record.layers)
    previous_gained = dict(record.gained)
    previous_members = {
            name: link.__dict__.get(name, _MISSING)
            for relation in added
            for name in (*_tag_scope_of(relation), *_published_names(relation))
            }
    written: list[tuple[Pair, list[Any]]] = []
    given: dict[int, list[type]] = {}   # the Pair Tags this extension gave each Pair, once its Parts are done
    settled: dict[int, dict[str, Any]] = {}   # each Pair's values once its Imprints ran

    def Undo() -> None:
        for pair, entry in reversed(entries):
            if id(pair) not in given:
                _rollback_to(
                        pair,
                        entry,
                        )   # not reached yet, or refused: as it was
                continue

            _undo_pair_layers(
                    pair,
                    entry,
                    given[id(pair)],
                    settled.get(id(pair)),
                    )   # a Pair dropped since stays dropped; what other calls gave it stays

        record.layers[:] = previous_layers
        record.gained = previous_gained
        _forget_pair_forms(record.family)

        for name, value in previous_members.items():
            if value is _MISSING:
                if name in link.__dict__:
                    type.__delattr__(link, name)
            else:
                type.__setattr__(link, name, value)

        _invalidate_declarations(link)

    record.family.busy += 1   # until every Pair has the Layer, the family gains no other

    try:
        record.layers.extend(added)

        for relation in added:
            record.gained[relation] = next(_gaining)

        _forget_pair_forms(record.family)

        for relation in added:
            for name, member in _tag_scope_of(relation).items():
                type.__setattr__(link, name, member)

                if isinstance(member, Report):
                    member.__set_name__(link, name)

            _publish_lines(
                    link,
                    relation,
                    )

        for pair in pairs:
            _gate_form(
                    pair,
                    form,
                    {},
                    )   # every Pair's gate first: one refusal refuses the whole call

        for pair, entry in entries:
            deferred: list[Any] = []
            _apply_form(
                    pair,
                    form,
                    {},
                    deferred,
                    gated=True,
                    )
            given[id(pair)] = _added_since(
                    pair,
                    entry,
                    )
            written.append(
                    (
                        pair,
                        deferred,
                        )
                    )
    except BaseException:
        Undo()
        raise
    finally:
        record.family.busy -= 1

    def Write() -> None:
        try:
            _write_all(
                    written,
                    {},
                    )
        finally:
            for pair, _deferred in written:
                namespace = _namespace_of(pair)

                if namespace is not None:
                    settled[id(pair)] = dict(namespace)

    if boundary is None:
        Write()
        return

    boundary.undo.append(_Undo_Step(
            (record.agent(),),
            Undo,
            ))
    boundary.writes.append(Write)


def _published_names(
        relation: type,
        ) -> list[str]:
    return [
            name
            for name, member in relation.__dict__.items()
            if _is_pair_member(name, member) and _has_flag(member, _PUBLIC)
            ]


def _pair_tags_of(
        relations: list[type],
        ) -> list[type]:
    """The Pair Tags for ``relations``, Bases first, each once."""

    form: list[type] = []

    for relation in relations:
        for pair_tag in _form_of(_pair_tag(relation)):
            if pair_tag not in form:
                form.append(pair_tag)

    return form


def _pair_form(
        link: type,
) -> list[type]:
    """Every Pair Tag a linking through ``link`` gives: the Layers of each
    Link in its Form (rules 5.2 and 5.3), in the order the Agent gained
    them. That is Form order, with a later extension on top, which is
    where an extension lands on the Pairs it already holds (rule 4.6). A
    Pair already held receives the Layers it lacks on top of what it
    carries (§1.2, latest Layer). Kept on the record until a Layer is
    added to any Link of the family: a new list then."""

    record = _record_of(link)

    if record.pair_form is not None:
        return record.pair_form

    gained: list[tuple[int, type]] = []

    for member in _form_of(link):
        member_record = _record_of(member)

        for relation in member_record.layers:
            gained.append(
                    (
                        member_record.gained[relation],
                        relation,
                        )
                    )

    gained.sort(key=_gaining_number)
    relations: list[type] = []

    for _number, relation in gained:
        if relation not in relations:
            relations.append(relation)

    record.pair_form = _pair_tags_of(relations)

    return record.pair_form


def _gaining_number(
        entry: tuple[int, type],
        ) -> int:
    return entry[0]


def _forget_pair_forms(
        family: "_Family",
        ) -> None:
    for link in family.Links():
        _record_of(link).pair_form = None


def _write_all(
        written: list[tuple[Pair, list[Any]]],
        inputs: dict[str, Any],
        ) -> None:
    """Every Pair's Imprints, then every Pair's promises; the first
    failure is raised, and the Layers stay."""

    first: BaseException | None = None

    for pair, deferred in written:
        try:
            _write(
                    pair,
                    deferred,
                    inputs,
                    )
        except Exception as error:
            first = first or error

    for pair, _deferred in written:
        try:
            _inspect(pair)
        except Exception as error:
            first = first or error

    try:
        if first is not None:
            raise first
    finally:
        first = None   # never keep Agents alive through a traceback that holds this frame


def _write(
        pair: Pair,
        deferred: list[Any],
        inputs: dict[str, Any],
        ) -> None:
    state = _state_of(pair)
    state.composing += 1

    try:
        for declarations in deferred:
            _imprint(
                    pair,
                    declarations,
                    inputs,
                    )
    finally:
        state.composing -= 1


# ------------------------------------------------------------------
# Linking (rule 5.1)
# ------------------------------------------------------------------


def _link(
        link: type,
        contact: object,
        inputs: dict[str, Any],
        ) -> object:
    """``charlie.Knows(ruth, **inputs)``: a tagging of the Contact, with
    the Pair as receiver. The Pair's gate; the Pair's Records; the Contact
    enters the Link's Field; the Pair's Imprints; the Pair's promises and
    the Contact's own. A failure up to her entry changes nothing; after
    it, the failure raises and the linking stays."""

    record = _record_of(link)
    agent = _agent_of(
            link,
            record,
            )
    _refuse_contact(
            link,
            contact,
            )
    contact_state = _state_of(contact)
    pending = [
            member
            for member in _form_of(link)
            if contact_state is None or member not in contact_state.active
            ]

    if not pending:
        return contact   # reapplying is a no-op (rule 5.4)

    form = _pair_form(link)
    _refuse_inputs_in_seats(
            form,
            inputs,
            )
    family = record.family
    pair = family.Pair_Of(contact)
    created = pair is None

    if created:
        pair = family.New_Pair(
                agent,
                contact,
                record.name,
                )

    outer = _open_boundary()   # a call this linking is part of (rule 5.6)
    local = _Call_Boundary()   # nested linkings made at the Pair's Parts report here
    pair_entry = _capture(pair)
    contact_entry = _capture(contact) if outer is not None else None
    deferred: list[Any] = []

    applied: list[list[type]] = []   # the Pair Tags this linking gave the Pair, once its Parts are done
    settled: list[dict[str, Any]] = []   # the Pair's values once the linking is done, Imprints included

    def Drop_Pair() -> None:
        if not created:
            given = applied[0] if applied else _added_since(pair, pair_entry)   # a failure during its Parts: all of it is this linking's
            _undo_pair_layers(
                    pair,
                    pair_entry,
                    given,
                    settled[0] if settled else None,
                    )   # an older Pair keeps what other calls gave it since
            return

        _rollback_to(
                pair,
                pair_entry,
                )   # a new Pair loses its state, so its teardowns never run (rule 8.5)
        current = object.__getattribute__(pair, "__dict__")[_PAIR_ENDS].family   # a join may have moved it

        if current.pairs.get(id(contact)) is pair:
            del current.pairs[id(contact)]

    token = _current_boundary.set(local)
    family.busy += 1   # until her entry, the family gains no Layer (rule 4.6)

    try:
        try:
            _apply_form(
                    pair,
                    form,
                    inputs,
                    deferred,
                    )
            applied.append(_added_since(
                    pair,
                    pair_entry,
                    ))
            _apply_form(
                    contact,
                    pending,
                    {},
                    [],
                    )   # a refusal rolls the Contact back by itself
        except BaseException:
            try:
                _undo_refused_linking(
                        local,
                        agent,
                        contact,
                        outer,
                        )   # its own linkings at the Pair's Parts, latest first
            finally:
                Drop_Pair()

            raise
    finally:
        family.busy -= 1
        _current_boundary.reset(token)
        local.open = False   # a task that copied this context links on its own from now on

    _hook(
            contact,
            pending,
            )

    if outer is not None:
        def Undo() -> None:
            _undo_linking(
                    contact,
                    contact_entry,
                    pending,
                    )
            Drop_Pair()

        _hand_over(
                local,
                outer,
                )
        outer.undo.append(_Undo_Step(
                (agent, contact),
                Undo,
                linking=True,
                ))

    _close(local)

    try:
        _write(
                pair,
                deferred,
                inputs,
                )
    finally:
        settled.append(dict(_namespace_of(pair)))   # whatever the Imprints do, the linking stays (§0.6)
    _inspect(pair)
    _inspect(contact)

    return contact


def _added_since(
        pair: Pair,
        entry: Any,
        ) -> list[type]:
    state = _state_of(pair)

    if state is None:
        return []

    return [
            tag
            for tag in state.active
            if tag not in entry.tags
            ]


def _undo_pair_layers(
        pair: Pair,
        entry: Any,
        applied: list[type],
        settled: dict[str, Any] | None,
        ) -> None:
    """Take back from a Pair that existed before the linking only the
    Pair Tags the linking applied. When nothing else reached the Pair
    since (its Tags, its history and its values are what the linking
    left), its snapshot is restored. Otherwise those Tags leave it as an
    unlinking leaves it, silently and with no teardown, their history
    forgotten and what they gave sticky (§0.7), and what other calls gave
    it or wrote on it stays."""

    state = _state_of(pair)

    if state is None or entry.state is None:
        return

    untouched = (
            list(state.active) == [*entry.tags, *applied]
            and state.ever == entry.state.ever | set(applied)
            and (settled is None or _same_values(_namespace_of(pair), settled))
            )

    if untouched:
        _rollback_to(
                pair,
                entry,
                )
        return

    for tag in reversed(applied):
        if tag in state.ever and tag not in entry.state.ever:
            state.ever.discard(tag)

        if tag in state.active:
            state.active.remove(tag)

        tag.__dict__["_topkit_field"]._Remove(pair)
        state.rips.pop(tag, None)
        state.snapshots.pop(tag, None)

    state.words = None


def _same_values(
        namespace: dict[str, Any],
        settled: dict[str, Any],
        ) -> bool:
    """The very same values under the very same names."""

    if namespace.keys() != settled.keys():
        return False

    return all(
            namespace[name] is settled[name]
            for name in namespace
            )


def _undo_linking(
        contact: object,
        entry: Any,
        links: list[type],
        ) -> None:
    """A linking undone with the call it was part of (rule 5.6) takes back
    only what it gave her: she leaves these Links silently, with no
    teardown, and her history of them is forgotten. Everything else she
    gained or did since stays. The lines they published stay on her,
    sticky, and answer no more, as after an unlink. If she was no Agent
    before and holds nothing else, she is a plain object again."""

    state = _state_of(contact)

    if state is None:
        return

    for link in reversed(links):
        if link in state.active:
            state.active.remove(link)

        link.__dict__["_topkit_field"]._Remove(contact)
        state.rips.pop(link, None)
        state.snapshots.pop(link, None)

        if state.ever_links is not None and not _was_in(link, entry):
            state.ever_links.discard(link)   # the history this linking gave her; an earlier one stays

    state.words = None

    if entry.state is None and _holds_only_lines(state):
        _forget_agent(
                contact,
                state,
                entry,
                )


def _was_in(
        link: type,
        entry: Any,
        ) -> bool:
    """She was a Contact of this Link before the call began."""

    if entry.state is None or entry.state.ever_links is None:
        return False

    return link in entry.state.ever_links


def _holds_only_lines(
        state: _State,
        ) -> bool:
    """Nothing on her but what Links published: no Tag, no history, no
    Record, no condition, no teardown."""

    if state.active or state.ever or state.ever_links:
        return False

    if state.records or state.preconditions or state.postconditions or state.rips:
        return False

    return all(
            _is_link(origin)
            for origin in state.action_origins.values()
            ) and all(
            _is_link(origin)
            for origin, _report in state.reports.values()
            )


def _forget_agent(
        contact: object,
        state: _State,
        entry: Any,
        ) -> None:
    """She was no Agent before the undone linking: she is a plain object
    again, with whatever plain values she holds. A value she held before
    under a line's name comes back, as a rollback gives it back."""

    namespace = _namespace_of(contact)

    for name in state.actions:
        bound = namespace.get(name)

        if not (isinstance(bound, _Bound) and bound._reference() is contact):
            continue   # a value she wrote since stays, another Agent's Action included

        if name in entry.namespace:
            namespace[name] = entry.namespace[name]   # her own value, which the line covered
        else:
            namespace.pop(name, None)   # the line bound on her

    namespace.pop(STATE, None)

    if type(contact) is not entry.host_class:
        _set_runtime_type(
                contact,
                entry.host_class,
                )


def _agent_of(
        link: type,
        record: _Link_Record,
        ) -> object:
    if record.ending:
        raise TagCompositionError(
                f"this {link.__name__} is ending with its Agent; nothing is"
                " linked through it now"
                )

    agent = record.agent()

    if agent is None or record.ended:
        raise TagCompositionError(
                f"this {link.__name__}'s Agent no longer exists; nothing is"
                " linked through it"
                )

    return agent


def _refuse_contact(
        link: type,
        contact: object,
        ) -> None:
    if contact is None:
        raise TagCompositionError(
                f"{link.__name__} links a Contact: an object, never None"
                )

    if isinstance(contact, type):
        raise TagCompositionError(
                f"{link.__name__} links objects, not classes; Links between"
                " Tags need their own receiver rule"
                )

    if _namespace_of(contact) is None:
        raise TagCompositionError(
                f"{type(contact).__name__} cannot carry TOP state (no instance"
                f" dictionary), so it cannot be a Contact of {link.__name__}"
                )

    try:
        weakref.ref(contact)
    except TypeError as error:
        raise TagCompositionError(
                "Contacts must support weak references: a Link's Field never"
                " keeps its Contacts alive"
                ) from error


def _refuse_inputs_in_seats(
        form: list[type],
        inputs: dict[str, Any],
        ) -> None:
    """An input never fills a seat (rule 3.4)."""

    if not inputs:
        return

    for pair_tag in form:
        for name, seats in _seats_of(pair_tag):
            taken = sorted(seats & inputs.keys())

            if taken:
                raise TagDeclarationError(
                        f"{pair_tag.__qualname__}.{name}: the input"
                        f" {taken[0]!r} is named like one of its seats; take"
                        " inputs by name after `*`:"
                        f" def {name}(agent, contact, *, {taken[0]})"
                        )


_seats: "WeakKeyDictionary[type, tuple[tuple[str, frozenset[str]], ...]]" = WeakKeyDictionary()


def _seats_of(
        pair_tag: type,
        ) -> tuple[tuple[str, frozenset[str]], ...]:
    """The seats of each Pair function that takes inputs, by name."""

    cached = _seats.get(pair_tag)

    if cached is None:
        cached = tuple(
                (
                    name,
                    member._topkit_seats,
                    )
                for name, member in pair_tag.__dict__.items()
                if _kind_of(member) in _TAKES_INPUTS
                and hasattr(member, "_topkit_seats")
                )
        _seats[pair_tag] = cached

    return cached


def _hook(
        contact: object,
        links: list[type],
) -> None:
    """Each Link the Contact entered gets its teardown on her: leaving it,
    by Rip or by her deletion, runs the Pair's teardowns (rules 8.1, 8.4).
    It is a teardown and not an Action: nothing callable lands on her."""

    state = _state_of(contact)

    for link in links:
        record = _record_of(link)

        if record.hook is None:
            record.hook = _leaving(link)

        state.rips[link] = ((link.__name__, record.hook),)   # (name, teardown), as an ordinary Tag's Rips


def _leaving(
        link: type,
        ) -> Function:
    """The Contact's teardown for one Link. It holds the Link strongly:
    in a reference cycle the language clears weak references before any
    finalizer runs, and the Link already keys this teardown on her."""

    def Unlink(
            contact: object,
            ) -> None:
        _leave(
                link,
                contact,
                )

    Unlink.__name__ = "Unlink"

    return Unlink


# ------------------------------------------------------------------
# The Pair, read through the Link (rule 7.1)
# ------------------------------------------------------------------


def _pair_of(
        link: type,
        contact: object,
        ) -> Pair:
    """``charlie.Knows[ruth]``: the Pair, live. It needs a linking, not
    active membership: it lives until the Link's teardowns have run."""

    record = link.__dict__.get(_RECORD)
    pair = None if record is None else record.family.Pair_Of(contact)

    if pair is None:
        raise TagResolutionError(
                f"{type(contact).__name__} is not a Contact of this"
                f" {link.__name__}; it holds no Pair of hers"
                )

    return pair


def _contact_holds(
        link: type,
        ) -> Callable[[object], bool]:
    """The sound Contacts: those whose own contract holds and whose Pair
    holds (rule 7.3). A broken Pair never makes her defective elsewhere."""

    from .contracts import _holds

    record = _record_of(link)

    def Holds(
            contact: object,
            ) -> bool:
        if not _holds(contact):
            return False

        pair = record.family.Pair_Of(contact)

        return pair is None or _holds(pair)

    return Holds


# ------------------------------------------------------------------
# Ending (section 8)
# ------------------------------------------------------------------


def _leave(
        link: type,
        contact: object,
        ) -> None:
    """One Contact leaves one Link: the Pair's teardowns of that Link's
    Layers run with ``(agent, contact)``. Then the Pair ends, unless
    another Link of the same family still holds her (rule 8.1): what the
    Ripped Link gave the Pair stays on it, sticky. When the Link's Agent
    cannot be reached, the Pair ends silently (rule 8.4)."""

    record = _record_of(link)
    family = record.family
    pair = family.Pair_Of(
            contact,
            leaving=True,
            )

    if pair is None:
        return

    state = _state_of(contact)
    agent = record.agent()

    if agent is None:
        agent = family.dying

    if agent is None:
        family.End(contact)
        return

    ends: _Ends = object.__getattribute__(pair, "__dict__")[_PAIR_ENDS]
    pair_state = _state_of(pair)
    first: BaseException | None = None
    ends.held = (
            agent,
            contact,
            )
    opened = state.composing
    state.composing = 0   # her door stays shut, even inside her own finalizer (rule 3.6)

    try:
        for relation in reversed(record.layers):
            pair_tag = _pair_tag(relation)

            if pair_state is None or pair_tag not in pair_state.active:
                continue

            try:
                _rip(
                        pair,
                        pair_tag,
                        )   # runs that Layer's teardowns, with the Pair
            except TagCompositionError as error:
                first = first or error
    finally:
        ends.held = None
        state.composing = opened

        if not _still_held(
                family,
                state,
                ):
            family.End(contact)   # asked after the teardowns, even an interrupted one: one may have linked her again (rule 5.7)

    try:
        if first is not None:
            raise first
    finally:
        first = None   # never keep Agents alive through a traceback that holds this frame


def _still_held(
        family: _Family,
        state: _State,
        ) -> bool:
    """A Link of the family still holds her: active, with its teardown
    still due on her."""

    return any(
            link in state.active
            and link in state.rips
            for link in family.Links()
            )


def _unlink_all(
        link: type,
        key: slice,
        ) -> None:
    """``del charlie.Knows[:]``: unlink every Contact (rule 8.2). Refused,
    nothing changed, while a Shape Link still holds any of them (§0.7);
    every teardown runs, and the first failure is raised after."""

    if key != slice(None):
        raise TypeError(
                "Link[:] is the whole Field; positional slices have no"
                " meaning for a population"
                )

    contacts = list(link.__dict__["_topkit_field"])
    held = [
            contact
            for contact in contacts
            if _requiring_shapes(link, _state_of(contact).active)
            ]

    if held:
        raise TagCompositionError(
                f"{link.__name__} is required by an active Shape Link for"
                f" {len(held)} of its Contacts; unlink them from the Shape"
                " first"
                )

    first: BaseException | None = None

    for contact in contacts:
        if link not in _state_of(contact).active:
            continue   # an earlier Contact's teardown already unlinked her

        try:
            _rip(
                    contact,
                    link,
                    )
        except TagCompositionError as error:
            first = first or error

    contacts = held = None   # the Contacts are not ours to keep

    try:
        if first is not None:
            raise first
    finally:
        first = None   # never keep Agents alive through a traceback that holds this frame


def _own_records(
        state: _State,
        ) -> list[_Link_Record]:
    """The records of the Agent's own Links, Shape Links first."""

    records = []

    for name in reversed(list(state.links)):
        link = state.links[name][0]

        if link is None:
            continue

        record = link.__dict__.get(_RECORD)

        if record is not None and not record.ended:
            records.append(record)

    return records


def _begin_ending(
        agent: object,
        state: _State,
        ) -> None:
    """The Agent's finalizer holds it: from now on it fills the first seat
    of its own Links, even when the language has already cleared every
    weak reference to it (a reference cycle, rule 8.3). Its own
    teardowns, its exits from Links that hold it included, run next."""

    for record in _own_records(state):
        record.family.dying = agent


def _end_links(
        agent: object,
        state: _State,
        ) -> None:
    """The Agent's deletion ends its Links (rule 8.3): after its own
    teardowns, each Link's Field is Ripped, Shape Links before their
    Bases, with the dying Agent in the first seat. Best effort, as every
    teardown at deletion is (§3.2). Linking through them is refused from
    then on."""

    records = _own_records(state)
    interrupted: BaseException | None = None

    try:
        for record in records:
            record.family.dying = agent
            record.ending = True

        for name in reversed(list(state.links)):
            link = state.links[name][0]

            if link is None or link.__dict__.get(_RECORD) not in records:
                continue

            for contact in list(link.__dict__["_topkit_field"]):
                try:
                    _rip(
                            contact,
                            link,
                            )
                except Exception:
                    pass   # best effort (§3.2)
                except BaseException as error:
                    interrupted = interrupted or error   # every other Contact still leaves (rule 8.3)
    finally:
        for record in records:
            record.family.dying = None
            record.ending = False
            record.ended = True

    try:
        if interrupted is not None:
            raise interrupted
    finally:
        interrupted = None   # never keep Agents alive through a traceback that holds this frame


__all__ = [
        "Link",
        ]
