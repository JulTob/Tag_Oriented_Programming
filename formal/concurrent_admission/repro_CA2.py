"""FINDING CA-2: one Agent tagged with the same Tag by two threads admits
twice -- user Imprint code runs twice and state.active holds the Tag twice
(TopKit/transactions.py:_apply lines 85-89 vs _apply_one line 228 onward).

Model: formal/concurrent_admission/ActiveCheckThenAdd.tla (CA2_AdmitOnce).
Classification: outside the documented promise -- spec Ring 4
(spec/SPECIFICATION.md:1767): "Threads. One Agent, one thread. Fields are
not synchronized." TopKit/IMPLEMENTATION_NOTES.md:676-677: "One Agent,
one thread. The composing counter and Fields are not synchronized."

Run from the repo root: python3 formal/concurrent_admission/repro_CA2.py
"""

import threading

from TopKit import Imprint, Pre, Tag
from TopKit.state import _state_of

gate_barrier = threading.Barrier(2)
imprint_lock = threading.Lock()
imprints = []


class Host:
    pass


class Wizard(Tag):
    @Pre
    def check(agent):
        # Both threads rendezvous INSIDE the user Pre code, i.e. inside the
        # model window between the line-85 check and training.add (line 228).
        gate_barrier.wait(timeout=15)
        return True

    @Imprint
    def train(agent):
        with imprint_lock:
            imprints.append(threading.get_ident())


def main():
    agent = Host()
    outcomes = []

    def work():
        try:
            Wizard(agent)
            outcomes.append("ok")
        except BaseException as error:  # keep the report, never raise
            outcomes.append("error: " + repr(error))

    threads = [threading.Thread(target=work), threading.Thread(target=work)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    state = _state_of(agent)
    active = [tag.__name__ for tag in state.active]
    print("outcomes:", outcomes, "(expected: ['ok', 'ok'])")
    print("imprints (Imprint ran):", len(imprints), "(expected: 1)")
    print("active:", active, "(expected: ['Wizard'])")
    ok = len(imprints) == 2 and active == ["Wizard", "Wizard"]
    print("FINDING REPRODUCED:" if ok else "finding NOT reproduced:", ok)


if __name__ == "__main__":
    main()
