"""Link Contributions accept callable objects without function metadata."""

from inspect import Parameter, Signature
import unittest

from TopKit import Constant, Link, Operation, Public, Record, Report, Rip, Secret, Tag
from TopKit import TagCompositionError


class Host:
    pass


class _Callable:
    def __init__(self, body, seats, hostile=False):
        self.body = body
        self.hostile = hostile
        self.__signature__ = Signature([
            Parameter(name, Parameter.POSITIONAL_OR_KEYWORD) for name in seats
        ])

    def __getattribute__(self, name):
        if name in ("__name__", "__qualname__", "__doc__", "__module__", "__dict__"):
            if object.__getattribute__(self, "hostile"):
                raise AssertionError("optional callable metadata was read")
        return object.__getattribute__(self, name)

    def __call__(self, *args, **kwargs):
        return self.body(*args, **kwargs)


class LinkCallableTests(unittest.TestCase):
    def test_callable_actions_records_rips_operations_and_reports(self):
        for hostile in (False, True):
            with self.subTest(hostile=hostile):
                events = []

                def pair(body):
                    return _Callable(body, ("agent", "contact"), hostile)

                def shared(body):
                    return _Callable(body, ("link",), hostile)

                operation = Operation(_Callable(lambda link: link, ("link",)))
                operation.__func__.hostile = hostile

                class Social(Tag):
                    @Link
                    class Knows(Tag):
                        Answer = pair(lambda agent, contact: (agent, contact))
                        count = Record(pair(lambda agent, contact: 42))
                        Forget = Rip(pair(lambda agent, contact: events.append((agent, contact))))
                        Owner = operation
                        label = Report(shared(lambda link: link.__name__))

                owner, contact = Host(), Host()
                Social(owner)
                owner.Knows(contact)
                self.assertEqual(owner.Knows[contact].Answer(), (owner, contact))
                self.assertEqual(owner.Knows[contact].count, 42)
                self.assertIs(owner.Knows.Owner(), owner.Knows)
                self.assertEqual(owner.Knows.label, "Knows")
                del owner.Knows[contact]
                self.assertEqual(events, [(owner, contact)])

    def test_callable_rip_failure_names_the_step_and_saves_later_cleanup(self):
        events = []
        cause = ValueError("cannot close")
        blocked = True

        def fail(agent, contact):
            nonlocal blocked
            events.append("first")
            if blocked:
                blocked = False
                raise cause

        class Social(Tag):
            @Link
            class Knows(Tag):
                Close = Rip(_Callable(fail, ("agent", "contact"), True))

                @Rip
                def Later(agent, contact):
                    events.append("later")

        owner, contact = Host(), Host()
        Social(owner)
        owner.Knows(contact)
        with self.assertRaises(TagCompositionError) as failure:
            del owner.Knows[contact]
        self.assertIn("Close", str(failure.exception.__cause__))
        self.assertIs(failure.exception.__cause__.__cause__, cause)
        self.assertEqual(events, ["first"])
        self.assertNotIn(contact, owner.Knows)
        self.assertIn(contact, owner.Knows[...])

        del owner.Knows[contact]
        self.assertEqual(events, ["first", "first", "later"])
        self.assertNotIn(contact, owner.Knows[...])

    def test_slotted_callable_marks_survive_adaptation(self):
        class Value:
            __slots__ = ("__topkit_kind__", "__topkit_constant__")

            def __call__(self, agent, contact):
                return 42

        class Work:
            __slots__ = ()

            def __call__(self, agent, contact):
                return (agent, contact)

        class Social(Tag):
            @Link
            class Knows(Tag):
                count = Constant(Record(Value()))
                Answer = Work()

        owner, contact = Host(), Host()
        Social(owner)
        owner.Knows(contact)
        self.assertEqual(owner.Knows[contact].Answer(), (owner, contact))
        self.assertEqual(owner.Knows[contact].count, 42)
        with self.assertRaises(TagCompositionError):
            owner.Knows[contact].count = 7

    def test_callable_public_and_secret_marks_survive_adaptation(self):
        operation = Operation(_Callable(lambda link: 7, ("link",)))
        operation.__func__.hostile = True

        class Social(Tag):
            @Link
            class Knows(Tag):
                Read = Public(_Callable(lambda agent, contact: 42, ("agent", "contact"), True))
                Hidden = Secret(operation)
                label = Public(Report(_Callable(lambda link: "public", ("link",), True)))

        owner, contact = Host(), Host()
        Social(owner)
        owner.Knows(contact)
        self.assertEqual(contact.Read(), 42)
        self.assertEqual(contact.label, "public")
        with self.assertRaises(AttributeError):
            owner.Knows.Hidden()

    def test_ordinary_reports_accept_the_same_callable_builders(self):
        for hostile in (False, True):
            with self.subTest(hostile=hostile):
                class Book(Tag):
                    title = Report(_Callable(lambda tag: "book", ("tag",), hostile))

                self.assertEqual(Book.title, "book")
                self.assertEqual(repr(vars(Book)["title"]), "<Report title>")


if __name__ == "__main__":
    unittest.main()
