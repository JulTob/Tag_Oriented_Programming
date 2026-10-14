"""Plain objects made from Agent runtime types keep native host truth."""
import unittest

from TopKit import Tag


class HostTruthRegressions(unittest.TestCase):
    def test_mixed_inheritance_keeps_actual_mro(self):
        class Host:
            def __len__(self):
                return 1

        class Member(Tag):
            pass

        first = Host()
        Member(first)

        class Empty(Host):
            def __len__(self):
                return 0

        class Derived(type(first), Empty):
            pass

        plain = Derived()
        self.assertEqual(len(plain), 0)
        self.assertFalse(plain)

    def test_descriptor_binding_ignores_descriptor_metaclass_lookup(self):
        class HiddenGetter(type):
            def __getattribute__(cls, name):
                if name == "__get__":
                    raise AttributeError(name)
                return type.__getattribute__(cls, name)

        class Length(metaclass=HiddenGetter):
            def __get__(self, instance, owner):
                return lambda: 0

            def __call__(self):
                return 1

        class Host:
            __len__ = Length()

        class Member(Tag):
            pass

        first = Host()
        self.assertFalse(first)
        Member(first)
        self.assertFalse(type(first)())

    def test_host_namespace_lookup_cannot_hide_real_length(self):
        class HiddenNamespace(type):
            def __getattribute__(cls, name):
                if name == "__dict__":
                    namespace = dict(type.__getattribute__(cls, name))
                    namespace.pop("__len__", None)
                    return namespace
                return type.__getattribute__(cls, name)

        class Host(metaclass=HiddenNamespace):
            def __len__(self):
                return 0

        class Member(Tag):
            pass

        first = Host()
        self.assertFalse(first)
        Member(first)
        self.assertFalse(type(first)())

    def test_class_equality_does_not_suppress_host_length(self):
        class EqualTypes(type):
            def __hash__(cls):
                return 1

            def __eq__(cls, other):
                return True

        class Host(metaclass=EqualTypes):
            def __len__(self):
                return 0

        class Member(Tag):
            pass

        first = Host()
        self.assertFalse(first)
        Member(first)
        self.assertFalse(type(first)())


if __name__ == "__main__":
    unittest.main()
