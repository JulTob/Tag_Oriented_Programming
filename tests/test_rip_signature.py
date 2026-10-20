"""A scheduled Pin Rip uses the signature of its selected declaration."""

from inspect import Parameter, Signature, signature
import unittest

from TopKit import Pin, Record, Rip, Tag, TagCompositionError, Underlay
from TopKit.lifecycle import _teardown_all


class Agent:
    pass


def _signature(*names):
    return Signature([
        Parameter(name, Parameter.POSITIONAL_OR_KEYWORD) for name in names
    ])


class RipSignatureTests(unittest.TestCase):
    def test_one_seat_wrapper_runs_directly_and_on_every_rip_path(self):
        for callable_object in (False, True):
            for pinned in (False, True):
                for fails in (False, True):
                    with self.subTest(callable_object=callable_object,
                                      pinned=pinned, fails=fails):
                        events = []
                        original = RuntimeError("body failure")

                        def Metadata(agent, originals):
                            raise AssertionError("metadata ancestor ran")

                        def Body(agent):
                            events.append("called")
                            if fails:
                                raise original

                        if callable_object:
                            class CallableRip:
                                __signature__ = _signature("agent")
                                __wrapped__ = staticmethod(Metadata)

                                def __call__(self, agent):
                                    Body(agent)

                            member = CallableRip()
                        else:
                            member = Body
                            actual = signature(member)
                            member.__wrapped__ = Metadata
                            member.__signature__ = actual

                        self.assertEqual(signature(member), _signature("agent"))
                        closing = type("Closing", (Tag,), {"Finish": Rip(member)})
                        if pinned:
                            closing = Pin(closing)
                        target = type("Target", (Tag,), {}) if pinned else Agent()
                        closing(target)

                        if fails:
                            with self.assertRaises(RuntimeError) as direct:
                                target.Finish()
                            self.assertIs(direct.exception, original)
                            with self.assertRaises(TagCompositionError) as rip:
                                del closing[target]
                            self.assertIs(rip.exception.__cause__, original)
                        else:
                            target.Finish()
                            del closing[target]

                        self.assertEqual(events, ["called", "called"])
                        self.assertNotIn(target, closing[:])
                        _teardown_all(target)
                        self.assertEqual(events, ["called", "called"])
                        if fails:
                            self.assertIn(target, closing[...])
                            fails = False
                            del closing[target]
                            self.assertEqual(events, ["called"] * 3)
                            self.assertNotIn(target, Tag[...])

    def test_explicit_two_seat_signature_receives_originals(self):
        events = []

        def Metadata(tag):
            raise AssertionError("metadata ancestor ran")

        def Unpatch(tag, originals):
            events.append("unpatch")
            tag.colour = originals.colour

        Unpatch.__wrapped__ = Metadata
        Unpatch.__signature__ = _signature("tag", "originals")

        class Target(Tag):
            colour = "original"

        @Pin
        class Patch(Tag):
            @Record
            def colour(tag, stored):
                return stored + "-patched"

            Finish = Rip(Unpatch)

        Patch(Target)
        self.assertEqual(Target.colour, "original-patched")
        del Patch[Target]
        self.assertEqual(Target.colour, "original")
        self.assertEqual(events, ["unpatch"])

    def test_composed_underlay_distinguishes_prior_from_originals(self):
        for with_originals in (False, True):
            with self.subTest(with_originals=with_originals):
                events = []

                class Target(Tag):
                    colour = "original"

                @Pin
                class Base(Tag):
                    def Finish(tag):
                        events.append("base")

                if with_originals:
                    def Added(tag, prior, originals):
                        prior()
                        tag.colour = originals.colour
                        events.append("added")
                else:
                    def Added(tag, prior):
                        prior()
                        events.append("added")

                class Shape(Base):
                    @Record
                    def colour(tag, stored):
                        return stored + "-patched"

                    Finish = Rip(Underlay(Added))

                Shape(Target)
                del Shape[Target]
                self.assertEqual(events, ["base", "added"])
                self.assertEqual(Target.colour,
                                 "original" if with_originals else "original-patched")

    def test_originals_reach_only_the_selected_rip_in_a_nested_chain(self):
        events = []

        class Target(Tag):
            colour = "original"

        @Pin
        class Base(Tag):
            @Rip
            def Finish(tag):
                events.append("base")

        class Middle(Base):
            @Rip
            @Underlay
            def Finish(tag, prior):
                prior()
                events.append("middle")

        class Shape(Middle):
            @Record
            def colour(tag, stored):
                return stored + "-patched"

            @Rip
            @Underlay
            def Finish(tag, prior, originals):
                prior()
                tag.colour = originals.colour
                events.append("shape")

        Shape(Target)
        del Shape[Target]
        self.assertEqual(events, ["base", "middle", "shape"])
        self.assertEqual(Target.colour, "original")

    def test_saved_nested_pin_rip_retries_with_the_same_originals_seat(self):
        events = []
        fail_once = [True]

        class Target(Tag):
            colour = "original"

        @Pin
        class Base(Tag):
            @Rip
            def Finish(tag):
                events.append("base")

        class Middle(Base):
            @Rip
            @Underlay
            def Finish(tag, prior):
                prior()
                events.append("middle")

        class Shape(Middle):
            @Record
            def colour(tag, stored):
                return stored + "-patched"

            @Rip
            @Underlay
            def Finish(tag, prior, originals):
                prior()
                tag.colour = originals.colour
                events.append("shape")
                if fail_once[0]:
                    fail_once[0] = False
                    raise ValueError("retry me")

        Shape(Target)
        with self.assertRaises(TagCompositionError) as failed:
            del Shape[Target]
        self.assertIsInstance(failed.exception.__cause__, ValueError)
        self.assertIn(Target, Shape[...])

        del Shape[Target]
        self.assertEqual(events, ["base", "middle", "shape"] * 2)
        self.assertEqual(Target.colour, "original")
        self.assertNotIn(Target, Tag[...])

    def test_direct_action_arguments_still_reach_the_underlay(self):
        events = []

        class Target(Tag):
            pass

        @Pin
        class Base(Tag):
            @Rip
            def Finish(tag, *extras):
                events.append(("base", extras))

        class Shape(Base):
            @Rip
            @Underlay
            def Finish(tag, prior, extra):
                prior()
                events.append(("shape", extra))

        Shape(Target)
        Target.Finish("direct")
        self.assertEqual(events, [("base", ("direct",)), ("shape", "direct")])

        del Shape[Target]
        self.assertEqual(events[2][0], "base")
        self.assertEqual(events[2][1], ())
        self.assertEqual(events[3][0], "shape")
        self.assertEqual(events[3][1].__class__.__name__, "_Originals")

    def test_state_copy_keeps_the_selected_rip_declaration(self):
        events = []

        def Metadata(tag, originals):
            raise AssertionError("metadata ancestor ran")

        def Close(tag):
            events.append("close")

        Close.__wrapped__ = Metadata
        Close.__signature__ = _signature("tag")
        closing = Pin(type("Closing", (Tag,), {"Close": Rip(Close)}))
        target = type("Target", (Tag,), {})
        closing(target)
        from TopKit.state import _state_of
        state = _state_of(target)
        state.Restore(state.Copy())

        _teardown_all(target)
        _teardown_all(target)
        self.assertEqual(events, ["close"])

    def test_underlay_mark_on_slotted_callable_does_not_move_to_wrapper(self):
        events = []

        class ClosingAction:
            __slots__ = ("__topkit_underlay__", "__topkit_kind__",
                         "__topkit_rip__", "__weakref__")

            def __call__(self, tag, prior):
                prior()
                events.append("shape")

        @Pin
        class Base(Tag):
            def Finish(tag):
                events.append("base")

        class Shape(Base):
            Finish = Rip(Underlay(ClosingAction()))

        target = type("Target", (Tag,), {})
        Shape(target)
        del Shape[target]
        self.assertEqual(events, ["base", "shape"])
