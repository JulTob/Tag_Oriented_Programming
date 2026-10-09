"""Constants preserve a Contribution's binding through TOP composition."""

import copy
import unittest

from TopKit import (Action, Constant, Contract, Delete, Imprint, Operation,
                    Pin, Post, Pre, Public, Record, Report, Secret, Tag,
                    TagCompositionError, TagDeclarationError, TagError,
                    TagPostconditionError, Underlay)


class Host:
    pass


class ConstantTests(unittest.TestCase):
    def test_record_binding_is_locked_but_its_value_can_mutate(self):
        class Given(Tag):
            @Constant
            @Record
            def items(agent):
                return []

        agent = Host()
        Given(agent)
        value = agent.items
        agent.items.append("kept")
        with self.assertRaises(TagCompositionError):
            agent.items = []
        with self.assertRaises(TagCompositionError):
            del agent.items
        self.assertIs(agent.items, value)
        self.assertEqual(value, ["kept"])
        self.assertTrue("items" @ agent)

    def test_constant_action_keeps_its_binding_and_can_perform_work(self):
        class Given(Tag):
            @Constant
            @Action
            def Increment(agent):
                agent.count += 1
                return agent.count

        agent = Host()
        agent.count = 0
        Given(agent)
        self.assertEqual(agent.Increment(), 1)
        with self.assertRaises(TagCompositionError):
            agent.Increment = lambda: 100
        with self.assertRaises(TagCompositionError):
            del agent.Increment
        self.assertEqual(agent.Increment(), 2)

    def test_host_write_hooks_keep_ordinary_behavior_but_cannot_change_constants(self):
        writes = []

        class Custom_Host:
            def __setattr__(agent, name, value):
                writes.append(("set", name))
                agent.__dict__[name] = value

            def __delattr__(agent, name):
                writes.append(("delete", name))
                del agent.__dict__[name]

        class Given(Tag):
            @Constant
            @Record
            def value(agent): return "original"

        agent = Custom_Host()
        Given(agent)
        writes.clear()
        agent.ordinary = 1
        del agent.ordinary
        with self.assertRaises(TagCompositionError):
            agent.value = "changed"
        with self.assertRaises(TagCompositionError):
            del agent.value
        self.assertEqual(writes, [("set", "ordinary"), ("delete", "ordinary")])
        self.assertEqual(agent.value, "original")

    def test_object_write_methods_cannot_bypass_constant_descriptors(self):
        class Given(Tag):
            @Constant
            @Record
            def value(agent): return "original"

            @Constant
            def Work(agent): return agent.value

        agent = Host()
        Given(agent)
        for name in ("value", "Work"):
            with self.subTest(name=name):
                with self.assertRaises(TagCompositionError):
                    object.__setattr__(agent, name, None)
                with self.assertRaises(TagCompositionError):
                    object.__delattr__(agent, name)
        self.assertEqual(agent.Work(), "original")

    def test_post_survives_rip_and_cannot_be_deleted_or_shadowed(self):
        class Sworn(Tag):
            @Constant
            @Post
            def Has_Balance(agent):
                return "balance" @ agent

        agent = Host()
        agent.balance = None
        Sworn(agent)
        del Sworn[agent]
        for mutate in (
                lambda: Contract.Delete(agent, "Has_Balance"),
                lambda: setattr(agent, "Has_Balance", lambda: True),
                lambda: delattr(agent, "Has_Balance"),
                ):
            with self.subTest(mutate=mutate):
                with self.assertRaises(TagCompositionError):
                    mutate()
        del agent.balance
        self.assertEqual(Contract.Status(agent), {"Has_Balance": False})
        with self.assertRaises(TagPostconditionError.Has_Balance):
            Contract.Postconditions(agent)

    def test_an_unrelated_post_cannot_replace_or_underlay_a_constant(self):
        class Sworn(Tag):
            @Post
            @Constant
            def Ready(agent):
                return agent.ready

        class Replace(Tag):
            @Post
            def Ready(agent):
                return True

        class Extend(Tag):
            @Post
            @Underlay
            def Ready(agent, prior):
                return prior() or True

        agent = Host()
        agent.ready = True
        Sworn(agent)
        for tag in (Replace, Extend):
            with self.subTest(tag=tag):
                with self.assertRaises(TagError):
                    tag(agent)
        agent.ready = False
        self.assertFalse(Contract.Holds(agent))

    def test_other_tags_cannot_change_a_constants_kind_or_delete_it(self):
        class Given(Tag):
            @Constant
            @Record
            def value(agent):
                return None

            @Constant
            @Action
            def Work(agent):
                return "original"

        class Record_To_Action(Tag):
            def value(agent):
                return "replacement"

        class Action_To_Record(Tag):
            @Record
            def Work(agent):
                return "replacement"

        class Remove(Tag):
            @Delete
            def value(agent): ...

        agent = Host()
        Given(agent)
        for tag in (Record_To_Action, Action_To_Record, Remove):
            with self.subTest(tag=tag):
                with self.assertRaises(TagError):
                    tag(agent)
                self.assertIsNone(agent.value)
                self.assertEqual(agent.Work(), "original")

    def test_underlay_cannot_wrap_a_constant_action(self):
        class Given(Tag):
            @Constant
            def Work(agent):
                return "original"

        class Extend(Tag):
            @Underlay
            def Work(agent, prior):
                return prior() + " extended"

        agent = Host()
        Given(agent)
        with self.assertRaises(TagError):
            Extend(agent)
        self.assertEqual(agent.Work(), "original")

    def test_retagging_keeps_constants_but_rebuilds_ordinary_records(self):
        builds = []

        class Given(Tag):
            @Constant
            @Record
            def token(agent):
                builds.append("token")
                return object()

            @Record
            def round(agent, stored):
                return (stored or 0) + 1

            @Constant
            def Work(agent):
                return agent.token

            @Constant
            @Post
            def Equipped(agent):
                return "token" @ agent

            @Imprint
            def Train(agent):
                agent.trained += 1

        agent = Host()
        agent.trained = 0
        Given(agent)
        original = agent.token
        del Given[agent]
        Given(agent)
        self.assertIs(agent.token, original)
        self.assertIs(agent.Work(), original)
        self.assertEqual((agent.round, agent.trained), (2, 2))
        self.assertEqual(builds, ["token"])
        self.assertEqual(Contract.Status(agent), {"Equipped": True})

    def test_unrelated_tagging_preserves_locks_and_copying_stays_refused(self):
        class Given(Tag):
            @Constant
            @Record
            def value(agent):
                return 0

            @Constant
            def Work(agent):
                return agent.value

        class More(Tag):
            @Record
            def extra(agent):
                return 2

            def Added(agent):
                return agent.extra

        agent = Host()
        Given(agent)
        More(agent)
        self.assertEqual((agent.Work(), agent.Added()), (0, 2))
        for name in ("value", "Work"):
            with self.subTest(name=name):
                with self.assertRaises(TagCompositionError):
                    setattr(agent, name, None)
                with self.assertRaises(TagCompositionError):
                    delattr(agent, name)
        for copier in (copy.copy, copy.deepcopy):
            with self.subTest(copier=copier):
                with self.assertRaises(TagCompositionError):
                    copier(agent)

    def test_secret_constants_keep_the_access_door_and_binding_lock(self):
        class Given(Tag):
            @Secret
            @Constant
            @Record
            def key(agent):
                return "original"

            @Constant
            @Secret
            def Secret_Key(agent):
                return agent.key

            def Read(agent):
                return agent.Secret_Key()

            def Replace(agent):
                agent.key = "replacement"

            def Remove(agent):
                del agent.Secret_Key

        agent = Host()
        Given(agent)
        self.assertEqual(agent.Read(), "original")
        self.assertFalse("key" @ agent)
        for name in ("key", "Secret_Key"):
            with self.subTest(name=name):
                with self.assertRaises(AttributeError):
                    getattr(agent, name)
        for mutate in (agent.Replace, agent.Remove):
            with self.assertRaises(TagCompositionError):
                mutate()
        self.assertEqual(agent.Read(), "original")

    def test_both_decorator_orders_work_for_every_supported_kind(self):
        class Given(Tag):
            @Constant
            @Record
            def first(agent): return 1

            @Record
            @Constant
            def second(agent): return 2

            @Constant
            @Action
            def First(agent): return 3

            @Action
            @Constant
            def Second(agent): return 4

            @Constant
            @Post
            def First_Promise(agent): return True

            @Post
            @Constant
            def Second_Promise(agent): return True

            @Constant
            @Report
            def third(tag): return 5

            @Report
            @Constant
            def fourth(tag): return 6

            @Constant
            @Operation
            def Third(tag): return 7

            @Operation
            @Constant
            def Fourth(tag): return 8

        agent = Host()
        Given(agent)
        self.assertEqual((agent.first, agent.second, agent.First(),
                          agent.Second(), Given.third, Given.fourth,
                          Given.Third(), Given.Fourth()), tuple(range(1, 9)))
        for name in ("first", "second", "First", "Second",
                     "First_Promise", "Second_Promise"):
            with self.subTest(name=name):
                with self.assertRaises(TagCompositionError):
                    setattr(agent, name, None)
        for name in ("third", "fourth", "Third", "Fourth"):
            with self.subTest(name=name):
                with self.assertRaises(TagCompositionError):
                    setattr(Given, name, None)

    def test_pre_only_imprint_and_delete_are_invalid_constant_declarations(self):
        for mark in (Pre, Imprint, Delete):
            for constant_first in (False, True):
                with self.subTest(mark=mark, constant_first=constant_first):
                    def member(agent):
                        return True

                    with self.assertRaises(TagDeclarationError):
                        declaration = (Constant(mark(member)) if constant_first
                                       else mark(Constant(member)))
                        type("Invalid", (Tag,), {"member": declaration})

    def test_combined_pre_and_post_can_be_constant(self):
        class Required(Tag):
            @Constant
            @Pre
            @Post
            def Ready(agent):
                return agent.ready

        agent = Host()
        agent.ready = True
        Required(agent)
        with self.assertRaises(TagCompositionError):
            Contract.Delete(agent, "Ready")
        agent.ready = False
        self.assertFalse(Contract.Holds(agent))
        self.assertEqual(Contract.Status(agent), {"Ready": False})

    def test_shapes_cannot_redeclare_inherited_constant_gains_or_posts(self):
        class Base(Tag):
            @Constant
            @Record
            def value(agent): return 1

            @Constant
            def Work(agent): return 2

            @Constant
            @Post
            def Ready(agent): return True

        for name in ("value", "Work", "Ready"):
            with self.subTest(name=name):
                with self.assertRaises(TagDeclarationError):
                    type("Shape", (Base,), {name: lambda agent: True})

    def test_tag_declarations_cannot_be_replaced_or_deleted_dynamically(self):
        class Base(Tag):
            @Constant
            @Record
            def value(agent): return 1

            @Constant
            def Work(agent): return 2

            @Constant
            @Post
            def Ready(agent): return True

        class Shape(Base):
            pass

        for tag in (Base, Shape):
            for name in ("value", "Work", "Ready"):
                with self.subTest(tag=tag, name=name):
                    with self.assertRaises(TagCompositionError):
                        setattr(tag, name, None)
                    with self.assertRaises(TagCompositionError):
                        delattr(tag, name)

    def test_report_builds_once_for_its_declaring_tag_even_if_shape_reads_first(self):
        builds = []

        class Base(Tag):
            @Constant
            @Report
            def label(tag):
                builds.append(tag)
                return {"name": tag.__name__}

        class Shape(Base):
            pass

        class Later(Shape):
            pass

        value = Shape.label
        self.assertEqual(value, {"name": "Base"})
        self.assertIs(Base.label, value)
        self.assertIs(Later.label, value)
        self.assertEqual(builds, [Base])
        value["count"] = 1
        self.assertEqual(Later.label["count"], 1)

    def test_report_is_locked_on_base_and_shapes(self):
        class Base(Tag):
            @Constant
            @Report
            def label(tag):
                return "Base"

        class Shape(Base):
            pass

        for tag in (Base, Shape):
            with self.subTest(tag=tag):
                with self.assertRaises(TagCompositionError):
                    tag.label = "changed"
                with self.assertRaises(TagCompositionError):
                    del tag.label
                self.assertEqual(tag.label, "Base")
        with self.assertRaises(TagDeclarationError):
            class Override(Base):
                @Report
                def label(tag):
                    return "changed"

    def test_operation_keeps_the_receiving_shape_but_implementation_is_locked(self):
        class Base(Tag):
            @Constant
            @Operation
            def Name(tag):
                return tag.__name__

        class Shape(Base):
            pass

        self.assertEqual((Base.Name(), Shape.Name()), ("Base", "Shape"))
        for tag in (Base, Shape):
            with self.subTest(tag=tag):
                with self.assertRaises(TagCompositionError):
                    tag.Name = lambda: "changed"
                with self.assertRaises(TagCompositionError):
                    del tag.Name
        with self.assertRaises(TagDeclarationError):
            class Override(Base):
                @Operation
                def Name(tag): return "changed"

    def test_published_constants_cannot_be_masked_on_an_agent(self):
        class Given(Tag):
            @Public
            @Constant
            @Report
            def label(tag):
                return tag.__name__

            @Constant
            @Public
            @Operation
            def Identify(tag, agent):
                return tag.label

        class Mask_Report(Tag):
            @Record
            def label(agent): return "changed"

        class Mask_Operation(Tag):
            def Identify(agent): return "changed"

        agent = Host()
        Given(agent)
        for name in ("label", "Identify"):
            with self.subTest(name=name):
                with self.assertRaises(TagCompositionError):
                    setattr(agent, name, None)
                with self.assertRaises(TagCompositionError):
                    delattr(agent, name)
        for tag in (Mask_Report, Mask_Operation):
            with self.subTest(tag=tag):
                with self.assertRaises(TagError):
                    tag(agent)
        self.assertEqual(agent.label, "Given")
        self.assertEqual(agent.Identify(), "Given")

    def test_an_internal_report_has_a_separate_scope_from_a_constant_record(self):
        class Agent_State(Tag):
            @Constant
            @Record
            def label(agent): return "Agent"

        class Tag_State(Tag):
            @Report
            def label(tag): return "Tag"

        for tags in ((Agent_State, Tag_State), (Tag_State, Agent_State)):
            with self.subTest(tags=tags):
                agent = Host()
                for tag in tags:
                    tag(agent)
                self.assertEqual(agent.label, "Agent")
                self.assertEqual(Tag_State.label, "Tag")
                with self.assertRaises(TagCompositionError):
                    agent.label = "changed"

    def test_public_constant_pin_protects_existing_and_future_field_members(self):
        class Base(Tag):
            pass

        class Shape(Base):
            pass

        existing = Host()
        Base(existing)
        shaped = Host()
        Shape(shaped)

        @Pin
        class Given(Tag):
            @Public
            @Constant
            @Record
            def label(tag):
                return {"owner": tag.__name__}

            @Public
            @Constant
            def Identify(tag, agent):
                return tag.label

        Given(Base)
        future = Host()
        Base(future)
        original = Base.label
        self.assertIs(Shape.label, original)
        del Given[Base]

        class More(Tag):
            @Record
            def extra(agent): return 1

        class Mask(Tag):
            @Record
            def label(agent): return "changed"

        for agent in (existing, shaped, future):
            with self.subTest(agent=agent):
                More(agent)
                self.assertIs(agent.label, original)
                self.assertIs(agent.Identify(), original)
                for name in ("label", "Identify"):
                    with self.assertRaises(TagCompositionError):
                        setattr(agent, name, None)
                    with self.assertRaises(TagCompositionError):
                        delattr(agent, name)
                with self.assertRaises(TagError):
                    Mask(agent)
                self.assertIs(agent.label, original)
                self.assertIs(agent.Identify(), original)

    def test_a_pin_cannot_replace_a_constant_report_or_operation(self):
        class Given(Tag):
            @Constant
            @Report
            def label(tag): return "original"

            @Constant
            @Operation
            def Work(tag): return "original"

        @Pin
        class Replace_Report(Tag):
            @Record
            def label(tag): return "replacement"

        @Pin
        class Replace_Operation(Tag):
            def Work(tag): return "replacement"

        for pin in (Replace_Report, Replace_Operation):
            with self.subTest(pin=pin):
                with self.assertRaises(TagError):
                    pin(Given)
        self.assertEqual((Given.label, Given.Work()), ("original", "original"))

    def test_pin_constants_stay_inherited_and_locked_after_rip(self):
        @Pin
        class Given(Tag):
            @Constant
            @Record
            def label(tag):
                return {"owner": tag.__name__}

            @Constant
            def Name(tag):
                return tag.__name__

        class Base(Tag):
            pass

        Given(Base)

        class Shape(Base):
            pass

        value = Base.label
        del Given[Base]
        self.assertIs(Shape.label, value)
        self.assertEqual((Base.Name(), Shape.Name()), ("Base", "Shape"))
        for tag in (Base, Shape):
            for name in ("label", "Name"):
                with self.subTest(tag=tag, name=name):
                    with self.assertRaises(TagCompositionError):
                        setattr(tag, name, None)
                    with self.assertRaises(TagCompositionError):
                        delattr(tag, name)
        with self.assertRaises(TagDeclarationError):
            class Override(Base):
                label = None

    def test_a_later_pin_cannot_shadow_an_inherited_pin_constant(self):
        @Pin
        class Given(Tag):
            @Constant
            @Record
            def label(tag): return "original"

        @Pin
        class Replace(Tag):
            @Record
            def label(tag): return "changed"

        class Base(Tag):
            pass

        Given(Base)

        class Shape(Base):
            pass

        with self.assertRaises(TagError):
            Replace(Shape)
        self.assertEqual(Shape.label, "original")

    def test_multiple_bases_may_hide_an_ordinary_report_but_not_a_constant(self):
        class Fixed(Tag):
            @Constant
            @Report
            def label(tag): return "fixed"

        class Ordinary(Tag):
            @Report
            def label(tag): return "ordinary"

        class Also_Fixed(Tag):
            @Constant
            @Report
            def label(tag): return "other fixed"

        class Allowed(Fixed, Ordinary):
            pass

        self.assertEqual(Allowed.label, "fixed")
        for bases in ((Ordinary, Fixed), (Fixed, Also_Fixed)):
            with self.subTest(bases=bases):
                with self.assertRaises(TagDeclarationError):
                    type("Shape", bases, {})

    def test_late_constant_pin_cannot_invalidate_an_existing_shapes_shadow(self):
        class Base(Tag):
            pass

        class Shape(Base):
            @Report
            def label(tag):
                return "existing"

        @Pin
        class Given(Tag):
            @Constant
            @Record
            def label(tag):
                return "fixed"

        with self.assertRaises(TagError):
            Given(Base)
        self.assertEqual(Shape.label, "existing")
        self.assertNotIn(Base, Given[:])
        with self.assertRaises(AttributeError):
            Base.label

    def test_late_constant_pin_cannot_be_hidden_by_an_earlier_base(self):
        class Earlier(Tag):
            @Report
            def label(tag): return "existing"

        class Base(Tag):
            pass

        class Shape(Earlier, Base):
            pass

        @Pin
        class Given(Tag):
            @Constant
            @Record
            def label(tag): return "fixed"

        with self.assertRaises(TagError):
            Given(Base)
        self.assertEqual(Shape.label, "existing")
        self.assertNotIn(Base, Given[:])

    def test_a_sibling_base_cannot_acquire_a_binding_that_hides_a_constant(self):
        for variant in ("assignment", "ordinary Pin", "Constant Pin"):
            with self.subTest(variant=variant):
                class Base(Tag):
                    pass

                class Other(Tag):
                    @Constant
                    @Report
                    def label(tag): return "locked"

                class Shape(Base, Other):
                    pass

                @Pin
                class Existing(Tag):
                    @Record
                    def anchor(tag): return object()

                Existing(Base)
                anchor = Base.anchor
                prior_type = type(Base)

                if variant == "assignment":
                    with self.assertRaises(TagCompositionError):
                        Base.label = "assigned"
                else:
                    def label(tag):
                        return "assigned"

                    declaration = Record(label)
                    if variant == "Constant Pin":
                        declaration = Constant(declaration)
                    Candidate = Pin(type("Candidate", (Tag,), {"label": declaration}))
                    with self.assertRaises(TagError):
                        Candidate(Base)
                    self.assertEqual(list(Candidate[:]), [])

                self.assertEqual(Shape.label, "locked")
                self.assertIs(Base.anchor, anchor)
                self.assertIs(type(Base), prior_type)
                self.assertEqual(list(Existing[:]), [Base])
                with self.assertRaises(AttributeError):
                    Base.label

    def test_a_later_sibling_base_can_acquire_an_ordinary_binding(self):
        for variant in ("assignment", "ordinary Pin"):
            with self.subTest(variant=variant):
                class Base(Tag):
                    pass

                class Other(Tag):
                    @Constant
                    @Report
                    def label(tag): return "locked"

                class Shape(Other, Base):
                    pass

                if variant == "assignment":
                    Base.label = "ordinary"
                else:
                    @Pin
                    class Given(Tag):
                        @Record
                        def label(tag): return "ordinary"

                    Given(Base)
                    self.assertIn(Base, Given[:])

                self.assertEqual(Base.label, "ordinary")
                self.assertEqual(Shape.label, "locked")

    def test_diamond_inheritance_keeps_the_same_constant_declaration(self):
        class Base(Tag):
            @Constant
            @Report
            def token(tag): return object()

            @Constant
            @Record
            def value(agent): return 1

        class Left(Base):
            pass

        class Right(Base):
            pass

        class Diamond(Left, Right):
            pass

        self.assertIs(Diamond.token, Base.token)
        agent = Host()
        Diamond(agent)
        self.assertEqual(agent.value, 1)
        with self.assertRaises(TagCompositionError):
            agent.value = 2

    def test_plain_class_values_cannot_hide_constant_declarations(self):
        class Base(Tag):
            @Constant
            @Record
            def gain(agent): return 1

        for replacement in (None, 0, property(lambda agent: 3)):
            with self.subTest(replacement=replacement):
                with self.assertRaises(TagDeclarationError):
                    type("Shape", (Base,), {"gain": replacement})

    def test_a_constant_post_remains_checked_after_unrelated_tagging(self):
        class Sworn(Tag):
            @Constant
            @Post
            def Ready(agent):
                return agent.ready

        class More(Tag):
            @Record
            def count(agent): return 1

        agent = Host()
        agent.ready = True
        Sworn(agent)
        agent.ready = False
        with self.assertRaises(TagPostconditionError.Ready):
            More(agent)
        self.assertEqual(Contract.Status(agent), {"Ready": False})
        with self.assertRaises(TagCompositionError):
            Contract.Delete(agent, "Ready")


if __name__ == "__main__":
    unittest.main()
