"""Conformance tests: contract namespace."""

from __future__ import annotations

import unittest
from TopKit import Contract
from TopKit import Post
from TopKit import Record
from TopKit import Tag
from TopKit import TagPostconditionError

from ._fixtures import Agent
from ._fixtures import Scholar


class ContractNamespaceTests(unittest.TestCase):
    def test_native_truth_replaces_holds_and_keeps_named_diagnostics(self) -> None:
        self.assertNotIn("Holds", vars(Contract))

        class Checked(Tag):
            @Record
            def contents(agent):
                return []

            @Post
            def Ready(agent):
                return agent.contents is not None

        agent = Agent()
        Checked(agent)
        self.assertFalse(agent.contents)     # held values keep Python truth
        self.assertTrue(agent)              # the empty list satisfies Ready
        self.assertTrue(Contract.Postconditions(agent))

        agent.contents = None
        self.assertFalse(agent)
        with self.assertRaises(TagPostconditionError.Ready):
            Contract.Postconditions(agent)
        self.assertEqual(Contract.Status(agent), {"Ready": False})

        Contract.Delete(agent, "Ready")
        self.assertTrue(agent)

    def test_contract_namespace_checks_the_live_posts_only(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)

        self.assertTrue(Contract.Postconditions(ari))
        self.assertFalse(hasattr(Contract, "Preconditions"))
        self.assertFalse(hasattr(Contract, "Conditions"))
        self.assertTrue(bool(ari))

        del ari.spellbook

        with self.assertRaises(TagPostconditionError):
            Contract.Postconditions(ari)

    def test_contract_status_and_display(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)

        self.assertEqual(Contract.Status(ari), {"Has_Book": True})

        del ari.spellbook
        text = Contract.Display(ari)

        self.assertTrue(text.startswith("Agent[Scholar] contract:"))
        self.assertNotIn("Pre:", text)
        self.assertIn("XX  Has_Book", text)
