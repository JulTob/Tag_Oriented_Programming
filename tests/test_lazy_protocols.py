"""Synchronous application protocols reject lazy return objects."""

from __future__ import annotations

import gc
import pathlib
import subprocess
import sys
import unittest
import warnings
from typing import Any
from typing import Callable

from TopKit import Imprint
from TopKit import Pin
from TopKit import Post
from TopKit import Pre
from TopKit import Rip
from TopKit import Tag
from TopKit import TagCompositionError
from TopKit import TagContractError
from TopKit import TagImprintError
from TopKit import Underlay


class Agent:
    pass


def _lazy_protocol(
        kind: str,
        marker: str,
        ) -> Callable[[object], Any]:
    if kind == "coroutine":
        async def Lazy(target: object) -> None:
            setattr(target, marker, True)
    elif kind == "generator":
        def Lazy(target: object) -> Any:
            setattr(target, marker, True)
            yield None
    else:
        async def Lazy(target: object) -> Any:
            setattr(target, marker, True)
            yield None

    return Lazy


def _protocol_tag(
        mark: Callable[[Callable[..., Any]], Callable[..., Any]],
        phase: str,
        kind: str,
        pinned: bool,
        marker: str,
        ) -> type:
    tag = type(
            f"Lazy_{phase}_{kind.replace(' ', '_')}_{'Pin' if pinned else 'Tag'}",
            (Tag,),
            {
                "Lazy": mark(
                        _lazy_protocol(
                                kind,
                                marker,
                                )
                        ),
                },
            )

    return Pin(tag) if pinned else tag


def _target(
        pinned: bool,
        name: str,
        ) -> object:
    if pinned:
        return type(
                f"{name}_Target",
                (Tag,),
                {},
                )

    return Agent()


class LazyProtocolTests(unittest.TestCase):
    kinds = (
            "coroutine",
            "generator",
            "async generator",
            )

    def assert_no_unawaited(
            self,
            caught: list[warnings.WarningMessage],
            ) -> None:
        self.assertFalse(
                any(
                    "was never awaited" in str(item.message)
                    for item in caught
                    ),
                caught,
                )

    def test_lazy_conditions_fail_in_their_established_phase(self) -> None:
        phases = (
                ("Precondition", Pre, False),
                ("Postcondition", Post, True),
                )

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            for phase, mark, keeps_tag in phases:
                for kind in self.kinds:
                    for pinned in (False, True):
                        marker = f"{phase}_{kind}_{pinned}_started"
                        tag = _protocol_tag(
                                mark,
                                phase,
                                kind,
                                pinned,
                                marker,
                                )
                        target = _target(
                                pinned,
                                tag.__name__,
                                )
                        original_type = type(target)

                        with self.subTest(
                                phase=phase,
                                kind=kind,
                                target="Pin" if pinned else "Agent",
                                ):
                            with self.assertRaises(TagContractError) as failure:
                                tag(target)

                            self.assertIn(
                                    f"{phase} 'Lazy' returned",
                                    str(failure.exception),
                                    )
                            self.assertIn(kind, str(failure.exception))
                            self.assertFalse(hasattr(target, marker))
                            self.assertEqual(target in tag, keeps_tag)

                            if not keeps_tag:
                                self.assertIs(type(target), original_type)

            gc.collect()

        self.assert_no_unawaited(caught)

    def test_a_lazy_condition_cannot_hide_beneath_an_underlay(self) -> None:
        phases = (
                ("Precondition", Pre, False),
                ("Postcondition", Post, True),
                )

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            for phase, mark, keeps_tag in phases:
                for kind in self.kinds:
                    marker = f"underlay_{phase}_{kind}_started"
                    prior = _lazy_protocol(
                            kind,
                            marker,
                            )
                    prior.__name__ = "Gate"
                    base = type(
                            f"Lazy_{phase}_{kind.replace(' ', '_')}_Base",
                            (Tag,),
                            {
                                "Gate": mark(prior),
                                },
                            )

                    def Gate(target: object, underlay: Callable[[], bool]) -> bool:
                        underlay()

                        return True

                    shape = type(
                            f"Lazy_{phase}_{kind.replace(' ', '_')}_Shape",
                            (base,),
                            {
                                "Gate": mark(Underlay(Gate)),
                                },
                            )
                    target = Agent()

                    with self.subTest(
                            phase=phase,
                            kind=kind,
                            ):
                        with self.assertRaises(TagContractError) as failure:
                            shape(target)

                        self.assertIn(
                                f"{phase} 'Gate'",
                                str(failure.exception),
                                )
                        self.assertIn(kind, str(failure.exception))
                        self.assertFalse(hasattr(target, marker))
                        self.assertEqual(target in shape, keeps_tag)

            gc.collect()

        self.assert_no_unawaited(caught)

    def test_lazy_condition_disposal_failure_stays_a_contract_failure(self) -> None:
        def Exploding_Close() -> Any:
            try:
                yield None
            finally:
                raise RuntimeError("close exploded")

        lazy = Exploding_Close()
        next(lazy)

        class Gated(Tag):
            @Pre
            def Ready(agent: object) -> Any:
                return lazy

        target = Agent()

        with self.assertRaises(TagContractError) as failure:
            Gated(target)

        self.assertIn("Precondition 'Ready'", str(failure.exception))
        self.assertIn("close exploded", str(failure.exception))
        self.assertIsInstance(failure.exception.__cause__, RuntimeError)
        self.assertNotIn(target, Gated)

    def test_lazy_imprints_fail_after_membership_without_starting(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            for kind in self.kinds:
                for pinned in (False, True):
                    marker = f"Imprint_{kind}_{pinned}_started"
                    tag = _protocol_tag(
                            Imprint,
                            "Imprint",
                            kind,
                            pinned,
                            marker,
                            )
                    target = _target(
                            pinned,
                            tag.__name__,
                            )

                    with self.subTest(
                            kind=kind,
                            target="Pin" if pinned else "Agent",
                            ):
                        with self.assertRaises(TagImprintError.Lazy) as failure:
                            tag(target)

                        self.assertIn(kind, str(failure.exception))
                        self.assertFalse(hasattr(target, marker))
                        self.assertIn(target, tag)

            gc.collect()

        self.assert_no_unawaited(caught)

    def test_lazy_rips_fail_after_membership_ends_without_starting(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            for kind in self.kinds:
                for pinned in (False, True):
                    marker = f"Rip_{kind}_{pinned}_started"
                    tag = _protocol_tag(
                            Rip,
                            "Rip",
                            kind,
                            pinned,
                            marker,
                            )
                    target = _target(
                            pinned,
                            tag.__name__,
                            )
                    tag(target)

                    with self.subTest(
                            kind=kind,
                            target="Pin" if pinned else "Agent",
                            ):
                        with self.assertRaises(TagCompositionError) as failure:
                            del tag[target]

                        self.assertIn("teardown failed in: Lazy", str(failure.exception))
                        self.assertIsInstance(
                                failure.exception.__cause__,
                                TagCompositionError,
                                )
                        self.assertIn(
                                kind,
                                str(failure.exception.__cause__),
                                )
                        self.assertFalse(hasattr(target, marker))
                        self.assertNotIn(target, tag)

            gc.collect()

        self.assert_no_unawaited(caught)

    def test_a_lazy_rip_cannot_hide_beneath_an_underlay(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            for kind in self.kinds:
                for pinned in (False, True):
                    marker = f"Rip_underlay_{kind}_{pinned}_started"
                    prior = _lazy_protocol(
                            kind,
                            marker,
                            )
                    prior.__name__ = "Close"
                    base = type(
                            f"Lazy_Rip_{kind.replace(' ', '_')}_Base_"
                            f"{'Pin' if pinned else 'Tag'}",
                            (Tag,),
                            {
                                "Close": Rip(prior),
                                },
                            )

                    if pinned:
                        base = Pin(base)

                    def Close(target: object, underlay: Callable[[], Any]) -> None:
                        underlay()

                    shape = type(
                            f"Lazy_Rip_{kind.replace(' ', '_')}_Shape_"
                            f"{'Pin' if pinned else 'Tag'}",
                            (base,),
                            {
                                "Close": Rip(Underlay(Close)),
                                },
                            )
                    target = _target(
                            pinned,
                            shape.__name__,
                            )
                    shape(target)

                    with self.subTest(
                            kind=kind,
                            target="Pin" if pinned else "Agent",
                            ):
                        with self.assertRaises(TagCompositionError) as failure:
                            del shape[target]

                        self.assertIn("teardown failed in: Close", str(failure.exception))
                        self.assertIn(
                                kind,
                                str(failure.exception.__cause__),
                                )
                        self.assertFalse(hasattr(target, marker))
                        self.assertNotIn(target, shape)
                        self.assertIn(target, base)

            gc.collect()

        self.assert_no_unawaited(caught)

    def test_an_ordinary_middle_layer_cannot_hide_a_lazy_rip_base(self) -> None:
        class Base(Tag):
            @Rip
            async def Close(agent: object) -> None:
                agent.started = True

        class Middle(Base):
            @Underlay
            def Close(agent: object, underlay: Callable[[], Any]) -> None:
                underlay()

        class Top(Middle):
            @Rip
            @Underlay
            def Close(agent: object, underlay: Callable[[], Any]) -> None:
                underlay()

        target = Agent()
        Top(target)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            with self.assertRaises(TagCompositionError):
                del Top[target]

            gc.collect()

        self.assertFalse(hasattr(target, "started"))
        self.assertNotIn(target, Top)
        self.assert_no_unawaited(caught)

    def test_a_rip_does_not_turn_an_ordinary_streaming_action_into_a_protocol(
            self,
            ) -> None:
        class Stream_Base(Tag):
            @Rip
            def Values(agent: object) -> Any:
                yield 1

        class Stream(Stream_Base):
            @Rip
            @Underlay
            def Values(agent: object, underlay: Callable[[], Any]) -> Any:
                yield from underlay()
                yield 2

        class Cleanup(Tag):
            @Rip
            def Read(agent: object) -> None:
                agent.seen = list(agent.Values())

        target = Agent()
        Stream(target)
        Cleanup(target)

        del Cleanup[target]

        self.assertEqual(target.seen, [1, 2])
        self.assertNotIn(target, Cleanup)
        self.assertIn(target, Stream)

    def test_a_caught_rip_disposal_error_still_fails_the_protocol(self) -> None:
        def Exploding_Close() -> Any:
            try:
                yield None
            finally:
                raise RuntimeError("close exploded")

        lazy = Exploding_Close()
        next(lazy)

        class Base(Tag):
            @Rip
            def Close(agent: object) -> Any:
                return lazy

        class Shape(Base):
            @Rip
            @Underlay
            def Close(agent: object, underlay: Callable[[], Any]) -> None:
                try:
                    underlay()
                except TagCompositionError:
                    pass

        target = Agent()
        Shape(target)

        with self.assertRaises(TagCompositionError) as failure:
            del Shape[target]

        protocol_failure = failure.exception.__cause__
        self.assertIsInstance(protocol_failure, TagCompositionError)
        self.assertIn("close exploded", str(protocol_failure))
        self.assertIsInstance(protocol_failure.__cause__, RuntimeError)
        self.assertNotIn(target, Shape)

    def test_automatic_teardown_closes_coroutines_and_starts_nothing(self) -> None:
        root = pathlib.Path(__file__).resolve().parent.parent
        program = """
from TopKit import At_Exit, Rip, Tag, Underlay
from TopKit.lifecycle import _run_exit_protocols

class Agent:
    pass

class Lazy_Base(Tag):
    @Rip
    async def Coroutine(agent):
        agent.coroutine_started = True

    @Rip
    def Generator(agent):
        agent.generator_started = True
        yield None

    @Rip
    async def Async_Generator(agent):
        agent.async_generator_started = True
        yield None

class Lazy(Lazy_Base):
    @Rip
    @Underlay
    def Coroutine(agent, base):
        base()

    @Rip
    @Underlay
    def Generator(agent, base):
        base()

    @Rip
    @Underlay
    def Async_Generator(agent, base):
        base()

def started(agent):
    return tuple(
        hasattr(agent, name)
        for name in (
            "coroutine_started",
            "generator_started",
            "async_generator_started",
        )
    )

finalized = Agent()
Lazy(finalized)
finalized.__del__()
print(started(finalized))

at_exit = Agent()
Lazy(at_exit)
At_Exit(at_exit)
_run_exit_protocols()
print(started(at_exit))
"""
        result = subprocess.run(
                [
                    sys.executable,
                    "-E",
                    "-W",
                    "always",
                    "-c",
                    program,
                    ],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=60,
                )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
                result.stdout.splitlines(),
                [
                    "(False, False, False)",
                    "(False, False, False)",
                    ],
                )
        self.assertNotIn("was never awaited", result.stderr)


if __name__ == "__main__":
    unittest.main()
