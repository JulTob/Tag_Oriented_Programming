"""Tag declarations inside checks cannot create a new TOP class."""

import unittest

from TopKit import Contract
from TopKit import Imprint
from TopKit import Post
from TopKit import Pre
from TopKit import Precondition
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagPostconditionError


class Host:
    pass


class ObservationalTagCreationTests(unittest.TestCase):
    def test_caught_tag_declaration_still_refuses_precondition(self):
        created = []
        body_effects = []

        class Candidate(Tag):
            @Pre
            def Ready(agent):
                try:
                    class Temp(Tag):
                        body_effects.append("class body ran")

                    created.append(Temp)
                except TagCompositionError:
                    pass
                return True

        agent = Host()
        with self.assertRaises(Precondition.Ready) as caught:
            Candidate(agent)

        self.assertIsInstance(caught.exception.__cause__, TagCompositionError)
        self.assertIn("create a Tag class", str(caught.exception))
        self.assertEqual(body_effects, ["class body ran"])
        self.assertEqual(created, [])
        self.assertNotIn(agent, Candidate[:])

    def test_caught_type_construction_still_fails_post(self):
        created = []

        class Checked(Tag):
            @Post
            def Ready(agent):
                if agent.try_create:
                    try:
                        created.append(type("Temp", (Tag,), {}))
                    except TagCompositionError:
                        pass
                return True

        agent = Host()
        agent.try_create = False
        Checked(agent)
        agent.try_create = True

        self.assertFalse(agent.Ready)
        with self.assertRaises(TagPostconditionError.Ready) as caught:
            Contract.Postconditions(agent)
        self.assertIsInstance(caught.exception.__cause__, TagCompositionError)
        self.assertIn("create a Tag class", str(caught.exception))
        self.assertEqual(created, [])
        self.assertIn(agent, Checked[:])

    def test_action_called_by_post_cannot_hide_class_creation(self):
        created = []

        class Checked(Tag):
            def Inspect(agent):
                if agent.try_create:
                    try:
                        class Temp(Tag):
                            pass

                        created.append(Temp)
                    except TagCompositionError:
                        pass
                return True

            @Post
            def Ready(agent):
                return agent.Inspect()

        agent = Host()
        agent.try_create = False
        Checked(agent)
        agent.try_create = True

        self.assertFalse(agent.Ready)
        self.assertEqual(created, [])
        self.assertIn(agent, Checked[:])

    def test_nested_tag_declaration_outside_a_check_remains_legal(self):
        class Outer(Tag):
            class Inner(Tag):
                pass

        self.assertTrue(issubclass(Outer.Inner, Tag))
        self.assertIsNot(Outer.Inner, Outer)
        self.assertEqual(len(Outer.Inner[:]), 0)

    def test_imprint_can_create_a_tag_class(self):
        created = []

        class Factory(Tag):
            @Imprint
            def Make(agent):
                class Product(Tag):
                    pass

                created.append(Product)

        agent = Host()
        Factory(agent)

        self.assertEqual(len(created), 1)
        self.assertTrue(issubclass(created[0], Tag))
        self.assertIn(agent, Factory[:])


if __name__ == "__main__":
    unittest.main()
