"""Ordinary Gains still pass the whole Gate before any builder runs."""

import unittest

from TopKit import (Record, Tag, TagCompositionError, TagResolutionError, Tool,
                    Underlay)


class Host:
    pass


class GainingPreflightTests(unittest.TestCase):
    def test_a_late_host_property_or_slot_refuses_before_earlier_builders(self):
        class PropertyHost:
            @property
            def occupied(self):
                return "host"

        class SlotHost:
            __slots__ = ("occupied", "__dict__", "__weakref__")

        for host_type in (PropertyHost, SlotHost):
            with self.subTest(host=host_type):
                built = []

                class Arriving(Tag):
                    @Record
                    def earlier(agent):
                        built.append("earlier")
                        return 1

                    @Record
                    def occupied(agent):
                        return "replacement"

                agent = host_type()
                with self.assertRaises(TagCompositionError):
                    Arriving(agent)
                self.assertEqual(built, [])
                self.assertNotIn("earlier", agent.__dict__)
                self.assertNotIn(agent, Arriving)

    def test_a_missing_underlay_refuses_before_earlier_builders(self):
        built = []

        class Arriving(Tag):
            @Record
            def earlier(agent):
                built.append("earlier")
                return 1

            @Underlay
            def Work(agent, underlay):
                return underlay()

        agent = Host()
        with self.assertRaises(TagResolutionError):
            Arriving(agent)
        self.assertEqual(built, [])
        self.assertNotIn("earlier", agent.__dict__)
        self.assertNotIn(agent, Arriving)

    def test_a_valid_underlay_composes_and_is_visible_to_the_next_builder(self):
        class WorkingHost:
            def Work(self):
                return 3

        class Arriving(Tag):
            @Underlay
            def Work(agent, underlay):
                return underlay() + 2

            @Record
            def result(agent):
                return agent.Work()

        agent = WorkingHost()
        Arriving(agent)
        self.assertEqual(agent.result, 5)
        self.assertEqual(agent.Work(), 5)

    def test_independent_kind_conflicts_refuse_before_earlier_builders(self):
        for existing_record in (False, True):
            with self.subTest(existing_record=existing_record):
                built = []

                def previous(agent):
                    return "previous"

                class Existing(Tag):
                    occupied = Record(previous) if existing_record else previous

                def replacement(agent):
                    return "replacement"

                class Arriving(Tag):
                    @Record
                    def earlier(agent):
                        built.append("earlier")
                        return 1

                    occupied = replacement if existing_record else Record(replacement)

                agent = Host()
                Existing(agent)
                with self.assertRaises(TagCompositionError):
                    Arriving(agent)
                self.assertEqual(built, [])
                self.assertNotIn("earlier", agent.__dict__)
                self.assertIn(agent, Existing)
                self.assertNotIn(agent, Arriving)
                value = agent.occupied if existing_record else agent.occupied()
                self.assertEqual(value, "previous")

    def test_late_record_metadata_failure_still_precedes_earlier_builders(self):
        class Builder:
            armed = False

            def __getattribute__(self, name):
                if name == "__func__" and object.__getattribute__(self, "armed"):
                    raise RuntimeError("metadata unavailable")
                return object.__getattribute__(self, name)

            def __call__(self, agent):
                return "value"

        builder = Record(Builder())
        built = []

        class Arriving(Tag):
            @Record
            def earlier(agent):
                built.append("earlier")
                return 1

            later = builder

        warm = Host()
        Arriving(warm)
        built.clear()
        builder.armed = True

        agent = Host()
        with self.assertRaisesRegex(RuntimeError, "metadata unavailable"):
            Arriving(agent)
        self.assertEqual(built, [])
        self.assertNotIn("earlier", agent.__dict__)
        self.assertNotIn(agent, Arriving)

    def test_a_refused_overlay_preserves_the_existing_tool_value_and_rule(self):
        class Sword:
            pass

        class Equipped(Tag):
            @Tool(Sword)
            def weapon(agent, *, weapon):
                return weapon

        built = []

        class Arriving(Equipped):
            @Record
            def weapon(agent):
                built.append("replacement")
                return None

            @Underlay
            def Missing(agent, underlay):
                return underlay()

        agent = Host()
        sword = Sword()
        Equipped(agent, weapon=sword)

        with self.assertRaises(TagResolutionError):
            Arriving(agent)
        self.assertEqual(built, [])
        self.assertIs(agent.weapon, sword)
        self.assertIn(agent, Equipped)
        self.assertNotIn(agent, Arriving)
        with self.assertRaises(TagCompositionError):
            agent.weapon = object()
        self.assertIs(agent.weapon, sword)


if __name__ == "__main__":
    unittest.main()
