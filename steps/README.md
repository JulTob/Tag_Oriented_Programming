# STEPs — Standard TOP Enhancement Proposals

A **STEP** is how Tag-Oriented Programming changes: one deliberate step at a time, written down, and decided in the open.

## One STEP, one thing

A STEP is **one task, one purpose, one topic.** Proposing two changes? Write two STEPs. Atomic STEPs are easy to review, easy to Clear or Burn on their own merits, and easy to point back to later. A sprawling STEP is a STEP that won't move.

## The lifecycle

A STEP travels a pipeline (plain meaning in the right column):

| Status | Meaning |
|---|---|
| **Recon** | an idea being scouted — an Issue or Discussion *(pre-draft)* |
| **Brief** | written up as a STEP *(draft)* |
| **Vetting** | under review |
| **Cleared** | accepted ✓ |
| **Redacted** | rejected, kept on the record ✗ |
| **Deployed** | reflected in the Specification *(final)* |

The **Director** (see [`../GOVERNANCE.md`](../GOVERNANCE.md)) moves a STEP from **Vetting** to **Cleared** or **Redacted**, and writes the reason into the STEP. Nothing is decided in silence.

## Desks, not a single queue

STEPs do not share one global number — work runs in parallel, at **Desks**. A Desk is a standing area of the project — the Spec Desk, the Process Desk, the Ada Desk — always open, always improvable. Each STEP belongs to a Desk and is numbered within it:

```
steps/
  process/     STEP-PROCESS-1-...
  spec/        STEP-SPEC-1-...   STEP-SPEC-2-...
  ada/         STEP-ADA-1-...    STEP-ADA-12-...
  java/        STEP-JAVA-1-...
```

A STEP at the Ada Desk and a STEP at the Spec Desk advance independently. Filenames stay clean — `STEP-ADA-12-security-model.md` — sortable, link-safe, no spaces or colons. The full title lives in the file's header.

## Writing one

Copy [`STEP-template.md`](STEP-template.md) into the right Desk folder, name it `STEP-<DESK>-<n>-<slug>.md`, fill it in, and open a PR with **Status: Brief**. From there it is on the record.
