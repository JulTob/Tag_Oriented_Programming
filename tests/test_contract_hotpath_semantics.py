"""Cheap Contract paths preserve observation cleanup and live membership."""

import gc
import unittest
import weakref

from TopKit import Tag, TagCompositionError
from TopKit.observations import _Observation, _refuse_observed_act
from TopKit.state import STATE


class Host:
    pass


class ContractHotPathTests(unittest.TestCase):
    def test_finished_observation_does_not_need_cyclic_gc(self):
        class TrackedObservation(_Observation):
            pass

        enabled = gc.isenabled()
        gc.disable()
        try:
            observation = TrackedObservation('Postcondition Ready')
            reference = weakref.ref(observation)
            with observation:
                pass
            del observation
            self.assertIsNone(reference())
        finally:
            if enabled:
                gc.enable()

    def test_reused_observation_does_not_keep_an_old_violation(self):
        observation = _Observation('Postcondition Ready')
        with self.assertRaises(TagCompositionError):
            with observation:
                _refuse_observed_act('Tagging')
        with observation:
            pass

    def test_membership_rechecks_after_no_post_state_lookup_callback(self):
        for rejoin in (False, True):
            with self.subTest(rejoin=rejoin):
                class Wizard(Tag):
                    pass

                target = Host()

                class LookupCallback(dict):
                    armed = False

                    def get(namespace, name, default=None):
                        value = dict.get(namespace, name, default)
                        if namespace.armed and name == STATE:
                            namespace.armed = False
                            del Wizard[target]
                            if rejoin:
                                Wizard(target)
                        return value

                target.__dict__ = LookupCallback()
                Wizard(target)
                target.__dict__.armed = True
                self.assertEqual(target in Wizard, rejoin)
                self.assertEqual(target in Wizard[:], rejoin)


if __name__ == '__main__':
    unittest.main()
