from __future__ import annotations

"""Base, Shape, Form, and leaf relationship queries."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .runtime_types import Tag


def _tag_types() -> tuple[type, type]:
    from .runtime_types import Tag
    from .runtime_types import _Tag_Type

    return (
            Tag,
            _Tag_Type,
            )


def _is_tag_type(
        candidate: type,
        ) -> bool:
    Tag, tag_type = _tag_types()

    return (
            isinstance(
                    candidate,
                    tag_type,
                    )
            and candidate is not Tag
            )


def _direct_bases_for(
        tag: type["Tag"],
        ) -> tuple[type["Tag"], ...]:
    return tuple(
            candidate
            for candidate in tag.__bases__
            if _is_tag_type(candidate)
            )


def _form_for(
        tag: type["Tag"],
        ) -> tuple[type["Tag"], ...]:
    form: list[type[Tag]] = []
    seen: set[type[Tag]] = set()
    pending: list[
            tuple[type[Tag], bool]
            ] = [
                    (
                        tag,
                        False,
                        ),
                    ]

    while pending:
        candidate, expanded = pending.pop()

        if expanded:
            form.append(candidate)

            continue

        if candidate in seen:
            continue

        seen.add(candidate)
        pending.append(
                (
                    candidate,
                    True,
                    )
                )

        for base in reversed(
                _direct_bases_for(candidate)
                ):
            if base in seen:
                continue

            pending.append(
                    (
                        base,
                        False,
                        )
                    )

    return tuple(form)


def _leaf_tags_for(
        active_tags: list[type["Tag"]],
        ) -> tuple[type["Tag"], ...]:
    active = set(active_tags)
    direct_bases = {
            tag: _direct_bases_for(tag)
            for tag in active_tags
            }
    upward_closed = all(
            base in active
            for bases in direct_bases.values()
            for base in bases
            )

    if upward_closed:
        # The normal path needs only direct Bases. This keeps repeated runtime
        # composition linear for deep Forms.
        non_leaves = {
                base
                for bases in direct_bases.values()
                for base in bases
                }
    else:
        # A successful Imprint may deliberately rebase a Tag after earlier
        # memberships were committed. Recover semantic leaves from the live
        # Form without pretending those new Bases were applied.
        non_leaves = {
                ancestor
                for tag in active_tags
                for ancestor in _form_for(tag)
                if ancestor is not tag
                }

    return tuple(
            tag
            for tag in active_tags
            if tag not in non_leaves
            )
