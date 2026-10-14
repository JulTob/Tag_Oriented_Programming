"""Conformance tests: rip."""

from __future__ import annotations

import unittest
from TopKit import Rip
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagResolutionError
from TopKit import Underlay

from ._fixtures import Agent
from ._fixtures import Beast
from ._fixtures import Knighted
from ._fixtures import Squire
from ._fixtures import Wolf


class RipTests(unittest.TestCase):
    def test_rip_leaves_a_rogue_agent_with_sticky_contributions(self) -> None:
        ari = Agent()

        Squire(ari)
        del Squire[ari]

        self.assertNotIn(ari, Squire)
        self.assertEqual(ari.rank, "squire")

    def test_rip_action_runs_on_rip(self) -> None:
        ari = Agent()

        Squire(ari)
        Knighted(ari)

        self.assertEqual(ari.rank_reset(), "Disrobed")

        ari.rank = "knight"
        del Knighted[ari]

        self.assertNotIn(ari, Knighted)
        self.assertIsNone(ari.rank)

    def test_rip_teardown_with_underlay_runs_composed(self) -> None:
        log: list[str] = []

        class Guard(Tag):
            def stand_down(agent) -> None:
                log.append("base")

        class Elite(Guard):
            @Rip
            @Underlay
            def stand_down(agent, base) -> None:
                base()
                log.append("elite")

        ari = Agent()
        Elite(ari)
        del Elite[ari]

        self.assertEqual(log, ["base", "elite"])

    def test_teardown_failure_is_reported_after_membership_ends(self) -> None:
        class Fragile(Tag):
            @Rip
            def boom(agent) -> None:
                raise RuntimeError("x")

        ari = Agent()
        Fragile(ari)

        with self.assertRaises(TagCompositionError):
            del Fragile[ari]

        self.assertNotIn(ari, Fragile)

    def test_ripping_a_required_base_is_refused(self) -> None:
        ari = Agent()

        Wolf(ari)

        with self.assertRaises(TagCompositionError):
            del Beast[ari]

        self.assertIn(ari, Beast)

        del Wolf[ari]
        self.assertIn(ari, Beast)

        del Beast[ari]
        self.assertNotIn(ari, Beast)

    def test_ripped_agent_is_not_yielded_by_field_iteration(self) -> None:
        ari = Agent()
        bea = Agent()

        Squire(ari)
        Squire(bea)
        del Squire[ari]

        self.assertEqual(list(Squire[:]), [bea])

    def test_ripping_an_inactive_tag_raises(self) -> None:
        ari = Agent()

        with self.assertRaises(TagResolutionError):
            del Knighted[ari]

    def test_reapply_after_rip_is_a_fresh_application(self) -> None:
        ari = Agent()

        Squire(ari)
        ari.rank = "knight"
        del Squire[ari]
        Squire(ari)

        self.assertIn(ari, Squire)
        self.assertEqual(ari.events, ["Squire", "Squire"])
        self.assertEqual(ari.rank, "squire")
