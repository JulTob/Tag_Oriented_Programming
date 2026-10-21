"""A recursive Post reads its own unfinished verdict as neutral True."""

from contextvars import copy_context
import asyncio
import gc
from threading import Thread, get_ident
import unittest
import weakref

from TopKit import Action, Contract, Post, Record, Rip, Secret, Tag, Underlay
from TopKit import TagCompositionError
from TopKit import TagPostconditionError


class Host:
    pass


class PostNeutralCycleTests(unittest.TestCase):
    def test_positive_self_queries_hold_across_truth_membership_status_and_name(self):
        for query in (
                lambda agent, tag: bool(agent),
                lambda agent, tag: Contract.Postconditions(agent),
                lambda agent, tag: Contract.Status(agent)["Ready"],
                lambda agent, tag: agent.Ready,
                lambda agent, tag: agent in tag,
                ):
            with self.subTest(query=query):
                class Reading(Tag):
                    @Post
                    def Ready(agent):
                        return query(agent, Reading)

                agent = Host()
                Reading(agent)
                self.assertIn(agent, Reading[:])
                self.assertIn(agent, Reading)
                self.assertTrue(agent.Ready)
                self.assertTrue(bool(agent))

    def test_negating_own_truth_yields_false_and_keeps_field_admission(self):
        class Reading(Tag):
            @Post
            def Ready(agent):
                return not bool(agent)

        agent = Host()
        with self.assertRaises(TagPostconditionError.Ready):
            Reading(agent)

        self.assertIn(agent, Reading[:])
        self.assertFalse(agent.Ready)
        self.assertFalse(bool(agent))
        self.assertEqual(Contract.Status(agent), {"Ready": False})

    def test_recursion_does_not_hide_an_unrelated_failed_post(self):
        class Reading(Tag):
            @Post
            def Ready(agent):
                return bool(agent)

            @Post
            def Safe(agent):
                return agent.safe

        agent = Host()
        agent.safe = True
        Reading(agent)
        agent.safe = False

        self.assertFalse(agent.Ready)
        self.assertFalse(bool(agent))
        self.assertEqual(Contract.Status(agent), {"Ready": False, "Safe": False})

    def test_named_post_cycles_are_neutral_and_acyclic_reads_still_follow_state(self):
        class Mutual(Tag):
            @Post
            def Ready(agent):
                return agent.Safe

            @Post
            def Safe(agent):
                return agent.Ready

        first = Host()
        Mutual(first)
        self.assertTrue(first.Ready)
        self.assertEqual(Contract.Status(first), {"Ready": True, "Safe": True})

        class Acyclic(Tag):
            @Post
            def Ready(agent):
                return agent.Safe

            @Post
            def Safe(agent):
                return agent.safe

        second = Host()
        second.safe = True
        Acyclic(second)
        self.assertTrue(second.Ready)
        second.safe = False
        self.assertFalse(second.Ready)

    def test_lower_underlay_post_can_read_the_visible_upper_post(self):
        class Base(Tag):
            @Post
            def Ready(agent):
                return agent.Ready

        class Shape(Tag):
            @Underlay
            @Post
            def Ready(agent, lower):
                return lower() and agent.safe

        agent = Host()
        agent.safe = True
        Base(agent)
        Shape(agent)
        self.assertTrue(agent.Ready)
        agent.safe = False
        self.assertFalse(agent.Ready)

    def test_repeated_post_underlay_reads_reuse_its_first_verdict(self):
        armed = [False]
        reads = []

        class Base(Tag):
            @Post
            def Ready(agent):
                if not armed[0]:
                    return True
                reads.append(True)
                return len(reads) % 2 == 1

        class Upper(Tag):
            @Underlay
            @Post
            def Ready(agent, lower):
                return lower() and lower()

        agent = Host()
        Base(agent)
        Upper(agent)
        armed[0] = True
        self.assertTrue(agent.Ready)
        self.assertEqual(reads, [True])
        self.assertFalse(agent.Ready)  # the next independent check reads again
        self.assertEqual(len(reads), 2)

    def test_collective_post_cycle_bounds_eight_member_rechecks(self):
        armed = [False]
        checks = [0]

        class Group(Tag):
            @Post
            def Everyone_Is_Sound(agent):
                if not armed[0]:
                    return True
                checks[0] += 1
                return len(Group) == len(Group[:])

        members = [Host() for _ in range(8)]
        for agent in members:
            Group(agent)

        armed[0] = True
        self.assertEqual(len(Group), len(members))
        self.assertEqual(checks[0], len(members))

        # The memo belongs to one question. New questions see changed facts.
        armed[0] = False
        self.assertEqual(len(Group), len(members))

    def test_one_population_query_reuses_a_shared_post_verdict(self):
        armed = [False]
        reads = []

        class Sensor(Tag):
            @Post
            def Signal(agent):
                if not armed[0]:
                    return True
                reads.append(True)
                return len(reads) % 2 == 1

        subject = Host()
        Sensor(subject)

        class Group(Tag):
            @Post
            def Ready(agent):
                return subject.Signal

        members = [Host(), Host()]
        for member in members:
            Group(member)
        armed[0] = True

        self.assertEqual(len(Group), 2)
        self.assertEqual(len(reads), 1)
        self.assertEqual(len(Group), 0)
        self.assertEqual(len(reads), 2)

    def test_one_combined_membership_query_reuses_its_first_verdict(self):
        armed = [False]
        reads = []

        class First(Tag):
            @Post
            def Ready(agent):
                if not armed[0]:
                    return True
                reads.append(True)
                return len(reads) % 2 == 1

        class Second(Tag):
            pass

        agent = Host()
        First(agent)
        Second(agent)
        armed[0] = True
        self.assertIn(agent, First & Second)
        self.assertEqual(len(reads), 1)
        self.assertNotIn(agent, First & Second)
        self.assertEqual(len(reads), 2)

    def test_bool_query_reuses_first_verdict_in_same_context_without_a_cycle(self):
        armed = [False]
        inside_pair = [False]
        sensor_reads = [0]

        class Sample(Tag):
            @Post
            def Pair(agent):
                if not armed[0]:
                    return True
                inside_pair[0] = True
                try:
                    first = agent.Sensor
                    second = agent.Sensor
                finally:
                    inside_pair[0] = False
                return first and second

            @Post
            def Sensor(agent):
                if not inside_pair[0]:
                    return True
                sensor_reads[0] += 1
                return sensor_reads[0] == 1

        agent = Host()
        Sample(agent)
        armed[0] = True

        self.assertTrue(bool(agent))
        self.assertEqual(sensor_reads[0], 1)
        sensor_reads[0] = 0
        self.assertTrue(bool(agent))
        self.assertEqual(sensor_reads[0], 1)

    def test_detailed_failure_reuses_its_verdict_within_the_same_query(self):
        armed = [False]
        reads = [0]

        class Subject(Tag):
            @Post
            def Ready(agent):
                if not armed[0]:
                    return True
                reads[0] += 1
                return False

        subject = Host()
        Subject(subject)

        class Witness(Tag):
            @Post
            def Checks_Twice(agent):
                if not armed[0]:
                    return True
                for _ in range(2):
                    try:
                        Contract.Postconditions(subject)
                    except TagPostconditionError.Ready:
                        pass
                return True

        witness = Host()
        Witness(witness)
        armed[0] = True

        self.assertTrue(bool(witness))
        self.assertEqual(reads[0], 1)

    def test_bool_query_shares_first_verdict_with_later_sibling_post(self):
        armed = [False]
        reads = [0]

        class Sample(Tag):
            @Post
            def Pair(agent):
                return True if not armed[0] else agent.Sensor

            @Post
            def Sensor(agent):
                if not armed[0]:
                    return True
                reads[0] += 1
                return reads[0] == 1

        agent = Host()
        Sample(agent)
        armed[0] = True

        self.assertTrue(bool(agent))
        self.assertEqual(reads[0], 1)
        self.assertFalse(bool(agent))  # a new query sees the new sensor input

    def test_named_and_status_queries_share_their_first_sibling_verdict(self):
        armed = [False]
        reads = [0]

        class Sample(Tag):
            @Post
            def Pair(agent):
                return True if not armed[0] else agent.Sensor

            @Post
            def Sensor(agent):
                if not armed[0]:
                    return True
                reads[0] += 1
                return reads[0] % 2 == 1

        agent = Host()
        Sample(agent)
        armed[0] = True

        self.assertTrue(Contract.Postconditions(agent))
        self.assertEqual(reads[0], 1)
        self.assertEqual(Contract.Status(agent), {"Pair": False, "Sensor": False})
        self.assertEqual(reads[0], 2)

    def test_first_completed_verdict_is_shared_across_paths_in_one_query(self):
        seen = []

        class Mixed(Tag):
            @Post
            def Observer(agent):
                seen.append(Contract.Status(agent))
                return True

            @Post
            def First(agent):
                return not agent.Second

            @Post
            def Second(agent):
                return agent.First

        agent = Host()
        with self.assertRaises(TagPostconditionError.First):
            Mixed(agent)

        self.assertEqual(seen[-1], {
                "Observer": True,
                "First": False,
                "Second": True,
                })
        self.assertFalse(agent.First)
        self.assertFalse(agent.Second)



    def test_secret_post_verdict_is_not_reused_after_its_door_closes(self):
        armed = [False]

        class Carrier(Tag):
            @Secret
            @Record
            def code(agent):
                return "private"

            @Action
            def Read_Promise(agent, subject):
                return subject.Promise

        carrier = Host()
        Carrier(carrier)

        class Subject(Tag):
            @Post
            def Promise(agent):
                try:
                    return carrier.code == "private"
                except AttributeError:
                    return False

        subject = Host()
        with self.assertRaises(TagPostconditionError.Promise):
            Subject(subject)

        class Witness(Tag):
            @Post
            def Safe(agent):
                if not armed[0]:
                    return True
                self.assertTrue(carrier.Read_Promise(subject))
                _ = agent.Safe   # the same query now has a cycle
                return subject.Promise

        witness = Host()
        Witness(witness)
        armed[0] = True

        self.assertFalse(witness.Safe)

    def test_root_truth_does_not_reuse_secret_verdict_after_door_closes(self):
        armed = [False]

        class Carrier(Tag):
            @Secret
            @Record
            def code(agent):
                return "private"

            @Action
            def Read_Promise(agent, subject):
                return subject.Promise

        carrier = Host()
        Carrier(carrier)

        class Subject(Tag):
            @Post
            def Promise(agent):
                try:
                    return carrier.code == "private"
                except AttributeError:
                    return False

        subject = Host()
        with self.assertRaises(TagPostconditionError.Promise):
            Subject(subject)

        class Witness(Tag):
            @Post
            def First(agent):
                if not armed[0]:
                    return True
                return carrier.Read_Promise(subject)

            @Post
            def Second(agent):
                return True if not armed[0] else subject.Promise

        witness = Host()
        Witness(witness)
        armed[0] = True
        self.assertFalse(bool(witness))

    def test_secret_probe_in_a_copied_context_taints_the_parent_query(self):
        armed = [False]
        reads = [0]

        class Carrier(Tag):
            @Secret
            @Record
            def code(agent):
                return "private"

        carrier = Host()
        Carrier(carrier)

        class Subject(Tag):
            @Post
            def Promise(agent):
                if not armed[0]:
                    return True
                reads[0] += 1
                return reads[0] == 1

        subject = Host()
        Subject(subject)

        class Witness(Tag):
            @Post
            def Safe(agent):
                if not armed[0]:
                    return True
                try:
                    copy_context().run(lambda: carrier.code)
                except AttributeError:
                    pass
                return subject.Promise and subject.Promise

        witness = Host()
        Witness(witness)
        armed[0] = True

        self.assertFalse(bool(witness))
        self.assertEqual(reads[0], 2)

    def test_copied_context_on_another_thread_does_not_reuse_parent_verdict(self):
        armed = [False]
        reads = [0]

        class Subject(Tag):
            @Post
            def Promise(agent):
                if not armed[0]:
                    return True
                reads[0] += 1
                return reads[0] == 1

        subject = Host()
        Subject(subject)

        class Witness(Tag):
            @Post
            def Safe(agent):
                if not armed[0]:
                    return True
                self.assertTrue(subject.Promise)
                result = []
                context = copy_context()
                worker = Thread(target=lambda: result.append(
                        context.run(lambda: subject.Promise),
                        ))
                worker.start()
                worker.join()
                return result == [False]

        witness = Host()
        Witness(witness)
        armed[0] = True

        self.assertTrue(bool(witness))
        self.assertEqual(reads[0], 2)

    def test_copied_thread_does_not_inherit_parent_active_post_as_neutral(self):
        armed = [False]
        main_thread = get_ident()
        reads = []

        class Subject(Tag):
            @Post
            def Ready(agent):
                if not armed[0]:
                    return True
                reads.append(get_ident())
                if get_ident() != main_thread:
                    return False
                result = []
                context = copy_context()
                worker = Thread(target=lambda: result.append(
                        context.run(lambda: agent.Ready),
                        ))
                worker.start()
                worker.join()
                return result == [False]

        subject = Host()
        Subject(subject)
        armed[0] = True

        self.assertTrue(bool(subject))
        self.assertEqual(len(reads), 2)

    def test_copied_thread_secret_probe_taints_parent_verdict_session(self):
        armed = [False]
        reads = [0]

        class Carrier(Tag):
            @Secret
            @Record
            def code(agent):
                return "private"

        carrier = Host()
        Carrier(carrier)

        class Subject(Tag):
            @Post
            def Promise(agent):
                if not armed[0]:
                    return True
                reads[0] += 1
                return reads[0] == 1

        subject = Host()
        Subject(subject)

        class Witness(Tag):
            @Post
            def Safe(agent):
                if not armed[0]:
                    return True
                self.assertTrue(subject.Promise)

                def Probe_Secret():
                    try:
                        carrier.code
                    except AttributeError:
                        pass

                context = copy_context()
                worker = Thread(target=lambda: context.run(Probe_Secret))
                worker.start()
                worker.join()
                return not subject.Promise

        witness = Host()
        Witness(witness)
        armed[0] = True

        self.assertTrue(bool(witness))
        self.assertEqual(reads[0], 2)

    def test_copied_thread_may_start_its_own_multi_post_truth_query(self):
        class Subject(Tag):
            @Post
            def First(agent):
                return True

            @Post
            def Second(agent):
                return True

        subject = Host()
        Subject(subject)

        class Witness(Tag):
            @Post
            def Safe(agent):
                answers = []
                context = copy_context()
                worker = Thread(target=lambda: answers.append(
                        context.run(lambda: bool(subject)),
                        ))
                worker.start()
                worker.join()
                return answers == [True]

        witness = Host()
        Witness(witness)
        self.assertTrue(bool(witness))

    def test_a_caught_top_change_cannot_be_cached_as_a_passing_post(self):
        seen = []
        calls = [0]

        class Checked(Tag):
            @Post
            def Observer(agent):
                seen.append((bool(agent), bool(agent)))
                return True

            @Post
            def Guard(agent):
                calls[0] += 1
                try:
                    del Checked[agent]
                except TagCompositionError:
                    pass
                return True

        with self.assertRaises(TagPostconditionError) as caught:
            Checked(Host())
        self.assertEqual(caught.exception.failed_posts, ("Observer", "Guard"))

        self.assertEqual(seen, [(False, False)])
        self.assertEqual(calls[0], 1)

    def test_failed_detailed_post_does_not_keep_an_agent_alive(self):
        class Checked(Tag):
            @Post
            def Ready(agent):
                _ = len(Checked)   # open a nested Post query session
                return False

        def Fail_Once():
            agent = Host()
            reference = weakref.ref(agent)
            with self.assertRaises(TagPostconditionError.Ready):
                Checked(agent)
            return reference

        self.assertIsNone(Fail_Once()())

    def test_a_copied_context_is_fresh_after_an_interrupted_query(self):
        contexts = []
        interrupt = [False]
        reads = []

        class Checked(Tag):
            @Post
            def Ready(agent):
                reads.append(True)
                contexts.append(copy_context())
                if interrupt[0]:
                    raise KeyboardInterrupt()
                return True

        agent = Host()
        Checked(agent)
        interrupt[0] = True
        with self.assertRaises(KeyboardInterrupt):
            bool(agent)
        interrupt[0] = False
        before = len(reads)
        self.assertTrue(contexts[-1].run(lambda: agent.Ready))
        self.assertEqual(len(reads), before + 1)

    def test_eager_child_task_does_not_share_a_parent_running_edge(self):
        armed = [False]
        caller = [None]
        reads = []

        class Checked(Tag):
            @Post
            def Ready(agent):
                if not armed[0]:
                    return True
                task = asyncio.current_task()
                reads.append(task)
                if task is not caller[0]:
                    return False

                async def Child():
                    return agent.Ready

                child = asyncio.create_task(Child())
                self.assertTrue(child.done())
                return child.result() is False

        agent = Host()
        Checked(agent)

        async def Run():
            loop = asyncio.get_running_loop()
            factory = loop.get_task_factory()
            loop.set_task_factory(asyncio.eager_task_factory)
            try:
                caller[0] = asyncio.current_task()
                armed[0] = True
                self.assertTrue(bool(agent))
            finally:
                loop.set_task_factory(factory)

        asyncio.run(Run())
        self.assertEqual(len(reads), 2)
        self.assertIsNot(reads[0], reads[1])

    def test_saved_query_context_does_not_retain_an_async_task(self):
        contexts = []

        class Checked(Tag):
            @Post
            def Ready(agent):
                contexts.append(copy_context())
                return True

        async def Run():
            agent = Host()
            Checked(agent)
            return weakref.ref(asyncio.current_task()), weakref.ref(agent)

        task, agent = asyncio.run(Run())
        gc.collect()
        self.assertIsNone(task())
        self.assertIsNone(agent())
        self.assertTrue(contexts)

    def test_a_post_cannot_return_a_pre_arrest_verdict_after_concurrent_rip(self):
        from TopKit.arrest import _safehouse
        self.addCleanup(_safehouse.clear)
        armed = [False]

        class Checked(Tag):
            @Post
            def Ready(agent):
                if not armed[0]:
                    return True

                def Remove():
                    try:
                        del Leaving[agent]
                    except TagCompositionError:
                        pass

                worker = Thread(target=Remove)
                worker.start()
                worker.join()
                return True

        class Leaving(Tag):
            @Rip
            def Close(agent):
                raise ValueError("not ready")

        agent = Host()
        Checked(agent)
        Leaving(agent)
        armed[0] = True
        with self.assertRaises(TagPostconditionError.Ready):
            Contract.Postconditions(agent)
        self.assertFalse(bool(agent))

    def test_a_captured_rip_permission_cannot_reuse_a_verdict_after_exit(self):
        from TopKit.arrest import _arrest_of, _rip_door, _safehouse
        self.addCleanup(_safehouse.clear)
        subject = Host()
        armed = [False]

        class Checked(Tag):
            @Post
            def Ready(agent):
                return True

        class Leaving(Tag):
            @Rip
            def Close(agent):
                raise ValueError("not ready")

        Checked(subject)
        Leaving(subject)
        with self.assertRaises(TagCompositionError):
            del Leaving[subject]
        self.assertIsNotNone(_arrest_of(subject))

        class Witness(Tag):
            @Post
            def Safe(agent):
                if not armed[0]:
                    return True
                with _rip_door(subject):
                    self.assertTrue(Contract.Postconditions(subject))
                    context = copy_context()
                try:
                    context.run(lambda: Contract.Postconditions(subject))
                except TagPostconditionError.Ready:
                    return True
                return False

        witness = Host()
        Witness(witness)
        armed[0] = True
        self.assertTrue(bool(witness))



if __name__ == "__main__":
    unittest.main()
