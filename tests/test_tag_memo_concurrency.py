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


class PausingToolInspectionAction(PausingAction):
    """Yield specifically while the Pin inspects Tool metadata."""

    @property
    def __func__(self):
        return self

    @property
    def __topkit_tool__(self):
        from TopKit.memo import _publication

        if _publication._is_owned():
            raise RuntimeError("Tool metadata was inspected under the memo lock")
        PausingAction.__func__.fget(self)
        return None


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

    def test_pin_tool_inspection_can_overlap_either_memo_publication(self):
        for kind in ("form", "declarations"):
            with self.subTest(kind=kind):
                action = PausingToolInspectionAction()
                candidate = type("Candidate", (Tag,), {"Work": action})
                if kind == "form":
                    publish = lambda: Form(candidate)
                else:
                    publish = lambda: _declarations_of(candidate)

                pinned, _ = self.interleave(
                    action, lambda: Pin(candidate), publish,
                )
                self.assertIs(pinned, candidate)

                class Receiver(Tag):
                    pass

                candidate(Receiver)
                self.assertIn(Receiver, candidate)
                self.assertEqual(Receiver.Work(), "ready")

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

    def test_memo_storage_does_not_evaluate_metaclass_namespace_getters(self):
        from TopKit.declarations import _invalidate_declarations
        from TopKit.memo import _publication

        getter_calls = []

        class Metadata(type(Tag)):
            @property
            def __dict__(tag):
                getter_calls.append("namespace")
                if _publication._is_owned():
                    raise RuntimeError("user dictionary getter ran under memo lock")
                return type.__dict__["__dict__"].__get__(tag)

            @property
            def __mro__(tag):
                getter_calls.append("mro")
                if _publication._is_owned():
                    raise RuntimeError("user MRO getter ran under memo lock")
                return type.__dict__["__mro__"].__get__(tag)

        class Base(Tag, metaclass=Metadata):
            def Work(agent):
                return "base"

        class Shape(Base):
            pass

        getter_calls.clear()
        self.assertEqual(Form(Shape), (Base, Shape))
        declarations = _declarations_of(Base)
        self.assertIs(_declarations_of(Base), declarations)
        _invalidate_declarations(Base)
        self.assertIsNot(_declarations_of(Base), declarations)
        self.assertIn("Work", _Class_Namespace(Base).copy())
        self.assertEqual(getter_calls, [])

    def test_a_metaclass_descriptor_collision_stays_uncached_without_evaluation(self):
        from TopKit.declarations import _invalidate_declarations

        class Metadata(type(Tag)):
            pass

        class Candidate(Tag, metaclass=Metadata):
            def Work(agent):
                return "ready"

        calls = []

        def forbidden(*args):
            calls.append(args)
            raise RuntimeError("memo evaluated the program's descriptor")

        descriptor = property(forbidden, forbidden, forbidden)
        declaration_name = _declaration_key(Candidate)
        form_name = _form_key(Candidate)
        type.__setattr__(Metadata, declaration_name, descriptor)
        type.__setattr__(Metadata, form_name, descriptor)
        first = _declarations_of(Candidate)
        self.assertIsNot(_declarations_of(Candidate), first)
        self.assertEqual(Form(Candidate), (Candidate,))
        _invalidate_declarations(Candidate)
        physical = type.__dict__["__dict__"].__get__(Candidate)
        self.assertNotIn(declaration_name, physical)
        self.assertNotIn(form_name, physical)
        self.assertEqual(calls, [])

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
