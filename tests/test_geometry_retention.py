"""Form memoization belongs to its Tag, not to an external lifetime root."""

import gc
import unittest
import weakref

from TopKit import Action, Form, Pin, Public, Record, Tag
from TopKit.geometry import _form_key


class GeometryRetentionTests(unittest.TestCase):
    def cyclic_form(self, kind):
        if kind == "closure":
            def Owner(agent):
                return shape
        else:
            def Owner(agent, owner=None):
                return owner

        declaration = Action(Owner)

        class Base(Tag):
            Owner = declaration

        class Shape(Base):
            pass

        shape = Shape
        if kind == "default":
            Owner.__defaults__ = (Shape,)
        elif kind == "annotation":
            Owner.__annotations__["return"] = Shape
        elif kind == "callable":
            class Callable:
                def __init__(self, owner):
                    self.owner = owner

                def __call__(self, agent):
                    return self.owner

            Base.Owner = Action(Callable(Shape))

        self.assertEqual(Form(Shape), (Base, Shape))
        return Base, Shape

    def test_base_contribution_backreferences_do_not_keep_its_shape_alive(self):
        def create(kind):
            base, shape = self.cyclic_form(kind)
            return weakref.ref(base), weakref.ref(shape)

        for kind in ("closure", "default", "annotation", "callable"):
            with self.subTest(kind=kind):
                self.assert_collected(create(kind))

    def test_an_empty_retained_population_does_not_own_the_form_memo(self):
        def create():
            base, shape = self.cyclic_form("closure")
            return shape[:], (weakref.ref(base), weakref.ref(shape))

        population, references = create()
        self.assert_collected(references)
        self.assertEqual(len(population), 0)
        self.assertEqual(list(population), [])

    def test_a_retained_form_intentionally_keeps_its_tags_alive(self):
        def create():
            base, shape = self.cyclic_form("closure")
            return Form(shape), (weakref.ref(base), weakref.ref(shape))

        form, references = create()
        gc.collect()
        self.assertTrue(all(reference() is not None for reference in references))
        self.assertEqual(tuple(reference() for reference in references), form)
        del form
        self.assert_collected(references)

    def test_a_retained_form_of_an_empty_tag_has_the_same_lifetime_contract(self):
        def create():
            class Empty(Tag):
                pass

            return Form(Empty), weakref.ref(Empty)

        form, reference = create()
        gc.collect()
        self.assertIs(reference(), form[0])
        del form
        self.assert_collected((reference,))

    def test_a_diamond_keeps_base_first_order_and_owns_independent_memos(self):
        class Base(Tag):
            pass

        class Left(Base):
            pass

        class Right(Base):
            pass

        class Shape(Left, Right):
            pass

        self.assertEqual(Form(Base), (Base,))
        self.assertEqual(Form(Left), (Base, Left))
        self.assertEqual(Form(Right), (Base, Right))
        self.assertEqual(Form(Shape), (Base, Left, Right, Shape))
        self.assertEqual(Form(Shape), (Base, Left, Right, Shape))

    def test_a_tag_creates_its_memo_only_at_the_first_form_query(self):
        class Base(Tag):
            pass

        class Shape(Base):
            pass

        name = _form_key(Shape)
        self.assertNotIn(name, vars(Shape))
        first = Form(Shape)
        memo = vars(Shape)[name]
        second = Form(Shape)

        self.assertIs(vars(Shape)[name], memo)
        self.assertEqual(first, (Base, Shape))
        self.assertEqual(second, first)
        self.assertIsNot(second, first)

    def test_an_own_private_collision_is_not_overwritten(self):
        for value in (None, False, (Tag,), "application-private"):
            with self.subTest(value=value):
                class Base(Tag):
                    pass

                class Shape(Base):
                    pass

                name = _form_key(Shape)
                setattr(Shape, name, value)
                self.assertEqual(Form(Shape), (Base, Shape))
                self.assertEqual(Form(Shape), (Base, Shape))
                self.assertIs(vars(Shape)[name], value)

    def test_an_inherited_private_collision_is_not_shadowed(self):
        class Earlier(Tag):
            pass

        class Base(Tag):
            pass

        class Shape(Earlier, Base):
            pass

        name = _form_key(Shape)
        setattr(Base, name, "application-private")
        self.assertEqual(Form(Earlier), (Earlier,))
        self.assertEqual(Form(Shape), (Earlier, Base, Shape))
        self.assertEqual(Form(Shape), (Earlier, Base, Shape))
        self.assertNotIn(name, vars(Shape))
        self.assertEqual(getattr(Shape, name), "application-private")

    def test_a_foreign_internal_memo_is_not_reused_or_overwritten(self):
        class Earlier(Tag):
            pass

        class Foreign(Earlier):
            pass

        class Base(Tag):
            pass

        class Shape(Base):
            pass

        Form(Foreign)
        foreign = vars(Foreign)[_form_key(Foreign)]
        name = _form_key(Shape)
        setattr(Shape, name, foreign)

        self.assertEqual(Form(Shape), (Base, Shape))
        self.assertEqual(Form(Shape), (Base, Shape))
        self.assertIs(vars(Shape)[name], foreign)

    def test_published_pins_do_not_change_the_receiving_tags_cached_form(self):
        class Base(Tag):
            pass

        class Shape(Base):
            pass

        before = Form(Shape)

        @Pin
        class Labelled(Tag):
            @Public
            @Record
            def label(tag):
                return tag.__name__

        Labelled(Shape)
        self.assertEqual(Form(Shape), before)
        self.assertEqual(Form(Labelled), (Labelled,))
        self.assertEqual(Shape.label, "Shape")
        self.assertIn(Shape, Labelled[:])

    def test_form_does_not_install_memos_on_ordinary_classes(self):
        class Plain:
            pass

        before = dict(vars(Plain))
        self.assertEqual(Form(Plain), (Plain,))
        self.assertEqual(Form(Plain), (Plain,))
        self.assertEqual(dict(vars(Plain)), before)
        self.assertEqual(Form(int), (int,))
        with self.assertRaises(TypeError):
            Form(None)

    def assert_collected(self, references):
        gc.collect()
        gc.collect()
        for reference in references:
            self.assertIsNone(reference())


if __name__ == "__main__":
    unittest.main()
