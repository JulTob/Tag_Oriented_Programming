from __future__ import annotations

"""Atomic Agent Tagging, rollback, Rip, and Scope."""

from contextlib import contextmanager
from contextvars import ContextVar
from types import GetSetDescriptorType
from types import MemberDescriptorType
from typing import Any
from typing import Iterator

from .contracts import _evaluate_conditions
from .contracts import _layer_conditions
from .declarations import _MISSING
from .declarations import _require_synchronous_result
from .declarations import _run_protocol
from .errors import ImprintingError
from .errors import TagCompositionError
from .errors import TagError
from .errors import TagPostconditionError
from .errors import TagPreconditionError
from .errors import TagResolutionError
from .geometry import _direct_bases_for
from .overlays import _install_declarations
from .pins import _capture_pinned_tag_namespace
from .pins import _declarations_with_pins
from .pins import _restore_pinned_tag_namespace
from .queries import _validate_tags
from .records import _apply_record_values
from .records import _capture_attribute
from .records import _commit_deletions
from .records import _materialize_records
from .records import _restore_attributes
from .records import _snapshot_for
from .runtime_types import Tag
from .runtime_types import _Agent_State
from .runtime_types import _Committed_Query
from .runtime_types import _Instance_Snapshot
from .runtime_types import _Mutable_Snapshot
from .runtime_types import _Slot_Snapshot
from .runtime_types import _Tag_Namespace_Snapshot
from .runtime_types import _Tagging_Transaction
from .runtime_types import _actualize_runtime_type
from .runtime_types import _committed_queries
from .runtime_types import _delete_state
from .runtime_types import _existing_state_for
from .runtime_types import _is_tag
from .runtime_types import _restore_runtime_type
from .runtime_types import _record_names_for
from .runtime_types import _runtime_type_for
from .runtime_types import _set_state
from .runtime_types import _state_for
from .runtime_types import _validate_agent_state_slot
from weakref import WeakKeyDictionary


_slot_descriptors_cache = WeakKeyDictionary()
_tagging_transactions = ContextVar(
        "tagkit_tagging_transactions",
        default=(),
        )
_checkpoint_controls = ContextVar(
        "tagkit_checkpoint_controls",
        default=(),
        )
_imprint_tagging = ContextVar(
        "tagkit_imprint_tagging",
        default=False,
        )


def _active_checkpoint_for(
        target: object,
        ) -> "_Checkpoint_Control | None":
    for checkpoint in reversed(
            _checkpoint_controls.get()
            ):
        if (
                checkpoint._active
                and checkpoint._target is target
                ):
            return checkpoint

    return None


def _tagging_boundary_is_active(
        target: object,
        ) -> bool:
    identity = id(target)

    return any(
            transaction.active
            and transaction.identity == identity
            for transaction in _tagging_transactions.get()
            )


def _imprint_tagging_is_active() -> bool:
    return _imprint_tagging.get()


@contextmanager
def _imprint_protocol() -> Iterator[None]:
    token = _imprint_tagging.set(True)

    try:
        yield
    finally:
        _imprint_tagging.reset(token)


def _run_imprints(
        target: object,
        imprints: tuple,
        inputs: dict[str, Any],
        ) -> None:
    """Run Imprints after the Tag has already applied.

    Nested Tagging is an ordinary later call. Its Precondition,
    Postcondition, Resolution, or Imprinting failures keep their type.
    Other failures become ImprintingError. Neither rolls back this Tag.
    """

    with _imprint_protocol():
        for imprint in imprints:
            try:
                _run_protocol(
                        imprint,
                        target,
                        inputs,
                        )
            except (
                    TagPreconditionError,
                    TagPostconditionError,
                    ImprintingError,
                    TagResolutionError,
                    ):
                raise
            except Exception as error:
                raise ImprintingError(
                        f"Imprint {imprint.__qualname__} failed"
                        ) from error


def _run_committed_imprints(
        target: object,
        entry_tags: frozenset[type["Tag"]],
        inputs: dict[str, Any],
        ) -> None:
    """Write into Tags that this call has already committed."""

    state = _existing_state_for(target)
    added = _tags_added_since(
            state,
            entry_tags,
            )

    for tag in added:
        declarations = _declarations_with_pins(tag)
        _run_imprints(
                target,
                declarations.imprints,
                inputs,
                )


def _run_committed_postconditions(
        target: object,
        inputs: dict[str, Any],
        ) -> None:
    """Inspect an already applied Tag. Failure does not un-apply it."""

    state = _existing_state_for(target)

    if (
            state is None
            or not state.postconditions
            ):
        return

    _evaluate_conditions(
            state.postconditions,
            target,
            TagPostconditionError,
            "Postcondition",
            inputs,
            )


@contextmanager
def _committed_query_boundary(
        target: object,
        state: _Agent_State | None,
        ) -> Iterator[None]:
    if _active_checkpoint_for(target) is not None:
        yield

        return

    query = _Committed_Query(
            target=target,
            state=state,
            record_names=_record_names_for(
                    target,
                    state,
                    ),
            )
    token = _committed_queries.set(
            (
                *_committed_queries.get(),
                query,
                )
            )

    try:
        yield
    finally:
        query.active = False
        _committed_queries.reset(token)


@contextmanager
def _tagging_boundary(
        target: object,
        tag: type["Tag"],
        ) -> Iterator[bool]:
    transaction_key = id(target)
    transactions = _tagging_transactions.get()

    if any(
            transaction.active
            and transaction.identity == transaction_key
            for transaction in transactions
            ):
        state = _existing_state_for(target)

        if (
                state is not None
                and tag in state.active_tags
                ):
            yield False

            return

        raise TagCompositionError(
                "Re-entrant Tag application on the same Target is only"
                " allowed from an Imprint; declare a required"
                " relationship through Bases or a Shape"
                )

    transaction = _Tagging_Transaction(
            identity=transaction_key,
            )
    token = _tagging_transactions.set(
            (
                *transactions,
                transaction,
                )
            )

    try:
        yield True
    finally:
        # Contexts copied into child asyncio Tasks keep this same boundary
        # object. Marking it inactive prevents a completed parent Tagging from
        # becoming a false re-entrancy failure in the child.
        transaction.active = False
        _tagging_transactions.reset(
                token
                )


def _target_is_tagging(
        target: object,
        ) -> bool:
    return (
            _tagging_boundary_is_active( target )
            or _active_checkpoint_for(target) is not None
            )


def _capture_mutable_snapshots(
        values: Iterator[object],
        ) -> tuple[_Mutable_Snapshot, ...]:
    snapshots: list[_Mutable_Snapshot] = []
    seen: set[int] = set()

    for value in values:
        pending = [
                value,
                ]

        while pending:
            current = pending.pop()
            value_type = type(current)

            if value_type not in (
                    bytearray,
                    dict,
                    list,
                    set,
                    tuple,
                    ):
                continue

            identity = id(current)

            if identity in seen:
                continue

            seen.add(identity)

            if value_type is tuple:
                pending.extend(
                        reversed(current)
                        )

                continue

            if value_type is list:
                snapshot: object = tuple(current)
                children = snapshot
            elif value_type is dict:
                snapshot = tuple(current.items())
                children = ()
            elif value_type is set:
                snapshot = tuple(current)
                children = snapshot
            elif value_type is bytearray:
                snapshot = bytes(current)
                children = ()
            else:
                continue

            snapshots.append(
                    _Mutable_Snapshot(
                            value=current,
                            snapshot=snapshot,
                            )
                    )

            if value_type is dict:
                for key, item in reversed(snapshot):
                    pending.append(item)
                    pending.append(key)
            else:
                pending.extend(
                        reversed(children)
                        )

    return tuple(snapshots)


def _restore_mutable_snapshots(
        snapshots: tuple[_Mutable_Snapshot, ...],
        ) -> None:
    for captured in snapshots:
        value = captured.value
        snapshot = captured.snapshot

        if type(value) is list:
            value[:] = snapshot
        elif type(value) is dict:
            value.clear()
            value.update(snapshot)
        elif type(value) is set:
            value.clear()
            value.update(snapshot)
        elif type(value) is bytearray:
            value[:] = snapshot


def _apply_form_layers(
        target: object,
        tag: type["Tag"],
        inputs: dict[str, Any],
        apply_layer: Callable[..., object],
        ) -> object:
    """Apply live Bases before each layer without consuming call-stack depth.

    The Form is discovered while it is traversed. Nested Tags applied from
    a later Imprint cannot change this call's Base walk; they are ordinary
    later Taggings after this Form has applied.
    """

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
        state = _existing_state_for(target)

        if (
                state is not None
                and candidate in state.active_tags
                ):
            continue

        if expanded:
            apply_layer(
                    target,
                    candidate,
                    inputs,
                    )

            continue

        pending.append(
                (
                    candidate,
                    True,
                    )
                )

        for base in reversed(
                _direct_bases_for(candidate)
                ):
            pending.append(
                    (
                        base,
                        False,
                        )
                    )

    return target


def _tags_added_since(
        state: _Agent_State | None,
        entry_tags: frozenset[type["Tag"]],
        ) -> tuple[type["Tag"], ...]:
    if state is None:
        return ()

    return tuple(
            tag
            for tag in state.active_tags
            if tag not in entry_tags
            )


def _commit_new_memberships(
        target: object,
        entry_tags: frozenset[type["Tag"]],
        ) -> None:
    if _active_checkpoint_for(target) is not None:
        return

    state = _existing_state_for(target)
    added = _tags_added_since(
            state,
            entry_tags,
            )

    for tag in added:
        tag._tagkit_field._add(target)

    if state is not None:
        state.ever_tags.update(added)


def _remove_new_memberships(
        target: object,
        entry_tags: frozenset[type["Tag"]],
        ) -> None:
    state = _existing_state_for(target)

    for tag in _tags_added_since(
            state,
            entry_tags,
            ):
        tag._tagkit_field._remove(target)


def _apply_agent_layer(
        agent: object,
        tag: type["Tag"],
        inputs: dict[str, Any],
        ) -> object:
    """Apply one already ordered Tag layer to an Agent."""
    state = _state_for(agent)

    if tag in state.active_tags:
        return agent

    declarations = _declarations_with_pins(tag)
    candidate = state.Copy()
    original_type = type(agent)

    _install_declarations(
            agent,
            candidate,
            tag,
            declarations,
            inputs,
            )

    candidate.active_tags.append(tag)
    next_type = _runtime_type_for(candidate)
    originals = {
            name: _capture_attribute(
                    agent,
                    name,
                    )
            for name in (
                    *declarations.deletions,
                    *(name for name, _ in declarations.records),
                    )
            }

    _set_state(
            agent,
            candidate,
            )

    try:
        _actualize_runtime_type(
                agent,
                next_type,
                )

        _evaluate_conditions(
                _layer_conditions(
                        candidate.preconditions,
                        declarations.preconditions,
                        ),
                agent,
                TagPreconditionError,
                "Precondition",
                inputs,
                )

        values = _materialize_records(
                agent,
                tag,
                declarations,
                state.deleted,
                inputs,
                )

        _apply_record_values(
                agent,
                values,
                )

        candidate.snapshots[tag] = _snapshot_for(
                agent,
                candidate,
                )

        _commit_deletions(
                agent,
                state,
                candidate,
                )

    except TagError:
        _restore_attributes(
                agent,
                originals,
                )

        if type(agent) is not original_type:
            _restore_runtime_type(
                    agent,
                    original_type,
                    )

        _set_state(
                agent,
                state,
                )
        raise

    return agent


def _apply_one(
        agent: object,
        tag: type["Tag"],
        inputs: dict[str, Any] | None = None,
        ) -> object:
    """Apply one Tag and every missing Base to an Agent.

    Form traversal is iterative, so a deep but valid Base chain does not
    consume Python call-stack depth. Re-applying an active layer remains a
    strict no-op.
    """

    application_inputs = inputs or {}

    _apply_form_layers(
            agent,
            tag,
            application_inputs,
            _apply_agent_layer,
            )

    return agent


def _slot_descriptors_for(
        host_type: type,
        ) -> tuple[Any, ...]:
    try:
        cached = _slot_descriptors_cache.get(host_type)
    except TypeError:
        cached = None

    if cached is not None:
        return cached

    descriptors: list[Any] = []

    for provider in host_type.__mro__:
        namespace = type.__getattribute__(
                provider,
                "__dict__",
                )

        for name, descriptor in namespace.items():
            if name == "_TAGKIT_STATE":
                continue

            if not isinstance(
                    descriptor,
                    MemberDescriptorType,
                    ):
                continue

            if descriptor not in descriptors:
                descriptors.append(descriptor)

    result = tuple(descriptors)

    try:
        _slot_descriptors_cache[host_type] = result
    except TypeError:
        pass

    return result


def _instance_namespace_for(
        agent: object,
        ) -> dict[str, Any] | None:
    descriptor = _MISSING

    for provider in type(agent).__mro__:
        candidate = provider.__dict__.get(
                "__dict__",
                _MISSING,
                )

        if isinstance(
                candidate,
                GetSetDescriptorType,
                ):
            descriptor = candidate

            break

    if descriptor is _MISSING:
        dictionary_offset = getattr(
                type(agent),
                "__dictoffset__",
                0,
                )

        if dictionary_offset:
            raise TagCompositionError(
                    "Target hides its instance dictionary behind a custom"
                    " __dict__ descriptor"
                    )

        return None

    try:
        namespace = descriptor.__get__(
                agent,
                type(agent),
                )
    except AttributeError:
        return None

    if not isinstance(
            namespace,
            dict,
            ):
        raise TagCompositionError(
                "Target must expose its instance __dict__ as a mutable"
                " dictionary"
                )

    return namespace


def _capture_instance_state(
        agent: object,
        ) -> _Instance_Snapshot:
    live_namespace = _instance_namespace_for(agent)
    namespace = (
            {
                name: value
                for name, value in live_namespace.items()
                if name != "_TAGKIT_STATE"
                }
            if live_namespace is not None
            else None
            )

    state = _existing_state_for(agent)
    host_type = (
            state.host_type
            if state is not None
            else type(agent)
            )
    slots: list[_Slot_Snapshot] = []

    for descriptor in _slot_descriptors_for(host_type):
        try:
            value = descriptor.__get__(
                    agent,
                    type(agent),
                    )
        except AttributeError:
            slots.append(
                    _Slot_Snapshot(
                            descriptor=descriptor,
                            was_present=False,
                            value=_MISSING,
                            )
                    )
        else:
            slots.append(
                    _Slot_Snapshot(
                            descriptor=descriptor,
                            was_present=True,
                            value=value,
                            )
                    )

    mutable_values = (
            list(namespace.values())
            if namespace is not None
            else []
            )
    mutable_values.extend(
            slot.value
            for slot in slots
            if slot.was_present
            )

    return _Instance_Snapshot(
            namespace=namespace,
            slots=tuple(slots),
            mutable_values=_capture_mutable_snapshots(
                    iter(mutable_values)
                    ),
            )


def _restore_instance_state(
        agent: object,
        captured: _Instance_Snapshot,
        ) -> None:
    _restore_mutable_snapshots(
            captured.mutable_values
            )

    if captured.namespace is not None:
        namespace = _instance_namespace_for(agent)

        if namespace is None:
            raise TagCompositionError(
                    "Target lost its instance __dict__ during Tagging"
                    )

        for name in list(namespace.keys()):
            if name == "_TAGKIT_STATE":
                continue

            del namespace[name]

        namespace.update(captured.namespace)

    for slot in captured.slots:
        if slot.was_present:
            slot.descriptor.__set__(
                    agent,
                    slot.value,
                    )
            continue

        try:
            slot.descriptor.__delete__(
                    agent,
                    )
        except AttributeError:
            pass


class _Checkpoint_Control:
    """Recover one Target while keeping provisional state off its API."""

    __slots__ = (
            "_active",
            "_entry_class",
            "_entry_snapshot",
            "_entry_state",
            "_entry_tags",
            "_query",
            "_target",
            "_target_is_tag",
            )

    def __init__(
            checkpoint,
            target: object,
            ) -> None:
        if _tagging_boundary_is_active(target):
            raise TagCompositionError(
                    "A Checkpoint cannot begin during Tag application"
                    )

        if _active_checkpoint_for(target) is not None:
            raise TagCompositionError(
                    "This Target already has an active Checkpoint"
                    )

        _validate_agent_state_slot(target)

        entry_state = _existing_state_for(target)
        target_is_tag = _is_tag(target)
        entry_snapshot: (
                _Instance_Snapshot
                | _Tag_Namespace_Snapshot
                )

        if target_is_tag:
            entry_snapshot = _capture_pinned_tag_namespace(target)
        else:
            entry_snapshot = _capture_instance_state(target)

        checkpoint._active = True
        checkpoint._entry_class = type(target)
        checkpoint._entry_snapshot = entry_snapshot
        checkpoint._entry_state = entry_state
        checkpoint._entry_tags = frozenset(
                entry_state.active_tags
                if entry_state is not None
                else ()
                )
        checkpoint._query = _Committed_Query(
                target=target,
                state=entry_state,
                record_names=_record_names_for(
                        target,
                        entry_state,
                        ),
                )
        checkpoint._target = target
        checkpoint._target_is_tag = target_is_tag

        _checkpoint_controls.set(
                (
                    *_checkpoint_controls.get(),
                    checkpoint,
                    )
                )
        _committed_queries.set(
                (
                    *_committed_queries.get(),
                    checkpoint._query,
                    )
                )

    def _require_active(
            checkpoint,
            ) -> None:
        if not checkpoint._active:
            raise TagCompositionError(
                    "This Checkpoint is already closed"
                    )

        if _tagging_boundary_is_active(checkpoint._target):
            raise TagCompositionError(
                    "A Checkpoint cannot close during Tag application"
                    )

    def _close_boundary(
            checkpoint,
            ) -> None:
        checkpoint._active = False
        checkpoint._query.active = False

        _checkpoint_controls.set(
                tuple(
                        candidate
                        for candidate in _checkpoint_controls.get()
                        if candidate is not checkpoint
                        )
                )
        _committed_queries.set(
                tuple(
                        query
                        for query in _committed_queries.get()
                        if query is not checkpoint._query
                        )
                )

    def _restore_captured_state(
            checkpoint,
            ) -> None:
        target = checkpoint._target

        _remove_new_memberships(
                target,
                checkpoint._entry_tags,
                )

        if checkpoint._target_is_tag:
            _restore_pinned_tag_namespace(
                    target,
                    checkpoint._entry_snapshot,
                    )
        else:
            if type(target) is not checkpoint._entry_class:
                _restore_runtime_type(
                        target,
                        checkpoint._entry_class,
                        )

            _restore_instance_state(
                    target,
                    checkpoint._entry_snapshot,
                    )

        if checkpoint._entry_state is not None:
            _set_state(
                    target,
                    checkpoint._entry_state,
                    )
        else:
            _delete_state(target)

    def _release_captured_state(
            checkpoint,
            ) -> None:
        checkpoint._entry_class = object
        checkpoint._entry_snapshot = None
        checkpoint._entry_state = None
        checkpoint._entry_tags = frozenset()
        checkpoint._query = None
        checkpoint._target = None
        checkpoint._target_is_tag = False

    def Commit(
            checkpoint,
            ) -> object:
        """Publish every Tag added since this Checkpoint began."""

        checkpoint._require_active()
        target = checkpoint._target
        checkpoint._close_boundary()

        try:
            _commit_new_memberships(
                    target,
                    checkpoint._entry_tags,
                    )
        except BaseException:
            try:
                checkpoint._restore_captured_state()
            finally:
                checkpoint._release_captured_state()

            raise

        checkpoint._release_captured_state()

        return target

    def Restore(
            checkpoint,
            ) -> object:
        """Restore the Target to this Checkpoint's entry state."""

        checkpoint._require_active()
        target = checkpoint._target
        checkpoint._close_boundary()

        try:
            checkpoint._restore_captured_state()
        finally:
            checkpoint._release_captured_state()

        return target

    def __enter__(
            checkpoint,
            ) -> object:
        checkpoint._require_active()

        return checkpoint._target

    def __exit__(
            checkpoint,
            error_type: type[BaseException] | None,
            error: BaseException | None,
            traceback: object,
            ) -> bool:
        if not checkpoint._active:
            return False

        if error_type is None:
            checkpoint.Commit()
        else:
            checkpoint.Restore()

        return False


def _checkpoint(
        target: object,
        ) -> _Checkpoint_Control:
    """Open a recoverable provisional boundary for one Target."""

    return _Checkpoint_Control( target )


def _run_transaction(
        agent: object,
        tag: type["Tag"],
        inputs: dict[str, Any] | None = None,
        ) -> object:
    """Apply one Tag as an atomic Overlay, Records, and Preconditions.

    Preconditions and Records still commit everything or nothing.
    Imprints and Postconditions run after this transaction and its
    tagging boundary have closed. An Imprint failure is a machine error.
    A Postcondition failure is a defective result. Neither un-applies
    the Tag.
    """

    _validate_agent_state_slot(agent)

    entry_state = _existing_state_for(agent)
    entry_tags = (
            frozenset(entry_state.active_tags)
            if entry_state is not None
            else frozenset()
            )
    entry_instance = _capture_instance_state(agent)
    entry_class = type(agent)
    application_inputs = inputs or {}

    with _committed_query_boundary(
            agent,
            entry_state,
            ):
        try:
            result = _apply_one(
                    agent,
                    tag,
                    application_inputs,
                    )
            _commit_new_memberships(
                    agent,
                    entry_tags,
                    )
        except BaseException:
            _remove_new_memberships(
                    agent,
                    entry_tags,
                    )

            if type(agent) is not entry_class:
                _restore_runtime_type(
                        agent,
                        entry_class,
                        )

            _restore_instance_state(
                    agent,
                    entry_instance,
                    )

            if entry_state is not None:
                _set_state(
                        agent,
                        entry_state,
                        )
            else:
                _delete_state(agent)

            raise

    return result


def _apply_transaction(
        agent: object,
        tag: type["Tag"],
        inputs: dict[str, Any] | None = None,
        ) -> object:
    state = _existing_state_for(agent)

    if state is not None and tag in state.active_tags:
        return agent

    entry_tags = (
            frozenset(state.active_tags)
            if state is not None
            else frozenset()
            )
    application_inputs = inputs or {}

    with _tagging_boundary(
            agent,
            tag,
            ) as should_apply:
        if not should_apply:
            return agent

        result = _run_transaction(
                agent,
                tag,
                application_inputs,
                )

    _run_committed_imprints(
            agent,
            entry_tags,
            application_inputs,
            )
    _run_committed_postconditions(
            agent,
            application_inputs,
            )

    return result


def _dependent_shapes(
        tag: type["Tag"],
        active_tags: list[type["Tag"]],
        ) -> tuple[type["Tag"], ...]:
    return tuple(
            other
            for other in reversed(active_tags)
            if (
                other is not tag
                and issubclass(
                        other,
                        tag,
                        )
                )
            )


def _rip_membership(
        agent: object,
        tag: type["Tag"],
        state: _Agent_State,
        ) -> None:
    state.active_tags = [
            candidate
            for candidate in state.active_tags
            if candidate is not tag
            ]

    tag._tagkit_field._remove(agent)

    rip_actions = state.rip_actions.pop(
            tag,
            (),
            )
    failures: list[
            tuple[str, Exception],
            ] = []

    for name, rip in rip_actions:
        try:
            _require_synchronous_result(
                    rip(agent),
                    f"Rip protocol {tag.__qualname__}.{name}",
                    )
        except Exception as error:
            failures.append(
                    (
                        name,
                        error,
                        )
                    )

    if failures:
        names = ", ".join(
                name
                for name, _error in failures
                )

        raise TagCompositionError(
                f"{tag.__name__} Rip teardown failed in: {names}"
                ) from failures[0][1]


def _rip_one(
        agent: object,
        tag: type["Tag"],
        ) -> object:
    """Extract an Agent from one Tag's Field (the Rip protocol).

    Membership ends but contributions are sticky: Actions and Records
    remain on the Agent (a "Rogue Agent") unless the Tag declares ``@Rip``
    teardown Actions, which run after the Agent leaves the Field. Ripping
    a Base first Rips its dependent Shapes in reverse application order,
    preserving upward closure. Ripping a Shape never auto-clears its Bases.
    """

    if _imprint_tagging_is_active():
        raise TagCompositionError(
                "A Target cannot be Ripped while an Imprint is running"
                )

    if _target_is_tagging(agent):
        raise TagCompositionError(
                "A Target cannot be Ripped while its tagging"
                " transaction is still provisional"
                )

    state = _existing_state_for(agent)

    if state is None or tag not in state.active_tags:
        raise TagResolutionError(
                f"{tag.__name__} is not active on this Agent"
                )

    dependents = _dependent_shapes(
            tag,
            state.active_tags,
            )

    for shape in dependents:
        current = _existing_state_for(agent)

        if (
                current is None
                or shape not in current.active_tags
                ):
            continue

        _rip_one(
                agent,
                shape,
                )

    state = _existing_state_for(agent)

    if state is None or tag not in state.active_tags:
        return agent

    remaining = _dependent_shapes(
            tag,
            state.active_tags,
            )

    if remaining:
        names = ", ".join(
                shape.__name__
                for shape in remaining
                )

        raise TagCompositionError(
                f"Cannot Rip {tag.__name__}; Rip protocol restored"
                f" dependent Shape(s): {names}"
                )

    _rip_membership(
            agent,
            tag,
            state,
            )

    return agent


@contextmanager
def Scope(
        agent: Target,
        *tags: type[Tag],
        ) -> Iterator[Target]:
    """Own the Tags added for a block and Rip that exact delta on exit.

    Memberships already active at entry are borrowed and remain active.
    Missing Bases pulled in by a requested Shape belong to the Scope too.
    Owned memberships are Ripped specific-first, even when setup or the
    block raises::

        with Scope(agent, Sentry):
            guard_the_gate(agent)
        # Sentry teardown has run here, exception or not.
    """

    _validate_tags(tags)

    entry_state = _existing_state_for(agent)
    entry_tags = frozenset(
            entry_state.active_tags
            if entry_state is not None
            else ()
            )
    owned: list[type[Tag]] = []
    primary_error: BaseException | None = None

    try:
        for tag in tags:
            tag(agent)

            current = _existing_state_for(agent)

            if current is None:
                continue

            for active in current.active_tags:
                if (
                        active not in entry_tags
                        and active not in owned
                        ):
                    owned.append(active)

        yield agent
    except BaseException as error:
        primary_error = error
        raise
    finally:
        cleanup_failures: list[
                tuple[type[Tag], TagError],
                ] = []

        for tag in reversed(owned):
            current = _existing_state_for(agent)

            if (
                    current is None
                    or tag not in current.active_tags
                    ):
                continue

            try:
                tag.Rip(agent)
            except TagError as error:
                cleanup_failures.append(
                        (
                            tag,
                            error,
                            )
                        )

        if cleanup_failures:
            names = ", ".join(
                    tag.__name__
                    for tag, _error in cleanup_failures
                    )
            cleanup_error = TagCompositionError(
                    f"Scope cleanup failed for Tag(s): {names}"
                    )
            cleanup_error.__cause__ = cleanup_failures[0][1]

            if primary_error is None:
                raise cleanup_error

            note = (
                    f"TagKit Scope also failed during cleanup: {names}"
                    )
            add_note = getattr(
                    primary_error,
                    "add_note",
                    None,
                    )

            if add_note is not None:
                add_note(note)

            try:
                setattr(
                        primary_error,
                        "tagkit_cleanup_error",
                        cleanup_error,
                        )
            except (
                    AttributeError,
                    TypeError,
                    ):
                pass
