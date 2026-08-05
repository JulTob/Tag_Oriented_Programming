from __future__ import annotations

import gc
import inspect
import operator
import unittest
import warnings
import weakref

from TagKit import Action
from TagKit import Apply
from TagKit import At_Exit
from TagKit import Delete
from TagKit import Has
from TagKit import Imprint
from TagKit import Operation
from TagKit import Post
from TagKit import Postcondition
from TagKit import Pre
from TagKit import Precondition
from TagKit import Record
from TagKit import Report
from TagKit import Rip
from TagKit import Scope
from TagKit import Tag
from TagKit import TagCompositionError
from TagKit import TagContractError
from TagKit import TagContractWarning
from TagKit import TagImprintError
from TagKit import TagOverwriteWarning
from TagKit import TagPostconditionError
from TagKit import TagPreconditionError
from TagKit import TagResolutionError
from TagKit import Tags
from TagKit import Contract
from TagKit import Underlay


class Agent:
    def __init__(
            agent,
            ) -> None:
        agent.events: list[str] = []
        agent.allowed = True
        agent.ready = True
        agent.weapon = "faulty weapon"

    def Attack(
            agent,
            ) -> str:
        return "Faulty OOP attack!"


class Root(Tag):
    @Imprint
    def Mark_Root(
            agent,
            ) -> None:
        agent.events.append("Root")


class Left(Root):
    @Imprint
    def Mark_Left(
            agent,
            ) -> None:
        agent.events.append("Left")


class Right(Root):
    @Imprint
    def Mark_Right(
            agent,
            ) -> None:
        agent.events.append("Right")


class Bridge(Left, Right):
    @Imprint
    def Mark_Bridge(
            agent,
            ) -> None:
        agent.events.append("Bridge")


class Person(Tag):
    def Attack(
            agent,
            ) -> str:
        return "Attack!"


class Elf(Person):
    @Underlay
    def Attack(
            agent,
            underlay,
            ) -> str:
        return (
                "With elven grace "
                + underlay()
                )


class Paladin(Person):
    @Underlay
    def Attack(
            agent,
            underlay,
            ) -> str:
        return (
                underlay()
                + " with a holy oath."
                )


class Berserker(Tag):
    def Attack(
            agent,
            ) -> str:
        return "Reckless attack!"


class Combatant(Tag):
    def Combat(
            agent,
            ) -> str:
        return agent.Attack()


class OOP_Refinement(Tag):
    @Underlay
    def Attack(
            agent,
            underlay,
            ) -> str:
        return (
                "Refined "
                + underlay()
                )


class Inventory(Tag):
    @Record
    def items(
            agent,
            ) -> list[str]:
        return []


class Armed(Tag):
    @Record
    def weapon(
            agent,
            ) -> str:
        return "arcane staff"


class Prepared(Inventory):
    @Record
    @Underlay
    def items(
            agent,
            underlay,
            ) -> list[str]:
        return (
                underlay()
                + ["rope"]
                )


class Lost_Inventory(Prepared):
    @Delete
    def items(
            agent,
            ) -> None:
        pass


class Needs_Inventory_Underlay(Lost_Inventory):
    @Record
    @Underlay
    def items(
            agent,
            underlay,
            ) -> list[str]:
        return underlay()


class Rebuilt_Inventory(Lost_Inventory):
    @Record
    def items(
            agent,
            ) -> list[str]:
        return ["shield"]


class Pacifist(Tag):
    @Delete
    def Attack(
            agent,
            ) -> None:
        pass

    @Delete
    def weapon(
            agent,
            ) -> None:
        pass


class Needs_Action_Underlay(Pacifist):
    @Underlay
    def Attack(
            agent,
            underlay,
            ) -> str:
        return underlay()


class Repaired_Pacifist(Pacifist):
    def Attack(
            agent,
            ) -> str:
        return "Defensive action!"

    @Record
    def weapon(
            agent,
            ) -> str:
        return "shield"


class Species(Tag):
    @Imprint
    def Establish_Species(
            agent,
            ) -> None:
        agent.events.append("Species")


class Human(Species):
    @Precondition
    def Has_Birthplace(
            agent,
            ) -> bool:
        return hasattr(
                agent,
                "birthplace",
                )


class Validated(Tag):
    @Precondition
    def Is_Allowed(
            agent,
            ) -> bool:
        return agent.allowed

    @Postcondition
    def Is_Ready(
            agent,
            ) -> bool:
        return agent.ready


class Advanced(Validated):
    pass


class Exempt(Validated):
    @Delete
    def Is_Allowed(
            agent,
            ) -> None:
        pass

    @Delete
    def Is_Ready(
            agent,
            ) -> None:
        pass


class Candidate_Record(Tag):
    @Record
    def token(
            agent,
            ) -> str:
        return "prepared"

    @Postcondition
    def Accepts_Token(
            agent,
            ) -> bool:
        return agent.ready


class Ordered_Imprints(Tag):
    @Imprint
    def First(
            agent,
            ) -> None:
        agent.events.append("First")

    @Imprint
    def Second(
            agent,
            ) -> None:
        agent.events.append("Second")


class Stocked(Tag):
    @Imprint
    def Note_Stocking(
            agent,
            ) -> None:
        agent.events.append("Stocked")

    @Record
    def supplies(
            agent,
            ) -> list[str]:
        return ["ration"]


class Broken_Imprint(Tag):
    @Imprint
    def Begin_Then_Fail(
            agent,
            ) -> None:
        agent.events.append("before failure")

        raise RuntimeError("expected imprint failure")


class Community(Tag):
    colour = Report("green")

    @Operation
    def Greet(
            tag,
            name: str,
            ) -> str:
        return f"{tag.__name__}:{name}"


class Silent_Community(Community):
    @Delete
    def colour(
            agent,
            ) -> None:
        pass

    @Delete
    def Greet(
            agent,
            ) -> None:
        pass


class Missing_Action(Tag):
    @Underlay
    def Missing(
            agent,
            underlay,
            ) -> str:
        return underlay()


class Arithmetic(Tag):
    def __add__(
            agent,
            amount: int,
            ) -> int:
        return amount + 1


class Field_Member(Tag):
    pass


class Territory(Tag):
    @Record
    def banner(
            agent,
            ) -> str:
        return "raised"


class Citadel(Territory):
    @Precondition
    def Has_Charter(
            agent,
            ) -> bool:
        return hasattr(
                agent,
                "charter",
                )


class Cursed_Blade(Tag):
    @Record
    def weapon(
            agent,
            ) -> str:
        return "cursed dagger"

    @Postcondition
    def Is_Worthy(
            agent,
            ) -> bool:
        return agent.ready


class Squire(Tag):
    @Imprint
    def Enlist(
            agent,
            ) -> None:
        agent.events.append("Squire")

    @Record
    def rank(
            agent,
            ) -> str:
        return "squire"


class Knighted(Tag):
    @Imprint
    def Knight(
            agent,
            ) -> None:
        agent.events.append("Knighted")

    @Action
    @Rip
    def rank_reset(
            agent,
            ) -> str:
        agent.rank = None

        return "Disrobed"


class Beast(Tag):
    @Record
    def legs(
            agent,
            ) -> int:
        return 4


class Wolf(Beast):
    @Record
    def howl(
            agent,
            ) -> str:
        return "Awooo"


class Base_Greeting(Tag):
    def Greet(
            agent,
            ) -> str:
        return "hi"


class Greeter(Base_Greeting):
    @Action
    @Underlay
    def Greet(
            agent,
            base,
            ) -> str:
        return "Hello and " + base()


class Politely(Greeter):
    @Action
    @Underlay
    def Greet(
            agent,
            prior,
            ) -> str:
        return prior() + " good day"


class Tally(Tag):
    @Record
    def marks(
            agent,
            ) -> list[str]:
        return ["one"]


class More_Tally(Tally):
    @Record
    @Underlay
    def marks(
            agent,
            existing,
            ) -> list[str]:
        return existing() + ["two"]


class Slotted_Agent:
    __slots__ = ()


# Exit-protocol fixtures. A @Rip teardown records to an external log,
# because the meaning of teardown on destruction is its outside-world
# side effect, not a mutation of the dying Agent.
_DEL_LOG: list[str] = []


class Sentry(Tag):
    @Action
    @Rip
    def stand_down(
            agent,
            ) -> str:
        _DEL_LOG.append("stood down")

        return "stood down"


class Recruit(Tag):
    # First parameter named 'spy', not 'agent': the Agent binding is
    # positional discipline, never a reserved word. 'code' is an application
    # input passed by name.
    @Imprint
    def assign(
            spy,
            code,
            ) -> None:
        spy.code = code


class Coded(Tag):
    @Precondition
    def Has_Code(
            agent,
            code,
            ) -> bool:
        return code is not None


class Scholar(Tag):
    @Pre
    def Level_Over_Zero(agent):
        assert agent.level > 0          # assert-style precondition

    @Imprint
    def Grant_Book(agent):
        agent.spellbook = "Tome"

    @Post
    def Has_Book(agent):
        assert agent.spellbook          # assert-style postcondition, bare


class Capped(Tag):
    @Post
    def Strength_Capped(agent):
        return agent.strength <= 20


class Bruiser(Capped):
    @Post
    def Strength_Capped(agent):         # crunch WITHOUT @Underlay -> weakens
        return agent.strength <= 24


class Disciplined(Capped):
    @Post
    @Underlay
    def Strength_Capped(agent, base):   # strengthen via the underlay
        return base() and agent.strength <= 18


class Reflective(Tag):
    @Post
    def Self_Aware(agent):
        if agent:                       # nested bool(agent) must not recurse
            return True


class Slotted(Tag):
    @Post
    def Raw_Slots(agent):
        return agent.spell_slots        # a raw int -- strict verdict rejects it


class Reserved(Tag):
    @Post
    def Has_Slots_Record(agent):
        assert agent.spell_slots is not None   # existence allows a real 0


class TagKitClaimTests(unittest.TestCase):
    def test_empty_tag_does_not_invent_application_reports(
            self,
            ) -> None:
        class Empty(Tag):
            pass

        for name in (
                "ABSTRACT",
                "DESCRIPTION",
                "NAME",
                ):
            with self.subTest(
                    name=name,
                    ):
                self.assertFalse(
                        hasattr(
                                Empty,
                                name,
                                )
                        )

                with self.assertRaises(
                        AttributeError
                        ):
                    getattr(
                            Empty,
                            name,
                            )

        self.assertFalse(
                hasattr(
                        Empty,
                        "Describe",
                        )
                )
        self.assertFalse(
                hasattr(
                        Empty,
                        "Label",
                        )
                )
        self.assertEqual(
                str( Empty ),
                "Empty",
                )
        self.assertEqual(
                repr( Empty ),
                "Empty",
                )

    def test_tag_text_uses_python_name_and_doc(
            self,
            ) -> None:
        class Fire(Tag):
            """A fire elemental creature."""

        self.assertEqual(
                Fire.__name__,
                "Fire",
                )
        self.assertEqual(
                str( Fire ),
                "Fire",
                )
        self.assertEqual(
                Fire.__doc__,
                "A fire elemental creature.",
                )
        self.assertEqual(
                repr( Fire ),
                "Fire\nA fire elemental creature.",
                )

    def test_name_and_description_are_ordinary_report_names(
            self,
            ) -> None:
        class Fire(Tag):
            """Python documentation."""

            NAME = "Flame"
            DESCRIPTION = "Application description."

        ari = Agent()

        Fire( ari )

        self.assertEqual(
                Fire[ ari ].NAME,
                "Flame",
                )
        self.assertEqual(
                Fire[ ari ].DESCRIPTION,
                "Application description.",
                )
        self.assertEqual(
                str( Fire ),
                "Fire",
                )
        self.assertEqual(
                repr( Fire ),
                "Fire\nPython documentation.",
                )
        self.assertTrue(
                Has(
                        ari,
                        "Fire",
                        )
                )
        self.assertFalse(
                Has(
                        ari,
                        "Flame",
                        )
                )

    def test_tag_repr_dunder_remains_an_agent_action(
            self,
            ) -> None:
        class Mask(Tag):
            def __repr__(
                    target,
                    ) -> str:
                return "Masked Agent"

        ari = Agent()

        Mask( ari )

        self.assertEqual(
                repr( Mask ),
                "Mask",
                )
        self.assertEqual(
                repr( ari ),
                "Masked Agent",
                )

    def test_public_tag_data_is_report_data(
            self,
            ) -> None:
        class Fire(Tag):
            COLOR = "#ef5b35"
            SOURCE = "Core rules"

        ari = Agent()

        Fire( ari )

        report_names = (
                "COLOR",
                "SOURCE",
                )

        for name in report_names:
            with self.subTest(
                    name=name,
                    ):
                expected = Fire.__dict__[ name ]

                self.assertEqual(
                        getattr(
                                Fire,
                                name,
                                ),
                        expected,
                        )
                self.assertEqual(
                        getattr(
                                Fire[ ari ],
                                name,
                                ),
                        expected,
                        )
                self.assertFalse(
                        hasattr(
                                ari,
                                name,
                                )
                        )

        self.assertTrue(
                Has(
                        ari,
                        "Fire",
                        )
                )

    def test_undeclared_tag_reports_remain_absent_from_bound_views(
            self,
            ) -> None:
        class Fire(Tag):
            COLOR = "#ef5b35"

        ari = Agent()

        Fire( ari )

        self.assertEqual(
                Fire[ ari ].COLOR,
                Fire.COLOR,
                )

        for name in (
                "SOURCE",
                "VERSION",
                ):
            with self.subTest(
                    name=name,
                    ):
                with self.assertRaises(
                        AttributeError
                        ):
                    getattr(
                            Fire[ ari ],
                            name,
                            )

    def test_pin_can_contribute_a_report(
            self,
            ) -> None:
        class Documented(Tag):
            @Record
            def LORE(
                    target,
                    text,
                    ) -> str:
                return text

        class Entry(Tag):
            pass

        Documented(
                Entry,
                text="Pinned lore.",
                )

        self.assertEqual(
                Entry.LORE,
                "Pinned lore.",
                )
        self.assertEqual(
                Documented[ Entry ].LORE,
                "Pinned lore.",
                )

    def test_a_tag_can_be_pinned_and_remain_a_tag(self) -> None:
        class Availability(Tag):
            pass

        class Available(Availability):
            pass

        class Acolyte(Tag):
            abilities = Report(
                    (
                        "INT",
                        "WIS",
                        "CHA",
                        )
                    )

            @Imprint
            def Establish_Background(
                    agent,
                    ) -> None:
                agent.events.append("Acolyte")

        identity = id(Acolyte)
        original_metaclass = type(Acolyte)

        returned = Available(
                Acolyte
                )

        self.assertIs(
                returned,
                Acolyte,
                )
        self.assertEqual(
                id(Acolyte),
                identity,
                )
        self.assertIs(
                type(Acolyte),
                original_metaclass,
                )
        self.assertIn(
                Acolyte,
                Available,
                )
        self.assertIn(
                Acolyte,
                Availability,
                )
        self.assertEqual(
                list(
                    Available.Field
                    ),
                [
                    Acolyte,
                    ],
                )
        self.assertEqual(
                Acolyte.abilities,
                (
                    "INT",
                    "WIS",
                    "CHA",
                    ),
                )

        ari = Agent()
        Acolyte(
                ari
                )

        self.assertIn(
                ari,
                Acolyte,
                )
        self.assertIsInstance(
                ari,
                Acolyte,
                )
        self.assertEqual(
                ari.events,
                [
                    "Acolyte",
                    ],
                )
        self.assertNotIn(
                ari,
                Available,
                )
        self.assertEqual(
                list(
                    Acolyte.Field
                    ),
                [
                    ari,
                    ],
                )

        Acolyte.Rip(
                ari
                )

        self.assertNotIn(
                ari,
                Acolyte,
                )
        self.assertIn(
                Acolyte,
                Available,
                )

    def test_pin_uses_actions_and_records_at_tag_scope(self) -> None:
        class Catalogue(Tag):
            policy = Report(
                    "Pin policy"
                    )

            @Operation
            def Owner(
                    pin,
                    ):
                return pin

            @Action
            def Explain(
                    target,
                    ) -> str:
                if isinstance(
                        target,
                        type,
                        ):
                    return target.__name__

                return "Agent"

            @Record
            def aliases(
                    target,
                    ) -> list[str]:
                return []

        class Entry(Tag):
            pass

        Catalogue(
                Entry
                )

        self.assertEqual(
                Entry.Explain(),
                "Entry",
                )
        self.assertEqual(
                Entry.aliases,
                [],
                )
        self.assertEqual(
                Catalogue.policy,
                "Pin policy",
                )
        self.assertIs(
                Catalogue.Owner(),
                Catalogue,
                )
        self.assertFalse(
                hasattr(
                    Entry,
                    "policy",
                    )
                )

        view = Entry.Tag(
                Catalogue
                )

        self.assertEqual(
                view.Explain(),
                "Entry",
                )
        self.assertEqual(
                view.aliases,
                [],
                )
        self.assertEqual(
                view.policy,
                "Pin policy",
                )
        self.assertIs(
                view.Owner(),
                Catalogue,
                )

        ari = Agent()
        Catalogue(
                ari
                )

        self.assertEqual(
                ari.Explain(),
                "Agent",
                )
        self.assertEqual(
                ari.aliases,
                [],
                )
        self.assertIsNot(
                ari.aliases,
                Entry.aliases,
                )

    def test_native_agent_scope_coexists_with_pinned_tag_scope(self) -> None:
        class Entry(Tag):
            def Describe_Value(
                    agent,
                    ) -> str:
                return "Agent Action"

            @Record
            def status(
                    agent,
                    ) -> str:
                return "Agent Record"

        class Catalogue(Tag):
            def Describe_Value(
                    target,
                    ) -> str:
                return "Tag Operation"

            @Record
            def status(
                    target,
                    ) -> str:
                return "Tag Report"

        Catalogue(
                Entry
                )

        self.assertEqual(
                Entry.Describe_Value(),
                "Tag Operation",
                )
        self.assertEqual(
                Entry.status,
                "Tag Report",
                )

        ari = Agent()
        Entry(
                ari
                )

        self.assertEqual(
                ari.Describe_Value(),
                "Agent Action",
                )
        self.assertEqual(
                ari.status,
                "Agent Record",
                )

    def test_pinned_tag_scope_enters_only_new_agent_snapshots(self) -> None:
        class Entry(Tag):
            pass

        early = Agent()
        Entry(
                early
                )

        class Catalogue(Tag):
            def Explain(
                    target,
                    ) -> str:
                return "Pin-provided"

            @Record
            def status(
                    target,
                    ) -> str:
                return "catalogued"

        Catalogue(
                Entry
                )

        late = Agent()
        Entry(
                late
                )

        with self.assertRaises(
                AttributeError
                ):
            early.Entry.Explain()

        with self.assertRaises(
                AttributeError
                ):
            _value = early.Entry.status

        self.assertEqual(
                late.Entry.Explain(),
                "Pin-provided",
                )
        self.assertEqual(
                late.Entry.status,
                "catalogued",
                )

    def test_successful_meta_imprint_invalidates_target_declarations(self) -> None:
        class Entry(Tag):
            pass

        early = Agent()
        Entry(
                early
                )

        class Enriched(Tag):
            @Imprint
            def Add_Report(
                    target,
                    ) -> None:
                target.imprinted = Report(
                        "committed"
                        )

        Enriched(
                Entry
                )

        late = Agent()
        Entry(
                late
                )

        self.assertEqual(
                Entry.imprinted,
                "committed",
                )

        with self.assertRaises(
                AttributeError
                ):
            _value = early.Entry.imprinted

        self.assertEqual(
                late.Entry.imprinted,
                "committed",
                )

    def test_pin_reapplication_is_a_strict_noop(self) -> None:
        class Catalogue(Tag):
            @Imprint
            def Count(
                    target,
                    ) -> None:
                target.pin_count = (
                        getattr(
                            target,
                            "pin_count",
                            0,
                            )
                        + 1
                        )

            @Record
            def token(
                    target,
                    ) -> object:
                return object()

        class Entry(Tag):
            pass

        first = Catalogue(
                Entry
                )
        second = Catalogue(
                Entry
                )
        token = Entry.token

        Catalogue(
                Entry
                )

        self.assertIs(
                first,
                Entry,
                )
        self.assertIs(
                second,
                Entry,
                )
        self.assertEqual(
                Entry.pin_count,
                1,
                )
        self.assertIs(
                Entry.token,
                token,
                )
        self.assertEqual(
                list(
                    Catalogue.Field
                    ).count(
                        Entry
                        ),
                1,
                )

    def test_pin_conditions_receive_application_inputs(self) -> None:
        class Named_Catalogue(Tag):
            def Accepts(
                    target,
                    prefix: str,
                    ) -> bool:
                return target.__name__.startswith(prefix)

            @Pre
            def Has_Prefix(
                    target,
                    prefix: str,
                    ) -> bool:
                target.trace = (
                        *target.trace,
                        "Pre",
                        )

                return target.Accepts(prefix)

            @Imprint
            def Mark(
                    target,
                    prefix: str,
                    ) -> None:
                target.trace = (
                        *target.trace,
                        "Imprint",
                        )
                target.pending_catalogue_name = prefix

            @Record
            def catalogue_name(
                    target,
                    ) -> str:
                target.trace = (
                        *target.trace,
                        "Record",
                        )

                return target.pending_catalogue_name

            @Post
            def Has_Report(
                    target,
                    ) -> bool:
                target.trace = (
                        *target.trace,
                        "Post",
                        )

                return target.catalogue_name == "Ent"

        class Entry(Tag):
            trace = ()

        returned = Named_Catalogue(
                Entry,
                prefix="Ent",
                )

        self.assertIs(
                returned,
                Entry,
                )
        self.assertIn(
                Entry,
                Named_Catalogue,
                )
        self.assertEqual(
                Entry.catalogue_name,
                "Ent",
                )
        self.assertEqual(
                Entry.trace,
                (
                    "Pre",
                    "Imprint",
                    "Record",
                    "Post",
                    ),
                )

    def test_failed_pinning_rolls_back_atomically(self) -> None:
        class Catalogue_Base(Tag):
            def Temporary_Operation(
                    target,
                    ) -> str:
                return "temporary"

            @Record
            def temporary_report(
                    target,
                    ) -> str:
                return "temporary"

            @Pre
            def Mutate_Namespace(
                    target,
                    ) -> bool:
                target.added_by_pre = True
                target.changed = "changed"

                if hasattr(
                        target,
                        "removed",
                        ):
                    del target.removed

                return True

        class Rejected(Catalogue_Base):
            @Imprint
            def Mutate_Metadata(
                    target,
                    ) -> None:
                target.__name__ = "Mutated_Entry"
                target.__qualname__ = "Mutated_Entry"

            @Post
            def Never_Accept(
                    target,
                    ) -> bool:
                return False

        class Entry(Tag):
            changed = "original"
            removed = "restore me"

        original_metaclass = type(Entry)
        original_name = Entry.__name__
        original_qualname = Entry.__qualname__

        with self.assertRaises(
                TagPostconditionError
                ):
            Rejected(
                    Entry
                    )

        self.assertNotIn(
                Entry,
                Catalogue_Base,
                )
        self.assertNotIn(
                Entry,
                Rejected,
                )
        self.assertNotIn(
                Entry,
                Catalogue_Base.Field,
                )
        self.assertNotIsInstance(
                Entry,
                Catalogue_Base,
                )
        self.assertNotIsInstance(
                Entry,
                Rejected,
                )
        self.assertFalse(
                hasattr(
                    Entry,
                    "Temporary_Operation",
                    )
                )
        self.assertFalse(
                hasattr(
                    Entry,
                    "temporary_report",
                    )
                )
        self.assertFalse(
                hasattr(
                    Entry,
                    "added_by_pre",
                    )
                )
        self.assertEqual(
                Entry.changed,
                "original",
                )
        self.assertEqual(
                Entry.removed,
                "restore me",
                )
        self.assertEqual(
                Entry.__name__,
                original_name,
                )
        self.assertEqual(
                Entry.__qualname__,
                original_qualname,
                )
        self.assertIs(
                type(Entry),
                original_metaclass,
                )

    def test_reentrant_pinning_fails_atomically(self) -> None:
        class Nested(Tag):
            pass

        class Outer(Tag):
            @Imprint
            def Apply_Nested(
                    target,
                    ) -> None:
                target.transient = True

                Nested(
                        target
                        )

        class Entry(Tag):
            pass

        with self.assertRaises(
                TagImprintError
                ):
            Outer(
                    Entry
                    )

        self.assertNotIn(
                Entry,
                Outer,
                )
        self.assertNotIn(
                Entry,
                Nested,
                )
        self.assertEqual(
                list(
                    Outer.Field
                    ),
                [],
                )
        self.assertEqual(
                list(
                    Nested.Field
                    ),
                [],
                )
        self.assertNotIsInstance(
                Entry,
                Outer,
                )
        self.assertNotIsInstance(
                Entry,
                Nested,
                )
        self.assertFalse(
                hasattr(
                    Entry,
                    "transient",
                    )
                )

    def test_pin_cannot_rip_itself_during_application(self) -> None:
        class Self_Ripping(Tag):
            @Imprint
            def Leave(
                    target,
                    ) -> None:
                Self_Ripping.Rip(
                        target
                        )

        class Entry(Tag):
            pass

        with self.assertRaises(
                TagImprintError
                ):
            Self_Ripping(
                    Entry
                    )

        self.assertNotIn(
                Entry,
                Self_Ripping,
                )
        self.assertEqual(
                list(
                    Self_Ripping.Field
                    ),
                [],
                )

    def test_failed_pinning_cannot_rip_prior_membership(self) -> None:
        class Existing(Tag):
            pass

        class Rejected(Tag):
            @Imprint
            def Remove_Existing(
                    target,
                    ) -> None:
                Existing.Rip(
                        target
                        )

        class Entry(Tag):
            pass

        Existing(
                Entry
                )

        with self.assertRaises(
                TagImprintError
                ):
            Rejected(
                    Entry
                    )

        self.assertIn(
                Entry,
                Existing,
                )
        self.assertIn(
                Entry,
                Existing.Field,
                )
        self.assertNotIn(
                Entry,
                Rejected,
                )

    def test_failed_pin_precondition_discards_its_mutation(
            self,
            ) -> None:
        class Rejected(Tag):
            @Pre
            def Mark_Then_Reject(
                    target,
                    ) -> bool:
                target.mandatory_security = "provisional"

                return False

        class Entry(Tag):
            pass

        with self.assertRaises(
                TagPreconditionError
                ):
            Rejected(
                    Entry
                    )

        self.assertNotIn(
                Entry,
                Rejected,
                )
        self.assertFalse(
                hasattr(
                    Entry,
                    "mandatory_security",
                    )
                )

    def test_failed_tag_scope_report_names_its_materialization_error(
            self,
            ) -> None:
        class Broken_Pin(Tag):
            @Record
            def policy(
                    target,
                    ) -> str:
                raise TypeError(
                        "invalid policy source"
                        )

        class Entry(Tag):
            pass

        with self.assertRaisesRegex(
                TagCompositionError,
                "Tag-scope Report .*Broken_Pin.policy"
                " failed to materialize",
                ) as caught:
            Broken_Pin(
                    Entry
                    )

        self.assertIsInstance(
                caught.exception.__cause__,
                TypeError,
                )
        self.assertNotIn(
                Entry,
                Broken_Pin,
                )
        self.assertFalse(
                hasattr(
                    Entry,
                    "policy",
                    )
                )

    def test_aliased_tag_scope_report_names_its_declaration(
            self,
            ) -> None:
        @Record
        def Shared_Policy(
                target,
                ) -> str:
            raise TypeError(
                    "invalid shared policy"
                    )

        class Broken_Pin(Tag):
            policy = Shared_Policy

        class Entry(Tag):
            pass

        with self.assertRaisesRegex(
                TagCompositionError,
                "Tag-scope Report .*Broken_Pin.policy"
                " failed to materialize",
                ):
            Broken_Pin(
                    Entry
                    )

    def test_failed_pinning_keeps_earlier_pin(self) -> None:
        class Published(Tag):
            pass

        class Rejected(Tag):
            @Post
            def Never_Accept(
                    target,
                    ) -> bool:
                return False

        class Entry(Tag):
            pass

        Published(
                Entry
                )

        with self.assertRaises(
                TagPostconditionError
                ):
            Rejected(
                    Entry
                    )

        self.assertIn(
                Entry,
                Published,
                )
        self.assertNotIn(
                Entry,
                Rejected,
                )
        self.assertEqual(
                list(
                    Published.Field
                    ),
                [
                    Entry,
                    ],
                )

    def test_pinned_tag_truth_rechecks_living_postconditions(self) -> None:
        class Validated_Catalogue(Tag):
            @Post
            def Is_Enabled(
                    target,
                    ) -> bool:
                return target.enabled

        class Entry(Tag):
            enabled = True

        Validated_Catalogue(
                Entry
                )

        self.assertTrue(
                bool(Entry)
                )
        self.assertTrue(
                Contract.Postconditions(
                    Entry
                    )
                )

        Entry.enabled = False

        self.assertFalse(
                bool(Entry)
                )

        with self.assertRaises(
                TagPostconditionError
                ):
            Contract.Postconditions(
                    Entry
                    )

    def test_ripped_pin_keeps_pinning_history(self) -> None:
        class Catalogue(Tag):
            secret = Report(
                    "field only"
                    )

            @Action
            @Rip
            def Mark_Rip(
                    target,
                    ) -> None:
                target.rip_count += 1

            @Record
            def status(
                    target,
                    ) -> str:
                return "catalogued"

        class Entry(Tag):
            rip_count = 0

        class Other(Tag):
            pass

        Catalogue(
                Entry
                )
        view = Entry.Tag(
                Catalogue
                )
        self.assertEqual(
                view.status,
                "catalogued",
                )
        self.assertEqual(
                view.secret,
                "field only",
                )

        Catalogue.Rip(
                Entry
                )

        self.assertNotIn(
                Entry,
                Catalogue,
                )
        self.assertEqual(
                Entry.rip_count,
                1,
                )
        self.assertEqual(
                Entry.status,
                "catalogued",
                )
        self.assertTrue(
                callable(
                    Entry.Mark_Rip
                    )
                )

        with self.assertRaises(
                TagResolutionError
                ):
            Entry.Tag(
                    Catalogue
                    )

        with self.assertRaises(
                TagResolutionError
                ):
            _value = view.secret

        with self.assertRaises(
                TagResolutionError
                ):
            _value = view.status

        with self.assertRaises(
                TagResolutionError
                ):
            view.Mark_Rip()

        Other(
                Entry
                )

        with self.assertRaises(
                AttributeError
                ):
            _value = Entry.Tag(
                    Other
                    ).secret
        self.assertNotIn(
                Entry,
                Catalogue.Field,
                )
        self.assertIsInstance(
                Entry,
                Catalogue,
                )

    def test_rip_revokes_field_resources_and_restores_active_provider(
            self,
            ) -> None:
        class First(Tag):
            label = Report(
                    "first"
                    )

            @Operation
            def Describe(
                    pin,
                    ) -> str:
                return pin.__name__

        class Second(Tag):
            label = Report(
                    "second"
                    )

            @Operation
            def Describe(
                    pin,
                    ) -> str:
                return pin.__name__

        class Before_Rip(Tag):
            pass

        class After_Rip(Tag):
            pass

        class Entry(Tag):
            pass

        First(
                Entry
                )
        Second(
                Entry
                )
        Before_Rip(
                Entry
                )

        captured = Entry.Tag(
                Before_Rip
                )

        Second.Rip(
                Entry
                )

        with self.assertRaises(
                TagResolutionError
                ):
            _value = captured.label

        with self.assertRaises(
                TagResolutionError
                ):
            captured.Describe()

        After_Rip(
                Entry
                )
        current = Entry.Tag(
                After_Rip
                )

        self.assertEqual(
                current.label,
                "first",
                )
        self.assertEqual(
                current.Describe(),
                "First",
                )

    def test_condition_name_does_not_resurrect_deleted_field_resource(
            self,
            ) -> None:
        class Has_Resources(Tag):
            value = Report(
                    "available"
                    )

            @Operation
            def Describe(
                    pin,
                    ) -> str:
                return pin.__name__

        class Mask(Tag):
            @Delete
            def value(
                    target,
                    ) -> None:
                pass

            @Delete
            def Describe(
                    target,
                    ) -> None:
                pass

        class Reuses_Names(Tag):
            @Pre
            def value(
                    target,
                    ) -> bool:
                return True

            @Post
            def Describe(
                    target,
                    ) -> bool:
                return True

        ari = Agent()

        Has_Resources(
                ari
                )
        Mask(
                ari
                )
        Reuses_Names(
                ari
                )

        view = ari.Tag(
                Reuses_Names
                )

        with self.assertRaises(
                AttributeError
                ):
            _value = view.value

        with self.assertRaises(
                AttributeError
                ):
            view.Describe()

    def test_rip_does_not_fall_back_past_active_field_delete(
            self,
            ) -> None:
        class First(Tag):
            value = Report(
                    "first"
                    )

            @Operation
            def Describe(
                    pin,
                    ) -> str:
                return pin.__name__

        class Mask(Tag):
            @Delete
            def value(
                    target,
                    ) -> None:
                pass

            @Delete
            def Describe(
                    target,
                    ) -> None:
                pass

        class Second(Tag):
            value = Report(
                    "second"
                    )

            @Operation
            def Describe(
                    pin,
                    ) -> str:
                return pin.__name__

        class Before_Rip(Tag):
            pass

        class After_Rip(Tag):
            pass

        ari = Agent()

        First(
                ari
                )
        Mask(
                ari
                )
        Second(
                ari
                )
        Before_Rip(
                ari
                )

        before = ari.Tag(
                Before_Rip
                )

        self.assertEqual(
                before.value,
                "second",
                )
        self.assertEqual(
                before.Describe(),
                "Second",
                )

        Second.Rip(
                ari
                )
        After_Rip(
                ari
                )

        after = ari.Tag(
                After_Rip
                )

        with self.assertRaises(
                AttributeError
                ):
            _value = after.value

        with self.assertRaises(
                AttributeError
                ):
            after.Describe()

    def test_field_delete_does_not_mask_later_sticky_agent_contribution(
            self,
            ) -> None:
        class Field_Source(Tag):
            Act = Report(
                    "field action"
                    )
            status = Report(
                    "field record"
                    )

        class Mask(Tag):
            @Delete
            def Act(
                    target,
                    ) -> None:
                pass

            @Delete
            def status(
                    target,
                    ) -> None:
                pass

        class Restores_Agent_Scope(Tag):
            def Act(
                    target,
                    ) -> str:
                return "agent action"

            @Record
            def status(
                    target,
                    ) -> str:
                return "agent record"

        class Observer(Tag):
            pass

        ari = Agent()

        Field_Source(
                ari
                )
        Mask(
                ari
                )
        Restores_Agent_Scope(
                ari
                )
        Restores_Agent_Scope.Rip(
                ari
                )
        Observer(
                ari
                )

        view = ari.Tag(
                Observer
                )

        self.assertEqual(
                view.Act(),
                "agent action",
                )
        self.assertEqual(
                view.status,
                "agent record",
                )

    def test_pin_base_rip_cascades_dependent_shapes(
            self,
            ) -> None:
        class Catalogue(Tag):
            pass

        class Featured(Catalogue):
            pass

        class Entry(Tag):
            pass

        Featured(
                Entry
                )

        Catalogue.Rip(
                Entry
                )

        self.assertNotIn(
                Entry,
                Catalogue,
                )
        self.assertNotIn(
                Entry,
                Featured,
                )
        self.assertNotIn(
                Entry,
                Catalogue.Field,
                )
        self.assertNotIn(
                Entry,
                Featured.Field,
                )
        self.assertIsInstance(
                Entry,
                Catalogue,
                )
        self.assertIsInstance(
                Entry,
                Featured,
                )

    def test_pin_field_is_non_owning(self) -> None:
        class Catalogue(Tag):
            @Record
            def owner(
                    target,
                    ):
                return target

        class Entry(Tag):
            pass

        Catalogue(
                Entry
                )
        reference = weakref.ref(
                Entry
                )

        del Entry
        gc.collect()

        self.assertIsNone(
                reference()
                )
        self.assertEqual(
                list(
                    Catalogue.Field
                    ),
                [],
                )

        def Self_Classified_Reference():
            class Loop(Tag):
                pass

            Loop(
                    Loop
                    )

            return weakref.ref(
                    Loop
                    )

        loop_reference = Self_Classified_Reference()
        gc.collect()

        self.assertIsNone(
                loop_reference()
                )

    def test_pin_state_is_not_inherited_by_target_shapes(self) -> None:
        class Catalogue(Tag):
            pass

        class Entry(Tag):
            pass

        Catalogue(
                Entry
                )

        class Specialized_Entry(Entry):
            pass

        self.assertIn(
                Entry,
                Catalogue,
                )
        self.assertNotIn(
                Specialized_Entry,
                Catalogue,
                )
        self.assertNotIsInstance(
                Specialized_Entry,
                Catalogue,
                )

        with self.assertRaises(
                TagCompositionError
                ):
            setattr(
                    Entry,
                    "__tagkit_pin_state__",
                    None,
                    )

        with self.assertRaises(
                TagCompositionError
                ):
            delattr(
                    Entry,
                    "__tagkit_pin_state__",
                    )

        self.assertIn(
                Entry,
                Catalogue,
                )

    def test_pin_contributions_extend_native_tag_scope(self) -> None:
        class Entry(Tag):
            labels = (
                    "native",
                    )

            @Operation
            def Explain(
                    target,
                    subject: str,
                    ) -> str:
                return f"{target.__name__}:{subject}"

        class Refined(Tag):
            @Action
            @Underlay
            def Explain(
                    target,
                    prior,
                    subject: str,
                    ) -> str:
                return (
                        prior(subject)
                        + ":refined"
                        )

            @Record
            @Underlay
            def labels(
                    target,
                    prior,
                    ) -> tuple[str, ...]:
                return (
                        *prior(),
                        "refined",
                        )

        Refined(
                Entry
                )

        self.assertEqual(
                Entry.Explain(
                    "subject"
                    ),
                "Entry:subject:refined",
                )
        self.assertEqual(
                Entry.labels,
                (
                    "native",
                    "refined",
                    ),
                )

    def test_pin_overlays_keep_pin_snapshots(self) -> None:
        class First(Tag):
            def Explain(
                    target,
                    ) -> str:
                return "first"

            @Record
            def labels(
                    target,
                    ) -> list[str]:
                return [
                        "first",
                        ]

        class Second(Tag):
            @Underlay
            def Explain(
                    target,
                    prior,
                    ) -> str:
                return (
                        prior()
                        + ":second"
                        )

            @Record
            @Underlay
            def labels(
                    target,
                    prior,
                    ) -> list[str]:
                return (
                        prior()
                        + ["second"]
                        )

        class Entry(Tag):
            pass

        First(
                Entry
                )
        first_view = Entry.Tag(
                First
                )

        Second(
                Entry
                )

        self.assertEqual(
                Entry.Explain(),
                "first:second",
                )
        self.assertEqual(
                Entry.labels,
                [
                    "first",
                    "second",
                    ],
                )
        self.assertEqual(
                first_view.Explain(),
                "first",
                )
        self.assertEqual(
                first_view.labels,
                [
                    "first",
                    ],
                )
        self.assertEqual(
                Entry.Tag(
                    Second
                    ).Explain(),
                "first:second",
                )

    def test_pin_delete_targets_tag_scope_only(self) -> None:
        class Entry(Tag):
            visible = "native report"

        class Context(Tag):
            visible = "Pin report"

        class Hidden(Tag):
            @Delete
            def visible(
                    target,
                    ) -> None:
                pass

        class Later_Context(Tag):
            visible = "later Pin report"

        Context(
                Entry
                )
        Hidden(
                Entry
                )
        Later_Context(
                Entry
                )

        self.assertEqual(
                Context.visible,
                "Pin report",
                )
        self.assertFalse(
                hasattr(
                    Entry,
                    "visible",
                    )
                )
        self.assertEqual(
                Entry.Tag(
                    Context
                    ).visible,
                "Pin report",
                )
        self.assertEqual(
                Entry.Tag(
                    Later_Context
                    ).visible,
                "later Pin report",
                )

        ari = Agent()
        Entry(
                ari
                )

        with self.assertRaises(
                AttributeError
                ):
            _value = ari.Entry.visible

    def test_pin_report_supports_assignment_and_deletion(self) -> None:
        class Ranked(Tag):
            @Record
            def rank(
                    target,
                    ) -> int:
                return 1

        class Entry(Tag):
            pass

        Ranked(
                Entry
                )

        Entry.rank = 2

        self.assertEqual(
                Entry.rank,
                2,
                )
        self.assertEqual(
                Entry.Tag(
                    Ranked
                    ).rank,
                1,
                )

        del Entry.rank

        self.assertFalse(
                hasattr(
                    Entry,
                    "rank",
                    )
                )

        Entry.rank = 3

        self.assertEqual(
                Entry.rank,
                3,
                )

    def test_cross_kind_tag_scope_collision_fails_atomically(self) -> None:
        class Report_Target(Tag):
            value = Report(
                    "report"
                    )

        class Operation_Source(Tag):
            def value(
                    target,
                    ) -> str:
                return "operation"

        class Operation_Target(Tag):
            @Operation
            def value(
                    target,
                    ) -> str:
                return "operation"

        class Report_Source(Tag):
            @Record
            def value(
                    target,
                    ) -> str:
                return "report"

        cases = (
                (
                    Operation_Source,
                    Report_Target,
                    ),
                (
                    Report_Source,
                    Operation_Target,
                    ),
                )

        for source, target in cases:
            with self.subTest(
                    source=source.__name__,
                    target=target.__name__,
                    ):
                with self.assertRaises(
                        TagCompositionError
                        ):
                    source(
                            target
                            )

                self.assertNotIn(
                        target,
                        source,
                        )
                self.assertNotIsInstance(
                        target,
                        source,
                        )

    def test_structural_dunder_badging_fails_before_mutation(self) -> None:
        class Ranked(Tag):
            @Record
            def rank(
                    target,
                    ) -> int:
                return 4

            def __add__(
                    target,
                    amount: int,
                    ) -> int:
                return target.rank + amount

        class Entry(Tag):
            pass

        with self.assertRaisesRegex(
                TagCompositionError,
                "structural member '__add__'",
                ):
            Ranked(
                    Entry
                    )

        self.assertNotIn(
                Entry,
                Ranked,
                )
        self.assertEqual(
                list(
                    Ranked.Field
                    ),
                [],
                )
        self.assertFalse(
                hasattr(
                    Entry,
                    "rank",
                    )
                )

    def test_tagging_preserves_identity_and_builds_base_membership(self) -> None:
        ari = Agent()
        returned = Elf(ari)

        self.assertIs(
                returned,
                ari,
                )
        self.assertIn(
                ari,
                Elf,
                )
        self.assertIn(
                ari,
                Person,
                )
        self.assertIsInstance(
                ari,
                Elf,
                )
        self.assertIsInstance(
                ari,
                Person,
                )

    def test_direct_bases_apply_in_declaration_order_and_diamond_once(self) -> None:
        ari = Agent()

        Bridge(ari)

        self.assertEqual(
                ari.events,
                [
                    "Root",
                    "Left",
                    "Right",
                    "Bridge",
                    ],
                )
        self.assertIn(
                ari,
                Root,
                )
        self.assertIn(
                ari,
                Left,
                )
        self.assertIn(
                ari,
                Right,
                )

    def test_active_reapply_is_a_strict_noop(self) -> None:
        ari = Agent()

        Stocked(ari)
        ari.supplies.append("torch")
        ari.events.append("between")

        # Re-applying a currently active Tag does NOTHING: Records are not
        # reset and Imprints do not re-run. Resetting is deliberate -- Rip
        # then apply again -- so an accidental reapplication in a complex
        # system can never silently wipe accumulated state.
        Stocked(ari)

        self.assertEqual(
                ari.supplies,
                [
                    "ration",
                    "torch",
                    ],
                )
        self.assertEqual(
                ari.events,
                [
                    "Stocked",
                    "between",
                    ],
                )
        self.assertEqual(
                list(Stocked.Field).count(ari),
                1,
                )

    def test_successful_reapplication_is_idempotent(self) -> None:
        ari = Agent()

        Ordered_Imprints(ari)
        Ordered_Imprints(ari)

        self.assertEqual(
                ari.events,
                [
                    "First",
                    "Second",
                    ],
                )
        self.assertEqual(
                list(Ordered_Imprints.Field).count(ari),
                1,
                )

    def test_underlay_captures_the_visible_overlay_at_tagging_time(self) -> None:
        ari = Agent()

        Elf(ari)
        Paladin(ari)

        self.assertEqual(
                ari.Attack(),
                "With elven grace Attack! with a holy oath.",
                )
        self.assertEqual(
                ari.Paladin.Attack(),
                "With elven grace Attack! with a holy oath.",
                )

        with self.assertWarns(TagOverwriteWarning):
            Berserker(ari)

        self.assertEqual(
                ari.Attack(),
                "Reckless attack!",
                )
        self.assertEqual(
                ari.Paladin.Attack(),
                "With elven grace Attack! with a holy oath.",
                )

    def test_agent_action_calls_resolve_the_current_overlay(self) -> None:
        ari = Agent()

        Elf(ari)
        Combatant(ari)

        self.assertEqual(
                ari.Combat(),
                "With elven grace Attack!",
                )

        with self.assertWarns(TagOverwriteWarning):
            Berserker(ari)

        self.assertEqual(
                ari.Combat(),
                "Reckless attack!",
                )

    def test_underlay_can_refine_an_original_oop_action(self) -> None:
        ari = Agent()

        OOP_Refinement(ari)

        self.assertEqual(
                ari.Attack(),
                "Refined Faulty OOP attack!",
                )

    def test_independent_action_replacement_emits_a_diagnostic(self) -> None:
        ari = Agent()

        Person(ari)

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            Berserker(ari)

        self.assertTrue(
                any(
                        issubclass(
                                warning.category,
                                TagOverwriteWarning,
                                )
                        for warning in captured
                        )
                )

    def test_records_are_fresh_per_agent_and_can_extend_an_underlay(self) -> None:
        ari = Agent()
        bea = Agent()

        Prepared(ari)
        Inventory(bea)

        self.assertEqual(
                ari.items,
                ["rope"],
                )
        self.assertEqual(
                bea.items,
                [],
                )
        self.assertIsNot(
                ari.items,
                bea.items,
                )

    def test_a_record_can_replace_an_existing_object_attribute(self) -> None:
        ari = Agent()

        Armed(ari)

        self.assertEqual(
                ari.weapon,
                "arcane staff",
                )

    def test_deletion_removes_oop_members_and_resets_the_underlay(self) -> None:
        ari = Agent()

        Pacifist(ari)

        self.assertFalse(
                hasattr(
                        ari,
                        "Attack",
                        )
                )
        self.assertFalse(
                hasattr(
                        ari,
                        "weapon",
                        )
                )

        with self.assertRaises(TagResolutionError):
            Needs_Action_Underlay(ari)

        Repaired_Pacifist(ari)

        self.assertEqual(
                ari.Attack(),
                "Defensive action!",
                )
        self.assertEqual(
                ari.weapon,
                "shield",
                )

    def test_delete_semantically_masks_a_read_only_host_descriptor(
            self,
            ) -> None:
        class Host:
            @property
            def value(
                    host,
                    ) -> int:
                return 7

        class Hidden(Tag):
            @Delete
            def value(
                    host,
                    ) -> None:
                pass

        host = Host()
        Hidden(host)

        with self.assertRaises(AttributeError):
            _ = host.value

        self.assertIn(
                host,
                Hidden,
                )

    def test_deleted_record_has_no_underlay_and_a_later_shape_can_rebuild_it(self) -> None:
        ari = Agent()

        Lost_Inventory(ari)

        self.assertFalse(
                hasattr(
                        ari,
                        "items",
                        )
                )

        with self.assertRaises(TagResolutionError):
            Needs_Inventory_Underlay(ari)

        Rebuilt_Inventory(ari)

        self.assertEqual(
                ari.items,
                ["shield"],
                )

    def test_failing_shape_rolls_back_its_bases_atomically(self) -> None:
        ari = Agent()

        with self.assertRaises(TagPreconditionError):
            Citadel(ari)

        # Atomic application: the whole Citadel(ari) call is one
        # transaction. When Citadel fails its Precondition, the Territory
        # Base pulled in by THIS call is rolled back too -- membership and
        # its TOP-managed `banner` Record vanish -- leaving the Agent
        # exactly as it was at call entry.
        self.assertNotIn(
                ari,
                Territory,
                )
        self.assertNotIn(
                ari,
                Citadel,
                )
        self.assertFalse(
                hasattr(
                        ari,
                        "banner",
                        )
                )
        self.assertEqual(
                ari.events,
                [],
                )

        # A later call succeeds: Territory and Citadel both commit, and
        # the rolled-back Base is reapplied cleanly.
        ari.charter = "royal"
        Citadel(ari)

        self.assertIn(
                ari,
                Citadel,
                )
        self.assertIn(
                ari,
                Territory,
                )
        self.assertEqual(
                ari.banner,
                "raised",
                )

    def test_atomic_rollback_keeps_earlier_committed_tags(self) -> None:
        ari = Agent()

        # An earlier, separate call commits Territory on its own.
        Territory(ari)

        self.assertIn(
                ari,
                Territory,
                )

        # A later Citadel call fails; its transaction rolls back, but the
        # Territory committed by the EARLIER call survives untouched.
        with self.assertRaises(TagPreconditionError):
            Citadel(ari)

        self.assertIn(
                ari,
                Territory,
                )
        self.assertNotIn(
                ari,
                Citadel,
                )
        self.assertEqual(
                ari.banner,
                "raised",
                )

    def test_active_preconditions_and_postconditions_run_on_later_tagging(self) -> None:
        ari = Agent()

        Validated(ari)
        ari.allowed = False

        with self.assertRaises(TagPreconditionError):
            Advanced(ari)

        ari.allowed = True
        ari.ready = False

        with self.assertRaises(TagPostconditionError):
            Advanced(ari)

        Exempt(ari)

        self.assertIn(
                ari,
                Exempt,
                )

    def test_postcondition_rejects_and_restores_top_managed_records(self) -> None:
        ari = Agent()
        ari.ready = False

        with self.assertRaises(TagPostconditionError):
            Candidate_Record(ari)

        self.assertNotIn(
                ari,
                Candidate_Record,
                )
        self.assertFalse(
                hasattr(
                        ari,
                        "token",
                        )
                )

    def test_imprints_run_in_order_and_failed_mutation_rolls_back(self) -> None:
        ari = Agent()

        Ordered_Imprints(ari)

        self.assertEqual(
                ari.events,
                [
                    "First",
                    "Second",
                    ],
                )

        with self.assertRaises(TagImprintError):
            Broken_Imprint(ari)

        self.assertNotIn(
                ari,
                Broken_Imprint,
                )
        self.assertEqual(
                ari.events,
                [
                    "First",
                    "Second",
                    ],
                )

    def test_reports_operations_and_their_deletion_follow_the_tag_view(self) -> None:
        ari = Agent()

        Community(ari)

        self.assertEqual(
                Community.colour,
                "green",
                )
        self.assertEqual(
                Community.Greet("Ari"),
                "Community:Ari",
                )
        self.assertEqual(
                ari.Community.colour,
                "green",
                )
        self.assertEqual(
                ari.Community.Greet("Ari"),
                "Community:Ari",
                )

        Silent_Community(ari)

        with self.assertRaises(AttributeError):
            ari.Silent_Community.colour

        with self.assertRaises(AttributeError):
            ari.Silent_Community.Greet

    def test_missing_underlay_and_missing_tag_view_raise_resolution_errors(self) -> None:
        ari = Agent()

        with self.assertRaises(TagResolutionError):
            Missing_Action(ari)

        Person(ari)

        with self.assertRaises(TagResolutionError):
            ari.Tag(Paladin)

    def test_tag_subscription_returns_the_active_agent_view(self) -> None:
        class Wizard(Tag):
            @Record
            def spellcasting_ability(
                    agent,
                    ) -> str:
                return "INT"

            def Cast(
                    agent,
                    ) -> str:
                return "Magic!"

        ari = Agent()

        Wizard(
                ari
                )

        wizard_view = Wizard[
                ari
                ]

        self.assertEqual(
                wizard_view.spellcasting_ability,
                "INT",
                )
        self.assertEqual(
                wizard_view.Cast(),
                "Magic!",
                )

        Wizard.Rip(
                ari
                )

        with self.assertRaisesRegex(
                TagResolutionError,
                "Wizard is not active on Agent",
                ):
            _view = Wizard[
                    ari
                    ]

    def test_tag_subscription_returns_the_active_pin_view(self) -> None:
        class Mage(Tag):
            purpose = Report(
                    "Magic-using character classes"
                    )

        class Wizard(Tag):
            pass

        Mage(
                Wizard
                )

        self.assertEqual(
                Mage[
                        Wizard
                        ].purpose,
                "Magic-using character classes",
                )

        Mage.Rip(
                Wizard
                )

        with self.assertRaisesRegex(
                TagResolutionError,
                "Mage is not active on Wizard",
                ):
            _view = Mage[
                    Wizard
                    ]

    def test_fields_are_non_owning_and_iterable_from_the_tag(self) -> None:
        ari = Agent()
        Field_Member(ari)
        reference = weakref.ref(ari)

        self.assertEqual(
                list(Field_Member.Field),
                [ari],
                )
        self.assertEqual(
                list(Field_Member),
                [ari],
                )
        self.assertIs(
                Field_Member[:],
                Field_Member.Field,
                )
        self.assertEqual(
                list(
                    Field_Member[:]
                    ),
                [
                    ari,
                    ],
                )

        with self.assertRaises(
                TypeError
                ):
            _partial_field = Field_Member[
                    1:
                    ]

        del ari
        gc.collect()

        self.assertIsNone(
                reference(),
                )
        self.assertEqual(
                list(Field_Member.Field),
                [],
                )

    def test_fields_index_equal_agents_by_identity(self) -> None:
        class Equal_Agent:
            def __eq__(
                    left,
                    right,
                    ) -> bool:
                return isinstance(
                        right,
                        Equal_Agent,
                        )

        class Member(Tag):
            pass

        first = Equal_Agent()
        second = Equal_Agent()

        Member(
                first
                )

        self.assertIn(
                first,
                Member.Field,
                )
        self.assertNotIn(
                second,
                Member.Field,
                )

        Member(
                second
                )

        self.assertEqual(
                list(
                    Member.Field
                    ),
                [
                    first,
                    second,
                    ],
                )

        Member.Rip(
                first
                )

        self.assertNotIn(
                first,
                Member.Field,
                )
        self.assertIn(
                second,
                Member.Field,
                )

    def test_special_method_actions_actualize_the_agent(self) -> None:
        ari = Agent()

        Arithmetic(ari)

        self.assertEqual(
                ari + 4,
                5,
                )

    def test_targets_that_cannot_carry_top_state_fail_explicitly(self) -> None:
        target = Slotted_Agent()

        with self.assertRaises(TagCompositionError):
            Person(target)

    def test_reserved_state_collision_fails_without_mutating_host_state(
            self,
            ) -> None:
        class Host:
            def __init__(
                    host,
                    ) -> None:
                host._TAGKIT_STATE = "domain state"

        host = Host()

        with self.assertRaisesRegex(
                TagCompositionError,
                "conflicts with TagKit's private runtime state",
                ):
            Person(host)

        self.assertEqual(
                host._TAGKIT_STATE,
                "domain state",
                )
        self.assertNotIn(
                host,
                Person,
                )

    def test_membership_queries_do_not_actualize_an_untagged_target(self) -> None:
        ari = Agent()

        self.assertNotIn(
                ari,
                Person,
                )
        self.assertFalse(
                hasattr(
                        ari,
                        "_TAGKIT_STATE",
                        )
                )

    # -- Atomic application: pre-existing attribute restore (rule 1) -----

    def test_failed_postcondition_restores_a_preexisting_instance_attribute(self) -> None:
        ari = Agent()
        ari.weapon = "iron sword"
        ari.ready = False

        # Cursed_Blade's Record overwrites the pre-existing `weapon`
        # instance attribute, then its Postcondition fails. Atomic
        # rollback must restore the ORIGINAL value (the line-861 path).
        with self.assertRaises(TagPostconditionError):
            Cursed_Blade(ari)

        self.assertNotIn(
                ari,
                Cursed_Blade,
                )
        self.assertEqual(
                ari.weapon,
                "iron sword",
                )

    def test_failed_tagging_restores_nested_mutable_instance_values(
            self,
            ) -> None:
        class Mutating(Tag):
            @Imprint
            def Change(
                    target,
                    ) -> None:
                target.items[0].append(
                        "provisional"
                        )
                target.items[0] = [
                        "replacement",
                        ]
                target.items.append(
                        [
                            "new",
                            ]
                        )

                raise RuntimeError(
                        "reject"
                        )

        ari = Agent()
        ari.items = [
                [
                    "kept",
                    ],
                ]
        original = ari.items
        nested = ari.items[0]

        with self.assertRaises(TagImprintError):
            Mutating(ari)

        self.assertIs(
                ari.items,
                original,
                )
        self.assertIs(
                ari.items[0],
                nested,
                )
        self.assertEqual(
                ari.items,
                [
                    [
                        "kept",
                        ],
                    ],
                )

    def test_failed_pinning_restores_mutable_tag_values(self) -> None:
        class Profession(Tag):
            choices = [
                    "kept",
                    ]

        class Mutating(Tag):
            @Imprint
            def Change(
                    target,
                    ) -> None:
                target.choices.append(
                        "provisional"
                        )

                raise RuntimeError(
                        "reject"
                        )

        original = Profession.choices

        with self.assertRaises(TagImprintError):
            Mutating(Profession)

        self.assertIs(
                Profession.choices,
                original,
                )
        self.assertEqual(
                Profession.choices,
                [
                    "kept",
                    ],
                )

    def test_failed_tagging_restores_preexisting_slot_values(self) -> None:
        class Slotted:
            __slots__ = (
                    "_TAGKIT_STATE",
                    "__weakref__",
                    "value",
                    )

            def __init__(
                    target,
                    ) -> None:
                target.value = "original"

        class Mutating(Tag):
            @Imprint
            def Change(
                    target,
                    ) -> None:
                target.value = "provisional"

        target = Slotted()

        with self.assertRaises(TagCompositionError):
            Mutating(target)

        self.assertEqual(
                target.value,
                "original",
                )
        self.assertNotIn(
                target,
                Mutating,
                )

    def test_records_use_host_slots_for_lookup_underlay_and_views(
            self,
            ) -> None:
        class Slotted:
            __slots__ = (
                    "__dict__",
                    "__weakref__",
                    "value",
                    )

            def __init__(
                    target,
                    ) -> None:
                target.value = 4

        class Raised(Tag):
            @Record
            @Underlay
            def value(
                    target,
                    prior,
                    ) -> int:
                return (
                        prior()
                        + 3
                        )

        target = Slotted()
        Raised(target)

        self.assertEqual(
                target.value,
                7,
                )
        self.assertEqual(
                Raised[target].value,
                7,
                )
        self.assertTrue(
                Has(
                        target,
                        Raised.value,
                        )
                )

    def test_reentrant_agent_application_fails_atomically(self) -> None:
        class Nested(Tag):
            @Record
            def nested_value(
                    target,
                    ) -> str:
                return "nested"

            def __add__(
                    target,
                    amount: int,
                    ) -> int:
                return amount + 1

        class Outer(Tag):
            @Imprint
            def Apply_Nested(
                    target,
                    ) -> None:
                target.transient = True

                Nested(
                        target
                        )

        ari = Agent()
        original_type = type(ari)

        with self.assertRaises(
                TagImprintError
                ):
            Outer(
                    ari
                    )

        self.assertIs(
                type(ari),
                original_type,
                )
        self.assertNotIn(
                ari,
                Outer,
                )
        self.assertNotIn(
                ari,
                Nested,
                )
        self.assertNotIn(
                ari,
                Outer.Field,
                )
        self.assertNotIn(
                ari,
                Nested.Field,
                )
        self.assertFalse(
                hasattr(
                    ari,
                    "transient",
                    )
                )
        self.assertFalse(
                hasattr(
                    ari,
                    "nested_value",
                    )
                )

    def test_reentrant_active_agent_tag_is_a_strict_noop(self) -> None:
        class Stable(Tag):
            @Imprint
            def Apply_Again(
                    target,
                    ) -> None:
                Stable(
                        target
                        )
                target.applications = (
                        getattr(
                            target,
                            "applications",
                            0,
                            )
                        + 1
                        )

        ari = Agent()

        Stable(
                ari
                )

        self.assertIn(
                ari,
                Stable,
                )
        self.assertEqual(
                ari.applications,
                1,
                )
        self.assertEqual(
                list(
                    Stable.Field
                    ).count(
                        ari
                        ),
                1,
                )

    def test_agent_cannot_rip_itself_during_application(self) -> None:
        class Self_Ripping(Tag):
            @Imprint
            def Leave(
                    target,
                    ) -> None:
                Self_Ripping.Rip(
                        target
                        )

        ari = Agent()

        with self.assertRaises(
                TagImprintError
                ):
            Self_Ripping(
                    ari
                    )

        self.assertNotIn(
                ari,
                Self_Ripping,
                )
        self.assertNotIn(
                ari,
                Self_Ripping.Field,
                )

    def test_failed_agent_tagging_cannot_rip_prior_membership(self) -> None:
        class Existing(Tag):
            pass

        class Rejected(Tag):
            @Imprint
            def Remove_Existing(
                    target,
                    ) -> None:
                Existing.Rip(
                        target
                        )

        ari = Agent()

        Existing(
                ari
                )

        with self.assertRaises(
                TagImprintError
                ):
            Rejected(
                    ari
                    )

        self.assertIn(
                ari,
                Existing,
                )
        self.assertIn(
                ari,
                Existing.Field,
                )
        self.assertNotIn(
                ari,
                Rejected,
                )

    def test_failed_record_names_its_materialization_error(self) -> None:
        class Broken_Record(Tag):
            @Record
            def value(
                    target,
                    ) -> int:
                raise TypeError(
                        "invalid source value"
                        )

        ari = Agent()

        with self.assertRaisesRegex(
                TagCompositionError,
                "Record .*Broken_Record.value failed to materialize",
                ) as caught:
            Broken_Record(
                    ari
                    )

        self.assertIsInstance(
                caught.exception.__cause__,
                TypeError,
                )
        self.assertNotIn(
                ari,
                Broken_Record,
                )
        self.assertFalse(
                hasattr(
                    ari,
                    "value",
                    )
                )

    def test_aliased_record_names_its_declaration(self) -> None:
        @Record
        def Shared_Value(
                target,
                ) -> int:
            raise TypeError(
                    "invalid shared source"
                    )

        class Broken_Record(Tag):
            value = Shared_Value

        ari = Agent()

        with self.assertRaisesRegex(
                TagCompositionError,
                "Record .*Broken_Record.value failed to materialize",
                ):
            Broken_Record(
                    ari
                    )

    def test_record_tag_error_passes_through_unchanged(
            self,
            ) -> None:
        class Coded_Resolution_Error(
                TagResolutionError
                ):
            def __init__(
                    error,
                    code: int,
                    detail: str,
                    ) -> None:
                super().__init__(
                        code,
                        detail,
                        )

                error.code = code
                error.detail = detail

        failure = Coded_Resolution_Error(
                404,
                "source unavailable",
                )

        class Broken_Record(Tag):
            @Record
            def value(
                    target,
                    ) -> int:
                raise failure

        ari = Agent()

        with self.assertRaises(
                Coded_Resolution_Error
                ) as caught:
            Broken_Record(
                    ari
                    )

        self.assertIs(
                caught.exception,
                failure,
                )
        self.assertEqual(
                caught.exception.code,
                404,
                )
        self.assertEqual(
                caught.exception.detail,
                "source unavailable",
                )
        self.assertNotIn(
                ari,
                Broken_Record,
                )

    # -- Rip protocol and redefined stickiness (rule 2) ----------------

    def test_rip_leaves_a_rogue_agent_with_sticky_contributions(self) -> None:
        ari = Agent()

        Squire(ari)

        self.assertIn(
                ari,
                Squire,
                )
        self.assertEqual(
                ari.rank,
                "squire",
                )

        Squire.Rip(ari)

        # Gone from the Field, but Action/Record contributions persist.
        self.assertNotIn(
                ari,
                Squire,
                )
        self.assertEqual(
                ari.rank,
                "squire",
                )

    def test_del_removes_a_record_the_native_way(self) -> None:
        ari = Agent()

        Armed(ari)

        self.assertEqual(
                ari.weapon,
                "arcane staff",
                )

        # Records are removed with the language's own ``del`` -- TOP keeps no
        # verb for it. Tags are ripped; Records are deleted.
        del ari.weapon

        self.assertFalse(
                hasattr(
                        ari,
                        "weapon",
                        )
                )

    def test_rip_action_runs_on_rip_and_resets_a_record(self) -> None:
        ari = Agent()

        Squire(ari)
        Knighted(ari)

        self.assertEqual(
                ari.rank,
                "squire",
                )

        # rank_reset is both a normal Action and a @Rip teardown.
        self.assertEqual(
                ari.rank_reset(),
                "Disrobed",
                )

        ari.rank = "knight"

        Knighted.Rip(ari)

        self.assertNotIn(
                ari,
                Knighted,
                )
        self.assertIsNone(
                ari.rank,
                )

    def test_ripping_a_base_cascades_dependent_shapes(self) -> None:
        ari = Agent()

        Wolf(ari)

        self.assertIn(
                ari,
                Beast,
                )

        Beast.Rip(ari)

        self.assertNotIn(
                ari,
                Wolf,
                )
        self.assertNotIn(
                ari,
                Beast,
                )
        self.assertNotIn(
                ari,
                Wolf.Field,
                )
        self.assertNotIn(
                ari,
                Beast.Field,
                )
        self.assertIsInstance(
                ari,
                Wolf,
                )
        self.assertIsInstance(
                ari,
                Beast,
                )

    def test_base_rip_is_specific_first_and_preserves_other_bases(
            self,
            ) -> None:
        class First_Base(Tag):
            @Rip
            def Leave_First(
                    target,
                    ) -> None:
                target.events.append(
                        "First"
                        )

        class Other_Base(Tag):
            pass

        class Shape(
                First_Base,
                Other_Base,
                ):
            @Rip
            def Leave_Shape(
                    target,
                    ) -> None:
                target.events.append(
                        "Shape"
                        )

        ari = Agent()

        Shape(
                ari
                )
        First_Base.Rip(
                ari
                )

        self.assertEqual(
                ari.events,
                [
                    "Shape",
                    "First",
                    ],
                )
        self.assertNotIn(
                ari,
                Shape,
                )
        self.assertNotIn(
                ari,
                First_Base,
                )
        self.assertIn(
                ari,
                Other_Base,
                )

    def test_ripped_agent_is_not_yielded_by_field_iteration(self) -> None:
        ari = Agent()
        bea = Agent()

        Squire(ari)
        Squire(bea)

        self.assertEqual(
                set(Squire.Field),
                {ari, bea},
                )

        Squire.Rip(ari)

        self.assertEqual(
                list(Squire.Field),
                [bea],
                )
        self.assertEqual(
                list(Squire),
                [bea],
                )

    def test_ripping_an_inactive_tag_raises(self) -> None:
        ari = Agent()

        Squire(ari)

        with self.assertRaises(TagResolutionError):
            Knighted.Rip(ari)

    # -- Retagging after Rip starts a new Tagging (rule 3) ---------------

    def test_reapply_after_rip_restores_membership_and_reruns_imprint(self) -> None:
        ari = Agent()

        Squire(ari)
        Squire.Rip(ari)

        self.assertNotIn(
                ari,
                Squire,
                )

        # A previously ripped Tag starts a new Tagging: membership is
        # restored and the Imprint runs again over sticky Rogue history.
        Squire(ari)

        self.assertIn(
                ari,
                Squire,
                )
        self.assertEqual(
                ari.events,
                [
                    "Squire",
                    "Squire",
                ],
                )

    def test_reapply_after_rip_layers_over_sticky_rogue_action(
            self,
            ) -> None:
        class Host:
            def Work(
                    host,
                    ) -> str:
                return "host"

        class Skilled(Tag):
            @Underlay
            def Work(
                    host,
                    prior,
                    ) -> str:
                return (
                        prior()
                        + "+skilled"
                        )

        host = Host()
        Skilled(host)

        self.assertEqual(
                host.Work(),
                "host+skilled",
                )

        Skilled.Rip(host)
        Skilled(host)

        self.assertEqual(
                host.Work(),
                "host+skilled+skilled",
                )

    # -- Explicit @Underlay with author-chosen parameter names (rule 4) -

    def test_underlay_decorator_extends_an_action_with_any_param_name(self) -> None:
        ari = Agent()

        Politely(ari)

        # Base_Greeting -> Greeter -> Politely, each extending via
        # @Underlay with a parameter named anything but "underlay".
        self.assertEqual(
                ari.Greet(),
                "Hello and hi good day",
                )

    def test_underlay_decorator_extends_a_record_with_any_param_name(self) -> None:
        ari = Agent()

        More_Tally(ari)

        self.assertEqual(
                ari.marks,
                [
                    "one",
                    "two",
                    ],
                )

    # -- Exit protocols: del / Scope / At_Exit --------------------------

    def test_rip_runs_best_effort_on_garbage_collection(self) -> None:
        _DEL_LOG.clear()

        ari = Agent()
        Sentry(ari)

        del ari
        gc.collect()

        # __del__ runs the @Rip teardown when the Agent is collected.
        self.assertEqual(
                _DEL_LOG.count("stood down"),
                1,
                )

    def test_explicit_rip_prevents_a_second_rip_on_collection(self) -> None:
        _DEL_LOG.clear()

        ari = Agent()
        Sentry(ari)
        Sentry.Rip(ari)

        self.assertEqual(
                _DEL_LOG.count("stood down"),
                1,
                )

        del ari
        gc.collect()

        # The Tag was already extracted, so collection does not re-run it.
        self.assertEqual(
                _DEL_LOG.count("stood down"),
                1,
                )

    def test_scope_applies_and_rips_with_guaranteed_teardown(self) -> None:
        _DEL_LOG.clear()

        ari = Agent()

        with Scope(ari, Sentry) as scoped:
            self.assertIs(
                    scoped,
                    ari,
                    )
            self.assertIn(
                    ari,
                    Sentry,
                    )

        self.assertNotIn(
                ari,
                Sentry,
                )
        self.assertEqual(
                _DEL_LOG.count("stood down"),
                1,
                )

    def test_scope_rips_even_when_the_block_raises(self) -> None:
        _DEL_LOG.clear()

        ari = Agent()

        with self.assertRaises(ValueError):
            with Scope(ari, Sentry):
                raise ValueError("boom")

        self.assertNotIn(
                ari,
                Sentry,
                )
        self.assertEqual(
                _DEL_LOG.count("stood down"),
                1,
                )

    def test_scope_reports_cleanup_failures_without_hiding_body_errors(
            self,
            ) -> None:
        class Broken(Tag):
            @Action
            @Rip
            def Release(
                    agent,
                    ) -> None:
                raise RuntimeError(
                        "lock still held"
                        )

        clean_body = Agent()

        with self.assertRaisesRegex(
                TagCompositionError,
                "Scope cleanup failed",
                ):
            with Scope(
                    clean_body,
                    Broken,
                    ):
                pass

        self.assertNotIn(
                clean_body,
                Broken,
                )

        failing_body = Agent()

        try:
            with Scope(
                    failing_body,
                    Broken,
                    ):
                raise ValueError(
                        "body failed"
                        )
        except ValueError as error:
            self.assertEqual(
                    str(error),
                    "body failed",
                    )
            self.assertIsInstance(
                    error.tagkit_cleanup_error,
                    TagCompositionError,
                    )
        else:
            self.fail(
                    "Scope hid the body failure"
                    )

        self.assertNotIn(
                failing_body,
                Broken,
                )

    def test_at_exit_registration_does_not_pin_the_agent(self) -> None:
        ari = Agent()
        Sentry(ari)
        At_Exit(ari)

        reference = weakref.ref(ari)

        del ari
        gc.collect()

        # Registration is weak: it never keeps the Agent alive.
        self.assertIsNone(
                reference(),
                )

    # -- Runtime-type sharing (resource use) ----------------------------

    def test_runtime_types_are_shared_across_agents_of_one_shape(self) -> None:
        ari = Agent()
        bea = Agent()

        Elf(ari)
        Elf(bea)

        # Same (host, leaves) with no special-method Actions: one shared
        # runtime type, not one synthesized per application.
        self.assertIs(
                type(ari),
                type(bea),
                )
        self.assertIsInstance(
                ari,
                Elf,
                )
        self.assertIsInstance(
                ari,
                Person,
                )

    def test_special_method_tag_uses_a_distinct_runtime_type(self) -> None:
        ari = Agent()
        bea = Agent()

        Arithmetic(ari)
        Arithmetic(bea)

        self.assertEqual(
                ari + 1,
                2,
                )
        self.assertEqual(
                bea + 1,
                2,
                )

        # A special-method Action must live on the type, so these are built
        # per agent rather than shared.
        self.assertIsNot(
                type(ari),
                type(bea),
                )

    # -- Application inputs to protocols --------------------------------

    def test_application_inputs_reach_imprints_by_name(self) -> None:
        bond = Agent()

        # MI6-style: Recruit(bond, code="007") -> the Imprint parameter named
        # 'code' receives "007"; the Agent binding 'spy' is positional.
        Recruit(bond, code="007")

        self.assertEqual(
                bond.code,
                "007",
                )

    def test_missing_application_input_defaults_to_none(self) -> None:
        bond = Agent()

        # No 'code' supplied -> the Imprint's 'code' parameter is None, not a
        # function default. The application call is the single source of truth.
        Recruit(bond)

        self.assertIsNone(
                bond.code,
                )

    def test_application_inputs_reach_conditions(self) -> None:
        ari = Agent()

        # Precondition Has_Code(agent, code) sees code=None and rejects.
        with self.assertRaises(TagPreconditionError):
            Coded(ari)

        self.assertNotIn(
                ari,
                Coded,
                )

        Coded(ari, code="x")

        self.assertIn(
                ari,
                Coded,
                )

    # -- isinstance as a reliable HAS-BEEN check ------------------------

    def test_isinstance_is_a_reliable_has_been_check(self) -> None:
        ari = Agent()

        Squire(ari)

        self.assertIsInstance(ari, Squire)
        self.assertIn(ari, Squire)

        Squire.Rip(ari)

        # IS (membership) ends; HAS-BEEN (isinstance) persists.
        self.assertNotIn(ari, Squire)
        self.assertIsInstance(ari, Squire)

        # And it stays reliable through later re-composition -- the runtime
        # type is rebuilt without Squire, but ever-membership endures.
        Knighted(ari)

        self.assertIsInstance(ari, Squire)
        self.assertNotIn(ari, Squire)
        self.assertIsInstance(ari, Knighted)

    # -- Conditions: @Pre/@Post, assert-style, None-pass ----------------

    def test_assert_style_condition_passes_on_no_raise(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)

        self.assertIn(ari, Scholar)
        self.assertEqual(ari.spellbook, "Tome")

    def test_assert_style_precondition_fails_by_raising(self) -> None:
        ari = Agent()
        ari.level = 0                       # assert agent.level > 0 will raise

        with self.assertRaises(TagPreconditionError):
            Scholar(ari)

        self.assertNotIn(ari, Scholar)

    # -- if/assert agent runs Posts; Contract names the detail ----------

    def test_bool_agent_runs_postconditions(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)

        self.assertTrue(bool(ari))          # all Posts hold

        del ari.spellbook                   # Has_Book now fails

        self.assertFalse(bool(ari))         # truthy iff Posts hold

    def test_contract_postconditions_raises_a_detailed_error(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)
        del ari.spellbook

        with self.assertRaises(TagPostconditionError):
            Contract.Postconditions(ari)

    def test_if_agent_inside_a_post_does_not_recurse(self) -> None:
        ari = Agent()

        Reflective(ari)

        # Self_Aware does `if agent`; the reentrancy guard returns True
        # instead of recursing into the Post sweep.
        self.assertTrue(bool(ari))

    # -- Forward-Post: crunch warns, @Underlay strengthens silently -----

    def test_crunching_a_post_without_underlay_warns_and_relaxes(self) -> None:
        ari = Agent()
        ari.strength = 15

        with self.assertWarns(TagContractWarning):
            Bruiser(ari)                    # crunch warns at application

        self.assertIn(ari, Bruiser)         # but it's allowed -- the saw stays in the box

        ari.strength = 22                   # grows past the Base cap of 20

        self.assertTrue(bool(ari))          # Bruiser's relaxed <= 24 holds

    def test_post_underlay_strengthens_without_warning(self) -> None:
        ari = Agent()
        ari.strength = 15

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            Disciplined(ari)

        self.assertFalse(
                any(
                        issubclass(w.category, TagContractWarning)
                        for w in captured
                        )
                )
        self.assertTrue(bool(ari))          # 15 <= 18 and 15 <= 20

        ari.strength = 19

        self.assertFalse(bool(ari))         # 19 > 18: the stronger promise fails

    def test_pre_and_post_are_aliases(self) -> None:
        self.assertIs(Pre, Precondition)
        self.assertIs(Post, Postcondition)

    def test_contract_namespace_checks_pre_post_and_both(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)

        # All hold right after a clean tagging.
        self.assertTrue(Contract.Preconditions(ari))
        self.assertTrue(Contract.Postconditions(ari))
        self.assertTrue(Contract.Conditions(ari))

        del ari.spellbook

        # Conditions() runs Pre then Post, so the Post failure surfaces.
        with self.assertRaises(TagPostconditionError):
            Contract.Conditions(ari)

    def test_contract_status_maps_each_condition_to_its_state(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)

        self.assertEqual(
                Contract.Status(ari),
                {
                    "Level_Over_Zero": True,
                    "Has_Book": True,
                    },
                )

        del ari.spellbook

        status = Contract.Status(ari)
        self.assertTrue(status["Level_Over_Zero"])   # Pre still holds
        self.assertFalse(status["Has_Book"])         # Post now broken
        # Status never raises, even with a broken condition.

    def test_contract_display_renders_the_status(self) -> None:
        ari = Agent()
        ari.level = 1

        Scholar(ari)
        text = Contract.Display(ari)

        self.assertIn("Has_Book", text)
        self.assertIn("Pre:", text)        # sections separated
        self.assertIn("Post:", text)
        self.assertIn("OK", text)

        del ari.spellbook
        self.assertIn("XX", Contract.Display(ari))

    # -- Strict boolean: no truthy/falsy coercion -----------------------

    def test_condition_must_yield_a_strict_boolean(self) -> None:
        ari = Agent()
        ari.spell_slots = 0

        # Returning a raw value (a falsy int) is rejected loudly -- you must
        # write the explicit comparison you mean.
        with self.assertRaises(TagContractError):
            Slotted(ari)

    def test_explicit_existence_check_separates_zero_from_missing(self) -> None:
        zero = Agent()
        zero.spell_slots = 0

        # 0 is a real value: `assert ... is not None` holds.
        Reserved(zero)
        self.assertIn(zero, Reserved)
        self.assertTrue(bool(zero))

        missing = Agent()               # no spell_slots attribute at all

        with self.assertRaises(TagPostconditionError):
            Reserved(missing)           # AttributeError -> fails, distinct from 0


    # -- Contribution existence via `in` -------------------------------

    def test_contribution_existence_via_in(self) -> None:
        ari = Agent()

        Inventory(ari)                     # Inventory contributes an `items` Record

        self.assertIn(Inventory.items, ari)        # Inventory.items in ari -> exists

        other = Agent()
        Field_Member(other)                        # tagged, but contributes no items
        self.assertNotIn(Inventory.items, other)   # -> no items Record

    # -- Neutral runtime composition -----------------------------------

    def test_runtime_type_does_not_inherit_tag_namespaces(self) -> None:
        class Semantic(Tag):
            Only_Tag = "private to the semantic category"
            Shared = Report("field knowledge")

            @Operation
            def Catalog(
                    tag,
                    ) -> str:
                return tag.__name__

            @Action
            def Act(
                    agent,
                    ) -> str:
                return "acting"

        ari = Agent()

        Semantic(ari)

        self.assertEqual(
                ari.Act(),
                "acting",
                )
        self.assertEqual(
                Semantic[ari].Shared,
                "field knowledge",
                )
        self.assertEqual(
                Semantic[ari].Catalog(),
                "Semantic",
                )
        self.assertFalse(
                hasattr(
                        ari,
                        "Shared",
                        )
                )
        self.assertFalse(
                hasattr(
                        ari,
                        "Catalog",
                        )
                )
        self.assertFalse(
                hasattr(
                        ari,
                        "Only_Tag",
                        )
                )
        self.assertNotIn(
                Semantic,
                type(ari).__mro__,
                )
        self.assertIsInstance(
                ari,
                Semantic,
                )

    def test_opposite_tag_orders_do_not_create_runtime_mro_conflicts(
            self,
            ) -> None:
        class X(Tag):
            pass

        class Y(Tag):
            pass

        class Forward(X, Y):
            pass

        class Reverse(Y, X):
            pass

        ari = Agent()

        Forward(ari)
        Reverse(ari)

        for tag in (
                X,
                Y,
                Forward,
                Reverse,
                ):
            self.assertIn(
                    ari,
                    tag,
                    )
            self.assertIsInstance(
                    ari,
                    tag,
                    )

    def test_top_managed_dunders_cannot_be_replaced(self) -> None:
        class Unsafe(Tag):
            @Action
            def __del__(
                    agent,
                    ) -> None:
                pass

        ari = Agent()
        original_type = type(ari)

        with self.assertRaisesRegex(
                TagCompositionError,
                "TOP-managed runtime protocol.*'__del__'",
                ):
            Unsafe(ari)

        self.assertIs(
                type(ari),
                original_type,
                )
        self.assertNotIn(
                ari,
                Unsafe,
                )

    # -- Read-only and commit-only membership --------------------------

    def test_field_is_a_read_only_population_view(self) -> None:
        class Member(Tag):
            pass

        ari = Agent()
        field = Member[:]

        self.assertFalse(
                hasattr(
                        field,
                        "Add",
                        )
                )
        self.assertFalse(
                hasattr(
                        field,
                        "Remove",
                        )
                )
        self.assertEqual(
                len(field),
                0,
                )

        Member(ari)

        self.assertEqual(
                len(field),
                1,
                )
        self.assertIn(
                ari,
                field,
                )

        Member.Rip(ari)

        self.assertEqual(
                len(field),
                0,
                )

    def test_failed_precondition_never_exposes_provisional_membership(
            self,
            ) -> None:
        observed: dict[str, object] = {}

        class Pending(Tag):
            def Act(
                    agent,
                    ) -> str:
                return "provisional"

            @Pre
            def Remains_Provisional(
                    agent,
                    ) -> bool:
                observed["in_tag"] = agent in Pending
                observed["in_field"] = agent in Pending[:]
                observed["has_been"] = isinstance(
                        agent,
                        Pending,
                        )
                observed["has_action"] = Has(
                        agent,
                        Pending.Act,
                        )

                try:
                    Pending[agent]
                except Exception as error:
                    observed["view_error"] = type(error)

                return False

        ari = Agent()

        with self.assertRaises(TagPreconditionError):
            Pending(ari)

        self.assertEqual(
                observed,
                {
                    "in_tag": False,
                    "in_field": False,
                    "has_been": False,
                    "has_action": False,
                    "view_error": TagResolutionError,
                    },
                )
        self.assertNotIn(
                ari,
                Pending,
                )
        self.assertNotIsInstance(
                ari,
                Pending,
                )

    def test_failed_shape_never_publishes_its_missing_base(self) -> None:
        observed: dict[str, bool] = {}

        class Base(Tag):
            pass

        class Shape(Base):
            @Pre
            def Reject(
                    agent,
                    ) -> bool:
                observed["active"] = agent in Base
                observed["field"] = agent in Base[:]
                observed["history"] = isinstance(
                        agent,
                        Base,
                        )

                return False

        ari = Agent()

        with self.assertRaises(TagPreconditionError):
            Shape(ari)

        self.assertEqual(
                observed,
                {
                    "active": False,
                    "field": False,
                    "history": False,
                    },
                )
        self.assertNotIn(
                ari,
                Base,
                )
        self.assertNotIsInstance(
                ari,
                Base,
                )

    def test_failed_pin_shape_never_publishes_its_missing_base(
            self,
            ) -> None:
        observed: dict[str, bool] = {}

        class Target(Tag):
            pass

        class Base_Pin(Tag):
            pass

        class Shape_Pin(Base_Pin):
            @Pre
            def Reject(
                    target,
                    ) -> bool:
                observed["active"] = target in Base_Pin
                observed["field"] = target in Base_Pin[:]
                observed["history"] = isinstance(
                        target,
                        Base_Pin,
                        )

                return False

        with self.assertRaises(TagPreconditionError):
            Shape_Pin(Target)

        self.assertEqual(
                observed,
                {
                    "active": False,
                    "field": False,
                    "history": False,
                    },
                )
        self.assertNotIn(
                Target,
                Base_Pin,
                )
        self.assertNotIsInstance(
                Target,
                Base_Pin,
                )

    # -- Inputs belong to their own Tagging ----------------------------

    def test_conditions_keep_inputs_from_each_tagging(self) -> None:
        class Coded_Base(Tag):
            @Pre
            def Correct_Code(
                    agent,
                    code,
                    ) -> bool:
                return code == "base"

            @Post
            def Stable_Code(
                    agent,
                    code,
                    ) -> bool:
                return code == "base"

        class Coded_Shape(Coded_Base):
            @Pre
            @Underlay
            def Correct_Code(
                    agent,
                    prior,
                    code,
                    ) -> bool:
                return (
                        prior()
                        and code == "shape"
                        )

            @Post
            @Underlay
            def Stable_Code(
                    agent,
                    prior,
                    code,
                    ) -> bool:
                return (
                        prior()
                        and code == "shape"
                        )

        class Unrelated(Tag):
            pass

        ari = Agent()

        Coded_Base(
                ari,
                code="base",
                )
        Coded_Shape(
                ari,
                code="shape",
                )
        Unrelated(
                ari,
                code="unrelated",
                )

        self.assertTrue(
                Contract.Conditions(ari)
                )

    def test_pin_conditions_keep_inputs_from_each_pinning(self) -> None:
        class Profession(Tag):
            pass

        class Base_Pin(Tag):
            @Pre
            def Correct_Code(
                    target,
                    code,
                    ) -> bool:
                return code == "base"

        class Shaped_Pin(Base_Pin):
            @Pre
            @Underlay
            def Correct_Code(
                    target,
                    prior,
                    code,
                    ) -> bool:
                return (
                        prior()
                        and code == "shape"
                        )

        class Unrelated_Pin(Tag):
            pass

        Base_Pin(
                Profession,
                code="base",
                )
        Shaped_Pin(
                Profession,
                code="shape",
                )
        Unrelated_Pin(
                Profession,
                code="unrelated",
                )

        self.assertTrue(
                Contract.Preconditions(Profession)
                )

    def test_record_builders_receive_application_inputs(self) -> None:
        class Named(Tag):
            @Record
            def title(
                    agent,
                    prefix,
                    ) -> str:
                return prefix

        class Ranked(Named):
            @Record
            @Underlay
            def title(
                    agent,
                    prior,
                    rank,
                    ) -> str:
                return (
                        prior()
                        + rank
                        )

        ari = Agent()

        Ranked(
                ari,
                prefix="Captain ",
                rank="of the Guard",
                )

        self.assertEqual(
                ari.title,
                "Captain of the Guard",
                )

    def test_pin_report_builders_receive_pinning_inputs(self) -> None:
        class Profession(Tag):
            pass

        class Headed(Tag):
            @Record
            def heading(
                    target,
                    prefix,
                    ) -> str:
                return (
                        prefix
                        + target.__name__
                        )

        Headed(
                Profession,
                prefix="Guild: ",
                )

        self.assertEqual(
                Profession.heading,
                "Guild: Profession",
                )
        self.assertTrue(
                Has(
                        Profession,
                        Headed.heading,
                        )
                )

    # -- Independent contribution adapters ----------------------------

    def test_contribution_decorators_do_not_mutate_shared_callables(
            self,
            ) -> None:
        def Shared(
                target,
                ) -> str:
            return "shared value"

        shared_action = Action(Shared)
        shared_record = Record(Shared)

        class Acting(Tag):
            Use = shared_action

        class Storing(Tag):
            Value = shared_record

        actor = Agent()
        record = Agent()

        Acting(actor)
        Storing(record)

        self.assertIsNot(
                Shared,
                shared_action,
                )
        self.assertIsNot(
                Shared,
                shared_record,
                )
        self.assertIsNot(
                shared_action,
                shared_record,
                )
        self.assertEqual(
                actor.Use(),
                "shared value",
                )
        self.assertEqual(
                record.Value,
                "shared value",
                )
        self.assertEqual(
                Shared(record),
                "shared value",
                )
        self.assertTrue(
                Has(
                        actor,
                        Acting.Use,
                        )
                )
        self.assertTrue(
                Has(
                        record,
                        Storing.Value,
                        )
                )

    def test_contribution_adapters_preserve_callable_kind(self) -> None:
        async def Awaitable(
                target,
                ) -> str:
            return "awaited"

        def Generated(
                target,
                ):
            yield target

        adapted_async = Action(Awaitable)
        adapted_generator = Action(Generated)

        self.assertTrue(
                inspect.iscoroutinefunction(
                        adapted_async
                        )
                )
        self.assertTrue(
                inspect.isgeneratorfunction(
                        adapted_generator
                        )
                )
        self.assertEqual(
                inspect.signature(adapted_async),
                inspect.signature(Awaitable),
                )
        self.assertEqual(
                inspect.signature(adapted_generator),
                inspect.signature(Generated),
                )

    def test_unhashable_callable_objects_compose_as_actions(self) -> None:
        class Strategy:
            __hash__ = None

            def __call__(
                    strategy,
                    agent,
                    ) -> str:
                return "strategy"

        class Strategic(Tag):
            Work = Strategy()

        ari = Agent()
        Strategic(ari)

        self.assertEqual(
                ari.Work(),
                "strategy",
                )

    def test_has_reports_only_the_visible_overlaid_contribution(
            self,
            ) -> None:
        class First(Tag):
            def Work(
                    agent,
                    ) -> str:
                return "first"

        class Second(Tag):
            def Work(
                    agent,
                    ) -> str:
                return "second"

        ari = Agent()
        First(ari)

        self.assertTrue(
                Has(
                        ari,
                        First.Work,
                        )
                )

        with warnings.catch_warnings():
            warnings.simplefilter(
                    "ignore",
                    TagOverwriteWarning,
                    )
            Second(ari)

        self.assertFalse(
                Has(
                        ari,
                        First.Work,
                        )
                )
        self.assertTrue(
                Has(
                        ari,
                        Second.Work,
                        )
                )

    def test_has_reads_the_committed_overlay_during_rejected_tagging(
            self,
            ) -> None:
        observed: dict[str, object] = {}

        class Host:
            def __contains__(
                    host,
                    probe,
                    ) -> bool:
                return False

        class Old(Tag):
            def Work(
                    agent,
                    ) -> str:
                return "old"

        class Rejecting(Tag):
            def Work(
                    agent,
                    ) -> str:
                return "new"

            @Pre
            def Reject(
                    agent,
                    ) -> bool:
                observed["old"] = Has(
                        agent,
                        Old.Work,
                        )
                observed["new"] = Has(
                        agent,
                        Rejecting.Work,
                        )
                observed["old_in"] = Old.Work in agent
                observed["new_in"] = Rejecting.Work in agent
                observed["direct"] = agent.Work()

                return False

        ari = Host()
        Old(ari)

        with warnings.catch_warnings():
            warnings.simplefilter(
                    "ignore",
                    TagOverwriteWarning,
                    )

            with self.assertRaises(TagPreconditionError):
                Rejecting(ari)

        self.assertEqual(
                observed,
                {
                    "old": True,
                    "new": False,
                    "old_in": True,
                    "new_in": False,
                    "direct": "new",
                    },
                )
        self.assertTrue(
                Has(
                        ari,
                        Old.Work,
                        )
                )
        self.assertFalse(
                Has(
                        ari,
                        Rejecting.Work,
                        )
                )

    def test_has_reads_the_committed_overlay_during_rejected_pinning(
            self,
            ) -> None:
        observed: dict[str, object] = {}

        class Profession(Tag):
            pass

        class Old(Tag):
            def Work(
                    target,
                    ) -> str:
                return "old"

        class Rejecting(Tag):
            def Work(
                    target,
                    ) -> str:
                return "new"

            @Pre
            def Reject(
                    target,
                    ) -> bool:
                observed["old"] = Has(
                        target,
                        Old.Work,
                        )
                observed["new"] = Has(
                        target,
                        Rejecting.Work,
                        )
                observed["direct"] = target.Work()

                return False

        Old(Profession)

        with warnings.catch_warnings():
            warnings.simplefilter(
                    "ignore",
                    TagOverwriteWarning,
                    )

            with self.assertRaises(TagPreconditionError):
                Rejecting(Profession)

        self.assertEqual(
                observed,
                {
                    "old": True,
                    "new": False,
                    "direct": "new",
                    },
                )
        self.assertTrue(
                Has(
                        Profession,
                        Old.Work,
                        )
                )
        self.assertFalse(
                Has(
                        Profession,
                        Rejecting.Work,
                        )
                )

    # -- Procedural and functional composition ------------------------

    def test_functional_facade_composes_without_target_methods(self) -> None:
        class First(Tag):
            @Imprint
            def Mark(
                    agent,
                    token,
                    ) -> None:
                agent.events.append(
                        f"first:{token}"
                        )

        class Domain_Names(Tag):
            def Tags(
                    agent,
                    ) -> str:
                return "domain Tags"

            def Has(
                    agent,
                    ) -> str:
                return "domain Has"

        ari = Agent()

        result = Apply(
                ari,
                First,
                Domain_Names,
                token="x",
                )

        self.assertIs(
                result,
                ari,
                )
        self.assertEqual(
                ari.events,
                [
                    "first:x",
                    ],
                )
        self.assertEqual(
                ari.Tags(),
                "domain Tags",
                )
        self.assertEqual(
                ari.Has(),
                "domain Has",
                )
        self.assertEqual(
                set(Tags(ari)),
                {
                    First,
                    Domain_Names,
                    },
                )
        self.assertTrue(
                Has(
                        ari,
                        First,
                        Domain_Names,
                        "First",
                        )
                )

        agents = [
                Agent(),
                Agent(),
                ]

        self.assertEqual(
                list(
                        map(
                                First,
                                agents,
                                )
                        ),
                agents,
                )

    def test_host_protocols_remain_available_after_tagging(self) -> None:
        class Root(Tag):
            pass

        class Host:
            FORM_ROOTS = (
                    Root,
                    )

            def __getattribute__(
                    host,
                    name,
                    ):
                if name == "native":
                    return "custom getattribute"

                return object.__getattribute__(
                        host,
                        name,
                        )

            def Tags(
                    host,
                    ) -> str:
                return "host Tags"

            def Has(
                    host,
                    ) -> str:
                return "host Has"

            def AppliedTags(
                    host,
                    ) -> str:
                return "host AppliedTags"

            def __contains__(
                    host,
                    value,
                    ) -> bool:
                return value == 7

            def __or__(
                    host,
                    value,
                    ) -> str:
                return (
                        "host|"
                        + value
                        )

            def __bool__(
                    host,
                    ) -> bool:
                return False

        class Semantic(Root):
            pass

        class Promised(Tag):
            @Post
            def Holds(
                    host,
                    ) -> bool:
                return True

        host = Host()
        Semantic(host)

        self.assertEqual(
                host.Tags(),
                "host Tags",
                )
        self.assertEqual(
                host.Has(),
                "host Has",
                )
        self.assertEqual(
                host.AppliedTags(),
                "host AppliedTags",
                )
        self.assertEqual(
                host.FORM_ROOTS,
                (
                    Root,
                    ),
                )
        self.assertEqual(
                host.native,
                "custom getattribute",
                )
        self.assertEqual(
                Tags(host),
                (
                    Semantic,
                    ),
                )
        self.assertTrue(
                7 in host
                )
        self.assertFalse(
                8 in host
                )
        self.assertTrue(
                Has(
                        host,
                        "Semantic",
                        )
                )
        self.assertEqual(
                host | "value",
                "host|value",
                )
        self.assertFalse(
                bool(host)
                )

        Promised(host)

        self.assertTrue(
                bool(host)
                )

    def test_host_instance_values_and_access_policy_win_name_collisions(
            self,
            ) -> None:
        class Root(Tag):
            pass

        class Host:
            FORM_ROOTS = (
                    Root,
                    )

            def __init__(
                    host,
                    ) -> None:
                host.FORM_ROOTS = ()
                host.Tags = "instance Tags"

            def __getattribute__(
                    host,
                    name,
                    ):
                if name == "Has":
                    return "policy Has"

                return object.__getattribute__(
                        host,
                        name,
                        )

            def Tags(
                    host,
                    ) -> str:
                return "class Tags"

        class Semantic(Tag):
            pass

        host = Host()
        Semantic(host)

        self.assertEqual(
                host.FORM_ROOTS,
                (),
                )
        self.assertEqual(
                host.Tags,
                "instance Tags",
                )
        self.assertEqual(
                host.Has,
                "policy Has",
                )
        self.assertTrue(
                Has(
                        host,
                        Semantic,
                        )
                )

    def test_descriptor_host_protocols_remain_available_after_tagging(
            self,
            ) -> None:
        class Descriptor_Host:
            @staticmethod
            def __bool__() -> bool:
                return False

            @staticmethod
            def __or__(
                    value,
                    ) -> str:
                return (
                        "descriptor|"
                        + value
                        )

            @classmethod
            def __contains__(
                    host_type,
                    value,
                    ) -> bool:
                return (
                        issubclass(
                                host_type,
                                Descriptor_Host,
                                )
                        and value == 7
                        )

        class Semantic(Tag):
            pass

        host = Descriptor_Host()
        Semantic(host)

        self.assertFalse(
                bool(host)
                )
        self.assertEqual(
                host | "value",
                "descriptor|value",
                )
        self.assertTrue(
                7 in host
                )
        self.assertFalse(
                8 in host
                )

    def test_disabled_host_protocols_remain_disabled_after_tagging(
            self,
            ) -> None:
        class Disabled_Host:
            __bool__ = None
            __getattr__ = None
            __ior__ = None
            __or__ = None

        class Reflected:
            def __ror__(
                    value,
                    other,
                    ) -> str:
                return "reflected"

        class Semantic(Tag):
            pass

        host = Disabled_Host()
        reflected = Reflected()

        for operation in (
                lambda: bool(host),
                lambda: getattr(
                        host,
                        "missing",
                        ),
                lambda: operator.or_(
                        host,
                        reflected,
                        ),
                lambda: operator.ior(
                        host,
                        reflected,
                        ),
                ):
            with self.assertRaises(TypeError):
                operation()

        Semantic(host)

        for operation in (
                lambda: bool(host),
                lambda: getattr(
                        host,
                        "missing",
                        ),
                lambda: operator.or_(
                        host,
                        reflected,
                        ),
                lambda: operator.ior(
                        host,
                        reflected,
                        ),
                ):
            with self.assertRaises(TypeError):
                operation()

    def test_host_truth_protocol_errors_remain_native_after_tagging(
            self,
            ) -> None:
        class Bad_Bool:
            def __bool__(
                    host,
                    ):
                return 1

        class Bad_Length:
            def __len__(
                    host,
                    ):
                return -1

        class Float_Length:
            def __len__(
                    host,
                    ):
                return 1.5

        class Semantic(Tag):
            pass

        for host, error_type in (
                (
                    Bad_Bool(),
                    TypeError,
                    ),
                (
                    Bad_Length(),
                    ValueError,
                    ),
                (
                    Float_Length(),
                    TypeError,
                    ),
                ):
            with self.assertRaises(error_type):
                bool(host)

            Semantic(host)

            with self.assertRaises(error_type):
                bool(host)

    def test_descriptor_host_finalizers_remain_available_after_tagging(
            self,
            ) -> None:
        events: list[str] = []

        class Static_Host:
            @staticmethod
            def __del__() -> None:
                events.append(
                        "static"
                        )

        class Class_Host:
            @classmethod
            def __del__(
                    host_type,
                    ) -> None:
                if issubclass(
                        host_type,
                        Class_Host,
                        ):
                    events.append(
                            "class"
                            )

        class Semantic(Tag):
            pass

        static_host = Static_Host()
        class_host = Class_Host()
        Semantic(static_host)
        Semantic(class_host)

        static_host.__del__()
        class_host.__del__()

        self.assertEqual(
                events,
                [
                    "static",
                    "class",
                    ],
                )

    def test_callable_host_descriptors_can_supply_action_underlays(
            self,
            ) -> None:
        class Callable_Descriptor:
            def __get__(
                    descriptor,
                    host,
                    host_type,
                    ):
                if host is None:
                    return descriptor

                return lambda: "host"

        class Host:
            Work = Callable_Descriptor()

        class Refined(Tag):
            @Underlay
            def Work(
                    host,
                    prior,
                    ) -> str:
                return (
                        prior()
                        + "+tag"
                        )

        host = Host()
        Refined(host)

        self.assertEqual(
                host.Work(),
                "host+tag",
                )

    def test_noncallable_host_descriptor_rejects_action_underlay(
            self,
            ) -> None:
        class Host:
            @property
            def Work(
                    host,
                    ) -> str:
                return "data"

        class Refined(Tag):
            @Underlay
            def Work(
                    host,
                    prior,
                    ) -> str:
                return prior()

        host = Host()

        with self.assertRaisesRegex(
                TagResolutionError,
                "requires a visible Underlay",
                ):
            Refined(host)

        self.assertNotIn(
                host,
                Refined,
                )

    def test_arbitrary_descriptor_host_finalizer_survives_tagging(
            self,
            ) -> None:
        events: list[str] = []

        class Finalizer_Descriptor:
            def __get__(
                    descriptor,
                    host,
                    host_type,
                    ):
                return lambda: events.append(
                        "descriptor"
                        )

        class Host:
            __del__ = Finalizer_Descriptor()

        class Semantic(Tag):
            pass

        host = Host()
        Semantic(host)
        host.__del__()

        self.assertEqual(
                events,
                [
                    "descriptor",
                    ],
                )

    def test_tag_length_drives_truth_without_postconditions(self) -> None:
        class Empty(Tag):
            def __len__(
                    agent,
                    ) -> int:
                return 0

        ari = Agent()
        Empty(ari)

        self.assertEqual(
                len(ari),
                0,
                )
        self.assertFalse(
                bool(ari)
                )

    def test_native_containment_fallbacks_remain_available_after_tagging(
            self,
            ) -> None:
        class Iteration_Host:
            def __iter__(
                    host,
                    ):
                return iter(
                        (
                            3,
                            7,
                            )
                        )

        class Indexed_Host:
            def __getitem__(
                    host,
                    index,
                    ):
                values = (
                        3,
                        7,
                        )

                if index >= len(values):
                    raise IndexError(index)

                return values[index]

        class Semantic(Tag):
            pass

        for host in (
                Iteration_Host(),
                Indexed_Host(),
                ):
            self.assertTrue(
                    7 in host
                    )
            self.assertFalse(
                    8 in host
                    )

            Semantic(host)

            self.assertTrue(
                    7 in host
                    )
            self.assertFalse(
                    8 in host
                    )

    def test_apply_validates_all_tags_before_mutating(self) -> None:
        class Valid(Tag):
            pass

        ari = Agent()

        with self.assertRaises(TypeError):
            Apply(
                    ari,
                    Valid,
                    object(),
                    )

        self.assertNotIn(
                ari,
                Valid,
                )

    def test_first_tag_candidate_actions_are_visible_to_its_contract(
            self,
            ) -> None:
        class Ready(Tag):
            def Is_Ready(
                    agent,
                    ) -> bool:
                return True

            @Post
            def Can_Act(
                    agent,
                    ) -> bool:
                return agent.Is_Ready()

        ari = Agent()
        Ready(ari)

        self.assertIn(
                ari,
                Ready,
                )
        self.assertTrue(
                ari.Is_Ready()
                )

    # -- Scope owns its membership delta -------------------------------

    def test_scope_owns_exactly_its_membership_delta(self) -> None:
        class Base(Tag):
            pass

        class Shape(Base):
            pass

        fresh = Agent()

        with Scope(
                fresh,
                Shape,
                ):
            self.assertIn(
                    fresh,
                    Base,
                    )
            self.assertIn(
                    fresh,
                    Shape,
                    )

        self.assertNotIn(
                fresh,
                Base,
                )
        self.assertNotIn(
                fresh,
                Shape,
                )

        borrowed = Agent()
        Base(borrowed)

        with Scope(
                borrowed,
                Shape,
                ):
            self.assertIn(
                    borrowed,
                    Shape,
                    )

        self.assertIn(
                borrowed,
                Base,
                )
        self.assertNotIn(
                borrowed,
                Shape,
                )

    def test_scope_setup_failure_cleans_only_owned_memberships(self) -> None:
        class Existing(Tag):
            pass

        class Temporary(Tag):
            pass

        class Rejecting(Tag):
            @Pre
            def Reject(
                    agent,
                    ) -> bool:
                return False

        ari = Agent()
        Existing(ari)

        with self.assertRaises(TagPreconditionError):
            with Scope(
                    ari,
                    Existing,
                    Temporary,
                    Rejecting,
                    ):
                self.fail(
                        "Rejecting should prevent Scope entry"
                        )

        self.assertIn(
                ari,
                Existing,
                )
        self.assertNotIn(
                ari,
                Temporary,
                )
        self.assertNotIn(
                ari,
                Rejecting,
                )

    # -- Reentrant diagnostics and complete teardown ------------------

    def test_contract_status_stops_reentrant_diagnostics(self) -> None:
        calls: list[str] = []

        class Reflective(Tag):
            @Post
            def Stable(
                    agent,
                    ) -> bool:
                calls.append("Stable")
                Contract.Status(agent)

                return True

        ari = Agent()
        Reflective(ari)
        calls.clear()

        self.assertEqual(
                Contract.Status(ari),
                {
                    "Stable": True,
                    },
                )
        self.assertEqual(
                calls,
                [
                    "Stable",
                    ],
                )

    def test_rip_runs_every_teardown_before_reporting_failure(self) -> None:
        events: list[str] = []

        class Equipped(Tag):
            @Action
            @Rip
            def Break(
                    agent,
                    ) -> None:
                events.append("Break")

                raise RuntimeError("broken teardown")

            @Action
            @Rip
            def Stow(
                    agent,
                    ) -> None:
                events.append("Stow")

        ari = Agent()
        Equipped(ari)

        with self.assertRaises(TagCompositionError):
            Equipped.Rip(ari)

        self.assertEqual(
                events,
                [
                    "Break",
                    "Stow",
                    ],
                )
        self.assertNotIn(
                ari,
                Equipped,
                )


if __name__ == "__main__":
    unittest.main()
