# Experimental Ada lifetime evidence

These native Ada probes provide executable scouting evidence for
[STEP-ADA-3](../../../steps/ada/STEP-ADA-3-target-lifetime.md). They select no
Target profile and expose no TOP public carrier, membership, Field, Tagging,
or Rip implementation. They make no Ring 0 or other conformance claim.

`carrier_probes` compares cleanup in an overridable ancestor finalizer with
cleanup in a private controlled component. It checks omitted/explicit ancestor
calls, a plain tagged limited containing host, a controlled containing host,
explicit deallocation, and a raising host finalizer. The counters represent
finalization events, not TOP membership. GNAT may report the raising finalizer
as `Program_Error`; the component cleanup is checked independently.

`companion_lifetime` checks same-scope declaration ordering, a legal premature
companion end, and legal explicit deallocation of a heap Target while its
companion survives. The last case uses external counters only: it never reads
the freed Target. These are lifetime observations, not membership cleanup.

`escape_static` must fail compilation with GNAT's checked-accessibility
diagnostic. `escape_dynamic` must raise the corresponding accessibility
`Program_Error` through an access parameter. `limited_copy` must fail with
GNAT's limited-assignment diagnostic. The runner checks those specific source
diagnostics, not just any compiler failure; unrelated failures fail the run.

With a GNAT toolchain on PATH, run from the repository root:

```sh
sh experimental/ada/lifetime/run-tests.sh
```

The runner enables Ada 2022, assertions, and warnings-as-errors. An assertion
sentinel rejects a run with disabled assertions. Compilation and execution use
a temporary directory removed on exit, including failure. `GNATMAKE` selects
the compiler; `GNAT_FLAGS` adds whitespace-separated arguments/search paths.

Checked accessibility is not ownership: it does not force companion and Target
lifetimes to match, prevent explicit early deallocation, or ensure one companion
per Target. Limited assignment does not prevent fresh construction. These
GNAT-specific probes select no supported profile or TOP failure spelling.

Registry lifetime and real Field cleanup remain separate work. Ordinary
finalization does not guarantee cleanup after
process termination, unchecked memory corruption, or a callback that never
returns. These experiments do not change the Director's still-open choices.
