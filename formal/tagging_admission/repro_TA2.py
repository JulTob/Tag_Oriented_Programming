"""Reproducer TA-2: Tagging is not atomic under an async interrupt (FINDING).

Model: formal/tagging_admission/FieldAdding.tla (TA2_AtomicAdmission:
Field entry, active membership and history are established together).
Trace: FieldAdd then InterruptAfterAdd -- KeyboardInterrupt lands between
TopKit/fields.py:_Field._Add (transactions.py:_enter_field:539) and
state.active.append (:540).

Method: this script injects the interrupt by patching field._Add so it
calls the REAL _Add and then raises KeyboardInterrupt -- i.e. the
interrupt lands exactly in the window the model describes. Prints
observed vs expected.
"""
import sys

sys.path.insert(0, "/home/io2007/Documents/Tag_Oriented_Programming")

from TopKit import Record, Tag
from TopKit import fields as _fields
from TopKit import state as _S
from TopKit import transactions as _T


class Host:
    pass


class T(Tag):
    @Record
    def val(agent):
        return 1


def main() -> None:
    real_add = _fields._Field._Add

    def patched(field, agent):
        real_add(field, agent)
        raise KeyboardInterrupt("injected right after the real _Add")

    agent = Host()
    _fields._Field._Add = patched
    try:
        T(agent)
        raised = None
    except BaseException as e:  # noqa: BLE001 -- we report the type
        raised = type(e).__name__
    finally:
        _fields._Field._Add = real_add

    st = _S._state_of(agent)
    in_field = agent in T[:]
    active = (T in st.active) if st else False
    ever = (T in st.ever) if st else False
    isinst = isinstance(agent, T)
    sound = agent in T
    print(f"raised during Tagging: {raised} (expected KeyboardInterrupt)")
    print(f"observed: field={in_field} active={active} ever={ever} "
          f"isinstance={isinst} sound={sound}")
    print("expected (spec 208-209 'Membership and history are established "
          "together'): field == active == ever, and a Field member "
          "is an instance")

    try:
        del T[agent]
        rip = "ok (removed)"
    except BaseException as e:  # noqa: BLE001
        rip = f"{type(e).__name__}: {e}"
    print(f"observed `del T[agent]`: {rip}")
    print("expected: member rippable (spec:305 'Rip is the only exit "
          "from a Field')")

    good = Host()
    T(good)
    try:
        del T[:]
        whole = "ok"
    except BaseException as e:  # noqa: BLE001
        whole = f"{type(e).__name__}: {e}"
    print(f"observed `del T[:]` with a healthy member present: {whole}")
    print("expected: ok (one phantom must not wedge whole-Field Rip)")
    try:
        if good in T[:]:
            del T[good]
    except BaseException:
        pass

    split = not (in_field == active == ever and (not in_field or isinst))
    wedged = rip != "ok (removed)" or whole != "ok"
    print("REPLAY:", "FINDING REPRODUCED (phantom member, Rip wedged)"
          if (split or wedged) else "OK (atomic admission)")
    if not (split or wedged):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
