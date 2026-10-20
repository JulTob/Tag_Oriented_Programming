"""The opt-in Host source guard catches methods saved before Tagging."""

from __future__ import annotations

from dataclasses import dataclass
from gc import collect
from inspect import signature
from types import SimpleNamespace
from typing import Any
import unittest
from unittest.mock import patch
from weakref import ref

from TopKit import GuardedHost
from TopKit import Rip
from TopKit import Tag
from TopKit import TagArrestedAccessError
from TopKit import TagCompositionError
from TopKit import TagDeclarationError
from TopKit.arrest import _Arrest
from TopKit.arrest import _rip_door
from TopKit.arrest import _safehouse


class GuardedHostTests(unittest.TestCase):
    def test_method_saved_before_tagging_obeys_later_arrest(self) -> None:
        class Base:
            def __getitem__(self, key: str) -> str:
                return key.upper()

        @GuardedHost
        class Vault(Base):
            def __getitem__(self, key: str) -> str:
                return super().__getitem__(key) + "!"

        class Custody(Tag):
            @Rip
            def Leave(agent):
                pass

        vault = Vault()
        host_type = type(vault)
        host_mro = Vault.__mro__
        saved = vault.__getitem__
        self.assertIs(saved.__self__, vault)
        self.assertIs(saved.__func__.__wrapped__,
                      Vault.__dict__["__getitem__"].__wrapped__)
        self.assertEqual(saved, vault.__getitem__)
        self.assertEqual(hash(saved), hash(vault.__getitem__))
        self.assertEqual(str(signature(saved)), "(key: 'str') -> 'str'")
        self.assertEqual(saved("a"), "A!")

        Custody(vault)
        arrest = _Arrest(vault)
        arrest.runs.append(SimpleNamespace(tag=Custody))
        with patch.dict(_safehouse, {id(vault): arrest}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                saved("b")
            with self.assertRaises(TagArrestedAccessError):
                vault["b"]
            with _rip_door(vault):
                self.assertEqual(saved("b"), "B!")

        self.assertIs(vault.__class__.__mro__[1], host_type)
        self.assertEqual(Vault.__mro__, host_mro)

    def test_each_python_base_needs_its_own_mark(self) -> None:
        class Base:
            def read(self):
                return "base"

        @GuardedHost
        class Vault(Base):
            def signal(self):
                return "vault"

        class Custody(Tag):
            @Rip
            def Leave(agent):
                pass

        vault = Vault()
        saved_base = vault.read
        saved_own = vault.signal
        Custody(vault)
        arrest = _Arrest(vault)
        arrest.runs.append(SimpleNamespace(tag=Custody))
        with patch.dict(_safehouse, {id(vault): arrest}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                saved_own()
            # This exact boundary is why the opt-in declaration must also
            # be placed on every Python Base whose methods need custody.
            self.assertEqual(saved_base(), "base")

        GuardedHost(Base)
        guarded_base = vault.read
        with patch.dict(_safehouse, {id(vault): arrest}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                guarded_base()
            self.assertEqual(saved_base(), "base")

    def test_method_cannot_return_after_catching_its_own_arrest(self) -> None:
        @GuardedHost
        class Vault:
            def read(self):
                arrest = _Arrest(self)
                arrest.runs.append(SimpleNamespace(tag=object()))
                _safehouse[id(self)] = arrest
                try:
                    self.read()
                except TagArrestedAccessError:
                    pass
                return "secret"

        class Custody(Tag):
            @Rip
            def Leave(agent):
                pass

        vault = Vault()
        saved = vault.read
        Custody(vault)
        with patch.dict(_safehouse, {}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                saved()

    def test_lazy_method_returned_before_tagging_checks_each_resume(self) -> None:
        @GuardedHost
        class Vault:
            def steps(self):
                yield "first"
                yield "second"

        class Custody(Tag):
            @Rip
            def Leave(agent):
                pass

        vault = Vault()
        steps = vault.steps()
        Custody(vault)
        self.assertEqual(next(steps), "first")

        arrest = _Arrest(vault)
        arrest.runs.append(SimpleNamespace(tag=Custody))
        with patch.dict(_safehouse, {id(vault): arrest}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                next(steps)
            with _rip_door(vault):
                self.assertEqual(next(steps), "second")

    def test_captured_lazy_method_cannot_yield_after_self_arrest(self) -> None:
        @GuardedHost
        class Vault:
            def steps(self):
                arrest = _Arrest(self)
                arrest.runs.append(SimpleNamespace(tag=Custody))
                _safehouse[id(self)] = arrest
                yield "must not escape"
                yield "repair"

        class Custody(Tag):
            @Rip
            def Leave(agent):
                pass

        vault = Vault()
        steps = vault.steps()   # captured before TOP actualizes this Host
        Custody(vault)

        with patch.dict(_safehouse, {}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                next(steps)
            self.assertEqual(len(_safehouse[id(vault)].lazy), 1)
            with _rip_door(vault):
                self.assertEqual(next(steps), "repair")
                steps.close()

    def test_coroutine_returned_before_tagging_checks_its_first_resume(self) -> None:
        @GuardedHost
        class Vault:
            async def read(self):
                return "secret"

        class Custody(Tag):
            @Rip
            def Leave(agent):
                pass

        vault = Vault()
        result = vault.read()
        Custody(vault)
        arrest = _Arrest(vault)
        arrest.runs.append(SimpleNamespace(tag=Custody))
        with patch.dict(_safehouse, {id(vault): arrest}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                result.send(None)
            with _rip_door(vault):
                with self.assertRaises(StopIteration) as completed:
                    result.send(None)
                self.assertEqual(completed.exception.value, "secret")

    def test_unweakrefable_untaggable_host_keeps_lazy_python_calls(self) -> None:
        @GuardedHost
        class Vault:
            __slots__ = ()

            def steps(self):
                yield "first"

            async def read(self):
                return "value"

        vault = Vault()
        self.assertEqual(next(vault.steps()), "first")
        result = vault.read()
        with self.assertRaises(StopIteration) as completed:
            result.send(None)
        self.assertEqual(completed.exception.value, "value")

    def test_captured_host_getter_and_setter_are_guarded(self) -> None:
        @GuardedHost
        class Vault:
            def __getattribute__(self, name: str) -> Any:
                return object.__getattribute__(self, name)

            def __setattr__(self, name: str, value: Any) -> None:
                object.__setattr__(self, name, value)

        class Custody(Tag):
            @Rip
            def Leave(agent):
                pass

        vault = Vault()
        vault.value = "secret"
        saved_read = vault.__getattribute__
        saved_write = vault.__setattr__
        Custody(vault)
        arrest = _Arrest(vault)
        arrest.runs.append(SimpleNamespace(tag=Custody))
        with patch.dict(_safehouse, {id(vault): arrest}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                saved_read("value")
            with self.assertRaises(TagArrestedAccessError):
                saved_write("value", "changed")
            with _rip_door(vault):
                self.assertEqual(saved_read("value"), "secret")
                saved_write("value", "changed")
        self.assertEqual(vault.value, "changed")

    def test_wrapped_frozen_dataclass_still_accepts_first_tagging(self) -> None:
        @GuardedHost
        @dataclass(frozen=True)
        class Vault:
            name: str

            def read(self):
                return self.name

        class Custody(Tag):
            @Rip
            def Leave(agent):
                pass

        vault = Vault("safe")
        saved = vault.read
        Custody(vault)
        self.assertEqual(saved(), "safe")
        self.assertIn(vault, Custody[:])

        arrest = _Arrest(vault)
        arrest.runs.append(SimpleNamespace(tag=Custody))
        with patch.dict(_safehouse, {id(vault): arrest}, clear=True):
            with self.assertRaises(TagArrestedAccessError):
                saved()

    def test_slotted_frozen_dataclass_retains_its_existing_tagging_boundary(self) -> None:
        class HostBase:
            pass   # supplies the instance dictionary TOP needs

        @GuardedHost
        @dataclass(frozen=True, slots=True)
        class Vault(HostBase):
            name: str

            def read(self):
                return self.name

        class Custody(Tag):
            pass

        vault = Vault("safe")
        Custody(vault)
        self.assertIn(vault, Custody[:])
        self.assertEqual(vault.read(), "safe")

    def test_a_tag_is_not_a_python_host_declaration(self) -> None:
        class Custody(Tag):
            pass

        with self.assertRaisesRegex(TagDeclarationError, "not a Tag"):
            GuardedHost(Custody)

    def test_cleanup_hooks_wait_for_their_separate_door(self) -> None:
        with self.assertRaisesRegex(TagDeclarationError, "cleanup hook"):
            @GuardedHost
            class Vault:
                def __exit__(self, error_type, error, traceback):
                    return False

        class Base:
            def __release_buffer__(self, buffer):
                pass

        with self.assertRaisesRegex(TagDeclarationError, "cleanup hook"):
            @GuardedHost
            class Child(Base):
                pass

        with self.assertRaisesRegex(TagDeclarationError, "cleanup hook"):
            @GuardedHost
            class Finalizer:
                def __del__(self):
                    pass

    def test_metaclass_cannot_mask_an_inherited_cleanup_hook(self) -> None:
        class Mask(type):
            @property
            def __dict__(cls):
                return {}

            @property
            def __mro__(cls):
                return (cls,)

        class Base:
            def __exit__(self, error_type, error, traceback):
                return False

        class Vault(Base, metaclass=Mask):
            def read(self):
                return "value"

        with self.assertRaisesRegex(TagDeclarationError, "__exit__"):
            GuardedHost(Vault)

    def test_async_generator_method_is_refused_before_partial_decoration(self) -> None:
        class Vault:
            def read(self):
                return "plain"

            async def stream(self):
                yield "value"

        original = Vault.__dict__["read"]
        with self.assertRaisesRegex(TagDeclarationError, "async generator"):
            GuardedHost(Vault)
        self.assertIs(Vault.__dict__["read"], original)

    def test_ordinary_method_returning_async_generator_is_refused_before_tagging(self) -> None:
        @GuardedHost
        class Vault:
            def stream(self):
                async def Values():
                    yield "value"

                return Values()

        vault = Vault()                         # no TOP Tagging has happened
        with self.assertRaisesRegex(
                TypeError,
                "async generator results cannot yet be guarded",
                ):
            vault.stream()

    def test_marking_the_same_class_twice_is_idempotent(self) -> None:
        @GuardedHost
        class Vault:
            def read(self):
                return "value"

        first = Vault.__dict__["read"]
        self.assertIs(GuardedHost(Vault), Vault)
        self.assertIs(Vault.__dict__["read"], first)

    def test_spoofed_function_metadata_cannot_skip_the_mark(self) -> None:
        def read(self):
            return "value"

        read.__topkit_host_source__ = read

        class Vault:
            pass

        Vault.read = read
        original = Vault.__dict__["read"]
        GuardedHost(Vault)
        self.assertIsNot(Vault.__dict__["read"], original)
        self.assertIs(Vault.__dict__["read"].__wrapped__, original)

    def test_spoofed_frozen_setter_metadata_cannot_skip_host_refusal(self) -> None:
        @dataclass(frozen=True)
        class Vault:
            name: str

        vault = Vault("safe")
        generated_setter = Vault.__dict__["__setattr__"]

        def refuse(self, name, value):
            raise RuntimeError("Host refuses the class change")

        refuse.__topkit_host_source__ = generated_setter
        Vault.__setattr__ = refuse
        GuardedHost(Vault)

        class Custody(Tag):
            pass

        with self.assertRaises(TagCompositionError):
            Custody(vault)
        self.assertIs(type(vault), Vault)

    def test_wrapper_ledger_does_not_retain_a_local_host_class(self) -> None:
        class Base:
            def read(self):
                return "base"

        def make_host():
            @GuardedHost
            class Vault(Base):
                def read(self):
                    return super().read()

            self.assertEqual(Vault().read(), "base")
            return ref(Vault)

        class_reference = make_host()
        collect()
        self.assertIsNone(class_reference())


if __name__ == "__main__":
    unittest.main()
