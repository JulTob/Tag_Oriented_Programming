"""Conformance tests: flag word."""

from __future__ import annotations

import unittest
from TopKit import Flag
from TopKit import Keyword
from TopKit import Pin
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagDeclarationError

from ._fixtures import Agent
from ._fixtures import Bag
from ._fixtures import Elf


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
            bag = Bag()

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
