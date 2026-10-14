"""Conformance tests: efficiency."""

from __future__ import annotations

import gc
import unittest
import warnings
import weakref
from TopKit import Flag
from TopKit import Form
from TopKit import Keyword
from TopKit import Outline
from TopKit import Post
from TopKit import Pre
from TopKit import Record
from TopKit import Tag
from TopKit import TagOverwriteWarning
from TopKit import TagPostconditionError
from TopKit import Tags
from TopKit import Underlay

from ._fixtures import Agent
from ._fixtures import Bridge
from ._fixtures import Combatant
from ._fixtures import Elf
from ._fixtures import Left
from ._fixtures import Person
from ._fixtures import Right
from ._fixtures import Root
from ._fixtures import Run_Program


class EfficiencyTests(unittest.TestCase):
    """What the kit keeps and what it answers, after the performance work:
    no memory that grows with repetition, and every shortcut answering
    exactly what the long way answered."""

    def test_a_reapplied_postcondition_keeps_nothing_per_turn(self) -> None:
        import tracemalloc

        class Guarded(Tag):
            @Post
            def Fine(agent) -> bool:
                return True

        ari = Agent()
        Guarded(ari)
        del Guarded[ari]
        gc.collect()
        tracemalloc.start()
        before, _peak = tracemalloc.get_traced_memory()

        for _ in range(500):
            Guarded(ari)
            del Guarded[ari]

        gc.collect()
        after, _peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.assertLess((after - before) / 500, 64)   # was about 800 B per turn

    def test_a_dropped_tag_class_is_freed(self) -> None:
        def Make() -> weakref.ref:
            class Temporary(Tag):
                @Record
                def x(agent) -> int:
                    return 1

            ari = Agent()
            Temporary(ari)
            del Temporary[ari]

            return weakref.ref(Temporary)

        reference = Make()
        gc.collect()

        self.assertIsNone(reference())

    def test_a_ripped_tag_leaves_no_view_behind(self) -> None:
        class Payload:
            pass

        class Carrier(Tag):
            @Record
            def payload(agent) -> Payload:
                return Payload()

        ari = Agent()
        Carrier(ari)
        first = weakref.ref(ari.payload)
        ari.payload = None                             # the Agent lets go of it

        self.assertIs(ari.Carrier.payload, first())    # the view still shows it

        del Carrier[ari]
        gc.collect()

        self.assertIsNone(first())                     # the view left with the membership

        Carrier(ari)
        self.assertIs(ari.Carrier.payload, ari.payload)   # a fresh view, taken now

    def test_a_gate_does_not_repeat_a_warning_once_given(self) -> None:
        class Base(Tag):
            def Attack(agent) -> str:
                return "base"

        class Gated(Tag):
            @Pre
            def Ready(agent) -> bool:
                return True

        class Rival(Tag):
            def Attack(agent) -> str:
                return "rival"

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("default")

            for _ in range(5):
                hero = Agent()
                Base(hero)
                Gated(hero)
                Rival(hero)   # replaces an independent Tag's Action: warned once per place

        overwrites = [w for w in caught if issubclass(w.category, TagOverwriteWarning)]

        self.assertEqual(len(overwrites), 1)

    def test_population_cardinality_tracks_sound_and_broken_members(self) -> None:
        class Fighter(Tag):
            @Post
            def Armed(agent) -> bool:
                return agent.ready

        self.assertEqual(len(Fighter), 0)
        self.assertFalse(~Fighter)

        broken = Agent()
        Fighter(broken)
        broken.ready = False

        self.assertEqual(len(Fighter), 0)   # nobody sound
        self.assertTrue(~Fighter)          # someone broken

        sound = Agent()
        Fighter(sound)

        self.assertGreater(len(Fighter), 0)
        self.assertEqual(list(Fighter), [sound])

        del sound
        gc.collect()

        self.assertEqual(len(Fighter), 0)

    def test_an_underlay_called_with_or_without_arguments(self) -> None:
        class Speaker(Tag):
            def Say(agent, word: str = "hello") -> str:
                return word

        class Echo(Speaker):
            @Underlay
            def Say(agent, base, word: str = "hello") -> str:
                return base() + "|" + base("again") + "|" + base(word="named")

        ari = Agent()
        Echo(ari)

        self.assertEqual(ari.Say(), "hello|again|named")
        self.assertEqual(ari.Say("hi"), "hi|again|named")
        self.assertEqual(ari.Say(word="yo"), "yo|again|named")

    def test_leaves_keep_application_order(self) -> None:
        ari = Agent()
        Combatant(ari)
        Elf(ari)
        Bridge(ari)

        self.assertEqual(Tags(ari), (Combatant, Elf, Bridge))
        self.assertEqual(
                Outline(ari),
                "Agent\n  Combatant\n  Person\n    Elf\n  Root\n    Left\n      Right\n        Bridge",
                )

    def test_leaves_are_the_tags_nothing_active_specializes(self) -> None:
        import random

        family = (Root, Left, Right, Bridge, Person, Elf, Combatant)
        chance = random.Random(1701)

        for _ in range(300):
            agent = Agent()
            active: list[type] = []

            for tag in chance.sample(family, chance.randint(1, len(family))):
                tag(agent)

                for member in Form(tag):
                    if member not in active:
                        active.append(member)

            pairwise = tuple(
                    candidate
                    for candidate in active
                    if not any(
                            other is not candidate and issubclass(other, candidate)
                            for other in active
                            )
                    )

            self.assertEqual(Tags(agent), pairwise)

    def test_reapplying_an_active_form_changes_nothing(self) -> None:
        ari = Agent()
        Elf(ari)
        before = (type(ari), dict(vars(ari)))

        self.assertIs(Elf(ari), ari)
        self.assertEqual((type(ari), dict(vars(ari))), before)

    def test_words_follow_a_flag_declared_after_use(self) -> None:
        class Wolfish(Tag):
            pass

        ari = Agent()
        Wolfish(ari)
        self.assertFalse(Keyword(ari, "Wolf"))   # the words are gathered here

        Flag("Wolf")(Wolfish)

        self.assertTrue(Keyword(ari, "Wolf"))    # and gathered again, not stale

    def test_at_exit_runs_every_registration_in_order(self) -> None:
        lines, stderr = Run_Program(
                """
from TopKit import Tag, Rip, At_Exit

class Door:
    def __init__(self, name): self.name = name

class Second(Tag):
    @Rip
    def Stand_Down(agent): print(agent.name, "second")

class First(Tag):
    @Rip
    def Down(agent):
        print(agent.name, "first")
        Second(agent)                         # leaving, it takes another Tag
        late = Door("late"); Second(late); keep.append(late)
        At_Exit(late)                         # registered while the exit pass runs

keep = []
ari = Door("ari"); First(ari)
At_Exit(ari)
At_Exit(ari)                                  # a second registration is its own pass
print("end")
""",
                )

        self.assertEqual(
                lines,
                ["end", "ari first", "ari second", "late second"],
                )
        self.assertEqual(stderr, "")

    def test_an_underlay_is_the_same_callable_with_or_without_arguments(self) -> None:
        seen: list[str] = []

        class Speaker(Tag):
            def Say(agent, word: str = "hello") -> str:
                return word

        class Echo(Speaker):
            @Underlay
            def Say(agent, base, word: str = "hello") -> str:
                seen.append(base.__name__)
                return base()

        ari = Agent()
        Echo(ari)
        ari.Say()
        ari.Say("hi")

        self.assertEqual(seen, ["prior", "prior"])

    def test_the_root_tag_is_never_a_leaf_beside_another_tag(self) -> None:
        class Wizard(Tag):
            pass

        ari = Agent()
        Tag(ari)
        Wizard(ari)

        self.assertEqual(Tags(ari), (Wizard,))

    def test_form_of_a_class_writes_nothing_into_it(self) -> None:
        class Plain:
            pass

        before = set(vars(Plain))

        self.assertEqual(Form(Plain), (Plain,))
        self.assertEqual(Form(int), (int,))
        self.assertEqual(set(vars(Plain)), before)

        with self.assertRaises(TypeError):
            Form(None)

    def test_a_renamed_flag_answers_to_its_new_name(self) -> None:
        @Flag("Wolf")
        class Werewolf(Tag):
            pass

        ari = Agent()
        Werewolf(ari)
        self.assertIn("Werewolf", ari)

        Werewolf.__name__ = "Lycan"

        self.assertIn("Lycan", ari)
        self.assertNotIn("Werewolf", ari)
        self.assertIn("Wolf", ari)

    def test_population_cardinality_agrees_with_its_walk(self) -> None:
        keep: dict[str, object] = {}

        class Enemy(Tag):
            @Post
            def Standing(agent) -> bool:
                if agent.name == "a":
                    keep.pop("b", None)    # a check that frees another member
                    return False

                return True

        for name in ("a", "b"):
            member = Agent()
            member.name = name
            keep[name] = member

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                try:
                    Enemy(member)
                except TagPostconditionError:
                    pass

        del member                         # keep["b"] is b's last reference
        count = len(Enemy)

        self.assertEqual(count, 1)         # b was a member when the question began
