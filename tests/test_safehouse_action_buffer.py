"""Python buffer hooks selected through TOP Actions share Safehouse custody."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from TopKit import Action
from TopKit import Rip
from TopKit import Tag
from TopKit import TagArrestedAccessError
from TopKit import TagCompositionError
from TopKit.arrest import _safehouse
from TopKit.buffers import _buffers


class SafehouseActionBufferTests(unittest.TestCase):
    def setUp(self) -> None:
        for ledger in (_safehouse, _buffers):
            empty = patch.dict(ledger, clear=True)
            empty.start()
            self.addCleanup(empty.stop)

    def test_top_action_pair_releases_old_view_but_refuses_new_one(self) -> None:
        events = []

        class Host:
            resource = "open"

        class Buffer(Tag):
            @Action
            def __buffer__(agent, flags):
                events.append("acquire")
                return memoryview(bytearray(b"top"))

            @Action
            def __release_buffer__(agent, view):
                events.append(("release", agent.resource, bytes(view)))

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        host = Host()
        Buffer(host)
        Custody(host)
        view = memoryview(host)
        with self.assertRaises(TagCompositionError):
            del Custody[host]

        with self.assertRaises(TagArrestedAccessError):
            memoryview(host)
        view.release()
        self.assertEqual(events, ["acquire", ("release", "open", b"top")])
        self.assertFalse(_buffers)

    def test_host_acquire_and_top_action_release_share_ticket(self) -> None:
        events = []

        class Host:
            resource = "open"

            def __buffer__(self, flags):
                return memoryview(bytearray(b"host"))

            def __release_buffer__(self, view):
                events.append("old host release")

        class NewRelease(Tag):
            @Action
            def __release_buffer__(agent, view):
                events.append(("top release", agent.resource, bytes(view)))

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        host = Host()
        NewRelease(host)
        Custody(host)
        view = memoryview(host)
        with self.assertRaises(TagCompositionError):
            del Custody[host]
        view.release()
        self.assertEqual(events, [("top release", "open", b"host")])
        self.assertFalse(_buffers)

    def test_top_action_acquire_and_host_release_share_ticket(self) -> None:
        events = []

        class Host:
            resource = "open"

            def __release_buffer__(self, view):
                events.append(("host release", self.resource, bytes(view)))

        class NewBuffer(Tag):
            @Action
            def __buffer__(agent, flags):
                return memoryview(bytearray(b"top"))

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        host = Host()
        NewBuffer(host)
        Custody(host)
        view = memoryview(host)
        with self.assertRaises(TagCompositionError):
            del Custody[host]
        view.release()
        self.assertEqual(events, [("host release", "open", b"top")])
        self.assertFalse(_buffers)

    def test_top_buffer_catching_its_own_failed_rip_cannot_export(self) -> None:
        events = []

        class Host:
            resource = "open"

        class Buffer(Tag):
            @Action
            def __buffer__(agent, flags):
                view = memoryview(bytearray(b"secret"))
                try:
                    del Custody[agent]
                except TagCompositionError:
                    events.append("rip failed")
                return view

            @Action
            def __release_buffer__(agent, view):
                events.append(("release", agent.resource, bytes(view)))

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        host = Host()
        Buffer(host)
        Custody(host)
        with self.assertRaises(TagArrestedAccessError) as caught:
            memoryview(host)
        self.assertIsInstance(caught.exception.__cause__, RuntimeError)
        self.assertEqual(
                events, ["rip failed", ("release", "open", b"secret")],
                )
        self.assertFalse(_buffers)

    def test_callable_object_action_pair_keeps_release_ticket(self) -> None:
        events = []

        class BufferSource:
            def __call__(self, flags):
                events.append(("acquire", flags))
                return memoryview(bytearray(b"object"))

        class BufferRelease:
            def __call__(self, view):
                events.append(("release", bytes(view)))

        class Host:
            pass

        class Buffer(Tag):
            __buffer__ = Action(BufferSource())
            __release_buffer__ = Action(BufferRelease())

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        host = Host()
        Buffer(host)
        Custody(host)
        view = memoryview(host)
        with self.assertRaises(TagCompositionError):
            del Custody[host]
        with self.assertRaises(TagArrestedAccessError):
            memoryview(host)
        view.release()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0][0], "acquire")
        self.assertIsInstance(events[0][1], int)
        self.assertEqual(events[1], ("release", b"object"))
        self.assertFalse(_buffers)

    def test_callable_buffer_catching_failed_rip_cannot_export(self) -> None:
        events = []

        class Host:
            resource = "open"

        class BufferSource:
            def __call__(self, flags):
                view = memoryview(bytearray(b"secret"))
                try:
                    del Custody[host]
                except TagCompositionError:
                    events.append("rip failed")
                return view

        class Buffer(Tag):
            __buffer__ = Action(BufferSource())

            @Action
            def __release_buffer__(agent, view):
                events.append(("release", agent.resource, bytes(view)))

        class Custody(Tag):
            @Rip
            def Leave(agent):
                raise RuntimeError("unfinished")

        host = Host()
        Buffer(host)
        Custody(host)
        with self.assertRaises(TagArrestedAccessError) as caught:
            memoryview(host)
        self.assertIsInstance(caught.exception.__cause__, RuntimeError)
        self.assertEqual(
                events, ["rip failed", ("release", "open", b"secret")],
                )
        self.assertFalse(_buffers)

    def test_callable_buffer_uses_real_descriptor_lookup(self) -> None:
        class Spoof(type):
            def __getattribute__(cls, name):
                if name == "__get__":
                    return lambda member, agent, owner: (
                            lambda flags: memoryview(b"spoofed")
                            )
                return super().__getattribute__(name)

        class Source(metaclass=Spoof):
            def __call__(self, flags):
                return memoryview(b"actual")

        class Host:
            pass

        class Buffer(Tag):
            __buffer__ = Action(Source())

        host = Host()
        Buffer(host)
        self.assertEqual(bytes(memoryview(host)), b"actual")


if __name__ == "__main__":
    unittest.main()
