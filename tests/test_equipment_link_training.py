"""Equipment Links use the same training boundary as ordinary Tagging."""

import unittest
import warnings
from unittest.mock import patch

from TopKit import (Imprint, Link, Post, Pre, Record, Tag, TagCompositionError,
                    TagPostconditionError, TaggingFailure, TrainingWarning,
                    agent, contact)
from TopKit.links import _data_of


class Host:
    pass


class EquipmentLinkTrainingTests(unittest.TestCase):
    def test_failed_steps_continue_and_warn_after_admission_and_posts(self):
        events = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def absent(owner, target):
                    raise ValueError("no initial value")

                @Record
                def position(owner, target):
                    return "belt"

                @Imprint
                def First(owner, target):
                    events.append("first")
                    raise ValueError("training failed")

                @Imprint
                def Later(owner, target):
                    events.append("later")

                @Post
                def Stored(owner, target):
                    events.append(("post", target in owner.Carries[:]))
                    return owner.Carries[target].position == "belt"

        owner, item = Host(), Host()
        Inventory(owner)

        def Show(message, *args, **kwargs):
            events.append(("warning", message.name, item in owner.Carries[:]))

        with warnings.catch_warnings(), patch.object(warnings, "showwarning", Show):
            warnings.simplefilter("always", TrainingWarning)
            self.assertIs(owner.Carries(item), item)
        self.assertEqual(events, ["first", "later", ("post", True),
                                  ("warning", "absent", True),
                                  ("warning", "First", True)])
        self.assertFalse("absent" @ owner.Carries[item])
        self.assertIn(item, owner.Carries)

    def test_training_can_break_contact_and_pair_but_still_admits_both(self):
        class Equipment(Tag):
            @Post
            def Charged(item):
                return item.charge > 0

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Imprint
                def Drain(owner, target):
                    target.charge = 0
                    raise ValueError("training failed")

                @Post
                def Stored(owner, target):
                    return False

        owner, item = Host(), Host()
        item.charge = 1
        Equipment(item)
        Inventory(owner)
        with self.assertWarns(TrainingWarning.Drain):
            with self.assertRaises(TaggingFailure) as caught:
                owner.Carries(item)
        self.assertEqual(caught.exception.failed_posts, ("Stored", "Charged"))
        self.assertIn(item, owner.Carries[:])
        self.assertIn(item, ~owner.Carries)
        self.assertFalse(bool(item))

    def test_broken_contact_is_refused_before_header_gate_or_pair_creation(self):
        events = []

        class Equipment(Tag):
            @Post
            def Charged(item):
                return item.charge > 0

        class Registered(Tag):
            @Pre
            def Allowed(item):
                events.append("header gate")
                return True

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Registered):
                @Pre
                def Allowed(owner, target):
                    events.append("pair gate")
                    return True

        owner, item = Host(), Host()
        item.charge = 1
        Equipment(item)
        item.charge = 0
        Inventory(owner)
        with self.assertRaises(TagCompositionError):
            owner.Carries(item)
        self.assertEqual(events, [])
        self.assertNotIn(item, Registered[:])
        self.assertNotIn(item, owner.Carries[:])
        self.assertEqual(_data_of(owner.Carries).pairs, {})

    def test_failed_header_post_stops_before_link_gate(self):
        events = []

        class Registered(Tag):
            @Post
            def Ready(item):
                return False

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Registered):
                @Pre
                def Allowed(owner, target):
                    events.append("pair gate")
                    return True

        owner, item = Host(), Host()
        Inventory(owner)
        with self.assertRaises(TagPostconditionError.Ready):
            owner.Carries(item)
        self.assertEqual(events, [])
        self.assertIn(item, Registered[:])
        self.assertNotIn(item, owner.Carries[:])
        self.assertEqual(_data_of(owner.Carries).pairs, {})


if __name__ == "__main__":
    unittest.main()
