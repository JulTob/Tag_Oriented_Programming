"""Tag-keyed Rip and view state uses Tag identity, even for custom metaclasses."""

from __future__ import annotations

import unittest

from TopKit import Rip
from TopKit import Tag
from TopKit.lifecycle import _teardown_all
from TopKit.state import _State
from TopKit.tags import MetaTag


class Host:
    pass


class TagIdentityMapTests(unittest.TestCase):
    def test_equal_but_distinct_tags_keep_separate_entries_and_copies(self) -> None:
        class EqualMeta(MetaTag):
            def __hash__(cls):
                return 1

            def __eq__(cls, other):
                return isinstance(other, EqualMeta)

        class First(Tag, metaclass=EqualMeta):
            pass

        class Second(Tag, metaclass=EqualMeta):
            pass

        first_view, second_view = object(), object()
        first_rips, second_rips = (("first", lambda agent: None),), (("second", lambda agent: None),)
        state = _State(host_type=Host)
        state.snapshots[First] = first_view
        state.snapshots[Second] = second_view
        state.rips[First] = first_rips
        state.rips[Second] = second_rips

        copied = state.Copy()
        self.assertEqual(len(copied.snapshots), 2)
        self.assertEqual(len(copied.rips), 2)
        self.assertIs(copied.snapshots[First], first_view)
        self.assertIs(copied.snapshots[Second], second_view)
        self.assertIs(copied.rips[First], first_rips)
        self.assertIs(copied.rips[Second], second_rips)

        state.snapshots.pop(First)
        state.rips.pop(First)
        self.assertIs(copied.snapshots[First], first_view)
        self.assertIs(copied.rips[First], first_rips)

        state.Restore(copied)
        self.assertIs(state.snapshots[First], first_view)
        self.assertIs(state.rips[Second], second_rips)

        retained = state.Copy()
        state.rips.clear()
        self.assertEqual(len(state.rips), 0)
        self.assertEqual(len(retained.rips), 2)
        self.assertEqual(len(state.snapshots), 2)

    def test_ordinary_rip_and_best_effort_teardown_do_not_hash_tag_state(self) -> None:
        hashes = []
        teardowns = []
        armed = False

        class NoisyMeta(MetaTag):
            def __hash__(cls):
                if armed:
                    hashes.append(cls)

                return type.__hash__(cls)

        class Closing(Tag, metaclass=NoisyMeta):
            @Rip
            def Finish(agent):
                teardowns.append(agent)

        agent = Host()
        Closing(agent)
        armed = True
        del Closing[agent]
        self.assertEqual(hashes, [])
        self.assertEqual(teardowns, [agent])

        armed = False
        Closing(agent)
        armed = True
        _teardown_all(agent)
        self.assertEqual(hashes, [])
        self.assertEqual(teardowns, [agent, agent])
