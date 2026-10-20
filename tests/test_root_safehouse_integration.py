"""Root Agent queries keep custody separate from Post-based defect."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from TopKit import Post, Tag
from TopKit.arrest import _Arrest, _safehouse


class Host:
    pass


class RootSafehouseIntegrationTests(unittest.TestCase):
    def test_arrested_agent_without_posts_is_neither_root_sound_nor_defective(self):
        class Fighter(Tag):
            pass

        agent = Host()
        Fighter(agent)
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Fighter))

        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            self.assertIn(agent, Fighter[:])
            self.assertIn(agent, Fighter[...])
            self.assertIn(agent, Tag[:])
            self.assertIsInstance(agent, Tag)
            self.assertNotIn(agent, Tag)
            self.assertNotIn(agent, ~Tag)
            self.assertNotIn(agent, Fighter)
            self.assertNotIn(agent, ~Fighter)
            self.assertEqual(list(Fighter[:] & Tag[:]), [agent])
            self.assertEqual(list(Fighter[:] & Tag), [])
            self.assertEqual(list(Fighter[:] & ~Tag), [])

        self.assertIn(agent, Tag)

    def test_arrested_agent_with_posts_is_neither_root_sound_nor_defective(self):
        class Fighter(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        agent = Host()
        agent.ready = True
        Fighter(agent)
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Fighter))

        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            self.assertIn(agent, Tag[:])
            self.assertNotIn(agent, Tag)
            self.assertNotIn(agent, ~Tag)
            self.assertNotIn(agent, Fighter)
            self.assertNotIn(agent, ~Fighter)

        self.assertIn(agent, Tag)
        agent.ready = False
        self.assertIn(agent, ~Tag)

    def test_post_that_arrests_its_agent_cannot_make_root_defective(self):
        arrest_on_read = False
        arrest = None

        class Fighter(Tag):
            @Post
            def Ready(agent):
                if arrest_on_read:
                    _safehouse[id(agent)] = arrest
                return True

        agent = Host()
        Fighter(agent)
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Fighter))
        arrest_on_read = True

        with patch.dict(_safehouse, {}, clear=True):
            self.assertNotIn(agent, ~Tag)
            self.assertIn(agent, Tag[:])
            self.assertIn(agent, Tag[...])


if __name__ == "__main__":
    unittest.main()
