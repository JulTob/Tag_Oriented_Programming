"""Saved Tag views resolve the same binding as a fresh Tag[agent] lookup."""

import unittest

from TopKit import Action
from TopKit import Operation
from TopKit import Pin
from TopKit import Public
from TopKit import Record
from TopKit import Tag
from TopKit import TagResolutionError


class Host:
    pass


class LiveTagViewTests(unittest.TestCase):
    def test_saved_view_follows_rip_and_new_tagging_position(self):
        class First(Tag):
            @Action
            def Work(agent):
                return "first"

            @Operation
            def Banner(tag):
                return "first"

        class Later(First):
            @Action
            def Work(agent):
                return "later"

            @Operation
            def Banner(tag):
                return "later"

        class Marker(Tag):
            @Record
            def level(agent):
                return agent.level_source

        agent = Host()
        agent.level_source = 1
        First(agent)
        Marker(agent)
        saved = Marker[agent]

        self.assertEqual(saved.Work(), "first")
        self.assertEqual(saved.level, 1)
        self.assertEqual(saved.Banner(), "first")
        self.assertTrue("Work" @ saved)

        del Marker[agent]
        with self.assertRaises(TagResolutionError):
            Marker[agent]
        for read in (
                lambda: saved.Work,
                lambda: saved.level,
                lambda: saved.Banner,
                lambda: "Work" @ saved,
                ):
            with self.subTest(read=read), self.assertRaises(TagResolutionError):
                read()

        agent.level_source = 2
        Later(agent)
        Marker(agent)
        fresh = Marker[agent]

        self.assertEqual(saved.Work(), fresh.Work())
        self.assertEqual(saved.Work(), "later")
        self.assertEqual(saved.level, fresh.level)
        self.assertEqual(saved.level, 2)
        self.assertEqual(saved.Banner(), fresh.Banner())
        self.assertEqual(saved.Banner(), "later")
        self.assertTrue("level" @ saved)

    def test_pin_view_also_rechecks_its_tag_membership(self):
        class Receiver(Tag):
            pass

        @Pin
        class Role(Tag):
            @Public
            @Action
            def Work(tag):
                return "ready"

        Role(Receiver)
        saved = Role[Receiver]
        self.assertEqual(saved.Work(), "ready")

        del Role[Receiver]
        with self.assertRaises(TagResolutionError):
            saved.Work
        with self.assertRaises(TagResolutionError):
            "Work" @ saved

        Role(Receiver)
        self.assertEqual(saved.Work(), Role[Receiver].Work())


if __name__ == "__main__":
    unittest.main()
