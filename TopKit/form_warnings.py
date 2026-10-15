"""Diagnose a Shape's sibling-Base Overlay at its declaration site.

The Form's ordered collision is an authoring decision. Keep the pairs on
the Shape so an application suppresses only those already diagnosed there;
an independent Tagging or a reversed Overlay still warns at its own call.
"""

from __future__ import annotations

from contextvars import ContextVar
from os import sep
from os.path import dirname
import warnings

from .declarations import _scan
from .declarations import _takes_stored
from .declarations import _takes_underlay
from .errors import TagContractWarning
from .errors import TagOverwriteWarning
from .geometry import _direct_bases
from .geometry import _form_of
from .geometry import _related
from .memo import _class_namespace


_FORM_WARNINGS = "_TOPKIT_FORM_WARNINGS"
_Collision = tuple[type, type, str, str]  # new Tag, prior Tag, kind, name
_current: ContextVar[frozenset[_Collision]] = ContextVar(
        "topkit_form_warnings", default=frozenset(),
        )


def _declared_collisions(shape: type) -> frozenset[_Collision]:
    """Record the sibling replacements this Shape's Form declares.

    A one-Base Shape carries its Base's diagnosis forward without rescanning
    it. In a multiple-Base Form, scan each Tag's *own* declarations in the
    order Tagging lays them. A Pin or later class edit can introduce a new
    collision after declaration; that pair is absent here and still warns
    at application time.
    """

    bases = _direct_bases(shape)
    if len(bases) == 1:
        result = _class_namespace(bases[0]).get(_FORM_WARNINGS, frozenset())
        type.__setattr__(shape, _FORM_WARNINGS, result)
        return result
    if not bases:
        type.__setattr__(shape, _FORM_WARNINGS, frozenset())
        return frozenset()

    ancestors = tuple(frozenset(_form_of(base, remember=False)) for base in bases)
    actions: dict[str, type] = {}
    records: dict[str, type] = {}
    posts: dict[str, type] = {}
    constants: set[str] = set()
    collisions: set[_Collision] = set()
    introduced: list[_Collision] = []

    def note(
            member: type,
            origin: type | None,
            kind: str,
            name: str,
            function: object | None,
            ) -> None:
        if (
                origin is None
                or name in constants
                or _related(member, origin)
                ):
            return
        if function is not None:
            try:
                explicit = (
                        _takes_stored(function) if kind == "Record"
                        else _takes_underlay(function, name)
                        )
            except Exception:
                # A hostile or malformed callable keeps its existing
                # application-time failure; class definition only diagnoses
                # a replacement it can establish without running a builder.
                return
            if explicit:
                return
        collision = (member, origin, kind, name)
        collisions.add(collision)
        if not any(member in form and origin in form for form in ancestors):
            introduced.append(collision)

    for member in _form_of(shape, remember=False)[:-1]:
        # Declaration-site inspection only reads existing Bases. It must
        # not publish a lazy memo into a Base's live class dictionary.
        declarations = _scan(member)
        for kind, step in declarations.gaining_steps:
            name = step.gain_order[0]
            if kind == "delete":
                actions.pop(name, None)
                records.pop(name, None)
                posts.pop(name, None)
                constants.discard(name)
            elif kind == "action":
                function = step.actions[0][1]
                note(member, actions.get(name), "Action", name, function)
                records.pop(name, None)
                actions[name] = member
            elif kind == "record":
                function = step.records[0][1]
                note(member, records.get(name), "Record", name, function)
                actions.pop(name, None)
                records[name] = member
            else:
                for post_name, function in step.postconditions:
                    note(member, posts.get(post_name), "Postcondition",
                         post_name, function)
                    posts[post_name] = member
            constants.update(step.constants)

        # Public Operations publish an Action on admission, after Gainings.
        for name, _operation, public in declarations.operations:
            if public:
                note(member, actions.get(name), "Action", name, None)
                records.pop(name, None)
                actions[name] = member
        constants.update(declarations.header.constants)

    result = frozenset(collisions)
    type.__setattr__(shape, _FORM_WARNINGS, result)

    for member, origin, kind, name in introduced:
        category: type[Warning] = (
                TagContractWarning if kind == "Postcondition"
                else TagOverwriteWarning
                )
        suffix = " without @Underlay" if kind != "Record" else " without a stored value"
        warnings.warn(
                f"{shape.__name__}'s Form lays {member.__name__}.{name}"
                f" over {origin.__name__}.{name} (an independent Tag's {kind})"
                f"{suffix}",
                category,
                skip_file_prefixes=(dirname(__file__) + sep,),
                )
    return result


def _collisions_of(shape: type) -> frozenset[_Collision]:
    return _class_namespace(shape).get(_FORM_WARNINGS, frozenset())


def _diagnosed(
        member: type,
        origin: type,
        kind: str,
        name: str,
        ) -> bool:
    return (member, origin, kind, name) in _current.get()
