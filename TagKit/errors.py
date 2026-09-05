"""Failures and diagnostics.

Every failure names the semantic law it violates. A language profile may
map these to its own exception types, but must keep them distinct.

Three failures also carry the name of the check that failed, as a
subclass: ``TagPreconditionError.Is_A_Caster`` is raised when the
Precondition declared as ``Is_A_Caster`` refuses, so a program writes
``except Precondition.Is_A_Caster:`` and reads its own words back.
"""

from __future__ import annotations


class _Named(type):
    """Metaclass for failures that name the check that failed.

    ``Failure.Name`` is the subclass raised when the check called ``Name``
    fails. A subclass exists only for a name that was declared, so a
    misspelt handler is an AttributeError at the ``except``, not a handler
    that never fires.
    """

    def __getattr__(
            cls,
            name: str,
            ) -> type:
        names = cls.__dict__.get("_names")

        if names is None or name.startswith("_"):
            raise AttributeError(name)

        try:
            return names[name]
        except KeyError:
            raise AttributeError(
                    f"{cls.__name__} has no {name!r}: no {cls._kind} called"
                    f" {name!r} has been declared"
                    ) from None

    def Named(
            cls,
            name: str,
            ) -> type:
        """The subclass raised when the check called ``name`` fails.

        Made once per name, when the check is declared.
        """

        names = cls.__dict__["_names"]

        if name not in names:
            names[name] = type(
                    name,
                    (cls,),
                    {
                        "__module__": cls.__module__,
                        "__qualname__": f"{cls.__qualname__}.{name}",
                        "name": name,
                        },
                    )

        return names[name]


class TagError(Exception):
    """Base failure for TagKit."""


class TagDeclarationError(TagError):
    """A Tag declaration is invalid (bad mark combination, bad signature)."""


class TagCompositionError(TagError):
    """Contributions cannot form a coherent Overlay, or a Record cannot
    be materialized, or a teardown failed."""


class TagResolutionError(TagError):
    """A required Underlay, Tag view, or contribution is unavailable."""


class TagPreconditionError(TagError, metaclass=_Named):
    """A Precondition refused the Tagging. Nothing committed.

    ``TagPreconditionError.Name`` is the subclass raised for the
    Precondition declared as ``Name``; ``error.name`` is that name.
    """

    _kind = "Precondition"
    _names: dict[str, type] = {}
    name: str | None = None


class TagImprintError(TagError, metaclass=_Named):
    """An Imprint failed after the Tag applied. The Tag stays.

    ``TagImprintError.Name`` is the subclass raised for the Imprint
    declared as ``Name``; ``error.name`` is that name.
    """

    _kind = "Imprint"
    _names: dict[str, type] = {}
    name: str | None = None


class TagPostconditionError(TagError, metaclass=_Named):
    """A Postcondition found the finished Tagging defective. The Tag stays.

    ``TagPostconditionError.Name`` is the subclass raised for the
    Postcondition declared as ``Name``; ``error.name`` is that name.
    """

    _kind = "Postcondition"
    _names: dict[str, type] = {}
    name: str | None = None


class TagContractError(TagError):
    """A condition yielded a non-boolean (truthy/falsy) value."""


class TagOverwriteWarning(UserWarning):
    """An independent Tag replaced a visible contribution."""


class TagContractWarning(UserWarning):
    """A Shape weakened a Base Postcondition without @Underlay."""
