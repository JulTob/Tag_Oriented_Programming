"""Host refusals at the first Tagging stay TOP composition failures."""

from __future__ import annotations

import unittest
import weakref
from dataclasses import dataclass
from dataclasses import FrozenInstanceError
from dataclasses import replace
from typing import Callable

from TopKit import Action
from TopKit import Constant
from TopKit import Flag
from TopKit import Imprint
from TopKit import Pin
from TopKit import Pre
from TopKit import Record
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

    def test_string_targets_are_refused_before_a_gate_or_actualization(self) -> None:
        class Text(str):
            pass

        visits: list[object] = []

        class Named(Tag):
            @Pre
            def Ready(agent) -> bool:
                visits.append(agent)
                return True

        for target in ("bare", Text("subclass")):
            with self.subTest(host_type=type(target)):
                host_type = type(target)
                namespace = dict(vars(target)) if type(target) is Text else None
                if type(target) is Text:
                    self.assertIs(weakref.ref(target)(), target)

                with self.assertRaisesRegex(TagCompositionError, "string Target"):
                    Named(target)

                self.assertIs(type(target), host_type)
                if namespace is not None:
                    self.assertEqual(vars(target), namespace)
                self.assertEqual(visits, [])
                self.assertEqual(Tags(target), ())
                self.assertNotIn(target, Named[:])
                self.assertNotIn(target, Named)
                self.assertNotIsInstance(target, Named)

    def test_string_subclass_remains_a_keyword_probe_on_a_tag(self) -> None:
        class Text(str):
            __hash__ = None

        class Named(Tag):
            pass

        @Pin
        @Flag("word")
        class Keyword_Pin(Tag):
            pass

        Keyword_Pin(Named)

        self.assertIn("word", Named)
        self.assertIn(Text("word"), Named)
        self.assertNotIn(Text("other"), Named)

        probe = Text("word")
        with self.assertRaisesRegex(TagCompositionError, "string Target"):
            Named(probe)

        self.assertIn(probe, Named)           # still a word, never a member
        self.assertNotIn(probe, Named[:])
        self.assertNotIsInstance(probe, Named)

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

    def test_a_frozen_dataclass_can_gain_records_and_train_in_place(self) -> None:
        @dataclass(frozen=True)
        class FrozenHost:
            kept: str = "host state"

        class Trained(Tag):
            @Record
            def gained(agent) -> list[str]:
                return []

            @Imprint
            def Train(agent) -> None:
                agent.gained.append(agent.kept)

        target = FrozenHost()
        identity, original_hash = id(target), hash(target)

        self.assertIs(self.Role(target), target)
        Trained(target)

        self.assertEqual(id(target), identity)
        self.assertEqual(hash(target), original_hash)
        self.assertIsInstance(target, FrozenHost)
        self.assertEqual(target.Signal(), "tagged")
        self.assertEqual(target.gained, ["host state"])
        self.assertIn(target, self.Role)
        self.assertIn(target, Trained)

        with self.assertRaises(FrozenInstanceError):
            target.kept = "changed"

        with self.assertRaises(FrozenInstanceError):
            del target.kept

    def test_frozen_dataclass_inheritance_preserves_every_frozen_field(self) -> None:
        @dataclass(frozen=True)
        class FrozenBase:
            first: int = 1

        @dataclass(frozen=True)
        class FrozenHost(FrozenBase):
            second: int = 2

        target = FrozenHost()
        self.Role(target)

        self.assertEqual(target.Signal(), "tagged")
        for name in ("first", "second"):
            with self.subTest(name=name):
                with self.assertRaises(FrozenInstanceError):
                    setattr(target, name, 0)

                with self.assertRaises(FrozenInstanceError):
                    delattr(target, name)

    def test_a_frozen_host_can_be_ripped_and_retagged(self) -> None:
        @dataclass(frozen=True)
        class FrozenHost:
            kept: int = 1

        target = FrozenHost()
        self.Role(target)
        del self.Role[target]
        self.assertNotIn(target, self.Role)
        self.Role(target)

        self.assertIn(target, self.Role)
        self.assertEqual(target.Signal(), "tagged")
        with self.assertRaises(FrozenInstanceError):
            target.kept = 2

    def test_a_slotted_frozen_dataclass_with_host_storage_can_be_tagged(self) -> None:
        class Storage:
            pass

        @dataclass(frozen=True, slots=True)
        class FrozenHost(Storage):
            kept: int = 1

        target = FrozenHost()
        self.Role(target)

        self.assertEqual(target.Signal(), "tagged")
        self.assertIn(target, self.Role)
        with self.assertRaises(FrozenInstanceError):
            target.kept = 2
        with self.assertRaises(FrozenInstanceError):
            del target.kept

    def test_a_slotted_frozen_dataclass_still_respects_base_class_write_hooks(self) -> None:
        class RestrictiveStorage:
            def __setattr__(self, name: str, value: object) -> None:
                if name == "__class__":
                    object.__setattr__(self, "leaked", "provisional")
                    raise RuntimeError("runtime type changes are forbidden")

                object.__setattr__(self, name, value)

        @dataclass(frozen=True, slots=True)
        class FrozenHost(RestrictiveStorage):
            kept: int = 1

        target = FrozenHost()
        error = self.refuse(target, FrozenHost)

        self.assertIsInstance(error.__cause__, RuntimeError)
        self.assertEqual(target.kept, 1)

    def test_descendants_of_a_slotted_frozen_dataclass_can_be_tagged(self) -> None:
        class Storage:
            pass

        @dataclass(frozen=True, slots=True)
        class FrozenBase(Storage):
            kept: int = 1

        @dataclass(frozen=True)
        class FrozenShape(FrozenBase):
            extra: int = 2

        class PlainShape(FrozenBase):
            pass

        for host_type in (FrozenShape, PlainShape):
            with self.subTest(host_type=host_type):
                target = host_type()
                self.Role(target)

                self.assertEqual(target.Signal(), "tagged")
                self.assertIn(target, self.Role)
                with self.assertRaises(FrozenInstanceError):
                    target.kept = 2
                with self.assertRaises(FrozenInstanceError):
                    del target.kept

    def test_replacing_a_frozen_agent_builds_an_untagged_host(self) -> None:
        @dataclass(frozen=True)
        class FrozenHost:
            kept: int = 1

        first = FrozenHost()
        self.Role(first)
        second = replace(first, kept=2)
        self.assertEqual(Tags(second), ())
        self.assertNotIn(second, self.Role)

        self.Role(second)

        self.assertEqual(second.kept, 2)
        self.assertEqual(second.Signal(), "tagged")
        self.assertIn(first, self.Role)
        self.assertIn(second, self.Role)
        with self.assertRaises(FrozenInstanceError):
            second.kept = 3

    def test_constant_bindings_do_not_thaw_a_frozen_hosts_fields(self) -> None:
        @dataclass(frozen=True)
        class FrozenHost:
            kept: int = 1

        class Locked(Tag):
            @Constant
            @Record
            def gained(agent) -> int:
                return 2

        target = FrozenHost()
        Locked(target)

        self.assertEqual(target.gained, 2)
        with self.assertRaises(TagCompositionError):
            target.gained = 3
        with self.assertRaises(TagCompositionError):
            del target.gained
        with self.assertRaises(FrozenInstanceError):
            target.kept = 3
        with self.assertRaises(FrozenInstanceError):
            del target.kept

    def test_a_frozen_dataclass_still_respects_its_bases_class_write_hook(self) -> None:
        class RestrictiveBase:
            def __setattr__(self, name: str, value: object) -> None:
                if name == "__class__":
                    object.__setattr__(self, "leaked", "provisional")
                    raise RuntimeError("runtime type changes are forbidden")

                object.__setattr__(self, name, value)

        @dataclass(frozen=True)
        class FrozenHost(RestrictiveBase):
            kept: str = "host state"

        error = self.refuse(FrozenHost(), FrozenHost)

        self.assertIsInstance(error.__cause__, RuntimeError)

    def test_a_replaced_frozen_dataclass_setter_is_not_bypassed(self) -> None:
        @dataclass(frozen=True)
        class FrozenHost:
            kept: str = "host state"

        def Custom_Setter(self, name: str, value: object) -> None:
            if name == "__class__":
                object.__setattr__(self, "leaked", "provisional")
                raise FrozenInstanceError("explicit host refusal")

            object.__setattr__(self, name, value)

        FrozenHost.__setattr__ = Custom_Setter
        error = self.refuse(FrozenHost(), FrozenHost)

        self.assertIsInstance(error.__cause__, FrozenInstanceError)


if __name__ == "__main__":
    unittest.main()
