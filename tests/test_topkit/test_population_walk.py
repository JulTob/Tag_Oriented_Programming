"""Conformance tests: population walk."""

from __future__ import annotations

import gc
import unittest
import weakref
from TopKit import Pin
from TopKit import Post
from TopKit import Tag
from TopKit import TagContractError

from ._fixtures import Agent


class PopulationWalkTests(unittest.TestCase):
    """STEP-SPEC-35: a walk saves join order, then asks membership at
    each member's turn."""

    @staticmethod
    def walked(population, act) -> list[object]:
        seen = []

        for member in population:
            seen.append(member)
            act(member)

        return seen

    def test_a_ripped_member_is_skipped_by_each_field_view(self) -> None:
        for view in ("sound", "whole", "defective"):
            with self.subTest(view=view):
                class Wizard(Tag):
                    @Post
                    def Ready(agent):
                        return agent.ready

                ari, bo, cal = Agent(), Agent(), Agent()

                for member in (ari, bo, cal):
                    Wizard(member)

                if view == "defective":
                    for member in (ari, bo, cal):
                        member.ready = False

                    population = ~Wizard
                elif view == "whole":
                    population = Wizard[:]
                else:
                    population = Wizard

                def Rip_Cal(member) -> None:
                    if member is ari:
                        del Wizard[cal]

                self.assertEqual(self.walked(population, Rip_Cal), [ari, bo])

    def test_a_pin_walk_skips_a_tag_ripped_before_its_turn(self) -> None:
        @Pin
        class School(Tag):
            pass

        class Mage(Tag):
            pass

        class Bard(Tag):
            pass

        class Druid(Tag):
            pass

        for tag in (Mage, Bard, Druid):
            School(tag)

        def Rip_Druid(tag) -> None:
            if tag is Mage:
                del School[Druid]

        self.assertEqual(self.walked(School, Rip_Druid), [Mage, Bard])

    def test_combined_walks_skip_a_member_ripped_from_the_left(self) -> None:
        for operator in ("|", "&", "-"):
            with self.subTest(operator=operator):
                class Left(Tag):
                    pass

                class Right(Tag):
                    pass

                ari, bo, cal = Agent(), Agent(), Agent()

                for member in (ari, bo, cal):
                    Left(member)

                if operator != "-":
                    for member in (ari, bo, cal):
                        Right(member)

                if operator == "|":
                    population = Left[:] | Right[:]
                elif operator == "&":
                    population = Left[:] & Right[:]
                else:
                    population = Left[:] - Right[:]

                def Rip_Bo(member) -> None:
                    if member is ari:
                        del Left[bo]

                        if operator == "|":
                            del Right[bo]

                self.assertEqual(self.walked(population, Rip_Bo), [ari, cal])

    def test_a_lazy_unions_right_field_starts_when_reached(self) -> None:
        """This change preserves the algebra's per-side walk timing."""

        class Wizard(Tag):
            pass

        class Fighter(Tag):
            pass

        ari, bo, cal = Agent(), Agent(), Agent()
        Wizard(ari)
        Fighter(bo)
        combatants = Wizard[:] | Fighter[:]

        def Join_Right(member) -> None:
            if member is ari:
                Fighter(cal)                                         # before the right Field starts

        self.assertEqual(self.walked(combatants, Join_Right), [ari, bo, cal])

    def test_a_union_walk_keeps_seen_identity_stable_until_it_finishes(self) -> None:
        class Wizard(Tag):
            pass

        class Fighter(Tag):
            pass

        class Druid(Tag):
            pass

        ari, bo, cal = Agent(), Agent(), Agent()
        Wizard(ari)
        Fighter(bo)
        Druid(cal)
        reference = weakref.ref(ari)
        combatants = iter((Wizard[:] | Fighter[:]) | Druid[:])

        self.assertIs(next(combatants), ari)
        del ari
        self.assertIs(next(combatants), bo)
        self.assertIs(next(combatants), cal)
        gc.collect()

        self.assertIsNotNone(reference())
        self.assertEqual([member for member in combatants], [])
        gc.collect()
        self.assertIsNone(reference())

    def test_a_new_member_waits_but_a_retagged_member_keeps_its_turn(self) -> None:
        class Wizard(Tag):
            pass

        ari, bo, cal, dee = Agent(), Agent(), Agent(), Agent()

        for member in (ari, bo, cal):
            Wizard(member)

        def Change_Field(member) -> None:
            if member is ari:
                del Wizard[bo]
                Wizard(bo)                                           # in again before its saved turn
                Wizard(dee)                                          # no saved turn in this walk

        self.assertEqual(self.walked(Wizard, Change_Field), [ari, bo, cal])
        self.assertEqual(list(Wizard), [ari, cal, bo, dee])

    def test_retagging_after_a_saved_turn_does_not_visit_it_twice(self) -> None:
        class Wizard(Tag):
            pass

        ari, bo, cal = Agent(), Agent(), Agent()

        for member in (ari, bo, cal):
            Wizard(member)

        def Return_Ari(member) -> None:
            if member is bo:
                del Wizard[ari]
                Wizard(ari)

        self.assertEqual(self.walked(Wizard[:], Return_Ari), [ari, bo, cal])
        self.assertEqual(list(Wizard[:]), [bo, cal, ari])

    def test_population_queries_share_membership_at_turn(self) -> None:
        def ask(question):
            checks = []
            changing = [False]
            pair: list[object] = []

            class Enemy(Tag):
                @Post
                def Standing(agent):
                    checks.append(agent)

                    if changing[0] and agent is pair[0]:
                        del Enemy[pair[1]]
                        return False

                    return True

            pair[:] = [Agent(), Agent()]
            Enemy(pair[0])
            Enemy(pair[1])
            checks.clear()
            changing[0] = True

            return question(Enemy), checks, pair

        questions = (
                ("population truth", lambda population: bool(population & population), False),
                ("length", len, 0),
                ("iteration", lambda population: [member for member in population], []),
                )

        for name, question, expected in questions:
            with self.subTest(question=name):
                answer, checks, pair = ask(question)

                self.assertEqual(answer, expected)
                self.assertEqual(checks, [pair[0]])

    def test_a_sound_view_rechecks_membership_after_its_postcondition(self) -> None:
        ripping = [False]

        class Wizard(Tag):
            @Post
            def Ready(agent):
                if ripping[0]:
                    del Wizard[agent]

                return True

        class Fighter(Tag):
            pass

        ari, bo = Agent(), Agent()
        Wizard(ari)
        Wizard(bo)
        ripping[0] = True

        self.assertEqual([member for member in Wizard], [])
        self.assertNotIn(ari, Wizard[:])

        cal = Agent()
        ripping[0] = False
        Wizard(cal)
        ripping[0] = True
        self.assertNotIn(cal, Wizard | Fighter)
        self.assertNotIn(cal, Wizard[:])

        dee = Agent()
        ripping[0] = False
        Wizard(dee)
        ripping[0] = True
        self.assertNotIn(dee, Wizard)                            # direct Tag membership also rechecks
        self.assertNotIn(dee, Wizard[:])

    def test_a_defective_view_rechecks_membership_after_its_postcondition(self) -> None:
        ripping = [False]

        class Wizard(Tag):
            @Post
            def Ready(agent):
                if ripping[0]:
                    del Wizard[agent]

                return not ripping[0]

        ari, bo = Agent(), Agent()
        Wizard(ari)
        Wizard(bo)
        ripping[0] = True

        self.assertEqual([member for member in ~Wizard], [])
        self.assertNotIn(ari, Wizard[:])

        cal = Agent()
        ripping[0] = False
        Wizard(cal)
        ripping[0] = True
        self.assertNotIn(cal, ~Wizard)
        self.assertNotIn(cal, Wizard[:])

    def test_a_post_cannot_rip_then_retag_during_its_own_soundness_check(self) -> None:
        ripping = [False]
        reapplied = [False]

        class Wizard(Tag):
            @Post
            def Ready(agent):
                if ripping[0] and not reapplied[0]:
                    reapplied[0] = True
                    del Wizard[agent]
                    Wizard(agent)

                return True

        ari = Agent()
        Wizard(ari)
        ripping[0] = True

        with self.assertRaisesRegex(TagContractError, "Post cannot ask"):
            list(Wizard)
        self.assertNotIn(ari, Wizard[:])

        # Outside the Post's own check, a fresh Tagging can start normally.
        ripping[0] = False
        Wizard(ari)
        self.assertIn(ari, Wizard[:])

    def test_a_one_pass_materialization_uses_a_comprehension(self) -> None:
        checks = []

        class Wizard(Tag):
            @Post
            def Ready(agent):
                checks.append(agent)
                return True

        ari, bo = Agent(), Agent()
        Wizard(ari)
        Wizard(bo)
        checks.clear()

        members = [member for member in Wizard]

        self.assertEqual(members, [ari, bo])
        self.assertEqual(checks, [ari, bo])
