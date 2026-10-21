"""Conditions query TOP without changing its Tags, Fields or contracts."""

from contextvars import copy_context
import gc
from threading import Thread
import unittest
import weakref

from TopKit import (Action, At_Exit, Constant, Contract, Flag, Imprint,
                    Link, Pin, Post, Pre, Precondition, Public, Report, Tag,
                    TagCompositionError, TagPostconditionError, agent, contact)
from TopKit.observations import _observing, _refuse_observed_act
from TopKit import lifecycle


class Host:
    pass


class ObservationalContractTests(unittest.TestCase):

    def test_caught_rip_refuses_gate_without_changing_existing_membership(self):
        class Existing(Tag):
            pass

        class Refused(Tag):
            @Pre
            def Ready(target):
                try:
                    del Existing[target]
                except TagCompositionError:
                    pass
                return True

        target = Host()
        Existing(target)
        with self.assertRaises(Precondition.Ready) as refusal:
            Refused(target)
        self.assertIsInstance(refusal.exception.__cause__, TagCompositionError)
        self.assertIn(target, Existing[:])
        self.assertNotIn(target, Refused[:])

    def test_read_actions_and_raw_queries_remain_allowed(self):
        class Reader(Tag):
            @Action
            def Twice(target):
                return target.value * 2

        class Accepted(Tag):
            @Pre
            def Ready(target):
                return target.Twice() == 6 and target in Reader[:]

        target = Host()
        target.value = 3
        Reader(target)
        Accepted(target)
        self.assertIn(target, Accepted[:])
        self.assertFalse("Ready" @ target)  # Pres never become Agent Gains.

    def test_pre_cannot_apply_a_tag_to_another_target(self):
        other = Host()

        class Changed(Tag):
            pass

        class Refused(Tag):
            @Pre
            def Ready(target):
                Changed(other)

        with self.assertRaises(Precondition.Ready):
            Refused(Host())
        self.assertNotIn(other, Changed[:])

    def test_post_mutation_is_false_for_boolean_named_and_status_queries(self):
        class Existing(Tag):
            pass

        class Checked(Tag):
            @Post
            def Ready(target):
                if target.attempt:
                    try:
                        del Existing[target]
                    except TagCompositionError:
                        pass
                return True

        target = Host()
        target.attempt = False
        Existing(target)
        Checked(target)
        target.attempt = True
        self.assertFalse(bool(target))
        self.assertFalse(target.Ready)
        self.assertEqual(Contract.Status(target), {"Ready": False})
        with self.assertRaises(TagPostconditionError.Ready):
            Contract.Postconditions(target)
        self.assertIn(target, Existing[:])

    def test_nested_post_failure_cannot_hide_a_pre_observation_violation(self):
        other = Host()

        class Changed(Tag):
            pass

        class Checked(Tag):
            @Post
            def Ready(target):
                if target.attempt:
                    Changed(other)
                return True

        class Refused(Tag):
            @Pre
            def Enter(target):
                checked.Ready  # Named Post reads map ordinary errors to False.
                return True

        checked, target = Host(), Host()
        checked.attempt = False
        Checked(checked)
        checked.attempt = True
        with self.assertRaises(Precondition.Enter):
            Refused(target)
        self.assertNotIn(other, Changed[:])
        self.assertNotIn(target, Refused[:])

    def test_top_mutations_are_refused_before_declaration_or_registry_changes(self):
        class Empty(Tag):
            pass

        class Existing(Tag):
            note = "original"

            def Work(target):
                return 1

            @Report
            def count(tag):
                return 2

            @Post
            def Ready(target):
                return True

        report = vars(Existing)["count"]
        acts = (
                lambda target: setattr(Existing, "note", "changed"),
                lambda target: delattr(Existing, "note"),
                lambda target: Contract.Delete(target, "Ready"),
                lambda target: Flag(Existing),
                lambda target: Pin(Empty),
                lambda target: Public(report),
                lambda target: Constant(Existing.Work),
                lambda target: At_Exit(target),
                )
        target = Host()
        Existing(target)
        exits = lifecycle._exit_count
        for act in acts:
            with self.subTest(act=act):
                class Refused(Tag):
                    @Pre
                    def Ready(target):
                        try:
                            act(target)
                        except TagCompositionError:
                            pass
                        return True

                with self.assertRaises(Precondition.Ready):
                    Refused(target)
        self.assertEqual(Existing.note, "original")
        self.assertFalse(report.public)
        self.assertNotIn("__topkit_constant__", vars(Existing.Work))
        self.assertNotIn("__topkit_pin__", vars(Empty))
        self.assertNotIn("__topkit_flag__", vars(Existing))
        self.assertEqual(lifecycle._exit_count, exits)
        self.assertTrue(target.Ready)

    def test_nested_tag_creation_is_refused_during_a_condition(self):
        created = []

        class Refused(Tag):
            @Pre
            def Ready(target):
                class Temporary(Tag):
                    pass

                created.append(Temporary)

        with self.assertRaises(Precondition.Ready):
            Refused(Host())
        self.assertEqual(created, [])

    def test_nested_declarations_and_imprint_tag_creation_remain_allowed(self):
        created = []
        other = Host()

        class Social(Tag):
            class Nested(Tag):
                pass

            @Imprint
            def Prepare(target):
                class Temporary(Tag):
                    pass

                Temporary(other)
                created.append(Temporary)

        target = Host()
        Social(target)
        self.assertIn(other, created[0][:])
        self.assertTrue(issubclass(Social.Nested, Tag))

    def test_verdict_and_error_rendering_cannot_escape_the_gate(self):
        other = Host()

        class Changed(Tag):
            pass

        class Invalid:
            def __repr__(self):
                Changed(other)
                return "invalid"

        class Failure(Exception):
            def __str__(self):
                Changed(other)
                return "failed"

        for supplied in (Invalid(), Failure()):
            with self.subTest(supplied=type(supplied).__name__):
                class Refused(Tag):
                    @Pre
                    def Ready(target):
                        if isinstance(supplied, Exception):
                            raise supplied
                        return supplied

                with self.assertRaises(Precondition.Ready) as refusal:
                    Refused(Host())
                self.assertIsInstance(refusal.exception.__cause__, TagCompositionError)
                self.assertNotIn(other, Changed[:])

    def test_disposing_invalid_lazy_verdict_cannot_change_a_field(self):
        other = Host()

        class Changed(Tag):
            pass

        class Refused(Tag):
            @Pre
            def Ready(target):
                def Result():
                    try:
                        yield True
                    finally:
                        Changed(other)

                value = Result()
                next(value)
                return value

        with self.assertRaises(Precondition.Ready) as refusal:
            Refused(Host())
        self.assertIsInstance(refusal.exception.__cause__, TagCompositionError)
        self.assertNotIn(other, Changed[:])

    def test_context_copy_loses_guard_when_the_observation_ends(self):
        saved = []

        class Known(Tag):
            pass

        class Accepted(Tag):
            @Pre
            def Ready(target):
                saved.append(copy_context())

        target, other = Host(), Host()
        Accepted(target)
        saved[0].run(Known, other)
        self.assertIn(other, Known[:])

    def test_saved_context_does_not_keep_an_observed_agent_alive_after_failure(self):
        saved = []

        class Refused(Tag):
            @Pre
            def Ready(target):
                saved.append(copy_context())
                try:
                    Refused(target)
                except TagCompositionError:
                    pass

        def attempt():
            target = Host()
            reference = weakref.ref(target)
            try:
                Refused(target)
            except Precondition.Ready:
                pass
            return reference

        reference = attempt()
        gc.collect()
        self.assertIsNone(reference())
        self.assertTrue(saved)

    def test_unrelated_thread_keeps_its_own_top_authority(self):
        failures = []
        other = Host()

        class Changed(Tag):
            pass

        def change():
            try:
                Changed(other)
            except BaseException as error:
                failures.append(error)

        class Accepted(Tag):
            @Pre
            def Ready(target):
                thread = Thread(target=change)
                thread.start()
                thread.join(2)
                return not thread.is_alive()

        Accepted(Host())
        self.assertEqual(failures, [])
        self.assertIn(other, Changed[:])

    def test_python_writes_remain_the_authors_responsibility(self):
        class Accepted(Tag):
            @Pre
            def Ready(target):
                target.note = "ordinary Python effect"

        target = Host()
        Accepted(target)
        self.assertEqual(target.note, "ordinary Python effect")

    def test_an_interruption_is_not_masked_by_an_earlier_caught_violation(self):
        with self.assertRaises(KeyboardInterrupt):
            with _observing("Postcondition Ready"):
                try:
                    _refuse_observed_act("apply a Tag")
                except TagCompositionError:
                    pass
                raise KeyboardInterrupt()

    def test_link_header_creation_is_refused_during_a_condition(self):
        class Refused(Tag):
            @Pre
            def Ready(target):
                @Link(agent, contact)
                class Temporary(agent.Knows):
                    pass

        with self.assertRaises(Precondition.Ready):
            Refused(Host())




if __name__ == "__main__":
    unittest.main()
