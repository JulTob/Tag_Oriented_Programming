"""A Precondition may query TOP, but cannot perform TOP state changes."""

from contextvars import copy_context
from threading import Event
from threading import Thread
import unittest

from TopKit import At_Exit
from TopKit import Contract
from TopKit import Flag
from TopKit import Form
from TopKit import Imprint
from TopKit import Pin
from TopKit import Post
from TopKit import Pre
from TopKit import Precondition
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import Underlay
from TopKit import lifecycle


class Host:
    pass


class ObservationalPreconditionTests(unittest.TestCase):
    def test_caught_rip_still_refuses_gate_without_removing_member(self):
        class Existing(Tag):
            pass

        class Rejected(Tag):
            @Pre
            def Gate(agent):
                try:
                    del Existing[agent]
                except TagCompositionError:
                    pass
                return True

        agent = Host()
        Existing(agent)

        with self.assertRaises(Precondition.Gate) as caught:
            Rejected(agent)

        self.assertIsInstance(caught.exception.__cause__, TagCompositionError)
        self.assertIn(agent, Existing[:])
        self.assertNotIn(agent, Rejected[:])

    def test_started_generator_cleanup_cannot_tag_after_pre_returns(self):
        other = Host()

        class Changed(Tag):
            pass

        class Rejected(Tag):
            @Pre
            def Gate(agent):
                def Result():
                    try:
                        yield True
                    finally:
                        Changed(other)

                result = Result()
                next(result)
                return result

        with self.assertRaises(Precondition.Gate) as caught:
            Rejected(Host())

        self.assertIsInstance(caught.exception.__cause__, TagCompositionError)
        self.assertNotIn(other, Changed[:])

    def test_result_repr_cannot_tag_during_condition_validation(self):
        other = Host()

        class Changed(Tag):
            pass

        class Result:
            def __repr__(self):
                Changed(other)
                return "invalid verdict"

        class Checked(Tag):
            @Pre
            def Ready(agent):
                return Result() if agent.invalid else True

        agent = Host()
        agent.invalid = False
        Checked(agent)
        agent.invalid = True

        self.assertIs(agent.Ready, False)
        self.assertEqual(Contract.Status(agent), {"Ready": False})
        self.assertNotIn(other, Changed[:])

    def test_exception_text_cannot_tag_during_named_pre_failure(self):
        other = Host()

        class Changed(Tag):
            pass

        class Failure(Exception):
            def __str__(self):
                Changed(other)
                return "failed"

        class Rejected(Tag):
            @Pre
            def Gate(agent):
                raise Failure()

        with self.assertRaises(Precondition.Gate) as caught:
            Rejected(Host())

        self.assertIsInstance(caught.exception.__cause__, TagCompositionError)
        self.assertNotIn(other, Changed[:])

    def test_query_action_is_allowed_but_its_other_target_tagging_is_not(self):
        other = Host()

        class Changed(Tag):
            pass

        class Reader(Tag):
            def Look(agent):
                if agent.perform:
                    try:
                        Changed(other)
                    except TagCompositionError:
                        pass
                return other in Changed[:]

        class Query(Tag):
            @Pre
            def Gate(agent):
                return agent.Look() is False

        class Forbidden(Tag):
            @Pre
            def Gate(agent):
                return agent.Look() is False

        agent = Host()
        agent.perform = False
        Reader(agent)
        Query(agent)                 # A read-only Action really can decide a Gate.

        agent.perform = True
        with self.assertRaises(Precondition.Gate):
            Forbidden(agent)

        self.assertNotIn(other, Changed[:])
        self.assertNotIn(agent, Forbidden[:])

    def test_cold_top_queries_and_nested_contract_query_stay_legal(self):
        class Known(Tag):
            @Pre
            def Ready(agent):
                return True

            def Look(agent):
                return "value"

        other = Host()
        Known(other)

        class Unused(Tag):
            pass

        class Query(Tag):
            @Pre
            def Gate(agent):
                return (
                        Form(Unused) == (Unused,)
                        and len(Unused[:]) == 0
                        and other in Known[:]
                        and isinstance(other, Known)
                        and "Look" @ other
                        and Contract.Status(other) == {"Ready": True}
                        )

        agent = Host()
        Query(agent)
        self.assertIn(agent, Query[:])

    def test_named_contract_paths_guard_at_exit_registration(self):
        armed = False

        class Guarded(Tag):
            @Pre
            def Ready(agent):
                if armed:
                    try:
                        At_Exit(agent)
                    except TagCompositionError:
                        pass
                return True

        agent = Host()
        Guarded(agent)
        armed = True
        original = lifecycle._exit_count

        with self.assertRaises(Precondition.Ready):
            Contract.Preconditions(agent)
        self.assertIs(agent.Ready, False)
        self.assertEqual(Contract.Status(agent), {"Ready": False})
        self.assertIn("Ready", Contract.Display(agent))
        self.assertEqual(lifecycle._exit_count, original)

    def test_contract_delete_tag_class_writes_and_marks_leave_no_effect(self):
        class Existing(Tag):
            label = "original"

            @Post
            def Ready(agent):
                return True

        class Rejected(Tag):
            @Pre
            def Gate(agent):
                for change in (
                        lambda: Contract.Delete(agent, "Ready"),
                        lambda: setattr(Existing, "label", "changed"),
                        lambda: delattr(Existing, "label"),
                        lambda: Flag(Existing),
                        lambda: Pin(Existing),
                        ):
                    try:
                        change()
                    except TagCompositionError:
                        pass
                return True

        agent = Host()
        Existing(agent)

        with self.assertRaises(Precondition.Gate):
            Rejected(agent)

        self.assertEqual(Contract.Status(agent), {"Ready": True})
        self.assertEqual(Existing.label, "original")
        self.assertNotIn("__topkit_flag__", Existing.__dict__)
        self.assertNotIn("__topkit_pin__", Existing.__dict__)

    def test_underlay_cannot_hide_mutation_and_keeps_completed_base(self):
        calls = []

        class Base(Tag):
            @Pre
            def Ready(agent):
                calls.append("Base")
                return True

        class Shape(Base):
            @Pre
            @Underlay
            def Ready(agent, prior):
                try:
                    del Base[agent]
                except TagCompositionError:
                    pass
                calls.append("Shape")
                return prior()

        agent = Host()
        with self.assertRaises(Precondition.Ready):
            Shape(agent)

        self.assertIn(agent, Base[:])
        self.assertNotIn(agent, Shape[:])
        self.assertEqual(calls, ["Base", "Shape", "Base"])

    def test_pin_precondition_guards_a_different_target(self):
        other = Host()

        class Changed(Tag):
            pass

        class Candidate(Tag):
            pass

        @Pin
        class Inspection(Tag):
            @Pre
            def Gate(tag):
                try:
                    Changed(other)
                except TagCompositionError:
                    pass
                return True

        with self.assertRaises(Precondition.Gate):
            Inspection(Candidate)

        self.assertNotIn(other, Changed[:])
        self.assertNotIn(Candidate, Inspection[:])

    def test_other_thread_and_expired_copied_context_are_not_guarded(self):
        entered = Event()
        release = Event()
        copied = []
        failures = []

        class Slow(Tag):
            @Pre
            def Gate(agent):
                copied.append(copy_context())
                entered.set()
                if not release.wait(3):
                    raise TimeoutError("test did not release the Gate")
                return True

        class Independent(Tag):
            pass

        def apply_slow():
            try:
                Slow(Host())
            except BaseException as error:
                failures.append(error)

        thread = Thread(target=apply_slow)
        thread.start()
        try:
            self.assertTrue(entered.wait(3))
            other = Host()
            Independent(other)       # A process-wide or Agent-wide lock fails.
            self.assertIn(other, Independent[:])
        finally:
            release.set()
            thread.join(3)

        self.assertFalse(thread.is_alive())
        self.assertEqual(failures, [])
        another = Host()
        copied[0].run(Independent, another)  # The inherited token has expired.
        self.assertIn(another, Independent[:])

    def test_imprint_and_post_still_allow_deliberate_tagging(self):
        trained = Host()
        checked = Host()
        doubly_checked = Host()

        class Training(Tag):
            pass

        class Checked(Tag):
            pass

        class Finished(Tag):
            @Imprint
            def Train(agent):
                Training(trained)

            @Post
            def Ready(agent):
                Checked(checked)
                return True

        Finished(Host())
        self.assertIn(trained, Training[:])
        self.assertIn(checked, Checked[:])

        class Both(Tag):
            @Pre
            @Post
            def Ready(agent):
                if agent in Both[:]:   # This is the Post, after Field entry.
                    Checked(doubly_checked)
                return True

        Both(Host())
        self.assertIn(doubly_checked, Checked[:])


if __name__ == "__main__":
    unittest.main()
