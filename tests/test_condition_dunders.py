"""Conditions use ordinary Contribution names, leaving Python protocol seats."""

import unittest

from TopKit import Action, Contract, Imprint, Pin, Post, Pre, Record, Tag
from TopKit import TagDeclarationError


class ConditionDunderTests(unittest.TestCase):
    names = ("__bool__", "__rmatmul__", "__del__", "__setattr__", "__unused__")
    marks = ((Pre,), (Post,), (Pre, Post), (Post, Pre))

    @staticmethod
    def condition(marks):
        def Readiness(agent):
            return agent.ready

        for mark in reversed(marks):
            Readiness = mark(Readiness)
        return Readiness

    def test_tag_and_pin_condition_dunders_fail_at_declaration(self):
        @Pin
        class Pinned(Tag):
            pass

        for base in (Tag, Pinned):
            for name in self.names:
                for marks in self.marks:
                    with self.subTest(base=base.__name__, name=name, marks=marks):
                        with self.assertRaises(TagDeclarationError) as caught:
                            type(Tag)("Refused", (base,), {name: self.condition(marks)})
                        self.assertIn("Refused." + name, str(caught.exception))

    def test_refusal_precedes_class_creation_and_target_effects(self):
        events = []

        class Existing(Tag):
            def __init_subclass__(cls, **kwargs):
                events.append("class created")
                super().__init_subclass__(**kwargs)

        class Host:
            ready = True

        agent = Host()
        agent.marker = False
        original = vars(agent).copy()

        @Record
        def Value(agent):
            events.append("Record built")
            return 1

        @Imprint
        def Train(agent):
            events.append("Imprint ran")

        with self.assertRaises(TagDeclarationError):
            refused = type(Tag)("Refused", (Existing,), {
                    "Value": Value,
                    "Train": Train,
                    "__bool__": self.condition((Post,)),
                    })
            refused(agent)

        self.assertEqual(events, [])
        self.assertEqual(vars(agent), original)
        self.assertIs(type(agent), Host)

    def test_namespace_name_decides_not_the_functions_original_name(self):
        for marks in self.marks:
            with self.subTest(marks=marks):
                def __bool__(agent):
                    return agent.ready

                check = __bool__
                for mark in reversed(marks):
                    check = mark(check)
                ordinary = type(Tag)("Ordinary", (Tag,), {"Ready": check})

                class Host:
                    ready = True

                agent = Host()
                ordinary(agent)
                self.assertIs(agent.Ready, True)
                self.assertTrue(Contract.Holds(agent))
                agent.ready = False
                self.assertIs(agent.Ready, False)

    def test_allowed_action_protocols_still_work(self):
        events = []

        class Protocols(Tag):
            @Action
            def __add__(agent, other):
                return agent.value + other

            def __enter__(agent):
                events.append("enter")
                return agent

            def __exit__(agent, kind, value, traceback):
                events.append("exit")

        class Host:
            value = 3

        agent = Host()
        Protocols(agent)
        self.assertEqual(agent + 4, 7)
        with agent as entered:
            self.assertIs(entered, agent)
        self.assertEqual(events, ["enter", "exit"])

    def test_late_condition_dunders_leave_existing_namespace_intact(self):
        @Pin
        class Pinned(Tag):
            pass

        for base in (Tag, Pinned):
            for name in self.names:
                for marks in self.marks:
                    with self.subTest(base=base.__name__, name=name, marks=marks):
                        original = lambda *arguments: True
                        # Pin protocols and Agent truth have separate rules.
                        # Plain values still test replacement atomicity.
                        if base is Pinned or name == "__bool__":
                            original = False
                        candidate = type(Tag)("Existing", (base,), {name: original})
                        before = dict(vars(candidate))
                        with self.assertRaises(TagDeclarationError):
                            setattr(candidate, name, self.condition(marks))
                        self.assertEqual(dict(vars(candidate)), before)
                        self.assertIs(vars(candidate)[name], original)

                        delattr(candidate, name)
                        before = dict(vars(candidate))
                        with self.assertRaises(TagDeclarationError):
                            setattr(candidate, name, self.condition(marks))
                        self.assertEqual(dict(vars(candidate)), before)

    def test_late_ordinary_value_does_not_inspect_function_metadata(self):
        class Value:
            @property
            def __func__(self):
                raise AssertionError("a stored value is not a function")

        class Existing(Tag):
            pass

        value = Value()
        Existing.setting = value
        self.assertIs(vars(Existing)["setting"], value)

    def test_scan_refuses_condition_marked_after_declaration(self):
        class Existing(Tag):
            def __unused__(agent):
                return True

        # Decorating the function in place bypasses metaclass assignment.
        # The ordinary scanner must still refuse the forbidden condition.
        Post(vars(Existing)["__unused__"])

        class Host:
            pass

        agent = Host()
        before = dict(vars(agent))
        with self.assertRaises(TagDeclarationError) as caught:
            Existing(agent)
        self.assertIn("Existing.__unused__", str(caught.exception))
        self.assertEqual(vars(agent), before)
        self.assertIs(type(agent), Host)
        self.assertNotIn(agent, Existing[:])


if __name__ == "__main__":
    unittest.main()
