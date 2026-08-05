from __future__ import annotations

"""Stable public TagKit API."""

from typing import Any

from .contracts import Contract
from .declarations import Action
from .declarations import Delete
from .declarations import Imprint
from .declarations import Operation
from .declarations import Postcondition
from .declarations import Precondition
from .declarations import Record
from .declarations import Report
from .declarations import Rip
from .declarations import Target
from .declarations import Underlay
from .errors import TagCompositionError
from .errors import TagContractError
from .errors import TagContractWarning
from .errors import TagDeletionError
from .errors import TagError
from .errors import TagImprintError
from .errors import TagOverwriteWarning
from .errors import TagPostconditionError
from .errors import TagPreconditionError
from .errors import TagResolutionError
from .lifecycle import At_Exit
from .queries import Has
from .queries import Tags
from .queries import _validate_tags
from .runtime_types import Tag
from .runtime_types import Tagged
from .transactions import Scope


Pre = Precondition
Post = Postcondition


def Apply(
        target: Target,
        *tags: type[Tag],
        **inputs: Any,
        ) -> Target:
    """Apply Tags in order and return the same Target.

    This procedural form keeps TOP composition independent of Target methods
    and works naturally in functional pipelines. All Tags are validated
    before the first application, so an invalid later argument cannot leave a
    partial sequence behind.
    """

    _validate_tags(tags)

    for tag in tags:
        tag(
                target,
                **inputs,
                )

    return target
