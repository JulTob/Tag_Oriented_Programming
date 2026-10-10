"""Extreme Geometry regressions ported from the archived stress layer."""

from __future__ import annotations

import sys
import unittest

from TopKit import Form
from TopKit import Tag


class GeometryRegressionTests(unittest.TestCase):

    def test_form_does_not_use_python_recursion_depth(self) -> None:
        depth = 250
        current = Tag
        expected: list[type[Tag]] = []

        for index in range(depth):
            current = type(
                    f"Deep_Form_{index}",
                    (current,),
                    {},
                    )
            expected.append(current)

        original_limit = sys.getrecursionlimit()

        try:
            sys.setrecursionlimit(200)
            self.assertEqual(
                    Form(current),
                    tuple(expected),
                    )
        finally:
            sys.setrecursionlimit(original_limit)


if __name__ == "__main__":
    unittest.main()
