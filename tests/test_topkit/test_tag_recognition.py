"""A Tag is recognized by MetaTag, not by a field-shaped host name."""

from __future__ import annotations

import unittest

from TopKit import Flag
from TopKit import Pin
from TopKit import Record
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagDeclarationError
from TopKit.tags import MetaTag

from ._fixtures import Agent


class TagRecognitionTests(unittest.TestCase):
    def test_field_slice_ignores_a_metaclass_mask_of_the_class_dictionary(self) -> None:
        class Masked(MetaTag):
            def __getattribute__(tag, name):
                if name == "__dict__" and type.__getattribute__(tag, "mask_field"):
                    return {}
                return super().__getattribute__(name)

        class Special(Tag, metaclass=Masked):
            mask_field = False

        member = Agent()
        Special(member)
        type.__setattr__(Special, "mask_field", True)

        self.assertEqual(list(Special[:]), [member])
        self.assertEqual(list(Special), [member])

    def test_tagging_and_rip_update_the_tags_own_field(self) -> None:
        class Masked(MetaTag):
            def __getattribute__(tag, name):
                if name == "_topkit_field":
                    raise AttributeError(name)
                return super().__getattribute__(name)

        class Special(Tag, metaclass=Masked):
            pass

        member = Agent()
        Special(member)
        self.assertIn(member, Special)
        self.assertEqual(list(Special[:]), [member])

        del Special[member]
        self.assertNotIn(member, Special)
        self.assertEqual(list(Special[:]), [])

    def test_flag_and_pin_refuse_a_host_that_only_looks_like_a_tag(self) -> None:
        class Lookalike:
            _topkit_field = object()

        with self.assertRaises(TagDeclarationError):
            Flag(Lookalike)

        with self.assertRaises(TagDeclarationError):
            Pin(Lookalike)

    def test_a_host_mixin_is_not_a_tag_base_of_a_pin(self) -> None:
        class HostBase:
            _topkit_field = object()

        class HostMixin(HostBase):
            pass

        @Pin
        class Pinned(Tag):
            pass

        class Shape(HostMixin, Pinned):
            pass

        self.assertTrue(issubclass(Shape, Pinned))

    def test_a_pin_cannot_replace_a_non_tag_host_protocol(self) -> None:
        class HostMixin:
            _topkit_field = object()
            status = "host protocol"

        class Victim(HostMixin, Tag):
            pass

        @Pin
        class Patch(Tag):
            @Record
            def status(tag):
                return "pin record"

        with self.assertRaises(TagCompositionError):
            Patch(Victim)

        self.assertEqual(Victim.status, "host protocol")
        self.assertNotIn(Victim, Patch)
