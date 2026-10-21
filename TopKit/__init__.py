"""TopKit: the Python reference implementation of Tag-Oriented Programming."""

from .contracts import Contract
from .declarations import Action
from .declarations import Constant
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
from .errors import TagArrestedAccessError
from .errors import TagCompositionError
from .errors import TagContractError
from .errors import TagContractWarning
from .errors import TagDeclarationError
from .errors import TagError
from .errors import TagImprintError
from .errors import TagTrainingWarning
from .errors import TrainingWarning
from .errors import TaggingFailure
from .errors import TagTargetError
from .errors import TagOverwriteWarning
from .errors import TagPostconditionError
from .errors import TagPreconditionError
from .errors import TagResolutionError
from .errors import TagRogueAccessError
from .lifecycle import At_Exit
from .queries import Apply
from .queries import Form
from .queries import Keyword
from .queries import Outline
from .queries import Tags
from .tags import Tag
from .tags import Tagged
from .tools import Tool
from .link_forms import Link
from .link_forms import agent
from .link_forms import contact
from .links import _Pair_View

# The two language seats are recognized by identity, keeping ordinary
# membership queries free of descriptor or proxy metadata lookups.
from . import fields as _fields
from . import tags as _tags
from . import link_forms as _link_forms
_fields._link_agent = _tags._link_agent = agent
_fields._link_contact = _tags._link_contact = contact
_fields._link_pair_view = _tags._link_pair_view = _Pair_View
_link_forms._pair_view_type = _Pair_View


__all__ = [
        "Action",
        "Apply",
        "At_Exit",
        "Constant",
        "Contract",
        "Delete",
        "Flag",
        "Form",
        "Keyword",
        "Link",
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
        "Secret",
        "Tag",
        "TagArrestedAccessError",
        "TagCompositionError",
        "TagContractError",
        "TagContractWarning",
        "TagDeclarationError",
        "TagError",
        "TagImprintError",
        "TagTrainingWarning",
        "TrainingWarning",
        "TaggingFailure",
        "TagTargetError",
        "TagOverwriteWarning",
        "TagPostconditionError",
        "TagPreconditionError",
        "TagResolutionError",
        "TagRogueAccessError",
        "Tagged",
        "Tags",
        "Tool",
        "Underlay",
        "agent",
        "contact",
        ]
