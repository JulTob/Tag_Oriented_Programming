"""A state-free copy of an Agent runtime still prepares as a fresh host."""

import unittest

from TopKit import Pre, Tag, TagCompositionError, TagPreconditionError, Tags
from TopKit.state import _state_of


class RuntimeClonePreparationTests(unittest.TestCase):
    def test_clone_normalization_is_internal_and_actualization_asks_the_host_once(self):
        changes = []

        class Host:
            def __setattr__(self, name, value):
                if name == "__class__":
                    changes.append(value)
                object.__setattr__(self, name, value)

        class Role(Tag):
            pass

        first = Host()
        Role(first)
        clone = type(first)()
        changes.clear()

        Role(clone)

        self.assertEqual(len(changes), 1)
        self.assertIs(changes[0], type(clone))
        self.assertIn(clone, Role)
        self.assertIn(first, Role)

    def test_a_clone_host_refusal_restores_its_class_dictionary_and_slots(self):
        armed = False

        class Host:
            __slots__ = ("kept", "__dict__", "__weakref__")

            def __init__(self):
                self.kept = 80
                self.marker = "original"

            def __setattr__(self, name, value):
                if name == "__class__" and armed:
                    object.__setattr__(self, "kept", 0)
                    object.__setattr__(self, "marker", "provisional")
                    object.__setattr__(self, name, value)
                    raise RuntimeError("explicit refusal")
                object.__setattr__(self, name, value)

        class Role(Tag):
            pass

        first = Host()
        Role(first)
        clone = type(first)()
        original_class = type(clone)
        original_dictionary = vars(clone)
        armed = True

        with self.assertRaises(TagCompositionError) as raised:
            Role(clone)

        self.assertIsInstance(raised.exception.__cause__, RuntimeError)
        self.assertIs(type(clone), original_class)
        self.assertIs(vars(clone), original_dictionary)
        self.assertEqual(vars(clone), {"marker": "original"})
        self.assertEqual(clone.kept, 80)
        self.assertIsNone(_state_of(clone))
        self.assertEqual(Tags(clone), ())
        self.assertNotIn(clone, Role[:])
        self.assertIn(first, Role)

    def test_a_refused_gate_restores_a_clones_original_representation(self):
        changes = []

        class Host:
            def __setattr__(self, name, value):
                if name == "__class__":
                    changes.append(value)
                object.__setattr__(self, name, value)

        class Role(Tag):
            pass

        class Refused(Tag):
            @Pre
            def Gate(agent):
                return False

        first = Host()
        Role(first)
        clone = type(first)()
        original_class = type(clone)
        original_dictionary = vars(clone)
        changes.clear()

        with self.assertRaises(TagPreconditionError):
            Refused(clone)

        self.assertEqual(changes, [])
        self.assertIs(type(clone), original_class)
        self.assertIs(vars(clone), original_dictionary)
        self.assertEqual(vars(clone), {})
        self.assertIsNone(_state_of(clone))
        self.assertEqual(Tags(clone), ())
        self.assertNotIn(clone, Refused[:])
        self.assertNotIn(clone, Role[:])


if __name__ == "__main__":
    unittest.main()
