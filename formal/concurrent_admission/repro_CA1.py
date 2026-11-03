"""FINDING CA-1: two threads tagging two Agents of one host build two runtime
types for one identical type key (TopKit/state.py:_runtime_type_for).

Model: formal/concurrent_admission/RuntimeTypeCache.tla (CA1_SingleType).
Classification: outside the documented promise -- spec Ring 4
(spec/SPECIFICATION.md:1767): "Threads. One Agent, one thread. Fields are
not synchronized." TopKit/IMPLEMENTATION_NOTES.md:676-677: "One Agent,
one thread. The composing counter and Fields are not synchronized."

Run from the repo root: python3 formal/concurrent_admission/repro_CA1.py
"""

import threading

from TopKit import Tag
from TopKit.state import _type_cache

builds = []
builds_lock = threading.Lock()
first_build_started = threading.Event()
allow_first_return = threading.Event()
racing = threading.Event()  # set only while the two taggings race


class Host:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__ != "Host":
            return  # only count runtime-type constructions, not TopKit internals
        with builds_lock:
            builds.append(cls)
            mine_first = len(builds) == 1
        if mine_first and racing.is_set():
            first_build_started.set()
            # Park the FIRST runtime-type construction inside host code (the
            # model gap between the cache read at state.py:1502-1506 and the
            # store at state.py:1642) so the peer also misses the cache.
            allow_first_return.wait(timeout=15)


class Wizard(Tag):
    pass


def main():
    a0, a1 = Host(), Host()
    outcomes = [None, None]

    def work(i, agent):
        try:
            Wizard(agent)
            outcomes[i] = ("ok", type(agent))
        except BaseException as error:  # keep the report, never raise
            outcomes[i] = ("error", repr(error))

    threads = [
        threading.Thread(target=work, args=(0, a0)),
        threading.Thread(target=work, args=(1, a1)),
    ]
    racing.set()
    threads[0].start()
    if not first_build_started.wait(timeout=15):
        print("TIMEOUT waiting for the first runtime-type construction")
        allow_first_return.set()
        for thread in threads:
            thread.join(timeout=20)
        raise SystemExit(2)
    threads[1].start()
    threads[1].join(timeout=30)
    allow_first_return.set()
    threads[0].join(timeout=30)
    print("builds (type(...) ran):", len(builds), "(expected: 1)")
    print("outcomes:", [kind for kind, _ in outcomes], "(expected: ['ok', 'ok'])")
    if outcomes[0][0] == "ok" and outcomes[1][0] == "ok":
        shared = outcomes[0][1] is outcomes[1][1]
        print("type(a0) is type(a1):", shared, "(expected: True)")
        from TopKit.state import _type_key_of, _state_of
        key = _type_key_of(_state_of(a0))
        print("cache is a0's type:", _type_cache.get(key) is outcomes[0][1],
              "| cache is a1's type:", _type_cache.get(key) is outcomes[1][1],
              "(expected: exactly one True; the loser is orphaned)")
    ok = (
        len(builds) == 2
        and outcomes[0][0] == "ok"
        and outcomes[1][0] == "ok"
        and outcomes[0][1] is not outcomes[1][1]
    )
    print("FINDING REPRODUCED:" if ok else "finding NOT reproduced:", ok)


if __name__ == "__main__":
    main()
