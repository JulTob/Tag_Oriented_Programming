"""Conformance tests: overlay."""

from __future__ import annotations

import gc
import inspect
import unittest
import weakref
from TopKit import Action
from TopKit import Apply
from TopKit import Pin
from TopKit import Rip
from TopKit import Tag
from TopKit import TagOverwriteWarning
from TopKit import Underlay

from ._fixtures import Agent
from ._fixtures import Berserker
from ._fixtures import Combatant
from ._fixtures import Elf
from ._fixtures import Missing_Action
from ._fixtures import Needs_Action_Underlay
from ._fixtures import OOP_Refinement
from ._fixtures import Pacifist
from ._fixtures import Paladin
from ._fixtures import Person
from ._fixtures import Politely
from ._fixtures import Repaired_Pacifist


class OverlayTests(unittest.TestCase):
    def test_the_overwrite_warning_points_through_apply(self) -> None:
        class Guard(Tag):
            @Action
            def Patrol(agent):
                return "guard"

        class Intruder(Tag):
            @Action
            def Patrol(agent):
                return "intruder"

        ari = Agent()
        Guard(ari)

        with self.assertWarns(TagOverwriteWarning) as caught:
            expected_line = inspect.currentframe().f_lineno + 1
            Apply(ari, Intruder)

        self.assertEqual(caught.filename, __file__)
        self.assertEqual(caught.lineno, expected_line)

    def test_the_overwrite_warning_keeps_a_sibling_directory_frame(self) -> None:
        from pathlib import Path
        import TopKit

        caller_file = Path(TopKit.__file__).parent.with_name("TopKitApp") / "application.py"

        for call in ("tag(agent)", "Apply(agent, tag)"):
            with self.subTest(call=call):
                namespace = {"__name__": "topkit_warning_caller", "Apply": Apply}
                exec(
                        compile(
                                "def Tag_Here(agent, tag):\n    " + call + "\n",
                                str(caller_file),
                                "exec",
                                ),
                        namespace,
                        )
                ari = Agent()
                Elf(ari)

                with self.assertWarns(TagOverwriteWarning) as caught:
                    namespace["Tag_Here"](ari, Berserker)

                self.assertEqual(caught.filename, str(caller_file))
                self.assertEqual(caught.lineno, 2)
                self.assertEqual(ari.Attack(), "Reckless attack!")

    def test_underlay_captures_the_visible_overlay_at_tagging_time(self) -> None:
        ari = Agent()

        Elf(ari)
        Paladin(ari)

        self.assertEqual(ari.Attack(), "With elven grace Attack! with a holy oath.")
        self.assertEqual(ari.Paladin.Attack(), "With elven grace Attack! with a holy oath.")

        with self.assertWarns(TagOverwriteWarning):
            Berserker(ari)

        self.assertEqual(ari.Attack(), "Reckless attack!")
        self.assertEqual(ari.Paladin.Attack(), "With elven grace Attack! with a holy oath.")

    def test_agent_action_calls_resolve_the_current_overlay(self) -> None:
        ari = Agent()

        Elf(ari)
        Combatant(ari)

        self.assertEqual(ari.Combat(), "With elven grace Attack!")

        with self.assertWarns(TagOverwriteWarning):
            Berserker(ari)

        self.assertEqual(ari.Combat(), "Reckless attack!")

    def test_underlay_can_refine_an_original_oop_action(self) -> None:
        ari = Agent()

        OOP_Refinement(ari)

        self.assertEqual(ari.Attack(), "Refined Faulty OOP attack!")

    def test_underlay_decorator_extends_with_any_parameter_name(self) -> None:
        ari = Agent()

        Politely(ari)

        self.assertEqual(ari.Greet(), "Hello and hi good day")

    def test_actions_are_bound_handles_that_do_not_pin_the_agent(self) -> None:
        ari = Agent()

        Person(ari)
        attack = ari.Attack
        reference = weakref.ref(ari)

        self.assertEqual(attack(), "Attack!")
        self.assertEqual(attack.__name__, "Attack")

        del ari
        gc.collect()

        self.assertIsNone(reference())

        with self.assertRaises(ReferenceError):
            attack()

    def test_missing_underlay_is_a_callable_null_action(self) -> None:
        ari = Agent()

        Missing_Action(ari)

        self.assertIn(ari, Missing_Action)
        self.assertIsNone(ari.Missing())

    def test_null_underlay_accepts_forwarded_and_explicit_arguments(self) -> None:
        class Host:
            def __getattr__(self, name):
                raise AssertionError(f"host fallback invoked for {name}")

        class Arriving(Tag):
            @Action
            @Underlay
            def Work(agent, prior, value):
                return (prior(), prior("other", detail=True), value)

        agent = Host()
        Arriving(agent)
        self.assertEqual(agent.Work("task"), (None, None, "task"))

    def test_pin_action_on_a_shape_without_a_prior_action_uses_null(self) -> None:
        class Base(Tag):
            pass

        class Shape(Base):
            pass

        @Pin
        class Patch(Tag):
            @Action
            @Underlay
            def Work(tag, prior, value):
                return (prior(value, detail=True), value)

        Patch(Shape)
        self.assertEqual(Shape.Work("task"), (None, "task"))

    def test_special_method_action_uses_null_underlay(self) -> None:
        class Product(Tag):
            @Underlay
            def __matmul__(agent, prior, other):
                return (prior("unused", detail=True), other)

        agent = Agent()
        Product(agent)
        self.assertEqual(agent @ 7, (None, 7))

    def test_first_rip_action_can_call_null_underlay(self) -> None:
        calls = []

        class Departing(Tag):
            @Rip
            @Underlay
            def Close(agent, prior):
                calls.append(prior())

        agent = Agent()
        Departing(agent)
        del Departing[agent]
        self.assertEqual(calls, [None])

    def test_deletion_removes_oop_members_and_resets_the_underlay(self) -> None:
        ari = Agent()

        Pacifist(ari)

        self.assertFalse(hasattr(ari, "Attack"))
        self.assertFalse(hasattr(ari, "weapon"))

        Needs_Action_Underlay(ari)
        self.assertIn(ari, Needs_Action_Underlay)
        self.assertIsNone(ari.Attack())

        with self.assertWarns(TagOverwriteWarning):
            Repaired_Pacifist(ari)

        self.assertEqual(ari.Attack(), "Defensive action!")
        self.assertEqual(ari.weapon, "shield")
