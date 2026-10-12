"""Tag memos stay local without invalidating other Agents' namespace scans."""

import gc
import threading
import unittest
import weakref

from TopKit import Form, Pin, Tag
from TopKit.declarations import _declaration_key, _declarations_of
from TopKit.geometry import _form_key
from TopKit.state import _Class_Namespace


class Host:
    pass


class PausingAction:
    """A supported callable whose metadata yields at a chosen scan step."""

    def __init__(self):
        self.entered = threading.Event()
        self.resume = threading.Event()
        self.worker_id = None
        self.armed = False

    @property
    def __func__(self):
        if self.armed and threading.get_ident() == self.worker_id:
            self.armed = False
            self.entered.set()
            if not self.resume.wait(5):
                raise TimeoutError("peer did not complete memo publication")
        return self

    def __call__(self, agent):
        return "ready"


class TagMemoConcurrencyTests(unittest.TestCase):
    def interleave(self, action, first, peer):
        results = []
        failures = []

        def run():
            action.worker_id = threading.get_ident()
            try:
                results.append(first())
            except BaseException as failure:
                failures.append(failure)

        action.armed = True
        worker = threading.Thread(target=run)
        worker.start()
        try:
            self.assertTrue(action.entered.wait(5), "scan did not reach metadata")
            peer_result = peer()
        finally:
            action.resume.set()
            worker.join(5)
        self.assertFalse(worker.is_alive(), "scan did not finish")
        self.assertEqual(failures, [])
        return results[0], peer_result

    def candidate(self):
        action = PausingAction()
        candidate = type("Candidate", (Tag,), {"Work": action})
        return candidate, action

    def test_different_agents_can_cold_scan_the_same_tag(self):
        candidate, action = self.candidate()
        agents = [Host(), Host()]
        self.interleave(action, lambda: candidate(agents[0]),
                        lambda: candidate(agents[1]))
        for agent in agents:
            self.assertIn(agent, candidate)
            self.assertEqual(agent.Work(), "ready")

    def test_first_pin_validation_can_overlap_first_form_publication(self):
        candidate, action = self.candidate()
        pinned, form = self.interleave(action, lambda: Pin(candidate),
                                       lambda: Form(candidate))
        self.assertIs(pinned, candidate)
        self.assertEqual(form, (candidate,))

    def test_base_constant_validation_can_overlap_memo_publication(self):
        candidate, action = self.candidate()

        def publish():
            agent = Host()
            candidate(agent)
            return agent

        shape, agent = self.interleave(
                action,
                lambda: type("Shape", (candidate,), {}),
                publish,
                )
        self.assertEqual(Form(shape), (candidate, shape))
        self.assertIn(agent, candidate)

    def test_concurrent_scans_return_the_same_published_memo(self):
        candidate, action = self.candidate()
        first, second = self.interleave(
                action,
                lambda: _declarations_of(candidate),
                lambda: _declarations_of(candidate),
                )
        self.assertIs(first, second)
        self.assertIs(first, _declarations_of(candidate))

    def test_tag_agent_namespace_iteration_is_stable_during_memo_publication(self):
        candidate, _ = self.candidate()
        namespace = _Class_Namespace(candidate)
        before = dict(vars(candidate))
        items = iter(namespace.items())
        keys = iter(namespace.keys())
        names = iter(namespace)
        _declarations_of(candidate)
        Form(candidate)
        self.assertEqual(dict(items), before)
        self.assertEqual(set(keys), set(before))
        self.assertEqual(set(names), set(before))

    def test_a_foreign_declaration_memo_is_not_accepted_or_deleted(self):
        original, _ = self.candidate()
        _declarations_of(original)
        foreign = vars(original)[_declaration_key(original)]
        candidate, _ = self.candidate()
        name = _declaration_key(candidate)
        setattr(candidate, name, foreign)
        first = _declarations_of(candidate)
        self.assertIsNot(first, _declarations_of(candidate))
        self.assertIs(vars(candidate)[name], foreign)
        from TopKit.declarations import _invalidate_declarations
        _invalidate_declarations(candidate)
        self.assertIs(vars(candidate)[name], foreign)

    def test_a_form_memo_cannot_be_used_as_the_same_tags_declaration_memo(self):
        candidate, _ = self.candidate()
        Form(candidate)
        foreign = vars(candidate)[_form_key(candidate)]
        name = _declaration_key(candidate)
        setattr(candidate, name, foreign)
        first = _declarations_of(candidate)
        self.assertIsNot(first, _declarations_of(candidate))
        self.assertIs(vars(candidate)[name], foreign)

    def test_real_tagging_releases_both_memos_with_a_held_field(self):
        def create():
            def Owner(agent):
                return shape

            class Base(Tag):
                Work = Owner

            class Shape(Base):
                pass

            shape = Shape
            agent = Host()
            Shape(agent)
            self.assertIs(agent.Work(), Shape)
            self.assertEqual(Form(Shape), (Base, Shape))
            return Shape[:], (weakref.ref(Base), weakref.ref(Shape), weakref.ref(agent))

        population, references = create()
        gc.collect()
        gc.collect()
        self.assertTrue(all(reference() is None for reference in references))
        self.assertEqual(len(population), 0)


if __name__ == "__main__":
    unittest.main()
