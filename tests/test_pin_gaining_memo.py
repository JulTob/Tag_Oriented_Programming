"""Pin Gainings invalidate the receiving Tag's current declaration memo."""

import unittest

from TopKit import (Imprint, Pin, Public, Record, Tag, TagImprintError,
                    TagOverwriteWarning)


class Host:
    pass


class PinGainingMemoTests(unittest.TestCase):
    def test_unfinished_gains_do_not_reuse_the_receivers_published_projection(self):
        class Receiver(Tag):
            pass

        class Established(Pin):
            @Public
            def Read(tag, agent):
                return "original"

            @Public
            @Record
            def marker(tag):
                return False

        Established(Receiver)
        existing = Host()
        Receiver(existing)  # Prime the receiving Tag's declaration memo.
        self.assertEqual(existing.Read(), "original")
        self.assertIs(existing.marker, False)

        observed = []
        during_training = Host()

        class Unfinished(Pin):
            @Public
            def Read(tag, agent):
                return "acquired", tag.marker

            @Public
            @Record
            def marker(tag):
                return None

            @Imprint
            def Finish(tag):
                # The new direct Gains are present, but this unfinished
                # Pin has not published them onto the Receiver's Field.
                tag(during_training)
                observed.append((
                        "Read" @ during_training,
                        "marker" @ during_training,
                        ))
                raise ValueError("unfinished Pin")

        with self.assertWarns(TagOverwriteWarning):
            with self.assertRaises(TagImprintError.Finish) as raised:
                Unfinished(Receiver)

        self.assertIsInstance(raised.exception.__cause__, ValueError)
        self.assertEqual(observed, [(False, False)])
        self.assertIn(Receiver, Established)
        self.assertNotIn(Receiver, Unfinished[:])
        self.assertEqual(Receiver.Read(during_training), ("acquired", None))
        self.assertIs(Receiver.marker, None)

        future = Host()
        Receiver(future)
        self.assertFalse("Read" @ future)
        self.assertFalse("marker" @ future)


if __name__ == "__main__":
    unittest.main()
