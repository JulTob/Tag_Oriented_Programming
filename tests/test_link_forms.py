"""The Link class header records ordered TOP turns, not a Python MRO."""

import gc
import asyncio
import unittest
import weakref

from TopKit import Record
from TopKit import Post
from TopKit import Rip
from TopKit import Tag
from TopKit import TagDeclarationError
from TopKit import TagResolutionError
from TopKit.fields import FIELD_SEAT
from TopKit.link_forms import Link
from TopKit.link_forms import _Relation
from TopKit.link_forms import _resolve_header
from TopKit.link_forms import _resolve_seat
from TopKit.link_forms import _seat_context
from TopKit.link_forms import agent
from TopKit.link_forms import contact


class Host:
    pass


class LinkFormTests(unittest.TestCase):

    def test_mixed_header_preserves_order_and_only_own_declarations(self):
        events = []

        class Network(Tag):
            @Record
            def base_record(target):
                return 7

            def __init_subclass__(cls):
                events.append("Python subclass hook")

        @Link(agent, contact)
        class Trusts(Network, agent.Knows, contact.Knows):
            @Record
            def since(agent, contact, *, since=2026):
                return since

        self.assertIsInstance(Trusts, _Relation)
        self.assertEqual(Trusts.header[0], Network)
        self.assertEqual(Trusts.header[1].Spelled(), "agent.Knows")
        self.assertEqual(Trusts.header[2].Spelled(), "contact.Knows")
        self.assertIn("since", Trusts.namespace)
        self.assertNotIn("base_record", Trusts.namespace)
        self.assertNotIn(FIELD_SEAT, Trusts.namespace)
        self.assertFalse(hasattr(Trusts, "base_record"))
        self.assertFalse(hasattr(Trusts, "__mro__"))
        self.assertEqual(events, [])

    def test_ordinary_header_rebuilds_blueprint_after_python_class_creation(self):
        events = []

        class Network(Tag):
            @Record
            def identifier(target):
                return 1

            def __init_subclass__(cls):
                events.append("Python subclass hook")

        @Link(agent, contact)
        class Carries(Network):
            own = 4

        self.assertEqual(Carries.header, (Network,))
        self.assertEqual(Carries.namespace["own"], 4)
        self.assertNotIn("identifier", Carries.namespace)
        self.assertNotIn(FIELD_SEAT, Carries.namespace)
        self.assertFalse(hasattr(Carries, "identifier"))
        self.assertFalse(hasattr(Carries, "__mro__"))
        self.assertEqual(events, ["Python subclass hook"])

    def test_root_header_has_no_prior_turn(self):
        @Link(agent, contact)
        class Carries(Tag):
            pass

        self.assertEqual(Carries.header, ())
        self.assertEqual(list(_resolve_header(Carries, Host(), Host())), [])

    def test_nested_relations_and_ordinary_tags_remain_distinct(self):
        class Social(Tag):
            @Link(agent, contact)
            class Knows(Tag):
                pass

            class Nested(Tag):
                pass

        self.assertIsInstance(Social.Knows, _Relation)
        self.assertIsInstance(Social.Nested, type)

    def test_turns_resolve_after_previous_turn_can_supply_a_later_link(self):
        class Network(Tag):
            pass

        class Knows(Tag):
            pass

        @Link(agent, contact)
        class Trusts(Network, contact.Knows):
            pass

        target = Host()
        turns = _resolve_header(Trusts, Host(), target)
        self.assertIs(next(turns), Network)
        target.Knows = Knows
        self.assertIs(next(turns), Knows)
        with self.assertRaises(StopIteration):
            next(turns)

    def test_contact_selector_preserves_contact_as_application_target(self):
        seen = []

        class Knows(Tag):
            @Record
            def marker(target):
                seen.append(target)
                return 1

        @Link(agent, contact)
        class Trusts(contact.Knows):
            pass

        owner, target = Host(), Host()
        target.Knows = Knows
        for selected in _resolve_header(Trusts, owner, target):
            selected(target)

        self.assertEqual(seen, [target])
        self.assertNotIn(owner, Knows[:])
        self.assertIn(target, Knows[:])

    def test_missing_selector_is_a_resolution_failure_at_its_turn(self):
        class Network(Tag):
            pass

        @Link(agent, contact)
        class Trusts(Network, contact.Knows):
            pass

        turns = _resolve_header(Trusts, Host(), Host())
        self.assertIs(next(turns), Network)
        with self.assertRaisesRegex(TagResolutionError, "contact.Knows") as failure:
            next(turns)
        self.assertIsInstance(failure.exception.__cause__, AttributeError)

    def test_selector_must_resolve_to_a_tag(self):
        @Link(agent, contact)
        class Trusts(agent.Knows):
            pass

        owner = Host()
        owner.Knows = lambda target: None
        with self.assertRaises(TagResolutionError):
            list(_resolve_header(Trusts, owner, Host()))

    def test_concrete_link_reference_resolves_live_without_retaining_owner(self):
        class Coordinate:
            def __init__(coordinate, owner):
                coordinate.owner = weakref.ref(owner)

            def Resolve(coordinate):
                owner = coordinate.owner()
                if owner is None:
                    raise TagResolutionError("Link owner has ended")
                return owner.current

        owner = Host()
        class Registry(Tag):
            pass
        class Replacement(Tag):
            pass
        owner.current = Registry
        Registry._topkit_link_coordinate = Coordinate(owner)

        @Link(agent, contact)
        class Trusts(Registry):
            pass

        self.assertEqual(list(_resolve_header(Trusts, Host(), Host())), [Registry])
        owner.current = Replacement
        self.assertEqual(list(_resolve_header(Trusts, Host(), Host())), [Replacement])
        retained = weakref.ref(owner)
        del owner
        gc.collect()
        self.assertIsNone(retained())
        with self.assertRaisesRegex(TagResolutionError, "owner has ended"):
            list(_resolve_header(Trusts, Host(), Host()))

    def test_python_still_refuses_inconsistent_ordinary_only_header(self):
        class Left(Tag):
            pass
        class Right(Tag):
            pass
        class LR(Left, Right):
            pass
        class RL(Right, Left):
            pass

        with self.assertRaises(TypeError):
            @Link(agent, contact)
            class Trusts(LR, RL):
                pass

    def test_relation_is_not_callable_and_not_a_bare_form_entry(self):
        @Link(agent, contact)
        class Knows(Tag):
            pass

        with self.assertRaisesRegex(TagDeclarationError, "blueprint"):
            Knows(Host())
        with self.assertRaisesRegex(TagDeclarationError, "actual Link"):
            @Link(agent, contact)
            class Trusts(Knows):
                pass

    def test_link_requires_exact_two_canonical_seats(self):
        for seats in ((), (Tag,), (contact, agent), (agent, Host())):
            with self.subTest(seats=seats), self.assertRaises(TagDeclarationError):
                Link(*seats)

    def test_plain_python_class_is_not_a_tag_turn(self):
        with self.assertRaises(TagDeclarationError):
            @Link(agent, contact)
            class Trusts(Host, agent.Knows):
                pass

    def test_symbolic_header_keeps_invalid_rip_and_condition_refusals(self):
        with self.assertRaises(TagDeclarationError):
            @Link(agent, contact)
            class Trusts(agent.Knows):
                @Rip
                @Record
                def bad(agent, contact):
                    return 1

        with self.assertRaises(TagDeclarationError):
            @Link(agent, contact)
            class Trusts(agent.Knows):
                @Post
                def __bool__(agent, contact):
                    return True


class LinkSeatTests(unittest.TestCase):

    def test_named_reads_writes_and_truth_use_current_seat(self):
        owner, target = Host(), Host()
        owner.name = "Ari"
        target.name = "sword"
        with _seat_context(owner, target):
            self.assertEqual(agent.name, "Ari")
            self.assertEqual(contact.name, "sword")
            self.assertIs(_resolve_seat(agent), owner)
            self.assertIs(_resolve_seat(contact), target)
            contact.damage = 6
            self.assertEqual(target.damage, 6)
            del contact.damage
            self.assertFalse(hasattr(target, "damage"))
            self.assertTrue(bool(agent))

    def test_zero_parameter_protocol_can_call_reciprocal_link_explicitly(self):
        owner, target = Host(), Host()
        seen = []
        target.Knows = lambda value: seen.append(_resolve_seat(value))

        def Connect():
            contact.Knows(agent)

        with _seat_context(owner, target):
            Connect()

        self.assertEqual(seen, [owner])

    def test_nested_context_restores_outer_seats_after_success_or_failure(self):
        owner, target, other_owner, other_target = (Host() for _ in range(4))
        with _seat_context(owner, target):
            with _seat_context(other_owner, other_target):
                self.assertIs(_resolve_seat(agent), other_owner)
                self.assertIs(_resolve_seat(contact), other_target)
            self.assertIs(_resolve_seat(agent), owner)
            self.assertIs(_resolve_seat(contact), target)
            with self.assertRaises(ValueError):
                with _seat_context(other_owner, other_target):
                    raise ValueError("failed nested protocol")
            self.assertIs(_resolve_seat(agent), owner)
            self.assertIs(_resolve_seat(contact), target)

        with self.assertRaises(TagResolutionError):
            _resolve_seat(agent)
        with self.assertRaises(TagResolutionError):
            bool(contact)

    def test_new_nested_context_can_take_current_seat_symbols(self):
        owner, target = Host(), Host()
        with _seat_context(owner, target):
            with _seat_context(contact, agent):
                self.assertIs(_resolve_seat(agent), target)
                self.assertIs(_resolve_seat(contact), owner)
            self.assertIs(_resolve_seat(agent), owner)

    def test_interleaved_tasks_keep_independent_current_seats(self):
        async def Run():
            async def Read(owner, target):
                with _seat_context(owner, target):
                    await asyncio.sleep(0)
                    self.assertIs(_resolve_seat(agent), owner)
                    self.assertIs(_resolve_seat(contact), target)
                    await asyncio.sleep(0)
                    self.assertIs(_resolve_seat(agent), owner)
                    return _resolve_seat(contact)

            first_owner, first_target, other_owner, other_target = (Host() for _ in range(4))
            self.assertEqual(
                    await asyncio.gather(
                            Read(first_owner, first_target),
                            Read(other_owner, other_target),
                            ),
                    [first_target, other_target],
                    )

        asyncio.run(Run())


if __name__ == "__main__":
    unittest.main()
