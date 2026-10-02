"""Differential fuzzing: two versions of TopKit, the same random programs.

Everything a program can observe must agree between the two kits. Each
seed makes one deterministic Python program that uses TOP broadly:
Tag families with Bases, Shapes and diamonds; Records with a stored seat
and inputs; Actions with and without @Underlay, special methods among
them; gates, promises and Requirements; Imprints, Rips, Deletes, Secrets,
published Reports and Operations, Flags with words, Pins; Scope, Apply,
applying, re-applying and Ripping; Flags marked and Tags renamed while
the program runs, and Tags declared in a function; broken promises and
the Fields that sort them; views, queries and keywords; At_Exit, deleted
Agents and collected cycles; hosts and Tags with finalizers of their
own; and what happens at interpreter exit.

A Flag is part of the Tag's declaration (STEP-SPEC-17, 2026-09-29): the
kit refuses a mark on a Tag that has members, or whose Shapes have. So a
Flag marked while the program runs lands only on a Tag nobody carries.
Where Agents carry it, the step expects the refusal, with the Tag's name
and the count, and the Tag's words unchanged; it writes "carried by N".
A kit from before the refusal takes the mark, and the step takes it back,
so both kits go on alike. A kit that stopped refusing would read the same
here; the unit tests pin the refusal. Every word the programs give a Flag
is a plain string literal, given one by one, so a word kept as its plain
text (a `str` subclass matched by its text) reads the same on both sides
too, and so do words given as a list, a tuple, a set or a frozenset
(2026-10-02), which a kit from before refuses; `tests/test_topkit.py`
alone covers both.

A Scope reports a Rip it cannot make, refused or with a teardown that
fails (STEP-SPEC-6, drafted 2026-10-02): the Composition Failure leaves
the `with`, or is a note on the block's own exception. A kit from before
dropped it, so such a step reads differently against one. A Tag keeps
its Report values under `_topkit_reports` in its own `__dict__`; the
look at a Tag leaves that name out, so kits before and after compare.

Every step writes what it observed: a value, or an exception's type,
message, cause and notes. A step that changes a Target is often followed by a
look at it: its Tags, soundness, contract, words, and the names it holds.
Warnings (category, message, file:line), finalizers, teardowns and
Imprints are written as events of the step that caused them. An
exception nobody can catch (a finalizer's) is reported on standard
error, which the transcript takes in order with standard output. The
program runs in a fresh interpreter on each kit, and the two transcripts
are compared line by line.

Run from the repository root:

    PYTHONPATH=. python3 tests/differential_fuzz.py --base origin/main --seeds 200 --steps 300
    PYTHONPATH=. python3 tests/differential_fuzz.py --base 1cedd77 --new b819b0a --steps 800 --heavy

--base and --new name a git ref, or `.` for the working tree. --new
defaults to the working tree and --base to HEAD, so a bare run asks what
the uncommitted work changes. A ref is unpacked with `git archive` into a
temporary directory: the repository is never written. Each differing
seed is printed with a short unified diff, then a summary; the exit
status is 1 when a seed differs, times out, or does not end cleanly.
--keep DIR keeps every program and both transcripts, to replay or diff.

Held fixed, so that a difference means the kit: the program, the hash
seed, and the garbage collector, which the program disables so a cycle
is collected only where it says (the events of one collection are
sorted: it frees in no promised order). Normalized, because they differ
between versions legitimately: memory addresses, and the kit's own file
paths and line numbers (as TopKit/<file>:N). The program's lines are
kept: a warning must blame the same line of the program on both kits.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from dataclasses import field
from typing import Callable
from typing import NamedTuple
import argparse
import difflib
import io
import os
import pathlib
import random
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import time


REPOSITORY = pathlib.Path(__file__).resolve().parent.parent
STANDARD_LIBRARY = os.path.dirname(os.__file__)   # where a warning raised through contextlib points
WORKING_TREE = "."
DIFF_LINES_SHOWN = 40           # per differing seed


# ------------------------------------------------------------------
# The program: a prelude, the Tags, the Agents, the steps
# ------------------------------------------------------------------


PRELUDE = r'''
import copy
import gc
import sys
import warnings

gc.disable()   # a cycle is collected only where the program says, alike on every kit

from TopKit import Action
from TopKit import Apply
from TopKit import At_Exit
from TopKit import Contract
from TopKit import Delete
from TopKit import Flag
from TopKit import Form
from TopKit import Imprint
from TopKit import Keyword
from TopKit import Operation
from TopKit import Outline
from TopKit import Pin
from TopKit import Post
from TopKit import Pre
from TopKit import Public
from TopKit import Record
from TopKit import Report
from TopKit import Requirement
from TopKit import Rip
from TopKit import Scope
from TopKit import Secret
from TopKit import Tag
from TopKit import Tags
from TopKit import Underlay


class Log:
    """The transcript, on standard output. Events wait for the end of
    their step; after "=== exit ===" they are written as they happen.
    A finalizer reaches the Log through a default argument, because the
    module's names may be gone when it runs."""

    def __init__(
            log,
            write,
            ):
        log.write = write
        log.events = []
        log.exiting = False

    def Say(
            log,
            line,
            ):
        log.write(line + "\n")

    def Event(
            log,
            text,
            ):
        if log.exiting:
            log.write("exit " + text + "\n")
        else:
            log.events.append(text)

    def Flush(
            log,
            step,
            collected=False,
            ):
        events = sorted(log.events) if collected else log.events   # one collection frees in no promised order
        log.events = []

        for text in events:
            log.write(step + " > " + text + "\n")

    def Show(
            log,
            value,
            ):
        if value is None or isinstance(value, (bool, int, float, str)):
            return repr(value)

        if isinstance(value, type):
            return value.__name__

        if isinstance(value, (tuple, list)):
            shown = ", ".join(log.Show(item) for item in value)

            return "(" + shown + ")" if isinstance(value, tuple) else "[" + shown + "]"

        if isinstance(value, dict):
            return "{" + ", ".join(log.Show(key) + ": " + log.Show(item) for key, item in value.items()) + "}"

        try:
            own = object.__getattribute__(value, "__dict__")
        except AttributeError:
            own = {}

        if "name" in own:
            return "<" + str(own["name"]) + ">"   # a host: by its name, never by its address

        return repr(value)

    def Failure(
            log,
            error,
            ):
        text = type(error).__qualname__ + ": " + str(error)
        cause = error.__cause__

        if cause is not None:
            text += " (from " + type(cause).__qualname__ + ": " + str(cause) + ")"

        for note in getattr(error, "__notes__", ()):
            text += " [note: " + str(note) + "]"

        return text


LOG = Log(sys.stdout.write)


def Do(
        step,
        label,
        thunk,
        *,
        log=LOG,
        ):
    """Run one step and write what it observed, then its events."""

    try:
        observed = "= " + log.Show(thunk())
    except Exception as error:
        observed = "! " + log.Failure(error)

    log.Say(step + " " + label + " " + observed)
    log.Flush(step)


def Warned(
        message,
        category,
        filename,
        lineno,
        file=None,
        line=None,
        *,
        log=LOG,
        ):
    log.Event("warning " + category.__name__ + ": " + str(message) + " @ " + filename + ":" + str(lineno))


# No sys.unraisablehook: one defined here would keep this module alive
# past exit, and its finalizers would never run.
warnings.showwarning = Warned


def Set(
        target,
        name,
        value,
        ):
    setattr(target, name, value)


def Unset(
        target,
        name,
        ):
    delattr(target, name)


def Rip_Of(
        tag,
        target,
        ):
    del tag[target]


def Tag_All(
        tag,
        *targets,
        **inputs,
        ):
    """One line tags them all: a warning given here is given once."""

    for target in targets:
        tag(target, **inputs)


def Look(
        target,
        ):
    """A Target after a step changed it: its Tags, whether its promises
    hold, its contract, the words it answers to, and the names it holds
    itself."""

    return (
            Tags(target),
            bool(target),
            Contract.Status(target),
            [word for word in KNOWN_WORDS if Keyword(target, word)],
            sorted(name for name in vars(target) if name != "_topkit_reports"),   # a Tag keeps its Report values there
            )


def Carried(
        tag,
        ):
    """How many live members the Tag has. A Shape's members are its Base's
    too (§0.3)."""

    return len({id(member) for member in tag[:]})


def Late_Flag(
        tag,
        mark,
        ):
    """A Flag marked while the program runs. A Flag is part of the Tag's
    declaration (STEP-SPEC-17, 2026-09-29): a Tag that has members refuses
    the mark, names itself and the count, and keeps its words. A kit from
    before the refusal took the mark; here it is taken back, so both kits
    go on alike."""

    carried = Carried(tag)

    if not carried:
        mark(tag)

        return "marked"

    missing = object()
    before = vars(tag).get("__topkit_flag__", missing)

    try:
        mark(tag)

    except Exception as error:
        if (
                type(error).__name__ != "TagDeclarationError"
                or not str(error).startswith(f"{tag.__name__} is carried by {carried} ")
                or vars(tag).get("__topkit_flag__", missing) is not before
                ):
            raise

    else:   # a kit from before the refusal
        if before is missing:
            delattr(tag, "__topkit_flag__")
        else:
            setattr(tag, "__topkit_flag__", before)

    return "carried by " + str(carried)


class Host:
    """An ordinary object that becomes an Agent."""

    def __init__(
            host,
            name,
            ):
        host.name = name
        host.ok = True                  # what the promises read
        host.level = 1

    def describe(
            host,
            ):
        return host.name + " at level " + str(host.level)

    def Speak(
            host,
            *words,
            ):
        return host.name + " says " + " ".join(str(word) for word in words)


class Keeper(Host):
    """A host with a finalizer of its own."""

    def __del__(
            host,
            *,
            log=LOG,
            ):
        log.Event("Keeper.__del__ " + host.name)


class Bag(Host):
    """A host that answers `in` itself: no Flag may take the seat."""

    def __contains__(
            host,
            item,
            ):
        return item == host.name

    def __iter__(
            host,
            ):
        return iter((host.name,))


class Roster(Host):
    """A host that answers `in` through iteration alone."""

    def __iter__(
            host,
            ):
        return iter(("roster", host.name))


class Ledger(Host):
    """A keyed host, an old-style sequence of two: `in` walks the keys."""

    def __getitem__(
            host,
            key,
            ):
        if isinstance(key, int) and key > 1:
            raise IndexError(key)

        return host.name + "[" + str(key) + "]"


class Keepsake:
    """Held only by a Tag declared in a function: freed when the Tag is."""

    def __init__(
            keepsake,
            label,
            ):
        keepsake.label = label

    def __del__(
            keepsake,
            *,
            log=LOG,
            ):
        log.Event("keepsake of " + keepsake.label + " freed")


class Witness:
    """Holds an Agent and asks about it: once before exit, and again from
    its own finalizer, which may run at interpreter exit."""

    def __init__(
            witness,
            label,
            agent,
            tag,
            word,
            ):
        witness.label = label
        witness.agent = agent
        witness.tag = tag
        witness.word = word

    def Ask(
            witness,
            *,
            log=LOG,
            Keyword=Keyword,
            Tags=Tags,
            Contract=Contract,
            ):
        agent = witness.agent
        questions = (
                ("bool", lambda: bool(agent)),
                ("keyword " + witness.word, lambda: Keyword(agent, witness.word)),
                ("in " + witness.tag.__name__, lambda: agent in witness.tag),
                ("Tags", lambda: Tags(agent)),
                ("Ok", lambda: agent.Ok),
                ("motto", lambda: agent.motto),
                ("contract", lambda: Contract.Status(agent)),
                )

        for question, ask in questions:
            try:
                answer = "= " + log.Show(ask())
            except Exception as error:
                answer = "! " + log.Failure(error)

            log.Event(witness.label + " asks " + question + " " + answer)

    def __del__(
            witness,
            ):
        witness.Ask()
'''


class Member(NamedTuple):
    """One declaration a Tag body may hold. ``kind`` says how the steps
    use it; the source takes {tag}, {k} (a small number) and {other}
    (another Tag)."""

    kind: str
    name: str
    weight: int
    source: str


AGENT_MEMBERS = (
        Member("record", "hp", 3, """
            @Record
            def hp(agent, stored):
                return (stored or 0) + {k}
            """),
        Member("record", "hp", 2, """
            @Record
            def hp(agent):
                return {k}
            """),
        Member("record", "hp", 1, """
            @Record
            @Underlay
            def hp(agent, stored):
                return (stored or 0) + agent.level
            """),
        Member("record", "gold", 2, """
            @Record
            def gold(agent):
                return {k} * 10
            """),
        Member("record", "gold", 1, """
            @Record
            def gold(agent):
                raise ValueError("{tag} has no gold")
            """),
        Member("record", "spells", 2, """
            @Record
            def spells(agent, stored):
                return (stored or ()) + ("{tag}",)
            """),
        Member("record", "rank", 2, """
            @Record
            def rank(agent, *, rank="none"):
                return rank
            """),
        Member("record", "rank", 1, """
            @Record
            def rank(agent, stored, *, rank=None):
                return (stored or "") + "/" + str(rank)
            """),
        Member("record", "rank", 1, """
            @Record
            def rank(agent, rank):
                return rank
            """),
        Member("secret record", "clearance", 2, """
            @Secret
            @Record
            def clearance(agent):
                return "{tag}-cleared"
            """),
        Member("action", "Speak", 5, """
            def Speak(agent, *words):
                return "{tag} says " + " ".join(str(word) for word in words) + " to " + agent.name
            """),
        Member("action", "Speak", 3, """
            @Action
            @Underlay
            def Speak(agent, underlay, *words):
                return "{tag}<" + str(underlay()) + ">"
            """),
        Member("action", "Speak", 2, """
            @Action
            @Underlay
            def Speak(agent, underlay, *words):
                return "{tag}<" + str(underlay("{tag}", *words)) + ">"
            """),
        Member("action", "Attack", 2, """
            def Attack(agent):
                return "{tag} attacks: " + str(agent.Speak("{tag}"))
            """),
        Member("action", "Attack", 1, """
            @Action
            @Underlay
            def Attack(agent, underlay):
                return str(underlay()) + " and {tag}"
            """),
        Member("action", "Train", 2, """
            def Train(agent):
                agent.level = agent.level + {k}
                return agent.level
            """),
        Member("action", "Status", 2, """
            def Status(agent):
                return (agent.hp, agent.level)
            """),
        Member("action", "Reveal", 1, """
            def Reveal(agent):
                return agent.clearance
            """),
        Member("secret action", "Whisper", 1, """
            @Secret
            def Whisper(agent):
                return "{tag} whispers to " + agent.name
            """),
        Member("action", "Relay", 1, """
            def Relay(agent):
                return agent.Whisper()
            """),
        Member("action", "describe", 1, """
            @Action
            @Underlay
            def describe(agent, underlay):
                return "{tag}/" + underlay()
            """),
        Member("action", "describe", 1, """
            def describe(agent):
                return "{tag} describes " + agent.name
            """),
        Member("rip", "Leave", 3, """
            @Rip
            def Leave(agent, *, log=LOG):
                log.Event("{tag}.Leave " + agent.name)
            """),
        Member("rip", "Leave", 1, """
            @Rip
            def Leave(agent, *, log=LOG):
                log.Event("{tag}.Leave " + agent.name + " ends Ok")
                Contract.Delete(agent, "Ok")
            """),
        Member("rip", "Leave", 1, """
            @Rip
            def Leave(agent):
                raise RuntimeError("{tag} will not let go")
            """),
        Member("rip", "Retire", 3, """
            @Rip
            def Retire(agent, *, log=LOG):
                log.Event("{tag}.Retire " + agent.name)
            """),
        Member("special", "__len__", 2, """
            def __len__(agent):
                return {k}
            """),
        Member("special", "__len__", 1, """
            @Action
            @Underlay
            def __len__(agent, underlay):
                return underlay() + 1
            """),
        Member("special", "__call__", 2, """
            def __call__(agent, *args):
                return ("{tag}", agent.name) + args
            """),
        Member("special", "__getitem__", 2, """
            def __getitem__(agent, key):
                if isinstance(key, int) and key > 1:
                    raise IndexError(key)   # a sequence of two: `in` and iteration end
                return "{tag}[" + str(key) + "]"
            """),
        Member("in", "__contains__", 1, """
            def __contains__(agent, item):
                return item == "{tag}"
            """),
        Member("in", "__iter__", 1, """
            def __iter__(agent):
                return iter(("{tag}", agent.name))
            """),
        Member("special", "__str__", 1, """
            def __str__(agent):
                return "{tag}:" + agent.name
            """),
        Member("special", "__bool__", 1, """
            def __bool__(agent):
                return agent.level > {k}
            """),
        Member("finalizer", "__del__", 1, """
            def __del__(agent, *, log=LOG):
                log.Event("{tag}.__del__ " + agent.name)
            """),
        Member("finalizer", "__del__", 1, """
            @Action
            @Underlay
            def __del__(agent, underlay, *, log=LOG):
                log.Event("{tag}.__del__ " + agent.name + ", then the one below")
                underlay()
            """),
        Member("delete", "__del__", 1, """
            @Delete
            def __del__(agent):
                pass
            """),
        Member("condition", "Ok", 4, """
            @Post
            def Ok(agent):
                return agent.ok
            """),
        Member("condition", "Ok", 1, """
            @Post
            def Ok(agent):
                assert agent.ok, "{tag} finds it not ok"
            """),
        Member("condition", "Ok", 2, """
            @Post
            @Underlay
            def Ok(agent, base):
                return base() and agent.level > 0
            """),
        Member("condition", "Ok", 1, """
            @Post
            def Ok(agent):
                return 1 if agent.ok else 0
            """),
        Member("condition", "Ready", 2, """
            @Pre
            def Ready(agent):
                return agent.level >= {k}
            """),
        Member("condition", "Ready", 1, """
            @Pre
            def Ready(agent, code):
                return code != "bad"
            """),
        Member("condition", "Ready", 1, """
            @Pre
            def Ready(agent):
                return agent in {other}
            """),
        Member("condition", "Alive", 2, """
            @Requirement
            def Alive(agent):
                return agent.ok
            """),
        Member("condition", "Alive", 1, """
            @Pre
            @Post
            def Alive(agent):
                return agent.level > 0
            """),
        Member("condition", "Leveled", 1, """
            @Post
            def Leveled(agent):
                return agent not in {other} or agent.level > {k}
            """),
        Member("imprint", "Enter", 2, """
            @Imprint
            def Enter(agent, *, log=LOG):
                log.Event("{tag}.Enter " + agent.name)
            """),
        Member("imprint", "Enter", 1, """
            @Imprint
            def Enter(agent, rank=None, *, log=LOG):
                log.Event("{tag}.Enter " + agent.name + " as " + str(rank))
            """),
        Member("imprint", "Enter", 1, """
            @Imprint
            def Enter(agent):
                raise RuntimeError("{tag} cannot settle in")
            """),
        Member("imprint", "Grow", 1, """
            @Imprint
            def Grow(agent):
                agent.level = agent.level + 1
            """),
        Member("delete", "Speak", 1, """
            @Delete
            def Speak(agent):
                pass
            """),
        Member("delete", "hp", 1, """
            @Delete
            def hp(agent):
                pass
            """),
        Member("delete", "describe", 1, """
            @Delete
            def describe(agent):
                pass
            """),
        Member("delete", "Ok", 1, """
            @Delete
            def Ok(agent):
                pass
            """),
        Member("delete", "__len__", 1, """
            @Delete
            def __len__(agent):
                pass
            """),
        Member("report", "motto", 2, """
            @Report
            def motto(tag):
                return tag.__name__ + " motto from {tag}"
            """),
        Member("public report", "motto", 2, """
            @Public
            @Report
            def motto(tag):
                return tag.__name__ + " motto from {tag}"
            """),
        Member("report", "die", 1, """
            @Report
            def die(tag, inherited):
                return (inherited or 0) + {k}
            """),
        Member("public report", "die", 1, """
            @Report
            @Public
            def die(tag, inherited):
                return (inherited or 0) + {k}
            """),
        Member("operation", "Hail", 2, """
            @Operation
            def Hail(tag, agent, *args):
                return tag.__name__ + " hails " + agent.name + str(args)
            """),
        Member("public operation", "Hail", 2, """
            @Public
            @Operation
            def Hail(tag, agent, *args):
                return tag.__name__ + " hails " + agent.name + str(args)
            """),
        Member("public operation", "Census", 1, """
            @Public
            @Operation
            def Census(tag, agent):
                return (len(tag[:]), len(tag))
            """),
        )


PIN_MEMBERS = (
        Member("record", "rarity", 3, """
            @Record
            def rarity(tag):
                return "{tag}-rare"
            """),
        Member("record", "era", 2, """
            @Record
            def era(tag, stored):
                return (stored or 0) + {k}
            """),
        Member("public record", "badge", 2, """
            @Public
            @Record
            def badge(tag):
                return "{tag} badge on " + tag.__name__
            """),
        Member("action", "Describe", 3, """
            @Action
            def Describe(tag):
                return tag.__name__ + " pinned by {tag}"
            """),
        Member("patch", "Hail", 2, """
            @Action
            @Underlay
            def Hail(tag, underlay, agent, *args):
                return "{tag}:" + str(underlay(agent, *args))
            """),
        Member("patch", "motto", 1, """
            @Record
            def motto(tag, stored):
                return str(stored) + " +{tag}"
            """),
        Member("rip", "Unpin", 2, """
            @Rip
            def Unpin(tag, original, *, log=LOG):
                log.Event("{tag} leaves " + tag.__name__ + ", restoring " + str(list(original)))
                if "Hail" in original:
                    tag.Hail = original.Hail
            """),
        Member("condition", "Has_Members", 1, """
            @Pre
            def Has_Members(tag):
                return len(tag[:]) > 0
            """),
        Member("condition", "Approved", 2, """
            @Post
            def Approved(tag):
                return vars(tag).get("approved", True) is not False
            """),
        Member("imprint", "Stamp", 1, """
            @Imprint
            def Stamp(tag, *, log=LOG):
                log.Event("{tag} stamps " + tag.__name__)
            """),
        Member("secret record", "seal", 1, """
            @Secret
            @Record
            def seal(tag):
                return "{tag}-seal"
            """),
        Member("action", "Seal_Of", 1, """
            @Action
            def Seal_Of(tag):
                return tag.seal
            """),
        )


WORDS = ("Kin", "Beast", "Undead", "Loner", "Wolf")
LATE_WORD = "Late"   # no Tag answers to it until a Flag marked while the program runs, on a Tag nobody carries yet, gives it
PIN_WORDS = ("Deprecated", "Homebrew", "Legacy")
HOSTS = (
        ("Host", 5),
        ("Keeper", 3),
        ("Bag", 1),
        ("Roster", 1),
        ("Ledger", 1),
        )


@dataclass
class Tag_Plan:
    """One Tag the program declares, and what steps may ask of it."""

    name: str                       # the variable
    title: str                      # its __name__: a twin shares another Tag's
    members: dict[str, str] = field(default_factory=dict)    # name -> kind


@dataclass
class Plan:
    """The program being written, and what its steps can reach."""

    randomizer: random.Random
    heavy: bool
    lines: list[str] = field(default_factory=list)
    tags: list[Tag_Plan] = field(default_factory=list)
    pins: list[Tag_Plan] = field(default_factory=list)
    words: list[str] = field(default_factory=list)
    pin_words: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)          # the Agents bound now
    witnesses: list[str] = field(default_factory=list)       # the Witnesses bound now
    offered: dict[str, list[Tag_Plan]] = field(default_factory=dict)   # the Tags each Agent was offered: a tagging may be refused
    made: int = 0                                            # a name is never reused
    shapes: dict[str, type] = field(default_factory=dict)    # a plain class per Tag, to test its MRO first


def Program(
        seed: int,
        steps: int,
        heavy: bool,
        ) -> str:
    """The program of one seed: the same text on every kit."""

    plan = Plan(
            random.Random(seed),
            heavy,
            )
    mix = ", heavy on Pins and Flags" if heavy else ""
    plan.lines.append(
            f'"""Differential fuzzing: seed {seed}, {steps} steps{mix}.'
            ' Made by tests/differential_fuzz.py."""'
            )
    plan.lines.append(PRELUDE)
    Declare_Tags(plan)
    Make_Agents(plan)

    for number in range(steps):
        Write_Step(
                plan,
                f"s{number}",
                )

    Write_Exit(plan)

    return "\n".join(plan.lines) + "\n"


# ------------------------------------------------------------------
# Declaring the Tags
# ------------------------------------------------------------------


def Declare_Tags(
        plan: Plan,
        ) -> None:
    randomizer = plan.randomizer
    plan.lines.append("\n# Tags\n")

    for index in range(randomizer.randint(6, 11)):
        Declare(
                plan,
                f"T{index}",
                pin=False,
                )

        if randomizer.random() < 0.06:
            Declare_Twin(
                    plan,
                    f"Twin{index}",
                    )

    plan.lines.append("\n# Pins\n")

    for index in range(randomizer.randint(2, 5) if plan.heavy else randomizer.randint(0, 2)):
        Declare(
                plan,
                f"P{index}",
                pin=True,
                )

    known: list[str] = []

    for word in (
            *plan.words,
            *plan.pin_words,
            *WORDS,
            *PIN_WORDS,
            LATE_WORD,
            *(tag.title for tag in plan.tags + plan.pins),
            ):
        if word not in known:
            known.append(word)

    plan.lines.append(f"KNOWN_WORDS = {known!r}   # every word a Target may answer to, asked by Look\n")


def Declare(
        plan: Plan,
        name: str,
        pin: bool,
        ) -> None:
    randomizer = plan.randomizer
    family = plan.pins if pin else plan.tags
    bases = Bases(
            plan,
            name,
            family,
            )
    flag = randomizer.random() < (0.55 if plan.heavy else 0.25)
    catalogue = PIN_MEMBERS if pin else AGENT_MEMBERS
    chosen: list[Member] = []

    for _ in range(randomizer.randint(0, 5)):
        member = randomizer.choices(
                catalogue,
                weights=[member.weight for member in catalogue],
                )[0]

        if any(member.name == taken.name for taken in chosen):
            continue

        if flag and member.kind == "in":
            continue                                   # a Flag with an `in` Action is refused at declaration

        chosen.append(member)

    tag = Tag_Plan(
            name=name,
            title=name,
            members={member.name: member.kind for member in chosen},
            )
    others = [known.name for known in plan.tags] or [name]
    decorators = []

    if flag:
        decorators.append(
                Flag_Line(
                        plan,
                        name,
                        pin,
                        )
                )

    if pin:
        decorators.append("@Pin")

    plan.lines.extend(decorators)
    plan.lines.append(f"class {name}({', '.join(bases)}):")

    for member in chosen:
        source = textwrap.dedent(member.source).strip("\n").format(
                tag=name,
                k=randomizer.randint(0, 3),
                other=randomizer.choice(others),
                )
        plan.lines.append("")
        plan.lines.append(textwrap.indent(source, "    "))

    if not chosen:
        plan.lines.append("    pass")

    plan.lines.append("\n")
    family.append(tag)


def Bases(
        plan: Plan,
        name: str,
        family: list[Tag_Plan],
        ) -> list[str]:
    """Tag, one Base, or two (a diamond when they share one), never an
    order Python refuses."""

    randomizer = plan.randomizer
    roll = randomizer.random()

    if not family or roll < 0.4:
        bases = ["Tag"]
    elif roll < 0.85 or len(family) < 2:
        bases = [randomizer.choice(family).name]
    else:
        bases = [tag.name for tag in randomizer.sample(family, 2)]

    try:
        shape = type(name, tuple(plan.shapes.get(base, object) for base in bases), {})
    except TypeError:
        bases = bases[:1]
        shape = type(name, (plan.shapes.get(bases[0], object),), {})

    plan.shapes[name] = shape

    return bases


def Declare_Twin(
        plan: Plan,
        name: str,
        ) -> None:
    """A Tag with another Tag's name: views by name see the latest."""

    randomizer = plan.randomizer
    twin = randomizer.choice(plan.tags)
    base = randomizer.choice(plan.tags)
    plan.lines.append(f'{name} = type("{twin.title}", ({base.name},), {{}})\n\n')
    plan.shapes[name] = type(name, (plan.shapes[base.name],), {})
    plan.tags.append(
            Tag_Plan(
                    name,
                    twin.title,
                    )
            )


def Flag_Line(
        plan: Plan,
        name: str,
        pin: bool,
        ) -> str:
    randomizer = plan.randomizer
    known = plan.pin_words if pin else plan.words

    if name not in known:
        known.append(name)                             # a Flag always answers to its own name

    if randomizer.random() < 0.4:
        return "@Flag"

    pool = list(PIN_WORDS if pin else WORDS)

    if not pin and plan.tags:
        pool.append(randomizer.choice(plan.tags).title)   # a word that is another Tag's name

    words = randomizer.sample(
            pool,
            randomizer.randint(1, 3),
            )

    for word in words:
        if word not in known:
            known.append(word)

    return "@Flag(" + ", ".join(f'"{word}"' for word in words) + ")"


def Make_Agents(
        plan: Plan,
        ) -> None:
    plan.lines.append("\n# Agents\n")

    for _ in range(plan.randomizer.randint(4, 7)):
        plan.lines.append(New_Agent(plan))

    plan.lines.append("\n\n# Steps\n")


def New_Agent(
        plan: Plan,
        ) -> str:
    host = plan.randomizer.choices(
            [host for host, _weight in HOSTS],
            weights=[weight for _host, weight in HOSTS],
            )[0]
    name = f"a{plan.made}"
    plan.made += 1
    plan.agents.append(name)

    return f'{name} = {host}("{name}")'


# ------------------------------------------------------------------
# Writing the steps
# ------------------------------------------------------------------


def Do_Line(
        step: str,
        expression: str,
        label: str | None = None,
        ) -> str:
    return f'Do("{step}", {(label or expression)!r}, lambda: {expression})'


def Any_Agent(
        plan: Plan,
        ) -> str:
    return plan.randomizer.choice(plan.agents)


def Any_Tag(
        plan: Plan,
        ) -> Tag_Plan:
    return plan.randomizer.choice(plan.tags)


def Names_Of(
        tags: list[Tag_Plan],
        *kinds: str,
        ) -> list[str]:
    """Every member name of these kinds, in declaration order, once."""

    names: list[str] = []

    for tag in tags:
        for name, kind in tag.members.items():
            if kind in kinds and name not in names:
                names.append(name)

    return names


def Inputs(
        plan: Plan,
        ) -> str:
    # half the taggings take no inputs: the empty string is four of eight
    return plan.randomizer.choice(
            (
                "",
                "",
                "",
                "",
                ', rank="knight"',
                ', code="bad"',
                ', code="007"',
                ', rank="page", code="007"',
                )
            )


def Arguments(
        plan: Plan,
        ) -> str:
    # half the calls take no arguments
    return plan.randomizer.choice(
            (
                "",
                "",
                "1",
                '"x", 2',
                )
            )


def Word(
        plan: Plan,
        ) -> str:
    return plan.randomizer.choice(plan.words + ["Stranger", Any_Tag(plan).title])


def Then_Look(
        plan: Plan,
        step: str,
        target: str,
        lines: list[str],
        ) -> list[str]:
    """Half the time, a step that changed a Target looks at it after."""

    if plan.randomizer.random() < 0.5:
        return lines + [Do_Line(step, f"Look({target})", f"look {target}")]

    return lines


def Offer(
        plan: Plan,
        agent: str,
        tag: Tag_Plan,
        ) -> Tag_Plan:
    """Remember that this step applies ``tag`` to ``agent``."""

    plan.offered.setdefault(agent, []).append(tag)

    return tag


def Offered_Tag(
        plan: Plan,
        agent: str,
        ) -> Tag_Plan:
    """Mostly a Tag ``agent`` was offered, so a Rip or a view has something
    to find; otherwise any Tag."""

    offered = plan.offered.get(agent, [])

    if offered and plan.randomizer.random() < 0.75:
        return plan.randomizer.choice(offered)

    return Any_Tag(plan)


def Tagging(
        plan: Plan,
        step: str,
        ) -> list[str]:
    agent = Any_Agent(plan)
    tag = Offer(
            plan,
            agent,
            Any_Tag(plan),
            )

    return Then_Look(
            plan,
            step,
            agent,
            [Do_Line(step, f"{tag.name}({agent}{Inputs(plan)})")],
            )


def Tagging_Many(
        plan: Plan,
        step: str,
        ) -> list[str] | None:
    if len(plan.agents) < 2:
        return None

    targets = plan.randomizer.sample(
            plan.agents,
            min(3, len(plan.agents)),
            )
    tag = Any_Tag(plan)

    for target in targets:
        Offer(
                plan,
                target,
                tag,
                )

    return Then_Look(
            plan,
            step,
            targets[-1],
            [Do_Line(step, f"Tag_All({tag.name}, {', '.join(targets)}{Inputs(plan)})")],
            )


def Ripping(
        plan: Plan,
        step: str,
        ) -> list[str]:
    agent = Any_Agent(plan)
    tag = Offered_Tag(plan, agent).name

    return Then_Look(
            plan,
            step,
            agent,
            [Do_Line(step, f"Rip_Of({tag}, {agent})", f"del {tag}[{agent}]")],
            )


def Scoping(
        plan: Plan,
        step: str,
        ) -> list[str]:
    """A block with Tags for its duration; sometimes it fails, and
    sometimes it Rips one of the Scope's own Tags, which the Scope then
    leaves alone."""

    randomizer = plan.randomizer
    agent = Any_Agent(plan)
    named = [Any_Tag(plan).name for _ in range(randomizer.randint(1, 3))]
    tags = ", ".join(named)
    head = f"Scope({agent}, {tags}{Inputs(plan)})"
    lines = [
            "",
            "",
            f"def Scope_{step}():",
            f"    with {head}:",
            ]

    for _ in range(randomizer.randint(1, 3)):
        own = randomizer.choice(named)
        expression, label = randomizer.choice(
                (
                    (f"Tags({agent})", None),
                    (f"bool({agent})", None),
                    (f'f"{{{agent}:contract}}"', None),
                    (Member_Read(plan, agent), None),
                    (f"{Any_Tag(plan).name}({agent})", None),
                    (f"Rip_Of({own}, {agent})", f"del {own}[{agent}]"),
                    )
                )
        lines.append("        " + Do_Line(step, expression, f"inside: {label or expression}"))

    if randomizer.random() < 0.3:
        lines.append(f'        raise LookupError("the block of {step} fails")')

    return Then_Look(
            plan,
            step,
            agent,
            lines + [
                "",
                "",
                Do_Line(step, f"Scope_{step}()", f"with {head}"),
                ],
            )


def Applying(
        plan: Plan,
        step: str,
        ) -> list[str]:
    agent = Any_Agent(plan)
    tags = ", ".join(
            Offer(plan, agent, Any_Tag(plan)).name
            for _ in range(plan.randomizer.randint(1, 3))
            )

    return Then_Look(
            plan,
            step,
            agent,
            [Do_Line(step, f"Apply({agent}, {tags}{Inputs(plan)})")],
            )


def Member_Read(
        plan: Plan,
        agent: str,
        ) -> str:
    """A member of the Agent, read or called: what any Tag gives, what
    the host has, and names no one gives."""

    reads = Names_Of(plan.tags, "record", "secret record", "condition", "public report") + Names_Of(
            plan.pins,
            "public record",
            )
    calls = Names_Of(plan.tags, "action", "secret action", "rip", "public operation") + ["describe"]
    name = plan.randomizer.choice(reads + calls + ["level", "nothing"])

    if name in calls:
        return f"{agent}.{name}({Arguments(plan)})"

    return f"{agent}.{name}"


def Reading(
        plan: Plan,
        step: str,
        ) -> list[str]:
    return [Do_Line(step, Member_Read(plan, Any_Agent(plan)))]


def Writing(
        plan: Plan,
        step: str,
        ) -> list[str]:
    """Break a promise, mend it, or write and delete a member."""

    randomizer = plan.randomizer
    agent = Any_Agent(plan)
    records = Names_Of(plan.tags, "record", "secret record") or ["hp"]
    published = Names_Of(plan.tags + plan.pins, "public report", "public record") or ["motto"]
    choice = randomizer.randrange(10)

    if choice < 5:
        value = randomizer.choice(("True", "False"))
        line = Do_Line(step, f'Set({agent}, "ok", {value})', f"{agent}.ok = {value}")
    elif choice < 7:
        value = randomizer.randint(0, 3)
        line = Do_Line(step, f'Set({agent}, "level", {value})', f"{agent}.level = {value}")
    elif choice == 7:
        name = randomizer.choice(records)
        value = randomizer.randint(0, 9)
        line = Do_Line(step, f'Set({agent}, "{name}", {value})', f"{agent}.{name} = {value}")
    elif choice == 8:
        name = randomizer.choice(records + ["describe"])
        line = Do_Line(step, f'Unset({agent}, "{name}")', f"del {agent}.{name}")
    else:
        name = randomizer.choice(published)
        line = Do_Line(step, f'Set({agent}, "{name}", "mine")', f'{agent}.{name} = "mine"')

    return Then_Look(
            plan,
            step,
            agent,
            [line],
            )


def Viewing(
        plan: Plan,
        step: str,
        ) -> list[str]:
    """A Tag's view of the Agent: by name, by class, and what it holds."""

    randomizer = plan.randomizer
    agent = Any_Agent(plan)
    tag = Offered_Tag(plan, agent)
    view = randomizer.choice((f"{agent}.{tag.title}", f"{tag.name}[{agent}]"))

    if randomizer.random() < 0.1:
        return [Do_Line(step, f'Set({view}, "hp", 1)', f"{view}.hp = 1")]

    reads = Names_Of([tag], "record", "report", "public report", "secret record") or ["hp"]
    calls = Names_Of([tag], "action", "operation", "public operation") or ["Speak"]
    expression = randomizer.choice(
            (
                view,
                f"{view}.{randomizer.choice(reads)}",
                f"{view}.{randomizer.choice(calls)}({Arguments(plan)})",
                f"repr({view})",
                )
            )

    return [Do_Line(step, expression)]


def Querying(
        plan: Plan,
        step: str,
        ) -> list[str]:
    agent = Any_Agent(plan)
    tag = Any_Tag(plan).name
    expression = plan.randomizer.choice(
            (
                f"Tags({agent})",
                f"Outline({agent})",
                f'f"{{{agent}:tags}}"',
                f'f"{{{agent}:outline}}"',
                f'f"{{{agent}:contract}}"',
                f'format({agent}, "bogus")',
                f"Form({tag})",
                f'f"{{{tag}:form}}"',
                f"Contract.Status({agent})",
                f"Contract.Holds({agent})",
                f"Contract.Postconditions({agent})",
                f"Contract.Preconditions({agent})",
                f"Contract.Conditions({agent})",
                f"Contract.Display({agent})",
                f"bool({agent})",
                f"isinstance({agent}, {tag})",
                f"type({agent}).__mro__",
                )
            )

    return [Do_Line(step, expression)]


def Keywording(
        plan: Plan,
        step: str,
        ) -> list[str]:
    agent = Any_Agent(plan)
    tag = Any_Tag(plan).name
    word = Word(plan)
    expression = plan.randomizer.choice(
            (
                f'Keyword({agent}, "{word}")',
                f'Keyword({agent}, "{word}", "{Word(plan)}")',
                f"Keyword({agent}, {tag})",
                f'"{word}" in {agent}',
                f"{tag} in {agent}",
                f"{agent} in {tag}",
                f'"{word}" in {tag}',
                )
            )

    return [Do_Line(step, expression)]


def Fielding(
        plan: Plan,
        step: str,
        ) -> list[str]:
    """Populations: sound, defective, whole, and their algebra."""

    agent = Any_Agent(plan)
    tag = Any_Tag(plan).name
    other = Any_Tag(plan).name
    expression = plan.randomizer.choice(
            (
                f"list({tag})",
                f"list(~{tag})",
                f"list({tag}[:])",
                f"len({tag})",
                f"bool({tag})",
                f"bool(~{tag})",
                f"len(~{tag})",
                f"list({tag} | {other})",
                f"list({tag} & {other})",
                f"list({tag} - {other})",
                f"list(~{tag} | {other})",
                f"list({tag}[:] | {other}[:])",
                f"list({tag}[:] & ~{other})",
                f"{agent} in ~{tag}",
                f"{agent} in {tag}[:]",
                f"{tag}[1:2]",
                f"{tag} | None",
                )
            )

    return [Do_Line(step, expression)]


def Specials(
        plan: Plan,
        step: str,
        ) -> list[str]:
    agent = Any_Agent(plan)
    expression = plan.randomizer.choice(
            (
                f"len({agent})",
                f"{agent}()",
                f"{agent}(1, 2)",
                f'{agent}["key"]',
                f"{agent}[0]",
                f"list({agent})",
                f"str({agent})",
                f"bool({agent})",
                )
            )

    return [Do_Line(step, expression)]


def Tag_Level(
        plan: Plan,
        step: str,
        ) -> list[str]:
    """What lives on the Tag itself: Reports, Operations, its name."""

    tag = Any_Tag(plan)
    reads = Names_Of([tag], "report", "public report") or ["motto"]
    calls = Names_Of([tag], "operation", "public operation") or ["Hail"]
    expression = plan.randomizer.choice(
            (
                f"{tag.name}.{plan.randomizer.choice(reads)}",
                f"{tag.name}.{plan.randomizer.choice(calls)}({Any_Agent(plan)})",
                f"{tag.name}.__name__",
                )
            )

    return [Do_Line(step, expression)]


def Pinning(
        plan: Plan,
        step: str,
        ) -> list[str] | None:
    """Pins: applied to Tags, left, asked from both sides."""

    if not plan.pins:
        return None

    randomizer = plan.randomizer
    pin = randomizer.choice(plan.pins)
    tag = Any_Tag(plan).name
    agent = Any_Agent(plan)
    tag_reads = Names_Of(plan.pins, "record", "patch", "secret record") or ["rarity"]
    tag_calls = Names_Of(plan.pins, "action", "rip") or ["Describe"]
    word = randomizer.choice(plan.pin_words + ["Stranger", pin.title])
    choice = randomizer.randrange(12)

    if choice < 3:
        return Then_Look(
                plan,
                step,
                tag,
                [Do_Line(step, f"{pin.name}({tag})")],
                )

    if choice == 3:
        return Then_Look(
                plan,
                step,
                tag,
                [Do_Line(step, f"Rip_Of({pin.name}, {tag})", f"del {pin.name}[{tag}]")],
                )

    if choice == 4:
        value = randomizer.choice(("True", "False"))

        return Then_Look(
                plan,
                step,
                tag,
                [Do_Line(step, f'Set({tag}, "approved", {value})', f"{tag}.approved = {value}")],
                )

    expression = randomizer.choice(
            (
                f"{tag} in {pin.name}",
                f"list({pin.name})",
                f"list(~{pin.name})",
                f"list({pin.name}[:])",
                f"{pin.name}[{tag}].{randomizer.choice(tag_reads)}",
                f"{tag}.{randomizer.choice(tag_reads)}",
                f"{tag}.{randomizer.choice(tag_calls)}()",
                f"{tag}.Hail({agent})",
                f"{agent}.badge",
                f'f"{{{tag}:pins}}"',
                f'f"{{{tag}:contract}}"',
                f"Tags({tag})",
                f"Outline({tag})",
                f'"{word}" in {tag}',
                f'Keyword({tag}, "{word}")',
                f"Keyword({tag}, {pin.name})",
                f"Contract.Status({tag})",
                f"isinstance({tag}, {pin.name})",
                f"bool({tag})",
                f"{pin.name}({pin.name})",
                f"{pin.name}({agent})",
                )
            )

    return [Do_Line(step, expression)]


def Flagging(
        plan: Plan,
        step: str,
        ) -> list[str]:
    """A Flag marked while the program runs. On a Tag nobody carries, and
    none of its Shapes, the mark takes, and the Agents tagged after it
    answer its words. On a Tag that has members it is refused, and
    nothing is marked."""

    randomizer = plan.randomizer
    tag = Any_Tag(plan)
    word = randomizer.choice(WORDS + (LATE_WORD,))
    given = [agent for agent in plan.agents if tag in plan.offered.get(agent, [])]

    for known in (word, tag.title):
        if known not in plan.words:
            plan.words.append(known)

    return Then_Look(
            plan,
            step,
            randomizer.choice(given or plan.agents),
            [Do_Line(step, f"Late_Flag({tag.name}, {randomizer.choice((f'Flag({word!r})', 'Flag'))})")],
            )


def Renaming(
        plan: Plan,
        step: str,
        ) -> list[str]:
    """A Tag renamed: views and words by name follow the new name."""

    tag = Any_Tag(plan)
    tag.title = f"{tag.name}_{step}"

    return [
            Do_Line(step, f'Set({tag.name}, "__name__", "{tag.title}")', f'{tag.name}.__name__ = "{tag.title}"'),
            f'KNOWN_WORDS.append("{tag.title}")',
            ]


def Passing(
        plan: Plan,
        step: str,
        ) -> list[str]:
    """A Tag declared in a function, applied to an Agent that dies with
    the call. What the Tag holds lives as long as the Tag."""

    return [
            "",
            "",
            f"def Pass_{step}():",
            f'    keepsake = Keepsake("{step}")',
            "",
            f"    class Passing_{step}(Tag):",
            "",
            "        @Record",
            "        def token(agent):",
            "            return keepsake.label",
            "",
            f'    carrier = Host("carrier of {step}")',
            f"    Passing_{step}(carrier)",
            "",
            "    return carrier.token",
            "",
            "",
            Do_Line(step, f"Pass_{step}()", f"a Tag of {step}, declared in a function"),
            ]


def Ending_A_Promise(
        plan: Plan,
        step: str,
        ) -> list[str]:
    agent = Any_Agent(plan)
    name = plan.randomizer.choice(Names_Of(plan.tags, "condition") + ["Nothing"])

    return Then_Look(
            plan,
            step,
            agent,
            [Do_Line(step, f'Contract.Delete({agent}, "{name}")')],
            )


def Making(
        plan: Plan,
        step: str,
        ) -> list[str]:
    line = New_Agent(plan)
    said = f"{step} {line}"

    return [
            line,
            f"LOG.Say({said!r})",
            ]


def Dropping(
        plan: Plan,
        step: str,
        ) -> list[str] | None:
    """`del` an Agent or a Witness: a finalizer may run right here."""

    randomizer = plan.randomizer

    if plan.witnesses and randomizer.random() < 0.3:
        name = randomizer.choice(plan.witnesses)
        plan.witnesses.remove(name)
    elif len(plan.agents) > 3:
        name = randomizer.choice(plan.agents)
        plan.agents.remove(name)
    else:
        return None

    return [
            f'LOG.Say("{step} del {name}")',
            f"del {name}",
            f'LOG.Flush("{step}")',
            ]


def Cycling(
        plan: Plan,
        step: str,
        ) -> list[str]:
    """A cycle: nothing but a collection frees it."""

    first = Any_Agent(plan)
    second = Any_Agent(plan)

    return [
            Do_Line(step, f'Set({first}, "friend", {second})', f"{first}.friend = {second}"),
            Do_Line(step, f'Set({second}, "friend", {first})', f"{second}.friend = {first}"),
            ]


def Collecting(
        plan: Plan,
        step: str,
        ) -> list[str]:
    return [
            f'LOG.Say("{step} gc.collect()")',
            "gc.collect()",
            f'LOG.Flush("{step}", collected=True)',
            ]


def Registering(
        plan: Plan,
        step: str,
        ) -> list[str]:
    return [Do_Line(step, f"At_Exit({Any_Agent(plan)})")]


def Witnessing(
        plan: Plan,
        step: str,
        ) -> list[str]:
    name = f"w{plan.made}"
    plan.made += 1
    plan.witnesses.append(name)
    agent = Any_Agent(plan)

    return [
            f'{name} = Witness("{name}", {agent}, {Any_Tag(plan).name}, "{Word(plan)}")',
            f'LOG.Say("{step} {name} watches {agent}")',
            ]


def Misusing(
        plan: Plan,
        step: str,
        ) -> list[str]:
    agent = Any_Agent(plan)
    tag = Any_Tag(plan).name
    expression = plan.randomizer.choice(
            (
                f"copy.copy({agent})",
                f"copy.deepcopy({agent})",
                f"{tag}()",
                f"{tag}({Any_Tag(plan).name})",
                f'format({tag}, "bogus")',
                )
            )

    return [Do_Line(step, expression)]


Step = Callable[[Plan, str], list[str] | None]

STEPS: tuple[tuple[int, int, Step], ...] = (   # weight in the ordinary mix, in the heavy mix
        (16, 12, Tagging),
        (2, 2, Tagging_Many),
        (6, 5, Ripping),
        (4, 3, Scoping),
        (3, 3, Applying),
        (14, 10, Reading),
        (8, 6, Writing),
        (5, 4, Viewing),
        (6, 5, Querying),
        (6, 10, Keywording),
        (6, 5, Fielding),
        (3, 2, Specials),
        (3, 2, Tag_Level),
        (3, 14, Pinning),
        (1, 1, Ending_A_Promise),
        (2, 2, Making),
        (4, 4, Dropping),
        (1, 1, Cycling),
        (1, 1, Collecting),
        (2, 2, Registering),
        (1, 1, Witnessing),
        (1, 1, Misusing),
        (1, 3, Flagging),
        (1, 1, Renaming),
        (1, 1, Passing),
        )


def Write_Step(
        plan: Plan,
        step: str,
        ) -> None:
    randomizer = plan.randomizer
    weights = [heavy if plan.heavy else ordinary for ordinary, heavy, _write in STEPS]

    while True:
        write = randomizer.choices(
                [write for _ordinary, _heavy, write in STEPS],
                weights=weights,
                )[0]
        lines = write(plan, step)

        if lines is not None:
            plan.lines.extend(lines)
            return


def Write_Exit(
        plan: Plan,
        ) -> None:
    """Leave some cycles and Witnesses to the interpreter's exit. Half the
    Witnesses ask once before it, so an answer at exit can be checked."""

    randomizer = plan.randomizer

    if randomizer.random() < 0.5:
        plan.lines.extend(Collecting(plan, "end"))

    for _ in range(randomizer.randint(0, 2)):
        plan.lines.extend(Witnessing(plan, "end"))

    for witness in plan.witnesses:
        # an answer to compare with the one at exit; the others ask first at exit
        if randomizer.random() < 0.5:
            plan.lines.append(Do_Line("end", f"{witness}.Ask()", f"{witness} asks before exit"))

    plan.lines.append('LOG.Say("=== exit ===")')
    plan.lines.append("LOG.exiting = True")


# ------------------------------------------------------------------
# Running a program on a kit
# ------------------------------------------------------------------


ADDRESS = re.compile(r"0x[0-9a-fA-F]+")
KIT_PATH = re.compile(r"[^\s\"'(]*/TopKit/(\w+\.py)")
KIT_LINE = re.compile(r"(TopKit/\w+\.py):\d+")
KIT_FRAME = re.compile(r'^(\s*)File "TopKit/\w+\.py", line \d+, in ')


def Kit(
        ref: str,
        directory: pathlib.Path,
        ) -> pathlib.Path:
    """The kit at ``ref`` (``.`` is the working tree) as a directory
    holding TopKit/, made without writing to the repository."""

    directory.mkdir(parents=True)

    if ref == WORKING_TREE:
        shutil.copytree(
                REPOSITORY / "TopKit",
                directory / "TopKit",
                ignore=shutil.ignore_patterns("__pycache__"),
                )
    else:
        archive = subprocess.run(
                ["git", "-C", str(REPOSITORY), "archive", ref, "TopKit"],
                capture_output=True,
                )

        if archive.returncode != 0:
            raise SystemExit(f"git archive {ref} failed: {archive.stderr.decode().strip()}")

        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as bundle:
            bundle.extractall(
                    directory,
                    filter="data",
                    )

    # A broken kit fails here, once; a sound one is compiled once.
    subprocess.run(
            [sys.executable, "-c", "import TopKit"],
            cwd=directory,
            env=Environment(directory),
            check=True,
            )

    return directory


def Environment(
        kit: pathlib.Path,
        ) -> dict[str, str]:
    return {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(kit),
            "PYTHONHASHSEED": "0",
            "PYTHONUNBUFFERED": "1",        # standard output and error reach the pipe in the order written
            "PYTHONIOENCODING": "utf-8",
            }


def Transcript(
        kit: pathlib.Path,
        program: pathlib.Path,
        timeout: float,
        ) -> list[str]:
    """What the program observed on this kit: its output and its errors,
    in order, normalized, then its exit status."""

    try:
        result = subprocess.run(
                [sys.executable, str(program)],
                cwd=kit,
                env=Environment(kit),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                )
    except subprocess.TimeoutExpired:
        return [f"timeout after {timeout:g} s"]

    return Normalized(
            result.stdout.decode("utf-8", errors="replace"),
            program,
            ) + [f"exit status {result.returncode}"]


def Normalized(
        text: str,
        program: pathlib.Path,
        ) -> list[str]:
    """Addresses and the kit's own paths and lines, which differ between
    versions legitimately, made equal; the kit's frames in a traceback
    folded into one line, since a refactoring moves them. The program's
    lines are kept, and the standard library's (one interpreter runs
    both kits)."""

    text = text.replace(str(program), "program.py").replace(STANDARD_LIBRARY, "<stdlib>")
    text = KIT_PATH.sub(r"TopKit/\1", text)
    lines: list[str] = []
    folding: int | None = None                         # the indent of the kit frame being folded

    for line in text.splitlines():
        line = ADDRESS.sub("0x?", KIT_LINE.sub(r"\1:N", line))
        frame = KIT_FRAME.match(line)

        if frame is not None:
            folded = frame.group(1) + "File TopKit (the kit's frames)"

            if not lines or lines[-1] != folded:
                lines.append(folded)

            folding = len(frame.group(1))
            continue

        indent = len(line) - len(line.lstrip())

        if folding is not None and indent > folding and not line.lstrip().startswith("File "):
            continue                                   # the kit's source line and its carets

        folding = None
        lines.append(line)

    return lines


class Outcome(NamedTuple):
    seed: int
    base: list[str]
    new: list[str]


def Run_Seed(
        seed: int,
        steps: int,
        heavy: bool,
        base: pathlib.Path,
        new: pathlib.Path,
        work: pathlib.Path,
        timeout: float,
        ) -> Outcome:
    program = work / f"seed_{seed:05d}.py"
    program.write_text(
            Program(
                    seed,
                    steps,
                    heavy,
                    ),
            encoding="utf-8",
            )

    return Outcome(
            seed,
            Transcript(base, program, timeout),
            Transcript(new, program, timeout),
            )


def Unfinished(
        transcript: list[str],
        ) -> bool:
    """A program that timed out or did not exit cleanly proves nothing."""

    return transcript[-1] != "exit status 0"


# ------------------------------------------------------------------
# Comparing
# ------------------------------------------------------------------


def Name_Of(
        ref: str,
        ) -> str:
    if ref == WORKING_TREE:
        return "the working tree"

    commit = subprocess.run(
            ["git", "-C", str(REPOSITORY), "rev-parse", "--short", f"{ref}^{{commit}}"],
            capture_output=True,
            text=True,
            )

    return f"{ref} ({commit.stdout.strip() or 'unknown'})"


def Keep(
        work: pathlib.Path,
        outcome: Outcome,
        ) -> None:
    """Both transcripts beside the program, to diff or replay later."""

    for side, transcript in (
            ("base", outcome.base),
            ("new", outcome.new),
            ):
        (work / f"seed_{outcome.seed:05d}.{side}.txt").write_text(
                "\n".join(transcript) + "\n",
                encoding="utf-8",
                )


def Print_Difference(
        outcome: Outcome,
        base: str,
        new: str,
        ) -> None:
    diff = list(
            difflib.unified_diff(
                    outcome.base,
                    outcome.new,
                    f"base {base}",
                    f"new {new}",
                    n=1,
                    lineterm="",
                    )
            )
    print(f"\nseed {outcome.seed} differs ({len(outcome.base)} / {len(outcome.new)} lines)")
    print("\n".join(diff[:DIFF_LINES_SHOWN]))

    if len(diff) > DIFF_LINES_SHOWN:
        print(f"... {len(diff) - DIFF_LINES_SHOWN} more diff lines")


def Main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--base", default="HEAD", help="a git ref, or . for the working tree (default: HEAD)")
    parser.add_argument("--new", default=WORKING_TREE, help="a git ref, or . for the working tree (the default)")
    parser.add_argument("--start", type=int, default=0, help="the first seed")
    parser.add_argument("--seeds", type=int, default=20, help="how many seeds")
    parser.add_argument("--steps", type=int, default=300, help="steps per program")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 1, help="programs run at once")
    parser.add_argument("--keep", type=pathlib.Path, help="keep every program and both transcripts here")
    parser.add_argument("--heavy", action="store_true", help="more Pins and Flags, and more steps through them")
    parser.add_argument("--timeout", type=float, default=60.0, help="seconds per program on one kit")
    arguments = parser.parse_args()
    started = time.perf_counter()
    seeds = range(arguments.start, arguments.start + arguments.seeds)
    base_name = Name_Of(arguments.base)
    new_name = Name_Of(arguments.new)
    differing: list[int] = []
    unfinished: list[int] = []
    lines = 0

    print(f"base: {base_name}")
    print(f"new:  {new_name}")

    with tempfile.TemporaryDirectory(prefix="topkit-fuzz-") as scratch:
        root = pathlib.Path(scratch).resolve()
        base = Kit(arguments.base, root / "base")
        new = Kit(arguments.new, root / "new")
        work = (arguments.keep or root / "programs").resolve()
        work.mkdir(parents=True, exist_ok=True)

        def Run(
                seed: int,
                ) -> Outcome:
            return Run_Seed(
                    seed,
                    arguments.steps,
                    arguments.heavy,
                    base,
                    new,
                    work,
                    arguments.timeout,
                    )

        with ThreadPoolExecutor(max(1, arguments.jobs)) as pool:
            for outcome in pool.map(Run, seeds):
                lines += len(outcome.base) + len(outcome.new)

                if arguments.keep:
                    Keep(
                            work,
                            outcome,
                            )

                if Unfinished(outcome.base) or Unfinished(outcome.new):
                    unfinished.append(outcome.seed)
                    print(
                            f"seed {outcome.seed} did not finish:"
                            f" base {outcome.base[-1]!r}, new {outcome.new[-1]!r}"
                            )

                if outcome.base != outcome.new:
                    differing.append(outcome.seed)
                    Print_Difference(
                            outcome,
                            base_name,
                            new_name,
                            )

    seconds = time.perf_counter() - started
    mix = ", heavy" if arguments.heavy else ""
    print()
    print(
            f"seeds {seeds.start}..{seeds.stop - 1} ({len(seeds)} x {arguments.steps} steps{mix}):"
            f" {len(differing)} differing, {len(unfinished)} unfinished,"
            f" {lines:,} transcript lines (both kits), {seconds:.1f} s"
            )

    if differing:
        print("differing seeds:", " ".join(str(seed) for seed in differing))

    sys.exit(1 if differing or unfinished else 0)


if __name__ == "__main__":
    Main()
