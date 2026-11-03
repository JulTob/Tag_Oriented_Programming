"""STEP_WORDS for formal/tagging_admission (used by formal/run.py trace printer)."""

STEP_WORDS = {
    "GateRefuse": "Gate refuses the turn (Precondition fails): turn ends, nothing installed",
    "GatePass": "Gate passes the turn",
    "GainFail": "a Record builder raises (Gainings failure): Gains kept, no membership",
    "GainOK": "Gainings complete",
    "ImprintFail": "an Imprint raises: Gains kept, no membership",
    "ImprintOK": "Imprints finish",
    "InterruptInTraining": "KeyboardInterrupt inside Gainings/Imprints (same boundary as failure)",
    "FieldAdd": "field._Add(agent): Field entry, no active/history yet",
    "InterruptAfterAdd": "KeyboardInterrupt between field._Add and state.active.append (TA-2 phantom)",
    "AddActive": "state.active.append(tag)",
    "InterruptAfterActive": "KeyboardInterrupt between state.active.append and state.ever.add",
    "AddEver": "state.ever.add(tag): history established",
    "PostsPass": "Posts hold (sound)",
    "PostsFail": "a Post fails after admission (defective, membership stays)",
    "Retry": "retry starts a fresh attempt at the failed turn",
    "Done": "terminal: nothing left to do",
}
