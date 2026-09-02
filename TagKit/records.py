from __future__ import annotations

"""Agent Record storage, materialization, and snapshots."""

from typing import Any

from .declarations import Record_Builder
from .declarations import _MISSING
from .declarations import _Tag_Declarations
from .declarations import _protocol_inputs
from .declarations import _require_synchronous_result
from .declarations import _takes_underlay
from .errors import TagCompositionError
from .errors import TagError
from .errors import TagResolutionError
from .access import _assigned
from .runtime_types import _Agent_State
from .runtime_types import _Tag_Snapshot
from .runtime_types import _bind_host_declaration
from .runtime_types import _existing_state_for
from .runtime_types import _host_declaration_for
from .runtime_types import _is_tag


def _capture_attribute(
        agent: object,
        name: str,
        ) -> tuple[bool, Any]:
    value = _record_value_for(
            agent,
            name,
            )

    if value is not _MISSING:
        return (
                True,
                value,
                )

    return (
            False,
            _MISSING,
            )


def _restore_attributes(
        agent: object,
        originals: dict[str, tuple[bool, Any]],
        ) -> None:
    for name, (was_instance_value, value) in originals.items():
        if was_instance_value:
            _set_record_value(
                    agent,
                    name,
                    value,
                    )
            continue

        try:
            _delete_record_value(
                    agent,
                    name,
                    )
        except AttributeError:
            pass


def _record_underlay(
        agent: object,
        name: str,
        ) -> Any:
    # The current value of a Record is an Agent instance value only -- never
    # the builder declaration retained by its Tag.
    return _record_value_for(
            agent,
            name,
            )


def _record_host_type(
        agent: object,
        ) -> type:
    state = _existing_state_for(agent)

    return (
            state.host_type
            if state is not None
            else type(agent)
            )


def _record_descriptor_for(
        agent: object,
        name: str,
        ) -> Any:
    declaration = _host_declaration_for(
            _record_host_type(agent),
            name,
            )

    if declaration is _MISSING:
        return _MISSING

    if (
            getattr(
                    declaration,
                    "__set__",
                    None,
                    )
            is None
            and getattr(
                    declaration,
                    "__delete__",
                    None,
                    )
            is None
            ):
        return _MISSING

    return declaration


def _record_value_for(
        agent: object,
        name: str,
        ) -> Any:
    descriptor = _record_descriptor_for(
            agent,
            name,
            )

    if descriptor is not _MISSING:
        try:
            return _bind_host_declaration(
                    agent,
                    descriptor,
                    )
        except AttributeError:
            return _MISSING

    try:
        namespace = object.__getattribute__(
                agent,
                "__dict__",
                )
    except AttributeError:
        return _MISSING

    if name in namespace:
        return namespace[name]

    return _MISSING


def _set_record_value(
        agent: object,
        name: str,
        value: Any,
        ) -> None:
    value = _assigned(value)
    descriptor = _record_descriptor_for(
            agent,
            name,
            )
    setter = (
            getattr(
                    descriptor,
                    "__set__",
                    None,
                    )
            if descriptor is not _MISSING
            else None
            )

    if setter is not None:
        setter(
                agent,
                value,
                )

        return

    object.__setattr__(
            agent,
            name,
            value,
            )


def _delete_record_value(
        agent: object,
        name: str,
        ) -> None:
    descriptor = _record_descriptor_for(
            agent,
            name,
            )
    deleter = (
            getattr(
                    descriptor,
                    "__delete__",
                    None,
                    )
            if descriptor is not _MISSING
            else None
            )

    if deleter is not None:
        deleter(
                agent,
                )

        return

    object.__delattr__(
            agent,
            name,
            )


def _materialize_value(
        target: object,
        owner: type["Tag"],
        name: str,
        builder: Record_Builder,
        underlay: Any,
        contribution_kind: str,
    inputs: dict[str, Any],
        ) -> Any:
    try:
        if not _takes_underlay(builder):
            value = builder(
                    target,
                    **_protocol_inputs(
                            builder,
                            inputs,
                            1,
                            ),
                    )
        else:
            if underlay is _MISSING:
                raise TagResolutionError(
                        f"{contribution_kind} {owner.__qualname__}.{name}"
                        " requires a visible Underlay"
                        )

            value = builder(
                    target,
                    lambda: underlay,
                    **_protocol_inputs(
                            builder,
                            inputs,
                            2,
                            ),
                    )

        return _require_synchronous_result(
                value,
                f"{contribution_kind} {owner.__qualname__}.{name}",
                allow_generator=True,
                )
    except TagError:
        raise
    except Exception as error:
        raise TagCompositionError(
                f"{contribution_kind} {owner.__qualname__}.{name}"
                " failed to materialize"
                ) from error


def _materialize_records(
        agent: object,
        tag: type["Tag"],
        declarations: _Tag_Declarations,
        deleted_before_tagging: set[str],
        inputs: dict[str, Any],
        ) -> dict[str, Any]:
    values: dict[str, Any] = {}

    for name, builder in declarations.records:
        if name in deleted_before_tagging:
            underlay = _MISSING
        else:
            underlay = _record_underlay(
                    agent,
                    name,
                    )

        values[name] = _materialize_value(
                    agent,
                    tag,
                    name,
                    builder,
                    underlay,
                    "Record",
                    inputs,
                    )

    return values


def _apply_record_values(
        agent: object,
        values: dict[str, Any],
        ) -> None:
    for name, value in values.items():
        _set_record_value(
                agent,
                name,
                value,
                )


def _commit_deletions(
        agent: object,
        original_state: _Agent_State,
        new_state: _Agent_State,
        ) -> None:
    new_deletions = new_state.deleted - original_state.deleted

    for name in new_deletions:
        if _record_value_for(
                agent,
                name,
                ) is _MISSING:
            continue

        try:
            _delete_record_value(
                    agent,
                    name,
                    )
        except (
                AttributeError,
                TypeError,
                ):
            # A read-only host descriptor cannot be physically removed.
            # The committed Delete layer still masks it semantically.
            pass


def _snapshot_for(
        agent: object,
        state: _Agent_State,
        ) -> _Tag_Snapshot:
    field_reports: dict[
            str,
            tuple[type["Tag"], Any],
            ] = {}
    field_operations: dict[
            str,
            tuple[type["Tag"], Operation_Body],
            ] = {}
    target_is_tag = _is_tag(agent)

    for origin in state.active_tags:
        if not target_is_tag:
            for name in state.field_deletions.get(
                    origin,
                    set(),
                    ):
                field_reports.pop(
                        name,
                        None,
                        )
                field_operations.pop(
                        name,
                        None,
                        )

        for name, value in state.field_reports.get(
                origin,
                {},
                ).items():
            field_reports[name] = (
                    origin,
                    value,
                    )

        for name, operation in state.field_operations.get(
                origin,
                {},
                ).items():
            field_operations[name] = (
                    origin,
                    operation,
                    )

    if target_is_tag:
        records = {
                name: value
                for name, value in state.record_values.items()
                if name not in state.deleted
                }
        deleted = (
                state.deleted
                - field_reports.keys()
                - field_operations.keys()
                )
    else:
        records: dict[str, Any] = {}
        deleted = state.deleted

        for name in state.record_builders:
            if name in state.deleted:
                continue

            value = _record_underlay(
                    agent,
                    name,
                    )

            if value is not _MISSING:
                records[name] = value

    return _Tag_Snapshot(
            actions=dict(state.actions),
            records=records,
            reports=field_reports,
            operations=field_operations,
            preconditions=dict(state.preconditions),
            postconditions=dict(state.postconditions),
            deleted=frozenset(deleted),
            )
