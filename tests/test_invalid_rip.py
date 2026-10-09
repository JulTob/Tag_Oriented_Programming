"""Declaration boundaries for the Rip protocol."""

from __future__ import annotations

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
                ("property", property),
                ):
            for order, build in (
                    ("Rip outside", _with_rip_outside),
                    ("Rip inside", _with_rip_inside),
                    ):
                with self.subTest(kind=kind, order=order):
                    self.assert_invalid(build(mark))

    def test_rip_is_rejected_on_a_private_name(self) -> None:
        self.assert_invalid(
                Rip(_member()),
                name="_Cleanup",
                )

    def test_bare_and_explicit_actions_remain_valid_rips(self) -> None:
        forms = (
                ("bare", lambda function: Rip(function)),
                ("Rip outside Action", lambda function: Rip(Action(function))),
                ("Rip inside Action", lambda function: Action(Rip(function))),
                ("Rip outside Constant", lambda function: Rip(Constant(function))),
                ("Rip inside Constant", lambda function: Constant(Rip(function))),
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
