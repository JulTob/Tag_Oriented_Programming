"""TagKit conformance tests, ring by ring.

Ring 0  Kernel: identity, membership, Geometry, Fields.
Ring 1  Contributions: Overlay, Underlay, Records, publication.
Ring 2  Contracts: Pre, Imprint, Post, defective taggings.
Ring 3  Lifecycle: Rip, teardown, Scope, exit.
Ring 4  Access and queries.
"""

from __future__ import annotations

import copy
import gc
import unittest
import warnings
import weakref

from TagKit import Action
from TagKit import Apply
from TagKit import At_Exit
from TagKit import Contract
from TagKit import Delete
from TagKit import Flag
from TagKit import Form
from TagKit import Keyword
from TagKit import Imprint
from TagKit import Operation
from TagKit import Outline
from TagKit import Post
from TagKit import Postcondition
from TagKit import Pre
from TagKit import Precondition
from TagKit import Public
from TagKit import Record
from TagKit import Report
from TagKit import Rip
from TagKit import Scope
from TagKit import Secret
from TagKit import Tag
from TagKit import TagCompositionError
from TagKit import TagContractError
from TagKit import TagContractWarning
from TagKit import TagDeclarationError
from TagKit import TagImprintError
from TagKit import TagOverwriteWarning
from TagKit import TagPostconditionError
from TagKit import TagPreconditionError
from TagKit import TagResolutionError
from TagKit import Tags
from TagKit import Underlay
import TagKit.lifecycle as lifecycle


# ==================================================================
# Fixtures
# ==================================================================


class Agent:
    def __init__(
            agent,
            ) -> None:
        agent.events: list[str] = []
        agent.allowed = True
        agent.ready = True
        agent.weapon = "faulty weapon"

    def Attack(
            agent,
            ) -> str:
        return "Faulty OOP attack!"


class Root(Tag):
    @Imprint
    def Mark_Root(agent) -> None:
        agent.events.append("Root")


class Left(Root):
    @Imprint
    def Mark_Left(agent) -> None:
        agent.events.append("Left")


class Right(Root):
    @Imprint
    def Mark_Right(agent) -> None:
        agent.events.append("Right")


class Bridge(Left, Right):
    @Imprint
    def Mark_Bridge(agent) -> None:
        agent.events.append("Bridge")


class Person(Tag):
    def Attack(agent) -> str:
        return "Attack!"


class Elf(Person):
    @Underlay
    def Attack(agent, underlay) -> str:
        return "With elven grace " + underlay()


class Paladin(Person):
    @Underlay
    def Attack(agent, underlay) -> str:
        return underlay() + " with a holy oath."


class Berserker(Tag):
    def Attack(agent) -> str:
        return "Reckless attack!"


class Combatant(Tag):
    def Combat(agent) -> str:
        return agent.Attack()


class OOP_Refinement(Tag):
    @Underlay
    def Attack(agent, underlay) -> str:
        return "Refined " + underlay()


class Inventory(Tag):
    @Record
    def items(agent) -> list[str]:
        return []


class Armed(Tag):
    @Record
    def weapon(agent) -> str:
        return "arcane staff"


class Prepared(Inventory):
    @Record
    def items(agent, stored) -> list[str]:
        return stored + ["rope"]


class Lost_Inventory(Prepared):
    @Delete
    def items(agent) -> None:
        pass


class Rebuilt_Inventory(Lost_Inventory):
    @Record
    def items(agent, stored) -> list[str]:
        assert stored is None
        return ["shield"]


class Pacifist(Tag):
    @Delete
    def Attack(agent) -> None:
        pass

    @Delete
    def weapon(agent) -> None:
        pass


class Needs_Action_Underlay(Pacifist):
    @Underlay
    def Attack(agent, underlay) -> str:
        return underlay()


class Repaired_Pacifist(Pacifist):
    def Attack(agent) -> str:
        return "Defensive action!"

    @Record
    def weapon(agent) -> str:
        return "shield"


class Species(Tag):
    @Imprint
    def Establish_Species(agent) -> None:
        agent.events.append("Species")


class Validated(Tag):
    @Precondition
    def Is_Allowed(agent) -> bool:
        return agent.allowed

    @Postcondition
    def Is_Ready(agent) -> bool:
        return agent.ready


class Advanced(Validated):
    pass


class Candidate_Record(Tag):
    @Record
    def token(agent) -> str:
        return "prepared"

    @Postcondition
    def Accepts_Token(agent) -> bool:
        return agent.ready


class Ordered_Imprints(Tag):
    @Imprint
    def First(agent) -> None:
        agent.events.append("First")

    @Imprint
    def Second(agent) -> None:
        agent.events.append("Second")


class Stocked(Tag):
    @Imprint
    def Note_Stocking(agent) -> None:
        agent.events.append("Stocked")

    @Record
    def supplies(agent) -> list[str]:
        return ["ration"]


class Broken_Imprint(Tag):
    @Imprint
    def Begin_Then_Fail(agent) -> None:
        agent.events.append("before failure")
        raise RuntimeError("expected imprint failure")


class Community(Tag):
    colour = Report("green")

    @Operation
    def Greet(tag, name: str) -> str:
        return f"{tag.__name__}:{name}"


class Silent_Community(Community):
    @Delete
    def colour(agent) -> None:
        pass

    @Delete
    def Greet(agent) -> None:
        pass


class Missing_Action(Tag):
    @Underlay
    def Missing(agent, underlay) -> str:
        return underlay()


class Arithmetic(Tag):
    def __add__(agent, amount: int) -> int:
        return amount + 1


class Field_Member(Tag):
    pass


class Territory(Tag):
    @Record
    def banner(agent) -> str:
        return "raised"


class Citadel(Territory):
    @Precondition
    def Has_Charter(agent) -> bool:
        return hasattr(agent, "charter")


class Cursed_Blade(Tag):
    @Record
    def weapon(agent) -> str:
        return "cursed dagger"

    @Postcondition
    def Is_Worthy(agent) -> bool:
        return agent.ready


class Squire(Tag):
    @Imprint
    def Enlist(agent) -> None:
        agent.events.append("Squire")

    @Record
    def rank(agent) -> str:
        return "squire"


class Knighted(Tag):
    @Imprint
    def Knight(agent) -> None:
        agent.events.append("Knighted")

    @Action
    @Rip
    def rank_reset(agent) -> str:
        agent.rank = None
        return "Disrobed"


class Beast(Tag):
    @Record
    def legs(agent) -> int:
        return 4


class Wolf(Beast):
    @Record
    def howl(agent) -> str:
        return "Awooo"


class Base_Greeting(Tag):
    def Greet(agent) -> str:
        return "hi"


class Greeter(Base_Greeting):
    @Action
    @Underlay
    def Greet(agent, base) -> str:
        return "Hello and " + base()


class Politely(Greeter):
    @Action
    @Underlay
    def Greet(agent, prior) -> str:
        return prior() + " good day"


class Slotted_Agent:
    __slots__ = ()


_DEL_LOG: list[str] = []


class Sentry(Tag):
    @Action
    @Rip
    def stand_down(agent) -> str:
        _DEL_LOG.append("stood down")
        return "stood down"


class Recruit(Tag):
    @Imprint
    def assign(spy, code) -> None:
        spy.code = code


class Coded(Tag):
    @Precondition
    def Has_Code(agent, code) -> bool:
        return code is not None


class Scholar(Tag):
    @Pre
    def Level_Over_Zero(agent):
        assert agent.level > 0

    @Imprint
    def Grant_Book(agent):
        agent.spellbook = "Tome"

    @Post
    def Has_Book(agent):
        assert agent.spellbook


class Capped(Tag):
    @Post
    def Strength_Capped(agent):
        return agent.strength <= 20


class Bruiser(Capped):
    @Post
    def Strength_Capped(agent):
        return agent.strength <= 24


class Disciplined(Capped):
    @Post
    @Underlay
    def Strength_Capped(agent, base):
        return base() and agent.strength <= 18


class Reflective(Tag):
    @Post
    def Self_Aware(agent):
        if agent:
            return True


class Slotted(Tag):
    @Post
    def Raw_Slots(agent):
        return agent.spell_slots


class Reserved(Tag):
    @Post
    def Has_Slots_Record(agent):
        assert agent.spell_slots is not None


# ==================================================================
# Ring 0: Kernel
# ==================================================================


class KernelTests(unittest.TestCase):
    def test_tagging_preserves_identity_and_builds_base_membership(self) -> None:
        ari = Agent()
        returned = Elf(ari)

        self.assertIs(returned, ari)
        self.assertIn(ari, Elf)
        self.assertIn(ari, Person)
        self.assertIsInstance(ari, Elf)
        self.assertIsInstance(ari, Person)

    def test_runtime_type_keeps_the_host_name(self) -> None:
        ari = Agent()

        Elf(ari)

        self.assertEqual(type(ari).__name__, "Agent")
        self.assertIsInstance(ari, Agent)

    def test_direct_bases_apply_in_declaration_order_and_diamond_once(self) -> None:
        ari = Agent()

        Bridge(ari)

        self.assertEqual(ari.events, ["Root", "Left", "Right", "Bridge"])
        self.assertIn(ari, Root)
        self.assertIn(ari, Left)
        self.assertIn(ari, Right)
        self.assertEqual(Form(Bridge), (Root, Left, Right, Bridge))

    def test_active_reapply_is_a_strict_noop(self) -> None:
        ari = Agent()

        Stocked(ari)
        ari.supplies.append("torch")
        ari.events.append("between")
        Stocked(ari)

        self.assertEqual(ari.supplies, ["ration", "torch"])
        self.assertEqual(ari.events, ["Stocked", "between"])
        self.assertEqual(list(Stocked[:]).count(ari), 1)

    def test_fields_are_non_owning_and_iterable_from_the_tag(self) -> None:
        ari = Agent()
        Field_Member(ari)
        reference = weakref.ref(ari)

        self.assertEqual(list(Field_Member[:]), [ari])
        self.assertEqual(list(Field_Member), [ari])
        self.assertEqual(len(Field_Member[:]), 1)
        self.assertEqual(len(Field_Member), 1)
        self.assertTrue(Field_Member)
        self.assertTrue(Field_Member[:])
        self.assertFalse(~Field_Member)

        del ari
        gc.collect()

        self.assertIsNone(reference())
        self.assertEqual(list(Field_Member[:]), [])
        self.assertFalse(Field_Member)
        self.assertFalse(Field_Member[:])

    def test_fields_index_by_identity_not_equality(self) -> None:
        class Twin:
            def __eq__(self, other) -> bool:
                return True

            def __hash__(self) -> int:
                return 1

        one = Twin()
        two = Twin()

        Field_Member(one)
        Field_Member(two)

        self.assertEqual(len(Field_Member[:]), 2)

        del Field_Member[one]

        self.assertEqual(list(Field_Member[:]), [two])

    def test_targets_that_cannot_carry_top_state_fail_explicitly(self) -> None:
        target = Slotted_Agent()

        with self.assertRaises(TagCompositionError):
            Person(target)

    def test_membership_queries_do_not_actualize_an_untagged_target(self) -> None:
        ari = Agent()

        self.assertNotIn(ari, Person)
        self.assertFalse(hasattr(ari, "_TAGKIT_STATE"))
        self.assertEqual(Tags(ari), ())

    def test_a_tag_needs_a_target(self) -> None:
        with self.assertRaises(TypeError):
            Person()

        with self.assertRaises(TypeError):
            Person(Agent)

    def test_isinstance_is_a_reliable_has_been_check(self) -> None:
        ari = Agent()

        Squire(ari)
        self.assertIsInstance(ari, Squire)

        del Squire[ari]
        self.assertNotIn(ari, Squire)
        self.assertIsInstance(ari, Squire)

        Knighted(ari)
        self.assertIsInstance(ari, Squire)
        self.assertIsInstance(ari, Knighted)

    def test_runtime_types_are_shared_across_agents_and_shapes(self) -> None:
        ari = Agent()
        bea = Agent()

        Elf(ari)
        Paladin(bea)

        # The runtime type is neutral: it does not depend on which Tags are
        # active, only on what the host needs at type level.
        self.assertIs(type(ari), type(bea))

    def test_special_method_actions_actualize_the_agent(self) -> None:
        ari = Agent()
        bea = Agent()

        Arithmetic(ari)
        Arithmetic(bea)

        self.assertEqual(ari + 4, 5)
        self.assertEqual(bea + 1, 2)


class HostPreservationTests(unittest.TestCase):
    """Tagging must not change what the host object already does."""

    class Bag:
        def __init__(self) -> None:
            self.items = ["x"]

        def __contains__(self, key) -> bool:
            return key in self.items

        def __len__(self) -> int:
            return len(self.items)

        def __or__(self, other) -> str:
            return "host-or"

        def __getattr__(self, name) -> str:
            if name == "dynamic":
                return "from host getattr"

            raise AttributeError(name)

    def test_host_special_methods_survive_tagging(self) -> None:
        bag = self.Bag()

        Field_Member(bag)

        self.assertIn("x", bag)
        self.assertNotIn(Field_Member, bag)       # the host keeps its `in`
        self.assertEqual(bag | 1, "host-or")
        self.assertTrue(bool(bag))

        bag.items.clear()

        self.assertFalse(bool(bag))
        self.assertEqual(bag.dynamic, "from host getattr")

    def test_tag_members_do_not_leak_onto_the_agent(self) -> None:
        ari = Agent()

        Community(ari)

        self.assertFalse(hasattr(ari, "colour"))
        self.assertFalse(hasattr(ari, "Greet"))
        self.assertFalse(hasattr(ari, "Form"))
        self.assertFalse(hasattr(ari, "Field"))
        self.assertEqual(Community.colour, "green")
        self.assertEqual(Community.Greet("Ari"), "Community:Ari")

    def test_copying_an_agent_is_refused_explicitly(self) -> None:
        ari = Agent()

        Squire(ari)

        with self.assertRaises(TagCompositionError):
            copy.copy(ari)

        with self.assertRaises(TagCompositionError):
            copy.deepcopy(ari)


# ==================================================================
# Ring 1: Contributions
# ==================================================================


class OverlayTests(unittest.TestCase):
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

    def test_missing_underlay_raises_a_resolution_error(self) -> None:
        ari = Agent()

        with self.assertRaises(TagResolutionError):
            Missing_Action(ari)

        self.assertNotIn(ari, Missing_Action)

    def test_deletion_removes_oop_members_and_resets_the_underlay(self) -> None:
        ari = Agent()

        Pacifist(ari)

        self.assertFalse(hasattr(ari, "Attack"))
        self.assertFalse(hasattr(ari, "weapon"))

        with self.assertRaises(TagResolutionError):
            Needs_Action_Underlay(ari)

        Repaired_Pacifist(ari)

        self.assertEqual(ari.Attack(), "Defensive action!")
        self.assertEqual(ari.weapon, "shield")


class RecordTests(unittest.TestCase):
    def test_records_are_fresh_per_agent_and_extend_the_stored_value(self) -> None:
        ari = Agent()
        bea = Agent()

        Prepared(ari)
        Inventory(bea)

        self.assertEqual(ari.items, ["rope"])
        self.assertEqual(bea.items, [])
        self.assertIsNot(ari.items, bea.items)

    def test_independent_tags_pile_up_on_one_record(self) -> None:
        class Elf_Spells(Tag):
            @Record
            def spells(agent, stored):
                return (stored or []) + ["Light"]

        class Wizard_Spells(Tag):
            @Record
            def spells(agent, stored):
                return (stored or []) + ["Fireball"]

        class Sage_Spells(Tag):
            @Record
            @Underlay
            def spells(agent, stored):
                return (stored or []) + ["Identify"]

        ari = Agent()

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            Elf_Spells(ari)
            Wizard_Spells(ari)
            Sage_Spells(ari)

        self.assertEqual(ari.spells, ["Light", "Fireball", "Identify"])
        self.assertEqual(ari.Elf_Spells.spells, ["Light"])

    def test_a_record_can_replace_an_existing_object_attribute(self) -> None:
        ari = Agent()

        Armed(ari)

        self.assertEqual(ari.weapon, "arcane staff")

    def test_a_record_can_extend_an_existing_object_attribute(self) -> None:
        class Sharpened(Tag):
            @Record
            def weapon(agent, stored):
                return "sharpened " + stored

        ari = Agent()

        Sharpened(ari)

        self.assertEqual(ari.weapon, "sharpened faulty weapon")

    def test_independent_record_replacement_without_stored_warns(self) -> None:
        ari = Agent()

        Armed(ari)

        with self.assertWarns(TagOverwriteWarning):
            Cursed_Blade(ari)

        self.assertEqual(ari.weapon, "cursed dagger")

    def test_deleted_record_has_no_stored_value_and_a_shape_can_rebuild_it(self) -> None:
        ari = Agent()

        Lost_Inventory(ari)

        self.assertFalse(hasattr(ari, "items"))

        Rebuilt_Inventory(ari)

        self.assertEqual(ari.items, ["shield"])

    def test_del_removes_a_record_the_native_way(self) -> None:
        ari = Agent()

        Armed(ari)
        del ari.weapon

        self.assertFalse(hasattr(ari, "weapon"))

    def test_record_over_a_host_property_is_refused_and_rolled_back(self) -> None:
        class Prop:
            @property
            def hp(self) -> int:
                return 1

        class Vital(Tag):
            @Record
            def hp(agent) -> int:
                return 99

        target = Prop()

        with self.assertRaises(TagCompositionError):
            Vital(target)

        self.assertNotIn(target, Vital)
        self.assertEqual(target.hp, 1)

    def test_record_builder_failure_is_a_composition_error_naming_it(self) -> None:
        class Bad(Tag):
            @Record
            def hp(agent):
                return 1 + "x"

        ari = Agent()

        with self.assertRaises(TagCompositionError) as caught:
            Bad(ari)

        self.assertIn("Bad.hp", str(caught.exception))
        self.assertNotIn(ari, Bad)

    def test_independent_tags_cannot_share_a_name_across_kinds(self) -> None:
        class Data(Tag):
            @Record
            def strike(agent) -> int:
                return 4

        class Behaviour(Tag):
            def strike(agent) -> int:
                return 1

        ari = Agent()
        Data(ari)

        with self.assertRaises(TagCompositionError):
            Behaviour(ari)

        self.assertEqual(ari.strike, 4)

    def test_a_shape_may_turn_a_base_action_into_a_record(self) -> None:
        class Combatant_(Tag):
            def strike(agent) -> int:
                return 1

        class Fire(Combatant_):
            @Record
            def strike(agent) -> int:
                return 4

        ari = Agent()
        Fire(ari)

        self.assertEqual(ari.strike, 4)
        self.assertEqual(ari.Combatant_.strike(), 1)


class PublicationTests(unittest.TestCase):
    class Fire(Tag):
        colour = Public(Report("#ef5b35"))
        heat = Report(3)

        @Public
        @Operation
        def roster(fire, agent) -> tuple:
            return tuple(a for a in fire)

        @Secret
        @Record
        def ember_heat(agent) -> int:
            return 3

        @Secret
        @Action
        def ignite(agent) -> int:
            return agent.ember_heat * 2

        @Action
        def strike(agent) -> int:
            return agent.ignite() + 1

        @Imprint
        def warm_up(agent) -> None:
            agent.warmth = agent.ember_heat

        @Rip
        def cool_down(agent) -> None:
            agent.warmth = agent.ember_heat - 3

    def test_published_report_reads_live_from_the_tag_and_is_read_only(self) -> None:
        ember = Agent()

        self.Fire(ember)

        self.assertEqual(ember.colour, "#ef5b35")
        self.assertFalse(hasattr(ember, "heat"))

        self.Fire.colour = "#ff0000"

        try:
            self.assertEqual(ember.colour, "#ff0000")
        finally:
            self.Fire.colour = "#ef5b35"

        with self.assertRaises(AttributeError):
            ember.colour = "blue"

    def test_published_operation_is_an_action_with_the_agent_as_second_input(self) -> None:
        ember = Agent()

        self.Fire(ember)

        self.assertEqual(ember.roster(), (ember,))
        self.assertEqual(self.Fire.roster(ember), (ember,))

    def test_secret_members_resolve_only_inside_composition(self) -> None:
        ember = Agent()

        self.Fire(ember)

        self.assertEqual(ember.strike(), 7)
        self.assertEqual(ember.warmth, 3)

        with self.assertRaises(AttributeError):
            ember.ignite()

        with self.assertRaises(AttributeError):
            ember.ember_heat

        self.assertFalse(hasattr(ember, "ember_heat"))

        del self.Fire[ember]

        self.assertEqual(ember.warmth, 0)

    def test_captured_secret_handles_fail_closed(self) -> None:
        ember = Agent()
        captured: list = []

        class Leak(self.Fire):
            @Action
            def leak(agent) -> None:
                captured.append(agent.ignite)

        Leak(ember)
        ember.leak()

        self.assertEqual(captured[0](), 6)

    def test_bad_mark_combinations_are_rejected_at_declaration(self) -> None:
        with self.assertRaises(TagDeclarationError):
            class Wrong(Tag):
                @Secret
                @Operation
                def op(tag) -> None:
                    pass

            Wrong(Agent())

        with self.assertRaises(TagDeclarationError):
            class Wrong_Too(Tag):
                @Public
                @Action
                def act(agent) -> None:
                    pass

            Wrong_Too(Agent())

    def test_reports_operations_and_their_deletion_follow_the_tag_view(self) -> None:
        ari = Agent()

        Community(ari)

        self.assertEqual(ari.Community.colour, "green")
        self.assertEqual(ari.Community.Greet("Ari"), "Community:Ari")

        Silent_Community(ari)

        with self.assertRaises(AttributeError):
            ari.Silent_Community.colour

        with self.assertRaises(AttributeError):
            ari.Silent_Community.Greet


# ==================================================================
# Ring 2: Contracts
# ==================================================================


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

    def test_failing_shape_rolls_back_its_bases_atomically(self) -> None:
        ari = Agent()

        with self.assertRaises(TagPreconditionError):
            Citadel(ari)

        self.assertNotIn(ari, Territory)
        self.assertNotIn(ari, Citadel)
        self.assertFalse(hasattr(ari, "banner"))
        self.assertFalse(isinstance(ari, Territory))

        ari.charter = "royal"
        Citadel(ari)

        self.assertIn(ari, Citadel)
        self.assertEqual(ari.banner, "raised")

    def test_atomic_rollback_keeps_earlier_committed_tags(self) -> None:
        ari = Agent()

        Territory(ari)

        with self.assertRaises(TagPreconditionError):
            Citadel(ari)

        self.assertIn(ari, Territory)
        self.assertNotIn(ari, Citadel)
        self.assertEqual(ari.banner, "raised")

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

        ari.mentor = "Elminster"
        Apprentice(ari)

        self.assertIn(ari, Apprentice)


class DefectiveTaggingTests(unittest.TestCase):
    def test_failed_postcondition_raises_but_the_tag_stays_defective(self) -> None:
        ari = Agent()
        ari.ready = False

        with self.assertRaises(TagPostconditionError):
            Candidate_Record(ari)

        self.assertIn(ari, Candidate_Record)          # still a member
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
        self.assertEqual(len(Candidate_Record), 1)
        self.assertEqual(len(~Candidate_Record), 1)
        self.assertEqual(len(Candidate_Record[:]), 2)
        self.assertTrue(Candidate_Record)          # someone sound
        self.assertTrue(~Candidate_Record)         # someone broken
        self.assertTrue(Candidate_Record[:])       # anyone

        bad.ready = True

        self.assertFalse(~Candidate_Record)        # nobody left to repair

    def test_posts_of_earlier_tags_recheck_on_later_tagging(self) -> None:
        ari = Agent()

        Validated(ari)
        ari.allowed = False
        Advanced(ari)
        self.assertIn(ari, Advanced)

        bea = Agent()
        Validated(bea)
        bea.ready = False

        with self.assertRaises(TagPostconditionError):
            Advanced(bea)

        self.assertIn(bea, Advanced)
        self.assertIn(bea, ~Advanced)

    def test_imprint_failure_keeps_the_tag_and_its_raw_effects(self) -> None:
        ari = Agent()

        Ordered_Imprints(ari)
        self.assertEqual(ari.events, ["First", "Second"])

        with self.assertRaises(TagImprintError):
            Broken_Imprint(ari)

        self.assertIn(ari, Broken_Imprint)
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

    def test_pre_and_post_are_aliases(self) -> None:
        self.assertIs(Pre, Precondition)
        self.assertIs(Post, Postcondition)


class ContractNamespaceTests(unittest.TestCase):
    def test_contract_namespace_checks_pre_post_and_both(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)

        self.assertTrue(Contract.Preconditions(ari))
        self.assertTrue(Contract.Postconditions(ari))
        self.assertTrue(Contract.Conditions(ari))
        self.assertTrue(Contract.Holds(ari))

        del ari.spellbook

        with self.assertRaises(TagPostconditionError):
            Contract.Conditions(ari)

    def test_contract_status_and_display(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)

        self.assertEqual(Contract.Status(ari), {"Level_Over_Zero": True, "Has_Book": True})

        del ari.spellbook
        text = Contract.Display(ari)

        self.assertTrue(text.startswith("Agent[Scholar] contract:"))
        self.assertIn("Pre:", text)
        self.assertIn("XX  Has_Book", text)


# ==================================================================
# Ring 3: Lifecycle
# ==================================================================


class RipTests(unittest.TestCase):
    def test_rip_leaves_a_rogue_agent_with_sticky_contributions(self) -> None:
        ari = Agent()

        Squire(ari)
        del Squire[ari]

        self.assertNotIn(ari, Squire)
        self.assertEqual(ari.rank, "squire")

    def test_rip_action_runs_on_rip(self) -> None:
        ari = Agent()

        Squire(ari)
        Knighted(ari)

        self.assertEqual(ari.rank_reset(), "Disrobed")

        ari.rank = "knight"
        del Knighted[ari]

        self.assertNotIn(ari, Knighted)
        self.assertIsNone(ari.rank)

    def test_rip_teardown_with_underlay_runs_composed(self) -> None:
        log: list[str] = []

        class Guard(Tag):
            def stand_down(agent) -> None:
                log.append("base")

        class Elite(Guard):
            @Rip
            @Underlay
            def stand_down(agent, base) -> None:
                base()
                log.append("elite")

        ari = Agent()
        Elite(ari)
        del Elite[ari]

        self.assertEqual(log, ["base", "elite"])

    def test_teardown_failure_is_reported_after_membership_ends(self) -> None:
        class Fragile(Tag):
            @Rip
            def boom(agent) -> None:
                raise RuntimeError("x")

        ari = Agent()
        Fragile(ari)

        with self.assertRaises(TagCompositionError):
            del Fragile[ari]

        self.assertNotIn(ari, Fragile)

    def test_ripping_a_required_base_is_refused(self) -> None:
        ari = Agent()

        Wolf(ari)

        with self.assertRaises(TagCompositionError):
            del Beast[ari]

        self.assertIn(ari, Beast)

        del Wolf[ari]
        self.assertIn(ari, Beast)

        del Beast[ari]
        self.assertNotIn(ari, Beast)

    def test_ripped_agent_is_not_yielded_by_field_iteration(self) -> None:
        ari = Agent()
        bea = Agent()

        Squire(ari)
        Squire(bea)
        del Squire[ari]

        self.assertEqual(list(Squire[:]), [bea])

    def test_ripping_an_inactive_tag_raises(self) -> None:
        ari = Agent()

        with self.assertRaises(TagResolutionError):
            del Knighted[ari]

    def test_reapply_after_rip_is_a_fresh_application(self) -> None:
        ari = Agent()

        Squire(ari)
        ari.rank = "knight"
        del Squire[ari]
        Squire(ari)

        self.assertIn(ari, Squire)
        self.assertEqual(ari.events, ["Squire", "Squire"])
        self.assertEqual(ari.rank, "squire")


class ExitProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        _DEL_LOG.clear()

    def test_rip_runs_best_effort_on_garbage_collection(self) -> None:
        ari = Agent()
        Sentry(ari)

        del ari
        gc.collect()

        self.assertEqual(_DEL_LOG.count("stood down"), 1)

    def test_explicit_rip_prevents_a_second_rip_on_collection(self) -> None:
        ari = Agent()
        Sentry(ari)
        del Sentry[ari]

        del ari
        gc.collect()

        self.assertEqual(_DEL_LOG.count("stood down"), 1)

    def test_host_finalizer_still_runs(self) -> None:
        seen: list[str] = []

        class Host:
            def __del__(self) -> None:
                seen.append("host del")

        host = Host()
        Sentry(host)

        del host
        gc.collect()

        self.assertEqual(seen, ["host del"])
        self.assertEqual(_DEL_LOG, ["stood down"])

    def test_scope_applies_and_rips_with_guaranteed_teardown(self) -> None:
        ari = Agent()

        with Scope(ari, Sentry) as scoped:
            self.assertIs(scoped, ari)
            self.assertIn(ari, Sentry)

        self.assertNotIn(ari, Sentry)
        self.assertEqual(_DEL_LOG, ["stood down"])

    def test_scope_rips_even_when_the_block_raises(self) -> None:
        ari = Agent()

        with self.assertRaises(ValueError):
            with Scope(ari, Sentry):
                raise ValueError("boom")

        self.assertNotIn(ari, Sentry)
        self.assertEqual(_DEL_LOG, ["stood down"])

    def test_at_exit_registration_is_weak_and_pruned(self) -> None:
        ari = Agent()
        Sentry(ari)
        At_Exit(ari)
        reference = weakref.ref(ari)

        del ari
        gc.collect()

        self.assertIsNone(reference())

        bea = Agent()
        At_Exit(bea)

        self.assertTrue(all(r() is not None for r in lifecycle._exit_registry))


# ==================================================================
# Ring 4: Access and queries
# ==================================================================


class AccessTests(unittest.TestCase):
    def test_views_by_name_and_by_class(self) -> None:
        ari = Agent()

        Elf(ari)
        Paladin(ari)

        self.assertEqual(ari.Elf.Attack(), "With elven grace Attack!")
        self.assertEqual(Elf[ari].Attack(), "With elven grace Attack!")

        with self.assertRaises(AttributeError):
            ari.Elf.Attack = None

    def test_view_by_class_distinguishes_tags_that_share_a_name(self) -> None:
        def make(colour: str) -> type:
            class Fire(Tag):
                hue = Report(colour)

            return Fire

        Fire_A = make("red")
        Fire_B = make("blue")
        ari = Agent()

        Fire_A(ari)
        Fire_B(ari)

        self.assertEqual(Fire_A[ari].hue, "red")
        self.assertEqual(Fire_B[ari].hue, "blue")
        self.assertEqual(ari.Fire.hue, "blue")

    def test_views_end_with_membership(self) -> None:
        ari = Agent()

        Squire(ari)
        del Squire[ari]

        with self.assertRaises(AttributeError):
            ari.Squire

        with self.assertRaises(TagResolutionError):
            Squire[ari]

        Person(ari)

        with self.assertRaises(TagResolutionError):
            Paladin[ari]

    def test_positional_slices_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            Squire[0:1]

    def test_tag_dotted_namespace_belongs_to_the_program(self) -> None:
        # Nothing TOP-level lives at Tag.name: a program may declare a
        # Report called Field, Form, or Rip without collision.
        class Freehold(Tag):
            Field = Report("a farm")
            Form = Report("a hut")
            Rip = Report("a tear")

        self.assertEqual(Freehold.Field, "a farm")
        self.assertEqual(Freehold.Form, "a hut")
        self.assertEqual(Freehold.Rip, "a tear")
        self.assertEqual(Form(Freehold), (Freehold,))


class QueryTests(unittest.TestCase):
    def test_flags_are_searchable_from_the_agent_side(self) -> None:
        @Flag
        class Undead(Tag):
            pass

        @Flag
        class Flying(Tag):
            pass

        ghoul = Agent()

        Undead(ghoul)
        Elf(ghoul)                                # an ordinary Tag, not a keyword

        self.assertIn("Undead", ghoul)
        self.assertIn(Undead, ghoul)
        self.assertNotIn("Flying", ghoul)
        self.assertNotIn(Flying, ghoul)
        self.assertNotIn("undead", ghoul)         # names match exactly
        self.assertNotIn("Elf", ghoul)            # Elf is not a Flag
        self.assertNotIn(Elf, ghoul)
        self.assertIn(ghoul, Elf)                 # membership is untouched

        self.assertTrue(Keyword(ghoul, "Undead", Undead))
        self.assertFalse(Keyword(ghoul, "Undead", "Flying"))
        self.assertFalse(Keyword(ghoul, "Elf"))
        self.assertFalse(Keyword(Agent(), "Undead"))   # works before any tagging

        del Undead[ghoul]

        self.assertNotIn("Undead", ghoul)

    def test_a_flag_on_a_container_host_is_refused(self) -> None:
        @Flag
        class Marked(Tag):
            pass

        bag = HostPreservationTests.Bag()

        with self.assertRaises(TagCompositionError):
            Marked(bag)

        self.assertNotIn(bag, Marked)
        self.assertIn("x", bag)

    def test_flag_marks_only_tags(self) -> None:
        with self.assertRaises(TagDeclarationError):
            Flag(Agent)

    def test_rules_written_as_keywords_port_between_programs(self) -> None:
        @Flag
        class Wizard(Tag):
            pass

        @Flag
        class Elven(Tag):
            pass

        rules = {
                "Wizard-Elven": lambda a: "arcane archer",
                "Wizard": lambda a: "caster",
                "Elven": lambda a: "archer",
                }

        def play(agent):
            for rule, act in rules.items():
                if Keyword(agent, *rule.split("-")):
                    return act(agent)

            return "commoner"

        ari = Agent()
        Wizard(ari)
        self.assertEqual(play(ari), "caster")

        Elven(ari)
        self.assertEqual(play(ari), "arcane archer")
        self.assertTrue(all(word in ari for word in "Wizard-Elven".split("-")))
        self.assertEqual(play(Agent()), "commoner")

    def test_apply_and_tags(self) -> None:
        ari = Apply(Agent(), Elf, Combatant)

        self.assertIn(ari, Elf)
        self.assertIn(ari, Person)
        self.assertNotIn(ari, Paladin)
        self.assertEqual(Tags(ari), (Elf, Combatant))

    def test_format_specs_are_the_display_door(self) -> None:
        ari = Agent()
        ari.level = 1

        Elf(ari)
        Scholar(ari)

        self.assertEqual(f"{Elf:form}", "Person → Elf")
        self.assertEqual(f"{Bridge:form}", "Root → Left → Right → Bridge")
        self.assertEqual(f"{Elf}", str(Elf))
        self.assertEqual(f"{ari:tags}", "Elf, Scholar")
        self.assertEqual(f"{ari:outline}", Outline(ari))
        self.assertEqual(f"{ari:contract}", Contract.Display(ari))
        self.assertEqual(f"{ari}", str(ari))

        with self.assertRaises(ValueError):
            f"{Elf:nope}"

        with self.assertRaises(ValueError):
            f"{ari:nope}"

    def test_host_format_keeps_its_seat(self) -> None:
        class Money:
            def __init__(self) -> None:
                self.cents = 1234

            def __format__(self, spec: str) -> str:
                return f"${self.cents / 100:.2f}"

        purse = Money()
        Field_Member(purse)

        self.assertEqual(f"{purse}", "$12.34")

    def test_outline_draws_each_form(self) -> None:
        ari = Agent()

        Elf(ari)
        Combatant(ari)

        self.assertEqual(
                Outline(ari),
                "Agent\n  Person\n    Elf\n  Combatant",
                )


if __name__ == "__main__":
    unittest.main()
