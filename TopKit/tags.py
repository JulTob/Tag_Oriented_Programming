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

A concrete Pin declared with ``class Rare(Pin)`` applies to Tags
(STEP-SPEC-9); the pinned Tag is then
an Agent in every spelling above: Rare(Wizard), Wizard in Rare,
for tag in Rare, Rare[Wizard], del Rare[Wizard], f"{Wizard:pins}".
"""

from __future__ import annotations

from typing import Any
from typing import Iterator

from .observations import _refuse_observed_act

from .arrest import _arrest_of
from .access import _keyword
from .access import _refuse_host_truth
from .access import _view_of
from .contracts import _holds
from .contracts import _holds_for_population
from .declarations import _MISSING
from .declarations import _check_application_target
from .declarations import _check_constant_declarations
from .declarations import _check_constant_shapes
from .declarations import _check_pin_bases
from .declarations import _check_rip_declarations
from .declarations import _check_tool_declarations
from .declarations import _constant_owner
from .declarations import _declarations_of
from .declarations import _is_dunder
from .declarations import _is_pin
from .declarations import _is_pin_locked
from .declarations import _is_pin_physical
from .declarations import _kind_of
from .declarations import _name_checks
from .declarations import _note_tag_kinds
from .declarations import _pin_publication
from .declarations import _publish_tool_kinds
from .declarations import _refuse_condition_dunder
from .declarations import _refuse_truth_gain
from .declarations import _tool_kind_of_static
from .declarations import _tool_tag_kinds
from .errors import TagCompositionError
from .errors import TagDeclarationError
from .fields import FIELD_SEAT
from .fields import _Field
from .fields import _Partition
from .fields import _field_of
from .fields import _population_of
from .fields import _sound_of
from .geometry import _form_of
from .geometry import _Category_Stamp
from .geometry import _META_KIND
from .geometry import _PIN_KIND
from .geometry import _TAG_KIND
from .geometry import _class_kind
from .geometry import _is_class
from .geometry import _is_tag
from .geometry import _is_tag_class
from .geometry import _metaclass_kind
from .lifecycle import _rip
from .lifecycle import _rip_field
from .memo import _class_namespace
from .memo import _metaclass_data_descriptor
from .memo import _namespace_has_callback_keys
from .memo import _physical_namespace_get
from .memo import _type_mro
from .memo import _type_name
from .state import Tagged
from .state import _guard_operation_declaration
from .state import _name_of
from .state import _state_of
from .transactions import _apply


def _check_late_binding(tag: type, name: str, value: Any) -> None:
    """Run declaration and Constant checks without holding the Pin lock."""

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


def _metaclass_setattr_tail(tag: type) -> bool:
    """Whether ``super()`` after MetaTag would run a program's setter.

    A late Tool cannot call that setter while Pin publication is locked.
    Refuse the declaration rather than silently bypassing the hook.
    """

    after_meta_tag = False
    for meta in _type_mro.__get__(type(tag)):
        if meta is MetaTag:
            after_meta_tag = True
            continue
        if not after_meta_tag:
            continue
        member = _physical_namespace_get(
                _class_namespace(meta), "__setattr__", _MISSING,
                )
        if member is not _MISSING:
            return member is not type.__setattr__
    return False


class _CategoryMeta(type):
    """Preserve the declaration identity of TOP's Python metaclasses."""

    def __new__(meta, name, bases, namespace, **kwargs):
        _refuse_observed_act('create a TOP metaclass')

        root = kwargs.pop("_topkit_meta_root", None)
        if root is _TAG_KIND and name == "MetaTag" and "MetaTag" not in globals() and bases == (type,):
            kind = _TAG_KIND
        elif root is _PIN_KIND and name == "MetaPin" and "MetaPin" not in globals() and bases == (MetaTag,):
            kind = _PIN_KIND
        else:
            if root is not None:
                raise TagDeclarationError("only TOP's metaclass roots use this bootstrap")
            kinds = tuple(_metaclass_kind(base) for base in bases)
            if not any(kind is not None for kind in kinds):
                raise TagDeclarationError("a TOP metaclass needs a TOP metaclass Base")
            kind = _PIN_KIND if any(item is _PIN_KIND for item in kinds) else _TAG_KIND
        if _META_KIND in namespace:
            raise TagDeclarationError("a TOP metaclass's declaration category cannot be supplied")
        # Bind the weak owner before subsequent descriptor/class hooks run.
        declared = {_META_KIND: _Category_Stamp(kind)}
        declared.update(namespace)
        return super().__new__(meta, name, bases, declared, **kwargs)

    def __setattr__(meta, name, value):
        _refuse_observed_act('change a TOP metaclass declaration')

        if type(name) is not str:
            name = str.__str__(name)
        if name == _META_KIND or name == "__class__":
            raise TagDeclarationError("a TOP metaclass's declaration category is fixed")
        if name == "__bases__" and issubclass(type(value), tuple):
            if meta is MetaTag or meta is MetaPin:
                raise TagDeclarationError("TOP's metaclass roots cannot change Bases")
            kinds = tuple(_metaclass_kind(base) for base in tuple.__iter__(value))
            kind = _PIN_KIND if any(item is _PIN_KIND for item in kinds) else _TAG_KIND
            if not any(item is not None for item in kinds) or kind is not _metaclass_kind(meta):
                raise TagDeclarationError("a TOP metaclass cannot change its Tag/Pin category or leave TOP")
        super().__setattr__(name, value)

    def __delattr__(meta, name):
        _refuse_observed_act('delete a TOP metaclass declaration')

        if type(name) is not str:
            name = str.__str__(name)
        if name == _META_KIND:
            raise TagDeclarationError("a TOP metaclass's declaration category is fixed")
        super().__delattr__(name)


class MetaTag(type, metaclass=_CategoryMeta, _topkit_meta_root=_TAG_KIND):
    """Metaclass of every Tag: the Tag-level acts, in language syntax."""

    def __new__(
            meta,
            name: str,
            bases: tuple[type, ...],
            namespace: dict[str, Any],
            **kwargs: Any,
            ) -> "MetaTag":
        _refuse_observed_act('create a Tag')

        if _metaclass_kind(meta) is None:
            raise TagDeclarationError("a Tag or Pin needs a declared TOP metaclass")
        pin_root = kwargs.pop("_topkit_pin_root", False)
        if pin_root:
            if meta is not MetaPin or bases or "Pin" in globals():
                raise TagDeclarationError("only the Pin declaration root uses this bootstrap")
        else:
            namespace.setdefault(
                    FIELD_SEAT,
                    _Field(),
                    )
        _check_rip_declarations(
                name,
                namespace,
                )
        _name_checks(namespace, name)
        for member_name, member in tuple(namespace.items()):
            namespace[member_name] = _guard_operation_declaration(member)

        tag = super().__new__(
                meta,
                name,
                bases,
                namespace,
                **kwargs,
                )
        _check_pin_bases(tag)
        _check_constant_declarations(tag, namespace)
        tools = _check_tool_declarations(tag, namespace)

        # Publish Tool-kind registrations together with the final physical
        # category checks. Stored namespace keys cannot call program code
        # inside this critical section.
        with _pin_publication():
            _check_pin_bases(tag, physical=True)
            if tools and _is_pin_physical(tag):
                raise TagDeclarationError(
                        f"{_type_name.__get__(tag)}.{tools[0][0]}: a Pin's"
                        " Records land as Reports of the pinned Tag;"
                        " a shared tool is a Report (§1.9)"
                        )
            _publish_tool_kinds(tag, tools)

        if _is_pin(tag) and not pin_root:
            _declarations_of(tag)   # validate Pin protocols at declaration

        return tag

    def __setattr__(
            tag,
            name: str,
            value: Any,
            ) -> None:
        _refuse_observed_act('change a Tag declaration')

        # ``setattr`` also accepts str subclasses. Their comparison and hash
        # hooks must not run while Pin publication owns its shared lock.
        if type(name) is not str:
            name = str.__str__(name)

        if name == "__bases__" and issubclass(type(value), tuple):
            _check_pin_bases(tag, bases=tuple(tuple.__iter__(value)))
        elif name == "__class__":
            if (
                    not _is_class(value)
                    or not issubclass(value, MetaTag)
                    or _metaclass_kind(value) is not _metaclass_kind(type(tag))
                    ):
                raise TagDeclarationError(
                        f"{_type_name.__get__(tag)} cannot change its Tag/Pin"
                        " category through __class__; declare a new class"
                        )
        tool_kind = _tool_kind_of_static(value)

        if tool_kind is None:
            _check_late_binding(tag, name, value)
            super().__setattr__(name, value)
            return

        tool_tags = _tool_tag_kinds(tool_kind)
        while True:
            # Hold the old binding strongly: replacing the class slot must
            # not run its finalizer while the shared Pin lock is held.
            old = _physical_namespace_get(_class_namespace(tag), name, _MISSING)
            _check_late_binding(tag, name, value)

            with _pin_publication():
                if _physical_namespace_get(
                        _class_namespace(tag), name, _MISSING,
                        ) is not old:
                    continue

                if _namespace_has_callback_keys(tag):
                    refusal = "namespace"
                elif _metaclass_data_descriptor(tag, name):
                    refusal = "descriptor"
                elif _metaclass_setattr_tail(tag):
                    refusal = "metaclass"
                elif _is_pin_locked(tag):
                    refusal = "pin"
                else:
                    pinned_kind = next(
                            (kind for kind in tool_tags if _is_pin_locked(kind)),
                            None,
                            )
                    if pinned_kind is not None:
                        refusal = "kind"
                    else:
                        # A plain class-dictionary slot publishes together
                        # with its Tool-kind registration. Descriptor slots
                        # were refused above because they can run user code.
                        type.__setattr__(tag, name, value)
                        if _physical_namespace_get(
                                _class_namespace(tag), name,
                                ) is value:
                            _note_tag_kinds(tag, tool_tags)
                        return

            if refusal == "namespace":
                raise TagDeclarationError(
                        f"{tag.__name__}.{name}: a late @Tool cannot publish"
                        " into a class namespace with custom key methods"
                        )
            if refusal == "descriptor":
                raise TagDeclarationError(
                        f"{tag.__name__}.{name}: a late @Tool cannot replace"
                        " a metaclass data descriptor"
                        )
            if refusal == "metaclass":
                raise TagDeclarationError(
                        f"{tag.__name__}.{name}: a late @Tool cannot use"
                        " a cooperative metaclass __setattr__ while Pin"
                        " publication is locked"
                        )
            if refusal == "pin":
                raise TagDeclarationError(
                        f"{tag.__name__}.{name}: a Pin's Records land as"
                        " Reports of the pinned Tag; a shared tool is a"
                        " Report (§1.9)"
                        )
            raise TagDeclarationError(
                    f"{tag.__name__}.{name}: @Tool cannot name"
                    f" {pinned_kind.__name__}, a Pin (§1.3)"
                    )

    def __delattr__(
            tag,
            name: str,
            ) -> None:
        _refuse_observed_act('delete a Tag declaration')

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
        _refuse_observed_act('apply a Tag or Pin')

        kind = _class_kind(tag)
        if kind is None:
            raise TypeError("Tagging requires a Tag or Pin receiver")

        pin = kind is _PIN_KIND
        if pin and not _is_tag(tag):
            _check_application_target(tag, target)   # Pin is a declaration root

        if target is _MISSING:
            raise TypeError(
                    f"{tag.__name__} is a Tag: apply it to a Target,"
                    f" {tag.__name__}(target)"
                    )

        selected_form = None
        if pin:
            _check_pin_target(tag, target)
        else:
            selected_form = _form_of(tag)
            if _is_class(target):
                raise TypeError(
                        f"{tag.__name__} is applied to objects, not classes"
                        )
            _refuse_host_truth(target)

        # Category is fixed at declaration. The application path
        # validates this actual Form before preparation;
        # no temporary reservation is needed to forbid Pin conversion.
        return _apply(target, tag, inputs, form=selected_form)

    def __contains__(
            tag,
            candidate: object,
            ) -> bool:
        """``agent in Wizard``: sound membership, as in the plain loop.
        ``agent in Wizard[:]`` is raw membership. A string asks for a
        keyword among the Tag's Flag Pins, never Agent membership."""

        if isinstance(candidate, str):
            return _keyword(
                    tag,
                    candidate,
                    )

        field = _field_of(tag)
        return (
                candidate in field
                and _arrest_of(candidate) is None
                and _holds_for_population(candidate)
                and candidate in field
                and _arrest_of(candidate) is None
                )

    def __instancecheck__(
            tag,
            candidate: object,
            ) -> bool:
        state = _state_of(candidate)

        if state is not None and tag in state.ever:
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
        if key is Ellipsis:
            from .safehouses import _Safehouse
            return _Safehouse(tag)
        if isinstance(key, slice):
            if key != slice(None):
                raise TypeError(
                        "Tag[:] is the whole Field; positional slices have"
                        " no meaning for a population"
                        )

            return _field_of(tag)

        return _view_of(
                key,
                tag,
                )

    def __delitem__(
            tag,
            agent: object,
            ) -> None:
        _refuse_observed_act('Rip a Tag')

        if isinstance(agent, slice):
            if agent != slice(None):
                raise TypeError("del Tag[:] Rips the whole Field; positional slices are unavailable")
            _rip_field(tag)
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
    _check_application_target(pin, target)

    if any(target is member for member in _form_of(pin)):
        raise TagCompositionError(
                f"{pin.__name__} cannot pin itself"
                )


class MetaPin(MetaTag, _topkit_meta_root=_PIN_KIND):
    """A fixed Pin category, sharing TOP's class operations with MetaTag."""


class Tag(metaclass=MetaTag):
    """A semantic category. Subclass it; its members are its contributions."""

    __slots__ = ()


class Pin(metaclass=MetaPin, _topkit_pin_root=True):
    """Declare a category of TOP classes: ``class Rare(Pin): ...``.

    A concrete Pin applies to Tags, Link Tags and other Pins. The root is
    neither an application nor a conversion function and owns no Field.
    """

    __slots__ = ()


__all__ = [
        "MetaTag",
        "MetaPin",
        "Pin",
        "Tag",
        "Tagged",
        ]
