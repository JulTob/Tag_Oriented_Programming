"""Link declaration memos remain collectible and safe to publish concurrently."""

import gc
import sys
import threading
import unittest
import weakref
from unittest.mock import patch

from TopKit import Form, Link, Tag
from TopKit import links


class Host:
    pass


class LinkMemoTests(unittest.TestCase):
    def test_pair_action_class_cell_does_not_keep_its_relation_alive(self):
        def create_link():
            class Social(Tag):
                @Link
                class Knows(Tag):
                    def Identify(agent, contact):
                        return __class__.__name__

            agent, contact = Host(), Host()
            Social(agent)
            agent.Knows(contact)
            self.assertEqual(agent.Knows[contact].Identify(), "Knows")
            return tuple(weakref.ref(value) for value in (
                Social, Social.Knows, agent, contact,
            ))

        references = create_link()
        gc.collect()
        self.assertEqual([reference() for reference in references], [None] * 4)

    def test_form_memo_can_publish_while_pair_declarations_are_inspected(self):
        entered, resume = threading.Event(), threading.Event()

        def Work(agent, contact):
            return "ready"

        class PausingAction:
            armed = False
            worker = None

            @property
            def __func__(action):
                if (action.armed
                        and threading.get_ident() == action.worker
                        and sys._getframe(2).f_code.co_name == "_pair_tag"):
                    action.armed = False
                    entered.set()
                    if not resume.wait(5):
                        raise TimeoutError("peer did not publish the Form memo")
                return Work

            def __call__(action, agent, contact):
                return "ready"

        action = PausingAction()

        class Social(Tag):
            @Link
            class Knows(Tag):
                Work = action

        owner, contact = Host(), Host()
        Social(owner)
        errors = []

        def link_contact():
            action.worker = threading.get_ident()
            action.armed = True
            try:
                owner.Knows(contact)
            except BaseException as error:
                errors.append(error)

        worker = threading.Thread(target=link_contact)
        worker.start()
        try:
            self.assertTrue(entered.wait(5), "Pair scan did not inspect metadata")
            Form(Social.Knows)
        finally:
            resume.set()
            worker.join(5)

        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        self.assertIn(contact, owner.Knows)
        self.assertEqual(owner.Knows[contact].Work(), "ready")

    def test_concurrent_pair_tag_builds_return_the_same_published_tag(self):
        @Link
        class Knows(Tag):
            def Identify(agent, contact):
                return "ready"

        barrier = threading.Barrier(2)
        original = links._two_seats
        results, errors = [], []

        def adapt(*args, **kwargs):
            barrier.wait(timeout=5)
            return original(*args, **kwargs)

        def build():
            try:
                results.append(links._pair_tag(Knows))
            except BaseException as error:
                errors.append(error)

        with patch.object(links, "_two_seats", adapt):
            workers = [threading.Thread(target=build) for _ in range(2)]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(10)

        self.assertTrue(all(not worker.is_alive() for worker in workers))
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        self.assertIs(results[0], results[1])
        self.assertIs(links._pair_tag(Knows), results[0])


if __name__ == "__main__":
    unittest.main()
