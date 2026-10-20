"""Tools: a Record whose value is an object of a declared kind
(STEP-SPEC-36). What an Agent *has*, beside what it *is* and what it is
*currently*.

A kind is a specific Tag (a member, now), a Python class (an instance),
or several of them, all holding; ``| None`` declares the empty hand.
Three laws: the slot has a kind, checked at admission (at the gaining
and at every write, ``object.__setattr__`` included); the slot is never
empty unless its kind says ``| None``; the slot never Tags, the forge
does.
"""

import gc
import unittest
import warnings
import weakref
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from TopKit import (Action, Constant, Contract, Delete, Imprint, Keyword,
                    Operation, Pin, Post, Pre, Public, Record, Report, Rip,
                    Secret, Tag, TagCompositionError, TagDeclarationError,
                    TagImprintError, TagOverwriteWarning, TagPreconditionError,
                    Tool)
from TopKit.tags import MetaTag


class Character:
    def __init__(character, name="x"):
        character.name = name


class Sword:
    def __init__(sword, name="a sword"):
        sword.name = name


class Staff:
    def __init__(staff, name="a staff"):
        staff.name = name


class Weapon(Tag):
    @Record
    def damage(tool):
        return 6


class Blessed(Tag):
    pass


class Cursed(Tag):
    pass


class Longsword(Weapon):
    pass


def Forge(agent, label="sword"):
    """A Weapon, Tagged in plain sight, as a forge does."""

    sword = Sword(f"{agent.name}'s {label}")
    Weapon(sword)
    return sword


class Fighter(Tag):
    @Tool(Weapon)
    def weapon(agent, *, weapon):
        return weapon


def Equip(tag, agent, slot="weapon", label="sword"):
    """Forge before Tagging; a Tool builder only receives the prepared object."""

    tag(agent, **{slot: Forge(agent, label)})


class Squire(Tag):
    @Tool(Weapon | None)
    def weapon(agent):
        return None


class Swordsman(Tag):
    @Tool(Sword)
    def weapon(agent, *, weapon):
        return weapon


# ------------------------------------------------------------------
# Law 1, a Tag kind: a member now
# ------------------------------------------------------------------


class Tag_Kind_Tests(unittest.TestCase):
    def test_the_gained_slot_holds_a_member_of_its_kind(self):
        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        self.assertIn(charlie.weapon, Weapon[:])
        self.assertNotIn(charlie, Weapon[:])             # the bearer is not a Weapon
        self.assertTrue("weapon" @ charlie)
        self.assertIsInstance(charlie.weapon, Sword)

    def test_a_non_member_is_refused_at_the_write_and_nothing_changes(self):
        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        held = charlie.weapon
        with self.assertRaises(TagCompositionError) as refusal:
            charlie.weapon = Sword("a stick")
        self.assertIn("not a Weapon now", str(refusal.exception))
        self.assertIs(charlie.weapon, held)
        with self.assertRaises(TagCompositionError):
            charlie.weapon = "a stick"
        self.assertIs(charlie.weapon, held)

    def test_object_setattr_passes_the_same_admission(self):
        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        held = charlie.weapon
        with self.assertRaises(TagCompositionError):
            object.__setattr__(charlie, "weapon", Sword("a stick"))
        self.assertIs(charlie.weapon, held)

    def test_a_member_is_admitted_by_assignment(self):
        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        other = Forge(charlie, "other")
        charlie.weapon = other
        self.assertIs(charlie.weapon, other)

    def test_an_agent_of_a_shape_of_the_kind_is_admitted(self):
        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        long = Sword("long")
        Longsword(long)                                   # membership is closed upward
        charlie.weapon = long
        self.assertIs(charlie.weapon, long)

    def test_a_defective_member_is_admitted_the_promise_judges_it(self):
        class Sharp(Tag):
            @Post
            def Has_An_Edge(tool):
                return tool.damage > 0

        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        blunt = Forge(charlie, "blunt")
        Sharp(blunt)
        blunt.damage = 0
        self.assertIn(blunt, ~Weapon)                     # defective, still a member
        charlie.weapon = blunt                            # admission asks membership, never soundness
        self.assertIs(charlie.weapon, blunt)

    def test_a_rogue_of_the_kind_is_refused_but_stays_in_hand(self):
        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        held = charlie.weapon
        del Weapon[held]                                  # a Rogue in hand: admission is a gate
        self.assertIs(charlie.weapon, held)
        self.assertTrue("weapon" @ charlie)
        self.assertNotIn(charlie.weapon, Weapon[:])
        bob = Character("Bob")
        Equip(Fighter, bob)
        with self.assertRaises(TagCompositionError) as refusal:
            bob.weapon = held                             # moved to another slot: refused
        self.assertIn("left Weapon", str(refusal.exception))

    def test_a_kind_of_two_tags_asks_for_both(self):
        class Holy(Tag):
            @Tool(Weapon, Blessed)
            def weapon(agent, *, weapon):
                return weapon

        hugh = Character("Hugh")
        sword = Forge(hugh)
        Blessed(sword)
        Holy(hugh, weapon=sword)
        plain = Forge(hugh, "plain")
        with self.assertRaises(TagCompositionError) as refusal:
            hugh.weapon = plain
        self.assertIn("not a Blessed now", str(refusal.exception))
        Blessed(plain)
        hugh.weapon = plain
        self.assertIs(hugh.weapon, plain)

    def test_a_builder_returning_a_non_member_refuses_the_gaining(self):
        class Careless(Tag):
            @Tool(Weapon)
            def weapon(agent):
                return Sword("untagged")

        charlie = Character("Charlie")
        with self.assertRaises(TagCompositionError) as refusal:
            Careless(charlie)
        self.assertIn("Tag it before the builder", str(refusal.exception))
        self.assertNotIn(charlie, Careless)
        self.assertFalse(hasattr(charlie, "weapon"))
        self.assertIsInstance(charlie, Character)       # actualized, without the failed Gain
        self.assertFalse("weapon" @ charlie)

    def test_the_bearer_is_admitted_only_when_it_is_of_the_kind(self):
        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        with self.assertRaises(TagCompositionError):
            charlie.weapon = charlie                      # not a Weapon: refused as any non-member
        Weapon(charlie)
        charlie.weapon = charlie                          # self-reference is the author's business
        self.assertIs(charlie.weapon, charlie)

    def test_membership_presence_and_soundness_stay_three_questions(self):
        class Sharp(Tag):
            @Post
            def Has_An_Edge(tool):
                return tool.damage > 0

        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        Sharp(charlie.weapon)
        charlie.weapon.damage = 0
        self.assertTrue("weapon" @ charlie)
        self.assertIn(charlie.weapon, Weapon[:])
        self.assertFalse(bool(charlie.weapon))


# ------------------------------------------------------------------
# Law 1, a class kind: an instance
# ------------------------------------------------------------------


class Class_Kind_Tests(unittest.TestCase):
    def test_a_class_kind_admits_untagged_and_tagged_instances_and_subclasses(self):
        class Broadsword(Sword):
            pass

        sam = Character("Sam")
        plain = Sword("plain")
        Swordsman(sam, weapon=plain)
        self.assertIs(sam.weapon, plain)
        self.assertNotIn(plain, Weapon[:])                # admission Tags nothing
        sam.weapon = Forge(sam)                           # a tagged Sword is still a Sword
        sam.weapon = Broadsword("broad")
        self.assertIsInstance(sam.weapon, Broadsword)

    def test_a_class_kind_refuses_another_class_even_when_tagged_weapon(self):
        sam = Character("Sam")
        Swordsman(sam, weapon=Sword())
        held = sam.weapon
        staff = Staff()
        Weapon(staff)
        with self.assertRaises(TagCompositionError) as refusal:
            sam.weapon = staff
        self.assertIn("not a Sword now", str(refusal.exception))
        self.assertIn("Hand over a Sword", str(refusal.exception))
        self.assertIs(sam.weapon, held)
        with self.assertRaises(TagCompositionError):
            object.__setattr__(sam, "weapon", "a stick")
        self.assertIs(sam.weapon, held)

    def test_a_class_kind_admits_a_rogue_of_any_tag(self):
        sam = Character("Sam")
        Swordsman(sam, weapon=Sword())
        rogue = Forge(sam, "rogue")
        del Weapon[rogue]
        sam.weapon = rogue                                # the class still holds; membership is a Post's question
        self.assertIs(sam.weapon, rogue)

    def test_a_class_and_a_tag_together_ask_both(self):
        class Armed(Tag):
            @Tool(Sword, Weapon)
            def weapon(agent, *, weapon):
                return weapon

        sam = Character("Sam")
        sword = Forge(sam)
        Armed(sam, weapon=sword)
        plain = Sword("plain")
        with self.assertRaises(TagCompositionError) as refusal:
            sam.weapon = plain                            # a Sword, not a Weapon
        self.assertIn("not a Weapon now", str(refusal.exception))
        staff = Staff()
        Weapon(staff)
        with self.assertRaises(TagCompositionError) as refusal:
            sam.weapon = staff                            # a Weapon, not a Sword
        self.assertIn("not a Sword now", str(refusal.exception))
        self.assertIs(sam.weapon, sword)
        with self.assertRaises(TagCompositionError):
            Armed(Character("Pat"), weapon=plain)         # the same at the gaining

    def test_a_union_of_classes_admits_either(self):
        class Wielder(Tag):
            @Tool(Sword | Staff)
            def item(agent):
                return Sword("start")

        sam = Character("Sam")
        Wielder(sam)
        sam.item = Staff()
        self.assertIsInstance(sam.item, Staff)
        with self.assertRaises(TagCompositionError) as refusal:
            sam.item = "a stick"
        self.assertIn("Sword | Staff", str(refusal.exception))

    def test_a_union_of_a_tag_and_a_class_admits_either(self):
        class Wielder(Tag):
            @Tool(Weapon | Staff)
            def item(agent, *, item):
                return item

        sam = Character("Sam")
        Wielder(sam, item=Staff())                        # an instance of the class
        sam.item = Forge(sam)                             # a member of the Tag
        with self.assertRaises(TagCompositionError):
            sam.item = Sword("plain")                     # neither

    def test_self_reference_by_class_is_allowed(self):
        class Buddy(Tag):
            @Tool(Character)
            def buddy(agent):
                return agent

        sam = Character("Sam")
        Buddy(sam)
        self.assertIs(sam.buddy, sam)

    def test_a_kind_of_type_preserves_the_held_tags_own_pin_truth(self):
        class Listed(Tag):
            pass

        @Pin
        class Checked(Tag):
            @Record
            def approved(tag):
                return True

            @Post
            def Approved(tag):
                return tag.approved

        Checked(Listed)

        class Catalogued(Tag):
            @Tool(type)
            def listed(agent):
                return Listed

        sam = Character("Sam")
        Catalogued(sam)
        self.assertIs(sam.listed, Listed)
        self.assertEqual(len(Listed), 0)
        self.assertTrue(sam.listed)                    # its own Pin Posts hold
        Listed.approved = False
        self.assertFalse(sam.listed)                   # the held Tag's contract changed
        self.assertTrue(sam)                          # the bearer made no such promise
        with self.assertRaises(TagCompositionError):
            sam.listed = Sword()

    def test_a_plain_class_with_a_protocol_marker_is_still_a_class(self):
        class Marked:
            _is_protocol = True

        class Holding(Tag):
            @Tool(Marked)
            def thing(agent, *, thing):
                return thing

        sam = Character("Sam")
        value = Marked()
        Holding(sam, thing=value)
        self.assertIs(sam.thing, value)

    def test_a_failing_instance_test_is_a_named_composition_failure(self):
        failure = RuntimeError("the instance test refused")

        class CheckedMeta(type):
            def __instancecheck__(kind, value):
                if getattr(value, "reject", False):
                    raise failure
                return isinstance(value, Sword)

        class Checked(metaclass=CheckedMeta):
            pass

        class Equipped(Tag):
            @Tool(Checked)
            def weapon(agent, *, weapon):
                return weapon

        rejected = Sword()
        rejected.reject = True
        sam = Character("Sam")
        with self.assertRaises(TagCompositionError) as caught:
            Equipped(sam, weapon=rejected)
        self.assertIs(caught.exception.__cause__, failure)
        self.assertIn("Equipped.weapon", str(caught.exception))
        self.assertNotIn(sam, Equipped[:])
        original = Sword()
        Equipped(sam, weapon=original)
        with self.assertRaises(TagCompositionError) as caught:
            sam.weapon = rejected
        self.assertIs(caught.exception.__cause__, failure)
        self.assertIs(sam.weapon, original)

    def test_an_interrupt_inside_the_instance_test_propagates_unchanged(self):
        interruption = KeyboardInterrupt("stop")

        class CheckedMeta(type):
            def __instancecheck__(kind, value):
                if getattr(value, "interrupt", False):
                    raise interruption
                return isinstance(value, Sword)

        class Checked(metaclass=CheckedMeta):
            pass

        class Equipped(Tag):
            @Tool(Checked)
            def weapon(agent, *, weapon):
                return weapon

        sam = Character("Sam")
        Equipped(sam, weapon=Sword())
        held = sam.weapon
        interrupted = Sword()
        interrupted.interrupt = True
        with self.assertRaises(KeyboardInterrupt) as caught:
            sam.weapon = interrupted
        self.assertIs(caught.exception, interruption)
        self.assertIs(sam.weapon, held)


# ------------------------------------------------------------------
# Law 2: never empty, unless the kind says so
# ------------------------------------------------------------------


class Emptiness_Tests(unittest.TestCase):
    def test_none_is_refused_at_the_write_without_the_empty_hand(self):
        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        held = charlie.weapon
        with self.assertRaises(TagCompositionError) as refusal:
            charlie.weapon = None
        self.assertIn("never empty", str(refusal.exception))
        self.assertIn("@Tool(Weapon | None)", str(refusal.exception))
        self.assertIs(charlie.weapon, held)

    def test_a_builder_returning_none_refuses_the_gaining(self):
        class Empty_Handed(Tag):
            @Tool(Weapon)
            def weapon(agent):
                return None

        charlie = Character("Charlie")
        with self.assertRaises(TagCompositionError) as refusal:
            Empty_Handed(charlie)
        self.assertIn("returned None", str(refusal.exception))
        self.assertNotIn(charlie, Empty_Handed)
        self.assertFalse(hasattr(charlie, "weapon"))

    def test_del_is_the_drop_and_the_kind_stays(self):
        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        del charlie.weapon
        self.assertFalse("weapon" @ charlie)
        self.assertIn(charlie, Fighter)
        charlie.weapon = Forge(charlie, "new")
        with self.assertRaises(TagCompositionError):
            charlie.weapon = Sword("a stick")

    def test_the_declared_empty_hand_admits_none_at_the_gaining_and_at_the_write(self):
        sam = Character("Sam")
        Squire(sam)
        self.assertTrue("weapon" @ sam)                   # the slot exists
        self.assertIsNone(sam.weapon)                     # and is empty, by declaration
        sam.weapon = Forge(sam)
        self.assertIn(sam.weapon, Weapon[:])
        sam.weapon = None
        self.assertIsNone(sam.weapon)
        with self.assertRaises(TagCompositionError):
            sam.weapon = Sword("a stick")                 # the stick is still a stick
        del sam.weapon
        self.assertFalse("weapon" @ sam)

    def test_the_empty_hand_may_be_written_in_any_position(self):
        class Optional(Tag):
            @Tool(None | Weapon)
            def weapon(agent):
                return None

        class Optional_Class(Tag):
            @Tool(Sword | None)
            def weapon(agent):
                return None

        for tag in (Optional, Optional_Class):
            sam = Character(tag.__name__)
            tag(sam)
            self.assertIsNone(sam.weapon)


# ------------------------------------------------------------------
# Law 3: the slot never Tags
# ------------------------------------------------------------------


class Forge_Tests(unittest.TestCase):
    def test_the_slot_tags_nothing(self):
        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        plain = Sword("plain")
        with self.assertRaises(TagCompositionError):
            charlie.weapon = plain                        # refused, not Tagged
        self.assertNotIn(plain, Weapon[:])
        self.assertFalse(isinstance(plain, Weapon))
        sam = Character("Sam")
        Swordsman(sam, weapon=plain)                      # admitted by class, still not Tagged
        self.assertNotIn(plain, Weapon[:])

    def test_tool_gate_failure_in_imprint_keeps_its_name_and_refuses_the_bearer(self):
        class Holy(Tag):
            @Pre
            def Blessed_Steel(tool):
                return tool.name != "a stick"

        class Crusader(Tag):
            @Tool(Weapon)
            def weapon(agent, *, weapon):
                return weapon

            @Imprint
            def Attempt_Blessing(agent):
                Holy(agent.weapon)

        dan = Character("Dan")
        stick = Sword("a stick")
        Weapon(stick)
        with self.assertRaises(TagImprintError) as failure:
            Crusader(dan, weapon=stick)
        self.assertIsInstance(failure.exception.__cause__, TagPreconditionError)
        self.assertNotIn(dan, Crusader)
        self.assertIs(dan.weapon, stick)                  # the Gain precedes the failed Imprint

    def test_a_later_imprint_failure_leaves_training_on_a_handed_in_object(self):
        class Armed_With(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

            @Imprint
            def Train_Weapon(agent):
                Weapon(agent.weapon)

            @Imprint
            def Drop_Weapon(agent):
                raise ValueError("dropped it")

        loan = Sword("a loan")
        dan = Character("Dan")
        with self.assertRaises(TagImprintError):
            Armed_With(dan, weapon=loan)
        self.assertNotIn(dan, Armed_With)
        self.assertIn(loan, Weapon[:])                    # the forge's act stands: Rip is not restoration
        del Weapon[loan]                                  # the caller's own compensation
        self.assertNotIn(loan, Weapon[:])


# ------------------------------------------------------------------
# The mark, at class use
# ------------------------------------------------------------------


class Declaration_Tests(unittest.TestCase):
    def test_tool_alone_declares_the_record_and_record_may_restate_it(self):
        class Plain(Tag):
            @Tool(Weapon)
            def weapon(agent, *, weapon):
                return weapon

        class Restated(Tag):
            @Record
            @Tool(Weapon)
            def weapon(agent, *, weapon):
                return weapon

        class Restated_Below(Tag):
            @Tool(Weapon)
            @Record
            def weapon(agent, *, weapon):
                return weapon

        for tag in (Plain, Restated, Restated_Below):
            agent = Character(tag.__name__)
            Equip(tag, agent)
            self.assertIn(agent.weapon, Weapon[:])
            with self.assertRaises(TagCompositionError):
                agent.weapon = Sword("a stick")

    def test_tool_needs_a_kind(self):
        with self.assertRaises(TagDeclarationError) as refusal:
            Tool()
        self.assertIn("@Tool(Weapon)", str(refusal.exception))
        self.assertIn("@Tool(Sword)", str(refusal.exception))

    def test_a_bare_tool_on_a_builder_is_refused_with_the_spelling(self):
        with self.assertRaises(TagDeclarationError) as refusal:
            class Invalid(Tag):
                @Tool
                def weapon(agent):
                    return None
        self.assertIn("parentheses", str(refusal.exception))

    def test_the_roots_name_no_kind(self):
        with self.assertRaises(TagDeclarationError) as refusal:
            Tool(Tag)
        self.assertIn("root Tag", str(refusal.exception))
        with self.assertRaises(TagDeclarationError) as refusal:
            Tool(object)
        self.assertIn("plain @Record", str(refusal.exception))

    def test_a_kind_is_a_tag_or_a_class(self):
        for not_a_kind in (7, Sword(), "Weapon", list[int], Weapon[:], ~Weapon):
            with self.subTest(kind=not_a_kind):
                with self.assertRaises(TagDeclarationError):
                    Tool(not_a_kind)

    def test_typing_constructs_are_refused(self):
        class SwordProtocol(Protocol):
            def Swing(sword): ...

        @runtime_checkable
        class RuntimeSwordProtocol(Protocol):
            def Swing(sword): ...

        for construct in (Any, Protocol, SwordProtocol, RuntimeSwordProtocol):
            with self.subTest(construct=construct):
                with self.assertRaises(TagDeclarationError) as refusal:
                    Tool(construct)
                self.assertIn("typing construct", str(refusal.exception))

    def test_none_alone_names_no_kind(self):
        with self.assertRaises(TagDeclarationError):
            Tool(None)
        with self.assertRaises(TagDeclarationError):
            Tool(type(None))

    def test_a_pin_is_not_a_kind(self):
        @Pin
        class Rare(Tag):
            pass

        with self.assertRaises(TagDeclarationError) as refusal:
            Tool(Rare)
        self.assertIn("is a Pin", str(refusal.exception))

    def test_a_population_is_not_a_kind(self):
        for population in (Weapon | Blessed, ~Weapon, Weapon[:], Weapon & Blessed):
            with self.subTest(population=population):
                with self.assertRaises(TagDeclarationError) as refusal:
                    Tool(population)
                self.assertIn("@Tool(Weapon, Blessed)", str(refusal.exception))
                self.assertIn("Base Tag", str(refusal.exception))

    def test_tool_over_other_kinds_is_refused_in_either_order(self):
        for kind in (Action, Report, Operation, Pre, Post, Imprint, Rip, Delete):
            for tool_outside in (False, True):
                with self.subTest(kind=kind.__name__, tool_outside=tool_outside):
                    with self.assertRaises(TagDeclarationError):
                        def weapon(agent):
                            return None

                        if tool_outside:
                            member = Tool(Sword)(kind(weapon))
                        else:
                            member = kind(Tool(Sword)(weapon))

                        type("Invalid", (Tag,), {"weapon": member})

    def test_tool_on_a_value_or_a_classmethod_is_refused(self):
        with self.assertRaises(TagDeclarationError):
            Tool(Weapon)(3)
        with self.assertRaises(TagDeclarationError):
            Tool(Weapon)(classmethod(lambda cls: None))
        with self.assertRaises(TagDeclarationError):
            Tool(Weapon)(staticmethod(lambda: None))

    def test_tool_inside_a_pin_is_refused(self):
        with self.assertRaises(TagDeclarationError) as refusal:
            @Pin
            class Armory(Tag):
                @Tool(Weapon)
                def standard(tag):
                    return None
        self.assertIn("a shared tool is a Report", str(refusal.exception))

        @Pin
        class Collection(Tag):
            pass

        with self.assertRaises(TagDeclarationError):
            class Armory_Shape(Collection):
                @Tool(Weapon)
                def standard(tag):
                    return None

    def test_a_private_name_is_refused(self):
        with self.assertRaises(TagDeclarationError):
            class Hidden(Tag):
                @Tool(Weapon)
                def _weapon(agent):
                    return None

    def test_the_builder_keeps_its_three_seats(self):
        class Armed_With(Tag):
            @Tool(Weapon)
            def weapon(agent, stored=None, *, weapon=None):
                return weapon if stored is None else stored

        gift = Sword("a gift")
        Weapon(gift)
        charlie = Character("Charlie")
        Armed_With(charlie, weapon=gift)
        self.assertIs(charlie.weapon, gift)
        bob = Character("Bob")
        Equip(Armed_With, bob)
        self.assertIn(bob.weapon, Weapon[:])


# ------------------------------------------------------------------
# Stacking with Constant, Secret and Public
# ------------------------------------------------------------------


class Stacking_Tests(unittest.TestCase):
    def test_a_constant_tool_is_bonded_in_either_order(self):
        class Oathbound(Tag):
            @Constant
            @Tool(Weapon)
            def relic(agent, *, relic):
                return relic

        class Sworn(Tag):
            @Tool(Weapon)
            @Constant
            def relic(agent, *, relic):
                return relic

        for tag in (Oathbound, Sworn):
            with self.subTest(tag=tag.__name__):
                agent = Character(tag.__name__)
                Equip(tag, agent, slot="relic", label="relic")
                relic = agent.relic
                with self.assertRaises(TagCompositionError):
                    agent.relic = Forge(agent, "copy")
                with self.assertRaises(TagCompositionError):
                    del agent.relic
                with self.assertRaises(TagCompositionError):
                    agent.relic = Sword("a stick")
                self.assertIs(agent.relic, relic)
                Cursed(agent.relic)                       # Constant fixes the binding, not the sword
                self.assertIn(agent.relic, Cursed)

    def test_a_secret_tool_hides_the_slot_not_the_tool_in_either_order(self):
        class Concealed(Tag):
            @Secret
            @Tool(Weapon)
            def dagger(agent, *, dagger):
                return dagger

            @Action
            def Draw(agent):
                return agent.dagger

        class Hidden(Tag):
            @Tool(Weapon)
            @Secret
            def dagger(agent, *, dagger):
                return dagger

            @Action
            def Draw(agent):
                return agent.dagger

        for tag in (Concealed, Hidden):
            with self.subTest(tag=tag.__name__):
                agent = Character(tag.__name__)
                Equip(tag, agent, slot="dagger", label="dagger")
                with self.assertRaises(AttributeError):
                    agent.dagger
                dagger = agent.Draw()
                self.assertIn(dagger, Weapon[:])          # the dagger is an ordinary Agent to anyone holding it
                with self.assertRaises(TagCompositionError):
                    agent.dagger = Sword("a stick")       # admission guards the hidden slot too

    def test_a_public_tool_restates_the_default_in_either_order(self):
        class Shown(Tag):
            @Public
            @Tool(Weapon)
            def weapon(agent, *, weapon):
                return weapon

        class Displayed(Tag):
            @Tool(Weapon)
            @Public
            def weapon(agent, *, weapon):
                return weapon

        for tag in (Shown, Displayed):
            with self.subTest(tag=tag.__name__):
                agent = Character(tag.__name__)
                Equip(tag, agent)
                self.assertIn(agent.weapon, Weapon[:])
                with self.assertRaises(TagCompositionError):
                    agent.weapon = Sword("a stick")


# ------------------------------------------------------------------
# Overlay on a Tool slot: ordinary, as any Record
# ------------------------------------------------------------------


class Overlay_Tests(unittest.TestCase):
    def test_a_shape_receives_the_tool_in_the_stored_seat_and_guards_with_its_own_kind(self):
        class Paladin(Fighter):
            @Tool(Weapon, Blessed)
            def weapon(agent, stored):
                return stored

        pat = Character("Pat")
        sword = Forge(pat)
        Blessed(sword)
        Paladin(pat, weapon=sword)
        self.assertIn(pat.weapon, Weapon[:])
        self.assertIn(pat.weapon, Blessed[:])
        plain = Forge(pat, "plain")
        with self.assertRaises(TagCompositionError):
            pat.weapon = plain                            # Blessed is asked now

    def test_a_shape_may_change_the_kind_to_a_class(self):
        class Collector(Fighter):
            @Tool(Sword)
            def weapon(agent, stored):
                return stored

        pat = Character("Pat")
        Equip(Collector, pat)
        del Weapon[pat.weapon]
        rogue = pat.weapon
        pat.weapon = Sword("plain")                       # the Shape's kind is the slot's now
        pat.weapon = rogue
        with self.assertRaises(TagCompositionError):
            pat.weapon = Staff()

    def test_a_plain_record_from_a_shape_ends_the_rule(self):
        class Rearmed(Fighter):
            @Record
            def weapon(agent, stored):
                return stored

        pat = Character("Pat")
        Equip(Rearmed, pat)
        self.assertIn(pat.weapon, Weapon[:])
        pat.weapon = "a stick"                            # a Record is a Record again
        self.assertEqual(pat.weapon, "a stick")

    def test_an_action_from_a_shape_ends_the_rule(self):
        class Smith(Fighter):
            @Action
            def weapon(agent):
                return Forge(agent)

        pat = Character("Pat")
        Equip(Smith, pat)
        self.assertIn(pat.weapon(), Weapon[:])            # a smith: every call forges

    def test_an_independent_record_replaces_with_the_usual_warning_and_ends_the_rule(self):
        class Other(Tag):
            @Record
            def weapon(agent):
                return "a stick"

        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagOverwriteWarning)
            Other(charlie)
        self.assertTrue(any(issubclass(w.category, TagOverwriteWarning) for w in caught))
        self.assertEqual(charlie.weapon, "a stick")
        charlie.weapon = 3                                # no kind any more

    def test_an_independent_action_over_the_record_keeps_the_cross_kind_refusal(self):
        class Other(Tag):
            @Action
            def weapon(agent):
                return "a stick"

        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        held = charlie.weapon
        with self.assertRaises(TagCompositionError):
            Other(charlie)
        self.assertIs(charlie.weapon, held)
        with self.assertRaises(TagCompositionError):
            charlie.weapon = Sword("a stick")             # the rule stands after the refused call

    def test_delete_frees_the_slot(self):
        class Unarmed(Fighter):
            @Delete
            def weapon(agent):
                pass

        class Rearmed(Unarmed):
            @Record
            def weapon(agent):
                return "a stick, and nobody minds"

        charlie = Character("Charlie")
        Equip(Unarmed, charlie)
        self.assertFalse("weapon" @ charlie)
        bob = Character("Bob")
        Equip(Rearmed, bob)
        self.assertEqual(bob.weapon, "a stick, and nobody minds")

    def test_a_tool_over_a_plain_record_takes_the_slot_and_guards_it(self):
        class Carrying(Tag):
            @Record
            def weapon(agent):
                return "a stick"

        class Knight(Carrying):
            @Tool(Weapon)
            def weapon(agent, stored, *, weapon):
                return weapon

        kay = Character("Kay")
        Equip(Knight, kay)
        self.assertIn(kay.weapon, Weapon[:])
        with self.assertRaises(TagCompositionError):
            kay.weapon = "a stick"

    def test_a_tool_name_over_a_condition_or_a_host_property_keeps_the_record_refusals(self):
        class Promising(Tag):
            @Post
            def weapon(agent):
                return True

        class Holding(Tag):
            @Tool(Weapon)
            def weapon(agent, *, weapon):
                return weapon

        charlie = Character("Charlie")
        Promising(charlie)
        with self.assertRaises(TagCompositionError):
            Equip(Holding, charlie)

        class Propertied:
            def __init__(self, name): self.name = name
            @property
            def weapon(self): return "fixed"

        with self.assertRaises(TagCompositionError):
            Equip(Holding, Propertied("p"))


# ------------------------------------------------------------------
# Lifecycle: Rip and reapplication
# ------------------------------------------------------------------


class Lifecycle_Tests(unittest.TestCase):
    def test_rip_of_the_bearer_leaves_the_slot_sticky_and_guarded(self):
        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        held = charlie.weapon
        del Fighter[charlie]
        self.assertNotIn(charlie, Fighter)
        self.assertTrue("weapon" @ charlie)
        self.assertIs(charlie.weapon, held)
        with self.assertRaises(TagCompositionError):
            charlie.weapon = Sword("a stick")             # sticky Contributions keep their laws

    def test_reapplication_rebuilds_an_ordinary_slot(self):
        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        held = charlie.weapon
        del Fighter[charlie]
        Equip(Fighter, charlie)
        self.assertIsNot(charlie.weapon, held)
        self.assertIn(charlie.weapon, Weapon[:])

    def test_reapplication_keeps_the_tool_through_the_stored_seat(self):
        class Keeper(Tag):
            @Tool(Weapon)
            def weapon(agent, stored=None, *, weapon=None):
                return weapon if stored is None else stored

        charlie = Character("Charlie")
        Equip(Keeper, charlie)
        held = charlie.weapon
        del Keeper[charlie]
        Keeper(charlie)
        self.assertIs(charlie.weapon, held)

    def test_reapplication_keeps_a_constant_tool_without_running_the_builder(self):
        forged = []

        class Oathbound(Tag):
            @Constant
            @Tool(Weapon)
            def relic(agent, *, relic=None):
                forged.append(agent)
                return relic

        charlie = Character("Charlie")
        Equip(Oathbound, charlie, slot="relic", label="relic")
        held = charlie.relic
        del Oathbound[charlie]
        self.assertIs(charlie.relic, held)                # survives Rip
        Oathbound(charlie)
        self.assertIs(charlie.relic, held)
        self.assertEqual(len(forged), 1)

    def test_rip_of_the_tools_tag_leaves_a_rogue_in_hand_that_the_bearers_post_notices(self):
        class Armed(Tag):
            @Tool(Weapon)
            def weapon(agent, *, weapon):
                return weapon

            @Post
            def Sound_Weapon(agent):
                return agent.weapon in Weapon[:] and bool(agent.weapon)

        charlie = Character("Charlie")
        Equip(Armed, charlie)
        self.assertTrue(bool(charlie))
        del Weapon[charlie.weapon]
        self.assertTrue("weapon" @ charlie)
        self.assertNotIn(charlie.weapon, Weapon[:])
        self.assertTrue(isinstance(charlie.weapon, Weapon))
        self.assertFalse(bool(charlie))
        Weapon(charlie.weapon)                            # a fresh tagging repairs it
        self.assertTrue(bool(charlie))

    def test_a_rip_protocol_may_disarm(self):
        class Conscript(Tag):
            @Tool(Weapon)
            def weapon(agent, *, weapon):
                return weapon

            @Rip
            def Disarm(agent):
                del agent.weapon

        charlie = Character("Charlie")
        Equip(Conscript, charlie)
        del Conscript[charlie]
        self.assertFalse("weapon" @ charlie)

    def test_an_imprint_may_fill_an_empty_hand(self):
        class Trained(Tag):
            @Tool(Weapon | None)
            def weapon(agent, stored=None):
                return stored

            @Imprint
            def Equip(agent):
                if agent.weapon is None:
                    agent.weapon = Forge(agent)

        erin = Character("Erin")
        Trained(erin)
        self.assertIn(erin.weapon, Weapon[:])


# ------------------------------------------------------------------
# Sharing, nesting, and the two doors
# ------------------------------------------------------------------


class Sharing_Tests(unittest.TestCase):
    def test_two_bearers_may_hold_one_tool(self):
        charlie, bob = Character("Charlie"), Character("Bob")
        Equip(Fighter, charlie)
        Equip(Fighter, bob)
        bob.weapon = charlie.weapon
        self.assertIs(bob.weapon, charlie.weapon)
        del charlie.weapon                                # hand-over, line two
        self.assertFalse("weapon" @ charlie)
        self.assertIn(bob.weapon, Weapon[:])

    def test_the_tools_tags_travel_with_it(self):
        charlie, bob = Character("Charlie"), Character("Bob")
        Equip(Fighter, charlie)
        Equip(Fighter, bob)
        Cursed(charlie.weapon)
        bob.weapon = charlie.weapon
        self.assertIn(bob.weapon, Cursed)
        self.assertNotIn(bob, Cursed)
        self.assertFalse(Keyword(bob, "Cursed"))

    def test_a_tool_may_bear_a_tool(self):
        class Gem:
            pass

        class Jewel(Tag):
            pass

        class Socketed(Tag):
            @Tool(Jewel)
            def gem(tool, *, gem):
                return gem

        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        gem = Gem()
        Jewel(gem)
        Socketed(charlie.weapon, gem=gem)
        self.assertIn(charlie.weapon.gem, Jewel[:])
        with self.assertRaises(TagCompositionError):
            charlie.weapon.gem = Gem()

    def test_a_bearers_action_reading_its_tools_secret_fails_closed(self):
        class Vault(Tag):
            @Secret
            @Record
            def combination(tool):
                return "1234"

            @Action
            def Open(tool):
                return tool.combination

        class Guard(Tag):
            @Tool(Vault)
            def vault(agent, *, vault):
                return vault

            @Action
            def Crack(agent):
                return agent.vault.combination

        ann = Character("Ann")
        vault = Sword("the vault")
        Vault(vault)
        Guard(ann, vault=vault)
        self.assertEqual(ann.vault.Open(), "1234")
        with self.assertRaises(AttributeError):
            ann.Crack()

    def test_the_slot_holds_strongly_and_the_type_retains_nothing(self):
        first, second = Character("First"), Character("Second")
        sword, staff = Sword(), Staff()

        class Staffed(Tag):
            @Tool(Staff)
            def weapon(agent, *, weapon):
                return weapon

        Swordsman(first, weapon=sword)
        Staffed(second, weapon=staff)
        with self.assertRaises(TagCompositionError):
            first.weapon = staff
        with self.assertRaises(TagCompositionError):
            second.weapon = sword
        first_ref, sword_ref = weakref.ref(first), weakref.ref(sword)
        del first, sword
        gc.collect()
        self.assertIsNone(first_ref())
        self.assertIsNone(sword_ref())                    # the slot held it; nothing else does
        self.assertIs(second.weapon, staff)


# ------------------------------------------------------------------
# Hosts, presence, runtime types, protocol names
# ------------------------------------------------------------------


class Host_Tests(unittest.TestCase):
    def test_a_host_write_hook_keeps_its_behaviour_and_admission_runs_first(self):
        writes = []

        class Logging_Host:
            def __init__(self, name): self.name = name
            def __setattr__(agent, name, value):
                if name == "__class__":
                    object.__setattr__(agent, name, value)
                    return

                writes.append(name)
                if name == "__class__":
                    object.__setattr__(agent, name, value)
                else:
                    agent.__dict__[name] = value

        lou = Logging_Host("Lou")
        Equip(Fighter, lou)
        writes.clear()
        with self.assertRaises(TagCompositionError):
            lou.weapon = Sword("a stick")
        self.assertEqual(writes, [])                      # refused before the host's hook ran
        lou.weapon = Forge(lou, "two")
        self.assertEqual(writes, ["weapon"])

    def test_a_frozen_dataclass_host_gains_through_the_kernel_path(self):
        @dataclass(frozen=True)
        class Frozen:
            name: str

        fay = Frozen("Fay")
        sword = Sword()
        Swordsman(fay, weapon=sword)
        self.assertIs(fay.weapon, sword)
        with self.assertRaises(TagCompositionError):
            object.__setattr__(fay, "weapon", Staff())
        self.assertIs(fay.weapon, sword)

    def test_presence_answers_for_the_slot_without_running_anything(self):
        charlie = Character("Charlie")
        self.assertFalse(hasattr(charlie, "weapon"))
        Equip(Fighter, charlie)
        self.assertTrue("weapon" @ charlie)
        self.assertTrue("weapon" @ Fighter[charlie])
        del charlie.weapon
        self.assertFalse("weapon" @ charlie)

    def test_a_tool_slot_does_not_multiply_runtime_types(self):
        charlie, bob = Character("Charlie"), Character("Bob")
        Equip(Fighter, charlie)
        Equip(Fighter, bob)
        self.assertIs(type(charlie), type(bob))
        sam = Character("Sam")
        Squire(sam)
        self.assertIs(type(sam), type(charlie))           # the gate reads each Agent's own kind
        with self.assertRaises(TagCompositionError):
            charlie.weapon = None                         # Fighter's slot is never empty
        sam.weapon = None                                 # Squire's may be

    def test_host_truth_and_the_tools_truth_stay_apart(self):
        class Sharp(Tag):
            @Post
            def Has_An_Edge(tool):
                return tool.damage > 0

        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        Sharp(charlie.weapon)
        charlie.weapon.damage = 0
        self.assertFalse(bool(charlie.weapon))
        self.assertTrue(bool(charlie))          # nothing on Charlie promised about the sword

    def test_a_tool_under_a_protocol_name_keeps_the_languages_hook(self):
        class Given(Tag):
            @Tool(Sword)
            def __rmatmul__(agent, *, tool):
                return tool

            @Record
            def visible(agent):
                return None

        sam = Character("Sam")
        sword = Sword()
        Given(sam, tool=sword)
        self.assertIs(sam.__rmatmul__, sword)
        self.assertTrue("__rmatmul__" @ sam)              # presence still answers through the type's hook
        self.assertTrue("visible" @ sam)
        self.assertFalse("missing" @ sam)
        with self.assertRaises(TagCompositionError):
            sam.__rmatmul__ = Staff()                     # an ordinary write is checked
        self.assertIs(sam.__rmatmul__, sword)
        object.__setattr__(sam, "__rmatmul__", None)      # the documented kernel bypass on a protocol name
        self.assertIsNone(sam.__rmatmul__)
        self.assertTrue("__rmatmul__" @ sam)

    def test_a_tool_under_getattribute_does_not_replace_lookup(self):
        class Given(Tag):
            @Tool(Sword)
            def __getattribute__(agent, *, tool):
                return tool

            @Record
            def visible(agent):
                return "ordinary lookup"

        sam = Character("Sam")
        sword = Sword()
        Given(sam, tool=sword)
        self.assertIs(sam.__getattribute__, sword)
        self.assertEqual(sam.visible, "ordinary lookup")
        with self.assertRaises(TagCompositionError):
            sam.__getattribute__ = Staff()
        self.assertEqual(sam.visible, "ordinary lookup")

    def test_a_tool_named_del_keeps_finalization_and_field_removal(self):
        seen = []                                         # from #159, on main's API

        class Finalized_Host:
            def __init__(host):
                host.name = "host"

            def __del__(host):
                seen.append("host finalizer")

        class Given(Tag):
            @Tool(Sword)
            def __del__(agent, *, tool):
                return tool

            @Rip
            def Stand_Down(agent):
                seen.append("Rip")

        agent = Finalized_Host()
        sword = Sword()
        Given(agent, tool=sword)
        self.assertIs(agent.__del__, sword)
        self.assertIn(agent, Given[:])
        reference = weakref.ref(agent)
        del agent
        gc.collect()
        self.assertIsNone(reference())
        self.assertEqual(list(Given[:]), [])
        self.assertEqual(seen, ["Rip", "host finalizer"])

    def test_a_late_plain_binding_never_reads_the_values_class(self):
        observed = []                                     # from #159, on main's API

        class Value:
            @property
            def __class__(value):
                observed.append("read")
                raise RuntimeError("a plain value must not be inspected")

        class Example(Tag):
            pass

        value = Value()
        Example.setting = value
        self.assertIs(Example.__dict__["setting"], value)
        self.assertEqual(observed, [])


# ------------------------------------------------------------------
# A Pin is marked at its declaration (§1.3, §1.9)
# ------------------------------------------------------------------


class Late_Pin_Tests(unittest.TestCase):
    def test_a_tag_with_a_shape_is_not_marked_a_pin_later(self):
        class Order(Tag):
            pass

        class Knight_Order(Order):
            @Tool(Weapon)
            def weapon(agent, *, weapon):
                return weapon

        with self.assertRaises(TagDeclarationError) as refusal:
            Pin(Order)                                    # the Shape's Tool would land on Tags
        self.assertIn("already has the Shape Knight_Order", str(refusal.exception))
        charlie = Character("Charlie")
        Equip(Knight_Order, charlie)                      # nothing changed: still an ordinary Tag
        self.assertIn(charlie.weapon, Weapon[:])

    def test_a_tag_with_agents_is_not_marked_a_pin_later(self):
        class Noted(Tag):
            pass

        charlie = Character("Charlie")
        Noted(charlie)
        with self.assertRaises(TagDeclarationError) as refusal:
            Pin(Noted)                                    # its Field would mix objects and Tags
        self.assertIn("already has Agents", str(refusal.exception))
        self.assertIn(charlie, Noted)

    def test_a_tag_named_as_a_tool_kind_is_not_marked_a_pin_later(self):
        class Prize(Tag):
            pass

        class Collector(Tag):
            @Tool(Prize | None)
            def prize(agent):
                return None

        with self.assertRaises(TagDeclarationError) as refusal:
            Pin(Prize)                                    # the slot would admit Tags
        self.assertIn("a @Tool already names Prize", str(refusal.exception))
        collector = Character("Collector")
        Collector(collector)
        trophy = Sword("a trophy")
        Prize(trophy)                                     # still applied to objects
        collector.prize = trophy
        self.assertIs(collector.prize, trophy)

    def test_a_host_lookalike_with_unhashable_metaclass_remains_a_class_kind(self):
        class Unhashable(type):
            __hash__ = None

        class Host(metaclass=Unhashable):
            _topkit_field = object()                     # a name is not a Tag

        class Holder(Tag):
            @Tool(Host)
            def held(agent):
                return Host()

        agent = Character("Charlie")
        Holder(agent)
        self.assertIsInstance(agent.held, Host)

    def test_equal_but_distinct_tag_classes_have_separate_kind_history(self):
        class Equal_Meta(MetaTag):
            def __eq__(cls, other):
                return isinstance(other, Equal_Meta)

            def __hash__(cls):
                return 17

        class Prize(Tag, metaclass=Equal_Meta):
            pass

        class Other(Tag, metaclass=Equal_Meta):
            pass

        class Collector(Tag):
            @Tool(Prize)
            def prize(agent):
                return None

        self.assertIsNot(Prize, Other)
        self.assertEqual(Prize, Other)
        self.assertIs(Pin(Other), Other)                   # only Prize was named
        with self.assertRaises(TagDeclarationError):
            Pin(Prize)

    def test_named_tool_kinds_are_tracked_weakly(self):
        def declare():
            class Prize(Tag):
                pass

            class Collector(Tag):
                @Tool(Prize)
                def prize(agent):
                    return None

            return weakref.ref(Prize), weakref.ref(Collector)

        prize, collector = declare()
        gc.collect()
        self.assertIsNone(collector())
        self.assertIsNone(prize())

    def test_a_dead_tool_owner_does_not_forever_bar_a_live_kind(self):
        class Prize(Tag):
            pass

        def declare():
            class Collector(Tag):
                @Tool(Prize)
                def prize(agent):
                    return None

            return weakref.ref(Collector)

        collector = declare()
        gc.collect()
        self.assertIsNone(collector())
        self.assertIs(Pin(Prize), Prize)

    def test_a_tool_marked_before_the_pin_is_checked_at_class_creation(self):
        class Prize(Tag):
            pass

        with self.assertRaises(TagDeclarationError) as refusal:
            class Collector(Tag):
                @Tool(Prize)
                def prize(agent):
                    return None

                Pin(Prize)                             # after the decorator, before Collector exists

        self.assertIn("now a Pin", str(refusal.exception))

    def test_a_late_tool_binding_also_prevents_a_late_pin(self):
        class Prize(Tag):
            pass

        class Collector(Tag):
            pass

        @Tool(Prize)
        def prize(agent):
            return None

        Collector.prize = prize
        with self.assertRaises(TagDeclarationError):
            Pin(Prize)

    def test_a_late_tool_binding_on_a_pin_is_refused(self):
        @Pin
        class Rare(Tag):
            pass

        class Prize(Tag):
            pass

        @Tool(Prize)
        def prize(tag):
            return None

        with self.assertRaises(TagDeclarationError):
            Rare.prize = prize
        self.assertNotIn("prize", Rare.__dict__)

    def test_a_refused_pin_leaves_no_mark(self):
        class Odd(Tag):
            @Delete
            def name(agent):
                pass

        with self.assertRaises(TagDeclarationError):
            Pin(Odd)                                      # a Pin's members are plain
        charlie = Character("Charlie")
        Odd(charlie)                                      # still an ordinary Tag
        self.assertIn(charlie, Odd)

    def test_a_shape_refused_for_its_ordinary_base_leaves_no_mark(self):
        class Base(Tag):
            pass

        class Mixed(Base):
            pass

        with self.assertRaises(TagDeclarationError):
            Pin(Mixed)                                    # one Form is all Pins or no Pins
        charlie = Character("Charlie")
        Mixed(charlie)                                    # still an ordinary Tag
        self.assertIn(charlie, Mixed)

    def test_a_pin_scanned_before_its_mark_is_validated_at_the_mark(self):
        class Plain(Tag):
            @Delete
            def name(agent):
                pass

        Plain(Character("Charlie"))                       # scanned as an ordinary Tag; the Agent dies at once
        gc.collect()
        with self.assertRaises(TagDeclarationError) as refusal:
            Pin(Plain)                                    # the earlier scan is not taken as a Pin's
        self.assertIn("@Delete of name", str(refusal.exception))

    def test_restating_the_mark_changes_nothing(self):
        @Pin
        class Rare(Tag):
            pass

        class Wizard(Tag):
            pass

        Rare(Wizard)
        self.assertIs(Pin(Rare), Rare)
        self.assertIn(Wizard, Rare)


# ------------------------------------------------------------------
# Coverage the review asked for
# ------------------------------------------------------------------


class Sequence_Tests(unittest.TestCase):
    def test_a_refused_tool_over_an_occupied_slot_keeps_the_held_tool(self):
        class Rearmed(Fighter):
            @Record
            def checkpoint(agent):
                return "gained before the refused Tool"

            @Tool(Weapon)
            def weapon(agent, stored):
                return Sword("an unforged blade")         # not a Weapon: refused at its turn

        charlie = Character("Charlie")
        Equip(Fighter, charlie)
        held = charlie.weapon
        with self.assertRaises(TagCompositionError):
            Rearmed(charlie)
        self.assertIs(charlie.weapon, held)               # the refused Tool did not replace it
        self.assertEqual(charlie.checkpoint, "gained before the refused Tool")
        self.assertNotIn(charlie, Rearmed[:])             # no Field entry for unfinished training
        with self.assertRaises(TagCompositionError):
            charlie.weapon = Sword("plain")               # Fighter's rule still guards the slot

    def test_an_imprint_failure_after_a_tool_gaining_keeps_the_tool(self):
        class Trained(Tag):
            @Tool(Weapon)
            def weapon(agent, *, weapon):
                return weapon

            @Imprint
            def Drill(agent):
                raise RuntimeError("the drill went wrong")

        charlie = Character("Charlie")
        with self.assertRaises(TagImprintError) as failure:
            Equip(Trained, charlie)
        self.assertIsInstance(failure.exception.__cause__, RuntimeError)
        self.assertIn(charlie.weapon, Weapon[:])          # acquired Tool stays on a Rogue
        self.assertNotIn(charlie, Trained[:])
        with self.assertRaises(TagCompositionError):
            charlie.weapon = Sword("plain")

    def test_admission_never_asks_the_held_things_truth(self):
        class Touchy(Sword):
            def __bool__(sword):
                raise RuntimeError("asked for its truth")

        class Holder(Tag):
            @Tool(Sword)
            def by_class(agent, *, held):
                return held

        class Tagged_Holder(Tag):
            @Tool(Weapon)
            def by_tag(agent, *, held):
                return held

        touchy = Touchy()                                 # a plain object keeps its own truth
        sam = Character("Sam")
        Holder(sam, held=touchy)                          # the class admission never called bool()
        self.assertIs(sam.by_class, touchy)

        with self.assertRaises(TagCompositionError):      # not a Weapon: refused, and still no bool()
            Tagged_Holder(Character("Tam"), held=touchy)


if __name__ == "__main__":
    unittest.main()
