"""Ordinary acts retry saved cleanup; custody does not block entered exits."""

import asyncio
import gc
import inspect
import unittest
import weakref

from TopKit import Action, Contract, Operation, Pin, Post, Record, Report, Rip, Tag
from TopKit.arrest import _arrest_of, _rip_door, _safehouse
from TopKit import TagArrestedAccessError, TagCompositionError
from TopKit.lifecycle import _retry_arrested


class Host:
    value = 7


class ArrestGuardTests(unittest.TestCase):

    def setUp(self):
        self.addCleanup(_safehouse.clear)

    def Role(self):
        flag = {"fail": True, "calls": 0}
        class Role(Tag):
            @Action
            def Work(agent):
                return "work"
            @Rip
            def Leave(agent):
                flag["calls"] += 1
                if flag["fail"]:
                    raise ValueError("cleanup blocked")
        return Role, flag

    def Arrest(self, Role, agent):
        with self.assertRaises(TagCompositionError):
            del Role[agent]
        self.assertIsNotNone(_arrest_of(agent))

    def test_saved_action_retries_before_call_and_preserves_original_cause(self):
        Role, flag = self.Role()
        agent = Host()
        Role(agent)
        work = agent.Work
        self.Arrest(Role, agent)
        with self.assertRaises(TagArrestedAccessError) as error:
            work()
        self.assertIsInstance(error.exception.__cause__, ValueError)
        self.assertEqual(flag["calls"], 2)
        flag["fail"] = False
        self.assertEqual(work(), "work")
        self.assertIsNone(_arrest_of(agent))

    def test_host_reads_and_writes_retry_and_remain_available_inside_rip(self):
        Role, flag = self.Role()
        agent = Host()
        Role(agent)
        self.Arrest(Role, agent)
        for act in (lambda: agent.value, lambda: setattr(agent, "value", 9), lambda: delattr(agent, "value")):
            with self.assertRaises(TagArrestedAccessError):
                act()
        with _rip_door(agent):
            agent.value = 11
            self.assertEqual(agent.value, 11)
            del agent.value
            self.assertEqual(agent.value, 7)
        flag["fail"] = False
        self.assertEqual(agent.value, 7)
        self.assertIsNone(_arrest_of(agent))

    def test_bool_does_not_retry_and_arrest_is_separate_from_broken_field(self):
        Role, flag = self.Role()
        checks = []
        ready = {"value": True}
        class Fighter(Tag):
            @Post
            def Ready(agent):
                checks.append(True)
                return ready["value"]
        agent = Host()
        Role(agent)
        Fighter(agent)
        ready["value"] = False
        checks.clear()
        self.Arrest(Role, agent)
        before = flag["calls"]
        self.assertFalse(bool(agent))
        self.assertFalse(agent in Fighter)
        self.assertFalse(agent in ~Fighter)
        self.assertIn(agent, Fighter[:])
        self.assertEqual(list(Fighter), [])
        self.assertEqual(list(~Fighter), [])
        self.assertEqual(checks, [])
        self.assertEqual(flag["calls"], before)

    def test_host_hooks_are_preserved_and_gate_survives_later_tagging(self):
        events = []
        class Logging:
            def __getattribute__(agent, name):
                events.append(("read", name))
                return object.__getattribute__(agent, name)
            def __setattr__(agent, name, value):
                events.append(("write", name))
                object.__setattr__(agent, name, value)
        Role, flag = self.Role()
        class Later(Tag):
            pass
        agent = Logging()
        Role(agent)
        flag["fail"] = False
        del Role[agent]
        Later(agent)
        agent.value = 9
        self.assertEqual(agent.value, 9)
        self.assertIn(("write", "value"), events)
        self.assertIn(("read", "value"), events)
        Role(agent)
        flag["fail"] = True
        self.Arrest(Role, agent)
        with self.assertRaises(TagArrestedAccessError):
            _ = agent.value

    def test_captured_operation_keeps_binding_metadata_and_custody_check(self):
        class Fighter(Tag):
            @Operation
            def Work(tag, amount=1):
                return amount
        @Pin
        class Registered(Tag):
            @Rip
            def Leave(tag):
                raise ValueError("registry blocked")
        saved = Fighter.Work
        self.assertIs(saved.__self__, Fighter)
        self.assertEqual(saved, Fighter.Work)
        self.assertEqual(hash(saved), hash(Fighter.Work))
        self.assertEqual(str(inspect.signature(saved)), "(amount=1)")
        Registered(Fighter)
        self.Arrest(Registered, Fighter)
        with self.assertRaises(TagArrestedAccessError):
            saved()
        with _rip_door(Fighter):
            self.assertEqual(saved(4), 4)

    def test_saved_generator_checks_each_resume_and_can_run_from_rip(self):
        Role, flag = self.Role()
        class Steps(Tag):
            @Action
            def Walk(agent):
                yield 1
                yield 2
        agent = Host()
        Role(agent)
        Steps(agent)
        result = agent.Walk()
        self.assertEqual(next(result), 1)
        self.Arrest(Role, agent)
        with self.assertRaises(TagArrestedAccessError):
            next(result)
        with _rip_door(agent):
            self.assertEqual(next(result), 2)
            result.close()
        flag["fail"] = False
        _retry_arrested(agent)

    def test_async_generator_keeps_normal_protocol_and_guards_resumption(self):
        async def Run():
            Role, flag = self.Role()
            class Steps(Tag):
                @Action
                async def Walk(agent):
                    yield 1
                    yield 2
            agent = Host()
            Role(agent)
            Steps(agent)
            result = agent.Walk()
            self.assertFalse(inspect.isasyncgen(result))
            self.assertEqual(await anext(result), 1)
            self.Arrest(Role, agent)
            with self.assertRaises(TagArrestedAccessError):
                await anext(result)
            with _rip_door(agent):
                self.assertEqual(await anext(result), 2)
                await result.aclose()
            flag["fail"] = False
            _retry_arrested(agent)
        asyncio.run(Run())

    def test_generator_close_checks_custody_after_source_cleanup(self):
        Role, flag = self.Role()
        class Steps(Tag):
            @Action
            def Walk(agent):
                try:
                    yield 1
                finally:
                    try:
                        del Role[agent]
                    except TagCompositionError:
                        pass
        agent = Host()
        Role(agent)
        Steps(agent)
        result = agent.Walk()
        self.assertEqual(next(result), 1)
        with self.assertRaises(TagArrestedAccessError):
            result.close()
        flag["fail"] = False
        _retry_arrested(agent)

    def test_entered_host_exit_cleans_up_without_masking_rip_failure(self):
        events = []
        class Resource:
            value = 7
            def __enter__(agent):
                events.append("enter")
                return agent
            def __exit__(agent, *error):
                events.append(("exit", agent.value))
                agent.cleaned = True
        Role, flag = self.Role()
        agent = Resource()
        Role(agent)
        with self.assertRaises(TagCompositionError):
            with agent:
                del Role[agent]
        self.assertEqual(events, ["enter", ("exit", 7)])
        self.assertIsNotNone(_arrest_of(agent))
        self.assertFalse(bool(agent))
        with self.assertRaises(TagArrestedAccessError):
            agent.__exit__(None, None, None)
        flag["fail"] = False
        self.assertTrue(agent.cleaned)

    def test_entered_async_host_exit_keeps_cleanup_door_across_await(self):
        async def Run():
            events = []
            class Resource:
                value = 7
                async def __aenter__(agent):
                    return agent
                async def __aexit__(agent, *error):
                    await asyncio.sleep(0)
                    events.append(agent.value)
                    agent.cleaned = True
            Role, flag = self.Role()
            agent = Resource()
            Role(agent)
            with self.assertRaises(TagCompositionError):
                async with agent:
                    del Role[agent]
            self.assertEqual(events, [7])
            self.assertIsNotNone(_arrest_of(agent))
            flag["fail"] = False
            self.assertTrue(agent.cleaned)
        asyncio.run(Run())

    def test_saved_tag_view_records_reports_presence_and_operations_obey_arrest(self):
        class Fighter(Tag):
            @Record
            def charge(agent):
                return 6
            @Report
            def level(tag):
                return 3
            @Operation
            def Work(tag, amount=1):
                return amount
        Role, flag = self.Role()
        agent = Host()
        Fighter(agent)
        Role(agent)
        view = Fighter[agent]
        saved = view.Work
        self.Arrest(Role, agent)
        for act in (lambda: view.charge, lambda: view.level,
                    lambda: "charge" @ view, lambda: saved(4)):
            with self.assertRaises(TagArrestedAccessError):
                act()
        with _rip_door(agent):
            self.assertEqual(view.charge, 6)
            self.assertEqual(view.level, 3)
            self.assertTrue("charge" @ view)
            self.assertEqual(saved(4), 4)
        flag["fail"] = False
        self.assertEqual(saved(5), 5)

    def test_saved_view_and_callable_follow_current_application_after_retag(self):
        class Role(Tag):
            @Record
            def charge(agent, *, charge):
                return charge
            def Work(agent):
                return agent.charge
        agent = Host()
        Role(agent, charge=6)
        view = Role[agent]
        saved = view.Work
        del Role[agent]
        from TopKit import TagResolutionError
        with self.assertRaises(TagResolutionError):
            saved()
        Role(agent, charge=9)
        self.assertEqual(view.charge, 9)
        self.assertEqual(saved(), 9)
        self.assertEqual(view.Work.__func__, saved.__func__)

    def test_saved_view_and_callable_do_not_own_agent(self):
        class Role(Tag):
            def Work(agent):
                return "work"
        agent = Host()
        Role(agent)
        view = Role[agent]
        saved = view.Work
        held = weakref.ref(agent)
        del agent
        gc.collect()
        self.assertIsNone(held())
        with self.assertRaises(ReferenceError):
            saved()

    def test_view_call_comparison_hash_and_repr_use_agent_identity(self):
        class IdentityOnly:
            def __eq__(agent, other):
                raise AssertionError("Host equality must not compare handles")
            def __hash__(agent):
                raise AssertionError("Host hashing must not hash handles")
        class Role(Tag):
            @Action
            def Work(agent, amount=1):
                """Work on the current Agent."""
                return amount
        agent, other = IdentityOnly(), IdentityOnly()
        Role(agent)
        Role(other)
        saved = Role[agent].Work
        self.assertEqual(saved, Role[agent].Work)
        self.assertEqual(hash(saved), hash(Role[agent].Work))
        self.assertNotEqual(saved, Role[other].Work)
        self.assertEqual({saved: "current"}[Role[agent].Work], "current")
        self.assertIn("Role.Work", repr(saved))
        self.assertIs(saved.__self__, agent)
        self.assertEqual(str(inspect.signature(saved)), "(amount=1)")
        self.assertEqual(saved.__doc__, "Work on the current Agent.")
        del Role[agent]
        Role(agent)
        self.assertEqual(saved, Role[agent].Work)

    def test_view_reports_read_current_false_none_and_deleted_tag_value(self):
        class Role(Tag):
            @Report
            def signal(tag):
                return "ready"
        agent = Host()
        Role(agent)
        view = Role[agent]
        self.assertEqual(view.signal, "ready")
        Role.signal = False
        self.assertIs(view.signal, False)
        self.assertTrue("signal" @ view)
        Role.signal = None
        self.assertIsNone(view.signal)
        self.assertTrue("signal" @ view)
        del Role.signal
        with self.assertRaises(AttributeError):
            _ = view.signal
        self.assertFalse("signal" @ view)

    def test_saved_view_operation_resolves_current_pin_replacement(self):
        class Role(Tag):
            @Operation
            def Work(tag, amount=1):
                return "original", tag, amount
        @Pin
        class Patch(Tag):
            @Action
            def Work(tag, amount=1):
                return "replacement", tag, amount
        agent = Host()
        Role(agent)
        saved = Role[agent].Work
        self.assertEqual(saved(2), ("original", Role, 2))
        Patch(Role)
        self.assertEqual(saved(3), ("replacement", Role, 3))

    def test_view_call_rechecks_membership_before_return(self):
        class Role(Tag):
            @Action
            def Leave(agent):
                del Role[agent]
                return "left"
        agent = Host()
        Role(agent)
        saved = Role[agent].Leave
        from TopKit import TagResolutionError
        with self.assertRaises(TagResolutionError):
            saved()
        self.assertNotIn(agent, Role[:])

    def test_view_operation_parks_started_result_before_arrest_denies_return(self):
        events = []
        Arresting, flag = self.Role()
        agent = Host()
        class Role(Tag):
            @Operation
            def Started(tag):
                def Source():
                    try:
                        yield 1
                        yield 2
                    finally:
                        events.append("closed")
                source = Source()
                next(source)
                try:
                    del Arresting[agent]
                except TagCompositionError:
                    pass
                return source
        Role(agent)
        Arresting(agent)
        saved = Role[agent].Started
        with self.assertRaises(TagArrestedAccessError):
            saved()
        gc.collect()
        self.assertEqual(events, [])
        flag["fail"] = False
        _retry_arrested(agent)
        gc.collect()
        self.assertEqual(events, ["closed"])

    def test_saved_view_operation_checks_agent_and_tag_on_lazy_resume(self):
        class Role(Tag):
            @Operation
            def Steps(tag):
                yield 1
                yield 2
        AgentRole, flag = self.Role()
        agent = Host()
        Role(agent)
        AgentRole(agent)
        result = Role[agent].Steps()
        self.assertEqual(next(result), 1)
        self.Arrest(AgentRole, agent)
        with self.assertRaises(TagArrestedAccessError):
            next(result)
        with _rip_door(agent):
            self.assertEqual(next(result), 2)
            result.close()
        flag["fail"] = False
        _retry_arrested(agent)

        @Pin
        class Registry(Tag):
            @Rip
            def Leave(tag):
                raise ValueError("registry blocked")
        result = Role[agent].Steps()
        self.assertEqual(next(result), 1)
        Registry(Role)
        self.Arrest(Registry, Role)
        with self.assertRaises(TagArrestedAccessError):
            next(result)
        with _rip_door(Role):
            self.assertEqual(next(result), 2)
            result.close()

    def test_public_safehouse_query_is_live_and_separate_from_raw_membership(self):
        Role, flag = self.Role()
        agent = Host()
        Role(agent)
        house = Role[...]
        self.assertNotIn(agent, house)
        self.Arrest(Role, agent)
        self.assertIn(agent, house)
        self.assertIn(agent, Tag[...])
        self.assertEqual(list(house), [agent])
        self.assertNotIn(agent, Role[:])
        self.assertNotIn(agent, ~Role)
        flag["fail"] = False
        del Role[agent]
        self.assertNotIn(agent, house)
        self.assertEqual(len(house), 0)

    def test_whole_field_rip_revokes_every_member_before_first_protocol(self):
        events = []
        fail = {"value": True}
        class Role(Tag):
            @Rip
            def Leave(agent):
                events.append(len(Role[:]))
                if fail["value"]:
                    raise ValueError("blocked")
        first, second = Host(), Host()
        Role(first)
        Role(second)
        with self.assertRaises(TagCompositionError):
            del Role[:]
        self.assertEqual(events, [0])
        self.assertEqual(list(Role[:]), [])
        self.assertEqual(len(Role[...]), 2)
        # Either Agent may be explicitly retried: no Field-wide priority.
        fail["value"] = False
        del Role[second]
        self.assertNotIn(second, Role[...])
        self.assertIn(first, Role[...])
        del Role[first]
        self.assertEqual(list(Role[...]), [])



if __name__ == "__main__":
    unittest.main()
