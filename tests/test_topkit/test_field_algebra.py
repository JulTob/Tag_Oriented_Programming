"""Conformance tests: field algebra."""

from __future__ import annotations

import unittest
from TopKit import Operation
from TopKit import Post
from TopKit import Postcondition
from TopKit import Report
from TopKit import Tag

from ._fixtures import Agent


class FieldAlgebraTests(unittest.TestCase):
    """STEP-SPEC-13: populations combine. A Tag in an operator seat is its
    sound population; `Tag[:]` is everyone; `~Tag` the defective ones."""

    def setUp(self) -> None:
        class Wizard(Tag):
            pass

        class Fighter(Tag):
            @Post
            def Fit(agent):
                return agent.fit

        self.Wizard, self.Fighter = Wizard, Fighter
        self.ari, self.bo, self.cal = Agent(), Agent(), Agent()
        self.bo.fit, self.cal.fit = True, False
        Wizard(self.ari)
        Wizard(self.bo)
        Fighter(self.bo)

        with self.assertRaises(Postcondition.Fit):
            Fighter(self.cal)                                         # a defective Fighter

    def test_union_of_sound_populations_in_application_order(self) -> None:
        both = self.Wizard | self.Fighter

        self.assertEqual(list(both), [self.ari, self.bo])             # cal is defective: not sound
        self.assertEqual(len(both), 2)
        self.assertTrue(both)
        self.assertIn(self.bo, both)
        self.assertNotIn(self.cal, both)
        self.assertEqual(list(self.Fighter | self.Wizard), [self.bo, self.ari])

    def test_union_of_whole_fields_includes_the_defective(self) -> None:
        everyone = self.Wizard[:] | self.Fighter[:]

        self.assertEqual(list(everyone), [self.ari, self.bo, self.cal])
        self.assertIn(self.cal, everyone)

    def test_intersection_and_difference(self) -> None:
        self.assertEqual(list(self.Wizard & self.Fighter), [self.bo])
        self.assertEqual(list(self.Wizard - self.Fighter), [self.ari])
        self.assertEqual(list(self.Wizard[:] - self.Fighter[:]), [self.ari])
        self.assertIn(self.ari, self.Wizard - self.Fighter)
        self.assertNotIn(self.bo, self.Wizard - self.Fighter)

    def test_levels_mix_and_the_defective_view_combines(self) -> None:
        self.assertEqual(list(~self.Fighter | self.Wizard), [self.cal, self.ari, self.bo])
        self.assertEqual(list(self.Wizard[:] & ~self.Fighter), [])
        self.assertEqual(list(self.Fighter[:] - self.Wizard), [self.cal])

    def test_tilde_absorbs_broken_twice_is_still_broken(self) -> None:
        """The Director's rule: "bad bad = bad". Every run of ``~`` is
        the defective population, never the sound one."""

        broken = ~self.Fighter

        for spelling in (
                ~~self.Fighter,
                ~~~self.Fighter,
                ~~~~~~~~~~~~~self.Fighter,
                ~broken,
                ):
            self.assertEqual(repr(spelling), "<defective Field>")
            self.assertEqual(list(spelling), [self.cal])
            self.assertEqual(len(spelling), 1)
            self.assertTrue(spelling)
            self.assertIn(self.cal, spelling)
            self.assertNotIn(self.bo, spelling)

        self.assertEqual(list(~~self.Wizard), [])
        self.assertFalse(~~self.Wizard)

        self.cal.fit = True
        self.assertEqual(list(~~self.Fighter), [])
        self.assertEqual(list(~~~self.Fighter), [])
        self.assertEqual(list(self.Fighter), [self.bo, self.cal])

    def test_a_combination_takes_no_tilde(self) -> None:
        for combination in (
                self.Wizard | self.Fighter,
                self.Wizard[:] & self.Fighter[:],
                ~self.Fighter - self.Wizard,
                ):
            with self.assertRaises(TypeError):
                ~combination

    def test_a_combined_view_is_lazy(self) -> None:
        both = self.Wizard | self.Fighter
        dee = Agent()
        self.Wizard(dee)                                              # joins after the view was made

        self.assertIn(dee, both)
        self.assertEqual(len(both), 3)

        self.cal.fit = True                                           # repaired: sound now
        self.assertIn(self.cal, both)

    def test_a_tag_in_an_operator_seat_keeps_typing_unions(self) -> None:
        self.assertEqual(repr(self.Wizard | self.Fighter), "<sound | sound Field>")
        union = self.Wizard | None                                    # a typing union, untouched

        self.assertIsNot(union, NotImplemented)
        self.assertIn("Wizard", repr(union))

        with self.assertRaises(TypeError):
            self.Wizard & 3

    def test_a_plain_class_with_a_sound_name_stays_a_type_union(self) -> None:
        class Ordinary:
            @staticmethod
            def _sound() -> None:
                raise AssertionError("a plain class is not a TOP population")

        union = self.Wizard | Ordinary
        reverse = Ordinary | self.Wizard

        self.assertIsInstance(self.ari, union)
        self.assertIsInstance(Ordinary(), union)
        self.assertIsInstance(self.ari, reverse)
        self.assertIsInstance(Ordinary(), reverse)

    def test_a_tag_may_use_sound_as_its_own_name(self) -> None:
        class Choir(Tag):
            @staticmethod
            def _sound() -> str:
                return "the program's value"

        solo = Agent()
        Choir(solo)

        self.assertEqual(Choir._sound(), "the program's value")
        self.assertEqual(list(Choir), [solo])
        self.assertEqual(len(Choir), 1)
        self.assertGreater(len(Choir), 0)
        self.assertEqual(
                list(Choir | self.Wizard),
                [solo, self.ari, self.bo],
                )

    def test_a_report_or_operation_named_sound_does_not_replace_the_field(self) -> None:
        class Reported(Tag):
            @Report
            def _sound(tag) -> str:
                return "the report"

        class Operated(Tag):
            @Operation
            def _sound(tag, agent) -> object:
                return agent

        report_agent = Agent()
        operation_agent = Agent()
        Reported(report_agent)
        Operated(operation_agent)

        self.assertEqual(Reported._sound, "the report")
        self.assertIs(Operated._sound(operation_agent), operation_agent)
        self.assertEqual(list(Reported), [report_agent])
        self.assertEqual(list(Operated), [operation_agent])
        self.assertEqual(list(~Reported), [])
        self.assertEqual(list(Operated[:]), [operation_agent])
