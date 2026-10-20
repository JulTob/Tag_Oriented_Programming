"""Conformance tests: defective tagging."""

from __future__ import annotations

import inspect
import unittest
import warnings
from TopKit import Apply
from TopKit import Post
from TopKit import Postcondition
from TopKit import Pre
from TopKit import Precondition
from TopKit import Tag
from TopKit import TagContractError
from TopKit import TagContractWarning
from TopKit import TagCompositionError
from TopKit import TagImprintError
from TopKit import TagPostconditionError
from TopKit import TagTrainingWarning

from ._fixtures import Advanced
from ._fixtures import Agent
from ._fixtures import Broken_Imprint
from ._fixtures import Bruiser
from ._fixtures import Candidate_Record
from ._fixtures import Capped
from ._fixtures import Disciplined
from ._fixtures import Ordered_Imprints
from ._fixtures import Reflective
from ._fixtures import Reserved
from ._fixtures import Scholar
from ._fixtures import Slotted
from ._fixtures import Validated


class DefectiveTaggingTests(unittest.TestCase):
    def test_failed_postcondition_raises_but_the_tag_stays_defective(self) -> None:
        ari = Agent()
        ari.ready = False

        with self.assertRaises(TagPostconditionError):
            Candidate_Record(ari)

        self.assertNotIn(ari, Candidate_Record)       # not sound
        self.assertIn(ari, Candidate_Record[:])       # everyone
        self.assertEqual(ari.token, "prepared")
        self.assertFalse(bool(ari))
        self.assertNotIn(ari, list(Candidate_Record)) # not in the sound loop
        self.assertIn(ari, ~Candidate_Record)

        ari.ready = True

        self.assertTrue(bool(ari))
        self.assertIn(ari, list(Candidate_Record))
        self.assertNotIn(ari, ~Candidate_Record)

    def test_sound_and_defective_partition_the_field(self) -> None:
        good = Agent()
        bad = Agent()
        bad.ready = False

        Candidate_Record(good)

        with self.assertRaises(TagPostconditionError):
            Candidate_Record(bad)

        self.assertEqual(list(Candidate_Record), [good])
        self.assertEqual(list(~Candidate_Record), [bad])
        self.assertEqual(set(Candidate_Record[:]), {good, bad})
        self.assertIn(good, Candidate_Record)
        self.assertNotIn(bad, Candidate_Record)
        self.assertIn(bad, Candidate_Record[:])
        self.assertIn(bad, ~Candidate_Record)
        self.assertEqual(len(Candidate_Record), 1)
        self.assertEqual(len(~Candidate_Record), 1)
        self.assertEqual(len(Candidate_Record[:]), 2)
        self.assertGreater(len(Candidate_Record), 0)  # someone sound
        self.assertTrue(~Candidate_Record)         # someone broken
        self.assertTrue(Candidate_Record[:])       # anyone

        bad.ready = True

        self.assertFalse(~Candidate_Record)        # nobody left to repair
        self.assertIn(bad, Candidate_Record)

    def test_broken_prior_post_refuses_later_tagging_until_repaired(self) -> None:
        ari = Agent()

        Validated(ari)
        ari.allowed = False
        Advanced(ari)
        self.assertIn(ari, Advanced)

        bea = Agent()
        Validated(bea)
        bea.ready = False

        with self.assertRaisesRegex(TagCompositionError, "current Posts fail"):
            Advanced(bea)

        self.assertNotIn(bea, Advanced)
        self.assertNotIn(bea, Advanced[:])

        bea.ready = True
        Advanced(bea)
        bea.ready = False
        self.assertNotIn(bea, Advanced)
        self.assertIn(bea, Advanced[:])                # later damage keeps admission
        self.assertIn(bea, ~Advanced)

    def test_imprint_failure_keeps_effects_and_admits_the_tag(self) -> None:
        ari = Agent()

        Ordered_Imprints(ari)
        self.assertEqual(ari.events, ["First", "Second"])

        with self.assertWarns(TagTrainingWarning):
            Broken_Imprint(ari)

        self.assertIn(ari, Broken_Imprint)
        self.assertIn(ari, Broken_Imprint[:])
        self.assertTrue(isinstance(ari, Broken_Imprint))
        self.assertEqual(ari.events, ["First", "Second", "before failure"])

    def test_bool_agent_runs_postconditions(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)
        self.assertTrue(bool(ari))

        del ari.spellbook
        self.assertFalse(bool(ari))

    def test_if_agent_inside_a_post_does_not_recurse(self) -> None:
        ari = Agent()

        Reflective(ari)

        self.assertTrue(bool(ari))

    def test_condition_must_yield_a_strict_boolean(self) -> None:
        ari = Agent()
        ari.spell_slots = 0

        with self.assertRaises(TagContractError):
            Slotted(ari)

    def test_explicit_existence_check_separates_zero_from_missing(self) -> None:
        zero = Agent()
        zero.spell_slots = 0

        Reserved(zero)
        self.assertTrue(bool(zero))

        missing = Agent()

        with self.assertRaises(TagPostconditionError):
            Reserved(missing)

        self.assertFalse(bool(missing))

    def test_weakening_a_post_without_underlay_warns(self) -> None:
        ari = Agent()
        ari.strength = 15

        with self.assertWarns(TagContractWarning):
            Bruiser(ari)

        ari.strength = 22
        self.assertTrue(bool(ari))

    def test_post_underlay_strengthens_without_warning(self) -> None:
        ari = Agent()
        ari.strength = 15

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            Disciplined(ari)

        self.assertTrue(bool(ari))

        ari.strength = 19
        self.assertFalse(bool(ari))

    def test_the_contract_warning_names_the_base_it_weakens(self) -> None:
        ari = Agent()
        ari.strength = 15

        with self.assertWarns(TagContractWarning) as caught:
            Bruiser(ari)

        message = str(caught.warning)
        self.assertIn("Bruiser.Strength_Capped", message)
        self.assertIn("its Base Capped", message)
        self.assertIn("weakens a promise", message)

    def test_the_contract_warning_names_an_independent_tag(self) -> None:
        class Sworn(Tag):
            @Post
            def Honest(agent):
                return agent.oath

        class Guild(Tag):
            @Post
            def Honest(agent):
                return True

        ari = Agent()
        ari.oath = True
        Sworn(ari)

        with self.assertWarns(TagContractWarning) as caught:
            Guild(ari)

        message = str(caught.warning)
        self.assertIn("Guild.Honest", message)
        self.assertIn("independent Tag Sworn", message)
        self.assertNotIn("Base", message)

        ari.oath = False
        self.assertTrue(bool(ari))                                    # as the text says: Sworn's promise no longer binds

    def test_the_contract_warning_names_the_shape_a_base_replaces(self) -> None:
        ari = Agent()
        ari.strength = 15

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            Bruiser(ari)

        del Bruiser[ari]
        del Capped[ari]

        with self.assertWarns(TagContractWarning) as caught:
            Capped(ari)                                               # over Bruiser's sticky promise

        message = str(caught.warning)
        self.assertIn("Capped.Strength_Capped", message)
        self.assertIn("its Shape Bruiser", message)
        self.assertNotIn("weakens", message)

    def test_the_contract_warning_points_at_the_tagging_line(self) -> None:
        ari = Agent()
        ari.strength = 15

        with self.assertWarns(TagContractWarning) as caught:
            expected_line = inspect.currentframe().f_lineno + 1
            Bruiser(ari)

        self.assertEqual(caught.filename, __file__)
        self.assertEqual(caught.lineno, expected_line)

    def test_the_contract_warning_points_through_apply(self) -> None:
        ari = Agent()
        ari.strength = 15

        with self.assertWarns(TagContractWarning) as caught:
            expected_line = inspect.currentframe().f_lineno + 1
            Apply(ari, Bruiser)

        self.assertEqual(caught.filename, __file__)
        self.assertEqual(caught.lineno, expected_line)

    def test_pre_and_post_are_aliases(self) -> None:
        self.assertIs(Pre, Precondition)
        self.assertIs(Post, Postcondition)
