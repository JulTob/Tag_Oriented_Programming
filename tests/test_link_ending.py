"""Links acquired by teardown code obey the Agent's ending boundary."""

import gc
import unittest
import weakref

from TopKit import (Imprint, Link, Pre, Public, Record, Rip, Tag,
                    TagCompositionError, TagImprintError, TagPreconditionError)
from TopKit.lifecycle import _teardown_all
from TopKit.links import _record_of


class Host:
    pass


class LinkEndingTests(unittest.TestCase):
    def test_failed_contact_finalizer_rip_keeps_retry_seats_then_releases_them(self):
        calls = []

        class Social(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Forget(owner, contact):
                    calls.append("run")
                    if len(calls) == 1:
                        raise ValueError("retry this Pair teardown")

        owner, contact = Host(), Host()
        Social(owner)
        held = owner.Knows
        held(contact)
        pair = _record_of(held).family.Pair_Of(contact)
        owner_ref = weakref.ref(owner)
        contact_ref = weakref.ref(contact)
        pair_ref = weakref.ref(pair)

        del pair, contact
        gc.collect()

        self.assertEqual(calls, ["run"])
        self.assertEqual(list(held[:]), [])
        self.assertIsNotNone(contact_ref())
        self.assertIsNotNone(pair_ref())
        self.assertEqual(list(held[...]), [contact_ref()])

        del owner
        gc.collect()
        self.assertIsNotNone(owner_ref())  # the saved Pair keeps its Agent seat

        arrested = list(held[...])
        del held[arrested[0]]
        self.assertEqual(calls, ["run", "run"])
        self.assertEqual(list(held[...]), [])

        del arrested
        gc.collect()
        self.assertIsNone(owner_ref())
        self.assertIsNone(contact_ref())
        self.assertIsNone(pair_ref())

    def test_an_interrupt_stops_later_teardowns_of_the_same_ordinary_tag(self):
        for failure in (KeyboardInterrupt, SystemExit, GeneratorExit):
            with self.subTest(failure=failure.__name__):
                seen = []
                interrupted = failure("stop this teardown")

                class Ordinary(Tag):
                    @Rip
                    def First(agent):
                        seen.append("first")
                        raise interrupted

                    @Rip
                    def Second(agent):
                        seen.append("second")

                agent = Host()
                Ordinary(agent)

                with self.assertRaises(failure) as caught:
                    _teardown_all(agent)

                self.assertIs(caught.exception, interrupted)
                self.assertEqual(seen, ["first"])

    def test_an_ordinary_interrupt_still_finishes_exits_from_links(self):
        seen = []
        interrupted = KeyboardInterrupt("stop ordinary teardowns")

        class Social(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Leave(agent, contact):
                    seen.append("link")

        class Ordinary(Tag):
            @Rip
            def First(agent):
                seen.append("first")
                raise interrupted

            @Rip
            def Second(agent):
                seen.append("second")

        owner, contact = Host(), Host()
        Social(owner)
        owner.Knows(contact)
        Ordinary(contact)

        with self.assertRaises(KeyboardInterrupt) as caught:
            _teardown_all(contact)

        self.assertIs(caught.exception, interrupted)
        self.assertEqual(seen, ["first", "link"])
        self.assertIsNone(_record_of(owner.Knows).family.Pair_Of(contact))

    def _refused_shape_after_nested_extension(self, cleanup, extension_cleanup=None):
        class Social(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Leave_Base(agent, contact):
                    cleanup.append("base")

            @Link
            class Trusts(Knows):
                @Pre
                def Ready(agent, contact):
                    if not contact.promoted:
                        contact.promoted = True
                        Rich(agent)
                        return False
                    return True

                @Rip
                def Leave_Shape(agent, contact):
                    cleanup.append("shape")

        class Rich(Social):
            @Link
            class Trusts(Social.Trusts):
                @Record
                def level(agent, contact):
                    return 1

                @Rip
                def Leave_Extension(agent, contact):
                    cleanup.append("extension")
                    if extension_cleanup is not None:
                        extension_cleanup(agent, contact)

        agent, contact = Host(), Host()
        contact.promoted = False
        Social(agent)
        with self.assertRaises(TagPreconditionError):
            agent.Trusts(contact)
        self.assertIn(agent, Rich)
        self.assertIn(contact, agent.Knows)
        self.assertNotIn(contact, agent.Trusts)
        return agent, contact

    def test_last_membership_rips_retained_completed_pair_tags_in_reverse_order(self):
        cleanup = []
        agent, contact = self._refused_shape_after_nested_extension(cleanup)

        del agent.Knows[contact]

        self.assertEqual(cleanup, ["extension", "shape", "base"])
        self.assertIsNone(_record_of(agent.Knows).family.Pair_Of(contact))

    def test_last_membership_cleanup_keeps_a_pair_relinked_by_a_retained_tag(self):
        cleanup = []
        agent, contact = self._refused_shape_after_nested_extension(
                cleanup, lambda owner, target: owner.Knows(target))
        pair = _record_of(agent.Knows).family.Pair_Of(contact)

        del agent.Knows[contact]

        self.assertEqual(cleanup, ["extension"])
        self.assertIn(contact, agent.Knows)
        self.assertIs(agent.Knows[contact], pair)
        del agent.Knows[contact]
        self.assertEqual(cleanup, ["extension", "shape", "base"])

    def test_retained_tag_teardown_failure_stops_before_its_completed_bases(self):
        blocked = True

        def fail(agent, contact):
            nonlocal blocked
            if blocked:
                blocked = False
                raise ValueError("extension teardown failed")

        cleanup = []
        agent, contact = self._refused_shape_after_nested_extension(cleanup, fail)

        with self.assertRaises(TagCompositionError):
            del agent.Knows[contact]

        self.assertEqual(cleanup, ["extension"])
        self.assertIn(contact, agent.Knows[...])
        del agent.Knows[contact]
        self.assertEqual(cleanup, ["extension", "extension", "shape", "base"])
        self.assertNotIn(contact, agent.Knows[...])

    def test_failed_shape_training_keeps_a_completed_base_extensions_teardown(self):
        cleanup = []

        class Social(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Leave_Base(agent, contact):
                    cleanup.append("base")

            @Link
            class Trusts(Knows):
                @Imprint
                def Train(agent, contact):
                    Spy(agent)
                    raise ValueError("Shape training fails after the extension completed")

        class Spy(Social):
            @Link
            class Knows(Social.Knows):
                @Rip
                def Leave_Extension(agent, contact):
                    cleanup.append("extension")

        agent, contact = Host(), Host()
        Social(agent)
        agent.Knows(contact)
        with self.assertRaises(TagImprintError):
            agent.Trusts(contact)
        self.assertIn(agent, Spy)
        self.assertIn(contact, agent.Knows)
        self.assertNotIn(contact, agent.Trusts)

        del agent.Knows[contact]

        self.assertEqual(cleanup, ["extension", "base"])

    def test_unadmitted_shape_does_not_block_ripping_a_completed_base_link(self):
        cleanup = []

        class Greeting(Tag):
            @Record
            def Greet(agent):
                return "the Contact's Record"

        class Social(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Leave_Base(agent, contact):
                    cleanup.append("base")

            @Link
            class Trusts(Knows):
                @Public
                def Greet(agent, contact):
                    return "the Shape's published Action"

                @Rip
                def Leave_Shape(agent, contact):
                    cleanup.append("shape")

        agent, contact = Host(), Host()
        Social(agent)
        Greeting(contact)
        with self.assertRaises(TagCompositionError):
            agent.Trusts(contact)   # Pair training succeeds, but the public Action cannot overlay a Record.
        self.assertIn(contact, agent.Knows)
        self.assertNotIn(contact, agent.Trusts)

        del agent.Knows[contact]

        self.assertEqual(cleanup, ["base"])
        self.assertIsNone(_record_of(agent.Knows).family.Pair_Of(contact))

    def test_a_link_acquired_during_exit_stays_ended_while_its_agent_is_live(self):
        held = []

        class Extra(Tag):
            @Link
            class Late(Tag):
                pass

        class Social(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Cleanup(agent, contact):
                    Extra(agent)
                    held.append(agent.Late)

        agent, contact = Host(), Host()
        Social(agent)
        agent.Knows(contact)

        _teardown_all(agent)   # At_Exit also ends Links while other names hold the Agent.

        self.assertEqual(len(held[0][:]), 0)
        with self.assertRaises(TagCompositionError):
            held[0](contact)

    def test_a_link_acquired_while_links_end_cannot_link_a_contact(self):
        cleanup = []
        held = []
        refused = []

        class Extra(Tag):
            @Link
            class Late(Tag):
                @Rip
                def Cleanup(agent, contact):
                    cleanup.append("late")

        class Social(Tag):
            @Link
            class Knows(Tag):
                @Rip
                def Cleanup(agent, contact):
                    cleanup.append("existing")
                    Extra(agent)
                    held.append(agent.Late)
                    try:
                        agent.Late(contact)
                    except TagCompositionError:
                        refused.append(True)

        agent, contact = Host(), Host()
        Social(agent)
        agent.Knows(contact)
        reference = weakref.ref(agent)

        del agent
        gc.collect()

        self.assertIsNone(reference())
        self.assertEqual(refused, [True])
        self.assertEqual(cleanup, ["existing"])
        self.assertEqual(len(held[0][:]), 0)
        self.assertNotIn(contact, held[0])
        with self.assertRaises(TagCompositionError):
            held[0](contact)

    def test_a_link_acquired_by_an_agents_own_teardown_is_ended_next(self):
        cleanup = []
        held = []
        contact = Host()

        class Extra(Tag):
            @Link
            class Late(Tag):
                @Rip
                def Cleanup(agent, contact):
                    cleanup.append("late")

        class Social(Tag):
            @Link
            class Knows(Tag):
                pass

            @Rip
            def Prepare(agent):
                Extra(agent)
                held.append(agent.Late)
                agent.Late(contact)

        agent = Host()
        Social(agent)
        reference = weakref.ref(agent)

        del agent
        gc.collect()

        self.assertIsNone(reference())
        self.assertEqual(cleanup, ["late"])
        self.assertEqual(len(held[0][:]), 0)
        self.assertNotIn(contact, held[0])


if __name__ == "__main__":
    unittest.main()
