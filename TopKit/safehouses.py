"""Live views of unfinished Rip work, separate from Field populations."""

from __future__ import annotations

from typing import Iterator

from .arrest import _arrest_of
from .arrest import _safehouse
from .fields import _Population


class _Safehouse(_Population):
    """A Tag's saved cleanup; the root view locates all arrested Agents."""

    _label = "Safehouse"

    def __init__(house, tag: type) -> None:
        house.tag = tag

    def __contains__(house, candidate: object) -> bool:
        arrest = _arrest_of(candidate)
        if arrest is None:
            return False
        from .tags import Tag
        return house.tag is Tag or any(run.tag is house.tag for run in arrest.runs)

    def __iter__(house) -> Iterator[object]:
        # Saved work holds an Agent until cleanup succeeds. Recheck at its
        # turn because an earlier retry may have finished a later entry.
        for arrest in list(_safehouse.values()):
            candidate = arrest.agent
            if candidate in house:
                yield candidate

    def __repr__(house) -> str:
        return f"<{house.tag.__name__} Safehouse>"
