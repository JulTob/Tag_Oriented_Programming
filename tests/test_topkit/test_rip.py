"""Conformance tests: rip."""

from __future__ import annotations

import unittest
from TopKit import Pin
from TopKit import Post
from TopKit import Record
from TopKit import Rip
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagResolutionError
from TopKit import Underlay

from ._fixtures import Agent
from ._fixtures import Knighted
from ._fixtures import Squire


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

    def test_ripping_a_base_keeps_its_shape_and_trains_the_base_again_on_request(self) -> None:
        teardowns: list[str] = []

        class Candidate(Tag):
            @Record
            def training(agent, stored):
                return (stored or 0) + 1

            def Call(agent):
                return "Candidate"

            @Rip
            def Leave_Candidate(agent):
                teardowns.append("Candidate")

        class CIA(Candidate):
            @Underlay
            def Call(agent, base):
                return f"CIA after {base()}"

            @Rip
            def Leave_CIA(agent):
                teardowns.append("CIA")

        ari = Agent()
        CIA(ari)

        del Candidate[ari]

        self.assertNotIn(ari, Candidate)
        self.assertIn(ari, CIA)
        self.assertEqual(list(CIA[:]), [ari])
        self.assertEqual(list(CIA), [ari])
        self.assertTrue(bool(ari))
        self.assertTrue(isinstance(ari, Candidate))
        self.assertEqual(ari.training, 1)
        self.assertEqual(ari.Call(), "CIA after Candidate")
        self.assertEqual(teardowns, ["Candidate"])

        with self.assertRaises(TagResolutionError):
            Candidate[ari]
        self.assertIsNotNone(CIA[ari])

        CIA(ari)                          # an active Shape does not silently restore a Base
        self.assertNotIn(ari, Candidate)
        self.assertEqual(ari.training, 1)

        Candidate(ari)                    # an explicit new Tagging trains the Base again
        self.assertIn(ari, Candidate)
        self.assertIn(ari, CIA)
        self.assertEqual(ari.training, 2)

        del CIA[ari]
        self.assertEqual(teardowns, ["Candidate", "CIA"])

    def test_a_shape_can_require_its_base_with_a_post(self) -> None:
        class Agency(Tag):
            pass

        class Operative(Agency):
            @Post
            def Still_Agency(agent):
                return agent not in Operative[:] or agent in Agency[:]

        ari = Agent()
        Operative(ari)

        del Agency[ari]

        self.assertIn(ari, Operative)
        self.assertFalse(bool(ari))
        self.assertEqual(list(Operative), [])
        self.assertEqual(list(~Operative), [ari])

        Agency(ari)
        self.assertTrue(bool(ari))
        self.assertEqual(list(Operative), [ari])

    def test_ripping_a_base_pin_keeps_its_shape_pin(self) -> None:
        @Pin
        class Basic(Tag):
            pass

        class Special(Basic):
            pass

        class Agency(Tag):
            pass

        Special(Agency)
        del Basic[Agency]

        self.assertNotIn(Agency, Basic)
        self.assertIn(Agency, Special)
        self.assertEqual(list(Special[:]), [Agency])

        Basic(Agency)
        self.assertIn(Agency, Basic)

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
