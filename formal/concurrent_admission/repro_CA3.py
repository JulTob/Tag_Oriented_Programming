"""FINDING CA-3: an Agent joining a Field mid-pinning never receives the
published member -- the pin thread snapshots the Field without it
(transactions.py:581) and publishes to the snapshot only (608-639).

Model: formal/concurrent_admission/PinPublication.tla (CA3_PublishAll).
Classification: outside the documented promise -- spec Ring 4
(spec/SPECIFICATION.md:1767): "Threads. One Agent, one thread. Fields are
not synchronized." TopKit/IMPLEMENTATION_NOTES.md:676-677: "One Agent,
one thread. The composing counter and Fields are not synchronized."

Run from the repo root: python3 formal/concurrent_admission/repro_CA3.py
"""

import threading

from TopKit import Imprint, Pin, Public, Record, Tag
from tests.test_tools import Character

entered_imprint = threading.Event()
release_imprint = threading.Event()


class Held(Tag):
    @Imprint
    def setup(agent):
        # Park ari's Tagging inside user Imprint code (the model's GateX):
        # ari passed the Gate but has not joined the Field yet.
        entered_imprint.set()
        release_imprint.wait(timeout=15)


class Rare(Pin):
    @Public
    @Record
    def rarity(tag):
        return "rare"


def main():
    present = Character("present")
    Held(present)
    ari = Character("ari")
    outcome = []

    def tag_ari():
        try:
            Held(ari)
            outcome.append("tag-ok")
        except BaseException as error:  # keep the report, never raise
            outcome.append("tag-error: " + repr(error))

    thread = threading.Thread(target=tag_ari)
    thread.start()
    if not entered_imprint.wait(timeout=15):
        print("TIMEOUT waiting for ari to enter its Imprint")
        release_imprint.set()
        thread.join(timeout=20)
        raise SystemExit(2)

    Rare(Held)  # plans snapshot the Field without ari, publishes to it
    print("pin applied; present.rarity:", present.rarity, "(expected: 'rare')")
    release_imprint.set()
    thread.join(timeout=30)
    print("tag thread:", outcome, "(expected: ['tag-ok'])")

    try:
        seen = ari.rarity
        print("ari.rarity:", seen, "(expected: AttributeError)")
        missing = False
    except AttributeError as error:
        print("ari MISSING member:", error, "(the finding)")
        missing = True

    late = Character("late")
    Held(late)
    print("late.rarity:", late.rarity, "(expected: 'rare')")
    ok = outcome == ["tag-ok"] and missing and late.rarity == "rare"
    print("FINDING REPRODUCED:" if ok else "finding NOT reproduced:", ok)


if __name__ == "__main__":
    main()
