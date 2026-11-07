"""TopKit tooling: Mermaid diagrams of an Agent's Geometry."""

from __future__ import annotations

import pathlib
import re
import sys
import tempfile
import types
import unittest
import warnings
from unittest import mock

from TopKit import Pin
from TopKit import Record
from TopKit import Tag
from TopKit.diagram import Diagram
from TopKit.diagram import Save

from ._fixtures import Agent
from ._fixtures import Bridge
from ._fixtures import Bruiser
from ._fixtures import Elf


HERE = __name__                     # the module that declares this file's Tags


def _nodes(text: str) -> dict[str, str]:
    """Node id → first label line."""

    return {
            node: label.split("<br>")[0]
            for node, label in re.findall(r'^  (\w+)\["([^"]*)"\]$', text, re.M)
            }


def _arrows(text: str) -> list[tuple[str, str]]:
    return re.findall(r"^  (\w+) -[-.]+>(?:\|\w+\|)? (\w+)$", text, re.M)


class DiagramTests(unittest.TestCase):
    def test_arrows_run_from_each_base_to_its_shape(self) -> None:
        ari = Agent()
        Bridge(ari)
        Elf(ari)

        (text,) = Diagram(ari).values()
        names = _nodes(text)

        self.assertEqual(
                {(names[a], names[b]) for a, b in _arrows(text)},
                {
                    ("Agent", "Root"),
                    ("Root", "Left"),
                    ("Root", "Right"),
                    ("Left", "Bridge"),
                    ("Right", "Bridge"),
                    ("Agent", "Person"),
                    ("Person", "Elf"),
                    },
                )

    def test_the_limit_is_soft_a_family_is_never_split(self) -> None:
        chain = []
        base = Tag
        for i in range(7):
            base = type(f"Link_{i}", (base,), {"__module__": HERE})
            chain.append(base)
        loose = [type(f"Loose_{i}", (Tag,), {"__module__": HERE}) for i in range(5)]
        ari = Agent()
        chain[-1](ari)
        for tag in loose:
            tag(ari)

        parts = Diagram(ari, limit=4)
        drawn = [
                [name for n, name in _nodes(part).items() if n != "host"]
                for part in parts.values()
                ]

        self.assertEqual(list(parts), [HERE, f"{HERE} (2)", f"{HERE} (3)"])
        self.assertEqual(
                drawn,
                [
                    [t.__name__ for t in chain],                        # 7, over the limit
                    [t.__name__ for t in loose[:4]],
                    [loose[4].__name__],
                    ],
                )

    def test_a_family_is_drawn_with_the_module_of_its_top_base(self) -> None:
        Species = type("Species", (Tag,), {"__module__": "game.species"})
        Elf = type("Elf", (Species,), {"__module__": "game.feats"})   # declared elsewhere
        Sage = type("Sage", (Tag,), {"__module__": "game.backgrounds"})
        Tough = type("Tough", (Tag,), {"__module__": "game.feats"})
        ari = Agent()
        for tag in (Elf, Sage, Tough):
            tag(ari)

        parts = Diagram(ari, limit=1)

        self.assertEqual(
                {
                    name: [label for n, label in _nodes(part).items() if n != "host"]
                    for name, part in parts.items()
                    },
                {
                    "game.species": ["Species", "Elf"],
                    "game.backgrounds": ["Sage"],
                    "game.feats": ["Tough"],
                    },
                )
        self.assertEqual(list(Diagram(ari, limit=4)), ["Agent"])      # under the limit

    def test_a_broken_post_is_marked_on_the_layer_that_declares_it(self) -> None:
        ari = Agent()
        ari.strength = 10
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            Bruiser(ari)
        ari.strength = 30

        (text,) = Diagram(ari).values()

        self.assertIn('["Bruiser<br>Post: Strength_Capped BROKEN"]', text)
        self.assertIn('["Capped<br>Post: Strength_Capped"]', text)

    def test_a_ripped_tag_stays_dashed(self) -> None:
        ari = Agent()
        Elf(ari)
        del Elf[ari]

        (text,) = Diagram(ari).values()
        ids = {name: n for n, name in _nodes(text).items()}

        self.assertIn(f"  host -.->|ripped| {ids['Elf']}", text)
        self.assertIn(f"  class {ids['Elf']} ripped", text)

    def test_a_tag_draws_its_form_and_its_pins(self) -> None:
        class Rare(Pin):
            @Record
            def rarity(tag) -> str:
                return "rare"

        class Hero(Elf):
            pass

        Rare(Hero)
        (text,) = Diagram(Hero).values()
        names = _nodes(text)

        self.assertNotIn("host", names)
        self.assertEqual(
                {(names[a], names[b]) for a, b in _arrows(text)},
                {("Person", "Elf"), ("Elf", "Hero"), ("Hero", "Rare")},
                )

    def test_a_tag_and_its_pins_are_one_family_never_divided(self) -> None:
        class Rare(Pin):
            pass

        class Rarer(Rare):
            pass

        class Solo(Tag):
            pass

        Rarer(Solo)
        (name, text), = Diagram(Solo, limit=1).items()
        names = _nodes(text)

        self.assertEqual(name, "Solo")
        self.assertEqual(list(names.values()), ["Solo", "Rare", "Rarer"])  # not the root Tag
        self.assertEqual(
                {(names[a], names[b]) for a, b in _arrows(text)},
                {("Rare", "Rarer"), ("Solo", "Rare")},
                )

    def test_labels_cannot_break_out_of_their_box(self) -> None:
        odd = type('Odd"<b>#', (), {})
        (text,) = Diagram(odd()).values()

        self.assertIn('host["Odd#quot;#lt;b#gt;#35;"]', text)

    def test_a_part_holds_at_least_one_tag(self) -> None:
        with self.assertRaises(ValueError):
            Diagram(Agent(), limit=0)

    def test_save_writes_mermaid_files_without_mmdr(self) -> None:
        ari = Agent()
        for module in ("game.feats", "game_feats"):                   # both "game_feats"
            type("Feat", (Tag,), {"__module__": module})(ari)

        with (
                mock.patch.dict(sys.modules, {"mmdr": None}),
                tempfile.TemporaryDirectory() as folder,
                ):
            paths = Save(ari, pathlib.Path(folder) / "ari", limit=1)
            written = {p.name: p.read_text() for p in paths}

        parts = Diagram(ari, limit=1)
        self.assertEqual(
                written,
                {
                    "ari-game_feats.mmd": parts["game.feats"],
                    "ari-game_feats-2.mmd": parts["game_feats"],
                    },
                )

    def test_save_draws_an_image_beside_each_mermaid_file(self) -> None:
        ari = Agent()
        Elf(ari)
        drawn = types.SimpleNamespace(
                render=lambda text, backend: types.SimpleNamespace(svg=lambda: "<svg/>"),
                )

        with (
                mock.patch.dict(sys.modules, {"mmdr": drawn}),
                tempfile.TemporaryDirectory() as folder,
                ):
            paths = Save(ari, pathlib.Path(folder) / "ari.svg", image="svg")
            written = {p.name: p.read_text() for p in paths}

        self.assertEqual(written, {"ari.mmd": Diagram(ari)["Agent"], "ari.svg": "<svg/>"})

    def test_an_image_without_mmdr_names_the_install(self) -> None:
        with (
                mock.patch.dict(sys.modules, {"mmdr": None}),
                self.assertRaisesRegex(ImportError, r"pip install topkit\[diagram\]"),
                ):
            Save(Agent(), "unused", image="png")


if __name__ == "__main__":
    unittest.main()
