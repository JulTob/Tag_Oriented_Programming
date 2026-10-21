"""Live Tool kinds and Field use constrain late Pin conversion."""

import gc
import unittest
import weakref

from TopKit import (Delete, Pin, Pre, Tag, TagDeclarationError,
                    TagPreconditionError, Tool)
from TopKit.tags import MetaTag
from tests.test_tools import Character, Equip, Sword, Weapon


class LatePinOwnershipTests(unittest.TestCase):

    def test_restating_a_pin_shape_with_members_and_shapes_changes_nothing(self):
        @Pin
        class Base(Tag):
            pass

        class Shape(Base):
            pass

        class Further(Shape):
            pass

        class Target(Tag):
            pass

        Shape(Target)
        self.assertIs(Pin(Shape), Shape)
        self.assertIs(Pin(Further), Further)
        self.assertIn(Target, Shape[:])
        self.assertNotIn("__topkit_pin__", Shape.__dict__)

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

    def test_a_tag_whose_agents_left_is_still_not_marked_a_pin(self):
        #-- A Pin is declared, not converted (Director ruling, 2026-10-21):
        #-- emptying the Field does not reopen the door.
        class Noted(Tag):
            pass

        charlie = Character("Charlie")
        Noted(charlie)
        del Noted[charlie]
        self.assertNotIn(charlie, Noted[:])

        with self.assertRaises(TagDeclarationError) as refusal:
            Pin(Noted)
        self.assertIn("already been applied", str(refusal.exception))
        self.assertNotIn("__topkit_pin__", Noted.__dict__)

    def test_a_refused_ordinary_attempt_does_not_commit_the_tag(self):
        #-- Only a completed ordinary application commits the class. A Gate
        #-- refusal trains nothing, so the class may still be declared a Pin.
        class Guarded(Tag):
            @Pre
            def Never(agent):
                return False

        with self.assertRaises(TagPreconditionError):
            Guarded(Character("Hopeful"))

        self.assertIs(Pin(Guarded), Guarded)

    def test_applying_a_pin_does_not_commit_it_as_an_ordinary_tag(self):
        #-- Pinning a Tag is not ordinary use, so restating the mark on a
        #-- Pin that has pinned Tags stays a no-op.
        @Pin
        class Rare(Tag):
            pass

        class Wizard(Tag):
            pass

        Rare(Wizard)
        self.assertIs(Pin(Rare), Rare)
        self.assertIn(Wizard, Rare[:])

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

