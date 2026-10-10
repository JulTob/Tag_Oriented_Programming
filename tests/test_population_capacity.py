"""Expression depth must not change lazy population evaluation semantics."""

import gc
import random
import sys
import unittest
import weakref

from TopKit import Post, Tag, TagPostconditionError
from TopKit.fields import _Combined, _Population, _population_of


class Agent:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        raise AssertionError("population identity must not call equality")

    __hash__ = None


class Recursive(_Population):
    """Independent reference to the previous recursive evaluation rules."""

    def __init__(self, left, right, operator):
        self.left, self.right, self.operator = left, right, operator

    def __iter__(self):
        left, right = self.left, self.right
        if self.operator == "|":
            seen = {}
            for agent in left:
                seen[id(agent)] = agent
                yield agent
            for agent in right:
                if seen.get(id(agent)) is not agent:
                    yield agent
        elif self.operator == "&":
            for agent in left:
                if agent in right:
                    yield agent
        else:
            for agent in left:
                if agent not in right:
                    yield agent

    def __contains__(self, agent):
        left, right = self.left, self.right
        if self.operator == "|":
            return agent in left or agent in right
        if self.operator == "&":
            return agent in left and agent in right
        return agent in left and agent not in right


class TraceLeaf(_Population):
    def __init__(self, label, members, events):
        self._label, self.members, self.events = label, list(members), events

    def __iter__(self):
        self.events.append(("start", self._label))
        held = tuple(self.members)

        def walk():
            try:
                for agent in held:
                    self.events.append(("turn", self._label, agent.name))
                    if any(member is agent for member in self.members):
                        yield agent
            finally:
                self.events.append(("close", self._label))

        return walk()

    def __contains__(self, agent):
        self.events.append(("in", self._label, agent.name))
        return any(member is agent for member in self.members)


def expression(kind, shape, leaves):
    if isinstance(shape, str):
        return leaves[shape]
    left, operator, right = shape
    return kind(expression(kind, left, leaves), expression(kind, right, leaves), operator)


class PopulationCapacityTests(unittest.TestCase):
    def trace(self, kind, shape, operation):
        agents = {name: Agent(name) for name in "abcd"}
        events = []
        leaves = {
            "A": TraceLeaf("A", [agents["a"], agents["b"], agents["a"]], events),
            "B": TraceLeaf("B", [agents["b"], agents["c"]], events),
            "C": TraceLeaf("C", [agents["a"], agents["c"]], events),
            "D": TraceLeaf("D", [], events),
        }
        population = expression(kind, shape, leaves)
        if operation == "walk":
            result = [agent.name for agent in population]
        elif operation == "bool":
            result = bool(population)
        elif operation == "len":
            result = len(population)
        else:
            result = agents[operation] in population
        return result, events

    def test_shallow_expressions_match_recursive_results_and_event_traces(self):
        randomizer = random.Random(100)

        def shape(depth):
            if depth == 0 or randomizer.randrange(4) == 0:
                return randomizer.choice("ABCD")
            return shape(depth - 1), randomizer.choice("|&-"), shape(depth - 1)

        for case in range(60):
            tree = (shape(3), randomizer.choice("|&-"), shape(3))
            for operation in ("walk", "len", "bool", "a", "b", "c", "d"):
                with self.subTest(case=case, operation=operation):
                    self.assertEqual(self.trace(_Combined, tree, operation),
                                     self.trace(Recursive, tree, operation))

    def test_mutations_between_turns_keep_leaf_start_timing(self):
        def trace(kind):
            agents = {name: Agent(name) for name in "abcd"}
            events = []
            leaves = {
                "A": TraceLeaf("A", [agents["a"], agents["b"]], events),
                "B": TraceLeaf("B", [agents["b"]], events),
                "C": TraceLeaf("C", [agents["a"], agents["b"], agents["c"]], events),
                "D": TraceLeaf("D", [], events),
            }
            tree = ((("A", "|", "B"), "&", "C"), "|", "D")
            iterator = iter(expression(kind, tree, leaves))
            result = [next(iterator).name]
            leaves["A"].members = [agents["a"], agents["d"]]
            leaves["B"].members.append(agents["c"])
            leaves["D"].members.extend([agents["c"], agents["d"]])
            result.extend(agent.name for agent in iterator)
            return result, events

        self.assertEqual(trace(_Combined), trace(Recursive))

    def test_postcondition_evaluation_counts_and_mutation_match_reference(self):
        def trace(kind):
            events = []

            class Left(Tag):
                pass

            class Right(Tag):
                @Post
                def Ready(agent):
                    events.append(agent.name)
                    if agent.name == "b" and agent in Left:
                        del Left[agent]
                    return agent.name != "c"

            agents = [Agent(name) for name in "abc"]
            for agent in agents:
                Left(agent)
                try:
                    Right(agent)
                except TagPostconditionError.Ready:
                    pass
            events.clear()
            leaves = {"A": Left[:], "B": _population_of(Right),
                      "C": Right[:], "D": _population_of(Left)}
            tree = (("A", "&", "B"), "|", ("C", "-", "D"))
            population = expression(kind, tree, leaves)
            walked = [agent.name for agent in population]
            return walked, events, [agent.name for agent in Left[:]]

        self.assertEqual(trace(_Combined), trace(Recursive))

    def test_suspension_close_and_throw_match_recursive_leaf_events(self):
        def trace(kind, close):
            events = []
            agent = Agent("a")
            leaves = {name: TraceLeaf(name, [agent], events) for name in "ABC"}
            iterator = iter(expression(kind, ("A", "|", ("B", "&", "C")), leaves))
            self.assertEqual(events, [])
            self.assertIs(next(iterator), agent)
            before = list(events)
            if close:
                iterator.close()
            else:
                with self.assertRaises(LookupError):
                    iterator.throw(LookupError("stop"))
            return before, events

        for close in (True, False):
            with self.subTest(close=close):
                self.assertEqual(trace(_Combined, close), trace(Recursive, close))

    def test_deep_left_right_mixed_and_right_difference_trees(self):
        class Full(Tag):
            pass

        class Empty(Tag):
            pass

        full, empty = Full[:], Empty[:]
        agents = [Agent(name) for name in "abc"]
        absent = Agent("absent")
        for agent in agents:
            Full(agent)
        depth = 1200
        for topology in ("left", "right", "mixed", "right difference"):
            with self.subTest(topology=topology):
                population = empty if topology == "right difference" else full
                for level in range(depth):
                    if topology == "left":
                        population = _Combined(population, empty, "|")
                    elif topology == "right":
                        population = _Combined(empty, population, "|")
                    elif topology == "right difference":
                        population = _Combined(full, population, "-")
                    elif level % 3 == 0:
                        population = _Combined(population, full, "&")
                    elif level % 3 == 1:
                        population = _Combined(empty, population, "|")
                    else:
                        population = _Combined(population, empty, "-")
                expected = [] if topology == "right difference" else agents
                previous_limit = sys.getrecursionlimit()
                try:
                    sys.setrecursionlimit(300)
                    self.assertEqual(bool(population), bool(expected))
                    self.assertEqual(len(population), len(expected))
                    self.assertEqual([id(agent) for agent in population],
                                     [id(agent) for agent in expected])
                    self.assertEqual(agents[0] in population, bool(expected))
                    self.assertNotIn(absent, population)
                finally:
                    sys.setrecursionlimit(previous_limit)

    def test_union_ownership_is_iterator_local_and_released_on_close(self):
        class Left(Tag):
            pass

        class Right(Tag):
            pass

        class Empty(Tag):
            pass

        left, right, empty = Left[:], Right[:], Empty[:]
        first, second = Agent("a"), Agent("b")
        Left(first)
        Right(first)
        Right(second)
        population = _Combined(_Combined(left, empty, "|"), right, "|")
        iterator = iter(population)
        self.assertIs(next(iterator), first)
        reference = weakref.ref(first)
        del Left[first]
        del Right[first]
        del first
        gc.collect()
        self.assertIsNotNone(reference())
        self.assertIs(next(iterator), second)
        self.assertIsNotNone(reference())
        iterator.close()
        gc.collect()
        self.assertIsNone(reference())
        del second
        gc.collect()
        self.assertFalse(population)

    def test_finished_filtered_branches_release_agents_before_the_next_leaf_starts(self):
        def trace(kind):
            class Left(Tag):
                pass

            class Right(Tag):
                pass

            class Empty(Tag):
                pass

            left, right, empty = Left[:], Right[:], Empty[:]
            held = {"agent": Agent("a")}
            reference = weakref.ref(held["agent"])
            Left(held["agent"])
            Right(held["agent"])

            class Reject(_Population):
                def __contains__(self, agent):
                    del Left[agent]
                    held.clear()
                    return False

            child = kind(kind(left, empty, "|"), Reject(), "&")
            iterator = iter(kind(child, right, "|"))
            result = [agent.name for agent in iterator]
            gc.collect()
            return result, reference() is None

        self.assertEqual(trace(_Combined), trace(Recursive))
        self.assertEqual(trace(_Combined), ([], True))

    def test_combined_subclass_overrides_remain_leaf_operations(self):
        events = []
        agent = Agent("a")
        leaf = TraceLeaf("A", [agent], events)

        class Custom(_Combined):
            def __iter__(self):
                events.append(("custom walk",))
                return super().__iter__()

            def __contains__(self, agent):
                events.append(("custom in",))
                return super().__contains__(agent)

        population = _Combined(Custom(leaf, leaf, "|"), leaf, "&")
        self.assertEqual([id(member) for member in population], [id(agent)])
        self.assertIn(agent, population)
        self.assertIn(("custom walk",), events)
        self.assertIn(("custom in",), events)

    def test_combined_subclass_descriptors_are_bound_only_to_instances(self):
        def trace(kind, operation):
            events = []
            agent = Agent("a")
            leaf = TraceLeaf("A", [agent], events)

            class InstanceOnly:
                def __init__(self, name, function):
                    self.name, self.function = name, function

                def __get__(self, instance, owner=None):
                    if instance is None:
                        raise RuntimeError("class lookup is forbidden")
                    events.append(("bind", self.name))
                    return self.function(instance)

            class Custom(_Combined):
                __iter__ = InstanceOnly("walk", lambda instance: lambda: iter((agent,)))
                __contains__ = InstanceOnly("in", lambda instance: lambda candidate: True)

            population = kind(Custom(leaf, leaf, "|"), leaf, "&")
            if operation == "walk":
                result = [member.name for member in population]
            else:
                result = agent in population
            return result, events

        for operation in ("walk", "in"):
            with self.subTest(operation=operation):
                self.assertEqual(trace(_Combined, operation), trace(Recursive, operation))

    def test_leaf_classification_does_not_probe_an_instances_class_hook(self):
        events = []
        agent = Agent("a")

        class InstanceOnly(TraceLeaf):
            def __getattribute__(self, name):
                if name == "__class__":
                    raise RuntimeError("instance class probing is forbidden")
                return object.__getattribute__(self, name)

        leaf = InstanceOnly("A", [agent], events)
        population = _Combined(leaf, leaf, "&")
        self.assertEqual([member.name for member in population], ["a"])
        self.assertIn(agent, population)


if __name__ == "__main__":
    unittest.main()
