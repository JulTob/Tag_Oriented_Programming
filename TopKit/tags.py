"""The public TOP types: Tag and its metaclass.

TOP borrows the language's own syntax for Tag-level acts and leaves the
Tag's dotted namespace to the program:

    Wizard(charlie)               apply (Bases first)
    charlie in Wizard             sound membership, as in the plain loop
    charlie in Wizard[:]          active membership, sound or defective
    "Deprecated" in Wizard        a keyword: the Tag carries the Flag Pin Deprecated
    Wizard in charlie             the same, from the Agent's side
    "Wizard" in charlie           the same, by name
    isinstance(charlie, Wizard)   ever a member ("ever a Wizard, always a Wizard")
    for w in Wizard               the sound population
    if Wizard                     do the Tag's own visible Posts hold?
    len(Wizard)                   the number of sound Wizards
    for w in ~Wizard              the defective population
    Wizard[:]                     everyone: the whole Field
    Wizard[charlie]               the Agent-bound view
    del Wizard[charlie]           leave the Field (Rip)
    Form(Wizard)                  the Base-first closure, as Tags
    f"{Wizard:form}"              the same, as text

A Tag marked @Pin applies to Tags (STEP-SPEC-9); the pinned Tag is then
an Agent in every spelling above: Rare(Wizard), Wizard in Rare,
for tag in Rare, Rare[Wizard], del Rare[Wizard], f"{Wizard:pins}".
"""

from __future__ import annotations

from typing import Any
from typing import Iterator

from .access import _keyword
from .access import _refuse_host_truth
from .access import _view_of
from .arrest import _arrest_of
from .arrest import _require_available
from .contracts import _holds
from .contracts import _holds_for_population
from .declarations import _MISSING
from .declarations import _check_constant_declarations
from .declarations import _check_constant_shapes
from .declarations import _check_link_declarations
from .declarations import _check_pin_bases
from .declarations import _check_rip_declarations
from .declarations import _check_tool_declarations
from .declarations import _constant_owner
from .declarations import _is_dunder
from .declarations import _is_link
from .declarations import _is_pin
from .declarations import _kind_of
from .declarations import _name_checks
from .declarations import _refuse_condition_dunder
from .declarations import _refuse_truth_gain
from .errors import TagCompositionError
from .errors import TagDeclarationError
from .errors import TagResolutionError
from .fields import FIELD_SEAT
from .fields import _Field
from .fields import _Partition
from .fields import _Safehouse
from .fields import _field_of
from .fields import _population_of
from .fields import _sound_of
from .geometry import _form_of
from .geometry import _is_tag
from .lifecycle import _rip
from .lifecycle import _rip_field
from .lifecycle import _retry_arrested
from .state import Tagged
from .state import _name_of
from .state import _state_of
from .state import _view_subject
from .transactions import _apply


def _refuse_relation(
        tag: type,
        ) -> None:
    """A Relation is a template, never a Tag in play (STEP-SPEC-22 §9):
    every act on it is refused and points to a Link; so is every act on
    the kit's Tag for a Pair. One cached class lookup: an ordinary Tag
    reads the root's None."""

    kind = tag._topkit_kind

    if kind is None or kind == "link":
        return

    if kind == "relation":
        raise TagCompositionError(
                f"{tag.__name__} is a Relation: link through an Agent,"
                f" agent.{tag.__name__}(contact)"
                )

    raise TagCompositionError(
            f"{tag.__name__} is the kit's Tag for a Pair: reach a Pair"
            f" through its Link, agent.{tag.__name__}[contact]"
            )


def _is_link_tag(
        tag: type,
        ) -> bool:
    """One Agent's Link, read on the hot paths: one cached class lookup."""

    return tag._topkit_kind == "link"


_making_link = 0   # raised by links while it builds one Agent's Link
_links_module: Any = None   # links builds on this module: bound on first use


def _links() -> Any:
    global _links_module

    if _links_module is None:
        from . import links

        _links_module = links

    return _links_module


class MetaTag(type):
    """Metaclass of every Tag: the Tag-level acts, in language syntax."""

    def __new__(
            meta,
            name: str,
            bases: tuple[type, ...],
            namespace: dict[str, Any],
            **kwargs: Any,
            ) -> "MetaTag":
        namespace.setdefault(
                FIELD_SEAT,
                _Field(),
                )
        namespace.setdefault(
                "_topkit_kind",
                None,
                )   # its own, never inherited: a Relation, a Link or a Pair Tag says so itself
        _check_rip_declarations(
                name,
                namespace,
                )
        _name_checks(namespace, name)

        if not _making_link and any(
                _is_link(base)
                for base in bases
                ):
            raise TagDeclarationError(
                    f"{name}: an Agent's Link is never the Base of a Tag;"
                    " a Shape of a Link is declared as a Relation,"
                    " @Link class Trusts(Knows)"
                    )

        tag = super().__new__(
                meta,
                name,
                bases,
                namespace,
                **kwargs,
                )
        _check_pin_bases(tag)
        _check_constant_declarations(tag, namespace)
        _check_tool_declarations(tag, namespace)
        _check_link_declarations(tag, namespace)

        return tag

    def __setattr__(
            tag,
            name: str,
            value: Any,
            ) -> None:
        _refuse_truth_gain(tag.__name__, name, value)
        if _is_dunder(name):
            _refuse_condition_dunder(tag.__name__, name, _kind_of(value))
        owner = _constant_owner(tag, name)

        if owner is not None:
            raise TagCompositionError(
                    f"{tag.__name__}.{name} is Constant from"
                    f" {owner.__name__}; it cannot be overwritten"
                    )

        _check_constant_shapes(tag, name)
        super().__setattr__(name, value)

    def __delattr__(
            tag,
            name: str,
            ) -> None:
        owner = _constant_owner(tag, name)

        if owner is not None:
            raise TagCompositionError(
                    f"{tag.__name__}.{name} is Constant from"
                    f" {owner.__name__}; it cannot be deleted"
                    )

        super().__delattr__(name)

    def __call__(
            tag,
            target: object = _MISSING,
            /,
            **inputs: Any,
            ) -> object:
        if tag._topkit_kind is not None:
            _refuse_relation(tag)   # a Relation or a Pair Tag; one attribute read for every other Tag

        if target is _MISSING:
            raise TypeError(
                    f"{tag.__name__} is a Tag: apply it to a Target,"
                    f" {tag.__name__}(target)"
                    )

        target = _view_subject(target)

        if _is_link_tag(tag):
            return _links()._link(
                    tag,
                    target,
                    inputs,
                    )

        if _is_pin(tag):
            _check_pin_target(
                    tag,
                    target,
                    )
        elif isinstance(target, type):
            raise TypeError(
                    f"{tag.__name__} is applied to objects, not classes"
                    )
        else:
            _refuse_host_truth(target)

        return _apply(
                target,
                tag,
                inputs,
                )

    def __contains__(
            tag,
            candidate: object,
            ) -> bool:
        """``agent in Wizard``: sound membership, as in the plain loop.
        ``agent in Wizard[:]`` is raw membership. A string asks for a
        keyword among the Tag's Flag Pins, never Agent membership."""

        if tag._topkit_kind is not None:
            _refuse_relation(tag)   # a Relation or a Pair Tag; one attribute read for every other Tag

        if isinstance(candidate, str):
            return _keyword(
                    tag,
                    candidate,
                    )

        field = _field_of(tag)
        candidate = field._Member(candidate)

        if candidate is None:
            return False

        holds = (
                _links()._contact_holds(tag)
                if tag._topkit_kind == "link"
                else _holds_for_population
                )
        return (
                _arrest_of(candidate) is None
                and holds(candidate)
                and _arrest_of(candidate) is None
                and candidate in field
                )

    def __instancecheck__(
            tag,
            candidate: object,
            ) -> bool:
        if tag._topkit_kind is not None:
            _refuse_relation(tag)   # a Relation or a Pair Tag; one attribute read for every other Tag
        state = _state_of(candidate)

        if state is None:
            candidate = _view_subject(candidate)
            state = _state_of(candidate)

        if state is not None and (
                tag in state.ever
                or (state.ever_links is not None and tag in state.ever_links)
                ):
            return True

        return super().__instancecheck__(candidate)

    def __iter__(
            tag,
            ) -> Iterator[object]:
        return iter(_sound_of(tag))

    def __len__(
            tag,
            ) -> int:
        return len(_sound_of(tag))

    def __bool__(
            tag,
            ) -> bool:
        if tag._topkit_kind is not None:
            _refuse_relation(tag)   # a Relation or a Pair Tag; one attribute read for every other Tag

        return _holds(tag)

    def __invert__(
            tag,
            ) -> _Partition:
        return ~_sound_of(tag)

    def __or__(
            tag,
            other: Any,
            ) -> Any:
        """``Wizard | Fighter``: the sound population of either. A Tag in an
        operator seat is its sound population; anything that is not a
        population keeps ``type``'s own meaning (``Wizard | None``)."""

        if _population_of(other) is NotImplemented:
            return super().__or__(other)

        return _sound_of(tag) | other

    def __ror__(
            tag,
            other: Any,
            ) -> Any:
        if _population_of(other) is NotImplemented:
            return super().__ror__(other)

        return other | _sound_of(tag)

    def __and__(
            tag,
            other: Any,
            ) -> Any:
        return _sound_of(tag) & other

    def __rand__(
            tag,
            other: Any,
            ) -> Any:
        return other & _sound_of(tag)

    def __sub__(
            tag,
            other: Any,
            ) -> Any:
        return _sound_of(tag) - other

    def __rsub__(
            tag,
            other: Any,
            ) -> Any:
        return other - _sound_of(tag)

    def __getitem__(
            tag,
            key: Any,
            ) -> Any:
        if tag._topkit_kind is not None:
            _refuse_relation(tag)   # a Relation or a Pair Tag; one attribute read for every other Tag

        if key is Ellipsis:
            return _Safehouse(None if tag is Tag else tag)

        if isinstance(key, slice):
            if key != slice(None):
                raise TypeError(
                        "Tag[:] is the whole Field; positional slices have"
                        " no meaning for a population"
                        )

            return _field_of(tag)

        if _is_link_tag(tag):
            key = _view_subject(key)
            return _links()._pair_view_of(
                    tag,
                    key,
                    )

        key = _view_subject(key)
        return _view_of(
                key,
                tag,
                )

    def __delitem__(
            tag,
            agent: object,
            ) -> None:
        if tag._topkit_kind is not None:
            _refuse_relation(tag)   # a Relation or a Pair Tag; one attribute read for every other Tag

        if _arrest_of(tag) is not None:
            _require_available(tag, "Rip")

        if isinstance(agent, slice):
            if agent != slice(None):
                raise TypeError(
                        "Tag[:] is the whole Field; positional slices have"
                        " no meaning for a population"
                        )

            if tag is Tag:
                raise TagResolutionError("root Tag has no Field to Rip")
            _rip_field(tag)
            return

        agent = _view_subject(agent)

        if tag is Tag:
            # Root Tag[...] sees every arrest, but root deletion handles only
            # teardowns orphaned by an ended Tag, never a live Tag's work.
            _retry_arrested(agent, orphaned_only=True)
            return

        _rip(
                agent,
                tag,
                )

    def __format__(
            tag,
            spec: str,
            ) -> str:
        if spec == "":
            return str(tag)

        if spec == "form":
            return " → ".join(
                    member.__name__
                    for member in _form_of(tag)
                    )

        if spec == "pins":
            from .queries import Tags

            return ", ".join(
                    pin.__name__
                    for pin in Tags(tag)
                    )

        if spec == "contract":
            from .contracts import Contract

            return Contract.Display(tag)

        raise ValueError(
                f"unknown format spec {spec!r} for a Tag; use 'form',"
                " 'pins', or 'contract'"
                )


def _check_pin_target(
        pin: type,
        target: object,
        ) -> None:
    if not _is_tag(target):
        raise TagCompositionError(
                f"{pin.__name__} is a Pin: apply it to a Tag, not to"
                f" {_name_of(target)}"
                )

    _refuse_relation(target)   # a template, or the kit's Tag for a Pair

    if _is_link(target):
        raise TagCompositionError(
                f"{pin.__name__} is a Pin, and {target.__name__} is one"
                " Agent's Link: Links between Tags need their own receiver"
                " rule (STEP-SPEC-22)"
                )

    if target in _form_of(pin):
        raise TagCompositionError(
                f"{pin.__name__} cannot pin itself"
                )


class Tag(metaclass=MetaTag):
    """A semantic category. Subclass it; its members are its contributions."""

    __slots__ = ()


__all__ = [
        "MetaTag",
        "Tag",
        "Tagged",
        ]
