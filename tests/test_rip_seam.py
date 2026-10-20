"""The Rip seam: revocation hands over the saved chain, teardown only runs it.

`_revoke_membership` ends one membership now and takes the saved `@Rip`
chain out of the Agent's state. `_teardown` runs exactly the tuple it is
given. These tests pin that contract, because `del Tag[:]` will rely on
it: revoke every member first, run the saved chains after, and keep each
old chain apart from any fresh Tagging a teardown starts.
"""

from __future__ import annotations

import unittest

from TopKit import Rip
from TopKit import Tag
from TopKit.lifecycle import _revoke_membership
from TopKit.lifecycle import _teardown
from TopKit.state import _state_of


class Host:
    pass


class RipSeamTests(unittest.TestCase):

    def test_revocation_ends_membership_and_takes_the_chain(self):
        ran = []

        class Guarded(Tag):
            @Rip
            def Release(agent):
                ran.append("released")

        agent = Host()
        Guarded(agent)

        state, chain = _revoke_membership(agent, Guarded)

        self.assertNotIn(agent, Guarded[:])
        self.assertNotIn(
                Guarded,
                state.rips,
                "the saved chain must leave the state at revocation",
                )
        self.assertEqual(ran, [], "revocation alone runs no teardown")
        self.assertEqual(len(chain), 1, "the chain is handed to the caller")

        _teardown(agent, state, Guarded, chain)

        self.assertEqual(ran, ["released"])

    def test_the_old_chain_survives_a_fresh_tagging_between_the_steps(self):
        #-- The whole-Field shape: revoke both members first, tear down after.
        log = []
        first, second = Host(), Host()

        class Guarded(Tag):
            @Rip
            def Release(agent):
                log.append("old:" + ("first" if agent is first else "second"))
                if agent is first:
                    Guarded(second)   # a teardown starts a fresh Tagging

        Guarded(first)
        Guarded(second)

        state_first, chain_first = _revoke_membership(first, Guarded)
        state_second, chain_second = _revoke_membership(second, Guarded)
        self.assertNotIn(first, Guarded[:])
        self.assertNotIn(second, Guarded[:])

        _teardown(first, state_first, Guarded, chain_first)

        self.assertIn(second, Guarded[:], "the fresh Tagging readmitted it")
        self.assertIn(
                Guarded,
                _state_of(second).rips,
                "the fresh Tagging saved a fresh chain of its own",
                )

        _teardown(second, state_second, Guarded, chain_second)

        self.assertEqual(log, ["old:first", "old:second"])
        self.assertIn(
                second,
                Guarded[:],
                "running the old chain does not touch the fresh membership",
                )


if __name__ == "__main__":
    unittest.main()
