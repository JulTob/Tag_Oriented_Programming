"""Failures and diagnostics.

Every failure names the semantic law it violates. A language profile may
map these to its own exception types, but must keep them distinct.
"""


class TagError(Exception):
    """Base failure for TagKit."""


class TagDeclarationError(TagError):
    """A Tag declaration is invalid (bad mark combination, bad signature)."""


class TagCompositionError(TagError):
    """Contributions cannot form a coherent Overlay, or a Record cannot
    be materialized, or a teardown failed."""


class TagResolutionError(TagError):
    """A required Underlay, Tag view, or contribution is unavailable."""


class TagPreconditionError(TagError):
    """A Precondition refused the Tagging. Nothing committed."""


class TagImprintError(TagError):
    """An Imprint failed after the Tag applied. The Tag stays."""


class TagPostconditionError(TagError):
    """A Postcondition found the finished Tagging defective. The Tag stays."""


class TagContractError(TagError):
    """A condition yielded a non-boolean (truthy/falsy) value."""


class TagOverwriteWarning(UserWarning):
    """An independent Tag replaced a visible contribution."""


class TagContractWarning(UserWarning):
    """A Shape weakened a Base Postcondition without @Underlay."""
