"""Ending membership closes view access, while entered cleanup may finish."""

import asyncio
import gc
import weakref
import gc
import unittest
import weakref

from TopKit import Action, Operation, Pin, Public, Rip, Secret, Tag
from TopKit import TagArrestedAccessError, TagCompositionError, TagResolutionError
from TopKit.arrest import _rip_door


class Host:
    pass


class Pause:
    def __await__(self):
        yield "paused"


class EnteredLazyCleanupTests(unittest.TestCase):
    def test_view_generator_cleanup_survives_rip_without_reopening_calls(self):
        events = []

        class Role(Tag):
            @Action
            def Work(agent):
                try:
                    yield "working"
                    events.append("ordinary work")
                finally:
                    events.append("closed")

        agent = Host()
        Role(agent)
        view = Role[agent]
        saved = view.Work
        result = saved()
        self.assertEqual(next(result), "working")
        del Role[agent]
        for resume in (lambda: next(result), lambda: result.send(None),
                       lambda: result.throw(GeneratorExit)):
            with self.assertRaises(TagResolutionError):
                resume()
        with self.assertRaises(TagResolutionError):
            saved()
        with self.assertRaises(TagResolutionError):
            view.Work
        result.close()
        result.close()
        self.assertEqual(events, ["closed"])

    def test_view_coroutine_cleanup_survives_rip(self):
        events = []

        class Role(Tag):
            @Action
            async def Work(agent):
                try:
                    await Pause()
                    events.append("ordinary work")
                finally:
                    events.append("closed")

        agent = Host()
        Role(agent)
        result = Role[agent].Work()
        self.assertEqual(result.send(None), "paused")
        del Role[agent]
        with self.assertRaises(TagResolutionError):
            result.send(None)
        result.close()
        self.assertEqual(events, ["closed"])

    def test_async_generator_cleanup_checks_each_await_step(self):
        events = []
        blocked = [True]

        class Arrester(Tag):
            @Rip
            def Release(agent):
                if blocked[0]:
                    raise ValueError("still held")

        class Role(Tag):
            @Action
            async def Work(agent):
                try:
                    yield "working"
                finally:
                    events.append("cleanup begins")
                    await Pause()
                    events.append("cleanup continues")
                    await Pause()
                    events.append("closed")

        agent = Host()
        Role(agent)
        Arrester(agent)
        result = Role[agent].Work()
        self.assertEqual(asyncio.run(anext(result)), "working")
        del Role[agent]
        cleanup = result.aclose()
        self.assertEqual(cleanup.send(None), "paused")
        with self.assertRaises(TagCompositionError):
            del Arrester[agent]
        with self.assertRaises(TagArrestedAccessError):
            cleanup.send(None)
        self.assertEqual(events, ["cleanup begins"])
        with _rip_door(agent):
            self.assertEqual(cleanup.send(None), "paused")
            with self.assertRaises(StopIteration):
                cleanup.send(None)
        self.assertEqual(events, ["cleanup begins", "cleanup continues", "closed"])
        blocked[0] = False
        del Arrester[agent]

    def test_cleanup_does_not_authorize_an_unrelated_continuation(self):
        events = []
        other = []

        class Role(Tag):
            @Action
            def Work(agent):
                try:
                    yield "working"
                finally:
                    try:
                        next(other[0])
                    except TagResolutionError:
                        events.append("other refused")

        agent = Host()
        Role(agent)
        first = Role[agent].Work()
        second = Role[agent].Work()
        next(first)
        next(second)
        other.append(second)
        del Role[agent]
        first.close()
        self.assertEqual(events, ["other refused"])
        second.close()
        self.assertEqual(events, ["other refused", "other refused"])

    def test_asyncio_task_can_finish_async_cleanup_after_rip(self):
        events = []

        class Role(Tag):
            @Action
            async def Work(agent):
                try:
                    yield "working"
                finally:
                    await asyncio.sleep(0)
                    events.append("closed")

        async def Run():
            agent = Host()
            Role(agent)
            result = Role[agent].Work()
            self.assertEqual(await anext(result), "working")
            del Role[agent]
            await asyncio.create_task(result.aclose())

        asyncio.run(Run())
        self.assertEqual(events, ["closed"])

    def test_secret_cleanup_keeps_its_captured_door(self):
        events = []

        class Role(Tag):
            @Secret
            @Action
            def Work(agent):
                try:
                    yield "working"
                finally:
                    events.append("closed")

            @Action
            def Capture(agent):
                return Role[agent].Work()

            @Action
            def Start(agent, result):
                return next(result)

            @Action
            def Close(agent, result):
                result.close()

        agent = Host()
        Role(agent)
        result = agent.Capture()
        self.assertEqual(agent.Start(result), "working")
        del Role[agent]
        with self.assertRaises(AttributeError):
            result.close()
        self.assertEqual(events, [])
        agent.Close(result)
        self.assertEqual(events, ["closed"])

    def test_arrested_cleanup_runs_from_its_saved_rip(self):
        events = []
        blocked = [True]
        result = None

        class Role(Tag):
            @Action
            def Work(agent):
                try:
                    yield "working"
                finally:
                    events.append("closed")

            @Rip
            def Release(agent):
                if blocked[0]:
                    raise ValueError("still held")
                result.close()

        agent = Host()
        Role(agent)
        result = Role[agent].Work()
        next(result)
        with self.assertRaises(TagCompositionError):
            del Role[agent]
        with self.assertRaises(TagArrestedAccessError):
            result.close()
        self.assertEqual(events, [])
        blocked[0] = False
        del Role[agent]
        self.assertEqual(events, ["closed"])

    def test_cleanup_rechecks_an_arrest_created_by_its_finally(self):
        events = []
        blocked = [True]

        class Arrester(Tag):
            @Rip
            def Release(agent):
                if blocked[0]:
                    raise ValueError("still held")

        class Role(Tag):
            @Action
            def Work(agent):
                try:
                    yield "working"
                finally:
                    try:
                        del Arrester[agent]
                    except TagCompositionError:
                        events.append("cleanup caused arrest")

        agent = Host()
        Role(agent)
        Arrester(agent)
        result = Role[agent].Work()
        next(result)
        del Role[agent]
        with self.assertRaises(TagArrestedAccessError):
            result.close()
        self.assertEqual(events, ["cleanup caused arrest"])
        blocked[0] = False
        del Arrester[agent]

    def test_public_operation_view_cleanup_survives_rip(self):
        events = []

        class Role(Tag):
            @Public
            @Operation
            def Work(tag, caller):
                try:
                    yield caller
                finally:
                    events.append("closed")

        agent = Host()
        Role(agent)
        result = Role[agent].Work()
        self.assertIs(next(result), agent)
        del Role[agent]
        with self.assertRaises(TagResolutionError):
            next(result)
        result.close()
        self.assertEqual(events, ["closed"])

    def test_pin_view_cleanup_survives_rip(self):
        events = []

        class Protocol(Pin):
            @Action
            def Work(tag):
                try:
                    yield "working"
                finally:
                    events.append("closed")

        class Target(Tag):
            pass

        Protocol(Target)
        result = Protocol[Target].Work()
        next(result)
        del Protocol[Target]
        result.close()
        self.assertEqual(events, ["closed"])

    def test_disposing_unstarted_results_never_enters_the_body(self):
        events = []

        class Role(Tag):
            @Action
            def Generate(agent):
                events.append("generator started")
                yield 1

            @Action
            async def Await(agent):
                events.append("coroutine started")

            @Action
            async def Stream(agent):
                events.append("async generator started")
                yield 1

        agent = Host()
        Role(agent)
        generator = Role[agent].Generate()
        coroutine = Role[agent].Await()
        stream = Role[agent].Stream()
        del Role[agent]
        generator.close()
        coroutine.close()
        asyncio.run(stream.aclose())
        self.assertEqual(events, [])

    def test_unstarted_nested_coroutine_closes_without_entering_either_view(self):
        events = []

        class Inner(Tag):
            @Action
            async def Work(agent):
                events.append("started")

        class Outer(Tag):
            @Action
            def Make(agent):
                return Inner[agent].Work()

        agent = Host()
        Inner(agent)
        Outer(agent)
        result = Outer[agent].Make()
        del Outer[agent]
        del Inner[agent]
        result.close()
        self.assertEqual(events, [])

    def test_cleanup_keeps_receiver_alive_through_its_postcheck_then_releases_it(self):
        holder = [Host()]
        events = []

        class Role(Tag):
            @Operation
            def Work(tag):
                try:
                    yield "working"
                finally:
                    holder.clear()
                    gc.collect()
                    events.append("closed")

        reference = weakref.ref(holder[0])
        Role(holder[0])
        result = Role[holder[0]].Work()
        next(result)
        del Role[holder[0]]
        result.close()
        gc.collect()
        self.assertIsNone(reference())
        result.close()   # completed disposal is still safe after receiver collection
        self.assertEqual(events, ["closed"])

    def test_closed_async_result_can_be_disposed_again_after_receiver_collection(self):
        events = []

        class Role(Tag):
            @Action
            async def Work(agent):
                try:
                    yield "working"
                finally:
                    events.append("closed")

        agent = Host()
        reference = weakref.ref(agent)
        Role(agent)
        result = Role[agent].Work()
        self.assertEqual(asyncio.run(anext(result)), "working")
        del Role[agent]
        cleanup = result.aclose()
        asyncio.run(cleanup)
        del agent
        gc.collect()
        self.assertIsNone(reference())
        cleanup.close()
        asyncio.run(result.aclose())
        self.assertEqual(events, ["closed"])


    def test_terminal_generator_error_is_disposable_after_receiver_collection(self):
        class Role(Tag):
            @Action
            def Work(agent):
                yield "working"
                raise ValueError("body failed")
        agent = Host()
        Role(agent)
        reference = weakref.ref(agent)
        result = Role[agent].Work()
        next(result)
        with self.assertRaisesRegex(ValueError, "body failed"):
            next(result)
        del agent
        gc.collect()
        self.assertIsNone(reference())
        result.close()
        result.close()

    def test_terminal_coroutine_error_is_disposable_after_receiver_collection(self):
        class Role(Tag):
            @Action
            async def Work(agent):
                await Pause()
                raise ValueError("body failed")
        agent = Host()
        Role(agent)
        reference = weakref.ref(agent)
        result = Role[agent].Work()
        self.assertEqual(result.send(None), "paused")
        with self.assertRaisesRegex(ValueError, "body failed"):
            result.send(None)
        del agent
        gc.collect()
        self.assertIsNone(reference())
        result.close()
        result.close()

    def test_terminal_async_generator_errors_remain_disposable_after_collection(self):
        async def Run(during_close):
            class Role(Tag):
                @Action
                async def Work(agent):
                    try:
                        yield "working"
                        if not during_close:
                            raise ValueError("body failed")
                    finally:
                        if during_close:
                            await asyncio.sleep(0)
                            raise ValueError("finally failed")
            agent = Host()
            Role(agent)
            reference = weakref.ref(agent)
            result = Role[agent].Work()
            await anext(result)
            operation = result.aclose() if during_close else anext(result)
            with self.assertRaises(ValueError):
                await operation
            del agent
            gc.collect()
            self.assertIsNone(reference())
            await result.aclose()
            await result.aclose()
        for during_close in (False, True):
            with self.subTest(during_close=during_close):
                asyncio.run(Run(during_close))

    def test_closed_source_recognition_does_not_probe_opaque_host_hooks(self):
        from TopKit.lazy_guard import _lazy_finished
        class Meta(type):
            def __eq__(kind, other):
                raise AssertionError("host type equality is opaque")
            def __hash__(kind):
                raise AssertionError("host type hashing is opaque")
        class Opaque(metaclass=Meta):
            @property
            def __class__(self):
                raise AssertionError("host attributes are opaque")
            def __getattribute__(self, name):
                raise AssertionError("host attributes are opaque")
        self.assertFalse(_lazy_finished(Opaque()))


    def test_terminal_arrest_error_completes_async_generator_bookkeeping(self):
        async def Run():
            class Role(Tag):
                @Action
                async def Work(agent):
                    yield "working"
                    raise TagArrestedAccessError("foreign protocol denied")
            agent = Host()
            Role(agent)
            reference = weakref.ref(agent)
            result = Role[agent].Work()
            await anext(result)
            step = anext(result)
            with self.assertRaises(TagArrestedAccessError):
                await step
            del agent
            gc.collect()
            self.assertIsNone(reference())
            await result.aclose()
        asyncio.run(Run())


if __name__ == "__main__":
    unittest.main()
