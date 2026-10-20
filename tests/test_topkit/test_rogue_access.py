"""Conformance tests: rogue access."""

from __future__ import annotations

import unittest
from TopKit import Operation
from TopKit import Post
from TopKit import Postcondition
from TopKit import Public
from TopKit import Report
from TopKit import Tag
from TopKit import TagRogueAccessError
from TopKit import TagResolutionError

from ._fixtures import Agent


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
        self.assertNotIn(ari, Agency)                                 # defective, so not sound
        self.assertIn(ari, Agency[:])                                 # raw membership remains

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
