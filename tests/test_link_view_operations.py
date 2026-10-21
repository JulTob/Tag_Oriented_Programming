"""A Pair-view Operation follows the current Link and current credential."""

import asyncio
import inspect
import unittest

from TopKit import (Action, Link, Operation, Public, Report, Rip, Secret, Tag,
                    TagArrestedAccessError, TagCompositionError,
                    TagResolutionError, agent, contact)


class Host:
    pass


class LinkViewOperationTests(unittest.TestCase):
    def Inventory(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Report
                def capacity(link):
                    return 2

                @Operation
                def Count(link):
                    return len(link[:])

                @Public
                @Operation
                def Identify(link, caller, prefix="item"):
                    return prefix, link, caller

                @Secret
                @Operation
                def Hidden(link):
                    return link

            @Action
            def Capture(owner, item):
                return owner.Carries[item].Hidden

            @Action
            def Invoke(owner, call):
                return call()

        return Inventory

    def test_public_caller_reports_and_call_metadata(self):
        inventory = self.Inventory()
        owner, item = Host(), Host()
        inventory(owner)
        owner.Carries(item)
        view = owner.Carries[item]
        self.assertEqual(view.Count(), 1)
        self.assertEqual(view.Identify(), ("item", owner.Carries, item))
        self.assertEqual(item.Identify("carried"), ("carried", owner.Carries, item))
        self.assertEqual(view.Count, view.Count)
        self.assertEqual(hash(view.Count), hash(view.Count))
        self.assertEqual(view.Count.__name__, "Count")
        self.assertIn("Count", repr(view.Count))
        self.assertEqual(str(inspect.signature(view.Count)), "()")
        self.assertEqual(str(inspect.signature(view.Identify)), "(prefix='item')")
        self.assertEqual(view.capacity, 2)
        owner.Carries.capacity = 3
        self.assertEqual(view.capacity, 3)

    def test_saved_operation_follows_current_binding_and_relink(self):
        inventory = self.Inventory()
        owner, item = Host(), Host()
        inventory(owner)
        owner.Carries(item)
        view = owner.Carries[item]
        saved = view.Count
        owner.Carries.Count = Operation(lambda link: len(link[:]) + 10)
        self.assertEqual(saved(), 11)
        del owner.Carries[item]
        with self.assertRaises(TagResolutionError):
            saved()
        self.assertEqual(owner.Carries.Count(), 10)  # direct Tag scope stays independent
        owner.Carries(item)
        self.assertEqual(saved(), 11)
        self.assertEqual(saved, view.Count)

    def test_secret_handle_requires_its_owners_current_door(self):
        inventory = self.Inventory()
        owner, item = Host(), Host()
        inventory(owner)
        owner.Carries(item)
        with self.assertRaises(AttributeError):
            _ = owner.Carries[item].Hidden
        saved = owner.Capture(item)
        with self.assertRaises(AttributeError):
            saved()
        self.assertIs(owner.Invoke(saved), owner.Carries)
        del owner.Carries[item]
        owner.Carries(item)
        with self.assertRaises(AttributeError):
            saved()
        self.assertIs(owner.Invoke(saved), owner.Carries)

    def test_operation_cannot_return_after_ending_its_pair(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Public
                @Operation
                def Leave(link, caller):
                    del link[caller]
                    return "must not escape"
        owner, item = Host(), Host()
        Inventory(owner)
        owner.Carries(item)
        with self.assertRaises(TagResolutionError):
            owner.Carries[item].Leave()
        self.assertNotIn(item, owner.Carries[:])

    def test_lazy_operation_checks_membership_before_each_resume(self):
        turns = []
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Operation
                def Steps(link):
                    turns.append(1)
                    yield 1
                    turns.append(2)
                    yield 2
        owner, item = Host(), Host()
        Inventory(owner)
        owner.Carries(item)
        result = owner.Carries[item].Steps()
        self.assertEqual(next(result), 1)
        del owner.Carries[item]
        with self.assertRaises(TagResolutionError):
            next(result)
        self.assertEqual(turns, [1])
        owner.Carries(item)
        self.assertEqual(next(result), 2)
        result.close()

    def test_async_operation_checks_membership_before_each_resume(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Operation
                async def Values(link):
                    yield 1
                    yield 2
        async def Run():
            owner, item = Host(), Host()
            Inventory(owner)
            owner.Carries(item)
            result = owner.Carries[item].Values()
            self.assertEqual(await anext(result), 1)
            del owner.Carries[item]
            with self.assertRaises(TagResolutionError):
                await anext(result)
            owner.Carries(item)
            self.assertEqual(await anext(result), 2)
            await result.aclose()
        asyncio.run(Run())

    def test_coroutine_operation_keeps_task_support_and_live_membership(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Operation
                async def Count(link):
                    await asyncio.sleep(0)
                    return len(link[:])
        async def Run():
            owner, item = Host(), Host()
            Inventory(owner)
            owner.Carries(item)
            view = owner.Carries[item]
            self.assertEqual(await asyncio.create_task(view.Count()), 1)
            paused = view.Count()
            del owner.Carries[item]
            with self.assertRaises(TagResolutionError):
                await paused
            owner.Carries(item)
            paused.close()
        asyncio.run(Run())

    def test_lazy_secret_operation_rechecks_owners_door(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Secret
                @Operation
                def Hidden(link):
                    yield 1
                    yield 2

            @Action
            def Start(owner, item):
                return owner.Carries[item].Hidden()

            @Action
            def Advance(owner, result):
                return next(result)

            @Action
            def Finish(owner, result):
                result.close()

        owner, item = Host(), Host()
        Inventory(owner)
        owner.Carries(item)
        result = owner.Start(item)
        with self.assertRaises(AttributeError):
            next(result)
        self.assertEqual(owner.Advance(result), 1)
        with self.assertRaises(AttributeError):
            next(result)
        self.assertEqual(owner.Advance(result), 2)
        owner.Finish(result)

    def test_direct_secret_operation_result_keeps_owners_door(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Secret
                @Operation
                def Hidden(link):
                    yield "secret"

            @Action
            def Start(owner):
                return owner.Carries.Hidden()

            @Action
            def Advance(owner, result):
                return next(result)

            @Action
            def Finish(owner, result):
                result.close()

        owner = Host()
        Inventory(owner)
        result = owner.Start()
        with self.assertRaises(AttributeError):
            next(result)
        self.assertEqual(owner.Advance(result), "secret")
        owner.Finish(result)

    def test_secret_pair_action_result_keeps_owners_door(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Secret
                @Action
                def Hidden(owner, target):
                    yield "secret"

            @Action
            def Start(owner, item):
                return owner.Carries[item].Hidden()

            @Action
            def Advance(owner, result):
                return next(result)

            @Action
            def Finish(owner, result):
                result.close()

        owner, item = Host(), Host()
        Inventory(owner)
        owner.Carries(item)
        result = owner.Start(item)
        with self.assertRaises(AttributeError):
            next(result)
        self.assertEqual(owner.Advance(result), "secret")
        owner.Finish(result)

    def test_secret_operation_presence_uses_owners_door(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Secret
                @Operation
                def Hidden(link):
                    return "secret"

            @Action
            def Knows(owner, item):
                return "Hidden" @ owner.Carries[item]

        owner, item = Host(), Host()
        Inventory(owner)
        owner.Carries(item)
        self.assertFalse("Hidden" @ owner.Carries[item])
        self.assertTrue(owner.Knows(item))

    def test_operation_checks_owner_custody_before_body_runs(self):
        fail = [True]
        class Cleanup(Tag):
            @Rip
            def Leave(owner):
                if fail[0]:
                    raise ValueError("cleanup blocked")
        inventory = self.Inventory()
        owner, item = Host(), Host()
        inventory(owner)
        Cleanup(owner)
        owner.Carries(item)
        saved = owner.Carries[item].Count
        with self.assertRaises(TagCompositionError):
            del Cleanup[owner]
        with self.assertRaises(TagArrestedAccessError):
            saved()
        fail[0] = False
        self.assertEqual(saved(), 1)

    def test_opaque_operation_result_does_not_compare_its_type(self):
        class Meta(type):
            def __eq__(kind, other):
                raise AssertionError("operation values are opaque")
        class Value(metaclass=Meta):
            pass
        value = Value()
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Operation
                def Value(link):
                    return value
        owner, item = Host(), Host()
        Inventory(owner)
        owner.Carries(item)
        self.assertIs(owner.Carries[item].Value(), value)


if __name__ == "__main__":
    unittest.main()
