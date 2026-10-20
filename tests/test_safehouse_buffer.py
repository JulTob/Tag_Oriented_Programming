"""An acquired Python Host buffer can finish its release after arrest."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from TopKit import Rip
from TopKit import Tag
from TopKit import TagArrestedAccessError
from TopKit import TagCompositionError
from TopKit.arrest import _safehouse
from TopKit.buffers import _buffers


class SafehouseBufferTests(unittest.TestCase):
    def setUp(self) -> None:
        empty_ledger = patch.dict(_safehouse, clear=True)
        empty_ledger.start()
        self.addCleanup(empty_ledger.stop)
        empty_buffers = patch.dict(_buffers, clear=True)
        empty_buffers.start()
        self.addCleanup(empty_buffers.stop)

    def test_acquired_view_releases_once_after_failed_rip(self) -> None:
        events = []
        ready = False

        class Host:
            resource = "open"

            def __buffer__(self, flags):
                events.append("acquire")
                return memoryview(bytearray(b"abc"))

            def __release_buffer__(self, view):
                events.append(("release", self.resource, bytes(view)))

        class Custody(Tag):
            @Rip
            def Leave(agent):
                if not ready:
                    raise RuntimeError("unfinished")

        host = Host()
        Custody(host)
        view = memoryview(host)

        with self.assertRaises(TagCompositionError):
            del Custody[host]

        with self.assertRaises(TagArrestedAccessError):
            memoryview(host)
        with self.assertRaises(TagArrestedAccessError):
            host.__release_buffer__(memoryview(b"forged"))

        view.release()
        view.release()
        self.assertEqual(events, ["acquire", ("release", "open", b"abc")])
        self.assertFalse(_buffers)

        with self.assertRaises(TagArrestedAccessError):
            host.__release_buffer__(memoryview(b"forged"))
        ready = True
        del Custody[host]

    def test_same_returned_view_has_one_release_per_acquisition(self) -> None:
        events = []

        class Host:
            def __init__(self):
                self.source = memoryview(bytearray(b"shared"))

            def __buffer__(self, flags):
                return self.source

            def __release_buffer__(self, view):
                events.append((view is self.source, bytes(view)))

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        host = Host()
        Custody(host)
        first = memoryview(host)
        second = memoryview(host)
        with self.assertRaises(TagCompositionError):
            del Custody[host]

        first.release()
        second.release()
        self.assertEqual(events, [(True, b"shared"), (True, b"shared")])
        self.assertFalse(_buffers)
        with self.assertRaises(TagArrestedAccessError):
            host.__release_buffer__(object.__getattribute__(host, "source"))

    def test_child_view_keeps_the_release_ticket_until_final_release(self) -> None:
        events = []

        class Host:
            resource = "open"

            def __buffer__(self, flags):
                return memoryview(bytearray(b"abc"))

            def __release_buffer__(self, view):
                events.append((self.resource, bytes(view)))

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        host = Host()
        Custody(host)
        parent = memoryview(host)
        child = parent[:]
        parent.release()
        self.assertEqual(events, [])

        with self.assertRaises(TagCompositionError):
            del Custody[host]
        child.release()
        self.assertEqual(events, [("open", b"abc")])
        self.assertFalse(_buffers)

    def test_rejected_pre_released_view_keeps_no_release_ticket(self) -> None:
        events = []

        class Host:
            def __init__(self):
                self.source = memoryview(bytearray(b"abc"))
                self.source.release()

            def __buffer__(self, flags):
                return self.source

            def __release_buffer__(self, view):
                events.append("release")

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        host = Host()
        Custody(host)
        with self.assertRaises(ValueError):
            memoryview(host)
        self.assertEqual(events, [])
        self.assertFalse(_buffers)

        with self.assertRaises(TagCompositionError):
            del Custody[host]
        with self.assertRaises(TagArrestedAccessError):
            host.__release_buffer__(object.__getattribute__(host, "source"))

    def test_host_none_mask_does_not_reenable_base_buffer(self) -> None:
        class Base:
            def __buffer__(self, flags):
                return memoryview(bytearray(b"base"))

        class Host(Base):
            __buffer__ = None

        class Present(Tag):
            pass

        host = Host()
        with self.assertRaises(TypeError):
            memoryview(host)
        Present(host)
        with self.assertRaises(TypeError):
            memoryview(host)

    def test_buffer_returned_after_self_caught_rip_does_not_escape(self) -> None:
        events = []
        ready = False

        class Host:
            resource = "open"

            def __buffer__(self, flags):
                view = memoryview(bytearray(b"secret"))
                try:
                    del Custody[self]
                except TagCompositionError:
                    events.append("rip failed")
                return view

            def __release_buffer__(self, view):
                events.append(("release", self.resource, bytes(view)))

        class Custody(Tag):
            @Rip
            def Leave(agent):
                if not ready:
                    raise RuntimeError("unfinished")

        host = Host()
        Custody(host)
        with self.assertRaises(TagArrestedAccessError) as caught:
            memoryview(host)
        self.assertIsInstance(caught.exception.__cause__, RuntimeError)
        self.assertEqual(
                events, ["rip failed", ("release", "open", b"secret")],
                )
        self.assertFalse(_buffers)
        ready = True
        del Custody[host]

    def test_view_acquired_before_rip_tag_has_matching_release(self) -> None:
        events = []

        class Host:
            resource = "open"

            def __buffer__(self, flags):
                return memoryview(bytearray(b"old"))

            def __release_buffer__(self, view):
                events.append((self.resource, bytes(view)))

        class Present(Tag):
            pass

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        host = Host()
        Present(host)
        view = memoryview(host)
        Custody(host)
        with self.assertRaises(TagCompositionError):
            del Custody[host]

        view.release()
        self.assertEqual(events, [("open", b"old")])
        self.assertFalse(_buffers)


if __name__ == "__main__":
    unittest.main()
