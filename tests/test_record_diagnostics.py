"""Record failures identify the declaration without callable metadata."""

from __future__ import annotations

from inspect import Parameter, Signature
import unittest

from TopKit import Pin, Record, Tag, TagCompositionError, TagResolutionError


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
    def test_failing_callable_names_record_and_preserves_original_cause(self):
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

                    with self.assertRaises(TagCompositionError) as caught:
                        Prepared(_target(pinned), seed=23)

                    self.assertIs(caught.exception.__cause__, original)
                    self.assertEqual(
                            str(caught.exception),
                            "Record Prepared.balance could not be materialized:"
                            " ValueError: value cannot be calculated",
                            )
                    self.assertEqual(events, [23])
                    self.assertEqual(vars(builder), original_namespace)

    def test_aliased_function_reports_declaration_without_renaming_it(self):
        original = RuntimeError("builder failed")

        def Implementation(agent):
            raise original

        metadata = Implementation.__name__, Implementation.__qualname__

        class Prepared(Tag):
            balance = Record(Implementation)

        with self.assertRaises(TagCompositionError) as caught:
            Prepared(Host())

        self.assertEqual(
                str(caught.exception),
                "Record Prepared.balance could not be materialized:"
                " RuntimeError: builder failed",
                )
        self.assertIs(caught.exception.__cause__, original)
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

    def test_top_failures_remain_the_same_exception(self):
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                original = TagResolutionError("query failed")

                def fail(agent, seed):
                    raise original

                class Prepared(Tag):
                    balance = Record(_Builder(fail, True))

                if pinned:
                    Prepared = Pin(Prepared)
                with self.assertRaises(TagResolutionError) as caught:
                    Prepared(_target(pinned))
                self.assertIs(caught.exception, original)
                self.assertIsNone(caught.exception.__cause__)

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
                with self.assertRaises(Stop) as caught:
                    Prepared(_target(pinned))
                self.assertIs(caught.exception, original)

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
                with self.assertRaises(TagCompositionError) as caught:
                    prepared(_target(pinned))
                self.assertIs(caught.exception.__cause__, original)
                self.assertEqual(
                        str(caught.exception),
                        "Record Prepared.balance could not be materialized:"
                        " ValueError: builder failed",
                        )

    def test_unprintable_exception_still_has_the_original_cause(self):
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
                with self.assertRaises(TagCompositionError) as caught:
                    Prepared(_target(pinned))
                self.assertIs(caught.exception.__cause__, original)
                self.assertEqual(
                        str(caught.exception),
                        "Record Prepared.balance could not be materialized:"
                        " Unprintable: <exception text unavailable>",
                        )


if __name__ == "__main__":
    unittest.main()
