# Conformance

An implementation of TOP — in **any** language — is *conformant* when it preserves the observable semantics defined in [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md) and passes the conformance suite.

## Obligations

A conforming implementation must provide:

- stable Target identity under tagging;
- observable membership and Base membership (`agent in Tag`), closed upward through Bases;
- "ever an instance, always an instance" identity that survives Rip (`isinstance`, or the language's equivalent, stays true);
- non-owning, iterable Fields;
- ordered Base-then-Shape application;
- **atomic** taggings — all-or-nothing, with no partial commits;
- **sticky** contributions — Actions and Records persist; only active Field membership ends, and only by explicit Rip;
- the latest visible Overlay by contribution name, with **captured Underlays** for extension;
- Agent-bound snapshot access;
- tag-time **`@Pre` / `@Imprint` / `@Post`**, conditions evaluated by **strict boolean** (no truthy/falsy coercion);
- the contract direction — `@Pre` relaxes backward, `@Post` strengthens forward; a *weakened* `@Post` is **diagnosed, not silent**;
- defined failure types and diagnostics.

Surface spellings may differ between languages; the **semantic laws** must not.

## The conformance suite

`tests/` is the seed of a language-agnostic conformance suite. An implementation passes by satisfying the behaviours those tests assert, ported to its language.

## The "TOP Verified" mark

Implementing TOP is free and open. **Claiming conformance under the "TOP Verified" / "TOP-conformant" designation** is what the steward authorizes, per implementation — so the mark continues to mean something. Request review by opening an issue.
