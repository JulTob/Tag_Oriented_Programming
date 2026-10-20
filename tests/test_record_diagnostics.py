"""Record failures identify the declaration without callable metadata."""

from __future__ import annotations

from inspect import Parameter, Signature
import unittest
import warnings

from TopKit import (Pin, Record, Tag, TagCompositionError, TagResolutionError,
                    TagTrainingWarning)


class Host:
    pass


class Stop(BaseException):
    pass


class _Builder:
    __signature__ = Signature([
            Parameter("agent", Parameter.POSITIONAL_OR_KEYWORD),
            Parameter("seed", Parameter.KEYWORD_ONLY, default=19),
            ])

    def __init__(self, body, hostile=False):
        self.body = body
        self.hostile = hostile

    def __getattribute__(self, name):
        if name in ("__name__", "__qualname__") and object.__getattribute__(
                self, "hostile"):
            raise AssertionError("callable metadata must not be read")
        return object.__getattribute__(self, name)

    def __repr__(self):
        raise AssertionError("callable representation must not be read")

    def __call__(self, agent, *, seed=19):
        return self.body(agent, seed)


def _target(pinned):
    return type("Receiver", (Tag,), {}) if pinned else Host()


class RecordDiagnosticTests(unittest.TestCase):
    def assert_record_warning(self, tag, target, **inputs):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", TagTrainingWarning)
            self.assertIs(tag(target, **inputs), target)
        self.assertEqual(len(caught), 1)
        self.assertIn(target, tag[:])
        self.assertEqual(caught[0].message.kind, "Record")
        return caught[0].message

    def test_callable_builders_can_store_native_lazy_objects_as_data(self):
        events = []

        async def deferred():
            events.append("coroutine ran")

        def stream():
            events.append("generator ran")
            yield 1

        async def async_stream():
            events.append("async generator ran")
            yield 1

        for pinned in (False, True):
            for factory in (deferred, stream, async_stream):
                with self.subTest(pinned=pinned, kind=factory.__name__):
                    value = factory()
                    builder = Record(_Builder(lambda agent, seed: value, True))
                    prepared = type("Prepared", (Tag,), {"payload": builder})
                    if pinned:
                        prepared = Pin(prepared)
                    target = _target(pinned)
                    try:
                        prepared(target)
                        self.assertIn(target, prepared)
                        self.assertIs(target.payload, value)
                        self.assertEqual(events, [])
                        if factory is deferred:
                            self.assertIsNotNone(value.cr_frame)
                        elif factory is stream:
                            self.assertIsNotNone(value.gi_frame)
                        else:
                            self.assertFalse(value.ag_running)
                    finally:
                        if factory is not async_stream:
                            value.close()

    def test_failing_callable_names_record_without_retaining_original(self):
        for pinned in (False, True):
            for hostile in (False, True):
                with self.subTest(pinned=pinned, hostile=hostile):
                    events = []
                    original = ValueError("value cannot be calculated")

                    def fail(agent, seed):
                        events.append(seed)
                        raise original

                    builder = Record(_Builder(fail, hostile))
                    original_namespace = dict(vars(builder))

                    class Prepared(Tag):
                        balance = builder

                        @Record
                        def later(agent):
                            events.append("later")
                            return None

                    if pinned:
                        Prepared = Pin(Prepared)

                    target = _target(pinned)
                    issue = self.assert_record_warning(Prepared, target, seed=23)
                    self.assertIsNone(issue.failure.__cause__)
                    self.assertEqual(
                            str(issue.failure),
                            "Record Prepared.balance could not be materialized:"
                            " ValueError: value cannot be calculated",
                            )
                    self.assertEqual(issue.cause_type, "ValueError")
                    self.assertEqual(issue.cause_text,
                                     "value cannot be calculated")
                    self.assertEqual(events, [23, "later"])
                    self.assertIsNone(target.later)
                    self.assertFalse("balance" @ target)
                    self.assertEqual(vars(builder), original_namespace)

    def test_aliased_function_reports_declaration_without_renaming_it(self):
        original = RuntimeError("builder failed")

        def Implementation(agent):
            raise original

        metadata = Implementation.__name__, Implementation.__qualname__

        class Prepared(Tag):
            balance = Record(Implementation)

        issue = self.assert_record_warning(Prepared, Host())

        self.assertEqual(
                str(issue.failure),
                "Record Prepared.balance could not be materialized:"
                " RuntimeError: builder failed",
                )
        self.assertIsNone(issue.failure.__cause__)
        self.assertEqual(
                (Implementation.__name__, Implementation.__qualname__),
                metadata,
                )

    def test_successful_callables_keep_defaults_inputs_false_and_none(self):
        for pinned in (False, True):
            for value in (False, None, 0, 29):
                with self.subTest(pinned=pinned, value=value):
                    events = []

                    def calculate(agent, seed):
                        events.append(seed)
                        return value

                    class Prepared(Tag):
                        balance = Record(_Builder(calculate, True))

                    if pinned:
                        Prepared = Pin(Prepared)
                    target = _target(pinned)
                    self.assertIs(Prepared(target), target)
                    self.assertIs(target.balance, value)
                    self.assertTrue("balance" @ target)
                    self.assertEqual(events, [19])

    def test_top_failures_are_reported_as_training_failures(self):
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                original = TagResolutionError("query failed")

                def fail(agent, seed):
                    raise original

                class Prepared(Tag):
                    balance = Record(_Builder(fail, True))

                if pinned:
                    Prepared = Pin(Prepared)
                issue = self.assert_record_warning(Prepared, _target(pinned))
                self.assertEqual(issue.cause_type, "TagResolutionError")
                self.assertEqual(issue.cause_text, "query failed")
                self.assertIsNone(issue.failure.__cause__)

    def test_python_interruptions_remain_the_same_exception(self):
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                original = Stop()

                def fail(agent, seed):
                    raise original

                class Prepared(Tag):
                    balance = Record(_Builder(fail, True))

                if pinned:
                    Prepared = Pin(Prepared)
                target = _target(pinned)
                with self.assertRaises(Stop) as caught:
                    Prepared(target)
                self.assertIs(caught.exception, original)
                self.assertIn(target, Prepared[:])

    def test_declaration_name_text_never_runs_subclass_diagnostic_hooks(self):
        class Name(str):
            def __repr__(self):
                raise RuntimeError("name representation must not be read")

            def __format__(self, spec):
                raise RuntimeError("name formatting must not run")

        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                original = ValueError("builder failed")

                def calculate(agent):
                    raise original

                prepared = type("Prepared", (Tag,), {
                        Name("balance"): Record(calculate),
                        })
                if pinned:
                    prepared = Pin(prepared)
                issue = self.assert_record_warning(prepared, _target(pinned))
                self.assertIsNone(issue.failure.__cause__)
                self.assertEqual(
                        str(issue.failure),
                        "Record Prepared.balance could not be materialized:"
                        " ValueError: builder failed",
                        )

    def test_unprintable_exception_has_safe_warning_text(self):
        class Unprintable(ValueError):
            def __str__(self):
                raise RuntimeError("exception text cannot be calculated")

        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                original = Unprintable()

                def fail(agent, seed):
                    raise original

                class Prepared(Tag):
                    balance = Record(_Builder(fail, True))

                if pinned:
                    Prepared = Pin(Prepared)
                issue = self.assert_record_warning(Prepared, _target(pinned))
                self.assertIsNone(issue.failure.__cause__)
                self.assertEqual(issue.cause_text,
                                 "<exception text unavailable>")
                self.assertEqual(
                        str(issue.failure),
                        "Record Prepared.balance could not be materialized:"
                        " Unprintable: <exception text unavailable>",
                        )


if __name__ == "__main__":
    unittest.main()
