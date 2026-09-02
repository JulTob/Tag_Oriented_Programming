from __future__ import annotations

"""TagKit failures and diagnostics."""


class TagError(Exception):
    """Base failure for TagKit."""


class TagCompositionError(TagError):
    """Raised when Tags cannot form a coherent Overlay."""


class TagResolutionError(TagError):
    """Raised when a required Underlay or Tag view is unavailable."""


class _Named_Condition_Error(type):
    """``TagPostconditionError.Has_Spellbook`` is a catchable named clause."""

    def __getattr__(
            error_type,
            name: str,
            ) -> type:
        if name.startswith("_"):
            raise AttributeError(name)

        cache = error_type.__dict__.get("_named_clauses")

        if cache is None:
            cache = {}
            type.__setattr__(
                    error_type,
                    "_named_clauses",
                    cache,
                    )

        named = cache.get(name)

        if named is None:
            named = _Named_Condition_Error(
                    f"{error_type.__name__}.{name}",
                    (
                        error_type,
                        ),
                    {
                        "__module__": error_type.__module__,
                        "_clause": name,
                        },
                    )
            cache[name] = named

        return named


class TagPreconditionError(
        TagError,
        metaclass=_Named_Condition_Error,
        ):
    """Raised when a Precondition prevents Tagging."""

    _clause: str | None = None

    def __init__(
            error,
            message: str = "",
            *,
            condition: str | None = None,
            ) -> None:
        clause = (
                condition
                if condition is not None
                else type(error)._clause
                )
        super().__init__(message)
        error.condition = clause


class TagPostconditionError(
        TagError,
        metaclass=_Named_Condition_Error,
        ):
    """Raised when a Postcondition finds a defective applied Tag."""

    _clause: str | None = None

    def __init__(
            error,
            message: str = "",
            *,
            condition: str | None = None,
            ) -> None:
        clause = (
                condition
                if condition is not None
                else type(error)._clause
                )
        super().__init__(message)
        error.condition = clause


class ImprintingError(TagError):
    """Raised when an Imprint fails after the Tag has already applied."""


TagImprintError = ImprintingError


class TagDeletionError(TagError):
    """Raised when a deletion declaration is invalid."""


class TagContractError(TagError):
    """Raised when a condition yields a non-boolean (truthy/falsy) value."""


class TagOverwriteWarning(UserWarning):
    """Warns when an independent Tag replaces a visible contribution."""


class TagContractWarning(UserWarning):
    """Warns when a Shape weakens a Base Postcondition without @Underlay."""


def _named_condition_error(
        failure_type: type[TagError],
        name: str,
        ) -> type[TagError]:
    """Return the catchable named subtype for one condition clause."""

    if isinstance(
            failure_type,
            _Named_Condition_Error,
            ):
        return getattr(
                failure_type,
                name,
                )

    return failure_type
