"""Declaration caching must not extend the lifetime of its owning Tag."""

import gc
import unittest
import weakref

from TopKit import Action, Constant, Pin, Public, Record, Tag, TagCompositionError
from TopKit.declarations import _declarations_of


class Host:
    pass


class DeclarationRetentionTests(unittest.TestCase):
    def assert_collected(self, references):
        gc.collect()
        gc.collect()
        for reference in references:
            self.assertIsNone(reference())

    def test_an_action_class_cell_does_not_keep_its_tag_alive(self):
        def create():
            class Ephemeral(Tag):
                @Action
                def Owner(agent):
                    return __class__

            agent = Host()
            Ephemeral(agent)
            self.assertIs(agent.Owner(), Ephemeral)
            return weakref.ref(Ephemeral), weakref.ref(agent)

        self.assert_collected(create())

    def test_action_defaults_and_annotations_do_not_keep_the_tag_alive(self):
        def create(kind):
            def Owner(agent, origin=None):
                return origin

            tag = type("Ephemeral", (Tag,), {"Owner": Action(Owner)})
            if kind == "default":
                Owner.__defaults__ = (tag,)
            else:
                Owner.__annotations__["return"] = tag
            agent = Host()
            tag(agent)
            if kind == "default":
                self.assertIs(agent.Owner(), tag)
            return weakref.ref(tag), weakref.ref(agent)

        for kind in ("default", "annotation"):
            with self.subTest(kind=kind):
                self.assert_collected(create(kind))

    def test_an_action_closure_does_not_keep_its_tag_alive(self):
        def create():
            def Owner(agent):
                return tag

            tag = type("Ephemeral", (Tag,), {"Owner": Action(Owner)})
            agent = Host()
            tag(agent)
            self.assertIs(agent.Owner(), tag)
            return weakref.ref(tag), weakref.ref(agent)

        self.assert_collected(create())

    def test_a_pin_scanned_at_declaration_does_not_keep_itself_alive(self):
        def create():
            @Pin
            class Ephemeral(Tag):
                def Owner(tag):
                    return __class__

            return (weakref.ref(Ephemeral),)

        self.assert_collected(create())

    def test_a_shape_owns_its_scan_instead_of_inheriting_the_bases(self):
        class Base(Tag):
            def Base_Work(agent):
                return "base"

        base_declarations = _declarations_of(Base)

        class Shape(Base):
            def Shape_Work(agent):
                return "shape"

        shape_declarations = _declarations_of(Shape)
        self.assertIsNot(base_declarations, shape_declarations)
        self.assertIs(_declarations_of(Base), base_declarations)
        self.assertIs(_declarations_of(Shape), shape_declarations)
        self.assertEqual([name for name, _ in base_declarations.actions], ["Base_Work"])
        self.assertEqual([name for name, _ in shape_declarations.actions], ["Shape_Work"])
        agent = Host()
        Shape(agent)
        self.assertEqual((agent.Base_Work(), agent.Shape_Work()), ("base", "shape"))

    def test_public_pin_invalidates_the_receiving_tags_cached_scan(self):
        class Base(Tag):
            pass

        existing = Host()
        Base(existing)
        before = _declarations_of(Base)

        @Pin
        class Given(Tag):
            @Public
            @Record
            def label(tag):
                return {"owner": tag.__name__}

            @Public
            def Identify(tag, agent):
                return tag.label

        Given(Base)
        after = _declarations_of(Base)
        self.assertIsNot(before, after)
        self.assertIs(_declarations_of(Base), after)
        self.assertEqual([name for name, _, _ in after.reports], ["label"])
        self.assertEqual([name for name, _, _ in after.operations], ["Identify"])
        future = Host()
        Base(future)
        for agent in (existing, future):
            with self.subTest(agent=agent):
                self.assertIs(agent.label, Base.label)
                self.assertIs(agent.Identify(), Base.label)

    def test_an_existing_private_binding_is_preserved(self):
        class Given(Tag):
            _TOPKIT_DECLARATIONS = "application-private"

            def Work(agent):
                return "given"

        before = _declarations_of(Given)
        after = _declarations_of(Given)
        self.assertIs(before, after)
        agent = Host()
        Given(agent)
        self.assertEqual(agent.Work(), "given")
        self.assertEqual(vars(Given)["_TOPKIT_DECLARATIONS"], "application-private")

    def test_a_shape_scan_is_independent_of_a_bases_private_binding(self):
        class Base(Tag):
            _TOPKIT_DECLARATIONS = "application-private"

        class Shape(Base):
            def Work(agent):
                return "shape"

        declarations = _declarations_of(Shape)
        self.assertIs(_declarations_of(Shape), declarations)
        self.assertEqual(vars(Base)["_TOPKIT_DECLARATIONS"], "application-private")
        self.assertEqual(Shape._TOPKIT_DECLARATIONS, "application-private")
        self.assertNotIn("_TOPKIT_DECLARATIONS", vars(Shape))
        agent = Host()
        Shape(agent)
        self.assertEqual(agent.Work(), "shape")

    def test_pin_invalidation_preserves_a_private_binding(self):
        class Base(Tag):
            _TOPKIT_DECLARATIONS = "application-private"

        existing = Host()
        Base(existing)

        @Pin
        class Given(Tag):
            @Public
            @Record
            def label(tag):
                return {"owner": tag.__name__}

        Given(Base)
        self.assertEqual(vars(Base)["_TOPKIT_DECLARATIONS"], "application-private")
        future = Host()
        Base(future)
        self.assertIs(existing.label, Base.label)
        self.assertIs(future.label, Base.label)

    def test_multiple_bases_keep_their_effective_private_binding(self):
        class Earlier(Tag):
            pass

        _declarations_of(Earlier)

        class Later(Tag):
            _TOPKIT_DECLARATIONS = "application-private"

        class Shape(Earlier, Later):
            pass

        self.assertEqual(Shape._TOPKIT_DECLARATIONS, "application-private")
        shape_declarations = _declarations_of(Shape)
        self.assertIs(_declarations_of(Shape), shape_declarations)
        self.assertEqual(Shape._TOPKIT_DECLARATIONS, "application-private")
        self.assertNotIn("_TOPKIT_DECLARATIONS", vars(Earlier))
        self.assertNotIn("_TOPKIT_DECLARATIONS", vars(Shape))

    def test_a_failed_publication_does_not_leave_a_stale_scan_after_rollback(self):
        class Base(Tag):
            pass

        class Fixed(Tag):
            @Constant
            @Record
            def label(agent):
                return "fixed"

        existing = Host()
        Base(existing)
        Fixed(existing)
        before = _declarations_of(Base)

        @Pin
        class Given(Tag):
            @Public
            @Record
            def label(tag):
                return "pinned"

        with self.assertRaises(TagCompositionError):
            Given(Base)

        after = _declarations_of(Base)
        self.assertEqual(after.reports, before.reports)
        self.assertEqual(after.operations, before.operations)
        self.assertEqual(existing.label, "fixed")
        future = Host()
        Base(future)
        self.assertFalse("label" @ future)


if __name__ == "__main__":
    unittest.main()
