"""Conformance tests: deliberate difference."""

from __future__ import annotations

import unittest
import warnings
from TopKit import Pre
from TopKit import Tag
from TopKit import TagOverwriteWarning

from ._fixtures import Agent
from ._fixtures import Run_Program


class DeliberateDifferenceTests(unittest.TestCase):
    """Two fixes of the performance work (PERFORMANCE-2026-09-24.md, 4.2)
    that change what a program can observe, each shown here."""

    def test_a_gate_in_one_thread_silences_no_warning_in_another(self) -> None:
        import sys
        import threading

        class Base(Tag):
            def Attack(agent) -> str:
                return "base"

        class Rival(Tag):
            def Attack(agent) -> str:   # replaces an independent Tag's Action: warns
                return "rival"

        class Gated(Tag):
            @Pre
            def Ready(agent) -> bool:
                return True

        rounds = 3000
        heard: list[int] = []
        warner: list[int] = []

        def Show(message, category, filename, lineno, file=None, line=None) -> None:
            if issubclass(category, TagOverwriteWarning) and threading.get_ident() in warner:
                heard.append(1)

        def Warn() -> None:
            warner.append(threading.get_ident())

            for _ in range(rounds):
                hero = Agent()
                Base(hero)
                Rival(hero)

        def Gate() -> None:
            while not done.is_set():
                Gated(Agent())                 # its scratch pass is silenced

        done = threading.Event()
        interval = sys.getswitchinterval()
        shown = warnings.showwarning

        with warnings.catch_warnings():
            warnings.simplefilter("always")
            warnings.showwarning = Show
            sys.setswitchinterval(1e-6)

            try:
                gate = threading.Thread(target=Gate)
                gate.start()
                warn = threading.Thread(target=Warn)
                warn.start()
                warn.join()
                done.set()
                gate.join()
            finally:
                sys.setswitchinterval(interval)
                warnings.showwarning = shown

        self.assertEqual(len(heard), rounds)   # the old kit delivered about four in five

    def test_queries_from_a_finalizer_answer_at_shutdown(self) -> None:
        lines, stderr = Run_Program(
                """
from TopKit import Tag, Flag, Keyword, Post, Public, Report

class Host:
    alive = True

@Flag("Wolf")
class Werewolf(Tag):
    @Post
    def Fed(agent): return agent.alive

    @Public
    @Report
    def pack(tag): return "north"

class Witness:                        # an untagged object whose finalizer asks
    def __init__(self, agent): self.agent = agent
    def __del__(self):
        for label, ask in (
                ("bool", lambda: bool(self.agent)),
                ("keyword", lambda: Keyword(self.agent, "Wolf")),
                ("condition", lambda: self.agent.Fed),
                ("report", lambda: self.agent.pack),
                ):
            try:
                print(label, ask())
            except Exception as error:
                print(label, type(error).__name__)

ari = Host()
Werewolf(ari)
witness = Witness(ari)
print("end")
""",
                )

        self.assertEqual(
                lines,
                ["end", "bool True", "keyword True", "condition True", "report north"],
                )
