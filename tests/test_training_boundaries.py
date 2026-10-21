"""Structural preparation and the training/admission diagnostic boundary."""

import unittest
import warnings
from unittest.mock import patch

from TopKit import (Action, Constant, Imprint, Post, Pre, Record, Tag,
                    TagCompositionError, TagPostconditionError,
                    TagPreconditionError, TagTargetError, TagTrainingWarning)
from TopKit.state import _state_of
from TopKit.transactions import _inspect


class Host:
    pass


class TrainingBoundaryTests(unittest.TestCase):
    def test_all_record_spaces_are_preflighted_before_gate_or_earlier_action(self):
        events = []

        class Slotted:
            __slots__ = ('wheels', '__dict__', '__weakref__')

        class Car(Tag):
            @Pre
            def Suitable(agent):
                events.append('pre')
                return True

            @Action
            def Start(agent):
                return 'running'

            @Record
            def wheels(agent):
                events.append('record')
                return 4

        target = Slotted()
        target.wheels = 'host value'
        original_namespace = vars(target)
        with self.assertRaisesRegex(TagTargetError, r'Car.wheels.*Record space'):
            Car(target)
        self.assertIsInstance(TagTargetError(), TagCompositionError)
        self.assertEqual(events, [])
        self.assertIs(type(target), Slotted)
        self.assertIs(vars(target), original_namespace)
        self.assertEqual(vars(target), {})
        self.assertEqual(target.wheels, 'host value')
        self.assertIsNone(_state_of(target))

    def test_failed_first_host_actualization_is_target_error_with_original_cause(self):
        cause = RuntimeError('host refuses the Agent runtime')

        class Restricted:
            def __setattr__(self, name, value):
                if name == '__class__':
                    raise cause
                object.__setattr__(self, name, value)

        class Car(Tag):
            pass

        target = Restricted()
        namespace = vars(target)
        with self.assertRaises(TagTargetError) as raised:
            Car(target)
        self.assertIs(raised.exception.__cause__, cause)
        self.assertIs(type(target), Restricted)
        self.assertIs(vars(target), namespace)
        self.assertEqual(vars(target), {})

    def test_each_completed_tag_checks_posts_before_later_shape_gate(self):
        events = []

        class Car(Tag):
            @Post
            def Ignites(agent):
                return False

        class Electric(Car):
            @Pre
            def Suitable(agent):
                events.append('gate')
                return True

            @Imprint
            def Repair(agent):
                events.append('repair')

        target = Host()
        with self.assertRaises(TagPostconditionError.Ignites):
            Electric(target)
        self.assertEqual(events, [])
        self.assertIn(target, Car[:])
        self.assertNotIn(target, Electric[:])

    def test_all_posts_share_one_query_scope_and_reuse_reached_verdicts(self):
        calls = []

        class Car(Tag):
            @Post
            def First(agent):
                return agent.Second

            @Post
            def Second(agent):
                calls.append('second')
                return True

        target = Host()
        Car(target)
        self.assertEqual(calls, ['second'])
        self.assertTrue(target)
        self.assertEqual(calls, ['second', 'second'])

    def test_refused_initial_gate_preserves_original_dictionary_object(self):
        class Refused(Tag):
            @Pre
            def Suitable(agent):
                return False

        target = Host()
        marker = target.marker = object()
        original_namespace = vars(target)
        with self.assertRaises(TagPreconditionError.Suitable):
            Refused(target)
        self.assertIs(type(target), Host)
        self.assertIs(vars(target), original_namespace)
        self.assertEqual(vars(target), {'marker': marker})
        self.assertIsNone(_state_of(target))



    def test_record_guard_representation_failure_warns_and_later_training_runs(self):
        events = []

        class Refusing(type):
            def __new__(metaclass, name, bases, namespace):
                if 'locked' in namespace:
                    raise RuntimeError('guarded Record rejected')
                return super().__new__(metaclass, name, bases, namespace)

        class Restricted(metaclass=Refusing):
            pass

        class Car(Tag):
            @Record
            def earlier(agent):
                return 1

            @Constant
            @Record
            def locked(agent):
                return 2

            @Record
            def later(agent):
                return 'locked' @ agent

            @Imprint
            def Train(agent):
                events.append('trained')

        target = Restricted()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', TagTrainingWarning)
            self.assertIs(Car(target), target)
        self.assertIn(target, Car[:])
        self.assertEqual(target.earlier, 1)
        self.assertFalse('locked' @ target)
        self.assertFalse(target.later)
        self.assertEqual(events, ['trained'])
        self.assertEqual([item.message.name for item in caught], ['locked'])
        self.assertIn('could not be applied', str(caught[0].message.failure))

    def test_record_guard_representation_interruption_stops_training_but_admits(self):
        interruption = KeyboardInterrupt('stop guarded Record application')
        events = []

        class Refusing(type):
            def __new__(metaclass, name, bases, namespace):
                if 'locked' in namespace:
                    raise interruption
                return super().__new__(metaclass, name, bases, namespace)

        class Restricted(metaclass=Refusing):
            pass

        class Car(Tag):
            @Record
            def earlier(agent):
                return 1

            @Post
            def Ready(agent):
                events.append('post')
                return True

            @Constant
            @Record
            def locked(agent):
                return 2

            @Imprint
            def Train(agent):
                events.append('trained')

        target = Restricted()
        with self.assertRaises(KeyboardInterrupt) as raised:
            Car(target)
        self.assertIs(raised.exception, interruption)
        self.assertIn(target, Car[:])
        self.assertEqual(target.earlier, 1)
        self.assertFalse('locked' @ target)
        self.assertEqual(events, ['post'])

    def test_hostile_record_diagnostic_cannot_apply_another_tag(self):
        events = []

        class Intruder(Tag):
            @Imprint
            def Enter(agent):
                events.append('intruder')

        target = Host()

        class HostileError(Exception):
            def __str__(self):
                Intruder(target)
                return 'unexpected'

        class Car(Tag):
            @Record
            def wheels(agent):
                raise HostileError()

            @Imprint
            def Continue(agent):
                events.append('continue')

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', TagTrainingWarning)
            self.assertIs(Car(target), target)
        self.assertEqual(events, ['continue'])
        self.assertNotIn(target, Intruder[:])
        self.assertIn(target, Car[:])
        self.assertEqual([item.message.name for item in caught], ['wheels'])
        self.assertIn('read-only boundary', str(caught[0].message.failure))
        self.assertFalse('wheels' @ target)

    def test_retained_constant_post_diagnostic_names_its_tag_layer(self):
        class NDA(Tag):
            @Constant
            @Post
            def Confidential(agent):
                return agent.secret_kept

        target = Host()
        target.secret_kept = True
        NDA(target)
        del NDA[target]
        target.secret_kept = False
        with self.assertRaises(TagPostconditionError.Confidential) as raised:
            _inspect(target)
        self.assertEqual(raised.exception.layer_provenance,
                         (('NDA', True, False, False),))
        self.assertIn('Constant Post underlay retained after Rip: NDA',
                      '\n'.join(raised.exception.__notes__))


if __name__ == '__main__':
    unittest.main()
