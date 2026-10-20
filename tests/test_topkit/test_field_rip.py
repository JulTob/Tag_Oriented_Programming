"""The whole-Field Rip success path and its current failure boundary."""

from __future__ import annotations

import gc
import unittest

from TopKit import Pin
from TopKit import Post
from TopKit import Record
from TopKit import Report
from TopKit import Rip
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit.tags import MetaTag

from ._fixtures import Agent


class FieldRipTests(unittest.TestCase):
    def test_accepted_dict_subclass_cannot_run_during_revocation(self) -> None:
        seen = []
        armed = False

        class NoisyDict(dict):
            def get(self, key, default=None):
                if armed:
                    seen.append(len(Squad[:]))

                return super().get(key, default)

        class Host:
            def __init__(self):
                self.__dict__ = NoisyDict()

        class Squad(Tag):
            pass

        members = [Host(), Host()]

        for member in members:
            Squad(member)

        armed = True

        try:
            del Squad[:]
        finally:
            armed = False

        self.assertEqual(seen, [])
        self.assertEqual(list(Squad[:]), [])

    def test_accepted_host_dict_property_cannot_run_during_revocation(self) -> None:
        seen = []
        armed = False

        class BaseHost:
            pass

        class Host(BaseHost):
            @property
            def __dict__(self):
                if armed:
                    seen.append(len(Squad[:]))

                    if len(seen) == 1:
                        Squad(members[0])

                return BaseHost.__dict__["__dict__"].__get__(self)

        class Squad(Tag):
            pass

        members = [Host(), Host()]

        for member in members:
            Squad(member)

        armed = True

        try:
            del Squad[:]
        finally:
            armed = False

        self.assertEqual(seen, [])
        self.assertEqual(list(Squad[:]), [])

    def test_metaclass_equality_and_hash_do_not_run_during_revocation(self) -> None:
        seen = []
        armed = False

        class NoisyMeta(MetaTag):
            def __eq__(cls, other):
                if armed:
                    seen.append(("equal", len(Target[:])))

                return cls is other

            def __hash__(cls):
                if armed:
                    seen.append(("hash", len(Target[:])))

                return type.__hash__(cls)

        class Other(Tag, metaclass=NoisyMeta):
            pass

        class Target(Tag, metaclass=NoisyMeta):
            pass

        members = [Agent(), Agent()]

        for member in members:
            Other(member)
            Target(member)

        armed = True

        try:
            del Target[:]
        finally:
            armed = False

        self.assertEqual(seen, [])
        self.assertEqual(list(Target[:]), [])
        self.assertEqual(list(Other[:]), members)

    def test_all_members_leave_before_teardowns_including_defective(self) -> None:
        seen = []

        class Squad(Tag):
            @Post
            def Ready(agent):
                return agent.ready

            @Rip
            def Stand_Down(agent):
                seen.append((
                        agent.label,
                        tuple(member in Squad for member in members),
                        tuple(Squad[:]),
                        ))

        members = [Agent(), Agent(), Agent()]

        for label, member in zip(("first", "second", "third"), members):
            member.label = label
            Squad(member)

        members[1].ready = False
        self.assertEqual(list(~Squad), [members[1]])

        del Squad[:]

        self.assertCountEqual(
                seen,
                [(label, (False, False, False), ())
                 for label in ("first", "second", "third")],
                )
        self.assertEqual(list(Squad[:]), [])

    def test_releasing_saved_record_values_waits_until_everyone_leaves(self) -> None:
        seen = []

        class Part:
            def __del__(self):
                seen.append((
                        tuple(member in Holder for member in members),
                        tuple(member in Holder[...] for member in members),
                        ))

        class Holder(Tag):
            @Record
            def part(agent, stored):
                return Part()

        members = [Agent(), Agent()]

        for member in members:
            Holder(member)
            del member.__dict__["part"]

        gc.collect()
        self.assertEqual(seen, [])

        del Holder[:]
        gc.collect()

        self.assertEqual(len(seen), 2)
        self.assertTrue(all(not any(memberships) for memberships, _ in seen))
        self.assertEqual([sum(custody) for _, custody in seen], [1, 0])

    def test_retagging_during_cleanup_keeps_the_new_field_and_rip_chain(self) -> None:
        seen = []
        retagged = None

        class Station(Tag):
            @Rip
            def Dismiss(agent):
                nonlocal retagged
                seen.append(agent)

                if retagged is None:
                    retagged = second if agent is first else first
                    Station(retagged)
                    Station(newcomer)

        first, second, newcomer = Agent(), Agent(), Agent()
        Station(first)
        Station(second)

        del Station[:]

        self.assertCountEqual(seen, [first, second])
        self.assertCountEqual(Station[:], [retagged, newcomer])

        del Station[retagged]
        self.assertEqual(seen.count(retagged), 2)
        self.assertEqual(seen.count(first if retagged is second else second), 1)
        self.assertEqual(list(Station[:]), [newcomer])

    def test_base_field_rip_keeps_shape_membership(self) -> None:
        seen = []

        class Candidate(Tag):
            @Rip
            def Leave_Candidate(agent):
                seen.append("Candidate")

        class CIA(Candidate):
            @Rip
            def Leave_CIA(agent):
                seen.append("CIA")

        agent = Agent()
        CIA(agent)

        del Candidate[:]

        self.assertNotIn(agent, Candidate)
        self.assertIn(agent, CIA)
        self.assertEqual(list(CIA[:]), [agent])
        self.assertEqual(seen, ["Candidate"])

        del CIA[agent]
        self.assertEqual(seen, ["Candidate", "CIA"])

    def test_pin_field_rip_unpins_without_deleting_its_tags(self) -> None:
        seen = []

        @Pin
        class Duty(Tag):
            @Rip
            def Dismiss(tag):
                seen.append(tag)

        class First(Tag):
            pass

        class Second(Tag):
            pass

        Duty(First)
        Duty(Second)

        del Duty[:]

        self.assertCountEqual(seen, [First, Second])
        self.assertEqual(list(Duty[:]), [])
        self.assertTrue(issubclass(First, Tag))
        self.assertTrue(issubclass(Second, Tag))

    def test_empty_field_is_reusable_and_keeps_reports(self) -> None:
        class Stable(Tag):
            @Report
            def colour(tag):
                return "green"

        self.assertEqual(Stable.colour, "green")
        del Stable[:]
        self.assertEqual(Stable.colour, "green")

        agent = Agent()
        Stable(agent)
        self.assertIn(agent, Stable)

    def test_positional_slices_are_refused(self) -> None:
        class Stable(Tag):
            pass

        for key in (slice(1, None), slice(None, None, 2)):
            with self.subTest(key=key):
                with self.assertRaisesRegex(TypeError, "positional slices"):
                    del Stable[key]

    def test_failure_stops_this_invocation_but_later_member_can_retry(self) -> None:
        seen = []
        completed = []
        failed = None
        blocked = True
        labels = {}

        class Hazard(Tag):
            @Rip
            def Release(agent):
                seen.append(("Release", labels[agent]))

                if len(seen) == 1:
                    self.assertEqual(tuple(Hazard[:]), ())
                    self.assertCountEqual(Hazard[...], members)

            @Rip
            def Finish(agent):
                nonlocal failed
                seen.append(("Finish", labels[agent]))

                if failed is None and len(completed) == 1:
                    failed = agent

                if agent is failed and blocked:
                    raise ValueError("failed")

                completed.append(agent)

        members = [Agent(), Agent(), Agent()]

        for label, member in zip(("first", "second", "third"), members):
            labels[member] = label
            member.label = label
            Hazard(member)

        with self.assertRaises(TagCompositionError):
            del Hazard[:]

        self.assertIsNotNone(failed)
        visited = [member for member in members
                   if ("Release", labels[member]) in seen]
        unvisited, = [member for member in members if member not in visited]
        self.assertEqual(len(visited), 2)
        self.assertEqual(len(completed), 1)
        self.assertEqual(tuple(Hazard[:]), ())
        self.assertCountEqual(Hazard[...], [failed, unvisited])

        # Choose an unvisited member while another member still owes Rip.
        # Members are peers: this succeeds without replaying that other's
        # failed teardown or waiting for it to finish.
        del Hazard[unvisited]

        self.assertIn(unvisited, completed)
        self.assertEqual(seen.count(("Release", labels[unvisited])), 1)
        self.assertEqual(seen.count(("Finish", labels[unvisited])), 1)
        self.assertCountEqual(Hazard[...], [failed])

        blocked = False
        del Hazard[failed]
        self.assertEqual(seen.count(("Release", labels[failed])), 1)
        self.assertEqual(seen.count(("Finish", labels[failed])), 2)
        self.assertEqual(tuple(Hazard[...]), ())

    def test_interruption_keeps_every_unvisited_member_in_custody(self) -> None:
        seen = []
        interrupted = False

        class Fleet(Tag):
            @Rip
            def Stand_Down(agent):
                nonlocal interrupted
                seen.append(agent)

                if not interrupted:
                    interrupted = True
                    raise KeyboardInterrupt

        members = [Agent(), Agent(), Agent()]

        for member in members:
            Fleet(member)

        with self.assertRaises(KeyboardInterrupt):
            del Fleet[:]

        self.assertEqual(tuple(Fleet[:]), ())
        self.assertCountEqual(Fleet[...], members)
        self.assertEqual(len(seen), 1)
        interrupted_member = seen[0]
        chosen = next(member for member in members
                      if member is not interrupted_member)

        del Fleet[chosen]
        self.assertEqual(seen, [interrupted_member, chosen])
        self.assertCountEqual(Fleet[...], [interrupted_member] + [
                member for member in members
                if member not in (interrupted_member, chosen)
                ])
        remaining, = [member for member in members
                      if member not in (interrupted_member, chosen)]
        del Fleet[interrupted_member]
        del Fleet[remaining]

        self.assertCountEqual(seen,
                              [interrupted_member, interrupted_member,
                               chosen, remaining])
        self.assertEqual(tuple(Fleet[...]), ())

    def test_failed_field_rip_keeps_unvisited_record_values_until_retry(self) -> None:
        finalized = []
        fail = True
        failed_agent = None

        class Part:
            def __init__(self, label):
                self.label = label

            def __del__(self):
                finalized.append(self.label)

        class Holder(Tag):
            @Record
            def part(agent, stored):
                return Part(agent.label)

            @Rip
            def Release(agent):
                nonlocal fail, failed_agent

                if fail:
                    fail = False
                    failed_agent = agent
                    raise ValueError("still in use")

        first, second = Agent(), Agent()

        for label, member in (("first", first), ("second", second)):
            member.label = label
            Holder(member)
            del member.__dict__["part"]

        with self.assertRaises(TagCompositionError):
            del Holder[:]

        gc.collect()
        self.assertEqual(finalized, [])

        del Holder[failed_agent]
        gc.collect()
        self.assertEqual(finalized, [failed_agent.label])

        remaining = second if failed_agent is first else first
        del Holder[remaining]
        gc.collect()
        self.assertEqual(finalized, [failed_agent.label, remaining.label])
