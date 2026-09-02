from __future__ import annotations

"""Read-only Tag, contribution, and membership queries."""

from typing import Any
from typing import Callable

from .declarations import _MISSING
from .geometry import _leaf_tags_for
from .runtime_types import Tag
from .runtime_types import _Agent_State
from .runtime_types import _Tag_Type
from .runtime_types import _existing_state_for
from .runtime_types import _query_record_names_for
from .runtime_types import _query_state_for


def _validate_tags(
        tags: tuple[type[Tag], ...],
        ) -> None:
    for tag in tags:
        if isinstance(
                tag,
                _Tag_Type,
                ):
            continue

        raise TypeError(
                f"{tag!r} is not a Tag class"
                )


def _committed_tags_for(
        target: object,
        ) -> list[type[Tag]]:
    state = _existing_state_for(target)

    if state is None:
        return []

    return [
            tag
            for tag in state.active_tags
            if target in tag._tagkit_field
            ]


def Tags(
        target: object,
        ) -> tuple[type[Tag], ...]:
    """Return the committed leaf Tags currently classifying a Target."""

    return tuple(
            reversed(
                    _leaf_tags_for(
                            _committed_tags_for(target)
                            )
                    )
            )


def _adapts_callable(
        candidate: Callable[..., Any],
        probe: object,
        ) -> bool:
    expected = getattr(
            probe,
            "__func__",
            probe,
            )
    current: object = candidate
    seen: set[int] = set()

    while callable(current) and id(current) not in seen:
        if current is expected:
            return True

        seen.add(id(current))
        current = getattr(
                current,
                "__wrapped__",
                _MISSING,
                )

    return False


def _contribution_matches(
        state: _Agent_State,
        probe: object,
        ) -> frozenset[tuple[str, str]]:
    if not callable(probe):
        return frozenset()

    matches: set[tuple[str, str]] = set()

    for name, action in state.actions.items():
        origin = state.action_origins.get(name)

        if (
                isinstance(
                        origin,
                        _Tag_Type,
                        )
                and origin in state.ever_tags
                and _adapts_callable(
                        action,
                        probe,
                        )
                ):
            matches.add(
                    (
                        "action",
                        name,
                        )
                    )

    for name, builder in state.record_builders.items():
        origin = state.record_origins.get(name)

        if (
                isinstance(
                        origin,
                        _Tag_Type,
                        )
                and origin in state.ever_tags
                and _adapts_callable(
                        builder,
                        probe,
                        )
                ):
            matches.add(
                    (
                        "record",
                        name,
                        )
                    )

    return frozenset(matches)


def Has(
        target: object,
        *probes: object,
        ) -> bool:
    """Report whether a Target carries every Tag, Tag name, or contribution."""

    active_tags = _committed_tags_for(target)
    state = _query_state_for(target)
    record_names = _query_record_names_for(
            target,
            state,
            )

    def Carries(
            probe: object,
            ) -> bool:
        if isinstance(
                probe,
                _Tag_Type,
                ):
            return target in probe._tagkit_field

        if isinstance(
                probe,
                str,
                ):
            return any(
                    tag.__name__.casefold() == probe.casefold()
                    for tag in active_tags
                    )

        if state is None:
            return False

        for kind, name in _contribution_matches(
                state,
                probe,
                ):
            if (
                    kind == "action"
                    and name in state.actions
                    ):
                return True

            if kind != "record":
                continue

            if name in record_names:
                return True

        return False

    return all(
            Carries(probe)
            for probe in probes
            )
