"""Provisional tests for mutation while judging compound populations (#99)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from TopKit import Post, Tag
from TopKit.fields import _Field
from TopKit.fields import _Population

from ._fixtures import Agent


class CompoundFieldMutationTests(unittest.TestCase):
    def test_later_post_cannot_keep_a_ripped_left_witness(self) -> None:
        for operator in ("&", "-"):
            for query in ("walk", "in", "len", "bool"):
                with self.subTest(operator=operator, query=query):
                    class Left(Tag):
                        pass

                    armed = [False]
                    calls = []

                    class Right(Tag):
                        @Post
                        def Ready(agent):
                            calls.append(agent)
                            if armed[0]:
                                del Left[agent]
                                return operator == "&"
                            return True

                    agent = Agent()
                    Left(agent)
                    Right(agent)
                    armed[0] = True
                    calls.clear()
                    population = Left[:] & Right if operator == "&" else Left[:] - Right

                    result = {
                            "walk": lambda: [member for member in population],
                            "in": lambda: agent in population,
                            "len": lambda: len(population),
                            "bool": lambda: bool(population),
                            }[query]()

                    self.assertEqual(result, [] if query == "walk" else 0)
                    self.assertEqual(calls, [agent])
                    self.assertNotIn(agent, Left[:])

    def test_outer_post_does_not_replay_selected_inner_union(self) -> None:
        for query in ("walk", "in", "len", "bool"):
            with self.subTest(query=query):
                class Left(Tag):
                    pass

                class Backup(Tag):
                    pass

                armed = [False]
                calls = []

                class Check(Tag):
                    @Post
                    def Ready(agent):
                        calls.append(agent)
                        if armed[0]:
                            del Left[agent]
                        return True

                agent = Agent()
                Left(agent)
                Backup(agent)
                Check(agent)
                armed[0] = True
                calls.clear()
                population = (Left[:] | Backup[:]) & Check

                result = {
                        "walk": lambda: [member for member in population],
                        "in": lambda: agent in population,
                        "len": lambda: len(population),
                        "bool": lambda: bool(population),
                        }[query]()

                self.assertEqual(result, [] if query == "walk" else 0)
                self.assertEqual(calls, [agent])
                self.assertIn(agent, Backup[:])

    def test_rip_and_retag_restores_the_same_field_witness(self) -> None:
        class Left(Tag):
            pass

        armed = [False]
        calls = []

        class Check(Tag):
            @Post
            def Ready(agent):
                calls.append(agent)
                if armed[0]:
                    armed[0] = False
                    del Left[agent]
                    Left(agent)
                return True

        agent = Agent()
        Left(agent)
        Check(agent)
        armed[0] = True
        calls.clear()
        population = Left[:] & Check

        self.assertEqual([member for member in population], [agent])
        # The nested Tagging itself may re-evaluate existing Posts.
        self.assertEqual(calls, [agent, agent])

    def test_union_tries_its_right_side_when_its_left_never_passes(self) -> None:
        for query in ("walk", "in", "len", "bool"):
            with self.subTest(query=query):
                class Left(Tag):
                    pass

                class Backup(Tag):
                    pass

                armed = [False]
                calls = []

                class Check(Tag):
                    @Post
                    def Ready(agent):
                        calls.append(agent)
                        if armed[0]:
                            del Left[agent]
                        return True

                agent = Agent()
                Left(agent)
                Check(agent)
                Backup(agent)
                armed[0] = True
                calls.clear()
                population = (Left[:] & Check) | Backup[:]

                result = {
                        "walk": lambda: [member for member in population],
                        "in": lambda: agent in population,
                        "len": lambda: len(population),
                        "bool": lambda: bool(population),
                        }[query]()

                self.assertEqual(result, [agent] if query == "walk" else 1)
                self.assertEqual(calls, [agent])

    def test_negative_evidence_is_saved_after_its_one_check(self) -> None:
        class Included(Tag):
            pass

        class Excluded(Tag):
            pass

        armed = [False]
        calls = []

        class Check(Tag):
            @Post
            def Ready(agent):
                calls.append(agent)
                if armed[0]:
                    armed[0] = False
                    Excluded(agent)
                return True

        agent = Agent()
        Included(agent)
        Check(agent)
        armed[0] = True
        calls.clear()
        population = (Included[:] - Excluded[:]) & Check

        self.assertEqual([member for member in population], [agent])
        # Excluded's Tagging checks the already established Post too.
        self.assertEqual(calls, [agent, agent])
        self.assertIn(agent, Excluded[:])

    def test_custom_population_can_invalidate_an_earlier_field(self) -> None:
        class Left(Tag):
            pass

        checks = []

        class RipLeft(_Population):
            def __contains__(self, agent):
                checks.append(agent)
                del Left[agent]
                return True

        agent = Agent()
        Left(agent)
        population = Left[:] & RipLeft()

        self.assertNotIn(agent, population)
        self.assertEqual(checks, [agent])

    def test_invalid_inner_intersection_skips_the_next_post(self) -> None:
        class First(Tag):
            pass

        armed = [False]
        calls = []

        class Ripper(Tag):
            @Post
            def Ready(agent):
                if armed[0]:
                    del First[agent]
                return True

        class Later(_Population):
            def __contains__(self, agent):
                calls.append(agent)
                return True

        agent = Agent()
        First(agent)
        Ripper(agent)
        armed[0] = True
        calls.clear()

        self.assertNotIn(agent, (First[:] & Ripper) & Later())
        self.assertEqual(calls, [])

    def test_deep_sound_intersections_check_each_field_a_bounded_number_of_times(self) -> None:
        class Member(Tag):
            pass

        agent = Agent()
        Member(agent)
        distinct = [
                type(f"Field_{index}", (Tag,), {})
                for index in range(300)
                ]
        for tag in distinct:
            tag(agent)
        original = _Field.__contains__

        for tags in ([Member] * 500, distinct):
            for direction in ("left", "right"):
                with self.subTest(fields=len(set(tags)), direction=direction):
                    population = tags[0]

                    for tag in tags[1:]:
                        population = (
                                population & tag
                                if direction == "left"
                                else tag & population
                                )

                    checks = [0]

                    def counted(field, member):
                        checks[0] += 1
                        return original(field, member)

                    with patch.object(_Field, "__contains__", counted):
                        self.assertIn(agent, population)
                        self.assertEqual([member for member in population], [agent])

                    self.assertLess(checks[0], 10 * len(tags))


if __name__ == "__main__":
    unittest.main()
