"""Concurrent publication cannot turn ordinary Tags into Pins."""

import gc
import unittest
from threading import Event, Thread
from unittest.mock import patch

from TopKit import Pin, Tag, TagCompositionError, TagDeclarationError, Tool
from tests.test_tools import Character


class PinPublicationRaceTests(unittest.TestCase):
    def run_conversion_while(self, kind, entered, release, build):
        outcomes, built = [], []
        def declare():
            try:
                built.append(build())
            except BaseException as error:
                outcomes.append(error)
        worker = Thread(target=declare)
        worker.start()
        try:
            self.assertTrue(entered.wait(2))
            with self.assertRaises(TagDeclarationError):
                Pin(kind)
        finally:
            release.set()
            worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(outcomes, [])
        return built[0]

    def test_shape_creation_cannot_race_an_ordinary_base_into_a_pin(self):
        entered, release = Event(), Event()
        class Base(Tag):
            def __init_subclass__(cls, **kwargs):
                super().__init_subclass__(**kwargs)
                entered.set()
                if not release.wait(2):
                    raise TimeoutError("Shape declaration did not resume")
        class Ordinary(Tag):
            pass
        def build():
            class Shape(Base, Ordinary):
                pass
            return Shape
        shape = self.run_conversion_while(Base, entered, release, build)
        target = Character("ordinary")
        shape(target)
        self.assertIn(target, Base[:])
        self.assertIn(target, Ordinary[:])
        self.assertIn(target, shape[:])

    def test_shape_tool_stays_an_object_gain_during_a_conversion_attempt(self):
        entered, release = Event(), Event()
        class Base(Tag):
            def __init_subclass__(cls, **kwargs):
                super().__init_subclass__(**kwargs)
                entered.set()
                if not release.wait(2):
                    raise TimeoutError("Tool Shape declaration did not resume")
        class Kind(Tag):
            pass
        @Tool(Kind | None)
        def prize(agent):
            return None
        def build():
            class Shape(Base):
                held = prize
            return Shape
        shape = self.run_conversion_while(Base, entered, release, build)
        target = Character("collector")
        shape(target)
        with self.assertRaises(TagCompositionError):
            target.held = object()
        item = Character("prize")
        Kind(item)
        target.held = item
        self.assertIs(target.held, item)

    def test_late_tool_binding_remains_valid_during_a_conversion_attempt(self):
        entered, release = Event(), Event()
        class Kind(Tag):
            pass
        class Old:
            armed = False
            def __call__(self, agent):
                return None
            def __getattribute__(self, name):
                if name == "__topkit_constant__" and object.__getattribute__(self, "armed"):
                    entered.set()
                    if not release.wait(2):
                        raise TimeoutError("late Tool binding did not resume")
                return object.__getattribute__(self, name)
        old = Old()
        class Candidate(Tag):
            prize = old
        @Tool(Kind | None)
        def prize(agent):
            return None
        old.armed = True
        def bind():
            Candidate.prize = prize
            return Candidate
        self.assertIs(self.run_conversion_while(Kind, entered, release, bind), Candidate)
        self.assertIs(Candidate.__dict__["prize"], prize)
        target = Character("collector")
        Candidate(target)
        with self.assertRaises(TagCompositionError):
            target.prize = object()

    def test_conversion_refusal_does_not_wait_for_tool_owner_registration(self):
        import TopKit.declarations as declarations
        class Prize(Tag):
            pass
        entered, release, refused = Event(), Event(), Event()
        failures, declared = [], []
        original = declarations._note_tag_kinds
        def pause(owner, tags):
            entered.set()
            if not release.wait(2):
                raise TimeoutError("Tool declaration did not resume")
            original(owner, tags)
        def declare():
            try:
                class Collector(Tag):
                    @Tool(Prize | None)
                    def prize(agent):
                        return None
                declared.append(Collector)
            except BaseException as error:
                failures.append(error)
        def convert():
            try:
                Pin(Prize)
            except TagDeclarationError:
                refused.set()
            except BaseException as error:
                failures.append(error)
        # Measure the refusal itself. Event.set() can trigger cyclic GC
        # after Pin has already raised, running an unrelated weak callback
        # that waits for the publication lock deliberately held here.
        gc.collect()
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            with patch.object(declarations, "_note_tag_kinds", pause):
                owner_thread, conversion_thread = Thread(target=declare), Thread(target=convert)
                owner_thread.start()
                try:
                    self.assertTrue(entered.wait(2))
                    conversion_thread.start()
                    self.assertTrue(refused.wait(1), "root refusal waited for a mutable owner ledger")
                finally:
                    release.set()
                    owner_thread.join(2)
                    if conversion_thread.ident is not None:
                        conversion_thread.join(2)
        finally:
            if gc_was_enabled:
                gc.enable()
        self.assertFalse(owner_thread.is_alive())
        self.assertFalse(conversion_thread.is_alive())
        self.assertEqual(failures, [])
        self.assertEqual(len(declared), 1)
        target = Character("collector")
        declared[0](target)
        self.assertIsNone(target.prize)
