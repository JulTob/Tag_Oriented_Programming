"""The whole-Field Rip success path and its current failure boundary."""

from __future__ import annotations

import gc
import unittest
from unittest.mock import patch

import TopKit.lifecycle as lifecycle
from TopKit import Pin
from TopKit import Post
from TopKit import Record
from TopKit import Report
from TopKit import Rip
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit.arrest import _arrest_of
from TopKit.fields import _field_of
from TopKit.state import _state_of
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

    def test_bulk_rip_retries_each_members_older_arrest_after_own_rip(self) -> None:
        events = []
        blocked = {}

        class Wizard(Tag):
            @Rip
            def Release(agent):
                events.append(("Wizard", agent))

                if blocked[agent]:
                    raise ValueError("still blocked")

        class Fighter(Tag):
            @Rip
            def Stand_Down(agent):
                events.append(("Fighter", agent))
                self.assertEqual(tuple(Fighter[:]), ())

        members = [Agent(), Agent()]

        for member in members:
            blocked[member] = True
            Wizard(member)
            Fighter(member)

            with self.assertRaises(TagCompositionError):
                del Wizard[member]

        self.assertCountEqual(Fighter[:], members)
        self.assertCountEqual(Wizard[...], members)
        events.clear()

        with self.assertRaises(TagCompositionError):
            del Fighter[:]

        attempted = [member for kind, member in events if kind == "Fighter"]
        self.assertEqual(len(attempted), 1)
        first = attempted[0]
        other, = [member for member in members if member is not first]
        self.assertEqual(events, [("Fighter", first), ("Wizard", first)])
        self.assertEqual(tuple(Fighter[:]), ())
        self.assertCountEqual(Fighter[...], [other])
        self.assertCountEqual(Wizard[...], members)

        blocked[other] = False
        del Fighter[other]
        self.assertEqual(events[-2:], [("Fighter", other), ("Wizard", other)])
        self.assertCountEqual(Wizard[...], [first])

        blocked[first] = False
        del Wizard[first]
        self.assertEqual(events.count(("Fighter", first)), 1)
        self.assertEqual(events.count(("Fighter", other)), 1)
        self.assertEqual(tuple(Fighter[...]), ())
        self.assertEqual(tuple(Wizard[...]), ())

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

    def test_bulk_rip_reuses_run_saved_before_interrupted_single_revoke(self) -> None:
        seen = []

        class Guard(Tag):
            @Rip
            def Clean(agent):
                seen.append(agent)

        agent = Agent()
        Guard(agent)
        field = _field_of(Guard)

        def Interrupt(target):
            raise KeyboardInterrupt("before Field removal")

        with patch.object(field, "_Remove", Interrupt):
            with self.assertRaises(KeyboardInterrupt):
                del Guard[agent]

        self.assertIn(agent, Guard[:])
        self.assertIn(agent, Guard[...])
        self.assertEqual(seen, [])

        del Guard[:]

        self.assertNotIn(agent, Guard[:])
        self.assertNotIn(agent, Guard[...])
        self.assertEqual(seen, [agent])

    def test_bulk_retry_reuses_run_saved_during_bulk_revocation(self) -> None:
        seen = []

        class Guard(Tag):
            @Rip
            def Clean(agent):
                seen.append(agent)

        members = [Agent(), Agent(), Agent()]

        for member in members:
            Guard(member)

        field = _field_of(Guard)
        remove = field._Remove
        attempted = 0

        def Interrupt(target):
            nonlocal attempted
            attempted += 1

            if attempted == 2:
                raise KeyboardInterrupt("during Field revocation")

            return remove(target)

        with patch.object(field, "_Remove", Interrupt):
            with self.assertRaises(KeyboardInterrupt):
                del Guard[:]

        remaining = list(Guard[:])
        self.assertEqual(len(remaining), 2)
        self.assertEqual(len(Guard[...]), 2)
        self.assertEqual(seen, [])
        revoked, = [member for member in members if member not in remaining]
        self.assertIn(revoked, Guard[...])

        del Guard[:]

        self.assertCountEqual(seen, remaining)
        self.assertEqual(tuple(Guard[:]), ())
        self.assertCountEqual(Guard[...], [revoked])

        del Guard[revoked]
        self.assertCountEqual(seen, members)
        self.assertEqual(len(seen), 3)
        self.assertEqual(tuple(Guard[...]), ())

    def test_bulk_rip_keeps_fresh_application_separate_from_older_arrest(self) -> None:
        attempts = 0

        class Guard(Tag):
            @Rip
            def Clean(agent):
                nonlocal attempts
                attempts += 1

                if attempts == 1:
                    raise ValueError("old application failed")

        agent = Agent()
        Guard(agent)

        with self.assertRaises(TagCompositionError):
            del Guard[agent]

        self.assertNotIn(agent, Guard[:])
        self.assertIn(agent, Guard[...])
        Guard(agent)
        self.assertIn(agent, Guard[:])

        del Guard[:]

        # The new application Rips once, then the old arrest retries once.
        self.assertEqual(attempts, 3)
        self.assertNotIn(agent, Guard[:])
        self.assertNotIn(agent, Guard[...])

    def test_interrupted_empty_run_does_not_stand_for_fresh_tagging(self) -> None:
        class Plain(Tag):
            pass

        agent = Agent()
        Plain(agent)
        state = _state_of(agent)

        class InterruptingActive(list):
            def pop(self, index=-1):
                value = super().pop(index)
                raise KeyboardInterrupt("after active removal")

        state.active = InterruptingActive(state.active)

        with self.assertRaises(KeyboardInterrupt):
            del Plain[:]

        old_run, = _arrest_of(agent).runs
        self.assertFalse(old_run.revoked)
        state.active = list(state.active)
        Plain(agent)
        self.assertIn(agent, Plain[:])

        selected = []
        original = lifecycle._run_one

        def Capture(target, current_state, run):
            selected.append(run)
            return original(target, current_state, run)

        with patch.object(lifecycle, "_run_one", Capture):
            del Plain[:]

        self.assertEqual(len(selected), 1)
        self.assertIsNot(selected[0], old_run)
        self.assertNotIn(agent, Plain[:])
        self.assertNotIn(agent, Plain[...])

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
