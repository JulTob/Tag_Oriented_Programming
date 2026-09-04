"""Queries on an Agent: procedural spellings that never touch the Agent's
own attribute namespace."""

from __future__ import annotations

from typing import Any

from .geometry import _form_of
from .geometry import _leaves
from .state import _state_of


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


def Has(
        agent: object,
        *tags: type,
        ) -> bool:
    """True when every given Tag is active on the Agent."""

    return all(
            agent in tag
            for tag in tags
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
