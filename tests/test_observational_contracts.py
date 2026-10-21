"""Conditions query TOP without changing its Tags, Fields or contracts."""

from contextvars import Context, ContextVar, copy_context
import gc
from threading import Thread
import unittest
import weakref

from TopKit import (Action, At_Exit, Constant, Contract, Flag, Imprint,
                    Pin, Post, Pre, Precondition, Public, Record, Report, Rip, Tag,
                    TagCompositionError, TagPostconditionError, Tool)
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

            @Post
            def Correct(target):
                return target.Twice() == 6 and target in Reader[:]

        target = Host()
        target.value = 3
        Reader(target)
        Accepted(target)
        self.assertIn(target, Accepted[:])
        self.assertTrue(target.Correct)
        self.assertEqual(Contract.Status(target), {"Correct": True})
        self.assertFalse("Ready" @ target)  # Pres never become Agent Gains.

    def test_pin_conditions_can_call_query_actions_on_the_target_tag(self):
        class Counted(Pin):
            @Action
            def Count(target):
                return len(target[:])

        class Checked(Pin):
            @Pre
            def Populated(target):
                return target.Count() == 1

            @Post
            def Stable(target):
                return target.Count() == 1

        class Target(Tag):
            pass

        member = Host()
        Target(member)
        Counted(Target)
        Checked(Target)
        self.assertTrue(Target.Stable)
        self.assertEqual(list(Target[:]), [member])
        self.assertIn(Target, Checked[:])

    def test_caught_mutation_inside_an_action_still_refuses_the_condition(self):
        for mark, failure in ((Pre, Precondition), (Post, TagPostconditionError)):
            with self.subTest(mark=mark):
                other, target = Host(), Host()
                caught = []

                class Changed(Tag):
                    pass

                class Queries(Tag):
                    @Action
                    def Attempt(target):
                        try:
                            Changed(other)
                        except TagCompositionError:
                            caught.append("refused")
                        return True

                checked = type("Checked", (Tag,), {
                        "Ready": mark(lambda target: target.Attempt()),
                        })
                Queries(target)
                with self.assertRaises(failure.Ready) as refusal:
                    checked(target)
                self.assertIsInstance(refusal.exception.__cause__, TagCompositionError)
                self.assertEqual(caught, ["refused"])
                self.assertNotIn(other, Changed[:])
                self.assertIn(target, Queries[:])
                self.assertEqual(target in checked[:], mark is Post)

    def test_a_post_cannot_rip_an_earlier_tag_in_its_completed_form(self):
        released = []

        class Earlier(Tag):
            @Rip
            def Release(target):
                released.append(target)

        class Later(Earlier):
            @Post
            def Ready(target):
                try:
                    del Earlier[target]
                except TagCompositionError:
                    pass
                return True

        target = Host()
        with self.assertRaises(TagPostconditionError.Ready) as refusal:
            Later(target)
        self.assertIsInstance(refusal.exception.__cause__, TagCompositionError)
        self.assertEqual(released, [])
        self.assertIn(target, Earlier[:])
        self.assertIn(target, Later[:])

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
                lambda target: type("NewPin", (Pin,), {}),
                lambda target: Public(report),
                lambda target: Constant(Existing.Work),
                lambda target: At_Exit(target),
                )
        target = Host()
        Existing(target)
        exits = lifecycle._exit_count
        pins = tuple(type.__subclasses__(Pin))
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
        self.assertEqual(tuple(type.__subclasses__(Pin)), pins)
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

    def test_conditions_cannot_declare_a_new_pin_even_if_they_catch_the_refusal(self):
        for mark, failure in ((Pre, Precondition), (Post, TagPostconditionError)):
            with self.subTest(mark=mark):
                created = []

                def Ready(target):
                    try:
                        class Temporary(Pin):
                            pass
                    except TagCompositionError:
                        pass
                    else:
                        created.append(Temporary)
                    return True

                checked = type("Checked", (Tag,), {"Ready": mark(Ready)})
                before = tuple(type.__subclasses__(Pin))
                target = Host()
                with self.assertRaises(failure.Ready) as refusal:
                    checked(target)
                self.assertIsInstance(refusal.exception.__cause__, TagCompositionError)
                self.assertEqual(created, [])
                self.assertEqual(tuple(type.__subclasses__(Pin)), before)
                self.assertEqual(target in checked[:], mark is Post)

    def test_observations_cannot_create_or_change_top_metaclasses(self):
        for base in (type(Tag), type(Pin)):
            meta = type(base)("CustomMeta", (base,), {"note": "original"})
            acts = (
                    lambda: type(meta)("CreatedMeta", (meta,), {}),
                    lambda: setattr(meta, "note", "changed"),
                    lambda: delattr(meta, "note"),
                    )
            for mark, failure in (
                    (Pre, Precondition),
                    (Post, TagPostconditionError),
                    (Record, TagCompositionError),
                    ):
                for act in acts:
                    with self.subTest(base=base, mark=mark, act=act):
                        def Ready(target):
                            try:
                                act()
                            except TagCompositionError:
                                pass
                            return True

                        checked = type("Checked", (Tag,), {"Ready": mark(Ready)})
                        expected = failure if mark is Record else failure.Ready
                        with self.assertRaises(expected):
                            checked(Host())
                        self.assertEqual(meta.note, "original")
                        self.assertEqual(type.__subclasses__(meta), [])

    def test_refused_modifiers_do_not_read_their_targets_metadata(self):
        for modifier in (Constant, Rip, Tool(Host)):
            with self.subTest(modifier=modifier):
                reads = []

                class Callable:
                    def __call__(self, target):
                        return True

                    def __getattribute__(self, name):
                        reads.append(name)
                        raise AssertionError("a refused modifier inspected its target")

                supplied = Callable()

                class Refused(Tag):
                    @Pre
                    def Ready(target):
                        try:
                            modifier(supplied)
                        except TagCompositionError:
                            pass
                        return True

                with self.assertRaises(Precondition.Ready) as refusal:
                    Refused(Host())
                self.assertIsInstance(refusal.exception.__cause__, TagCompositionError)
                self.assertEqual(reads, [])
                self.assertEqual(object.__getattribute__(supplied, "__dict__"), {})

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

    def test_saved_context_releases_old_ambient_values_after_observation(self):
        for mark in (Pre, Post, Record):
            with self.subTest(mark=mark):
                saved = []
                ambient = ContextVar("observation_ambient")
                ambient_value = Host()
                reference = weakref.ref(ambient_value)
                context = Context()
                context.run(ambient.set, ambient_value)

                def Ready(target):
                    saved.append(copy_context())
                    return True

                checked = type("Checked", (Tag,), {"Ready": mark(Ready)})
                target = Host()
                context.run(checked, target)
                self.assertEqual(len(saved), 1)
                saved[0].run(ambient.set, None)
                del ambient_value, context
                gc.collect()
                gc.collect()
                self.assertIsNone(reference())

                class Known(Tag):
                    pass

                other = Host()
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


if __name__ == "__main__":
    unittest.main()
