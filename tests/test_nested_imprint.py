"""Imprints own nested failures after their Tag has committed."""

import unittest

from TopKit import (Imprint, Pre, Rip, Tag, TagCompositionError,
                    TagImprintError, TagPreconditionError)


class Host:
    pass


class NestedImprintTests(unittest.TestCase):
    def test_nested_gate_failure_is_owned_by_outer_imprint_and_cleanup_survives(self):
        events = []

        class Nested(Tag):
            @Pre
            def Refuse(agent):
                return False

        class Outer(Tag):
            @Imprint
            def Acquire(agent):
                events.append("acquire")

            @Imprint
            def Continue(agent):
                Nested(agent)

            @Rip
            def Release(agent):
                events.append("release")

        agent = Host()
        with self.assertRaises(TagImprintError.Continue) as caught:
            Outer(agent)
        self.assertIsInstance(caught.exception.__cause__, TagPreconditionError.Refuse)
        self.assertIn(agent, Outer[:])
        self.assertTrue(isinstance(agent, Outer))
        self.assertNotIn(agent, Nested[:])
        del Outer[agent]
        self.assertEqual(events, ["acquire", "release"])

    def test_nested_composition_error_is_owned_by_outer_imprint(self):
        class Outer(Tag):
            @Imprint
            def Work(agent):
                raise TagCompositionError("nested refusal")

        agent = Host()
        with self.assertRaises(TagImprintError.Work) as caught:
            Outer(agent)
        self.assertIsInstance(caught.exception.__cause__, TagCompositionError)
        self.assertIn(agent, Outer[:])

