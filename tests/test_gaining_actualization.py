"""A Gain is acquired only with the runtime protection it requires."""

import unittest

from TopKit import (Action, Constant, Contract, Imprint, Operation, Post, Public,
                    Record, Report, Secret, Tag,
                    TagCompositionError, TagResolutionError)


class GainingActualizationTests(unittest.TestCase):
    def assert_not_admitted(self, tag, agent):
        self.assertNotIn(agent, tag)
        self.assertNotIn(agent, tag[:])
        self.assertFalse(isinstance(agent, tag))
        with self.assertRaises(TagResolutionError):
            tag[agent]

    def test_a_rejected_guard_leaves_earlier_gains_but_no_new_binding(self):
        for modifier, kind in ((Secret, Record), (Secret, Action),
                               (Constant, Record), (Constant, Action)):
            with self.subTest(modifier=modifier.__name__, kind=kind.__name__):
                events = []

                class RejectingHostType(type):
                    reject = True

                    def __new__(meta, name, bases, namespace):
                        if meta.reject and "guarded" in namespace:
                            raise TypeError("guarded runtime refused")
                        return super().__new__(meta, name, bases, namespace)

                class Host(metaclass=RejectingHostType):
                    pass

                class Trained(Tag):
                    @Record
                    def earlier(agent):
                        events.append("earlier")
                        return False

                    @Action
                    def Read(agent):
                        return agent.earlier

                    @modifier
                    @kind
                    def guarded(agent):
                        if kind is Record:
                            events.append("guarded")
                        return "protected value"

                    @Record
                    def later(agent):
                        events.append("later")
                        return "completed"

                    @Action
                    def ReadGuarded(agent):
                        return agent.guarded() if kind is Action else agent.guarded

                agent = Host()
                with self.assertRaises(TagCompositionError):
                    Trained(agent)

                self.assert_not_admitted(Trained, agent)
                self.assertTrue("earlier" @ agent)
                self.assertTrue("Read" @ agent)
                self.assertIs(agent.Read(), False)
                self.assertFalse("guarded" @ agent)
                with self.assertRaises(AttributeError):
                    agent.guarded
                self.assertFalse("later" @ agent)
                expected = ["earlier", "guarded"] if kind is Record else ["earlier"]
                self.assertEqual(events, expected)

                # A failed guard must not leave an acquired Constant or a
                # hidden binding that prevents this fresh Tagging attempt.
                RejectingHostType.reject = False
                Trained(agent)
                self.assertIn(agent, Trained[:])
                self.assertEqual(agent.later, "completed")
                self.assertEqual(agent.ReadGuarded(), "protected value")
                if modifier is Secret:
                    self.assertFalse("guarded" @ agent)
                    with self.assertRaises(AttributeError):
                        agent.guarded
                else:
                    self.assertTrue("guarded" @ agent)
                    value = agent.guarded() if kind is Action else agent.guarded
                    self.assertEqual(value, "protected value")
                    with self.assertRaises(TagCompositionError):
                        agent.guarded = "replacement"

    def test_a_rejected_constant_gain_restores_an_existing_false_or_none_binding(self):
        for original, source in ((False, "host"), (None, "host"),
                                 (False, "TOP"), (None, "TOP")):
            with self.subTest(original=original, source=source):
                class RejectingHostType(type):
                    def __new__(meta, name, bases, namespace):
                        if "value" in namespace:
                            raise TypeError("Constant runtime refused")
                        return super().__new__(meta, name, bases, namespace)

                class Host(metaclass=RejectingHostType):
                    pass

                class Existing(Tag):
                    @Record
                    def value(agent):
                        return original

                class Trained(Tag):
                    @Record
                    def earlier(agent):
                        return "acquired"

                    @Constant
                    @Record
                    def value(agent, stored):
                        self.assertIs(stored, original)
                        return "candidate"

                agent = Host()
                if source == "TOP":
                    Existing(agent)
                else:
                    agent.value = original
                with self.assertRaises(TagCompositionError):
                    Trained(agent)

                self.assert_not_admitted(Trained, agent)
                self.assertEqual(agent.earlier, "acquired")
                self.assertTrue("value" @ agent)
                self.assertIs(agent.value, original)
                if source == "TOP":
                    self.assertIn(agent, Existing[:])
                    self.assertIs(Existing[agent].value, original)
                agent.value = "ordinary host write"
                self.assertEqual(agent.value, "ordinary host write")

    def test_a_rejected_post_is_not_acquired_and_later_actions_do_not_arrive(self):
        events = []

        class RejectingHostType(type):
            def __new__(meta, name, bases, namespace):
                if "__bool__" in namespace:
                    raise TypeError("Post runtime refused")
                return super().__new__(meta, name, bases, namespace)

        class Host(metaclass=RejectingHostType):
            pass

        class Trained(Tag):
            @Record
            def earlier(agent):
                return None

            @Post
            def Ready(agent):
                events.append("post")
                return False

            @Action
            def Launch(agent):
                return "not reached"

        agent = Host()
        with self.assertRaises(TagCompositionError):
            Trained(agent)

        self.assert_not_admitted(Trained, agent)
        self.assertTrue("earlier" @ agent)
        self.assertIsNone(agent.earlier)
        with self.assertRaises(AttributeError):
            agent.Ready
        self.assertFalse("Launch" @ agent)
        Contract.Postconditions(agent)
        self.assertEqual(events, [])

    def test_rejected_publication_replacement_restores_the_prior_binding_for_retry(self):
        stored_values = []

        class RejectingHostType(type):
            reject = False

            def __new__(meta, name, bases, namespace):
                if meta.reject and "__len__" in namespace and "title" not in namespace:
                    raise TypeError("removing the published descriptor is refused")
                return super().__new__(meta, name, bases, namespace)

        class Host(metaclass=RejectingHostType):
            pass

        class Existing(Tag):
            @Public
            @Report
            def title(tag):
                return "published"

        class Trained(Tag):
            @Action
            def __len__(agent):
                return 7

            @Record
            def title(agent, stored):
                stored_values.append(stored)
                return False

        agent = Host()
        Existing(agent)
        RejectingHostType.reject = True
        with self.assertRaises(TagCompositionError):
            Trained(agent)

        self.assert_not_admitted(Trained, agent)
        self.assertIn(agent, Existing[:])
        self.assertTrue("__len__" @ agent)
        self.assertEqual(len(agent), 7)
        self.assertEqual(agent.title, "published")
        self.assertEqual(Existing[agent].title, "published")
        self.assertEqual(stored_values, [None])

        RejectingHostType.reject = False
        Trained(agent)
        self.assertIn(agent, Trained[:])
        self.assertIs(agent.title, False)
        self.assertEqual(stored_values, [None, None])

    def test_a_failed_guard_preserves_an_existing_tags_protected_bindings(self):
        class RejectingHostType(type):
            def __new__(meta, name, bases, namespace):
                if "rejected" in namespace:
                    raise TypeError("new Constant runtime refused")
                return super().__new__(meta, name, bases, namespace)

        class Host(metaclass=RejectingHostType):
            pass

        class Base(Tag):
            @Secret
            @Record
            def hidden(agent):
                return None

            @Action
            def Read(agent):
                return agent.hidden

            @Constant
            @Record
            def fixed(agent):
                return False

        class Shape(Base):
            @Record
            def earlier(agent):
                return "acquired"

            @Constant
            @Record
            def rejected(agent):
                return "candidate"

        agent = Host()
        Base(agent)
        with self.assertRaises(TagCompositionError):
            Shape(agent)

        self.assert_not_admitted(Shape, agent)
        self.assertIn(agent, Base[:])
        self.assertIsNone(agent.Read())
        self.assertIs(Base[agent].fixed, False)
        with self.assertRaises(AttributeError):
            agent.hidden
        self.assertIs(agent.fixed, False)
        with self.assertRaises(TagCompositionError):
            agent.fixed = "replacement"
        with self.assertRaises(TagCompositionError):
            object.__setattr__(agent, "fixed", "replacement")
        self.assertEqual(agent.earlier, "acquired")
        self.assertFalse("rejected" @ agent)
        with self.assertRaises(AttributeError):
            agent.rejected

    def test_a_rejected_service_runtime_preserves_predecessor_services_and_training_gains(self):
        events = []

        class RejectingHostType(type):
            def __new__(meta, name, bases, namespace):
                if "rejected" in namespace:
                    raise TypeError("new published runtime refused")
                return super().__new__(meta, name, bases, namespace)

        class Host(metaclass=RejectingHostType):
            pass

        class Existing(Tag):
            @Public
            @Report
            def title(tag):
                return "existing"

            @Public
            @Operation
            def Signal(tag, agent):
                return "existing"

        class Candidate(Existing):
            @Record
            def gained(agent):
                return None

            @Action
            def ReadGained(agent):
                return agent.gained

            @Public
            @Report
            def title(tag):
                return "candidate"

            @Public
            @Operation
            def Signal(tag, agent):
                return "candidate"

            @Public
            @Operation
            def CandidateOnly(tag, agent):
                return "candidate only"

            @Public
            @Report
            def rejected(tag):
                return "not acquired"

            @Imprint
            def Train(agent):
                events.append((agent.title, agent.Signal()))

        agent = Host()
        Existing(agent)
        with self.assertRaises(TagCompositionError):
            Candidate(agent)

        self.assert_not_admitted(Candidate, agent)
        self.assertIn(agent, Existing[:])
        self.assertTrue("gained" @ agent)
        self.assertTrue("ReadGained" @ agent)
        self.assertIsNone(agent.ReadGained())
        self.assertEqual(events, [("existing", "existing")])
        self.assertEqual(agent.title, "existing")
        self.assertEqual(agent.Signal(), "existing")
        self.assertFalse("rejected" @ agent)
        self.assertFalse("CandidateOnly" @ agent)
        with self.assertRaises(AttributeError):
            agent.rejected
        with self.assertRaises(AttributeError):
            agent.CandidateOnly


if __name__ == "__main__":
    unittest.main()
