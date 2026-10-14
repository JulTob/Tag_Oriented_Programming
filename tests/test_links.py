"""Links: a Tag of one's own (STEP-SPEC-22).

Organised as the STEP's Acceptance requirements: the rules and their
refusals, the five findings of the hand-made workaround as regressions,
the Pair, the seats, Bases, extending a held Link, the closed slot, the
doors, the Relation's refused spellings, ending in reference cycles, and
the barrier; and a Shape gained while a linking is under way.
"""

import asyncio
import contextvars
import copy
import gc
import inspect
import sys
import types
import unittest
import warnings
import weakref

from TopKit import (Action, At_Exit, Contract, Delete, Flag, Imprint,
                    Keyword, Link, Operation, Outline, Pin, Post, Pre, Public, Record,
                    Report, Rip, Secret, Tag, TagCompositionError,
                    TagDeclarationError, TagError, TagImprintError,
                    TagOverwriteWarning, TagPostconditionError,
                    TagPreconditionError, TagResolutionError,
                    TagRogueAccessError, Tags, Tool, Underlay)
from TopKit.lifecycle import _teardown_all
from TopKit.links import _stepper_of
from TopKit.links import _pair_ends, _pair_form, _pair_tag, _pair_tags_of, _record_of
from TopKit.state import _state_of


class Character:
    def __init__(character, name="x"):
        character.name = name
        character.honest = True

    def __repr__(character):
        return character.name


class Social(Tag):
    @Link
    class Knows(Tag):
        @Pre
        def Not_Oneself(agent, contact):
            return contact is not agent

        @Record
        def since(agent, contact, *, since=None):
            return since

        def Greet(agent, contact):
            return f"{agent.name} waves at {contact.name}"

    @Link
    class Trusts(Knows):
        @Post
        def Still_Honest(agent, contact):
            return contact.honest

        def Confide(agent, contact, secret):
            return f"{agent.name} tells {contact.name}: {secret}"


def People(*names):
    return [Character(name) for name in names]


# ------------------------------------------------------------------
# Granting (section 4)
# ------------------------------------------------------------------


class Granting_Tests(unittest.TestCase):
    def test_each_agent_holds_a_distinct_link_under_the_relations_name(self):
        charlie, bob = People("Charlie", "Bob")
        Social(charlie)
        Social(bob)
        self.assertIsNot(charlie.Knows, bob.Knows)
        self.assertIsNot(charlie.Knows, Social.Knows)
        self.assertTrue("Knows" @ charlie)
        self.assertEqual(charlie.Knows.__name__, "Knows")

    def test_a_link_is_the_whole_of_its_agents_link_and_the_name_alone_is_no_tag(self):
        charlie, ruth, bob = People("Charlie", "Ruth", "Bob")
        Social(charlie)
        Social(ruth)
        charlie.Knows(bob)
        with self.assertRaises(TagCompositionError):
            bob in Social.Knows                           # 'Knows' by itself is no Tag
        self.assertIn(bob, charlie.Knows)                 # Charlie's Link answers
        self.assertNotIn(bob, ruth.Knows)                 # Ruth's is another Tag
        self.assertTrue(isinstance(bob, charlie.Knows))
        self.assertFalse(isinstance(bob, ruth.Knows))
        self.assertIsNot(charlie.Knows, ruth.Knows)
        self.assertEqual(list(charlie.Knows), [bob])
        self.assertEqual(list(ruth.Knows), [])
        for link in (charlie.Knows, ruth.Knows):          # printed alike: no Agent is named
            self.assertNotIn("Charlie", repr(link))
            self.assertNotIn("Ruth", repr(link))

    def test_a_link_is_built_at_parts_and_rolled_back_with_the_call(self):
        class Failing(Tag):
            @Link
            class Knows(Tag):
                pass

            @Record
            def broken(agent):
                raise ValueError("no")

        charlie = Character("Charlie")
        with self.assertRaises(TagCompositionError):
            Failing(charlie)
        self.assertFalse(hasattr(charlie, "Knows"))
        self.assertNotIn(charlie, Failing)

    def test_a_held_link_is_read_only(self):
        charlie = Character("Charlie")
        Social(charlie)
        held = charlie.Knows
        for write in (
                lambda: setattr(charlie, "Knows", 3),
                lambda: delattr(charlie, "Knows"),
                lambda: object.__setattr__(charlie, "Knows", 3),
                ):
            with self.subTest(write=write):
                with self.assertRaises(TagCompositionError):
                    write()
        self.assertIs(charlie.Knows, held)

    def test_a_host_setter_never_runs_for_a_link_name(self):
        writes = []

        class Logging:
            def __init__(self, name): self.name = name
            def __setattr__(agent, name, value):
                writes.append(name)
                object.__setattr__(agent, name, value)   # a host must let the kit give it its runtime type (STEP-SPEC-37)

        lou = Logging("Lou")
        Social(lou)
        writes.clear()
        with self.assertRaises(TagCompositionError):
            lou.Knows = 3
        self.assertEqual(writes, [])

    def test_links_are_sticky_and_reapplication_keeps_them(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Knows(ruth, since=2010)
        held = charlie.Knows
        del Social[charlie]
        self.assertIs(charlie.Knows, held)               # sticky (rule 4.5)
        self.assertIn(ruth, charlie.Knows)
        Social(charlie)
        self.assertIs(charlie.Knows, held)               # identity, Field and Pairs kept
        self.assertEqual(charlie.Knows[ruth].since, 2010)

    def test_the_kit_never_checks_the_linking_agents_membership(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        del Social[charlie]
        charlie.Knows(ruth)                               # a Rogue may link: a gate that cares says so
        self.assertIn(ruth, charlie.Knows)


# ------------------------------------------------------------------
# Linking (section 5)
# ------------------------------------------------------------------


class Linking_Tests(unittest.TestCase):
    def test_the_summary(self):
        charlie, bob, ruth = People("Charlie", "Bob", "Ruth")
        Social(charlie)
        Social(bob)
        charlie.Knows(ruth, since=2010)
        self.assertIn(ruth, charlie.Knows)
        self.assertNotIn(ruth, bob.Knows)
        self.assertEqual(charlie.Knows[ruth].since, 2010)
        self.assertEqual(charlie.Knows[ruth].Greet(), "Charlie waves at Ruth")
        bob.Knows(ruth)
        self.assertEqual(list(charlie.Knows & bob.Knows), [ruth])
        del charlie.Knows[ruth]
        self.assertNotIn(ruth, charlie.Knows)
        self.assertTrue(isinstance(ruth, charlie.Knows))   # was ever linked

    def test_every_ring_zero_act_works_on_a_link(self):
        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Social(charlie)
        charlie.Knows(ruth)
        charlie.Knows(sam)
        self.assertEqual(list(charlie.Knows), [ruth, sam])
        self.assertEqual(len(charlie.Knows), 2)
        self.assertTrue(charlie.Knows)
        self.assertEqual(list(charlie.Knows[:]), [ruth, sam])
        self.assertEqual(list(~charlie.Knows), [])
        self.assertEqual(list(charlie.Knows - charlie.Trusts), [ruth, sam])
        self.assertEqual(f"{charlie.Knows:form}", "Knows")

    def test_the_gate_refuses_and_nothing_changes(self):
        charlie = Character("Charlie")
        Social(charlie)
        with self.assertRaises(TagPreconditionError):
            charlie.Knows(charlie)                        # Not_Oneself
        self.assertNotIn(charlie, charlie.Knows)
        with self.assertRaises(TagResolutionError):
            charlie.Knows[charlie]

    def test_a_failing_pair_record_rolls_the_linking_back(self):
        class Strict(Tag):
            @Link
            class Knows(Tag):
                @Record
                def broken(agent, contact):
                    raise ValueError("no")

        charlie, ruth = People("Charlie", "Ruth")
        Strict(charlie)
        with self.assertRaises(TagCompositionError):
            charlie.Knows(ruth)
        self.assertNotIn(ruth, charlie.Knows)
        self.assertEqual(Tags(ruth), ())
        self.assertIs(type(ruth), Character)              # she never became an Agent
        with self.assertRaises(TagResolutionError):
            charlie.Knows[ruth]

    def test_a_contacts_refused_entry_rolls_the_pair_back(self):
        class Greeting(Tag):
            @Record
            def Greet(agent): return "her own Record"

        class Club(Tag):
            @Link
            class Member(Tag):
                @Record
                def since(agent, contact): return 1

                @Public
                def Greet(agent, contact): return "a line"

        charlie, ruth = People("Charlie", "Ruth")
        Club(charlie)
        Greeting(ruth)
        with self.assertRaises(TagCompositionError):
            charlie.Member(ruth)                          # the line cannot take her Record's name
        self.assertNotIn(ruth, charlie.Member)
        self.assertEqual(ruth.Greet, "her own Record")
        with self.assertRaises(TagResolutionError):
            charlie.Member[ruth]

    def test_an_imprint_failure_raises_and_the_linking_stays(self):
        class Shaky(Tag):
            @Link
            class Knows(Tag):
                @Imprint
                def Train(agent, contact):
                    raise ValueError("training failed")

        charlie, ruth = People("Charlie", "Ruth")
        Shaky(charlie)
        with self.assertRaises(TagImprintError):
            charlie.Knows(ruth)
        self.assertIn(ruth, charlie.Knows)
        self.assertIsNotNone(charlie.Knows[ruth])

    def test_a_broken_pair_promise_raises_and_the_linking_stays(self):
        charlie, ruth = People("Charlie", "Ruth")
        ruth.honest = False
        Social(charlie)
        with self.assertRaises(TagPostconditionError):
            charlie.Trusts(ruth)
        self.assertIn(ruth, charlie.Trusts)
        self.assertIn(ruth, ~charlie.Trusts)

    def test_the_contacts_own_promises_are_rechecked_at_linking(self):
        class Honest(Tag):
            @Post
            def Tells_Truth(agent):
                return agent.honest

        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        Honest(ruth)
        ruth.honest = False
        with self.assertRaises(TagPostconditionError):
            charlie.Knows(ruth)
        self.assertIn(ruth, charlie.Knows)                # a broken one raises, and the linking stays

    def test_reapplying_is_a_noop_so_a_link_back_ends_after_one_echo(self):
        class Friendly(Tag):
            @Link
            class Friends(Tag):
                @Imprint
                def Both_Ways(agent, contact):
                    Friendly(contact)
                    contact.Friends(agent)

        ann, bob = People("Ann", "Bob")
        Friendly(ann)
        ann.Friends(bob)
        self.assertIn(bob, ann.Friends)
        self.assertIn(ann, bob.Friends)

    def test_a_nested_linking_refusal_is_the_imprints_failure(self):
        class Picky(Tag):
            @Link
            class Knows(Tag):
                @Pre
                def Never(agent, contact):
                    return False

        class Introducing(Tag):
            @Link
            class Meets(Tag):
                @Imprint
                def Introduce(agent, contact):
                    agent.Knows(contact)

        charlie, ruth = People("Charlie", "Ruth")
        Picky(charlie)
        Introducing(charlie)
        with self.assertRaises(TagImprintError) as raised:
            charlie.Meets(ruth)
        self.assertIsInstance(raised.exception.__cause__, TagPreconditionError)
        self.assertIn(ruth, charlie.Meets)                # the linking stays (§0.6)

    def test_a_linking_inside_a_rolled_back_call_is_undone(self):
        class Joining(Tag):
            @Record
            def friend(agent, *, friend=None):
                agent.Knows(friend)
                return friend

            @Record
            def broken(agent):
                raise ValueError("no")

        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        with self.assertRaises(TagCompositionError):
            Joining(charlie, friend=ruth)
        self.assertNotIn(ruth, charlie.Knows)

    def test_neither_seat_is_ever_none_and_classes_are_refused(self):
        charlie = Character("Charlie")
        Social(charlie)
        with self.assertRaises(TagCompositionError):
            charlie.Knows(None)
        with self.assertRaises(TagCompositionError):
            charlie.Knows(Character)

    def test_a_contact_becomes_an_agent_and_copying_her_is_refused(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Knows(ruth)
        self.assertIsNot(type(ruth), Character)
        with self.assertRaises(TagCompositionError):
            copy.copy(ruth)

    def test_a_contact_without_weak_references_is_refused(self):
        class Plain:
            __slots__ = ("__dict__",)

        charlie = Character("Charlie")
        Social(charlie)
        with self.assertRaises(TagCompositionError):
            charlie.Knows(Plain())

    def test_unlink_every_contact(self):
        charlie = Character("Charlie")
        Social(charlie)
        people = People("A", "B", "C")
        for person in people:
            charlie.Knows(person)
        del charlie.Knows[:]
        self.assertEqual(list(charlie.Knows[:]), [])
        with self.assertRaises(TypeError):
            del charlie.Knows[0:1]

    def test_unlink_every_contact_is_refused_while_a_shape_link_holds_one(self):
        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Social(charlie)
        charlie.Knows(sam)
        charlie.Trusts(ruth)
        with self.assertRaises(TagCompositionError):
            del charlie.Knows[:]
        self.assertEqual(list(charlie.Knows[:]), [sam, ruth])   # nothing changed


# ------------------------------------------------------------------
# The Pair (section 7)
# ------------------------------------------------------------------


class Pair_Tests(unittest.TestCase):
    def test_records_are_read_and_written_as_attributes(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Knows(ruth, since=2010)
        charlie.Knows[ruth].since = 2011
        self.assertEqual(charlie.Knows[ruth].since, 2011)

    def test_actions_take_arguments_after_the_two_seats(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Trusts(ruth)
        self.assertEqual(
                charlie.Trusts[ruth].Confide("the map"),
                "Charlie tells Ruth: the map",
                )

    def test_conditions_are_read_by_name_as_plain_booleans(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Trusts(ruth)
        self.assertIs(charlie.Trusts[ruth].Still_Honest, True)
        ruth.honest = False
        self.assertIs(charlie.Trusts[ruth].Still_Honest, False)

    def test_a_pair_is_sound_or_defective_on_its_own(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Trusts(ruth)
        self.assertTrue(charlie.Trusts[ruth])
        ruth.honest = False
        self.assertFalse(charlie.Trusts[ruth])
        self.assertEqual(list(charlie.Trusts), [])
        self.assertEqual(list(~charlie.Trusts), [ruth])
        self.assertTrue(bool(ruth))             # finding 4: never defective elsewhere

    def test_the_sound_population_needs_the_contacts_own_contract_too(self):
        class Honest(Tag):
            @Post
            def Tells_Truth(agent):
                return agent.honest

        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Knows(ruth)
        Honest(ruth)
        ruth.honest = False
        self.assertEqual(list(charlie.Knows), [])
        self.assertEqual(list(~charlie.Knows), [ruth])

    def test_one_pair_for_each_contact_across_a_links_form(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Trusts(ruth, since=2015)
        self.assertIn(ruth, charlie.Knows)                # linking is closed upward
        self.assertIs(charlie.Knows[ruth], charlie.Trusts[ruth])
        self.assertEqual(charlie.Knows[ruth].since, 2015)

    def test_independent_links_of_one_agent_have_separate_pairs(self):
        class Work(Tag):
            @Link
            class Colleague(Tag):
                @Record
                def since(agent, contact, *, since=None): return since

        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        Work(charlie)
        charlie.Knows(ruth, since=1)
        charlie.Colleague(ruth, since=2)
        self.assertIsNot(charlie.Knows[ruth], charlie.Colleague[ruth])
        self.assertEqual((charlie.Knows[ruth].since, charlie.Colleague[ruth].since), (1, 2))

    def test_a_flag_link_answers_its_words_on_the_pair_never_on_the_contact(self):
        class Guild(Tag):
            @Link
            @Flag("Trusted")
            class Ally(Tag):
                pass

        charlie, ruth = People("Charlie", "Ruth")
        Guild(charlie)
        charlie.Ally(ruth)
        self.assertIn("Ally", charlie.Ally[ruth])
        self.assertIn("Trusted", charlie.Ally[ruth])
        self.assertTrue(Keyword(charlie.Ally[ruth], "Trusted"))
        self.assertFalse(Keyword(ruth, "Ally"))
        self.assertFalse(Keyword(ruth, "Trusted"))

    def test_the_links_reports_and_operations_belong_to_the_link(self):
        class Bounded(Tag):
            @Link
            class Knows(Tag):
                @Report
                def capacity(link):
                    return 2

                @Action
                @Record
                def note(agent, contact): return None

                @Pre
                def Has_Room(agent, contact):
                    return len(agent.Knows[:]) < agent.Knows.capacity

        fay = Character("Fay")
        Bounded(fay)
        people = People("A", "B", "C")
        self.assertEqual(fay.Knows.capacity, 2)
        fay.Knows(people[0])
        fay.Knows(people[1])
        with self.assertRaises(TagPreconditionError):
            fay.Knows(people[2])

    def test_reaching_a_pair_after_it_ended_is_a_resolution_failure(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Knows(ruth)
        del charlie.Knows[ruth]
        with self.assertRaises(TagResolutionError):
            charlie.Knows[ruth]
        charlie.Knows(ruth, since=3)                      # linking again builds it fresh
        self.assertEqual(charlie.Knows[ruth].since, 3)


# ------------------------------------------------------------------
# Seats (section 3)
# ------------------------------------------------------------------


class Seat_Tests(unittest.TestCase):
    def test_each_kind_reads_its_own_seats_after_the_two(self):
        class Ledger(Tag):
            @Link
            class Owes(Tag):
                @Record
                def amount(agent, contact, stored, *, amount=0):
                    return (stored or 0) + amount

                @Pre
                def Positive(agent, contact, *, amount=0):
                    return amount >= 0

                def Remind(agent, contact, greeting="hi"):
                    return f"{greeting}, {contact.name}: {agent.Owes[contact].amount}"

                @Imprint
                def Note(agent, contact, *, amount=0):
                    agent.log.append((contact.name, amount))

        charlie, ruth = People("Charlie", "Ruth")
        charlie.log = []
        Ledger(charlie)
        charlie.Owes(ruth, amount=5)
        self.assertEqual(charlie.Owes[ruth].amount, 5)
        self.assertEqual(charlie.Owes[ruth].Remind("hello"), "hello, Ruth: 5")
        self.assertEqual(charlie.log, [("Ruth", 5)])
        with self.assertRaises(TagPreconditionError):
            charlie.Owes(Character("Sam"), amount=-1)

    def test_an_underlay_extends_an_action_after_the_two_seats(self):
        class Polite(Social):
            @Link
            class Knows(Social.Knows):
                @Action
                @Underlay
                def Greet(agent, contact, underlay):
                    return underlay() + ", politely"

        charlie, ruth = People("Charlie", "Ruth")
        Polite(charlie)
        charlie.Knows(ruth)
        self.assertEqual(charlie.Knows[ruth].Greet(), "Charlie waves at Ruth, politely")

    def test_fewer_than_two_seats_is_refused_at_class_use(self):
        with self.assertRaises(TagDeclarationError) as refusal:
            class Broken(Tag):
                @Link
                class Knows(Tag):
                    @Pre
                    def Is_Person(agent):
                        return True
        self.assertIn("def Is_Person(agent, contact)", str(refusal.exception))

    def test_a_contact_seat_with_a_default_is_refused(self):
        with self.assertRaises(TagDeclarationError):
            class Broken(Tag):
                @Link
                class Knows(Tag):
                    def Greet(agent, contact=None):
                        return None

    def test_an_underlay_needs_a_third_seat(self):
        with self.assertRaises(TagDeclarationError) as refusal:
            class Broken(Tag):
                @Link
                class Knows(Tag):
                    @Action
                    @Underlay
                    def Greet(agent, contact):
                        return None
        self.assertIn("underlay", str(refusal.exception))

    def test_reports_and_operations_take_the_link_alone(self):
        class Fine(Tag):
            @Link
            class Knows(Tag):
                @Report
                def capacity(link): return 3

        charlie = Character("Charlie")
        Fine(charlie)
        self.assertEqual(charlie.Knows.capacity, 3)

    def test_an_input_named_like_a_seat_is_refused_at_linking_nothing_changed(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        for seat in ("agent", "contact"):
            with self.subTest(seat=seat):
                with self.assertRaises(TagDeclarationError) as refusal:
                    charlie.Knows(ruth, **{seat: 1})
                self.assertIn("after `*`", str(refusal.exception))
        self.assertNotIn(ruth, charlie.Knows)

    def test_an_input_named_like_the_stored_seat_is_refused(self):
        class Stored(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, stored): return stored

        charlie, ruth = People("Charlie", "Ruth")
        Stored(charlie)
        with self.assertRaises(TagDeclarationError):
            charlie.Knows(ruth, stored=1)
        self.assertNotIn(ruth, charlie.Knows)


# ------------------------------------------------------------------
# Bases (rule 2.4, rules 5.2 and 5.3)
# ------------------------------------------------------------------


class Base_Tests(unittest.TestCase):
    def test_a_relations_bases_resolve_per_agent(self):
        charlie, bob = People("Charlie", "Bob")
        Social(charlie)
        Social(bob)
        self.assertTrue(issubclass(charlie.Trusts, charlie.Knows))
        self.assertFalse(issubclass(charlie.Trusts, bob.Knows))
        self.assertFalse(issubclass(charlie.Trusts, Social.Knows))

    def test_linking_through_a_shape_link_links_its_bases_first(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Trusts(ruth)
        self.assertIn(ruth, charlie.Knows)
        self.assertIn(ruth, charlie.Trusts)

    def test_unlinking_a_base_link_is_refused_while_a_shape_link_holds_her(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Trusts(ruth)
        with self.assertRaises(TagCompositionError):
            del charlie.Knows[ruth]                       # §0.7, as main says today
        del charlie.Trusts[ruth]
        self.assertIn(ruth, charlie.Knows)
        self.assertIsNotNone(charlie.Knows[ruth])         # the Pair stays (rule 8.1)
        del charlie.Knows[ruth]
        self.assertNotIn(ruth, charlie.Knows)

    def test_a_base_relation_from_a_base_of_the_declaring_tag(self):
        class Close(Social):
            @Link
            class Intimate(Social.Trusts):
                pass

        charlie, ruth = People("Charlie", "Ruth")
        Close(charlie)
        charlie.Intimate(ruth)
        self.assertIn(ruth, charlie.Knows)
        self.assertIs(charlie.Knows[ruth], charlie.Intimate[ruth])

    def test_an_ordinary_tag_as_a_base_of_a_relation_is_refused(self):
        class Vetted(Tag):
            pass

        with self.assertRaises(TagDeclarationError) as refusal:
            class Broken(Tag):
                @Link
                class Knows(Vetted):
                    pass
        self.assertIn("Imprint", str(refusal.exception))

    def test_a_relation_of_another_tag_as_a_base_is_refused(self):
        with self.assertRaises(TagDeclarationError):
            class Other(Tag):
                @Link
                class Trusts(Social.Knows):
                    pass

    def test_a_relation_or_a_link_as_the_base_of_an_ordinary_tag_is_refused(self):
        with self.assertRaises(TagDeclarationError):
            class Nested(Tag):
                class Fake(Social.Knows):
                    pass

        class Top(Social.Knows):
            pass

        with self.assertRaises(TagDeclarationError):
            Top(Character("x"))

        charlie = Character("Charlie")
        Social(charlie)
        with self.assertRaises(TagDeclarationError):
            class From_A_Link(charlie.Knows):
                pass


# ------------------------------------------------------------------
# Extending a held Link (rules 2.6 and 4.6)
# ------------------------------------------------------------------


class Spy(Social):
    @Link
    class Knows(Social.Knows):
        @Secret
        @Record
        def cover_story(agent, contact):
            return "a cousin from Lyon"

        @Action
        @Underlay
        def Greet(agent, contact, underlay):
            return underlay() + f", as {agent.Knows[contact].cover_story}"


class Extension_Tests(unittest.TestCase):
    def test_a_shape_extends_every_pair_the_link_already_holds(self):
        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Social(charlie)
        charlie.Knows(ruth, since=2010)
        held = charlie.Knows
        Spy(charlie)
        self.assertIs(charlie.Knows, held)                # identity kept
        self.assertEqual(list(charlie.Knows[:]), [ruth])  # Field kept
        self.assertEqual(
                charlie.Knows[ruth].Greet(),
                "Charlie waves at Ruth, as a cousin from Lyon",
                )
        self.assertEqual(charlie.Knows[ruth].since, 2010)
        charlie.Knows(sam)                                # later linkings get every Layer
        self.assertEqual(
                charlie.Knows[sam].Greet(),
                "Charlie waves at Sam, as a cousin from Lyon",
                )

    def test_granting_and_extending_in_one_call_builds_both_layers(self):
        charlie, ruth = People("Charlie", "Ruth")
        Spy(charlie)
        charlie.Knows(ruth)
        self.assertTrue(charlie.Knows[ruth].Greet().endswith("Lyon"))

    def test_one_pairs_refusal_refuses_the_whole_call(self):
        class Strict(Social):
            @Link
            class Knows(Social.Knows):
                @Pre
                def Only_Honest(agent, contact):
                    return contact.honest

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        sam.honest = False
        Social(charlie)
        charlie.Knows(ruth)
        charlie.Knows(sam)
        with self.assertRaises(TagPreconditionError):
            Strict(charlie)
        self.assertNotIn(charlie, Strict)
        charlie.Knows(Character("Tom"))                   # the Link has no Strict Layer
        self.assertFalse(hasattr(charlie.Knows[ruth], "Only_Honest"))

    def test_a_failing_pair_record_rolls_the_whole_call_back(self):
        class Leveled(Tag):
            @Link
            class Knows(Tag):
                @Record
                def level(agent, contact): return 1

        class Raised(Leveled):
            @Link
            class Knows(Leveled.Knows):
                @Record
                def level(agent, contact, stored): return stored + 1

            @Record
            def broken(agent):
                raise ValueError("later failure")

        charlie, ruth = People("Charlie", "Ruth")
        Leveled(charlie)
        charlie.Knows(ruth)
        with self.assertRaises(TagCompositionError):
            Raised(charlie)
        self.assertEqual(charlie.Knows[ruth].level, 1)
        self.assertNotIn(charlie, Raised)

    def test_imprints_and_promises_run_for_every_pair(self):
        seen = []

        class Audited(Social):
            @Link
            class Knows(Social.Knows):
                @Imprint
                def Audit(agent, contact):
                    seen.append(contact.name)

                @Post
                def Still_Honest_Too(agent, contact):
                    return contact.honest

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Social(charlie)
        charlie.Knows(ruth)
        charlie.Knows(sam)
        sam.honest = False
        with self.assertRaises(TagPostconditionError):
            Audited(charlie)
        self.assertEqual(seen, ["Ruth", "Sam"])
        self.assertIn(charlie, Audited)                   # after Commit: the Layers stay
        self.assertEqual(list(~charlie.Knows), [sam])

    def test_a_same_name_relation_that_does_not_extend_is_refused(self):
        with self.assertRaises(TagDeclarationError) as refusal:
            class Rival(Social):
                @Link
                class Knows(Tag):
                    pass
        self.assertIn("class Knows(Social.Knows)", str(refusal.exception))


# ------------------------------------------------------------------
# The closed slot (rule 4.4)
# ------------------------------------------------------------------


class Closed_Slot_Tests(unittest.TestCase):
    def test_nothing_else_arrives_at_a_links_name(self):
        class Recorded(Tag):
            @Record
            def Knows(agent): return 1

        class Acting(Tag):
            def Knows(agent): return 1

        class Promising(Tag):
            @Post
            def Knows(agent): return True

        class Deleting(Social):
            @Delete
            def Knows(agent): pass

        for intruder in (Recorded, Acting, Promising):
            with self.subTest(intruder=intruder.__name__):
                charlie = Character("Charlie")
                Social(charlie)
                held = charlie.Knows
                with self.assertRaises(TagCompositionError):
                    intruder(charlie)
                self.assertIs(charlie.Knows, held)
        with self.assertRaises(TagCompositionError):
            Deleting(Character("Dan"))

    def test_a_link_never_arrives_where_something_is(self):
        class Recorded(Tag):
            @Record
            def Knows(agent): return 1

        class Hosting:
            def Knows(self): return "host"

        charlie = Character("Charlie")
        Recorded(charlie)
        with self.assertRaises(TagCompositionError):
            Social(charlie)
        self.assertNotIn(charlie, Social)
        with self.assertRaises(TagCompositionError):
            Social(Hosting())


# ------------------------------------------------------------------
# Publication: seen by the Contact, or in-house (rule 2.7)
# ------------------------------------------------------------------


class Club(Tag):
    @Secret
    @Record
    def motto(agent):
        return "the Agent's secret"

    @Link
    class Member(Tag):
        @Public
        def Greet(agent, contact):
            return f"{agent.name} greets {contact.name}"

        @Public
        @Record
        def badge(agent, contact, *, badge=None):
            return badge

        @Secret
        @Record
        def code(agent, contact):
            return "the Pair's secret"

        def Reveal(agent, contact):
            return (agent.motto, agent.Member[contact].code)

        def Peek(agent, contact):
            return contact.diary

        @Public
        @Report
        def rules(link):
            return "be kind"


class Diarist(Tag):
    @Secret
    @Record
    def diary(agent):
        return "the Contact's secret"

    def Write(agent):
        return agent.Greet()


class Publication_Tests(unittest.TestCase):
    def test_public_members_are_lines_onto_the_contact(self):
        charlie, ruth = People("Charlie", "Ruth")
        Club(charlie)
        charlie.Member(ruth, badge=7)
        self.assertEqual(ruth.Greet(), "Charlie greets Ruth")   # the Agent fills the first seat
        self.assertEqual(ruth.badge, 7)
        self.assertEqual(ruth.rules, "be kind")
        charlie.Member[ruth].badge = 9
        self.assertEqual(ruth.badge, 9)                   # read live from the Pair
        with self.assertRaises(AttributeError):
            ruth.badge = 1                                # read-only on the Contact

    def test_a_line_answers_members_only(self):
        charlie, ruth = People("Charlie", "Ruth")
        Club(charlie)
        charlie.Member(ruth)
        del charlie.Member[ruth]
        with self.assertRaises(TagRogueAccessError):
            ruth.Greet()
        with self.assertRaises(TagRogueAccessError):
            ruth.badge

    def test_the_last_linking_is_what_she_sees_with_the_usual_warning(self):
        charlie, bob, ruth = People("Charlie", "Bob", "Ruth")
        Club(charlie)
        Club(bob)
        charlie.Member(ruth)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            bob.Member(ruth)
        self.assertTrue(any(issubclass(w.category, TagOverwriteWarning) for w in caught))
        self.assertEqual(ruth.Greet(), "Bob greets Ruth")  # a line, not a fan-out

    def test_unpublished_members_never_reach_the_contact(self):
        charlie, ruth = People("Charlie", "Ruth")
        Club(charlie)
        charlie.Member(ruth)
        for name in ("Reveal", "Peek", "code", "motto", "Member"):
            with self.subTest(name=name):
                self.assertFalse(hasattr(ruth, name))


# ------------------------------------------------------------------
# The doors (rule 3.6)
# ------------------------------------------------------------------


class Door_Tests(unittest.TestCase):
    def test_the_agents_and_the_pairs_secrets_resolve_the_contacts_never(self):
        charlie, ruth = People("Charlie", "Ruth")
        Club(charlie)
        Diarist(ruth)
        charlie.Member(ruth)
        self.assertEqual(
                charlie.Member[ruth].Reveal(),
                ("the Agent's secret", "the Pair's secret"),
                )
        with self.assertRaises(AttributeError):
            charlie.Member[ruth].code                     # outside the Link's functions
        with self.assertRaises(AttributeError):
            charlie.Member[ruth].Peek()                   # the Contact's door stays shut

    def test_the_contacts_door_stays_shut_even_when_her_own_action_calls_the_line(self):
        class Snooping(Tag):
            @Link
            class Member(Tag):
                @Public
                def Greet(agent, contact):
                    return contact.diary

        charlie, ruth = People("Charlie", "Ruth")
        Snooping(charlie)
        Diarist(ruth)
        charlie.Member(ruth)
        with self.assertRaises(AttributeError):
            ruth.Write()                                  # her door opens for Write, not for the Link

    def test_a_teardown_reads_the_agents_secrets_never_the_contacts(self):
        seen = []

        class Keeping(Tag):
            @Secret
            @Record
            def ledger(agent): return "agent ledger"

            @Link
            class Knows(Tag):
                @Rip
                def Forget(agent, contact):
                    seen.append(agent.ledger)
                    try:
                        contact.diary
                    except AttributeError:
                        seen.append("shut")

        charlie, ruth = People("Charlie", "Ruth")
        Keeping(charlie)
        Diarist(ruth)
        charlie.Knows(ruth)
        del charlie.Knows[ruth]
        self.assertEqual(seen, ["agent ledger", "shut"])
        seen.clear()
        sam = Character("Sam")
        Diarist(sam)
        charlie.Knows(sam)
        del sam
        gc.collect()
        self.assertEqual(seen, ["agent ledger", "shut"])  # at the Contact's deletion too


# ------------------------------------------------------------------
# The Relation itself (section 9)
# ------------------------------------------------------------------


class Relation_Tests(unittest.TestCase):
    def test_every_act_on_the_relation_is_refused_and_points_to_a_link(self):
        ruth = Character("Ruth")
        charlie = Character("Charlie")
        Social(charlie)
        acts = {
                "apply": lambda: Social.Knows(ruth),
                "in": lambda: ruth in Social.Knows,
                "isinstance": lambda: isinstance(ruth, Social.Knows),
                "iter": lambda: list(Social.Knows),
                "len": lambda: len(Social.Knows),
                "bool": lambda: bool(Social.Knows),
                "invert": lambda: ~Social.Knows,
                "field": lambda: Social.Knows[:],
                "view": lambda: Social.Knows[ruth],
                "and": lambda: Social.Knows & charlie.Knows,
                "or": lambda: charlie.Knows | Social.Knows,
                "sub": lambda: charlie.Knows - Social.Knows,
                "rip": lambda: Social.Knows.__delitem__(ruth),
                "rip all": lambda: Social.Knows.__delitem__(slice(None)),
                }
        for name, act in acts.items():
            with self.subTest(act=name):
                with self.assertRaises(TagCompositionError) as refusal:
                    act()
                self.assertIn("is a Relation: link through an Agent", str(refusal.exception))

    def test_the_relation_keeps_types_own_union(self):
        self.assertEqual((Social.Knows | None).__args__, (Social.Knows, type(None)))

    def test_a_relation_is_not_a_kind_and_never_a_pin(self):
        with self.assertRaises(TagDeclarationError):
            Tool(Social.Knows)
        with self.assertRaises(TagDeclarationError):
            class Broken(Tag):
                @Link
                @Pin
                class Knows(Tag):
                    pass
        with self.assertRaises(TagDeclarationError):
            @Pin
            class Pinned(Tag):
                @Link
                class Knows(Tag):
                    pass

    def test_a_link_name_is_ordinary(self):
        with self.assertRaises(TagDeclarationError):
            class Broken(Tag):
                __len__ = Link(type("Counted", (Tag,), {}))


# ------------------------------------------------------------------
# Ending (section 8), including reference cycles
# ------------------------------------------------------------------


class Net(Tag):
    @Link
    class Knows(Tag):
        @Rip
        def Forget(agent, contact):
            Net.log.append((
                    agent.name if agent is not None else None,
                    contact.name if contact is not None else None,
                    ))

    log = []


class Ending_Tests(unittest.TestCase):
    def setUp(self):
        Net.log.clear()

    def test_unlinking_runs_the_teardowns_with_both_seats(self):
        charlie, ruth = People("Charlie", "Ruth")
        Net(charlie)
        charlie.Knows(ruth)
        del charlie.Knows[ruth]
        self.assertEqual(Net.log, [("Charlie", "Ruth")])

    def test_a_contacts_deletion_unlinks_her(self):
        charlie = Character("Charlie")
        Net(charlie)
        ruth = Character("Ruth")
        charlie.Knows(ruth)
        del ruth
        gc.collect()
        self.assertEqual(Net.log, [("Charlie", "Ruth")])
        self.assertEqual(list(charlie.Knows[:]), [])

    def test_the_agents_deletion_ends_its_links_with_the_dying_agent(self):
        charlie, ruth = People("Charlie", "Ruth")
        Net(charlie)
        charlie.Knows(ruth)
        held = charlie.Knows
        reference = weakref.ref(charlie)
        del charlie
        gc.collect()
        self.assertIsNone(reference())                    # finding 1: a Link never keeps its Agent alive
        self.assertEqual(Net.log, [("Charlie", "Ruth")])
        self.assertEqual(list(held[:]), [])

    def test_a_link_that_outlives_its_agent(self):
        charlie, ruth = People("Charlie", "Ruth")
        Net(charlie)
        charlie.Knows(ruth)
        held = charlie.Knows
        del charlie
        gc.collect()
        with self.assertRaises(TagCompositionError) as refusal:
            held(Character("Sam"))
        self.assertIn("no longer exists", str(refusal.exception))
        with self.assertRaises(TagResolutionError):
            held[ruth]
        with self.assertRaises(TagResolutionError):
            del held[ruth]

    def test_each_pairs_teardowns_run_at_most_once_on_a_self_link(self):
        charlie = Character("Charlie")
        Net(charlie)
        charlie.Knows(charlie)
        del charlie
        gc.collect()
        self.assertEqual(Net.log, [("Charlie", "Charlie")])

    def test_an_agent_in_a_reference_cycle_built_before_or_after_its_link(self):
        for order in ("before", "after"):
            with self.subTest(order=order):
                Net.log.clear()
                charlie, ruth = People("Charlie", "Ruth")

                if order == "before":
                    charlie.me = charlie
                    Net(charlie)
                else:
                    Net(charlie)
                    charlie.me = charlie

                charlie.Knows(ruth)
                del charlie
                gc.collect()
                self.assertEqual(Net.log, [("Charlie", "Ruth")])   # once, with the Agent, never None

    def test_a_contact_in_a_reference_cycle_still_reaches_her_pair(self):
        read = []

        class Noting(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None): return since

                @Rip
                def Forget(agent, contact):
                    read.append(agent.Knows[contact].since)

        charlie = Character("Charlie")
        Noting(charlie)
        ruth = Character("Ruth")
        ruth.me = ruth
        charlie.Knows(ruth, since=2010)
        del ruth
        gc.collect()
        self.assertEqual(read, [2010])

    def test_a_self_link_in_a_reference_cycle_runs_its_teardowns_once(self):
        charlie = Character("Charlie")
        charlie.me = charlie                              # the language clears weak references first
        Net(charlie)
        charlie.Knows(charlie)
        del charlie
        gc.collect()
        self.assertEqual(Net.log, [("Charlie", "Charlie")])   # the Agent in hand fills both seats

    def test_agent_and_contact_collected_together_end_silently(self):
        charlie, ruth = People("Charlie", "Ruth")
        Net(charlie)
        charlie.Knows(ruth)
        charlie.friend = ruth
        ruth.friend = charlie
        del charlie, ruth
        gc.collect()
        self.assertTrue(all(None not in entry for entry in Net.log))

    def test_at_exit_ends_the_agents_links(self):
        charlie, ruth = People("Charlie", "Ruth")
        Net(charlie)
        charlie.Knows(ruth)
        At_Exit(charlie)
        _teardown_all(charlie)                            # what the exit pass runs
        self.assertEqual(Net.log, [("Charlie", "Ruth")])
        self.assertEqual(list(charlie.Knows[:]), [])
        with self.assertRaises(TagCompositionError):
            charlie.Knows(Character("Sam"))

    def test_an_agent_that_is_also_a_contact_leaves_first_then_ends_its_links(self):
        charlie, bob, ruth = People("Charlie", "Bob", "Ruth")
        Net(charlie)
        Net(bob)
        bob.Knows(charlie)
        charlie.Knows(ruth)
        del charlie
        gc.collect()
        self.assertEqual(Net.log, [("Bob", "Charlie"), ("Charlie", "Ruth")])

    def test_a_teardown_failure_is_reported_and_the_contact_still_leaves(self):
        class Failing(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Forget(agent, contact):
                    raise ValueError("no")

        charlie, ruth = People("Charlie", "Ruth")
        Failing(charlie)
        charlie.Knows(ruth)
        with self.assertRaises(TagCompositionError):
            del charlie.Knows[ruth]
        self.assertNotIn(ruth, charlie.Knows)


# ------------------------------------------------------------------
# The five findings of the hand-made workaround, and the barrier
# ------------------------------------------------------------------


class Finding_Tests(unittest.TestCase):
    def test_finding_1_the_contact_never_keeps_the_agent_alive(self):
        ruth = Character("Ruth")

        def Grow():
            charlie = Character("Charlie")
            Social(charlie)
            charlie.Knows(ruth, since=1)
            return weakref.ref(charlie)

        reference = Grow()
        gc.collect()
        self.assertIsNone(reference())
        self.assertTrue(bool(ruth))

    def test_finding_2_two_agents_records_never_share_a_slot_on_the_contact(self):
        charlie, bob, ruth = People("Charlie", "Bob", "Ruth")
        Social(charlie)
        Social(bob)
        with warnings.catch_warnings():
            warnings.simplefilter("error")                # and no Overwrite Warning
            charlie.Knows(ruth, since=2010)
            bob.Knows(ruth, since=2024)
        self.assertEqual(charlie.Knows[ruth].since, 2010)
        self.assertEqual(bob.Knows[ruth].since, 2024)
        self.assertFalse(hasattr(ruth, "since"))

    def test_finding_3_two_links_promises_stay_two(self):
        charlie, bob, ruth = People("Charlie", "Bob", "Ruth")
        Social(charlie)
        Social(bob)
        charlie.Trusts(ruth)
        bob.Trusts(ruth)
        self.assertEqual(Contract.Status(ruth), {})       # nothing in her contract
        self.assertIn("Still_Honest", Contract.Status(charlie.Trusts[ruth]))
        self.assertIn("Still_Honest", Contract.Status(bob.Trusts[ruth]))

    def test_finding_4_a_broken_link_never_makes_the_contact_defective(self):
        class Guild(Tag):
            @Public
            @Report
            def banner(tag): return "guild"

        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        Guild(ruth)
        charlie.Trusts(ruth)
        ruth.honest = False
        self.assertFalse(charlie.Trusts[ruth])
        self.assertEqual(ruth.banner, "guild")            # her own published members answer
        self.assertTrue(bool(ruth))

    def test_finding_5_the_links_protocols_never_land_on_the_contact(self):
        Net.log.clear()
        charlie, bob, ruth = People("Charlie", "Bob", "Ruth")
        Net(charlie)
        Net(bob)
        charlie.Knows(ruth)
        bob.Knows(ruth)
        self.assertFalse(hasattr(ruth, "Forget"))
        self.assertFalse(hasattr(ruth, "Not_Oneself"))
        del charlie.Knows[ruth]
        self.assertEqual(Net.log, [("Charlie", "Ruth")])  # Charlie's teardown, never Bob's

    def test_nothing_on_a_contact_names_the_agent_who_links_her(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Knows(ruth)
        self.assertEqual(Tags(ruth), ())
        self.assertEqual(Outline(ruth), "Character")
        self.assertEqual(f"{ruth:tags}", "")
        self.assertNotIn("Knows", f"{ruth:contract}")
        self.assertFalse(hasattr(ruth, "Knows"))          # never a view of another Agent's Link
        self.assertTrue(isinstance(ruth, charlie.Knows))  # asked with the Link in hand

    def test_a_contacts_own_link_is_hers_by_name(self):
        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Social(charlie)
        Social(ruth)
        charlie.Knows(ruth)
        ruth.Knows(sam)
        self.assertIs(ruth.Knows[sam], ruth.Knows[sam])
        self.assertNotIn(sam, charlie.Knows)

    def test_nothing_on_a_link_or_a_pair_names_its_agent(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Knows(ruth)
        pair = charlie.Knows[ruth]
        public = [
                name
                for name in dir(charlie.Knows)
                if not name.startswith("_")
                ] + [
                name
                for name in dir(pair)
                if not name.startswith("_")
                ]
        for name in public:
            with self.subTest(name=name):
                try:
                    value = getattr(pair, name) if hasattr(pair, name) else getattr(charlie.Knows, name)
                except Exception:
                    continue
                self.assertIsNot(value, charlie)
        self.assertNotIn("Charlie", repr(pair))
        self.assertNotIn("Charlie", repr(charlie.Knows))


# ------------------------------------------------------------------
# Rollback across Targets (rules 4.6, 5.6, 5.7, 8.2, 8.5): the review's
# findings, one regression each
# ------------------------------------------------------------------


class Rollback_Tests(unittest.TestCase):
    def test_an_agent_linked_during_its_own_rolled_back_call_is_as_it_was(self):
        class Member(Tag):
            @Record
            def card(agent):
                return "member card"

        class Vip(Member):
            @Record
            def sponsored(agent, *, sponsor=None):
                sponsor.Knows(agent)                      # the sponsor links the newcomer at his Parts
                return True

            @Record
            def badge(agent):
                raise ValueError("no badge left")

        bob, charlie = People("Bob", "Charlie")
        Social(bob)
        with self.assertRaises(TagCompositionError):
            Vip(charlie, sponsor=bob)
        self.assertEqual(Tags(charlie), ())
        self.assertNotIn(charlie, Member)
        self.assertFalse(hasattr(charlie, "card"))       # not even an Agent any more
        self.assertNotIn(charlie, bob.Knows)
        Member(charlie)                                   # a retry enters the Field
        self.assertIn(charlie, list(Member[:]))

    def test_a_self_link_at_parts_is_undone_with_the_call(self):
        class Base(Tag):
            @Record
            def base_value(agent):
                return 1

        class Mirror(Base):
            @Record
            def looked(agent):
                agent.Knows(agent)
                return True

            @Record
            def broken(agent):
                raise ValueError("later Record fails")

        charlie = Character("Charlie")
        Net(charlie)
        with self.assertRaises(TagCompositionError):
            Mirror(charlie)
        self.assertEqual(Tags(charlie), (Net,))
        self.assertNotIn(charlie, Base)
        self.assertNotIn(charlie, list(Base[:]))
        self.assertNotIn(charlie, charlie.Knows)
        self.assertFalse("looked" @ charlie)

    def test_a_linking_in_an_earlier_imprint_is_undone_when_a_later_part_fails(self):
        torn = []

        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    return since

                @Rip
                def Forget(agent, contact):
                    torn.append((agent.name, contact.name))

        class Introduced(Circle):
            @Imprint
            def Meet(agent, *, friend=None):
                agent.Knows(friend, since=2020)

        class Sponsored(Introduced):
            @Record
            def broken(agent):
                raise ValueError("Parts of the Shape fail")

        charlie, ruth = People("Charlie", "Ruth")
        with self.assertRaises(TagCompositionError):
            Sponsored(charlie, friend=ruth)               # Circle grants the Link in this same call
        self.assertFalse(hasattr(charlie, "Knows"))       # not even an Agent any more
        self.assertNotIn(ruth, Agents_Of_Any_Link(ruth))
        Circle(charlie)
        self.assertNotIn(ruth, charlie.Knows)
        del ruth
        gc.collect()
        self.assertEqual(torn, [])                        # no teardown for a linking that was undone

    def test_a_linking_through_a_held_link_is_undone_when_a_later_part_fails(self):
        class Introduced(Tag):
            @Imprint
            def Meet(agent, *, friend=None):
                agent.Knows(friend, since=2020)

        class Sponsored(Introduced):
            @Record
            def broken(agent):
                raise ValueError("Parts of the Shape fail")

        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        with self.assertRaises(TagCompositionError):
            Sponsored(charlie, friend=ruth)
        self.assertNotIn(ruth, charlie.Knows)
        self.assertFalse(isinstance(ruth, charlie.Knows))
        with self.assertRaises(TagResolutionError):
            charlie.Knows[ruth]

    def test_a_dropped_pair_never_runs_its_teardowns(self):
        torn = []

        class Greeting(Tag):
            @Record
            def Greet(agent):
                return "her own Record"

        class Club_With_Teardown(Tag):
            @Link
            class Member(Tag):
                @Public
                def Greet(agent, contact):
                    return "a line"

                @Rip
                def Leave(agent, contact):
                    torn.append("Member")

        class Joining(Tag):
            @Record
            def friend(agent, *, friend=None):
                agent.Knows(friend)
                return friend

            @Record
            def broken(agent):
                raise ValueError("no")

        class Counted(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Forget(agent, contact):
                    torn.append("Knows")

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Club_With_Teardown(charlie)
        Counted(charlie)
        Greeting(ruth)
        with self.assertRaises(TagCompositionError):
            charlie.Member(ruth)                          # her entry is refused after the Pair's call
        with self.assertRaises(TagCompositionError):
            Joining(charlie, friend=sam)                  # the linking is undone by the rollback
        gc.collect()
        self.assertEqual(torn, [])

    def test_a_nested_linking_at_a_pairs_parts_is_undone_when_her_entry_is_refused(self):
        class Greeting(Tag):
            @Record
            def Greet(agent):
                return "her own Record"

        class Nesting_Club(Tag):
            @Link
            class Member(Tag):
                @Record
                def joined(agent, contact):
                    agent.Knows(contact, since=1999)      # a nested linking, at the Pair's Parts
                    return 1

                @Public
                def Greet(agent, contact):
                    return "a line"

        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        Nesting_Club(charlie)
        Greeting(ruth)
        with self.assertRaises(TagCompositionError):
            charlie.Member(ruth)
        self.assertNotIn(ruth, charlie.Knows)
        self.assertFalse(isinstance(ruth, charlie.Knows))

    def test_a_nested_linking_in_an_extension_is_undone_when_another_pair_refuses(self):
        class Registry(Tag):
            @Link
            class Listed(Tag):
                pass

        class Plain(Tag):
            @Link
            class Knows(Tag):
                pass

        class Strict(Plain):
            @Link
            class Knows(Plain.Knows):
                @Pre
                def Only_Honest(agent, contact):
                    return contact.honest

                @Record
                def vetted(agent, contact):
                    agent.Listed(contact)
                    return True

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        sam.honest = False
        Registry(charlie)
        Plain(charlie)
        charlie.Knows(ruth)
        charlie.Knows(sam)
        with self.assertRaises(TagPreconditionError):
            Strict(charlie)
        self.assertNotIn(charlie, Strict)
        self.assertNotIn(ruth, charlie.Listed)
        self.assertFalse("vetted" @ charlie.Knows[ruth])

    def test_every_pairs_gate_runs_before_any_pairs_records(self):
        log = []

        class Plain(Tag):
            @Link
            class Knows(Tag):
                pass

        class Strict(Plain):
            @Link
            class Knows(Plain.Knows):
                @Pre
                def Only_Honest(agent, contact):
                    log.append(f"gate {contact.name}")
                    return contact.honest

                @Record
                def vetted(agent, contact):
                    log.append(f"Record {contact.name}")
                    return True

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        sam.honest = False
        Plain(charlie)
        charlie.Knows(ruth)
        charlie.Knows(sam)
        with self.assertRaises(TagPreconditionError):
            Strict(charlie)
        self.assertEqual(log, ["gate Ruth", "gate Sam"])

    def test_a_rolled_back_grant_leaves_independent_links_apart(self):
        class Two(Tag):
            @Link
            class Knows(Tag):
                @Record
                def known(agent, contact):
                    return "known"

            @Link
            class Likes(Tag):
                @Record
                def liked(agent, contact):
                    return "liked"

        class Close(Two):
            @Link
            class Bonded(Two.Knows, Two.Likes):
                pass

        class Doomed(Close):
            @Record
            def broken(agent):
                raise ValueError("a later Record fails")

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Two(charlie)
        charlie.Knows(ruth)
        charlie.Likes(sam)
        with self.assertRaises(TagCompositionError):
            Doomed(charlie)                               # joins the two families, then rolls back
        charlie.Likes(ruth)
        self.assertIsNot(charlie.Likes[ruth], charlie.Knows[ruth])
        self.assertFalse("known" @ charlie.Likes[ruth])
        del charlie.Knows[ruth]
        with self.assertRaises(TagResolutionError):
            charlie.Knows[ruth]

    def test_a_refused_join_joins_nothing(self):
        class Three(Tag):
            @Link
            class Knows(Tag):
                pass

            @Link
            class Likes(Tag):
                pass

            @Link
            class Trusts(Tag):
                pass

        class Close(Three):
            @Link
            class Bonded(Three.Knows, Three.Likes, Three.Trusts):
                pass

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Three(charlie)
        charlie.Knows(sam)
        charlie.Likes(ruth)
        charlie.Trusts(ruth)                              # Likes and Trusts hold separate Pairs for her
        with self.assertRaises(TagCompositionError):
            Close(charlie)
        charlie.Likes(sam)
        self.assertIsNot(charlie.Likes[sam], charlie.Knows[sam])   # Knows and Likes were never joined

    def test_a_teardown_that_links_her_again_keeps_her_pair(self):
        calls = []

        class Again(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    return since

                @Public
                def Hello(agent, contact):
                    return f"hello from {agent.name}"

                @Rip
                def Relink(agent, contact):
                    calls.append(contact.name)
                    if len(calls) == 1:
                        agent.Knows(contact, since=2024)

        charlie, ruth = People("Charlie", "Ruth")
        Again(charlie)
        charlie.Knows(ruth, since=2010)
        del charlie.Knows[ruth]
        self.assertIn(ruth, charlie.Knows)
        self.assertEqual(charlie.Knows[ruth].since, 2024)
        self.assertEqual(ruth.Hello(), "hello from Charlie")
        del charlie.Knows[ruth]                           # her teardown runs again
        self.assertEqual(calls, ["Ruth", "Ruth"])
        self.assertNotIn(ruth, charlie.Knows)

    def test_unlinking_everyone_skips_a_contact_a_teardown_already_unlinked(self):
        ran = []
        people = {}

        class Chain(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Forget(agent, contact):
                    ran.append(contact.name)
                    if contact.name == "A":
                        del agent.Knows[people["B"]]

        charlie = Character("Charlie")
        Chain(charlie)
        for name in "ABC":
            people[name] = Character(name)
            charlie.Knows(people[name])
        del charlie.Knows[:]
        self.assertEqual(ran, ["A", "B", "C"])
        self.assertEqual(list(charlie.Knows[:]), [])


# ------------------------------------------------------------------
# The law review's findings, one regression each
# ------------------------------------------------------------------


def Read_Or_Shut(contact, name):
    try:
        return getattr(contact, name)
    except AttributeError:
        return "shut"


class Law_Review_Tests(unittest.TestCase):
    def test_the_contacts_door_stays_shut_when_the_call_starts_in_her_own_code(self):
        seen = []

        class Vetting_Club(Tag):
            @Link
            class Member(Tag):
                @Pre
                def Vet(agent, contact):
                    seen.append(Read_Or_Shut(contact, "diary"))
                    return True

                @Record
                def copy(agent, contact):
                    return Read_Or_Shut(contact, "diary")

                @Imprint
                def Note(agent, contact):
                    seen.append(Read_Or_Shut(contact, "diary"))

                def Peek(agent, contact):
                    return Read_Or_Shut(contact, "diary")

        class Joiner(Tag):
            @Secret
            @Record
            def diary(agent):
                return "her secret diary"

            def Join(agent, leader):
                leader.Member(agent)                      # linked from her own Action: her door is open

            def Ask(agent, leader):
                return leader.Member[agent].Peek()        # a Pair Action called from her own Action

        bob, ann = People("Bob", "Ann")
        Vetting_Club(bob)
        Joiner(ann)
        ann.Join(bob)
        self.assertEqual(seen, ["shut", "shut"])
        self.assertEqual(bob.Member[ann].copy, "shut")
        self.assertEqual(ann.Ask(bob), "shut")

    def test_the_two_ways_pattern_never_reads_the_first_agents_secret(self):
        seen = []

        class Friendly(Tag):
            @Secret
            @Record
            def password(agent):
                return f"{agent.name}'s password"

            @Link
            class Friends(Tag):
                @Pre
                def Look(agent, contact):
                    seen.append(Read_Or_Shut(contact, "password"))
                    return True

                @Imprint
                def Both_Ways(agent, contact):
                    Friendly(contact)
                    contact.Friends(agent)               # Dan's door is open here, and Dan is the Contact

        dan, eve = People("Dan", "Eve")
        Friendly(dan)
        dan.Friends(eve)
        self.assertEqual(seen, ["shut", "shut"])

    def test_a_published_link_operation_runs_with_her_door_shut(self):
        class Keeper(Tag):
            @Secret
            @Record
            def diary(agent):
                return "her secret diary"

        class Op_Club(Tag):
            @Link
            class Member(Tag):
                @Public
                @Operation
                def Peek_Op(link, contact):
                    return Read_Or_Shut(contact, "diary")

        charlie, ruth = People("Charlie", "Ruth")
        Op_Club(charlie)
        Keeper(ruth)
        charlie.Member(ruth)
        self.assertEqual(ruth.Peek_Op(), "shut")
        self.assertEqual(charlie.Member.Peek_Op(ruth), "shut")

    def test_a_link_never_arrives_over_the_agents_own_value(self):
        charlie = Character("Charlie")
        charlie.Knows = ["Ruth", "Sam"]
        with self.assertRaises(TagCompositionError):
            Social(charlie)
        self.assertEqual(charlie.Knows, ["Ruth", "Sam"])
        self.assertNotIn(charlie, Social)

    def test_an_extension_names_the_relation_it_extends_as_its_only_base(self):
        with self.assertRaises(TagDeclarationError):
            class Through_A_Shape(Social):
                @Link
                class Knows(Social.Trusts):               # a Shape of Knows, not Knows
                    pass

        class Two(Tag):
            @Link
            class Knows(Tag):
                pass

            @Link
            class Likes(Tag):
                pass

        with self.assertRaises(TagDeclarationError):
            class Two_Bases(Two):
                @Link
                class Knows(Two.Knows, Two.Likes):        # would bring Likes' Layer into Knows' Pairs
                    pass

    def test_every_pair_of_a_field_is_overlaid_alike_after_an_extension(self):
        class Layered(Tag):
            @Link
            class Knows(Tag):
                def Greet(agent, contact):
                    return "knows"

            @Link
            class Trusts(Knows):
                def Greet(agent, contact):
                    return "trusts"

        class Layered_Spy(Layered):
            @Link
            class Knows(Layered.Knows):
                def Greet(agent, contact):
                    return "spy"

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        dan, tom = People("Dan", "Tom")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", TagOverwriteWarning)
            Layered(charlie)
            charlie.Trusts(ruth)                          # before the extension
            Layered_Spy(charlie)
            charlie.Trusts(sam)                           # after it
            Layered_Spy(dan)                              # granted and extended in one call
            dan.Trusts(tom)
        self.assertEqual(charlie.Trusts[ruth].Greet(), charlie.Trusts[sam].Greet())
        self.assertEqual(charlie.Trusts[sam].Greet(), "spy")   # the latest Layer, as on any Agent (§1.2)
        self.assertEqual(dan.Trusts[tom].Greet(), "spy")

    def test_the_pairs_own_tags_are_out_of_reach(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Knows(ruth)
        pair = charlie.Knows[ruth]
        self.assertEqual(Tags(pair), ())
        self.assertNotIn("Knows", Outline(pair))
        with self.assertRaises(AttributeError):
            pair.Knows                                    # no view by name
        from TopKit.state import _state_of

        pair_tag = _state_of(pair).active[0]
        for act in (
                lambda: list(pair_tag[:]),
                lambda: pair in pair_tag,
                lambda: isinstance(pair, pair_tag),
                lambda: len(pair_tag),
                lambda: pair_tag(Character("x")),
                ):
            with self.subTest(act=act):
                with self.assertRaises(TagCompositionError):
                    act()
        with self.assertRaises(TagCompositionError):
            del pair_tag[pair]
        self.assertIn(ruth, charlie.Knows)

    def test_a_published_report_never_arrives_at_a_links_name(self):
        class Guild(Tag):
            @Public
            @Report
            def Knows(tag):
                return "the guild's published Report"

        charlie = Character("Charlie")
        Social(charlie)
        with self.assertRaises(TagCompositionError):
            Guild(charlie)
        self.assertNotIn(charlie, Guild)

    def test_a_relation_is_never_a_pin_in_either_decorator_order(self):
        with self.assertRaises(TagDeclarationError):
            class Over_Link(Tag):
                @Pin
                @Link
                class Knows(Tag):
                    pass

    def test_an_ended_pair_answers_with_a_resolution_failure(self):
        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        charlie.Knows(ruth, since=2010)
        held = charlie.Knows[ruth]
        del charlie.Knows[ruth]
        with self.assertRaises(TagResolutionError):
            held.Greet()

        bob, sam = People("Bob", "Sam")
        Social(bob)
        bob.Knows(sam)
        held = bob.Knows[sam]
        del bob
        gc.collect()
        with self.assertRaises(TagResolutionError):
            held.Greet()

    def test_a_relations_plain_values_and_class_methods_belong_to_the_link(self):
        class Bounded(Tag):
            @Link
            class Chats(Tag):
                capacity = 2

                @classmethod
                def Describe(link):
                    return f"{link.__name__} holds {link.capacity}"

                @Pre
                def Has_Room(agent, contact):
                    return len(agent.Chats[:]) < agent.Chats.capacity

        charlie = Character("Charlie")
        Bounded(charlie)
        self.assertEqual(charlie.Chats.capacity, 2)
        self.assertEqual(charlie.Chats.Describe(), "Chats holds 2")
        contacts = People("A", "B", "C")                  # held: a Field never keeps its Contacts alive
        charlie.Chats(contacts[0])
        charlie.Chats(contacts[1])
        with self.assertRaises(TagPreconditionError):
            charlie.Chats(contacts[2])                    # the gate reads the plain value


# ------------------------------------------------------------------
# The lifetime review's findings, one regression each
# ------------------------------------------------------------------


class Lifetime_Review_Tests(unittest.TestCase):
    def setUp(self):
        Net.log.clear()

    def test_a_linking_in_a_context_copied_from_a_finished_call_holds_nothing(self):
        captured = []

        class Scheduler(Tag):
            @Imprint
            def Capture(agent):
                captured.append(contextvars.copy_context())   # as asyncio does for a task started here

        charlie = Character("Charlie")
        Net(charlie)
        Scheduler(charlie)

        def Link_A_Stranger():
            stranger = Character("Stranger")
            charlie.Knows(stranger)
            return weakref.ref(stranger)

        reference = captured[0].run(Link_A_Stranger)      # after the call has returned
        gc.collect()
        self.assertIsNone(reference())                    # the Field never keeps her alive
        self.assertEqual(Net.log, [("Charlie", "Stranger")])
        self.assertEqual(list(charlie.Knows[:]), [])

    def test_a_living_contact_never_keeps_a_dead_agents_link(self):
        ruth = Character("Ruth")
        references = []

        for index in range(20):
            agent = Character(f"A{index}")
            Social(agent)
            agent.Knows(ruth)
            references.append(weakref.ref(agent.Knows))
            del agent

        gc.collect()
        self.assertEqual(sum(1 for reference in references if reference() is not None), 0)

        charlie = Character("Charlie")
        Social(charlie)
        charlie.Knows(ruth)
        held = charlie.Knows
        del charlie.Knows[ruth]
        self.assertTrue(isinstance(ruth, held))           # history answers while the Link is held

    def test_an_interrupted_teardown_at_deletion_still_unlinks_every_contact(self):
        ran = []

        class Touchy(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Forget(agent, contact):
                    ran.append(contact.name)
                    if contact.name == "R1":
                        raise KeyboardInterrupt

        charlie = Character("Charlie")
        contacts = People("R1", "R2", "R3")
        Touchy(charlie)
        for contact in contacts:
            charlie.Knows(contact)
        held = charlie.Knows
        with self.assertRaises(KeyboardInterrupt):
            _teardown_all(charlie)                        # what the finalizer runs
        self.assertEqual(ran, ["R1", "R2", "R3"])
        self.assertEqual(list(held[:]), [])

    def test_an_interrupted_unlink_still_ends_her_pair(self):
        class Touchy(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Forget(agent, contact):
                    raise KeyboardInterrupt

        charlie, ruth = People("Charlie", "Ruth")
        Touchy(charlie)
        charlie.Knows(ruth)
        with self.assertRaises(KeyboardInterrupt):
            del charlie.Knows[ruth]
        self.assertNotIn(ruth, charlie.Knows)
        with self.assertRaises(TagResolutionError):
            charlie.Knows[ruth]

    def test_a_refused_shape_grant_leaves_the_family_as_it_was(self):
        from TopKit.links import _record_of

        class Widened(Social):
            @Link
            class Admires(Social.Knows):                  # joins the family of charlie.Knows
                pass

        class Doomed(Widened):
            @Record
            def broken(agent):
                raise ValueError("refused at Parts, after Widened granted its Link")

        charlie = Character("Charlie")
        Social(charlie)
        family = _record_of(charlie.Knows).family
        before = len(family.links)
        for _attempt in range(10):
            with self.assertRaises(TagCompositionError):
                Doomed(charlie)
        self.assertEqual(len(family.links), before)
        self.assertFalse("Admires" @ charlie)


# ------------------------------------------------------------------
# The doors review's findings, one regression each
# ------------------------------------------------------------------


class Door_Review_Tests(unittest.TestCase):
    def test_her_own_views_never_carry_the_links_members_or_the_link(self):
        class Rostered(Tag):
            @Link
            class Member(Tag):
                @Report
                def roster_size(link):
                    return "the Link's own"

                @Operation
                def audit(link):
                    return "the Link's own"

                @Public
                @Operation
                def ping(link, contact):
                    return "a published Operation"

        class Wizard(Tag):
            @Record
            def mana(agent):
                return 3

        charlie, ruth = People("Charlie", "Ruth")
        Rostered(charlie)
        charlie.Member(ruth)
        Wizard(ruth)                                      # her own Tag, gained after the linking
        view = ruth.Wizard
        for name in ("roster_size", "audit"):
            with self.subTest(name=name):
                self.assertFalse(name @ view)
                with self.assertRaises(AttributeError):
                    getattr(view, name)
        self.assertFalse("audit" @ ruth)
        self.assertEqual(ruth.ping(), "a published Operation")
        self.assertEqual(view.ping(), "a published Operation")   # what she already sees, as an Action
        self.assertFalse(hasattr(view.ping, "args"))      # never a handle that carries the Link

    def test_a_link_report_is_never_built_inside_a_contacts_door(self):
        class Keeper(Tag):
            @Secret
            @Record
            def diary(agent):
                return "her secret"

            def Read_It(agent, leader):
                return leader.Member.first_impression    # first read from her own Action: her door is open

        class Impressed(Tag):
            @Link
            class Member(Tag):
                @Public
                @Report
                def first_impression(link):
                    return [Read_Or_Shut(contact, "diary") for contact in link[:]]

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Impressed(charlie)
        Keeper(ruth)
        charlie.Member(ruth)                              # her door is open while the Link is applied to her
        self.assertEqual(ruth.Read_It(charlie), ["shut"])
        Keeper(sam)
        charlie.Member(sam)
        self.assertEqual(sam.first_impression, ["shut"])  # the kept value never carries her secret

    def test_an_unpublished_link_report_never_replaces_her_own(self):
        class Guild(Tag):
            @Public
            @Report
            def capacity(tag):
                return "her guild's"

        class Sized(Tag):
            @Link
            class Member(Tag):
                @Report
                def capacity(link):
                    return "the Link's own"

        charlie, ruth = People("Charlie", "Ruth")
        Guild(ruth)
        Sized(charlie)
        charlie.Member(ruth)
        self.assertEqual(ruth.capacity, "her guild's")
        del charlie.Member[ruth]
        self.assertEqual(ruth.capacity, "her guild's")

    def test_a_record_line_over_her_action_is_refused_and_over_her_record_warns(self):
        class Own(Tag):
            def rank(agent):
                return "her own Action"

            @Record
            def title(agent):
                return "her own Record"

        class Ranked(Tag):
            @Link
            class Member(Tag):
                @Public
                @Record
                def rank(agent, contact):
                    return "the Pair's rank"

        class Titled(Tag):
            @Link
            class Member(Tag):
                @Public
                @Record
                def title(agent, contact):
                    return "the Pair's title"

        charlie, bob, ruth = People("Charlie", "Bob", "Ruth")
        Own(ruth)
        Ranked(charlie)
        Titled(bob)
        with self.assertRaises(TagCompositionError):
            charlie.Member(ruth)                          # a value over her Action: refused, nothing changed
        self.assertEqual(ruth.rank(), "her own Action")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            bob.Member(ruth)
        self.assertTrue(any(issubclass(w.category, TagOverwriteWarning) for w in caught))
        self.assertEqual(ruth.title, "the Pair's title")

    def test_a_secret_link_member_answers_only_in_its_agents_code(self):
        class Vaulted(Tag):
            @Link
            class Member(Tag):
                @Secret
                @Report
                def vault(link):
                    return "the vault"

                @Secret
                @Operation
                def purge(link):
                    return "purged"

                def Inside(agent, contact):
                    return (agent.Member.vault, agent.Member.purge())

        charlie, ruth = People("Charlie", "Ruth")
        Vaulted(charlie)
        charlie.Member(ruth)
        self.assertEqual(charlie.Member[ruth].Inside(), ("the vault", "purged"))
        with self.assertRaises(AttributeError):
            charlie.Member.vault
        with self.assertRaises(AttributeError):
            charlie.Member.purge()


# ------------------------------------------------------------------
# Undo steps belong to Agents: what another Agent's call keeps, stays
# ------------------------------------------------------------------


class Ownership_Tests(unittest.TestCase):
    def test_a_successful_nested_tagging_keeps_its_linking_when_the_outer_call_fails(self):
        class Member(Tag):
            @Record
            def card(agent):
                return "member card"

        class Vip(Member):
            @Record
            def sponsored(agent, *, sponsor=None):
                sponsor.Knows(agent)
                return True

        class Host(Tag):
            @Record
            def guest(agent, *, guest=None, sponsor=None):
                Vip(guest, sponsor=sponsor)               # charlie's own tagging succeeds
                return guest

            @Record
            def broken(agent):
                raise ValueError("the host's call fails after it")

        hall, bob, charlie = People("Hall", "Bob", "Charlie")
        Social(bob)
        with self.assertRaises(TagCompositionError):
            Host(hall, guest=charlie, sponsor=bob)
        self.assertIn(charlie, list(Vip[:]))              # another Agent's tagging stays (§0.6)
        self.assertIn(charlie, bob.Knows)                 # and the linking it made, consistent
        self.assertIn(charlie, list(bob.Knows[:]))
        bob.Knows[charlie]                                # her Pair is there

    def test_a_link_granted_in_a_nested_tagging_keeps_its_family(self):
        class Two(Tag):
            @Link
            class Knows(Tag):
                @Record
                def known(agent, contact):
                    return "known"

            @Link
            class Likes(Tag):
                @Record
                def liked(agent, contact):
                    return "liked"

        class Close(Two):
            @Link
            class Bonded(Two.Knows, Two.Likes):
                pass

        class Host(Tag):
            @Record
            def guest(agent, *, guest=None):
                Close(guest)
                return guest

            @Record
            def broken(agent):
                raise ValueError("the host's call fails after it")

        hall, charlie, dave = People("Hall", "Charlie", "Dave")
        with self.assertRaises(TagCompositionError):
            Host(hall, guest=charlie)
        self.assertIn(charlie, Close)
        charlie.Bonded(dave)
        self.assertIs(charlie.Likes[dave], charlie.Knows[dave])   # one family, one Pair
        self.assertEqual(charlie.Likes[dave].known, "known")

    def test_an_undone_linking_leaves_what_she_gained_since(self):
        class Wizard(Tag):
            pass

        class Introducing(Tag):
            @Record
            def friend(agent, *, friend=None):
                agent.Knows(friend)                       # charlie's linking: undone with his call
                Wizard(friend)                            # her own tagging: independent, stays
                return friend

            @Record
            def broken(agent):
                raise ValueError("refused at Parts")

        charlie, ruth = People("Charlie", "Ruth")
        Social(charlie)
        with self.assertRaises(TagCompositionError):
            Introducing(charlie, friend=ruth)
        self.assertNotIn(ruth, charlie.Knows)
        self.assertNotIn(ruth, list(charlie.Knows[:]))
        with self.assertRaises(TagResolutionError):
            charlie.Knows[ruth]
        self.assertIn(ruth, Wizard)
        self.assertIn(ruth, list(Wizard[:]))


# ------------------------------------------------------------------
# The integration review's findings, one regression each
# ------------------------------------------------------------------


class Integration_Review_Tests(unittest.TestCase):
    def test_a_tag_that_declares_a_relation_is_never_marked_a_pin_later(self):
        class Later_Social(Tag):
            @Link
            class Knows(Tag):
                pass

        Later_Social(Character("Charlie"))                # its scan is cached as an ordinary Tag
        with self.assertRaises(TagDeclarationError):
            Pin(Later_Social)
        charlie = Character("Charlie")
        Later_Social(charlie)                             # still an ordinary Tag
        self.assertIn(charlie, Later_Social)

    def test_a_pin_never_pins_a_relation_or_a_link(self):
        @Pin
        class Rare(Tag):
            @Record
            def rarity(tag):
                return 3

        with self.assertRaises(TagCompositionError):
            Rare(Social.Knows)
        self.assertNotIn(Social.Knows, list(Rare[:]))
        charlie = Character("Charlie")
        Social(charlie)
        with self.assertRaises(TagCompositionError):
            Rare(charlie.Knows)
        self.assertFalse(hasattr(charlie.Knows, "rarity"))

    def test_an_unpublished_report_at_the_name_never_refuses_a_link(self):
        class Census(Tag):
            @Report
            def Knows(tag):
                return "a Tag-scope Report"

            @Operation
            def Follows(tag):
                return "a Tag-scope Operation"

        class Counted(Census):
            @Link
            class Knows(Tag):
                pass

            @Link
            class Follows(Tag):
                pass

        charlie, ruth = People("Charlie", "Ruth")
        Counted(charlie)                                  # Tag scope and Agent scope never collide (rule 4.4)
        charlie.Knows(ruth)
        self.assertIn(ruth, charlie.Knows)

    def test_a_relation_has_no_special_methods(self):
        for name in ("__del__", "__len__"):
            with self.subTest(name=name):
                with self.assertRaises(TagDeclarationError):
                    type(
                            "Holder",
                            (Tag,),
                            {"Knows": Link(type("Knows", (Tag,), {name: lambda agent, contact: None}))},
                            )

    def test_the_declaring_tags_view_shows_its_link(self):
        charlie = Character("Charlie")
        Social(charlie)
        self.assertIs(Social[charlie].Knows, charlie.Knows)
        self.assertTrue("Knows" @ Social[charlie])

    def test_a_builtin_in_a_relation_is_a_declaration_failure(self):
        with self.assertRaises(TagDeclarationError):
            class With_Builtin(Tag):
                @Link
                class Knows(Tag):
                    pick = max


# ------------------------------------------------------------------
# The second round's findings, one regression each
# ------------------------------------------------------------------


class Second_Round_Tests(unittest.TestCase):
    def test_a_context_copied_during_any_tagging_never_keeps_its_agent(self):
        captured = []
        torn = []

        class Monitored(Tag):                             # no Link anywhere
            @Imprint
            def Capture(agent):
                captured.append(contextvars.copy_context())   # as asyncio does for a task started here

            @Rip
            def Bye(agent):
                torn.append(agent.name)

        host = Character("Host")
        Monitored(host)
        reference = weakref.ref(host)
        del host
        gc.collect()
        self.assertIsNone(reference())                    # the copied context holds no Agent
        self.assertEqual(torn, ["Host"])
        self.assertEqual(len(captured), 1)

    def test_an_undone_linking_never_rewinds_her_own_finished_tagging(self):
        log = []
        people = {}

        class Trained(Tag):
            @Record
            def level(agent):
                return 1

            @Imprint
            def Register(agent):
                people["bob"].Knows(agent)                # bob links her at her own Write

            @Imprint
            def Train(agent):
                agent.level = 5
                log.append("trained")

        class Recruiting(Tag):
            @Record
            def recruit(agent, *, recruit=None):
                Trained(recruit)                          # her own tagging: completes
                return recruit

            @Record
            def broken(agent):
                raise ValueError("Parts fails")

        bob, ruth = People("Bob", "Ruth")
        people["bob"] = bob
        Social(bob)
        with self.assertRaises(TagCompositionError):
            Recruiting(bob, recruit=ruth)                 # bob's call rolls back: his linking is undone
        self.assertNotIn(ruth, bob.Knows)
        self.assertIn(ruth, Trained)
        self.assertEqual(ruth.level, 5)                   # her Write stays (§0.6)
        self.assertEqual(Trained[ruth].level, 5)          # and her view of it
        self.assertEqual(log, ["trained"])

    def test_an_undone_linking_never_erases_a_tag_she_gained_and_left_since(self):
        class Probation(Tag):
            @Record
            def strikes(agent):
                return 3

        class Supervising(Tag):
            @Record
            def ward(agent, *, ward=None):
                agent.Knows(ward)                         # bob's linking
                Probation(ward)                           # her own tagging, then her Rip
                del Probation[ward]
                return ward

            @Record
            def broken(agent):
                raise ValueError("Parts fails")

        bob, ruth = People("Bob", "Ruth")
        Social(bob)
        with self.assertRaises(TagCompositionError):
            Supervising(bob, ward=ruth)
        self.assertNotIn(ruth, bob.Knows)
        self.assertTrue(isinstance(ruth, Probation))      # her history stays
        self.assertEqual(ruth.strikes, 3)                 # and her sticky Record (§0.7)


class Variant_Tests(unittest.TestCase):
    """The second review round's variants of the first round's findings."""

    def test_a_pin_member_named_like_a_relation_is_refused(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    return since

        @Pin
        class Notes(Tag):
            @Public
            @Record
            def Knows(tag):
                return "the Pin's Report"

        with self.assertRaises(TagCompositionError):
            Notes(Circle)                                 # the Relation is Agent scope: no Pin overlays it
        self.assertTrue(Circle.Knows is Circle.__dict__["Knows"])
        bob, sam = People("Bob", "Sam")
        Circle(bob)                                       # an Agent tagged afterwards still gets his Link
        bob.Knows(sam, since=2)
        self.assertEqual(bob.Knows[sam].since, 2)

    def test_an_owned_undo_keeps_the_layer_an_unowned_extension_laid(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    return since

            @Link
            class Trusts(Knows):
                pass

        class Vetting(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def vetted(agent, contact):
                    return "vetted"

                def Report_In(agent, contact):
                    return f"{contact.name} is vetted"

        class Joining(Tag):                               # a call on Ruth
            @Record
            def trusted(agent, *, by=None):
                by.Trusts(agent)                          # Bob and Ruth own this linking
                return True

            @Record
            def promoted(agent, *, by=None):
                Vetting(by)                               # Bob's own call: it succeeds, Bob owns it
                return True

            @Record
            def broken(agent):
                raise ValueError("Ruth's later Record fails")

        bob, ruth, sam = People("Bob", "Ruth", "Sam")
        Circle(bob)
        bob.Knows(ruth, since=1)
        bob.Knows(sam, since=2)
        with self.assertRaises(TagCompositionError):
            Joining(ruth, by=bob)                         # Ruth's call rolls back: her linking is undone
        self.assertIn(bob, Vetting)                       # Bob's call stays
        self.assertNotIn(ruth, bob.Trusts)
        self.assertIn(ruth, bob.Knows)
        for contact in (ruth, sam):                       # every Pair of the Field is overlaid alike
            self.assertEqual(bob.Knows[contact].vetted, "vetted")
            self.assertEqual(bob.Knows[contact].Report_In(), f"{contact.name} is vetted")

    def test_an_operation_given_the_contact_by_keyword_runs_with_her_door_shut(self):
        class Circle(Tag):
            @Link
            class Member(Tag):
                @Operation
                def Peek(link, contact):
                    return Read_Or_Shut(contact, "diary")

        class Writer(Tag):
            @Secret
            @Record
            def diary(agent):
                return "her secret"

            def Ask_By_Position(agent, link):
                return link.Peek(agent)

            def Ask_By_Keyword(agent, link):
                return link.Peek(contact=agent)

        charlie, ruth = People("Charlie", "Ruth")
        Circle(charlie)
        Writer(ruth)
        charlie.Member(ruth)
        self.assertEqual(ruth.Ask_By_Position(charlie.Member), "shut")
        self.assertEqual(ruth.Ask_By_Keyword(charlie.Member), "shut")
        self.assertEqual(charlie.Member.Peek(contact=ruth), "shut")

    def test_a_refused_linking_keeps_what_finished_calls_inside_it_did(self):
        holder = {}

        class Club(Tag):
            @Link
            class Member(Tag):
                @Public
                @Report
                def gossip(link):
                    return Read_Or_Shut(holder["contact"], "diary")   # built with every Contact's door shut

        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def joined(agent, contact):
                    Club(agent)                           # the Agent's own call: it finishes
                    agent.Member(contact)                 # a linking at the Pair's Parts: the refusal's own
                    return True

                @Record
                def broken(agent, contact):
                    raise ValueError("the linking is refused")

        class Writer(Tag):
            @Secret
            @Record
            def diary(agent):
                return "her secret"

            def Read_Gossip(agent):
                return agent.gossip                       # the Report, first built from her own code

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Circle(charlie)
        with self.assertRaises(TagCompositionError):
            charlie.Knows(ruth)
        self.assertNotIn(ruth, charlie.Knows)
        self.assertIn(charlie, Club)                      # his finished call stays (§0.6)
        self.assertNotIn(ruth, charlie.Member)            # the linking made inside the refusal is undone
        Writer(sam)
        holder["contact"] = sam
        charlie.Member(sam)                               # the Link his call granted is whole
        self.assertEqual(sam.Read_Gossip(), "shut")

    def test_link_operations_and_report_builders_read_the_agents_secrets(self):
        holder = {}

        class Keeper(Tag):
            @Secret
            @Record
            def journal(agent):
                return "his secret"

        class Circle(Tag):
            @Link
            class Member(Tag):
                @Secret
                @Report
                def quota(link):
                    return 3

                @Public
                @Report
                def summary(link):
                    return Read_Or_Shut(holder["agent"], "journal")

                @Operation
                def Room_Left(link):
                    return link.quota - len(link[:])

                @Operation
                def Journal(link):
                    return Read_Or_Shut(holder["agent"], "journal")

        charlie, ruth = People("Charlie", "Ruth")
        holder["agent"] = charlie
        Keeper(charlie)
        Circle(charlie)
        charlie.Member(ruth)
        self.assertEqual(charlie.Member.Room_Left(), 2)   # the Link's own @Secret Report
        self.assertEqual(charlie.Member.Journal(), "his secret")
        self.assertEqual(charlie.Member.summary, "his secret")
        self.assertEqual(Read_Or_Shut(charlie, "journal"), "shut")   # outside his code, still shut

    def test_an_interrupted_teardown_at_a_contacts_deletion_still_leaves_her_other_links(self):
        import sys

        torn = []
        unraisable = []

        class Payload:
            pass

        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def memo(agent, contact, *, memo=None):
                    return memo

                @Rip
                def Forget(agent, contact):
                    torn.append(agent.name)
                    if agent.name == "Bob":
                        raise KeyboardInterrupt

        charlie, bob, ruth = People("Charlie", "Bob", "Ruth")
        Circle(charlie)
        Circle(bob)
        payload = Payload()
        payload_reference = weakref.ref(payload)
        charlie.Knows(ruth, memo=payload)
        bob.Knows(ruth)
        del payload
        hook = sys.unraisablehook
        sys.unraisablehook = lambda report: unraisable.append(type(report.exc_value))
        try:
            del ruth
            gc.collect()
        finally:
            sys.unraisablehook = hook
        self.assertEqual(sorted(torn), ["Bob", "Charlie"])   # the interrupt stops no other Link's exit
        self.assertEqual(unraisable, [KeyboardInterrupt])     # and is still reported
        self.assertEqual(len(charlie.Knows[:]), 0)
        self.assertEqual(len(bob.Knows[:]), 0)
        self.assertIsNone(payload_reference())            # no living Agent's family keeps her Pair

    def test_a_layer_that_reaches_a_held_pair_goes_on_top_with_a_warning(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                def Greet(agent, contact):
                    return "knows"

            @Link
            class Trusts(Knows):
                def Greet(agent, contact):
                    return "trusts"

        class Undercover(Circle):
            @Link
            class Knows(Circle.Knows):
                def Greet(agent, contact):
                    return "undercover"

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Circle(charlie)
        charlie.Knows(ruth)                               # her Pair is held before the extension
        Undercover(charlie)
        with self.assertWarns(TagOverwriteWarning):
            charlie.Trusts(ruth)                          # Trusts reaches her Pair last: on top
        with self.assertWarns(TagOverwriteWarning):
            charlie.Trusts(sam)                           # a fresh Pair: the order the Agent gained them
        self.assertEqual(charlie.Trusts[ruth].Greet(), "trusts")
        self.assertEqual(charlie.Trusts[sam].Greet(), "undercover")


class New_Code_Review_Tests(unittest.TestCase):
    """The second round's review of the newest code."""

    def test_an_undone_linking_gives_a_plain_object_back_her_own_values(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Public
                @Record
                def nickname(agent, contact, *, nickname=None):
                    return nickname

                @Public
                def Greet(agent, contact):
                    return "the line"

        class Introducing(Tag):
            @Record
            def friend(agent, *, friend=None):
                agent.Knows(friend, nickname="Ru")
                return friend

            @Record
            def broken(agent):
                raise ValueError("refused at Parts")

        charlie, ruth = People("Charlie", "Ruth")
        ruth.nickname = "her own nickname"
        ruth.Greet = "her own greeting"
        before = dict(vars(ruth))
        Circle(charlie)
        with self.assertRaises(TagCompositionError):      # the call's own failure, never a NameError
            Introducing(charlie, friend=ruth)
        self.assertEqual(vars(ruth), before)              # she is a plain object again, her values back
        self.assertEqual(Tags(ruth), ())
        with self.assertRaises(TagResolutionError):
            charlie.Knows[ruth]                           # no Pair is left behind
        charlie.Knows(ruth, nickname="Ru2")
        self.assertEqual(charlie.Knows[ruth].nickname, "Ru2")   # a new linking builds a new Pair

    def test_a_generator_or_coroutine_is_a_links_function_only_where_the_kit_steps_it(self):
        def Declare(body):
            return type("Holder", (Tag,), {"Member": Link(type("Member", (Tag,), body))})

        def Generator():
            def generator(agent, contact):
                yield 1

            return generator

        def Coroutine():
            async def coroutine(agent, contact):
                return 1

            return coroutine

        def Async_Generator():
            async def async_generator(agent, contact):
                yield 1

            return async_generator

        def Link_Generator():
            def generator(link):
                yield 1

            return generator

        def Link_Async_Generator():
            async def async_generator(link):
                yield 1

            return async_generator

        def Link_Coroutine():
            async def coroutine(link):
                return 1

            return coroutine

        @types.coroutine
        def old_style_coroutine(agent, contact):
            yield

        async_generators = {
                "an async generator Pair Action": {"Feed": Async_Generator()},
                "an async generator Operation": {"Scan": Operation(Link_Async_Generator())},
                }
        generator_based = {
                "a types.coroutine Pair Action": {"Old": old_style_coroutine},
                }
        never_stepped = {
                "a generator Record": {"stream": Record(Generator())},
                "a coroutine Record": {"fetch": Record(Coroutine())},
                "a generator Precondition": {"Vet": Pre(Generator())},
                "a coroutine Postcondition": {"Still": Post(Coroutine())},
                "a generator Imprint": {"Note": Imprint(Generator())},
                "a coroutine Imprint": {"Later": Imprint(Coroutine())},
                "a generator teardown": {"Forget": Rip(Generator())},
                "a coroutine teardown": {"Forget": Rip(Coroutine())},
                "a coroutine Report builder": {"total": Report(Link_Coroutine())},
                "a generator Report builder": {"count": Report(Link_Generator())},
                }

        for label, body in async_generators.items():
            with self.subTest(label):
                with self.assertRaises(TagDeclarationError) as raised:
                    Declare(body)

                self.assertIn("async generator", str(raised.exception))

        for label, body in generator_based.items():
            with self.subTest(label):
                with self.assertRaises(TagDeclarationError) as raised:
                    Declare(body)

                self.assertIn("@types.coroutine", str(raised.exception))

        for label, body in never_stepped.items():
            with self.subTest(label):
                with self.assertRaises(TagDeclarationError) as raised:
                    Declare(body)

                self.assertIn("never iterates or awaits", str(raised.exception))

        for label, body in {
                "a generator Pair Action": {"Stream": Generator()},
                "a coroutine Pair Action": {"Fetch": Coroutine()},
                "a generator Operation": {"Scan": Operation(Link_Generator())},
                "a coroutine Operation": {"Wait": Operation(Link_Coroutine())},
                "a coroutine class method": {"Later": classmethod(Link_Coroutine())},
                }.items():
            with self.subTest(label):
                Declare(body)                         # the kit steps these behind the doors

        async def _helper(value):
            yield value

        def numbers():
            yield 1

        Declare({"_helper": _helper, "numbers": staticmethod(numbers)})   # the Relation's own, plain Python

    def test_a_generator_handed_through_a_link_is_left_alone(self):
        holder = {}

        class Circle(Tag):
            @Secret
            @Record
            def ledger(agent):
                return "his ledger"

            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    return since

                @Public
                def Hand_Back(agent, contact, thing):
                    return thing

        class Writer(Tag):
            @Secret
            @Record
            def diary(agent):
                return "her secret"

            def Round_Trip(agent):
                own = (Read_Or_Shut(agent, "diary") for _ in range(1))
                return list(agent.Hand_Back(own))         # her own generator, iterated in her own code

        charlie, dora, ruth = People("Charlie", "Dora", "Ruth")
        holder["agent"] = charlie
        Circle(charlie)
        Writer(ruth)
        stranger = (Read_Or_Shut(holder["agent"], "ledger") for _ in range(1))
        charlie.Knows(dora, since=stranger)
        self.assertIs(charlie.Knows[dora].since, stranger)   # the Record keeps what it was given
        self.assertEqual(list(stranger), ["shut"])        # a stranger's code never runs inside his door
        charlie.Knows(ruth)
        self.assertEqual(ruth.Round_Trip(), ["her secret"])

    def test_a_relation_bound_a_second_time_is_refused(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                pass

            @Link
            class Trusts(Knows):
                pass

        with self.assertRaises(TagDeclarationError):
            class Undercover(Circle):
                Knows = Circle.Trusts                     # a Shape Relation passed off as an extension

        with self.assertRaises(TagDeclarationError):
            class Fans(Tag):
                Follows = Circle.Knows                    # another Tag's Relation, under another name

        with self.assertRaises(TagDeclarationError):
            class Twice(Tag):
                @Link
                class Likes(Tag):
                    pass

                Adores = Likes                            # one body, two names

        bob, ruth = People("Bob", "Ruth")
        Circle(bob)
        bob.Trusts(ruth)                                  # the declaring Tag is unharmed
        self.assertIn(ruth, bob.Knows)

    def test_a_relation_whose_body_was_refused_can_be_declared_again(self):
        class Elsewhere(Tag):
            @Link
            class Likes(Tag):
                pass

        @Link
        class Knows(Tag):
            pass

        relation = Knows

        with self.assertRaises(TagDeclarationError):
            class Refused(Tag):
                Knows = relation                          # checked first, then the body is refused
                Likes = Elsewhere.Likes

        class Circle(Tag):
            Knows = relation                              # the refused body declared nothing

        self.assertIs(Circle.Knows, relation)

    def test_secret_on_a_relations_static_method_is_refused(self):
        with self.assertRaises(TagDeclarationError):
            class Vault(Tag):
                @Link
                class Member(Tag):
                    @Secret
                    @staticmethod
                    def code():
                        return "static secret"

        with self.assertRaises(TagDeclarationError):
            class Vault_Again(Tag):
                @Link
                class Member(Tag):
                    @staticmethod
                    @Secret
                    def code():
                        return "static secret"

    def test_public_on_a_pair_condition_or_imprint_is_refused(self):
        with self.assertRaises(TagDeclarationError):
            class Watching(Tag):
                @Link
                class Knows(Tag):
                    @Public
                    @Post
                    def Still_Honest(agent, contact):
                        return contact.honest

        with self.assertRaises(TagDeclarationError):
            class Welcoming(Tag):
                @Link
                class Knows(Tag):
                    @Public
                    @Imprint
                    def Welcome(agent, contact):
                        pass

        class Parting(Tag):                               # a teardown is callable, as on any Tag
            @Link
            class Knows(Tag):
                @Public
                @Rip
                def Forget(agent, contact):
                    return "forgotten"

        charlie, ruth = People("Charlie", "Ruth")
        Parting(charlie)
        charlie.Knows(ruth)
        self.assertEqual(ruth.Forget(), "forgotten")

    def test_a_name_is_a_line_or_a_link_member_never_both(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Public
                def Greet(agent, contact):
                    return "the line"

                @Report
                def capacity(link):
                    return 150

        with self.assertRaises(TagDeclarationError):
            class Plain_Over_Line(Circle):
                @Link
                class Knows(Circle.Knows):
                    Greet = "a plain value of the extension"

        with self.assertRaises(TagDeclarationError):
            class Line_Over_Report(Circle):
                @Link
                class Knows(Circle.Knows):
                    @Public
                    def capacity(agent, contact):
                        return "a line"

        class Fine(Circle):                               # other names extend as before
            @Link
            class Knows(Circle.Knows):
                motto = "kind words"

        charlie, ruth = People("Charlie", "Ruth")
        Fine(charlie)
        charlie.Knows(ruth)
        self.assertEqual(ruth.Greet(), "the line")
        self.assertEqual(charlie.Knows.capacity, 150)
        self.assertEqual(charlie.Knows.motto, "kind words")


class Third_Round_Tests(unittest.TestCase):
    """The third review round, on the newest code."""

    def test_an_undone_linking_keeps_what_another_call_wrote_on_the_pair(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    return since

            @Link
            class Trusts(Knows):
                pass

        class Annotating(Tag):                            # Bob's own call: it finishes
            @Record
            def note(agent, *, about=None):
                agent.Knows[about].since = "annotated by Bob"
                return True

        class Joining(Tag):                               # a call on Ruth
            @Record
            def trusted(agent, *, by=None):
                by.Trusts(agent)
                return True

            @Record
            def annotated(agent, *, by=None):
                Annotating(by, about=agent)
                return True

            @Record
            def broken(agent):
                raise ValueError("Ruth's later Record fails")

        bob, ruth = People("Bob", "Ruth")
        Circle(bob)
        bob.Knows(ruth, since=1)
        with self.assertRaises(TagCompositionError):
            Joining(ruth, by=bob)
        self.assertIn(bob, Annotating)
        self.assertNotIn(ruth, bob.Trusts)
        self.assertEqual(bob.Knows[ruth].since, "annotated by Bob")

    def test_an_undone_linking_keeps_a_value_she_wrote_since(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Public
                def Greet(agent, contact):
                    return "the line"

        class Introducing(Tag):
            @Record
            def friend(agent, *, friend=None):
                agent.Knows(friend)
                friend.Greet = "written after the linking"
                return friend

            @Record
            def broken(agent):
                raise ValueError("refused at Parts")

        charlie, ruth = People("Charlie", "Ruth")
        Circle(charlie)
        with self.assertRaises(TagCompositionError):
            Introducing(charlie, friend=ruth)
        self.assertEqual(ruth.Greet, "written after the linking")

    def test_an_undone_relinking_keeps_her_earlier_history(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                pass

        class Reintroducing(Tag):
            @Record
            def friend(agent, *, friend=None):
                agent.Knows(friend)
                return friend

            @Record
            def broken(agent):
                raise ValueError("refused at Parts")

        charlie, ruth = People("Charlie", "Ruth")
        Circle(charlie)
        charlie.Knows(ruth)
        del charlie.Knows[ruth]
        self.assertTrue(isinstance(ruth, charlie.Knows))
        with self.assertRaises(TagCompositionError):
            Reintroducing(charlie, friend=ruth)
        self.assertTrue(isinstance(ruth, charlie.Knows))  # the linking undone gave her none of it

    def test_the_first_interrupt_at_a_deletion_is_the_one_raised(self):
        class First(KeyboardInterrupt):
            pass

        class Second(KeyboardInterrupt):
            pass

        log = []

        class Guard(Tag):
            @Rip
            def Stand_Down(agent):
                log.append("guard")
                raise First("her own teardown")

        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Forget(agent, contact):
                    log.append(contact.name)
                    if contact.name == "Ruth":
                        raise Second("a Link's exit")

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Circle(charlie)
        charlie.Knows(ruth)
        charlie.Knows(sam)
        Guard(charlie)
        raised = None
        try:
            _teardown_all(charlie)
        except BaseException as error:                    # an interrupt must not stop the test run
            raised = type(error)
        self.assertIs(raised, First)
        self.assertEqual(log[0], "guard")
        self.assertEqual(sorted(log[1:]), ["Ruth", "Sam"])   # every Link exit still runs

    def test_extending_a_shape_relation_checks_its_own_link_only(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Public
                def x(agent, contact):
                    return "the Knows line"

            @Link
            class Trusts(Knows):
                @Report
                def x(link):
                    return "the Trusts Report"

        class Undercover(Circle):                         # Trusts' Link holds no Knows line
            @Link
            class Trusts(Circle.Trusts):
                @Report
                def x(link):
                    return "the extended Report"

        charlie, ruth = People("Charlie", "Ruth")
        Undercover(charlie)
        charlie.Trusts(ruth)
        self.assertEqual(ruth.x(), "the Knows line")
        self.assertEqual(charlie.Trusts.x, "the extended Report")

    def test_sibling_extensions_that_mix_a_line_and_a_link_member_meet_refused(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                pass

        class Spy(Circle):
            @Link
            class Knows(Circle.Knows):
                @Public
                def x(agent, contact):
                    return "a line"

        class Clerk(Circle):
            @Link
            class Knows(Circle.Knows):
                @Report
                def x(link):
                    return "a Report"

        charlie, ruth = People("Charlie", "Ruth")
        Spy(charlie)
        charlie.Knows(ruth)
        with self.assertRaises(TagCompositionError):
            Clerk(charlie)                                # the two meet on Charlie's Link
        self.assertNotIn(charlie, Clerk)                  # nothing changed
        self.assertEqual(ruth.x(), "a line")

        bob = Character("Bob")
        Clerk(bob)
        with self.assertRaises(TagCompositionError):
            Spy(bob)                                      # in the other order too
        self.assertEqual(bob.Knows.x, "a Report")

    def test_a_relation_whose_declaring_tag_is_gone_can_be_declared_again(self):
        @Link
        class Knows(Tag):
            pass

        relation = Knows

        def Declare_And_Drop():
            class Gone(Tag):
                Knows = relation

        Declare_And_Drop()
        gc.collect()                                      # the first declaring Tag is gone

        class Circle(Tag):
            Knows = relation

        self.assertIs(Circle.Knows, relation)

    def test_an_undone_linking_on_a_shared_pair_keeps_what_the_agents_extension_gave_it(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                pass

            @Link
            class Trusts(Knows):
                @Record
                def level(agent, contact, *, level=None):
                    return level

        class Vetting(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def vetted(agent, contact):
                    return True

        class Joining(Tag):                               # a call on Ruth
            @Record
            def trusted(agent, *, by=None):
                by.Trusts(agent, level=5)
                return True

            @Record
            def promoted(agent, *, by=None):
                Vetting(by)                               # Bob's own call reaches her Pair since
                return True

            @Record
            def broken(agent):
                raise ValueError("Ruth's later Record fails")

        bob, ruth = People("Bob", "Ruth")
        Circle(bob)
        bob.Knows(ruth)
        with self.assertRaises(TagCompositionError):
            Joining(ruth, by=bob)
        self.assertNotIn(ruth, bob.Trusts)                # she left Trusts
        self.assertTrue(bob.Knows[ruth].vetted)           # what Bob's call gave stays
        self.assertFalse(hasattr(bob.Knows[ruth], "level"))   # and only that: nothing of Trusts stays, no sticky Record


class Final_Round_Tests(unittest.TestCase):
    """The last review round, on the third round's fixes."""

    def test_an_undone_extension_never_brings_back_what_a_refusal_took(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                pass

            @Link
            class Trusts(Knows):
                @Record
                def level(agent, contact, *, level=None):
                    return level

        class Vetting(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def vetted(agent, contact):
                    return True

        class Elsewhere(Tag):
            @Link
            class Other(Tag):
                @Record
                def trusted(agent, contact, *, ruth=None):
                    agent.Trusts(ruth, level=5)           # undone with the refusal
                    return True

                @Record
                def vetted(agent, contact, *, ruth=None):
                    Vetting(agent)                        # his own call, handed outward
                    return True

                @Record
                def broken(agent, contact, *, ruth=None):
                    raise ValueError("the Other linking is refused")

        class Outer(Tag):
            @Record
            def first(agent, *, sam=None, ruth=None):
                agent.Other(sam, ruth=ruth)               # the refusal rolls Outer back too
                return True

        bob, ruth, sam = People("Bob", "Ruth", "Sam")
        Circle(bob)
        Elsewhere(bob)
        bob.Knows(ruth)
        with self.assertRaises(TagCompositionError):
            Outer(bob, sam=sam, ruth=ruth)
        self.assertNotIn(bob, Vetting)
        self.assertNotIn(ruth, bob.Trusts)
        bob.Trusts(ruth, level=7)                         # the Trusts Layer is off: a new linking builds it
        self.assertEqual(bob.Trusts[ruth].level, 7)

    def test_an_undone_extension_never_revives_a_dropped_pair(self):
        torn = []

        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Forget(agent, contact):
                    torn.append(contact.name)

        class Vetting(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def vetted(agent, contact):
                    return True

        class Elsewhere(Tag):
            @Link
            class Other(Tag):
                @Record
                def a(agent, contact, *, ruth=None):
                    agent.Knows(ruth)                     # a new Pair, dropped with the refusal
                    return True

                @Record
                def b(agent, contact, *, ruth=None):
                    Vetting(agent)
                    return True

                @Record
                def broken(agent, contact, *, ruth=None):
                    raise ValueError("refused")

        class Outer(Tag):
            @Record
            def first(agent, *, sam=None, ruth=None):
                agent.Other(sam, ruth=ruth)
                return True

        bob, ruth, sam = People("Bob", "Ruth", "Sam")
        Circle(bob)
        Elsewhere(bob)
        with self.assertRaises(TagCompositionError):
            Outer(bob, sam=sam, ruth=ruth)
        gc.collect()
        self.assertNotIn(ruth, bob.Knows)
        self.assertEqual(torn, [])                        # no teardown for a linking that never happened

    def test_a_failed_imprint_still_lets_an_undo_keep_another_calls_write(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    return since

            @Link
            class Trusts(Knows):
                @Imprint
                def Welcome(agent, contact):
                    raise ValueError("after her entry: the linking stays")

        class Annotating(Tag):
            @Record
            def note(agent, *, about=None):
                agent.Knows[about].since = "annotated by Bob"
                return True

        class Joining(Tag):                               # a call on Ruth
            @Record
            def trusted(agent, *, by=None):
                try:
                    by.Trusts(agent)
                except TagImprintError:
                    pass
                return True

            @Record
            def annotated(agent, *, by=None):
                Annotating(by, about=agent)
                return True

            @Record
            def broken(agent):
                raise ValueError("Ruth's later Record fails")

        bob, ruth = People("Bob", "Ruth")
        Circle(bob)
        bob.Knows(ruth, since=1)
        with self.assertRaises(TagCompositionError):
            Joining(ruth, by=bob)
        self.assertNotIn(ruth, bob.Trusts)
        self.assertEqual(bob.Knows[ruth].since, "annotated by Bob")

    def test_an_undone_linking_keeps_another_agents_action_she_holds(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Public
                def Greet(agent, contact):
                    return "the line"

        class Speaker(Tag):
            def Speak(agent):
                return f"{agent.name} speaks"

        class Introducing(Tag):
            @Record
            def friend(agent, *, friend=None, other=None):
                agent.Knows(friend)
                friend.Greet = other.Speak                # another Agent's Action, written on her since
                return friend

            @Record
            def broken(agent):
                raise ValueError("refused at Parts")

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Circle(charlie)
        Speaker(sam)
        with self.assertRaises(TagCompositionError):
            Introducing(charlie, friend=ruth, other=sam)
        self.assertEqual(ruth.Greet(), "Sam speaks")

    def test_a_refusal_never_calls_an_agents_own_equality(self):
        class Strict:
            def __init__(strict, name):
                strict.name = name

            def __eq__(strict, other):
                if strict is other:
                    return True
                raise TypeError(f"{strict.name} is not comparable")

            __hash__ = object.__hash__

        class Club(Tag):
            @Link
            class Member(Tag):
                pass

        holder = {}

        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def joined(agent, contact):
                    agent.Member(contact)
                    Club(holder["dora"])
                    return True

                @Record
                def broken(agent, contact):
                    raise ValueError("the linking is refused")

        charlie, ruth, dora = Strict("charlie"), Strict("ruth"), Strict("dora")
        holder["dora"] = dora
        Club(charlie)
        Circle(charlie)
        with self.assertRaises(TagCompositionError):
            charlie.Knows(ruth)
        self.assertNotIn(ruth, charlie.Member)
        self.assertIn(dora, Club)


# ------------------------------------------------------------------
# Generators and coroutines in a Relation: every step behind the doors
# ------------------------------------------------------------------


Seen: list = []   # what a Link's cleanup saw, cleared by each test

OPEN_DOORS = ("his ledger", "the Pair's secret", "shut")   # the Agent's and the Pair's open, the Contact's shut


def Doors_Seen(agent, contact):
    """What a Link's code sees at one step: the Agent's secret, the Pair's,
    the Contact's."""

    return (
            Read_Or_Shut(agent, "ledger"),
            Read_Or_Shut(agent.Sees[contact], "code"),
            Read_Or_Shut(contact, "journal"),
            )


def Counters(*things):
    """The composition counter of each: zero when no door of it is open."""

    return tuple(_state_of(thing).composing for thing in things)


@types.coroutine
def Pause():
    yield   # a bare suspension: whoever drives the coroutine resumes it


class Observed(Tag):
    @Secret
    @Record
    def ledger(agent):
        return "his ledger"

    @Link
    class Sees(Tag):
        @Secret
        @Record
        def code(agent, contact):
            return "the Pair's secret"

        @Public
        def Stream(agent, contact):
            yield Doors_Seen(agent, contact)
            yield Doors_Seen(agent, contact)
            return "finished"

        def Echo(agent, contact):
            got = yield "ready"
            got = yield (got, Doors_Seen(agent, contact))
            return got

        def Guarded(agent, contact):
            try:
                yield "first"
            except ValueError:
                yield ("caught", Doors_Seen(agent, contact))
            yield "after"

        def Cleaning(agent, contact):
            try:
                yield "working"
            finally:
                Seen.append(Doors_Seen(agent, contact))

        def Goodbye(agent, contact):
            try:
                yield "working"
            except GeneratorExit:
                Seen.append(Doors_Seen(agent, contact))
                return "goodbye"

        def Stubborn(agent, contact):
            try:
                yield 1
            except GeneratorExit:
                yield 2

        def Interrupted(agent, contact):
            yield 1
            raise KeyboardInterrupt

        def Relay(agent, contact):
            inner = yield from agent.Sees[contact].Stream()
            yield ("relayed", inner)

        def Forgets(agent, contact):
            del agent, contact
            yield 1
            yield 2

        def Calls_Her(agent, contact):
            yield contact.Read_Own()   # her own Action: her door opens for it, as for any code that calls her

        async def Fetch(agent, contact):
            before = Doors_Seen(agent, contact)
            await asyncio.sleep(0)
            after = Doors_Seen(agent, contact)
            return before, after

        async def Slow(agent, contact):
            try:
                await asyncio.sleep(10)
            finally:
                Seen.append(Doors_Seen(agent, contact))

        async def Hang(agent, contact):
            try:
                await Pause()
            finally:
                Seen.append(Doors_Seen(agent, contact))

            return Doors_Seen(agent, contact)

        async def Coroutine_Goodbye(agent, contact):
            try:
                await Pause()
            except GeneratorExit:
                Seen.append(Doors_Seen(agent, contact))
                return "goodbye"

        async def Enter_Her_Hook(agent, contact):
            async with contact as inside:       # her own async context hook, entered by the Link's code
                return inside

        async def Fails(agent, contact):
            await asyncio.sleep(0)
            raise ValueError("a failing coroutine")

        async def Forgets_Later(agent, contact):
            del agent, contact
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            return "done"

        async def Calls_Her_Later(agent, contact):
            await asyncio.sleep(0)
            return contact.Read_Own()

        @Public
        async def Greet_Later(agent, contact):
            await asyncio.sleep(0)
            return Doors_Seen(agent, contact)


class Journaled(Tag):
    @Secret
    @Record
    def journal(agent):
        return "her journal"

    def Read_Own(agent):
        return agent.journal

    def Walk(agent, steps):
        return [(step, Read_Or_Shut(agent, "journal")) for step in steps]

    def Walk_Own_Line(agent):
        return [(step, Read_Or_Shut(agent, "journal")) for step in agent.Stream()]

    def Close_It(agent, steps):
        return steps.close()

    def Drop_It(agent, held):
        held.clear()   # the last reference goes while her door is open

    def Collect(agent):
        gc.collect()   # the cyclic collector runs while her door is open

    def Run_Own_Line(agent):
        return asyncio.run(agent.Greet_Later())

    def Drive(agent, work):
        before = _state_of(agent).composing
        work()

        return before, _state_of(agent).composing


class Step_Contextvar_Tests(unittest.TestCase):
    """A generator function or a coroutine function of a Relation: its body
    runs later, when it is iterated or awaited, so the kit takes each of its
    steps behind the doors of rule 3.6 (the Agent's and the Pair's open, every
    Contact's shut), and leaves every door as the caller had it between
    steps. An async generator, and a Record, a condition, an Imprint, a
    teardown or a Report builder that is lazy, stay refused."""

    def setUp(self):
        Seen.clear()
        self.charlie, self.ruth = People("Charlie", "Ruth")
        Observed(self.charlie)
        Journaled(self.ruth)
        self.charlie.Sees(self.ruth)
        self.pair = self.charlie.Sees[self.ruth]

    def counters(self):
        return Counters(self.charlie, self.ruth, self.pair)

    # -- generators --------------------------------------------------

    def test_a_generator_takes_every_step_behind_the_doors(self):
        steps = self.pair.Stream()
        self.assertEqual(next(steps), OPEN_DOORS)
        self.assertEqual(next(steps), OPEN_DOORS)         # the second step, long after the call returned
        with self.assertRaises(StopIteration) as stopped:
            next(steps)
        self.assertEqual(stopped.exception.value, "finished")
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_a_generator_is_a_generator_and_keeps_its_name(self):
        steps = self.pair.Stream()
        self.assertTrue(inspect.isgenerator(steps))
        self.assertEqual(steps.__name__, "Stream")
        self.assertIn("Sees.Stream", steps.__qualname__)
        self.assertEqual(list(self.pair.Stream()), [OPEN_DOORS, OPEN_DOORS])

    def test_her_own_code_keeps_her_door_between_two_steps(self):
        walked = self.ruth.Walk(self.ruth.Stream())       # her line, iterated in her Action
        self.assertEqual(walked, [(OPEN_DOORS, "her journal"), (OPEN_DOORS, "her journal")])
        self.assertEqual(self.ruth.Walk_Own_Line(), walked)   # a line made and iterated in her Action
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_send_throw_and_the_return_value_reach_the_links_code(self):
        echo = self.pair.Echo()
        self.assertEqual(next(echo), "ready")
        self.assertEqual(echo.send("hello"), ("hello", OPEN_DOORS))
        with self.assertRaises(StopIteration) as stopped:
            echo.send("bye")
        self.assertEqual(stopped.exception.value, "bye")
        with self.assertRaises(TypeError):
            self.pair.Echo().send("not yet")              # Python's own refusal, a just-started generator

        guarded = self.pair.Guarded()
        self.assertEqual(next(guarded), "first")
        self.assertEqual(guarded.throw(ValueError("in")), ("caught", OPEN_DOORS))   # handled in the body
        self.assertEqual(next(guarded), "after")

        stream = self.pair.Stream()
        next(stream)
        with self.assertRaises(KeyError):
            stream.throw(KeyError("out"))                 # not handled: it comes out
        with self.assertRaises(StopIteration):
            next(stream)

        with self.assertRaises(KeyError):
            self.pair.Stream().throw(KeyError("before the first step"))
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_close_runs_the_links_cleanup_behind_the_doors(self):
        steps = self.pair.Cleaning()
        next(steps)
        steps.close()
        self.assertEqual(Seen, [OPEN_DOORS])
        steps.close()                                     # closing again does nothing
        self.assertEqual(Seen, [OPEN_DOORS])
        self.pair.Cleaning().close()                      # never started: no cleanup, as Python's
        self.assertEqual(Seen, [OPEN_DOORS])

    def test_close_returns_what_the_body_returns_on_generator_exit(self):
        steps = self.pair.Goodbye()
        next(steps)
        closed = steps.close()
        self.assertEqual(Seen, [OPEN_DOORS])
        self.assertEqual(closed, "goodbye" if sys.version_info >= (3, 13) else None)

    def test_a_coroutine_close_returns_what_the_body_returns_on_generator_exit(self):
        coroutine = self.pair.Coroutine_Goodbye()
        coroutine.send(None)
        closed = coroutine.close()
        self.assertEqual(Seen, [OPEN_DOORS])
        self.assertEqual(closed, "goodbye" if sys.version_info >= (3, 13) else None)

        coroutine = self.pair.Coroutine_Goodbye()
        coroutine.send(None)
        with self.assertRaises(StopIteration) as stopped:
            coroutine.throw(GeneratorExit)               # the body returns on it, as a plain coroutine's does
        self.assertEqual(stopped.exception.value, "goodbye")
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_an_error_thrown_into_a_link_coroutine_leaves_no_reference_cycle_behind(self):
        gc.disable()
        self.addCleanup(gc.enable)
        dora, sam = People("Dora", "Sam")
        Observed(dora)
        Journaled(sam)
        dora.Sees(sam)
        gone = [weakref.ref(dora), weakref.ref(sam)]

        coroutine = dora.Sees[sam].Hang()
        coroutine.send(None)

        with self.assertRaises(asyncio.CancelledError):
            coroutine.throw(asyncio.CancelledError())   # a task's cancellation, not caught by the body

        del coroutine, dora, sam
        self.assertEqual([reference() for reference in gone], [None, None])   # by reference count alone

    def test_a_generator_that_yields_on_close_is_a_runtime_error_and_stays_where_it_was(self):
        steps = self.pair.Stubborn()
        next(steps)
        with self.assertRaises(RuntimeError):
            steps.close()
        self.assertEqual(self.counters(), (0, 0, 0))
        with self.assertRaises(StopIteration):
            next(steps)                                   # still suspended where it yielded, as Python's

    def test_a_generator_exit_thrown_in_comes_out_as_it_does_from_any_generator(self):
        steps = self.pair.Stream()
        next(steps)
        with self.assertRaises(GeneratorExit):
            steps.throw(GeneratorExit)                    # not caught by the body: it comes out of throw()
        with self.assertRaises(StopIteration):
            next(steps)
        steps = self.pair.Goodbye()
        next(steps)
        with self.assertRaises(StopIteration) as stopped:
            steps.throw(GeneratorExit)                    # caught by the body, which returns
        self.assertEqual(stopped.exception.value, "goodbye")
        self.assertEqual(Seen, [OPEN_DOORS])

    def test_a_generator_closed_or_dropped_in_her_own_action_cleans_up_behind_the_doors(self):
        steps = self.pair.Cleaning()
        next(steps)
        self.ruth.Close_It(steps)                         # her door is open while she closes it
        self.assertEqual(Seen, [OPEN_DOORS])
        Seen.clear()
        held = [self.pair.Cleaning()]
        next(held[0])
        self.ruth.Drop_It(held)                           # collected while her door is open
        self.assertEqual(Seen, [OPEN_DOORS])
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_suspended_link_code_in_cyclic_garbage_is_closed_behind_the_doors(self):
        for make in (self.pair.Cleaning, self.pair.Hang):
            with self.subTest(make.__name__):
                Seen.clear()
                thing = make()
                if inspect.isgenerator(thing):
                    next(thing)
                else:
                    thing.send(None)

                holder = [thing]
                holder.append(holder)                     # a cycle: only the cyclic collector frees it
                del thing, holder
                self.ruth.Collect()                       # it runs while her door is open
                self.assertEqual(Seen, [OPEN_DOORS])      # the object she held is the older, so it closes first

    def test_every_door_is_as_it_was_after_any_way_out_of_a_generator(self):
        def work():
            list(self.pair.Stream())                      # to the end
            steps = self.pair.Stream()
            next(steps)
            steps.close()                                 # closed
            steps = self.pair.Stream()
            next(steps)
            with self.assertRaises(KeyError):
                steps.throw(KeyError("thrown"))           # thrown through
            steps = self.pair.Interrupted()
            next(steps)
            with self.assertRaises(KeyboardInterrupt):
                next(steps)                               # the body is interrupted
            steps = self.pair.Stream()
            next(steps)
            with self.assertRaises(KeyboardInterrupt):
                steps.throw(KeyboardInterrupt)            # an interrupt thrown in

        self.assertEqual(self.ruth.Drive(work), (1, 1))   # her door was open, and is again
        work()
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_a_generator_inside_a_generator_keeps_every_step_behind_the_doors(self):
        self.assertEqual(
                list(self.pair.Relay()),
                [OPEN_DOORS, OPEN_DOORS, ("relayed", "finished")],
                )
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_her_own_action_called_from_the_links_generator_opens_her_door_for_itself(self):
        self.assertEqual(list(self.pair.Calls_Her()), ["her journal"])   # doors follow the call

    def test_a_generator_never_keeps_its_agent_or_contact_alive(self):
        kept = [self.pair.Stream() for _ in range(2)]
        list(kept[0])                                     # to the end
        next(kept[1])
        kept[1].close()                                   # started, then closed
        forgetful = self.pair.Forgets()
        next(forgetful)                                   # the body let go of both
        references = (weakref.ref(self.charlie), weakref.ref(self.ruth))
        self.pair = None
        del self.charlie, self.ruth
        gc.collect()
        self.assertEqual([reference() for reference in references], [None, None])
        self.assertEqual(next(forgetful), 2)              # the next step finds nobody to open or shut

    # -- coroutines --------------------------------------------------

    def test_a_coroutine_takes_every_step_behind_the_doors(self):
        before, after = asyncio.run(self.pair.Fetch())
        self.assertEqual(before, OPEN_DOORS)
        self.assertEqual(after, OPEN_DOORS)               # after an await, in a later step
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_a_coroutine_is_a_coroutine_and_keeps_its_name(self):
        coroutine = self.pair.Fetch()
        self.assertTrue(inspect.iscoroutine(coroutine))
        self.assertTrue(asyncio.iscoroutine(coroutine))
        self.assertEqual(coroutine.__name__, "Fetch")
        self.assertIn("Sees.Fetch", coroutine.__qualname__)
        asyncio.run(coroutine)

    def test_a_coroutine_run_inside_her_own_action_still_finds_her_door_shut(self):
        self.assertEqual(self.ruth.Run_Own_Line(), OPEN_DOORS)   # asyncio.run beneath her open door
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_other_tasks_keep_their_own_doors_while_a_link_coroutine_waits(self):
        async def hers():
            await asyncio.sleep(0)
            return self.ruth.Read_Own()                   # her Action in another task: her door opens for it

        async def his():
            await asyncio.sleep(0)
            return Read_Or_Shut(self.charlie, "ledger")   # nobody's Action: his door is shut

        async def main():
            return await asyncio.gather(self.pair.Fetch(), hers(), his())

        self.assertEqual(
                asyncio.run(main()),
                [(OPEN_DOORS, OPEN_DOORS), "her journal", "shut"],
                )
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_her_own_action_called_from_the_links_coroutine_opens_her_door_for_itself(self):
        self.assertEqual(asyncio.run(self.pair.Calls_Her_Later()), "her journal")

    def test_gather_wait_for_and_a_coroutine_awaited_from_another(self):
        async def main():
            both = await asyncio.gather(self.pair.Fetch(), self.pair.Fetch())
            only = await asyncio.wait_for(self.pair.Fetch(), 5)

            async def outer():
                first = await self.pair.Fetch()
                with self.assertRaises(ValueError):
                    await self.pair.Fails()

                return first

            return both, only, await outer()

        both, only, third = asyncio.run(main())
        self.assertEqual(both, [(OPEN_DOORS, OPEN_DOORS)] * 2)
        self.assertEqual(only, (OPEN_DOORS, OPEN_DOORS))
        self.assertEqual(third, (OPEN_DOORS, OPEN_DOORS))
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_a_cancelled_task_cleans_up_behind_the_doors(self):
        async def main():
            task = asyncio.ensure_future(self.pair.Slow())
            await asyncio.sleep(0)                        # its first step: the body waits
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        asyncio.run(main())
        self.assertEqual(Seen, [OPEN_DOORS])
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_a_timeout_cleans_up_behind_the_doors(self):
        async def main():
            with self.assertRaises(TimeoutError):
                await asyncio.wait_for(self.pair.Slow(), 0.01)

            with self.assertRaises(TimeoutError):
                async with asyncio.timeout(0.01):
                    await self.pair.Slow()

        asyncio.run(main())
        self.assertEqual(Seen, [OPEN_DOORS, OPEN_DOORS])
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_a_task_group_cancels_the_others_and_each_cleans_up_behind_the_doors(self):
        async def main():
            with self.assertRaises(ExceptionGroup):
                async with asyncio.TaskGroup() as group:
                    group.create_task(self.pair.Slow())
                    group.create_task(self.pair.Slow())
                    group.create_task(self.pair.Fails())

        asyncio.run(main())
        self.assertEqual(Seen, [OPEN_DOORS, OPEN_DOORS])
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_a_task_cancelled_before_its_first_step_runs_nothing_and_warns_of_nothing(self):
        async def main():
            task = asyncio.ensure_future(self.pair.Slow())
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            asyncio.run(main())
            gc.collect()

        self.assertEqual(Seen, [])                        # the body never began
        self.assertEqual([str(w.message) for w in caught if "never awaited" in str(w.message)], [])

    def test_a_coroutine_never_awaited_warns_once_under_the_links_name(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.pair.Fetch()                             # dropped at once
            gc.collect()

        messages = [str(w.message) for w in caught if "never awaited" in str(w.message)]
        self.assertEqual(len(messages), 1)
        self.assertIn("Sees.Fetch", messages[0])

    def test_a_wrong_call_fails_at_the_call_as_pythons_does(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with self.assertRaises(TypeError) as raised:
                self.pair.Fetch(1, 2, 3)

            self.assertIn("Sees.Fetch()", str(raised.exception))   # it names the function, as Python's does
            with self.assertRaises(TypeError) as raised:
                self.pair.Stream(1, 2, 3)

            self.assertIn("Stream()", str(raised.exception))

            gc.collect()

        self.assertEqual(caught, [])

    def test_a_coroutine_driven_by_hand_takes_every_step_behind_the_doors(self):
        coroutine = self.pair.Hang()
        self.assertIsNone(coroutine.send(None))           # up to the first suspension
        self.assertEqual(self.counters(), (0, 0, 0))      # between steps every door is the caller's
        with self.assertRaises(StopIteration) as stopped:
            coroutine.send(None)
        self.assertEqual(stopped.exception.value, OPEN_DOORS)
        self.assertEqual(Seen, [OPEN_DOORS])

    def test_a_coroutine_driven_by_hand_leaves_her_own_code_her_door(self):
        coroutine = self.pair.Hang()
        coroutine.send(None)                              # suspended; nothing of it is left on her
        self.assertEqual(self.ruth.Read_Own(), "her journal")
        coroutine.close()

    def test_an_interrupt_thrown_into_a_coroutine_leaves_every_door_as_it_was(self):
        coroutine = self.pair.Hang()
        coroutine.send(None)
        with self.assertRaises(KeyboardInterrupt):
            coroutine.throw(KeyboardInterrupt)
        self.assertEqual(Seen, [OPEN_DOORS])
        self.assertEqual(self.counters(), (0, 0, 0))

    def test_a_coroutine_closed_in_another_context_cleans_up_behind_the_doors(self):
        coroutine = self.pair.Hang()
        contextvars.copy_context().run(coroutine.send, None)   # its first step, in a context of its own
        self.ruth.Close_It(coroutine)                     # closed from her Action, in this one
        self.assertEqual(Seen, [OPEN_DOORS])

    def test_a_coroutine_collected_in_her_own_action_cleans_up_behind_the_doors(self):
        held = [self.pair.Hang()]
        held[0].send(None)
        self.ruth.Drop_It(held)
        self.assertEqual(Seen, [OPEN_DOORS])

    def test_her_async_context_hook_awaiting_a_line_finds_her_door_shut(self):
        class Hooked(Tag):
            @Secret
            @Record
            def journal(agent):
                return "her journal"

            async def __aenter__(agent):
                before = agent.journal
                seen = await agent.Greet_Later()          # a line, awaited inside her hook
                return before, seen, agent.journal

            async def __aexit__(agent, kind, value, traceback):
                return None

        sam = Character("Sam")
        Hooked(sam)
        self.charlie.Sees(sam)

        async def main():
            async with sam as got:
                return got

        before, seen, after = asyncio.run(main())
        self.assertEqual(before, "her journal")
        self.assertEqual(seen, OPEN_DOORS)                # the Link's code found her door shut
        self.assertEqual(after, "her journal")            # and her hook has it back

    def test_her_async_hook_entered_by_the_links_coroutine_is_her_own_code_at_every_step(self):
        class Hooked(Tag):
            @Secret
            @Record
            def journal(agent):
                return "her journal"

            async def __aenter__(agent):
                before = agent.journal
                await asyncio.sleep(0)                   # the Link's coroutine waits inside her hook
                return before, agent.journal             # and her hook still has its door

            async def __aexit__(agent, kind, value, traceback):
                return None

        sam = Character("Sam")
        Hooked(sam)
        self.charlie.Sees(sam)
        self.assertEqual(
                asyncio.run(self.charlie.Sees[sam].Enter_Her_Hook()),
                ("her journal", "her journal"),
                )

    def test_a_hook_the_links_coroutine_enters_leaves_her_hooks_door_in_place(self):
        holder = {}

        class Other(Tag):
            async def __aenter__(agent):
                return "in"

            async def __aexit__(agent, kind, value, traceback):
                return None

        class Busy(Tag):
            @Link
            class Sees(Tag):
                @Public
                async def Meanwhile(agent, contact):
                    async with holder["other"]:       # another Agent's hook opens and closes a door here
                        await asyncio.sleep(0)

                    return Read_Or_Shut(contact, "journal")

        class Hooked(Tag):
            @Secret
            @Record
            def journal(agent):
                return "her journal"

            async def __aenter__(agent):
                seen = await agent.Meanwhile()
                return seen, agent.journal                # her hook's door must still be hers

            async def __aexit__(agent, kind, value, traceback):
                return None

        dora, sam, tom = Character("Dora"), Character("Sam"), Character("Tom")
        Busy(dora)
        Hooked(sam)
        Other(tom)
        holder["other"] = tom
        dora.Sees(sam)

        async def main():
            async with sam as got:
                return got

        self.assertEqual(asyncio.run(main()), ("shut", "her journal"))

    def test_a_sync_function_marked_as_a_coroutine_function_is_called_behind_the_doors(self):
        class Marked(Tag):
            @Link
            class Sees(Tag):
                @Public
                @inspect.markcoroutinefunction
                def Late(agent, contact):
                    prelude = Read_Or_Shut(contact, "journal")   # plain code: it runs when the call is made

                    async def body():
                        return prelude

                    return body()

        class Waiting(Tag):
            @Secret
            @Record
            def journal(agent):
                return "her journal"

            def Run_Late(agent):
                return asyncio.run(agent.Late())              # beneath her open door

        dora, sam = Character("Dora"), Character("Sam")
        Marked(dora)
        Waiting(sam)
        dora.Sees(sam)
        self.assertEqual(sam.Run_Late(), "shut")

    def test_a_coroutine_never_keeps_its_agent_or_contact_alive(self):
        async def main():
            task = asyncio.ensure_future(self.pair.Forgets_Later())
            await asyncio.sleep(0)                        # the body let go of both, and waits
            references = (weakref.ref(self.charlie), weakref.ref(self.ruth))
            self.pair = None
            del self.charlie, self.ruth
            gc.collect()
            gone = [reference() for reference in references]
            return gone, await task

        self.assertEqual(asyncio.run(main()), ([None, None], "done"))

    # -- Operations and class methods --------------------------------

    def test_an_operation_that_is_a_generator_or_a_coroutine_is_stepped_behind_the_doors(self):
        holder = {}

        class Rostered(Tag):
            @Secret
            @Record
            def ledger(agent):
                return "his ledger"

            @Link
            class Sees(Tag):
                @Operation
                def Scan(link, contact):
                    yield Read_Or_Shut(holder["agent"], "ledger"), Read_Or_Shut(contact, "journal")

                @Operation
                async def Scan_Later(link, *, who):
                    await asyncio.sleep(0)
                    return Read_Or_Shut(holder["agent"], "ledger"), Read_Or_Shut(who, "journal")

                @classmethod
                def Walk(link, contact):
                    yield Read_Or_Shut(contact, "journal")

                @Secret
                @Operation
                def Vault(link):
                    yield Read_Or_Shut(holder["agent"], "ledger")

        class Keeper(Tag):
            def Look(agent):
                return list(agent.Sees.Vault())           # inside his own code

        dora = Character("Dora")
        Rostered(dora)
        Keeper(dora)
        holder["agent"] = dora
        dora.Sees(self.ruth)
        self.assertEqual(list(dora.Sees.Scan(self.ruth)), [("his ledger", "shut")])   # a Contact by position
        self.assertEqual(asyncio.run(dora.Sees.Scan_Later(who=self.ruth)), ("his ledger", "shut"))   # by name
        self.assertEqual(list(dora.Sees.Walk(self.ruth)), ["shut"])
        self.assertEqual(dora.Look(), ["his ledger"])
        with self.assertRaises(AttributeError):
            dora.Sees.Vault()                             # a secret Operation answers inside its Agent only
        self.assertEqual(Counters(dora, self.ruth), (0, 0))

    def test_an_underlay_chain_of_generator_and_coroutine_actions_steps_every_layer(self):
        class Circle(Tag):
            @Secret
            @Record
            def ledger(agent):
                return "his ledger"

            @Link
            class Knows(Tag):
                def Count(agent, contact):
                    yield ("base", Read_Or_Shut(agent, "ledger"), Read_Or_Shut(contact, "journal"))

                async def Later(agent, contact):
                    await asyncio.sleep(0)
                    return ("base", Read_Or_Shut(agent, "ledger"), Read_Or_Shut(contact, "journal"))

            @Link
            class Trusts(Knows):
                @Underlay
                def Count(agent, contact, underlay):
                    yield ("top", Read_Or_Shut(agent, "ledger"), Read_Or_Shut(contact, "journal"))
                    yield from underlay()                     # the Layer beneath is stepped too

                @Underlay
                async def Later(agent, contact, underlay):
                    return ("top", await underlay(), Read_Or_Shut(agent, "ledger"))

        dora = Character("Dora")
        Circle(dora)
        dora.Trusts(self.ruth)
        self.assertEqual(
                list(dora.Trusts[self.ruth].Count()),
                [("top", "his ledger", "shut"), ("base", "his ledger", "shut")],
                )
        self.assertEqual(
                asyncio.run(dora.Trusts[self.ruth].Later()),
                ("top", ("base", "his ledger", "shut"), "his ledger"),
                )
        self.assertEqual(Counters(dora, self.ruth), (0, 0))

    def test_a_self_link_opens_her_door_as_the_agent(self):
        class Selfish(Tag):
            @Secret
            @Record
            def ledger(agent):
                return "his ledger"

            @Link
            class Sees(Tag):
                def Mirror(agent, contact):
                    yield Read_Or_Shut(contact, "ledger")

                async def Mirror_Later(agent, contact):
                    await asyncio.sleep(0)
                    return Read_Or_Shut(contact, "ledger")

        dora = Character("Dora")
        Selfish(dora)
        dora.Sees(dora)
        self.assertEqual(list(dora.Sees[dora].Mirror()), ["his ledger"])
        self.assertEqual(asyncio.run(dora.Sees[dora].Mirror_Later()), "his ledger")

    # -- what stays refused ------------------------------------------

    def test_only_a_function_declared_as_a_generator_or_a_coroutine_is_stepped(self):
        def ordinary(agent, contact):
            return None

        def handed_back(agent, contact):
            return (value for value in range(2))          # makes a generator: it is not one

        def generator(agent, contact):
            yield None

        async def coroutine(agent, contact):
            return None

        Link(type("Member", (Tag,), {
                "Ordinary": ordinary,
                "Handed_Back": handed_back,
                "Generator": generator,
                "Coroutine": coroutine,
                }))
        self.assertIsNone(_stepper_of(ordinary))          # no stepping, no extra work per call
        self.assertIsNone(_stepper_of(handed_back))       # what it hands back runs under whoever runs it
        self.assertIsNotNone(_stepper_of(generator))
        self.assertIsNotNone(_stepper_of(coroutine))


# ------------------------------------------------------------------
# An extension while a linking is under way (rule 4.6)
# ------------------------------------------------------------------


def Whole(test, agent):
    """Section 1.10's law, read from the kit's own books: every Pair of
    every Link of the Agent holds every Layer of the Links that hold her
    Contact, holds no Layer none of them has, carries no name such a Layer
    does not declare, has no linking left in flight; every door is shut."""

    members = [agent]

    for link, _layers in _state_of(agent).links.values():
        if link is None:
            continue

        family = _record_of(link).family
        known = set(_pair_tags_of([
                relation
                for member in family.Links()
                for relation in _record_of(member).layers
                ]))

        for contact in link.__dict__["_topkit_field"]:
            members.append(contact)
            pair = family.Pair_Of(contact)
            test.assertIsNotNone(pair, f"{contact} is a Contact without a Pair")

            for tag in _pair_form(link):
                test.assertIn(tag, _state_of(pair).active, f"the Pair of {contact} lacks {tag.__qualname__}")

        for pair in family.pairs.values():
            ends = _pair_ends(pair)
            contact = ends.contact()
            state = _state_of(pair)
            holding = [member for member in family.Links() if member in _state_of(contact).active]
            declared = set()

            for tag in _pair_tags_of([relation for member in holding for relation in _record_of(member).layers]):
                declared.update(name for name in tag.__dict__ if not name.startswith("_"))

            for tag in state.active:
                test.assertIn(tag, known, f"the Pair of {contact} holds {tag.__qualname__}, which its Links lack")

            leftovers = {name for name in vars(pair) if not name.startswith("_")} - declared
            test.assertEqual(leftovers, set(), f"the Pair of {contact} carries what no Layer of its Links declares")
            test.assertEqual(ends.flights, [], "a linking is left in flight")
            test.assertEqual(state.composing, 0, "a Pair's door is left open")

    for member in members:
        test.assertEqual(_state_of(member).composing, 0, f"{member}'s door is left open")


def Promoting_Circle(plan):
    """A Circle of Knows and Trusts Links, and the Popular Shape that
    extends Knows, for tests that gain the Shape in the middle of a
    linking. ``plan`` says where the Agent gains it (``promote_at``: the
    ``gate``, the ``record`` or the ``imprint`` of Knows, or the same of
    Trusts under ``trusts_``), for which Contact (``target``), and where
    a linking fails (``fail_at``, the ``record`` or the ``imprint``)."""

    def Promote(agent, contact, where):
        if plan.get("promote_at") == where and contact is plan.get("target") and agent not in Popular:
            plan.get("promote", Popular)(agent)

    def Fail(contact, where):
        if plan.get("fail_at") == where and contact is plan.get("target"):
            raise ValueError(f"refused at {where}")

    def Interrupt(contact, where):
        if plan.get("interrupt_at") == where and contact is plan.get("target"):
            raise KeyboardInterrupt(where)

    class Circle(Tag):
        @Link
        class Knows(Tag):
            @Pre
            def Gate(agent, contact):
                Promote(agent, contact, "gate")
                return True

            @Record
            def since(agent, contact, *, since=None):
                Promote(agent, contact, "record")
                return since

            @Record
            def later(agent, contact):
                Fail(contact, "record")
                Interrupt(contact, "after_promotion")
                return "later"

            @Imprint
            def Note(agent, contact):
                Promote(agent, contact, "imprint")
                Fail(contact, "imprint")
                Interrupt(contact, "imprint")

            @Rip
            def Forget(agent, contact):
                plan.setdefault("torn", []).append(contact.name)

            @Public
            def Greet(agent, contact):
                return "knows"

        @Link
        class Trusts(Knows):
            @Pre
            def Trust_Gate(agent, contact):
                Promote(agent, contact, "trusts_gate")
                return True

            @Record
            def level(agent, contact, stored=None, *, level=None):
                plan.setdefault("stored", []).append(stored)
                Promote(agent, contact, "trusts_record")
                return level

            @Record
            def trust_later(agent, contact):
                Fail(contact, "trusts_record")
                Interrupt(contact, "after_promotion")
                return "later"

            @Imprint
            def Trust_Note(agent, contact):
                Promote(agent, contact, "trusts_imprint")
                Fail(contact, "trusts_imprint")
                Interrupt(contact, "imprint")

            @Public
            def Hail(agent, contact):
                return "hail"

    class Popular(Circle):
        @Link
        class Knows(Circle.Knows):
            @Pre
            def Vip_Gate(agent, contact):
                plan.setdefault("gated", []).append(contact.name)
                Interrupt(contact, "popular_gate")
                return True

            @Record
            def vip(agent, contact):
                Interrupt(contact, "popular_record")
                builds = plan.setdefault("builds", {})
                builds[contact.name] = builds.get(contact.name, 0) + 1

                if contact is plan.get("target") and builds[contact.name] == plan.get("vip_fails_on"):
                    raise ValueError("this Record cannot be built a second time")

                if contact is plan.get("target") and builds[contact.name] == plan.get("vip_interrupted_on"):
                    raise KeyboardInterrupt("this Record is interrupted the second time it is built")

                return True

            @Imprint
            def Vip_Note(agent, contact):
                Interrupt(contact, "popular_imprint")

            @Action
            @Underlay
            def Greet(agent, contact, underlay):
                return underlay() + " and vips"

    return Circle, Popular


class Lining_Club(Tag):
    """A Link whose lines take the names Knows and Trusts publish: a Contact
    it holds meets the Overwrite Warning at her entry into either."""

    @Link
    class Member(Tag):
        @Public
        def Greet(agent, contact):
            return "member"

        @Public
        def Hail(agent, contact):
            return "member hail"


class Failing_Call(Tag):
    """A call on any Agent that links, then fails at a later Record: it rolls
    back, and the linking inside it is undone with it when the call is on
    the Link's Agent or on the Contact (rule 5.6)."""

    @Record
    def linking(agent, *, through=None, contact=None, inputs=None):
        through(contact, **(inputs or {}))
        return True

    @Record
    def broken(agent):
        raise ValueError("the call fails at a later Record")


class Ext_Nested_Tests(unittest.TestCase):
    """The Agent gains a Shape that extends one of his Links while a
    linking of that Link's family is under way (rule 4.6): it works as
    any tagging. The Layer reaches every Pair the Link holds, the Pair
    being linked included; it is the Agent's tagging, so it stays or goes
    with his call; a refused or undone linking undoes only its own work."""

    def Make(self, plan, held=False):
        Circle, Popular = Promoting_Circle(plan)
        charlie, ruth, sam, tom = People("Charlie", "Ruth", "Sam", "Tom")
        Circle(charlie)
        charlie.Knows(ruth, since=1)
        charlie.Knows(sam, since=2)

        if held:
            charlie.Knows(tom, since=3)                   # her Pair is held through the Base Link

        plan["target"] = tom

        return Circle, Popular, charlie, ruth, sam, tom

    def Assert_Extended(self, charlie, Popular, contacts):
        self.assertIn(charlie, Popular)

        for contact in contacts:
            self.assertTrue(charlie.Knows[contact].vip, contact.name)
            self.assertEqual(charlie.Knows[contact].Greet(), "knows and vips", contact.name)

        Whole(self, charlie)

    # --- where the extension comes from, the Pair being linked is new ---

    def test_an_extension_from_the_pairs_gate_reaches_the_pair_being_linked(self):
        plan = {"promote_at": "gate"}
        _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan)
        charlie.Knows(tom)
        self.Assert_Extended(charlie, Popular, [ruth, sam, tom])

    def test_an_extension_from_the_pairs_records_reaches_the_pair_being_linked(self):
        plan = {"promote_at": "record"}
        _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan)
        charlie.Knows(tom)
        self.Assert_Extended(charlie, Popular, [ruth, sam, tom])
        self.assertEqual(ruth.Greet(), "knows and vips")  # her line reads the Pair, whole

    def test_an_extension_from_the_pairs_imprint_reaches_the_pair_being_linked(self):
        plan = {"promote_at": "imprint"}
        _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan)
        charlie.Knows(tom)
        self.Assert_Extended(charlie, Popular, [ruth, sam, tom])

    def test_an_extension_from_the_contacts_own_entry_reaches_the_pair_being_linked(self):
        class Club(Tag):
            @Link
            class Member(Tag):
                @Public
                def Greet(agent, contact):
                    return "member"

        plan = {}
        Circle, Popular = Promoting_Circle(plan)
        charlie, ruth, tom = People("Charlie", "Ruth", "Tom")
        Circle(charlie)
        Club(charlie)
        charlie.Knows(ruth)
        charlie.Member(tom)                               # her line Greet is taken: Knows replaces it at her entry
        plan["target"] = tom

        def Gain_At_Entry(message, category, filename, lineno, file=None, line=None):
            if charlie not in Popular:
                Popular(charlie)                          # while she enters, with her Pair whole and not yet a member

        with warnings.catch_warnings():
            warnings.simplefilter("always")
            previous, warnings.showwarning = warnings.showwarning, Gain_At_Entry

            try:
                charlie.Knows(tom)
            finally:
                warnings.showwarning = previous

        self.Assert_Extended(charlie, Popular, [ruth, tom])
        self.assertIn(tom, charlie.Knows)

    # --- ... or already held through a Base Link of the same family ---

    def test_an_extension_reaches_a_shared_pair_from_the_shape_links_gate(self):
        for where in ("trusts_gate", "trusts_record", "trusts_imprint"):
            with self.subTest(where=where):
                plan = {"promote_at": where}
                _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan, held=True)
                charlie.Trusts(tom, level=7)
                self.Assert_Extended(charlie, Popular, [ruth, sam, tom])
                self.assertEqual(charlie.Trusts[tom].level, 7)
                self.assertEqual(plan["stored"], [None])  # her Trusts Record saw nothing stored

    def test_an_extension_from_a_new_shape_links_pair_reaches_it_whole(self):
        plan = {"promote_at": "trusts_record"}
        _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan)
        charlie.Trusts(tom, level=3)                      # linked through the Shape: both Layers at once
        self.Assert_Extended(charlie, Popular, [ruth, sam, tom])
        self.assertEqual(charlie.Trusts[tom].level, 3)
        self.assertIn(tom, charlie.Knows)

    def test_the_extension_lies_over_the_layers_it_extends_on_every_pair(self):
        plan = {"promote_at": "gate"}
        _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan)
        charlie.Knows(tom)
        for contact in (ruth, sam, tom):                  # the Underlay finds the Layer it extends below it
            self.assertEqual(charlie.Knows[contact].Greet(), "knows and vips")

    def test_linkings_after_the_extension_get_every_layer(self):
        plan = {"promote_at": "record"}
        _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan)
        charlie.Knows(tom)
        late = Character("Late")
        charlie.Knows(late)
        self.Assert_Extended(charlie, Popular, [ruth, sam, tom, late])

    # --- the linking is refused, or fails, after the extension ---

    def test_a_refused_linking_keeps_the_extension_and_drops_a_new_pair(self):
        plan = {"promote_at": "record", "fail_at": "record"}
        _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan)

        with self.assertRaises(TagCompositionError):
            charlie.Knows(tom)

        self.assertNotIn(tom, charlie.Knows)              # the linking is refused
        with self.assertRaises(TagResolutionError):
            charlie.Knows[tom]                            # and her Pair never was
        self.assertIn(charlie, Popular)                   # his own tagging finished: it stays
        self.Assert_Extended(charlie, Popular, [ruth, sam])   # with its Layer on every Pair
        plan["fail_at"] = None
        charlie.Knows(tom)
        self.Assert_Extended(charlie, Popular, [ruth, sam, tom])

    def test_a_refused_linking_keeps_the_extension_on_the_held_pair(self):
        for where in ("trusts_gate", "trusts_record"):
            with self.subTest(where=where):
                plan = {"promote_at": where, "fail_at": "trusts_record"}
                _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan, held=True)

                with self.assertRaises(TagCompositionError):
                    charlie.Trusts(tom, level=9)

                self.assertNotIn(tom, charlie.Trusts)
                self.assertIn(tom, charlie.Knows)         # she was a Contact before
                self.assertFalse(hasattr(charlie.Knows[tom], "level"))   # the refused Layer left nothing on her Pair
                self.Assert_Extended(charlie, Popular, [ruth, sam, tom])   # and his Layer is there, laid again

                plan["fail_at"] = None
                plan["stored"] = []
                charlie.Trusts(tom, level=4)
                self.assertEqual(plan["stored"], [None])  # no value of the refused Layer reached the next linking
                self.assertEqual(charlie.Trusts[tom].level, 4)
                self.Assert_Extended(charlie, Popular, [ruth, sam, tom])

    def test_a_linking_refused_at_the_contacts_entry_keeps_the_extension(self):
        for held in (False, True):
            with self.subTest(held=held):
                plan = {"promote_at": "trusts_record" if held else "record"}
                Circle, Popular = Promoting_Circle(plan)
                charlie, ruth, tom = People("Charlie", "Ruth", "Tom")
                Circle(charlie)
                Lining_Club(charlie)
                charlie.Knows(ruth)

                if held:
                    charlie.Knows(tom)                    # her Pair is held through the Base Link

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    charlie.Member(tom)                   # her lines Greet and Hail are now Member's

                plan["target"] = tom

                with warnings.catch_warnings():
                    warnings.simplefilter("error", TagOverwriteWarning)

                    with self.assertRaises(TagOverwriteWarning):
                        (charlie.Trusts if held else charlie.Knows)(tom)

                self.assertIn(charlie, Popular)
                self.assertNotIn(tom, charlie.Trusts if held else charlie.Knows)
                self.Assert_Extended(charlie, Popular, [ruth, tom] if held else [ruth])

    def test_a_linking_whose_imprint_fails_stays_with_the_extension(self):
        plan = {"promote_at": "record", "fail_at": "imprint"}
        _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan)

        with self.assertRaises(TagImprintError):
            charlie.Knows(tom)

        self.assertIn(tom, charlie.Knows)                 # after her entry the failure raises and the linking stays
        self.Assert_Extended(charlie, Popular, [ruth, sam, tom])

    # --- the call around everything rolls back, or does not ---

    def test_a_rolled_back_call_on_the_agent_takes_the_extension_and_the_linking_back(self):
        for held in (False, True):
            with self.subTest(held=held):
                plan = {"promote_at": "trusts_record" if held else "record"}
                _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan, held=held)
                through = charlie.Trusts if held else charlie.Knows

                with self.assertRaises(TagCompositionError):
                    Failing_Call(charlie, through=through, contact=tom, inputs={})

                self.assertNotIn(charlie, Popular)
                self.assertNotIn(tom, charlie.Trusts)
                self.assertEqual(tom in charlie.Knows, held)
                for contact in ([ruth, sam, tom] if held else [ruth, sam]):
                    self.assertFalse(hasattr(charlie.Knows[contact], "vip"))
                    self.assertEqual(charlie.Knows[contact].Greet(), "knows")
                Whole(self, charlie)
                self.assertEqual(plan.get("torn", []), [])   # a Pair that never was ends with no teardown

                plan["promote_at"] = None                 # and the Link can be extended again, then linked
                Popular(charlie)
                if not held:
                    charlie.Knows(tom)
                self.Assert_Extended(charlie, Popular, [ruth, sam, tom])

    def test_a_rolled_back_call_on_the_contact_undoes_the_linking_and_keeps_the_extension(self):
        for held in (False, True):
            with self.subTest(held=held):
                plan = {"promote_at": "trusts_record" if held else "record"}
                _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan, held=held)
                through = charlie.Trusts if held else charlie.Knows

                with self.assertRaises(TagCompositionError):
                    Failing_Call(tom, through=through, contact=tom, inputs={"level": 5} if held else {})

                self.assertIn(charlie, Popular)           # his tagging finished, and is not hers to undo
                self.assertNotIn(tom, charlie.Trusts)
                self.assertEqual(tom in charlie.Knows, held)
                self.Assert_Extended(charlie, Popular, [ruth, sam, tom] if held else [ruth, sam])
                if held:
                    self.assertFalse(hasattr(charlie.Knows[tom], "level"))   # no Record of the undone Layer stays
                    plan["stored"] = []
                    charlie.Trusts(tom, level=8)
                    self.assertEqual(plan["stored"], [None])
                    self.assertEqual(charlie.Trusts[tom].level, 8)

    def test_a_rolled_back_call_on_a_third_agent_undoes_nothing(self):
        plan = {"promote_at": "record"}
        _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan)

        with self.assertRaises(TagCompositionError):
            Failing_Call(sam, through=charlie.Knows, contact=tom, inputs={})

        self.assertIn(tom, charlie.Knows)                 # her call is not his, nor hers
        self.Assert_Extended(charlie, Popular, [ruth, sam, tom])

    # --- two extensions in a row ---

    def test_two_extensions_in_one_linking_reach_every_pair(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    if since == "promote":
                        Popular(agent)
                        Vetting(agent)                    # a second Shape, in the same Record
                    return since

        class Popular(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def vip(agent, contact):
                    return True

        class Vetting(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def vetted(agent, contact):
                    return "vetted"

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Circle(charlie)
        charlie.Knows(ruth)
        charlie.Knows(sam, since="promote")
        for contact in (ruth, sam):
            self.assertTrue(charlie.Knows[contact].vip)
            self.assertEqual(charlie.Knows[contact].vetted, "vetted")
        Whole(self, charlie)

    def test_an_extension_whose_record_gains_another_reaches_every_pair(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    return since

        class First(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def first(agent, contact):
                    if agent not in Second:
                        Second(agent)                     # gained by the extension's own Record, on its first Pair
                    return "first"

        class Second(First):
            @Link
            class Knows(First.Knows):
                @Record
                def second(agent, contact):
                    return "second"

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Circle(charlie)
        charlie.Knows(ruth)
        charlie.Knows(sam)
        First(charlie)
        self.assertIn(charlie, Second)
        for contact in (ruth, sam):
            self.assertEqual(charlie.Knows[contact].first, "first")
            self.assertEqual(charlie.Knows[contact].second, "second")
        Whole(self, charlie)

    def test_an_extension_chain_started_in_a_pairs_record_reaches_every_pair(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    if since == "promote" and agent not in First:
                        First(agent)
                    return since

        class First(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def first(agent, contact, *, since=None):
                    if since == "promote" and agent not in Second:
                        Second(agent)                     # given to the Pair being linked with its linking's inputs
                    return "first"

        class Second(First):
            @Link
            class Knows(First.Knows):
                @Record
                def second(agent, contact):
                    return "second"

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Circle(charlie)
        charlie.Knows(ruth)
        charlie.Knows(sam, since="promote")
        self.assertIn(charlie, First)
        self.assertIn(charlie, Second)
        for contact in (ruth, sam):
            self.assertEqual(charlie.Knows[contact].first, "first")
            self.assertEqual(charlie.Knows[contact].second, "second")
        Whole(self, charlie)

    def test_two_extensions_then_a_refused_linking_keep_both(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                pass

            @Link
            class Trusts(Knows):
                @Record
                def level(agent, contact, *, level=None):
                    if level == "promote":
                        Popular(agent)
                        Vetting(agent)
                    return level

                @Record
                def later(agent, contact, *, level=None):
                    if level == "promote":
                        raise ValueError("the linking is refused")
                    return 1

        class Popular(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def vip(agent, contact):
                    return True

        class Vetting(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def vetted(agent, contact):
                    return "vetted"

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Circle(charlie)
        charlie.Knows(ruth)
        charlie.Knows(sam)                                # held through the Base Link
        with self.assertRaises(TagCompositionError):
            charlie.Trusts(sam, level="promote")
        self.assertIn(charlie, Popular)
        self.assertIn(charlie, Vetting)
        self.assertNotIn(sam, charlie.Trusts)
        for contact in (ruth, sam):
            self.assertTrue(charlie.Knows[contact].vip)
            self.assertEqual(charlie.Knows[contact].vetted, "vetted")
        self.assertFalse(hasattr(charlie.Knows[sam], "level"))
        Whole(self, charlie)

    # --- an extension that is refused in the middle of a linking ---

    def Strict_Circle(self, catching):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    if since == "promote":
                        try:
                            Strict(agent)
                        except TagError:
                            if not catching:
                                raise
                    return since

            @Link
            class Trusts(Knows):
                @Record
                def level(agent, contact, *, level=None):
                    if level == "promote":
                        try:
                            Strict(agent)
                        except TagError:
                            if not catching:
                                raise
                    return level

        class Strict(Circle):
            @Link
            class Knows(Circle.Knows):
                @Pre
                def Only_Honest(agent, contact):
                    return contact.honest

                @Record
                def vetted(agent, contact):
                    return True

        return Circle, Strict

    def test_a_refusal_by_a_held_pair_is_the_extensions_and_a_catching_record_goes_on(self):
        Circle, Strict = self.Strict_Circle(catching=True)
        charlie, ruth, liar = People("Charlie", "Ruth", "Liar")
        liar.honest = False
        Circle(charlie)
        charlie.Knows(ruth)
        charlie.Knows(liar)
        charlie.Trusts(ruth, level="promote")             # Strict refuses the liar's Pair: his call is refused, nothing changed
        self.assertNotIn(charlie, Strict)
        self.assertIn(ruth, charlie.Trusts)               # her Record caught it, and the linking went on
        self.assertFalse(hasattr(charlie.Knows[ruth], "vetted"))
        self.assertFalse(hasattr(charlie.Knows[liar], "vetted"))
        Whole(self, charlie)

    def test_a_refusal_by_a_held_pair_refuses_the_linking_when_nothing_catches_it(self):
        Circle, Strict = self.Strict_Circle(catching=False)
        charlie, ruth, liar = People("Charlie", "Ruth", "Liar")
        liar.honest = False
        Circle(charlie)
        charlie.Knows(ruth)
        charlie.Knows(liar)
        with self.assertRaises(TagPreconditionError):
            charlie.Trusts(ruth, level="promote")
        self.assertNotIn(charlie, Strict)
        self.assertNotIn(ruth, charlie.Trusts)
        self.assertFalse(hasattr(charlie.Knows[ruth], "level"))
        Whole(self, charlie)

    def test_the_pair_being_linked_is_refused_by_the_layer_not_the_extension(self):
        Circle, Strict = self.Strict_Circle(catching=False)
        charlie, ruth, liar = People("Charlie", "Ruth", "Liar")
        liar.honest = False
        Circle(charlie)
        charlie.Knows(ruth)
        with self.assertRaises(TagPreconditionError):
            charlie.Knows(liar, since="promote")          # she is not a Contact yet: Strict's gate refuses her linking
        self.assertIn(charlie, Strict)                    # the Agent's tagging stands: every Contact he has holds it
        self.assertTrue(charlie.Knows[ruth].vetted)
        self.assertNotIn(liar, charlie.Knows)
        with self.assertRaises(TagPreconditionError):
            charlie.Knows(liar)                           # and the Link's gate holds for her from now on
        Whole(self, charlie)

    def test_a_promise_of_the_extension_is_checked_for_the_pair_in_flight_with_its_linking(self):
        for held in (False, True):
            with self.subTest(held=held):
                class Circle(Tag):
                    @Link
                    class Knows(Tag):
                        @Record
                        def since(agent, contact, *, since=None):
                            if since == "promote" and not held and agent not in Popular:
                                Popular(agent)
                            return since

                    @Link
                    class Trusts(Knows):
                        @Record
                        def level(agent, contact, *, level=None):
                            if level == "promote" and agent not in Popular:
                                Popular(agent)
                            return level

                class Popular(Circle):
                    @Link
                    class Knows(Circle.Knows):
                        @Post
                        def Still_Honest(agent, contact):
                            return contact.honest

                charlie, ruth, tom = People("Charlie", "Ruth", "Tom")
                tom.honest = False
                Circle(charlie)
                charlie.Knows(ruth)

                if held:
                    charlie.Knows(tom)

                with self.assertRaises(TagPostconditionError):
                    if held:
                        charlie.Trusts(tom, level="promote")
                    else:
                        charlie.Knows(tom, since="promote")

                self.assertIn(charlie, Popular)           # after her entry the failure raises, and the Layers stay
                self.assertIn(tom, charlie.Knows)
                self.assertEqual(list(~charlie.Knows), [tom])   # her Pair holds the promise and breaks it
                self.assertEqual(list(charlie.Knows), [ruth])
                Whole(self, charlie)

    def test_a_call_that_extends_then_links_and_fails_leaves_the_pair_as_it_was(self):
        plan = {"promote_at": None}
        Circle, Popular = Promoting_Circle(plan)

        class Promoting_Call(Tag):                        # a call on the Agent: his extension first, then a linking, then it fails
            @Record
            def promote(agent):
                Popular(agent)
                return True

            @Record
            def link(agent, *, contact=None):
                agent.Trusts(contact, level=3)
                return True

            @Record
            def broken(agent):
                raise ValueError("the call fails")

        charlie, ruth, tom = People("Charlie", "Ruth", "Tom")
        Circle(charlie)
        charlie.Knows(ruth)
        charlie.Knows(tom)

        with self.assertRaises(TagCompositionError):
            Promoting_Call(charlie, contact=tom)

        self.assertNotIn(charlie, Popular)
        self.assertNotIn(tom, charlie.Trusts)
        for contact in (ruth, tom):
            self.assertFalse(hasattr(charlie.Knows[contact], "vip"))   # neither the Layer nor the linking's stays
        self.assertFalse(hasattr(charlie.Knows[tom], "level"))
        Whole(self, charlie)

    def test_a_silent_undo_of_a_linking_never_takes_the_extension_with_it(self):
        plan = {"promote_at": "trusts_record"}
        Circle, Popular = Promoting_Circle(plan)
        charlie, ruth, tom = People("Charlie", "Ruth", "Tom")
        Circle(charlie)
        Lining_Club(charlie)
        charlie.Knows(ruth)
        charlie.Knows(tom)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            charlie.Member(tom)                           # her line Hail is Member's: Trusts' replaces it at her entry

        plan["target"] = tom

        def Write_Then_Refuse(message, category, filename, lineno, file=None, line=None):
            charlie.Knows[tom].since = "written at her entry"   # someone writes on the Pair, then her entry is refused
            raise ValueError("her entry is refused")

        with warnings.catch_warnings():
            warnings.simplefilter("always")
            previous, warnings.showwarning = warnings.showwarning, Write_Then_Refuse

            try:
                with self.assertRaises(ValueError):
                    charlie.Trusts(tom, level=2)
            finally:
                warnings.showwarning = previous

        self.assertNotIn(tom, charlie.Trusts)
        self.assertEqual(charlie.Knows[tom].since, "written at her entry")   # what was written stays
        self.assertIn(charlie, Popular)
        self.assertTrue(charlie.Knows[tom].vip)           # and the Agent's Layer, which is not the linking's to take
        self.assertIn(_pair_tag(Popular.Knows), _state_of(charlie.Knows[tom]).active)
        self.assertNotIn(_pair_tag(Circle.Trusts), _state_of(charlie.Knows[tom]).active)   # the linking's Layer left, sticky

    def test_an_extension_undone_after_its_contact_was_unlinked_leaves_the_ended_pair_alone(self):
        plan = {"promote_at": None}
        Circle, Popular = Promoting_Circle(plan)

        class Promoting_Call(Tag):                        # his extension, then an unlinking that nothing rolls back, then a failure
            @Record
            def promote(agent):
                Popular(agent)
                return True

            @Record
            def unlink(agent, *, contact=None):
                del agent.Knows[contact]
                return True

            @Record
            def broken(agent):
                raise ValueError("the call fails")

        charlie, ruth, tom = People("Charlie", "Ruth", "Tom")
        Circle(charlie)
        charlie.Knows(ruth)
        charlie.Knows(tom)

        with self.assertRaises(TagCompositionError) as refusal:
            Promoting_Call(charlie, contact=tom)

        self.assertIn("the call fails", str(refusal.exception))   # the undoing added no failure of its own
        self.assertNotIn(charlie, Popular)
        self.assertNotIn(tom, charlie.Knows)              # an unlinking is never rolled back (§0.7)
        self.assertFalse(hasattr(charlie.Knows[ruth], "vip"))
        Whole(self, charlie)

    def test_the_extension_does_not_check_the_promises_of_a_pair_still_being_made(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                pass

            @Link
            class Trusts(Knows):
                @Post
                def Has_Level(agent, contact):
                    return agent.Knows[contact].level is not None   # true once her Records are built

                @Record
                def level(agent, contact, *, level=None):
                    if agent not in Popular:
                        Popular(agent)                    # while this very Record builds, her promise cannot hold yet
                    return level

        class Popular(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def vip(agent, contact):
                    return True

        charlie, tom = People("Charlie", "Tom")
        Circle(charlie)
        charlie.Knows(tom)
        charlie.Trusts(tom, level=4)                      # her promise is checked with her linking, when it is whole
        self.assertTrue(charlie.Knows[tom].vip)
        self.assertIn(tom, charlie.Trusts)
        Whole(self, charlie)

    def test_an_interrupt_while_the_repair_lays_a_layer_again_is_raised_and_the_pair_stays_whole(self):
        plan = {"promote_at": "trusts_record", "vip_interrupted_on": 2}
        _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan, held=True)
        plan["builds"] = {}

        class Joining(Tag):                               # a call on the Contact: her linking is undone, his extension stays
            @Record
            def trusted(agent, *, by=None):
                by.Trusts(agent, level=5)
                return True

            @Record
            def broken(agent):
                raise ValueError("her call fails")

        with self.assertRaises(KeyboardInterrupt):
            Joining(tom, by=charlie)                      # the undoing is interrupted, and the interrupt is what is raised

        self.assertTrue(charlie.Knows[tom].vip)           # her Pair still holds his Layer
        self.assertIn(charlie, Popular)
        for member in (charlie, ruth, sam, tom):
            self.assertEqual(_state_of(member).composing, 0)
        for contact in (ruth, sam, tom):
            self.assertEqual(_pair_ends(charlie.Knows[contact]).flights, [])

    def test_an_input_that_would_fill_a_seat_of_the_new_layer_refuses_the_linking_not_the_agent(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    if since == "promote" and agent not in Popular:
                        Popular(agent)
                    return since

        class Popular(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def vip(agent, tier):                     # its seat for the Contact is named like an input
                    return True

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Circle(charlie)
        charlie.Knows(ruth)

        with self.assertRaises(TagDeclarationError):
            charlie.Knows(sam, since="promote", tier=1)   # an input never fills a seat (rule 3.4): as for any linking after the Shape

        self.assertNotIn(sam, charlie.Knows)
        self.assertIn(charlie, Popular)                   # his tagging stands
        self.assertTrue(charlie.Knows[ruth].vip)
        with self.assertRaises(TagResolutionError):
            charlie.Knows[sam]                            # and her Pair never was
        Whole(self, charlie)

    def test_an_extension_of_the_first_link_at_the_entry_into_the_second_reaches_her_once(self):
        plan = {}
        Circle, Popular = Promoting_Circle(plan)
        charlie, ruth, tom = People("Charlie", "Ruth", "Tom")
        Circle(charlie)
        Lining_Club(charlie)
        charlie.Knows(ruth)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            charlie.Member(tom)                           # her line Hail is Member's: Trusts' replaces it at her entry

        def Gain_At_Entry(message, category, filename, lineno, file=None, line=None):
            if "Hail" in str(message) and charlie not in Popular:
                Popular(charlie)                          # she is a member of Knows already, and enters Trusts

        with warnings.catch_warnings():
            warnings.simplefilter("always")
            previous, warnings.showwarning = warnings.showwarning, Gain_At_Entry

            try:
                charlie.Trusts(tom, level=1)
            finally:
                warnings.showwarning = previous

        self.assertIn(tom, charlie.Trusts)
        self.Assert_Extended(charlie, Popular, [ruth, tom])
        self.assertEqual(charlie.Trusts[tom].level, 1)
        self.assertEqual(sorted(plan["gated"]), ["Ruth", "Tom"])   # the Layer's gate asked once for each Pair

    def test_a_layer_given_late_to_a_pair_held_through_another_link_leaves_with_a_refusal(self):
        class Two(Tag):
            @Link
            class Knows(Tag):
                @Record
                def known(agent, contact, *, promote=False):
                    if promote and agent not in Popular:
                        Popular(agent)
                    return "known"

            @Link
            class Likes(Tag):
                @Record
                def liked(agent, contact):
                    return "liked"

            @Link
            class Bonded(Knows, Likes):
                @Public
                def Hail(agent, contact):
                    return "bonded hail"

        class Popular(Two):
            @Link
            class Knows(Two.Knows):
                @Record
                def vip(agent, contact):
                    return True

        charlie, ruth = People("Charlie", "Ruth")
        Two(charlie)
        Lining_Club(charlie)
        charlie.Likes(ruth)                               # her Pair is held through Likes

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            charlie.Member(ruth)                          # her line Hail is Member's: Bonded's replaces it at her entry

        with warnings.catch_warnings():
            warnings.simplefilter("error", TagOverwriteWarning)

            with self.assertRaises(TagOverwriteWarning):
                charlie.Bonded(ruth, promote=True)        # Knows' Layer is given late, then her entry is refused

        self.assertIn(charlie, Popular)                   # the Agent's tagging stands, and she is not in Knows
        self.assertNotIn(ruth, charlie.Knows)
        self.assertFalse(hasattr(charlie.Likes[ruth], "vip"))   # her Pair holds what it did, and none of the refused Layers
        self.assertFalse(hasattr(charlie.Likes[ruth], "known"))
        Whole(self, charlie)

    def test_an_undo_after_an_imprint_wrote_on_the_pair_still_goes_back_exactly(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    return since

        class Popular(Circle):
            @Link
            class Knows(Circle.Knows):
                @Imprint
                def Stamp(agent, contact):
                    agent.Knows[contact].since = "stamped by the extension"   # the Agent's Layer writes, and that is its own

        class Promoting_Call(Tag):
            @Record
            def promote(agent):
                Popular(agent)
                return True

            @Record
            def broken(agent):
                raise ValueError("the call fails")

        charlie, ruth = People("Charlie", "Ruth")
        Circle(charlie)
        charlie.Knows(ruth, since=1)

        with self.assertRaises(TagCompositionError):
            Promoting_Call(charlie)

        self.assertEqual(charlie.Knows[ruth].since, 1)    # back to what it was, not left as the Imprint wrote it
        Whole(self, charlie)

    def test_the_layers_two_links_gained_are_laid_again_in_the_order_they_were_gained(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                def Greet(agent, contact):
                    return "k"

            @Link
            class Trusts(Knows):
                pass

            @Link
            class Likes(Knows):
                @Record
                def liked(agent, contact, *, promote=False):
                    if promote:
                        Shaping_Trusts(agent)             # Trusts' extension first, then Knows'
                        Shaping_Knows(agent)
                        raise ValueError("the linking is refused")

                    return "liked"

        class Shaping_Trusts(Circle):
            @Link
            class Trusts(Circle.Trusts):
                @Action
                @Underlay
                def Greet(agent, contact, underlay):
                    return underlay() + "S"

        class Shaping_Knows(Circle):
            @Link
            class Knows(Circle.Knows):
                @Action
                @Underlay
                def Greet(agent, contact, underlay):
                    return underlay() + "K"

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Circle(charlie)
        charlie.Trusts(ruth)                              # her Pair is held through Trusts and Knows

        with self.assertRaises(TagCompositionError):
            charlie.Likes(ruth, promote=True)             # both Layers are laid on her Pair, then the linking is refused

        self.assertEqual(charlie.Knows[ruth].Greet(), "kSK")
        charlie.Trusts(sam)
        self.assertEqual(charlie.Knows[sam].Greet(), "kSK")   # as a Pair linked after them
        Whole(self, charlie)

    # --- an interrupt at each step ---

    def test_an_interrupt_at_any_step_leaves_every_pair_whole(self):
        for held in (False, True):
            for where in ("popular_gate", "popular_record", "popular_imprint", "after_promotion", "imprint"):
                with self.subTest(held=held, where=where):
                    plan = {"promote_at": "trusts_record" if held else "record", "interrupt_at": where}
                    _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan, held=held)
                    through = charlie.Trusts if held else charlie.Knows

                    with self.assertRaises(KeyboardInterrupt):
                        through(tom)

                    record = _record_of(charlie.Knows)
                    self.assertEqual(charlie in Popular, Popular.Knows in record.layers)   # the Agent and his Link agree
                    Whole(self, charlie)

                    plan["interrupt_at"] = None           # and the Link links on, with whatever Layers it holds
                    through(tom)
                    Whole(self, charlie)

    def test_an_interrupt_is_not_swallowed_by_the_undoing(self):
        plan = {"promote_at": "record", "interrupt_at": "after_promotion"}
        _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan)

        with self.assertRaises(KeyboardInterrupt):
            Failing_Call(charlie, through=charlie.Knows, contact=tom, inputs={})   # interrupted inside the call

        self.assertNotIn(charlie, Popular)
        self.assertNotIn(tom, charlie.Knows)
        Whole(self, charlie)

    # --- a nested call of the Agent that gains the Shape and fails ---

    def test_a_nested_call_that_gains_the_shape_and_fails_leaves_the_linking_whole(self):
        for held in (False, True):
            with self.subTest(held=held):
                plan = {"promote_at": "trusts_record" if held else "record"}
                _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan, held=held)

                class Gaining(Tag):                       # the Agent's own call, inside the linking: it gains the Shape, then fails
                    @Record
                    def gain(agent):
                        Popular(agent)
                        return True

                    @Record
                    def broken(agent):
                        raise ValueError("the nested call fails")

                def Try(agent):
                    try:
                        Gaining(agent)
                    except TagCompositionError:
                        plan["caught"] = True

                plan["promote"] = Try
                (charlie.Trusts if held else charlie.Knows)(tom)
                self.assertTrue(plan["caught"])
                self.assertNotIn(charlie, Popular)
                self.assertNotIn(Popular.Knows, _record_of(charlie.Knows).layers)
                for contact in (ruth, sam, tom):
                    self.assertFalse(hasattr(charlie.Knows[contact], "vip"))
                Whole(self, charlie)

    # --- what stays sticky: a value someone else wrote on the Pair ---

    def test_a_value_written_since_stays_with_the_extension_and_the_undone_layers_contributions(self):
        plan = {"promote_at": None}
        Circle, Popular = Promoting_Circle(plan)

        class Annotating(Tag):                            # the Agent's own call: it finishes, and writes on the Pair
            @Record
            def note(agent, *, about=None):
                agent.Knows[about].since = "annotated by Charlie"
                return True

        class Joining(Tag):                               # a call on the Contact
            @Record
            def trusted(agent, *, by=None):
                by.Trusts(agent, level=5)
                return True

            @Record
            def promoted(agent, *, by=None):
                Popular(by)
                return True

            @Record
            def annotated(agent, *, by=None):
                Annotating(by, about=agent)
                return True

            @Record
            def broken(agent):
                raise ValueError("her call fails")

        charlie, ruth, tom = People("Charlie", "Ruth", "Tom")
        Circle(charlie)
        charlie.Knows(ruth, since=1)
        charlie.Knows(tom, since=2)

        with self.assertRaises(TagCompositionError):
            Joining(tom, by=charlie)

        self.assertNotIn(tom, charlie.Trusts)
        self.assertEqual(charlie.Knows[tom].since, "annotated by Charlie")   # what he wrote stays
        self.assertTrue(charlie.Knows[tom].vip)           # and his Layer
        self.assertEqual(charlie.Knows[tom].level, 5)     # the undone Layer leaves as an unlinking leaves it: sticky (§0.7)
        self.assertTrue(charlie.Knows[ruth].vip)

    def test_an_undone_linking_leaves_the_pair_as_the_extension_found_it(self):
        plan = {"promote_at": None}
        Circle, Popular = Promoting_Circle(plan)

        class Joining(Tag):                               # a call on the Contact
            @Record
            def trusted(agent, *, by=None):
                by.Trusts(agent, level=5)
                return True

            @Record
            def promoted(agent, *, by=None):
                Popular(by)                               # his call reaches her Pair since, and nobody writes on it
                return True

            @Record
            def broken(agent):
                raise ValueError("her call fails")

        charlie, ruth, tom = People("Charlie", "Ruth", "Tom")
        Circle(charlie)
        charlie.Knows(tom, since=2)
        plan["stored"] = []

        with self.assertRaises(TagCompositionError):
            Joining(tom, by=charlie)

        self.assertTrue(charlie.Knows[tom].vip)
        self.assertFalse(hasattr(charlie.Knows[tom], "level"))   # no Record of the undone Layer stays
        Whole(self, charlie)
        charlie.Trusts(tom, level=6)
        self.assertEqual(plan["stored"], [None, None])    # and none reaches the next linking
        self.assertEqual(charlie.Trusts[tom].level, 6)

    def test_an_undone_extension_after_an_undone_linking_leaves_the_pair_as_it_was(self):
        plan = {"promote_at": None}
        Circle, Popular = Promoting_Circle(plan)

        class Elsewhere(Tag):
            @Link
            class Other(Tag):
                @Record
                def trusted(agent, contact, *, tom=None):
                    agent.Trusts(tom, level=5)            # undone with the refusal
                    return True

                @Record
                def promoted(agent, contact, *, tom=None):
                    Popular(agent)                        # his finished call, handed outward
                    return True

                @Record
                def broken(agent, contact, *, tom=None):
                    raise ValueError("the Other linking is refused")

        class Outer(Tag):
            @Record
            def first(agent, *, sam=None, tom=None):
                agent.Other(sam, tom=tom)                 # the refusal rolls Outer back too
                return True

        charlie, tom, sam = People("Charlie", "Tom", "Sam")
        Circle(charlie)
        Elsewhere(charlie)
        charlie.Knows(tom, since=2)

        with self.assertRaises(TagCompositionError):
            Outer(charlie, sam=sam, tom=tom)

        self.assertNotIn(charlie, Popular)
        self.assertFalse(hasattr(charlie.Knows[tom], "vip"))      # nothing of either stays on her Pair
        self.assertFalse(hasattr(charlie.Knows[tom], "level"))
        Whole(self, charlie)

    # --- a Record that cannot be built a second time: the repair's own failure ---

    def test_a_pair_that_cannot_be_laid_again_stays_as_the_linking_left_it(self):
        plan = {"promote_at": "trusts_record", "vip_fails_on": 2}
        _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan, held=True)
        plan["builds"] = {}

        class Joining(Tag):                               # a call on the Contact: her linking is undone, his extension stays
            @Record
            def trusted(agent, *, by=None):
                by.Trusts(agent, level=5)
                return True

            @Record
            def broken(agent):
                raise ValueError("her call fails")

        with self.assertRaises(TagCompositionError) as refusal:
            Joining(tom, by=charlie)

        self.assertIn("her call fails", str(refusal.exception))   # the undoing swallowed nothing and replaced nothing
        self.assertNotIn(tom, charlie.Trusts)
        self.assertTrue(charlie.Knows[tom].vip)           # its Layer was not taken off: the Record is not built again
        self.assertIn(charlie, Popular)

    def test_a_pair_the_repair_cannot_lay_again_raises_what_failed(self):
        plan = {"promote_at": "trusts_record", "fail_at": "trusts_record", "vip_fails_on": 2}
        _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan, held=True)
        plan["builds"] = {}

        with self.assertRaises(TagCompositionError) as failure:
            charlie.Trusts(tom, level=3)                  # refused at Parts: her Pair goes back, his Layer is laid again

        self.assertIn("cannot be built a second time", str(failure.exception))   # the Pair lacks it now, and says so
        self.assertIsInstance(failure.exception.__context__, ValueError)
        self.assertIn(charlie, Popular)                   # his tagging stands
        self.assertNotIn(tom, charlie.Trusts)
        for contact in (ruth, sam):
            self.assertTrue(charlie.Knows[contact].vip)

    # --- families joined while a linking is under way ---

    def test_a_family_joined_while_a_linking_is_under_way_is_not_refused(self):
        class Two(Tag):
            @Link
            class Knows(Tag):
                @Record
                def known(agent, contact, *, joining=False):
                    if joining and agent not in Close:
                        Close(agent)                      # the Agent gains a Shape that joins Knows and Likes
                    return "known"

            @Link
            class Likes(Tag):
                @Record
                def liked(agent, contact):
                    return "liked"

        class Close(Two):
            @Link
            class Bonded(Two.Knows, Two.Likes):
                pass

        charlie, ruth, sam, dave = People("Charlie", "Ruth", "Sam", "Dave")
        Two(charlie)
        charlie.Likes(sam)
        charlie.Knows(ruth, joining=True)
        self.assertIn(charlie, Close)
        self.assertIn(ruth, charlie.Knows)
        charlie.Bonded(dave)
        self.assertIs(charlie.Likes[dave], charlie.Knows[dave])   # one family, one Pair
        Whole(self, charlie)

    def test_a_family_joined_during_a_linking_is_split_again_with_the_call_that_rolls_back(self):
        class Two(Tag):
            @Link
            class Knows(Tag):
                @Record
                def known(agent, contact, *, joining=False):
                    if joining and agent not in Close:
                        Close(agent)
                    return "known"

            @Link
            class Likes(Tag):
                @Record
                def liked(agent, contact):
                    return "liked"

        class Close(Two):
            @Link
            class Bonded(Two.Knows, Two.Likes):
                pass

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Two(charlie)
        charlie.Likes(sam)

        with self.assertRaises(TagCompositionError):
            Failing_Call(charlie, through=charlie.Knows, contact=ruth, inputs={"joining": True})

        self.assertNotIn(charlie, Close)
        self.assertNotIn(ruth, charlie.Knows)
        charlie.Likes(ruth)
        charlie.Knows(ruth)
        self.assertIsNot(charlie.Likes[ruth], charlie.Knows[ruth])   # Knows and Likes are apart again
        Whole(self, charlie)

    # --- the Agent links himself; nothing keeps the Agents alive ---

    def test_an_agent_that_links_himself_can_gain_the_shape_in_the_pairs_record(self):
        plan = {"promote_at": "record"}
        Circle, Popular = Promoting_Circle(plan)
        charlie, = People("Charlie")
        Circle(charlie)
        plan["target"] = charlie
        charlie.Knows(charlie)
        self.assertTrue(charlie.Knows[charlie].vip)
        Whole(self, charlie)

    def test_nothing_of_a_refused_or_extended_linking_keeps_an_agent_alive(self):
        for where in ("record", "gate"):
            with self.subTest(where=where):
                plan = {"promote_at": where, "fail_at": "record"}
                _Circle, Popular, charlie, ruth, sam, tom = self.Make(plan)

                with self.assertRaises(TagCompositionError):
                    charlie.Knows(tom)

                references = [weakref.ref(charlie), weakref.ref(ruth), weakref.ref(sam), weakref.ref(tom)]
                plan.clear()                              # the plan itself holds her Contact
                del plan, _Circle, Popular, charlie, ruth, sam, tom, where
                gc.collect()
                self.assertEqual([reference() for reference in references], [None] * 4)

    # --- more cases ---

    def test_an_extension_at_the_contacts_entry_is_kept_when_her_entry_is_then_refused(self):
        for held in (False, True):
            with self.subTest(held=held):
                plan = {}
                Circle, Popular = Promoting_Circle(plan)
                charlie, ruth, tom = People("Charlie", "Ruth", "Tom")
                Circle(charlie)
                Lining_Club(charlie)
                charlie.Knows(ruth)

                if held:
                    charlie.Knows(tom)                    # her Pair is held through the Base Link

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    charlie.Member(tom)                   # her lines are Member's: the Link's replace them at her entry

                plan["target"] = tom

                def Gain_Then_Refuse(message, category, filename, lineno, file=None, line=None):
                    if charlie not in Popular:
                        Popular(charlie)                  # while she enters, her Pair whole
                        raise ValueError("her entry is refused")

                with warnings.catch_warnings():
                    warnings.simplefilter("always")
                    previous, warnings.showwarning = warnings.showwarning, Gain_Then_Refuse

                    try:
                        with self.assertRaises(ValueError):
                            (charlie.Trusts if held else charlie.Knows)(tom)
                    finally:
                        warnings.showwarning = previous

                self.assertNotIn(tom, charlie.Trusts if held else charlie.Knows)
                self.Assert_Extended(charlie, Popular, [ruth, tom] if held else [ruth])

    def test_a_linking_made_at_a_pairs_records_is_given_the_layer_too(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None, then=None, promote=False):
                    if then is not None:
                        agent.Knows(then, promote=True)   # a second linking, in flight inside the first
                    if promote and agent not in Popular:
                        Popular(agent)
                    return since

        class Popular(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def vip(agent, contact):
                    return True

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Circle(charlie)
        charlie.Knows(ruth, then=sam)
        self.assertIn(charlie, Popular)
        for contact in (ruth, sam):
            self.assertTrue(charlie.Knows[contact].vip)
        Whole(self, charlie)

    def test_the_first_linking_of_a_link_can_gain_the_shape_too(self):
        plan = {"promote_at": "record"}
        Circle, Popular = Promoting_Circle(plan)
        charlie, ruth = People("Charlie", "Ruth")
        Circle(charlie)
        plan["target"] = ruth
        charlie.Knows(ruth)                               # the Link holds no Contact yet
        self.Assert_Extended(charlie, Popular, [ruth])

    def test_a_pair_reached_while_it_enters_a_joined_family_is_given_the_layer(self):
        class Two(Tag):
            @Link
            class Knows(Tag):
                @Record
                def known(agent, contact, *, promote=False):
                    if promote and agent not in Popular:
                        Popular(agent)
                    return "known"

            @Link
            class Likes(Tag):
                @Record
                def liked(agent, contact):
                    return "liked"

            @Link
            class Bonded(Knows, Likes):
                pass

        class Popular(Two):
            @Link
            class Knows(Two.Knows):
                @Record
                def vip(agent, contact):
                    return True

        charlie, ruth, sam = People("Charlie", "Ruth", "Sam")
        Two(charlie)
        charlie.Likes(ruth)                               # her Pair is held through Likes
        charlie.Knows(sam)
        charlie.Bonded(ruth, promote=True)                # and she enters Knows and Bonded, gaining the Shape on the way
        self.assertTrue(charlie.Bonded[ruth].vip)
        self.assertTrue(charlie.Knows[sam].vip)
        Whole(self, charlie)

    def test_the_extensions_teardowns_run_once_for_each_pair_it_reached(self):
        torn = []

        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, promote=False):
                    if promote and agent not in Popular:
                        Popular(agent)
                    return 1

            @Link
            class Trusts(Knows):
                @Record
                def level(agent, contact, *, promote=False):
                    if promote and agent not in Popular:
                        Popular(agent)
                    return 1

        class Popular(Circle):
            @Link
            class Knows(Circle.Knows):
                @Rip
                def Goodbye(agent, contact):
                    torn.append(contact.name)

        charlie, ruth, sam, tom = People("Charlie", "Ruth", "Sam", "Tom")
        Circle(charlie)
        charlie.Knows(ruth)
        charlie.Knows(sam)
        charlie.Trusts(sam, promote=True)                 # a held Pair in flight reached
        charlie.Knows(tom, promote=False)                 # a Pair linked after the extension
        del charlie.Trusts[sam]
        del charlie.Knows[sam]
        del charlie.Knows[ruth]
        del charlie.Knows[tom]
        self.assertEqual(sorted(torn), ["Ruth", "Sam", "Tom"])

    def test_a_linking_refused_at_the_contacts_entry_takes_back_all_it_gave_a_held_pair(self):
        plan = {}
        Circle, Popular = Promoting_Circle(plan)
        charlie, ruth, tom = People("Charlie", "Ruth", "Tom")
        Circle(charlie)
        Lining_Club(charlie)
        charlie.Knows(tom, level=0)                       # her Pair is held through the Base Link

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            charlie.Member(tom)                           # her line Hail is Member's: Trusts' replaces it at her entry

        with warnings.catch_warnings():
            warnings.simplefilter("error", TagOverwriteWarning)

            with self.assertRaises(TagOverwriteWarning):
                charlie.Trusts(tom, level=4)

        self.assertFalse(hasattr(charlie.Knows[tom], "level"))   # a failure up to her entry changes nothing
        Whole(self, charlie)


def Agents_Of_Any_Link(contact):
    """The Links a Contact is a member of now, read from her state."""

    from TopKit.declarations import _is_link
    from TopKit.state import _state_of

    state = _state_of(contact)

    if state is None:
        return []

    return [tag for tag in state.active if _is_link(tag)]


if __name__ == "__main__":
    unittest.main()
