"""TopKit tooling: Mermaid and Graphviz diagrams of an Agent's Geometry."""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest
import warnings
from unittest import mock

from TopKit import Constant
from TopKit import Flag
from TopKit import Pin
from TopKit import Post
from TopKit import Record
from TopKit import Tag
from TopKit.diagram import Diagram
from TopKit.diagram import Save

from ._fixtures import Agent
from ._fixtures import Bridge
from ._fixtures import Bruiser
from ._fixtures import Elf


LINKS = "game.links"               # a module name that does not depend on how tests run


def _nodes(text: str) -> dict[str, str]:
    """Node id → first label line, its markup removed, for Mermaid or DOT."""

    found = re.findall(r'^\s+(\w+)(?:\(\[|\(|\{\{|>)"([^"]*)"(?:\]\)|\)|\}\}|\])$', text, re.M)
    found += re.findall(r"^\s+(\w+) \[label=<(.*?)>(?:,|\];)", text, re.M)

    return {
            node: re.sub(r"<[^>]*>", "", re.split(r"<br>|<BR/>", label)[0])
            for node, label in found
            }


def _arrows(text: str) -> list[tuple[str, str, str]]:
    """(source, label, shape) for each arrow, in order; a solid arrow's label is ""."""

    mermaid = re.findall(r"^  (\w+) (?:-->|-\.->\|(\w+)\|) (\w+)$", text, re.M)
    dot = [
            (a, b, label)
            for a, b, label in re.findall(
                    r'^  (\w+) -> (\w+)(?: \[style=dashed, label=" (\w+) "\])?;$', text, re.M,
                    )
            ]

    return [*((a, label, b) for a, label, b in mermaid), *((a, label, b) for a, b, label in dot)]


def _boxes(text: str) -> dict[str, list[str]]:
    """Module box name → the node ids inside it, for Mermaid."""

    boxes: dict[str, list[str]] = {}

    for module, body in re.findall(r'^  subgraph \w+\["([^"]*)"\]\n(.*?)^  end$', text, re.M | re.DOTALL):
        boxes[module] = re.findall(r'^    (\w+)\W', body, re.M)

    return boxes


class DiagramTests(unittest.TestCase):
    def test_arrows_run_from_each_base_to_its_shape(self) -> None:
        ari = Agent()
        Bridge(ari)
        Elf(ari)

        expected = [
                ("Agent", "", "Root"),
                ("Root", "", "Left"),
                ("Root", "", "Right"),
                ("Left", "", "Bridge"),
                ("Right", "", "Bridge"),
                ("Agent", "", "Person"),
                ("Person", "", "Elf"),
                ]

        for format in ("mermaid", "graphviz"):
            (text,) = Diagram(ari, format=format).values()
            names = _nodes(text)

            self.assertCountEqual(
                    [(names[a], label, names[b]) for a, label, b in _arrows(text)],
                    expected,
                    format,
                    )

    def test_direction_heads_the_chart(self) -> None:
        ari = Agent()
        Elf(ari)

        (mermaid,) = Diagram(ari, direction="LR").values()
        (dot,) = Diagram(ari, direction="TD", format="graphviz").values()

        self.assertTrue(mermaid.startswith("flowchart LR\n"))
        self.assertIn("rankdir=TB", dot)

    def test_each_module_of_a_chart_is_a_box(self) -> None:
        Species = type("Species", (Tag,), {"__module__": "game.species"})
        Elf = type("Elf", (Species,), {"__module__": "game.feats"})
        Sage = type("Sage", (Tag,), {"__module__": "game.backgrounds"})
        ari = Agent()
        Elf(ari)
        Sage(ari)

        (text,) = Diagram(ari).values()
        names = _nodes(text)

        self.assertEqual(
                {module: [names[n] for n in ids] for module, ids in _boxes(text).items()},
                {"game.species": ["Species"], "game.feats": ["Elf"], "game.backgrounds": ["Sage"]},
                )

        (dot,) = Diagram(ari, format="graphviz").values()
        self.assertEqual(dot.count("subgraph cluster_"), 3)

    def test_a_chart_of_one_module_has_no_box(self) -> None:
        ari = Agent()
        Bridge(ari)

        (text,) = Diagram(ari).values()
        (dot,) = Diagram(ari, format="graphviz").values()

        self.assertEqual(_boxes(text), {})
        self.assertNotIn("subgraph", dot)

    def test_the_limit_is_soft_a_family_is_never_split(self) -> None:
        chain = []
        base = Tag
        for i in range(7):
            base = type(f"Link_{i}", (base,), {"__module__": LINKS})
            chain.append(base)
        loose = [type(f"Loose_{i}", (Tag,), {"__module__": LINKS}) for i in range(5)]
        ari = Agent()
        chain[-1](ari)
        for tag in loose:
            tag(ari)

        parts = Diagram(ari, limit=4)
        drawn = [
                [name for n, name in _nodes(part).items() if n != "host"]
                for part in parts.values()
                ]

        self.assertEqual(list(parts), [LINKS, f"{LINKS} (2)", f"{LINKS} (3)"])
        self.assertEqual(
                drawn,
                [
                    [t.__name__ for t in chain],                        # 7, over the limit
                    [t.__name__ for t in loose[:4]],
                    [loose[4].__name__],
                    ],
                )
        self.assertIn(f'host(["Agent<br>{LINKS} (2)"])', parts[f"{LINKS} (2)"])

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
        (dot,) = Diagram(ari, format="graphviz").values()

        self.assertIn('("Bruiser<br>Post: Strength_Capped BROKEN")', text)
        self.assertIn('("Capped<br>Post: Strength_Capped")', text)
        self.assertRegex(dot, r"label=<Bruiser<BR/>.*Strength_Capped BROKEN.*>, shape=box, color=\"#e5484d\"")

    def test_a_ripped_tag_stays_dashed(self) -> None:
        ari = Agent()
        Elf(ari)
        del Elf[ari]

        (text,) = Diagram(ari).values()
        ids = {name: n for n, name in _nodes(text).items()}

        self.assertIn(f"  host -.->|ripped| {ids['Elf']}", text)
        self.assertIn(f"  class {ids['Elf']} ripped", text)

    def test_a_base_applied_again_after_its_rip_still_heads_its_family(self) -> None:
        Base_Again = type("Base_Again", (Tag,), {"__module__": "game.bases"})
        Shape_Kept = type("Shape_Kept", (Base_Again,), {"__module__": "game.shapes"})
        Other = type("Other", (Tag,), {"__module__": "game.other"})
        ari = Agent()
        Shape_Kept(ari)
        Other(ari)
        del Base_Again[ari]                                           # the Shape stays
        Base_Again(ari)                                               # now after its Shape

        (text,) = Diagram(ari).values()
        names = _nodes(text)

        self.assertCountEqual(
                [(names[a], label, names[b]) for a, label, b in _arrows(text)],
                [
                    ("Agent", "", "Base_Again"),
                    ("Base_Again", "", "Shape_Kept"),
                    ("Agent", "", "Other"),
                    ],
                )
        self.assertEqual(list(Diagram(ari, limit=1)), ["game.bases", "game.other"])

    def test_a_constant_post_broken_after_its_rip_is_still_marked(self) -> None:
        class Intelligence(Tag):
            @Constant
            @Post
            def NDA(agent) -> bool:
                return agent.keeps_secret

        lance = Agent()
        lance.keeps_secret = True
        Intelligence(lance)
        del Intelligence[lance]
        lance.keeps_secret = False                                    # the lifetime term breaks

        (text,) = Diagram(lance).values()
        ids = {name: n for n, name in _nodes(text).items()}

        self.assertIn('("Intelligence<br>Post: NDA (constant) BROKEN")', text)
        self.assertIn(f"  host -.->|ripped| {ids['Intelligence']}", text)
        self.assertIn(f"  class {ids['Intelligence']} broken", text)

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
        self.assertCountEqual(
                [(names[a], label, names[b]) for a, label, b in _arrows(text)],
                [("Person", "", "Elf"), ("Elf", "", "Hero"), ("Hero", "pins", "Rare")],
                )
        rare = next(n for n, v in names.items() if v == "Rare")
        self.assertIn(f'  {rare}{{{{"Rare<br>Record: rarity"}}}}', text)            # a hexagon
        self.assertIn(f"  class {rare} pin", text)

    def test_what_a_tag_is_picks_its_box(self) -> None:
        @Flag
        class Inspired(Tag):
            pass

        class Rare(Pin):
            pass

        class Hero(Tag):
            pass

        Rare(Hero)
        ari = Agent()
        Hero(ari)
        Inspired(ari)

        (text,) = Diagram(ari).values()
        (dot,) = Diagram(ari, format="graphviz").values()
        (pinned,) = Diagram(Hero, format="graphviz").values()

        self.assertRegex(text, r'\n  t\d+\("Hero"\)\n')                   # rounded
        self.assertRegex(text, r'\n  t\d+>"Inspired"\]\n')                # a flag
        self.assertRegex(dot, r"label=<Hero>, shape=box\]")
        self.assertRegex(dot, r"label=<Inspired>, shape=cds, ")
        self.assertRegex(pinned, r"label=<Rare>, shape=hexagon, ")

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
        self.assertCountEqual(
                [(names[a], label, names[b]) for a, label, b in _arrows(text)],
                [("Rare", "", "Rarer"), ("Solo", "pins", "Rare")],
                )

    def test_labels_cannot_break_out_of_their_box(self) -> None:
        odd = type('Odd"<b>&#', (), {})
        (text,) = Diagram(odd()).values()
        (dot,) = Diagram(odd(), format="graphviz").values()

        self.assertIn('host(["Odd#quot;#lt;b#gt;&#35;"])', text)
        self.assertIn('digraph "Odd\\"<b>&#" {', dot)
        self.assertIn("host [label=<Odd&quot;&lt;b&gt;&amp;#>,", dot)

    @unittest.skipUnless(shutil.which("dot"), "Graphviz is not installed")
    def test_graphviz_reads_every_chart(self) -> None:
        odd = type('Odd"<b>&#\\', (Tag,), {"__module__": 'game "odd"'})
        ari = Agent()
        Bridge(ari)
        odd(ari)
        del Bridge[ari]

        for text in Diagram(ari, format="graphviz").values():
            done = subprocess.run(["dot", "-Tsvg"], input=text, capture_output=True, text=True, check=False)
            self.assertEqual(done.returncode, 0, done.stderr)

    def test_a_part_holds_at_least_one_tag(self) -> None:
        with self.assertRaises(ValueError):
            Diagram(Agent(), limit=0)

    def test_an_unknown_format_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            Diagram(Agent(), format="plantuml")

    def test_save_writes_mermaid_files(self) -> None:
        ari = Agent()
        for module in ("game.feats", "game_feats"):                   # both "game_feats"
            type("Feat", (Tag,), {"__module__": module})(ari)

        with tempfile.TemporaryDirectory() as folder:
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

    def test_save_writes_dot_files_with_graphviz(self) -> None:
        ari = Agent()
        Elf(ari)

        with tempfile.TemporaryDirectory() as folder:
            paths = Save(ari, pathlib.Path(folder) / "ari", format="graphviz")
            written = {p.name: p.read_text() for p in paths}

        self.assertEqual(written, {"ari.dot": Diagram(ari, format="graphviz")["Agent"]})

    def test_a_mermaid_chart_has_no_image(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "format='graphviz'"):
                Save(Agent(), pathlib.Path(folder) / "ari", image="svg")

            self.assertEqual(list(pathlib.Path(folder).iterdir()), [])

    @unittest.skipUnless(shutil.which("dot"), "Graphviz is not installed")
    def test_save_draws_a_graphviz_image_with_dot(self) -> None:
        ari = Agent()
        Elf(ari)

        with tempfile.TemporaryDirectory() as folder:
            paths = Save(ari, pathlib.Path(folder) / "ari", format="graphviz", image="svg")
            names = [p.name for p in paths]
            picture = paths[1].read_text()

        self.assertEqual(names, ["ari.dot", "ari.svg"])
        self.assertIn("<svg", picture)
        self.assertIn(">Elf</text>", picture)

    def test_an_unknown_image_is_refused_before_anything_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                Save(Agent(), pathlib.Path(folder) / "ari", format="graphviz", image="jpg")

            self.assertEqual(list(pathlib.Path(folder).iterdir()), [])

    def test_a_graphviz_image_without_dot_names_the_install(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with (
                    mock.patch("TopKit.diagram.shutil.which", return_value=None),
                    self.assertRaisesRegex(FileNotFoundError, "install Graphviz"),
                    ):
                Save(Agent(), pathlib.Path(folder) / "ari", format="graphviz", image="png")

            self.assertEqual(list(pathlib.Path(folder).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
