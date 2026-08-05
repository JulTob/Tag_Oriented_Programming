from __future__ import annotations

"""Atomic Agent Tagging, rollback, Rip, and Scope."""

from contextlib import contextmanager
from contextvars import ContextVar
from types import GetSetDescriptorType
from types import MemberDescriptorType
from typing import Any
from typing import Iterator

from .contracts import _evaluate_conditions
from .declarations import _MISSING
from .declarations import _require_synchronous_result
from .declarations import _run_protocol
from .errors import TagCompositionError
from .errors import TagError
from .errors import TagImprintError
from .errors import TagPostconditionError
from .errors import TagPreconditionError
from .errors import TagResolutionError
from .geometry import _direct_bases_for
from .overlays import _install_declarations
from .pins import _declarations_with_pins
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
from .runtime_types import _Tagging_Transaction
from .runtime_types import _actualize_runtime_type
from .runtime_types import _committed_queries
from .runtime_types import _delete_state
from .runtime_types import _existing_state_for
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


@contextmanager
def _committed_query_boundary(
        target: object,
        state: _Agent_State | None,
        ) -> Iterator[None]:
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
                "Re-entrant Tag application on the same Target is not"
                " supported; declare the relationship through Bases"
                " or a Shape"
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
    identity = id(target)

    return any(
            transaction.active
            and transaction.identity == identity
            for transaction in _tagging_transactions.get()
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

    The Form is discovered while it is traversed. A successful earlier
    Imprint may therefore rebase a later sibling while retaining support for
    very deep Forms.
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
                candidate.preconditions,
                agent,
                TagPreconditionError,
                "Precondition",
                inputs,
                )

        for imprint in declarations.imprints:
            try:
                _run_protocol(imprint, agent, inputs)
            except Exception as error:
                raise TagImprintError(
                        f"Imprint {imprint.__qualname__} failed"
                        ) from error

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

        _evaluate_conditions(
                candidate.postconditions,
                agent,
                TagPostconditionError,
                "Postcondition",
                inputs,
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


def _run_transaction(
        agent: object,
        tag: type["Tag"],
        inputs: dict[str, Any] | None = None,
        ) -> object:
    """Apply one Tag as an atomic transaction.

    A single ``Tag(target, **inputs)`` call commits everything or nothing.
    If any Base pulled in by this call, or the requested Tag itself, fails,
    the Agent is restored to exactly its state at call entry. Tags committed
    by earlier calls survive untouched.
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

    with _committed_query_boundary(
            agent,
            entry_state,
            ):
        try:
            result = _apply_one(
                    agent,
                    tag,
                    inputs,
                    )
            _commit_new_memberships(
                    agent,
                    entry_tags,
                    )

            return result
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


def _apply_transaction(
        agent: object,
        tag: type["Tag"],
        inputs: dict[str, Any] | None = None,
        ) -> object:
    state = _existing_state_for(agent)

    if state is not None and tag in state.active_tags:
        return agent

    with _tagging_boundary(
            agent,
            tag,
            ) as should_apply:
        if not should_apply:
            return agent

        return _run_transaction(
                agent,
                tag,
                inputs,
                )


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
