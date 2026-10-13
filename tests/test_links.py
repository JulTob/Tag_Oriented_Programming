"""Links: a Tag of one's own (STEP-SPEC-22).

Organised as the STEP's Acceptance requirements: the rules and their
refusals, the five findings of the hand-made workaround as regressions,
the Pair, the seats, Bases, extending a held Link, the closed slot, the
doors, the Relation's refused spellings, ending in reference cycles, and
the barrier.
"""

import asyncio
import contextvars
import copy
import gc
import unittest
import warnings
import weakref

from TopKit import (Action, At_Exit, Contract, Delete, Flag, Imprint,
                    Keyword, Link, Operation, Outline, Pin, Post, Pre, Public, Record,
                    Report, Rip, Secret, Tag, TagCompositionError,
                    TagDeclarationError, TagImprintError,
                    TagOverwriteWarning, TagPostconditionError,
                    TagPreconditionError, TagResolutionError,
                    TagRogueAccessError, Tags, Tool, Underlay)
from TopKit.lifecycle import _teardown_all


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
                agent.__dict__[name] = value

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
        self.assertTrue(Contract.Holds(ruth))             # finding 4: never defective elsewhere

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
        self.assertTrue(Contract.Holds(ruth))

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
        self.assertTrue(Contract.Holds(ruth))

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

    def test_an_extension_made_during_a_linking_reaches_the_pair_in_flight(self):
        class Circle(Tag):
            @Link
            class Knows(Tag):
                @Record
                def since(agent, contact, *, since=None):
                    if since == "promote" and agent not in Popular:
                        Popular(agent)                    # the Agent gains the Shape that extends Knows
                    return since

        class Popular(Circle):
            @Link
            class Knows(Circle.Knows):
                @Record
                def vip(agent, contact):
                    return True

                def Greet(agent, contact):
                    return "a popular greeting"

        charlie, ruth, sam, tom = People("Charlie", "Ruth", "Sam", "Tom")
        Circle(charlie)
        charlie.Knows(ruth, since=1)
        charlie.Knows(sam, since="promote")               # Popular(charlie) happens inside this linking
        charlie.Knows(tom, since=3)
        self.assertIn(charlie, Popular)
        for contact in (ruth, sam, tom):
            self.assertTrue(charlie.Knows[contact].vip)
            self.assertEqual(charlie.Knows[contact].Greet(), "a popular greeting")

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

    def test_a_generator_line_runs_each_step_behind_the_doors(self):
        from TopKit.state import _state_of

        closed = []

        class Circle(Tag):
            @Secret
            @Record
            def ledger(agent):
                return "his ledger"

            @Link
            class Member(Tag):
                @Public
                def Stream(agent, contact):
                    received = yield (Read_Or_Shut(contact, "diary"), Read_Or_Shut(agent, "ledger"))
                    yield received
                    return "done"

                @Public
                def Guarded(agent, contact):
                    try:
                        yield 1
                    except ValueError:
                        yield Read_Or_Shut(contact, "diary")   # handling a throw is a step too
                    finally:
                        closed.append(Read_Or_Shut(contact, "diary"))

        class Writer(Tag):
            @Secret
            @Record
            def diary(agent):
                return "her secret"

            def Drive(agent):
                steps = agent.Stream()
                first = next(steps)
                between = agent.diary                     # her own code between steps: her door is open
                echoed = steps.send("hello")
                try:
                    next(steps)
                except StopIteration as stop:
                    final = stop.value
                return first, between, echoed, final

            def Drive_Guarded(agent):
                steps = agent.Guarded()
                next(steps)
                handled = steps.throw(ValueError("thrown in"))
                steps.close()
                return handled

        charlie, ruth = People("Charlie", "Ruth")
        Circle(charlie)
        Writer(ruth)
        charlie.Member(ruth)
        self.assertEqual(
                ruth.Drive(),
                (("shut", "his ledger"), "her secret", "hello", "done"),
                )
        self.assertEqual(ruth.Drive_Guarded(), "shut")
        self.assertEqual(closed, ["shut"])
        self.assertEqual(_state_of(ruth).composing, 0)    # every door is back as it was
        self.assertEqual(_state_of(charlie).composing, 0)

    def test_a_coroutine_line_runs_each_step_behind_the_doors(self):
        from TopKit.state import _state_of

        class Circle(Tag):
            @Secret
            @Record
            def ledger(agent):
                return "his ledger"

            @Link
            class Member(Tag):
                @Public
                async def Fetch(agent, contact):
                    await asyncio.sleep(0)
                    return (Read_Or_Shut(contact, "diary"), Read_Or_Shut(agent, "ledger"))

                @Public
                async def Fail(agent, contact):
                    await asyncio.sleep(0)
                    raise ValueError("refused")

                async def Wait(agent, contact):
                    await asyncio.sleep(10)

        class Writer(Tag):
            @Secret
            @Record
            def diary(agent):
                return "her secret"

            def Sync_Fetch(agent):
                return asyncio.run(agent.Fetch())

            def Sync_Fail(agent):
                return asyncio.run(agent.Fail())

        charlie, ruth = People("Charlie", "Ruth")
        Circle(charlie)
        Writer(ruth)
        charlie.Member(ruth)
        self.assertEqual(ruth.Sync_Fetch(), ("shut", "his ledger"))
        with self.assertRaises(ValueError):
            ruth.Sync_Fail()

        async def Cancel_It():
            task = asyncio.ensure_future(charlie.Member[ruth].Wait())
            await asyncio.sleep(0)
            task.cancel()
            await task

        with self.assertRaises(asyncio.CancelledError):
            asyncio.run(Cancel_It())
        self.assertEqual(_state_of(ruth).composing, 0)
        self.assertEqual(_state_of(charlie).composing, 0)

    def test_a_generator_operation_keeps_her_door_shut_at_each_step(self):
        class Circle(Tag):
            @Link
            class Member(Tag):
                @Operation
                def Scan(link, contact):
                    yield Read_Or_Shut(contact, "diary")

        class Writer(Tag):
            @Secret
            @Record
            def diary(agent):
                return "her secret"

            def Ask(agent, link):
                return list(link.Scan(contact=agent))

        charlie, ruth = People("Charlie", "Ruth")
        Circle(charlie)
        Writer(ruth)
        charlie.Member(ruth)
        self.assertEqual(ruth.Ask(charlie.Member), ["shut"])

    def test_an_async_generator_in_a_relation_is_refused(self):
        with self.assertRaises(TagDeclarationError):
            class Circle(Tag):
                @Link
                class Member(Tag):
                    async def Stream(agent, contact):
                        yield 1

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
