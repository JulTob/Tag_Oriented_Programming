"""Optional documentation does not determine Public Operation behavior."""

import unittest

from TopKit import (Operation, Post, Postcondition, Public, Tag,
                    TagRogueAccessError)


class Host:
    pass


class CallableOperation:
    def __init__(operation, documentation_error=None):
        operation.documentation_error = documentation_error

    def __getattribute__(operation, name):
        if name == "__doc__":
            error = object.__getattribute__(operation, "documentation_error")
            if error is not None:
                raise error
        return object.__getattribute__(operation, name)

    def __call__(operation, tag, agent=None, value=0, *, scale=1):
        return tag, agent, value * scale


class PublicOperationMetadataTests(unittest.TestCase):
    def agency(self, operation):
        class Agency(Tag):
            Work = Public(Operation(operation))

        return Agency

    def check_calls(self, Agency, documentation):
        self.assertEqual(Agency.Work(value=4, scale=2), (Agency, None, 8))
        direct = Agency.Work
        agent = Host()
        self.assertIs(Agency(agent), agent)
        self.assertIn(agent, Agency[:])
        self.assertIn(agent, Agency)
        view = Agency[agent]
        captured = agent.Work
        captured_view = view.Work

        self.assertEqual(direct(agent, 4, scale=2), (Agency, agent, 8))
        for call in (agent.Work, view.Work, captured, captured_view):
            self.assertEqual(call(4, scale=2), (Agency, agent, 8))
            self.assertEqual(call.__doc__, documentation)
            self.assertEqual(call.__name__, "Work")
            self.assertEqual(call.__func__.__qualname__, f"{Agency.__qualname__}.Work")

    def test_callable_without_documentation_publishes(self):
        operation = CallableOperation(AttributeError("__doc__"))
        self.check_calls(self.agency(operation), None)

    def test_ordinary_documentation_failure_is_optional(self):
        operation = CallableOperation()
        Agency = self.agency(operation)
        # Metadata may become unreadable after the declaration was accepted.
        operation.documentation_error = RuntimeError("unreadable documentation")
        self.check_calls(Agency, None)

    def test_function_documentation_is_preserved(self):
        def Work(tag, agent=None, value=0, *, scale=1):
            """An ordinary documented Operation."""
            return tag, agent, value * scale

        self.check_calls(self.agency(Work), Work.__doc__)

    def test_documentation_interruptions_propagate_unchanged(self):
        for failure in (KeyboardInterrupt("stop"), SystemExit("exit")):
            with self.subTest(failure=type(failure).__name__):
                operation = CallableOperation()
                Agency = self.agency(operation)
                operation.documentation_error = failure
                with self.assertRaises(type(failure)) as raised:
                    Agency(Host())
                self.assertIs(raised.exception, failure)

    def test_missing_documentation_does_not_bypass_rogue_access(self):
        Agency = self.agency(CallableOperation(AttributeError("__doc__")))
        agent = Host()
        Agency(agent)
        captured = agent.Work
        view = Agency[agent]
        captured_view = view.Work
        del Agency[agent]

        self.assertNotIn(agent, Agency[:])
        self.assertIsInstance(agent, Agency)
        for call in (agent.Work, view.Work, captured, captured_view):
            with self.assertRaises(TagRogueAccessError):
                call()
        self.assertEqual(Agency.Work(), (Agency, None, 0))

        Agency(agent)
        self.assertIn(agent, Agency[:])
        self.assertEqual(captured(3), (Agency, agent, 3))

    def test_missing_documentation_does_not_bypass_postconditions(self):
        Agency = self.agency(CallableOperation(AttributeError("__doc__")))

        class Promise(Tag):
            @Post
            def Ready(agent):
                return agent.ready

        agent = Host()
        agent.ready = True
        Promise(agent)
        Agency(agent)
        captured = agent.Work
        view = Agency[agent]
        captured_view = view.Work
        agent.ready = False

        self.assertIn(agent, Agency[:])
        self.assertIn(agent, Agency)
        for call in (agent.Work, view.Work, captured, captured_view):
            with self.assertRaises(Postcondition.Ready):
                call()
        self.assertEqual(Agency.Work(), (Agency, None, 0))

        agent.ready = True
        self.assertEqual(captured(3), (Agency, agent, 3))

    def test_operation_body_errors_are_not_metadata_errors(self):
        failure = ValueError("operation failed")

        def Work(tag, agent=None):
            raise failure

        Agency = self.agency(Work)
        agent = Host()
        Agency(agent)
        captured = agent.Work
        for call in (Agency.Work, agent.Work, Agency[agent].Work, captured):
            with self.assertRaises(ValueError) as raised:
                call()
            self.assertIs(raised.exception, failure)


if __name__ == "__main__":
    unittest.main()
