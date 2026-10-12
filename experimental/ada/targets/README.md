# Experimental Ada Target identity

This is the first library candidate for the initial direction selected in
[STEP-ADA-3](../../../steps/ada/STEP-ADA-3-target-lifetime.md): opt-in limited
hosts, automatic host initialization/finalization hooks, private contained
cleanup, sequential use and eventually retained Tag metadata. The package
names and operations are experimental proposals, not a settled TOP Ada API.

`Top_Targets.Target` is an abstract limited-controlled carrier. A host opts in
by deriving from it. The private controlled token owns independent identity
metadata; it never stores a pointer to, address of, or callback into the host.
Host overrides of `Initialize` and `Finalize` retain their automatic Ada
behavior. Omitting an ancestor `Finalize` call does not omit token cleanup.
Explicit host/ancestor finalizer calls do not finalize the private token or
mark a living Target as ended. Host code remains responsible for its own
resources if it explicitly calls its hooks.

An `Identity_Handle` retains only that metadata. Copying or returning a handle
does not copy or keep a Target alive. Its default value has no identity;
`Is_Present` distinguishes that default from an ended Target's identity.
`Is_Live` is true while the token lives and false after it ends. This is not
proof that the host is usable: its outer finalizer runs before the token ends.
Later Field access must separately handle destruction and reentrancy. Equal
empty handles compare equal; other handles compare their opaque unique IDs.
Distinct live hosts receive distinct IDs even if their ordinary equality says
they are equal.
IDs are issued monotonically and are never recycled: exhaustion raises the
experimental `Identity_Exhausted` exception instead of wrapping. Failed
allocation can consume an ID without assigning it to a Target.

Handle adjustment clears its raw copied pointer before retaining metadata,
so a failed retain cannot release an ownership reference it did not acquire.
Token and handle finalization clear their pointers before releasing them;
cleanup is idempotent and allocation-free. The metadata is released when
neither its Target token nor any handle requires it. No host access is
available through a handle, before or after the Target ends.

The native tests exercise default, copied, returned, self-assigned and
reassigned handles; ordinary host equality; build-in-place creation;
normal scope end and explicit
deallocation; host initialization failure; finalizer overrides that omit the
ancestor; automatic finalizer failure at a normal master end; repeated
explicit host/ancestor hook calls; and handle cleanup during an exception.
Three paired compilation controls refuse ordinary limited Target assignment,
client access to the private token, and client calls to the identity handle's
private finalizer. Hiding the handle's controlled ancestry prevents clients
from revoking its reference accounting through ordinary Ada calls. Legal and
forbidden variants use separate fresh object directories, and compiler exit
status determines refusal rather than diagnostic wording.

With GNAT on PATH:

```sh
sh experimental/ada/targets/run-tests.sh
```

The runner uses Ada 2022, assertions and warnings-as-errors. The executable
has an explicit sentinel that refuses to report evidence when assertions are
disabled. Builds occur in a temporary directory removed on success or failure.
`GNATMAKE` selects the compiler; `GNAT_FLAGS` adds whitespace-separated tool
arguments and search paths. Development evidence uses GNAT 14.2.

This is identity groundwork only. It implements no Fields, Tagging, Geometry,
Contributions, Posts, Rip, walks or retained Tag callbacks. The retained object
here is identity metadata; later Tag metadata must independently prove its
storage and callback lifetimes. No borrowed Target access, arbitrary existing
host adaptation, shared-task safety, pure SPARK or `No_Finalization` support is
claimed. Unchecked memory manipulation, process termination and host hooks
that never return are outside the tested boundary. Controlled containment
requires a finalization-capable Ada runtime. This is not a Ring 0 or safety
conformance claim.
