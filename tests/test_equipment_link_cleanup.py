"""Link cleanup keeps original Pair work independently of fresh membership."""

import gc
import unittest
import weakref

from TopKit import (Action, Link, Post, Public, Record, Rip, Tag,
                    TagArrestedAccessError, TagCompositionError,
                    TagPostconditionError, agent, contact)
from TopKit.arrest import _arrest_of
from TopKit.arrest import _safehouse


class Host:
    pass


class EquipmentLinkCleanupTests(unittest.TestCase):
    def test_failed_pair_rip_retries_its_saved_steps(self):
        calls = []
        fail = [True]

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def position(agent, contact, *, position="pack"):
                    return position

                @Rip
                def Put_Down(agent, contact):
                    calls.append("put down")

                @Rip
                def Unfasten(agent, contact):
                    calls.append(agent.Carries[contact].position)
                    if fail[0]:
                        raise ValueError("strap jammed")

        hero, sword = Host(), Host()
        Inventory(hero)
        hero.Carries(sword, position="belt")
        with self.assertRaises(TagCompositionError):
            del hero.Carries[sword]
        self.assertNotIn(sword, hero.Carries[:])
        self.assertIn(sword, hero.Carries[...])
        fail[0] = False
        del hero.Carries[sword]
        self.assertEqual(calls, ["put down", "belt", "belt"])
        self.assertIsNone(_arrest_of(sword))
        self.assertFalse(hero.Carries[...])

    def test_failed_old_pair_does_not_rip_fresh_pair(self):
        calls = []
        fail = [True]

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def position(agent, contact, *, position="pack"):
                    return position

                @Rip
                def Repack(agent, contact):
                    agent.Carries(contact, position="new")
                    calls.append("repacked")

                @Rip
                def Release_Old(agent, contact):
                    calls.append("release old")
                    if fail[0]:
                        raise ValueError("old strap jammed")

        hero, sword = Host(), Host()
        Inventory(hero)
        hero.Carries(sword, position="old")
        with self.assertRaises(TagCompositionError):
            del hero.Carries[sword]
        self.assertIn(sword, hero.Carries[:])
        fail[0] = False
        del hero.Carries[sword]
        self.assertIn(sword, hero.Carries[:])
        self.assertEqual(hero.Carries[sword].position, "new")
        self.assertEqual(calls, ["repacked", "release old", "release old"])
        self.assertIsNone(_arrest_of(sword))

    def test_bulk_rip_revokes_every_contact_before_first_callback(self):
        seen = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Rip
                def Put_Down(agent, contact):
                    seen.append(len(agent.Carries[:]))

        hero, sword, shield = Host(), Host(), Host()
        Inventory(hero)
        hero.Carries(sword)
        hero.Carries(shield)
        del hero.Carries[:]
        self.assertEqual(seen, [0, 0])
        self.assertNotIn(sword, hero.Carries[:])
        self.assertNotIn(shield, hero.Carries[:])

    def test_contact_reads_and_saved_link_calls_retry_failed_cleanup(self):
        fail = [True]
        calls = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Rip
                def Release(owner, target):
                    calls.append("release")
                    if fail[0]:
                        raise ValueError("jammed")

        hero, sword = Host(), Host()
        sword.name = "sword"
        Inventory(hero)
        carry = hero.Carries
        carry(sword)
        with self.assertRaises(TagCompositionError):
            del carry[sword]
        with self.assertRaises(TagArrestedAccessError):
            _ = sword.name
        with self.assertRaises(TagArrestedAccessError):
            carry(sword)
        self.assertEqual(calls, ["release"] * 3)
        fail[0] = False
        self.assertEqual(sword.name, "sword")
        carry(sword)
        self.assertIn(sword, carry)

    def test_fresh_membership_is_raw_only_until_old_cleanup_finishes(self):
        fail = [True]

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def position(owner, target, *, position="pack"):
                    return position

                @Action
                def Where(owner, target):
                    return owner.Carries[target].position

                @Rip
                def Repack(owner, target):
                    owner.Carries(target, position="fresh")

                @Rip
                def Release(owner, target):
                    if fail[0]:
                        raise ValueError("jammed")

        hero, sword = Host(), Host()
        Inventory(hero)
        carry = hero.Carries
        carry(sword)
        view, where = carry[sword], carry[sword].Where
        with self.assertRaises(TagCompositionError):
            del carry[sword]
        self.assertIn(sword, carry[:])
        self.assertNotIn(sword, carry)
        self.assertNotIn(sword, ~carry)
        self.assertIn(sword, carry[...])
        with self.assertRaises(TagArrestedAccessError):
            _ = view.position
        with self.assertRaises(TagArrestedAccessError):
            where()
        fail[0] = False
        self.assertEqual(where(), "fresh")
        self.assertIn(sword, carry)
        self.assertNotIn(sword, carry[...])

    def test_bulk_failure_allows_explicit_later_contact_cleanup(self):
        calls = []
        failing = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Rip
                def Release(owner, target):
                    self.assertEqual(len(owner.Carries[:]), 0)
                    calls.append(target)
                    if any(target is item for item in failing):
                        raise ValueError("jammed")

        hero, sword, shield = Host(), Host(), Host()
        Inventory(hero)
        carry = hero.Carries
        carry(sword)
        carry(shield)
        failing.append(sword)
        with self.assertRaises(TagCompositionError):
            del carry[:]
        self.assertEqual(list(carry[:]), [])
        self.assertEqual(list(carry[...]), [sword, shield])
        del carry[shield]
        self.assertEqual(list(carry[...]), [sword])
        self.assertEqual(calls, [sword, shield])
        failing.clear()
        del carry[sword]

    def test_pair_posts_guard_contact_publications_but_allow_inspection(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Public
                @Record
                def position(owner, target):
                    return "pack"

                @Post
                def Stored(owner, target):
                    return bool(owner.Carries[target].position)

                @Public
                @Action
                def Where(owner, target):
                    return owner.Carries[target].position

        hero, sword = Host(), Host()
        Inventory(hero)
        hero.Carries(sword)
        view = hero.Carries[sword]
        view.position = ""
        self.assertEqual(view.position, "")
        self.assertIn(sword, ~hero.Carries)
        with self.assertRaises(TagPostconditionError):
            _ = sword.position
        with self.assertRaises(TagPostconditionError):
            sword.Where()
        view.position = "belt"
        self.assertEqual(sword.Where(), "belt")

    def test_cyclic_owner_finalization_preserves_failed_pair_cleanup(self):
        calls = []
        fail = [True]

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Rip
                def Release(owner, target):
                    calls.append("release")
                    if fail[0]:
                        raise ValueError("jammed")

        hero, sword = Host(), Host()
        hero.cycle = hero
        Inventory(hero)
        carry = hero.Carries
        carry(sword)
        owner_reference = weakref.ref(hero)
        before = set(_safehouse)
        del hero
        gc.collect()
        self.assertIsNone(owner_reference())
        self.assertEqual(calls, ["release"])
        self.assertIn(sword, carry[...])
        fail[0] = False
        del carry[sword]
        self.assertEqual(calls, ["release", "release"])
        self.assertNotIn(sword, carry[...])
        self.assertEqual(set(_safehouse), before)

    def test_contact_finalization_exposes_failed_cleanup_in_safehouse(self):
        for cyclic in (False, True):
            with self.subTest(cyclic=cyclic):
                calls = []
                fail = [True]

                class Inventory(Tag):
                    @Link(agent, contact)
                    class Carries(Tag):
                        @Rip
                        def Release(owner, target):
                            calls.append("release")
                            if fail[0]:
                                raise ValueError("jammed")

                hero, sword = Host(), Host()
                if cyclic:
                    sword.cycle = sword
                Inventory(hero)
                carry = hero.Carries
                carry(sword)
                before = set(_safehouse)
                del sword
                gc.collect()
                self.assertEqual(calls, ["release"])
                detained, = list(carry[...])
                self.assertNotIn(detained, carry[:])
                self.assertNotIn(detained, carry)
                self.assertNotIn(detained, ~carry)
                self.assertFalse(bool(detained))
                fail[0] = False
                del carry[detained]
                self.assertEqual(calls, ["release", "release"])
                self.assertEqual(set(_safehouse), before)

    def test_abandoned_link_generator_does_not_finalize_while_arrested(self):
        finalized = []
        fail = [True]

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Action
                def Inspect(owner, target):
                    try:
                        yield "ready"
                    finally:
                        finalized.append(_arrest_of(target) is not None)

                @Rip
                def Release(owner, target):
                    if fail[0]:
                        raise ValueError("jammed")

        hero, sword = Host(), Host()
        Inventory(hero)
        carry = hero.Carries
        carry(sword)
        result = carry[sword].Inspect()
        self.assertEqual(next(result), "ready")
        with self.assertRaises(TagCompositionError):
            del carry[sword]
        with self.assertRaises(TagArrestedAccessError):
            next(result)
        # Custody must start before the caller drops the proxy. In a
        # cycle, GC may schedule the native finalizer before __del__ on
        # the proxy gets a chance to park it.
        self.assertTrue(any(source is result.native
                            for source in _arrest_of(sword).lazy))
        pair = result.ends.pair()
        self.assertTrue(any(source is result.native
                            for source in _arrest_of(pair).lazy))
        del result
        gc.collect()
        self.assertEqual(finalized, [])
        fail[0] = False
        del carry[sword]
        gc.collect()
        self.assertEqual(finalized, [False])

    def test_link_generator_completion_cannot_release_value_during_arrest(self):
        fail = [True]

        class Stuck(Tag):
            @Rip
            def Release(target):
                if fail[0]:
                    raise ValueError("jammed")

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Action
                def Inspect(owner, target):
                    yield "ready"
                    try:
                        del Stuck[target]
                    except TagCompositionError:
                        pass
                    return "protected result"

        hero, sword = Host(), Host()
        Inventory(hero)
        Stuck(sword)
        hero.Carries(sword)
        result = hero.Carries[sword].Inspect()
        self.assertEqual(next(result), "ready")
        with self.assertRaises(TagArrestedAccessError):
            next(result)
        fail[0] = False
        del Stuck[sword]

    def test_mutual_owner_contact_cycles_hand_off_both_cleanup_seats(self):
        for contact_first in (False, True):
            for initially_fails in (False, True):
                with self.subTest(contact_first=contact_first, fails=initially_fails):
                    calls = []
                    fail = [initially_fails]

                    class Inventory(Tag):
                        @Link(agent, contact)
                        class Carries(Tag):
                            @Rip
                            def Release(owner, target):
                                self.assertIs(owner.item, target)
                                self.assertIs(target.bearer, owner)
                                calls.append("release")
                                if fail[0]:
                                    raise ValueError("jammed")

                    if contact_first:
                        sword, hero = Host(), Host()
                    else:
                        hero, sword = Host(), Host()
                    hero.item, sword.bearer = sword, hero
                    Inventory(hero)
                    carry = hero.Carries
                    carry(sword)
                    before = set(_safehouse)
                    del hero, sword
                    gc.collect()
                    self.assertEqual(calls, ["release"])
                    if initially_fails:
                        detained, = list(carry[...])
                        fail[0] = False
                        del carry[detained]
                        self.assertEqual(calls, ["release", "release"])
                        del detained
                    self.assertEqual(list(carry[...]), [])
                    self.assertEqual(set(_safehouse), before)

    def test_owner_end_revokes_whole_link_before_first_cleanup(self):
        seen = []
        fail = [True]

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Rip
                def Release(owner, target):
                    seen.append(len(owner.Carries[:]))
                    if fail[0]:
                        raise ValueError("jammed")

        hero, sword, shield = Host(), Host(), Host()
        Inventory(hero)
        carry = hero.Carries
        carry(sword)
        carry(shield)
        del hero
        gc.collect()
        self.assertEqual(seen, [0])
        self.assertEqual(list(carry[:]), [])
        self.assertEqual(list(carry[...]), [sword, shield])
        fail[0] = False
        del carry[shield]
        del carry[sword]
        self.assertEqual(seen, [0, 0, 0])
        self.assertEqual(list(carry[...]), [])


if __name__ == "__main__":
    unittest.main()
