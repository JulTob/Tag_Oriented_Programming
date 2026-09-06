"""TagKit: the Python reference implementation of Tag-Oriented Programming."""

from .contracts import Contract
from .declarations import Action
from .declarations import Delete
from .declarations import Flag
from .declarations import Imprint
from .declarations import Operation
from .declarations import Pin
from .declarations import Post
from .declarations import Postcondition
from .declarations import Pre
from .declarations import Precondition
from .declarations import Public
from .declarations import Record
from .declarations import Report
from .declarations import Rip
from .declarations import Secret
from .declarations import Underlay
from .errors import TagCompositionError
from .errors import TagContractError
from .errors import TagContractWarning
from .errors import TagDeclarationError
from .errors import TagError
from .errors import TagImprintError
from .errors import TagOverwriteWarning
from .errors import TagPostconditionError
from .errors import TagPreconditionError
from .errors import TagResolutionError
from .lifecycle import At_Exit
from .lifecycle import Scope
from .queries import Apply
from .queries import Form
from .queries import Keyword
from .queries import Outline
from .queries import Tags
from .tags import Tag
from .tags import Tagged


__all__ = [
        "Action",
        "Apply",
        "At_Exit",
        "Contract",
        "Delete",
        "Flag",
        "Form",
        "Keyword",
        "Imprint",
        "Operation",
        "Outline",
        "Pin",
        "Post",
        "Postcondition",
        "Pre",
        "Precondition",
        "Public",
        "Record",
        "Report",
        "Rip",
        "Scope",
        "Secret",
        "Tag",
        "TagCompositionError",
        "TagContractError",
        "TagContractWarning",
        "TagDeclarationError",
        "TagError",
        "TagImprintError",
        "TagOverwriteWarning",
        "TagPostconditionError",
        "TagPreconditionError",
        "TagResolutionError",
        "Tagged",
        "Tags",
        "Underlay",
        ]
