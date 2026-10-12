"""Tools: a Record whose value is an Agent of the Tags its declaration
names (STEP-SPEC-36). What an Agent *has*, beside what it *is* and what
it is *currently*.

Three laws: the slot has a kind, checked at admission (at Parts and at
every write, ``object.__setattr__`` included); the slot is never empty
unless its kind says ``| None``; the slot never Tags, the forge does.
"""

import unittest
import warnings

from TopKit import (Action, Constant, Contract, Delete, Keyword, Pin, Post,
                    Pre, Public, Record, Report, Rip, Secret, Tag,
                    TagCompositionError, TagDeclarationError,
                    TagOverwriteWarning, TagPreconditionError, Tool)


class Character:
    def __init__(character, name="x"):
        character.name = name


class Sword:
    def __init__(sword, name="a sword"):
        sword.name = name


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
    def weapon(agent):
        return Forge(agent)


class Squire(Tag):
    @Tool(Weapon | None)
    def weapon(agent):
        return None


# ------------------------------------------------------------------
# Law 1: the slot has a kind, checked at admission
# ------------------------------------------------------------------


class Admission_Tests(unittest.TestCase):
    def test_the_gained_slot_holds_a_member_of_its_kind(self):
        charlie = Character("Charlie")
        Fighter(charlie)
        self.assertIn(charlie.weapon, Weapon[:])
        self.assertNotIn(charlie, Weapon[:])             # the bearer is not a Weapon
        self.assertTrue("weapon" @ charlie)
        self.assertIsInstance(charlie.weapon, Sword)

    def test_a_non_member_is_refused_at_the_write_and_nothing_changes(self):
        charlie = Character("Charlie")
        Fighter(charlie)
        held = charlie.weapon
        stick = Sword("a stick")
        with self.assertRaises(TagCompositionError) as refusal:
            charlie.weapon = stick
        self.assertIn("not a Weapon now", str(refusal.exception))
        self.assertIs(charlie.weapon, held)
        with self.assertRaises(TagCompositionError):
            charlie.weapon = "a stick"
        self.assertIs(charlie.weapon, held)

    def test_object_setattr_passes_the_same_admission(self):
        charlie = Character("Charlie")
        Fighter(charlie)
        held = charlie.weapon
        with self.assertRaises(TagCompositionError):
            object.__setattr__(charlie, "weapon", Sword("a stick"))
        self.assertIs(charlie.weapon, held)

    def test_a_member_is_admitted_by_assignment(self):
        charlie = Character("Charlie")
        Fighter(charlie)
        other = Forge(charlie, "other")
        charlie.weapon = other
        self.assertIs(charlie.weapon, other)

    def test_an_agent_of_a_shape_of_the_kind_is_admitted(self):
        charlie = Character("Charlie")
        Fighter(charlie)
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
        Fighter(charlie)
        blunt = Forge(charlie, "blunt")
        Sharp(blunt)
        blunt.damage = 0
        self.assertIn(blunt, ~Weapon)                     # defective, still a member
        charlie.weapon = blunt                            # admission asks membership, never soundness
        self.assertIs(charlie.weapon, blunt)

    def test_a_rogue_of_the_kind_is_refused_but_stays_in_hand(self):
        charlie = Character("Charlie")
        Fighter(charlie)
        held = charlie.weapon
        del Weapon[held]                                  # a Rogue in hand: admission is a gate
        self.assertIs(charlie.weapon, held)
        self.assertTrue("weapon" @ charlie)
        self.assertNotIn(charlie.weapon, Weapon[:])
        bob = Character("Bob")
        Fighter(bob)
        with self.assertRaises(TagCompositionError) as refusal:
            bob.weapon = held                             # moved to another slot: refused
        self.assertIn("left Weapon", str(refusal.exception))

    def test_the_bearer_is_refused_at_the_write(self):
        charlie = Character("Charlie")
        Fighter(charlie)
        Weapon(charlie)                                   # even as a Weapon himself
        with self.assertRaises(TagCompositionError) as refusal:
            charlie.weapon = charlie
        self.assertIn("never the Agent", str(refusal.exception))

    def test_a_kind_of_two_tags_asks_for_both(self):
        class Holy(Tag):
            @Tool(Weapon, Blessed)
            def weapon(agent):
                sword = Forge(agent)
                Blessed(sword)
                return sword

        hugh = Character("Hugh")
        Holy(hugh)
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
        self.assertIn("Tag it in the builder", str(refusal.exception))
        self.assertNotIn(charlie, Careless)
        self.assertFalse(hasattr(charlie, "weapon"))
        self.assertIs(type(charlie), Character)          # the whole call rolled back

    def test_a_builder_returning_the_bearer_refuses_the_gaining(self):
        class Selfish(Tag):
            @Tool(Weapon)
            def weapon(agent):
                Weapon(agent)
                return agent

        charlie = Character("Charlie")
        with self.assertRaises(TagCompositionError):
            Selfish(charlie)
        self.assertNotIn(charlie, Selfish)
        self.assertNotIn(charlie, Weapon)                 # the builder's own tagging of the bearer rolled back too

    def test_membership_presence_and_soundness_stay_three_questions(self):
        class Sharp(Tag):
            @Post
            def Has_An_Edge(tool):
                return tool.damage > 0

        charlie = Character("Charlie")
        Fighter(charlie)
        Sharp(charlie.weapon)
        charlie.weapon.damage = 0
        self.assertTrue("weapon" @ charlie)
        self.assertIn(charlie.weapon, Weapon[:])
        self.assertFalse(Contract.Holds(charlie.weapon))


# ------------------------------------------------------------------
# Law 2: never empty, unless the kind says so
# ------------------------------------------------------------------


class Emptiness_Tests(unittest.TestCase):
    def test_none_is_refused_at_the_write_without_the_empty_hand(self):
        charlie = Character("Charlie")
        Fighter(charlie)
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

    def test_del_is_the_drop(self):
        charlie = Character("Charlie")
        Fighter(charlie)
        del charlie.weapon
        self.assertFalse("weapon" @ charlie)
        self.assertIn(charlie, Fighter)
        charlie.weapon = Forge(charlie, "new")            # the slot keeps its kind after the drop
        with self.assertRaises(TagCompositionError):
            charlie.weapon = Sword("a stick")

    def test_the_declared_empty_hand_admits_none_at_parts_and_at_the_write(self):
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

    def test_the_empty_hand_may_be_written_after_the_tags(self):
        class Optional(Tag):
            @Tool(None | Weapon)
            def weapon(agent):
                return None

        sam = Character("Sam")
        Optional(sam)
        self.assertIsNone(sam.weapon)


# ------------------------------------------------------------------
# Law 3: the slot never Tags
# ------------------------------------------------------------------


class Forge_Tests(unittest.TestCase):
    def test_the_slot_tags_nothing(self):
        charlie = Character("Charlie")
        Fighter(charlie)
        plain = Sword("plain")
        with self.assertRaises(TagCompositionError):
            charlie.weapon = plain                        # assignment Tags nothing: refused, not Tagged
        self.assertNotIn(plain, Weapon[:])
        self.assertFalse(isinstance(plain, Weapon))

    def test_the_tools_own_gate_failure_keeps_its_name_and_refuses_the_bearer(self):
        class Holy(Tag):
            @Pre
            def Blessed_Steel(tool):
                return tool.name != "a stick"

        class Crusader(Tag):
            @Tool(Weapon)
            def weapon(agent):
                stick = Sword("a stick")
                Weapon(stick)
                Holy(stick)
                return stick

        dan = Character("Dan")
        with self.assertRaises(TagPreconditionError):
            Crusader(dan)
        self.assertNotIn(dan, Crusader)
        self.assertFalse(hasattr(dan, "weapon"))

    def test_a_later_gaining_failure_leaves_the_forged_tag_on_a_handed_in_object(self):
        class Armed_With(Tag):
            @Tool(Weapon)
            def weapon(agent, *, weapon):
                Weapon(weapon)
                return weapon

            @Record
            def balance(agent):
                raise ValueError("dropped it")

        loan = Sword("a loan")
        dan = Character("Dan")
        with self.assertRaises(TagCompositionError):
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
            def weapon(agent):
                return Forge(agent)

        class Restated(Tag):
            @Record
            @Tool(Weapon)
            def weapon(agent):
                return Forge(agent)

        class Restated_Below(Tag):
            @Tool(Weapon)
            @Record
            def weapon(agent):
                return Forge(agent)

        for tag in (Plain, Restated, Restated_Below):
            agent = Character(tag.__name__)
            tag(agent)
            self.assertIn(agent.weapon, Weapon[:])
            with self.assertRaises(TagCompositionError):
                agent.weapon = Sword("a stick")

    def test_tool_needs_a_kind(self):
        with self.assertRaises(TagDeclarationError) as refusal:
            Tool()
        self.assertIn("@Tool(Weapon)", str(refusal.exception))

    def test_a_kind_is_a_tag_recognised_by_its_metaclass(self):
        for not_a_tag in (Sword, int, Sword("x"), Tag, "Weapon"):
            with self.subTest(kind=not_a_tag):
                with self.assertRaises(TagDeclarationError) as refusal:
                    Tool(not_a_tag)
                self.assertIn("not a Tag", str(refusal.exception))

    def test_none_alone_names_no_kind(self):
        with self.assertRaises(TagDeclarationError):
            Tool(None)

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
                self.assertIn("@Tool(Weapon | None)", str(refusal.exception))

    def test_tool_over_other_kinds_is_refused(self):
        with self.assertRaises(TagDeclarationError) as refusal:
            class Doing(Tag):
                @Tool(Weapon)
                @Action
                def weapon(agent):
                    return Forge(agent)
        self.assertIn("an Action", str(refusal.exception))

        with self.assertRaises(TagDeclarationError):
            class Promising(Tag):
                @Tool(Weapon)
                @Post
                def weapon(agent):
                    return True

        with self.assertRaises(TagDeclarationError):
            class Sharing(Tag):
                @Tool(Weapon)
                @Report
                def weapon(tag):
                    return Forge(tag)

        with self.assertRaises(TagDeclarationError):
            class Leaving(Tag):
                @Tool(Weapon)
                @Rip
                def weapon(agent):
                    pass

        with self.assertRaises(TagDeclarationError):
            class Freeing(Tag):
                @Tool(Weapon)
                @Delete
                def weapon(agent):
                    pass

    def test_other_kinds_over_tool_are_refused(self):
        with self.assertRaises(TagDeclarationError):
            class Doing(Tag):
                @Action
                @Tool(Weapon)
                def weapon(agent):
                    return Forge(agent)

        with self.assertRaises(TagDeclarationError):
            class Promising(Tag):
                @Post
                @Tool(Weapon)
                def weapon(agent):
                    return True

        with self.assertRaises(TagDeclarationError):
            class Leaving(Tag):
                @Rip
                @Tool(Weapon)
                def weapon(agent):
                    return Forge(agent)

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
                    return Forge(tag)
        self.assertIn("a shared tool is a Report", str(refusal.exception))

        @Pin
        class Collection(Tag):
            pass

        with self.assertRaises(TagDeclarationError):
            class Armory_Shape(Collection):
                @Tool(Weapon)
                def standard(tag):
                    return Forge(tag)

    def test_a_private_name_is_refused(self):
        with self.assertRaises(TagDeclarationError):
            class Hidden(Tag):
                @Tool(Weapon)
                def _weapon(agent):
                    return Forge(agent)

    def test_the_builder_keeps_its_three_seats(self):
        class Armed_With(Tag):
            @Tool(Weapon)
            def weapon(agent, stored=None, *, weapon=None):
                if weapon is not None:
                    Weapon(weapon)
                    return weapon
                return Forge(agent) if stored is None else stored

        gift = Sword("a gift")
        charlie = Character("Charlie")
        Armed_With(charlie, weapon=gift)
        self.assertIs(charlie.weapon, gift)
        bob = Character("Bob")
        Armed_With(bob)
        self.assertIn(bob.weapon, Weapon[:])


# ------------------------------------------------------------------
# Stacking with Constant, Secret and Public
# ------------------------------------------------------------------


class Stacking_Tests(unittest.TestCase):
    def test_a_constant_tool_is_bonded_in_either_order(self):
        class Oathbound(Tag):
            @Constant
            @Tool(Weapon)
            def relic(agent):
                return Forge(agent, "relic")

        class Sworn(Tag):
            @Tool(Weapon)
            @Constant
            def relic(agent):
                return Forge(agent, "relic")

        for tag in (Oathbound, Sworn):
            with self.subTest(tag=tag.__name__):
                agent = Character(tag.__name__)
                tag(agent)
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
            def dagger(agent):
                return Forge(agent, "dagger")

            @Action
            def Draw(agent):
                return agent.dagger

        class Hidden(Tag):
            @Tool(Weapon)
            @Secret
            def dagger(agent):
                return Forge(agent, "dagger")

            @Action
            def Draw(agent):
                return agent.dagger

        for tag in (Concealed, Hidden):
            with self.subTest(tag=tag.__name__):
                agent = Character(tag.__name__)
                tag(agent)
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
            def weapon(agent):
                return Forge(agent)

        class Displayed(Tag):
            @Tool(Weapon)
            @Public
            def weapon(agent):
                return Forge(agent)

        for tag in (Shown, Displayed):
            with self.subTest(tag=tag.__name__):
                agent = Character(tag.__name__)
                tag(agent)
                self.assertIn(agent.weapon, Weapon[:])
                with self.assertRaises(TagCompositionError):
                    agent.weapon = Sword("a stick")


# ------------------------------------------------------------------
# Overlay on a Tool slot
# ------------------------------------------------------------------


class Overlay_Tests(unittest.TestCase):
    def test_a_shape_receives_the_tool_in_the_stored_seat_and_guards_with_its_own_kind(self):
        class Paladin(Fighter):
            @Tool(Weapon, Blessed)
            def weapon(agent, stored):
                Blessed(stored)
                return stored

        pat = Character("Pat")
        Paladin(pat)
        self.assertIn(pat.weapon, Weapon[:])
        self.assertIn(pat.weapon, Blessed[:])
        plain = Forge(pat, "plain")
        with self.assertRaises(TagCompositionError):
            pat.weapon = plain                            # Blessed is asked now

    def test_a_tool_slot_stays_a_tool_slot_against_a_plain_record(self):
        class Rearmed(Fighter):
            @Record
            def weapon(agent, stored):
                return stored

        charlie = Character("Charlie")
        with self.assertRaises(TagCompositionError) as refusal:
            Rearmed(charlie)
        self.assertIn("a Tool slot stays a Tool slot", str(refusal.exception))
        self.assertIn("@Delete", str(refusal.exception))
        self.assertNotIn(charlie, Fighter)                # the whole call rolled back

    def test_a_tool_slot_stays_a_tool_slot_against_an_action(self):
        class Smith(Fighter):
            @Action
            def weapon(agent):
                return Forge(agent)

        charlie = Character("Charlie")
        with self.assertRaises(TagCompositionError) as refusal:
            Smith(charlie)
        self.assertIn("an Action cannot take it", str(refusal.exception))

    def test_an_independent_tag_cannot_take_the_slot_either_and_no_warning_precedes_the_refusal(self):
        class Other(Tag):
            @Record
            def weapon(agent):
                return "a stick"

        charlie = Character("Charlie")
        Fighter(charlie)
        held = charlie.weapon
        with warnings.catch_warnings():
            warnings.simplefilter("error", TagOverwriteWarning)
            with self.assertRaises(TagCompositionError):
                Other(charlie)
        self.assertIs(charlie.weapon, held)
        self.assertNotIn(charlie, Other)

    def test_delete_frees_the_slot_and_a_later_record_may_take_the_name(self):
        class Unarmed(Fighter):
            @Delete
            def weapon(agent):
                pass

        class Rearmed(Unarmed):
            @Record
            def weapon(agent):
                return "a stick, and nobody minds"

        charlie = Character("Charlie")
        Unarmed(charlie)
        self.assertFalse("weapon" @ charlie)
        bob = Character("Bob")
        Rearmed(bob)
        self.assertEqual(bob.weapon, "a stick, and nobody minds")

    def test_a_tool_over_a_plain_record_takes_the_slot_and_guards_it(self):
        class Carrying(Tag):
            @Record
            def weapon(agent):
                return "a stick"

        class Knight(Carrying):
            @Tool(Weapon)
            def weapon(agent, stored):
                return Forge(agent)

        kay = Character("Kay")
        Knight(kay)
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
            def weapon(agent):
                return Forge(agent)

        charlie = Character("Charlie")
        Promising(charlie)
        with self.assertRaises(TagCompositionError):
            Holding(charlie)

        class Propertied:
            def __init__(self, name): self.name = name
            @property
            def weapon(self): return "fixed"

        with self.assertRaises(TagCompositionError):
            Holding(Propertied("p"))


# ------------------------------------------------------------------
# Lifecycle: Rip and reapplication
# ------------------------------------------------------------------


class Lifecycle_Tests(unittest.TestCase):
    def test_rip_of_the_bearer_leaves_the_slot_sticky_and_guarded(self):
        charlie = Character("Charlie")
        Fighter(charlie)
        held = charlie.weapon
        del Fighter[charlie]
        self.assertNotIn(charlie, Fighter)
        self.assertTrue("weapon" @ charlie)
        self.assertIs(charlie.weapon, held)
        with self.assertRaises(TagCompositionError):
            charlie.weapon = Sword("a stick")             # sticky Contributions keep their laws

    def test_reapplication_rebuilds_an_ordinary_slot(self):
        charlie = Character("Charlie")
        Fighter(charlie)
        held = charlie.weapon
        del Fighter[charlie]
        Fighter(charlie)
        self.assertIsNot(charlie.weapon, held)
        self.assertIn(charlie.weapon, Weapon[:])

    def test_reapplication_keeps_the_tool_through_the_stored_seat(self):
        class Keeper(Tag):
            @Tool(Weapon)
            def weapon(agent, stored=None):
                return Forge(agent) if stored is None else stored

        charlie = Character("Charlie")
        Keeper(charlie)
        held = charlie.weapon
        del Keeper[charlie]
        Keeper(charlie)
        self.assertIs(charlie.weapon, held)

    def test_reapplication_keeps_a_constant_tool_without_running_the_builder(self):
        forged = []

        class Oathbound(Tag):
            @Constant
            @Tool(Weapon)
            def relic(agent):
                forged.append(agent)
                return Forge(agent, "relic")

        charlie = Character("Charlie")
        Oathbound(charlie)
        held = charlie.relic
        del Oathbound[charlie]
        self.assertIs(charlie.relic, held)                # survives Rip
        Oathbound(charlie)
        self.assertIs(charlie.relic, held)
        self.assertEqual(len(forged), 1)

    def test_rip_of_the_tools_tag_leaves_a_rogue_in_hand_that_the_bearers_post_notices(self):
        class Armed(Tag):
            @Tool(Weapon)
            def weapon(agent):
                return Forge(agent)

            @Post
            def Sound_Weapon(agent):
                return agent.weapon in Weapon[:] and Contract.Holds(agent.weapon)

        charlie = Character("Charlie")
        Armed(charlie)
        self.assertTrue(Contract.Holds(charlie))
        del Weapon[charlie.weapon]
        self.assertTrue("weapon" @ charlie)
        self.assertNotIn(charlie.weapon, Weapon[:])
        self.assertTrue(isinstance(charlie.weapon, Weapon))
        self.assertFalse(Contract.Holds(charlie))
        Weapon(charlie.weapon)                            # a fresh tagging repairs it
        self.assertTrue(Contract.Holds(charlie))

    def test_a_rip_protocol_may_disarm(self):
        class Conscript(Tag):
            @Tool(Weapon)
            def weapon(agent):
                return Forge(agent)

            @Rip
            def Disarm(agent):
                del agent.weapon

        charlie = Character("Charlie")
        Conscript(charlie)
        del Conscript[charlie]
        self.assertFalse("weapon" @ charlie)


# ------------------------------------------------------------------
# Sharing, nesting, and the two doors
# ------------------------------------------------------------------


class Sharing_Tests(unittest.TestCase):
    def test_two_bearers_may_hold_one_tool(self):
        charlie, bob = Character("Charlie"), Character("Bob")
        Fighter(charlie)
        Fighter(bob)
        bob.weapon = charlie.weapon
        self.assertIs(bob.weapon, charlie.weapon)
        del charlie.weapon                                # hand-over, line two
        self.assertFalse("weapon" @ charlie)
        self.assertIn(bob.weapon, Weapon[:])

    def test_the_tools_tags_travel_with_it(self):
        charlie, bob = Character("Charlie"), Character("Bob")
        Fighter(charlie)
        Fighter(bob)
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
            def gem(tool):
                gem = Gem()
                Jewel(gem)
                return gem

        charlie = Character("Charlie")
        Fighter(charlie)
        Socketed(charlie.weapon)
        self.assertIn(charlie.weapon.gem, Jewel[:])
        with self.assertRaises(TagCompositionError):
            charlie.weapon.gem = Gem()

    def test_a_bearers_action_reads_its_tools_secret_fails_closed(self):
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
            def vault(agent):
                vault = Sword("the vault")
                Vault(vault)
                return vault

            @Action
            def Crack(agent):
                return agent.vault.combination

        ann = Character("Ann")
        Guard(ann)
        self.assertEqual(ann.vault.Open(), "1234")
        with self.assertRaises(AttributeError):
            ann.Crack()


# ------------------------------------------------------------------
# Hosts, presence, runtime types
# ------------------------------------------------------------------


class Host_Tests(unittest.TestCase):
    def test_a_host_write_hook_keeps_its_behaviour_and_admission_still_runs(self):
        writes = []

        class Logging_Host:
            def __init__(self, name): self.name = name
            def __setattr__(agent, name, value):
                writes.append(name)
                agent.__dict__[name] = value

        lou = Logging_Host("Lou")
        Fighter(lou)
        writes.clear()
        with self.assertRaises(TagCompositionError):
            lou.weapon = Sword("a stick")
        self.assertEqual(writes, [])                      # refused before the host's hook ran
        lou.weapon = Forge(lou, "two")
        self.assertEqual(writes, ["weapon"])

    def test_presence_answers_for_the_slot_without_running_anything(self):
        charlie = Character("Charlie")
        self.assertFalse(hasattr(charlie, "weapon"))
        Fighter(charlie)
        self.assertTrue("weapon" @ charlie)
        self.assertTrue("weapon" @ Fighter[charlie])
        del charlie.weapon
        self.assertFalse("weapon" @ charlie)

    def test_a_tool_slot_does_not_multiply_runtime_types(self):
        charlie, bob = Character("Charlie"), Character("Bob")
        Fighter(charlie)
        Fighter(bob)
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
        Fighter(charlie)
        Sharp(charlie.weapon)
        charlie.weapon.damage = 0
        self.assertFalse(Contract.Holds(charlie.weapon))
        self.assertTrue(Contract.Holds(charlie))          # nothing on Charlie promised about the sword


if __name__ == "__main__":
    unittest.main()
