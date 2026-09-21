"""Every runnable block of the guides, and every example of the
Specification, runs. A block that stops running is a change to TOP nobody
decided.

Each guide is run as one program: its ```python blocks are executed in
order in one namespace, as a reader following along would.
"""

from __future__ import annotations

import contextlib
import io
import pathlib
import re
import unittest
import warnings

from tests import spec_examples


ROOT = pathlib.Path(__file__).resolve().parent.parent
BLOCK = re.compile(r"```python\n(.*?)```", re.S)


def Run_Blocks(
        document: pathlib.Path,
        ) -> int:
    """Run every python block of ``document`` in one namespace; return
    how many ran. The failing block's number and text are in the error."""

    blocks = BLOCK.findall(document.read_text())
    namespace: dict[str, object] = {}

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        for index, block in enumerate(blocks, 1):
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    exec(
                            compile(block, f"{document.name} block {index}", "exec"),
                            namespace,
                            )
            except Exception as error:
                raise AssertionError(
                        f"{document.name} block {index} failed:"
                        f" {type(error).__name__}: {error}\n{block}"
                        ) from error

    return len(blocks)


class DocumentTests(unittest.TestCase):

    def test_the_specification_examples(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spec_examples.Run()

    def test_the_guide(self) -> None:
        self.assertGreater(Run_Blocks(ROOT / "TopKit" / "GUIDE.md"), 20)

    def test_the_contracts_guide(self) -> None:
        self.assertGreater(Run_Blocks(ROOT / "TopKit" / "CONTRACTS.md"), 15)

    def test_the_fields_guide(self) -> None:
        self.assertGreater(Run_Blocks(ROOT / "TopKit" / "FIELDS.md"), 8)

    def test_the_index_guide(self) -> None:
        self.assertGreater(Run_Blocks(ROOT / "TopKit" / "INDEX.md"), 12)


if __name__ == "__main__":
    unittest.main()
