"""Named failures remember a check's text without owning its name object."""

import gc
import unittest
import weakref

from TopKit import Imprint, Post, Pre, Tag
from TopKit.errors import TagImprintError, TagPostconditionError
from TopKit.errors import TagPreconditionError


class Name(str):
    pass


class Host:
    pass


class NamedFailureRetentionTests(unittest.TestCase):
    def test_each_declared_failure_keeps_text_but_releases_the_name_and_agent(self):
        cases = (
                (Pre, TagPreconditionError, "Pre"),
                (Imprint, TagImprintError, "Imprint"),
                (Post, TagPostconditionError, "Post"),
                )

        for mark, failure, kind in cases:
            with self.subTest(kind=kind):
                text = f"Transient_{kind}_296"

                def declare():
                    class Agency(Tag):
                        pass

                    agent = Host()
                    Agency(agent)
                    name = Name(text)
                    name.owner = agent
                    role = type("Role", (Tag,), {
                            name: mark(lambda agent: True),
                            })
                    selected = failure.Named(text)
                    self.assertIs(getattr(failure, text), selected)
                    return selected, (
                            weakref.ref(name),
                            weakref.ref(agent),
                            weakref.ref(role),
                            )

                selected, references = declare()
                gc.collect()
                gc.collect()
                for label, reference in zip(("name", "Agent", "Tag"), references):
                    self.assertIsNone(reference(), label)
                self.assertIs(type(selected.name), str)
                self.assertEqual(selected.name, text)
                self.assertIs(failure.Named(Name(text)), selected)

    def test_registration_does_not_call_string_subclass_hooks(self):
        def forbidden(*arguments):
            raise AssertionError("user string hook ran")

        class Hostile(str):
            __str__ = forbidden
            __repr__ = forbidden
            __format__ = forbidden
            __hash__ = forbidden
            __eq__ = forbidden
            startswith = forbidden

        text = "Hostile_Post_296"
        selected = TagPostconditionError.Named(Hostile(text))
        self.assertIs(TagPostconditionError.Named(text), selected)
        self.assertIs(getattr(TagPostconditionError, text), selected)
        self.assertEqual(selected.__name__, text)
        self.assertEqual(selected.name, text)
        self.assertIs(type(selected.name), str)


if __name__ == "__main__":
    unittest.main()
