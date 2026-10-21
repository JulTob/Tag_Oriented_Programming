"""Ordinary Tagging reserves its Form until completion or interruption."""

import gc
import sys
import unittest
from threading import Event, Thread

from TopKit import (
    Form,
    Imprint,
    Pin,
    Pre,
    Tag,
    TagCompositionError,
    TagDeclarationError,
    TagImprintError,
    TagPreconditionError,
)
from TopKit.tags import MetaTag
from tests.test_tools import Character


class PinTaggingReservationTests(unittest.TestCase):

    def test_one_failed_call_does_not_release_another_calls_reservation(self):
        first_entered, second_entered = Event(), Event()
        release_first, release_second = Event(), Event()
        failures = []

        class First(Tag):
            @Imprint
            def Train(agent):
                first_entered.set()
                if not release_first.wait(2):
                    raise TimeoutError("first training did not resume")
                raise ValueError("first training failed")

        class Second(Tag):
            @Imprint
            def Train(agent):
                second_entered.set()
                if not release_second.wait(2):
                    raise TimeoutError("second training did not resume")

        def train(tag, agent):
            try:
                tag(agent)
            except Exception as error:
                failures.append(error)

        second = Character("second")
        first_thread = Thread(target=train, args=(First, Character("first")))
        second_thread = Thread(target=train, args=(Second, second))
        first_thread.start()
        try:
            self.assertTrue(first_entered.wait(2))
            second_thread.start()
            self.assertTrue(second_entered.wait(2))
            release_first.set()
            first_thread.join(2)
            self.assertFalse(first_thread.is_alive())
            self.assertIs(Pin(First), First)
            with self.assertRaises(TagDeclarationError):
                Pin(Second)
        finally:
            release_first.set()
            release_second.set()
            first_thread.join(2)
            if second_thread.ident is not None:
                second_thread.join(2)

        self.assertFalse(second_thread.is_alive())
        self.assertEqual(len(failures), 1)
        self.assertIsInstance(failures[0], TagImprintError)
        self.assertIn(second, Second[:])

    def test_interruption_after_extra_registration_releases_its_tags(self):
        class Old(Tag):
            pass

        class New(Tag):
            pass

        class Shape(Old):
            pass

        self.assertEqual(Form(Shape), (Old, Shape))
        Shape.__bases__ = (New,)
        registrations = []

        def interrupt(frame, event, arg):
            if frame.f_code.co_name == "_begin_ordinary_form" and event == "return":
                registrations.append(True)
                if len(registrations) == 2:
                    raise KeyboardInterrupt("after extra registration")
            return interrupt

        before = sys.gettrace()
        try:
            sys.settrace(interrupt)
            with self.assertRaises(KeyboardInterrupt):
                Shape(Character("interrupted"))
        finally:
            sys.settrace(before)

        self.assertIs(Pin(Old), Old)
        del Shape
        gc.collect()
        self.assertIs(Pin(New), New)

    def test_interruption_before_nested_registration_preserves_outer_call(self):
        entered = []
        refused = []

        class Role(Tag):
            @Imprint
            def Train(agent):
                if entered:
                    return
                entered.append(agent)

                def interrupt(frame, event, arg):
                    if event == "call" and frame.f_code.co_name == "_begin_ordinary_form":
                        raise KeyboardInterrupt("before nested registration")
                    return interrupt

                before = sys.gettrace()
                try:
                    sys.settrace(interrupt)
                    try:
                        Role(Character("nested"))
                    except KeyboardInterrupt:
                        pass
                    else:
                        raise AssertionError("the nested call was not interrupted")
                finally:
                    sys.settrace(before)

                try:
                    Pin(Role)
                except TagDeclarationError:
                    refused.append(True)

        agent = Character("outer")
        Role(agent)
        self.assertEqual(refused, [True])
        self.assertNotIn("__topkit_pin__", Role.__dict__)
        self.assertIn(agent, Role[:])

    def test_a_cached_form_cannot_apply_a_base_already_converted_to_pin(self):
        class Old(Tag):
            pass

        class New(Tag):
            pass

        class Shape(Old):
            pass

        self.assertEqual(Form(Shape), (Old, Shape))
        Shape.__bases__ = (New,)
        Pin(Old)
        agent = Character("Ari")

        with self.assertRaises(TagCompositionError):
            Shape(agent)
        self.assertNotIn(agent, Old[:])
        self.assertNotIn(agent, New[:])
        self.assertNotIn(agent, Shape[:])

    def test_cold_form_hash_can_wait_for_a_concurrent_pin_refusal(self):
        armed = [False]
        completed = Event()
        outcomes = []

        class Hashing(MetaTag):
            def __hash__(cls):
                if armed[0]:
                    armed[0] = False

                    def pin():
                        try:
                            Pin(cls)
                        except TagDeclarationError as error:
                            outcomes.append(str(error))
                        finally:
                            completed.set()

                    worker = Thread(target=pin)
                    worker.start()
                    outcomes.append(completed.wait(2))
                    worker.join(2)
                return type.__hash__(cls)

        class Candidate(Tag, metaclass=Hashing):
            pass

        armed[0] = True
        ari = Character("Ari")
        Candidate(ari)

        self.assertIn(True, outcomes)
        self.assertTrue(any("Tagging is in flight" in item
                            for item in outcomes if isinstance(item, str)))
        self.assertIn(ari, Candidate[:])

    def test_cold_form_hash_hook_cannot_pin_the_tag_before_reservation(self):
        armed = [False]
        refusals = []

        class Hashing(MetaTag):
            def __hash__(cls):
                if armed[0]:
                    armed[0] = False
                    try:
                        Pin(cls)
                    except TagDeclarationError as error:
                        refusals.append(str(error))
                return type.__hash__(cls)

        class Candidate(Tag, metaclass=Hashing):
            pass

        armed[0] = True
        ari = Character("Ari")
        Candidate(ari)

        self.assertEqual(len(refusals), 1)
        self.assertIn("Tagging is in flight", refusals[0])
        self.assertNotIn("__topkit_pin__", Candidate.__dict__)
        self.assertIn(ari, Candidate[:])

    def test_cold_form_failure_releases_provisional_pin_reservation(self):
        armed = [False]
        completed = Event()
        outcomes = []

        class Hashing(MetaTag):
            def __hash__(cls):
                if armed[0]:
                    armed[0] = False

                    def pin():
                        try:
                            Pin(cls)
                        except TagDeclarationError as error:
                            outcomes.append(str(error))
                        finally:
                            completed.set()

                    worker = Thread(target=pin)
                    worker.start()
                    outcomes.append(completed.wait(2))
                    worker.join(2)
                    raise ValueError("cold Form failed")
                return type.__hash__(cls)

        class Candidate(Tag, metaclass=Hashing):
            pass

        armed[0] = True
        with self.assertRaisesRegex(ValueError, "cold Form failed"):
            Candidate(Character("Ari"))

        self.assertIn(True, outcomes)
        self.assertTrue(any("Tagging is in flight" in item
                            for item in outcomes if isinstance(item, str)))
        later = []
        worker = Thread(target=lambda: later.append(Pin(Candidate)))
        worker.start()
        worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(later, [Candidate])

    def test_a_new_pin_base_during_form_calculation_refuses_ordinary_tagging(self):
        armed = [False]

        class Old(Tag):
            pass

        class New(Tag):
            pass

        class Hashing(MetaTag):
            def __hash__(cls):
                if armed[0]:
                    armed[0] = False
                    Pin(New)
                    type.__setattr__(cls, "__bases__", (New,))
                return type.__hash__(cls)

        class Shape(Old, metaclass=Hashing):
            pass

        armed[0] = True
        ari = Character("Ari")
        with self.assertRaisesRegex(TagCompositionError, "Pin Base"):
            Shape(ari)
        self.assertNotIn(ari, New[:])

    def test_cached_form_base_stays_reserved_after_real_bases_change(self):
        refusals = []

        class Old(Tag):
            @Imprint
            def Train(agent):
                try:
                    Pin(Old)
                except TagDeclarationError as error:
                    refusals.append(str(error))

        class New(Tag):
            pass

        class Shape(Old):
            pass

        self.assertEqual(Form(Shape), (Old, Shape))
        Shape.__bases__ = (New,)

        ari = Character("Ari")
        Shape(ari)

        self.assertEqual(len(refusals), 1)
        self.assertIn("Tagging is in flight", refusals[0])
        self.assertNotIn("__topkit_pin__", Old.__dict__)
        self.assertIn(ari, Old[:])

    def test_an_imprint_cannot_turn_its_unfinished_tag_into_a_pin(self):
        refusals = []

        class Candidate(Tag):
            @Imprint
            def Train(agent):
                Candidate(agent)                  # same-Tag reentry is a no-op
                try:
                    Pin(Candidate)
                except TagDeclarationError as error:
                    refusals.append(str(error))

        ari = Character("Ari")
        Candidate(ari)
        self.assertEqual(len(refusals), 1)
        self.assertIn("Tagging is in flight", refusals[0])
        self.assertNotIn("__topkit_pin__", Candidate.__dict__)
        self.assertIn(ari, Candidate[:])

    def test_a_concurrent_pin_cannot_reclassify_an_unfinished_tag(self):
        entered = Event()
        resume = Event()
        outcome = []

        class Candidate(Tag):
            @Imprint
            def Train(agent):
                entered.set()
                if not resume.wait(2):
                    raise TimeoutError("Tagging did not resume")

        ari = Character("Ari")

        def apply():
            try:
                Candidate(ari)
            except BaseException as error:
                outcome.append(type(error).__name__)
            else:
                outcome.append("tagged")

        worker = Thread(target=apply)
        worker.start()
        try:
            self.assertTrue(entered.wait(2))
            with self.assertRaises(TagDeclarationError) as refusal:
                Pin(Candidate)
            self.assertIn("Tagging is in flight", str(refusal.exception))
        finally:
            resume.set()
            worker.join(2)

        self.assertEqual(outcome, ["tagged"])
        self.assertFalse(worker.is_alive())
        self.assertNotIn("__topkit_pin__", Candidate.__dict__)
        self.assertIn(ari, Candidate[:])

    def test_a_refused_or_interrupted_gate_releases_the_pending_mark(self):
        class Refused(Tag):
            @Pre
            def Gate(agent):
                return False

        class Interrupted(Tag):
            @Pre
            def Gate(agent):
                raise KeyboardInterrupt

        with self.assertRaises(TagPreconditionError):
            Refused(Character("Ari"))
        with self.assertRaises(KeyboardInterrupt):
            Interrupted(Character("Bob"))

        self.assertIs(Pin(Refused), Refused)
        self.assertIs(Pin(Interrupted), Interrupted)

