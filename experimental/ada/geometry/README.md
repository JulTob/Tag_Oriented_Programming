# Experimental Ada Geometry

This is a small, provisional Geometry/Form experiment. It is not an Ada TOP
language profile, a supported library API, or a Ring 0 conformance claim.
It defines no Target, Agent, Field, Tagging, contribution, or Rip behaviour.
The final Ada surface remains the Director's decision in STEP-ADA-1 (#5).

A limited `Registry` owns an append-only vector of Tag descriptors. `Add_Tag`
accepts only existing Bases from that Registry and preserves their order.
There is no operation to change Bases, so cycles cannot be declared. `Form`
uses an explicit work stack to produce the Base-first, duplicate-free closure,
ending with the requested Tag. Work storage tracks only that Tag's reachable
closure. Container values own their storage; no allocated
descriptor is left to the caller to free.

Opaque Tag IDs combine a Registry identity with a position. An unissued ID,
a foreign Registry's ID, or an ended Registry's ID raises `Invalid_Tag` when
used with a different/current Registry. IDs do not retain a Registry. Registry
identities are never recycled; exhaustion raises `Constraint_Error`. Creation
is single-threaded in this experiment. These are experimental storage choices,
not new TOP laws or final Ada API choices.

With a GNAT toolchain on PATH:

```sh
sh experimental/ada/geometry/run-tests.sh
```

The runner enables Ada 2022 and assertions, builds in a temporary directory,
and removes its build outputs on exit. `GNATMAKE` can select a compiler;
`GNAT_FLAGS` supplies additional whitespace-separated arguments, such as GNAT
runtime search paths. A sentinel refuses to report success if assertions were
disabled. The ten focused tests cover an empty Registry/root, chains,
ordered independent Bases, diamonds, overlapping/duplicate Bases, a 3,000-Tag
chain, detached input/result lists, invalid handles, and handles from ended
Registries.

A separate finite-space oracle checks every Form in 10,400 five-Tag
declaration graphs (52,000 comparisons). Each direct Base list is an ordered,
repetition-free subset of earlier Tags: `1 × 2 × 5 × 16 × 65` graphs. All
smaller prefixes are covered too. A bounded recursive reference follows a
separate model of integer Base lists; only its final expected order is mapped
to issued Tag IDs for comparison. It does not use Registry internals or the
production traversal helpers. Executed graph/comparison counts are asserted.

This checks the existing experiment's Form ordering and deduplication, not a
new allowable Geometry or final Tag-ID API. It is exhaustive only within the
five-Tag, repetition-free declaration space. The focused duplicate-Base and
depth-3,000 tests remain necessary: this bounded oracle does not test direct
repetitions, prove stack safety, or establish full TOP conformance.

Target lifetime/identity carriers, native Field/view syntax, and the Tagging
and Rip protocols belong to separate design proposals. This experiment does
not choose them.
