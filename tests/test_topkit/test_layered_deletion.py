"""Conformance tests: layered deletion."""

from __future__ import annotations

import gc
import unittest
from TopKit import Delete
from TopKit import Operation
from TopKit import Pre
from TopKit import Public
from TopKit import Record
from TopKit import Rip
from TopKit import Secret
from TopKit import Tag
from TopKit import TagDeclarationError
from TopKit import TagOverwriteWarning
from TopKit import TagPreconditionError
from TopKit import Underlay

from ._fixtures import Run_Program


class LayeredDeletionTests(unittest.TestCase):
    """STEP-SPEC-18: deletion in layers. The Agent leaves its Tags first
    (every teardown runs), then its own __del__ runs as the Overlay shows
    it: the host's own is the first Layer, a Tag's __del__ replaces the
    Layers beneath or, with @Underlay, extends them."""

    def setUp(self) -> None:
        self.log: list[str] = []
        log = self.log

        class Door:
            def __del__(self) -> None:
                log.append("host")

        class Guard(Tag):
            @Rip
            def Leave(agent) -> None:
                log.append("teardown")

        self.Door, self.Guard = Door, Guard

    def delete(self, *tags: type, host: type | None = None) -> list[str]:
        door = (host or self.Door)()

        for tag in tags:
            tag(door)

        del door
        gc.collect()

        return self.log

    def reported(self, act) -> list[str]:
        """What Python reports as unraisable (a finalizer's error) while
        ``act`` runs."""

        import sys

        caught: list[str] = []
        hook = sys.unraisablehook
        sys.unraisablehook = lambda raised: caught.append(type(raised.exc_value).__name__)

        try:
            act()
        finally:
            sys.unraisablehook = hook

        return caught

    def test_with_nothing_stated_the_host_finalizer_is_the_layer(self) -> None:
        self.assertEqual(self.delete(self.Guard), ["teardown", "host"])

    def test_a_tag_may_replace_the_layers_beneath(self) -> None:
        log = self.log

        class Sealed(Tag):
            def __del__(agent) -> None:
                log.append("sealed")

        self.assertEqual(self.delete(self.Guard, Sealed), ["teardown", "sealed"])

    def test_a_tag_may_extend_the_layers_beneath(self) -> None:
        log = self.log

        class Warded(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("warded")
                underlay()

        class Blessed(Warded):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("blessed")
                underlay()

        self.assertEqual(
                self.delete(self.Guard, Blessed),
                ["teardown", "blessed", "warded", "host"],
                )

    def test_a_deleted_finalizer_leaves_only_the_teardowns(self) -> None:
        class Silent(Tag):
            @Delete
            def __del__(agent): ...

        self.assertEqual(self.delete(self.Guard, Silent), ["teardown"])

    def test_the_layer_beneath_is_callable_even_where_the_host_has_none(self) -> None:
        log = self.log

        class Bare:
            pass

        class Warded(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("warded")
                underlay()                 # nothing beneath: does nothing
                log.append("after")

        reported = self.reported(lambda: self.delete(self.Guard, Warded, host=Bare))

        self.assertEqual(self.log, ["teardown", "warded", "after"])
        self.assertEqual(reported, [])

    def test_after_a_delete_the_layer_beneath_is_nothing(self) -> None:
        log = self.log

        class Silent(Tag):
            @Delete
            def __del__(agent): ...

        class Warded(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("warded")
                underlay()                 # the host's own was deleted: nothing
                log.append("after")

        self.assertEqual(
                self.delete(self.Guard, Silent, Warded),
                ["teardown", "warded", "after"],
                )

    def test_a_hosts_error_is_reported_like_any_finalizers(self) -> None:
        log = self.log

        class Cracked:
            def __del__(self) -> None:
                log.append("host")
                raise ValueError("cracked")

        reported = self.reported(lambda: self.delete(self.Guard, host=Cracked))

        self.assertEqual(log, ["teardown", "host"])
        self.assertEqual(reported, ["ValueError"])

    def test_replacing_an_independent_tags_layer_is_diagnosed(self) -> None:
        class Sealed(Tag):
            def __del__(agent) -> None:
                pass

        class Resealed(Tag):
            def __del__(agent) -> None:
                pass

        door = self.Door()
        Sealed(door)

        with self.assertWarns(TagOverwriteWarning):
            Resealed(door)

    def test_an_object_built_from_an_agents_type_is_a_plain_host(self) -> None:
        import dataclasses

        log = self.log

        @dataclasses.dataclass(eq=False)
        class Lantern:
            name: str

            def __del__(self) -> None:
                log.append(f"{self.name} host")

        class Enchanted(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append(f"{agent.name} layer")
                underlay()

        first = Lantern("first")
        self.Guard(first)
        second = dataclasses.replace(first, name="second")   # an instance of first's runtime type
        log.clear()

        def Delete_Second() -> None:
            nonlocal second
            self.Guard(second)
            Enchanted(second)
            del second
            gc.collect()

        reported = self.reported(Delete_Second)

        self.assertEqual(log, ["teardown", "second layer", "second host"])
        self.assertEqual(reported, [])

    def test_layers_and_teardowns_read_their_own_secrets(self) -> None:
        log = self.log

        class Vault(Tag):
            @Secret
            @Record
            def combination(agent) -> str:
                return "1234"

            @Rip
            def Lock(agent) -> None:
                log.append("teardown " + agent.combination)

            def __del__(agent) -> None:
                log.append("layer " + agent.combination)

        self.assertEqual(self.delete(Vault), ["teardown 1234", "layer 1234"])

    def test_an_interrupted_teardown_still_lets_the_layers_run(self) -> None:
        log = self.log

        class Impatient(Tag):
            @Rip
            def Leave(agent) -> None:
                log.append("impatient")
                raise KeyboardInterrupt

        reported = self.reported(lambda: self.delete(Impatient))

        self.assertEqual(log, ["impatient", "host"])
        self.assertEqual(reported, ["KeyboardInterrupt"])

    def test_the_hosts_finalizer_is_found_as_python_finds_it(self) -> None:
        import functools

        log = self.log

        def Closing(self, how: str) -> None:
            log.append(how)

        class Described:
            __del__ = functools.partialmethod(Closing, "described")   # a descriptor

        class Base:
            def __del__(self) -> None:
                log.append("base")

        class Muted(Base):
            __del__ = None                 # Python: this class has no finalizer

        class Later:
            pass

        self.assertEqual(self.delete(self.Guard, host=Described), ["teardown", "described"])
        log.clear()
        self.assertEqual(self.delete(self.Guard, host=Muted), ["teardown"])
        log.clear()

        early = Later()
        self.Guard(early)
        Later.__del__ = lambda self: log.append("added later")
        del early
        gc.collect()

        self.assertEqual(log, ["teardown", "added later"])

    def test_an_untagged_object_built_from_an_agents_type_keeps_its_finalizer(self) -> None:
        log = self.log

        class Lamp:
            def __init__(self, name: str) -> None:
                self.name = name

            def __del__(self) -> None:
                log.append(f"{self.name} host")

            def Twin(self) -> "Lamp":
                return type(self)(self.name + " twin")   # an instance of the runtime type

        first = Lamp("first")
        self.Guard(first)
        twin = first.Twin()
        del twin
        gc.collect()

        self.assertEqual(log, ["first twin host"])   # never tagged: a plain host

    def test_the_hosts_finalizer_is_found_past_every_runtime_type(self) -> None:
        log = self.log

        class Warded(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("warded")
                underlay()

        first = self.Door()
        self.Guard(first)

        class Built_On(type(first)):   # a class built on an Agent's runtime type
            pass

        def Delete_Built() -> None:
            built = Built_On()
            Warded(built)
            del built
            gc.collect()

        log.clear()
        reported = self.reported(Delete_Built)

        self.assertEqual(log, ["warded", "host"])   # once, and down to the host's own
        self.assertEqual(reported, [])

    def test_a_pinned_shape_with_a_flag_pin_ends_quietly(self) -> None:
        program = """
from TopKit import Tag, Pin, Flag, Record

class Rare(Pin):
    @Record
    def rarity(tag): return "rare"

@Flag
class Deprecated(Pin): pass

class Wizard(Tag): pass

Rare(Wizard)

class Archmage(Wizard): pass     # its metaclass is Wizard's runtime type

Deprecated(Archmage)
print("end", "Deprecated" in Archmage)
"""
        lines, stderr = Run_Program(program)

        self.assertEqual(lines, ["end True"])
        self.assertEqual(stderr, "")                   # no finalizer recursed at exit

    def test_an_interruption_is_reported_even_when_a_layer_raises(self) -> None:
        import sys

        caught: list[BaseException] = []

        class Impatient(Tag):
            @Rip
            def Leave(agent) -> None:
                raise KeyboardInterrupt

        class Cracked(Tag):
            def __del__(agent) -> None:
                raise ValueError("cracked")

        hook = sys.unraisablehook
        sys.unraisablehook = lambda raised: caught.append(raised.exc_value)

        try:
            self.delete(Impatient, Cracked)
        finally:
            sys.unraisablehook = hook

        self.assertEqual([type(error) for error in caught], [KeyboardInterrupt])
        self.assertIsInstance(caught[0].__context__, ValueError)   # the Layer's error, kept

    def test_a_proxy_host_is_finalized_as_python_finalizes_it(self) -> None:
        log = self.log

        class Target:
            def __del__(self) -> None:
                log.append("the wrapped class's __del__")

        class Proxy:
            def __init__(self, wrapped: object) -> None:
                self._wrapped = wrapped

            def __getattribute__(self, name: str):
                if name in ("__class__", "__dict__"):
                    return getattr(object.__getattribute__(self, "_wrapped"), name)

                return object.__getattribute__(self, name)

            def __del__(self) -> None:
                log.append("proxy host")

        keep = Target()
        proxy = Proxy(keep)
        self.Guard(proxy)
        del proxy
        gc.collect()

        self.assertEqual(log, ["teardown", "proxy host"])

    def test_a_published_operation_named_del_is_a_layer_too(self) -> None:
        log = self.log

        class Closing(Tag):
            @Public
            @Operation
            def __del__(tag, agent) -> None:
                log.append("published layer")

        door = self.Door()
        self.Guard(door)
        Closing(door)

        self.assertIs(door.__del__.__func__, type(door).__del__)
        self.assertNotIn("__del__", vars(door))

        del door
        gc.collect()

        self.assertEqual(log, ["teardown", "published layer"])

    def test_a_refused_tagging_inside_a_teardown_closes_the_door(self) -> None:
        class Gate(Tag):
            @Pre
            def Never(agent) -> bool:
                return False

        class Vault(Tag):
            @Secret
            @Record
            def code(agent) -> str:
                return "1234"

            @Rip
            def Lock(agent) -> None:
                try:
                    Gate(agent)            # refused: the tagging rolls back
                except TagPreconditionError:
                    pass

        door = self.Door()
        Vault(door)
        del Vault[door]

        with self.assertRaises(AttributeError):
            door.code                      # the door closed again: the secret stays hidden

    def test_the_door_closes_after_a_finalizer_is_called_by_hand(self) -> None:
        class Vault(Tag):
            @Secret
            @Record
            def code(agent) -> str:
                return "1234"

            def __del__(agent) -> None:
                raise ValueError("cracked")

        def By_Hand() -> None:
            door = self.Door()
            Vault(door)

            with self.assertRaises(ValueError):
                door.__del__()

            with self.assertRaises(AttributeError):
                door.code

        self.reported(By_Hand)             # the real deletion reports the Layer's error again

    def test_the_hosts_finalizer_under_a_layer_is_found_as_python_finds_it(self) -> None:
        import functools

        log = self.log

        class Warded(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                log.append("warded")
                underlay()

        def Closing(self, how: str) -> None:
            log.append(how)

        class Described:
            __del__ = functools.partialmethod(Closing, "described")

        class Base:
            def __del__(self) -> None:
                log.append("base")

        class Muted(Base):
            __del__ = None

        class Callable_Finalizer:
            def __call__(self) -> None:
                log.append("called")

        class Plain_Call:
            __del__ = Callable_Finalizer()   # not a descriptor: called as it is

        class Later:
            pass

        for host, expected in (
                (Described, ["warded", "described"]),
                (Muted, ["warded"]),
                (Plain_Call, ["warded", "called"]),
                ):
            log.clear()
            reported = self.reported(lambda: self.delete(Warded, host=host))

            self.assertEqual(log, expected, host.__name__)
            self.assertEqual(reported, [], host.__name__)

        log.clear()
        early = Later()
        Warded(early)
        Later.__del__ = lambda self: log.append("added later")
        del early
        gc.collect()

        self.assertEqual(log, ["warded", "added later"])

    def test_a_descriptor_finalizer_is_bound_with_the_objects_type(self) -> None:
        log = self.log

        class Recording:
            def __get__(self, agent, owner):
                log.append(f"owner is the object's type: {owner is type(agent)}")
                return lambda: log.append("bound")

        class Owned:
            __del__ = Recording()

        self.assertEqual(
                self.delete(self.Guard, host=Owned),
                ["teardown", "owner is the object's type: True", "bound"],
                )

    def test_a_secret_layer_named_del_keeps_the_finalizer(self) -> None:
        log = self.log

        class Hushed(Tag):
            @Secret
            def __del__(agent) -> None:
                log.append("hushed")

        door = self.Door()
        self.Guard(door)
        Hushed(door)

        self.assertIs(door.__del__.__func__, type(door).__del__)

        del door
        gc.collect()

        self.assertEqual(log, ["teardown", "hushed"])

    def test_a_copy_built_from_a_gated_agent_is_a_plain_host(self) -> None:
        class Lamp:
            def Light(self) -> str:
                return "lit"

            def Twin(self) -> "Lamp":
                return type(self)()

        class Dark(Tag):
            @Delete
            def Light(agent): ...

        dark = Lamp()
        Dark(dark)
        twin = dark.Twin()                 # wears Dark's runtime type and its gate
        self.Guard(twin)
        plain = Lamp()
        self.Guard(plain)

        self.assertEqual(twin.Light(), "lit")
        self.assertIs(type(twin), type(plain))

    def test_a_muted_hosts_finalizer_reports_nothing(self) -> None:
        class Base:
            def __del__(self) -> None:
                pass

        class Muted(Base):
            __del__ = None

        self.assertEqual(self.reported(lambda: self.delete(self.Guard, host=Muted)), [])

    def test_a_restored_finalizer_shares_the_runtime_type(self) -> None:
        class Sealed(Tag):
            def __del__(agent) -> None:
                pass

        class Silent(Tag):
            @Delete
            def __del__(agent): ...

        first, second = self.Door(), self.Door()
        Sealed(first)
        Silent(second)
        Sealed(second)

        self.assertIs(type(first), type(second))

    def test_agent_del_reads_the_finalizer_with_secrets_too(self) -> None:
        class Vaulted(Tag):
            @Secret
            @Record
            def code(agent) -> str:
                return "1234"

            def __del__(agent) -> None:
                pass

        door = self.Door()
        Vaulted(door)

        self.assertIs(door.__del__.__func__, type(door).__del__)
        self.assertNotIn("__del__", vars(door))

    def test_rip_on_a_finalizer_is_refused(self) -> None:
        with self.assertRaises(TagDeclarationError):
            class Keeper(Tag):
                @Rip
                def __del__(agent) -> None:
                    pass

    def test_a_host_that_subclasses_tagged_gets_its_teardowns(self) -> None:
        from TopKit import Tagged

        log = self.log

        class Marked(Tagged):
            def __del__(self) -> None:
                log.append("host")

        self.assertEqual(self.delete(self.Guard, host=Marked), ["teardown", "host"])

    def test_the_finalizer_is_what_agent_del_reads(self) -> None:
        class Sealed(Tag):
            def __del__(agent) -> None:
                pass

        class Silent(Tag):
            @Delete
            def __del__(agent): ...

        for tags in ((self.Guard,), (Sealed,), (Silent,)):
            door = self.Door()

            for tag in tags:
                tag(door)

            self.assertIs(door.__del__.__func__, type(door).__del__)   # Python's to call, one meaning

    def test_a_layer_is_sticky_after_its_tag_leaves(self) -> None:
        log = self.log

        class Sealed(Tag):
            def __del__(agent) -> None:
                log.append("sealed")

        door = self.Door()
        Sealed(door)
        del Sealed[door]
        del door
        gc.collect()

        self.assertEqual(log, ["sealed"])

    def test_a_layers_error_is_reported_like_any_finalizers(self) -> None:
        import sys

        reported: list[BaseException] = []

        class Cracked(Tag):
            def __del__(agent) -> None:
                raise ValueError("cracked")

        hook = sys.unraisablehook
        sys.unraisablehook = lambda raised: reported.append(raised.exc_value)

        try:
            self.delete(self.Guard, Cracked)
        finally:
            sys.unraisablehook = hook

        self.assertEqual(self.log, ["teardown"])
        self.assertEqual([type(error) for error in reported], [ValueError])

    def test_layers_do_not_split_the_runtime_types(self) -> None:
        class Sealed(Tag):
            def __del__(agent) -> None:
                pass

        class Warded(Tag):
            @Underlay
            def __del__(agent, underlay) -> None:
                underlay()

        class Silent(Tag):
            @Delete
            def __del__(agent): ...

        first, second, third = self.Door(), self.Door(), self.Door()
        Sealed(first)
        Warded(second)
        Silent(third)

        self.assertIs(type(first), type(second))
        self.assertIs(type(first), type(third))

    def test_at_exit_only_the_layers_run(self) -> None:
        program = """
from TopKit import Tag, Rip, At_Exit, Underlay

class Door:
    def __init__(self, name): self.name = name
    def __del__(self): print(self.name, "host")

class Guard(Tag):
    @Rip
    def Leave(agent): print(agent.name, "teardown")

class Warded(Tag):
    @Underlay
    def __del__(agent, underlay):
        print(agent.name, "warded")
        underlay()

alive = Door("alive"); Guard(alive); Warded(alive)
listed = Door("listed"); Guard(listed); At_Exit(listed)
print("end")
"""

        late = """
import os, sys
from TopKit import Tag, Rip, Underlay

class Door:
    def __init__(self, name): self.name = name
    def __del__(self, write=os.write): write(1, (self.name + " host\\n").encode())

class Guard(Tag):
    @Rip
    def Leave(agent): print(agent.name, "teardown")

class Warded(Tag):
    @Underlay
    def __del__(agent, underlay, write=os.write):
        write(1, (agent.name + " warded\\n").encode())
        underlay()

import TopKit.access, TopKit.lifecycle, TopKit.overlay, TopKit.state

KIT = (TopKit.access, TopKit.lifecycle, TopKit.overlay, TopKit.state)

def Hook(kind, value, trace, kit=KIT): sys.__excepthook__(kind, value, trace)

sys.excepthook = Hook                 # keeps this module, and the kit's modules, alive
                                      # until sys itself goes: their globals are wiped first

class Closer:
    def __call__(self, write=os.write): write(1, b"closer host\\n")

class Called:
    __del__ = Closer()                # a finalizer that is not a descriptor

guarded = Door("guarded"); Guard(guarded)
warded = Door("warded"); Guard(warded); Warded(warded)
called = Called(); Guard(called)
plain = type(guarded).__new__(type(guarded))   # built from an Agent's runtime type, never tagged
plain.name = "plain"
print("end")
"""
        lines, stderr = Run_Program(program)

        self.assertEqual(lines[0], "end")
        self.assertEqual(lines.index("listed teardown"), 1)   # At_Exit: while Python is whole
        self.assertNotIn("alive teardown", lines)             # teardowns at exit are opt-in
        self.assertLess(lines.index("alive warded"), lines.index("alive host"))
        self.assertIn("listed host", lines)
        self.assertEqual(stderr, "")

        lines, stderr = Run_Program(late)

        self.assertEqual(lines[0], "end")
        self.assertIn("guarded host", lines)                  # even after the kit's modules are gone
        self.assertIn("closer host", lines)
        self.assertIn("plain host", lines)                    # an untagged object of a runtime type, too
        self.assertLess(lines.index("warded warded"), lines.index("warded host"))
        self.assertNotIn("guarded teardown", lines)
