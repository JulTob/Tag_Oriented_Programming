"""STEP-SPEC-43 prototype: a Tag may state a Post about itself."""

import unittest

from TopKit import (Constant, Contract, Operation, Pin, Post, Pre, Public,
                    Secret, Tag, TagCompositionError, TagContractWarning,
                    TagContractError, TagDeclarationError, TagPostconditionError,
                    Underlay)
from TopKit.tags import MetaTag


class Host:
    pass


class NativeTagPostTests(unittest.TestCase):
    def test_multiple_native_posts_keep_declaration_order(self):
        calls = []

        class Fleet(Tag):
            @Post
            @Operation
            def First(tag):
                calls.append("first")
                return True

            @Post
            def Member_Only(agent):
                return True

            @Operation
            @Post
            def Second(tag):
                calls.append("second")
                return True

        self.assertEqual(
                Contract.Status(Fleet),
                {"First": True, "Second": True},
                )
        self.assertEqual(calls, ["first", "second"])

    def test_both_decorator_orders_read_the_tag_now_without_a_pin(self):
        for outer_post in (True, False):
            with self.subTest(outer_post=outer_post):
                if outer_post:
                    class Fleet(Tag):
                        ready = False

                        @Post
                        @Operation
                        def Ready(tag):
                            return tag.ready
                else:
                    class Fleet(Tag):
                        ready = False

                        @Operation
                        @Post
                        def Ready(tag):
                            return tag.ready

                self.assertIs(type(Fleet), MetaTag)
                self.assertIs(Fleet.Ready, False)
                self.assertIs(bool(Fleet), False)
                self.assertEqual(Contract.Status(Fleet), {"Ready": False})
                with self.assertRaises(TagPostconditionError.Ready):
                    Contract.Postconditions(Fleet)
                self.assertEqual(len(Fleet), 0)
                self.assertFalse(Fleet[:])

                Fleet.ready = True
                self.assertIs(Fleet.Ready, True)
                self.assertIs(bool(Fleet), True)
                self.assertEqual(Contract.Status(Fleet), {"Ready": True})
                self.assertTrue(Contract.Postconditions(Fleet))

    def test_native_tag_post_is_separate_from_each_members_post(self):
        class Fleet(Tag):
            capacity = 1

            @Post
            @Operation
            def Within_Capacity(tag):
                return len(tag[:]) <= tag.capacity

            @Post
            def Charged(agent):
                return agent.charge > 0

        car = Host()
        car.charge = 0
        with self.assertRaises(TagPostconditionError.Charged):
            Fleet(car)

        self.assertIs(Fleet.Within_Capacity, True)
        self.assertIs(bool(Fleet), True)
        self.assertIn(car, Fleet[:])
        self.assertIn(car, ~Fleet)
        self.assertEqual(len(Fleet), 0)
        self.assertEqual(Contract.Status(car), {"Charged": False})
        self.assertEqual(Contract.Status(Fleet), {"Within_Capacity": True})

        Fleet.capacity = 0
        self.assertIs(Fleet.Within_Capacity, False)
        self.assertFalse(Fleet)
        self.assertEqual(len(~Fleet), 1)

    def test_a_base_post_judges_only_its_declaring_tag(self):
        class Crew(Tag):
            required = 2

            @Post
            @Operation
            def Ready(tag):
                return len(tag[:]) >= tag.required

        class Pilots(Crew):
            pass

        one, two = Host(), Host()
        Pilots(one)
        Crew(two)
        self.assertIs(Crew.Ready, True)
        self.assertTrue(Crew)
        self.assertTrue(Pilots)
        self.assertEqual(len(Pilots), 1)
        self.assertEqual(Contract.Status(Pilots), {})
        with self.assertRaises(AttributeError):
            Pilots.Ready

        Crew.required = 3
        self.assertIs(Crew.Ready, False)
        self.assertFalse(Crew)
        self.assertTrue(Pilots)

        @Pin
        class PilotApproval(Tag):
            @Post
            def Ready(tag):
                return True

        PilotApproval(Pilots)
        self.assertIs(Pilots.Ready, True)
        self.assertEqual(Contract.Status(Pilots), {"Ready": True})
        self.assertIs(Crew.Ready, False)

    def test_pin_post_overlays_native_post_and_delete_does_not_restore_it(self):
        class Crew(Tag):
            safe = False

            @Post
            @Operation
            def Safe(tag):
                return tag.safe

        @Pin
        class Audited(Tag):
            @Underlay
            @Post
            def Safe(tag, prior):
                return prior() or True

        self.assertFalse(Crew)
        Audited(Crew)
        self.assertIs(Crew.Safe, True)
        self.assertTrue(Crew)
        del Audited[Crew]
        self.assertNotIn(Crew, Audited)
        self.assertIs(Crew.Safe, True)   # established Posts survive Rip

        Contract.Delete(Crew, "Safe")
        self.assertTrue(Crew)
        self.assertEqual(Contract.Status(Crew), {})
        with self.assertRaises(AttributeError):
            Crew.Safe

        @Pin
        class Rechecked(Tag):
            @Post
            def Safe(tag):
                return False

        with self.assertRaises(TagPostconditionError.Safe):
            Rechecked(Crew)
        self.assertIs(Crew.Safe, False)

    def test_replacing_a_native_post_warns_and_keeps_one_visible_check(self):
        class Crew(Tag):
            @Post
            @Operation
            def Ready(tag):
                return True

        @Pin
        class Replacement(Tag):
            @Post
            def Ready(tag):
                return False

        with self.assertWarns(TagContractWarning):
            with self.assertRaises(TagPostconditionError.Ready):
                Replacement(Crew)

        self.assertIs(Crew.Ready, False)
        self.assertEqual(Contract.Status(Crew), {"Ready": False})
        self.assertEqual(len(Contract.Status(Crew)), 1)

    def test_native_failure_uses_the_existing_verdict_and_pin_population(self):
        class Crew(Tag):
            verdict = False

            @Post
            @Operation
            def Ready(tag):
                return tag.verdict

        @Pin
        class Listed(Tag):
            pass

        with self.assertRaises(TagPostconditionError.Ready):
            Listed(Crew)
        self.assertIn(Crew, Listed[:])
        self.assertIn(Crew, ~Listed)
        self.assertEqual(len(Listed), 0)

        Crew.verdict = 0
        with self.assertRaises(TagContractError):
            Crew.Ready
        self.assertFalse(Crew)
        self.assertEqual(Contract.Status(Crew), {"Ready": False})

        Crew.verdict = True
        self.assertIs(Crew.Ready, True)
        self.assertIn(Crew, Listed)

    def test_an_ordinary_operation_remains_callable_for_repair(self):
        class Crew(Tag):
            ready = False

            @Post
            @Operation
            def Ready(tag):
                return tag.ready

            @Operation
            def Repair(tag):
                tag.ready = True

        self.assertFalse(Crew)
        Crew.Repair()
        self.assertIs(Crew.Ready, True)
        self.assertTrue(Crew)

    def test_a_visible_native_post_cannot_be_assigned_or_deleted(self):
        class Crew(Tag):
            @Post
            @Operation
            def Ready(tag):
                return True

        with self.assertRaises(TagCompositionError):
            Crew.Ready = False
        with self.assertRaises(TagCompositionError):
            del Crew.Ready
        self.assertIs(Crew.Ready, True)

        Contract.Delete(Crew, "Ready")
        self.assertIs(type(Crew), MetaTag)  # no Pin or implicit actualization
        self.assertEqual(Contract.Status(Crew), {})
        with self.assertRaises(AttributeError):
            Crew.Ready

    def test_constant_native_post_locks_its_declaration_and_pin_overlay(self):
        for outer_constant in (True, False):
            with self.subTest(outer_constant=outer_constant):
                if outer_constant:
                    class Crew(Tag):
                        @Constant
                        @Post
                        @Operation
                        def Ready(tag):
                            return True
                else:
                    class Crew(Tag):
                        @Operation
                        @Constant
                        @Post
                        def Ready(tag):
                            return True

                @Pin
                class Replacement(Tag):
                    @Post
                    def Ready(tag):
                        return False

                with self.assertRaises(TagCompositionError):
                    Replacement(Crew)
                with self.assertRaises(TagCompositionError):
                    Contract.Delete(Crew, "Ready")
                with self.assertRaises(TagCompositionError):
                    Crew.Ready = False
                with self.assertRaises(TagCompositionError):
                    del Crew.Ready
                self.assertIs(Crew.Ready, True)

                class Shape(Crew):
                    @Post
                    @Operation
                    def Ready(tag):
                        return False

                self.assertIs(Crew.Ready, True)
                self.assertIs(Shape.Ready, False)
                self.assertTrue(Crew)
                self.assertFalse(Shape)

    def test_a_base_constant_does_not_lock_a_shapes_separate_pin_post(self):
        class Crew(Tag):
            @Constant
            @Post
            @Operation
            def Ready(tag):
                return True

        class Pilots(Crew):
            pass

        @Pin
        class Pilot_Check(Tag):
            @Post
            def Ready(tag):
                return False

        with self.assertRaises(TagPostconditionError.Ready):
            Pilot_Check(Pilots)

        self.assertIs(Crew.Ready, True)
        self.assertTrue(Crew)
        self.assertIs(Pilots.Ready, False)
        self.assertFalse(Pilots)
        self.assertEqual(Contract.Status(Crew), {"Ready": True})
        self.assertEqual(Contract.Status(Pilots), {"Ready": False})

        with self.assertRaises(TagCompositionError):
            Pilot_Check(Crew)

    def test_base_and_shape_native_posts_with_same_name_are_independent(self):
        class Crew(Tag):
            ready = True

            @Post
            @Operation
            def Ready(tag):
                return tag.ready

        class Pilots(Crew):
            ready = False

            @Post
            @Operation
            def Ready(tag):
                return tag.ready

        self.assertTrue(Crew)
        self.assertFalse(Pilots)
        Crew.ready = False
        Pilots.ready = True
        self.assertFalse(Crew)
        self.assertTrue(Pilots)
        self.assertIs(Crew.Ready, False)
        self.assertIs(Pilots.Ready, True)

        Contract.Delete(Pilots, "Ready")
        self.assertEqual(Contract.Status(Pilots), {})
        self.assertEqual(Contract.Status(Crew), {"Ready": False})

    def test_constant_pin_post_on_base_does_not_reach_shapes_own_post(self):
        class Crew(Tag):
            pass

        class Pilots(Crew):
            @Post
            @Operation
            def Ready(tag):
                return False

        @Pin
        class Crew_Check(Tag):
            @Constant
            @Post
            def Ready(tag):
                return True

        Crew_Check(Crew)
        self.assertIs(Crew.Ready, True)
        self.assertIs(Pilots.Ready, False)
        self.assertTrue(Crew)
        self.assertFalse(Pilots)

        @Pin
        class Pilot_Repair(Tag):
            @Post
            def Ready(tag):
                return True

        with self.assertWarns(TagContractWarning):
            Pilot_Repair(Pilots)
        self.assertIs(Pilots.Ready, True)
        self.assertIs(Crew.Ready, True)

        with self.assertRaises(TagCompositionError):
            Pilot_Repair(Crew)

    def test_unsupported_combinations_fail_at_declaration(self):
        with self.assertRaises(TagDeclarationError):
            class Gate(Tag):
                @Operation
                @Pre
                def Ready(tag):
                    return True

        with self.assertRaises(TagDeclarationError):
            class Published(Tag):
                @Public
                @Post
                @Operation
                def Ready(tag):
                    return True

        with self.assertRaises(TagDeclarationError):
            class Hidden(Tag):
                @Secret
                @Post
                @Operation
                def Ready(tag):
                    return True

        with self.assertRaises(TagDeclarationError):
            class No_Prior(Tag):
                @Underlay
                @Post
                @Operation
                def Ready(tag, prior):
                    return prior()

        with self.assertRaises(TagDeclarationError):
            class Protocol_Name(Tag):
                @Post
                @Operation
                def __bool__(tag):
                    return True

        class Crew(Tag):
            pass

        @Post
        @Operation
        def Late(tag):
            return True

        with self.assertRaises(TagDeclarationError):
            Crew.Late = Late

        @Operation
        def Repair(tag):
            return True

        Crew.Repair = Repair
        self.assertTrue(Crew.Repair())


if __name__ == "__main__":
    unittest.main()
