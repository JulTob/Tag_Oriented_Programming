# STEP-SPEC-18: Deletion in Layers

- **STEP:** SPEC-18
- **Desk:** spec
- **Title:** Deletion in Layers
- **Author:** Julio Toboso (@JulTob)
- **Status:** Vetting
- **Created:** 2026-09-29

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

An Agent's `__del__` is a member of its Overlay like any Action. The
host's own finalizer is its first Layer. A Tag's `__del__` replaces the
Layers beneath it, or with `@Underlay` extends them, and `@Delete`
removes them. When an Agent is deleted, it first leaves its Tags (every
`@Rip` teardown runs), then its `__del__` runs as the Overlay shows it.
When nothing is stated, that is the host's own `__del__`. At interpreter
exit only the `__del__` Layers run; teardowns there stay opt-in through
`At_Exit`.

## Motivation

Found in the performance work (PERFORMANCE-2026-09-24.md, §5.6). Tagging
took behaviour away from the host at its end:

```python
class Door:
    def __del__(self): print("the door's own __del__")

plain = Door()                     # at exit: prints
guarded = Door(); Guard(guarded)   # at exit: prints nothing
```

The kit's finalizer imported its teardown runner at call time. At
interpreter exit that import fails, and the finalizer swallowed the error
and skipped everything after it, the host's own `__del__` included. §0.1
promises that every method the Target had keeps working unless a Tag
deliberately contributes a member of that name. Here no Tag had.

A Tag that did contribute a `__del__` broke deletion in other ways. A
plain `def __del__` replaced the kit's finalizer, so no `@Rip` teardown ran
when the Agent was collected. An `@Underlay def __del__` reached the
host's finalizer but still skipped the teardowns. `@Delete def __del__`
left a gate where the finalizer should be, and nothing ran at all.

The Director: "then it should del in layers, as an overlay. We should be
able to overrun it, but if nothing is stated, just overlay the del with a
call to the underlaying del."

## Specification

1. **`__del__` is a member of the Overlay.** The host's own `__del__` is
   its first Layer, found as the language finds it (in Python: the first
   class that defines it decides, `None` means none, a descriptor is
   bound, and one added after tagging counts). A Tag's `__del__` without `@Underlay` replaces the
   Layers beneath it; with `@Underlay` it receives them as a callable and
   decides when to call them. `@Delete` removes them (§1.6). The ordinary
   rules of §1.2 hold: replacing an independent Tag's `__del__` without an
   Underlay is diagnosed, and the Layer is sticky after its Tag is Ripped.
2. **With nothing stated, the host's own `__del__` runs**, exactly as it
   would for the untagged object.
3. **The Layer beneath a `__del__` is always callable.** Where the host
   has no finalizer, or a Tag deleted it, calling it does nothing, so
   `@Underlay def __del__(agent, underlay): ...; underlay()` is safe on
   any host.
4. **Deletion order.** When the Agent is collected, every teardown still
   due runs, best effort (§3.1). Then its `__del__` runs as the Overlay
   shows it, top Layer first. Both run inside the composition door
   (§1.5), so a Tag's teardown and Layer read its own `@Secret` members.
5. **A `__del__` never stops a teardown,** and a teardown never stops the
   Layers. Replacing the `__del__` Layers replaces only them; running the
   teardowns is a protocol of its own (§3.2), so no Tag can skip another
   Tag's teardown. A teardown interrupted by the language (a `Ctrl-C`) does
   not skip the Layers; the interruption is reported after them.
6. **At interpreter exit** only the `__del__` Layers run. Teardowns at
   exit stay opt-in: `At_Exit` runs them while the interpreter is still
   whole. Every teardown still runs at most once, whichever tier reaches
   it first.
7. **A `__del__` Layer's own error** is reported the way the language
   reports any finalizer's error (in Python, through
   `sys.unraisablehook`). The kit no longer swallows it. The kit's own
   best-effort work (the teardowns) stays silent, as §3.2 says.
8. **`@Rip` on `__del__` is a Declaration Failure.** A `__del__` Layer
   already runs at deletion; as a teardown too it would run twice.
9. **The language calls `__del__`, not the program.** In Python the
   finalizer must be found on the runtime type, so `agent.__del__` always
   reads the kit's finalizer, whatever the Layers are, even after
   `@Delete`. Calling it by hand runs the whole deletion, teardowns
   included, while the Agent is still a member: end an Agent with `del`,
   or a Rip instead. For a block, tag before `try` and Rip in `finally`;
   STEP-SPEC-31 supersedes this STEP's former `Scope` spelling.
10. **Known limits.** In a reference cycle the language may clear weak
    references before finalizers run (Python does), so a teardown or a
    Layer that calls one of the Agent's own Actions there fails. Late in
    interpreter exit, after the kit's own modules are cleared, the Layers
    still run and still reach the host's own `__del__`, but a Layer that
    reads a member the kit gates (a `@Secret`, a view or a condition by
    name, a published member) may fail there.

```python
class Lantern:
    def __del__(self):
        print("wick out")                  # the first Layer

class Carried(Tag):
    @Rip
    def Put_Down(agent):
        print("put down")                  # a teardown: runs first

class Enchanted(Tag):
    @Underlay
    def __del__(agent, underlay):          # a Layer over the host's own
        print("spell fades")
        underlay()

lamp = Lantern()
Carried(lamp)
Enchanted(lamp)
del lamp          # put down / spell fades / wick out
```

## Rationale

**One rule, not a special case.** Actions already compose in Layers: the
latest contribution is visible, `@Underlay` reaches the one beneath, and
`@Delete` frees the name. `__del__` is a method like any other, so it
follows the same rule. The one thing it cannot be is the kit's own entry
point, because Python calls a type's `__del__` directly. So the finalizer
stays on the runtime type and serves the Agent's `__del__` Layers after
the teardowns.

**Teardowns are not a Layer.** Leaving the Tags belongs to the Tags; the
`__del__` belongs to the object. Letting a `__del__` skip teardowns would
let one Tag break another's clean-up, which §3.1 rules out ("every one of
them").

**Why nothing at exit but the Layers.** An untagged object's `__del__`
runs at exit, so the tagged one's must too (§0.1). Teardowns at exit
would run while the interpreter is half shut down, where a teardown that
uses other modules can fail without a word, and many programs would print
new output at exit. `At_Exit` already offers them, at a safer moment.

## Backwards compatibility

- A tagged object's own `__del__` now runs at interpreter exit, as it
  does untagged. (Before, it ran only when a Tag's `@Underlay __del__`
  sat over it on the runtime type.)
- A Tag's `__del__` no longer stops the teardowns.
- `@Delete def __del__` no longer stops the teardowns.
- An error raised by a host's `__del__` is now reported (on stderr,
  through `sys.unraisablehook`) instead of being swallowed. A Tag's
  `__del__` errors were already reported, and still are.
- Teardowns of Agents collected as cyclic garbage during interpreter exit
  no longer run (before, they ran when that collection came while the
  kit's modules were still loaded); `At_Exit` runs them, while the
  interpreter is whole.
- `@Rip def __del__` is refused; `agent.__del__` reads the kit's
  finalizer where it used to read a Tag's Layer or, after `@Delete`, raise
  `AttributeError`.
- Agents whose only difference is their `__del__` Layers, deleted ones
  included, now share a runtime type.
- A host class that subclasses `Tagged` but cannot be subclassed itself
  (an `Enum`, a class whose `__init_subclass__` refuses) is now refused at
  its first tagging, as any such host already was; before, it was tagged
  in place and kept its own class.
- Fixed with it: an object built from an Agent's runtime type
  (`dataclasses.replace`, `type(self)(...)`) is tagged as a plain host,
  and one that is never tagged runs its own `__del__`; a
  host class that subclasses `Tagged` gets its runtime type at the first
  tagging, and with it the finalizer (and views by name and format specs,
  which it also lacked until a Tag brought a type-level fact); the
  finalizer works late in interpreter exit, after the kit's modules are
  cleared.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Run the host's own `__del__` at exit and change nothing else | Set aside by the Director in favour of Layers: a Tag must be able to overrun the finalizer |
| `__del__` Layers first, then the teardowns | Rejected by the Director: the Agent leaves its Tags first, as the kit already did for the host's finalizer |
| A replacing `__del__` owns the whole deletion, teardowns included | Rejected by the Director: one Tag could break another's clean-up |
| Teardowns also at interpreter exit, best effort | Rejected by the Director: they stay opt-in through `At_Exit` |
| An `@Underlay` with nothing beneath is an error, as for other Actions | Set aside: every object can be finalized, so "nothing" is a valid Layer beneath a finalizer |

## Acceptance requirements

Covered by `tests/test_topkit.py::LayeredDeletionTests`, including real
interpreter exits in a subprocess (one of them late, after the kit's
modules are cleared), and by the existing `ExitProtocolTests`. Two
rounds of adversarial verification (kernel edge cases, a differential
fuzz against `main`, a docs-and-tests lens, then the fixed code and a
mutation lens) found eleven defects in the first draft and seven in the
fixes; each is fixed here and pinned by a test, and every mutation that
undid a fix now fails a test.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-29, per
> the Director's direction: "then it should del in layers, as an overlay.
> We should be able to overrun it, but if nothing is stated, just overlay
> the del with a call to the underlaying del"; with teardowns first, a
> `__del__` that never stops a teardown, and only the Layers at exit.
