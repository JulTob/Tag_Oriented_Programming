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

    def test_all_members_leave_before_fifo_teardowns_including_defective(self) -> None:
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

        self.assertEqual(
                seen,
                [(label, (False, False, False), ())
                 for label in ("first", "second", "third")],
                )
        self.assertEqual(list(Squad[:]), [])

    def test_releasing_saved_record_values_waits_until_everyone_leaves(self) -> None:
        seen = []

        class Part:
            def __del__(self):
                seen.append(tuple(member in Holder for member in members))

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

        self.assertEqual(seen, [(False, False), (False, False)])

    def test_retagging_during_cleanup_keeps_the_new_field_and_rip_chain(self) -> None:
        seen = []

        class Station(Tag):
            @Rip
            def Dismiss(agent):
                seen.append(agent)

                if agent is first:
                    Station(second)
                    Station(newcomer)

        first, second, newcomer = Agent(), Agent(), Agent()
        Station(first)
        Station(second)

        del Station[:]

        self.assertEqual(seen, [first, second])
        self.assertEqual(list(Station[:]), [second, newcomer])

        del Station[second]
        self.assertEqual(seen, [first, second, second])
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

        self.assertEqual(seen, [First, Second])
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

    def test_failure_is_reported_after_all_initial_memberships_end(self) -> None:
        seen_membership = []

        class Hazard(Tag):
            @Rip
            def Fail(agent):
                if agent is first:
                    seen_membership.append(
                            tuple(member in Hazard for member in members)
                            )
                    raise ValueError("failed")

        members = [Agent(), Agent()]
        first = members[0]

        for member in members:
            Hazard(member)

        # STEP-SPEC-32 still decides whether later teardowns run.
        with self.assertRaises(Exception):
            del Hazard[:]

        self.assertEqual(seen_membership, [(False, False)])
        self.assertEqual(list(Hazard[:]), [])
