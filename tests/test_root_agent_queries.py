"""The root Tag answers Agent status without an enumerable Field."""

from __future__ import annotations

from dataclasses import dataclass
import unittest

from TopKit import Flag
from TopKit import Imprint
from TopKit import Pin
from TopKit import Post
from TopKit import Pre
from TopKit import Record
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagImprintError
from TopKit import TagPostconditionError
from TopKit import TagPreconditionError
from TopKit import TagResolutionError
from TopKit import Tags
from TopKit.state import STATE
from TopKit.state import _State


class RootAgentQueryTests(unittest.TestCase):
    def test_host_dict_property_cannot_forge_root_agent_status(self) -> None:
        class Host:
            @property
            def __dict__(self):
                return {STATE: _State(host_type=Host, actualized=True)}

        untouched = Host()
        self.assertNotIn(untouched, Tag[:])
        self.assertNotIn(untouched, Tag)
        self.assertNotIn(untouched, ~Tag)
        self.assertNotIsInstance(untouched, Tag)

    def test_actualized_string_subclass_uses_membership_before_keyword(self) -> None:
        class Text(str):
            pass

        class Fighter(Tag):
            pass

        @Pin
        @Flag("Marked")
        class Mark(Tag):
            pass

        Mark(Fighter)
        self.assertIn("Marked", Fighter)   # plain strings remain keywords

        agent = Text("unmarked")
        Tag(agent)
        self.assertIn(agent, Tag[:])
        self.assertIn(agent, Tag)
        self.assertNotIn(agent, Fighter)

        Fighter(agent)
        self.assertIn(agent, Fighter[:])
        self.assertIn(agent, Fighter)
        self.assertNotIn("unmarked", Fighter)

    def test_nested_tagging_marks_a_completed_agent_during_first_transition(self) -> None:
        class Extra(Tag):
            pass

        class Outer(Tag):
            pass

        class Host:
            def __init__(self):
                self.once = False

            def __setattr__(self, name, value):
                if name == "__class__" and not self.once:
                    object.__setattr__(self, "once", True)
                    object.__setattr__(self, name, value)
                    Extra(self)
                    raise RuntimeError("outer rejects after nested Tagging")
                object.__setattr__(self, name, value)

        agent = Host()
        with self.assertRaises(TagCompositionError):
            Outer(agent)

        # Extra completed even though Outer failed. Restoring Outer also
        # restores Host's plain runtime type; that separate host rollback
        # defect is outside this root-status change.
        self.assertIn(agent, Extra[:])
        self.assertIn(agent, Tag[:])
        self.assertIn(agent, Tag)
        self.assertIsInstance(agent, Tag)

    def test_refused_gate_and_host_transition_do_not_make_an_agent(self) -> None:
        class Host:
            pass

        class Refused(Tag):
            @Pre
            def Ready(agent):
                return False

        untouched = Host()
        with self.assertRaises(TagPreconditionError.Ready):
            Refused(untouched)

        for candidate in (untouched, Host()):
            self.assertNotIn(candidate, Tag[:])
            self.assertNotIn(candidate, Tag)
            self.assertNotIn(candidate, ~Tag)
            self.assertNotIsInstance(candidate, Tag)

        class Dict_Without_Weakrefs:
            __slots__ = ("__dict__",)

        rejected = Dict_Without_Weakrefs()
        with self.assertRaises(TagCompositionError):
            Tag(rejected)

        self.assertNotIn(rejected, Tag[:])
        self.assertNotIsInstance(rejected, Tag)

    def test_root_application_actualizes_without_agency_and_survives_last_rip(self) -> None:
        class Host:
            pass

        class Fighter(Tag):
            pass

        agent = Host()
        self.assertIs(Tag(agent), agent)
        self.assertEqual(Tags(agent), ())
        self.assertIn(agent, Tag[:])
        self.assertIn(agent, Tag)
        self.assertNotIn(agent, ~Tag)
        self.assertIsInstance(agent, Tag)
        self.assertEqual(list(Fighter[:]), [])

        Fighter(agent)
        del Fighter[agent]
        self.assertIn(agent, Tag[:])
        self.assertIn(agent, Tag)
        self.assertIsInstance(agent, Tag)

    def test_failed_imprint_keeps_a_rogue_and_current_posts_classify_it(self) -> None:
        ready = False

        class Unfinished(Tag):
            @Post
            def Ready(agent):
                return ready

            @Record
            def Part(agent):
                return "acquired"

            @Imprint
            def Train(agent):
                raise RuntimeError("interrupted")

        class Host:
            pass

        agent = Host()
        with self.assertRaises(TagImprintError.Train):
            Unfinished(agent)

        self.assertEqual(agent.Part, "acquired")
        self.assertNotIn(agent, Unfinished[:])
        self.assertIn(agent, Tag[:])
        self.assertNotIn(agent, Tag)
        self.assertIn(agent, ~Tag)
        self.assertIsInstance(agent, Tag)

        ready = True
        self.assertIn(agent, Tag)
        self.assertNotIn(agent, ~Tag)
        self.assertNotIn(agent, Unfinished[:])

    def test_pin_and_frozen_host_actualization_use_the_same_root_query(self) -> None:
        class Fighter(Tag):
            pass

        @Pin
        class Rare(Tag):
            pass

        self.assertNotIn(Fighter, Tag[:])
        Rare(Fighter)
        self.assertIn(Fighter, Tag[:])
        self.assertIn(Fighter, Tag)
        self.assertIsInstance(Fighter, Tag)

        @dataclass(frozen=True)
        class Frozen:
            serial: int

        host = Frozen(7)
        Tag(host)
        self.assertIn(host, Tag[:])
        self.assertIn(host, Tag)
        self.assertIsInstance(host, Tag)
        self.assertEqual(host.serial, 7)

    def test_root_queries_filter_concrete_populations_on_the_right(self) -> None:
        class Host:
            pass

        class Fighter(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        sound, broken = Host(), Host()
        sound.ready = True
        broken.ready = False
        Fighter(sound)
        with self.assertRaises(TagPostconditionError.Ready):
            Fighter(broken)

        self.assertEqual(list(Fighter[:] & Tag[:]), [sound, broken])
        self.assertEqual(list(Fighter[:] & Tag), [sound])
        self.assertEqual(list(Fighter[:] & ~Tag), [broken])
        self.assertEqual(list(Fighter[:] - ~Tag), [sound])
        self.assertEqual(list(Fighter & Tag), [sound])
        self.assertIn(sound, Tag & Fighter)
        self.assertIn(broken, Tag[:] & Fighter[:])
        self.assertNotIn(broken, Tag & Fighter)
        self.assertIn(broken, ~~Tag)

    def test_root_walks_lengths_and_unions_fail_before_yielding(self) -> None:
        class Host:
            pass

        class Fighter(Tag):
            pass

        agent = Host()
        Fighter(agent)

        self.assertTrue(Tag)   # the root Tag's own Post contract
        for query in (Tag, ~Tag, Tag[:]):
            with self.assertRaisesRegex(TagResolutionError, "root Tag has no Field"):
                iter(query)
            with self.assertRaisesRegex(TagResolutionError, "root Tag has no Field"):
                len(query)

        with self.assertRaisesRegex(TagResolutionError, "root Tag has no Field"):
            bool(Tag[:])
        with self.assertRaisesRegex(TagResolutionError, "root Tag has no Field"):
            bool(~Tag)

        for query in (Tag & Fighter, Tag[:] & Fighter[:]):
            self.assertIn(agent, query)
            with self.assertRaisesRegex(TagResolutionError, "root Tag has no Field"):
                iter(query)

        self.assertNotIn(agent, Tag[:] - Fighter[:])
        with self.assertRaisesRegex(TagResolutionError, "root Tag has no Field"):
            iter(Tag[:] - Fighter[:])

        for left, right in ((Fighter, Tag), (Tag, Fighter),
                            (Fighter[:], Tag[:])):
            with self.assertRaisesRegex(TagResolutionError, "root Tag has no Field"):
                _ = left | right

        self.assertEqual(list(Fighter[:] & Tag[:]), [agent])
        self.assertIsNotNone(Tag | None)   # Python typing unions still work


if __name__ == "__main__":
    unittest.main()
