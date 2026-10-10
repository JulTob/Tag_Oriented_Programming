"""Python optimization removes assertions, not TOP's Constant binding locks."""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
PROGRAM = """
import json
import sys
from TopKit import (Constant, Contract, Post, Pre, Tag, TagCompositionError,
                    TagPostconditionError, TagPreconditionError)

class Host:
    ready = False

class Assertion_Gate(Tag):
    @Pre
    def Ready(agent):
        assert agent.ready

class Return_Gate(Tag):
    @Pre
    def Ready(agent):
        return agent.ready

class Assertion_Promise(Tag):
    @Constant
    @Post
    def Ready(agent):
        assert agent.ready

class Return_Promise(Tag):
    @Constant
    @Post
    def Ready(agent):
        return agent.ready

results = {"optimization": sys.flags.optimize}
for role in (Assertion_Gate, Return_Gate, Assertion_Promise, Return_Promise):
    agent = Host()
    phase = "accepted"
    try:
        role(agent)
    except TagPreconditionError:
        phase = "Precondition"
    except TagPostconditionError:
        phase = "Postcondition"
    result = {"phase": phase, "member": agent in role[:],
              "holds": Contract.Holds(agent)}
    if role in (Assertion_Promise, Return_Promise):
        locks = []
        for change in (lambda: setattr(agent, "Ready", False),
                       lambda: delattr(agent, "Ready"),
                       lambda: Contract.Delete(agent, "Ready")):
            try:
                change()
            except TagCompositionError:
                locks.append(True)
            else:
                locks.append(False)
        result.update(locks=locks, status=Contract.Status(agent),
                      holds_after=Contract.Holds(agent))
    results[role.__name__] = result
print(json.dumps(results, sort_keys=True))
"""


class OptimizedConditionTests(unittest.TestCase):

    def test_assertion_conditions_and_constant_locks_in_each_python_mode(self):
        environment = os.environ.copy()
        environment.pop("PYTHONOPTIMIZE", None)
        environment["PYTHONPATH"] = str(ROOT)

        for optimization, flags in ((0, ()), (1, ("-O",)), (2, ("-OO",))):
            with self.subTest(optimization=optimization):
                child = subprocess.run(
                        [sys.executable, "-E", "-B", *flags, "-c", PROGRAM],
                        cwd=ROOT,
                        env=environment,
                        capture_output=True,
                        text=True,
                        timeout=15,
                        )
                self.assertEqual(child.returncode, 0, child.stderr)
                observed = json.loads(child.stdout)
                self.assertEqual(observed.pop("optimization"), optimization)

                gate = {"phase": "Precondition", "member": False, "holds": True}
                promise = {"phase": "Postcondition", "member": True, "holds": False,
                           "locks": [True, True, True], "status": {"Ready": False},
                           "holds_after": False}
                accepted = {"phase": "accepted", "member": True, "holds": True}
                accepted_promise = {**accepted, "locks": [True, True, True],
                                    "status": {"Ready": True}, "holds_after": True}
                self.assertEqual(observed, {
                        "Assertion_Gate": accepted if optimization else gate,
                        "Return_Gate": gate,
                        "Assertion_Promise": accepted_promise if optimization else promise,
                        "Return_Promise": promise,
                        })


if __name__ == "__main__":
    unittest.main()
