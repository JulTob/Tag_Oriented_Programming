"""Pin marks and Tool declarations publish atomically across threads."""

import unittest
from threading import Event, Thread
from unittest.mock import patch

from TopKit import Pin, Tag, TagDeclarationError, Tool


class PinPublicationRaceTests(unittest.TestCase):

    def test_shape_creation_rechecks_pin_bases_after_a_concurrent_mark(self):
        import TopKit.declarations as declarations
        import TopKit.tags as tags

        class Base(Tag):
            pass

        class Ordinary(Tag):
            pass

        mark_checked = Event()
        shape_checked = Event()
        release_mark = Event()
        outcomes = []
        original_refuse = declarations._refuse_late_pin
        original_check = tags._check_pin_bases

        def pause_mark(tag):
            original_refuse(tag)
            if tag is Base:
                mark_checked.set()
                if not release_mark.wait(2):
                    raise TimeoutError("Shape did not reach its Base check")

        def note_shape(tag, **kwargs):
            result = original_check(tag, **kwargs)
            if tag.__name__ == "Mixed" and not kwargs.get("physical"):
                shape_checked.set()
            return result

        def mark():
            try:
                Pin(Base)
            except BaseException as error:
                outcomes.append(error)
            else:
                outcomes.append("marked")

        def make_shape():
            try:
                class Mixed(Base, Ordinary):
                    pass
            except TagDeclarationError as error:
                outcomes.append(str(error))
            except BaseException as error:
                outcomes.append(error)
            else:
                outcomes.append(Mixed)

        with (patch.object(declarations, "_refuse_late_pin", pause_mark),
              patch.object(tags, "_check_pin_bases", note_shape)):
            marker = Thread(target=mark)
            builder = Thread(target=make_shape)
            marker.start()
            try:
                self.assertTrue(mark_checked.wait(2))
                builder.start()
                self.assertTrue(shape_checked.wait(2))
            finally:
                release_mark.set()
                marker.join(2)
                if builder.ident is not None:
                    builder.join(2)

        self.assertFalse(marker.is_alive())
        self.assertFalse(builder.is_alive())
        self.assertEqual(outcomes[0], "marked")
        self.assertIn("mixes Pins and Tags", outcomes[1])

    def test_shape_tool_rechecks_base_after_a_concurrent_pin_mark(self):
        import TopKit.declarations as declarations
        import TopKit.tags as tags

        class Base(Tag):
            pass

        class Kind(Tag):
            pass

        @Tool(Kind)
        def prize(agent):
            return None

        mark_checked = Event()
        shape_checked = Event()
        release_mark = Event()
        outcomes = []
        original_refuse = declarations._refuse_late_pin
        original_check = tags._check_pin_bases

        def pause_mark(tag):
            original_refuse(tag)
            if tag is Base:
                mark_checked.set()
                if not release_mark.wait(2):
                    raise TimeoutError("Shape did not reach its Base check")

        def note_shape(tag, **kwargs):
            result = original_check(tag, **kwargs)
            if tag.__name__ == "Shape" and not kwargs.get("physical"):
                shape_checked.set()
            return result

        def mark():
            try:
                Pin(Base)
            except BaseException as error:
                outcomes.append(error)
            else:
                outcomes.append("marked")

        def make_shape():
            try:
                class Shape(Base):
                    held = prize
            except TagDeclarationError as error:
                outcomes.append(str(error))
            except BaseException as error:
                outcomes.append(error)
            else:
                outcomes.append(Shape)

        with (patch.object(declarations, "_refuse_late_pin", pause_mark),
              patch.object(tags, "_check_pin_bases", note_shape)):
            marker = Thread(target=mark)
            builder = Thread(target=make_shape)
            marker.start()
            try:
                self.assertTrue(mark_checked.wait(2))
                builder.start()
                self.assertTrue(shape_checked.wait(2))
            finally:
                release_mark.set()
                marker.join(2)
                if builder.ident is not None:
                    builder.join(2)

        self.assertFalse(marker.is_alive())
        self.assertFalse(builder.is_alive())
        self.assertEqual(outcomes[0], "marked")
        self.assertIn("shared tool is a Report", outcomes[1])

    def test_pin_rechecks_when_a_tool_lands_during_unlocked_scan(self):
        import TopKit.declarations as declarations

        class Kind(Tag):
            pass

        class Candidate(Tag):
            pass

        entered = Event()
        resume = Event()
        outcome = []
        original = declarations._validate_pin

        def pause_once(tag, scanned):
            original(tag, scanned)
            if not entered.is_set():
                entered.set()
                if not resume.wait(2):
                    raise TimeoutError("Tool write could not finish")

        def mark():
            try:
                Pin(Candidate)
            except TagDeclarationError:
                outcome.append("refused")
            except BaseException as error:
                outcome.append(error)
            else:
                outcome.append("accepted")

        @Tool(Kind)
        def tool(agent):
            return None

        with patch.object(declarations, "_validate_pin", pause_once):
            worker = Thread(target=mark)
            worker.start()
            try:
                self.assertTrue(entered.wait(2))
                Candidate.tool = tool
            finally:
                resume.set()
                worker.join(2)

        self.assertFalse(worker.is_alive())
        self.assertEqual(outcome, ["refused"])
        self.assertNotIn("__topkit_pin__", Candidate.__dict__)

    def test_a_concurrent_pin_cannot_pass_while_a_tool_owner_is_registering(self):
        import TopKit.declarations as declarations

        class Prize(Tag):
            pass

        registering = Event()
        continue_registration = Event()
        marking = Event()
        declared = []
        outcome = []
        note = declarations._note_tag_kinds

        def pause(owner, tags):
            registering.set()
            if not continue_registration.wait(2):
                raise TimeoutError("Tool declaration did not resume")
            note(owner, tags)

        def declare():
            class Collector(Tag):
                @Tool(Prize)
                def prize(agent):
                    return None

            declared.append(Collector)

        def mark():
            marking.set()
            try:
                Pin(Prize)
            except TagDeclarationError:
                outcome.append("refused")
            else:
                outcome.append("accepted")

        with patch.object(declarations, "_note_tag_kinds", pause):
            owner_thread = Thread(target=declare)
            mark_thread = Thread(target=mark)
            owner_thread.start()
            try:
                self.assertTrue(registering.wait(2))
                mark_thread.start()
                self.assertTrue(marking.wait(2))
                mark_thread.join(0.02)
                self.assertEqual(outcome, [])          # mark waits for registration
            finally:
                continue_registration.set()
                owner_thread.join(2)
                if mark_thread.ident is not None:
                    mark_thread.join(2)

        self.assertEqual(outcome, ["refused"])
        self.assertTrue(declared)
        self.assertNotIn("__topkit_pin__", Prize.__dict__)

