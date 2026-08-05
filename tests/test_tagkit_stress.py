from __future__ import annotations

import asyncio
import gc
import inspect
import unittest
import warnings

from TagKit import Action
from TagKit import At_Exit
from TagKit import Delete
from TagKit import Imprint
from TagKit import Post
from TagKit import Pre
from TagKit import Record
from TagKit import Rip
from TagKit import Tag
from TagKit import TagCompositionError
from TagKit import TagContractError
from TagKit import TagImprintError
from TagKit import TagPostconditionError
from TagKit import Tags
from TagKit import Underlay
from TagKit.TagKit import _run_exit_protocols


class Agent:
    pass


class TagKitExtremeRegressionTests(
        unittest.TestCase,
        ):
    def test_structural_state_dunders_are_rejected_before_mutation(
            self,
            ) -> None:
        cases = (
                (
                    Action,
                    None,
                    ),
                (
                    Delete,
                    None,
                    ),
                (
                    Record,
                    {},
                    ),
                )

        for decorator, value in cases:
            for name in (
                    "__class__",
                    "__dict__",
                    ):
                with self.subTest(
                        decorator=decorator.__name__,
                        name=name,
                        ):
                    shape = type(
                            f"Structural_{decorator.__name__}_{name}",
                            (Tag,),
                            {
                                name:
                                    decorator(
                                            lambda target, value=value: value
                                            ),
                                },
                            )
                    target = Agent()

                    with self.assertRaises(
                            TagCompositionError
                            ):
                        shape(target)

                    self.assertIs(
                            type(target),
                            Agent,
                            )
                    self.assertEqual(
                            Tags(target),
                            (),
                            )
                    self.assertNotIn(
                            target,
                            shape,
                            )

    def test_field_iterator_skips_a_member_ripped_after_iteration_begins(
            self,
            ) -> None:
        class Member(Tag):
            pass

        first = Agent()
        second = Agent()

        Member(first)
        Member(second)

        stream = iter(
                Member[:]
                )
        yielded = next(stream)
        removed = (
                second
                if yielded is first
                else first
                )

        Member.Rip(removed)

        self.assertEqual(
                list(stream),
                [],
                )
        self.assertNotIn(
                removed,
                Member,
                )

    def test_form_and_application_do_not_use_python_recursion_depth(
            self,
            ) -> None:
        form_depth = 1_100
        current = Tag
        form: list[type[Tag]] = []

        for index in range(form_depth):
            current = type(
                    f"Deep_Form_{index}",
                    (current,),
                    {},
                    )
            form.append(current)

        self.assertEqual(
                current.Form(),
                tuple(form),
                )

        target = Agent()
        current(target)

        self.assertEqual(
                Tags(target),
                (
                    current,
                    ),
                )
        self.assertTrue(
                all(
                        target in tag
                        for tag in form
                        )
                )

        form[0].Rip(target)

        self.assertTrue(
                all(
                        target not in tag
                        for tag in form
                        )
                )

    def test_form_and_geometry_are_the_canonical_relationship_queries(
            self,
            ) -> None:
        class Being(Tag):
            pass

        class Person(Being):
            pass

        class Wizard(Person):
            pass

        class Hero:
            FORM_ROOTS = (
                    Person,
                    )

        target = Hero()
        Wizard(target)

        self.assertEqual(
                Wizard.Form(),
                (
                    Being,
                    Person,
                    Wizard,
                    ),
                )
        self.assertEqual(
                Wizard.Form(
                        roots=Hero.FORM_ROOTS,
                        ),
                (
                    Person,
                    Wizard,
                    ),
                )
        self.assertEqual(
                target.Forms(),
                (
                    (
                        Person,
                        Wizard,
                        ),
                    ),
                )
        self.assertEqual(
                target.Geometry(),
                {
                    Person:
                        (
                            Wizard,
                            ),
                    Wizard: (),
                    },
                )

        class Root(Tag):
            pass

        class First(Root):
            pass

        class Second(Root):
            pass

        class Diamond(
                First,
                Second,
                ):
            pass

        diamond_target = Agent()
        Diamond(diamond_target)

        self.assertEqual(
                diamond_target.Geometry(),
                {
                    Root:
                        (
                            First,
                            Second,
                            ),
                    First:
                        (
                            Diamond,
                            ),
                    Second:
                        (
                            Diamond,
                            ),
                    Diamond: (),
                    },
                )

    def test_deep_mutable_graph_rolls_back_without_recursive_capture(
            self,
            ) -> None:
        class Rejected(Tag):
            @Imprint
            def Mutate(
                    target,
                    ) -> None:
                target.leaf.append(
                        "changed"
                        )
                target.root.append(
                        "outer change"
                        )

            @Post
            def Reject(
                    target,
                    ) -> bool:
                return False

        depth = 5_000
        target = Agent()
        root: list[object] = []
        cursor = root

        for _index in range(depth):
            child: list[object] = []
            cursor.append(child)
            cursor = child

        target.root = root
        target.alias = root
        target.leaf = cursor

        with self.assertRaises(
                TagPostconditionError
                ):
            Rejected(target)

        self.assertIs(
                target.root,
                root,
                )
        self.assertIs(
                target.alias,
                root,
                )

        cursor = target.root

        for _index in range(depth):
            self.assertEqual(
                    len(cursor),
                    1,
                    )
            cursor = cursor[0]

        self.assertEqual(
                cursor,
                [],
                )
        self.assertNotIn(
                target,
                Rejected,
                )

    def test_bound_actions_preserve_async_and_generator_kinds(
            self,
            ) -> None:
        class Base(Tag):
            @Action
            async def Async_Value(
                    target,
                    ) -> int:
                return 1

            @Action
            def Values(
                    target,
                    ):
                yield 1

            @Action
            async def Async_Values(
                    target,
                    ):
                yield 1

        class Refined(Base):
            @Action
            @Underlay
            async def Async_Value(
                    target,
                    prior,
                    ) -> int:
                return (
                        await prior()
                        + 1
                        )

            @Action
            @Underlay
            def Values(
                    target,
                    prior,
                    ):
                yield from prior()
                yield 2

            @Action
            @Underlay
            async def Async_Values(
                    target,
                    prior,
                    ):
                async for value in prior():
                    yield value

                yield 2

        target = Agent()
        Refined(target)

        self.assertTrue(
                inspect.iscoroutinefunction(
                        target.Async_Value
                        )
                )
        self.assertTrue(
                inspect.isgeneratorfunction(
                        target.Values
                        )
                )
        self.assertTrue(
                inspect.isasyncgenfunction(
                        target.Async_Values
                        )
                )
        self.assertEqual(
                list(
                        target.Values()
                        ),
                [
                    1,
                    2,
                    ],
                )

        async def Exercise() -> None:
            self.assertEqual(
                    await target.Async_Value(),
                    2,
                    )
            self.assertEqual(
                    [
                        value
                        async for value in target.Async_Values()
                        ],
                    [
                        1,
                        2,
                        ],
                    )

        asyncio.run(
                Exercise()
                )

    def test_child_task_does_not_inherit_a_finished_tagging_boundary(
            self,
            ) -> None:
        tasks: list[asyncio.Task[None]] = []

        class Inner(Tag):
            pass

        class Outer(Tag):
            @Imprint
            def Schedule(
                    target,
                    ) -> None:
                async def Later() -> None:
                    await asyncio.sleep(0)
                    Inner(target)

                tasks.append(
                        asyncio.create_task(
                                Later()
                                )
                        )

        async def Exercise() -> None:
            target = Agent()

            Outer(target)
            await tasks[0]

            self.assertIn(
                    target,
                    Outer,
                    )
            self.assertIn(
                    target,
                    Inner,
                    )

        asyncio.run(
                Exercise()
                )

    def test_async_application_protocols_fail_without_unawaited_work(
            self,
            ) -> None:
        class Async_Imprint(Tag):
            @Imprint
            async def Establish(
                    target,
                    ) -> None:
                target.established = True

        class Async_Pre(Tag):
            @Pre
            async def Allowed(
                    target,
                    ) -> bool:
                return True

        class Async_Post(Tag):
            @Post
            async def Ready(
                    target,
                    ) -> bool:
                return True

        class Async_Record(Tag):
            @Record
            async def value(
                    target,
                    ) -> int:
                return 1

        cases = (
                (
                    Async_Imprint,
                    TagImprintError,
                    ),
                (
                    Async_Pre,
                    TagContractError,
                    ),
                (
                    Async_Post,
                    TagContractError,
                    ),
                (
                    Async_Record,
                    TagCompositionError,
                    ),
                )

        with warnings.catch_warnings(
                record=True,
                ) as caught:
            warnings.simplefilter(
                    "always"
                    )

            for tag, failure in cases:
                targets = (
                        (
                            "Agent",
                            Agent(),
                            ),
                        (
                            "Tag",
                            type(
                                    f"{tag.__name__}_Target",
                                    (Tag,),
                                    {},
                                    ),
                            ),
                        )

                for target_kind, target in targets:
                    with self.subTest(
                            tag=tag.__name__,
                            target=target_kind,
                            ):
                        original_type = type(target)

                        with self.assertRaises(failure):
                            tag(target)

                        self.assertNotIn(
                                target,
                                tag,
                                )
                        self.assertIs(
                                type(target),
                                original_type,
                                )
                        self.assertEqual(
                                Tags(target),
                                (),
                                )

            gc.collect()

        unawaited = [
                warning
                for warning in caught
                if "was never awaited" in str(
                        warning.message
                        )
                ]

        self.assertEqual(
                unawaited,
                [],
                )

    def test_async_rip_protocol_fails_explicitly_after_membership_ends(
            self,
            ) -> None:
        class Async_Teardown(Tag):
            @Rip
            async def Teardown(
                    target,
                    ) -> None:
                target.closed = True

        target = Agent()
        Async_Teardown(target)

        with warnings.catch_warnings(
                record=True,
                ) as caught:
            warnings.simplefilter(
                    "always"
                    )

            with self.assertRaises(
                    TagCompositionError
                    ):
                Async_Teardown.Rip(target)

            gc.collect()

        self.assertNotIn(
                target,
                Async_Teardown,
                )
        self.assertFalse(
                hasattr(
                        target,
                        "closed",
                        )
                )
        self.assertFalse(
                any(
                        "was never awaited" in str(
                                warning.message
                                )
                        for warning in caught
                        )
                )

    def test_generator_imprints_are_rejected_without_partial_execution(
            self,
            ) -> None:
        class Generator_Imprint(Tag):
            @Imprint
            def Establish(
                    target,
                    ):
                target.generator_imprint_started = True

                yield None

        class Async_Generator_Imprint(Tag):
            @Imprint
            async def Establish(
                    target,
                    ):
                target.async_generator_imprint_started = True

                yield None

        cases = (
                (
                    Generator_Imprint,
                    "generator_imprint_started",
                    ),
                (
                    Async_Generator_Imprint,
                    "async_generator_imprint_started",
                    ),
                )

        for tag, marker in cases:
            targets = (
                    Agent(),
                    type(
                            f"{tag.__name__}_Target",
                            (Tag,),
                            {},
                            ),
                    )

            for target in targets:
                with self.subTest(
                        tag=tag.__name__,
                        target=type(target).__name__,
                        ):
                    original_type = type(target)

                    with self.assertRaises(
                            TagImprintError
                            ):
                        tag(target)

                    self.assertFalse(
                            hasattr(
                                    target,
                                    marker,
                                    )
                            )
                    self.assertIs(
                            type(target),
                            original_type,
                            )
                    self.assertEqual(
                            Tags(target),
                            (),
                            )
                    self.assertNotIn(
                            target,
                            tag,
                            )

    def test_async_generator_records_are_rejected_for_agents_and_pins(
            self,
            ) -> None:
        class Async_Stream(Tag):
            @Record
            async def stream(
                    target,
                    ):
                yield 1

        targets = (
                Agent(),
                type(
                        "Async_Stream_Target",
                        (Tag,),
                        {},
                        ),
                )

        for target in targets:
            with self.subTest(
                    target=type(target).__name__,
                    ):
                original_type = type(target)

                with self.assertRaises(
                        TagCompositionError
                        ):
                    Async_Stream(target)

                self.assertIs(
                        type(target),
                        original_type,
                        )
                self.assertEqual(
                        Tags(target),
                        (),
                        )
                self.assertNotIn(
                        target,
                        Async_Stream,
                        )

    def test_generator_records_remain_valid_lazy_data(
            self,
            ) -> None:
        class Stream(Tag):
            @Record
            def values(
                    target,
                    ):
                yield 1
                yield 2

        agent = Agent()
        pin_target = type(
                "Stream_Target",
                (Tag,),
                {},
                )

        Stream(agent)
        Stream(pin_target)

        self.assertEqual(
                list(
                        agent.values
                        ),
                [
                    1,
                    2,
                    ],
                )
        self.assertEqual(
                list(
                        pin_target.values
                        ),
                [
                    1,
                    2,
                    ],
                )

    def test_generator_rips_fail_after_membership_ends(
            self,
            ) -> None:
        class Generator_Teardown(Tag):
            @Rip
            def Teardown(
                    target,
                    ):
                target.generator_rip_started = True

                yield None

        class Async_Generator_Teardown(Tag):
            @Rip
            async def Teardown(
                    target,
                    ):
                target.async_generator_rip_started = True

                yield None

        cases = (
                (
                    Generator_Teardown,
                    "generator_rip_started",
                    ),
                (
                    Async_Generator_Teardown,
                    "async_generator_rip_started",
                    ),
                )

        for tag, marker in cases:
            target = Agent()
            tag(target)

            with self.subTest(
                    tag=tag.__name__,
                    ):
                with self.assertRaises(
                        TagCompositionError
                        ):
                    tag.Rip(target)

                self.assertNotIn(
                        target,
                        tag,
                        )
                self.assertFalse(
                        hasattr(
                                target,
                                marker,
                                )
                        )

    def test_automatic_rips_discard_lazy_results_without_warnings(
            self,
            ) -> None:
        class Lazy_Teardown(Tag):
            @Rip
            async def Coroutine(
                    target,
                    ) -> None:
                target.coroutine_rip_started = True

            @Rip
            def Generator(
                    target,
                    ):
                target.generator_rip_started = True

                yield None

            @Rip
            async def Async_Generator(
                    target,
                    ):
                target.async_generator_rip_started = True

                yield None

        finalizer_target = Agent()
        exit_target = Agent()

        Lazy_Teardown(finalizer_target)
        Lazy_Teardown(exit_target)
        At_Exit(exit_target)

        with warnings.catch_warnings(
                record=True,
                ) as caught:
            warnings.simplefilter(
                    "always"
                    )

            finalizer_target.__del__()
            _run_exit_protocols()
            gc.collect()

        markers = (
                "coroutine_rip_started",
                "generator_rip_started",
                "async_generator_rip_started",
                )

        for target in (
                finalizer_target,
                exit_target,
                ):
            for marker in markers:
                self.assertFalse(
                        hasattr(
                                target,
                                marker,
                                )
                        )

        self.assertFalse(
                any(
                        "was never awaited" in str(
                                warning.message
                                )
                        for warning in caught
                        )
                )

    def test_atlas_discovers_a_later_base_after_successful_rebase(
            self,
            ) -> None:
        events: list[str] = []

        class Old_Root(Tag):
            @Imprint
            def Mark(
                    target,
                    ) -> None:
                events.append(
                        "old"
                        )

        class New_Root(Tag):
            @Imprint
            def Mark(
                    target,
                    ) -> None:
                events.append(
                        "new"
                        )

        class Later(Old_Root):
            @Imprint
            def Mark_Later(
                    target,
                    ) -> None:
                events.append(
                        "later"
                        )

        class First(Tag):
            @Imprint
            def Rebase(
                    target,
                    ) -> None:
                events.append(
                        "first"
                        )
                Later.__bases__ = (
                        New_Root,
                        )

        class Combined(
                First,
                Later,
                ):
            pass

        target = Agent()

        try:
            Combined(target)

            self.assertEqual(
                    events,
                    [
                        "first",
                        "new",
                        "later",
                        ],
                    )
            self.assertNotIn(
                    target,
                    Old_Root,
                    )
            self.assertIn(
                    target,
                    New_Root,
                    )
        finally:
            Later.__bases__ = (
                    Old_Root,
                    )

    def test_leaf_query_recovers_after_a_pin_rebases_an_active_tag(
            self,
            ) -> None:
        class Root(Tag):
            pass

        class Bridge(Root):
            pass

        class Shape(Tag):
            pass

        class Rebase(Tag):
            @Imprint
            def Attach_Bridge(
                    target,
                    ) -> None:
                target.__bases__ = (
                        Bridge,
                        )

        target = Agent()

        Root(target)
        Shape(target)

        try:
            Rebase(Shape)

            self.assertEqual(
                    Shape.Form(),
                    (
                        Root,
                        Bridge,
                        Shape,
                        ),
                    )
            self.assertEqual(
                    Tags(target),
                    (
                        Shape,
                        ),
                    )
        finally:
            Shape.__bases__ = (
                    Tag,
                    )

    def test_host_actualization_failure_is_normalized_and_atomic(
            self,
            ) -> None:
        class Restrictive_Host:
            def __setattr__(
                    target,
                    name: str,
                    value: object,
                    ) -> None:
                if name == "__class__":
                    raise RuntimeError(
                            "runtime type changes are forbidden"
                            )

                object.__setattr__(
                        target,
                        name,
                        value,
                        )

        class Role(Tag):
            pass

        target = Restrictive_Host()

        with self.assertRaises(
                TagCompositionError
                ) as raised:
            Role(target)

        self.assertIsInstance(
                raised.exception.__cause__,
                RuntimeError,
                )
        self.assertIs(
                type(target),
                Restrictive_Host,
                )
        self.assertEqual(
                Tags(target),
                (),
                )
        self.assertNotIn(
                target,
                Role,
                )

    def test_silent_host_actualization_is_detected_and_rolled_back(
            self,
            ) -> None:
        class Silent_Host:
            def __setattr__(
                    target,
                    name: str,
                    value: object,
                    ) -> None:
                if name == "__class__":
                    return

                object.__setattr__(
                        target,
                        name,
                        value,
                        )

        class Role(Tag):
            @Action
            def Signal(
                    target,
                    ) -> str:
                return "tagged"

        target = Silent_Host()

        with self.assertRaises(
                TagCompositionError
                ):
            Role(target)

        self.assertIs(
                type(target),
                Silent_Host,
                )
        self.assertEqual(
                Tags(target),
                (),
                )
        self.assertNotIn(
                target,
                Role,
                )
        self.assertFalse(
                hasattr(
                        target,
                        "Signal",
                        )
                )

    def test_failed_tagging_bypasses_a_host_veto_during_restoration(
            self,
            ) -> None:
        class One_Way_Host:
            def __setattr__(
                    target,
                    name: str,
                    value: object,
                    ) -> None:
                restoring_host = (
                        name == "__class__"
                        and value is One_Way_Host
                        and type(target) is not One_Way_Host
                        )

                if restoring_host:
                    raise RuntimeError(
                            "host refuses restoration"
                            )

                object.__setattr__(
                        target,
                        name,
                        value,
                        )

        class Rejected(Tag):
            @Action
            def Ghost(
                    target,
                    ) -> str:
                return "visible only while provisional"

            @Post
            def Reject(
                    target,
                    ) -> bool:
                return False

        target = One_Way_Host()

        with self.assertRaises(
                TagPostconditionError
                ):
            Rejected(target)

        self.assertIs(
                type(target),
                One_Way_Host,
                )
        self.assertEqual(
                Tags(target),
                (),
                )
        self.assertNotIn(
                target,
                Rejected,
                )
        self.assertFalse(
                hasattr(
                        target,
                        "Ghost",
                        )
                )

    def test_non_dictionary_instance_namespace_is_rejected_cleanly(
            self,
            ) -> None:
        class Misleading_Host:
            @property
            def __dict__(
                    target,
                    ) -> dict[str, object]:
                return {}

        class Role(Tag):
            pass

        target = Misleading_Host()

        with self.assertRaises(
                TagCompositionError
                ):
            Role(target)

        self.assertIs(
                type(target),
                Misleading_Host,
                )
        self.assertEqual(
                Tags(target),
                (),
                )
        self.assertNotIn(
                target,
                Role,
                )

    def test_shadowed_base_slot_rolls_back_through_its_storage_descriptor(
            self,
            ) -> None:
        class Slotted_Base:
            __slots__ = (
                    "value",
                    "__dict__",
                    "__weakref__",
                    )

        value_slot = Slotted_Base.__dict__[
                "value"
                ]

        class Shadowed_Host(Slotted_Base):
            @property
            def value(
                    target,
                    ) -> str:
                return "visible property"

        class Rejected(Tag):
            @Imprint
            def Mutate_Hidden_Slot(
                    target,
                    ) -> None:
                value_slot.__set__(
                        target,
                        "changed",
                        )

            @Post
            def Reject(
                    target,
                    ) -> bool:
                return False

        target = Shadowed_Host()
        value_slot.__set__(
                target,
                "original",
                )

        with self.assertRaises(
                TagPostconditionError
                ):
            Rejected(target)

        self.assertEqual(
                value_slot.__get__(
                        target,
                        Shadowed_Host,
                        ),
                "original",
                )
        self.assertEqual(
                target.value,
                "visible property",
                )
        self.assertEqual(
                Tags(target),
                (),
                )

    def test_host_subclass_hook_failure_is_normalized_and_atomic(
            self,
            ) -> None:
        class Explosive_Host:
            def __init_subclass__(
                    host,
                    **kwargs,
                    ) -> None:
                raise RuntimeError(
                        "runtime subclass creation denied"
                        )

        class Role(Tag):
            pass

        target = Explosive_Host()

        with self.assertRaises(
                TagCompositionError
                ) as raised:
            Role(target)

        self.assertIsInstance(
                raised.exception.__cause__,
                RuntimeError,
                )
        self.assertIs(
                type(target),
                Explosive_Host,
                )
        self.assertEqual(
                Tags(target),
                (),
                )
        self.assertNotIn(
                target,
                Role,
                )

    def test_host_metaclass_cannot_substitute_the_requested_runtime_type(
            self,
            ) -> None:
        class Substituting_Metaclass(type):
            def __new__(
                    metaclass,
                    name: str,
                    bases: tuple[type, ...],
                    namespace: dict[str, object],
                    ):
                if name.startswith(
                        "Substituting_Host__"
                        ):
                    return bases[-1]

                return super().__new__(
                        metaclass,
                        name,
                        bases,
                        namespace,
                        )

        class Substituting_Host(
                metaclass=Substituting_Metaclass,
                ):
            pass

        class Role(Tag):
            @Action
            def Signal(
                    target,
                    ) -> str:
                return "tagged"

        target = Substituting_Host()

        with self.assertRaises(
                TagCompositionError
                ):
            Role(target)

        self.assertIs(
                type(target),
                Substituting_Host,
                )
        self.assertEqual(
                Tags(target),
                (),
                )
        self.assertNotIn(
                target,
                Role,
                )
        self.assertFalse(
                hasattr(
                        target,
                        "Signal",
                        )
                )

    def test_deep_pin_atlas_uses_the_same_iterative_order(
            self,
            ) -> None:
        depth = 400
        current = Tag
        pins: list[type[Tag]] = []

        for index in range(depth):
            current = type(
                    f"Deep_Pin_{index}",
                    (current,),
                    {},
                    )
            pins.append(current)

        class Entry(Tag):
            pass

        current(Entry)

        self.assertEqual(
                Tags(Entry),
                (
                    current,
                    ),
                )
        self.assertTrue(
                all(
                        Entry in pin
                        for pin in pins
                        )
                )

        pins[0].Rip(Entry)

        self.assertTrue(
                all(
                        Entry not in pin
                        for pin in pins
                        )
                )


if __name__ == "__main__":
    unittest.main()
