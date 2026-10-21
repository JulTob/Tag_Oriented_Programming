"""Explicit Rip and whole-Field Rip share saved application cleanup."""

import gc
import unittest
import weakref
from unittest.mock import patch

from TopKit import Constant, Contract, Post, Rip, Tag, TagCompositionError
from TopKit.arrest import _arrest_of, _safehouse
from TopKit.fields import _field_of
from TopKit.lifecycle import _retry_arrested, _rip_field
import TopKit.lifecycle as lifecycle
from TopKit.rip_runs import _pending_run
from TopKit.state import _state_of


class Host:
    pass


class SafehouseReleaseRipTests(unittest.TestCase):
    def setUp(self):
        ledger = patch.dict(_safehouse, clear=True)
        ledger.start()
        self.addCleanup(ledger.stop)

    def test_single_rip_retry_resumes_the_failed_protocol(self):
        events = []
        broken = True
        class Role(Tag):
            @Rip
            def First(agent):
                events.append("first")
            @Rip
            def Verify(agent):
                events.append("verify")
                if broken:
                    raise ValueError("not ready")
            @Rip
            def Last(agent):
                events.append("last")
        agent = Host()
        Role(agent)
        with self.assertRaisesRegex(TagCompositionError, "Role teardown failed in: Verify"):
            del Role[agent]
        self.assertNotIn(agent, Role[:])
        self.assertEqual(events, ["first", "verify"])
        broken = False
        del Role[agent]
        self.assertEqual(events, ["first", "verify", "verify", "last"])
        self.assertIsNone(_arrest_of(agent))

    def test_another_explicit_rip_runs_before_retrying_older_work(self):
        events = []
        broken = True
        class Older(Tag):
            @Rip
            def Clean(agent):
                events.append("older")
                if broken:
                    raise ValueError("old failure")
        class Later(Tag):
            @Rip
            def Clean_Later(agent):
                events.append("later")
        agent = Host()
        Older(agent)
        Later(agent)
        with self.assertRaises(TagCompositionError):
            del Older[agent]
        broken = False
        del Later[agent]
        self.assertEqual(events, ["older", "later", "older"])
        self.assertIsNone(_arrest_of(agent))

    def test_field_is_empty_and_every_run_held_before_the_first_protocol(self):
        events = []
        members = [Host(), Host(), Host()]
        class Role(Tag):
            @Rip
            def Clean(agent):
                self.assertEqual(list(Role[:]), [])
                self.assertTrue(all(_pending_run(member, Role) is not None for member in members if member not in events))
                events.append(agent)
        for member in members:
            Role(member)
        _rip_field(Role)
        self.assertCountEqual(events, members)
        self.assertTrue(all(_arrest_of(member) is None for member in members))

    def test_later_field_member_may_retry_while_another_member_is_pending(self):
        attempted = []
        broken = True
        class Role(Tag):
            @Rip
            def Clean(agent):
                attempted.append(agent)
                if broken:
                    raise ValueError("blocked")
        members = [Host(), Host(), Host()]
        for member in members:
            Role(member)
        with self.assertRaises(TagCompositionError):
            _rip_field(Role)
        self.assertEqual(len(attempted), 1)
        self.assertEqual(list(Role[:]), [])
        self.assertTrue(all(_pending_run(member, Role) is not None for member in members))
        failed = attempted[0]
        chosen = next(member for member in members if member is not failed)
        broken = False
        del Role[chosen]
        self.assertIsNone(_arrest_of(chosen))
        self.assertIsNotNone(_arrest_of(failed))
        for member in members:
            if _arrest_of(member) is not None:
                del Role[member]
        self.assertTrue(all(_arrest_of(member) is None for member in members))

    def test_interruption_keeps_all_revoked_members_and_original_work(self):
        interrupt = KeyboardInterrupt()
        interrupted = True
        events = []
        class Role(Tag):
            @Rip
            def Clean(agent):
                events.append(agent)
                if interrupted:
                    raise interrupt
        members = [Host(), Host()]
        for member in members:
            Role(member)
        with self.assertRaises(KeyboardInterrupt) as caught:
            _rip_field(Role)
        self.assertIs(caught.exception, interrupt)
        self.assertEqual(len(events), 1)
        self.assertEqual(list(Role[:]), [])
        self.assertTrue(all(_arrest_of(member) is not None for member in members))
        interrupted = False
        for member in members:
            del Role[member]
        self.assertTrue(all(_arrest_of(member) is None for member in members))

    def test_old_failed_rip_keeps_fresh_same_tag_application_and_posts(self):
        broken = True
        class Role(Tag):
            @Post
            def Ready(agent):
                return agent in Role[:]
            @Rip
            def Rejoin(agent):
                Role(agent)
            @Rip
            def Close(agent):
                if broken:
                    raise ValueError("old application")
        agent = Host()
        Role(agent)
        with self.assertRaises(TagCompositionError):
            del Role[agent]
        fresh_posts = _state_of(agent).post_applications[Role]
        fresh_rips = _state_of(agent).rips[Role]
        self.assertIn(agent, Role[:])
        broken = False
        del Role[agent]
        self.assertIn(agent, Role[:])
        self.assertIs(_state_of(agent).post_applications[Role], fresh_posts)
        self.assertIs(_state_of(agent).rips[Role], fresh_rips)
        self.assertEqual(Contract.Status(agent), {"Ready": True})
        self.assertIsNone(_arrest_of(agent))

    def test_bulk_revocation_ends_ordinary_posts_and_preserves_constants(self):
        class Role(Tag):
            @Post
            def Ready(agent):
                return True
            @Constant
            @Post
            def NDA(agent):
                return True
            @Rip
            def Fail(agent):
                self.assertEqual(Contract.Status(agent), {"NDA": True})
                raise ValueError("blocked")
        agent = Host()
        Role(agent)
        with self.assertRaises(TagCompositionError):
            _rip_field(Role)
        self.assertEqual(Contract.Status(agent), {"NDA": True})

    def test_interrupted_post_runtime_update_does_not_remove_a_fresh_layer(self):
        class Role(Tag):
            @Post
            def Ready(agent):
                return agent in Role[:]
        agent = Host()
        Role(agent)
        with patch.object(lifecycle, "_set_runtime_type", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                del Role[agent]
        self.assertNotIn(agent, Role[:])
        # Ordinary Tagging would first drain the old arrest. A Rip callback
        # may instead create a fresh application while its old work remains.
        from TopKit.arrest import _rip_door
        with _rip_door(agent):
            Role(agent)
        fresh = _state_of(agent).post_applications[Role]
        del Role[agent]
        self.assertIn(agent, Role[:])
        self.assertIs(_state_of(agent).post_applications[Role], fresh)
        self.assertEqual(Contract.Status(agent), {"Ready": True})

    def test_empty_application_interruption_saves_its_original_field_seat(self):
        class Plain(Tag):
            pass
        agent = Host()
        Plain(agent)
        field = _field_of(Plain)
        original = field._Remove
        def Interrupt(target):
            original(target)
            raise KeyboardInterrupt()
        with patch.object(field, "_Remove", Interrupt):
            with self.assertRaises(KeyboardInterrupt):
                del Plain[agent]
        self.assertNotIn(agent, Plain[:])
        run = _pending_run(agent, Plain)
        self.assertIsNotNone(run)
        self.assertEqual(run.teardowns, ())
        del Plain[agent]
        self.assertIsNone(_arrest_of(agent))
        self.assertNotIn(Plain, _state_of(agent).active)

    def test_safehouse_keeps_agent_until_saved_cleanup_succeeds(self):
        broken = True
        class Role(Tag):
            @Rip
            def Close(agent):
                if broken:
                    raise ValueError("blocked")
        agent = Host()
        Role(agent)
        reference = weakref.ref(agent)
        with self.assertRaises(TagCompositionError):
            del Role[agent]
        del agent
        gc.collect()
        self.assertIsNotNone(reference())
        broken = False
        _retry_arrested(reference())
        gc.collect()
        self.assertIsNone(reference())


    def test_empty_rip_uses_memberships_left_after_field_removal_reenters(self):
        class Earlier(Tag):
            pass
        class Later(Tag):
            pass
        agent = Host()
        Earlier(agent)
        Later(agent)
        field = _field_of(Later)
        remove = field._Remove

        def Reenter(target):
            del Earlier[target]
            remove(target)

        with patch.object(field, '_Remove', Reenter):
            del Later[agent]
        self.assertNotIn(agent, Earlier[:])
        self.assertNotIn(agent, Later[:])
        self.assertEqual(_state_of(agent).active, [])
        self.assertIsNone(_arrest_of(agent))

    def test_empty_rip_retries_custody_created_during_its_field_removal(self):
        blocked = [True]
        calls = []
        class Older(Tag):
            @Rip
            def Clean(agent):
                calls.append('older')
                if blocked[0]:
                    raise ValueError('cleanup blocked')
        class Plain(Tag):
            pass
        agent = Host()
        Older(agent)
        Plain(agent)
        field = _field_of(Plain)
        remove = field._Remove

        def Arrest(target):
            try:
                del Older[target]
            except TagCompositionError:
                pass
            remove(target)

        with patch.object(field, '_Remove', Arrest):
            with self.assertRaises(TagCompositionError):
                del Plain[agent]
        self.assertNotIn(agent, Plain[:])
        self.assertEqual(calls, ['older', 'older'])
        self.assertIsNotNone(_arrest_of(agent))
        blocked[0] = False
        del Older[agent]
        self.assertEqual(calls, ['older', 'older', 'older'])
        self.assertIsNone(_arrest_of(agent))
