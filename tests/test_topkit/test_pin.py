"""Conformance tests: pin."""

from __future__ import annotations

import unittest
import warnings
from TopKit import Action
from TopKit import Contract
from TopKit import Flag
from TopKit import Form
from TopKit import Keyword
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
from TopKit import Rip
from TopKit import Secret
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagDeclarationError
from TopKit import TagResolutionError
from TopKit import Tags
from TopKit import Underlay

from ._fixtures import Agent
from ._fixtures import Run_Program


class PinTests(unittest.TestCase):
    """STEP-SPEC-9: a Tag marked @Pin applies to Tags. The pinned Tag is
    the Pin's Agent; the receiver rule lands Records as Reports and
    Actions as Operations of that Tag."""

    def test_root_tag_cannot_be_marked_as_a_pin(self) -> None:
        lines, stderr = Run_Program("""
from TopKit import Pin, Tag, TagDeclarationError

try:
    Pin(Tag)
except TagDeclarationError:
    pass
else:
    raise AssertionError("the root Tag became a Pin")

class Ordinary(Tag):
    pass

class Host:
    pass

host = Host()
print(Ordinary(host) is host)
print(host in Ordinary[:])

@Pin
class Rare(Tag):
    pass

print(Rare(Ordinary) is Ordinary)
print(Ordinary in Rare[:])
""")
        self.assertEqual(lines, ["True"] * 4)
        self.assertEqual(stderr, "")

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
        self.assertGreater(len(Rare), 0)
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
        self.assertEqual(len(Wizard), 0)                              # no sound members
        ari = Agent()
        Wizard(ari)
        self.assertGreater(len(Wizard), 0)

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

        self.assertNotIn(Wizard, Promised)             # a defective pinned Tag is not sound
        self.assertIn(Wizard, Promised[:])             # the Pin's Field still has it
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

    def test_a_failed_patch_keeps_acquired_gain_without_pin_membership(self) -> None:
        Wizard = self.Wizard
        existing = Agent()
        Wizard(existing)

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

        self.assertEqual(Wizard.Greet("x"), "patched")
        self.assertTrue("Greet" @ Wizard)
        self.assertFalse("boom" @ Wizard)
        self.assertNotIn(Wizard, Broken[:])
        self.assertFalse(isinstance(Wizard, Broken))
        self.assertFalse("Greet" @ existing)
        future = Agent()
        Wizard(future)
        self.assertFalse("Greet" @ future)
        self.assertFalse("boom" @ future)

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
        unaffected = Agent()
        Wizard(unaffected)
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
            def Greet(tag, agent):
                return "patched"

            @Public
            @Action
            def firmware(tag, agent):
                return 1

        with self.assertRaises(TagCompositionError):
            Engine(Wizard)

        self.assertNotIn(Wizard, Engine)
        self.assertNotIn(Wizard, Engine[:])
        self.assertFalse(isinstance(Wizard, Engine))
        self.assertEqual(ari.firmware, "own")
        self.assertTrue("firmware" @ Wizard)
        self.assertEqual(Wizard.firmware(ari), 1)
        self.assertEqual(Wizard.Greet("x"), "patched")
        self.assertFalse("firmware" @ unaffected)
        self.assertFalse("Greet" @ unaffected)
        self.assertFalse("Greet" @ ari)
        future = Agent()
        Wizard(future)
        self.assertFalse("firmware" @ future)
        self.assertFalse("Greet" @ future)

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
