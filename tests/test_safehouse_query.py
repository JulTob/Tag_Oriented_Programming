"""Public Safehouse query and its separate population status."""

from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from TopKit import Post
from TopKit import Postcondition
from TopKit import Tag
from TopKit.arrest import _Arrest
from TopKit.arrest import _safehouse
from TopKit.fields import _Partition
from TopKit.fields import _field_of


class Host:
    pass


class SafehouseQueryTests(unittest.TestCase):
    def test_owning_tag_and_root_query_saved_work_by_identity(self) -> None:
        Old = type("Role", (Tag,), {})
        New = type("Role", (Tag,), {})
        Other = type("Other", (Tag,), {})
        agent = Host()
        Old(agent)
        Other(agent)
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Old))

        self.assertEqual(list(Tag[...]), [])
        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            self.assertIn(agent, Old[...])
            self.assertIn(agent, Tag[...])
            self.assertNotIn(agent, New[...])
            self.assertNotIn(agent, Other[...])
            self.assertEqual(list(Old[...]), [agent])
            self.assertEqual(len(Tag[...]), 1)
            self.assertTrue(Old[...])
            self.assertEqual(list(Old[...] | Other[...]), [agent])

            # Custody is global; an Agent remains raw-admitted in each
            # Field but is not in either sound population during arrest.
            self.assertIn(agent, Old[:])
            self.assertIn(agent, Other[:])
            self.assertNotIn(agent, Old)
            self.assertNotIn(agent, Other)
            self.assertEqual(list(Old), [])
            self.assertEqual(list(Other), [])
            self.assertEqual(len(Old), 0)

        self.assertNotIn(agent, Old[...])
        self.assertIn(agent, Old)

    def test_arrested_post_failure_is_neither_sound_nor_defective(self) -> None:
        class Fighter(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        agent = Host()
        agent.ready = False
        with self.assertRaises(Postcondition.Ready):
            Fighter(agent)

        self.assertIn(agent, Fighter[:])
        self.assertIn(agent, ~Fighter)
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Fighter))

        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            self.assertIn(agent, Fighter[:])
            self.assertIn(agent, Fighter[...])
            self.assertNotIn(agent, Fighter)
            self.assertNotIn(agent, ~Fighter)
            self.assertEqual(list(Fighter), [])
            self.assertEqual(list(~Fighter), [])
            self.assertEqual(len(Fighter[:]), 1)
            self.assertEqual(len(Fighter) + len(~Fighter), 0)

        self.assertIn(agent, ~Fighter)

    def test_arrest_during_a_population_check_does_not_yield_agent(self) -> None:
        class Role(Tag):
            pass

        agent = Host()
        Role(agent)
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Role))

        def Check(candidate):
            self.assertIs(candidate, agent)
            _safehouse[id(agent)] = arrest
            return True

        with patch.dict(_safehouse, {}, clear=True):
            sound = _Partition(_field_of(Role), Check, "sound")
            self.assertEqual(list(sound), [])


if __name__ == "__main__":
    unittest.main()
