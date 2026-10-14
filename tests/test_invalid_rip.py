"""Declaration boundaries for the Rip protocol."""

from __future__ import annotations

from functools import cached_property, partial, partialmethod
import unittest

from TopKit import Action
from TopKit import Constant
from TopKit import Delete
from TopKit import Imprint
from TopKit import Operation
from TopKit import Post
from TopKit import Pre
from TopKit import Public
from TopKit import Record
from TopKit import Report
from TopKit import Rip
from TopKit import Secret
from TopKit import Tag
from TopKit import Underlay
from TopKit.errors import TagDeclarationError


class Host:
    pass


def _member():
    def Cleanup(agent):
        return True

    return Cleanup


def _with_rip_outside(mark):
    return Rip(mark(_member()))


def _with_rip_inside(mark):
    return mark(Rip(_member()))


class InvalidRipTests(unittest.TestCase):
    def assert_invalid(self, member, *, name: str = "Cleanup") -> None:
        with self.assertRaisesRegex(
                TagDeclarationError,
                r"@Rip.*@Rip marks an Action",
                ):
            type(
                    "Declared",
                    (Tag,),
                    {
                        name: member,
                        },
                    )

    def test_rip_is_rejected_on_every_other_contribution_kind(self) -> None:
        marks = (
                ("Record", Record),
                ("Imprint", Imprint),
                ("Pre", Pre),
                ("Post", Post),
                ("Pre outside Post", lambda function: Pre(Post(function))),
                ("Post outside Pre", lambda function: Post(Pre(function))),
                ("Delete", Delete),
                ("Report", Report),
                ("Operation", Operation),
                )

        for kind, mark in marks:
            for order, build in (
                    ("Rip outside", _with_rip_outside),
                    ("Rip inside", _with_rip_inside),
                    ):
                with self.subTest(kind=kind, order=order):
                    self.assert_invalid(build(mark))

    def test_rip_is_rejected_on_python_method_wrappers(self) -> None:
        for kind, mark in (
                ("classmethod", classmethod),
                ("staticmethod", staticmethod),
                ("cached_property", cached_property),
                ("partialmethod", partialmethod),
                ):
            for order, build in (
                    ("Rip outside", _with_rip_outside),
                    ("Rip inside", _with_rip_inside),
                    ):
                with self.subTest(kind=kind, order=order):
                    self.assert_invalid(build(mark))

    def test_rip_is_rejected_inside_nested_known_descriptors(self) -> None:
        for outer, inner in (
                (cached_property, partialmethod),
                (partialmethod, cached_property),
                (classmethod, cached_property),
                (property, partialmethod),
                ):
            with self.subTest(outer=outer, inner=inner):
                self.assert_invalid(outer(inner(Rip(_member()))))

    def test_functools_descriptors_are_validated_without_running_them(self) -> None:
        for wrapper in (cached_property, partialmethod):
            with self.subTest(wrapper=wrapper):
                events: list[str] = []

                class Unbound(wrapper):
                    def __get__(self, instance, owner=None):
                        events.append("descriptor")
                        raise AssertionError("validation bound the descriptor")

                def Cleanup(agent):
                    events.append("body")
                    raise AssertionError("validation ran the body")

                self.assert_invalid(Unbound(Rip(Cleanup)))
                self.assertEqual(events, [])

    def test_callable_descriptor_subclasses_still_cannot_be_rips(self) -> None:
        for wrapper in (property, cached_property, partialmethod):
            with self.subTest(wrapper=wrapper):
                class CallableDescriptor(wrapper):
                    def __call__(self, agent):
                        raise AssertionError("validation called the descriptor")

                self.assert_invalid(CallableDescriptor(Rip(_member())))

    def test_unmarked_functools_descriptors_remain_valid_declarations(self) -> None:
        for wrapper in (cached_property, partialmethod):
            with self.subTest(wrapper=wrapper):
                events: list[str] = []

                def Cleanup(agent):
                    events.append("body")

                member = wrapper(Cleanup)
                Declared = type("Declared", (Tag,), {"Cleanup": member})
                agent = Host()
                Declared(agent)
                del Declared[agent]

                self.assertIs(vars(Declared)["Cleanup"], member)
                self.assertFalse(hasattr(agent, "Cleanup"))
                self.assertEqual(events, [])

    def test_a_later_rip_mark_inside_a_descriptor_refuses_tagging(self) -> None:
        for wrapper in (cached_property, partialmethod):
            with self.subTest(wrapper=wrapper):
                member = _member()
                Declared = type("Declared", (Tag,), {"Cleanup": wrapper(member)})
                Rip(member)
                agent = Host()

                with self.assertRaisesRegex(TagDeclarationError, r"Declared\.Cleanup.*@Rip"):
                    Declared(agent)

                self.assertIs(type(agent), Host)
                self.assertEqual(vars(agent), {})
                self.assertNotIn(agent, Declared[:])

    def test_rip_is_rejected_outside_a_property_without_marking_its_accessor(self) -> None:
        log: list[str] = []

        def Cleanup(agent) -> None:
            log.append("clean")

        with self.assertRaisesRegex(
                TagDeclarationError,
                r"@Rip.*property.*@Rip marks an Action",
                ):
            Rip(property(Cleanup))

        Declared = type(
                "Declared",
                (Tag,),
                {
                    "Cleanup": Cleanup,
                    },
                )
        agent = Host()
        Declared(agent)
        del Declared[agent]

        self.assertEqual(log, [])

    def test_rip_is_rejected_inside_a_property(self) -> None:
        self.assert_invalid(property(Rip(_member())))

    def test_rip_is_rejected_on_an_accessorless_property(self) -> None:
        with self.assertRaisesRegex(
                TagDeclarationError,
                r"@Rip.*property.*@Rip marks an Action",
                ):
            Rip(property())

    def test_rip_is_rejected_on_a_private_name(self) -> None:
        self.assert_invalid(
                Rip(_member()),
                name="_Cleanup",
                )

    def test_constant_rips_are_refused_in_both_orders(self) -> None:
        for mark in (lambda function: function, Action, Secret, Public):
            for order, build in (
                    ("Rip outside", _with_rip_outside),
                    ("Rip inside", _with_rip_inside),
                    ):
                with self.subTest(mark=mark, order=order):
                    with self.assertRaisesRegex(
                            TagDeclarationError,
                            r"Declared\.Release.*@Rip.*@Constant",
                            ):
                        type(
                                "Declared",
                                (Tag,),
                                {"Release": mark(build(Constant))},
                                )

    def test_constant_rip_is_refused_when_the_second_mark_is_added_later(self) -> None:
        for first, second in ((Rip, Constant), (Constant, Rip)):
            with self.subTest(first=first, second=second):
                member = first(_member())
                Declared = type("Declared", (Tag,), {"Cleanup": member})
                second(member)
                agent = Host()

                with self.assertRaisesRegex(TagDeclarationError, r"@Rip.*@Constant"):
                    Declared(agent)

                self.assertIs(type(agent), Host)
                self.assertEqual(vars(agent), {})
                self.assertNotIn(agent, Declared[:])

    def test_rip_finalizer_is_refused_when_the_tag_is_declared(self) -> None:
        with self.assertRaisesRegex(TagDeclarationError, r"Declared\.__del__.*@Rip"):
            type("Declared", (Tag,), {"__del__": Rip(_member())})

    def test_bare_and_explicit_actions_remain_valid_rips(self) -> None:
        forms = (
                ("bare", lambda function: Rip(function)),
                ("callable partial", lambda function: Rip(partial(function))),
                ("Rip outside Action", lambda function: Rip(Action(function))),
                ("Rip inside Action", lambda function: Action(Rip(function))),
                ("Rip outside Secret", lambda function: Rip(Secret(function))),
                ("Rip inside Secret", lambda function: Secret(Rip(function))),
                ("Rip outside Public", lambda function: Rip(Public(function))),
                ("Rip inside Public", lambda function: Public(Rip(function))),
                )

        for form, decorate in forms:
            log: list[str] = []

            def Cleanup(agent) -> None:
                log.append("clean")

            Declared = type(
                    "Declared",
                    (Tag,),
                    {
                        "Cleanup": decorate(Cleanup),
                        },
                    )
            agent = Host()

            with self.subTest(form=form):
                Declared(agent)
                del Declared[agent]

                self.assertEqual(log, ["clean"])
                self.assertNotIn(agent, Declared)

    def test_underlay_remains_a_valid_rip_in_either_order(self) -> None:
        for order, decorate in (
                ("Rip outside", lambda function: Rip(Underlay(function))),
                ("Rip inside", lambda function: Underlay(Rip(function))),
                ):
            log: list[str] = []

            class Base(Tag):
                def Cleanup(agent) -> None:
                    log.append("base")

            def Cleanup(agent, underlay) -> None:
                log.append("shape")
                underlay()

            Shape = type(
                    "Shape",
                    (Base,),
                    {
                        "Cleanup": decorate(Cleanup),
                        },
                    )
            agent = Host()

            with self.subTest(order=order):
                Shape(agent)
                del Shape[agent]

                self.assertEqual(log, ["shape", "base"])
                self.assertIn(agent, Base)
                self.assertNotIn(agent, Shape)


if __name__ == "__main__":
    unittest.main()
