from __future__ import annotations

"""TagKit failures and diagnostics."""


class TagError(Exception):
    """Base failure for TagKit."""


class TagCompositionError(TagError):
    """Raised when Tags cannot form a coherent Overlay."""


class TagResolutionError(TagError):
    """Raised when a required Underlay or Tag view is unavailable."""


class TagPreconditionError(TagError):
    """Raised when a Precondition prevents Tagging."""


class TagPostconditionError(TagError):
    """Raised when a Postcondition rejects a candidate Overlay."""


class TagImprintError(TagError):
    """Raised when an Imprint cannot complete."""


class TagDeletionError(TagError):
    """Raised when a deletion declaration is invalid."""


class TagContractError(TagError):
    """Raised when a condition yields a non-boolean (truthy/falsy) value."""


class TagOverwriteWarning(UserWarning):
    """Warns when an independent Tag replaces a visible contribution."""


class TagContractWarning(UserWarning):
    """Warns when a Shape weakens a Base Postcondition without @Underlay."""
