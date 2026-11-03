"""SD-4: cross-thread door leak. While one thread runs inside hold(), another
thread reads the same Agent's Secret and is ALLOWED.

Classification: OUTSIDE the documented promise ('One Agent, one thread. The
composing counter and Fields are not synchronized',
TopKit/IMPLEMENTATION_NOTES.md:676-677). Kept as a failing invariant.
"""
import sys
import threading
import time

sys.path.insert(0, "/home/io2007/Documents/Tag_Oriented_Programming")
from TopKit import Action, Record, Secret, Tag  # noqa: E402
from TopKit.state import _state_of  # noqa: E402


class Host:
    pass


class Leaky(Tag):
    @Secret
    @Record
    def code(agent):
        return "private"

    @Action
    def hold(agent, gate):
        gate.wait(5)
        return agent.code


def main():
    h = Host()
    Leaky(h)
    gate = threading.Event()
    out = {}

    def in_door():
        try:
            out["v"] = h.hold(gate)
        except BaseException as e:  # noqa: BLE001
            out["v"] = f"ERR: {e}"

    t = threading.Thread(target=in_door)
    t.start()
    time.sleep(0.3)
    try:
        leaked = h.code
    except AttributeError as e:
        leaked = f"DENIED: {e}"
    print(f"cross-thread read during open door: observed={leaked!r} expected=DENIED")
    gate.set()
    t.join()
    print(f"door thread result: {out.get('v')!r} (expected 'private')")
    print("composing after:", _state_of(h).composing, "(expected 0)")


if __name__ == "__main__":
    main()
