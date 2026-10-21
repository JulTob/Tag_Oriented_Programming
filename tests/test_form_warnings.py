"""Sibling Base collisions are diagnosed where a Shape's Form is declared."""

from __future__ import annotations

import inspect
import unittest
import warnings
from unittest.mock import patch

from TopKit import Action, Imprint, Post, Record, Tag, TagContractWarning
from TopKit import TagDeclarationError
from TopKit import TagOverwriteWarning, Underlay
from TopKit.tags import MetaTag


class Host:
    pass


class FormWarningTests(unittest.TestCase):
    def test_warning_bookkeeping_does_not_replace_a_programmer_member(self) -> None:
        class A(Tag):
            @Action
            def Fine(agent):
                return "A"

        class B(Tag):
            @Action
            def Fine(agent):
                return "B"

        with warnings.catch_warnings(record=True) as declared:
            warnings.simplefilter("always")
            class C(A, B):
                _TOPKIT_FORM_WARNINGS = "programmer value"

        self.assertEqual(C.__dict__["_TOPKIT_FORM_WARNINGS"], "programmer value")
        self.assertEqual(len(declared), 1, declared)
        with warnings.catch_warnings(record=True) as applied:
            warnings.simplefilter("always")
            C(Host())
        self.assertEqual(applied, [])

        # Even a deliberate collision with the owner-qualified key leaves
        # the programmer's binding alone. The warning then stays at the
        # existing application boundary because no class memo was saved.
        with patch("TopKit.form_warnings._memo_key", return_value="occupied"):
            with warnings.catch_warnings(record=True) as declared:
                warnings.simplefilter("always")
                class D(A, B):
                    occupied = "another programmer value"

            self.assertEqual(D.__dict__["occupied"], "another programmer value")
            self.assertEqual(declared, [])
            with warnings.catch_warnings(record=True) as applied:
                warnings.simplefilter("always")
                D(Host())
            self.assertEqual(len(applied), 1, applied)

    def test_sibling_collisions_warn_at_the_shape_declaration_only(self) -> None:
        for mark, warning_type in (
                (Action, TagOverwriteWarning),
                (Record, TagOverwriteWarning),
                (Post, TagContractWarning),
                ):
            with self.subTest(mark=mark.__name__):
                class A(Tag):
                    pass

                class B(Tag):
                    pass

                A.Fine = mark(lambda agent: True)
                B.Fine = mark(lambda agent: True)

                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    declaration_line = inspect.currentframe().f_lineno + 1
                    class C(A, B):
                        pass

                    C(Host())
                    C(Host())

                self.assertEqual(len(caught), 1, caught)
                self.assertIs(caught[0].category, warning_type)
                self.assertEqual(caught[0].filename, __file__)
                self.assertEqual(caught[0].lineno, declaration_line)
                self.assertIn("C", str(caught[0].message))
                self.assertIn("A.Fine", str(caught[0].message))
                self.assertIn("B.Fine", str(caught[0].message))
                if mark is Post:
                    self.assertIn("independent", str(caught[0].message))
                    self.assertNotIn("weaken", str(caught[0].message))

    def test_warning_as_error_fails_at_declaration(self) -> None:
        class A(Tag):
            @Action
            def Fine(agent):
                return "A"

        class B(Tag):
            @Action
            def Fine(agent):
                return "B"

        with warnings.catch_warnings():
            warnings.simplefilter("error", TagOverwriteWarning)
            with self.assertRaises(TagOverwriteWarning):
                class C(A, B):
                    pass

    def test_custom_metatag_subclass_keeps_declaration_diagnosis(self) -> None:
        class Extension(MetaTag):
            def __new__(meta, name, bases, namespace, **kwargs):
                return super().__new__(meta, name, bases, namespace, **kwargs)

        class A(Tag):
            @Action
            def Fine(agent):
                return "A"

        class B(Tag):
            @Action
            def Fine(agent):
                return "B"

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            declaration_line = inspect.currentframe().f_lineno + 1
            class C(A, B, metaclass=Extension):
                pass

            C(Host())
            C(Host())

        self.assertEqual(len(caught), 1, caught)
        self.assertIn("C's Form", str(caught[0].message))
        self.assertEqual(caught[0].filename, __file__)
        self.assertEqual(caught[0].lineno, declaration_line)

    def test_invalid_underlay_keeps_its_application_time_failure(self) -> None:
        class A(Tag):
            @Action
            def Fine(agent):
                return "A"

        class B(Tag):
            @Action
            @Underlay
            def Fine(agent):  # missing the callable Underlay parameter
                return "B"

        class C(A, B):
            pass

        with self.assertRaises(TagDeclarationError):
            C(Host())

    def test_independent_application_and_reversed_form_still_warn_at_runtime(self) -> None:
        class A(Tag):
            @Action
            def Fine(agent):
                return "A"

        class B(Tag):
            @Action
            def Fine(agent):
                return "B"

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            class C(A, B):
                pass

        direct = Host()
        A(direct)
        with self.assertWarns(TagOverwriteWarning):
            B(direct)

        reversed_order = Host()
        B(reversed_order)
        with self.assertWarns(TagOverwriteWarning) as caught:
            C(reversed_order)
        self.assertIn("A.Fine", str(caught.warning))
        self.assertIn("B", str(caught.warning))
        self.assertEqual(reversed_order.Fine(), "A")

    def test_preexisting_first_sibling_keeps_declared_order(self) -> None:
        class A(Tag):
            @Action
            def Fine(agent):
                return "A"

        class B(Tag):
            @Action
            def Fine(agent):
                return "B"

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            class C(A, B):
                pass

        agent = Host()
        A(agent)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            C(agent)
        self.assertEqual(caught, [])
        self.assertEqual(agent.Fine(), "B")

    def test_nested_form_and_diamond_do_not_repeat_existing_diagnosis(self) -> None:
        class Root(Tag):
            pass

        class A(Root):
            @Action
            def Fine(agent):
                return "A"

        class B(Root):
            @Action
            def Fine(agent):
                return "B"

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            class C(A, B):
                pass

            class D(C):
                pass

            D(Host())
        self.assertEqual(len(caught), 1, caught)
        self.assertIn("C", str(caught[0].message))

    def test_a_later_shape_warns_only_for_the_collision_it_introduces(self) -> None:
        class A(Tag):
            @Action
            def Fine(agent):
                return "A"

        class B(Tag):
            @Action
            def Fine(agent):
                return "B"

        class X(Tag):
            @Action
            def Fine(agent):
                return "X"

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            class C(A, B):
                pass

            class D(C, X):
                pass

            D(Host())
        self.assertEqual(len(caught), 2, caught)
        self.assertIn("C's Form", str(caught[0].message))
        self.assertIn("B.Fine over A.Fine", str(caught[0].message))
        self.assertIn("D's Form", str(caught[1].message))
        self.assertIn("X.Fine over B.Fine", str(caught[1].message))

    def test_nested_independent_tagging_keeps_its_own_warning_context(self) -> None:
        class A(Tag):
            @Action
            def Fine(agent):
                return "A"

            @Imprint
            def Bring_B(agent):
                B(agent)

        class B(Tag):
            @Action
            def Fine(agent):
                return "B"

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            class C(A, B):
                pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            C(Host())
        self.assertEqual(len(caught), 1, caught)
        self.assertIn("B.Fine replaces the Action of independent Tag A",
                      str(caught[0].message))

    def test_collision_added_after_shape_declaration_warns_at_runtime(self) -> None:
        class A(Tag):
            pass

        class B(Tag):
            pass

        class C(A, B):
            pass

        A.Fine = Action(lambda agent: "A")
        B.Fine = Action(lambda agent: "B")

        with self.assertWarns(TagOverwriteWarning):
            C(Host())

    def test_explicit_underlay_and_stored_value_are_silent(self) -> None:
        class A(Tag):
            @Action
            def Fine(agent):
                return "A"

            @Record
            def Score(agent):
                return 1

        class B(Tag):
            @Action
            @Underlay
            def Fine(agent, prior):
                return prior() + "B"

            @Record
            def Score(agent, stored):
                return stored + 1

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            class C(A, B):
                pass

            agent = Host()
            C(agent)
        self.assertEqual(caught, [])
        self.assertEqual(agent.Fine(), "AB")
        self.assertEqual(agent.Score, 2)


if __name__ == "__main__":
    unittest.main()
