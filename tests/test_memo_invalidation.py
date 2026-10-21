"""A late metadata collision must not obstruct public Pin invalidation."""

from dataclasses import FrozenInstanceError
import gc
import unittest
import weakref

from TopKit import Pin, Public, Record, Tag
from TopKit.declarations import (
    _declaration_key, _declarations_of, _invalidate_declarations,
)


class Host:
    pass


class MemoInvalidationTests(unittest.TestCase):
    def receiver(self):
        class Metadata(type(Tag)):
            pass

        class Receiver(Tag, metaclass=Metadata):
            pass

        existing = Host()
        Receiver(existing)
        return Metadata, Receiver, existing

    def collide(self, metadata, receiver):
        calls = []

        def forbidden(*args):
            calls.append(args)
            raise RuntimeError("memo called the program's metadata descriptor")

        name = _declaration_key(receiver)
        setattr(metadata, name, property(forbidden, forbidden, forbidden))
        return name, calls

    def publish_label(self, receiver):
        class Given(Pin):
            @Public
            @Record
            def label(tag):
                return {"owner": tag.__name__}

            @Public
            def Identify(tag, agent):
                return tag.label

        Given(receiver)
        return Given

    def assert_label(self, receiver, *agents):
        for agent in agents:
            with self.subTest(agent=agent):
                self.assertIs(agent.label, receiver.label)
                self.assertIs(agent.Identify(), receiver.label)

    def test_public_pin_reaches_future_agents_after_a_late_metadata_collision(self):
        metadata, receiver, existing = self.receiver()
        _, calls = self.collide(metadata, receiver)
        self.publish_label(receiver)

        future = Host()
        receiver(future)
        self.assert_label(receiver, existing, future)
        self.assertEqual(calls, [])

    def test_retired_scan_releases_references_when_metadata_blocks_deletion(self):
        metadata, receiver, _ = self.receiver()
        old_scan = weakref.ref(_declarations_of(receiver))
        self.assertIsNotNone(old_scan())
        _, calls = self.collide(metadata, receiver)

        self.publish_label(receiver)
        gc.collect()
        gc.collect()
        self.assertIsNone(old_scan())
        self.assertEqual(calls, [])

    def test_removing_the_collision_resumes_caching_without_reviving_the_old_scan(self):
        metadata, receiver, existing = self.receiver()
        old_scan = weakref.ref(_declarations_of(receiver))
        name, calls = self.collide(metadata, receiver)
        self.publish_label(receiver)
        delattr(metadata, name)

        future = Host()
        receiver(future)
        self.assert_label(receiver, existing, future)
        current = _declarations_of(receiver)
        self.assertIsNot(current, old_scan())
        self.assertIs(_declarations_of(receiver), current)
        self.assertEqual(calls, [])

    def test_repeated_publication_invalidates_a_retired_wrapper(self):
        metadata, receiver, existing = self.receiver()
        name, calls = self.collide(metadata, receiver)
        self.publish_label(receiver)

        middle = Host()
        receiver(middle)

        class Later(Pin):
            @Public
            @Record
            def revision(tag):
                return 2

            @Public
            def Revision(tag, agent):
                return tag.revision

        Later(receiver)
        delattr(metadata, name)

        future = Host()
        receiver(future)
        self.assert_label(receiver, existing, middle, future)
        for agent in (existing, middle, future):
            self.assertEqual((agent.revision, agent.Revision()), (2, 2))
        self.assertEqual(calls, [])

    def test_invalidation_preserves_a_foreign_memos_payload(self):
        metadata, receiver, existing = self.receiver()

        class Original(Tag):
            def Work(agent):
                return "original"

        original_scan = _declarations_of(Original)
        foreign = vars(Original)[_declaration_key(Original)]
        name = _declaration_key(receiver)
        setattr(receiver, name, foreign)
        _, calls = self.collide(metadata, receiver)
        self.publish_label(receiver)

        future = Host()
        receiver(future)
        self.assert_label(receiver, existing, future)
        self.assertIs(vars(receiver)[name], foreign)
        self.assertIs(_declarations_of(Original), original_scan)
        self.assertEqual(calls, [])

    def test_retired_wrapper_does_not_shadow_a_later_base_binding(self):
        class Metadata(type(Tag)):
            pass

        class Base(Tag):
            pass

        class Receiver(Base, metaclass=Metadata):
            pass

        existing = Host()
        Receiver(existing)
        name, calls = self.collide(Metadata, Receiver)
        self.publish_label(Receiver)
        setattr(Base, name, "application-private")
        delattr(Metadata, name)

        future = Host()
        Receiver(future)
        self.assert_label(Receiver, existing, future)
        first = _declarations_of(Receiver)
        self.assertIsNot(_declarations_of(Receiver), first)
        self.assertEqual(vars(Base)[name], "application-private")
        self.assertEqual(calls, [])

    def test_retirement_callbacks_can_replace_or_recursively_invalidate_the_binding(self):
        for kind in ("replace", "invalidate"):
            with self.subTest(kind=kind):
                _, receiver, existing = self.receiver()
                name = _declaration_key(receiver)
                calls = []

                def on_retirement(_):
                    calls.append(kind)
                    if kind == "replace":
                        setattr(receiver, name, "application-private")
                    else:
                        _invalidate_declarations(receiver)

                old_scan = weakref.ref(_declarations_of(receiver), on_retirement)
                self.publish_label(receiver)
                self.assertIsNone(old_scan())
                self.assertEqual(calls, [kind])
                if kind == "replace":
                    self.assertEqual(vars(receiver)[name], "application-private")

                future = Host()
                receiver(future)
                self.assert_label(receiver, existing, future)

    def test_memo_identity_remains_immutable(self):
        _, receiver, _ = self.receiver()
        name = _declaration_key(receiver)
        memo = vars(receiver)[name]
        for field, value in (("owner", Tag), ("name", "foreign")):
            with self.subTest(field=field):
                with self.assertRaises(FrozenInstanceError):
                    setattr(memo, field, value)


if __name__ == "__main__":
    unittest.main()
