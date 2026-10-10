"""Protocol signatures are memoized by callable identity without ownership."""

from dataclasses import dataclass
import gc
import inspect
import unittest
from unittest.mock import patch
import weakref

from TopKit import Action, Imprint, Pin, Pre, Record, Tag, Underlay
from TopKit import declarations


class Host:
    pass


class NonWeakGate:
    __slots__ = ("__dict__",)

    def __call__(self, agent, *, allowed=True):
        return allowed


class NonWeakRecord:
    __slots__ = ("__dict__",)

    def __call__(self, agent, stored=None, *, increment=2):
        return (0 if stored is None else stored) + increment


class NonWeakImprint:
    __slots__ = ("__dict__",)

    def __call__(self, agent, *, trained=3):
        agent.trained = trained


class Equal:
    def __eq__(self, other):
        return isinstance(other, Equal)

    def __hash__(self):
        return 7


class Initial(Equal):
    def __call__(self, agent):
        return 42


class Evolving(Equal):
    def __call__(self, agent, stored=None):
        return stored


class ParameterCacheTests(unittest.TestCase):
    def test_nonweak_markable_protocols_work_on_objects_and_pinned_tags(self):
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                gate, builder, imprint = NonWeakGate(), NonWeakRecord(), NonWeakImprint()

                class Role(Tag):
                    Ready = Pre(gate)
                    total = Record(builder)
                    Train = Imprint(imprint)

                if pinned:
                    Role = Pin(Role)

                    class Target(Tag):
                        total = 10

                    agent = Target
                else:
                    agent = Host()
                    agent.total = 10

                before = [dict(vars(function)) for function in (gate, builder, imprint)]
                Role(agent, increment=7, trained=5)
                self.assertEqual(agent.total, 17)
                self.assertEqual(agent.trained, 5)
                del Role[agent]
                Role(agent)
                self.assertEqual(agent.total, 19)
                self.assertEqual(agent.trained, 3)
                self.assertEqual(before, [dict(vars(function))
                                          for function in (gate, builder, imprint)])

    def test_unhashable_dataclass_preconditions_and_records_work(self):
        @dataclass
        class Ready:
            def __call__(self, agent):
                return True

        @dataclass
        class Value:
            def __call__(self, agent, stored=None):
                return (0 if stored is None else stored) + 1

        class Role(Tag):
            Gate = Pre(Ready())
            total = Record(Value())

        agent = Host()
        Role(agent)
        self.assertEqual(agent.total, 1)
        del Role[agent]
        Role(agent)
        self.assertEqual(agent.total, 2)

    def test_equal_distinct_record_builders_keep_their_own_stored_seats(self):
        class First(Tag):
            value = Record(Initial())

        class Second(Tag):
            value = Record(Evolving())

        first, second = Host(), Host()
        second.value = 91
        First(first)
        Second(second)
        self.assertEqual(first.value, 42)
        self.assertEqual(second.value, 91)

    def test_cache_never_calls_the_callable_hash_or_equality(self):
        class PureIdentity:
            def __hash__(self):
                raise AssertionError("the signature cache called __hash__")

            def __eq__(self, other):
                raise AssertionError("the signature cache called __eq__")

            def __call__(self, agent, stored=None, *, increment=2):
                return (0 if stored is None else stored) + increment

        builder = PureIdentity()

        class Role(Tag):
            total = Record(builder)

        agent = Host()
        Role(agent, increment=4)
        del Role[agent]
        Role(agent)
        self.assertEqual(agent.total, 6)
        self.assertIs(declarations._parameters_of(builder),
                      declarations._parameters_of(builder))

    def test_a_nonweak_underlay_callable_keeps_its_declared_second_seat(self):
        class Extension:
            __slots__ = ("__dict__",)

            def __call__(self, agent, previous, offset=3):
                return previous() + offset

        class Base(Tag):
            def Value(agent, offset=3):
                return 4

        class Shape(Base):
            Value = Underlay(Action(Extension()))

        agent = Host()
        Shape(agent)
        self.assertEqual(agent.Value(), 7)
        self.assertEqual(agent.Value(offset=6), 10)

    def test_named_inputs_defaults_and_extra_keywords_keep_their_policy(self):
        class Builder:
            def __hash__(self):
                raise AssertionError("hash ran")

            def __call__(self, agent, stored=None, required=None, *, factor=2, **extra):
                return stored, required, factor, extra

        class Role(Tag):
            value = Record(Builder())

        agent = Host()
        agent.value = 9
        Role(agent, required=7, unknown="kept")
        self.assertEqual(agent.value, (9, 7, 2, {"unknown": "kept"}))

    def test_weak_identity_cache_preserves_first_signature_inspection(self):
        def Protocol(agent, *, initial=3):
            return initial

        with patch.object(declarations, "signature", wraps=inspect.signature) as inspect_once:
            first = declarations._parameters_of(Protocol)
            Protocol.__signature__ = inspect.Signature([
                inspect.Parameter("agent", inspect.Parameter.POSITIONAL_OR_KEYWORD),
                inspect.Parameter("later", inspect.Parameter.KEYWORD_ONLY),
            ])
            second = declarations._parameters_of(Protocol)

        self.assertIs(second, first)
        self.assertEqual(inspect_once.call_count, 1)
        self.assertEqual(first.named, (("agent", False), ("initial", True)))

    def test_nonweak_callables_are_inspected_without_memoization(self):
        function = NonWeakGate()
        before = dict(vars(function))
        with patch.object(declarations, "signature", wraps=inspect.signature) as inspect_each:
            first = declarations._parameters_of(function)
            second = declarations._parameters_of(function)

        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertEqual(inspect_each.call_count, 2)
        self.assertEqual(vars(function), before)

    def test_a_stale_identity_slot_does_not_supply_another_callables_signature(self):
        previous, current = Initial(), Evolving()
        declarations._parameters_of(previous)
        previous_entry = declarations._parameter_cache[id(previous)]
        key = id(current)
        declarations._parameter_cache[key] = previous_entry

        try:
            spec = declarations._parameters_of(current)
            self.assertEqual(spec.positional, 2)
            self.assertIs(declarations._parameter_cache[key][0](), current)
        finally:
            declarations._parameter_cache.pop(key, None)

    def test_an_expired_callback_cannot_delete_a_replacement_identity_entry(self):
        previous, current = Initial(), Evolving()
        declarations._parameters_of(previous)
        declarations._parameters_of(current)
        key = id(previous)
        previous_reference = declarations._parameter_cache[key][0]
        replacement = declarations._parameter_cache[id(current)]
        declarations._parameter_cache[key] = replacement

        try:
            del previous
            gc.collect()
            self.assertIsNone(previous_reference())
            self.assertIs(declarations._parameter_cache[key], replacement)
        finally:
            declarations._parameter_cache.pop(key, None)

    def test_a_callable_closure_and_its_owners_are_collectible(self):
        def create():
            agent = Host()

            def Protocol(receiver, *, amount=2):
                return agent, role, amount

            role = type("Ephemeral", (Tag,), {"Calculate": Action(Protocol)})
            agent.protocol = Protocol
            spec = declarations._parameters_of(Protocol)
            return ((weakref.ref(Protocol), weakref.ref(agent), weakref.ref(role)),
                    spec, id(Protocol))

        references, spec, key = create()
        gc.collect()
        gc.collect()
        self.assertTrue(all(reference() is None for reference in references))
        self.assertNotIn(key, declarations._parameter_cache)
        self.assertEqual(spec.named, (("receiver", False), ("amount", True)))

    def test_a_parameter_identifier_backreference_is_copied_as_plain_text(self):
        class Name(str):
            def __str__(self):
                raise AssertionError("an identifier is not a user formatter")

        def create():
            def Protocol(agent, **inputs):
                return inputs.get("count", 9)

            name = Name("count")
            name.owner = Protocol
            Protocol.__signature__ = inspect.Signature([
                inspect.Parameter("agent", inspect.Parameter.POSITIONAL_OR_KEYWORD),
                inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, default=9),
            ])
            spec = declarations._parameters_of(Protocol)
            return weakref.ref(Protocol), spec

        reference, spec = create()
        gc.collect()
        gc.collect()
        self.assertIsNone(reference())
        self.assertTrue(all(type(name) is str for name, _ in spec.named))

    def test_copied_parameter_identifiers_still_bind_named_inputs_and_defaults(self):
        class Name(str):
            def __str__(self):
                raise AssertionError("an identifier is not a user formatter")

        def Calculate(agent, **inputs):
            return inputs.get("count", 9)

        name = Name("count")
        name.owner = Calculate
        Calculate.__signature__ = inspect.Signature([
            inspect.Parameter("agent", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, default=9),
        ])

        class Role(Tag):
            total = Record(Calculate)

        first, second = Host(), Host()
        Role(first)
        Role(second, count=12)
        self.assertEqual(first.total, 9)
        self.assertEqual(second.total, 12)


if __name__ == "__main__":
    unittest.main()
