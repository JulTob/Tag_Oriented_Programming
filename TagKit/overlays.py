from __future__ import annotations

"""Action binding and contribution Overlay assembly."""

from functools import wraps
from inspect import isasyncgenfunction
from inspect import iscoroutinefunction
from inspect import isgeneratorfunction
from typing import Any
import warnings

from .contracts import _bind_condition
from .declarations import Action_Body
from .declarations import _MISSING
from .declarations import _Tag_Declarations
from .declarations import _takes_underlay
from .errors import TagContractWarning
from .errors import TagOverwriteWarning
from .errors import TagResolutionError
from .runtime_types import _Agent_State
from .runtime_types import _Tag_Type
from .runtime_types import _host_action_for


def _bind_action(
        function: Action_Body,
        underlay: Action_Body | None,
        ) -> Action_Body:
    uses_underlay = _takes_underlay(function)

    if uses_underlay and underlay is None:
        raise TagResolutionError(
                f"{function.__qualname__} requires a visible Underlay"
                )

    if not uses_underlay:
        return function

    def Prior(
            agent: object,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
            ) -> Callable[..., Any]:
        def Call(
                *next_args: Any,
                **next_kwargs: Any,
                ) -> Any:
            if next_args or next_kwargs:
                return underlay(
                        agent,
                        *next_args,
                        **next_kwargs,
                        )

            return underlay(
                    agent,
                    *args,
                    **kwargs,
                    )

        return Call

    if iscoroutinefunction(function):
        @wraps(function)
        async def Async_Call(
                agent: object,
                *args: Any,
                **kwargs: Any,
                ) -> Any:
            return await function(
                    agent,
                    Prior(
                            agent,
                            args,
                            kwargs,
                            ),
                    *args,
                    **kwargs,
                    )

        return Async_Call

    if isasyncgenfunction(function):
        @wraps(function)
        async def Async_Generator_Call(
                agent: object,
                *args: Any,
                **kwargs: Any,
                ) -> Any:
            async for item in function(
                    agent,
                    Prior(
                            agent,
                            args,
                            kwargs,
                            ),
                    *args,
                    **kwargs,
                    ):
                yield item

        return Async_Generator_Call

    if isgeneratorfunction(function):
        @wraps(function)
        def Generator_Call(
                agent: object,
                *args: Any,
                **kwargs: Any,
                ) -> Any:
            yield from function(
                    agent,
                    Prior(
                            agent,
                            args,
                            kwargs,
                            ),
                    *args,
                    **kwargs,
                    )

        return Generator_Call

    @wraps(function)
    def Call(
            agent: object,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        return function(
                agent,
                Prior(
                        agent,
                        args,
                        kwargs,
                        ),
                *args,
                **kwargs,
                )

    return Call


def _is_independent(
        new_tag: type["Tag"],
        prior_origin: type["Tag"] | type,
        ) -> bool:
    if not isinstance(prior_origin, _Tag_Type):
        return False

    return not (
            issubclass(
                    new_tag,
                    prior_origin,
                    )
            or issubclass(
                    prior_origin,
                    new_tag,
                    )
            )


def _same_bound_member(
        left: object,
        right: object,
        ) -> bool:
    if left is right:
        return True

    return (
            getattr(
                    left,
                    "__func__",
                    _MISSING,
                    )
            is getattr(
                    right,
                    "__func__",
                    _MISSING,
                    )
            and getattr(
                    left,
                    "__self__",
                    _MISSING,
                    )
            is getattr(
                    right,
                    "__self__",
                    _MISSING,
                    )
            )


def _remove_contribution(
        state: _Agent_State,
        name: str,
        ) -> None:
    state.actions.pop(name, None)
    state.action_origins.pop(name, None)
    state.record_builders.pop(name, None)
    state.record_origins.pop(name, None)
    state.record_values.pop(name, None)
    state.preconditions.pop(name, None)
    state.postconditions.pop(name, None)
    state.reports.pop(name, None)
    state.operations.pop(name, None)
    state.deleted.add(name)


def _install_declarations(
        target: object,
        state: _Agent_State,
        tag: type["Tag"],
        declarations: _Tag_Declarations,
        inputs: dict[str, Any],
        ) -> None:
    state.field_reports[tag] = {
            name: value
            for name, value in declarations.reports
            }
    state.field_operations[tag] = {
            name: operation
            for name, operation in declarations.operations
            }
    state.field_deletions[tag] = set(
            declarations.deletions
            )

    for name in declarations.deletions:
        _remove_contribution(
                state,
                name,
                )

    for name, predicate in declarations.preconditions:
        state.preconditions[name] = _bind_condition(
                predicate,
                state.preconditions.get(name),
                inputs,
                )
        state.deleted.discard(name)

    for name, predicate in declarations.postconditions:
        prior = state.postconditions.get(name)

        if prior is not None and not _takes_underlay(predicate):
            warnings.warn(
                    f"{tag.__name__}.{name} crunches a Base Postcondition"
                    " without @Underlay (weakens a promise; see Forward-Post)",
                    TagContractWarning,
                    stacklevel=4,
                    )

        state.postconditions[name] = _bind_condition(
                predicate,
                prior,
                inputs,
                )
        state.deleted.discard(name)

    for name, value in declarations.reports:
        state.reports[name] = value
        state.deleted.discard(name)

    for name, operation in declarations.operations:
        state.operations[name] = (
                tag,
                operation,
                )
        state.deleted.discard(name)

    for name, function in declarations.actions:
        underlay = state.actions.get(name)
        prior_origin = state.action_origins.get(name, state.host_type)
        was_deleted = name in state.deleted

        if (
                underlay is None
                and not was_deleted
                ):
            underlay = _host_action_for(
                    state.host_type,
                    name,
                    target,
                    )

        if (
                underlay is not None
                and not _takes_underlay(function)
                and _is_independent(
                        tag,
                        prior_origin,
                        )
                ):
            warnings.warn(
                    f"{tag.__name__}.{name} replaces an independent Tag Action",
                    TagOverwriteWarning,
                    stacklevel=3,
                    )

        state.actions[name] = _bind_action(
                function,
                underlay,
                )
        state.action_origins[name] = tag
        state.deleted.discard(name)

    for name, builder in declarations.records:
        state.record_builders[name] = builder
        state.record_origins[name] = tag
        state.deleted.discard(name)

    if declarations.rips:
        state.rip_actions[tag] = declarations.rips
