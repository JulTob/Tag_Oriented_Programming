"""TopKit conformance tests, ring by ring.

Ring 0  Kernel: identity, membership, Geometry, Fields.
Ring 1  Contributions: Overlay, Underlay, Records, publication.
Ring 2  Contracts: Pre, Imprint, Post, defective taggings.
Ring 3  Lifecycle: Rip, teardown, Scope, exit.
Ring 4  Access and queries.
"""

from __future__ import annotations

import collections.abc
import copy
import gc
import unittest
import warnings
import weakref

from TopKit import Action
from TopKit import Apply
from TopKit import At_Exit
from TopKit import Contract
from TopKit import Delete
from TopKit import Flag
from TopKit import Form
from TopKit import Keyword
from TopKit import Imprint
from TopKit import Operation
from TopKit import Outline
from TopKit import Pin
from TopKit import Post
from TopKit import Postcondition
from TopKit import Pre
from TopKit import Precondition
from TopKit import Public
from TopKit import Record
from TopKit import Report
from TopKit import Requirement
from TopKit import Rip
from TopKit import Scope
from TopKit import Secret
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagContractError
from TopKit import TagContractWarning
from TopKit import TagDeclarationError
from TopKit import TagImprintError
from TopKit import TagOverwriteWarning
from TopKit import TagPostconditionError
from TopKit import TagPreconditionError
from TopKit import TagRogueAccessError
from TopKit import TagTriageWarning
from TopKit import TagResolutionError
from TopKit import Tags
from TopKit import Underlay


def Run_Program(
        source: str,
        ) -> tuple[list[str], str]:
    """Run ``source`` in a fresh interpreter with this TopKit; return its
    output lines and its stderr. What a program does at exit is observable
    only there."""

    import pathlib
    import subprocess
    import sys

    root = pathlib.Path(__file__).resolve().parent.parent
    result = subprocess.run(
            [sys.executable, "-E", "-c", source],   # -E: the caller's PYTHON* settings stay out;
            cwd=root,                               # -c puts this checkout, the cwd, first on the path
            capture_output=True,
            text=True,
            timeout=60,                             # a hang at exit fails the test, not the run
            )

    return result.stdout.splitlines(), result.stderr


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
    @Report
    def colour(tag) -> str:
        return "green"

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
        self.assertFalse(hasattr(ari, "_TOPKIT_STATE"))
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
        @Public
        @Report
        def colour(tag) -> str:
            return "#ef5b35"

        @Report
        def heat(tag) -> int:
            return 3

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

    def test_contradictory_marks_are_rejected_and_redundant_ones_accepted(self) -> None:
        with self.assertRaises(TagDeclarationError):
            class Wrong(Tag):
                @Secret
                @Public
                @Action
                def act(agent) -> None:
                    pass

            Wrong(Agent())

        class Redundant(Tag):
            @Public                     # Records are external already
            @Record
            def hp(agent) -> int:
                return 1

            @Secret                     # Reports are internal already
            @Report
            def lore(tag) -> str:
                return "old"

        ari = Agent()
        Redundant(ari)

        self.assertEqual(ari.hp, 1)
        self.assertEqual(Redundant.lore, "old")
        self.assertFalse(hasattr(ari, "lore"))

    def test_reports_are_builders_that_run_once_per_tag_and_extend_bases(self) -> None:
        calls: list[str] = []

        class Class_(Tag):
            @Report
            def hit_die(tag) -> int:
                calls.append(tag.__name__)
                return 8

            @Report
            def traits(tag, inherited) -> list[str]:
                return (inherited or []) + ["mortal"]

        class Fighter(Class_):
            @Report
            def hit_die(tag) -> int:
                return 10

            @Report
            def traits(tag, inherited) -> list[str]:
                return inherited + ["armoured"]

        class Rogue(Class_):                          # a Shape that does not override
            pass

        self.assertEqual(Class_.hit_die, 8)
        self.assertEqual(Class_.hit_die, 8)
        self.assertEqual(calls, ["Class_"])           # built once
        self.assertEqual(Fighter.hit_die, 10)
        self.assertEqual(Fighter.traits, ["mortal", "armoured"])
        self.assertEqual(Class_.traits, ["mortal"])
        self.assertEqual(Rogue.hit_die, 8)
        self.assertEqual(Rogue.hit_die, 8)
        self.assertEqual(calls, ["Class_", "Rogue"])  # once per Tag: the Shape keeps its own
        self.assertEqual(Class_.hit_die, 8)
        self.assertEqual(calls, ["Class_", "Rogue"])

        with self.assertRaises(TagDeclarationError):
            Report(8)                                 # a builder, not a value

    def test_a_builder_that_reads_another_report_leaves_each_built_once(self) -> None:
        calls: list[str] = []

        class Fen(Tag):
            @Report
            def depth(tag) -> int:
                calls.append("depth")
                return 1

            @Report
            def reach(tag) -> int:
                calls.append("reach")
                return tag.depth + 1                  # another Report of Fen, read first here

        self.assertEqual(Fen.reach, 2)
        self.assertEqual(Fen.depth, 1)
        self.assertEqual(Fen.depth, 1)
        self.assertEqual(Fen.reach, 2)
        self.assertEqual(calls, ["reach", "depth"])   # each built once

    def test_a_tag_body_cannot_use_the_name_of_its_report_values(self) -> None:
        with self.assertRaises(TagDeclarationError) as refused:
            class Mine(Tag):
                _topkit_reports = "mine"

                @Report
                def depth(tag) -> int:
                    return 1

        self.assertIn("Mine defines _topkit_reports", str(refused.exception))

    def test_a_report_on_a_plain_class_is_built_once_and_a_subclass_builds_its_own(self) -> None:
        calls: list[str] = []

        class Ledger:
            @Report
            def depth(owner) -> int:
                calls.append("depth of " + owner.__name__)
                return len(owner.__name__)

            @Report
            def reach(owner) -> int:
                calls.append("reach of " + owner.__name__)
                return owner.depth + 1                # another Report, read first here

        class Journal(Ledger):
            pass

        self.assertEqual(Ledger.reach, 7)
        self.assertEqual(Ledger.depth, 6)
        self.assertEqual(Ledger.reach, 7)
        self.assertEqual(Journal.depth, 7)            # its own value, not its parent's
        self.assertEqual(Journal.depth, 7)
        self.assertEqual(
                calls,
                ["reach of Ledger", "depth of Ledger", "depth of Journal"],   # each built once per class
                )

    def test_a_builder_that_reads_its_own_report_keeps_the_first_value(self) -> None:
        calls: list[str] = []

        class Echo(Tag):
            @Report
            def sound(tag) -> str:
                calls.append("sound")

                if len(calls) == 1:
                    return "outer, after " + tag.sound        # its own Report, read while it builds

                return "inner"

        self.assertEqual(Echo.sound, "inner")                 # the value kept first wins, for the outer read too
        self.assertEqual(Echo.sound, "inner")
        self.assertEqual(calls, ["sound", "sound"])           # built twice, kept once

    def test_a_report_read_at_exit_gives_the_value_the_tag_kept(self) -> None:
        """The Tag keeps its value, so a finalizer at interpreter exit
        reads the value built before, not a new one."""

        lines, stderr = Run_Program(
                """
from TopKit import Tag, Report, Public

class Wolf(Tag):
    @Public
    @Report
    def motto(tag):
        return tag.__name__ + " howls"

class Howler:
    def __del__(self):
        print("exit", self.motto)

pack = Howler()
Wolf(pack)
print(pack.motto)
Wolf.__name__ = "Renamed"
""",
                )

        self.assertEqual(stderr, "")
        self.assertEqual(lines, ["Wolf howls", "exit Wolf howls"])

    def test_a_dropped_shape_is_freed_after_its_base_report_was_read(self) -> None:
        """The value lives on the Tag it was built for, so a Report whose
        value holds that Tag does not keep it alive."""

        class Kin(Tag):
            @Report
            def me(tag):
                return tag

        def Make() -> weakref.ref:
            class Temporary(Kin):
                pass

            self.assertIs(Temporary.me, Temporary)

            return weakref.ref(Temporary)

        reference = Make()
        gc.collect()

        self.assertIsNone(reference())
        self.assertIs(Kin.me, Kin)

    def test_a_pin_that_rolls_back_leaves_the_report_it_read_built_once(self) -> None:
        """A Tag has its Report values from its declaration, so a Pin's
        tagging that rolls back keeps the value its gate built."""

        calls: list[str] = []

        class Wizard(Tag):
            @Report
            def roster(tag) -> list[str]:
                calls.append(tag.__name__)
                return []

        @Pin
        class Audited(Tag):
            @Pre
            def Has_A_Roster(tag):
                return tag.roster == ["nobody"]               # reads the pinned Tag's Report, and refuses

        with self.assertRaises(TagPreconditionError):
            Audited(Wizard)

        self.assertEqual(Wizard.roster, [])
        self.assertIs(Wizard.roster, Wizard.roster)
        self.assertEqual(calls, ["Wizard"])                   # built once, by the gate
        self.assertNotIn(Wizard, Audited)

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


class RogueAccessTests(unittest.TestCase):
    """STEP-SPEC-10: a published member answers members only. A Rogue
    Agent keeps its own Actions and Records; the Agency's published
    Operations and Reports fail closed after Rip."""

    def setUp(self) -> None:
        class Agency(Tag):
            @Public
            @Report
            def colour(tag):
                return "navy"

            @Public
            @Operation
            def Dispatch(agency, agent, message):
                return f"{agency.__name__}:{message}"

            def Own(agent):
                return "mine"

        self.Agency = Agency

    def test_published_members_work_for_members(self) -> None:
        ari = Agent()
        self.Agency(ari)

        self.assertEqual(ari.colour, "navy")
        self.assertEqual(ari.Dispatch("go"), "Agency:go")

    def test_published_members_are_revoked_on_rip(self) -> None:
        Agency = self.Agency
        ari = Agent()
        Agency(ari)
        send = ari.Dispatch                                           # a stale handle

        del Agency[ari]

        self.assertEqual(ari.Own(), "mine")                           # the Agent's own stays
        self.assertTrue(hasattr(ari, "Dispatch"))                     # the Action is still there

        with self.assertRaises(TagRogueAccessError):
            ari.Dispatch("go")                                        # and refuses: a Rogue Agent

        with self.assertRaises(TagRogueAccessError):
            send("go")

        with self.assertRaises(TagRogueAccessError):
            ari.colour                                                # the published Report, the same way

        self.assertTrue(issubclass(TagRogueAccessError, TagResolutionError))
        self.assertFalse(issubclass(TagRogueAccessError, AttributeError))

        with self.assertRaises(TagRogueAccessError):
            hasattr(ari, "colour")                                    # a TOP failure is not swallowed below

        Agency(ari)                                                   # back in: a member reads again
        self.assertEqual(ari.Dispatch("go"), "Agency:go")
        self.assertEqual(ari.colour, "navy")

    def test_published_members_are_suspended_while_defective(self) -> None:
        """Soundness is holistic: any broken promise on the Agent suspends
        every published member, and the refusal names the promise."""

        Agency = self.Agency

        class Elf(Tag):
            @Post
            def Has_Homeland(agent):
                return agent.homeland is not None

        ari = Agent()
        ari.homeland = "Rivendell"
        Elf(ari)
        Agency(ari)
        self.assertEqual(ari.Dispatch("go"), "Agency:go")

        ari.homeland = None                                           # Elf's promise breaks, not Agency's

        with self.assertRaises(Postcondition.Has_Homeland):
            ari.Dispatch("go")

        with self.assertRaises(Postcondition.Has_Homeland):
            ari.colour

        self.assertEqual(ari.Own(), "mine")                           # her own Action still works
        self.assertIn(ari, Agency)                                    # still a member, just defective

        ari.homeland = "Rivendell"                                    # repaired
        self.assertEqual(ari.Dispatch("go"), "Agency:go")
        self.assertEqual(ari.colour, "navy")

    def test_the_autofix_pattern(self) -> None:
        Agency = self.Agency

        class Elf(Tag):
            @Post
            def Has_Homeland(agent):
                return agent.homeland is not None

        ari = Agent()
        ari.homeland = None
        Agency(ari)

        with self.assertRaises(Postcondition.Has_Homeland):
            Elf(ari)                                                  # applied, defective

        try:
            ari.Dispatch("go")
        except Postcondition.Has_Homeland:
            ari.homeland = "Rivendell"                                # repair what the failure names
            sent = ari.Dispatch("go")                                 # and retry

        self.assertEqual(sent, "Agency:go")


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


class ConditionTests(unittest.TestCase):
    """@Pre and @Post stacked on one function: necessary to enter and
    necessary to stay."""

    def test_a_stacked_condition_gates_and_promises(self) -> None:
        class Elf(Tag):
            @Pre
            @Post
            def Alive(agent):
                return agent.alive

        dead = Agent()
        dead.alive = False

        with self.assertRaises(Precondition.Alive):
            Elf(dead)                                                 # necessary to enter

        ari = Agent()
        ari.alive = True
        Elf(ari)
        self.assertEqual(Contract.Status(ari), {"Alive": True})
        self.assertTrue(ari)

        ari.alive = False                                             # necessary to stay
        self.assertFalse(ari)
        self.assertIn(ari, ~Elf)

        with self.assertRaises(Postcondition.Alive):
            Contract.Postconditions(ari)

        self.assertIs(Precondition.Alive, TagPreconditionError.Alive)
        self.assertIs(Postcondition.Alive, TagPostconditionError.Alive)

    def test_requirement_is_the_stacked_pair_in_one_word(self) -> None:
        class Vampire(Tag):
            @Requirement
            def Undead(agent):
                return agent.undead

        mortal = Agent()
        mortal.undead = False

        with self.assertRaises(Precondition.Undead):
            Vampire(mortal)                                           # necessary to enter

        nosferatu = Agent()
        nosferatu.undead = True
        Vampire(nosferatu)

        nosferatu.undead = False                                      # necessary to stay
        with self.assertRaises(Postcondition.Undead):
            Contract.Postconditions(nosferatu)

    def test_a_requirement_names_no_failure_of_its_own(self) -> None:
        with self.assertRaises(AttributeError) as caught:
            Requirement.Undead

        self.assertIn("Precondition.Undead", str(caught.exception))
        self.assertIn("Postcondition.Undead", str(caught.exception))


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
                assert agent.level > 0

        with self.assertRaises(Precondition.Is_A_Caster):
            Caster(Agent())

    def test_postcondition_and_imprint_failures_are_named(self) -> None:
        class Armed(Tag):
            @Imprint
            def Arm(agent):
                raise ValueError("no arms")

        class Shielded(Tag):
            @Post
            def Has_Shield(agent):
                return False

        with self.assertRaises(Imprint.Arm) as caught:
            Armed(Agent())

        self.assertEqual(caught.exception.name, "Arm")
        self.assertIsInstance(caught.exception, TagImprintError)

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


class PinTests(unittest.TestCase):
    """STEP-SPEC-9: a Tag marked @Pin applies to Tags. The pinned Tag is
    the Pin's Agent; the receiver rule lands Records as Reports and
    Actions as Operations of that Tag."""

    def setUp(self) -> None:
        class Wizard(Tag):
            @Report
            def colour(tag):
                return "blue"

            @Operation
            def Greet(tag, who):
                return f"{tag.__name__}:{who}"

            def Attack(agent):
                return "casts"

        class War_Caster(Wizard):
            pass

        @Pin
        class Rare(Tag):
            @Record
            def rarity(tag):
                return "rare"

            @Action
            def Describe(tag):
                return f"{tag.__name__} is {tag.rarity}"

        self.Wizard = Wizard
        self.War_Caster = War_Caster
        self.Rare = Rare

    def test_a_pin_makes_a_tag_its_agent(self) -> None:
        Wizard, Rare = self.Wizard, self.Rare
        identity = (id(Wizard), hash(Wizard), Wizard.__name__, Form(Wizard))

        self.assertIs(Rare(Wizard), Wizard)

        self.assertIn(Wizard, Rare)
        self.assertEqual(list(Rare), [Wizard])
        self.assertEqual(list(Rare[:]), [Wizard])
        self.assertEqual(len(Rare), 1)
        self.assertTrue(Rare)
        self.assertTrue(isinstance(Wizard, Rare))
        self.assertEqual(identity, (id(Wizard), hash(Wizard), Wizard.__name__, Form(Wizard)))
        self.assertIs(type(self.War_Caster), type(Tag))

    def test_records_land_as_reports_and_actions_as_operations(self) -> None:
        Wizard, War_Caster, Rare = self.Wizard, self.War_Caster, self.Rare
        ari = Agent()
        Wizard(ari)

        Rare(Wizard)

        self.assertEqual(Wizard.rarity, "rare")
        self.assertEqual(Wizard.Describe(), "Wizard is rare")
        self.assertEqual(War_Caster.rarity, "rare")                 # a Report: inherited
        self.assertEqual(War_Caster.Describe(), "War_Caster is rare")   # an Operation: the receiver is the Tag read
        self.assertNotIn(War_Caster, Rare)                            # membership does not inherit
        self.assertFalse(hasattr(ari, "rarity"))
        self.assertFalse(hasattr(ari, "Describe"))
        self.assertEqual((Wizard.colour, Wizard.Greet("x"), ari.Attack()), ("blue", "Wizard:x", "casts"))

        bo = Agent()
        Wizard(bo)                                                    # tagging after the pinning

        self.assertFalse(hasattr(bo, "rarity"))
        self.assertFalse(hasattr(bo, "Describe"))

    def test_view_format_and_queries(self) -> None:
        Wizard, Rare = self.Wizard, self.Rare
        Rare(Wizard)

        self.assertEqual(Rare[Wizard].rarity, "rare")
        self.assertEqual(Rare[Wizard].Describe(), "Wizard is rare")
        self.assertEqual(Wizard.Rare.rarity, "rare")
        self.assertEqual(f"{Wizard:pins}", "Rare")
        self.assertEqual(f"{Wizard:form}", "Wizard")
        self.assertEqual(Tags(Wizard), (Rare,))
        self.assertEqual(Outline(Wizard), "Wizard\n  Rare")
        self.assertTrue(f"{Wizard:contract}".startswith("Wizard[Rare]"))
        self.assertFalse(Wizard)                                      # still "any sound member"
        ari = Agent()
        Wizard(ari)
        self.assertTrue(Wizard)

    def test_refusals(self) -> None:
        Wizard, Rare = self.Wizard, self.Rare
        ari = Agent()

        with self.assertRaises(TagCompositionError):
            Rare(ari)                                                 # a Pin on an object

        with self.assertRaises(TypeError):
            Wizard(Rare)                                              # an ordinary Tag on a class

        with self.assertRaises(TagCompositionError):
            Rare(Rare)                                                # itself

        @Pin
        class Loud(Tag):
            @Action
            def Attack(tag):                                          # the Tag's own Agent-scope member
                return "shout"

        with self.assertRaises(TagCompositionError):
            Loud(Wizard)

        bo = Agent()
        Wizard(bo)
        self.assertEqual(bo.Attack(), "casts")                        # the declaration survived
        self.assertNotIn(Wizard, Loud)


        @Pin
        class Named(Tag):
            def mro(tag):
                return 1

        with self.assertRaises(TagCompositionError):
            Named(Wizard)                                             # what every Tag answers

        with self.assertRaises(TagDeclarationError):
            @Pin
            class Loudspeaker(Tag):
                @Public
                @Report
                def x(tag):                                           # a Pin's own Report: nowhere to publish
                    return 1

        with self.assertRaises(TagDeclarationError):
            class Mixed(Rare, Wizard):
                pass

        with self.assertRaises(TagCompositionError):
            Rare(Tag)                                                 # the root is nobody's Target

    def test_a_failed_gate_leaves_the_tag_untouched(self) -> None:
        Wizard = self.Wizard
        before = dict(vars(Wizard))

        @Pin
        class Gated(Tag):
            @Pre
            def Has_Members(tag):
                return bool(tag[:])

            @Record
            def stamp(tag):
                return 1

        with self.assertRaises(Precondition.Has_Members):
            Gated(Wizard)

        self.assertEqual(dict(vars(Wizard)), before)
        self.assertIs(type(Wizard), type(Tag))
        self.assertNotIn(Wizard, Gated)

        ari = Agent()
        Wizard(ari)
        Gated(Wizard)
        self.assertIn(Wizard, Gated)

    def test_a_failed_promise_leaves_the_tag_pinned_and_defective(self) -> None:
        Wizard = self.Wizard

        @Pin
        class Promised(Tag):
            @Post
            def Has_Members(tag):
                return bool(tag[:])

        with self.assertRaises(Postcondition.Has_Members):
            Promised(Wizard)

        self.assertIn(Wizard, Promised)
        self.assertIn(Wizard, ~Promised)
        self.assertEqual(list(Promised), [])

        ari = Agent()
        Wizard(ari)                                                   # repaired
        self.assertEqual(list(Promised), [Wizard])

    def test_rip_is_sticky_and_repinning_is_fresh(self) -> None:
        Wizard, Rare = self.Wizard, self.Rare

        @Pin
        class Checked(Rare):
            @Post
            def Fine(tag):
                return True

        Checked(Wizard)
        del Checked[Wizard]

        self.assertNotIn(Wizard, Checked)
        self.assertIn(Wizard, Rare)                                   # the Base stays
        self.assertTrue(isinstance(Wizard, Checked))
        self.assertEqual(Wizard.rarity, "rare")                       # sticky

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            Checked(Wizard)                                           # fresh, and silent

        self.assertIn(Wizard, Checked)

    def test_a_shape_of_a_pin_is_a_pin_and_a_pin_may_be_pinned(self) -> None:
        Wizard, War_Caster, Rare = self.Wizard, self.War_Caster, self.Rare

        class Homebrew(Rare):
            @Record
            def source(tag):
                return "mine"

        Homebrew(War_Caster)

        self.assertIn(War_Caster, Rare)
        self.assertIn(War_Caster, Homebrew)
        self.assertEqual((War_Caster.source, War_Caster.rarity), ("mine", "rare"))
        self.assertNotIn(Wizard, Rare)

        @Pin
        class Meta(Tag):
            @Record
            def level(tag):
                return 2

        Meta(Rare)

        self.assertIn(Rare, Meta)
        self.assertEqual(Rare.level, 2)
        self.assertEqual(Homebrew.level, 2)

    def test_a_pin_patches_the_tags_own_operations_and_reports(self) -> None:
        """A Tag's Tag-scope declarations are host members to a Pin: the
        Operation is the Underlay, the Report's value the stored seat."""

        Wizard, War_Caster = self.Wizard, self.War_Caster
        ari = Agent()
        Wizard(ari)

        class Caller(Tag):
            def Hail(agent):
                return Wizard.Greet("all")                            # through the Tag, at call time

        Caller(ari)
        self.assertEqual(ari.Hail(), "Wizard:all")

        @Pin
        class Patch(Tag):
            @Action
            @Underlay
            def Greet(tag, underlay, who):
                return underlay(who).upper()

            @Record
            def colour(tag, stored):
                return stored + "-patched"

        with warnings.catch_warnings():
            warnings.simplefilter("error")                            # a host member: silent
            Patch(Wizard)

        self.assertEqual(Wizard.Greet("x"), "WIZARD:X")
        self.assertEqual(War_Caster.Greet("x"), "WAR_CASTER:X")
        self.assertEqual(Wizard.colour, "blue-patched")
        self.assertEqual(ari.Hail(), "WIZARD:ALL")                    # every Agent actualized, no per-Agent work

        del Patch[Wizard]
        self.assertEqual(Wizard.Greet("x"), "WIZARD:X")               # sticky, like a Rogue Agent

    def test_a_failed_patch_rolls_the_declaration_back(self) -> None:
        Wizard = self.Wizard

        @Pin
        class Broken(Tag):
            @Action
            def Greet(tag, who):
                return "patched"

            @Record
            def boom(tag):
                raise ValueError("no")

        with self.assertRaises(TagCompositionError):
            Broken(Wizard)

        self.assertEqual(Wizard.Greet("x"), "Wizard:x")
        self.assertIsInstance(vars(Wizard)["Greet"], classmethod)

    def test_a_flag_pin_is_a_keyword_on_the_tag(self) -> None:
        Wizard, Rare = self.Wizard, self.Rare
        ari = Agent()
        Wizard(ari)

        @Flag
        @Pin
        class Deprecated(Tag):
            pass

        Rare(Wizard)
        Deprecated(Wizard)

        self.assertTrue("Deprecated" in Wizard)                       # a string asks for a keyword
        self.assertFalse("Rare" in Wizard)                            # only Flags are words
        self.assertTrue(ari in Wizard)                                # an object asks membership
        self.assertFalse(Deprecated in Wizard)                        # a class asks membership too
        self.assertTrue(Keyword(Wizard, "Deprecated"))
        self.assertTrue(Keyword(Wizard, Deprecated))
        self.assertFalse(Keyword(Wizard, "Rare"))
        self.assertIn(Wizard, Deprecated)

    def test_a_secret_pin_member_is_pin_private_state_on_the_tag(self) -> None:
        Wizard = self.Wizard

        @Pin
        class Licensed(Tag):
            @Secret
            @Record
            def key(tag):
                return "k-1"

            @Action
            def Check(tag, key):
                return key == tag.key                                 # inside the door

            @Post
            def Keyed(tag):
                return tag.key is not None                            # protocols see it

        Licensed(Wizard)

        self.assertTrue(Wizard.Check("k-1"))
        self.assertFalse(Wizard.Check("nope"))

        with self.assertRaises(AttributeError):
            Wizard.key                                                # hidden from main

        self.assertNotIn("key", vars(Wizard))                         # not in the class dictionary at all
        self.assertEqual(Contract.Status(Wizard), {"Keyed": True})

    def test_a_public_pin_member_reaches_the_whole_field(self) -> None:
        Wizard, War_Caster = self.Wizard, self.War_Caster
        ari = Agent()
        Wizard(ari)                                                   # present before the pinning
        cal = Agent()
        War_Caster(cal)

        @Pin
        class Engine(Tag):
            @Public
            @Record
            def firmware(tag):
                return "v2"

            @Public
            @Action
            def Control(tag, agent, level):
                return f"{tag.__name__} sets {agent.name} to {level}"

        ari.name, cal.name = "Ari", "Cal"
        Engine(Wizard)

        self.assertEqual(Wizard.firmware, "v2")
        self.assertEqual(Wizard.Control(ari, 3), "Wizard sets Ari to 3")
        self.assertEqual(ari.firmware, "v2")                          # a present Agent, actualized
        self.assertEqual(ari.Control(3), "Wizard sets Ari to 3")
        self.assertEqual(cal.Control(1), "Wizard sets Cal to 1")      # through the Base's Layer

        bo = Agent()
        bo.name = "Bo"
        Wizard(bo)                                                    # a future Agent
        self.assertEqual(bo.firmware, "v2")
        self.assertEqual(bo.Control(2), "Wizard sets Bo to 2")

        with self.assertRaises(AttributeError):
            ari.firmware = "v3"                                       # read-only on the Agent

        del Wizard[ari]
        with self.assertRaises(TagResolutionError):
            ari.Control(3)                                            # published: members only

    def test_a_public_pin_member_that_cannot_reach_every_agent_reaches_none(self) -> None:
        Wizard = self.Wizard
        ari = Agent()
        Wizard(ari)

        class Holder(Tag):
            @Record
            def firmware(agent):
                return "own"

        Holder(ari)                                                   # an independent Record of that name

        @Pin
        class Engine(Tag):
            @Public
            @Action
            def firmware(tag, agent):
                return 1

        with self.assertRaises(TagCompositionError):
            Engine(Wizard)

        self.assertNotIn(Wizard, Engine)
        self.assertEqual(ari.firmware, "own")
        self.assertFalse(hasattr(Wizard, "firmware"))

    def test_a_pins_teardown_receives_the_originals_for_unpatching(self) -> None:
        Wizard = self.Wizard
        ari = Agent()
        Wizard(ari)

        @Pin
        class Patch(Tag):
            @Action
            @Underlay
            def Greet(tag, underlay, who):
                return underlay(who).upper()

            @Record
            def colour(tag, stored):
                return stored + "-patched"

            @Rip
            def Unpatch(tag, original):                               # the second seat: the originals
                tag.Greet = original.Greet
                tag.colour = original.colour

        Patch(Wizard)
        self.assertEqual((Wizard.Greet("x"), Wizard.colour), ("WIZARD:X", "blue-patched"))

        del Patch[Wizard]                                             # one deliberate line each: un-patched

        self.assertEqual((Wizard.Greet("x"), Wizard.colour), ("Wizard:x", "blue"))
        self.assertIsInstance(vars(Wizard)["Greet"], classmethod)
        self.assertTrue(isinstance(Wizard, Patch))

    def test_a_pins_teardown_without_the_seat_leaves_the_patch(self) -> None:
        Wizard = self.Wizard

        @Pin
        class Patch(Tag):
            @Action
            def Greet(tag, who):
                return "patched"

            @Rip
            def Note(tag):
                tag.noted = True

        Patch(Wizard)
        del Patch[Wizard]

        self.assertEqual(Wizard.Greet("x"), "patched")                # sticky
        self.assertTrue(Wizard.noted)

    def test_a_ripped_tag_reapplied_to_an_object_is_silent(self) -> None:
        class Promising(Tag):
            @Post
            def Fine(agent):
                return True

        ari = Agent()
        Promising(ari)
        del Promising[ari]

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            Promising(ari)


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

    def test_a_failed_teardown_refuses_the_rip_and_rolls_it_back(self) -> None:
        log: list[str] = []
        stuck = [True]

        class Fragile(Tag):
            @Record
            def charge(agent) -> int:
                return 3

            def Spark(agent) -> str:
                return "spark"

            @Rip
            def boom(agent) -> None:
                log.append(("in", agent in Fragile))                 # it runs after membership ended
                agent.charge = 0

                if stuck:
                    raise RuntimeError("x")

        ari, bea = Agent(), Agent()
        Fragile(ari)
        Fragile(bea)
        view = Fragile[ari]

        with self.assertRaises(TagCompositionError) as raised:
            del Fragile[ari]

        self.assertIsInstance(raised.exception.__cause__, RuntimeError)
        self.assertIn("the Rip is refused and rolled back", str(raised.exception))
        self.assertEqual(log, [("in", False)])
        self.assertIn(ari, Fragile)                                    # the Agent stays a member
        self.assertEqual(list(Fragile[:]), [ari, bea])                 # in its place in the Field
        self.assertEqual(ari.charge, 3)                                # as before the Rip
        self.assertEqual(ari.Spark(), "spark")
        self.assertEqual(Fragile[ari].charge, view.charge)
        self.assertEqual(Tags(ari), (Fragile,))

        stuck.clear()                                                  # repaired: the Agent ends quietly

    def test_a_later_failing_teardown_undoes_the_earlier_ones(self) -> None:
        stuck = [True]

        class Knight(Tag):
            @Post
            def Has_Sword(agent) -> bool:
                return agent.sword is not None

            @Record
            def rank(agent) -> str:
                return "knight"

            @Rip
            def Undub(agent) -> None:
                Contract.Delete(agent, "Has_Sword")                  # ends the promise ...
                agent.rank = "squire"
                del agent.sword

            @Rip
            def Return_Horse(agent) -> None:
                if stuck:
                    raise LookupError("the horse is gone")           # ... and then the Rip fails

        lance = Agent()
        lance.sword = "Excalibur"
        Knight(lance)
        before = dict(Contract.Status(lance))

        with self.assertRaises(TagCompositionError) as raised:
            del Knight[lance]

        self.assertIn("Return_Horse", str(raised.exception))
        self.assertIn(lance, Knight)
        self.assertEqual(Contract.Status(lance), before)               # the deleted promise is back
        self.assertEqual((lance.rank, lance.sword), ("knight", "Excalibur"))

        lance.sword = None
        self.assertFalse(lance)                                        # and it binds again

        lance.sword = "Excalibur"
        stuck.clear()                                                  # repaired: the Agent ends quietly

    def test_a_rip_retried_after_repair_succeeds(self) -> None:
        log: list[str] = []
        stuck = [True]

        class Sentry(Tag):
            @Rip
            def Stand_Down(agent) -> None:
                log.append("stand down")

            @Rip
            def Hand_Over(agent) -> None:
                if stuck[0]:
                    raise ValueError("nobody to hand over to")

                log.append("handed over")

        guard = Agent()
        Sentry(guard)

        with self.assertRaises(TagCompositionError):
            del Sentry[guard]

        stuck[0] = False                                               # repaired
        del Sentry[guard]                                              # every teardown is due again

        self.assertNotIn(guard, Sentry)
        self.assertEqual(log, ["stand down", "stand down", "handed over"])
        self.assertTrue(isinstance(guard, Sentry))

    def test_a_shapes_failed_rip_leaves_its_base_alone(self) -> None:
        stuck = [True]

        class Beast(Tag):
            @Rip
            def Calm(agent) -> None:
                agent.events.append("calm")

        class Wolf(Beast):
            @Rip
            def Howl(agent) -> None:
                if stuck:
                    raise RuntimeError("will not be quiet")

        rex = Agent()
        Wolf(rex)

        with self.assertRaises(TagCompositionError):
            del Wolf[rex]

        self.assertTrue(rex in Wolf and rex in Beast)                 # nothing cascades, as before
        self.assertNotIn("calm", rex.events)

        stuck.clear()                                                  # repaired: the Agent ends quietly

    def test_a_rip_made_inside_a_failed_teardown_is_rolled_back_too(self) -> None:
        stuck = [True]

        class Badge(Tag):
            pass

        class Sworn(Tag):
            @Rip
            def Unswear(agent) -> None:
                del Badge[agent]                                       # a Rip of its own, which succeeds

                if stuck:
                    raise RuntimeError("the oath holds")

        ari, bea = Agent(), Agent()
        Badge(ari)
        Badge(bea)
        Sworn(ari)

        with self.assertRaises(TagCompositionError):
            del Sworn[ari]

        self.assertEqual(Tags(ari), (Badge, Sworn))
        self.assertEqual(list(Badge[:]), [ari, bea])                   # back in its place

        stuck.clear()                                                  # repaired: the Agent ends quietly

    def test_an_interrupted_rip_is_rolled_back_and_the_interruption_leaves(self) -> None:
        stuck = [True]

        class Sentry(Tag):
            @Rip
            def Stand_Down(agent) -> None:
                agent.on_duty = False

                if stuck:
                    raise KeyboardInterrupt

        guard = Agent()
        guard.on_duty = True
        Sentry(guard)

        with self.assertRaises(KeyboardInterrupt):
            del Sentry[guard]

        self.assertIn(guard, Sentry)                                   # the Rip never finished
        self.assertTrue(guard.on_duty)

        stuck.clear()                                                  # repaired: the Agent ends quietly

    def test_what_a_failed_teardown_did_outside_the_agent_stays_done(self) -> None:
        outside: list[str] = []
        stuck = [True]

        class Clerk(Tag):
            @Rip
            def Shred(agent) -> None:
                outside.append("shredded")                            # the world, not the Agent

                if stuck:
                    raise RuntimeError("the shredder jams")

        ari = Agent()
        Clerk(ari)

        with self.assertRaises(TagCompositionError):
            del Clerk[ari]

        self.assertEqual(outside, ["shredded"])
        self.assertIn(ari, Clerk)

        stuck.clear()                                                  # repaired: the Agent ends quietly

    def test_a_refused_rip_keeps_no_cycle(self) -> None:
        """Once repaired, the Agent dies with its last reference, gc or
        not: the failed teardown's error held no frame that held it."""

        stuck = [True]

        class Clerk(Tag):
            @Rip
            def Shred(agent) -> None:
                if stuck:
                    raise RuntimeError("the shredder jams")

        gc.collect()
        gc.disable()

        try:
            ari = Agent()
            reference = weakref.ref(ari)
            Clerk(ari)

            try:
                del Clerk[ari]                                         # not assertRaises: it clears the frames
            except TagCompositionError as error:
                caught = type(error)

            self.assertIs(caught, TagCompositionError)
            stuck.clear()                                              # repaired: its teardown runs at deletion
            del ari

            self.assertIsNone(reference())                             # freed by its count: no cycle held it
        finally:
            gc.enable()

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


class StickyConditionTests(unittest.TestCase):
    """STEP-SPEC-12: conditions are sticky, like contributions. Rip never
    touches them. The author ends them: a guard in the condition, or an
    explicit deletion from the Tag's own @Rip protocol."""

    def test_a_ripped_tags_promise_still_binds(self) -> None:
        class Wizard(Tag):
            @Post
            def Has_Book(agent):
                return agent.book is not None

        ari = Agent()
        ari.book = []
        Wizard(ari)
        del Wizard[ari]                                               # a Rogue Agent
        ari.book = None

        self.assertEqual(Contract.Status(ari), {"Has_Book": False})   # the promise stays, and fails loud
        self.assertFalse(Contract.Holds(ari))

    def test_a_ripped_gate_stays_on_the_record(self) -> None:
        class Gated(Tag):
            @Pre
            def Ready(agent):
                return agent.ready

        ari = Agent()
        ari.ready = True
        Gated(ari)
        del Gated[ari]
        ari.ready = False

        self.assertEqual(Contract.Status(ari), {"Ready": False})      # sticky: still on the Agent's record

        with self.assertRaises(Precondition.Ready):
            Contract.Preconditions(ari)

    def test_the_author_ends_a_promise_from_the_rip_protocol(self) -> None:
        class Sworn(Tag):
            @Post
            def Has_Oath(agent):
                return agent.oath is not None

            @Rip
            def Release(agent):
                Contract.Delete(agent, "Has_Oath")                    # one deliberate name

        ari = Agent()
        ari.oath = "sworn"
        Sworn(ari)
        del Sworn[ari]
        ari.oath = None

        self.assertEqual(Contract.Status(ari), {})
        self.assertTrue(Contract.Holds(ari))

    def test_the_author_guards_a_promise_with_membership(self) -> None:
        class Sworn(Tag):
            @Post
            def Has_Oath(agent):
                if agent not in Sworn:                                # the guard, in the author's words
                    return True
                return agent.oath is not None

        ari = Agent()
        ari.oath = "sworn"
        Sworn(ari)
        del Sworn[ari]
        ari.oath = None

        self.assertEqual(Contract.Status(ari), {"Has_Oath": True})    # still listed, holds by the guard
        self.assertTrue(Contract.Holds(ari))

        with self.assertRaises(Postcondition.Has_Oath):
            Sworn(ari)                                                # back in: the promise bites again

        self.assertFalse(Contract.Holds(ari))

    def test_deleting_a_condition_that_is_not_there_is_refused(self) -> None:
        ari = Agent()

        with self.assertRaises(TagResolutionError):
            Contract.Delete(ari, "Has_Oath")

        class Plain(Tag):
            pass

        Plain(ari)

        with self.assertRaises(TagResolutionError):
            Contract.Delete(ari, "Has_Oath")

    def test_deletion_ends_both_halves_of_a_requirement(self) -> None:
        class Elf(Tag):
            @Requirement
            def Alive(agent):
                return agent.alive

            @Rip
            def Release(agent):
                Contract.Delete(agent, "Alive")

        ari = Agent()
        ari.alive = True
        Elf(ari)
        self.assertEqual(Contract.Status(ari), {"Alive": True})

        del Elf[ari]
        self.assertEqual(Contract.Status(ari), {})

    def test_an_underlay_over_a_ripped_tag_keeps_calling_it_unless_guarded(self) -> None:
        class Alive(Tag):
            @Post
            def Fine(agent):
                return agent.alive

        class Elf(Tag):
            @Post
            @Underlay
            def Fine(agent, base):
                underneath = base() if agent in Alive else True       # whose promise base() is
                return underneath and agent.pointy_ears

        ari = Agent()
        ari.alive, ari.pointy_ears = True, True
        Alive(ari)
        Elf(ari)
        del Alive[ari]
        ari.alive = False

        self.assertTrue(Contract.Holds(ari))                          # the guard skipped the dead beat

    def test_a_pins_promise_is_sticky_and_the_pin_may_end_it(self) -> None:
        class Wizard(Tag):
            pass

        @Pin
        class Promised(Tag):
            @Post
            def Has_Members(tag):
                return bool(tag[:])

            @Rip
            def Release(tag):
                Contract.Delete(tag, "Has_Members")

        with self.assertRaises(Postcondition.Has_Members):
            Promised(Wizard)

        self.assertIn(Wizard, ~Promised)
        del Promised[Wizard]
        self.assertEqual(Contract.Status(Wizard), {})

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

        self.assertIsNone(reference())                 # weak: it never kept the Agent

        import tracemalloc

        gc.collect()
        tracemalloc.start()
        before, _peak = tracemalloc.get_traced_memory()

        for _ in range(2000):
            At_Exit(Agent())                           # each registration dies with its Agent

        gc.collect()
        after, _peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.assertLess((after - before) / 2000, 16)   # nothing kept per dead registration


# ==================================================================
# Ring 4: Access and queries
# ==================================================================


class ScopeTests(unittest.TestCase):
    """A Scope Rips the Tags it names that it applied, and only those. A
    Rip it cannot make is reported, as a Rip reports it, once every Rip
    is done."""

    def test_a_tag_the_agent_already_had_survives_the_scope(self) -> None:
        class Wizard(Tag):
            pass

        ari = Agent()
        Wizard(ari)

        with Scope(ari, Wizard):
            self.assertIn(ari, Wizard)

        self.assertIn(ari, Wizard)                                    # it was Ari's, not the Scope's

    def test_a_tag_whose_promise_broke_at_the_door_is_ripped_on_exit(self) -> None:
        class Sworn(Tag):
            @Post
            def Has_Oath(agent):
                return agent.oath is not None

        bo = Agent()
        bo.oath = None

        with self.assertRaises(Postcondition.Has_Oath):
            with Scope(bo, Sworn):
                raise AssertionError("the body must not run")

        self.assertNotIn(bo, Sworn)                                   # applied, defective, and Ripped on the way out
        self.assertTrue(isinstance(bo, Sworn))                        # the history stays

    def test_a_refused_gate_applies_nothing_and_rips_nothing(self) -> None:
        class Gated(Tag):
            @Pre
            def Ready(agent):
                return agent.ready

        class Plain(Tag):
            pass

        cal = Agent()
        cal.ready = False

        with self.assertRaises(Precondition.Ready):
            with Scope(cal, Plain, Gated):
                pass

        self.assertNotIn(cal, Plain)                                  # Plain was the Scope's: gone
        self.assertNotIn(cal, Gated)

    def test_a_tag_whose_imprint_failed_at_the_door_is_ripped_on_exit(self) -> None:
        class Cursed(Tag):
            @Imprint
            def Mark(agent):
                raise ValueError("the mark will not take")

        ari = Agent()

        with self.assertRaises(Imprint.Mark):
            with Scope(ari, Cursed):
                raise AssertionError("the body must not run")

        self.assertNotIn(ari, Cursed)                                 # applied, failed at the door, and Ripped
        self.assertTrue(isinstance(ari, Cursed))                      # the history stays

    def test_a_base_the_scope_pulled_in_stays(self) -> None:
        class Wolf(Tag):
            pass

        class Dire(Wolf):
            pass

        bo = Agent()

        with Scope(bo, Dire):
            self.assertIn(bo, Wolf)

        self.assertNotIn(bo, Dire)                                    # the Tag it named and applied
        self.assertIn(bo, Wolf)                                       # the Base it pulled in stays

        cy, di = Agent(), Agent()

        with Scope(cy, Dire, Wolf):                                   # Wolf is carried by its turn
            pass

        with Scope(di, Wolf, Dire):                                   # Wolf is the Scope's own
            pass

        self.assertIn(cy, Wolf)
        self.assertNotIn(cy, Dire)
        self.assertNotIn(di, Wolf)
        self.assertNotIn(di, Dire)

    def test_a_base_whose_imprint_fails_under_a_shape_stays_after_the_scope(self) -> None:
        class Wolf(Tag):
            @Imprint
            def Enter(agent):
                raise ValueError("the wolf will not come")

        class Dire(Wolf):
            pass

        bo = Agent()

        with self.assertRaises(Imprint.Enter):
            with Scope(bo, Dire):
                raise AssertionError("the body must not run")

        self.assertEqual(Tags(bo), (Wolf,))                           # the Base the Shape pulled in stays (STEP-SPEC-6: open)
        self.assertNotIn(bo, Dire)                                    # the Shape never landed

    def test_a_tag_a_shape_still_requires_stays_and_the_scope_raises(self) -> None:
        class Wolf(Tag):
            pass

        class Dire(Wolf):
            pass

        bo = Agent()

        with self.assertRaises(TagCompositionError) as raised:
            with Scope(bo, Wolf):
                Dire(bo)                                              # the block brings a Shape that requires Wolf

        self.assertIn("Wolf is required by active Shape(s): Dire", str(raised.exception))
        self.assertIn(bo, Dire)
        self.assertIn(bo, Wolf)                                       # the Rip was refused, as `del Wolf[bo]` is

    def test_the_scope_rips_the_rest_before_it_reports_a_refusal(self) -> None:
        class Wolf(Tag):
            pass

        class Dire(Wolf):
            pass

        class Hunting(Tag):
            pass

        class Howling(Tag):
            pass

        cy = Agent()

        with self.assertRaises(TagCompositionError) as raised:
            with Scope(cy, Wolf, Hunting, Howling):
                Dire(cy)

        self.assertEqual(Tags(cy), (Dire,))                           # Howling and Hunting were Ripped all the same
        self.assertIn(cy, Wolf)
        self.assertFalse(getattr(raised.exception, "__notes__", None))

    def test_a_refusal_is_a_note_on_the_exception_that_leaves_the_block(self) -> None:
        class Wolf(Tag):
            pass

        class Dire(Wolf):
            pass

        di = Agent()

        with self.assertRaises(LookupError) as raised:
            with Scope(di, Wolf):
                Dire(di)
                raise LookupError("the block fails")

        self.assertEqual(
                raised.exception.__notes__,
                ["On leaving the Scope: TagCompositionError: Wolf is required by active Shape(s): Dire"],
                )
        self.assertIn(di, Wolf)

    def test_a_teardown_that_fails_in_a_scope_refuses_the_rip_and_the_tag_stays(self) -> None:
        stuck = [True]

        class Sentry(Tag):
            @Imprint
            def Post(agent):
                agent.on_duty = True

            @Rip
            def Stand_Down(agent):
                agent.on_duty = False
                if stuck:
                    raise ValueError("the post will not be left")

        class Watch(Tag):
            pass

        guard = Agent()

        with self.assertRaises(TagCompositionError) as raised:        # raised at the exit, as a plain Rip raises it
            with Scope(guard, Sentry, Watch):
                pass

        self.assertEqual(
                str(raised.exception),
                "Sentry teardown failed in: Stand_Down; the Rip is refused and rolled back:"
                " Agent is still a member of Sentry",
                )
        self.assertIsInstance(raised.exception.__cause__, ValueError)
        self.assertEqual(Tags(guard), (Sentry,))                      # a failed Rip blocks the expulsion; Watch was Ripped
        self.assertTrue(guard.on_duty)                                # what the teardown changed is undone

        stuck.clear()                                                  # repaired: the Agent ends quietly

    def test_a_teardown_that_fails_as_the_block_raises_is_a_note_and_the_tag_stays(self) -> None:
        stuck = [True]

        class Sentry(Tag):
            @Rip
            def Stand_Down(agent):
                if stuck:
                    raise ValueError("the post will not be left")

        guard = Agent()

        with self.assertRaises(LookupError) as raised:                # the block's own exception keeps its place
            with Scope(guard, Sentry):
                raise LookupError("the block fails")

        self.assertEqual(
                raised.exception.__notes__,
                ["On leaving the Scope: TagCompositionError: Sentry teardown failed in: Stand_Down;"
                 " the Rip is refused and rolled back: Agent is still a member of Sentry"],
                )
        self.assertIn(guard, Sentry)

        stuck.clear()                                                  # repaired: the Agent ends quietly

    def test_every_failed_rip_after_the_first_is_a_note(self) -> None:
        stuck = [True]

        class Wolf(Tag):
            pass

        class Dire(Wolf):
            pass

        class Sentry(Tag):
            @Rip
            def Stand_Down(agent):
                if stuck:
                    raise ValueError("the post will not be left")

        ed = Agent()

        with self.assertRaises(TagCompositionError) as raised:
            with Scope(ed, Wolf, Sentry):
                Dire(ed)

        self.assertTrue(str(raised.exception).startswith("Sentry teardown failed in: Stand_Down;"))   # the last named is Ripped first
        self.assertEqual(
                raised.exception.__notes__,
                ["On leaving the Scope: TagCompositionError: Wolf is required by active Shape(s): Dire"],
                )

        stuck.clear()                                                  # repaired: the Agent ends quietly

    def test_a_tag_the_block_ripped_is_not_ripped_again(self) -> None:
        class Wizard(Tag):
            pass

        fay = Agent()

        with Scope(fay, Wizard):
            del Wizard[fay]                                           # the block takes it away itself

        self.assertNotIn(fay, Wizard)

    def test_a_tag_the_block_ripped_and_applied_again_is_the_blocks(self) -> None:
        """A Scope Rips what it applied, and only that: the application the
        block made is the block's, and stays."""

        ripped = []

        class Wizard(Tag):
            @Rip
            def Leave(agent):
                ripped.append(agent)

        fay = Agent()

        with Scope(fay, Wizard):
            del Wizard[fay]                                           # the Scope's Wizard ends here
            Wizard(fay)                                               # and the block's begins

        self.assertIn(fay, Wizard)
        self.assertEqual(len(ripped), 1)                              # the block's Rip, and no other

    def test_a_tag_the_block_ripped_and_a_shape_pulled_in_again_is_the_blocks(self) -> None:
        """A Base the block's Shape pulls in is the block's: the Scope
        leaves it, and has no Rip to report."""

        class Wolf(Tag):
            pass

        class Dire(Wolf):
            pass

        bo = Agent()

        with Scope(bo, Wolf):
            del Wolf[bo]
            Dire(bo)                                                  # Wolf comes back as Dire's Base

        self.assertEqual(Tags(bo), (Dire,))
        self.assertIn(bo, Wolf)

    def test_a_scope_leaves_a_tag_a_string_agent_already_carries(self) -> None:
        """The Scope asks whether the Agent carries the Tag, not whether
        the Agent, read as a word, is one of its keywords."""

        class Name(str):
            pass

        class Wolf(Tag):
            pass

        rex = Name("rex")
        Wolf(rex)

        with Scope(rex, Wolf):
            pass

        self.assertEqual(Tags(rex), (Wolf,))                          # it was Rex's, not the Scope's

    def test_a_scope_that_reports_a_refused_rip_keeps_no_cycle(self) -> None:
        """The Agent dies with its last reference, gc or not, after a
        Scope raised the refusal, or noted it on the block's exception."""

        class Wolf(Tag):
            pass

        class Dire(Wolf):
            pass

        for block_fails in (False, True):
            with self.subTest(block_fails=block_fails):
                gc.collect()
                gc.disable()

                try:
                    gus = Agent()
                    reference = weakref.ref(gus)

                    try:
                        with Scope(gus, Wolf):
                            Dire(gus)                                 # Wolf's Rip will be refused

                            if block_fails:
                                raise ValueError("the block fails")
                    except (TagCompositionError, ValueError) as error:
                        caught = type(error)

                    self.assertIs(caught, ValueError if block_fails else TagCompositionError)

                    del gus

                    self.assertIsNone(reference())                    # freed by its count: no cycle held it
                finally:
                    gc.enable()


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
                @Report
                def hue(tag) -> str:
                    return colour

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
            @Report
            def Field(tag) -> str:
                return "a farm"

            @Report
            def Form(tag) -> str:
                return "a hut"

            @Report
            def Rip(tag) -> str:
                return "a tear"

        self.assertEqual(Freehold.Field, "a farm")
        self.assertEqual(Freehold.Form, "a hut")
        self.assertEqual(Freehold.Rip, "a tear")
        self.assertEqual(Form(Freehold), (Freehold,))


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


class ConditionMemberTests(unittest.TestCase):
    """STEP-SPEC-14: a condition is read on the Agent by its name, as a
    plain bool, computed on read. Nothing lands on the Agent."""

    def test_a_condition_reads_as_a_bool_on_the_agent(self) -> None:
        class Wizard(Tag):
            @Post
            def Has_Book(agent):
                return agent.book is not None

            @Pre
            def Is_Awake(agent):
                return agent.awake

        ari = Agent()
        ari.book, ari.awake = [], True
        Wizard(ari)

        self.assertIs(ari.Has_Book, True)
        self.assertIs(ari.Is_Awake, True)
        self.assertTrue(hasattr(ari, "Has_Book"))
        self.assertNotIn("Has_Book", vars(ari))                       # computed on read, not stored

        ari.book = None
        self.assertIs(ari.Has_Book, False)
        self.assertFalse(ari)
        self.assertNotIn("Has_Book", vars(ari))
        self.assertIs(Contract.Status(ari)["Has_Book"], False)

        with self.assertRaises(AttributeError):
            ari.Has_Sword                                             # no such condition

    def test_a_raising_condition_reads_false_and_a_non_bool_raises_on_the_member(self) -> None:
        class Loud(Tag):
            @Post
            def Ready(agent):
                assert agent.ready

            @Post
            def Count(agent):
                return agent.count

        ari = Agent()
        ari.ready, ari.count = True, True
        Loud(ari)
        ari.ready = False
        self.assertIs(ari.Ready, False)

        ari.count = 0
        with self.assertRaises(TagContractError):
            ari.Count

        with self.assertRaises(TagContractError):
            hasattr(ari, "Count")                                     # 0.2.0a3 gave False

        with self.assertRaises(TagContractError):
            getattr(ari, "Count", None)                               # 0.2.0a3 gave None

        self.assertIs(Contract.Status(ari)["Count"], False)          # the status counts it
        self.assertFalse(ari)

    def test_a_gate_is_read_without_the_taggings_inputs(self) -> None:
        class Coded(Tag):
            @Pre
            def Has_Code(agent, code=None):
                return code == "007"

        bond = Agent()
        Coded(bond, code="007")                                       # the gate passed, with its input

        self.assertIs(bond.Has_Code, False)                           # read now, with its default
        self.assertEqual(Contract.Status(bond), {"Has_Code": False})
        self.assertTrue(bond)                                         # a gate is no promise

        class Cleared(Tag):
            @Pre
            def Has_Clearance(agent, code=None):
                return code != "forbidden"

            @Pre
            def Has_Badge(agent, badge):
                return badge == "gold"

        class Visitor(Tag):
            @Pre
            def Has_No_Badge(agent, badge):
                return badge is None

            @Pre
            def Has_No_Pass(agent, *, badge):
                return badge is None

        Cleared(bond, code="x", badge="gold")
        Visitor(bond)

        self.assertIs(bond.Has_Clearance, True)                       # the default decides, not the tagging's input
        self.assertIs(bond.Has_Badge, False)                          # no default: bound to None, and None == "gold" is False
        self.assertIs(bond.Has_No_Badge, True)                        # bound to None as at the door (§2.2), so True
        self.assertIs(bond.Has_No_Pass, True)                         # keyword-only: the same binding

    def test_a_pinned_tags_condition_reads_on_the_tag(self) -> None:
        class Wizard(Tag):
            pass

        @Pin
        class Promised(Tag):
            @Post
            def Has_Members(tag):
                return bool(tag[:])

        with self.assertRaises(Postcondition.Has_Members):
            Promised(Wizard)

        self.assertIs(Wizard.Has_Members, False)
        ari = Agent()                                                 # held: Fields are weak
        Wizard(ari)
        self.assertIs(Wizard.Has_Members, True)

    def test_a_condition_cannot_share_a_name_with_an_action_or_record(self) -> None:
        class Named(Tag):
            @Post
            def Has_Book(agent):
                return True

        class Clash_Record(Tag):
            @Record
            def Has_Book(agent):
                return 1

        class Clash_Action(Tag):
            def Has_Book(agent):
                return 1

        ari = Agent()
        Named(ari)

        with self.assertRaises(TagCompositionError):
            Clash_Record(ari)

        with self.assertRaises(TagCompositionError):
            Clash_Action(ari)

        bo = Agent()
        Clash_Record(bo)

        with self.assertRaises(TagCompositionError):
            Named(bo)                                                 # the other way round

        self.assertNotIn(bo, Named)                                   # rolled back

    def test_a_condition_cannot_share_a_name_with_the_host(self) -> None:
        class Host:
            def Has_Book(self):
                return "host"

        class Named(Tag):
            @Post
            def Has_Book(agent):
                return True

        with self.assertRaises(TagCompositionError):
            Named(Host())

        class Valued(Tag):
            @Post
            def book(agent):
                return True

        ari = Agent()
        ari.book = []                                                 # a value the Agent holds

        with self.assertRaises(TagCompositionError):
            Valued(ari)

        self.assertNotIn(ari, Valued)

    def test_the_member_and_the_status_agree(self) -> None:
        class Elf(Tag):
            @Requirement
            def Alive(agent):
                return agent.alive

        ari = Agent()
        ari.alive = True
        Elf(ari)
        self.assertEqual(Contract.Status(ari), {"Alive": True})
        self.assertIs(ari.Alive, True)

        ari.alive = False
        self.assertEqual(Contract.Status(ari), {"Alive": False})
        self.assertIs(ari.Alive, False)


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



class FlagWordTests(unittest.TestCase):
    """STEP-SPEC-17: a Flag answers to its own name and to the words it
    lists. A word is a keyword, never membership."""

    def test_a_flag_answers_to_its_words(self) -> None:
        @Flag("Wolf", "Lycanthrope")
        class Werewolf(Tag):
            pass

        howler = Agent()
        Werewolf(howler)

        self.assertIn("Werewolf", howler)                 # the name always flags
        self.assertIn("Wolf", howler)
        self.assertIn("Lycanthrope", howler)
        self.assertIn(Werewolf, howler)                   # the class form is unchanged
        self.assertNotIn("wolf", howler)                  # words match exactly
        self.assertNotIn("Were", howler)
        self.assertNotIn("Lycan", howler)                 # no prefixes of a word
        self.assertNotIn("Lycanthropes", howler)
        self.assertTrue(Keyword(howler, "Wolf", "Lycanthrope", Werewolf))
        self.assertFalse(Keyword(howler, "Wolf", "Vampire"))

        del Werewolf[howler]

        self.assertNotIn("Wolf", howler)
        self.assertFalse(Keyword(howler, "Werewolf"))

    def test_a_bare_flag_and_an_empty_flag_are_the_name_alone(self) -> None:
        @Flag()
        class Undead(Tag):
            pass

        @Flag
        class Flying(Tag):
            pass

        ghoul = Agent()
        Undead(ghoul)
        Flying(ghoul)

        self.assertTrue(Keyword(ghoul, "Undead", "Flying", Undead, Flying))
        self.assertFalse(Keyword(ghoul, "Wolf"))

    def test_an_alias_is_not_membership(self) -> None:
        """The secret identity: the word answers for the public persona,
        membership for what the Agent is."""

        @Flag
        class Beast(Tag):
            pass

        @Flag("Beast")
        class Werewolf(Tag):
            pass

        howler = Agent()
        Werewolf(howler)

        self.assertIn("Beast", howler)                    # the word, through Werewolf
        self.assertNotIn(howler, Beast)                   # not a Beast
        self.assertNotIn(Beast, howler)                   # a class asks for the Flag itself
        self.assertFalse(Keyword(howler, Beast))
        self.assertTrue(Keyword(howler, "Beast"))
        self.assertEqual(list(Beast), [])                 # an alias joins no Field

    def test_words_follow_the_form(self) -> None:
        @Flag("Hunter")
        class Wolf(Tag):
            pass

        class Alpha(Wolf):                                # a Shape, not a Flag
            pass

        @Flag("Leader")
        class Pack_Lord(Alpha):
            pass

        alpha, lord = Agent(), Agent()
        Alpha(alpha)
        Pack_Lord(lord)

        self.assertTrue(Keyword(alpha, "Wolf", "Hunter"))  # the Base's words, the Base is active
        self.assertFalse(Keyword(alpha, "Alpha"))         # a Shape does not inherit being a Flag
        self.assertFalse(Keyword(alpha, "Leader"))
        self.assertTrue(Keyword(lord, "Pack_Lord", "Leader", "Wolf", "Hunter"))
        self.assertFalse(Keyword(lord, "Alpha"))

    def test_one_word_many_tags(self) -> None:
        @Flag("Monster")
        class Werewolf(Tag):
            pass

        @Flag("Monster")
        class Vampire(Tag):
            pass

        count = Agent()
        Werewolf(count)
        Vampire(count)

        self.assertIn("Monster", count)

        del Werewolf[count]
        self.assertIn("Monster", count)                   # Vampire still says it

        del Vampire[count]
        self.assertNotIn("Monster", count)

    def test_stacked_flags_add_their_words(self) -> None:
        @Flag("Wolf")
        @Flag("Lycanthrope")
        class Werewolf(Tag):
            pass

        howler = Agent()
        Werewolf(howler)

        self.assertTrue(Keyword(howler, "Werewolf", "Wolf", "Lycanthrope"))

    def test_words_are_non_empty_strings(self) -> None:
        class Werewolf(Tag):
            pass

        for spelling in (
                lambda: Flag("Wolf", 3),
                lambda: Flag(""),
                lambda: Flag(Werewolf, "Wolf"),
                lambda: Flag(None),
                lambda: Flag("Wolf")(Agent),
                ):
            with self.assertRaises(TagDeclarationError):
                spelling()

        howler = Agent()
        Werewolf(howler)

        self.assertFalse(Keyword(howler, "Werewolf"))     # nothing was marked
        self.assertFalse(Keyword(howler, Werewolf))

    def test_a_word_is_matched_as_plain_text(self) -> None:
        """A str subclass is read as its text: exact, and never unhashable."""

        class Loose(str):
            def __eq__(self, other):
                return isinstance(other, str) and self.lower() == other.lower()

        @Flag("Wolf")
        class Werewolf(Tag):
            pass

        howler = Agent()
        Werewolf(howler)

        self.assertIn(Loose("Wolf"), howler)
        self.assertIn(Loose("Werewolf"), howler)
        self.assertNotIn(Loose("wolf"), howler)           # exact, whatever the subclass says
        self.assertNotIn(Loose("werewolf"), howler)
        self.assertNotIn(Loose("Fiend"), howler)          # no TypeError from an unhashable word
        self.assertFalse(Keyword(howler, Loose("Fiend")))

    def test_a_flag_word_is_kept_as_its_plain_text(self) -> None:
        """A str subclass given to @Flag is kept as its text, as a probe is."""

        class Folded(str):
            def __eq__(self, other):
                return isinstance(other, str) and self.lower() == other.lower()

            def __hash__(self):
                return hash(self.lower())

        @Flag(Folded("Wolf"))
        class Lycan(Tag):
            pass

        @Flag([Folded("Beast")])
        class Warg(Tag):
            pass

        moon, fang = Agent(), Agent()
        Lycan(moon)
        Warg(fang)

        self.assertIn("Wolf", moon)                       # its own word matches
        self.assertNotIn("wolf", moon)                    # exact, whatever the subclass says
        self.assertTrue(Keyword(moon, "Wolf"))
        self.assertFalse(Keyword(moon, "wolf"))
        self.assertIn("Beast", fang)
        self.assertNotIn("beast", fang)

        for tag in (Lycan, Warg):
            self.assertEqual({type(word) for word in vars(tag)["__topkit_flag__"]}, {str})

    def test_an_unhashable_word_is_refused_by_name(self) -> None:
        """A str subclass that does not hash is no word for a set of words."""

        class Unhashable(str):
            __hash__ = None

            def __eq__(self, other):
                return True

        class BadHash(str):
            def __hash__(self):
                raise ValueError("no hash today")

        class Werewolf(Tag):
            pass

        for words, named in (
                ((Unhashable("Wolf"),), "got 'Wolf'; its type, Unhashable, does not hash"),
                (([Unhashable("Wolf"), "Beast"],), "got 'Wolf' in ['Wolf', 'Beast']; its type, Unhashable, does not hash"),
                (("Beast", (Unhashable("Wolf"),)), "got 'Wolf' in ('Wolf',); its type, Unhashable, does not hash"),
                ((BadHash("Wolf"),), "got 'Wolf'; its type, BadHash, does not hash"),
                ((["Beast", BadHash("Wolf")],), "got 'Wolf' in ['Beast', 'Wolf']; its type, BadHash, does not hash"),
                ):
            with self.subTest(words=words):
                with self.assertRaises(TagDeclarationError) as caught:
                    Flag(*words)

                self.assertIn(named, str(caught.exception))   # the message names the item

                self.assertIsNone(caught.exception.__cause__)     # the hash's own error is not chained
                self.assertTrue(caught.exception.__suppress_context__)

        howler = Agent()
        Werewolf(howler)

        self.assertFalse(Keyword(howler, "Werewolf"))     # nothing was marked
        self.assertFalse(Keyword(howler, "Wolf"))

    def test_a_flag_takes_its_words_as_a_list_a_tuple_or_a_set(self) -> None:
        """The Director, 2026-10-02: "The flags as text or a list of texts
        makes sense"."""

        @Flag(["Wolf", "Beast"])
        class Werewolf(Tag):
            pass

        @Flag(("Wolf", "Beast"))
        class Warg(Tag):
            pass

        @Flag({"Lycan", "Lupus"})
        class Lycanthrope(Tag):
            pass

        @Flag(frozenset({"Lycan", "Lupus"}))
        class Lupine(Tag):
            pass

        for tag, words in (
                (Werewolf, ("Wolf", "Beast")),
                (Warg, ("Wolf", "Beast")),
                (Lycanthrope, ("Lycan", "Lupus")),
                (Lupine, ("Lycan", "Lupus")),
                ):
            agent = Agent()
            tag(agent)

            self.assertTrue(Keyword(agent, tag.__name__, *words))   # the name always flags
            self.assertIn(words[0], agent)
            self.assertIn(words[1], agent)
            self.assertEqual(vars(tag)["__topkit_flag__"], frozenset(words))

    def test_words_and_collections_of_words_mix(self) -> None:
        @Flag("Wolf", ["Beast", "Howler"], {"Lycan"}, ("Wolf", "Beast"))
        class Werewolf(Tag):
            pass

        howler = Agent()
        Werewolf(howler)

        self.assertTrue(Keyword(howler, "Werewolf", "Wolf", "Beast", "Howler", "Lycan"))
        self.assertEqual(                                 # flattened, a word given twice kept once
                vars(Werewolf)["__topkit_flag__"],
                frozenset({"Wolf", "Beast", "Howler", "Lycan"}),
                )

    def test_a_collection_of_words_holds_non_empty_strings_one_level_deep(self) -> None:
        class Beast(Tag):
            pass

        for words, named in (
                ([], "[]"),
                ((), "()"),
                (set(), "set()"),
                (frozenset(), "frozenset()"),
                (["Wolf", 3], "got 3 in ['Wolf', 3]"),
                (["Wolf", ""], "got '' in ['Wolf', '']"),
                (["Wolf", ["Beast"]], "got ['Beast'] in ['Wolf', ['Beast']]"),
                (("Wolf", {"Beast"}), "got {'Beast'} in ('Wolf', {'Beast'})"),
                (["Wolf", ("Beast",)], "got ('Beast',) in ['Wolf', ('Beast',)]"),   # one that hashes, too
                (("Wolf", frozenset({"Beast"})), "got frozenset({'Beast'}) in ('Wolf', frozenset({'Beast'}))"),
                ([Beast], "got <class"),
                ({"Wolf": "Beast"}, "got {'Wolf': 'Beast'}"),
                ):
            with self.subTest(words=words):
                with self.assertRaises(TagDeclarationError) as caught:
                    Flag(words)

                self.assertIn(named, str(caught.exception))   # the message names the item

        with self.assertRaises(TagDeclarationError):
            Flag("Wolf", [])                              # beside a word, too

        howler = Agent()
        Beast(howler)

        self.assertFalse(Keyword(howler, "Beast"))        # nothing was marked
        self.assertFalse(Keyword(howler, "Wolf"))

    def test_a_flag_on_a_tag_with_members_is_refused(self) -> None:
        """A Flag is part of the Tag's declaration (STEP-SPEC-17, 2026-09-29)."""

        class Wolf(Tag):
            pass

        class Dire(Wolf):
            pass

        ari, bo = Agent(), Agent()
        Wolf(ari)
        self.assertFalse(Keyword(ari, "Howler"))          # the words are gathered here
        Dire(bo)                                          # a Shape's member carries the Base

        for mark, hint in (
                (Flag("Howler"), ""),
                (Flag, "; a word is written as a string, @Flag('Wolf')"),   # a lone class may be a word meant
                ):
            with self.assertRaises(TagDeclarationError) as refused:
                mark(Wolf)

            self.assertEqual(
                    str(refused.exception),
                    "Wolf is carried by 2 Agents; a Flag is part of the Tag's declaration" + hint,
                    )

        self.assertNotIn("__topkit_flag__", vars(Wolf))  # nothing was marked
        self.assertFalse(Keyword(ari, "Howler"))
        self.assertFalse(Keyword(bo, "Wolf"))

    def test_a_base_whose_shape_has_members_is_refused(self) -> None:
        class Wolf(Tag):
            pass

        class Dire(Wolf):
            pass

        class Howling(Tag):
            @Post
            def Is_Loud(agent):
                return agent.loud

        bo = Agent()
        Dire(bo)

        with self.assertRaisesRegex(TagDeclarationError, "^Wolf is carried by 1 Agent;"):
            Flag("Howler")(Wolf)

        ari = Agent()
        ari.loud = False

        with self.assertRaises(TagPostconditionError):
            Howling(ari)                                  # a defective member still carries it

        with self.assertRaisesRegex(TagDeclarationError, "^Howling is carried by 1 Agent;"):
            Flag(Howling)

    def test_a_flag_is_taken_once_nobody_carries_the_tag(self) -> None:
        class Wolf(Tag):
            pass

        class Dire(Wolf):
            pass

        ari, bo = Agent(), Agent()
        Wolf(ari)
        Wolf(bo)

        del Wolf[ari]                                     # Ripped
        del bo                                            # gone
        gc.collect()

        Flag("Howler")(Dire)                              # a Shape nobody carries
        Flag("Hunter")(Wolf)

        Dire(ari)

        self.assertTrue(Keyword(ari, "Wolf", "Hunter", "Dire", "Howler"))
        self.assertIn("Hunter", ari)

    def test_a_flag_on_a_pin_that_pinned_a_tag_is_refused(self) -> None:
        @Pin
        class Deprecated(Tag):
            pass

        class Wizard(Tag):
            pass

        Deprecated(Wizard)

        with self.assertRaisesRegex(
                TagDeclarationError,
                "^Deprecated is carried by 1 Tag; a Flag is part of the Tag's declaration$",
                ):
            Flag("Obsolete")(Deprecated)

        self.assertNotIn("Obsolete", Wizard)

    def test_a_flag_that_lands_after_another_tag_takes_the_seat(self) -> None:
        @Flag("Wolf")
        class Werewolf(Tag):
            pass

        howler = Agent()
        Elf(howler)                                       # the runtime type exists already
        Werewolf(howler)

        self.assertIn("Wolf", howler)
        self.assertIn(Werewolf, howler)

    def test_a_flag_base_that_lands_after_another_tag_takes_the_seat(self) -> None:
        @Flag("Hunter")
        class Wolf(Tag):
            pass

        class Alpha(Wolf):
            pass

        howler = Agent()
        Elf(howler)
        Alpha(howler)

        self.assertIn("Hunter", howler)

    def test_a_flag_with_words_on_a_container_host_is_refused(self) -> None:
        @Flag("Mark")
        class Marked(Tag):
            pass

        for tagged_first in (False, True):
            bag = HostPreservationTests.Bag()

            if tagged_first:
                Elf(bag)

            with self.assertRaises(TagCompositionError):
                Marked(bag)

            self.assertNotIn(bag, Marked)
            self.assertIn("x", bag)
            self.assertNotIn("Mark", bag)                 # the host's own `in` answers
            self.assertFalse(Keyword(bag, "Mark"))

    def test_a_flag_pin_answers_to_its_words_on_the_tag(self) -> None:
        @Pin
        @Flag("Obsolete")
        class Deprecated(Tag):
            pass

        class Wizard(Tag):
            pass

        ari = Agent()
        Wizard(ari)
        Deprecated(Wizard)

        self.assertIn("Obsolete", Wizard)
        self.assertIn("Deprecated", Wizard)
        self.assertTrue(Keyword(Wizard, "Obsolete", Deprecated))
        self.assertNotIn("Obsolete", Deprecated)          # the Pin itself carries nothing
        self.assertIn(ari, Wizard)
        self.assertFalse(Keyword(ari, "Obsolete"))        # a Pin's word stays on the Tag

    def test_rules_written_as_data_read_aliases(self) -> None:
        @Flag("Wolf", "Beast")
        class Werewolf(Tag):
            pass

        @Flag("Beast")
        class Bear(Tag):
            pass

        rules = {
                "Beast-Silver": "vulnerable",
                "Wolf": "howls",
                "Beast": "growls",
                }

        def react(agent):
            for rule, reaction in rules.items():
                if Keyword(agent, *rule.split("-")):
                    return reaction

            return "stares"

        howler, grizzly = Agent(), Agent()
        Werewolf(howler)
        Bear(grizzly)

        self.assertEqual(react(howler), "howls")
        self.assertEqual(react(grizzly), "growls")
        self.assertEqual(react(Agent()), "stares")



class RestoredNameTests(unittest.TestCase):
    """A name a Tag deleted and a later Layer stored again keeps its gate
    on the runtime type, so a type rebuilt for any later reason (a Flag,
    a Postcondition, another deletion) never lets the host's own member
    back over the Layer's."""

    class Host:
        @property
        def speak(self) -> str:
            return "host property"

    def setUp(self) -> None:
        class Mute(Tag):
            @Delete
            def speak(agent): ...

        class Talker(Mute):
            def speak(agent) -> str:
                return "Talker action"

        self.Talker = Talker

    def test_a_later_tag_that_rebuilds_the_type_keeps_the_layer(self) -> None:
        @Flag("Wolf")
        class Werewolf(Tag):
            pass

        class Promised(Tag):
            @Post
            def Fine(agent) -> bool:
                return True

        class Gone(Tag):
            @Delete
            def unrelated(agent): ...

        for later in (Werewolf, Promised, Gone):
            host = self.Host()
            self.Talker(host)
            self.assertEqual(host.speak(), "Talker action")

            later(host)

            self.assertEqual(host.speak(), "Talker action", later.__name__)

    def test_the_order_of_a_flag_does_not_change_the_layer(self) -> None:
        @Flag
        class Werewolf(Tag):
            pass

        first, second = self.Host(), self.Host()
        self.Talker(first)
        Werewolf(first)
        Werewolf(second)
        self.Talker(second)

        self.assertEqual(first.speak(), "Talker action")
        self.assertEqual(second.speak(), "Talker action")
        self.assertIs(type(first), type(second))



class InSeatTests(unittest.TestCase):
    """STEP-SPEC-7, amended: a Flag's words need the Agent's `in`. The host
    (through __contains__ or __iter__) or a Tag's Action of either name
    may already answer it; the two collide, in either order, and the
    collision is refused and named. `in` never changes meaning in silence."""

    class Party:
        def __init__(self) -> None:
            self.members = ["alice", "bob"]

        def __iter__(self):
            return iter(self.members)

    def setUp(self) -> None:
        @Flag("Wolf")
        class Werewolf(Tag):
            pass

        class Roster(Tag):
            def __iter__(agent):
                return iter(["alice", "bob"])

        class Gate(Tag):
            def __contains__(agent, key) -> bool:
                return key == "alice"

        self.Werewolf, self.Roster, self.Gate = Werewolf, Roster, Gate

    def refused(self, act, *mentions: str) -> None:
        with self.assertRaises(TagCompositionError) as caught:
            act()

        for mention in mentions:
            self.assertIn(mention, str(caught.exception))

    def test_an_iterable_host_refuses_a_flag(self) -> None:
        for tagged_first in (False, True):
            party = self.Party()

            if tagged_first:
                Elf(party)

            self.refused(lambda: self.Werewolf(party), "Werewolf", "Party.__iter__")

            self.assertIn("alice", party)                 # membership keeps its meaning
            self.assertNotIn(party, self.Werewolf)
            self.assertFalse(Keyword(party, "Wolf"))

    def test_the_refusal_names_the_class_that_answers(self) -> None:
        class Crew(self.Party):
            pass

        class Deck:
            def __iter__(self):
                yield "ace"

        self.refused(lambda: self.Werewolf(Crew()), "Crew already answers", "Party.__iter__")
        self.refused(lambda: self.Werewolf(Deck()), "Deck.__iter__")
        self.refused(lambda: self.Werewolf(HostPreservationTests.Bag()), "Bag.__contains__")

    def test_a_host_that_declares_no_in_is_a_free_seat(self) -> None:
        class Loud(self.Party):
            __contains__ = None                           # Python: `in` is unavailable

        class Mute:
            __iter__ = None

        class Guild(collections.abc.Sequence):            # the parent owns `in`; the child says no
            __contains__ = None

            def __getitem__(self, index):
                return ["alice"][index]

            def __len__(self) -> int:
                return 1

        for host in (Loud(), Mute(), Guild()):
            with self.assertRaises(TypeError):
                "alice" in host

            self.Werewolf(host)

            self.assertIn("Wolf", host)                   # the Flag holds the seat
            self.assertNotIn("alice", host)

        self.assertEqual(list(Loud()), ["alice", "bob"])  # iteration is untouched

    def test_a_keyed_host_gives_its_seat_to_a_flag(self) -> None:
        class Sheet:
            def __init__(self) -> None:
                self.scores = {"STR": 16}

            def __getitem__(self, key):
                return self.scores[key]

        sheet = Sheet()

        with self.assertRaises(KeyError):
            "STR" in sheet                                # Python's fallback asks sheet[0]

        self.Werewolf(sheet)

        self.assertIn("Wolf", sheet)
        self.assertEqual(sheet["STR"], 16)

    def test_a_tag_that_answers_in_then_a_flag(self) -> None:
        for answering, method in (
                (self.Roster, "Roster.__iter__"),
                (self.Gate, "Gate.__contains__"),
                ):
            ari = Agent()
            answering(ari)
            before = "alice" in ari

            self.refused(lambda: self.Werewolf(ari), "Werewolf", method)

            self.assertIs("alice" in ari, before)         # unchanged
            self.assertTrue(before)
            self.assertNotIn(ari, self.Werewolf)

    def test_a_flag_then_a_tag_that_answers_in(self) -> None:
        for answering, method in (
                (self.Roster, "Roster.__iter__"),
                (self.Gate, "Gate.__contains__"),
                ):
            ari = Agent()
            self.Werewolf(ari)

            self.refused(lambda: answering(ari), method, "Flag Werewolf")

            self.assertIn("Wolf", ari)                    # the words keep the seat
            self.assertNotIn(ari, answering)

    def test_a_shape_that_answers_in_over_a_flag_base_rolls_back(self) -> None:
        Werewolf = self.Werewolf

        class Pack_Leader(Werewolf):
            def __iter__(agent):
                return iter(["alice"])

        ari = Agent()

        self.refused(lambda: Pack_Leader(ari), "Pack_Leader.__iter__", "Flag Werewolf")

        self.assertNotIn(ari, Werewolf)                   # the whole Form rolled back
        self.assertNotIn(ari, Pack_Leader)

    def test_a_flag_cannot_answer_in_itself(self) -> None:
        class Pack(Tag):
            def __iter__(agent):
                return iter(())

        class Den(Tag):
            def __contains__(agent, key) -> bool:
                return False

        for tag, method in (
                (Pack, "__iter__"),
                (Den, "__contains__"),
                ):
            with self.assertRaises(TagDeclarationError) as caught:
                Flag("Wolf")(tag)

            self.assertIn(method, str(caught.exception))
            self.assertIsNone(vars(tag).get("__topkit_flag__"))   # nothing was marked

        @Flag
        class Quiet(Tag):                                 # a Record by that name answers nothing
            @Record
            def __iter__(agent):
                return None

    def test_after_the_flag_is_ripped_a_tag_may_answer_in(self) -> None:
        ari = Agent()
        self.Werewolf(ari)
        del self.Werewolf[ari]

        self.Roster(ari)

        self.assertIn("alice", ari)                       # iteration answers again
        self.assertNotIn("Wolf", ari)

    def test_a_ripped_tag_leaves_its_answer_and_the_refusal(self) -> None:
        ari = Agent()
        self.Roster(ari)
        del self.Roster[ari]                              # Actions are sticky (§0.7)

        self.assertIn("alice", ari)
        self.refused(lambda: self.Werewolf(ari), "Roster.__iter__")

    def test_contains_is_read_before_iter(self) -> None:
        class Odd(HostPreservationTests.Bag):
            __iter__ = None                               # the parent's __contains__ still answers

        class Hushed(self.Party):
            __iter__ = None                               # Python: `in` is unavailable

        odd = Odd()

        self.refused(lambda: self.Werewolf(odd), "Bag.__contains__")
        self.assertIn("x", odd)

        hushed = Hushed()
        self.Werewolf(hushed)
        self.assertIn("Wolf", hushed)

    def test_a_published_operation_answers_in_too(self) -> None:
        class Keeper(Tag):
            @Public
            @Operation
            def __contains__(tag, agent, key) -> bool:
                return key == "alice"

        class Promised(Keeper):
            @Post
            def Fine(agent) -> bool:
                return True

        for keeper in (Keeper, Promised):
            ari = Agent()
            self.Werewolf(ari)

            self.refused(lambda: keeper(ari), "Keeper.__contains__", "Flag Werewolf")
            self.assertIn("Wolf", ari)

        bob = Agent()
        Keeper(bob)

        self.refused(lambda: self.Werewolf(bob), "Keeper.__contains__")

        class Den(Tag):
            @Public
            @Operation
            def __contains__(tag, agent, key) -> bool:
                return False

        with self.assertRaises(TagDeclarationError):
            Flag("Wolf")(Den)

    def test_a_flag_shape_over_a_base_that_answers_in(self) -> None:
        for answering, method in (
                (self.Roster, "Roster.__iter__"),
                (self.Gate, "Gate.__contains__"),
                ):
            @Flag("Alpha")
            class Alpha(answering):
                pass

            carrying, fresh = Agent(), Agent()
            answering(carrying)

            self.refused(lambda: Alpha(carrying), "Alpha", method)
            self.refused(lambda: Alpha(fresh), "Alpha", method)

            self.assertIn(carrying, answering)            # it keeps what it had
            self.assertNotIn(fresh, answering)            # the whole Form rolled back
            self.assertIn("alice", carrying)

    def test_a_form_collides_before_anything_runs(self) -> None:
        log: list[str] = []

        @Flag
        class Wolfkin(Tag):
            @Imprint
            def Note(agent) -> None:
                log.append("Wolfkin")

        class Alpha(Wolfkin):
            def __iter__(agent):
                return iter(())

        ari = Agent()

        self.refused(lambda: Alpha(ari), "Alpha.__iter__", "Flag Wolfkin")

        self.assertEqual(log, [])                         # the Base's Imprint never ran
        self.assertNotIn(ari, Wolfkin)

    def test_a_form_may_free_the_seat_before_its_flag(self) -> None:
        class Ungate(self.Gate):
            @Delete
            def __contains__(agent): ...

        @Flag("Wolf")
        class Freed(Ungate):
            pass

        ari = Agent()
        Freed(ari)

        self.assertIn("Wolf", ari)

    def test_a_flag_given_an_in_method_later_is_refused_on_use(self) -> None:
        for method in ("__iter__", "__contains__"):
            @Flag("Beast")
            class Howler(Tag):
                pass

            setattr(Howler, method, lambda agent, *rest: iter(()))
            ari = Agent()

            self.refused(lambda: Howler(ari), f"Howler.{method}")
            self.assertNotIn(ari, Howler)

    def test_deleting_the_in_method_leaves_the_flag_its_words(self) -> None:
        class Ungate(Tag):
            @Delete
            def __contains__(agent): ...

            @Post
            def Fine(agent) -> bool:
                return True

        first, second = Agent(), Agent()
        self.Gate(first)
        Ungate(first)
        self.Werewolf(first)                              # the seat was freed
        self.Werewolf(second)
        Ungate(second)                                    # a later rebuild keeps the Flag's hook

        self.assertIn("Wolf", first)
        self.assertIn("Wolf", second)

    def test_a_pin_is_untouched(self) -> None:
        @Pin
        @Flag("Obsolete")
        class Deprecated(Tag):
            pass

        class Wizard(Tag):
            pass

        Deprecated(Wizard)

        self.assertIn("Obsolete", Wizard)



class EfficiencyTests(unittest.TestCase):
    """What the kit keeps and what it answers, after the performance work:
    no memory that grows with repetition, and every shortcut answering
    exactly what the long way answered."""

    def test_a_reapplied_postcondition_keeps_nothing_per_turn(self) -> None:
        import tracemalloc

        class Guarded(Tag):
            @Post
            def Fine(agent) -> bool:
                return True

        ari = Agent()
        Guarded(ari)
        del Guarded[ari]
        gc.collect()
        tracemalloc.start()
        before, _peak = tracemalloc.get_traced_memory()

        for _ in range(500):
            Guarded(ari)
            del Guarded[ari]

        gc.collect()
        after, _peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.assertLess((after - before) / 500, 64)   # was about 800 B per turn

    def test_a_dropped_tag_class_is_freed(self) -> None:
        def Make() -> weakref.ref:
            class Temporary(Tag):
                @Record
                def x(agent) -> int:
                    return 1

            ari = Agent()
            Temporary(ari)
            del Temporary[ari]

            return weakref.ref(Temporary)

        reference = Make()
        gc.collect()

        self.assertIsNone(reference())

    def test_a_ripped_tag_leaves_no_view_behind(self) -> None:
        class Payload:
            pass

        class Carrier(Tag):
            @Record
            def payload(agent) -> Payload:
                return Payload()

        ari = Agent()
        Carrier(ari)
        first = weakref.ref(ari.payload)
        ari.payload = None                             # the Agent lets go of it

        self.assertIs(ari.Carrier.payload, first())    # the view still shows it

        del Carrier[ari]
        gc.collect()

        self.assertIsNone(first())                     # the view left with the membership

        Carrier(ari)
        self.assertIs(ari.Carrier.payload, ari.payload)   # a fresh view, taken now

    def test_a_gate_does_not_repeat_a_warning_once_given(self) -> None:
        class Base(Tag):
            def Attack(agent) -> str:
                return "base"

        class Gated(Tag):
            @Pre
            def Ready(agent) -> bool:
                return True

        class Rival(Tag):
            def Attack(agent) -> str:
                return "rival"

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("default")

            for _ in range(5):
                hero = Agent()
                Base(hero)
                Gated(hero)
                Rival(hero)   # replaces an independent Tag's Action: warned once per place

        overwrites = [w for w in caught if issubclass(w.category, TagOverwriteWarning)]

        self.assertEqual(len(overwrites), 1)

    def test_a_population_is_true_exactly_when_someone_counts(self) -> None:
        class Fighter(Tag):
            @Post
            def Armed(agent) -> bool:
                return agent.ready

        self.assertFalse(Fighter)
        self.assertFalse(~Fighter)

        broken = Agent()
        Fighter(broken)
        broken.ready = False

        self.assertFalse(Fighter)          # nobody sound
        self.assertTrue(~Fighter)          # someone broken

        sound = Agent()
        Fighter(sound)

        self.assertTrue(Fighter)
        self.assertEqual(list(Fighter), [sound])

        del sound
        gc.collect()

        self.assertFalse(Fighter)

    def test_an_underlay_called_with_or_without_arguments(self) -> None:
        class Speaker(Tag):
            def Say(agent, word: str = "hello") -> str:
                return word

        class Echo(Speaker):
            @Underlay
            def Say(agent, base, word: str = "hello") -> str:
                return base() + "|" + base("again") + "|" + base(word="named")

        ari = Agent()
        Echo(ari)

        self.assertEqual(ari.Say(), "hello|again|named")
        self.assertEqual(ari.Say("hi"), "hi|again|named")
        self.assertEqual(ari.Say(word="yo"), "yo|again|named")

    def test_leaves_keep_application_order(self) -> None:
        ari = Agent()
        Combatant(ari)
        Elf(ari)
        Bridge(ari)

        self.assertEqual(Tags(ari), (Combatant, Elf, Bridge))
        self.assertEqual(
                Outline(ari),
                "Agent\n  Combatant\n  Person\n    Elf\n  Root\n    Left\n      Right\n        Bridge",
                )

    def test_leaves_are_the_tags_nothing_active_specializes(self) -> None:
        import random

        family = (Root, Left, Right, Bridge, Person, Elf, Combatant)
        chance = random.Random(1701)

        for _ in range(300):
            agent = Agent()
            active: list[type] = []

            for tag in chance.sample(family, chance.randint(1, len(family))):
                tag(agent)

                for member in Form(tag):
                    if member not in active:
                        active.append(member)

            pairwise = tuple(
                    candidate
                    for candidate in active
                    if not any(
                            other is not candidate and issubclass(other, candidate)
                            for other in active
                            )
                    )

            self.assertEqual(Tags(agent), pairwise)

    def test_reapplying_an_active_form_changes_nothing(self) -> None:
        ari = Agent()
        Elf(ari)
        before = (type(ari), dict(vars(ari)))

        self.assertIs(Elf(ari), ari)
        self.assertEqual((type(ari), dict(vars(ari))), before)

    def test_at_exit_runs_every_registration_in_order(self) -> None:
        lines, stderr = Run_Program(
                """
from TopKit import Tag, Rip, At_Exit

class Door:
    def __init__(self, name): self.name = name

class Second(Tag):
    @Rip
    def Stand_Down(agent): print(agent.name, "second")

class First(Tag):
    @Rip
    def Down(agent):
        print(agent.name, "first")
        Second(agent)                         # leaving, it takes another Tag
        late = Door("late"); Second(late); keep.append(late)
        At_Exit(late)                         # registered while the exit pass runs

keep = []
ari = Door("ari"); First(ari)
At_Exit(ari)
At_Exit(ari)                                  # a second registration is its own pass
print("end")
""",
                )

        self.assertEqual(
                lines,
                ["end", "ari first", "ari second", "late second"],
                )
        self.assertEqual(stderr, "")

    def test_an_underlay_is_the_same_callable_with_or_without_arguments(self) -> None:
        seen: list[str] = []

        class Speaker(Tag):
            def Say(agent, word: str = "hello") -> str:
                return word

        class Echo(Speaker):
            @Underlay
            def Say(agent, base, word: str = "hello") -> str:
                seen.append(base.__name__)
                return base()

        ari = Agent()
        Echo(ari)
        ari.Say()
        ari.Say("hi")

        self.assertEqual(seen, ["prior", "prior"])

    def test_the_root_tag_is_never_a_leaf_beside_another_tag(self) -> None:
        class Wizard(Tag):
            pass

        ari = Agent()
        Tag(ari)
        Wizard(ari)

        self.assertEqual(Tags(ari), (Wizard,))

    def test_form_of_a_class_writes_nothing_into_it(self) -> None:
        class Plain:
            pass

        before = set(vars(Plain))

        self.assertEqual(Form(Plain), (Plain,))
        self.assertEqual(Form(int), (int,))
        self.assertEqual(set(vars(Plain)), before)

        with self.assertRaises(TypeError):
            Form(None)

    def test_a_renamed_flag_answers_to_its_new_name(self) -> None:
        @Flag("Wolf")
        class Werewolf(Tag):
            pass

        ari = Agent()
        Werewolf(ari)
        self.assertIn("Werewolf", ari)

        Werewolf.__name__ = "Lycan"

        self.assertIn("Lycan", ari)
        self.assertNotIn("Werewolf", ari)
        self.assertIn("Wolf", ari)

    def test_a_population_truth_agrees_with_its_walk(self) -> None:
        keep: dict[str, object] = {}

        class Enemy(Tag):
            @Post
            def Standing(agent) -> bool:
                if agent.name == "a":
                    keep.pop("b", None)    # a check that frees another member
                    return False

                return True

        for name in ("a", "b"):
            member = Agent()
            member.name = name
            keep[name] = member

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                try:
                    Enemy(member)
                except TagPostconditionError:
                    pass

        del member                         # keep["b"] is b's last reference
        answer = bool(Enemy)

        self.assertTrue(answer)            # b was a member when the question began


def Triage() -> None:
    """Let go of whatever a test left in the safehouse, quietly."""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        del Tag[...]


class LayeredDeletionTests(unittest.TestCase):
    """STEP-SPEC-18: deletion in layers. Every teardown runs first, while
    the Agent is still a member of its Tags, then its own __del__ runs as
    the Overlay shows it: the host's own is the first Layer, a Tag's
    __del__ replaces the Layers beneath or, with @Underlay, extends them.
    Amended 2026-09-29: the Agent's Actions answer a teardown and a Layer
    in a collected cycle, and a Layer at program end; a failed teardown
    is reported after the Layers."""

    def setUp(self) -> None:
        self.log: list[str] = []
        log = self.log

        class Door:
            def __del__(self) -> None:
                log.append("host")

        class Guard(Tag):
            @Rip
            def Leave(agent) -> None:
                log.append("teardown")

        self.Door, self.Guard = Door, Guard
        self.addCleanup(Triage)

    def delete(self, *tags: type, host: type | None = None) -> list[str]:
        door = (host or self.Door)()

        for tag in tags:
            tag(door)

        del door
        gc.collect()

        return self.log

    def reported(self, act, keep=lambda raised: type(raised.exc_value).__name__) -> list:
        """What Python reports as unraisable (a finalizer's error) while
        ``act`` runs: the error's type name, or what ``keep`` takes from
        each report (``err_msg``, ``exc_value``, ``object``)."""

        import sys

        caught: list = []
        hook = sys.unraisablehook
        sys.unraisablehook = lambda raised: caught.append(keep(raised))

        try:
            act()
        finally:
            sys.unraisablehook = hook

        return caught

    def alive(self) -> list:
        """The Doors still on the heap. In a collected cycle Python clears
        weak references before any finalizer runs, so only the heap can
        tell a freed Agent from a resurrected one."""

        return [kept for kept in gc.get_objects() if isinstance(kept, self.Door)]

    def test_with_nothing_stated_the_host_finalizer_is_the_layer(self) -> None:
        self.assertEqual(self.delete(self.Guard), ["teardown", "host"])

    def test_a_tag_may_replace_the_layers_beneath(self) -> None:
        log = self.log

        class Sealed(Tag):
            def __del__(agent) -> None:
                log.append("sealed")

        self.assertEqual(self.delete(self.Guard, Sealed), ["teardown", "sealed"])

    def test_a_tag_may_extend_the_layers_beneath(self) -> None:
        log = self.log

        class Warded(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("warded")
                underlay()

        class Blessed(Warded):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("blessed")
                underlay()

        self.assertEqual(
                self.delete(self.Guard, Blessed),
                ["teardown", "blessed", "warded", "host"],
                )

    def test_a_deleted_finalizer_leaves_only_the_teardowns(self) -> None:
        class Silent(Tag):
            @Delete
            def __del__(agent): ...

        self.assertEqual(self.delete(self.Guard, Silent), ["teardown"])

    def test_the_layer_beneath_is_callable_even_where_the_host_has_none(self) -> None:
        log = self.log

        class Bare:
            pass

        class Warded(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("warded")
                underlay()                 # nothing beneath: does nothing
                log.append("after")

        reported = self.reported(lambda: self.delete(self.Guard, Warded, host=Bare))

        self.assertEqual(self.log, ["teardown", "warded", "after"])
        self.assertEqual(reported, [])

    def test_after_a_delete_the_layer_beneath_is_nothing(self) -> None:
        log = self.log

        class Silent(Tag):
            @Delete
            def __del__(agent): ...

        class Warded(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("warded")
                underlay()                 # the host's own was deleted: nothing
                log.append("after")

        self.assertEqual(
                self.delete(self.Guard, Silent, Warded),
                ["teardown", "warded", "after"],
                )

    def test_a_hosts_error_is_reported_like_any_finalizers(self) -> None:
        log = self.log

        class Cracked:
            def __del__(self) -> None:
                log.append("host")
                raise ValueError("cracked")

        reported = self.reported(lambda: self.delete(self.Guard, host=Cracked))

        self.assertEqual(log, ["teardown", "host"])
        self.assertEqual(reported, ["ValueError"])

    def test_replacing_an_independent_tags_layer_is_diagnosed(self) -> None:
        class Sealed(Tag):
            def __del__(agent) -> None:
                pass

        class Resealed(Tag):
            def __del__(agent) -> None:
                pass

        door = self.Door()
        Sealed(door)

        with self.assertWarns(TagOverwriteWarning):
            Resealed(door)

    def test_an_object_built_from_an_agents_type_is_a_plain_host(self) -> None:
        import dataclasses

        log = self.log

        @dataclasses.dataclass(eq=False)
        class Lantern:
            name: str

            def __del__(self) -> None:
                log.append(f"{self.name} host")

        class Enchanted(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append(f"{agent.name} layer")
                underlay()

        first = Lantern("first")
        self.Guard(first)
        second = dataclasses.replace(first, name="second")   # an instance of first's runtime type
        log.clear()

        def Delete_Second() -> None:
            nonlocal second
            self.Guard(second)
            Enchanted(second)
            del second
            gc.collect()

        reported = self.reported(Delete_Second)

        self.assertEqual(log, ["teardown", "second layer", "second host"])
        self.assertEqual(reported, [])

    def test_layers_and_teardowns_read_their_own_secrets(self) -> None:
        log = self.log

        class Vault(Tag):
            @Secret
            @Record
            def combination(agent) -> str:
                return "1234"

            @Rip
            def Lock(agent) -> None:
                log.append("teardown " + agent.combination)

            def __del__(agent) -> None:
                log.append("layer " + agent.combination)

        self.assertEqual(self.delete(Vault), ["teardown 1234", "layer 1234"])

    def test_an_interrupted_teardown_still_lets_the_layers_run(self) -> None:
        log = self.log

        class Impatient(Tag):
            @Rip
            def Leave(agent) -> None:
                log.append("impatient")
                raise KeyboardInterrupt

        reported = self.reported(lambda: self.delete(Impatient))

        self.assertEqual(log, ["impatient", "host"])
        self.assertEqual(reported, ["KeyboardInterrupt"])

    def test_the_hosts_finalizer_is_found_as_python_finds_it(self) -> None:
        import functools

        log = self.log

        def Closing(self, how: str) -> None:
            log.append(how)

        class Described:
            __del__ = functools.partialmethod(Closing, "described")   # a descriptor

        class Base:
            def __del__(self) -> None:
                log.append("base")

        class Muted(Base):
            __del__ = None                 # Python: this class has no finalizer

        class Later:
            pass

        self.assertEqual(self.delete(self.Guard, host=Described), ["teardown", "described"])
        log.clear()
        self.assertEqual(self.delete(self.Guard, host=Muted), ["teardown"])
        log.clear()

        early = Later()
        self.Guard(early)
        Later.__del__ = lambda self: log.append("added later")
        del early
        gc.collect()

        self.assertEqual(log, ["teardown", "added later"])

    def test_an_untagged_object_built_from_an_agents_type_keeps_its_finalizer(self) -> None:
        log = self.log

        class Lamp:
            def __init__(self, name: str) -> None:
                self.name = name

            def __del__(self) -> None:
                log.append(f"{self.name} host")

            def Twin(self) -> "Lamp":
                return type(self)(self.name + " twin")   # an instance of the runtime type

        first = Lamp("first")
        self.Guard(first)
        twin = first.Twin()
        del twin
        gc.collect()

        self.assertEqual(log, ["first twin host"])   # never tagged: a plain host

    def test_the_hosts_finalizer_is_found_past_every_runtime_type(self) -> None:
        log = self.log

        class Warded(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("warded")
                underlay()

        first = self.Door()
        self.Guard(first)

        class Built_On(type(first)):   # a class built on an Agent's runtime type
            pass

        def Delete_Built() -> None:
            built = Built_On()
            Warded(built)
            del built
            gc.collect()

        log.clear()
        reported = self.reported(Delete_Built)

        self.assertEqual(log, ["warded", "host"])   # once, and down to the host's own
        self.assertEqual(reported, [])

    def test_a_pinned_shape_with_a_flag_pin_ends_quietly(self) -> None:
        program = """
from TopKit import Tag, Pin, Flag, Record

@Pin
class Rare(Tag):
    @Record
    def rarity(tag): return "rare"

@Flag
@Pin
class Deprecated(Tag): pass

class Wizard(Tag): pass

Rare(Wizard)

class Archmage(Wizard): pass     # its metaclass is Wizard's runtime type

Deprecated(Archmage)
print("end", "Deprecated" in Archmage)
"""
        lines, stderr = Run_Program(program)

        self.assertEqual(lines, ["end True"])
        self.assertEqual(stderr, "")                   # no finalizer recursed at exit

    def test_an_interruption_is_reported_even_when_a_layer_raises(self) -> None:
        import sys

        caught: list[BaseException] = []

        class Impatient(Tag):
            @Rip
            def Leave(agent) -> None:
                raise KeyboardInterrupt

        class Cracked(Tag):
            def __del__(agent) -> None:
                raise ValueError("cracked")

        hook = sys.unraisablehook
        sys.unraisablehook = lambda raised: caught.append((raised.err_msg, raised.exc_value))

        try:
            self.delete(Impatient, Cracked)
        finally:
            sys.unraisablehook = hook

        self.assertEqual([type(error) for _, error in caught], [ValueError, KeyboardInterrupt])
        self.assertEqual(caught[0][0], "Exception ignored in __del__, deleting Door")   # the Layer's own
        self.assertEqual(str(caught[0][1]), "cracked")                                   # error, reported

    def test_a_proxy_host_is_finalized_as_python_finalizes_it(self) -> None:
        log = self.log

        class Target:
            def __del__(self) -> None:
                log.append("the wrapped class's __del__")

        class Proxy:
            def __init__(self, wrapped: object) -> None:
                self._wrapped = wrapped

            def __getattribute__(self, name: str):
                if name in ("__class__", "__dict__"):
                    return getattr(object.__getattribute__(self, "_wrapped"), name)

                return object.__getattribute__(self, name)

            def __del__(self) -> None:
                log.append("proxy host")

        keep = Target()
        proxy = Proxy(keep)
        self.Guard(proxy)
        del proxy
        gc.collect()

        self.assertEqual(log, ["teardown", "proxy host"])

    def test_a_published_operation_named_del_is_a_layer_too(self) -> None:
        log = self.log

        class Closing(Tag):
            @Public
            @Operation
            def __del__(tag, agent) -> None:
                log.append("published layer")

        door = self.Door()
        self.Guard(door)
        Closing(door)

        self.assertIs(door.__del__.__func__, type(door).__del__)
        self.assertNotIn("__del__", vars(door))

        del door
        gc.collect()

        self.assertEqual(log, ["teardown", "published layer"])

    def test_a_refused_tagging_inside_a_teardown_closes_the_door(self) -> None:
        class Gate(Tag):
            @Pre
            def Never(agent) -> bool:
                return False

        class Vault(Tag):
            @Secret
            @Record
            def code(agent) -> str:
                return "1234"

            @Rip
            def Lock(agent) -> None:
                try:
                    Gate(agent)            # refused: the tagging rolls back
                except TagPreconditionError:
                    pass

        door = self.Door()
        Vault(door)
        del Vault[door]

        with self.assertRaises(AttributeError):
            door.code                      # the door closed again: the secret stays hidden

    def test_the_door_closes_after_a_finalizer_is_called_by_hand(self) -> None:
        class Vault(Tag):
            @Secret
            @Record
            def code(agent) -> str:
                return "1234"

            def __del__(agent) -> None:
                raise ValueError("cracked")

        def By_Hand() -> None:
            door = self.Door()
            Vault(door)

            with self.assertRaises(ValueError):
                door.__del__()

            with self.assertRaises(AttributeError):
                door.code

        self.reported(By_Hand)             # the real deletion reports the Layer's error again

    def test_the_hosts_finalizer_under_a_layer_is_found_as_python_finds_it(self) -> None:
        import functools

        log = self.log

        class Warded(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("warded")
                underlay()

        def Closing(self, how: str) -> None:
            log.append(how)

        class Described:
            __del__ = functools.partialmethod(Closing, "described")

        class Base:
            def __del__(self) -> None:
                log.append("base")

        class Muted(Base):
            __del__ = None

        class Callable_Finalizer:
            def __call__(self) -> None:
                log.append("called")

        class Plain_Call:
            __del__ = Callable_Finalizer()   # not a descriptor: called as it is

        class Later:
            pass

        for host, expected in (
                (Described, ["warded", "described"]),
                (Muted, ["warded"]),
                (Plain_Call, ["warded", "called"]),
                ):
            log.clear()
            reported = self.reported(lambda: self.delete(Warded, host=host))

            self.assertEqual(log, expected, host.__name__)
            self.assertEqual(reported, [], host.__name__)

        log.clear()
        early = Later()
        Warded(early)
        Later.__del__ = lambda self: log.append("added later")
        del early
        gc.collect()

        self.assertEqual(log, ["warded", "added later"])

    def test_a_descriptor_finalizer_is_bound_with_the_objects_type(self) -> None:
        log = self.log

        class Recording:
            def __get__(self, agent, owner):
                log.append(f"owner is the object's type: {owner is type(agent)}")
                return lambda: log.append("bound")

        class Owned:
            __del__ = Recording()

        self.assertEqual(
                self.delete(self.Guard, host=Owned),
                ["teardown", "owner is the object's type: True", "bound"],
                )

    def test_a_secret_layer_named_del_keeps_the_finalizer(self) -> None:
        log = self.log

        class Hushed(Tag):
            @Secret
            def __del__(agent) -> None:
                log.append("hushed")

        door = self.Door()
        self.Guard(door)
        Hushed(door)

        self.assertIs(door.__del__.__func__, type(door).__del__)

        del door
        gc.collect()

        self.assertEqual(log, ["teardown", "hushed"])

    def test_a_copy_built_from_a_gated_agent_is_a_plain_host(self) -> None:
        class Lamp:
            def Light(self) -> str:
                return "lit"

            def Twin(self) -> "Lamp":
                return type(self)()

        class Dark(Tag):
            @Delete
            def Light(agent): ...

        dark = Lamp()
        Dark(dark)
        twin = dark.Twin()                 # wears Dark's runtime type and its gate
        self.Guard(twin)
        plain = Lamp()
        self.Guard(plain)

        self.assertEqual(twin.Light(), "lit")
        self.assertIs(type(twin), type(plain))

    def test_a_muted_hosts_finalizer_reports_nothing(self) -> None:
        class Base:
            def __del__(self) -> None:
                pass

        class Muted(Base):
            __del__ = None

        self.assertEqual(self.reported(lambda: self.delete(self.Guard, host=Muted)), [])

    def test_a_restored_finalizer_shares_the_runtime_type(self) -> None:
        class Sealed(Tag):
            def __del__(agent) -> None:
                pass

        class Silent(Tag):
            @Delete
            def __del__(agent): ...

        first, second = self.Door(), self.Door()
        Sealed(first)
        Silent(second)
        Sealed(second)

        self.assertIs(type(first), type(second))

    def test_agent_del_reads_the_finalizer_with_secrets_too(self) -> None:
        class Vaulted(Tag):
            @Secret
            @Record
            def code(agent) -> str:
                return "1234"

            def __del__(agent) -> None:
                pass

        door = self.Door()
        Vaulted(door)

        self.assertIs(door.__del__.__func__, type(door).__del__)
        self.assertNotIn("__del__", vars(door))

    def test_rip_on_a_finalizer_is_refused(self) -> None:
        class Keeper(Tag):
            @Rip
            def __del__(agent) -> None:
                pass

        with self.assertRaises(TagDeclarationError):
            Keeper(Agent())

    def test_a_host_that_subclasses_tagged_gets_its_teardowns(self) -> None:
        from TopKit import Tagged

        log = self.log

        class Marked(Tagged):
            def __del__(self) -> None:
                log.append("host")

        self.assertEqual(self.delete(self.Guard, host=Marked), ["teardown", "host"])

    def test_the_finalizer_is_what_agent_del_reads(self) -> None:
        class Sealed(Tag):
            def __del__(agent) -> None:
                pass

        class Silent(Tag):
            @Delete
            def __del__(agent): ...

        for tags in ((self.Guard,), (Sealed,), (Silent,)):
            door = self.Door()

            for tag in tags:
                tag(door)

            self.assertIs(door.__del__.__func__, type(door).__del__)   # Python's to call, one meaning

    def test_a_layer_is_sticky_after_its_tag_leaves(self) -> None:
        log = self.log

        class Sealed(Tag):
            def __del__(agent) -> None:
                log.append("sealed")

        door = self.Door()
        Sealed(door)
        del Sealed[door]
        del door
        gc.collect()

        self.assertEqual(log, ["sealed"])

    def test_a_layers_error_is_reported_like_any_finalizers(self) -> None:
        import sys

        reported: list[BaseException] = []

        class Cracked(Tag):
            def __del__(agent) -> None:
                raise ValueError("cracked")

        hook = sys.unraisablehook
        sys.unraisablehook = lambda raised: reported.append(raised.exc_value)

        try:
            self.delete(self.Guard, Cracked)
        finally:
            sys.unraisablehook = hook

        self.assertEqual(self.log, ["teardown"])
        self.assertEqual([type(error) for error in reported], [ValueError])

    def test_layers_do_not_split_the_runtime_types(self) -> None:
        class Sealed(Tag):
            def __del__(agent) -> None:
                pass

        class Warded(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                underlay()

        class Silent(Tag):
            @Delete
            def __del__(agent): ...

        first, second, third = self.Door(), self.Door(), self.Door()
        Sealed(first)
        Warded(second)
        Silent(third)

        self.assertIs(type(first), type(second))
        self.assertIs(type(first), type(third))

    def test_a_teardown_and_a_layer_call_the_agents_actions_in_a_collected_cycle(self) -> None:
        log = self.log
        freed: list[bool] = []

        class Rung(Tag):
            def Ring(agent) -> str:
                return "ring"

            @Rip
            def Leave(agent) -> None:
                log.append("teardown " + agent.Ring())

            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("layer " + agent.Ring())
                underlay()

        def Make() -> weakref.ref:
            bell = self.Door()
            Rung(bell)
            bell.me = bell                     # a cycle: Python clears its weak references first

            return weakref.ref(bell, lambda _: freed.append(True))

        reference = Make()
        gc.collect()

        self.assertEqual(log, ["teardown ring", "layer ring", "host"])
        self.assertEqual(freed, [True])
        self.assertIsNone(reference())
        self.assertEqual(gc.garbage, [])
        self.assertEqual(self.alive(), [])     # Python cleared the weak reference first: asked of the heap, nothing was resurrected

    def test_a_secret_action_is_callable_from_a_teardown_in_a_cycle(self) -> None:
        log = self.log

        class Whisperer(Tag):
            @Secret
            def Whisper(agent) -> str:
                return "hush"

            def Relay(agent) -> str:
                return agent.Whisper()

            @Rip
            def Leave(agent) -> None:
                log.append("teardown " + agent.Relay() + " " + agent.Whisper())

            def __del__(agent) -> None:
                log.append("layer " + agent.Relay())

        def Make() -> None:
            bell = self.Door()
            Whisperer(bell)
            bell.me = bell

        Make()
        gc.collect()

        self.assertEqual(log, ["teardown hush hush", "layer hush"])
        self.assertEqual(self.alive(), [])     # the composing binding resurrects nothing either

    def test_the_re_tie_ends_with_the_finalizer(self) -> None:
        log = self.log

        class Keeper:
            """Holds an Action taken in a teardown; freed with the Agent,
            once the collection clears it, after its finalizer ran."""

            def __init__(self, action) -> None:
                self.action = action

            def __del__(self) -> None:
                try:
                    log.append(("answered", self.action()))
                except ReferenceError:
                    log.append("ReferenceError")

        class Rung(Tag):
            def Ring(agent) -> str:
                return "ring"

            @Rip
            def Leave(agent) -> None:
                agent.keeper = Keeper(agent.Ring)

        class Hushed(Tag):
            @Secret
            def Hush(agent) -> str:
                return "hush"

            def Ring(agent) -> str:
                return agent.Hush()

            @Rip
            def Leave(agent) -> None:
                agent.keeper = Keeper(agent.Ring)

        for kind in (Rung, Hushed):                  # a plain binding, and a composing one
            def Make() -> None:
                bell = self.Door()
                kind(bell)
                bell.me = bell

            log.clear()
            Make()
            gc.collect()

            self.assertEqual(log, ["host", "ReferenceError"], kind.__name__)   # the Agent is gone, as before the re-tie

    def test_an_action_bound_during_the_finalizer_ends_with_it(self) -> None:
        log = self.log

        class Keeper:
            def __init__(self, action) -> None:
                self.action = action

            def __del__(self) -> None:
                try:
                    log.append(("answered", self.action()))
                except ReferenceError:
                    log.append("ReferenceError")

        class Later(Tag):
            def Ping(agent) -> str:
                return "ping"

        class Hush(Tag):
            @Secret
            def Quiet(agent) -> str:
                return "quiet"

        def Tagged_Then_Kept(agent) -> None:     # a fresh binding
            Later(agent)
            agent.keeper = Keeper(agent.Ping)

        def Hushed_Then_Kept(agent) -> None:     # every Action bound again, composing
            Hush(agent)
            agent.keeper = Keeper(agent.Ring)

        def Kept_Then_Hushed(agent) -> None:     # a re-tied binding, then replaced
            agent.keeper = Keeper(agent.Ring)
            Hush(agent)

        for then in (Tagged_Then_Kept, Hushed_Then_Kept, Kept_Then_Hushed):
            class Rung(Tag):
                def Ring(agent) -> str:
                    return "ring"

                @Rip
                def Leave(agent) -> None:
                    then(agent)

            def Make() -> None:
                bell = self.Door()
                Rung(bell)
                bell.me = bell

            log.clear()
            Make()
            gc.collect()

            self.assertEqual(log, ["host", "ReferenceError"], then.__name__)   # not an Agent the collection cleared
            self.assertEqual(self.alive(), [], then.__name__)

        class Sealed(Tag):                        # no bound Action at all: only a Layer
            @Underlay
            def __del__(agent, underlay) -> None:
                Tagged_Then_Kept(agent)
                underlay()

        def Make() -> None:
            bell = self.Door()
            Sealed(bell)
            bell.me = bell

        log.clear()
        Make()
        gc.collect()

        self.assertEqual(log, ["host", "ReferenceError"], "a Layer")
        self.assertEqual(self.alive(), [], "a Layer")

    def test_actions_answer_in_a_cycle_where_another_finalizer_made_a_weak_reference(self) -> None:
        log = self.log
        references: list = []

        class Watcher:
            def __del__(self) -> None:
                references.append(weakref.ref(self.bell))   # the bell has a weak reference again

        class Rung(Tag):
            def Ring(agent) -> str:
                return "ring"

            @Rip
            def Leave(agent) -> None:
                try:
                    log.append(agent.Ring())
                except ReferenceError:
                    log.append("ReferenceError")

        for watcher_first in (False, True):   # the collection finalizes in no promised order: try both
            def Make() -> None:
                if watcher_first:
                    watcher = Watcher()
                    bell = self.Door()
                else:
                    bell = self.Door()
                    watcher = Watcher()

                Rung(bell)
                watcher.bell = bell
                bell.watcher = watcher

            log.clear()
            Make()
            gc.collect()

            self.assertEqual(log, ["ring", "host"], watcher_first)
            self.assertEqual(self.alive(), [], watcher_first)

    def test_another_agents_action_stored_under_an_actions_name_is_not_re_tied(self) -> None:
        log = self.log

        class Chimed(Tag):
            def Chime(agent) -> str:
                return "chime of " + agent.name

        class Rung(Tag):
            def Ring(agent) -> str:
                return "ring of " + agent.name

            @Rip
            def Leave(agent) -> None:
                try:
                    log.append(agent.Ring())
                except ReferenceError:
                    log.append("ReferenceError")

        def Make() -> None:
            bell = self.Door()
            bell.name = "bell"
            Rung(bell)
            other = self.Door()
            other.name = "other"
            Chimed(other)
            bell.Ring = other.Chime            # the program's choice: another Agent's Action
            bell.other = other
            other.bell = bell                  # both in one cycle

        Make()
        gc.collect()

        self.assertIn("ReferenceError", log)   # its Agent is gone: never run on the bell
        self.assertNotIn("chime of bell", log)

    def test_another_agents_binding_of_the_same_action_is_not_re_tied(self) -> None:
        log = self.log

        class Rung(Tag):
            def Ring(agent) -> str:
                return "ring of " + agent.name

            def Chime(agent) -> str:
                return "chime of " + agent.name

            @Rip
            def Hush(agent) -> None:
                try:
                    log.append((agent.name, agent.Ring()))
                except ReferenceError:
                    log.append((agent.name, "ReferenceError"))

        def Pair(cycle: bool) -> tuple:
            bell, other = self.Door(), self.Door()
            bell.name, other.name = "bell", "other"
            Rung(bell)
            Rung(other)
            bell.Ring = other.Ring             # the same Action, bound to the other Agent

            if cycle:
                bell.other = other
                other.bell = bell

            return bell, other

        for cycle in (False, True):
            log.clear()
            bell, other = Pair(cycle)

            if cycle:
                del bell, other
                gc.collect()
            else:
                del other                      # its binding on the bell now answers nobody
                del bell

            self.assertIn(("bell", "ReferenceError"), log, cycle)   # never the bell's own Ring
            self.assertNotIn(("bell", "ring of bell"), log, cycle)

    def test_another_agents_binding_does_not_untie_a_kept_agent_s_actions(self) -> None:
        saved: list = []

        class Rung(Tag):
            def Ring(agent) -> str:
                return "ring of " + agent.name

            def Chime(agent) -> str:
                return "chime of " + agent.name

        class Kept(Tag):
            @Rip
            def Save(agent) -> None:
                saved.append(agent)            # the program keeps the Agent past its deletion

        bell, other = self.Door(), self.Door()
        bell.name, other.name = "bell", "other"
        Rung(bell)
        Rung(other)
        Kept(bell)
        bell.Ring = other.Ring
        del other
        del bell

        self.assertEqual(saved[0].Chime(), "chime of bell")   # its own Actions still answer it
        saved.clear()

    def test_an_agent_its_teardown_keeps_and_tags_again_keeps_every_action(self) -> None:
        saved: list = []

        class Later(Tag):
            def Ping(agent) -> str:
                return "ping"

        class Saver(Tag):
            def Ring(agent) -> str:
                return "ring"

            @Rip
            def Save(agent) -> None:
                saved.append(agent)            # kept by the program, at a plain del
                Later(agent)

        door = self.Door()
        Saver(door)
        del door
        kept = saved.pop()

        self.assertEqual((kept.Ring(), kept.Ping()), ("ring", "ping"))
        self.assertIn(kept, Later)

    def test_a_layer_calls_an_action_at_a_plain_del_and_the_agent_is_freed(self) -> None:
        log = self.log

        class Rung(Tag):
            def Ring(agent) -> str:
                return "ring"

            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("layer " + agent.Ring())
                underlay()

        bell = self.Door()
        Rung(bell)
        reference = weakref.ref(bell)
        del bell
        gc.collect()

        self.assertEqual(log, ["layer ring", "host"])
        self.assertIsNone(reference())

    def test_a_teardown_at_deletion_still_sees_the_agent_as_a_member(self) -> None:
        log = self.log

        class Watchful(Tag):
            @Rip
            def Leave(agent) -> None:
                log.append(("in", agent in Watchful, "walked", any(a is agent for a in Watchful[:])))

        door = self.Door()
        Watchful(door)
        del door
        gc.collect()

        self.assertEqual(log, [("in", True, "walked", True), "host"])   # a member, found by a walk

        log.clear()
        other = self.Door()
        Watchful(other)
        del Watchful[other]                                              # a Rip: membership ended first

        self.assertEqual(log, [("in", False, "walked", False)])

        log.clear()

        def Make() -> None:
            bell = self.Door()
            Watchful(bell)
            bell.me = bell

        Make()
        gc.collect()                                                     # a collected cycle: still a member,
                                                                         # but Python cleared the Field's weak
        self.assertEqual(log, [("in", True, "walked", False), "host"])  # reference before the finalizer

    def test_a_failed_teardown_at_deletion_keeps_the_agent_and_is_reported(self) -> None:
        log = self.log

        class Stubborn(Tag):
            @Rip
            def Hold(agent) -> None:
                log.append("hold")
                raise RuntimeError("will not let go")

        class Warded(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("layer")
                underlay()

        def Keep(raised) -> tuple:
            log.append("reported")

            return type(raised.exc_value), str(raised.exc_value), type(raised.exc_value.__cause__)

        reports = self.reported(lambda: self.delete(self.Guard, Stubborn, Warded), Keep)

        self.assertEqual(log, ["hold", "teardown", "reported", "reported"])   # every teardown ran; no Layer
        self.assertEqual(reports, [
                (RuntimeError, "will not let go", type(None)),               # the teardown, as ruling (C) reports it
                (TagCompositionError,                                        # then the Agent kept, as (E) rules
                 "teardown failed at the deletion of Door: Hold of Stubborn; Door was kept,"
                 " still a member of its Tags, in the safehouse, Stubborn[...]",
                 RuntimeError),
                ])
        kept = list(Tag[...])

        self.assertEqual(len(kept), 1)
        self.assertTrue(kept[0] in self.Guard and kept[0] in Stubborn and kept[0] in Warded)

    def test_every_failed_teardown_is_named_in_one_report(self) -> None:
        log = self.log

        class Stubborn(Tag):
            @Rip
            def Hold(agent) -> None:
                log.append("hold")
                raise RuntimeError("will not let go")

            @Rip
            def Cling(agent) -> None:
                log.append("cling")
                raise ValueError("clings")

        class Sealed(Tag):
            def __del__(agent) -> None:
                log.append("sealed")

        reports = self.reported(
                lambda: self.delete(Stubborn, Sealed),
                lambda raised: raised.err_msg if type(raised.exc_value) is not TagCompositionError
                else str(raised.exc_value),
                )
        gc.collect()

        self.assertEqual(log, ["hold", "cling"])               # every teardown ran, once; no Layer
        self.assertEqual(reports, [
                "Exception ignored in teardown Hold of Stubborn, deleting Door",
                "Exception ignored in teardown Cling of Stubborn, deleting Door",
                "teardown failed at the deletion of Door: Hold of Stubborn, Cling of Stubborn;"
                " Door was kept, still a member of its Tags, in the safehouse, Stubborn[...]",
                ])

    def test_a_kept_agent_is_freed_at_once_when_triage_lets_it_go(self) -> None:
        class Stubborn(Tag):
            @Rip
            def Hold(agent) -> None:
                raise RuntimeError("will not let go")

        door = self.Door()
        Stubborn(door)
        reference = weakref.ref(door)
        gc.disable()   # a refcount death must free it at once: no collection may help

        try:
            def Delete() -> None:
                nonlocal door
                del door

            reports = self.reported(Delete)

            self.assertEqual(reports, ["RuntimeError", "TagCompositionError"])
            self.assertIs(reference(), list(Stubborn[...])[0])   # kept, and only by the safehouse:

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                del Tag[...]

            self.assertIsNone(reference())                       # no report's traceback held it
            self.assertEqual(list(Stubborn[:]), [])
            self.assertEqual(self.log, [])                       # its finalizer ran once, and kept it
        finally:
            gc.enable()

    def test_an_interrupted_teardown_does_not_keep_the_agent_alive(self) -> None:
        class Impatient(Tag):
            @Rip
            def Leave(agent) -> None:
                raise KeyboardInterrupt

        class Cracked(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                underlay()
                raise ValueError("cracked")

        for tags, reports in (
                ((Impatient,), ["KeyboardInterrupt"]),
                ((Impatient, Cracked), ["ValueError", "KeyboardInterrupt"]),   # the Layer's error too
                ):
            self.log.clear()
            door = self.Door()

            for tag in tags:
                tag(door)

            reference = weakref.ref(door)
            gc.disable()   # a refcount death must free it at once: no collection may help

            try:
                def Delete() -> None:
                    nonlocal door
                    del door

                self.assertEqual(self.reported(Delete), reports)
                self.assertIsNone(reference())      # each traceback held the finalizer's frame
                self.assertEqual(self.log, ["host"])
            finally:
                gc.enable()

    def test_a_hook_that_raises_stops_no_report_and_no_interruption(self) -> None:
        import contextlib
        import io
        import sys

        log = self.log

        class Impatient(Tag):
            @Rip
            def Leave(agent) -> None:
                log.append("impatient")
                raise KeyboardInterrupt

        class Stubborn(Tag):
            @Rip
            def Hold(agent) -> None:
                log.append("hold")
                raise RuntimeError("will not let go")

            @Rip
            def Cling(agent) -> None:
                log.append("cling")
                raise ValueError("clings")

        def Strict(raised) -> None:
            log.append("reported " + type(raised.exc_value).__name__)
            raise RuntimeError("strict hook")

        hook = sys.unraisablehook
        sys.unraisablehook = Strict
        printed = io.StringIO()

        try:
            with contextlib.redirect_stderr(printed):
                self.delete(Impatient, Stubborn)   # reverse order: Stubborn's first
        finally:
            sys.unraisablehook = hook

        self.assertEqual(log, [
                "hold", "cling", "impatient",
                "reported RuntimeError", "reported ValueError",
                "reported TagCompositionError", "reported KeyboardInterrupt",
                ])                                   # each report made, the Agent kept, the interruption last
        self.assertEqual(printed.getvalue().count("Exception ignored in sys.unraisablehook"), 4)

    def test_a_hook_that_raises_an_interruption_stops_no_report(self) -> None:
        import contextlib
        import io
        import sys

        log = self.log

        class Impatient(Tag):
            @Rip
            def Leave(agent) -> None:
                raise KeyboardInterrupt

        class Stubborn(Tag):
            @Rip
            def Hold(agent) -> None:
                raise RuntimeError("will not let go")

        def Strict(raised) -> None:
            log.append("reported " + type(raised.exc_value).__name__)
            raise KeyboardInterrupt            # an interruption from the hook itself

        class Broken:
            def write(self, text: str) -> None:
                raise OSError("stderr is gone")

            def flush(self) -> None:
                raise OSError("stderr is gone")

        for stderr in (io.StringIO(), Broken()):   # Python's default hook reports it, or fails too
            log.clear()
            hook = sys.unraisablehook
            sys.unraisablehook = Strict

            try:
                with contextlib.redirect_stderr(stderr):
                    self.delete(Impatient, Stubborn)
            finally:
                sys.unraisablehook = hook

            self.assertEqual(
                    log,
                    ["reported RuntimeError", "reported TagCompositionError", "reported KeyboardInterrupt"],
                    type(stderr).__name__,
                    )

    def test_the_kit_imports_with_no_hook_set_and_leaves_it_unset(self) -> None:
        lines, stderr = Run_Program("""
import sys
del sys.unraisablehook
import TopKit
print("imported", hasattr(sys, "unraisablehook"))
""")

        self.assertEqual(lines, ["imported False"], stderr)

    def test_with_no_hook_set_python_s_default_reports(self) -> None:
        import contextlib
        import io
        import sys

        class Stubborn(Tag):
            @Rip
            def Hold(agent) -> None:
                raise RuntimeError("will not let go")

        class Impatient(Tag):
            @Rip
            def Leave(agent) -> None:
                raise KeyboardInterrupt

        hook = sys.unraisablehook

        for unset in ("None", "deleted"):
            for tags, said in (
                    ((Stubborn,), "Exception ignored"),                        # raised: Python reports it
                    ((Impatient, Stubborn), "Exception ignored deleting Door"),  # the kit reports it, then the interruption
                    ):
                printed = io.StringIO()

                try:
                    if unset == "None":
                        sys.unraisablehook = None  # Python's own reports go to its default hook then
                    else:
                        del sys.unraisablehook

                    with contextlib.redirect_stderr(printed):
                        self.delete(*tags)
                finally:
                    sys.unraisablehook = hook

                self.assertIn(said, printed.getvalue(), unset)
                self.assertIn("Exception ignored in teardown Hold of Stubborn, deleting Door", printed.getvalue(), unset)
                self.assertIn(
                        "TagCompositionError: teardown failed at the deletion of Door: Hold of Stubborn;",
                        printed.getvalue(),
                        unset,
                        )
                self.assertIn("RuntimeError: will not let go", printed.getvalue(), unset)
                self.assertNotIn("sys.unraisablehook", printed.getvalue(), unset)

    def test_a_deletion_before_the_interpreter_finalizes_is_an_ordinary_one(self) -> None:
        program = """
import atexit, sys
registry = []

def Release():                     # registered before TopKit: runs after the At_Exit pass
    print("finalizing", sys.is_finalizing(), flush=True)
    registry.clear()

atexit.register(Release)

from TopKit import Tag, Rip

class Door: pass

class Stubborn(Tag):
    @Rip
    def Hold(agent):
        print("hold", flush=True)
        raise RuntimeError("will not let go")

door = Door(); Stubborn(door); registry.append(door); del door
print("end", flush=True)
"""
        lines, stderr = Run_Program(program)

        self.assertEqual(lines, ["end", "finalizing False", "hold"])   # its teardowns run, as at any del
        self.assertIn("teardown failed at the deletion of Door: Hold of Stubborn; Door was kept", stderr)

    def test_a_teardown_that_ran_on_a_rip_has_nothing_left_to_report_at_deletion(self) -> None:
        log = self.log

        class Stubborn(Tag):
            @Rip
            def Hold(agent) -> None:
                log.append("hold")

        door = self.Door()
        Stubborn(door)
        del Stubborn[door]

        def Delete() -> None:
            nonlocal door
            del door
            gc.collect()

        self.assertEqual(self.reported(Delete), [])    # at most once: nothing to run, nothing to report
        self.assertEqual(log, ["hold", "host"])

    def test_failures_gathered_before_an_interruption_are_reported_before_it(self) -> None:
        log = self.log

        class Impatient(Tag):
            @Rip
            def Leave(agent) -> None:
                log.append("impatient")
                raise KeyboardInterrupt

        class Stubborn(Tag):
            @Rip
            def Hold(agent) -> None:
                log.append("hold")
                raise RuntimeError("will not let go")

        reported = self.reported(lambda: self.delete(Impatient, Stubborn))   # reverse order: Hold first

        self.assertEqual(log, ["hold", "impatient"])                         # kept: no Layer
        self.assertEqual(reported, ["RuntimeError", "TagCompositionError", "KeyboardInterrupt"])
        self.assertEqual(len(Stubborn[...]), 1)

    def test_a_failed_teardown_in_the_exit_pass_is_reported(self) -> None:
        program = """
from TopKit import Tag, Rip, At_Exit

class Door:
    def __init__(self, name): self.name = name

class Stubborn(Tag):
    @Rip
    def Hold(agent):
        print(agent.name, "hold", flush=True)
        raise RuntimeError(agent.name + " will not let go")

class Guard(Tag):
    @Rip
    def Leave(agent):
        member = agent in Guard and any(a is agent for a in Guard[:])
        print(agent.name, "teardown", "as a member" if member else "as a stranger", flush=True)

first = Door("first"); Stubborn(first); At_Exit(first)
second = Door("second"); Guard(second); At_Exit(second)
print("end", flush=True)
"""
        lines, stderr = Run_Program(program)

        self.assertEqual(lines, ["end", "first hold", "second teardown as a member"])   # once, and on
        self.assertIn("Exception ignored in teardown Hold of Stubborn, in the At_Exit pass of Door", stderr)
        self.assertIn("RuntimeError: first will not let go", stderr)
        self.assertEqual(stderr.count("Exception ignored"), 1)

    def test_a_failed_teardown_in_the_exit_pass_rolls_that_agent_back(self) -> None:
        program = """
import atexit

def After():                       # registered before TopKit: runs after the At_Exit pass
    print("first", first.on_duty, first in Guard, first in Stubborn, flush=True)
    print("second", second.on_duty, flush=True)

atexit.register(After)

from TopKit import Tag, Rip, At_Exit

class Door:
    def __init__(self, name): self.name = name; self.on_duty = True

class Guard(Tag):
    @Rip
    def Leave(agent):
        agent.on_duty = False

class Stubborn(Tag):
    @Rip
    def Hold(agent):
        raise RuntimeError(agent.name + " will not let go")

first = Door("first"); Guard(first); Stubborn(first); At_Exit(first)
second = Door("second"); Guard(second); At_Exit(second)
"""
        lines, stderr = Run_Program(program)

        self.assertEqual(lines, ["first True True True", "second False"])   # rolled back; the pass went on
        self.assertIn("Exception ignored in teardown Hold of Stubborn, in the At_Exit pass of Door", stderr)
        self.assertEqual(stderr.count("Exception ignored"), 1)

    def test_a_hook_that_raises_stops_nothing_in_the_exit_pass(self) -> None:
        program = """
import sys
from TopKit import Tag, Rip, At_Exit

class Door:
    def __init__(self, name): self.name = name

class Stubborn(Tag):
    @Rip
    def Hold(agent):
        print(agent.name, "hold", flush=True)
        raise RuntimeError(agent.name + " will not let go")

class Guard(Tag):
    @Rip
    def Leave(agent): print(agent.name, "teardown", flush=True)

def Strict(report): raise RuntimeError("strict hook")

sys.unraisablehook = Strict
first = Door("first"); Guard(first); At_Exit(first)
second = Door("second"); Stubborn(second); At_Exit(second)
third = Door("third"); Guard(third); At_Exit(third)
print("end", flush=True)
"""
        lines, stderr = Run_Program(program)

        self.assertEqual(lines, ["end", "first teardown", "second hold", "third teardown"])   # the pass goes on
        self.assertIn("Exception ignored in sys.unraisablehook", stderr)   # as Python reports a hook's own error
        self.assertIn("RuntimeError: strict hook", stderr)

    def test_a_failure_in_the_exit_pass_is_reported_before_an_interruption(self) -> None:
        program = """
from TopKit import Tag, Rip, At_Exit

class Door:
    def __init__(self, name): self.name = name

class Halting(Tag):
    @Rip
    def Halt(agent):
        print(agent.name, "halt", flush=True)
        raise KeyboardInterrupt

class Stubborn(Tag):
    @Rip
    def Hold(agent):
        print(agent.name, "hold", flush=True)
        raise RuntimeError(agent.name + " will not let go")

door = Door("door"); Halting(door); Stubborn(door); At_Exit(door)   # reverse order: Hold first
print("end", flush=True)
"""
        lines, stderr = Run_Program(program)
        report = stderr.find("Exception ignored in teardown Hold of Stubborn, in the At_Exit pass of Door")

        self.assertEqual(lines, ["end", "door hold", "door halt"])
        self.assertNotEqual(report, -1)
        self.assertIn("RuntimeError: door will not let go", stderr)
        self.assertLess(report, stderr.index("KeyboardInterrupt"))   # the failure first, then the interruption

    def test_actions_answer_a_layer_and_the_exit_pass_at_program_end(self) -> None:
        program = """
import os
from TopKit import Tag, Rip, Underlay, At_Exit

class Bell:
    def __init__(self, name): self.name = name

class Rung(Tag):
    def Ring(agent): return agent.name + " rings"

    @Rip
    def Leave(agent, write=os.write, kind=type, base=BaseException):
        try: write(1, ("teardown: " + agent.Ring() + "\\n").encode())
        except base as error: write(1, ("teardown FAILED " + kind(error).__name__ + "\\n").encode())

    @Underlay
    def __del__(agent, underlay, write=os.write, kind=type, base=BaseException):
        try: write(1, ("layer: " + agent.Ring() + "\\n").encode())
        except base as error: write(1, ("layer FAILED " + kind(error).__name__ + "\\n").encode())
        underlay()

held = Bell("held"); Rung(held)       # in a cycle through Rung's functions: freed at exit by a collection
listed = Bell("listed"); Rung(listed); At_Exit(listed)
print("end", flush=True)              # the finalizers write with os.write, past the buffer
"""
        lines, stderr = Run_Program(program)

        self.assertEqual(lines[0], "end")
        self.assertIn("teardown: listed rings", lines)   # the At_Exit pass
        self.assertIn("layer: held rings", lines)        # the Layer, at program end
        self.assertIn("layer: listed rings", lines)
        self.assertEqual([line for line in lines if "FAILED" in line], [])
        self.assertEqual(stderr, "")

    def test_at_exit_only_the_layers_run(self) -> None:
        program = """
from TopKit import Tag, Rip, At_Exit, Underlay

class Door:
    def __init__(self, name): self.name = name
    def __del__(self): print(self.name, "host")

class Guard(Tag):
    @Rip
    def Leave(agent): print(agent.name, "teardown")

class Warded(Tag):
    @Underlay
    def __del__(agent, underlay):
        print(agent.name, "warded")
        underlay()

alive = Door("alive"); Guard(alive); Warded(alive)
listed = Door("listed"); Guard(listed); At_Exit(listed)
print("end")
"""

        late = """
import os, sys
from TopKit import Tag, Rip, Underlay

class Door:
    def __init__(self, name): self.name = name
    def __del__(self, write=os.write): write(1, (self.name + " host\\n").encode())

class Guard(Tag):
    @Rip
    def Leave(agent): print(agent.name, "teardown")

class Warded(Tag):
    @Underlay
    def __del__(agent, underlay, write=os.write):
        write(1, (agent.name + " warded\\n").encode())
        underlay()

class Rung(Tag):
    def Ring(agent): return agent.name + " rings"

    @Underlay
    def __del__(agent, underlay, write=os.write, base=BaseException):
        try: write(1, ("layer: " + agent.Ring() + "\\n").encode())
        except base: write(1, b"layer FAILED\\n")
        underlay()

import TopKit.access, TopKit.lifecycle, TopKit.overlay, TopKit.state

KIT = (TopKit.access, TopKit.lifecycle, TopKit.overlay, TopKit.state)

def Hook(kind, value, trace, kit=KIT): sys.__excepthook__(kind, value, trace)

sys.excepthook = Hook                 # keeps this module, and the kit's modules, alive
                                      # until sys itself goes: their globals are wiped first

class Closer:
    def __call__(self, write=os.write): write(1, b"closer host\\n")

class Called:
    __del__ = Closer()                # a finalizer that is not a descriptor

guarded = Door("guarded"); Guard(guarded)
warded = Door("warded"); Guard(warded); Warded(warded)
called = Called(); Guard(called)
rung = Door("rung"); Rung(rung)       # in a cycle through Rung's functions: freed late, by a collection
plain = type(guarded).__new__(type(guarded))   # built from an Agent's runtime type, never tagged
plain.name = "plain"
print("end")
"""
        lines, stderr = Run_Program(program)

        self.assertEqual(lines[0], "end")
        self.assertEqual(lines.index("listed teardown"), 1)   # At_Exit: while Python is whole
        self.assertNotIn("alive teardown", lines)             # teardowns at exit are opt-in
        self.assertLess(lines.index("alive warded"), lines.index("alive host"))
        self.assertIn("listed host", lines)
        self.assertEqual(stderr, "")

        lines, stderr = Run_Program(late)

        self.assertEqual(lines[0], "end")
        self.assertIn("guarded host", lines)                  # even after the kit's modules are gone
        self.assertIn("closer host", lines)
        self.assertIn("plain host", lines)                    # an untagged object of a runtime type, too
        self.assertLess(lines.index("warded warded"), lines.index("warded host"))
        self.assertNotIn("guarded teardown", lines)
        self.assertIn("layer: rung rings", lines)             # a plain Action answers there too
        self.assertLess(lines.index("layer: rung rings"), lines.index("rung host"))


class SafehouseTests(unittest.TestCase):
    """STEP-SPEC-18, amendment E: a teardown that fails at deletion blocks
    the deletion. The Agent is rolled back to what it was before the
    deletion's teardowns, still a member of its Tags, and kept in the
    safehouse, ``Tag[...]``, by the Tags whose teardown failed; the
    finalizer raises the Composition Failure, which Python reports."""

    def setUp(self) -> None:
        import sys

        self.log: list[str] = []
        self.reports: list = []
        self.stuck = [True]
        log, stuck = self.log, self.stuck
        hook = sys.unraisablehook
        sys.unraisablehook = lambda raised: self.reports.append((type(raised.exc_value), str(raised.exc_value)))
        self.addCleanup(setattr, sys, "unraisablehook", hook)
        self.addCleanup(Triage)

        class Door:
            def __init__(self, name: str = "door") -> None:
                self.name = name

            def __del__(self) -> None:
                log.append("host " + self.name)

        class Guard(Tag):
            def Ping(agent) -> str:
                return "ping " + agent.name

            @Rip
            def Leave(agent) -> None:
                log.append("leave " + agent.name)
                agent.left = True

        class Cached(Tag):
            @Rip
            def Clear(agent) -> None:
                log.append("clear " + agent.name)

                if stuck:
                    raise RuntimeError("the cache will not clear")

        class Hot(Cached):                 # a Shape: one of Cached's departments
            pass

        class Other(Tag):
            @Rip
            def Close(agent) -> None:
                if stuck:
                    raise OSError("will not close")

        self.Door, self.Guard, self.Cached, self.Hot, self.Other = Door, Guard, Cached, Hot, Other

    def test_a_plain_del_whose_teardown_fails_keeps_the_agent(self) -> None:
        door = self.Door("d")
        bystander = self.Door("b")
        self.Guard(door)
        self.Guard(bystander)
        self.Cached(door)
        reference = weakref.ref(door)
        del door

        kept = reference()

        self.assertIsNotNone(kept)                                       # not destroyed
        self.assertEqual(self.log, ["clear d", "leave d"])               # every teardown ran; no Layer
        self.assertIn(kept, self.Cached[...])
        self.assertIn(kept, Tag[...])
        self.assertTrue(kept in self.Cached and kept in self.Guard)       # still a member
        self.assertEqual(list(self.Guard[:]), [kept, bystander])          # in its place in the Field
        self.assertFalse(hasattr(kept, "left"))                           # what the teardowns did is undone
        self.assertEqual(kept.Ping(), "ping d")
        self.assertEqual(
                [kind for kind, _message in self.reports],
                [RuntimeError, TagCompositionError],
                )
        self.assertEqual(
                self.reports[1][1],
                "teardown failed at the deletion of Door: Clear of Cached; Door was kept,"
                " still a member of its Tags, in the safehouse, Cached[...]",
                )

    def test_a_collected_cycle_whose_teardown_fails_is_kept(self) -> None:
        def Make() -> None:
            door = self.Door("c")
            self.Guard(door)
            self.Cached(door)
            door.me = door                                               # a cycle

        Make()
        gc.collect()

        kept = list(Tag[...])

        self.assertEqual(len(kept), 1)
        self.assertTrue(kept[0] in self.Cached and kept[0] in self.Guard)
        self.assertEqual(list(self.Guard[:]), kept)                      # back in its Field
        self.assertEqual(kept[0].Ping(), "ping c")                       # its Actions answer the live Agent
        self.assertEqual(self.reports[-1][0], TagCompositionError)
        self.assertNotIn("host c", self.log)

    def test_repaired_and_ripped_a_kept_agent_leaves_and_is_freed(self) -> None:
        door = self.Door("d")
        self.Cached(door)
        reference = weakref.ref(door)
        del door

        self.assertEqual(len(self.Cached[...]), 1)

        kept = reference()
        self.stuck.clear()                                               # repaired
        del self.Cached[kept]

        self.assertNotIn(kept, Tag[...])                                 # out of the safehouse
        self.assertEqual(self.log, ["clear d", "clear d"])

        del kept
        gc.collect()

        self.assertIsNone(reference())                                   # let go
        self.assertNotIn("host d", self.log)                            # Python runs a finalizer once per object

    def test_a_kept_agent_from_a_cycle_is_freed_after_its_rip(self) -> None:
        def Make() -> None:
            door = self.Door("c")
            self.Cached(door)
            door.me = door

        Make()
        gc.collect()
        kept = list(self.Cached[...])[0]
        reference = weakref.ref(kept)
        self.stuck.clear()
        del self.Cached[kept]
        del kept
        gc.collect()

        self.assertIsNone(reference())

    def test_a_teardown_that_keeps_failing_on_the_explicit_rip_stays_refused(self) -> None:
        door = self.Door("d")
        self.Cached(door)
        reference = weakref.ref(door)
        del door
        kept = reference()

        with self.assertRaises(TagCompositionError):
            del self.Cached[kept]

        self.assertIn(kept, self.Cached)
        self.assertIn(kept, self.Cached[...])                            # still kept

    def test_a_rip_of_another_tag_leaves_the_agent_kept(self) -> None:
        door = self.Door("d")
        self.Guard(door)
        self.Cached(door)
        reference = weakref.ref(door)
        del door
        kept = reference()
        del self.Guard[kept]                                             # not the Tag that keeps it

        self.assertIn(kept, Tag[...])

    def test_the_safehouse_is_organized_by_department(self) -> None:
        def Kept(*tags: type) -> object:
            door = self.Door("/".join(tag.__name__ for tag in tags))

            for tag in tags:
                tag(door)

            reference = weakref.ref(door)
            del door

            return reference()

        by_base = Kept(self.Cached)
        by_shape = Kept(self.Hot)                                        # Cached's teardown, on a Hot Agent
        by_other = Kept(self.Other)
        by_both = Kept(self.Cached, self.Other)

        class Hotter(self.Hot):
            @Rip
            def Melt(agent) -> None:
                raise RuntimeError("too hot")

        by_shape_only = Kept(Hotter)                                     # its own and its Base's teardowns fail

        self.assertEqual(list(Tag[...]), [by_base, by_shape, by_other, by_both, by_shape_only])
        self.assertEqual(list(self.Cached[...]), [by_base, by_shape, by_both, by_shape_only])
        self.assertEqual(list(self.Hot[...]), [by_shape_only])           # a branch lists its sub-branches only
        self.assertEqual(list(Hotter[...]), [by_shape_only])
        self.assertEqual(list(self.Other[...]), [by_other, by_both])
        self.assertEqual(list(self.Guard[...]), [])

    def test_the_safehouse_is_a_population_like_the_others(self) -> None:
        def Kept(*tags: type) -> object:
            door = self.Door("/".join(tag.__name__ for tag in tags))

            for tag in tags:
                tag(door)

            reference = weakref.ref(door)
            del door

            return reference()

        cached = Kept(self.Guard, self.Cached)
        other = Kept(self.Other)

        self.assertEqual(len(Tag[...]), 2)
        self.assertTrue(Tag[...])
        self.assertFalse(self.Guard[...])
        self.assertEqual(list(self.Cached[...] | self.Other[...]), [cached, other])
        self.assertEqual(list(Tag[...] - self.Cached[...]), [other])
        self.assertEqual(list(Tag[...] & self.Guard[:]), [cached])
        self.assertEqual(list(Tag[...] & self.Guard), [cached])          # a Tag in a seat: its sound population
        self.assertIn(cached, self.Guard)                                # and in its Tags' populations too
        self.assertIn(cached, list(self.Guard))
        self.assertNotIn(self.Door(), Tag[...])
        self.assertEqual(repr(self.Cached[...]), "<safehouse of Cached>")

    def test_the_other_keys_keep_their_meaning(self) -> None:
        door = self.Door()
        self.Guard(door)

        self.assertEqual(self.Guard[door].Ping(), "ping door")           # the view
        self.assertEqual(list(self.Guard[:]), [door])                    # the whole Field

        with self.assertRaises(TypeError):
            self.Guard[1:]

    def test_an_interrupted_deletion_whose_teardown_failed_is_kept_and_reported_first(self) -> None:
        import sys

        caught: list = []

        class Impatient(Tag):
            @Rip
            def Halt(agent) -> None:
                if self.stuck:
                    raise KeyboardInterrupt

        sys.unraisablehook = lambda raised: caught.append((raised.err_msg, type(raised.exc_value)))
        door = self.Door("d")
        Impatient(door)
        self.Cached(door)                                                # reverse order: Clear first
        reference = weakref.ref(door)
        del door

        self.assertEqual(caught, [
                ("Exception ignored in teardown Clear of Cached, deleting Door", RuntimeError),
                ("Exception ignored deleting Door", TagCompositionError),
                (caught[2][0], KeyboardInterrupt),                       # Python's own report, last
                ])
        self.assertIn(reference(), Tag[...])

    def test_a_finalizer_called_by_hand_raises_to_its_caller_and_keeps(self) -> None:
        door = self.Door("d")
        self.Cached(door)

        with self.assertRaises(TagCompositionError) as raised:
            door.__del__()

        self.assertIsInstance(raised.exception.__cause__, RuntimeError)
        self.assertIn(door, self.Cached[...])
        self.assertIn(door, self.Cached)

    def test_every_teardown_succeeding_keeps_nothing(self) -> None:
        self.stuck.clear()
        door = self.Door("d")
        self.Guard(door)
        self.Cached(door)
        reference = weakref.ref(door)
        del door

        def Make() -> None:
            other = self.Door("c")
            self.Cached(other)
            other.me = other

        Make()
        gc.collect()

        self.assertIsNone(reference())
        self.assertFalse(Tag[...])
        self.assertEqual([kept for kept in gc.get_objects() if isinstance(kept, self.Door)], [])   # the heap agrees
        self.assertEqual(self.reports, [])

    def test_at_program_end_nothing_is_kept_and_the_failure_is_reported(self) -> None:
        program = """
import atexit

def After():                       # registered before TopKit: runs after the At_Exit pass
    from TopKit import Tag
    print("kept", len(Tag[...]), "member", door in Stubborn, flush=True)

atexit.register(After)

from TopKit import Tag, Rip, At_Exit

class Door: pass

class Stubborn(Tag):
    @Rip
    def Hold(agent):
        raise RuntimeError("will not let go")

class Late(Tag):
    @Rip
    def Hold(agent):
        print("never at program end", flush=True)
        raise RuntimeError("never run")

door = Door(); Stubborn(door); At_Exit(door)
late = Door(); Late(late)           # left to program end: its teardowns do not run there
"""
        lines, stderr = Run_Program(program)

        self.assertEqual(lines, ["kept 0 member True"])
        self.assertIn("Exception ignored in teardown Hold of Stubborn, in the At_Exit pass of Door", stderr)
        self.assertNotIn("kept, still a member", stderr)
        self.assertEqual(stderr.count("Exception ignored"), 1)


class TriageTests(unittest.TestCase):
    """STEP-SPEC-18, amendment F: ``del Tag[...]`` is the last resort. Each
    Agent ``Tag[...]`` lists is Ripped from every Tag it carries, without
    running a teardown again, taken out of the safehouse and let go, with
    one TagTriageWarning naming it and the teardowns that never finished."""

    def setUp(self) -> None:
        import sys

        self.log: list[str] = []
        log = self.log
        hook = sys.unraisablehook
        sys.unraisablehook = lambda raised: None
        self.addCleanup(setattr, sys, "unraisablehook", hook)
        self.addCleanup(Triage)

        class Door:
            def __init__(self, name: str) -> None:
                self.name = name

        class Guard(Tag):
            @Rip
            def Leave(agent) -> None:
                log.append("leave " + agent.name)

        class Cached(Tag):
            @Rip
            def Clear(agent) -> None:
                log.append("clear " + agent.name)
                raise RuntimeError("the cache will not clear")

        class Hot(Cached):
            pass

        class Other(Tag):
            @Rip
            def Close(agent) -> None:
                log.append("close " + agent.name)
                raise OSError("will not close")

        self.Door, self.Guard, self.Cached, self.Hot, self.Other = Door, Guard, Cached, Hot, Other

    def kept(self, name: str, *tags: type) -> weakref.ref:
        door = self.Door(name)

        for tag in tags:
            tag(door)

        reference = weakref.ref(door)
        del door

        return reference

    def triage(self, house) -> list[str]:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            del house[...]

        self.assertTrue(all(warning.category is TagTriageWarning for warning in caught))

        return [str(warning.message) for warning in caught]

    def test_triage_of_the_root_empties_the_safehouse_and_frees_its_agents(self) -> None:
        first = self.kept("first", self.Guard, self.Cached)
        second = self.kept("second", self.Other)
        self.log.clear()

        warned = self.triage(Tag)
        gc.collect()

        self.assertFalse(Tag[...])
        self.assertIsNone(first())
        self.assertIsNone(second())
        self.assertEqual(self.log, [])                                   # no teardown ran again
        self.assertEqual(len(warned), 2)                                 # one per Agent
        self.assertRegex(warned[0], r"^triage let go of Door \(id 0x[0-9a-f]+\) without its teardowns:")
        self.assertTrue(warned[0].endswith(": Leave of Guard, Clear of Cached"))   # every one that never finished
        self.assertTrue(warned[1].endswith(": Close of Other"))

    def test_triage_of_a_tag_takes_its_whole_tree_and_nothing_else(self) -> None:
        log = self.log

        class Hotter(self.Hot):                                          # a Shape two levels down
            @Rip
            def Melt(agent) -> None:
                log.append("melt " + agent.name)
                raise RuntimeError("too hot")

        class Sealed(self.Other):                                        # a Shape of another department
            pass

        by_base = self.kept("base", self.Cached)
        by_shape = self.kept("shape", self.Hot)
        by_sub_shape = self.kept("sub-shape", Hotter)                   # kept by Hotter and by Cached
        by_other = self.kept("other", self.Other)
        by_other_shape = self.kept("other shape", Sealed)
        self.log.clear()

        warned = self.triage(self.Cached)
        gc.collect()

        self.assertEqual(len(warned), 3)
        self.assertTrue(warned[2].endswith(": Clear of Cached, Melt of Hotter"), warned[2])
        self.assertIsNone(by_base())
        self.assertIsNone(by_shape())
        self.assertIsNone(by_sub_shape())
        self.assertEqual(list(Tag[...]), [by_other(), by_other_shape()])   # the other department stays
        self.assertEqual(self.log, [])                                   # no teardown ran again

    def test_triage_of_a_shape_takes_only_its_own_branch(self) -> None:
        log = self.log

        class Hotter(self.Hot):
            @Rip
            def Melt(agent) -> None:
                log.append("melt " + agent.name)
                raise RuntimeError("too hot")

        by_base = self.kept("base", self.Cached)
        by_sub_shape = self.kept("sub-shape", Hotter)

        warned = self.triage(self.Hot)                                   # Hot's branch: Hotter's kept Agent
        gc.collect()

        self.assertEqual(len(warned), 1)
        self.assertIsNone(by_sub_shape())
        self.assertEqual(list(Tag[...]), [by_base()])                    # kept by Cached alone: not Hot's

    def test_an_agent_the_program_still_holds_lives_on_carrying_no_tag(self) -> None:
        self.kept("held", self.Guard, self.Hot)
        door = list(self.Cached[...])[0]                                 # the program holds it again
        self.log.clear()

        self.triage(Tag)

        self.assertEqual(Tags(door), ())                                 # no longer an Agent
        self.assertNotIn(door, self.Hot)
        self.assertNotIn(door, self.Cached)
        self.assertEqual(list(self.Guard[:]), [])                        # in no Field
        self.assertNotIn(door, Tag[...])
        self.assertTrue(isinstance(door, self.Hot) and isinstance(door, self.Guard))   # has been, as after any Rip
        self.assertEqual(self.log, [])

    def test_an_empty_safehouse_makes_triage_do_nothing(self) -> None:
        door = self.Door("free")
        self.Guard(door)

        self.assertEqual(self.triage(Tag), [])
        self.assertIn(door, self.Guard)

    def test_triage_is_done_before_a_warning_can_raise(self) -> None:
        self.kept("first", self.Cached)
        self.kept("second", self.Cached)

        with warnings.catch_warnings():
            warnings.simplefilter("error")

            with self.assertRaises(TagTriageWarning):
                del Tag[...]

        self.assertFalse(Tag[...])                                       # every Agent let go first


class DeliberateDifferenceTests(unittest.TestCase):
    """Two fixes of the performance work (PERFORMANCE-2026-09-24.md, 4.2)
    that change what a program can observe, each shown here."""

    def test_a_gate_in_one_thread_silences_no_warning_in_another(self) -> None:
        import sys
        import threading

        class Base(Tag):
            def Attack(agent) -> str:
                return "base"

        class Rival(Tag):
            def Attack(agent) -> str:   # replaces an independent Tag's Action: warns
                return "rival"

        class Gated(Tag):
            @Pre
            def Ready(agent) -> bool:
                return True

        rounds = 3000
        heard: list[int] = []
        warner: list[int] = []

        def Show(message, category, filename, lineno, file=None, line=None) -> None:
            if issubclass(category, TagOverwriteWarning) and threading.get_ident() in warner:
                heard.append(1)

        def Warn() -> None:
            warner.append(threading.get_ident())

            for _ in range(rounds):
                hero = Agent()
                Base(hero)
                Rival(hero)

        def Gate() -> None:
            while not done.is_set():
                Gated(Agent())                 # its scratch pass is silenced

        done = threading.Event()
        interval = sys.getswitchinterval()
        shown = warnings.showwarning

        with warnings.catch_warnings():
            warnings.simplefilter("always")
            warnings.showwarning = Show
            sys.setswitchinterval(1e-6)

            try:
                gate = threading.Thread(target=Gate)
                gate.start()
                warn = threading.Thread(target=Warn)
                warn.start()
                warn.join()
                done.set()
                gate.join()
            finally:
                sys.setswitchinterval(interval)
                warnings.showwarning = shown

        self.assertEqual(len(heard), rounds)   # the old kit delivered about four in five

    def test_queries_from_a_finalizer_answer_at_shutdown(self) -> None:
        lines, stderr = Run_Program(
                """
from TopKit import Tag, Flag, Keyword, Post, Public, Report

class Host:
    alive = True

@Flag("Wolf")
class Werewolf(Tag):
    @Post
    def Fed(agent): return agent.alive

    @Public
    @Report
    def pack(tag): return "north"

class Witness:                        # an untagged object whose finalizer asks
    def __init__(self, agent): self.agent = agent
    def __del__(self):
        for label, ask in (
                ("bool", lambda: bool(self.agent)),
                ("keyword", lambda: Keyword(self.agent, "Wolf")),
                ("condition", lambda: self.agent.Fed),
                ("report", lambda: self.agent.pack),
                ):
            try:
                print(label, ask())
            except Exception as error:
                print(label, type(error).__name__)

ari = Host()
Werewolf(ari)
witness = Witness(ari)
print("end")
""",
                )

        self.assertEqual(
                lines,
                ["end", "bool True", "keyword True", "condition True", "report north"],
                )


if __name__ == "__main__":
    unittest.main()
