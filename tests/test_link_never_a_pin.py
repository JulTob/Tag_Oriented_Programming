"""One Agent's Link and a Pair are never Pins (§1.9).

Both hold objects: a Link holds its owner's contacts, a Pair holds its
two ends. A Pin's Field holds Tags. So the kit refuses the mark at once,
read from the class's own slot: empty or full, idle or mid-linking.
"""

import unittest

from TopKit import Link, Pin, Pre, Record, Tag, TagDeclarationError
from TopKit.declarations import _is_pin_physical
from TopKit.links import _pair_tag


class Character:
    def __init__(character, name):
        character.name = name


class Social(Tag):
    @Link
    class Knows(Tag):
        @Record
        def since(agent, contact, *, since=None):
            return since


class Link_Never_A_Pin_Tests(unittest.TestCase):
    def test_an_empty_link_is_never_a_pin(self):
        ruth = Character("Ruth")
        Social(ruth)                                      # Ruth's Link exists, nobody in it yet
        with self.assertRaises(TagDeclarationError):
            Pin(ruth.Knows)
        self.assertFalse(_is_pin_physical(ruth.Knows))

    def test_a_link_is_never_a_pin_while_it_is_linking(self):
        refusals = []

        class Watchful(Tag):
            @Link
            class Knows(Tag):
                @Pre
                def Try_To_Pin(agent, contact):
                    try:
                        Pin(agent.Knows)                  # a hook runs mid-linking
                    except TagDeclarationError:
                        refusals.append(contact)
                    return True

        charlie, bob = Character("Charlie"), Character("Bob")
        Watchful(charlie)
        charlie.Knows(bob)
        self.assertEqual(refusals, [bob])
        self.assertFalse(_is_pin_physical(charlie.Knows))
        self.assertIn(bob, charlie.Knows)

    def test_a_pair_is_never_a_pin(self):
        pair_tag = _pair_tag(Social.Knows)
        with self.assertRaises(TagDeclarationError):
            Pin(pair_tag)
        self.assertFalse(_is_pin_physical(pair_tag))


if __name__ == "__main__":
    unittest.main()
