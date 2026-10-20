"""Conformance tests: named failure."""

from __future__ import annotations

import unittest
import warnings
from TopKit import Contract
from TopKit import Imprint
from TopKit import Post
from TopKit import Postcondition
from TopKit import Pre
from TopKit import Precondition
from TopKit import Tag
from TopKit import TagImprintError
from TopKit import TagPostconditionError
from TopKit import TagPreconditionError
from TopKit import TagTrainingWarning

from ._fixtures import Agent


class NamedFailureTests(unittest.TestCase):
    """A failure carries the name of the check that failed, as a subclass:
    ``except Precondition.Is_A_Caster`` reads the program's own words."""

    def test_precondition_failure_is_caught_by_its_name(self) -> None:
        class Caster(Tag):
            @Pre
            def Is_A_Caster(agent):
                return False

        with self.assertRaises(Precondition.Is_A_Caster) as caught:
            Caster(Agent())

        self.assertEqual(caught.exception.name, "Is_A_Caster")
        self.assertIs(Precondition.Is_A_Caster, TagPreconditionError.Is_A_Caster)
        self.assertEqual(
                Precondition.Is_A_Caster.__qualname__,
                "TagPreconditionError.Is_A_Caster",
                )

    def test_named_failure_is_still_the_general_failure(self) -> None:
        class Caster(Tag):
            @Pre
            def Is_A_Caster(agent):
                return False

        with self.assertRaises(TagPreconditionError):
            Caster(Agent())

        self.assertTrue(issubclass(Precondition.Is_A_Caster, TagPreconditionError))

    def test_a_raising_check_is_named_too(self) -> None:
        class Caster(Tag):
            @Pre
            def Is_A_Caster(agent):
                if not agent.level > 0:
                    raise AssertionError("a Caster needs a level")

        with self.assertRaises(Precondition.Is_A_Caster):
            Caster(Agent())

    def test_post_failure_and_imprint_warning_keep_declared_names(self) -> None:
        class Armed(Tag):
            @Imprint
            def Arm(agent):
                raise ValueError("no arms")

        class Shielded(Tag):
            @Post
            def Has_Shield(agent):
                return False

        agent = Agent()
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always", TagTrainingWarning)
            self.assertIs(Armed(agent), agent)
        self.assertEqual(len(recorded), 1)
        warning = recorded[0].message
        self.assertIsInstance(warning, TagTrainingWarning)
        self.assertEqual(warning.name, "Arm")
        self.assertIsInstance(warning.failure, Imprint.Arm)
        self.assertIsInstance(warning.failure, TagImprintError)
        self.assertIn(agent, Armed[:])

        with self.assertRaises(Postcondition.Has_Shield) as caught:
            Shielded(Agent())

        self.assertEqual(caught.exception.name, "Has_Shield")
        self.assertIsInstance(caught.exception, TagPostconditionError)

    def test_a_misspelt_name_is_an_error_at_the_except(self) -> None:
        class Caster(Tag):
            @Pre
            def Is_A_Caster(agent):
                return False

        with self.assertRaises(AttributeError) as caught:
            Precondition.Is_A_Castor

        self.assertIn("Is_A_Castor", str(caught.exception))
        self.assertIn("Precondition", str(caught.exception))

    def test_one_name_in_two_tags_is_one_handler(self) -> None:
        class Left(Tag):
            @Pre
            def Ready(agent):
                return False

        class Right(Tag):
            @Pre
            def Ready(agent):
                return False

        for tag in (Left, Right):
            with self.assertRaises(Precondition.Ready):
                tag(Agent())

    def test_the_general_failure_has_no_name(self) -> None:
        self.assertIsNone(TagPreconditionError("plain").name)

    def test_the_marks_still_mark(self) -> None:
        class Gated(Tag):
            @Precondition
            def Open(agent):
                return True

            @Postcondition
            def Done(agent):
                return True

        ari = Agent()
        Gated(ari)

        self.assertIn(ari, Gated)
        self.assertEqual(Contract.Status(ari), {"Open": True, "Done": True})
