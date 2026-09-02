from __future__ import annotations

"""Tag-on-Tag Pin composition and rollback."""

from functools import wraps
from typing import Any

from .contracts import _evaluate_conditions
from .contracts import _layer_conditions
from .declarations import Operation_Body
from .declarations import _MISSING
from .declarations import _Tag_Declarations
from .declarations import _declarations_cache
from .declarations import _declarations_for
from .declarations import _dunder
from .declarations import _kind_of
from .declarations import _report_value
from .errors import TagCompositionError
from .errors import TagPreconditionError
from .geometry import _form_for
from .overlays import _install_declarations
from .records import _materialize_value
from .records import _snapshot_for
from .runtime_types import _Agent_State
from .runtime_types import _PIN_STATE
from .runtime_types import _PIN_PROTECTED_MEMBERS
from .runtime_types import _Tag_Namespace_Snapshot
from .runtime_types import _delete_state
from .runtime_types import _existing_state_for
from .runtime_types import _set_state
from .runtime_types import _state_for


def _transaction_helper(
        name: str,
        ) -> Any:
    from . import transactions

    return getattr(
            transactions,
            name,
            )


def _apply_form_layers(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    return _transaction_helper( "_apply_form_layers" )(
            *args,
            **kwargs,
            )


def _capture_mutable_snapshots(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    return _transaction_helper( "_capture_mutable_snapshots" )(
            *args,
            **kwargs,
            )


def _commit_new_memberships(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    return _transaction_helper( "_commit_new_memberships" )(
            *args,
            **kwargs,
            )


def _committed_query_boundary(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    return _transaction_helper( "_committed_query_boundary" )(
            *args,
            **kwargs,
            )


def _remove_new_memberships(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    return _transaction_helper( "_remove_new_memberships" )(
            *args,
            **kwargs,
            )


def _restore_mutable_snapshots(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    return _transaction_helper( "_restore_mutable_snapshots" )(
            *args,
            **kwargs,
            )


def _tagging_boundary(
        *args: Any,
        **kwargs: Any,
        ) -> Any:
    return _transaction_helper( "_tagging_boundary" )(
            *args,
            **kwargs,
            )


def _validate_pin_application(
        tag: type["Tag"],
        ) -> None:
    """Protect Tag identity during Pinning."""

    form = _form_for(tag)

    for candidate in form:
        declarations = _declarations_for(candidate)
        tag_scope_names = (
                *(name for name, _function in declarations.actions),
                *(name for name, _builder in declarations.records),
                *declarations.deletions,
                )

        for name in tag_scope_names:
            if (
                    _dunder(name)
                    or name in _PIN_PROTECTED_MEMBERS
                ):
                raise TagCompositionError(
                        "Pinning cannot replace"
                        f" structural member {name!r}"
                        )


def _native_tag_report(
        target: type["Tag"],
        name: str,
        ) -> Any:
    for provider in target.__mro__:
        namespace = type.__getattribute__(
                provider,
                "__dict__",
                )
        attribute = namespace.get(
                name,
                _MISSING,
                )

        report_value = _report_value(
                name,
                attribute,
                )

        if report_value is not _MISSING:
            return report_value

        if attribute is not _MISSING:
            return _MISSING

    return _MISSING


def _native_tag_operation(
        target: type["Tag"],
        name: str,
        ) -> Action_Body | None:
    for provider in target.__mro__:
        namespace = type.__getattribute__(
                provider,
                "__dict__",
                )
        attribute = namespace.get(
                name,
                _MISSING,
                )

        if attribute is _MISSING:
            continue

        if (
                not isinstance(
                        attribute,
                        classmethod,
                        )
                or _kind_of(attribute) != "operation"
                ):
            return None

        operation = attribute.__func__

        @wraps(operation)
        def Call(
                pinned_tag: type["Tag"],
                *args: Any,
                _operation: Operation_Body = operation,
                **kwargs: Any,
                ) -> Any:
            return _operation(
                    pinned_tag,
                    *args,
                    **kwargs,
                    )

        return Call

    return None


def _seed_native_tag_operations(
        state: _Agent_State,
        target: type["Tag"],
        declarations: _Tag_Declarations,
        ) -> None:
    for name, _function in declarations.actions:
        if (
                name in state.actions
                or name in state.deleted
                ):
            continue

        native = _native_tag_operation(
                target,
                name,
                )

        if native is None:
            continue

        state.actions[name] = native
        state.action_origins[name] = target


def _validate_pin_contribution_kinds(
        target: type["Tag"],
        state: _Agent_State,
        declarations: _Tag_Declarations,
        ) -> None:
    for name, _function in declarations.actions:
        if name in state.deleted:
            continue

        if (
                name in state.record_builders
                or _native_tag_report(
                        target,
                        name,
                        ) is not _MISSING
                ):
            raise TagCompositionError(
                    f"Tag-scope Operation {name!r}"
                    " conflicts with a Tag Report"
                    )

    for name, _builder in declarations.records:
        if name in state.deleted:
            continue

        if (
                name in state.actions
                or _native_tag_operation(
                        target,
                        name,
                        ) is not None
                ):
            raise TagCompositionError(
                    f"Tag-scope Report {name!r}"
                    " conflicts with a Tag Operation"
                    )


def _install_pin_declarations(
        target: type["Tag"],
        state: _Agent_State,
        tag: type["Tag"],
        declarations: _Tag_Declarations,
        inputs: dict[str, Any],
        ) -> None:
    """Install declarations without deleting Pin Field resources."""

    prior_deletions = set(state.deleted)
    preserved: dict[
            str,
            dict[str, Any],
            ] = {
            name: {
                "precondition": state.preconditions.get(
                        name,
                        _MISSING,
                        ),
                "postcondition": state.postconditions.get(
                        name,
                        _MISSING,
                        ),
                "report": state.reports.get(
                        name,
                        _MISSING,
                        ),
                "operation": state.operations.get(
                        name,
                        _MISSING,
                        ),
                }
            for name in declarations.deletions
            }

    _install_declarations(
            target,
            state,
            tag,
            declarations,
            inputs,
            )

    scopes = (
            (
                "precondition",
                state.preconditions,
                ),
            (
                "postcondition",
                state.postconditions,
                ),
            (
                "report",
                state.reports,
                ),
            (
                "operation",
                state.operations,
                ),
            )

    for name, values in preserved.items():
        for scope, contributions in scopes:
            value = values[scope]

            if value is not _MISSING:
                contributions[name] = value

    reintroduced = {
            *(name for name, _function in declarations.actions),
            *(name for name, _builder in declarations.records),
            }
    state.deleted.update(
            prior_deletions
            - reintroduced
            )
    state.deleted.update(
            declarations.deletions
            )


def _pin_report_underlay(
        target: type["Tag"],
        state: _Agent_State,
        name: str,
        ) -> Any:
    if name in state.deleted:
        return _MISSING

    if name in state.record_builders:
        return state.record_values.get(
                name,
                _MISSING,
                )

    return _native_tag_report(
            target,
            name,
            )


def _materialize_pin_reports(
        target: type["Tag"],
        tag: type["Tag"],
        declarations: _Tag_Declarations,
        prior_state: _Agent_State,
        inputs: dict[str, Any],
        ) -> dict[str, Any]:
    values: dict[str, Any] = {}

    for name, builder in declarations.records:
        underlay = _pin_report_underlay(
                target,
                prior_state,
                name,
                )

        values[name] = _materialize_value(
                    target,
                    tag,
                    name,
                    builder,
                    underlay,
                    "Tag-scope Report",
                    inputs,
                    )

    return values


def _capture_pinned_tag_namespace(
        target: type["Tag"],
        ) -> _Tag_Namespace_Snapshot:
    namespace = type.__getattribute__(
            target,
            "__dict__",
            )

    captured_namespace = {
            name: value
            for name, value in namespace.items()
            if name != _PIN_STATE
            }

    return _Tag_Namespace_Snapshot(
            namespace=captured_namespace,
            mutable_values=_capture_mutable_snapshots(
                    iter(captured_namespace.values())
                    ),
            name=type.__getattribute__(
                    target,
                    "__name__",
                    ),
            qualname=type.__getattribute__(
                    target,
                    "__qualname__",
                    ),
            bases=type.__getattribute__(
                    target,
                    "__bases__",
                    ),
            )


def _restore_pinned_tag_namespace(
        target: type["Tag"],
        captured: _Tag_Namespace_Snapshot,
        ) -> None:
    _restore_mutable_snapshots(
            captured.mutable_values
            )

    protected = {
            _PIN_STATE,
            "__dict__",
            "__weakref__",
            }
    current = type.__getattribute__(
            target,
            "__dict__",
            )

    for name in tuple(current):
        if (
                name in captured.namespace
                or name in protected
                ):
            continue

        try:
            type.__delattr__(
                    target,
                    name,
                    )
        except (
                AttributeError,
                TypeError,
                ):
            pass

    metadata = (
            (
                "__bases__",
                captured.bases,
                ),
            (
                "__name__",
                captured.name,
                ),
            (
                "__qualname__",
                captured.qualname,
                ),
            )

    for name, value in metadata:
        try:
            type.__setattr__(
                    target,
                    name,
                    value,
                    )
        except (
                AttributeError,
                TypeError,
                ):
            pass

    for name, value in captured.namespace.items():
        if name in protected:
            continue

        try:
            type.__setattr__(
                    target,
                    name,
                    value,
                    )
        except (
                AttributeError,
                TypeError,
                ):
            pass

    _declarations_cache.pop(
            target,
            None,
            )


def _apply_pin_layer(
        target: type["Tag"],
        tag: type["Tag"],
        inputs: dict[str, Any],
        ) -> type["Tag"]:
    """Apply one already ordered Pin layer to a Tag Target."""

    state = _state_for(target)

    if tag in state.active_tags:
        return target

    declarations = _declarations_with_pins(tag)
    candidate = state.Copy()

    _validate_pin_contribution_kinds(
            target,
            candidate,
            declarations,
            )
    _seed_native_tag_operations(
            candidate,
            target,
            declarations,
            )
    _install_pin_declarations(
            target,
            candidate,
            tag,
            declarations,
            inputs,
            )

    candidate.active_tags.append(tag)

    _set_state(
            target,
            candidate,
            )

    try:
        _evaluate_conditions(
                _layer_conditions(
                        candidate.preconditions,
                        declarations.preconditions,
                        ),
                target,
                TagPreconditionError,
                "Precondition",
                inputs,
                )

        values = _materialize_pin_reports(
                target,
                tag,
                declarations,
                state,
                inputs,
                )
        candidate.record_values.update(values)

        candidate.snapshots[tag] = _snapshot_for(
                target,
                candidate,
                )
    except BaseException:
        _set_state(
                target,
                state,
                )
        raise

    return target


def _apply_pin_one(
        target: type["Tag"],
        tag: type["Tag"],
        inputs: dict[str, Any],
        ) -> type["Tag"]:
    """Apply one Pin and every missing Base to a Tag Target."""

    _apply_form_layers(
            target,
            tag,
            inputs,
            _apply_pin_layer,
            )

    return target


def _run_pin_transaction(
        target: type["Tag"],
        tag: type["Tag"],
        inputs: dict[str, Any] | None = None,
        ) -> type["Tag"]:
    """Pin one Tag atomically to another Tag."""

    _validate_pin_application(
            tag,
            )

    entry_state = _existing_state_for(target)
    entry_tags = (
            frozenset(entry_state.active_tags)
            if entry_state is not None
            else frozenset()
            )
    entry_namespace = _capture_pinned_tag_namespace(target)
    application_inputs = inputs or {}

    with _committed_query_boundary(
            target,
            entry_state,
            ):
        try:
            result = _apply_pin_one(
                    target,
                    tag,
                    application_inputs,
                    )
            _commit_new_memberships(
                    target,
                    entry_tags,
                    )
        except BaseException:
            _remove_new_memberships(
                    target,
                    entry_tags,
                    )

            _restore_pinned_tag_namespace(
                    target,
                    entry_namespace,
                    )

            if entry_state is not None:
                _set_state(
                        target,
                        entry_state,
                        )
            else:
                _delete_state(target)

            raise

    return result


def _apply_pin_transaction(
        target: type["Tag"],
        tag: type["Tag"],
        inputs: dict[str, Any] | None = None,
        ) -> type["Tag"]:
    state = _existing_state_for(target)

    if state is not None and tag in state.active_tags:
        return target

    entry_tags = (
            frozenset(state.active_tags)
            if state is not None
            else frozenset()
            )
    application_inputs = inputs or {}

    with _tagging_boundary(
            target,
            tag,
            ) as should_apply:
        if not should_apply:
            return target

        result = _run_pin_transaction(
                target,
                tag,
                application_inputs,
                )

    _transaction_helper( "_run_committed_imprints" )(
            target,
            entry_tags,
            application_inputs,
            )
    _transaction_helper( "_run_committed_postconditions" )(
            target,
            application_inputs,
            )

    return result


def _declarations_with_pins(
        tag: type["Tag"],
        ) -> _Tag_Declarations:
    """Include Pin-provided Tag contributions in new Agent snapshots."""

    declarations = _declarations_for(tag)
    target_state = _existing_state_for(tag)

    if target_state is None:
        return declarations

    tag_scope_names = (
            target_state.actions.keys()
            | target_state.record_builders.keys()
            )
    native_reports = tuple(
            (
                name,
                value,
                )
            for name, value in declarations.reports
            if (
                name not in target_state.deleted
                and name not in tag_scope_names
                )
            )
    native_operations = tuple(
            (
                name,
                operation,
                )
            for name, operation in declarations.operations
            if (
                name not in target_state.deleted
                and name not in tag_scope_names
                )
            )
    pin_reports = tuple(
            (
                name,
                value,
                )
            for name, value in target_state.record_values.items()
            if name not in target_state.deleted
            )
    pin_operations = tuple(
            (
                name,
                operation,
                )
            for name, operation in target_state.actions.items()
            if name not in target_state.deleted
            )

    return _Tag_Declarations(
            actions=declarations.actions,
            records=declarations.records,
            imprints=declarations.imprints,
            preconditions=declarations.preconditions,
            postconditions=declarations.postconditions,
            deletions=declarations.deletions,
            reports=(
                *native_reports,
                *pin_reports,
                ),
            operations=(
                *native_operations,
                *pin_operations,
                ),
            rips=declarations.rips,
            )
