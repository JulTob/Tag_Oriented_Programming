"""Queries on an Agent: procedural spellings that never touch the Agent's
own attribute namespace."""

from __future__ import annotations

from typing import Any

from .access import _keyword
from .declarations import _is_link
from .geometry import _form_of
from .geometry import _leaves
from .state import _name_of
from .state import _state_of


def Form(
        tag: type,
        ) -> tuple[type, ...]:
    """The Base-first closure of a Tag, ending with the Tag itself."""

    return _form_of(tag)


def Apply(
        target: object,
        *tags: type,
        **inputs: Any,
        ) -> object:
    """Apply several Tags in order; return the same Target."""

    for tag in tags:
        tag(
                target,
                **inputs,
                )

    return target


def Keyword(
        agent: object,
        *words: type | str,
        ) -> bool:
    """True when the Agent carries every given keyword: the name, a listed
    word (``@Flag("Wolf")``), or the class of an active Flag Tag. On a Tag,
    its Flag Pins. Works on any object, tagged or not."""

    return all(
            _keyword(agent, word)
            for word in words
            )


def Tags(
        agent: object,
        ) -> tuple[type, ...]:
    """The active leaf Tags, in application order."""

    state = _state_of(agent)

    if state is None:
        return ()

    return _leaves(_own_tags(state.active))


def _own_tags(
        active: list[type],
        ) -> list[type]:
    """The Agent's own Tags: never the Links that hold it as a Contact,
    since nothing on a Contact names the Agent who links her
    (STEP-SPEC-22 rule 6.2)."""

    return [
            tag
            for tag in active
            if not _is_link(tag)
            ]


def Outline(
        agent: object,
        indent: str = "  ",
        ) -> str:
    """A readable picture of the Agent's Geometry: host, then each leaf's
    Form from Base to Shape."""

    state = _state_of(agent)
    host = _name_of(agent)
    lines = [host]

    if state is None:
        return host

    active = set(state.active)

    for leaf in _leaves(_own_tags(state.active)):
        depth = 1

        for tag in _form_of(leaf):
            if tag in active:
                lines.append(f"{indent * depth}{tag.__name__}")
                depth += 1

    return "\n".join(lines)
