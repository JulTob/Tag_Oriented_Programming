"""Pin marks and Forms are declarations, not metaclass lookup results."""

import unittest

from TopKit import Pin, Record, Tag, TagDeclarationError, Tool
from TopKit.declarations import _is_pin
from TopKit.geometry import _form_of


class PhysicalPinMarkTests(unittest.TestCase):
    def test_a_metaclass_cannot_hide_a_real_pin_mark(self):
        class Mask(type(Tag)):
            def __getattribute__(tag, name):
                if name == "__topkit_pin__":
                    return False
                return super().__getattribute__(name)

        @Pin
        class Rare(Tag, metaclass=Mask):
            @Record
            def label(tag):
                return "rare"

        class Wizard(Tag):
            pass

        Rare(Wizard)
        self.assertTrue(_is_pin(Rare))
        self.assertIn(Wizard, Rare[:])
        self.assertEqual(Wizard.label, "rare")

    def test_a_metaclass_cannot_invent_a_pin_mark(self):
        class Pretend(type(Tag)):
            def __getattribute__(tag, name):
                if name == "__topkit_pin__":
                    return True
                return super().__getattribute__(name)

        class Role(Tag, metaclass=Pretend):
            pass

        class Host:
            pass

        agent = Host()
        Role(agent)
        self.assertFalse(_is_pin(Role))
        self.assertIn(agent, Role[:])

    def test_a_metaclass_cannot_hide_the_pin_base_from_a_shape(self):
        class Mask(type(Tag)):
            def __getattribute__(tag, name):
                if name == "__mro__":
                    return (tag,)
                if name == "__bases__":
                    return ()
                return super().__getattribute__(name)

        @Pin
        class Base(Tag, metaclass=Mask):
            pass

        class Shape(Base):
            pass

        class Kind:
            pass

        self.assertTrue(_is_pin(Shape))
        self.assertEqual(_form_of(Shape), (Base, Shape))
        with self.assertRaises(TagDeclarationError):
            class Invalid(Shape):
                @Tool(Kind)
                def item(agent):
                    return Kind()

    def test_a_mixed_form_is_refused_even_if_metaclass_hides_bases(self):
        class Mask(type(Tag)):
            def __getattribute__(tag, name):
                if name == "__bases__":
                    return ()
                return super().__getattribute__(name)

        @Pin
        class Mark(Tag, metaclass=Mask):
            pass

        class Ordinary(Tag):
            pass

        with self.assertRaises(TagDeclarationError):
            class Mixed(Mark, Ordinary):
                pass

    def test_physical_mark_does_not_call_arbitrary_truth(self):
        class Truth:
            def __bool__(self):
                raise AssertionError("a physical Pin mark is exactly True")

        class Ordinary(Tag):
            pass

        type.__setattr__(Ordinary, "__topkit_pin__", Truth())
        self.assertFalse(_is_pin(Ordinary))
