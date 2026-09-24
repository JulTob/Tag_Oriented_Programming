# STEP-SPEC-17: A Flag's Words

- **STEP:** SPEC-17
- **Desk:** spec
- **Title:** A Flag's Words
- **Author:** Julio Toboso (@JulTob)
- **Status:** Vetting
- **Created:** 2026-09-24

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

`@Flag` takes the words a Tag also answers to. `@Flag("Wolf",
"Lycanthrope")` over `class Werewolf` makes `"Wolf" in howler` and
`Keyword(howler, "Lycanthrope")` True while Werewolf is active, beside its
own name. A word is only a word: it answers `in` and `Keyword`, never
membership. Bare `@Flag` is unchanged.

## Motivation

A rule written as data names a word, and the word is not always the Tag's
name. Tables say *Wolf* where the program says `Werewolf`; one table says
*Lycanthrope*, another *Beast*. Under STEP-SPEC-7 a Tag answers to exactly
one word, its name, so each variant needed a Tag of its own, with a Field,
a place in the Form and a class nobody reads.

Some neighbours already have a home. A Flag Base answers for its Shapes,
because the Base is active (§0.3):

```python
@Flag
class Beast(Tag): pass

@Flag
class Werewolf(Beast): pass

Werewolf(howler)
assert "Beast" in howler            # already true under STEP-SPEC-7
```

That is right when *Beast* is a category the program walks, gates or
promises on. It is too heavy for a variant that rules only match. The gap
is the variant: a word with no Field behind it.

## Specification

1. `@Flag` takes zero or more words: `@Flag("Wolf", "Lycanthrope")`. Bare
   `@Flag` and `@Flag()` mark the Tag with its name alone.
2. **The name always flags.** A Flag answers to its own name and to every
   word it lists. There is no spelling that leaves the name out.
3. While an Agent carries an active Tag that is a Flag listing a word,
   `word in agent` and `Keyword(agent, word)` are True. Words match
   exactly, like names.
4. **A word is not membership.** `"Beast" in howler` may be True while
   `howler in Beast` is False and `Beast in howler` is False. A word that
   names another Tag is accepted, and says nothing about that Tag's
   Field. The class form, `Werewolf in howler`, still asks for the active
   Flag itself.
5. **Many Tags may share a word.** It answers while any of them is active.
6. **The words are the Tag's own.** A Shape does not inherit being a Flag
   or its words; it answers its Base's words because the Base is active.
   A Shape that is a Flag itself adds its own.
7. Stacked `@Flag` marks add their words together.
8. Words are non-empty strings, and a probe is read as its text. Anything
   else among the words, including a class beside them (`@Flag(Beast,
   "Wolf")`), is a Declaration Failure at the decorator; nothing is
   marked. A lone class is the bare form applied to that class:
   `@Flag(Beast)` over another class marks `Beast` itself and then
   applies `Beast` to the new class. No kit can tell that from `Flag(Beast)`
   called on its own, so the Guide says it: a word is the string
   `"Beast"`, never the class.
9. **Flag Pins** answer their words on the Tag: `@Pin @Flag("Obsolete")
   class Deprecated` gives `"Obsolete" in Wizard` while `Deprecated(Wizard)`
   holds, by the rule of §1.9.
10. Every other rule of §1.8 stands: Flags are opt-in, ordinary Tags are
    never found by name, and a Flag on a host that owns `in` is refused.

```python
@Flag("Wolf", "Lycanthrope")
class Werewolf(Tag):
    pass

Werewolf(howler)

assert "Wolf" in howler              # a word
assert "Werewolf" in howler          # the name always flags
assert Werewolf in howler            # the class form is unchanged
assert Keyword(howler, "Lycanthrope")
```

## Rationale

**A decorator argument, not a member.** The words are what the Tag is
called, fixed when the Tag is declared, and they belong at the top of the
class next to its name. A Record would make them per-Agent state that
flips without a tagging or a Rip, which is what §1.9 argues a keyword
must not do ("a value implies it may be flipped back"). A Report would
work, but runs lazily and can be reassigned, and adds nothing: decorator
arguments are ordinary expressions, so `@Flag(*Load_Words("werewolf"))`
still reads a vocabulary from data, and Shapes already answer their
Bases' words through the Form.

**The secret identity.** A word answering where membership does not is
the feature, not a leak. The word is the public name the Agent goes by in
the rules; membership is what the Agent is. The Director: "This would
also allow for flag behaviour different from tag membership, which is
the 'Alias' behavior. It feels a lot like an agent having an alias or a
secret identity. The public persona has a public behavior." When a word
needs a Field, a gate or a promise, it should be a Tag and a Base; when
rules only match it, a word is enough. The Guide says so.

**Explicit variants.** STEP-SPEC-7 rejected case-insensitive names as
magical. A listed word is the explicit form of the same wish: the author
writes each variant the rules may use.

## Backwards compatibility

None broken. Bare `@Flag` means what it meant. `Flag("Wolf")` was a
Declaration Failure before and is a decorator now.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| `@Flag` on a member returning the words (a Record) | Set aside: per-Agent state; keywords would flip without a tagging, against §1.9 |
| `@Flag` on a `@Report` returning the words | Set aside: lazy and reassignable, and adds nothing an argument cannot say |
| Neighbours only as Flag Bases | Kept for categories; too heavy for a variant that rules only match |
| Refuse a word that names another Flag | Rejected by the Director: "a reasonable and expected behaviour. We should accept the risk, and let the programmers use their heads a little bit" |
| A spelling that drops the Tag's name | Rejected by the Director: "The tag name always flags. It makes no sense to use Flag otherwise" |
| Shapes inherit their Base's words | Unnecessary: the Base is active and answers them; inheriting would also make every Shape of a Flag a Flag, which STEP-SPEC-7 does not do |

## Acceptance requirements

Covered by `tests/test_topkit.py::FlagWordTests`, by the §1.8 and §1.9
examples in `tests/spec_examples.py`, by Pattern 7 of the Guide, and by
the oracle (`tests/oracle_topkit.py`, `Assert_Keywords`), which checks
every name, word and class of a Family after every transition: a word
shared by two Tags, a word that names another Flag, words through the
Form, on Agents and on pinned Tags.

Building it found a TopKit defect in STEP-SPEC-7: a Flag applied to an
Agent that already carried another Tag did not take the Agent's `in`.
Fixed with this STEP; `FlagWordTests` and the oracle cover it. The fix
rebuilds the Agent's runtime type when a Flag lands, and that exposed an
older defect: a rebuild dropped the gate of a name a Tag had deleted and
a later Layer stored again, so the host's property came back over the
Layer's Action (a Postcondition did the same before this STEP). The gate
now survives any rebuild; `RestoredNameTests` covers it.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-24, per
> the Director's review: "I love the @Flag(names) over the tag. [...]
> Let's apply that." A word that names another Tag is accepted as the
> alias behaviour; the Tag's name always flags; Flag Pins answer their
> words on the Tag.
