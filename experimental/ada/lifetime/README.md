# Experimental Ada lifetime evidence

These native Ada probes provide executable scouting evidence for
[STEP-ADA-3](../../../steps/ada/STEP-ADA-3-target-lifetime.md). They select no
Target profile and expose no TOP public carrier, membership, Field, Tagging,
or Rip implementation. They make no Ring 0 or other conformance claim.

`carrier_probes` compares cleanup in an overridable ancestor finalizer with
cleanup in a private controlled component. It checks omitted/explicit ancestor
calls, a plain tagged limited containing host, a controlled containing host,
explicit deallocation, and a raising host finalizer. The counters represent
finalization events, not TOP membership. The raising-finalizer probe leaves
its master normally and accepts only `Program_Error`, as RM 7.6.1(17.2/1)
requires for this bounded-error context; component cleanup is checked
independently. It makes no claim about an explicit `Finalize` call, abort,
termination, or every finalization-exception context.

`companion_lifetime` checks same-scope declaration ordering, a legal premature
companion end, and legal explicit deallocation of a heap Target while its
companion survives. The last case uses external counters only: it never reads
the freed Target. These are lifetime observations, not membership cleanup.

`escape_static` and `limited_copy` each have legal and forbidden variants of
the same source, selected by GNAT's native `-gnateDIllegal=False/True`
preprocessing. The static pair changes only the Target's declaration scope;
the copying pair changes only `Controlled` versus `Limited_Controlled`. Their
allocator and assignment statements are identical in both variants. The runner
first requires the legal variant to compile, then requires refusal of the
forbidden variant, using separate fresh object directories and strict flags.
Compiler diagnostic wording is not a verdict: logs explain unexpected outcomes
for humans. A shared source/toolchain error fails the legal control rather than
counting as evidence of the intended refusal.

`private_cleanup` adds two independent client-boundary pairs. Ordinary client
code outside the fixture package can call its public identity query, but
cannot read its private lifetime component or name the private finalizer.
Each forbidden access has its own legal control and fresh build directory.
Taking a private finalizer's address tests its visibility without relying on
the component-access refusal. These fixtures test ordinary Ada privacy;
unchecked operations and arbitrary host finalizer behavior are outside this
evidence. They introduce no public TOP carrier or cleanup API.

`no_finalization` changes only whether GNAT's implementation-defined
`No_Finalization` restriction is enabled. With the selected GNAT 14 toolchain,
the ordinary controlled fixture must compile and the restricted variant must
be rejected. This checks that exact source and compiler profile, not portable
Ada type availability, every restricted runtime, or a SPARK verification
boundary. The result uses compiler exit status, not diagnostic wording.

`rosen_probes` exercises a private controlled `Lifetime(Carrier'Access)`
component in plain and controlled outer carriers. Its current-instance address
is cached and compared only while the Host is live, including a limited
build-in-place result and two distinct live Hosts. Each token receives a unique
scouting ID during initialization. Cleanup uses only that ID and external trace
events: it never dereferences the owner, reads host extension state, or dispatches
a host callback. These IDs and addresses are test observations, not TOP identity
or Registry implementations.

Ordinary component order is observed, not asserted as portable. Ada RM
§7.6.1(9/3) instead gives priority to components whose access discriminants use
per-object expressions, with reverse declaration order between such components.
The probe checks a Rosen token before an ordinary extension, and a later
dependent extension before that token. It also checks that automatic outer
`Finalize` precedes components, while repeated explicit Host/ancestor `Finalize`
calls leave the private token untouched until automatic finalization. Containment
does not by itself establish a universally safe point for host callbacks.

`escape_dynamic` first attaches a same-scope Target successfully, then requires
`Program_Error` around only the inner Target's `Attach` call. It does not inspect
exception text. Allocations accepted by either path are disposed before their
Targets end, without dereferencing a ceased Target. These probes still test
Ada mechanics, not TOP membership or a selected carrier profile.

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

The trace and ID counters are sequential scouting fixtures, not task-safe
shared state. No concurrent Field/query/destruction or Registry synchronization
contract is implemented. The probes require automatic controlled hooks; a
`No_Finalization` restriction that disables those hooks cannot provide this
evidence. No SPARK lifecycle proof or supported SPARK profile is claimed.

Registry lifetime and real Field cleanup remain separate work. Ordinary
finalization does not guarantee cleanup after
process termination, unchecked memory corruption, or a callback that never
returns. These experiments do not change the Director's still-open choices.
