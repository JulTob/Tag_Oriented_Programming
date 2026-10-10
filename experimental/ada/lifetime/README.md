# Experimental Ada carrier finalization

These native Ada probes provide executable scouting evidence for
[STEP-ADA-3](../../../steps/ada/STEP-ADA-3-target-lifetime.md). They select no
Target profile and expose no TOP public carrier, membership, Field, Tagging,
or Rip implementation. They make no Ring 0 or other conformance claim.

The one executable compares cleanup in an overridable ancestor finalizer with
cleanup in a private controlled component. It checks omitted/explicit ancestor
calls, a plain tagged limited containing host, a controlled containing host,
explicit deallocation, and a raising host finalizer. The counters represent
finalization events, not TOP membership. GNAT may report the raising finalizer
as `Program_Error`; the component cleanup is checked independently.

With a GNAT toolchain on PATH, run from the repository root:

```sh
sh experimental/ada/lifetime/run-tests.sh
```

The runner enables Ada 2022, assertions, and warnings-as-errors. An assertion
sentinel rejects a run with disabled assertions. Compilation and execution use
a temporary directory removed on exit, including failure. `GNATMAKE` selects
the compiler; `GNAT_FLAGS` adds whitespace-separated arguments/search paths.

Companion accessibility, copying, Registry lifetime, and real Field cleanup
remain separate work. Ordinary finalization does not guarantee cleanup after
process termination, unchecked memory corruption, or a callback that never
returns. These experiments do not change the Director's still-open choices.
