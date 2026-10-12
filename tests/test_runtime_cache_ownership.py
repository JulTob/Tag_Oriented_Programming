"""Shared runtime types must not make their original Hosts global roots."""

import gc
import unittest
import weakref

from TopKit import Action, Constant, Record, Rip, Secret, Tag, TagCompositionError
from TopKit import state as runtime


class RuntimeCacheOwnershipTests(unittest.TestCase):
    def setUp(self):
        class Role(Tag):
            @Action
            def Read(agent):
                return agent

        self.Role = Role

    def discard_entry(self, reference):
        # Also keep failing before-fix runs from retaining their test fixture.
        agent = reference()
        if agent is not None:
            key = runtime._type_key_of(runtime._state_of(agent))
            runtime._type_cache.pop(key, None)

    def temporary(self, ownership="closure", keep_action=False):
        if ownership == "metaclass":
            class Meta(type):
                def Owner(cls):
                    return agent

            class Host(metaclass=Meta):
                pass
        elif ownership == "default":
            owners = []

            class Host:
                def Owner(self, retained=owners):
                    return retained[0]
        else:
            class Host:
                def Owner(self):
                    return agent

        agent = Host()
        if ownership == "default":
            owners.append(agent)
        self.Role(agent)
        owner = Host.Owner() if ownership == "metaclass" else agent.Owner()
        self.assertIs(owner, agent)

        references = weakref.ref(Host), weakref.ref(agent), weakref.ref(type(agent))
        self.addCleanup(gc.collect)
        self.addCleanup(self.discard_entry, references[1])
        return references, agent.Read if keep_action else None

    def test_host_closures_defaults_and_metaclasses_do_not_root_agents(self):
        for ownership in ("closure", "default", "metaclass"):
            with self.subTest(ownership=ownership):
                references, _ = self.temporary(ownership)
                gc.collect()
                for label, reference in zip(("Host", "Agent", "runtime"), references):
                    self.assertIsNone(reference(), label)
                self.assertEqual(tuple(self.Role[:]), ())

    def test_a_retained_public_action_does_not_keep_a_host_cycle_alive(self):
        references, action = self.temporary(keep_action=True)
        gc.collect()
        for reference in references:
            self.assertIsNone(reference())
        with self.assertRaises(ReferenceError):
            action()

    def test_an_action_function_that_captures_its_agent_is_still_an_owner(self):
        # A weak receiver cannot undo ownership deliberately held by the body.
        # Isolate that limit from the separate declaration-scan cache (#95).
        class Host:
            pass

        def capture():
            agent = Host()
            self.Role(agent)

            def Read(receiving_agent, owner=agent):
                return owner

            return weakref.ref(agent), runtime._Bound(Read, agent)

        reference, action = capture()
        gc.collect()
        self.assertIsNotNone(reference())
        self.assertIs(action(), reference())
        del action
        gc.collect()
        self.assertIsNone(reference())

    def test_cyclic_cleanup_preserves_the_documented_weak_action_limit(self):
        calls = []

        class Cleaned(Tag):
            @Action
            def Read(agent):
                return agent

            @Rip
            def Leave(agent):
                calls.append("teardown")
                try:
                    agent.Read()
                except ReferenceError:
                    calls.append("weak Action expired")

        def create():
            class Host:
                def Owner(self):
                    return agent

            agent = Host()
            Cleaned(agent)
            return weakref.ref(agent)

        reference = create()
        gc.collect()
        self.assertIsNone(reference())
        self.assertEqual(calls, ["teardown", "weak Action expired"])
        self.assertEqual(tuple(Cleaned[:]), ())

    def test_distinct_identity_equal_hosts_do_not_share_a_runtime_type(self):
        class Equal(type):
            def __eq__(cls, other):
                return isinstance(other, Equal)

            def __hash__(cls):
                return 17

        class First(metaclass=Equal):
            def Kind(self):
                return "first"

        class Second(metaclass=Equal):
            def Kind(self):
                return "second"

        self.assertEqual(First, Second)
        first, second = First(), Second()
        self.Role(first)
        self.Role(second)
        self.assertIsNot(type(first), type(second))
        self.assertTrue(any(ancestor is First for ancestor in type(first).__mro__))
        self.assertTrue(any(ancestor is Second for ancestor in type(second).__mro__))
        self.assertEqual(first.Kind(), "first")
        self.assertEqual(second.Kind(), "second")

    def test_unhashable_hosts_can_use_the_identity_cache(self):
        class Unhashable(type):
            __hash__ = None

        class Host(metaclass=Unhashable):
            pass

        agent = Host()
        self.Role(agent)
        self.assertIs(agent.Read(), agent)
        self.assertTrue(any(ancestor is Host for ancestor in type(agent).__mro__))

    def test_live_runtime_type_keeps_its_host_and_is_shared(self):
        def create():
            class Host:
                pass

            agent = Host()
            self.Role(agent)
            return weakref.ref(Host), weakref.ref(agent), type(agent)

        host_reference, agent_reference, shared = create()
        gc.collect()
        self.assertIsNone(agent_reference())
        host = host_reference()
        self.assertIsNotNone(host)
        other = host()
        self.Role(other)
        self.assertIs(type(other), shared)
        key = runtime._type_key_of(runtime._state_of(other))
        self.assertIs(type(key[0]), int)
        self.assertEqual(key[0], id(host))
        self.assertIs(runtime._type_cache[key], shared)
        shared_reference = weakref.ref(shared)
        del host, other, shared
        gc.collect()
        self.assertIsNone(host_reference())
        self.assertIsNone(shared_reference())
        self.assertNotIn(key, runtime._type_cache)

    def test_same_host_and_facts_share_without_mutating_the_host(self):
        class Host:
            pass

        class Other(Tag):
            pass

        original = dict(vars(Host))
        first, second = Host(), Host()
        self.Role(first)
        Other(second)
        self.assertIs(type(first), type(second))
        self.assertEqual(dict(vars(Host)), original)

    def test_transient_host_churn_expires_the_weak_cache_entries(self):
        references = []
        for _ in range(100):
            current, _ = self.temporary()
            references.extend(current)
        gc.collect()
        self.assertTrue(all(reference() is None for reference in references))
        self.assertEqual(tuple(self.Role[:]), ())

    def test_secret_constant_and_context_type_facts_stay_distinct(self):
        class Host:
            pass

        class Context(Tag):
            @Constant
            @Secret
            @Record
            def code(agent):
                return 41

            @Constant
            @Action
            def Read(agent):
                return agent.code

            @Action
            def __enter__(agent):
                return agent.Read()

            @Action
            def __exit__(agent, kind, value, traceback):
                return False

        plain, first, second = Host(), Host(), Host()
        self.Role(plain)
        Context(first)
        Context(second)
        self.assertIsNot(type(plain), type(first))
        self.assertIs(type(first), type(second))
        with first as value:
            self.assertEqual(value, 41)
        with self.assertRaises(AttributeError):
            first.code
        self.assertFalse("code" @ first)
        with self.assertRaises(TagCompositionError):
            first.code = 42
        with self.assertRaises(TagCompositionError):
            del first.Read
        self.assertEqual(second.Read(), 41)


if __name__ == "__main__":
    unittest.main()
