"""Independent equipment relationships use ordinary Tag training and Rip."""

import asyncio
import gc
import inspect
import unittest
import weakref

from TopKit import (Action, Imprint, Link, Operation, Pin, Post, Pre, Public,
                    Record, Report, Rip, Secret, Tag, TagCompositionError,
                    TagImprintError, TagPostconditionError, TagPreconditionError,
                    TagDeclarationError, TagResolutionError, agent, contact)
from TopKit import TrainingWarning


class Host:
    pass


class EquipmentLinksTests(unittest.TestCase):
    def inventory(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target, *, slot="pack"):
                    return slot

                @Action
                def Move(owner, target, slot):
                    owner.Carries[target].slot = slot
                    return slot

        owner, target = Host(), Host()
        Inventory(owner)
        return Inventory, owner, target

    def test_actual_links_have_independent_fields(self):
        inventory, owner, target = self.inventory()
        other = Host()
        inventory(other)
        self.assertIsNot(owner.Carries, other.Carries)
        owner.Carries(target, slot="hand")
        self.assertIn(target, owner.Carries)
        self.assertNotIn(target, other.Carries[:])
        self.assertEqual(owner.Carries[target].slot, "hand")
        self.assertFalse("slot" @ owner)
        self.assertFalse("slot" @ target)

    def test_an_actual_link_cannot_be_reclassified_as_a_pin(self):
        inventory, owner, target = self.inventory()
        with self.assertRaises(TagDeclarationError):
            Pin(owner.Carries)
        owner.Carries(target)
        self.assertIn(target, owner.Carries)

    def test_contextual_presence_and_direct_seat_results_use_actual_objects(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def bearer():
                    return agent

                @Action
                def Item():
                    assert "name" @ contact
                    return contact

                @Action
                def Inspect():
                    yield contact
                    return agent

        owner, target = Host(), Host()
        target.name = "sword"
        Inventory(owner)
        owner.Carries(target)
        view = owner.Carries[target]
        self.assertIs(view.bearer, owner)
        self.assertIs(view.Item(), target)
        result = view.Inspect()
        self.assertIs(next(result), target)
        with self.assertRaises(StopIteration) as stopped:
            next(result)
        self.assertIs(stopped.exception.value, owner)

    def test_read_only_checks_refuse_linking_before_any_pair_is_created(self):
        from TopKit.links import _data_of
        for mark, error in ((Pre, TagPreconditionError), (Post, TagPostconditionError)):
            with self.subTest(mark=mark.__name__):
                inventory, owner, target = self.inventory()
                link = owner.Carries

                class Checked(Tag):
                    @mark
                    def Ready(subject):
                        link(target)
                        return True

                with self.assertRaises(error):
                    Checked(Host())
                self.assertEqual(_data_of(link).pairs, {})
                self.assertNotIn(target, link[:])
                self.assertIs(type(target), Host)
                self.assertEqual(target.__dict__, {})

    def test_post_cannot_create_a_form_using_an_existing_actual_link(self):
        inventory, owner, target = self.inventory()
        link = owner.Carries

        class Checked(Tag):
            @Post
            def Ready(subject):
                @Link(agent, contact)
                class Forbidden(link):
                    pass
                return True

        with self.assertRaises(TagPostconditionError.Ready):
            Checked(Host())
        self.assertNotIn(target, link[:])

    def test_two_links_keep_distinct_pair_gains(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def note(owner, target, *, note):
                    return note

            @Link(agent, contact)
            class Stores(Tag):
                @Record
                def note(owner, target, *, note):
                    return note

        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target, note="belt")
        owner.Stores(target, note="locker")
        self.assertEqual(owner.Carries[target].note, "belt")
        self.assertEqual(owner.Stores[target].note, "locker")
        del owner.Carries[target]
        self.assertIn(target, owner.Stores)
        self.assertEqual(owner.Stores[target].note, "locker")

    def test_same_name_links_keep_declaring_tag_identity(self):
        base, owner, target = self.inventory()

        class Later(base):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def pocket(owner, target):
                    return "coat"

        base_link = owner.Carries
        base_link(target)
        Later(owner)
        later_link = owner.Carries
        self.assertIsNot(base_link, later_link)
        self.assertIs(base[owner].Carries, base_link)
        self.assertNotIn(target, later_link[:])
        later_link(target)
        self.assertEqual(later_link[target].pocket, "coat")
        self.assertEqual(base_link[target].slot, "pack")

    def test_repeated_admitted_call_does_not_train_again(self):
        inventory, owner, target = self.inventory()
        owner.Carries(target, slot="hand")
        owner.Carries(target, slot="pack")
        self.assertEqual(owner.Carries[target].slot, "hand")

    def test_saved_view_and_action_follow_current_pair(self):
        inventory, owner, target = self.inventory()
        owner.Carries(target)
        view = owner.Carries[target]
        move = view.Move
        del owner.Carries[target]
        with self.assertRaises(TagResolutionError):
            _ = view.slot
        with self.assertRaises(TagResolutionError):
            move("hand")
        owner.Carries(target, slot="belt")
        self.assertEqual(view.slot, "belt")
        self.assertEqual(move("hand"), "hand")
        self.assertEqual(view.slot, "hand")

    def test_live_action_handles_have_stable_identity_and_metadata(self):
        class Unhashable(Host):
            __hash__ = None

            def __eq__(self, other):
                raise AssertionError("Link handles must not compare Contacts")

        inventory, owner, _ = self.inventory()
        target = Unhashable()
        owner.Carries(target)
        first, second = owner.Carries[target].Move, owner.Carries[target].Move
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        self.assertEqual(first.__name__, "Move")
        self.assertIn("Move", repr(first))
        self.assertEqual(str(inspect.signature(first)), "(slot)")
        self.assertEqual(first.__self__.slot, "pack")
        self.assertTrue(callable(first.__func__))
        before = hash(first)
        del owner.Carries[target]
        owner.Carries(target)
        self.assertEqual(first, owner.Carries[target].Move)
        self.assertEqual(hash(first), before)
        another = Host()
        inventory(another)
        another.Carries(target)
        unrelated = another.Carries[target].Move
        self.assertNotEqual(first, unrelated)
        reference = weakref.ref(target)
        del target
        gc.collect()
        self.assertIsNone(reference())
        self.assertEqual(first, second)
        self.assertNotEqual(first, unrelated)
        self.assertEqual(hash(first), before)

    def test_view_writes_delete_and_presence_follow_pair(self):
        inventory, owner, target = self.inventory()
        owner.Carries(target)
        view = owner.Carries[target]
        view.slot = None
        self.assertTrue("slot" @ view)
        self.assertIsNone(view.slot)
        del view.slot
        self.assertFalse("slot" @ view)
        with self.assertRaises(AttributeError):
            _ = view.slot

    def test_own_imprint_sees_earlier_pair_gains(self):
        observed = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return "hand"

                @Imprint
                def Check():
                    observed.append(agent.Carries[contact].slot)

        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        self.assertEqual(observed, ["hand"])

    def test_posts_judge_after_contact_enters_field(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Post
                def Admitted(owner, target):
                    return target in owner.Carries[:]

        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        self.assertIn(target, owner.Carries)

    def test_contact_preparation_refusal_precedes_relationship_training(self):
        trained = []

        class Refusing:
            def __setattr__(self, name, value):
                if name == "__class__":
                    raise TypeError("host refuses TOP representation")
                object.__setattr__(self, name, value)

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def number(owner, target):
                    trained.append("record")
                    return 1

                @Imprint
                def Train(owner, target):
                    trained.append("imprint")

        owner, target = Host(), Refusing()
        target.original = "preserved"
        old_dictionary = target.__dict__
        Inventory(owner)
        with self.assertRaises(TagCompositionError):
            owner.Carries(target)
        self.assertEqual(trained, [])
        self.assertIs(type(target), Refusing)
        self.assertIs(target.__dict__, old_dictionary)
        self.assertEqual(target.__dict__, {"original": "preserved"})

    def test_pair_gate_refusal_does_not_actualize_contact(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Pre
                def Allowed(owner, target):
                    return False

        owner, target = Host(), Host()
        Inventory(owner)
        with self.assertRaises(TagPreconditionError):
            owner.Carries(target)
        self.assertIs(type(target), Host)
        self.assertEqual(target.__dict__, {})

    def test_contact_publication_refusal_retrains_the_unfinished_link(self):
        trained = []

        class RuntimeMeta(type):
            def __new__(meta, name, bases, namespace):
                if "stamp" in namespace and "_TOPKIT_HOST_TYPE" in namespace:
                    raise TypeError("host refuses stamp publication")
                return super().__new__(meta, name, bases, namespace)

        class RejectStamp(metaclass=RuntimeMeta):
            pass

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Public
                @Record
                def stamp(owner, target):
                    return "checked"

                @Imprint
                def Train(owner, target):
                    trained.append("imprint")

        owner, target = Host(), RejectStamp()
        Inventory(owner)
        for _ in range(2):
            with self.assertRaises((TypeError, TagCompositionError)):
                owner.Carries(target)
            self.assertNotIn(target, owner.Carries[:])
        self.assertEqual(trained, ["imprint", "imprint"])

    def test_context_restores_after_nested_link_call_and_failure(self):
        seen = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Stores(Tag):
                @Imprint
                def Store():
                    seen.append((agent.name, contact.name))
                    if contact.name == "bad":
                        raise ValueError("nested training failed")

            @Link(agent, contact)
            class Carries(Tag):
                @Imprint
                def Carry():
                    seen.append((agent.name, contact.name))
                    contact.Stores(agent)
                    seen.append((agent.name, contact.name))

        owner, target = Host(), Host()
        owner.name, target.name = "owner", "target"
        Inventory(owner)
        Inventory(target)
        owner.Carries(target)
        self.assertEqual(seen, [("owner", "target"), ("target", "owner"),
                                ("owner", "target")])
        with self.assertRaises(TagResolutionError):
            bool(agent)
        bad = Host()
        bad.name = "bad"
        with self.assertWarns(TrainingWarning.Store):
            target.Stores(bad)
        self.assertIn(bad, target.Stores)
        with self.assertRaises(TagResolutionError):
            bool(contact)

    def test_header_resolves_each_turn_and_keeps_all_targets_the_contact(self):
        seen = []

        class Registry(Tag):
            @Link(agent, contact)
            class Registre(Tag):
                @Imprint
                def Register(owner, target):
                    seen.append(("register", owner.name, target.name))

        server = Host()
        server.name = "server"
        Registry(server)

        class Network(Tag):
            @Link(agent, contact)
            class Knows(Tag):
                @Imprint
                def Know(owner, target):
                    seen.append(("network-knows", owner.name, target.name))

            @Imprint
            def Join(target):
                seen.append(("network", target.name))

        class Social(Tag):
            @Link(agent, contact)
            class Knows(Tag):
                @Imprint
                def Know(owner, target):
                    seen.append(("social-knows", owner.name, target.name))

            @Link(agent, contact)
            class Trusts(Network, agent.Knows, contact.Knows, server.Registre):
                @Imprint
                def Trust():
                    seen.append(("trust", agent.name, contact.name))
                    contact.Knows(agent)

        owner, target = Host(), Host()
        owner.name, target.name = "owner", "target"
        Social(owner)
        owner.Trusts(target)
        self.assertEqual(seen, [
                ("network", "target"),
                ("social-knows", "owner", "target"),
                ("network-knows", "target", "target"),
                ("register", "server", "target"),
                ("trust", "owner", "target"),
                ("network-knows", "target", "owner"),
                ])
        self.assertIn(target, owner.Trusts)

    def test_broken_pair_is_admitted_and_readable_for_repair(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def balanced(owner, target):
                    return False

                @Post
                def Balanced(owner, target):
                    return owner.Carries[target].balanced

        owner, target = Host(), Host()
        Inventory(owner)
        with self.assertRaises(TagPostconditionError):
            owner.Carries(target)
        self.assertIn(target, owner.Carries[:])
        self.assertIn(target, ~owner.Carries)
        self.assertNotIn(target, owner.Carries)
        self.assertTrue(bool(target))
        view = owner.Carries[target]
        self.assertFalse(view.balanced)
        view.balanced = True
        self.assertIn(target, owner.Carries)

    def test_gate_refusal_leaves_no_public_pair(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Pre
                def Allowed(owner, target):
                    return False

        owner, target = Host(), Host()
        Inventory(owner)
        with self.assertRaises(TagPreconditionError):
            owner.Carries(target)
        self.assertNotIn(target, owner.Carries[:])
        with self.assertRaises(TagResolutionError):
            _ = owner.Carries[target]

    def test_failed_imprint_admits_pair_and_captured_view_resolves_it(self):
        captured = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return "hand"

                @Imprint
                def Fail():
                    captured.append(agent.Carries[contact])
                    raise ValueError("unfinished")

        owner, target = Host(), Host()
        Inventory(owner)
        with self.assertWarns(TrainingWarning.Fail):
            owner.Carries(target)
        self.assertIn(target, owner.Carries)
        self.assertEqual(captured[0].slot, "hand")

    def test_reports_and_operations_belong_to_actual_link(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Report
                def capacity(link):
                    return 4

                @Report
                def label():
                    return "equipment"

                @Operation
                def Count(link):
                    return len(link[:])

        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        self.assertEqual(owner.Carries.capacity, 4)
        self.assertEqual(owner.Carries[target].capacity, 4)
        self.assertEqual(owner.Carries[target].label, "equipment")
        self.assertEqual(owner.Carries.Count(), 1)
        self.assertFalse("capacity" @ owner)
        self.assertFalse("capacity" @ target)

    def test_public_pair_records_and_actions_are_live_contact_lines(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Public
                @Record
                def slot(owner, target):
                    return "hand"

                @Public
                @Action
                def Location(owner, target):
                    return owner.Carries[target].slot

        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        self.assertEqual(target.slot, "hand")
        self.assertEqual(target.Location(), "hand")
        owner.Carries[target].slot = "belt"
        self.assertEqual(target.slot, "belt")
        self.assertEqual(target.Location(), "belt")
        with self.assertRaises(AttributeError):
            target.slot = "bag"

    def test_public_pair_action_and_record_both_guard_contact_contract(self):
        class Healthy(Tag):
            @Record
            def ready(value):
                return True

            @Post
            def Ready(value):
                return value.ready

        called = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Public
                @Record
                def stamp(owner, target):
                    return "checked"

                @Public
                @Action
                def Fire(owner, target):
                    called.append("fired")

        owner, target = Host(), Host()
        Healthy(target)
        Inventory(owner)
        owner.Carries(target)
        saved = target.Fire
        target.ready = False
        with self.assertRaises(TagPostconditionError):
            _ = target.stamp
        with self.assertRaises(TagPostconditionError):
            target.Fire()
        with self.assertRaises(TagPostconditionError):
            saved()
        self.assertEqual(called, [])

    def test_rip_can_read_its_own_removed_pairs_record(self):
        observed = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target):
                    return "hand"

                @Rip
                def Leave():
                    observed.append(agent.Carries[contact].slot)

        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        del owner.Carries[target]
        self.assertEqual(observed, ["hand"])

    def test_rip_relink_creates_a_fresh_pair_and_preserves_new_membership(self):
        observed = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def slot(owner, target, *, slot="pack"):
                    return slot

                @Rip
                def Relink(owner, target):
                    if not observed:
                        observed.append("relinked")
                        owner.Carries(target, slot="new")
                        observed.append(owner.Carries[target].slot)

        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target, slot="old")
        view = owner.Carries[target]
        del owner.Carries[target]
        self.assertIn(target, owner.Carries)
        self.assertEqual(view.slot, "new")
        self.assertEqual(observed, ["relinked", "new"])

    def test_owner_does_not_live_through_a_saved_link(self):
        inventory, owner, target = self.inventory()
        link = owner.Carries
        link(target)
        owner_reference = weakref.ref(owner)
        del owner
        gc.collect()
        self.assertIsNone(owner_reference())
        self.assertNotIn(target, link[:])
        with self.assertRaises(TagResolutionError):
            link(target)

    def test_contact_does_not_live_through_a_link_or_saved_view(self):
        inventory, owner, target = self.inventory()
        owner.Carries(target)
        view = owner.Carries[target]
        reference = weakref.ref(target)
        del target
        gc.collect()
        self.assertIsNone(reference())
        self.assertEqual(len(owner.Carries[:]), 0)
        with self.assertRaises(TagResolutionError):
            _ = view.slot

    def test_admitted_failed_training_does_not_keep_dead_contact_or_values(self):
        class Payload:
            pass

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Record
                def payload(owner, target, *, payload):
                    return payload

                @Imprint
                def Fail(owner, target):
                    raise ValueError("unfinished")

        owner, target, payload = Host(), Host(), Payload()
        Inventory(owner)
        with self.assertWarns(TrainingWarning.Fail):
            owner.Carries(target, payload=payload)
        self.assertIn(target, owner.Carries[:])
        target_reference, payload_reference = weakref.ref(target), weakref.ref(payload)
        del target, payload
        gc.collect()
        self.assertIsNone(target_reference())
        self.assertIsNone(payload_reference())

    def test_pair_protocol_opens_owner_secret_but_not_contact_secret(self):
        class Classified(Tag):
            @Secret
            @Record
            def code(value):
                return "secret"

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Action
                def Owner_Code(owner, target):
                    return owner.code

                @Action
                def Contact_Code(owner, target):
                    return target.code

        owner, target = Host(), Host()
        Classified(owner)
        Classified(target)
        Inventory(owner)
        owner.Carries(target)
        self.assertEqual(owner.Carries[target].Owner_Code(), "secret")
        with self.assertRaises(AttributeError):
            owner.Carries[target].Contact_Code()
        with self.assertRaises(AttributeError):
            _ = owner.code

    def test_secret_pair_action_is_guarded_at_capture_and_invocation(self):
        captured = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Secret
                @Action
                def Hidden(owner, target):
                    return "private"

                @Action
                def Capture(owner, target):
                    captured.append(owner.Carries[target].Hidden)

        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        with self.assertRaises(AttributeError):
            _ = owner.Carries[target].Hidden
        owner.Carries[target].Capture()
        with self.assertRaises(AttributeError):
            captured[0]()

    def test_owner_action_can_read_pair_secrets_but_contact_action_cannot(self):
        captured = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Secret
                @Record
                def code(owner, target):
                    return "private"

                @Secret
                @Action
                def Hidden(owner, target):
                    return "secret action"

            @Action
            def Inspect(owner, target):
                view = owner.Carries[target]
                captured.append(view.Hidden)
                return view.code, view.Hidden()

        class ContactRole(Tag):
            @Action
            def Inspect(target, owner):
                return owner.Carries[target].code

        owner, target = Host(), Host()
        Inventory(owner)
        ContactRole(target)
        owner.Carries(target)
        self.assertEqual(owner.Inspect(target), ("private", "secret action"))
        with self.assertRaises(AttributeError):
            target.Inspect(owner)
        with self.assertRaises(AttributeError):
            captured[0]()

    def test_secret_link_operation_checks_owner_door_on_every_call(self):
        captured = []

        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Secret
                @Operation
                def Vault(link):
                    return "private operation"

            @Action
            def Inspect(owner):
                captured.append(owner.Carries.Vault)
                return owner.Carries.Vault()

        owner = Host()
        Inventory(owner)
        with self.assertRaises(AttributeError):
            owner.Carries.Vault()
        self.assertEqual(owner.Inspect(), "private operation")
        with self.assertRaises(AttributeError):
            captured[0]()

    def test_secret_pair_record_presence_and_writes_use_owner_authority(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Secret
                @Record
                def code(owner, target):
                    return "old"

            @Action
            def Update(owner, target):
                view = owner.Carries[target]
                present = "code" @ view
                view.code = "new"
                value = view.code
                del view.code
                return present, value, "code" @ view

        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        view = owner.Carries[target]
        self.assertFalse("code" @ view)
        with self.assertRaises(AttributeError):
            view.code = "outside"
        self.assertEqual(owner.Update(target), (True, "new", False))

    def test_lazy_action_resumes_in_its_own_seat_context(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Action
                def Names():
                    yield agent.name, contact.name
                    yield agent.name, contact.name

        a, b, first, second = (Host() for _ in range(4))
        for value, name in zip((a, b, first, second), ("a", "b", "first", "second")):
            value.name = name
        Inventory(a)
        Inventory(b)
        a.Carries(first)
        b.Carries(second)
        left = a.Carries[first].Names()
        right = b.Carries[second].Names()
        self.assertEqual(next(left), ("a", "first"))
        self.assertEqual(next(right), ("b", "second"))
        self.assertEqual(next(left), ("a", "first"))
        left.close()
        right.close()

    def test_lazy_result_cannot_resume_after_its_pair_ends(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Action
                def Steps(owner, target):
                    yield 1
                    yield 2

        owner, target = Host(), Host()
        Inventory(owner)
        owner.Carries(target)
        result = owner.Carries[target].Steps()
        self.assertEqual(next(result), 1)
        del owner.Carries[target]
        with self.assertRaises(TagResolutionError):
            next(result)

    def test_native_async_imprint_warns_without_starting_and_admits(self):
        started = []
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Imprint
                async def Train(owner, target):
                    started.append(True)
                    return None

        owner, target = Host(), Host()
        Inventory(owner)
        with self.assertWarns(TrainingWarning.Train):
            owner.Carries(target)
        self.assertIn(target, owner.Carries)
        self.assertEqual(started, [])

    def test_coroutine_and_async_generator_use_seats_on_every_step(self):
        class Inventory(Tag):
            @Link(agent, contact)
            class Carries(Tag):
                @Action
                async def Name():
                    await asyncio.sleep(0)
                    return agent.name, contact.name

                @Action
                async def Names():
                    yield agent.name, contact.name
                    await asyncio.sleep(0)
                    yield agent.name, contact.name

        owner, target = Host(), Host()
        owner.name, target.name = "ari", "sword"
        Inventory(owner)
        owner.Carries(target)

        async def Run():
            task = asyncio.create_task(owner.Carries[target].Name())
            self.assertEqual(await task, ("ari", "sword"))
            names = [name async for name in owner.Carries[target].Names()]
            self.assertEqual(names, [("ari", "sword"), ("ari", "sword")])

        asyncio.run(Run())


if __name__ == "__main__":
    unittest.main()
