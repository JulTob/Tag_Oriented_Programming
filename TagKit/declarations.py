"""Declarations: the marks an author puts on a Tag, and how they are read.

Agent scope:  @Action, @Record          (external by default, @Secret hides)
Tag scope:    @Operation, @Report     (internal by default, @Public publishes)
Protocols:    @Imprint, @Pre, @Post, @Rip, @Delete
Composition:  @Underlay                 (extend the prior visible contribution)

A Tag class is scanned once; the result is cached per class.
"""

from __future__ import annotations

from dataclasses import dataclass
from inspect import Parameter
from inspect import signature
from typing import Any
from typing import Callable
from weakref import WeakKeyDictionary

from .errors import TagDeclarationError
from .errors import TagImprintError
from .errors import TagPostconditionError
from .errors import TagPreconditionError


_KIND = "__tagkit_kind__"
_UNDERLAY = "__tagkit_underlay__"
_RIP = "__tagkit_rip__"
_SECRET = "__tagkit_secret__"
_PUBLIC = "__tagkit_public__"
_FLAG = "__tagkit_flag__"
_PIN = "__tagkit_pin__"

STATE = "_TAGKIT_STATE"

_MISSING = object()

Function = Callable[..., Any]


# ------------------------------------------------------------------
# Marks
# ------------------------------------------------------------------


def _mark(
        function: Function,
        kind: str,
        ) -> Function:
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


def Rip(
        function: Function,
        ) -> Function:
    """Teardown. Runs when the Agent leaves the Tag's Field. It is also a
    normally callable Action."""

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
        return f"<TagKit mark @{mark.__name__}>"


Imprint = _Check_Mark(
        "imprint",
        TagImprintError,
        "Work performed after the Tag has applied.",
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


def Operation(
        function: Function,
        ) -> classmethod:
    """Tag behaviour. The Tag is its first input."""

    _mark(
            function,
            "operation",
            )

    return classmethod(function)


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
        tag: type,
        ) -> type:
    """Mark a Tag as a keyword: searchable from the Agent's side by name
    or by class, ``"Undead" in ghoul`` and ``Undead in ghoul``.

    Applying a Flag to a host that defines its own ``in`` is refused.
    """

    if not isinstance(tag, type) or not hasattr(tag, "_tagkit_field"):
        raise TagDeclarationError(
                "@Flag marks a Tag class"
                )

    if _is_pin(tag):
        raise TagDeclarationError(
                f"{tag.__name__}: a Pin cannot be a Flag; on a Tag, `in`"
                " is membership (STEP-SPEC-9 §6)"
                )

    setattr(
            tag,
            _FLAG,
            True,
            )

    return tag


def _is_flag(
        tag: type,
        ) -> bool:
    return bool(
            tag.__dict__.get(
                    _FLAG,
                    False,
                    )
            )


def Pin(
        tag: type,
        ) -> type:
    """Mark a Tag whose Targets are Tags (STEP-SPEC-9).

    ``Rare(Wizard)`` makes the Tag ``Wizard`` an Agent of ``Rare``: its
    Records land on ``Wizard`` as Reports, its Actions as Operations, and
    the Field of ``Rare`` is a population of Tags. A Pin applies to
    nothing else, and its Bases must be Pins.
    """

    if not isinstance(tag, type) or not hasattr(tag, "_tagkit_field"):
        raise TagDeclarationError(
                "@Pin marks a Tag class"
                )

    if _is_flag(tag):
        raise TagDeclarationError(
                f"{tag.__name__}: a Pin cannot be a Flag; on a Tag, `in`"
                " is membership (STEP-SPEC-9 §6)"
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

    return hasattr(base, "_tagkit_field") and any(
            hasattr(deeper, "_tagkit_field")
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
    Record extends what is stored.
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
        report._values: "WeakKeyDictionary[type, Any]" = WeakKeyDictionary()

    def __set_name__(
            report,
            owner: type,
            name: str,
            ) -> None:
        report._name = name

    def __get__(
            report,
            instance: object,
            owner: type | None = None,
            ) -> Any:
        if owner is None:
            owner = type(instance)

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
    secrets: frozenset[str]
    imprints: tuple[tuple[str, Function], ...]
    preconditions: tuple[tuple[str, Function], ...]
    postconditions: tuple[tuple[str, Function], ...]
    deletions: tuple[str, ...]
    reports: tuple[tuple[str, Any, bool], ...]
    operations: tuple[tuple[str, Function, bool], ...]
    rips: tuple[str, ...]
    dunders: frozenset[str]


_scan_cache: "WeakKeyDictionary[type, _Declarations]" = WeakKeyDictionary()


def _declarations_of(
        tag: type,
        ) -> _Declarations:
    cached = _scan_cache.get(tag)

    if cached is None:
        cached = _scan(tag)
        _scan_cache[tag] = cached

    return cached


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


_NAMED_FAILURES: dict[str, type] = {
        "imprint": TagImprintError,
        "precondition": TagPreconditionError,
        "postcondition": TagPostconditionError,
        }


def _name_checks(
        namespace: dict[str, Any],
        ) -> None:
    """Give every check in a Tag body its named failure, at class creation.

    Done when the class is made, not at the first tagging, so
    ``except Precondition.Is_A_Caster`` is valid as soon as the Tag exists.
    """

    for name, attribute in namespace.items():
        if _is_private(name):
            continue

        failure = _NAMED_FAILURES.get(_kind_of(attribute))

        if failure is not None:
            failure.Named(name)


def _scan(
        tag: type,
        ) -> _Declarations:
    actions: list[tuple[str, Function]] = []
    records: list[tuple[str, Function]] = []
    secrets: set[str] = set()
    imprints: list[tuple[str, Function]] = []
    preconditions: list[tuple[str, Function]] = []
    postconditions: list[tuple[str, Function]] = []
    deletions: list[str] = []
    reports: list[tuple[str, Any, bool]] = []
    operations: list[tuple[str, Function, bool]] = []
    rips: list[str] = []
    dunders: set[str] = set()
    modified: list[str] = []
    managed = tag.__dict__.get(STATE)   # names a Pin landed here

    for name, attribute in tag.__dict__.items():
        if _is_private(name):
            continue

        if managed is not None and (
                name in managed.actions
                or name in managed.records
                ):
            continue

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

        if secret or public:
            modified.append(name)

        if kind == "record":
            _reject_both(tag, name, secret, public)
            records.append(
                    (
                        name,
                        attribute,
                        )
                    )

            if secret:
                secrets.add(name)

            continue

        if kind == "imprint":
            imprints.append(
                    (
                        name,
                        attribute,
                        )
                    )
            continue

        if kind == "precondition":
            preconditions.append(
                    (
                        name,
                        attribute,
                        )
                    )
            continue

        if kind == "postcondition":
            postconditions.append(
                    (
                        name,
                        attribute,
                        )
                    )
            continue

        if kind == "delete":
            deletions.append(name)
            continue

        # Anything else callable is an Action (kind "action" or unmarked).
        _reject_both(tag, name, secret, public)
        actions.append(
                (
                    name,
                    attribute,
                    )
                )

        if secret:
            secrets.add(name)

        if _has_flag(attribute, _RIP):
            rips.append(name)

        if _is_dunder(name):
            dunders.add(name)

    declarations = _Declarations(
            actions=tuple(actions),
            records=tuple(records),
            secrets=frozenset(secrets),
            imprints=tuple(imprints),
            preconditions=tuple(preconditions),
            postconditions=tuple(postconditions),
            deletions=tuple(deletions),
            reports=tuple(reports),
            operations=tuple(operations),
            rips=tuple(rips),
            dunders=frozenset(dunders),
            )

    if _is_pin(tag):
        _validate_pin(
                tag,
                declarations,
                modified,
                )

    return declarations


def _validate_pin(
        tag: type,
        declarations: _Declarations,
        modified: list[str],
        ) -> None:
    """A Pin's members are plain: no publication modifiers, no deletions,
    no special-method Actions. Each of those would put a descriptor or a
    hook on the Tag's metaclass; none has a meaning there yet."""

    problems: list[str] = []

    if modified:
        problems.append(
                "@Secret / @Public on " + ", ".join(modified)
                )

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
                "@Public on " + ", ".join(published)
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


_parameter_cache: "WeakKeyDictionary[Function, _Parameters]" = (
        WeakKeyDictionary()
        )


def _parameters_of(
        function: Function,
        ) -> _Parameters:
    cached = _parameter_cache.get(function)

    if cached is not None:
        return cached

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
    _parameter_cache[function] = spec

    return spec


def _takes_underlay(
        function: Function,
        ) -> bool:
    """An Action or condition extends the prior contribution when marked
    @Underlay. The mark requires a second positional parameter."""

    if not _has_flag(function, _UNDERLAY):
        return False

    if _parameters_of(function).positional < 2:
        raise TagDeclarationError(
                f"{function.__qualname__} is marked @Underlay but has no"
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
