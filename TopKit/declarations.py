"""Declarations: the marks an author puts on a Tag, and how they are read.

Agent scope:  @Action, @Record          (external by default, @Secret hides)
Tag scope:    @Operation, @Report     (internal by default, @Public publishes)
Protocols:    @Imprint, @Pre, @Post, @Rip, @Delete
Composition:  @Underlay                 (extend the prior visible contribution)
Protection:   @Constant                 (keep a contribution's binding fixed)

A Tag class is scanned once; the result is cached per class.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from dataclasses import field
from dataclasses import replace
from functools import cached_property
from functools import partialmethod
from inspect import Parameter
from inspect import getattr_static
from inspect import signature
from types import AsyncGeneratorType
from types import CoroutineType
from types import GeneratorType
from types import MethodType
from typing import Any
from typing import Callable
from typing import NamedTuple
from weakref import WeakKeyDictionary
from weakref import ref

from .arrest import _require_available
from .arrest import _safehouse
from .errors import TagDeclarationError
from .errors import TagCompositionError
from .errors import TagImprintError
from .errors import TagPostconditionError
from .errors import TagPreconditionError
from .geometry import _is_tag_class
from .lazy_guard import _guard_lazy_result
from .memo import _forget_memo
from .memo import _memo_key
from .memo import _memo_of
from .memo import _namespace_snapshot
from .memo import _remember_memo


_KIND = "__topkit_kind__"
_UNDERLAY = "__topkit_underlay__"
_RIP = "__topkit_rip__"
_SECRET = "__topkit_secret__"
_PUBLIC = "__topkit_public__"
_FLAG = "__topkit_flag__"
_PIN = "__topkit_pin__"
_CONSTANT = "__topkit_constant__"
_TOOL = "__topkit_tool__"   # a Record's kind: the Tags its slot admits (tools._Kind)
_ACTION_CHAIN = "__topkit_action_chain__"

STATE = "_TOPKIT_STATE"

_flags_declared = 0   # counts every @Flag, so an Agent's gathered words know when they are stale

_MISSING = object()

Function = Callable[..., Any]


class _Lazy_Rip_Guard:
    """Failures found inside composed Rip Underlays during one teardown."""

    __slots__ = (
            "active",
            "chain",
            "failures",
            "name",
            )

    def __init__(
            guard,
            name: str,
            chain: object | None,
            ) -> None:
        guard.active = True
        guard.chain = chain
        guard.failures: list[TagCompositionError] = []
        guard.name = name


_lazy_rip_guard: ContextVar[_Lazy_Rip_Guard | None] = ContextVar(
        "topkit_lazy_rip_guard",
        default=None,
        )


def _action_chain(function: Function) -> object | None:
    """Optional composition metadata cannot invalidate an accepted callable."""

    try:
        return getattr(function, _ACTION_CHAIN, None)
    except Exception:
        return None


# ------------------------------------------------------------------
# Marks
# ------------------------------------------------------------------


_CONDITION_KINDS = ("precondition", "postcondition", "condition")


def _mark(
        function: Function,
        kind: str,
        ) -> Function:
    """Mark a function with its kind. ``@Pre`` and ``@Post`` stacked on one
    function make it a *condition*: necessary to enter and to stay."""

    existing = getattr(
            function,
            _KIND,
            None,
            )

    if (
            existing is not None
            and existing != kind
            and existing in _CONDITION_KINDS
            and kind in _CONDITION_KINDS
            ):
        kind = "condition"

    setattr(
            function,
            _KIND,
            kind,
            )

    return function


def _flag(
        target: Any,
        name: str,
        ) -> Any:
    if isinstance(target, Report):
        function = target.builder
    else:
        function = getattr(
                target,
                "__func__",
                target,
                )
    setattr(
            function,
            name,
            True,
            )

    return target


def Action(
        function: Function,
        ) -> Function:
    """Agent behaviour. A bare method on a Tag is already an Action; this
    is the explicit, stackable spelling."""

    return _mark(
            function,
            "action",
            )


def Record(
        function: Function,
        ) -> Function:
    """Agent state. The builder runs at tagging and its value is stored on
    the Agent. A second positional parameter receives the value already
    stored under that name, or None when there is none::

        @Record
        def spells(agent, stored):
            return (stored or []) + ["Fireball"]
    """

    return _mark(
            function,
            "record",
            )


def Underlay(
        function: Function,
        ) -> Function:
    """Extend the prior visible contribution of the same name.

    For an Action or a condition the second positional parameter receives a
    callable that runs the prior contribution. For a Record the second
    positional parameter receives the stored value (the mark is optional
    there; the parameter alone is enough).
    """

    return _flag(
            function,
            _UNDERLAY,
            )


def Constant(
        member: Any,
        ) -> Any:
    """Keep a Contribution's binding fixed after it is established.

    Records keep their initial binding; their values may still be mutable.
    Actions and Posts cannot be replaced or deleted. Constant Reports
    keep the declaring Tag's value, shared by its Shapes, and Constant
    Operations keep their implementation. Stacks with the declaration's
    other modifiers in either order.
    """

    target = member.builder if isinstance(member, Report) else getattr(
            member,
            "__func__",
            member,
            )

    if not callable(target):
        raise TagDeclarationError(
                "@Constant marks a Record, Action, Post, Report or Operation"
                )

    return _flag(member, _CONSTANT)


def Rip(
        function: Any,
        ) -> Any:
    """Teardown. Runs when the Agent leaves the Tag's Field. It is also a
    normally callable Action."""

    if isinstance(function, property):
        raise TagDeclarationError(
                "@Rip cannot mark a property; @Rip marks an Action because"
                " a teardown is also callable as an Action"
                )

    return _flag(
            function,
            _RIP,
            )


class _Check_Mark:
    """A mark for a named check: Imprint, Precondition, Postcondition.

    Called, it marks the function. Read as a namespace, it names the
    failure of one check: ``Precondition.Is_A_Caster`` is the error raised
    when the Precondition declared as ``Is_A_Caster`` refuses, so a program
    writes ``except Precondition.Is_A_Caster:`` in its own words.
    """

    def __init__(
            mark,
            kind: str,
            failure: type,
            doc: str,
            ) -> None:
        mark.kind = kind
        mark.failure = failure
        mark.__name__ = kind.capitalize()
        mark.__doc__ = doc

    def __call__(
            mark,
            function: Function,
            ) -> Function:
        return _mark(
                function,
                mark.kind,
                )

    def __getattr__(
            mark,
            name: str,
            ) -> type:
        return getattr(
                mark.failure,
                name,
                )

    def __repr__(
            mark,
            ) -> str:
        return f"<TopKit mark @{mark.__name__}>"


Imprint = _Check_Mark(
        "imprint",
        TagImprintError,
        "Training performed after Gainings and before Field admission.",
        )


Precondition = _Check_Mark(
        "precondition",
        TagPreconditionError,
        "A gate on the incoming Agent. Evaluated before the Tag applies.",
        )

Postcondition = _Check_Mark(
        "postcondition",
        TagPostconditionError,
        "A promise about the finished Agent. Evaluated after every Tagging.",
        )


Pre = Precondition
Post = Postcondition


def Delete(
        function: Function,
        ) -> Function:
    """Remove a visible contribution (or host member) by name."""

    return _mark(
            function,
            "delete",
            )


def _call_tag_operation(
        function: Function,
        tag: type,
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    """Check a Tag's custody around its own Operation and later work."""

    if _safehouse:
        _require_available(tag, "Operation")

    result = function(tag, *args, **kwargs)
    return _guard_lazy_result(result, tag, "Operation", _require_available)


class _Operation_Bound:
    """A Tag Operation handle that remains revocable after capture."""

    __slots__ = ("_function", "_tag", "_name")

    def __init__(
            bound,
            function: Function,
            tag: type,
            name: str,
            ) -> None:
        bound._function = function
        bound._tag = tag
        bound._name = name

    def __call__(bound, *args: Any, **kwargs: Any) -> Any:
        tag = bound._tag
        if _safehouse:
            _require_available(tag, "Operation")

        result = bound._function(tag, *args, **kwargs)
        return _guard_lazy_result(result, tag, "Operation", _require_available)

    def __eq__(bound, other: object) -> Any:
        if isinstance(other, _Operation_Bound):
            other = MethodType(other._function, other._tag)

        return MethodType(bound._function, bound._tag).__eq__(other)

    def __hash__(bound) -> int:
        return hash(MethodType(bound._function, bound._tag))

    def __repr__(bound) -> str:
        return f"<Operation {bound._name} of {bound._tag.__name__}>"

    @property
    def __self__(bound) -> type:
        return bound._tag

    @property
    def __func__(bound) -> Function:
        return bound._function

    @property
    def __signature__(bound) -> Any:
        return signature(MethodType(bound._function, bound._tag))

    @property
    def __name__(bound) -> str:
        try:
            name = getattr(bound._function, "__name__", None)
        except Exception:
            name = None
        return name if isinstance(name, str) else bound._name

    @property
    def __doc__(bound) -> str | None:
        try:
            return getattr(bound._function, "__doc__", None)
        except Exception:
            return None


class _Guarded_Operation(classmethod):
    """The classmethod source, returning a guarded bound handle."""

    def __set_name__(operation, owner: type, name: str) -> None:
        operation._name = name

    def __get__(
            operation,
            instance: object,
            owner: type | None = None,
            ) -> _Operation_Bound:
        if owner is None:
            owner = type(instance)

        return _Operation_Bound(
                operation.__func__,
                owner,
                getattr(operation, "_name", "Operation"),
                )


def Operation(
        function: Function,
        ) -> classmethod:
    """Tag behaviour. The Tag is its first input."""

    _mark(
            function,
            "operation",
            )

    return _Guarded_Operation(function)


def Secret(
        function: Function,
        ) -> Function:
    """Hide an Action or Record from code outside composition."""

    return _flag(
            function,
            _SECRET,
            )


def Public(
        member: Any,
        ) -> Any:
    """Publish a Report or Operation on the Agent: a Report as a read-only
    name, an Operation as an Action that forwards to it with the Agent as
    its second input. Stacks with ``@Report`` / ``@Operation`` in either
    order."""

    if isinstance(member, Report):
        member.public = True

        return member

    return _flag(
            member,
            _PUBLIC,
            )


def Flag(
        *words: type | str,
        ) -> Any:
    """Mark a Tag as a keyword: searchable from the Agent's side by name
    or by class, ``"Undead" in ghoul`` and ``Undead in ghoul``.

    With words, the Tag answers to those too (STEP-SPEC-17)::

        @Flag("Wolf", "Lycanthrope")
        class Werewolf(Tag): ...

    The Tag's own name is always a word. An alias is only a word: it
    answers ``"Wolf" in agent``, never membership. Applying a Flag to a
    host that defines its own ``in`` is refused.
    """

    if len(words) == 1 and isinstance(words[0], type):
        return _mark_flag(
                words[0],
                frozenset(),
                )

    for word in words:
        if not isinstance(word, str) or not word:
            raise TagDeclarationError(
                    "@Flag marks a Tag class, or takes the words it also"
                    f" answers to as non-empty strings; got {word!r}"
                    )

    aliases = frozenset(words)

    def Flag_With_Words(
            tag: type,
            ) -> type:
        return _mark_flag(
                tag,
                aliases,
                )

    return Flag_With_Words


def _mark_flag(
        tag: type,
        aliases: frozenset[str],
        ) -> type:
    if not _is_tag_class(tag):
        raise TagDeclarationError(
                "@Flag marks a Tag class"
                )

    for name in (
            "__contains__",
            "__iter__",
            ):
        member = tag.__dict__.get(name)

        if (
                callable(member)
                and not isinstance(member, (classmethod, staticmethod))
                and _kind_of(member) in (None, "action")
                ) or (
                isinstance(member, classmethod)
                and _has_flag(member, _PUBLIC)   # a published Operation is an Action on the Agent
                ):
            raise TagDeclarationError(
                    f"{tag.__name__} is a Flag and needs the Agent's `in` for"
                    f" its words, but its Action {name} would answer `in`"
                    " too; a Flag cannot hold both"
                    )

    global _flags_declared

    setattr(
            tag,
            _FLAG,
            tag.__dict__.get(_FLAG, frozenset()) | aliases,
            )
    _flags_declared += 1

    return tag


class _Words(NamedTuple):
    """What an Agent's Flags answer to, gathered once until its Tags change."""

    flags_declared: int          # the count of @Flag marks when these were gathered
    flags: tuple[type, ...]      # the active Flags; their names are read live
    aliases: frozenset[str]      # every word they list


def _words_of(
        active: list[type],
        flags_declared: int,
        ) -> _Words:
    """The active Flags and every alias they list. Their names are not
    kept: they are read at each question, so a renamed Tag answers to its
    new name."""

    flags = []
    aliases: set[str] = set()

    for tag in active:
        listed = tag.__dict__.get(_FLAG)

        if listed is not None:
            flags.append(tag)
            aliases.update(listed)

    return _Words(
            flags_declared,
            tuple(flags),
            frozenset(aliases),
            )


def _is_flag(
        tag: type,
        ) -> bool:
    return tag.__dict__.get(_FLAG) is not None


def Pin(
        tag: type,
        ) -> type:
    """Mark a Tag whose Targets are Tags (STEP-SPEC-9).

    ``Rare(Wizard)`` makes the Tag ``Wizard`` an Agent of ``Rare``: its
    Records land on ``Wizard`` as Reports, its Actions as Operations, and
    the Field of ``Rare`` is a population of Tags. A Pin applies to
    nothing else, and its Bases must be Pins.
    """

    if not _is_tag_class(tag):
        raise TagDeclarationError(
                "@Pin marks a Tag class"
                )

    _refuse_tools_on_a_pin(
            tag,
            _namespace_snapshot(tag),
            )
    setattr(
            tag,
            _PIN,
            True,
            )

    _check_pin_bases(tag)
    _declarations_of(tag)   # validate the members now, not at first pinning

    return tag


def _is_pin(
        tag: type,
        ) -> bool:
    """A Shape of a Pin is a Pin."""

    return bool(
            getattr(
                    tag,
                    _PIN,
                    False,
                    )
            )


def _is_tag_base(
        base: type,
        ) -> bool:
    """A Tag class other than the root ``Tag`` (the root is the only Tag
    with no Tag among its own bases)."""

    return _is_tag_class(base) and any(
            _is_tag_class(deeper)
            for deeper in base.__bases__
            )


def _check_pin_bases(
        tag: type,
        ) -> None:
    """One Form is all Pins or no Pins."""

    bases = tuple(
            base
            for base in tag.__bases__
            if _is_tag_base(base)
            )
    pins = [
            base
            for base in bases
            if _is_pin(base)
            ]
    marked = bool(tag.__dict__.get(_PIN, False))

    if not bases or len(pins) == len(bases):
        return

    if not pins and not marked:
        return

    raise TagDeclarationError(
                f"{tag.__name__} mixes Pins and Tags in one Form; a Pin's"
                " Bases must be Pins (STEP-SPEC-9 §2)"
                )


class Report:
    """Shared data belonging to a Tag, written like a Record::

        @Report
        def hit_die(tag):
            return 8

    The builder receives the Tag and runs once per Tag, on first read. A
    second positional parameter receives the value the Tag's Bases give
    that name, or None, so a Shape can extend a Base's Report the way a
    Record extends what is stored. With @Constant, the builder instead
    runs once on the declaring Tag; every Shape reads that same value.
    """

    def __init__(
            report,
            builder: Function,
            ) -> None:
        if not callable(builder):
            raise TagDeclarationError(
                    "@Report marks a builder: `@Report def name(tag): ...`"
                    )

        report.builder = builder
        report.public = _has_flag(builder, _PUBLIC)
        report.__name__ = builder.__name__
        report.__doc__ = builder.__doc__
        report._name = builder.__name__
        report._owner_ref = None
        report._values: "WeakKeyDictionary[type, Any]" = WeakKeyDictionary()

    def __set_name__(
            report,
            owner: type,
            name: str,
            ) -> None:
        report._name = name

        if report._owner_ref is None:
            report._owner_ref = ref(owner)

    def __get__(
            report,
            instance: object,
            owner: type | None = None,
            ) -> Any:
        if owner is None:
            owner = type(instance)

        if _is_constant(report) and report._owner_ref is not None:
            declaring = report._owner_ref()

            if declaring is not None:
                owner = declaring

        try:
            return report._values[owner]
        except KeyError:
            pass

        value = report._build(owner)
        report._values[owner] = value

        return value

    def _build(
            report,
            owner: type,
            ) -> Any:
        if _parameters_of(report.builder).positional >= 2:
            return report.builder(
                    owner,
                    report._inherited(owner),
                    )

        return report.builder(owner)

    def _inherited(
            report,
            owner: type,
            ) -> Any:
        """The value the Bases give this name, or None: the first member of
        that name declared after this Report's own class in the MRO."""

        passed_own_class = False

        for klass in owner.__mro__:
            member = klass.__dict__.get(report._name)

            if member is report:
                passed_own_class = True
                continue

            if not passed_own_class or member is None:
                continue

            if isinstance(member, Report):
                return member.__get__(
                        None,
                        owner,
                        )

            return member

        return None

    def __repr__(
            report,
            ) -> str:
        return f"<Report {report._name}>"


# ------------------------------------------------------------------
# Scanning a Tag class
# ------------------------------------------------------------------


@dataclass(frozen=True)
class _Declarations:
    actions: tuple[tuple[str, Function], ...]
    records: tuple[tuple[str, Function], ...]
    gain_order: tuple[str, ...]   # Agent declarations, including conditions and deletions
    secrets: frozenset[str]
    imprints: tuple[tuple[str, Function], ...]
    preconditions: tuple[tuple[str, Function], ...]
    postconditions: tuple[tuple[str, Function], ...]
    deletions: tuple[str, ...]
    reports: tuple[tuple[str, Any, bool], ...]
    operations: tuple[tuple[str, Function, bool], ...]
    rips: tuple[str, ...]
    dunders: frozenset[str]
    published: frozenset[str]   # Agent-scope members marked @Public (Pins)
    constants: frozenset[str]
    runtime: bool = field(default=False, compare=False, repr=False)
    header: _Declarations | None = field(default=None, compare=False, repr=False)
    gaining_steps: tuple[tuple[str, _Declarations], ...] = field(
            default=(), compare=False, repr=False,
            )
    tools: frozenset[str] = frozenset()   # Records marked @Tool: their slots admit only their kind


def _declarations_of(
        tag: type,
        ) -> _Declarations:
    # A Tag owns its memo, never its public Field or a global weak-key
    # cache: declaration values may refer back to the Tag or its Agents.
    name = _declaration_key(tag)
    cached = _memo_of(tag, name)

    if type(cached) is _Declarations:
        return cached

    return _remember_memo(tag, name, _scan(tag))


def _declaration_key(
        tag: type,
        ) -> str:
    # Distinct Base and Shape memos have different keys.
    return _memo_key(tag, "DECLARATIONS")


def _invalidate_declarations(
        tag: type,
        ) -> None:
    _forget_memo(tag, _declaration_key(tag))


def _is_private(
        name: str,
        ) -> bool:
    return (
            name.startswith("_")
            and not _is_dunder(name)
            )


def _is_dunder(
        name: str,
        ) -> bool:
    return (
            name.startswith("__")
            and name.endswith("__")
            )


def _kind_of(
        attribute: Any,
        ) -> str | None:
    function = getattr(
            attribute,
            "__func__",
            attribute,
            )

    return getattr(
            function,
            _KIND,
            None,
            )


def _refuse_truth_gain(
        owner: str,
        name: str,
        member: Any,
        ) -> None:
    """The Agent's truth protocol cannot be gained, replaced or deleted."""

    if name != "__bool__":
        return

    if isinstance(member, Report):
        gained = member.public
    elif isinstance(member, (classmethod, staticmethod)):
        gained = (
                isinstance(member, classmethod)
                and _kind_of(member) == "operation"
                and _has_flag(member, _PUBLIC)
                )
    else:
        gained = callable(member) and _kind_of(member) in (
                None, "action", "record", "delete",
                )

    if gained:
        raise TagDeclarationError(
                f"{owner}.{name}: an Agent's truth is reserved for its"
                " visible Postconditions; a Contribution cannot redefine"
                " or delete it"
                )


def _refuse_condition_dunder(
        owner: str,
        name: str,
        kind: str | None,
        ) -> None:
    """Conditions expose verdicts; Python's protocol names need callables."""

    if _is_dunder(name) and kind in _CONDITION_KINDS:
        raise TagDeclarationError(
                f"{owner}.{name}: a Precondition or Postcondition must have"
                " an ordinary name; dunder names belong to Python protocols"
                )


def _has_flag(
        attribute: Any,
        name: str,
        ) -> bool:
    function = getattr(
            attribute,
            "__func__",
            attribute,
            )

    return bool(
            getattr(
                    function,
                    name,
                    False,
                    )
            )


def _tool_kind_of(
        attribute: Any,
        ) -> Any:
    """The kind a ``@Tool`` declaration names (a ``tools._Kind``), or None.
    Looks through a classmethod, a staticmethod and a Report's builder, so
    a mark hidden under another declaration is still seen and refused."""

    if isinstance(attribute, Report):
        attribute = attribute.builder

    function = getattr(
            attribute,
            "__func__",
            attribute,
            )

    return getattr(
            function,
            _TOOL,
            None,
            )


def _is_constant(
        member: Any,
        ) -> bool:
    return _has_flag(
            member.builder if isinstance(member, Report) else member,
            _CONSTANT,
            )


def _constant_owner(
        tag: type,
        name: str,
        ) -> type | None:
    """The class protecting a name, including Contributions from Pins.

    Look through the complete MRO: an ordinary earlier binding must not
    hide the protection of a later Base. Only raw namespaces are read;
    asking about protection never initializes a Report.
    """

    for klass in tag.__mro__:
        namespace = vars(klass)

        if _is_constant(namespace.get(name)):
            return klass

        managed = namespace.get(STATE)

        if managed is not None and name in managed.constants:
            return klass

    return None


def _check_constant_shapes(tag: type, name: str) -> None:
    """A late Base binding must not hide another Base's Constant in a Shape."""

    pending = list(type.__subclasses__(tag))
    seen = set()
    while pending:
        shape = pending.pop()
        if shape in seen:
            continue
        seen.add(shape)
        owner = _constant_owner(shape, name)
        if owner is not None and shape.__mro__.index(tag) < shape.__mro__.index(owner):
            raise TagCompositionError(
                    f"{tag.__name__}.{name} would hide the Constant from"
                    f" {owner.__name__} in {shape.__name__}"
                    )
        pending.extend(type.__subclasses__(shape))


def _check_constant_declarations(
        tag: type,
        namespace: dict[str, Any],
        ) -> None:
    """Validate Constant declarations without changing other scan timing."""

    for name, member in namespace.items():
        if not _is_constant(member):
            continue

        kind = _kind_of(member)
        supported = (
                isinstance(member, Report)
                or isinstance(member, classmethod) and kind == "operation"
                or not isinstance(member, (classmethod, staticmethod))
                and callable(member)
                and kind in (None, "action", "record", "postcondition", "condition")
                )

        if _is_private(name) or not supported:
            raise TagDeclarationError(
                    f"{tag.__name__}.{name}: @Constant requires a named"
                    " Record, Action, Post, Report or Operation"
                    )

    for base in tag.__mro__[1:]:
        base_namespace = _namespace_snapshot(base)
        protected = {
                name
                for name, member in base_namespace.items()
                if _is_constant(member)
                }
        managed = base_namespace.get(STATE)

        if managed is not None:
            protected.update(managed.constants)

        for name in protected:
            if name in namespace:
                raise TagDeclarationError(
                        f"{tag.__name__}.{name} cannot redefine the Constant"
                        f" from {base.__name__}"
                        )

            for earlier in tag.__mro__[1:]:
                if earlier is base:
                    break

                if name in vars(earlier):
                    raise TagDeclarationError(
                            f"{tag.__name__}: {earlier.__name__}.{name} masks"
                            f" the Constant from {base.__name__}"
                            )


def _refuse_tools_on_a_pin(
        tag: type,
        namespace: Any,
        ) -> None:
    """A Pin's Records land as Reports of the pinned Tag (§1.9): one value
    on the Tag, which is Tag-scope having and not a Tool."""

    for name, member in namespace.items():
        if _tool_kind_of(member) is not None:
            raise TagDeclarationError(
                    f"{tag.__name__}.{name}: a Pin's Records land as Reports"
                    " of the pinned Tag; a shared tool is a Report (§1.9)"
                    )


def _check_tool_declarations(
        tag: type,
        namespace: dict[str, Any],
        ) -> None:
    """A ``@Tool`` marks a Record, whatever the order of its decorators,
    and never a member of a Pin."""

    for name, member in namespace.items():
        if _tool_kind_of(member) is None:
            continue

        if (
                _is_private(name)
                or isinstance(member, (classmethod, staticmethod))
                or _kind_of(member) != "record"
                or _has_flag(member, _RIP)
                ):
            raise TagDeclarationError(
                    f"{tag.__name__}.{name}: @Tool declares what the Agent"
                    f" has, a Record; {name} is not one here"
                    )

    if any(
            _is_pin(base)
            for base in tag.__mro__[1:]
            ):
        _refuse_tools_on_a_pin(
                tag,
                namespace,
                )


_NAMED_FAILURES: dict[str, type] = {
        "imprint": TagImprintError,
        "precondition": TagPreconditionError,
        "postcondition": TagPostconditionError,
        }


def _name_checks(
        namespace: dict[str, Any],
        owner: str,
        ) -> None:
    """Give every check in a Tag body its named failure, at class creation.

    Done when the class is made, not at the first tagging, so
    ``except Precondition.Is_A_Caster`` is valid as soon as the Tag exists.
    """

    for name, attribute in namespace.items():
        if _is_private(name):
            continue

        _refuse_truth_gain(owner, name, attribute)
        kind = _kind_of(attribute)
        _refuse_condition_dunder(owner, name, kind)

        if kind == "condition":
            TagPreconditionError.Named(name)
            TagPostconditionError.Named(name)
            continue

        failure = _NAMED_FAILURES.get(kind)

        if failure is not None:
            failure.Named(name)


def _check_rip_declarations(
        owner: str,
        namespace: dict[str, Any],
        ) -> None:
    """Reject a Rip mark which class creation would otherwise ignore."""

    for name, attribute in namespace.items():
        _check_rip_declaration(
                owner,
                name,
                attribute,
                )


def _scan(
        tag: type,
        ) -> _Declarations:
    actions: list[tuple[str, Function]] = []
    records: list[tuple[str, Function]] = []
    gain_order: list[str] = []
    secrets: set[str] = set()
    imprints: list[tuple[str, Function]] = []
    preconditions: list[tuple[str, Function]] = []
    postconditions: list[tuple[str, Function]] = []
    deletions: list[str] = []
    reports: list[tuple[str, Any, bool]] = []
    operations: list[tuple[str, Function, bool]] = []
    rips: list[str] = []
    dunders: set[str] = set()
    published: set[str] = set()
    constants: set[str] = set()
    tools: set[str] = set()
    namespace = _namespace_snapshot(tag)
    managed = namespace.get(STATE)   # names a Pin landed here

    if managed is not None:
        _emit_published_pins(
                managed,
                reports,
                operations,
                )
        constants.update(
                name for name in managed.published
                if name in managed.constants
                )

    for name, attribute in namespace.items():
        _refuse_truth_gain(tag.__name__, name, attribute)
        if managed is not None and (
                name in managed.actions
                or name in managed.records
                ):
            continue

        _check_rip_declaration(
                tag,
                name,
                attribute,
                )

        if _is_private(name):
            continue

        if _is_constant(attribute):
            constants.add(name)

        if isinstance(attribute, Report):
            if attribute.public and _has_flag(attribute.builder, _SECRET):
                _reject_both(tag, name, True, True)

            reports.append(
                    (
                        name,
                        attribute,
                        attribute.public,
                        )
                    )
            continue

        kind = _kind_of(attribute)
        _refuse_condition_dunder(tag.__name__, name, kind)
        secret = _has_flag(attribute, _SECRET)
        public = _has_flag(attribute, _PUBLIC)

        if kind == "operation":
            _reject_both(tag, name, secret, public)
            operations.append(
                    (
                        name,
                        attribute.__func__,
                        public,
                        )
                    )
            continue

        if isinstance(
                attribute,
                (
                    classmethod,
                    staticmethod,
                ),
                ):
            continue

        if not callable(attribute):
            continue

        if public:
            published.add(name)

        if kind == "record":
            _reject_both(tag, name, secret, public)
            records.append(
                    (
                        name,
                        attribute,
                        )
                    )
            gain_order.append(name)

            if secret:
                secrets.add(name)

            if _tool_kind_of(attribute) is not None:
                tools.add(name)

            continue

        if kind == "imprint":
            imprints.append(
                    (
                        name,
                        attribute,
                        )
                    )
            continue

        if kind in ("precondition", "condition"):
            preconditions.append(
                    (
                        name,
                        attribute,
                        )
                    )

        if kind in ("postcondition", "condition"):
            postconditions.append(
                    (
                        name,
                        attribute,
                        )
                    )

        if kind in _CONDITION_KINDS:
            gain_order.append(name)
            continue

        if kind == "delete":
            deletions.append(name)
            gain_order.append(name)
            continue

        # Anything else callable is an Action (kind "action" or unmarked).
        _reject_both(tag, name, secret, public)
        actions.append(
                (
                    name,
                    attribute,
                    )
                )
        gain_order.append(name)

        if secret:
            secrets.add(name)

        if _has_flag(attribute, _RIP):
            rips.append(name)

        if _is_dunder(name):
            dunders.add(name)

    declarations = _Declarations(
            actions=tuple(actions),
            records=tuple(records),
            gain_order=tuple(gain_order),
            secrets=frozenset(secrets),
            imprints=tuple(imprints),
            preconditions=tuple(preconditions),
            postconditions=tuple(postconditions),
            deletions=tuple(deletions),
            reports=tuple(reports),
            operations=tuple(operations),
            rips=tuple(rips),
            dunders=frozenset(dunders),
            published=frozenset(published),
            constants=frozenset(constants),
            tools=frozenset(tools),
            )

    if _is_pin(tag):
        _validate_pin(
                tag,
                declarations,
                )

    return _prepare_declarations(declarations)


def _prepare_declarations(
        declarations: _Declarations,
        ) -> _Declarations:
    """Prepare immutable phase slices once, alongside the Tag's scan."""

    names = frozenset(declarations.gain_order)
    header = replace(
            declarations,
            actions=(),
            records=(),
            preconditions=(),
            postconditions=(),
            deletions=(),
            gain_order=(),
            secrets=declarations.secrets - names,
            constants=declarations.constants - names,
            published=declarations.published - names,
            dunders=declarations.dunders - names,
            tools=declarations.tools - names,
            rips=(),
            )
    header = replace(header, runtime=_runtime_facts(header))
    actions = dict(declarations.actions)
    records = dict(declarations.records)
    preconditions = dict(declarations.preconditions)
    postconditions = dict(declarations.postconditions)
    steps = []

    for name in declarations.gain_order:
        kind = (
                "action" if name in actions
                else "record" if name in records
                else "condition" if name in preconditions or name in postconditions
                else "delete"
                )
        selected = frozenset((name,))
        one = _Declarations(
                actions=((name, actions[name]),) if name in actions else (),
                records=((name, records[name]),) if name in records else (),
                gain_order=(name,),
                preconditions=((name, preconditions[name]),) if name in preconditions else (),
                postconditions=((name, postconditions[name]),) if name in postconditions else (),
                deletions=(name,) if kind == "delete" else (),
                secrets=declarations.secrets & selected,
                dunders=declarations.dunders & selected,
                published=declarations.published & selected,
                constants=declarations.constants & selected,
                tools=declarations.tools & selected,
                reports=(),
                operations=(),
                imprints=(),
                rips=(),
                )
        one = replace(one, runtime=_runtime_facts(one))
        steps.append((kind, one))

    return replace(declarations, header=header, gaining_steps=tuple(steps), runtime=_runtime_facts(declarations))


def _runtime_facts(declarations: _Declarations) -> bool:
    return bool(
            declarations.deletions
            or declarations.secrets
            or declarations.dunders
            or declarations.published
            or declarations.constants
            or declarations.preconditions
            or declarations.postconditions
            or declarations.tools
            or any(public for _name, _report, public in declarations.reports)
            )


def _has_rip_declaration(
        attribute: Any,
        ) -> bool:
    """Find Rip marks inside known wrappers without binding descriptors."""

    pending = [attribute]
    seen: set[int] = set()

    while pending:
        member = pending.pop()

        if id(member) in seen:
            continue

        seen.add(id(member))

        if isinstance(member, (cached_property, partialmethod)):
            if getattr_static(member, _RIP, False) is True:
                return True

            pending.append(getattr_static(member, "func", None))
        elif isinstance(member, property):
            pending.extend(
                    accessor.__get__(member)
                    for accessor in (property.fget, property.fset, property.fdel)
                    )
        elif isinstance(member, Report):
            pending.append(getattr_static(member, "builder", None))
        elif isinstance(member, classmethod):
            pending.append(classmethod.__func__.__get__(member))
        elif isinstance(member, staticmethod):
            pending.append(staticmethod.__func__.__get__(member))
        elif _has_flag(member, _RIP):
            return True

    return False


def _check_rip_declaration(
        owner: type | str,
        name: str,
        attribute: Any,
        ) -> None:
    """A Rip protocol is an Action too; never ignore the mark on another
    declaration kind or on a name which cannot become a Contribution."""

    if not _has_rip_declaration(attribute):
        return

    kind = _kind_of(attribute)

    if _is_constant(attribute):
        reason = "@Constant cannot mark a Rip protocol"
    elif name == "__del__":
        reason = (
                "a __del__ Layer already runs when the Agent is deleted,"
                " after its teardowns; give the teardown a name of its own"
                )
    elif (
            not _is_private(name)
            and not isinstance(attribute, (
                    Report, property, classmethod, staticmethod,
                    cached_property, partialmethod,
                    ))
            and callable(attribute)
            and kind in (None, "action")
            ):
        return
    elif _is_private(name):
        reason = "private names are not Contributions"
    elif isinstance(attribute, Report):
        reason = "it is a Report"
    elif kind is not None:
        reason = f"its declaration kind is {kind.replace('_', ' ')}"
    else:
        reason = f"it is a {type(attribute).__name__}"

    owner_name = owner if isinstance(owner, str) else owner.__name__

    raise TagDeclarationError(
            f"{owner_name}.{name} is marked @Rip, but {reason};"
            " @Rip marks an Action because a teardown is also callable"
            " as an Action"
            )


def _emit_published_pins(
        managed: Any,
        reports: list[tuple[str, Any, bool]],
        operations: list[tuple[str, Function, bool]],
        ) -> None:
    """Members a Pin landed on this Tag with @Public are the Tag's own
    published Reports and Operations to every Agent tagged from now on
    (STEP-SPEC-9 §5). Present Agents were reached at pinning."""

    for name in managed.published:
        if name in managed.records:
            reports.append(
                    (
                        name,
                        None,
                        True,
                        )
                    )
        elif name in managed.actions:
            operations.append(
                    (
                        name,
                        managed.actions[name],
                        True,
                        )
                    )


def _validate_pin(
        tag: type,
        declarations: _Declarations,
        ) -> None:
    """A Pin's members carry no @Delete and no special-method Actions, and
    its own Reports and Operations are not published: each would need a
    descriptor or a hook on the Tag's metaclass, and none has a meaning
    there yet. @Secret and @Public on its Agent-scope members do."""

    problems: list[str] = []

    published = [
            name
            for name, _value, public in declarations.reports
            if public
            ] + [
            name
            for name, _function, public in declarations.operations
            if public
            ]

    if published:
        problems.append(
                "@Public on the Pin's own Reports / Operations " + ", ".join(published)
                )

    if declarations.deletions:
        problems.append(
                "@Delete of " + ", ".join(declarations.deletions)
                )

    if declarations.dunders:
        problems.append(
                "special-method Actions " + ", ".join(sorted(declarations.dunders))
                )

    if problems:
        raise TagDeclarationError(
                f"{tag.__name__} is a Pin; its members are plain:"
                f" {'; '.join(problems)} (STEP-SPEC-9 §5)"
                )


def _reject_both(
        tag: type,
        name: str,
        secret: bool,
        public: bool,
        ) -> None:
    """A modifier that restates the default is accepted; both at once is
    a contradiction."""

    if secret and public:
        raise TagDeclarationError(
                f"{tag.__name__}.{name}: @Secret and @Public together say"
                " nothing; a member is internal or external"
                )


# ------------------------------------------------------------------
# Parameters
# ------------------------------------------------------------------


@dataclass(frozen=True)
class _Parameters:
    positional: int
    named: tuple[tuple[str, bool], ...]
    var_keyword: bool


_parameter_cache: "dict[int, tuple[ref[Function], _Parameters]]" = {}


def _parameters_of(
        function: Function,
        ) -> _Parameters:
    key = id(function)
    cached = _parameter_cache.get(key)

    if cached is not None and cached[0]() is function:
        return cached[1]

    positional = 0
    named: list[tuple[str, bool]] = []
    var_keyword = False

    for parameter in signature(function).parameters.values():
        if parameter.kind is Parameter.VAR_KEYWORD:
            var_keyword = True
            continue

        if parameter.kind is Parameter.VAR_POSITIONAL:
            continue

        if parameter.kind is not Parameter.KEYWORD_ONLY:
            positional += 1

        named.append(
                (
                    parameter.name,
                    parameter.default is not Parameter.empty,
                    )
                )

    spec = _Parameters(
            positional=positional,
            named=tuple(named),
            var_keyword=var_keyword,
            )

    # Preserve native keyword keys without letting their optional payloads
    # make the global memo own the callable (or its other references).
    if any(type(name) is not str for name, _ in spec.named):
        return spec

    def Forget(expired: ref[Function], key: int = key) -> None:
        current = _parameter_cache.get(key)

        if current is not None and current[0] is expired:
            del _parameter_cache[key]

    try:
        reference = ref(function, Forget)
    except TypeError:
        pass   # valid non-weakrefable callables are inspected without a memo
    else:
        _parameter_cache[key] = reference, spec

    return spec


def _takes_underlay(
        function: Function,
        name: str,
        ) -> bool:
    """An Action or condition extends the prior contribution when marked
    @Underlay. The mark requires a second positional parameter."""

    if not _has_flag(function, _UNDERLAY):
        return False

    if _parameters_of(function).positional < 2:
        raise TagDeclarationError(
                f"{str.__str__(name)!r} is marked @Underlay but has no"
                " second positional parameter to receive the underlay"
                )

    return True


def _takes_stored(
        function: Function,
        ) -> bool:
    """A Record builder receives the stored value when it declares a second
    positional parameter (the @Underlay mark is accepted as documentation)."""

    return _parameters_of(function).positional >= 2


def _protocol_inputs(
        function: Function,
        inputs: dict[str, Any],
        skip: int,
        ) -> dict[str, Any]:
    """Bind application inputs to a protocol's named parameters.

    The first ``skip`` positional parameters are bound by position (the
    Agent, and an underlay or stored value when present), so their names
    are the author's choice. Later parameters, positional or keyword-only,
    are filled from ``inputs`` by name. A parameter the caller did not
    supply keeps its own default, or receives None when it has none.
    ``**kwargs`` receives any remaining inputs.
    """

    spec = _parameters_of(function)
    bound: dict[str, Any] = {}

    for index, (name, has_default) in enumerate(spec.named):
        if index < skip:
            continue

        if name in inputs:
            bound[name] = inputs[name]
        elif not has_default:
            bound[name] = None

    if spec.var_keyword:
        for name, value in inputs.items():
            bound.setdefault(
                    name,
                    value,
                    )

    return bound


def _discard_lazy_result(
        result: Any,
        ) -> str | None:
    """Dispose of a lazy result a synchronous protocol cannot use.

    Return its kind for the phase-specific failure message. Coroutines and
    synchronous generators have a synchronous ``close`` operation that does
    not start an unentered body. Async generators can only be closed by
    awaiting ``aclose``; TOP does not invent an event loop merely to reject
    one, so it leaves the unstarted object for Python to reclaim.
    """

    result_type = type(result)

    # Native lazy types cannot be subclassed. Identity avoids consulting an
    # ordinary return value's potentially effectful __class__ descriptor.
    if result_type is CoroutineType:
        result.close()

        return "coroutine"

    if result_type is AsyncGeneratorType:
        return "async generator"

    if result_type is GeneratorType:
        result.close()

        return "generator"

    return None
