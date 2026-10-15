"""TopKit conformance tests, grouped by behavior.

Run the whole package with ``python -m unittest tests.test_topkit``.
TestCase exports preserve individual-class targets such as
``tests.test_topkit.RecordTests``; the loader discovers each file once.
"""

from .test_kernel import KernelTests
from .test_host_preservation import HostPreservationTests
from .test_overlay import OverlayTests
from .test_record import RecordTests
from .test_publication import PublicationTests
from .test_rogue_access import RogueAccessTests
from .test_precondition import PreconditionTests
from .test_condition import ConditionTests
from .test_defective_tagging import DefectiveTaggingTests
from .test_contract_namespace import ContractNamespaceTests
from .test_named_failure import NamedFailureTests
from .test_pin import PinTests
from .test_rip import RipTests
from .test_field_rip import FieldRipTests
from .test_sticky_condition import StickyConditionTests
from .test_exit_protocol import ExitProtocolTests
from .test_try_finally import TryFinallyTests
from .test_access import AccessTests
from .test_field_algebra import FieldAlgebraTests
from .test_tag_recognition import TagRecognitionTests
from .test_population_walk import PopulationWalkTests
from .test_condition_member import ConditionMemberTests
from .test_query import QueryTests
from .test_flag_word import FlagWordTests
from .test_restored_name import RestoredNameTests
from .test_in_seat import InSeatTests
from .test_efficiency import EfficiencyTests
from .test_layered_deletion import LayeredDeletionTests
from .test_deliberate_difference import DeliberateDifferenceTests


def load_tests(loader, standard_tests, pattern):
    # Use the package name so direct invocation and both discovery roots
    # retain relative imports. Discover children instead of adding the
    # re-exported classes in standard_tests a second time.
    return loader.discover(__name__, pattern=pattern or "test*.py")
