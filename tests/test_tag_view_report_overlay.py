"""Agent-bound Tag views read Reports at their recorded Overlay point."""

import unittest

from TopKit import Report
from TopKit import Tag
from TopKit import TagResolutionError


class TagViewReportOverlayTests(unittest.TestCase):
    class Host:
        pass

    def test_shape_view_reads_base_report_at_its_tagging_point(self):
        class Base(Tag):
            @Report
            def colour(tag):
                return "blue"

        class Shape(Base):
            pass

        agent = self.Host()
        Shape(agent)

        self.assertEqual(Base[agent].colour, "blue")
        self.assertEqual(Shape[agent].colour, "blue")

    def test_independent_report_at_shape_point_wins_over_base(self):
        class Base(Tag):
            @Report
            def colour(tag):
                return "base"

        class Other(Tag):
            @Report
            def colour(tag):
                return "other"

        class Shape(Base):
            pass

        class Later(Tag):
            @Report
            def colour(tag):
                return "later"

        agent = self.Host()
        Base(agent)
        Other(agent)
        Shape(agent)
        view = Shape[agent]

        self.assertEqual(view.colour, "other")
        self.assertTrue("colour" @ view)
        Other.colour = "changed"
        self.assertEqual(view.colour, "changed")

        Later(agent)
        self.assertEqual(view.colour, "changed")
        self.assertEqual(Later[agent].colour, "later")

    def test_deleting_top_report_reveals_previous_recorded_layer(self):
        class Base(Tag):
            @Report
            def colour(tag):
                return None

        class Other(Tag):
            @Report
            def colour(tag):
                return False

        class Shape(Base):
            pass

        agent = self.Host()
        Base(agent)
        Other(agent)
        Shape(agent)
        view = Shape[agent]
        self.assertIs(view.colour, False)

        del Other.colour
        self.assertIsNone(view.colour)
        self.assertTrue("colour" @ view)

        del Base.colour
        with self.assertRaises(AttributeError):
            _ = view.colour
        self.assertFalse("colour" @ view)

    def test_own_report_wins_then_deletion_reveals_earlier_overlay(self):
        class Base(Tag):
            @Report
            def colour(tag):
                return "base"

        class Other(Tag):
            @Report
            def colour(tag):
                return "other"

        class Shape(Base):
            @Report
            def colour(tag):
                return "shape"

        agent = self.Host()
        Base(agent)
        Other(agent)
        Shape(agent)
        view = Shape[agent]
        self.assertEqual(view.colour, "shape")

        del Shape.colour
        self.assertEqual(view.colour, "other")
        del Other.colour
        self.assertEqual(view.colour, "base")

    def test_rip_removes_source_but_not_other_recorded_layers(self):
        class Base(Tag):
            @Report
            def colour(tag):
                return "base"

        class Other(Tag):
            @Report
            def colour(tag):
                return "other"

        class Shape(Base):
            pass

        agent = self.Host()
        Base(agent)
        Other(agent)
        Shape(agent)
        view = Shape[agent]

        del Other[agent]
        self.assertEqual(view.colour, "base")
        del Base[agent]
        with self.assertRaises(AttributeError):
            _ = view.colour
        self.assertFalse("colour" @ view)

    def test_saved_view_uses_new_tagging_point_after_retag(self):
        class Base(Tag):
            @Report
            def colour(tag):
                return "base"

        class First(Tag):
            @Report
            def colour(tag):
                return "first"

        class Second(Tag):
            @Report
            def colour(tag):
                return "second"

        class Shape(Base):
            pass

        agent = self.Host()
        First(agent)
        Shape(agent)
        saved = Shape[agent]
        self.assertEqual(saved.colour, "base")

        del Shape[agent]
        with self.assertRaises(TagResolutionError):
            _ = saved.colour

        Second(agent)
        Shape(agent)
        self.assertEqual(saved.colour, "second")
        self.assertEqual(saved.colour, Shape[agent].colour)
        del Second[agent]
        self.assertEqual(saved.colour, "base")


if __name__ == "__main__":
    unittest.main()
