"""Pin Gainings invalidate the receiving Tag's current declaration memo."""

import unittest
import warnings

from TopKit import (Imprint, Pin, Public, Record, Tag, TagImprintError,
                    TagOverwriteWarning, TrainingWarning)


class Host:
    pass


class PinGainingMemoTests(unittest.TestCase):
    def test_unfinished_gains_do_not_reuse_the_receivers_published_projection(self):
        class Receiver(Tag):
            pass

        @Pin
        class Established(Tag):
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

        @Pin
        class Unfinished(Tag):
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

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Unfinished(Receiver)

        training, = [entry.message for entry in caught
                     if isinstance(entry.message, TrainingWarning)]
        self.assertIsInstance(training, TrainingWarning.Finish)
        self.assertEqual(training.cause_type, "ValueError")
        self.assertTrue(any(isinstance(entry.message, TagOverwriteWarning)
                            for entry in caught))
        self.assertEqual(observed, [(False, False)])
        self.assertIn(Receiver, Established)
        self.assertIn(Receiver, Unfinished[:])
        self.assertEqual(Receiver.Read(during_training), ("acquired", None))
        self.assertIs(Receiver.marker, None)

        future = Host()
        Receiver(future)
        self.assertTrue("Read" @ future)
        self.assertTrue("marker" @ future)
        self.assertEqual(future.Read(), ("acquired", None))
        self.assertIsNone(future.marker)


if __name__ == "__main__":
    unittest.main()
