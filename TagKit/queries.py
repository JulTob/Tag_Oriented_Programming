"""Queries on an Agent: procedural spellings that never touch the Agent's
own attribute namespace."""

from __future__ import annotations

from typing import Any

from .geometry import _form_of
from .geometry import _leaves
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
    """True when the Agent carries every given keyword: the name, or the
    class, of an active Flag Tag. Works on any object, tagged or not."""

    from .access import _keyword

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

    return _leaves(state.active)


def Outline(
        agent: object,
        indent: str = "  ",
        ) -> str:
    """A readable picture of the Agent's Geometry: host, then each leaf's
    Form from Base to Shape."""

    state = _state_of(agent)
    host = type(agent).__name__
    lines = [host]

    if state is None:
        return host

    active = set(state.active)

    for leaf in _leaves(state.active):
        depth = 1

        for tag in _form_of(leaf):
            if tag in active:
                lines.append(f"{indent * depth}{tag.__name__}")
                depth += 1

    return "\n".join(lines)
