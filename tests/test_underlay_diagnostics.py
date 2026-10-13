"""Validation failures name Contributions, not Python callable metadata."""

from inspect import Parameter, Signature
import unittest
import warnings

from TopKit import (Action, Pin, Post, Pre, Record, Rip, Tag,
                    TagDeclarationError, TagResolutionError, Underlay)
from TopKit.declarations import _declarations_of


class Host:
    pass


class Unformattable(str):
    def __str__(self):
        raise AssertionError("custom string conversion ran")

    __repr__ = __str__

    def __format__(self, spec):
        return self.__str__()


def implementation(events, seats, mode="missing", record=False, extend=False):
    def result(agent, second=None):
        events.append("Work")
        if record:
            return (second or 0) + 1
        return second() if extend else True

    if mode == "function":
        if seats == 1:
            def Implementation(agent):
                return result(agent)
        elif record:
            def Implementation(agent, stored):
                return result(agent, stored)
        else:
            def Implementation(agent, prior):
                return result(agent, prior)
        return Implementation

    class One:
        def __getattribute__(self, name):
            if name in ("__name__", "__qualname__"):
                if mode == "hostile":
                    raise AssertionError("callable metadata was read")
                if mode == "missing-name" and name == "__qualname__":
                    return "NotTheDeclaredContribution"
            return object.__getattribute__(self, name)

        def __repr__(self):
            raise AssertionError("callable repr was read")

        def __call__(self, agent):
            return result(agent)

    class Two(One):
        def __call__(self, agent, prior):
            return result(agent, prior)

    class Stored(One):
        def __call__(self, agent, stored):
            return result(agent, stored)

    member = (Stored if record else One if seats == 1 else Two)()
    # Public signature metadata keeps inspect.signature from consulting the
    # deliberately hostile Python naming metadata before our diagnostic path.
    names = ("agent",) if seats == 1 else ("agent", "stored" if record else "prior")
    member.__signature__ = Signature([
            Parameter(name, Parameter.POSITIONAL_OR_KEYWORD) for name in names
            ])
    return member


class UnderlayDiagnosticTests(unittest.TestCase):
    def build(self, mark, seats, mode, pinned, prior=False, name="Work"):
        events = []
        member = implementation(events, seats, mode, record=mark is Record)
        role = type("Proposed", (Tag,), {
                name: mark(member if mark is Record else Underlay(member)),
                })
        role = Pin(role) if pinned else role
        target = type("Receiver", (Tag,), {}) if pinned else Host()
        previous = None
        if prior:
            def Previous(agent):
                return True
            previous = type("Previous", (Tag,), {name: mark(Previous)})
            previous = Pin(previous) if pinned else previous
            previous(target)
        return role, target, events, previous, member

    def test_validation_families_names_and_timing_match_function_controls(self):
        cases = [(mark, seats, False, TagResolutionError if seats == 2 else TagDeclarationError)
                 for mark in (Action, Pre, Post) for seats in (1, 2)]
        cases += [(Action, 1, True, TagDeclarationError),
                  (Post, 1, True, TagDeclarationError),
                  (Record, 2, False, TagDeclarationError)]
        for mark, seats, prior, failure in cases:
            for pinned in (False, True):
                modes = ("function", "missing", "hostile")
                if mark is Record:
                    modes += ("missing-name",)
                for mode in modes:
                    with self.subTest(mark=mark, seats=seats, prior=prior,
                                      pinned=pinned, mode=mode):
                        role, target, events, previous, _ = self.build(
                                mark, seats, mode, pinned, prior)
                        with warnings.catch_warnings():
                            warnings.simplefilter("error")
                            with self.assertRaises(failure) as caught:
                                role(target, **({"stored": 42} if mark is Record else {}))
                        self.assertIn("Work", str(caught.exception))
                        self.assertNotIn("Implementation", str(caught.exception))
                        self.assertIsNone(caught.exception.__cause__)
                        if mark is Record:
                            self.assertIn("def Work(agent, *, stored)", str(caught.exception))
                        self.assertEqual(events, [])
                        self.assertNotIn(target, role[:])
                        if previous is not None:
                            self.assertIn(target, previous[:])

    def test_declared_name_formatters_do_not_run_or_replace_names(self):
        name = Unformattable("Work")
        for mark in (Action, Pre, Post, Record):
            # New named-failure class construction is a separate boundary;
            # register the ordinary spelling before testing these diagnostics.
            def Known(agent):
                return True
            type("Known", (Tag,), {"Work": mark(Known)})
            for pinned in (False, True):
                for seats in ((2,) if mark is Record else (1, 2)):
                    with self.subTest(mark=mark, pinned=pinned, seats=seats):
                        role, target, _, _, _ = self.build(mark, seats, "missing", pinned, name=name)
                        declarations = _declarations_of(role)
                        contributions = getattr(declarations, {
                                Action: "actions", Pre: "preconditions",
                                Post: "postconditions", Record: "records",
                                }[mark])
                        self.assertIs(contributions[0][0], name)
                        failure = TagDeclarationError if mark is Record or seats == 1 else TagResolutionError
                        with self.assertRaises(failure) as caught:
                            role(target, **({"stored": 42} if mark is Record else {}))
                        self.assertIn("Work", str(caught.exception))

    def test_stored_seat_formatters_do_not_run(self):
        for pinned in (False, True):
            with self.subTest(pinned=pinned):
                role, target, events, _, member = self.build(Record, 2, "missing", pinned)
                member.__signature__ = Signature([
                        Parameter("agent", Parameter.POSITIONAL_OR_KEYWORD),
                        Parameter(Unformattable("stored"), Parameter.POSITIONAL_OR_KEYWORD),
                        ])
                with self.assertRaises(TagDeclarationError) as caught:
                    role(target, stored=42)
                self.assertIn("def Work(agent, *, stored)", str(caught.exception))
                self.assertEqual(events, [])
                self.assertNotIn(target, role[:])

    def test_successful_underlays_and_stored_records_are_unchanged(self):
        for mark in (Action, Pre, Post, Record):
            for pinned in (False, True):
                for mode in ("function", "missing"):
                    with self.subTest(mark=mark, pinned=pinned, mode=mode):
                        def Previous(agent):
                            return 41 if mark is Record else True
                        base = type("Base", (Tag,), {"Work": mark(Previous)})
                        base = Pin(base) if pinned else base
                        member = implementation([], 2, mode, record=mark is Record,
                                                extend=mark is not Record)
                        shape = type("Shape", (base,), {
                                "Work": mark(member if mark is Record else Underlay(member)),
                                })
                        target = type("Receiver", (Tag,), {}) if pinned else Host()
                        shape(target)
                        self.assertIn(target, base[:])
                        self.assertIn(target, shape[:])
                        value = target.Work() if mark is Action else target.Work
                        self.assertEqual(value, 42 if mark is Record else True)

    def test_pin_rip_underlay_keeps_its_receiver_and_order(self):
        events = []
        class Base(Tag):
            @Rip
            def Close(agent):
                events.append(("Base", agent))
        base = Pin(Base)
        class Added:
            def __call__(self, agent, prior):
                prior()
                events.append(("Shape", agent))
        shape = type("Shape", (base,), {"Close": Rip(Underlay(Added()))})
        target = type("Receiver", (Tag,), {})
        shape(target)
        del shape[target]
        self.assertEqual(events, [("Base", target), ("Shape", target)])
        self.assertIn(target, base[:])
        self.assertNotIn(target, shape[:])


if __name__ == "__main__":
    unittest.main()
