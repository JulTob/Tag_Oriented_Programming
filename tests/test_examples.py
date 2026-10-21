"""Every example runs, and its own assertions hold.

The examples are the design patterns the project recommends; a pattern
that stops running is a change to TOP nobody decided.
"""

from __future__ import annotations

import contextlib
import io
import pathlib
import runpy
import unittest


EXAMPLES = pathlib.Path(__file__).resolve().parent.parent / "examples"


class ExampleTests(unittest.TestCase):

    def run_example(
            self,
            name: str,
            ) -> str:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            runpy.run_path(
                    str(EXAMPLES / name),
                    run_name="__main__",
                    )

        return output.getvalue()

    def test_dnd_character(self) -> None:
        self.run_example("dnd_character.py")

    def test_biome(self) -> None:
        self.run_example("biome.py")

    def test_fleet_patching(self) -> None:
        output = self.run_example("fleet_patching.py")

        self.assertIn("patched: Flyer v2: thrust 80", output)
        self.assertIn("rolled back: Flyer v1: thrust 100", output)
        self.assertIn("Courier is retired", output)
        self.assertIn("Sprayer refused", output)
        self.assertIn("grounded drone: audit refused", output)

    def test_crew_access(self) -> None:
        output = self.run_example("crew_access.py")

        self.assertIn("relieved: the Bridge's weapons refuse him", output)
        self.assertIn("repaired and fired", output)
        self.assertIn("every published door is closed", output)
        self.assertIn("queued command refused at run time", output)
        self.assertIn("not alive: cannot join the crew", output)
        self.assertIn("Weapons_Locked follows the Bridge", output)
        self.assertIn("Veteran.Alive guards its own Underlay", output)


    def test_equipment(self) -> None:
        output = self.run_example("equipment.py")

        self.assertIn("Ari strikes with longsword for 6", output)
        self.assertIn("worn weapon: attack refused", output)
        self.assertIn("repaired: Ari strikes with longsword for 6", output)
        self.assertIn("wrong kind: assignment refused", output)
        self.assertIn("swapped: Ari strikes with shortsword for 4", output)
        self.assertIn("empty hand: attack refused", output)
        self.assertIn("equipped again: shortsword", output)


    def test_equipment_links(self) -> None:
        output = self.run_example("equipment_links.py")

        self.assertIn("distinct Pairs: Ari's hand; Bob's pack", output)
        self.assertIn("broken carrying Post: attack refused", output)
        self.assertIn("Reports belong to each actual Carries Tag", output)
        self.assertIn("Ripped: saved Pair view refuses absent membership", output)
        self.assertIn("reLinked: saved view and Action follow Ari's current Pair", output)


if __name__ == "__main__":
    unittest.main()
