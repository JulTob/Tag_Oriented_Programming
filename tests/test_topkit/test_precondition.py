"""Conformance tests: precondition."""

from __future__ import annotations

import unittest
from TopKit import Imprint
from TopKit import Post
from TopKit import Pre
from TopKit import Precondition
from TopKit import Record
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagDeclarationError
from TopKit import TagPreconditionError
from TopKit import Underlay

from ._fixtures import Agent
from ._fixtures import Citadel
from ._fixtures import Coded
from ._fixtures import Field_Member
from ._fixtures import Recruit
from ._fixtures import Scholar
from ._fixtures import Territory


class PreconditionTests(unittest.TestCase):
    def test_preconditions_gate_only_the_current_call(self) -> None:
        ari = Agent()

        Coded(ari, code="x")
        Field_Member(ari)

        self.assertIn(ari, Field_Member)

    def test_application_inputs_reach_preconditions_and_imprints(self) -> None:
        ari = Agent()

        with self.assertRaises(TagPreconditionError):
            Coded(ari)

        self.assertNotIn(ari, Coded)

        Coded(ari, code="x")
        self.assertIn(ari, Coded)

        bond = Agent()
        Recruit(bond, code="007")
        self.assertEqual(bond.code, "007")

    def test_records_take_inputs_by_name(self) -> None:
        class MI6(Tag):
            @Record
            def code(agent, *, code):
                return code

            @Record
            def aliases(agent, stored, alias=None):
                return (stored or []) + ([alias] if alias else [])

        bond = Agent()
        bond.aliases = ["Jimmy"]

        MI6(bond, code="007", alias="Bond")

        self.assertEqual(bond.code, "007")
        self.assertEqual(bond.aliases, ["Jimmy", "Bond"])

        quiet = Agent()
        MI6(quiet)

        self.assertIsNone(quiet.code)           # unsupplied, no default
        self.assertEqual(quiet.aliases, [])     # unsupplied, default kept

    def test_stored_parameter_named_like_an_input_is_refused_loudly(self) -> None:
        class Slip(Tag):
            @Record
            def code(agent, code):              # second positional = stored!
                return code

        bond = Agent()

        with self.assertRaises(TagDeclarationError) as caught:
            Slip(bond, code="007")

        self.assertIn("def code(agent, *, code)", str(caught.exception))
        self.assertNotIn(bond, Slip)

        Slip(bond)                              # no input: stored is meant
        self.assertIsNone(bond.code)

    def test_missing_input_keeps_the_declared_default_or_becomes_none(self) -> None:
        class With_Default(Tag):
            @Imprint
            def assign(agent, code="unknown") -> None:
                agent.code = code

        ari = Agent()
        With_Default(ari)
        self.assertEqual(ari.code, "unknown")

        bond = Agent()
        Recruit(bond)
        self.assertIsNone(bond.code)

    def test_a_later_gate_refusal_keeps_the_completed_base(self) -> None:
        ari = Agent()

        with self.assertRaises(TagPreconditionError):
            Citadel(ari)

        self.assertIn(ari, Territory)
        self.assertNotIn(ari, Citadel)
        self.assertEqual(ari.banner, "raised")
        self.assertTrue(isinstance(ari, Territory))
        self.assertFalse(isinstance(ari, Citadel))

        ari.charter = "royal"
        Citadel(ari)

        self.assertIn(ari, Citadel)
        self.assertEqual(ari.banner, "raised")

    def test_a_refused_tag_keeps_an_already_active_base(self) -> None:
        ari = Agent()

        Territory(ari)

        with self.assertRaises(TagPreconditionError):
            Citadel(ari)

        self.assertIn(ari, Territory)
        self.assertNotIn(ari, Citadel)
        self.assertEqual(ari.banner, "raised")

    def test_each_tag_gates_before_its_own_tagging_begins(self) -> None:
        events = []
        observed = {}

        class Foundation(Tag):
            @Pre
            def Foundation_Open(agent, code):
                events.append(f"Foundation Gate:{code}")
                return code == "007"

            @Record
            def foundation_record(agent):
                events.append("Foundation Record")
                return "built"

            def Foundation_Action(agent):
                return "ready"

            @Imprint
            def Foundation_Training(agent):
                events.append("Foundation Imprint")

        class Refused_Shape(Foundation):
            @Pre
            def Shape_Open(agent, code):
                events.append(f"Shape Gate:{code}")
                observed.update(
                        foundation_membership=agent in Foundation,
                        shape_membership=agent in Refused_Shape,
                        foundation_record="foundation_record" @ agent,
                        foundation_action="Foundation_Action" @ agent,
                        shape_record="shape_record" @ agent,
                        shape_action="Shape_Action" @ agent,
                        )
                return False

            @Record
            def shape_record(agent):
                events.append("Shape Record")
                return "not built"

            def Shape_Action(agent):
                return "not attached"

            @Imprint
            def Shape_Training(agent):
                events.append("Shape Imprint")

        ari = Agent()

        with self.assertRaises(Precondition.Shape_Open):
            Refused_Shape(ari, code="007")

        self.assertEqual(
                events,
                [
                    "Foundation Gate:007",
                    "Foundation Record",
                    "Foundation Imprint",
                    "Shape Gate:007",
                    ],
                )
        self.assertEqual(
                observed,
                {
                    "foundation_membership": True,
                    "shape_membership": False,
                    "foundation_record": True,
                    "foundation_action": True,
                    "shape_record": False,
                    "shape_action": False,
                    },
                )
        self.assertIn(ari, Foundation)
        self.assertNotIn(ari, Refused_Shape)
        self.assertEqual(ari.foundation_record, "built")
        self.assertEqual(ari.Foundation_Action(), "ready")

    def test_a_shape_gate_does_not_replace_its_base_gate(self) -> None:
        events = []

        class Base(Tag):
            @Pre
            def Ready(agent):
                events.append("Base")
                return agent.ready

        class Shape(Base):
            @Pre
            def Ready(agent):
                events.append("Shape")
                return True

        ari = Agent()
        ari.ready = False

        with self.assertRaises(Precondition.Ready):
            Shape(ari)

        self.assertEqual(events, ["Base"])
        self.assertNotIn(ari, Base)
        self.assertNotIn(ari, Shape)

        ari.ready = True
        Shape(ari)

        self.assertEqual(events, ["Base", "Base", "Shape"])
        self.assertIn(ari, Base)
        self.assertIn(ari, Shape)

    def test_a_later_condition_collision_keeps_the_completed_base(self) -> None:
        events = []

        class Foundation(Tag):
            @Record
            def foundation_record(agent):
                return "built"

            @Imprint
            def Foundation_Training(agent) -> None:
                events.append("Foundation")

        class Colliding_Shape(Foundation):
            @Post
            def Taken(agent) -> bool:
                return True

        ari = Agent()
        ari.Taken = "host value"

        with self.assertRaises(TagCompositionError):
            Colliding_Shape(ari)

        self.assertEqual(events, ["Foundation"])
        self.assertIn(ari, Foundation)
        self.assertNotIn(ari, Colliding_Shape)
        self.assertEqual(ari.foundation_record, "built")
        self.assertEqual(ari.Taken, "host value")

    def test_assert_style_precondition_fails_by_raising(self) -> None:
        ari = Agent()
        ari.level = 0

        with self.assertRaises(TagPreconditionError):
            Scholar(ari)

        self.assertNotIn(ari, Scholar)

    def test_precondition_underlay_composes_with_the_base_gate(self) -> None:
        class Apprentice(Scholar):
            @Pre
            @Underlay
            def Level_Over_Zero(agent, base):
                assert agent.mentor
                return base()

        ari = Agent()
        ari.level = 1
        ari.mentor = None

        with self.assertRaises(TagPreconditionError):
            Apprentice(ari)

        self.assertIn(ari, Scholar)
        self.assertNotIn(ari, Apprentice)

        ari.mentor = "Elminster"
        Apprentice(ari)

        self.assertIn(ari, Apprentice)
