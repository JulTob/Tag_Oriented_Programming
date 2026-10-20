"""A scratch copy of an Agent's State holds every seat, and shares no container."""

import dataclasses
import unittest

from TopKit.state import _State
from TopKit.state import _Tag_Identity_Map


class Host:
    pass


SENTINEL = object()


def a_state_with_every_seat_filled():
    state = _State(host_type=Host)
    for seat in dataclasses.fields(_State):
        current = getattr(state, seat.name)
        if isinstance(current, list):
            current.append(SENTINEL)
        elif isinstance(current, set):
            current.add("name")
        elif isinstance(current, dict):
            current["name"] = SENTINEL
        elif isinstance(current, _Tag_Identity_Map):
            current[Host] = SENTINEL
    state.pinned = Host
    state.restored = frozenset({"restored"})
    state.composing = 3
    state.checking = True
    state.words = SENTINEL
    return state


class StateCopyTests(unittest.TestCase):
    def test_the_copy_holds_every_seat_of_the_state(self):
        state = a_state_with_every_seat_filled()
        copy = state.Copy()
        for seat in dataclasses.fields(_State):
            with self.subTest(seat=seat.name):
                self.assertEqual(getattr(copy, seat.name), getattr(state, seat.name))

    def test_the_copy_shares_no_container_with_the_state(self):
        state = a_state_with_every_seat_filled()
        copy = state.Copy()
        for seat in dataclasses.fields(_State):
            held = getattr(state, seat.name)
            if isinstance(held, (list, set, dict, _Tag_Identity_Map)):
                with self.subTest(seat=seat.name):
                    self.assertIsNot(getattr(copy, seat.name), held)

    def test_changing_the_copy_leaves_the_state_alone(self):
        state = a_state_with_every_seat_filled()
        before = {seat.name: _snapshot(getattr(state, seat.name)) for seat in dataclasses.fields(_State)}
        copy = state.Copy()
        for seat in dataclasses.fields(_State):
            held = getattr(copy, seat.name)
            if isinstance(held, list):
                held.append("added")
            elif isinstance(held, set):
                held.add("added")
            elif isinstance(held, dict):
                held["added"] = SENTINEL
            elif isinstance(held, _Tag_Identity_Map):
                held[Added] = SENTINEL
        for seat in dataclasses.fields(_State):
            with self.subTest(seat=seat.name):
                self.assertEqual(_snapshot(getattr(state, seat.name)), before[seat.name])


def _snapshot(held):
    if isinstance(held, (list, set, dict)):
        return type(held)(held)
    if isinstance(held, _Tag_Identity_Map):
        return held.copy()
    return held


class Added:
    pass


if __name__ == "__main__":
    unittest.main()
