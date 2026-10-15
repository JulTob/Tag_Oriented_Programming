"""A Rip trained Agent's Host reads and writes obey Safehouse custody."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from TopKit import Pin
from TopKit import Rip
from TopKit import Tag
from TopKit import TagArrestedAccessError
from TopKit.arrest import _Arrest
from TopKit.arrest import _rip_door
from TopKit.arrest import _safehouse


class SafehouseReadWriteTests(unittest.TestCase):
    def test_host_getter_cannot_return_after_catching_its_own_arrest(self) -> None:
        class Host:
            def __init__(self):
                self.value = "secret"
                self.armed = False

            def __getattribute__(self, name):
                if name == "value" and object.__getattribute__(self, "armed"):
                    arrest = _Arrest(self)
                    arrest.runs.append(SimpleNamespace(tag=Role))
                    _safehouse[id(self)] = arrest
                    try:
                        self.Work()
                    except TagArrestedAccessError:
                        pass
                return object.__getattribute__(self, name)

        class Role(Tag):
            def Work(agent):
                return "work"

            @Rip
            def Leave(agent):
                pass

        agent = Host()
        Role(agent)
        with patch.dict(_safehouse, {}, clear=True):
            agent.armed = True
            with self.assertRaises(TagArrestedAccessError):
                _ = agent.value
            self.assertIn(agent, Role[...])

    def test_custody_identity_bypasses_a_host_class_descriptor(self) -> None:
        calls = []

        class Host:
            def __getattribute__(self, name):
                if name == "__class__":
                    calls.append("host class getter")
                    return str
                return object.__getattribute__(self, name)

        class Role(Tag):
            @Rip
            def Leave(agent):
                pass

        agent = Host()
        Role(agent)
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Role))
        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            before = len(calls)
            self.assertIs(agent.__class__, type(agent))
            self.assertEqual(len(calls), before)
            with self.assertRaises(TagArrestedAccessError):
                _ = agent.__dict__

    def test_hostile_str_subclass_cannot_fake_identity_exception(self) -> None:
        class Name(str):
            def __eq__(self, other):
                return other == "__class__"

            def __ne__(self, other):
                return False

        class Host:
            value = "secret"

        class Role(Tag):
            @Rip
            def Leave(agent):
                pass

        agent = Host()
        Role(agent)
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Role))
        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                getattr(agent, Name("value"))

    def test_host_writers_are_blocked_but_work_inside_rip_door(self) -> None:
        writes = []

        class Host:
            def __setattr__(self, name, value):
                writes.append(("set", name))
                object.__setattr__(self, name, value)

            def __delattr__(self, name):
                writes.append(("del", name))
                object.__delattr__(self, name)

        class Role(Tag):
            @Rip
            def Leave(agent):
                pass

        agent = Host()
        Role(agent)
        agent.value = 1
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Role))
        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            before = list(writes)
            with self.assertRaises(TagArrestedAccessError):
                agent.value = 2
            with self.assertRaises(TagArrestedAccessError):
                del agent.value
            self.assertEqual(writes, before)
            with _rip_door(agent):
                agent.value = 3
                del agent.value
            self.assertEqual(writes[-2:], [("set", "value"), ("del", "value")])

    def test_host_setter_cannot_report_success_after_arresting_itself(self) -> None:
        class Host:
            armed = False

            def __setattr__(self, name, value):
                if name == "value" and object.__getattribute__(self, "armed"):
                    arrest = _Arrest(self)
                    arrest.runs.append(SimpleNamespace(tag=Role))
                    _safehouse[id(self)] = arrest
                object.__setattr__(self, name, value)

        class Role(Tag):
            @Rip
            def Leave(agent):
                pass

        agent = Host()
        Role(agent)
        with patch.dict(_safehouse, {}, clear=True):
            agent.armed = True
            with self.assertRaises(TagArrestedAccessError):
                agent.value = 9
            self.assertIn(agent, Role[...])

    def test_frozen_host_with_rip_can_be_tagged(self) -> None:
        @dataclass(frozen=True)
        class Frozen:
            value: int

        class Role(Tag):
            @Rip
            def Leave(agent):
                pass

        agent = Frozen(5)
        Role(agent)
        self.assertEqual(agent.value, 5)
        self.assertIn(agent, Role[:])

    def test_pinned_tag_reads_and_writes_use_its_agent_gate(self) -> None:
        class Fighter(Tag):
            status = "active"

        @Pin
        class Registered(Tag):
            @Rip
            def Leave(tag):
                pass

        Registered(Fighter)
        arrest = _Arrest(Fighter)
        arrest.runs.append(SimpleNamespace(tag=Registered))
        with patch.dict(_safehouse, {id(Fighter): arrest}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                _ = Fighter.status
            with self.assertRaises(TagArrestedAccessError):
                Fighter.status = "changed"
            with _rip_door(Fighter):
                self.assertEqual(Fighter.status, "active")
                Fighter.status = "clearing"
            with self.assertRaises(TagArrestedAccessError):
                _ = Fighter.status
        self.assertEqual(Fighter.status, "clearing")

    def test_read_gate_survives_rip_and_later_unrelated_tagging(self) -> None:
        class Host:
            value = "kept"

        class Trained(Tag):
            @Rip
            def Leave(agent):
                pass

        class Later(Tag):
            pass

        agent = Host()
        Trained(agent)
        del Trained[agent]
        Later(agent)
        arrest = _Arrest(agent)
        arrest.runs.append(SimpleNamespace(tag=Trained))
        with patch.dict(_safehouse, {id(agent): arrest}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                _ = agent.value


if __name__ == "__main__":
    unittest.main()
