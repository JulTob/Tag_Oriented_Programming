"""Published Link continuations retain the calling Contact's custody guard."""

import asyncio
import inspect
import unittest

from TopKit import (Action, Link, Operation, Public, Rip, Tag,
                    TagArrestedAccessError, TagCompositionError, agent, contact)


class Host:
    pass


class LinkLazyPublicationTests(unittest.TestCase):
    def Arrange(self):
        events = []
        release = [False]

        class Held(Tag):
            @Rip
            def Clean(target):
                if not release[0]:
                    raise ValueError("cleanup still required")

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Public
                @Operation
                def Steps(link, caller):
                    yield "start"
                    events.append(caller)
                    yield "continued"

                @Public
                @Operation
                async def Task(link, caller):
                    await asyncio.sleep(0)
                    events.append(caller)
                    return "continued"

                @Public
                @Operation
                async def Values(link, caller):
                    yield "start"
                    events.append(caller)
                    yield "continued"

        class Inspected(Tag):
            pass

        owner, item = Host(), Host()
        Inventory(owner)
        owner.Carries(item)
        Held(item)
        Inspected(item)
        return owner, item, Held, Inspected, release, events

    def Arrest(self, held, item):
        with self.assertRaises(TagCompositionError):
            del held[item]

    def Release(self, held, item, release):
        release[0] = True
        del held[item]

    def test_generator_direct_and_later_tag_views_check_contact_custody(self):
        owner, item, held, inspected, release, events = self.Arrange()
        results = (item.Steps(), inspected[item].Steps())
        self.assertEqual([next(result) for result in results], ["start", "start"])
        self.assertTrue(all(result.__name__ == "Steps" for result in results))
        self.assertFalse(inspect.isgenerator(results[0]))
        self.Arrest(held, item)
        for result in results:
            with self.assertRaises(TagArrestedAccessError):
                next(result)
        self.assertEqual(events, [])
        self.Release(held, item, release)
        self.assertEqual([next(result) for result in results], ["continued", "continued"])
        self.assertEqual(events, [item, item])
        for result in results:
            result.close()

    def test_coroutine_direct_and_later_tag_views_check_contact_custody(self):
        owner, item, held, inspected, release, events = self.Arrange()
        results = (item.Task(), inspected[item].Task())
        for result in results:
            self.assertIsNone(result.send(None))
        self.Arrest(held, item)
        for result in results:
            with self.assertRaises(TagArrestedAccessError):
                result.send(None)
        self.assertEqual(events, [])
        self.Release(held, item, release)
        for result in results:
            with self.assertRaises(StopIteration) as stopped:
                result.send(None)
            self.assertEqual(stopped.exception.value, "continued")
        self.assertEqual(events, [item, item])

    def test_async_generator_direct_and_later_tag_views_check_contact_custody(self):
        async def Run():
            owner, item, held, inspected, release, events = self.Arrange()
            results = (item.Values(), inspected[item].Values())
            self.assertEqual([await anext(result) for result in results], ["start", "start"])
            self.Arrest(held, item)
            for result in results:
                with self.assertRaises(TagArrestedAccessError):
                    await anext(result)
            self.assertEqual(events, [])
            self.Release(held, item, release)
            self.assertEqual([await anext(result) for result in results], ["continued", "continued"])
            self.assertEqual(events, [item, item])
            for result in results:
                await result.aclose()
        asyncio.run(Run())

    def test_public_coroutine_remains_accepted_by_create_task(self):
        async def Run():
            owner, item, held, inspected, release, events = self.Arrange()
            self.assertEqual(await asyncio.create_task(item.Task()), "continued")
            self.assertEqual(await asyncio.create_task(inspected[item].Task()), "continued")
            self.assertEqual(events, [item, item])
        asyncio.run(Run())

    def test_public_contact_guard_preserves_the_links_owner_guard(self):
        owner, item, held, inspected, release, events = self.Arrange()
        held(owner)
        result = item.Steps()
        self.assertEqual(next(result), "start")
        self.Arrest(held, owner)
        with self.assertRaises(TagArrestedAccessError):
            next(result)
        self.assertEqual(events, [])
        self.Release(held, owner, release)
        self.assertEqual(next(result), "continued")
        self.assertEqual(events, [item])
        result.close()

    def test_cancelled_pair_action_keeps_native_body_parked_in_custody(self):
        async def Run():
            started, waiting = asyncio.Event(), asyncio.Event()
            finalized = []
            release = [False]

            class Held(Tag):
                @Rip
                def Clean(target):
                    if not release[0]:
                        raise ValueError("cleanup still required")

            class Inventory(Tag):
                @Link(agent, contact)
                class Carries(Tag):
                    @Action
                    async def Wait(owner, target):
                        try:
                            started.set()
                            await waiting.wait()
                        finally:
                            finalized.append("finished")

            owner, item = Host(), Host()
            Inventory(owner)
            owner.Carries(item)
            Held(item)
            result = owner.Carries[item].Wait()
            task = asyncio.create_task(result)
            await started.wait()
            self.Arrest(Held, item)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
            self.assertTrue(task.cancelled())
            self.assertEqual(finalized, [])
            self.Release(Held, item, release)
            result.close()
            self.assertEqual(finalized, ["finished"])

        asyncio.run(Run())


if __name__ == "__main__":
    unittest.main()
