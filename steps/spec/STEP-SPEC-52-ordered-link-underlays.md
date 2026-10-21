# STEP-SPEC-52: Ordered Link Underlays

- **STEP:** SPEC-52
- **Desk:** spec
- **Title:** Ordered Link Underlays
- **Author:** Codex, recording the Director's 2026-10-20 and 2026-10-21 rulings
- **Status:** Brief
- **Created:** 2026-10-20
- **Issue:** [#347](https://github.com/JulTob/Tag_Oriented_Programming/issues/347)
- **Related Brief:** [STEP-SPEC-51 / PR #352](https://github.com/JulTob/Tag_Oriented_Programming/pull/352)
- **Related runtime draft:** [STEP-SPEC-22 / PR #171](https://github.com/JulTob/Tag_Oriented_Programming/pull/171)

> One STEP, one topic. This Brief proposes how a Link declaration writes the
> ordered Form that runs before its own Pair training. STEP-SPEC-51 separately
> defines who owns each actual Link Field and Pair.

## Summary

A Relation declares its two runtime seats and writes its ordered underlays in
the class header, using TOP's existing Form language:

```python
@Link(agent, contact)
class Trusts(Network, agent.Knows, contact.Knows, server.Registre):
    pass
```

`agent` and `contact` are symbolic Link seats. They are not objects captured
while the class is declared. When `ari.Trusts(ruth)` runs, TOP resolves the
header afresh and performs these complete Taggings in order:

```python
Network(ruth)
ari.Knows(ruth)
ruth.Knows(ari)
server.Registre(ruth)
ari.Trusts(ruth)
```

The class header is the language. The underlays are not repeated as a tuple
inside `@Link`, and they are not Python inheritance. Each turn keeps its own
Field, Pair, Gains, Services, Gate, Contract and Rip protocol. A bare Relation
name such as `Knows` is only a blueprint; an actual Link is reached through an
Agent seat or a particular Agent such as `server`.

## Motivation

An owner may know a Contact and then trust that Contact. Trust may also
require the Contact to enter a network, the Contact to know the owner in
return, and a server to register the Contact. These are ordered Tags, not one
shared object and not configuration passed to a decorator.

The rejected spelling

```python
@Link(underlays=(Network, Agent.Knows, server.Registre))
class Trusts(Tag):
    pass
```

hid TOP's layering in a keyword argument, invented an uppercase selector,
and omitted the Contact's own Link seat. It also preserved the older model in
which Relation bases described a shared Link family. This Brief replaces that
spelling; it was never Director-cleared behavior.

## Specification

1. **Every Relation names its seats.** A Relation is declared with
   `@Link(agent, contact)`. `agent` is the Agent whose actual Link receives the
   call; `contact` is the other Agent in that call. Bare `@Link` is refused.
   Protocol functions continue to receive the same two ordered inputs.
2. **The class header is the ordered Form.** Entries are resolved and applied
   from left to right. The selected actual Link runs after the header completes.
   The header is TOP syntax and must not grant Python MRO lookup, copy members,
   create `issubclass` promises, or join Link families.
3. **Ordinary Tag.** An ordinary Tag such as `Network` applies to the Contact:
   `Network(contact)`.
4. **Agent-seat Link.** `agent.Knows` resolves through the Agent seat and takes
   the opposite seat as its Contact. In `ari.Trusts(ruth)`, it means
   `ari.Knows(ruth)`.
5. **Contact-seat Link.** `contact.Knows` resolves through the Contact seat and
   also takes the opposite seat as its Contact. In `ari.Trusts(ruth)`, it means
   `ruth.Knows(ari)`. It is the declarative reciprocal Link; no reciprocal is
   otherwise implied.
6. **A particular Agent's Link.** `server.Registre` resolves that Agent's
   current actual Link and applies it to the Contact:
   `server.Registre(contact)`. The declaration stores a soft Agent-and-name
   reference, not the current Field, Pair, or a strong reference keeping the
   Agent alive.
7. **No bare Relation.** `Knows` alone is refused in the header. A Relation is
   a blueprint and owns no Field. `agent.Knows`, `contact.Knows`, and
   `server.Registre` identify actual Tags that can take a target.
8. **Complete independent turns.** Every header entry performs an ordinary
   complete Tagging with its own Gate, Gainings, Imprints, Field admission,
   Posts, diagnostics and recovery. A failed turn stops the sequence. Earlier
   completed turns remain complete under the ordinary Tagging law.
9. **Selected Link last.** After the header, TOP applies `ari.Trusts` to Ruth.
   Its Pair remains distinct from the Pair in `ari.Knows`, `ruth.Knows`, or
   `server.Registre`, even though some turns involve the same two Agents.
10. **Repeated admitted call.** Calling `ari.Trusts(ruth)` when Ruth is already
    admitted to that actual Link is the ordinary active-Tag no-op. It does not
    rerun the header merely because the Relation later changed. Rip Ruth from
    `ari.Trusts`, then link her again to run the current Form and training.

## Example

```python
from TopKit import Link, Report, Tag, agent, contact


class Network(Tag):
    pass


class Host:
    pass


server = Host()


class Registry(Tag):

    @Link(agent, contact)
    class Registre(Tag):
        pass


Registry(server)


class Social(Tag):

    @Link(agent, contact)
    class Knows(Tag):
        pass

    @Link(agent, contact)
    class Trusts(Network, agent.Knows, contact.Knows, server.Registre):

        @Report
        def trusted(link):
            return True


Social(ari)
Social(ruth)
ari.Trusts(ruth)
```

The Link call performs:

1. `Network(ruth)`;
2. `ari.Knows(ruth)`;
3. `ruth.Knows(ari)`;
4. `server.Registre(ruth)`; and
5. `ari.Trusts(ruth)`.

The Report belongs only to Ari's actual Trusts Link and is read through that
Link, for example `ari.Trusts[ruth].trusted`. It is not copied into Ari, Ruth,
Network, either Knows Link, or the server's Registre Link.

## Resolution and lifetime

Seat expressions are soft declarations. `agent.Knows` does not capture the
Agent that happened to exist when the Relation was written; each Link call
substitutes its own Agent. `contact.Knows` does the same with its Contact.
Two owners calling Trusts therefore resolve different actual Knows Links.

A concrete expression such as `server.Registre` also resolves live. The
Relation remembers `server` weakly and the coordinate `Registre`. If either
is no longer available, that turn fails clearly before the selected Trusts
Gate. A later Link at that coordinate is the one the next call uses.

Inputs supplied to the selected Link call are available to the turns through
the ordinary ordered-input abstraction. This STEP does not make Fields or
Pairs share storage, and it does not merge their protocols.

## Python profile boundary

The surface syntax uses a Python class header, but its meaning is TOP's
ordered Form. An implementation must consume symbolic seats before ordinary
Python base behavior can leak through. In particular it must not route these
entries into STEP-SPEC-22's Relation-extension bases, `_base_links`, shared
families, or Pair-Tag inheritance.

The lowercase `agent` and `contact` words are declaration-time symbolic seats
exported by TopKit. Their attribute selections are deferred until Link use.
An implementation may use Python's deferred-base facilities and original-base
metadata, but those are implementation mechanics rather than language
semantics. It must preserve source order and remove strong references to a
particular Agent after recording a soft Link coordinate.

The runtime mechanism needs its own focused implementation PR and tests. This
Brief records the language; it does not claim that the current Link draft can
already execute the spelling.

## Backwards compatibility

Links remain a Vetting design. PR #171 currently uses Relation class bases as
an inheritance-like extension system, joins actual Links into families, and
shares Pair training through those families. That is the old system and is
not the meaning of this header.

Before deployment, STEP-SPEC-22, tests, the Specification and Link guides must
be rewritten around explicit `@Link(agent, contact)` seats and independent
ordered Taggings. Existing bare `@Link` declarations must gain their two seat
words. No deployed user program relies on the draft spelling.

## Alternatives considered

| Alternative | Why this Brief sets it aside |
| --- | --- |
| `@Link(underlays=(...))` | Hides TOP layering in configuration, duplicates the class header and cannot express the Contact seat naturally. |
| `Agent.Knows` | Invents a type-like global selector instead of using the Link's declared `agent` seat. |
| Relation inheritance and shared Link families | Conflates independent Tags, Fields and Pairs; this is the old #171 model. |
| Put every preparatory call in an Imprint | Legal and sometimes useful, but it hides required Tagging order in procedure code and runs after the selected Link's Gate. |
| Treat `contact.Knows` as `contact.Knows(contact)` | Rejected: a seat-relative Link takes the opposite Link seat as its Contact; the useful symmetric reading is `ruth.Knows(ari)`. |
| Keep bare `@Link` | Rejected: both Link seats are part of the Relation declaration and should be explicit. |

## Acceptance requirements

- The exact form `@Link(agent, contact)` with ordered class-header underlays is
  accepted; tuple configuration and uppercase `Agent` are not the language.
- Every Relation explicitly names both seats; bare `@Link` is refused.
- An ordinary Tag applies to the Contact.
- `agent.Knows` means the Agent's actual Link applied to the Contact.
- `contact.Knows` means the Contact's actual Link applied to the Agent.
- A particular Agent's Link resolves softly and applies to the Contact without
  keeping that Agent alive.
- Header entries and the selected Link have independent Fields, Pairs, Gains,
  Services, Gates, Contracts and Rip state.
- A failed turn stops later turns without undoing completed earlier Taggings.
- Bare Relations are refused because they have no actual Field.
- Repeating an admitted Link is a no-op; Rip and link again runs the current
  ordered Form.
- The implementation proves that the header creates no Python inheritance,
  Link-family sharing, Pair reuse, or implicit reciprocal beyond an explicit
  Contact-seat selector.
- STEP-SPEC-22, the Specification, tests and Link guides agree before runtime
  deployment.

---

### Decision *(filled by the Director)*

> **Brief.** On 2026-10-21 the Director rejected the provisional
> `@Link(underlays=(...))` syntax and the old Relation-family model. The chosen
> design is `@Link(agent, contact)` with the ordered Link Form in the class
> header. `contact.Knows` applies the Agent to the Contact's actual Knows Link,
> and every Relation declares its seats explicitly. This STEP changes no
> runtime by itself.
