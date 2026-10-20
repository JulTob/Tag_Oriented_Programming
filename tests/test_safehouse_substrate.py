"""Private Safehouse mechanics before public Rip routing is enabled."""

from __future__ import annotations

from contextvars import copy_context
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from TopKit import Post
from TopKit import Tag
from TopKit import TagArrestedAccessError
from TopKit import TagContractError
from TopKit import TagResolutionError
from TopKit.arrest import _Arrest
from TopKit.arrest import _arrest_of
from TopKit.arrest import _hold_lazy_result
from TopKit.arrest import _may_act
from TopKit.arrest import _rip_door
from TopKit.arrest import _safehouse
from TopKit.fields import _Safehouse


class SafehouseSubstrateTests(unittest.TestCase):
    def test_saved_custody_does_not_weaken_recursive_post_guard(self) -> None:
        class Host:
            pass

        class Checking(Tag):
            @Post
            def Ready(agent):
                return agent in ~Checking

        agent = Host()
        with self.assertRaises(TagContractError):
            Checking(agent)

        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Checking))
        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            self.assertIn(agent, _Safehouse(Checking))
            self.assertIn(agent, Checking[:])
            with self.assertRaises(TagContractError):
                list(Checking)

    def test_error_is_a_resolution_failure(self) -> None:
        self.assertTrue(issubclass(TagArrestedAccessError, TagResolutionError))

    def test_exact_tag_identity_and_live_removal_need_no_host_protocol(self) -> None:
        class Host:
            def __hash__(self):
                raise AssertionError("host hash ran")

            def __eq__(self, other):
                raise AssertionError("host equality ran")

            def __repr__(self):
                raise AssertionError("host display ran")

        old_tag = type("Wizard", (), {})
        new_tag = type("Wizard", (), {})
        agent = Host()
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=old_tag))
        old_house = _Safehouse(old_tag)
        new_house = _Safehouse(new_tag)
        root_house = _Safehouse(None)

        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            self.assertIs(_arrest_of(agent), arrest)
            self.assertIn(agent, old_house)
            self.assertIn(agent, root_house)
            self.assertNotIn(agent, new_house)
            self.assertEqual(len(old_house), 1)
            self.assertTrue(old_house)
            self.assertEqual(len(new_house), 0)
            self.assertFalse(new_house)
            self.assertIs(next(iter(old_house)), agent)
            self.assertIs(next(iter(root_house)), agent)

            _safehouse.pop(id(agent))
            self.assertIsNone(_arrest_of(agent))
            self.assertNotIn(agent, old_house)
            self.assertEqual(list(old_house), [])

    def test_entry_without_a_saved_run_is_not_an_arrest(self) -> None:
        agent = object()
        arrest = _Arrest(agent)
        house = _Safehouse(None)

        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            self.assertIsNone(_arrest_of(agent))
            self.assertNotIn(agent, house)
            self.assertEqual(list(house), [])
            self.assertEqual(len(house), 0)
            self.assertFalse(house)

            arrest.runs.append(SimpleNamespace(tag=object()))
            self.assertIs(_arrest_of(agent), arrest)
            self.assertIn(agent, house)
            self.assertEqual(len(house), 1)
            self.assertTrue(house)

    def test_walk_rechecks_custody_at_each_saved_turn(self) -> None:
        origin = type("Origin", (), {})
        first, second = object(), object()
        first_arrest, second_arrest = _Arrest(first), _Arrest(second)
        first_arrest.runs.append(SimpleNamespace(tag=origin))
        second_arrest.runs.append(SimpleNamespace(tag=origin))
        house = _Safehouse(origin)

        with patch.dict(
                _safehouse,
                {id(first): first_arrest, id(second): second_arrest},
                clear=True,
                ):
            walk = iter(house)
            self.assertIs(next(walk), first)
            _safehouse.pop(id(second))
            with self.assertRaises(StopIteration):
                next(walk)

    def test_length_and_truth_survive_changes_during_the_query(self) -> None:
        origin = type("Origin", (), {})
        first, second, third = object(), object(), object()
        entries = {id(item): _Arrest(item) for item in (first, second, third)}
        for arrest in entries.values():
            arrest.runs.append(SimpleNamespace(tag=origin))
        house = _Safehouse(origin)

        def Change_On_Length(self, arrest):
            _safehouse.pop(id(third), None)
            return True

        with patch.dict(_safehouse, entries, clear=True):
            with patch.object(_Safehouse, "_keeps", Change_On_Length):
                self.assertEqual(len(house), 2)

        def Change_On_Truth(self, arrest):
            if arrest.agent is first:
                _safehouse.pop(id(third), None)
                return False
            return arrest.agent is second

        with patch.dict(_safehouse, entries, clear=True):
            with patch.object(_Safehouse, "_keeps", Change_On_Truth):
                self.assertTrue(house)

    def test_copied_context_cannot_reopen_a_closed_rip_door(self) -> None:
        agent = object()
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=object()))

        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            self.assertFalse(_may_act(agent))
            door = _rip_door(agent)
            door.__enter__()
            copied = copy_context()
            self.assertTrue(_may_act(agent))
            self.assertTrue(copied.run(_may_act, agent))

            copied.run(door.__exit__, None, None, None)
            self.assertFalse(_may_act(agent))
            self.assertFalse(copied.run(_may_act, agent))

    def test_nested_rip_doors_keep_permissions_separate(self) -> None:
        first, second = object(), object()
        arrests = (_Arrest(first), _Arrest(second))
        for arrest in arrests:
            arrest.runs.append(SimpleNamespace(tag=object()))

        with patch.dict(
                _safehouse,
                {id(arrest.agent): arrest for arrest in arrests},
                clear=True,
                ):
            with _rip_door(first):
                self.assertTrue(_may_act(first))
                self.assertFalse(_may_act(second))
                with self.assertRaisesRegex(RuntimeError, "stop"):
                    with _rip_door(second):
                        self.assertTrue(_may_act(first))
                        self.assertTrue(_may_act(second))
                        raise RuntimeError("stop")
                self.assertTrue(_may_act(first))
                self.assertFalse(_may_act(second))
            self.assertFalse(_may_act(first))

    def test_held_lazy_sources_are_deduplicated_by_identity(self) -> None:
        agent = object()
        source = object()
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=object()))

        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            _hold_lazy_result(agent, source)
            _hold_lazy_result(agent, source)
            self.assertEqual(len(arrest.lazy), 1)
            self.assertIs(arrest.lazy[0], source)

    def test_late_lazy_parking_survives_cleared_module_globals(self) -> None:
        agent = object()
        source = object()
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=object()))
        lookup = _arrest_of
        park = _hold_lazy_result

        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            with patch("TopKit.arrest._safehouse", None):
                with patch("TopKit.arrest._arrest_of", None):
                    self.assertIs(lookup(agent), arrest)
                    park(agent, source)
        self.assertIs(arrest.lazy[0], source)


if __name__ == "__main__":
    unittest.main()
