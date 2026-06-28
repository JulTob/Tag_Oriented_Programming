# TagKit Implementation Notes

Optimization + semantics pass over `TagKit/TagKit.py`, `TagKit/__init__.py`,
and `tests/test_tagkit.py`. The guide was not edited.

**Test result: 44 tests, all passing** (`PYTHONPATH=. python3 -m unittest
tests.test_tagkit`).

---

## 1. Underlay syntax: explicit `@Underlay` only (backcompat removed)

The implicit "second positional parameter literally named `underlay`"
convention is gone. Extension is declared explicitly:

```python
class Paladin(Person):
    @Underlay
    def Attack(agent, past):        # name the underlay anything you like
        return past() + " with a holy oath."
```

- `@Underlay` marks an Action **or** Record as extending the prior visible
  contribution; the captured underlay arrives as the second positional
  parameter under whatever name the author chooses. Decorators mark the
  first parameter as the `agent` (self-like) binding by convention.
- Stacks with `@Action` / `@Record` in either order.
- A function marked `@Underlay` with fewer than two positional parameters
  raises `TagResolutionError` (clear diagnostic, raised once).
- The verdict is cached per function (`_underlay_cache`), so `signature()`
  is inspected at most once per declaration rather than per application.

## 2. Active reapply is a strict no-op

Re-applying a Tag that is already active does **nothing**: Records are not
reset and Imprints do not re-run. The previous "crunch" behaviour and the
`is_root` machinery were removed. Rationale (your call): in a complex
system a Tag is far more likely to be re-applied by accident than as a
deliberate reset, so reset must be explicit — `Rip` then apply again.
Re-applying a Tag that was previously Ripped is still a full fresh
application (Imprint runs again).

## 3. Exit protocols: `__del__`, `Scope`, `At_Exit`

"Deletion always Rips on `del`" is now implemented, with honest tiers:

- **`__del__` (best-effort).** When an Agent is garbage-collected, its
  still-active `@Rip` teardown Actions run (reverse application order).
  The teardown's value is its outside-world side effect (release a lock,
  revoke a token, log) — mutating the dying Agent is moot. The whole
  finalizer body is guarded, so a dying Agent never raises, even at
  interpreter shutdown when module globals are torn down. A host
  `__del__` shadowed by `Tagged.__del__` is still called (`_host_finalizer`).
  Caveat: Python does **not** guarantee `__del__` at interpreter shutdown
  or inside reference cycles — so for anything critical, use:
- **`Scope(agent, *tags)` (guaranteed).** Context manager: applies on
  entry, Rips in reverse on exit via `try/finally`, so teardown runs
  even if the block raises. This is the robust path for security-style
  exit protocols.
- **`At_Exit(agent)` (best-effort, opt-in).** Registers the Agent's
  teardown to also run at normal interpreter exit. Registration is **weak**
  (a `weakref`), so it never keeps the Agent alive.

A `ripped` flag on the Agent state makes teardown run at most once, so an
explicit `Rip` followed by collection does not double-fire.

## API verbs: Tags are Ripped, Records are deleted

`Clear` was removed (it overloads "empty everything" and "approved", and
collides with names users will want). The only Tag-extraction verb is
`Tag.Rip(agent)`. Records are removed with the language's own
`del agent.record` — TOP adds no verb. `Tagged.__getattribute__` resolves a
Record name to its Agent instance value only, so after `del` the name is
absent (and re-assignable), never the Tag-class builder method that the
runtime MRO would otherwise reveal.

## Application inputs to protocols

`Tag(target, **inputs)` passes keyword inputs to every Imprint, Precondition
and Postcondition applied during that call. Each protocol receives the inputs
whose names match its parameters; a declared parameter the caller did not
supply is passed as `None` — the application call is the single source of
truth (a function default is not consulted). Inputs propagate to Bases too,
so any Imprint in the chain that declares `code` gets it; unknown inputs are
ignored (an input meant for one Tag must not break another).

    MI6(bond, code="007")   # every Imprint that declares `code` receives "007"

The Agent binding is the first positional parameter and its name is the
author's free choice — `agent` is a convention, never a reserved word (no
second `self`). The per-function parameter spec is cached.

## 4. Resource optimizations (no wasted work)

- **Shared runtime types.** Previously every Tag application synthesized a
  fresh Python type per Agent. Now, when a composition contributes no
  special-method (dunder) Action, the runtime type is a pure `isinstance`
  marker depending only on `(host, leaves)` and is **shared** across every
  Agent of that shape via a `WeakValueDictionary`. Measured: 2000 agents of
  the same shape now share **1** runtime type instead of 2000. Ordinary
  (non-dunder) Actions resolve through `Tagged.__getattribute__` and never
  need to live on the type, so the marker carries nothing but the MRO.
  Compositions that *do* define a special-method Action still get a
  per-Agent type (that behaviour has to live on the type).
- **Cached declarations.** `_declarations_for` scans a Tag's `__dict__`
  once per Tag class (`WeakKeyDictionary`), not once per application.
- All caches are weakly keyed/valued, so dynamically created Tags,
  functions, and runtime types are not pinned in memory.

## 5. Cleanup

- Removed the unused `TypeVar` import.
- Removed the dead `Action = Callable[...]` type alias that was shadowed by
  the `Action` decorator; `Action` now unambiguously means the decorator.
- Added `Scope`, `At_Exit` to `__all__` and the package `__init__`.

---

## Decisions / edge cases (judgment calls)

- **`in` vs `isinstance` (IS vs HAS-BEEN) — now reliable.** `agent in Tag`
  is the IS check (current Field membership); it becomes `False` immediately
  after `Rip`. `isinstance(agent, Tag)` is the HAS-BEEN check: a per-Agent
  `ever_tags` set records every Tag ever applied, and
  `MetaTag.__instancecheck__` consults it, so isinstance stays `True` after
  `Rip` and through later re-composition ("ever an X, always an X"). It is a
  deliberate, dependable signal now — useful for spotting rogue / expelled
  Agents — rather than the fragile artifact it was. (OOP-flavoured rather
  than pure TOP, kept because it is genuinely handy. A failed tagging rolls
  `ever_tags` back atomically, so only committed memberships count.)
- **Reapply/Imprint:** active reapply = no-op; post-Rip reapply = fresh
  (see §2).
- **Raw side-effect limit (unchanged):** atomic rollback restores
  TOP-managed state, but cannot undo an Imprint's in-place mutation of a
  pre-existing mutable (e.g. `events.append`). Use a `@Rip`/Record for
  reversible state.
- **Thread-safety:** not addressed. Application, Fields, and Agent state
  mutate without locks; TOP assumes single-threaded use per Agent. Flag for
  later if concurrency becomes a requirement.

## Divergences between guide and implementation (guide unedited)

1. **"Reapplying an active Tag does nothing"** — now **matches** the code
   again (no-op reapply). Convergence; no guide change needed here.
2. **Underlay examples** in the guide (e.g. `class Elf(Person): def
   Attack(agent, underlay)`) now need an explicit `@Underlay`, or they read
   as plain replace-Actions. Update the guide's code examples.
3. **`@Rip` on `del`** is now real and best-effort; the guide can state the
   three tiers (`__del__` best-effort / `Scope` guaranteed / `At_Exit`
   opt-in) and the shutdown/cycle caveat.
4. **`Scope` / `At_Exit`** are new public API not yet described in the guide.
5. **Imprints with inputs** — the guide's intent (e.g. `MI6(bond, code="007")`
   feeding an Imprint's `code`) now works for real, spelled
   `@Imprint def recruit(agent, code): ...` with the value passed at
   application. The `@Rip(agent, status=None)` decorator-with-args pseudocode
   still differs from the method-marking API (`@Rip def teardown(agent): ...`).
6. **`bond = Person("Bond James Bond")`** — the guide constructs an Agent by
   applying a Tag to a raw string. The kit tags an *existing* host object;
   strings / immutables cannot carry TOP state. Use a host object
   (`bond = Hero("Bond"); Person(bond)`), then `MI6(bond, code="007")`.
