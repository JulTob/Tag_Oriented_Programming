"""A recursive Post reads its own unfinished verdict as neutral True."""

from contextvars import copy_context
from threading import Thread
import unittest
import weakref

from TopKit import Action, Contract, Post, Pre, Record, Secret, Tag, Underlay
from TopKit import TagCompositionError
from TopKit import TagPostconditionError
from TopKit import TagPreconditionError


class Host:
    pass


class PostNeutralCycleTests(unittest.TestCase):
    def test_positive_self_queries_hold_across_truth_membership_status_and_name(self):
        for query in (
                lambda agent, tag: bool(agent),
                lambda agent, tag: Contract.Postconditions(agent),
                lambda agent, tag: Contract.Conditions(agent),
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
        self.assertLessEqual(checks[0], 2048)

        # The memo belongs to one question. New questions see changed facts.
        armed[0] = False
        self.assertEqual(len(Group), len(members))

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

    def test_pre_checks_do_not_reuse_post_verdicts_from_a_different_flow(self):
        armed = [False]

        class Mixed(Tag):
            @Pre
            def Gate(agent):
                return True if not armed[0] else not agent.Promise

            @Post
            def Promise(agent):
                try:
                    return Contract.Preconditions(agent)
                except TagPreconditionError.Gate:
                    return False

            @Post
            def Witness(agent):
                if not armed[0]:
                    return True
                try:
                    Contract.Preconditions(agent)
                except TagPreconditionError.Gate:
                    pass
                _ = agent.Witness
                return agent.Promise

        agent = Host()
        Mixed(agent)
        armed[0] = True

        self.assertFalse(agent.Witness)
        self.assertFalse(agent.Promise)
        self.assertFalse(Contract.Status(agent)["Gate"])

    def test_entering_a_pre_discards_earlier_post_verdicts(self):
        armed = [False]
        reads = [0]

        class Subject(Tag):
            @Pre
            def Gate(agent):
                return True

            @Post
            def Promise(agent):
                reads[0] += 1
                return True

        subject = Host()
        Subject(subject)
        reads[0] = 0

        class Witness(Tag):
            @Post
            def Safe(agent):
                if not armed[0]:
                    return True
                _ = agent.Safe   # enable this query's cycle memo
                self.assertTrue(subject.Promise)
                self.assertTrue(Contract.Preconditions(subject))
                self.assertTrue(subject.Promise)
                return True

        witness = Host()
        Witness(witness)
        armed[0] = True
        self.assertTrue(witness.Safe)
        self.assertEqual(reads[0], 2)

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

        with self.assertRaises(TagPostconditionError.Observer):
            Checked(Host())

        self.assertEqual(seen, [(False, False)])
        self.assertEqual(calls[0], 2)

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

    def test_failed_post_diagnostic_keeps_a_hostile_name_inside_observation(self):
        class Mutated(Tag):
            pass

        other = Host()

        class Name(str):
            armed = False
            calls = 0

            def __repr__(self):
                if type(self).armed:
                    type(self).calls += 1
                    if type(self).calls >= 2:
                        try:
                            Mutated(other)
                        except TagCompositionError:
                            pass
                return str.__repr__(self)

        name = Name("Ready")
        Broken = type(
                "Broken", (Tag,), {name: Post(lambda agent: False)},
                )
        Name.armed = True

        with self.assertRaises(TagPostconditionError.Ready):
            Broken(Host())

        self.assertGreaterEqual(Name.calls, 2)
        self.assertNotIn(other, Mutated[:])


if __name__ == "__main__":
    unittest.main()
