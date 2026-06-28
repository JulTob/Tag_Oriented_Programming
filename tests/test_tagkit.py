from __future__ import annotations

import gc
import unittest
import warnings
import weakref

from TagKit import Action
from TagKit import At_Exit
from TagKit import Delete
from TagKit import Imprint
from TagKit import Operation
from TagKit import Post
from TagKit import Postcondition
from TagKit import Pre
from TagKit import Precondition
from TagKit import Record
from TagKit import Report
from TagKit import Rip
from TagKit import Scope
from TagKit import Tag
from TagKit import TagCompositionError
from TagKit import TagContractError
from TagKit import TagContractWarning
from TagKit import TagImprintError
from TagKit import TagOverwriteWarning
from TagKit import TagPostconditionError
from TagKit import TagPreconditionError
from TagKit import TagResolutionError
from TagKit import Contract
from TagKit import Underlay


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
    def Mark_Root(
            agent,
            ) -> None:
        agent.events.append("Root")


class Left(Root):
    @Imprint
    def Mark_Left(
            agent,
            ) -> None:
        agent.events.append("Left")


class Right(Root):
    @Imprint
    def Mark_Right(
            agent,
            ) -> None:
        agent.events.append("Right")


class Bridge(Left, Right):
    @Imprint
    def Mark_Bridge(
            agent,
            ) -> None:
        agent.events.append("Bridge")


class Person(Tag):
    def Attack(
            agent,
            ) -> str:
        return "Attack!"


class Elf(Person):
    @Underlay
    def Attack(
            agent,
            underlay,
            ) -> str:
        return (
                "With elven grace "
                + underlay()
                )


class Paladin(Person):
    @Underlay
    def Attack(
            agent,
            underlay,
            ) -> str:
        return (
                underlay()
                + " with a holy oath."
                )


class Berserker(Tag):
    def Attack(
            agent,
            ) -> str:
        return "Reckless attack!"


class Combatant(Tag):
    def Combat(
            agent,
            ) -> str:
        return agent.Attack()


class OOP_Refinement(Tag):
    @Underlay
    def Attack(
            agent,
            underlay,
            ) -> str:
        return (
                "Refined "
                + underlay()
                )


class Inventory(Tag):
    @Record
    def items(
            agent,
            ) -> list[str]:
        return []


class Armed(Tag):
    @Record
    def weapon(
            agent,
            ) -> str:
        return "arcane staff"


class Prepared(Inventory):
    @Record
    @Underlay
    def items(
            agent,
            underlay,
            ) -> list[str]:
        return (
                underlay()
                + ["rope"]
                )


class Lost_Inventory(Prepared):
    @Delete
    def items(
            agent,
            ) -> None:
        pass


class Needs_Inventory_Underlay(Lost_Inventory):
    @Record
    @Underlay
    def items(
            agent,
            underlay,
            ) -> list[str]:
        return underlay()


class Rebuilt_Inventory(Lost_Inventory):
    @Record
    def items(
            agent,
            ) -> list[str]:
        return ["shield"]


class Pacifist(Tag):
    @Delete
    def Attack(
            agent,
            ) -> None:
        pass

    @Delete
    def weapon(
            agent,
            ) -> None:
        pass


class Needs_Action_Underlay(Pacifist):
    @Underlay
    def Attack(
            agent,
            underlay,
            ) -> str:
        return underlay()


class Repaired_Pacifist(Pacifist):
    def Attack(
            agent,
            ) -> str:
        return "Defensive action!"

    @Record
    def weapon(
            agent,
            ) -> str:
        return "shield"


class Species(Tag):
    @Imprint
    def Establish_Species(
            agent,
            ) -> None:
        agent.events.append("Species")


class Human(Species):
    @Precondition
    def Has_Birthplace(
            agent,
            ) -> bool:
        return hasattr(
                agent,
                "birthplace",
                )


class Validated(Tag):
    @Precondition
    def Is_Allowed(
            agent,
            ) -> bool:
        return agent.allowed

    @Postcondition
    def Is_Ready(
            agent,
            ) -> bool:
        return agent.ready


class Advanced(Validated):
    pass


class Exempt(Validated):
    @Delete
    def Is_Allowed(
            agent,
            ) -> None:
        pass

    @Delete
    def Is_Ready(
            agent,
            ) -> None:
        pass


class Candidate_Record(Tag):
    @Record
    def token(
            agent,
            ) -> str:
        return "prepared"

    @Postcondition
    def Accepts_Token(
            agent,
            ) -> bool:
        return agent.ready


class Ordered_Imprints(Tag):
    @Imprint
    def First(
            agent,
            ) -> None:
        agent.events.append("First")

    @Imprint
    def Second(
            agent,
            ) -> None:
        agent.events.append("Second")


class Stocked(Tag):
    @Imprint
    def Note_Stocking(
            agent,
            ) -> None:
        agent.events.append("Stocked")

    @Record
    def supplies(
            agent,
            ) -> list[str]:
        return ["ration"]


class Broken_Imprint(Tag):
    @Imprint
    def Begin_Then_Fail(
            agent,
            ) -> None:
        agent.events.append("before failure")

        raise RuntimeError("expected imprint failure")


class Community(Tag):
    colour = Report("green")

    @Operation
    def Greet(
            tag,
            name: str,
            ) -> str:
        return f"{tag.__name__}:{name}"


class Silent_Community(Community):
    @Delete
    def colour(
            agent,
            ) -> None:
        pass

    @Delete
    def Greet(
            agent,
            ) -> None:
        pass


class Missing_Action(Tag):
    @Underlay
    def Missing(
            agent,
            underlay,
            ) -> str:
        return underlay()


class Arithmetic(Tag):
    def __add__(
            agent,
            amount: int,
            ) -> int:
        return amount + 1


class Field_Member(Tag):
    pass


class Territory(Tag):
    @Record
    def banner(
            agent,
            ) -> str:
        return "raised"


class Citadel(Territory):
    @Precondition
    def Has_Charter(
            agent,
            ) -> bool:
        return hasattr(
                agent,
                "charter",
                )


class Cursed_Blade(Tag):
    @Record
    def weapon(
            agent,
            ) -> str:
        return "cursed dagger"

    @Postcondition
    def Is_Worthy(
            agent,
            ) -> bool:
        return agent.ready


class Squire(Tag):
    @Imprint
    def Enlist(
            agent,
            ) -> None:
        agent.events.append("Squire")

    @Record
    def rank(
            agent,
            ) -> str:
        return "squire"


class Knighted(Tag):
    @Imprint
    def Knight(
            agent,
            ) -> None:
        agent.events.append("Knighted")

    @Action
    @Rip
    def rank_reset(
            agent,
            ) -> str:
        agent.rank = None

        return "Disrobed"


class Beast(Tag):
    @Record
    def legs(
            agent,
            ) -> int:
        return 4


class Wolf(Beast):
    @Record
    def howl(
            agent,
            ) -> str:
        return "Awooo"


class Base_Greeting(Tag):
    def Greet(
            agent,
            ) -> str:
        return "hi"


class Greeter(Base_Greeting):
    @Action
    @Underlay
    def Greet(
            agent,
            base,
            ) -> str:
        return "Hello and " + base()


class Politely(Greeter):
    @Action
    @Underlay
    def Greet(
            agent,
            prior,
            ) -> str:
        return prior() + " good day"


class Tally(Tag):
    @Record
    def marks(
            agent,
            ) -> list[str]:
        return ["one"]


class More_Tally(Tally):
    @Record
    @Underlay
    def marks(
            agent,
            existing,
            ) -> list[str]:
        return existing() + ["two"]


class Slotted_Agent:
    __slots__ = ()


# Exit-protocol fixtures. A @Rip teardown records to an external log,
# because the meaning of teardown on destruction is its outside-world
# side effect, not a mutation of the dying Agent.
_DEL_LOG: list[str] = []


class Sentry(Tag):
    @Action
    @Rip
    def stand_down(
            agent,
            ) -> str:
        _DEL_LOG.append("stood down")

        return "stood down"


class Recruit(Tag):
    # First parameter named 'spy', not 'agent': the Agent binding is
    # positional discipline, never a reserved word. 'code' is an application
    # input passed by name.
    @Imprint
    def assign(
            spy,
            code,
            ) -> None:
        spy.code = code


class Coded(Tag):
    @Precondition
    def Has_Code(
            agent,
            code,
            ) -> bool:
        return code is not None


class Scholar(Tag):
    @Pre
    def Level_Over_Zero(agent):
        assert agent.level > 0          # assert-style precondition

    @Imprint
    def Grant_Book(agent):
        agent.spellbook = "Tome"

    @Post
    def Has_Book(agent):
        assert agent.spellbook          # assert-style postcondition, bare


class Capped(Tag):
    @Post
    def Strength_Capped(agent):
        return agent.strength <= 20


class Bruiser(Capped):
    @Post
    def Strength_Capped(agent):         # crunch WITHOUT @Underlay -> weakens
        return agent.strength <= 24


class Disciplined(Capped):
    @Post
    @Underlay
    def Strength_Capped(agent, base):   # strengthen via the underlay
        return base() and agent.strength <= 18


class Reflective(Tag):
    @Post
    def Self_Aware(agent):
        if agent:                       # nested bool(agent) must not recurse
            return True


class Slotted(Tag):
    @Post
    def Raw_Slots(agent):
        return agent.spell_slots        # a raw int -- strict verdict rejects it


class Reserved(Tag):
    @Post
    def Has_Slots_Record(agent):
        assert agent.spell_slots is not None   # existence allows a real 0


class TagKitClaimTests(unittest.TestCase):
    def test_tagging_preserves_identity_and_builds_base_membership(self) -> None:
        ari = Agent()
        returned = Elf(ari)

        self.assertIs(
                returned,
                ari,
                )
        self.assertIn(
                ari,
                Elf,
                )
        self.assertIn(
                ari,
                Person,
                )
        self.assertIsInstance(
                ari,
                Elf,
                )
        self.assertIsInstance(
                ari,
                Person,
                )

    def test_direct_bases_apply_in_declaration_order_and_diamond_once(self) -> None:
        ari = Agent()

        Bridge(ari)

        self.assertEqual(
                ari.events,
                [
                    "Root",
                    "Left",
                    "Right",
                    "Bridge",
                    ],
                )
        self.assertIn(
                ari,
                Root,
                )
        self.assertIn(
                ari,
                Left,
                )
        self.assertIn(
                ari,
                Right,
                )

    def test_active_reapply_is_a_strict_noop(self) -> None:
        ari = Agent()

        Stocked(ari)
        ari.supplies.append("torch")
        ari.events.append("between")

        # Re-applying a currently active Tag does NOTHING: Records are not
        # reset and Imprints do not re-run. Resetting is deliberate -- Rip
        # then apply again -- so an accidental reapplication in a complex
        # system can never silently wipe accumulated state.
        Stocked(ari)

        self.assertEqual(
                ari.supplies,
                [
                    "ration",
                    "torch",
                    ],
                )
        self.assertEqual(
                ari.events,
                [
                    "Stocked",
                    "between",
                    ],
                )
        self.assertEqual(
                list(Stocked.Field).count(ari),
                1,
                )

    def test_successful_reapplication_is_idempotent(self) -> None:
        ari = Agent()

        Ordered_Imprints(ari)
        Ordered_Imprints(ari)

        self.assertEqual(
                ari.events,
                [
                    "First",
                    "Second",
                    ],
                )
        self.assertEqual(
                list(Ordered_Imprints.Field).count(ari),
                1,
                )

    def test_underlay_captures_the_visible_overlay_at_tagging_time(self) -> None:
        ari = Agent()

        Elf(ari)
        Paladin(ari)

        self.assertEqual(
                ari.Attack(),
                "With elven grace Attack! with a holy oath.",
                )
        self.assertEqual(
                ari.Paladin.Attack(),
                "With elven grace Attack! with a holy oath.",
                )

        with self.assertWarns(TagOverwriteWarning):
            Berserker(ari)

        self.assertEqual(
                ari.Attack(),
                "Reckless attack!",
                )
        self.assertEqual(
                ari.Paladin.Attack(),
                "With elven grace Attack! with a holy oath.",
                )

    def test_agent_action_calls_resolve_the_current_overlay(self) -> None:
        ari = Agent()

        Elf(ari)
        Combatant(ari)

        self.assertEqual(
                ari.Combat(),
                "With elven grace Attack!",
                )

        with self.assertWarns(TagOverwriteWarning):
            Berserker(ari)

        self.assertEqual(
                ari.Combat(),
                "Reckless attack!",
                )

    def test_underlay_can_refine_an_original_oop_action(self) -> None:
        ari = Agent()

        OOP_Refinement(ari)

        self.assertEqual(
                ari.Attack(),
                "Refined Faulty OOP attack!",
                )

    def test_independent_action_replacement_emits_a_diagnostic(self) -> None:
        ari = Agent()

        Person(ari)

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            Berserker(ari)

        self.assertTrue(
                any(
                        issubclass(
                                warning.category,
                                TagOverwriteWarning,
                                )
                        for warning in captured
                        )
                )

    def test_records_are_fresh_per_agent_and_can_extend_an_underlay(self) -> None:
        ari = Agent()
        bea = Agent()

        Prepared(ari)
        Inventory(bea)

        self.assertEqual(
                ari.items,
                ["rope"],
                )
        self.assertEqual(
                bea.items,
                [],
                )
        self.assertIsNot(
                ari.items,
                bea.items,
                )

    def test_a_record_can_replace_an_existing_object_attribute(self) -> None:
        ari = Agent()

        Armed(ari)

        self.assertEqual(
                ari.weapon,
                "arcane staff",
                )

    def test_deletion_removes_oop_members_and_resets_the_underlay(self) -> None:
        ari = Agent()

        Pacifist(ari)

        self.assertFalse(
                hasattr(
                        ari,
                        "Attack",
                        )
                )
        self.assertFalse(
                hasattr(
                        ari,
                        "weapon",
                        )
                )

        with self.assertRaises(TagResolutionError):
            Needs_Action_Underlay(ari)

        Repaired_Pacifist(ari)

        self.assertEqual(
                ari.Attack(),
                "Defensive action!",
                )
        self.assertEqual(
                ari.weapon,
                "shield",
                )

    def test_deleted_record_has_no_underlay_and_a_later_shape_can_rebuild_it(self) -> None:
        ari = Agent()

        Lost_Inventory(ari)

        self.assertFalse(
                hasattr(
                        ari,
                        "items",
                        )
                )

        with self.assertRaises(TagResolutionError):
            Needs_Inventory_Underlay(ari)

        Rebuilt_Inventory(ari)

        self.assertEqual(
                ari.items,
                ["shield"],
                )

    def test_failing_shape_rolls_back_its_bases_atomically(self) -> None:
        ari = Agent()

        with self.assertRaises(TagPreconditionError):
            Citadel(ari)

        # Atomic application: the whole Citadel(ari) call is one
        # transaction. When Citadel fails its Precondition, the Territory
        # Base pulled in by THIS call is rolled back too -- membership and
        # its TOP-managed `banner` Record vanish -- leaving the Agent
        # exactly as it was at call entry.
        self.assertNotIn(
                ari,
                Territory,
                )
        self.assertNotIn(
                ari,
                Citadel,
                )
        self.assertFalse(
                hasattr(
                        ari,
                        "banner",
                        )
                )
        self.assertEqual(
                ari.events,
                [],
                )

        # A later call succeeds: Territory and Citadel both commit, and
        # the rolled-back Base is reapplied cleanly.
        ari.charter = "royal"
        Citadel(ari)

        self.assertIn(
                ari,
                Citadel,
                )
        self.assertIn(
                ari,
                Territory,
                )
        self.assertEqual(
                ari.banner,
                "raised",
                )

    def test_atomic_rollback_keeps_earlier_committed_tags(self) -> None:
        ari = Agent()

        # An earlier, separate call commits Territory on its own.
        Territory(ari)

        self.assertIn(
                ari,
                Territory,
                )

        # A later Citadel call fails; its transaction rolls back, but the
        # Territory committed by the EARLIER call survives untouched.
        with self.assertRaises(TagPreconditionError):
            Citadel(ari)

        self.assertIn(
                ari,
                Territory,
                )
        self.assertNotIn(
                ari,
                Citadel,
                )
        self.assertEqual(
                ari.banner,
                "raised",
                )

    def test_active_preconditions_and_postconditions_run_on_later_tagging(self) -> None:
        ari = Agent()

        Validated(ari)
        ari.allowed = False

        with self.assertRaises(TagPreconditionError):
            Advanced(ari)

        ari.allowed = True
        ari.ready = False

        with self.assertRaises(TagPostconditionError):
            Advanced(ari)

        Exempt(ari)

        self.assertIn(
                ari,
                Exempt,
                )

    def test_postcondition_rejects_and_restores_top_managed_records(self) -> None:
        ari = Agent()
        ari.ready = False

        with self.assertRaises(TagPostconditionError):
            Candidate_Record(ari)

        self.assertNotIn(
                ari,
                Candidate_Record,
                )
        self.assertFalse(
                hasattr(
                        ari,
                        "token",
                        )
                )

    def test_imprints_run_in_declaration_order_and_failure_keeps_raw_effects(self) -> None:
        ari = Agent()

        Ordered_Imprints(ari)

        self.assertEqual(
                ari.events,
                [
                    "First",
                    "Second",
                    ],
                )

        with self.assertRaises(TagImprintError):
            Broken_Imprint(ari)

        self.assertNotIn(
                ari,
                Broken_Imprint,
                )
        self.assertEqual(
                ari.events,
                [
                    "First",
                    "Second",
                    "before failure",
                    ],
                )

    def test_reports_operations_and_their_deletion_follow_the_tag_view(self) -> None:
        ari = Agent()

        Community(ari)

        self.assertEqual(
                Community.colour,
                "green",
                )
        self.assertEqual(
                Community.Greet("Ari"),
                "Community:Ari",
                )
        self.assertEqual(
                ari.Community.colour,
                "green",
                )
        self.assertEqual(
                ari.Community.Greet("Ari"),
                "Community:Ari",
                )

        Silent_Community(ari)

        with self.assertRaises(AttributeError):
            ari.Silent_Community.colour

        with self.assertRaises(AttributeError):
            ari.Silent_Community.Greet

    def test_missing_underlay_and_missing_tag_view_raise_resolution_errors(self) -> None:
        ari = Agent()

        with self.assertRaises(TagResolutionError):
            Missing_Action(ari)

        Person(ari)

        with self.assertRaises(TagResolutionError):
            ari.Tag(Paladin)

    def test_fields_are_non_owning_and_iterable_from_the_tag(self) -> None:
        ari = Agent()
        Field_Member(ari)
        reference = weakref.ref(ari)

        self.assertEqual(
                list(Field_Member.Field),
                [ari],
                )
        self.assertEqual(
                list(Field_Member),
                [ari],
                )

        del ari
        gc.collect()

        self.assertIsNone(
                reference(),
                )
        self.assertEqual(
                list(Field_Member.Field),
                [],
                )

    def test_special_method_actions_actualize_the_agent(self) -> None:
        ari = Agent()

        Arithmetic(ari)

        self.assertEqual(
                ari + 4,
                5,
                )

    def test_targets_that_cannot_carry_top_state_fail_explicitly(self) -> None:
        target = Slotted_Agent()

        with self.assertRaises(TagCompositionError):
            Person(target)

    def test_membership_queries_do_not_actualize_an_untagged_target(self) -> None:
        ari = Agent()

        self.assertNotIn(
                ari,
                Person,
                )
        self.assertFalse(
                hasattr(
                        ari,
                        "_TAGKIT_STATE",
                        )
                )

    # -- Atomic application: pre-existing attribute restore (rule 1) -----

    def test_failed_postcondition_restores_a_preexisting_instance_attribute(self) -> None:
        ari = Agent()
        ari.weapon = "iron sword"
        ari.ready = False

        # Cursed_Blade's Record overwrites the pre-existing `weapon`
        # instance attribute, then its Postcondition fails. Atomic
        # rollback must restore the ORIGINAL value (the line-861 path).
        with self.assertRaises(TagPostconditionError):
            Cursed_Blade(ari)

        self.assertNotIn(
                ari,
                Cursed_Blade,
                )
        self.assertEqual(
                ari.weapon,
                "iron sword",
                )

    # -- Rip protocol and redefined stickiness (rule 2) ----------------

    def test_rip_leaves_a_rogue_agent_with_sticky_contributions(self) -> None:
        ari = Agent()

        Squire(ari)

        self.assertIn(
                ari,
                Squire,
                )
        self.assertEqual(
                ari.rank,
                "squire",
                )

        Squire.Rip(ari)

        # Gone from the Field, but Action/Record contributions persist.
        self.assertNotIn(
                ari,
                Squire,
                )
        self.assertEqual(
                ari.rank,
                "squire",
                )

    def test_del_removes_a_record_the_native_way(self) -> None:
        ari = Agent()

        Armed(ari)

        self.assertEqual(
                ari.weapon,
                "arcane staff",
                )

        # Records are removed with the language's own ``del`` -- TOP keeps no
        # verb for it. Tags are ripped; Records are deleted.
        del ari.weapon

        self.assertFalse(
                hasattr(
                        ari,
                        "weapon",
                        )
                )

    def test_rip_action_runs_on_rip_and_resets_a_record(self) -> None:
        ari = Agent()

        Squire(ari)
        Knighted(ari)

        self.assertEqual(
                ari.rank,
                "squire",
                )

        # rank_reset is both a normal Action and a @Rip teardown.
        self.assertEqual(
                ari.rank_reset(),
                "Disrobed",
                )

        ari.rank = "knight"

        Knighted.Rip(ari)

        self.assertNotIn(
                ari,
                Knighted,
                )
        self.assertIsNone(
                ari.rank,
                )

    def test_ripping_a_required_base_is_refused(self) -> None:
        ari = Agent()

        Wolf(ari)

        self.assertIn(
                ari,
                Beast,
                )

        # Beast is a Base still required by the active Wolf Shape.
        with self.assertRaises(TagCompositionError):
            Beast.Rip(ari)

        self.assertIn(
                ari,
                Beast,
                )

        # Ripping the leaf Shape is always allowed and does not
        # auto-rip its Base.
        Wolf.Rip(ari)

        self.assertNotIn(
                ari,
                Wolf,
                )
        self.assertIn(
                ari,
                Beast,
                )

        Beast.Rip(ari)

        self.assertNotIn(
                ari,
                Beast,
                )

    def test_ripped_agent_is_not_yielded_by_field_iteration(self) -> None:
        ari = Agent()
        bea = Agent()

        Squire(ari)
        Squire(bea)

        self.assertEqual(
                set(Squire.Field),
                {ari, bea},
                )

        Squire.Rip(ari)

        self.assertEqual(
                list(Squire.Field),
                [bea],
                )
        self.assertEqual(
                list(Squire),
                [bea],
                )

    def test_ripping_an_inactive_tag_raises(self) -> None:
        ari = Agent()

        Squire(ari)

        with self.assertRaises(TagResolutionError):
            Knighted.Rip(ari)

    # -- Retagging after Rip is a full fresh application (rule 3) -------

    def test_reapply_after_rip_restores_membership_and_reruns_imprint(self) -> None:
        ari = Agent()

        Squire(ari)
        Squire.Rip(ari)

        self.assertNotIn(
                ari,
                Squire,
                )

        # A previously ripped Tag re-applies as a fresh application:
        # membership is restored and the Imprint runs again.
        Squire(ari)

        self.assertIn(
                ari,
                Squire,
                )
        self.assertEqual(
                ari.events,
                [
                    "Squire",
                    "Squire",
                    ],
                )

    # -- Explicit @Underlay with author-chosen parameter names (rule 4) -

    def test_underlay_decorator_extends_an_action_with_any_param_name(self) -> None:
        ari = Agent()

        Politely(ari)

        # Base_Greeting -> Greeter -> Politely, each extending via
        # @Underlay with a parameter named anything but "underlay".
        self.assertEqual(
                ari.Greet(),
                "Hello and hi good day",
                )

    def test_underlay_decorator_extends_a_record_with_any_param_name(self) -> None:
        ari = Agent()

        More_Tally(ari)

        self.assertEqual(
                ari.marks,
                [
                    "one",
                    "two",
                    ],
                )

    # -- Exit protocols: del / Scope / At_Exit --------------------------

    def test_rip_runs_best_effort_on_garbage_collection(self) -> None:
        _DEL_LOG.clear()

        ari = Agent()
        Sentry(ari)

        del ari
        gc.collect()

        # __del__ runs the @Rip teardown when the Agent is collected.
        self.assertEqual(
                _DEL_LOG.count("stood down"),
                1,
                )

    def test_explicit_rip_prevents_a_second_rip_on_collection(self) -> None:
        _DEL_LOG.clear()

        ari = Agent()
        Sentry(ari)
        Sentry.Rip(ari)

        self.assertEqual(
                _DEL_LOG.count("stood down"),
                1,
                )

        del ari
        gc.collect()

        # The Tag was already extracted, so collection does not re-run it.
        self.assertEqual(
                _DEL_LOG.count("stood down"),
                1,
                )

    def test_scope_applies_and_rips_with_guaranteed_teardown(self) -> None:
        _DEL_LOG.clear()

        ari = Agent()

        with Scope(ari, Sentry) as scoped:
            self.assertIs(
                    scoped,
                    ari,
                    )
            self.assertIn(
                    ari,
                    Sentry,
                    )

        self.assertNotIn(
                ari,
                Sentry,
                )
        self.assertEqual(
                _DEL_LOG.count("stood down"),
                1,
                )

    def test_scope_rips_even_when_the_block_raises(self) -> None:
        _DEL_LOG.clear()

        ari = Agent()

        with self.assertRaises(ValueError):
            with Scope(ari, Sentry):
                raise ValueError("boom")

        self.assertNotIn(
                ari,
                Sentry,
                )
        self.assertEqual(
                _DEL_LOG.count("stood down"),
                1,
                )

    def test_at_exit_registration_does_not_pin_the_agent(self) -> None:
        ari = Agent()
        Sentry(ari)
        At_Exit(ari)

        reference = weakref.ref(ari)

        del ari
        gc.collect()

        # Registration is weak: it never keeps the Agent alive.
        self.assertIsNone(
                reference(),
                )

    # -- Runtime-type sharing (resource use) ----------------------------

    def test_runtime_types_are_shared_across_agents_of_one_shape(self) -> None:
        ari = Agent()
        bea = Agent()

        Elf(ari)
        Elf(bea)

        # Same (host, leaves) with no special-method Actions: one shared
        # runtime type, not one synthesized per application.
        self.assertIs(
                type(ari),
                type(bea),
                )
        self.assertIsInstance(
                ari,
                Elf,
                )
        self.assertIsInstance(
                ari,
                Person,
                )

    def test_special_method_tag_uses_a_distinct_runtime_type(self) -> None:
        ari = Agent()
        bea = Agent()

        Arithmetic(ari)
        Arithmetic(bea)

        self.assertEqual(
                ari + 1,
                2,
                )
        self.assertEqual(
                bea + 1,
                2,
                )

        # A special-method Action must live on the type, so these are built
        # per agent rather than shared.
        self.assertIsNot(
                type(ari),
                type(bea),
                )

    # -- Application inputs to protocols --------------------------------

    def test_application_inputs_reach_imprints_by_name(self) -> None:
        bond = Agent()

        # MI6-style: Recruit(bond, code="007") -> the Imprint parameter named
        # 'code' receives "007"; the Agent binding 'spy' is positional.
        Recruit(bond, code="007")

        self.assertEqual(
                bond.code,
                "007",
                )

    def test_missing_application_input_defaults_to_none(self) -> None:
        bond = Agent()

        # No 'code' supplied -> the Imprint's 'code' parameter is None, not a
        # function default. The application call is the single source of truth.
        Recruit(bond)

        self.assertIsNone(
                bond.code,
                )

    def test_application_inputs_reach_conditions(self) -> None:
        ari = Agent()

        # Precondition Has_Code(agent, code) sees code=None and rejects.
        with self.assertRaises(TagPreconditionError):
            Coded(ari)

        self.assertNotIn(
                ari,
                Coded,
                )

        Coded(ari, code="x")

        self.assertIn(
                ari,
                Coded,
                )

    # -- isinstance as a reliable HAS-BEEN check ------------------------

    def test_isinstance_is_a_reliable_has_been_check(self) -> None:
        ari = Agent()

        Squire(ari)

        self.assertIsInstance(ari, Squire)
        self.assertIn(ari, Squire)

        Squire.Rip(ari)

        # IS (membership) ends; HAS-BEEN (isinstance) persists.
        self.assertNotIn(ari, Squire)
        self.assertIsInstance(ari, Squire)

        # And it stays reliable through later re-composition -- the runtime
        # type is rebuilt without Squire, but ever-membership endures.
        Knighted(ari)

        self.assertIsInstance(ari, Squire)
        self.assertNotIn(ari, Squire)
        self.assertIsInstance(ari, Knighted)

    # -- Conditions: @Pre/@Post, assert-style, None-pass ----------------

    def test_assert_style_condition_passes_on_no_raise(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)

        self.assertIn(ari, Scholar)
        self.assertEqual(ari.spellbook, "Tome")

    def test_assert_style_precondition_fails_by_raising(self) -> None:
        ari = Agent()
        ari.level = 0                       # assert agent.level > 0 will raise

        with self.assertRaises(TagPreconditionError):
            Scholar(ari)

        self.assertNotIn(ari, Scholar)

    # -- if/assert agent runs Posts; Contract names the detail ----------

    def test_bool_agent_runs_postconditions(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)

        self.assertTrue(bool(ari))          # all Posts hold

        del ari.spellbook                   # Has_Book now fails

        self.assertFalse(bool(ari))         # truthy iff Posts hold

    def test_contract_postconditions_raises_a_detailed_error(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)
        del ari.spellbook

        with self.assertRaises(TagPostconditionError):
            Contract.Postconditions(ari)

    def test_if_agent_inside_a_post_does_not_recurse(self) -> None:
        ari = Agent()

        Reflective(ari)

        # Self_Aware does `if agent`; the reentrancy guard returns True
        # instead of recursing into the Post sweep.
        self.assertTrue(bool(ari))

    # -- Forward-Post: crunch warns, @Underlay strengthens silently -----

    def test_crunching_a_post_without_underlay_warns_and_relaxes(self) -> None:
        ari = Agent()
        ari.strength = 15

        with self.assertWarns(TagContractWarning):
            Bruiser(ari)                    # crunch warns at application

        self.assertIn(ari, Bruiser)         # but it's allowed -- the saw stays in the box

        ari.strength = 22                   # grows past the Base cap of 20

        self.assertTrue(bool(ari))          # Bruiser's relaxed <= 24 holds

    def test_post_underlay_strengthens_without_warning(self) -> None:
        ari = Agent()
        ari.strength = 15

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            Disciplined(ari)

        self.assertFalse(
                any(
                        issubclass(w.category, TagContractWarning)
                        for w in captured
                        )
                )
        self.assertTrue(bool(ari))          # 15 <= 18 and 15 <= 20

        ari.strength = 19

        self.assertFalse(bool(ari))         # 19 > 18: the stronger promise fails

    def test_pre_and_post_are_aliases(self) -> None:
        self.assertIs(Pre, Precondition)
        self.assertIs(Post, Postcondition)

    def test_contract_namespace_checks_pre_post_and_both(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)

        # All hold right after a clean tagging.
        self.assertTrue(Contract.Preconditions(ari))
        self.assertTrue(Contract.Postconditions(ari))
        self.assertTrue(Contract.Conditions(ari))

        del ari.spellbook

        # Conditions() runs Pre then Post, so the Post failure surfaces.
        with self.assertRaises(TagPostconditionError):
            Contract.Conditions(ari)

    def test_contract_status_maps_each_condition_to_its_state(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)

        self.assertEqual(
                Contract.Status(ari),
                {
                    "Level_Over_Zero": True,
                    "Has_Book": True,
                    },
                )

        del ari.spellbook

        status = Contract.Status(ari)
        self.assertTrue(status["Level_Over_Zero"])   # Pre still holds
        self.assertFalse(status["Has_Book"])         # Post now broken
        # Status never raises, even with a broken condition.

    def test_contract_display_renders_the_status(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)
        text = Contract.Display(ari)

        self.assertIn("Has_Book", text)
        self.assertIn("Pre:", text)        # sections separated
        self.assertIn("Post:", text)
        self.assertIn("OK", text)

        del ari.spellbook
        self.assertIn("XX", Contract.Display(ari))

    # -- Strict boolean: no truthy/falsy coercion -----------------------

    def test_condition_must_yield_a_strict_boolean(self) -> None:
        ari = Agent()
        ari.spell_slots = 0

        # Returning a raw value (a falsy int) is rejected loudly -- you must
        # write the explicit comparison you mean.
        with self.assertRaises(TagContractError):
            Slotted(ari)

    def test_explicit_existence_check_separates_zero_from_missing(self) -> None:
        zero = Agent()
        zero.spell_slots = 0

        # 0 is a real value: `assert ... is not None` holds.
        Reserved(zero)
        self.assertIn(zero, Reserved)
        self.assertTrue(bool(zero))

        missing = Agent()               # no spell_slots attribute at all

        with self.assertRaises(TagPostconditionError):
            Reserved(missing)           # AttributeError -> fails, distinct from 0


    # -- Contribution existence via `in` -------------------------------

    def test_contribution_existence_via_in(self) -> None:
        ari = Agent()

        Inventory(ari)                     # Inventory contributes an `items` Record

        self.assertIn(Inventory.items, ari)        # Inventory.items in ari -> exists

        other = Agent()
        Field_Member(other)                        # tagged, but contributes no items
        self.assertNotIn(Inventory.items, other)   # -> no items Record


if __name__ == "__main__":
    unittest.main()
