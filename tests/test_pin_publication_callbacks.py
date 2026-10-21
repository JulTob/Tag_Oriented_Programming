"""Pin publication keeps program callbacks outside shared locks."""

import unittest
from threading import Event, Thread

from TopKit import Pin, Tag, TagCompositionError, TagDeclarationError, Tool
from TopKit.tags import MetaTag
from tests.test_tools import Character


class PinPublicationCallbackTests(unittest.TestCase):

    def test_nested_tag_and_host_classes_keep_their_own_namespaces(self):
        class Social(Tag):
            class Nested(Tag):
                pass

            class Host:
                pass

        self.assertIsInstance(Social.Nested, MetaTag)
        self.assertIsInstance(Social.Host, type)
        self.assertNotIn("__topkit_tool__", Social.Nested.__dict__)
        self.assertNotIn("__topkit_tool__", Social.Host.__dict__)
        target = Character("nested")
        Social(target)
        self.assertIn(target, Social)

    def test_tool_getter_waiting_for_a_pin_declaration_does_not_deadlock(self):
        class Kind(Tag):
            pass
        entered, release, peer_done = Event(), Event(), Event()
        failures, declared = [], []
        class Builder:
            armed = False
            def __call__(self, agent):
                return None
            def __getattribute__(self, name):
                if name == "__topkit_tool__" and object.__getattribute__(self, "armed"):
                    entered.set()
                    if not release.wait(2):
                        raise TimeoutError("peer Pin could not finish")
                return object.__getattribute__(self, name)
        builder = Tool(Kind | None)(Builder())
        builder.armed = True
        def declare_collector():
            try:
                declared.append(type("Collector", (Tag,), {"prize": builder}))
            except BaseException as error:
                failures.append(error)
        def declare_pin():
            try:
                declared.append(type(Pin)("PeerPin", (Pin,), {}))
            except BaseException as error:
                failures.append(error)
            finally:
                peer_done.set()
        first, second = Thread(target=declare_collector), Thread(target=declare_pin)
        first.start()
        try:
            self.assertTrue(entered.wait(2))
            second.start()
            self.assertTrue(peer_done.wait(1), "Pin declaration blocked behind user getter")
        finally:
            release.set()
            first.join(2)
            if second.ident is not None:
                second.join(2)
        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(failures, [])
        self.assertEqual(len(declared), 2)

    def test_one_tool_kind_snapshot_guards_an_alternating_getter(self):
        class Kind(Tag):
            pass
        class Builder:
            reads = 0
            def __call__(self, agent):
                return object()
            def __getattribute__(self, name):
                if name == "__topkit_tool__":
                    reads = object.__getattribute__(self, "reads") + 1
                    object.__setattr__(self, "reads", reads)
                    if reads == 2:
                        return None
                return object.__getattribute__(self, name)
        builder = Tool(Kind | None)(Builder())
        builder.reads = 0
        class Collector(Tag):
            prize = builder
        # A disappearing observed mark must not remove the physical Tool rule.
        with self.assertRaises(TagCompositionError):
            Collector(Character())
        self.assertIs(Collector.__dict__["prize"], builder)

    def test_physical_tool_mark_survives_a_getter_hiding_its_first_read(self):
        class Kind(Tag):
            pass
        class Builder:
            reads = 0
            def __call__(self, agent):
                return object()
            def __getattribute__(self, name):
                if name == "__topkit_tool__":
                    reads = object.__getattribute__(self, "reads") + 1
                    object.__setattr__(self, "reads", reads)
                    if reads == 1:
                        return None
                return object.__getattribute__(self, name)
        builder = Tool(Kind | None)(Builder())
        builder.reads = 0
        class Collector(Tag):
            prize = builder
        self.assertEqual(builder.reads, 1)
        with self.assertRaises(TagCompositionError):
            Collector(Character())
        self.assertIs(Collector.__dict__["prize"], builder)

    def test_descriptor_tool_mark_still_guards_gaining_after_getter_hides_it(self):
        class Kind(Tag):
            pass

        class Builder:
            hidden = False
            value = None

            def __call__(self, agent):
                return self.value

            @property
            def __topkit_tool__(self):
                return None if self.hidden else self._kind

            @__topkit_tool__.setter
            def __topkit_tool__(self, kind):
                self._kind = kind

        builder = Tool(Kind)(Builder())

        class Owner(Tag):
            prize = builder

        builder.hidden = True
        builder.value = object()
        with self.assertRaises(TagCompositionError):
            Owner(Character())

    def test_dynamic_only_tool_metadata_still_guards_gaining(self):
        class Kind(Tag):
            pass

        class Builder:
            dynamic_kind = None

            def __call__(self, agent):
                return object()

            def __getattribute__(self, name):
                if name == "__topkit_tool__":
                    return object.__getattribute__(self, "dynamic_kind")
                return object.__getattribute__(self, name)

        builder = Tool(Kind)(Builder())
        builder.dynamic_kind = builder.__dict__.pop("__topkit_tool__")

        class Owner(Tag):
            prize = builder

        with self.assertRaises(TagCompositionError):
            Owner(Character())

    def test_slotted_physical_tool_mark_still_guards_gaining(self):
        class Kind(Tag):
            pass

        class Builder:
            __slots__ = ("hidden", "__topkit_kind__", "__topkit_tool__")

            def __init__(self):
                self.hidden = False

            def __call__(self, agent):
                return object()

            def __getattribute__(self, name):
                if name == "__topkit_tool__" and object.__getattribute__(self, "hidden"):
                    return None
                return object.__getattribute__(self, name)

        builder = Tool(Kind)(Builder())

        class Owner(Tag):
            prize = builder

        builder.hidden = True
        with self.assertRaises(TagCompositionError):
            Owner(Character())


    def test_malformed_real_kind_cannot_iterate_terms_under_pin_lock(self):
        from TopKit.tools import _Kind

        class Kind(Tag):
            pass

        class PoisonTerms:
            def __iter__(self):
                raise AssertionError("kind terms were iterated")

        @Tool(Kind)
        def prize(agent):
            return None

        prize.__topkit_tool__ = _Kind(PoisonTerms(), False)
        with self.assertRaisesRegex(TagDeclarationError, "invalid kind metadata"):
            class Collector(Tag):
                held = prize

    def test_late_tool_refuses_hostile_physical_namespace_keys(self):
        import TopKit.declarations as declarations

        class Kind(Tag):
            pass

        class Peer(Tag):
            pass

        peer_done = Event()
        under_lock = Event()
        failures = []
        peers = []

        def mark_peer():
            try:
                type(Pin)("PeerPin", (Pin,), {})
            except BaseException as error:
                failures.append(error)
            finally:
                peer_done.set()

        class BlockingName(str):
            armed = False

            def probe(self):
                if (not self.armed or not declarations._pin_mark_lock._is_owned()
                        or under_lock.is_set()):
                    return
                under_lock.set()
                peer = Thread(target=mark_peer)
                peers.append(peer)
                peer.start()
                if not peer_done.wait(0.5):
                    failures.append(AssertionError("peer Pin blocked by class key"))

            def __hash__(self):
                self.probe()
                return str.__hash__(self)

            def __eq__(self, other):
                self.probe()
                return str.__eq__(self, other)

        tool_key = BlockingName("prize")
        Collector = MetaTag(
                "Collector", (Tag,), {"__module__": __name__, tool_key: object()},
                )
        tool_key.armed = True

        @Tool(Kind)
        def prize(agent):
            return None

        with self.assertRaisesRegex(TagDeclarationError, "custom key methods"):
            Collector.prize = prize

        for peer in peers:
            peer.join(2)
        self.assertFalse(under_lock.is_set())
        self.assertEqual(failures, [])
        self.assertFalse(any(
                type(name) is str and name == "prize"
                for name in Collector.__dict__
                ))

    def test_late_tool_checks_old_binding_outside_pin_lock(self):
        class Kind(Tag):
            pass

        entered = Event()
        release = Event()
        peer_done = Event()
        outcomes = []

        class Old:
            armed = False

            def __call__(self, agent):
                return None

            def __getattribute__(self, name):
                if name == "__topkit_constant__" and object.__getattribute__(self, "armed"):
                    entered.set()
                    while not peer_done.is_set() and not release.wait(0.01):
                        pass
                return object.__getattribute__(self, name)

        old = Old()

        class Collector(Tag):
            prize = old

        old.armed = True

        @Tool(Kind)
        def prize(agent):
            return None

        def assign():
            try:
                Collector.prize = prize
            except TagDeclarationError:
                outcomes.append("refused")
            except BaseException as error:
                outcomes.append(error)
            else:
                outcomes.append("accepted")

        def mark_kind():
            try:
                type(Pin)("PeerPin", (Pin,), {})
            except BaseException as error:
                outcomes.append(error)
            finally:
                peer_done.set()

        first = Thread(target=assign)
        second = Thread(target=mark_kind)
        first.start()
        try:
            self.assertTrue(entered.wait(2))
            second.start()
            self.assertTrue(peer_done.wait(1), "Pin blocked behind old binding getter")
        finally:
            release.set()
            first.join(2)
            if second.ident is not None:
                second.join(2)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(outcomes, ["accepted"])
        self.assertIs(Collector.__dict__["prize"], prize)

    def test_late_tool_on_pin_does_not_read_callable_mark_under_lock(self):
        class Rare(Pin):
            pass

        class Kind(Tag):
            pass

        class Builder:
            armed = False

            def __call__(self, agent):
                return None

            def __getattribute__(self, name):
                if name == "__topkit_tool__" and object.__getattribute__(self, "armed"):
                    raise AssertionError("late Tool mark was read dynamically")
                return object.__getattribute__(self, name)

        builder = Tool(Kind)(Builder())
        builder.armed = True
        with self.assertRaises(TagDeclarationError):
            Rare.prize = builder
        self.assertNotIn("prize", Rare.__dict__)

    def test_replaced_binding_finalizer_runs_after_pin_lock(self):
        class Kind(Tag):
            pass

        class Peer(Tag):
            pass

        finalized = Event()
        peer_done = Event()
        failures = []

        def mark_peer():
            try:
                type(Pin)("PeerPin", (Pin,), {})
            except BaseException as error:
                failures.append(error)
            finally:
                peer_done.set()

        class Old:
            def __del__(self):
                finalized.set()
                peer = Thread(target=mark_peer)
                peer.start()
                if not peer_done.wait(1):
                    failures.append(AssertionError("Pin blocked by old binding finalizer"))
                peer.join(2)

        class Collector(Tag):
            prize = Old()

        @Tool(Kind)
        def prize(agent):
            return None

        Collector.prize = prize
        self.assertTrue(finalized.is_set())
        self.assertTrue(peer_done.is_set())
        self.assertEqual(failures, [])

    def test_a_metaclass_mark_descriptor_cannot_reclassify_a_declared_pin(self):
        setters = []
        class Blocking:
            def __get__(self, owner, klass=None):
                raise AssertionError("native Pin category must not read a mark descriptor")
            def __set__(self, owner, value):
                setters.append(value)
                raise AssertionError("native Pin category must not write a mark descriptor")
        class Meta(type(Pin)):
            __topkit_pin__ = Blocking()
        class Candidate(Pin, metaclass=Meta):
            pass
        class Target(Tag):
            pass
        self.assertIs(Candidate(Target), Target)
        self.assertIn(Target, Candidate[:])
        self.assertEqual(setters, [])

