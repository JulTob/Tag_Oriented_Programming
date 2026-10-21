"""Entered Link continuations may finish cleanup after successful unlinking."""

import asyncio
import gc
from contextvars import copy_context
import weakref
import unittest

from TopKit import (Action, Link, Operation, Public, Record, Rip, Secret, Tag,
                    TagArrestedAccessError, TagCompositionError, TagResolutionError,
                    agent, contact)


class Host:
    pass


class LinkEnteredCleanupTests(unittest.TestCase):
    def test_started_pair_action_can_close_after_unlink_and_collection(self):
        events = []
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Action
                def Read(owner, target):
                    try:
                        yield 'entered'
                    finally:
                        events.append('closed')
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        result = owner.Carries[target].Read()
        self.assertEqual(next(result), 'entered')
        del owner.Carries[target]
        gc.collect()
        for resume in (lambda: next(result), lambda: result.send(None),
                       lambda: result.throw(GeneratorExit)):
            with self.assertRaises(TagResolutionError):
                resume()
        result.close()
        self.assertEqual(events, ['closed'])
        result.close()  # a retained, disposed proxy is safely repeatable

    def test_started_pair_operation_can_close_after_unlink_and_collection(self):
        events = []
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Operation
                def Read(link):
                    try:
                        yield 'entered'
                    finally:
                        events.append('closed')
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        view = owner.Carries[target]
        result = view.Read()
        self.assertEqual(next(result), 'entered')
        del owner.Carries[target]
        gc.collect()
        with self.assertRaises(TagResolutionError):
            _ = view.Read
        result.close()
        self.assertEqual(events, ['closed'])

    def test_started_async_pair_action_can_aclose_after_unlink(self):
        async def Run():
            events = []
            class Inventory(Tag):
                @Link(agent, contact)
                class Carries(Tag):
                    @Action
                    async def Read(owner, target):
                        try:
                            yield 'entered'
                        finally:
                            await asyncio.sleep(0)
                            events.append('closed')
            owner, target = Host(), Host()
            Inventory(owner)
            owner.Carries(target)
            result = owner.Carries[target].Read()
            self.assertEqual(await anext(result), 'entered')
            del owner.Carries[target]
            gc.collect()
            await result.aclose()
            self.assertEqual(events, ['closed'])
        asyncio.run(Run())


    def test_cleanup_can_read_its_pair_resource_and_revokes_copied_context(self):
        events, contexts = [], []
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return "pack"

                @Action
                def Read():
                    try:
                        yield "entered"
                    finally:
                        events.append(agent.Carries[contact].slot)
                        contexts.append(copy_context())
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        view = owner.Carries[target]
        result = view.Read()
        next(result)
        del owner.Carries[target]
        gc.collect()
        result.close()
        self.assertEqual(events, ["pack"])
        with self.assertRaises(TagResolutionError):
            contexts[0].run(lambda: view.slot)
        with self.assertRaises(TagResolutionError):
            _ = view.slot

    def test_cleanup_keeps_fresh_pair_views_fresh_after_relink(self):
        events = []
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return target.slot

                @Action
                def Read(owner, target):
                    resource = owner.Carries[target].slot
                    try:
                        yield resource
                    finally:
                        events.append((resource, owner.Carries[target].slot))
        owner, target = Host(), Host()
        target.slot = "old"
        Inventory(owner)
        owner.Carries(target)
        view = owner.Carries[target]
        result = view.Read()
        self.assertEqual(next(result), "old")
        del owner.Carries[target]
        target.slot = "new"
        owner.Carries(target)
        result.close()
        self.assertEqual(events, [("old", "new")])
        self.assertEqual(view.slot, "new")

    def test_async_cleanup_keeps_resource_across_awaits_without_leaking_to_task(self):
        async def Run():
            events, tasks = [], []
            class Inventory(Tag):
                @Link(agent, contact)
                class Carries(Tag):
                    @Record
                    def slot(owner, target):
                        return "pack"

                    @Action
                    async def Read():
                        try:
                            yield "entered"
                        finally:
                            async def Outside():
                                try:
                                    agent.Carries[contact].slot
                                except (TagResolutionError, ReferenceError):
                                    events.append("task refused")
                            tasks.append(asyncio.create_task(Outside()))
                            await asyncio.sleep(0)
                            events.append(agent.Carries[contact].slot)
                            await asyncio.sleep(0)
                            events.append(agent.Carries[contact].slot)
            owner, target = Host(), Host()
            Inventory(owner)
            owner.Carries(target)
            result = owner.Carries[target].Read()
            await anext(result)
            del owner.Carries[target]
            gc.collect()
            await result.aclose()
            await asyncio.gather(*tasks)
            self.assertEqual(events, ["task refused", "pack", "pack"])
        asyncio.run(Run())

    def test_cleanup_does_not_authorize_an_unrelated_action_resume(self):
        events, other = [], []
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Action
                def Read(owner, target):
                    try:
                        yield "entered"
                    finally:
                        try:
                            next(other[0])
                        except TagResolutionError:
                            events.append("refused")
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        first, second = (owner.Carries[target].Read() for _ in range(2))
        next(first)
        next(second)
        other.append(second)
        del owner.Carries[target]
        first.close()
        second.close()
        self.assertEqual(events, ["refused", "refused"])

    def test_secret_action_cleanup_still_requires_owner_door(self):
        events = []
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Secret
                @Action
                def Read(owner, target):
                    try:
                        yield "entered"
                    finally:
                        events.append("closed")

            @Action
            def Start(owner, target):
                result = owner.Carries[target].Read()
                next(result)
                return result

            @Action
            def Finish(owner, result):
                result.close()
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        result = owner.Start(target)
        del owner.Carries[target]
        with self.assertRaises(AttributeError):
            result.close()
        self.assertEqual(events, [])
        owner.Finish(result)
        self.assertEqual(events, ["closed"])

    def test_secret_pair_operation_cleanup_still_requires_owner_door(self):
        events = []
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Secret
                @Operation
                def Read(link):
                    try:
                        yield "entered"
                    finally:
                        events.append("closed")

            @Action
            def Start(owner, target):
                result = owner.Carries[target].Read()
                next(result)
                return result

            @Action
            def Finish(owner, result):
                result.close()
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        result = owner.Start(target)
        del owner.Carries[target]
        with self.assertRaises(AttributeError):
            result.close()
        self.assertEqual(events, [])
        owner.Finish(result)
        self.assertEqual(events, ["closed"])

    def test_custody_blocks_cleanup_but_own_saved_rip_can_finish_it(self):
        events, results = [], []
        blocked = [True]
        class Held(Tag):
            @Rip
            def Clean(target):
                if blocked[0]:
                    raise ValueError("still held")
                results[0].close()
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Action
                def Read(owner, target):
                    try:
                        yield "entered"
                    finally:
                        events.append("closed")
        owner, target = Host(), Host()
        Inventory(owner)
        Held(target)
        owner.Carries(target)
        result = owner.Carries[target].Read()
        results.append(result)
        next(result)
        del owner.Carries[target]
        with self.assertRaises(TagCompositionError):
            del Held[target]
        with self.assertRaises(TagArrestedAccessError):
            result.close()
        self.assertEqual(events, [])
        blocked[0] = False
        del Held[target]
        self.assertEqual(events, ["closed"])

    def test_unstarted_action_and_operation_cleanup_runs_no_body(self):
        events = []
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Action
                def Read(owner, target):
                    events.append("entered")
                    yield 1

                @Operation
                async def Work(link):
                    events.append("entered")
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        result, task = owner.Carries[target].Read(), owner.Carries[target].Work()
        del owner.Carries[target]
        gc.collect()
        result.close()
        task.close()
        self.assertEqual(events, [])

    def test_disposing_continuation_releases_its_old_pair_resource(self):
        class Resource:
            pass
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return Resource()

                @Action
                def Read(owner, target):
                    yield "entered"
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        resource = weakref.ref(owner.Carries[target].slot)
        result = owner.Carries[target].Read()
        next(result)
        del owner.Carries[target]
        gc.collect()
        self.assertIsNotNone(resource())
        result.close()
        gc.collect()
        self.assertIsNone(resource())


    def test_async_cleanup_rechecks_contact_custody_after_each_await(self):
        class Pause:
            def __await__(self):
                yield "paused"
        events = []
        blocked = [True]
        class Held(Tag):
            @Rip
            def Clean(target):
                if blocked[0]:
                    raise ValueError("still held")
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Action
                async def Read(owner, target):
                    try:
                        yield "entered"
                    finally:
                        events.append("begin")
                        await Pause()
                        events.append("continue")
                        await Pause()
                        events.append("closed")
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        Held(target)
        result = owner.Carries[target].Read()
        self.assertEqual(asyncio.run(anext(result)), "entered")
        del owner.Carries[target]
        cleanup = result.aclose()
        self.assertEqual(cleanup.send(None), "paused")
        with self.assertRaises(TagCompositionError):
            del Held[target]
        with self.assertRaises(TagArrestedAccessError):
            cleanup.send(None)
        self.assertEqual(events, ["begin"])
        blocked[0] = False
        del Held[target]
        self.assertEqual(cleanup.send(None), "paused")
        with self.assertRaises(StopIteration):
            cleanup.send(None)
        self.assertEqual(events, ["begin", "continue", "closed"])

    def test_cleanup_cannot_hide_a_contact_arrest_created_by_finally(self):
        class Resource:
            pass
        events = []
        blocked = [True]
        class Held(Tag):
            @Rip
            def Clean(target):
                if blocked[0]:
                    raise ValueError("still held")
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return Resource()

                @Action
                def Read(owner, target):
                    try:
                        yield "entered"
                    finally:
                        try:
                            del Held[target]
                        except TagCompositionError:
                            events.append("arrested")
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        Held(target)
        resource = weakref.ref(owner.Carries[target].slot)
        result = owner.Carries[target].Read()
        next(result)
        del owner.Carries[target]
        with self.assertRaises(TagArrestedAccessError):
            result.close()
        self.assertEqual(events, ["arrested"])
        gc.collect()
        self.assertIsNotNone(resource())
        blocked[0] = False
        del Held[target]
        result.close()
        gc.collect()
        self.assertIsNone(resource())
        result.close()


    def test_natural_completion_releases_pair_while_result_is_retained(self):
        class Resource:
            pass
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return Resource()

                @Action
                def Read(owner, target):
                    yield "entered"
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        resource = weakref.ref(owner.Carries[target].slot)
        result = owner.Carries[target].Read()
        next(result)
        with self.assertRaises(StopIteration):
            next(result)
        del owner.Carries[target]
        gc.collect()
        self.assertIsNone(resource())

    def test_async_close_releases_pair_while_generator_and_awaitable_are_retained(self):
        async def Run():
            class Resource:
                pass
            class Inventory(Tag):
                @Link(agent, contact)
                class Carries(Tag):
                    @Record
                    def slot(owner, target):
                        return Resource()

                    @Action
                    async def Read(owner, target):
                        try:
                            yield "entered"
                        finally:
                            await asyncio.sleep(0)
            owner, target = Host(), Host()
            Inventory(owner)
            owner.Carries(target)
            resource = weakref.ref(owner.Carries[target].slot)
            result = owner.Carries[target].Read()
            await anext(result)
            del owner.Carries[target]
            cleanup = result.aclose()
            await cleanup
            gc.collect()
            self.assertIsNone(resource())
            await result.aclose()
            await result.aclose()
        asyncio.run(Run())


    def test_closing_unfinished_aclose_awaitable_does_not_dispose_parent_resource(self):
        class Resource:
            pass
        class Pause:
            def __await__(self):
                yield "paused"
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return Resource()

                @Action
                async def Read(owner, target):
                    try:
                        yield "entered"
                    finally:
                        await Pause()
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        resource = weakref.ref(owner.Carries[target].slot)
        result = owner.Carries[target].Read()
        step = anext(result)
        with self.assertRaises(StopIteration) as first:
            step.send(None)
        self.assertEqual(first.exception.value, "entered")
        del owner.Carries[target]
        cleanup = result.aclose()
        self.assertEqual(cleanup.send(None), "paused")
        cleanup.close()
        gc.collect()
        self.assertIsNotNone(resource())


    def test_terminal_body_error_releases_pair_without_an_extra_close(self):
        class Resource:
            pass
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return Resource()

                @Action
                def Read(owner, target):
                    yield "entered"
                    raise ValueError("body failed")
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        resource = weakref.ref(owner.Carries[target].slot)
        result = owner.Carries[target].Read()
        next(result)
        with self.assertRaisesRegex(ValueError, "body failed"):
            next(result)
        del owner.Carries[target]
        gc.collect()
        self.assertIsNone(resource())
        result.close()

    def test_terminal_finally_error_releases_pair_without_an_extra_close(self):
        class Resource:
            pass
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return Resource()

                @Action
                def Read(owner, target):
                    try:
                        yield "entered"
                    finally:
                        raise ValueError("finally failed")
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        resource = weakref.ref(owner.Carries[target].slot)
        result = owner.Carries[target].Read()
        next(result)
        del owner.Carries[target]
        with self.assertRaisesRegex(ValueError, "finally failed"):
            result.close()
        gc.collect()
        self.assertIsNone(resource())
        result.close()

    def test_invalid_send_keeps_suspended_pair_available_for_cleanup(self):
        class Resource:
            pass
        events = []
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return Resource()

                @Action
                def Read(owner, target):
                    try:
                        yield "entered"
                    finally:
                        events.append(owner.Carries[target].slot)
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        resource = weakref.ref(owner.Carries[target].slot)
        result = owner.Carries[target].Read()
        with self.assertRaises(TypeError):
            result.send("cannot send before starting")
        gc.collect()
        self.assertIsNotNone(resource())
        next(result)
        del owner.Carries[target]
        result.close()
        self.assertEqual(len(events), 1)
        self.assertIs(events[0], resource())


    def test_terminal_coroutine_error_releases_pair_and_remains_disposable(self):
        class Resource:
            pass
        class Pause:
            def __await__(self):
                yield "paused"
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return Resource()

                @Action
                async def Read(owner, target):
                    await Pause()
                    raise ValueError("body failed")
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        resource = weakref.ref(owner.Carries[target].slot)
        result = owner.Carries[target].Read()
        self.assertEqual(result.send(None), "paused")
        with self.assertRaisesRegex(ValueError, "body failed"):
            result.send(None)
        del owner.Carries[target]
        gc.collect()
        self.assertIsNone(resource())
        result.close()

    def test_async_generator_body_error_releases_pair_and_remains_disposable(self):
        async def Run():
            class Resource:
                pass
            class Inventory(Tag):
                @Link(agent, contact)
                class Carries(Tag):
                    @Record
                    def slot(owner, target):
                        return Resource()

                    @Action
                    async def Read(owner, target):
                        yield "entered"
                        raise ValueError("body failed")
            owner, target = Host(), Host()
            Inventory(owner)
            owner.Carries(target)
            resource = weakref.ref(owner.Carries[target].slot)
            result = owner.Carries[target].Read()
            await anext(result)
            with self.assertRaisesRegex(ValueError, "body failed"):
                await anext(result)
            del owner.Carries[target]
            gc.collect()
            self.assertIsNone(resource())
            await result.aclose()
        asyncio.run(Run())

    def test_async_generator_finally_error_releases_pair_and_remains_disposable(self):
        async def Run():
            class Resource:
                pass
            class Inventory(Tag):
                @Link(agent, contact)
                class Carries(Tag):
                    @Record
                    def slot(owner, target):
                        return Resource()

                    @Action
                    async def Read(owner, target):
                        try:
                            yield "entered"
                        finally:
                            await asyncio.sleep(0)
                            raise ValueError("finally failed")
            owner, target = Host(), Host()
            Inventory(owner)
            owner.Carries(target)
            resource = weakref.ref(owner.Carries[target].slot)
            result = owner.Carries[target].Read()
            await anext(result)
            del owner.Carries[target]
            with self.assertRaisesRegex(ValueError, "finally failed"):
                await result.aclose()
            gc.collect()
            self.assertIsNone(resource())
            await result.aclose()
        asyncio.run(Run())


    def test_foreign_arrest_error_does_not_retain_a_completed_free_pair(self):
        class Resource:
            pass
        blocked = [True]
        class Foreign(Tag):
            @Action
            def Touch(target):
                pass
            @Rip
            def Clean(target):
                if blocked[0]:
                    raise ValueError("foreign cleanup blocked")
        foreign = Host()
        Foreign(foreign)
        with self.assertRaises(TagCompositionError):
            del Foreign[foreign]
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return Resource()
                @Action
                def Read(owner, target):
                    yield "entered"
                    foreign.Touch()
        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        resource = weakref.ref(owner.Carries[target].slot)
        result = owner.Carries[target].Read()
        next(result)
        with self.assertRaises(TagArrestedAccessError):
            next(result)
        del owner.Carries[target]
        gc.collect()
        self.assertIsNone(resource())
        result.close()
        blocked[0] = False
        del Foreign[foreign]

    def test_async_foreign_arrest_error_releases_completed_pair_and_parent(self):
        async def Run():
            class Resource:
                pass
            class Inventory(Tag):
                @Link(agent, contact)
                class Carries(Tag):
                    @Record
                    def slot(owner, target):
                        return Resource()
                    @Action
                    async def Read(owner, target):
                        yield "entered"
                        raise TagArrestedAccessError("foreign protocol denied")
            owner, target = Host(), Host()
            Inventory(owner)
            owner.Carries(target)
            resource = weakref.ref(owner.Carries[target].slot)
            result = owner.Carries[target].Read()
            await anext(result)
            step = anext(result)
            with self.assertRaises(TagArrestedAccessError):
                await step
            del owner.Carries[target]
            gc.collect()
            self.assertIsNone(resource())
            await result.aclose()
        asyncio.run(Run())


if __name__ == '__main__':
    unittest.main()
