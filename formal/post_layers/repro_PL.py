"""PL1-PL8 real-code replay of the shortest break traces (PostLayers model).

Run: python3 formal/post_layers/repro_PL.py. Prints observed vs expected per invariant.
Covers: ordinary ends before teardown; top reveals survivor; middle rebinds
(neutral True); Constant survives Rip/Delete; retry keeps fresh app; failed
admission discards provisional; nested inner stays on outer failure; arrested
truth gated without evaluating Posts.
"""
import sys
import warnings

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else ".")
from TopKit import (
    Constant, Contract, Imprint, Post, Record, Rip, Tag, Underlay,
)
from TopKit.contracts import _holds
from TopKit.state import _state_of


class Host:
    pass


def check(name, observed, expected):
    mark = "ok" if observed == expected else "MISMATCH"
    print(f"{name}: observed={observed} expected={expected} [{mark}]")
    return observed == expected


results = []

# PL1: ordinary Post ends before its teardown runs (even a failing one).
observed = []
class Car(Tag):
    @Post
    def Ready(agent):
        return True

    @Rip
    def Fail(agent):
        observed.append(dict(Contract.Status(agent)))
        raise RuntimeError("cleanup failed")

a = Host()
Car(a)
try:
    del Car[a]
except Exception:
    pass
results.append(check("PL1 teardown-status", observed, [{}]))

# PL2: ending the top layer reveals the next survivor.
class Base(Tag):
    @Post
    def Ready(agent):
        return agent.ready

class Later(Tag):
    @Post
    def Ready(agent):
        return True

b = Host()
b.ready = True
Base(b)
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    Later(b)
b.ready = False
results.append(check("PL2 top-visible", (b.Ready, Contract.Status(b)), (True, {"Ready": True})))
del Later[b]
results.append(check("PL2 survivor", (b.Ready, Contract.Status(b)), (False, {"Ready": False})))

# PL3: middle removal reconnects the upper Underlay; neutral True if none.
calls = []
class B0(Tag):
    @Post
    def Ready(agent):
        calls.append("B0")
        return True

class M0(Tag):
    @Post
    @Underlay
    def Ready(agent, prior):
        calls.append("M0")
        return prior()

class T0(Tag):
    @Post
    @Underlay
    def Ready(agent, prior):
        calls.append("T0")
        return prior()

c = Host()
B0(c); M0(c); T0(c)
del M0[c]
calls.clear()
c.Ready
results.append(check("PL3 rebind", list(calls), ["T0", "B0"]))
del B0[c]
calls.clear()
c.Ready
results.append(check("PL3 neutral", (list(calls), bool(Contract.Status(c))), (["T0"], True)))

# PL4: admitted Constant survives Rip and refuses Contract.Delete.
class Emp(Tag):
    @Constant
    @Post
    def NDA(agent):
        return agent.keeps_secret

d = Host()
d.keeps_secret = True
Emp(d)
del Emp[d]
results.append(check("PL4 survives-rip", Contract.Status(d), {"NDA": True}))
try:
    Contract.Delete(d, "NDA")
    refused = False
except Exception:
    refused = True
results.append(check("PL4 delete-refused", (refused, Contract.Status(d)), (True, {"NDA": True})))

# PL5: an old Rip retry never removes a fresh same-Tag application.
class CC(Tag):
    @Post
    def Ready(agent):
        return agent in CC[:]

    @Rip
    def Rejoin(agent):
        CC(agent)

e = Host()
CC(e)
del CC[e]
results.append(check("PL5 fresh-kept", (e in CC[:], Contract.Status(e)), (True, {"Ready": True})))

# PL6: a failed admission discards provisional Posts incl. Constant lock.
def Rdy(agent):
    return True

Broken = type("Broken", (Tag,), {
    "Ready": Post(Rdy),
    "value": Record(lambda agent: (_ for _ in ()).throw(RuntimeError("no value"))),
})
f = Host()
try:
    Broken(f)
except Exception:
    pass
results.append(check("PL6 discarded", (Contract.Status(f), hasattr(f, "Ready")), ({}, False)))

# PL7: outer failure after its Imprint keeps the admitted inner layer.
class Inner(Tag):
    @Post
    def Go(agent):
        return True

class Outer(Tag):
    @Post
    def Go(agent):
        return True

    @Imprint
    def Enter1(agent):
        Inner(agent)

    @Imprint
    def Enter2(agent):
        raise RuntimeError("outer imprint fails late")

g = Host()
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    try:
        Outer(g)
    except Exception:
        pass
st = _state_of(g)
results.append(check(
    "PL7 inner-stays",
    ([l.tag.__name__ for l in st.post_layers.get("Go", ())], Contract.Status(g)),
    (["Inner"], {"Go": True}),
))

# PL8: arrested truth is False without evaluating Posts.
class Arr(Tag):
    @Post
    def Ready(agent):
        return True

    @Rip
    def Stuck(agent):
        raise RuntimeError("stuck")

h = Host()
Arr(h)
try:
    del Arr[h]
except Exception:
    pass
results.append(check("PL8 gated", (_holds(h), Contract.Status(h)), (False, {})))

print("ALL OK" if all(results) else "MISMATCHES PRESENT")
