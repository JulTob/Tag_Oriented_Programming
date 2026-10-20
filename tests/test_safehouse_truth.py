"""An arrested Agent cannot answer True to its contract truth query."""

from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from TopKit import Pin
from TopKit import Post
from TopKit import Tag
from TopKit.arrest import _Arrest
from TopKit.arrest import _safehouse


class Host:
    pass


class SafehouseTruthTests(unittest.TestCase):
    def test_no_post_agent_is_false_while_arrested(self) -> None:
        class Fighter(Tag):
            pass

        agent = Host()
        Fighter(agent)
        self.assertTrue(bool(agent))
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Fighter))

        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            self.assertFalse(bool(agent))
            self.assertIn(agent, Fighter[:])
            self.assertNotIn(agent, Fighter)
            self.assertNotIn(agent, ~Fighter)
        self.assertTrue(bool(agent))

    def test_arrest_prevents_post_evaluation(self) -> None:
        checks = []

        class Fighter(Tag):
            @Post
            def Ready(agent):
                checks.append("evaluated")
                return True

        agent = Host()
        Fighter(agent)
        checks.clear()
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Fighter))

        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            self.assertFalse(bool(agent))
            self.assertEqual(checks, [])

    def test_post_that_catches_its_own_arrest_cannot_make_agent_true(self) -> None:
        armed = False

        class Fighter(Tag):
            @Post
            def Ready(agent):
                if armed:
                    arrest = _Arrest(agent)
                    arrest.runs.append(SimpleNamespace(tag=Fighter))
                    _safehouse[id(agent)] = arrest
                return True

        agent = Host()
        Fighter(agent)
        armed = True
        with patch.dict(_safehouse, {}, clear=True):
            self.assertFalse(bool(agent))
            self.assertIn(agent, Fighter[...])

    def test_pinned_tag_agent_is_false_during_its_own_arrest(self) -> None:
        class Fighter(Tag):
            pass

        @Pin
        class Registered(Tag):
            pass

        Registered(Fighter)
        self.assertTrue(bool(Fighter))
        arrest = _Arrest(Fighter)
        arrest.runs.append(SimpleNamespace(tag=Registered))

        with patch.dict(_safehouse, {id(Fighter): arrest}, clear=True):
            self.assertFalse(bool(Fighter))
        self.assertTrue(bool(Fighter))


if __name__ == "__main__":
    unittest.main()
