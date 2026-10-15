"""A deleted public Report reveals the Host's earlier Python binding."""

from __future__ import annotations

import unittest

from TopKit import Action
from TopKit import Delete
from TopKit import Public
from TopKit import Report
from TopKit import Secret
from TopKit import Tag


class ReportHostFallbackTests(unittest.TestCase):
    def test_class_value_and_method_reappear_with_normal_instance_precedence(self) -> None:
        class Host:
            value = None

            def Work(self):
                return "host work"

        class Service(Tag):
            @Public
            @Report
            def value(tag):
                return "report value"

            @Public
            @Report
            def Work(tag):
                return "report work"

        agent = Host()
        Service(agent)
        self.assertEqual(agent.value, "report value")
        self.assertTrue("value" @ agent)

        del Service.value
        del Service.Work

        self.assertIsNone(agent.value)
        self.assertEqual(agent.Work(), "host work")
        self.assertTrue("value" @ agent)
        self.assertTrue("Work" @ agent)

        agent.value = False
        self.assertIs(agent.value, False)
        del agent.value
        self.assertIsNone(agent.value)
        with self.assertRaises(AttributeError):
            del agent.value

    def test_host_property_keeps_its_get_set_and_delete_rules(self) -> None:
        class Host:
            def __init__(self):
                self._value = "host"
                self.reads = 0

            @property
            def value(self):
                self.reads += 1
                return self._value

            @value.setter
            def value(self, new):
                self._value = new

            @value.deleter
            def value(self):
                self._value = "deleted"

        class Service(Tag):
            @Public
            @Report
            def value(tag):
                return "report"

        agent = Host()
        Service(agent)
        del Service.value

        self.assertTrue("value" @ agent)
        self.assertEqual(agent.reads, 0)
        self.assertEqual(agent.value, "host")
        agent.value = "changed"
        self.assertEqual(agent.value, "changed")
        del agent.value
        self.assertEqual(agent.value, "deleted")

    def test_host_data_descriptor_precedes_a_retained_action(self) -> None:
        class Host:
            @property
            def Work(self):
                return "host property"

        class Gained(Tag):
            @Action
            def Work(agent):
                return "TOP Action"

        class Service(Tag):
            @Public
            @Report
            def Work(tag):
                return "report"

        agent = Host()
        Gained(agent)
        self.assertEqual(agent.Work, "host property")
        Service(agent)
        del Service.Work
        self.assertEqual(agent.Work, "host property")
        self.assertTrue("Work" @ agent)
        with self.assertRaises(AttributeError):
            agent.Work = "forbidden"
        with self.assertRaises(AttributeError):
            del agent.Work

    def test_explicit_delete_and_secret_still_hide_a_host_binding(self) -> None:
        class Host:
            value = "host"

        class Removed(Tag):
            @Delete
            def value(agent):
                pass

        class Service(Tag):
            @Public
            @Report
            def value(tag):
                return "report"

        agent = Host()
        Removed(agent)
        Service(agent)
        del Service.value
        with self.assertRaises(AttributeError):
            agent.value
        self.assertFalse("value" @ agent)

        class Hidden(Tag):
            @Secret
            @Action
            def value(agent):
                return "secret"

        other = Host()
        Hidden(other)
        Service(other)
        with self.assertRaises(AttributeError):
            other.value
        self.assertFalse("value" @ other)

    def test_secret_action_still_uses_its_binding_inside_composition(self) -> None:
        class Host:
            @property
            def Work(self):
                return "host property"

        class Hidden(Tag):
            @Secret
            @Action
            def Work(agent):
                return "secret action"

            @Action
            def Probe(agent):
                return agent.Work()

        class Service(Tag):
            @Public
            @Report
            def Work(tag):
                return "report"

        agent = Host()
        Hidden(agent)
        Service(agent)
        del Service.Work

        with self.assertRaises(AttributeError):
            agent.Work
        self.assertFalse("Work" @ agent)
        self.assertEqual(agent.Probe(), "secret action")


if __name__ == "__main__":
    unittest.main()
