"""Runtime types use an identifier's text without owning its source object."""

import gc
import unittest
import weakref

from TopKit import Action, Constant, Delete, Pin, Public, Record
from TopKit import Report, Secret, Tag, Tool
from TopKit import state as runtime


class Name(str):
    pass


class Host:
    pass


class RuntimeIdentifierOwnershipTests(unittest.TestCase):
    def collected(self, references):
        gc.collect()
        gc.collect()
        for label, reference in zip(
                ("name", "Agent or Tag", "Tag or Pin", "runtime type"),
                references,
                ):
            self.assertIsNone(reference(), label)

    def retain_field(self, declaration_factory, spelling):
        def create():
            agent = Host()
            name = Name(spelling)
            name.owner = agent
            role = type("Role", (Tag,), {name: declaration_factory()})
            population = role[:]
            role(agent)
            return population, (
                    weakref.ref(name),
                    weakref.ref(agent),
                    weakref.ref(role),
                    weakref.ref(type(agent)),
                    )

        population, references = create()
        self.collected(references)
        self.assertEqual(len(population), 0)

    def test_secret_constant_and_dunder_names_do_not_root_a_field(self):
        cases = (
                (lambda: Secret(Record(lambda agent: 41)), "vault"),
                (lambda: Constant(Record(lambda agent: 41)), "vault"),
                (lambda: Action(lambda agent: 7), "__len__"),
                (lambda: Delete(lambda agent: None), "removed"),
                (lambda: Tool(Host)(lambda agent: Host()), "equipment"),
                )
        for factory, spelling in cases:
            with self.subTest(spelling=spelling, factory=factory):
                self.retain_field(factory, spelling)

    def test_published_report_name_does_not_root_a_field(self):
        self.retain_field(lambda: Public(Report(lambda tag: 41)), "signal")

    def test_all_key_seats_own_plain_text_without_calling_name_hooks(self):
        class Names(str):
            pass

        names = {
                spelling: Names(spelling)
                for spelling in (
                        "deleted", "restored", "secret", "published", "Ready",
                        "__len__", "constant", "tool",
                        )
                }
        state = runtime._State(host_type=Host)
        state.deleted.add(names["deleted"])
        state.restored = frozenset((names["restored"],))
        state.secrets.add(names["secret"])
        state.published.add(names["published"])
        state.postconditions[names["Ready"]] = lambda agent: True
        length = lambda agent: 7
        state.actions[names["__len__"]] = length
        state.constants[names["constant"]] = (Tag, "record", None)
        state.tools[names["tool"]] = (Tag, object())

        def forbidden(*arguments):
            raise AssertionError("a user string hook ran while making the key")

        # The names have already entered their sets and mappings. The key
        # builder must inspect their built-in text, not ask their methods.
        for method in ("__str__", "__repr__", "__format__", "__hash__",
                       "__eq__", "startswith", "endswith"):
            setattr(Names, method, forbidden)

        key = runtime._type_key_of(state)
        self.assertEqual(
                tuple(type(name) for seat in (1, 2, 3, 4, 7, 8)
                      for name in key[seat]),
                (str,) * 7,
                )
        self.assertEqual(key[6], (("__len__", id(length)),))
        self.assertIs(type(key[6][0][0]), str)
        runtime_type = runtime._runtime_type_for(state)
        self.assertTrue(all(type(name) is str for name in vars(runtime_type)))
        for spelling in ("deleted", "restored", "secret", "published", "Ready",
                         "constant", "tool"):
            self.assertIs(type(vars(runtime_type)[spelling].name), str)

    def test_equal_text_shares_runtime_type_and_preserves_native_dispatch(self):
        class HostWithLength:
            pass

        def length(agent):
            return 7

        name = Name("__len__")
        given = type("Length", (Tag,), {name: Action(length)})
        plain = type("PlainLength", (Tag,), {"__len__": Action(length)})
        first = HostWithLength()
        given(first)
        second = HostWithLength()
        plain(second)
        self.assertIs(type(first), type(second))
        self.assertEqual((len(first), len(second)), (7, 7))
        self.assertTrue(any(type(key[6][0][0]) is str for key in runtime._type_cache
                            if key[6] and key[6][0][0] == "__len__"))

    def test_pin_target_keeps_published_name_behavior(self):
        name = Name("signal")
        pin = Pin(type("Given", (Tag,), {
                name: Public(Record(lambda tag: 41)),
                }))
        target = type("Target", (Tag,), {})
        pin(target)
        self.assertEqual(target.signal, 41)
        self.assertEqual(next(iter(target.__dict__[runtime.STATE].published)), "signal")
        key = runtime._type_key_of(target.__dict__[runtime.STATE])
        self.assertEqual(key[3], frozenset(("signal",)))
        self.assertTrue(all(type(text) is str for text in key[3]))

    def test_a_pins_name_does_not_root_its_target_tag(self):
        def create():
            target = type("Target", (Tag,), {})
            name = Name("signal")
            name.owner = target
            pin = Pin(type("Given", (Tag,), {
                    name: Public(Record(lambda tag: 41)),
                    }))
            pin(target)
            self.assertEqual(target.signal, 41)
            return target[:], (
                    weakref.ref(name),
                    weakref.ref(target),
                    weakref.ref(pin),
                    weakref.ref(type(target)),
                    )

        population, references = create()
        self.collected(references)
        self.assertEqual(len(population), 0)


if __name__ == "__main__":
    unittest.main()
