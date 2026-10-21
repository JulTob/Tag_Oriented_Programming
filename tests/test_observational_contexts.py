"""Copied contexts retain read-only checks for each active calculation."""

from contextvars import copy_context
from threading import Event, Thread
import unittest

from TopKit import (
    Pin, Post, Pre, Record, Tag, TagCompositionError, TagPreconditionError,
)


class Host:
    pass


class ObservationalContextTests(unittest.TestCase):
    def check_copied_post_outlives_parent(self, phase):
        entered, release = Event(), Event()
        changed, child, parent = Host(), Host(), Host()
        threads, answers, failures = [], [], []

        class Changed(Tag):
            pass

        class Child(Tag):
            @Post
            def Ready(target):
                if target.wait:
                    entered.set()
                    if not release.wait(2):
                        raise TimeoutError("parent calculation did not finish")
                    try:
                        Changed(changed)
                    except TagCompositionError:
                        pass
                return True

        child.wait = False
        Child(child)
        child.wait = True

        def start_child(target):
            context = copy_context()
            def query():
                try:
                    answers.append(bool(child))
                except BaseException as error:
                    failures.append(error)
            worker = Thread(target=lambda: context.run(query))
            threads.append(worker)
            worker.start()
            if not entered.wait(2):
                raise TimeoutError("copied Post did not start")
            return True

        if phase == "Pre":
            class Parent(Tag):
                Ready = Pre(start_child)
        else:
            class Parent(Tag):
                prepared = Record(start_child)

        try:
            Parent(parent)
            self.assertIn(parent, Parent[:])
            if phase == "Record":
                self.assertIs(parent.prepared, True)
        finally:
            release.set()
            for worker in threads:
                worker.join(2)
        self.assertFalse(any(worker.is_alive() for worker in threads))
        self.assertEqual(failures, [])
        self.assertEqual(answers, [False])
        self.assertNotIn(changed, Changed[:])

    def test_copied_thread_post_stays_read_only_after_parent_pre_finishes(self):
        self.check_copied_post_outlives_parent("Pre")

    def test_copied_thread_post_stays_read_only_after_parent_record_finishes(self):
        self.check_copied_post_outlives_parent("Record")

    def test_a_direct_act_in_a_copied_active_context_still_poisons_the_gate(self):
        changed, parent = Host(), Host()
        failures = []
        class Changed(Tag):
            pass
        class Refused(Tag):
            @Pre
            def Ready(target):
                context = copy_context()
                def mutate():
                    try:
                        Changed(changed)
                    except TagCompositionError:
                        pass
                    except BaseException as error:
                        failures.append(error)
                worker = Thread(target=lambda: context.run(mutate))
                worker.start()
                worker.join(2)
                if worker.is_alive():
                    raise TimeoutError("copied act did not finish")
                return True
        with self.assertRaises(TagPreconditionError.Ready):
            Refused(parent)
        self.assertEqual(failures, [])
        self.assertNotIn(changed, Changed[:])
        self.assertNotIn(parent, Refused[:])

    def test_a_same_thread_nested_post_cannot_hide_a_caught_mutation(self):
        changed = Host()
        class Changed(Tag):
            pass
        class Child(Tag):
            @Post
            def Ready(target):
                if target.attempt:
                    try:
                        Changed(changed)
                    except TagCompositionError:
                        pass
                return True
        child = Host()
        child.attempt = False
        Child(child)
        child.attempt = True
        class Refused(Tag):
            @Pre
            def Ready(target):
                self.assertFalse(child.Ready)
                return True
        parent = Host()
        with self.assertRaises(TagPreconditionError.Ready):
            Refused(parent)
        self.assertNotIn(changed, Changed[:])
        self.assertNotIn(parent, Refused[:])

    def test_a_copied_finished_context_starts_a_fresh_guarded_pin_gate(self):
        contexts = []
        class Capture(Tag):
            @Pre
            def Ready(target):
                contexts.append(copy_context())
                return True
        Capture(Host())
        class Target(Tag):
            pass
        class Changed(Tag):
            pass
        changed = Host()
        class Refused(Pin):
            @Pre
            def Ready(target):
                Changed(changed)
                return True
        with self.assertRaises(TagPreconditionError.Ready):
            contexts[0].run(Refused, Target)
        self.assertNotIn(Target, Refused[:])
        self.assertNotIn(changed, Changed[:])
