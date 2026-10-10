"""Host refusals at the first Tagging stay TOP composition failures."""

from __future__ import annotations

import unittest
from typing import Callable

from TopKit import Action
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import Tags


class HostActualizationTests(unittest.TestCase):
    def setUp(self) -> None:
        class Role(Tag):
            @Action
            def Signal(agent) -> str:
                return "tagged"

        self.Role = Role

    def refuse(
            self,
            target: object,
            host_type: type,
            namespace_of: Callable[[object], dict[str, object]] = vars,
            ) -> TagCompositionError:
        entry_namespace = dict(namespace_of(target))

        with self.assertRaises(TagCompositionError) as raised:
            self.Role(target)

        self.assertIs(type(target), host_type)
        self.assertEqual(dict(namespace_of(target)), entry_namespace)
        self.assertEqual(Tags(target), ())
        self.assertNotIn(target, self.Role)
        self.assertEqual(tuple(self.Role[:]), ())
        self.assertFalse(hasattr(target, "Signal"))

        return raised.exception

    def test_a_raising_class_hook_is_normalized_and_rolled_back(self) -> None:
        class RestrictiveHost:
            def __init__(self) -> None:
                self.kept = "host state"

            def __setattr__(self, name: str, value: object) -> None:
                if name == "__class__":
                    object.__setattr__(self, "leaked", "provisional")
                    object.__setattr__(self, name, value)
                    raise RuntimeError("runtime type changes are forbidden")

                object.__setattr__(self, name, value)

        error = self.refuse(RestrictiveHost(), RestrictiveHost)

        self.assertIsInstance(error.__cause__, RuntimeError)

    def test_rollback_restores_the_type_before_reading_its_namespace(self) -> None:
        class PoisonType:
            @property
            def __dict__(self) -> None:
                raise RuntimeError("poisoned namespace")

        class RestrictiveHost:
            def __init__(self) -> None:
                self.kept = "host state"

            def __setattr__(self, name: str, value: object) -> None:
                if name == "__class__":
                    object.__setattr__(self, name, PoisonType)
                    raise RuntimeError("installed the wrong type")

                object.__setattr__(self, name, value)

        error = self.refuse(RestrictiveHost(), RestrictiveHost)

        self.assertIsInstance(error.__cause__, RuntimeError)

    def test_a_silently_ignored_class_change_is_refused(self) -> None:
        class SilentHost:
            def __init__(self) -> None:
                self.kept = "host state"

            def __setattr__(self, name: str, value: object) -> None:
                if name != "__class__":
                    object.__setattr__(self, name, value)

        error = self.refuse(SilentHost(), SilentHost)

        self.assertIsNone(error.__cause__)

    def test_a_host_cannot_erase_agent_state_during_actualization(self) -> None:
        class ErasingHost:
            def __init__(self) -> None:
                self.kept = "host state"

            def __setattr__(self, name: str, value: object) -> None:
                if name == "__class__":
                    object.__setattr__(self, name, value)
                    object.__getattribute__(self, "__dict__").clear()
                    return

                object.__setattr__(self, name, value)

        error = self.refuse(ErasingHost(), ErasingHost)

        self.assertIsNone(error.__cause__)

    def test_a_rejected_runtime_subclass_is_a_composition_failure(self) -> None:
        class ClosedHost:
            def __init_subclass__(cls, **kwargs: object) -> None:
                raise RuntimeError("runtime subclasses are forbidden")

        error = self.refuse(ClosedHost(), ClosedHost)

        self.assertIsInstance(error.__cause__, RuntimeError)

    def test_a_substituting_metaclass_cannot_fake_the_runtime_type(self) -> None:
        class SubstitutingMetaclass(type):
            armed = False

            def __new__(metaclass, name, bases, namespace):
                if metaclass.armed:
                    return bases[0]

                return super().__new__(metaclass, name, bases, namespace)

        class SubstitutingHost(metaclass=SubstitutingMetaclass):
            pass

        target = SubstitutingHost()
        SubstitutingMetaclass.armed = True
        error = self.refuse(target, SubstitutingHost)

        self.assertIsNone(error.__cause__)

    def test_a_metaclass_cannot_strip_requested_runtime_machinery(self) -> None:
        class StrippingMetaclass(type):
            armed = False

            def __new__(metaclass, name, bases, namespace):
                if metaclass.armed:
                    namespace.pop("_TOPKIT_HOST_TYPE", None)
                    namespace.pop("__getattr__", None)

                return super().__new__(metaclass, name, bases, namespace)

        class StrippingHost(metaclass=StrippingMetaclass):
            pass

        target = StrippingHost()
        StrippingMetaclass.armed = True
        error = self.refuse(target, StrippingHost)

        self.assertIsNone(error.__cause__)

    def test_a_disposable_dict_view_cannot_hold_agent_state(self) -> None:
        class MisleadingHost:
            __slots__ = ("kept", "__weakref__")

            @property
            def __dict__(self) -> dict[str, object]:
                return {}

        target = MisleadingHost()
        target.kept = "host state"
        error = self.refuse(target, MisleadingHost)

        self.assertIsNone(error.__cause__)
        self.assertEqual(target.kept, "host state")

    def test_a_persistent_dict_shadow_is_not_instance_storage(self) -> None:
        class Storage:
            __slots__ = ("fake", "kept", "__dict__", "__weakref__")

        physical_namespace = Storage.__dict__["__dict__"]

        class MisleadingHost(Storage):
            __slots__ = ()

            def __init__(self) -> None:
                self.fake: dict[str, object] = {}
                self.kept = "host state"

            @property
            def __dict__(self) -> dict[str, object]:
                return self.fake

        target = MisleadingHost()
        entry_physical = dict(physical_namespace.__get__(target))
        error = self.refuse(target, MisleadingHost)

        self.assertIsNone(error.__cause__)
        self.assertEqual(target.kept, "host state")
        self.assertEqual(dict(physical_namespace.__get__(target)), entry_physical)


if __name__ == "__main__":
    unittest.main()
