# Catalog of the Tag Algebra

*A map for the Director and the team. It reads each branch at the commit named in "Which branch each status refers to".*

The Director asked: "I think we need a catalog of the Set algebra associated with tags because it's growing a bit."

This catalog lists the spellings found so far that read a Tag or a population, or act on one. Each row gives the spelling, its meaning in one plain line, what it gives back, and where it stands.

**The Specification and the STEPs are the authority. Where they disagree, this catalog shows both and chooses nothing.** main's Specification (`spec/SPECIFICATION.md`) is the reference. Brief and Vetting STEPs propose; the Director decides. If this catalog disagrees with its sources, the catalog has a bug.

## Words used here

**The basics**
- **Tag**: a class that gives objects a role. `class Wizard(Tag):`.
- **Agent**: an object a Tag was applied to. `Wizard(ari)` makes `ari` an Agent.
- **Field**: all the current members of one Tag, `Wizard[:]`.
- **Population**: a group of Agents you can walk, count and combine. A Field is one.
- **Combination**: a population made with `|`, `&` or `-`.
- **Shape and Base**: in `class Wizard(Officer):`, Wizard is a **Shape** of Officer, and Officer is Wizard's **Base**.
- **Form**: a Tag and all its Bases, Base first. `Form(Wizard)` is `(Officer, Wizard)`.
- **Pin**: a Tag applied to Tags, `Rare(Wizard)`.
- **Flag**: a Tag that is also a keyword, `"Undead" in ghoul`.
- **Kit**: TopKit, the Python library that builds TOP.
- **STEP**: a written proposal to change TOP. Its status moves from Brief (a draft) to Vetting (under review), then Cleared or Redacted, then Deployed (`steps/README.md`).

**Promises**
- **Precondition**: a check at the door. It can refuse a tagging.
- **Postcondition**: a promise the Agent must keep after the tagging.
- **Contract**: all the conditions on an Agent. `Contract` is also the kit's name for the functions that read them.
- **Sound**: every visible promise (Postcondition) of the Agent holds.
- **Defective** (or broken): a member with a broken promise. It is still a member.

**What a Tag gives**
- **Action**: a function a Tag gives each Agent. `ari.Greet()`.
- **Record**: a value a Tag gives each Agent. `ari.hp`.
- **Report**: a value of the Tag itself, shared by all. `Wizard.motto`.
- **Operation**: a function of the Tag itself. `Enemy.Volley(5)`.
- **Published member** (`@Public`): a Report or Operation the Tag lends to its members.
- **Rogue Agent**: an Agent that left a Tag. Using that Tag's published members raises a Rogue Access Failure.
- **View**: `Wizard[ari]`. A read-only snapshot of what Wizard gave ari, taken right after Wizard applied.
- **Underlay**: the Action beneath an Action of the same name. `@Underlay` lets the upper one call it.

**Leaving**
- **Rip**: ending one membership, `del Wizard[ari]`.
- **Teardown**: code a Tag runs when an Agent leaves it (a `@Rip` protocol).
- **Spin-off** (STEP-26, Brief): an Agent that holds a Shape but has left one of its Bases.
- **Finalizer**: code Python runs when an object is about to be destroyed (`__del__`).
- **`__del__` Layers**: an Agent's finalizer, stacked: the host's own `__del__` first, then each Tag's.
- **Collection**: Python's garbage collector freeing objects that nothing can reach.
- **Safehouse** (S19 only): where the kit keeps an Agent whose teardown failed when it was deleted.
- **Triage** (S19 only): giving up on kept Agents and letting them go.

**In Brief STEPs**
- **Projection**: the values of one name across a population, `Wizard.level`. The population it reads is its **root**.
- **Filter**: the members whose value passes a comparison, `Wizard.level > 3`.
- **No value** ("NULL-like"): a member that lacks the name, or holds `None`. Like SQL's `NULL`.
- **Link**: a Tag that belongs to one Agent. `charlie.Knows` is charlie's Link.
- **The Link's Agent**: the one who holds the Link and acts through it (charlie).
- **The Link's Contact**: a member of the Link's Field (ruth). `charlie.Knows(ruth)` makes her one.
- **Pair**: one Agent and one Contact, linked. `charlie.Knows[ruth]`.
- **Relation**: the `@Link` declaration itself, `Knows` inside `class Social`.
- **Field Rip**: `del Wizard[:]`, a Rip of every member at once.
- **Category error**: treating one kind of TOP thing as another, such as a Tag as its Agents.

**Logic words**
- **Epsilon** ("any one"): pick some member that fits, if there is one. From Hilbert.
- **Iota** ("the only one"): the one member that fits; an error if there are none or several. From Russell.
- **Mask**: a list of True and False values that picks items, as in `df[df.level > 3]` (pandas).

## How to read the Status column

| Status | What it means |
| --- | --- |
| **On main** | Written in main's Specification (or its guides) and built in main's kit. You can use it today. If the STEP behind it is still at Vetting, the row or the section says so. |
| **On main (kit only)** | main's kit does it, but the Specification does not say so, or says otherwise. Do not build on it. |
| **Vetting** | Written into the Specification and the kit on the step-19 branch (S19), in the STEP named. Under review. Not merged. |
| **Brief** | In a draft STEP, on the branch named. No kit builds it yet. |
| **Brief, decided** | In a Brief STEP, and the Director has ruled on this point. His words are in the STEP. The STEP as a whole is still undecided. |
| **Proposed** | Said in discussion or by the design panel. Not in a STEP's rules yet. The row says when a STEP records it as an open question. |
| **Set aside** | Not chosen in a STEP's "Alternatives" table, or by the design panel. Not a ruling by the Director. |
| **Rejected** | Turned down by the Director himself, in the STEP named. |
| **Withdrawn** | Its STEP was closed without merging. |
| **Not Python** | A syntax error. Python cannot read it. See section 12. |
| **No status** | Legal Python, but no kit and no STEP gives it a meaning. |

Notes:
- **"Deployed" is not used here.** It is a STEP status, and only the Director sets it. On main, STEP-SPEC-13 (Field Algebra), 14 (Condition Members), 17 (A Flag's Words) and 18 (Deletion in Layers) still say Vetting, "Drafted for the Director's confirmation". What they describe is in main's Specification and kit, so it is "On main" here, with a note.
- The STEP process calls a whole rejected STEP "Redacted". Here "Rejected" and "Set aside" are about one spelling.
- In the Status column, "§0.3" is a section of the Specification. After a STEP's name, "r1.2" is its rule 1.2, "OQ1" its open question 1, and "section 5" its own section 5.

## Which branch each status refers to

| Short name | Branch | Commit | What it carries |
| --- | --- | --- | --- |
| **main** | `origin/main` | ce35726 | The Specification and the kit. "On main" means this branch. |
| **S19** | `origin/Julio_Cl/step-19-sound-in` | e1fbcdd | Not merged. STEP-SPEC-13 items 5 to 7, STEP-SPEC-18 amendments D, E and F, and STEP-SPEC-19, all at Vetting and built into its Specification and kit. It also amends STEP-SPEC-4, 6, 7, 9, 12, 14 and 17 (for example STEP-6's Scope rows and STEP-17 item 8). "Vetting" means this branch. |
| **PR #26** (HEAD) | `julio_cl/exciting-heisenberg-o475s5` | this commit | STEP-SPEC-22 (Links), 23 (Field Filters), 24 (Field Rip), 26 (A Shape Keeps No Base Hostage), 27 (Emergency Stop) and 28 (Category Error), all Brief. The Guide's `all(...)` and `any(...)` rows. Its kit is main's, except that `Wizard[:].Add` and `Wizard[:].Remove` became private. |
| **PR #27** | `julio_cl/nifty-cray-wha6gn` | 1953bce | STEP-SPEC-20, Brief. One note in section 8. |
| **PR #28** | `julio_cl/step-25-commands-to-a-population` | 1fceebf | STEP-SPEC-25 (writes and commands through populations), Brief. Its kit is PR #26's. Its copies of STEP-SPEC-22, 23 and 24 are older, so this catalog reads PR #26's copies. |

STEP-SPEC-27 (Emergency Stop, Brief) proposes `Stopped(Wizard)` (a stop at category 1), `Stopped(Wizard, category=0)`, `Wizard in Stopped[:]` (is the latch on?) and `del Stopped[Wizard]` (reset; nobody comes back). No kit builds them.

> **Brief only, in no kit.** Pairs, Links, Projections, Filters, the Field Rip (`del Wizard[:]`), spin-offs, the writes of STEP-SPEC-25, `TagCategoryError`, `Stopped`, and the proposed `Sound` and `Only`. `from TopKit import Link` and `from TopKit import Sound` both fail with an ImportError (checked on PR #26 and on S19).

## Where the sources disagree

**main and S19.** These topics have two rows, one marked **main** and one marked **S19**:
- what `ari in Wizard` means (section 2);
- what `Wizard[...]` and `Tag[...]` mean (sections 3, 5 and 8);
- a Pin's population mixed with a Tag's (section 4);
- what a failed Rip does (section 8);
- what a failed teardown does when an Agent is deleted (section 8);
- what a Scope's exit does with a failed Rip (section 8);
- a Flag's words given as a list (section 9);
- whether `Wizard[:].Add` and `Wizard[:].Remove` are public (section 3; private on PR #26).

**The STEPs with each other** (all Brief):
- `Wizard.hp = 10` over a Record: STEP-25 r4.2 (PR #28) raises `TagCompositionError`; STEP-28 r3 (HEAD) names it `TagCategoryError` (section 6).
- A misspelt name: HEAD's STEP-23 r1.7 skips members with no value, and warns only when no member has the name. PR #28's STEP-25 r2.7 still says a misspelt read "stops at the first member", and r2.1 leans on it (section 6).
- STEP-25 r2.7 cites "STEP-SPEC-24, rule 1.2" for collected failures. That is rule 1.4, on HEAD and in PR #28's own copy, where rule 1.2 was the refusal at the door.
- The sound members as a write root: STEP-25 r1.2 writes `(Enemy[:] & Enemy).hp = 10`. For reads, the Director refused the same shape, `(Wizard[:] & Wizard).colour`: "I refuse that monstrosity with redundant information" (STEP-23 OQ2).

**main's Specification and main's kit**:
- `bool(ari)` for a host with its own `__bool__` (section 2).
- Deleting an Agent: §3.2 line 1225 says deletion "Rips it", but the kit runs the teardowns while the Agent is still a member (section 8).

## The cast used in the examples

This runs on main, on PR #26 and on S19. Other names (`ghoul`, `Deprecated`, `howler`, `Enemy`, `Social`, `charlie`, `ruth`, `Cached`, `Human`, `bob`, `Werewolf`, and so on) are made where they are used.

```python
from TopKit import Tag, Post, Pin, Flag

class Crew:
    def __init__(self, name):
        self.name = name
        self.alive = True
        self.level = 1

class Officer(Tag):
    @Post
    def Alive(agent):                 # a promise: a member must stay alive
        return agent.alive

class Wizard(Officer):                # a Shape of Officer
    pass

class Fighter(Officer):
    pass

class Sworn(Tag):                     # an independent Tag
    pass

@Pin
class Rare(Tag):                      # a Pin: applied to Tags
    pass

@Flag
class Undead(Tag):                    # a Flag: a keyword on its Agents
    pass

ari, bo, cal = Crew("ari"), Crew("bo"), Crew("cal")
Wizard(ari)
Wizard(bo)
Fighter(cal)
cal.alive = False                     # cal breaks its promise: cal is defective
```

---

## 1. Applying a Tag

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `Wizard(ari)` | Apply Wizard to ari. Its Bases apply first (here Officer), each once. | ari | **On main** · §0.5 |
| `Wizard(ari, **inputs)`, for example `MI6(bond, code="007")` | The same, with inputs. Each input goes by name to the Preconditions, Record builders and Imprints that ask for it. | ari | **On main** · §0.5 |
| `Wizard(ari)`, while ari is already a Wizard | Does nothing. To reset, Rip and apply again. | ari | **On main** · §0.5 |
| `Apply(ari, Wizard, Sworn)` | Apply several Tags, in order (section 10). | ari | **On main** · §0.8 |
| `Wizard(int)` (a class) | An ordinary Tag applies to objects only. | TypeError today: "Wizard is applied to objects, not classes". `TagCategoryError` (a TypeError) under STEP-28. | **On main** · §1.9. **Brief** · STEP-28 r3 · PR #26 |
| `Rare(ari)` (a Pin, on an object) | A Pin applies to Tags only. | TagCompositionError today. `TagCategoryError` under STEP-28. | **On main** · §1.9. **Brief** · STEP-28 r3 |
| `Wizard(None)`, `Wizard(3)`, `Wizard(True)` | These objects cannot carry TOP state, so they can never be Agents. | TagCompositionError | **On main** · Failure model ("a Target that cannot carry state") |
| `Wizard(ari)`, when ari is a spin-off (still a Wizard, no longer an Officer) | **STEP-26:** recommended, it does nothing, as for any active Tag. Without that rule, today's kit would lay Officer over Wizard. | ari | **Brief** · STEP-26 r5.1, OQ2 · PR #26 |
| `Officer(ari)`, when ari is a spin-off | **STEP-26:** Officer comes back, on top of Wizard, with a warning (recommended). | ari | **Brief** · STEP-26 r5.3, OQ2 |
| `Wizard[ari] = x` | No meaning today. | AttributeError: `__setitem__` | **On main (kit only)**. The design panel proposes a refusal that names `Wizard(ari)` (see "Proposed"). |

Linking (`charlie.Knows(ruth)`) is in section 7. Pinning (`Rare(Wizard)`) is in section 9.

## 2. Asking about one Agent

Membership questions. Each answers `True` or `False`.

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `ari in Wizard` | **main:** Is ari a member now? Sound or defective both count. | bool | **On main** · §0.3 |
| `ari in Wizard` | **S19:** Is ari a *sound* member now? The same group the loop walks. | bool | **Vetting** · S19 · STEP-19 item 1 |
| `ari in Wizard`, written inside a check (a Postcondition, a condition read by name, a `Contract` read) | **S19:** The Agent being checked counts as sound, so this reads plain membership. | bool | **Vetting** · S19 · STEP-19 item 5 |
| `ari in Wizard[:]` | Is ari a member at all, sound or defective? It reads the same on every branch. | bool | **On main** · FIELDS guide (`TopKit/FIELDS.md`); S19 §0.3 |
| `ari in ~Wizard` | Is ari a defective member? | bool | **On main** · §0.8 |
| `ari in (Wizard \| Fighter)` | Answered from the two sides, as a set would. | bool | **On main** · §2.5 (STEP-13 at Vetting); S19 states it in STEP-19 item 3 |
| `ari in Officer`, while ari is a Wizard | **Today:** always True. Tagging is closed upward, and the Base cannot be Ripped while the Shape is active. | bool | **On main** · §0.3, §0.7 |
| `ari in Officer`, after `del Officer[ari]` while ari stays a Wizard | **STEP-26:** False. Each membership stands alone. `ari in Wizard` stays True. | bool | **Brief** · STEP-26 r1.2 · PR #26 |
| `isinstance(ari, Wizard)` | Was ari ever a Wizard? Stays `True` after a Rip. This is also what `case Wizard():` asks (section 11). | bool | **On main** · §0.3 |
| `bool(ari)`, `if ari:` | Do all of ari's visible promises hold? Without a visible Postcondition, a host's own `__bool__` or `__len__` answers instead. | bool | **On main** · §2.5 |
| `bool(ari)`, when ari's host class has its own `__bool__` | The host's `__bool__` still answers, even when a visible Postcondition is broken. (A host whose truth comes from `__len__` does get the contract.) | bool | **On main (kit only)**: §2.5 says the contract takes over once a Postcondition is visible. S19's §2.5 was rewritten to match the kit. Open: STEP-19 Decision, question 3. |
| `ari.Alive` | One promise, read by its name. | bool | **On main** · §2.5 (STEP-14 at Vetting) |
| `kept in Tag[...]`, `kept in Cached[...]` | Is this Agent kept in the safehouse? | bool | **Vetting** · S19 · STEP-18 amendment E |
| `s in Sworn`, where `s` is an Agent made from a `str` subclass | Gives `False` even though `s` is a member. Every string goes to the keyword lookup. | bool (wrong) | **On main (kit only)**: a defect, `TopKit/tags.py:113`. Same on S19. |
| `Wizard in ari`, `"Wizard" in ari` (Wizard is not a Flag) | No meaning. The Agent's own `in` is kept for keywords. | TypeError, or `False` if ari carries some Flag | **On main** · §0.8. The `tags.py` docstring says otherwise. |

Keywords on an Agent (`"Undead" in ghoul`) are in section 9. Links (`ruth in charlie.Knows`) are in section 7. Filters (`ruth in f`) are in section 6.

## 3. Populations

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `for w in Wizard:`, `list(Wizard)` | The sound Wizards, in the order they joined. | iterator | **On main** · §0.8, §2.5 |
| `len(Wizard)` | How many sound Wizards. | int | **On main** · §0.8 |
| `if Wizard:`, `while Enemy:`, `if not Boss:` | Is anyone sound? Stops at the first sound member. | bool | **On main** · §0.8 |
| `~Wizard` | The defective Wizards. | population | **On main** · §0.8 |
| `for w in ~Wizard:`, `len(~Wizard)`, `if ~Wizard:` | Walk, count, or ask about the defective ones. | iterator, int, bool | **On main** · §0.8 |
| `~~Wizard` | The sound Wizards again. | population | **On main (kit only)** |
| `Wizard[:]` | Everyone in the Field, sound or defective. The same object on every read. | population | **On main** · §0.8 |
| `len(Wizard[:])`, `if Wizard[:]:` | How many members; is there any member at all. | int, bool | **On main** · §0.8 |
| `Tag[:]` | The root Tag's own Field. Always empty: the root `Tag` is never part of a Form, so nobody joins its Field. Careful: on S19, `Tag[...]` is everyone kept in the safehouse. The two look alike. | population | **On main (kit only)** |
| `Wizard[...]` | **main:** read as "the view of the Agent `...`", which fails. | TagResolutionError | **On main (kit only)** |
| `Wizard[...]` | **S19:** the safehouse: Agents kept at a failed deletion, by Wizard or by any Shape over it. | population | **Vetting** · S19 · STEP-18 amendment E |
| `Tag[...]` | **S19:** every kept Agent. | population | **Vetting** · S19 · STEP-18 amendment E |
| `Wizard[:].Add(x)`, `Wizard[:].Remove(x)` | Put an object in the Field, or take it out, with no tagging. | None | **On main (kit only)**. Made private on PR #26. Kept public on S19, with `Wizard[:].Rejoin`. |
| `for e in Enemy:` while an earlier turn Rips a later member | **Today:** the walk still visits the member that was Ripped. | iterator | **On main (kit only)** |
| `for e in Enemy:` while an earlier turn Rips a later member | **STEP-25:** a member that has left is skipped. | iterator | **Brief** · STEP-25 r6.5 · PR #28 |
| `+Wizard`, `-Wizard` | A short spelling for the sound members, or for the safehouse. | TypeError today | **Set aside** · STEP-19 and STEP-18 Alternatives (S19); STEP-23 Alternatives (PR #26). Reopened in STEP-25 OQ4 (PR #28). The design panel set `(+Wizard).level` aside again (STEP-23 OQ2). |

## 4. Combining

A **combination** is lazy and alive: it reads its Fields each time you use it. It answers `in`, `len`, truth and `for`. A Tag in an operator seat means its sound members. The rows marked §2.5 came from STEP-SPEC-13, which is still at Vetting on main.

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `Wizard \| Fighter` | Sound members of either, each once, left side first. | population | **On main** · §2.5 |
| `Wizard & Fighter` | Sound members of both. | population | **On main** · §2.5 |
| `Wizard - Sworn` | Sound Wizards who are not sound Sworn members. | population | **On main** · §2.5 |
| `Wizard[:] \| Fighter[:]` | Every member of either, sound or not. | population | **On main** · §2.5 |
| `(Wizard[:] \| Fighter[:]) - Sworn` | Anyone with a role who has not sworn. The levels mix. | population | **On main** · §2.5 |
| `~Wizard \| ~Fighter` | Defective in either. | population | **On main** · §0.8 |
| `~(Wizard \| Fighter)` | Refused: a union has no universe to take the rest from. | TypeError | **On main** · §2.5 |
| `~Wizard[:]` | Refused: the same reason. | TypeError | **On main (kit only)** |
| `Wizard - Officer` | **Today:** always empty, since every Wizard is an Officer. **STEP-26:** the spin-offs, sound Wizards who left Officer (STEP-26 shows `list(Werewolf - Human)` as `[bob]`). | population | **On main** · §2.5. **Brief** · STEP-26 section 3 |
| `Wizard \| None`, `Wizard \| int` | Python's own type union, for type hints. | `types.UnionType` | **On main** · §2.5 |
| `None \| Wizard \| Fighter` | Python joins left to right, so this is a type union, not a population. | `types.UnionType` | **On main (kit only)**; S19 writes it down in STEP-13 item 5 |
| `None \| (Wizard \| Fighter)` | A population is not a type. | TypeError | **main:** Python's plain message (kit only). **S19:** the message names `typing.Optional[typing.Union[Wizard, Fighter]]` (**Vetting** · STEP-13 item 5). Under STEP-28: `TagCategoryError` (**Brief** · r3). |
| `Wizard \| Fighter \| None` | A population is not a type. | TypeError | **main:** Python's plain message (kit only). **S19:** the message names `typing.Optional[typing.Union[Wizard, Fighter]]` (**Vetting** · STEP-13 item 5). Under STEP-28: `TagCategoryError` (**Brief** · r3). |
| `isinstance(x, Wizard \| Fighter)` | A population is not a type. Write `isinstance(x, (Wizard, Fighter))`. | TypeError | **main:** Python's plain message (kit only). **S19:** the message names the rewrite (**Vetting** · STEP-13 item 5). Under STEP-28: `TagCategoryError` (**Brief** · r3). |
| `Wizard & None`, `Wizard - int` | No meaning. | TypeError | **On main (kit only)** |
| `Rare \| Wizard` (a Pin's population with a Tag's) | **main:** allowed. The result mixes Tags and Agents: `[Wizard, ari, bo]` when Wizard is pinned. | population | **On main (kit only)** |
| `Rare[:] & Wizard` | **main:** allowed, and always empty: no Tag is an Agent. | population | **On main (kit only)** |
| `Rare \| Wizard`, `Rare[:] & Wizard` | **S19:** refused, naming both sides. | TypeError | **Vetting** · S19 · STEP-13 item 6. Under STEP-28: `TagCategoryError` (**Brief** · r3). |
| `Cached[...] \| Wizard[:]` | The safehouse combines like any population. | population | **Vetting** · S19 · STEP-18 amendment E |

Links combine too (section 7). Filters combine too (section 6).

## 5. Views and keys inside `[ ]`

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `Wizard[ari]` | The view of ari as a Wizard: a read-only snapshot from just after Wizard applied. ari must be a member, sound or defective. | view | **On main** · §1.7 |
| `ari.Wizard` | The same view, by the Tag's name. | view | **On main** · §1.7 |
| `Wizard[:]` | The whole Field. | population | **On main** · §0.8 |
| `Wizard[::]` | The same as `Wizard[:]` (section 13). | population | **On main (kit only)** |
| `Wizard[...]` | **main:** fails. **S19:** the safehouse. See section 3. | error, or population | main: **On main (kit only)**. S19: **Vetting** · STEP-18 amendment E |
| `Wizard[0]`, `Wizard[-1]`, `Wizard["x"]`, `Wizard[True]`, `Wizard[()]` | Any other key is read as an Agent, so these fail. | TagResolutionError | **On main (kit only)**. For positions, see "Proposed". |
| `Wizard[1:2]`, `Wizard[0:]`, `Wizard[::1]` | Positional slices have no meaning for a population. | TypeError | **On main (kit only)** · `TopKit/tags.py:216-217` |
| `Wizard[:][0]`, `reversed(Wizard[:])` | A population has no index and no reverse order. | TypeError | **On main (kit only)** |
| `Rare[Wizard]`, `Wizard.Rare` | The view of Wizard as a Rare Tag, by class or by name. | view | **On main** · §1.9 |
| `charlie.Knows[ruth]` | The Pair: what charlie's link to ruth holds. Live, not a snapshot. | Pair | **Brief** · STEP-22 r7.1 · PR #26 |
| `k[ruth]`, where `k = charlie.Knows` outlived charlie | Fails: that Link's Agent is gone. | TagResolutionError | **Brief** · STEP-22 r5.8 · PR #26 |
| `Social.Knows[:]` | `[:]` on a Projection fans out: it walks each value's members. The only key a Projection takes. | Projection | **Brief** · STEP-23 r4.2 · PR #26 |
| `with Wizard[h]:`, `with Wizard[h](code="007"):` | A Scope in a bracket spelling: h joins Wizard for the block. Today `Wizard[h]` is the view, and needs h to be a member already. | none | **Proposed**: the Director chose this spelling on 2026-09-30, for a STEP-SPEC-21 that is not written on any branch. Recorded in S19's STEP-6 amendment ("When, and the spelling"). |
| `Wizard[:][Wizard[:].level > 3]` | Pick members with a mask. | none | **Set aside** · STEP-23 Alternatives (Brief) |
| `Signal.t[5]`, `Signal.t[a:b]` (a Record marked `@Index`, read on its Tag) | The Index: a key that names one Agent, or a range of them. | none | **Withdrawn** (PR #18 closed unmerged on 2026-10-05). Its spellings clash with STEP-23 r1.1 (`Signal.t` is a Projection), r1.8 (it refuses `Signal.t[5]` and `5 in Signal.t`) and r4.2 (`Signal.t[:]` is a fan-out). |

The Director asked: "Wizard[ari] : I know we use it to delete, but just for that? maybe could do more than that". The design panel's answer is under "Proposed".

## 6. Projections and Filters

Most rows here are Brief. Reads are STEP-SPEC-23 (PR #26). Writes are STEP-SPEC-25 (PR #28). The failure's name is STEP-SPEC-28 (PR #26). Rows marked **On main** say what the kit does today. The design panel proposes a new root for the members, `Wizard[Sound]` (see "Proposed").

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `Wizard.level` | Each sound Wizard's `level`, in join order. | Projection (today: AttributeError) | **Brief** · STEP-23 r1.1 · PR #26. The Director found it implicit: "Wizard.level makes it so the record looks like a report" (STEP-23 OQ2). |
| `Wizard.spells` (a name the Tag declares for its Agents) | Each sound Wizard's `spells`. | Projection (today: the plain function) | **Brief** · STEP-23 r1.1 |
| `Wizard.colour`, when Wizard has a Report `colour` | The Tag's own Report. The Tag's own names always win. | value | **Brief** · STEP-23 r1.1, r1.3 |
| `Wizard.motto = "brave"` (a name the Tag does not give its Agents) | Sets a value of the Tag itself: a Report written by hand. | none | **On main** (Python's own meaning; §1.4 for a declared Report). **Brief, decided**: "if it looks like a report, then it is, and we just have more than one way to handle that" (STEP-23 section 6; STEP-28 r3). |
| `Wizard[:].level` | Every member's `level`, defective ones too. | Projection | **Brief** · STEP-23 r1.2 |
| `Wizard[:].colour`, when Wizard also has a Report `colour` | Every member's own `colour`, past the Tag's Report. | Projection | **Brief** · STEP-23 r1.3 |
| `(~Wizard).level` | Each defective member's `level`. The brackets matter: `~Wizard.level` means `~(Wizard.level)`. | Projection | **Brief** · STEP-23 r1.2 |
| `(Wizard \| Fighter).level` | Over a combination. | Projection | **Brief** · STEP-23 r1.2 |
| `(Wizard[:] & Wizard).colour` | The sound members' own `colour`, past the Tag's Report. | Projection | **Brief** · STEP-23 r1.3. The Director refused this spelling: "I refuse that monstrosity with redundant information" (STEP-23 OQ2). |
| `Rare.rarity` | Each pinned Tag's `rarity`. | Projection | **Brief** · STEP-23 r1.6 |
| `Wizard.familiar.name` | A chain: each familiar's name. | Projection | **Brief** · STEP-23 r4.1 |
| `sum(Wizard.level)`, `len(Wizard.level)` | Walk the values. Members with no value are skipped, as SQL's `SUM` skips `NULL`. | int | **Brief, decided** · STEP-23 r1.7 (the skip); `len` counting values is r1.8, not ruled on. |
| `Wizard.dance == None`, `Wizard.Dance != None` | The members with no value; the members that have one. "No value" means the name is missing or holds `None`. | Filter | **Brief, decided** · STEP-23 r1.7: "== None is the way to check for non-defined gains (records, contracts, actions...) and != None so it simply exists". Style checkers flag `== None` (E711); TOP writes it on purpose. |
| `Wizard.dance == True`, `Wizard.dance == False` | The members whose `dance` is defined and True (or False). A member with no value never matches. | Filter | **Brief, decided** · STEP-23 r1.7 |
| `Wizard.levle > 3`, where no member has `levle` | A misspelt name. The walk warns. | RuntimeWarning | **Brief** · STEP-23 r1.7. The Director decided the NULL-like reading; this warning is not in his words. |
| `Wizard.level > 3`, and the same with `==`, `!=`, `<`, `<=`, `>=` | A Filter: the sound Wizards whose level is above 3. It re-reads at every walk. | Filter, a population (today: an error) | **Brief** · STEP-23 r2.1 |
| `Wizard.Can_Cast("Light") == True` | A Filter by a call. The call runs again at every walk. | Filter | **Brief** · STEP-23 r3.1, r3.2 |
| `(Wizard.level > 3) & Sworn` | A Filter combines like any population. | population | **Brief** · STEP-23 r2.4 |
| `(Wizard.level > 3).spells` | A Filter projects again. | Projection | **Brief** · STEP-23 r1.2 |
| `ruth in f`, where `f` is a Filter | Is ruth in the Filter? | bool | **Brief** · STEP-23 r2.4 |
| `len(f) > 0` | Is anyone in the Filter? | bool | **Brief, decided** · STEP-23 Decision: the Director's choice for now; he will come back to it. |
| `bool(f)`, `if f:`, `2000 < Wizard.level < 2020` | Refused, so that a chained comparison fails loudly. | TypeError. `TagCategoryError` (a TypeError) under STEP-28. | **Brief, decided** · STEP-23 section 5 and Decision: "your reasoning makes sense. we'll refuse to protect that." STEP-28 r3 · PR #26 |
| `any(f)` | Not "anyone?". It asks each member's own truth (section 11). | bool | **Brief** · STEP-23 section 5 |
| `(Wizard.level > 2000) & (Wizard.level < 2020)` | A range. | Filter | **Brief** · STEP-23 section 5 |
| `ruth in Wizard.level` | Refused: a Projection holds values, not Agents. The message says to compare first. | TypeError. `TagCategoryError` under STEP-28. | **Brief** · STEP-23 r1.8; STEP-28 r3 |
| `ruth in Wizard.level > 3` | Python reads it as `(ruth in Wizard.level) and (Wizard.level > 3)`, so it fails on the first part. | TypeError | **Brief** · STEP-23 section 5 |
| `~Wizard.level`, `Wizard.level \| Fighter.level` | Refused: a Projection takes no `~` and no population operator. | TypeError | **Brief** · STEP-23 r1.8 |
| `Social.Knows[:] == ruth` | The sound Social Agents with *some* Contact who is ruth: "who knows Ruth?" | Filter | **Brief** · STEP-23 r4.3 |
| `Social[:].Knows[:] == ruth` | The same question, over the whole Field. | Filter | **Brief** · STEP-23 r4.3 |
| `Social.Knows[:] != ruth` | Those with *some* Contact who is not ruth. It does not mean "does not know Ruth". | Filter | **Brief** · STEP-23 r4.5 |
| `Social - (Social.Knows[:] == ruth)` | Those who do not know Ruth. "Not" is a difference. | population | **Brief** · STEP-23 r4.5 |
| `Social - (Social.Knows[:].friendly == False)` | Those whose Contacts are all friendly. "All" is a difference of a "some". | population | **Brief** · STEP-23 r4.4 |
| `charlie.Knows.since < 2000` | charlie's sound Contacts whose Pair's `since` is below 2000. Through a Link, a name the Pair answers reads the Pair. | Filter | **Brief** · STEP-23 r1.5. OQ1 asks whether a name both the Pair and the Contact hold should be refused. |
| `(charlie.Knows & bob.Knows).since` | Each Contact's own `since`: a combination sees no Link. | Projection | **Brief** · STEP-23 r1.5 |
| `(charlie.Knows.since < 2000) & bob.Knows` | Filter one Link by its Pair, then combine. | population | **Brief** · STEP-23 r1.5 |
| `Social.Knows == link` | Finds the Agent who holds that Link. | Filter | **Brief** · STEP-22 r6.5 |
| `Social.Knows(ruth)` | Refused: a Projection never applies a Tag. | TypeError | **Brief** · STEP-23 r1.9 |
| `Enemy.Take_Damage(5)`, alone on a line | A question nobody walks. It does nothing, and warns. | RuntimeWarning | **Brief** · STEP-23 r3.3. STEP-25 r6.4 makes the warning name the loop. |
| `Wizard.hp = 10`, over a declared Report `hp` | Changes the shared value. | none | **On main** · §1.4 |
| `Wizard.hp = 10`, over a Record or Action `hp` | **Today:** sets a value on the Tag. Before the Tag's first use it erases the Record, so new Wizards get no `hp`. After, Agents still get `hp`, but `Wizard.hp` and its Shapes' `.hp` read 10. | none | **On main (kit only)**: a defect. STEP-23 section 6 calls it a category error. |
| `Wizard.hp = 10`, `del Wizard.hp` (a name the Tag gives its Agents) | Refused, before anything changes. | TagCompositionError (STEP-25 r4.2, PR #28) or `TagCategoryError` (STEP-28 r3, PR #26): the two Briefs disagree. | **Brief** · STEP-25 r4.2; STEP-28 r3. The Director: "should probably rise a category error, as it is probably a misconception." |
| `Wizard.level = 3`, where `level` is new on the Tag and the members hold it | Sets a value of the Tag, and warns, naming the population spelling. | warning | **Brief** · STEP-25 r4.3 · PR #28 |
| `Wizard[:].hp = 10` | **Today:** stored on the Field object. No member changes. | none | **On main (kit only)** |
| `Wizard[:].hp = 10` | **STEP-25:** writes `hp` on every member, all or nothing. (STEP-23 r1.4 refused it; STEP-25 amends that.) | none | **Brief** · STEP-25 r1.1, r3.2 · PR #28 |
| `(Enemy[:] & Enemy).hp = 10` | Writes the sound Enemies only. | none | **Brief** · STEP-25 r1.2 |
| `(~Enemy).hp = 10` | Writes each defective Enemy, from a snapshot taken at the start. Today the write is lost. | none | **Brief** · STEP-25 r1.1, r3.1 |
| `(Enemy[:].hp < 5).hp = 5` | Writes every Enemy that was weak at the start. | none | **Brief** · STEP-25 r3.1 |
| `Wizard[:].spells = []` | Every Wizard gets the same one list. Nothing is copied. | none | **Brief** · STEP-25 r1.4, OQ3 |
| `Enemy[:].hp = Enemy[:].max_hp` | Refused: a Projection is never a value. | TypeError | **Brief** · STEP-25 r1.5 |
| `Enemy[:].hp_ = 10` (a misspelt name) | Refused: a write never creates a name. | TagCompositionError | **Brief** · STEP-25 r2.1 |
| `Rare[:].rarity = "common"` | Writes each pinned Tag's own value. | none | **Brief** · STEP-25 r1.6 |
| `charlie.Knows[:].since = 2011` | Writes every Pair. Never the Contact. | none | **Brief** · STEP-25 r5.1 |
| `(charlie.Knows & bob.Knows).since = 2011` | Refused: a combination sees no Link, so it would write the Contacts. | error | **Brief** · STEP-25 r5.3 |
| `charlie.Knows.since = 2011` | Refused: `since` is a Record the Link gives its Pairs. The message shows `charlie.Knows[:].since = 2011`. | TagCompositionError | **Brief** · STEP-25 r5.4 |
| `Social.Knows[:].since = 2011` | Refused: a fan-out is a Projection, not a population. | error | **Brief** · STEP-25 r5.5 |
| `Enemy[:].hp -= 5` | Refused: a Projection has no arithmetic. | TypeError | **Brief** · STEP-25 section 7 |
| `(0 < Enemy.hp < 5).hp = 5` | Fails before anything is written: a Filter refuses `bool()`. | TypeError | **Brief** · STEP-25 section 7 |
| `Enemy[:].weapon.damage = 3` | Refused: it assigns on a Projection. | error | **Brief** · STEP-25 section 7 |
| `Enemy.Volley(5)`, where `Volley` is an Operation that walks its Field | Runs now, because it is a Tag's own name. | none | **On main** (Operations, §1.4). Taught by **Brief** STEP-25 r6.3. |
| `for e in Enemy: e.Take_Damage(5)` | The command to each member, one by one. | none | **On main** · §0.8. STEP-25 r6.2 teaches it. |
| `Each(Enemy).Take_Damage(5)` | A function for a broadcast. | none | **Set aside for now** · STEP-25 Alternatives; open in STEP-25 OQ1 |
| `Where(Wizard, lambda w: w.level > 3)` | A filter function. | none | **Set aside** · STEP-23 Alternatives (Brief) |

## 7. Links

All **Brief**, in STEP-SPEC-22 on PR #26. A Relation is declared inside a Tag:

```python
class Social(Tag):

    @Link
    class Knows(Tag):                                # the Relation: each Social Agent gets its own Link

        @Record
        def since(agent, contact, *, since=None):    # a Record of the Pair
            return since

        @Public
        def Greet(agent, contact):                   # seen by the Contact: ruth.Greet()
            return f"{agent.name} waves at {contact.name}"

        @Secret
        def Rate(agent, contact):                    # in-house: the Link's Agent's own code only
            return 5
```

`Link` is not in any kit yet, so this block parses but does not run.

Three points are decided by the Director (2026-10-08):
- **The words.** "It is the Link's agent and the Link's Contact." (STEP-22 Rationale, *The Link's Agent, the Link's Contact*; the words are fixed in section 1)
- **Who sees what.** `@Public` means "seen by the Contact". `@Secret` means in-house, the Link's Agent's alone: "Secret stays inhouse, the contact is external by default." (STEP-22 r2.7)
- **No fan-out.** "a Link may establish a line, not an open connection." (STEP-22 r2.7)

Two Agents at the same level are not a Link: they are members of one ordinary Tag whose Precondition keeps its Field at two (STEP-22 section 1).

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `charlie.Knows(ruth)`, `charlie.Knows(ruth, since=2010)` | Link ruth to charlie: ruth becomes a Contact of charlie's Link. | ruth | **Brief** · STEP-22 section 5 |
| `charlie.Trusts(ruth)`, where `Trusts` extends `Knows` | Links through the Base Links first, so `ruth in charlie.Knows` too. | ruth | **Brief** · STEP-22 r5.2 |
| `charlie.Knows[ruth] is charlie.Trusts[ruth]` | True: one Pair for each Contact, across a Link's Form. | bool | **Brief** · STEP-22 r5.3 |
| `ruth in charlie.Knows` | Is ruth linked now? (Written with main's meaning of `in`.) | bool | **Brief** · STEP-22 section 5 |
| `isinstance(ruth, charlie.Knows)` | Was ruth ever linked? | bool | **Brief** · STEP-22 section 5 |
| `for c in charlie.Knows:` | charlie's sound Contacts. Both the Contact's own contract and her Pair must hold. | iterator | **Brief** · STEP-22 section 5, r7.3 |
| `~charlie.Knows` | Contacts whose own contract, or whose Pair, is broken. A broken Pair does not make the Contact defective anywhere else. | population | **Brief** · STEP-22 section 5, r7.3 |
| `charlie.Knows[:]` | All of charlie's Contacts. | population | **Brief** · STEP-22 section 5 |
| `charlie.Knows & bob.Knows`, and `\|`, `-` | Contacts of both Links (or either, or one without the other). | population | **Brief** · STEP-22 section 5 |
| `charlie.Knows[ruth]` | The Pair (section 5). | Pair | **Brief** · STEP-22 r7.1 |
| `charlie.Knows[ruth].since`, `charlie.Knows[ruth].Greet()`, `charlie.Knows[ruth].Still_Honest` | The Pair's Record; the Pair's Action; one of the Pair's conditions, read by name. | value | **Brief** · STEP-22 r7.2 |
| `charlie.Knows[ruth].since = 2011` | Write the Pair's Record. | none | **Brief** · STEP-22 r7.2 |
| `bool(charlie.Knows[ruth])` | Is the Pair sound? | bool | **Brief** · STEP-22 r7.3 |
| `"Trusted" in charlie.Knows[ruth]` | A Flag Link answers its words on the Pair, never on the Contact. | bool | **Brief** · STEP-22 r2.3 |
| `ruth.Greet()`, where `Greet` is `@Public` | Seen by the Contact. It runs as `Greet(charlie, ruth)`, inside the Link's own code. It never calls every Pair that holds ruth. If two Links publish `Greet` onto her, the last linking wins, with the usual Overwrite Warning between independent Tags. | value | **Brief, decided** · STEP-22 r2.7 |
| `ruth.capacity`, where `capacity` is a `@Public` Report of the Link | The Link's Report, seen by its Contacts. | value | **Brief, decided** · STEP-22 r2.7 |
| A `@Secret` member of the Pair or of the Link | In-house. It resolves only inside the Link's own functions, the Link's Agent's code. The Contact never sees it and never calls it. | value, inside the Link only | **Brief, decided** · STEP-22 r2.7 |
| `ruth.Greet()`, after `del charlie.Knows[ruth]` | The line is dead but still on top. It raises a Rogue Access Failure, and her own `Greet` beneath never answers again. | TagRogueAccessError | **Brief** · STEP-22 r2.7 (§1.5). OQ4 proposes taking the line off her when the Pair ends. |
| A `@Public` `Greet` linked onto a ruth who already has a `Greet` | Today's rule (§1.5): it lands on top and replaces hers, for every caller. | none | **Brief** · STEP-22 r2.7. OQ4 proposes a refusal unless the Relation declares `@Underlay` (a Composition Failure). |
| `charlie.Knows.capacity` | A Report of the Link. | value | **Brief** · STEP-22 r2.3 |
| `charlie.Knows is not bob.Knows` | Each Agent's Link is its own Tag. | bool | **Brief** · STEP-22 r4.2 |
| `ruth.Knows` | ruth's own Link, if she holds one. Never another Agent's Link. | Link, or AttributeError | **Brief** · STEP-22 r6.2 |
| `Social.Knows` | Without STEP-23: the Relation, and every act on it is refused. With STEP-23: a Projection of each sound Agent's Link. In a class statement's Bases: always the Relation. | Relation, or Projection | **Brief** · STEP-22 section 9. The design panel proposes: always the Relation. |
| `x in Social.Knows`, `isinstance(x, Social.Knows)`, `Social.Knows & bob.Knows`, `Scope(x, Social.Knows)` | Refused. A Relation has no Field, and nothing walks back from a Contact. | error | **Brief** · STEP-22 section 9. STEP-28 r3 names `isinstance(x, Social.Knows)` and `Scope(x, Social.Knows)` as `TagCategoryError`. |
| `charlie.Knows = None`, `del charlie.Knows` | Refused: a held Link is read-only. | TagCompositionError | **Brief** · STEP-22 r4.3 |
| `Owners(ruth, Social.Knows)` | A function that walks back from a Contact. | none | **Rejected** by the Director · STEP-22 Alternatives |
| A `@Public` Pair member on the Contact that calls every Pair holding her (fan-out) | Two behaviours for one spelling. | none | **Rejected** by the Director · STEP-22 Alternatives |

Unlinking is in section 8.

## 8. Deletion: every `del` and every ending

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `del Wizard[ari]` | **Rip.** ari leaves the Field; then Wizard's teardowns run. What Wizard gave stays on ari. | None | **On main** · §0.7 |
| `del Officer[ari]`, while ari is a Wizard | **Today:** refused: "Officer is required by active Shape(s): Wizard". Rip the Shape first. Same on PR #26 and S19. | TagCompositionError | **On main** · §0.7 |
| `del Officer[ari]`, while ari is a Wizard (STEP-26's example: `del Human[bob]` while bob is a Werewolf) | **STEP-26:** ari leaves Officer, Officer's teardowns run, and ari stays a Wizard: a spin-off. Nothing cascades. What Officer gave stays. ari loses Officer's view and Officer's Flag words. Officer's published members refuse ari too, today (STEP-26 OQ1). | None | **Brief** · STEP-26 r2.1 · PR #26. Model decided by the Director (2026-10-08): "a shape should not keep a base hostage." Open questions remain. |
| `del charlie.Knows[ruth]`, while `charlie.Trusts` holds her | Not refused. She leaves `charlie.Knows`, stays in `charlie.Trusts`, and her Pair stays. | None | **Brief** · STEP-22 r5.2 (revised), STEP-26 r2.3 |
| `del Rare[Sword]`, while `Legendary(Sword)` is active (`Legendary` a Shape of the Pin `Rare`) | **Today:** refused. **STEP-26:** works; Sword stays Legendary. | TagCompositionError today | **On main** · §0.7. **Brief** · STEP-26 r8.1 |
| `del Wizard[dee]`, where dee is not a member | Fails. | TagResolutionError | **On main** · §0.7 |
| `del Wizard[ari]`, and a teardown fails | **main:** ari has already left, and stays out. The error is raised. | TagCompositionError | **On main** · §3.1 |
| `del Wizard[ari]`, and a teardown fails | **S19:** the Rip is refused and rolled back. ari is a member again, and the teardowns are due again. | TagCompositionError | **Vetting** · S19 · STEP-18 amendment D. STEP-24 OQ1 may change it. |
| `del Wizard[:]` | **Today:** the slice is read as an Agent, so it fails. | TagResolutionError | **On main (kit only)**, on main and S19 |
| `del Wizard[:]` | **Field Rip.** Everyone leaves first; no user code runs in that phase. Then each member's teardowns run. Both phases go in join order. Failures are collected and raised once, at the end. A member that holds a Shape of Wizard leaves Wizard and keeps the Shape. | None | **Brief** · STEP-24 r1.1 to r1.5 · PR #26. Join order and "everyone leaves first" decided by the Director (2026-10-08). |
| `del Rare[Wizard]` | Un-pin Wizard. The Pin's teardowns run. What the Pin gave stays. | None | **On main** · §1.9 |
| `del Rare[:]` | Un-pin every Tag. | None | **Brief** · STEP-24 r1.6 |
| `del charlie.Knows[ruth]` | Unlink ruth. She leaves; the teardowns run with charlie and ruth; then the Pair ends, unless a Link of the same Form still holds her. | None | **Brief** · STEP-22 r8.1 |
| `del charlie.Knows[:]` | Unlink every Contact: a Field Rip of the Link. | None | **Brief** · STEP-22 r8.2; STEP-24 r1.6 |
| `del Social.Knows[ruth]`, `del Social.Knows[:]` | Refused: a Relation has no Field. | error | **Brief** · STEP-22 section 9 |
| `del k[ruth]`, where `k = charlie.Knows` outlived charlie | Fails. | TagResolutionError | **Brief** · STEP-22 r5.8 |
| `del Wizard[...]` | **main:** read as an Agent, so it fails. | TagResolutionError | **On main (kit only)** |
| `del Wizard[...]` | **S19: Triage.** Each kept Agent is Ripped from all its Tags with no teardowns, taken out, and let go. One `TagTriageWarning` each. Never refused. | None, and warnings | **Vetting** · S19 · STEP-18 amendment F |
| `del Tag[...]` | **S19:** triage of the whole safehouse. | None, and warnings | **Vetting** · S19 · STEP-18 amendment F |
| `del Cached[kept]`, when Cached keeps that Agent | **S19:** a Rip that goes through also takes it out of the safehouse. | None | **Vetting** · S19 · STEP-18 item 12 |
| `del ari` (the last reference goes) | **main:** the teardowns run while ari is still a member (§3.2 line 1225 says deletion "Rips", but the kit does not), then the `__del__` Layers. A failed teardown is silent. | none | **On main** · §3.2 (STEP-18 at Vetting) |
| `del ari` (the last reference goes) | **S19:** the teardowns run the same way. If one fails, ari is rolled back and kept in the safehouse, the failure is reported, and the `__del__` Layers do not run. | none | **Vetting** · S19 · STEP-18 amendment E |
| An Agent that holds Links is deleted | Each of its Links is Field-Ripped inside its finalizer, Shape Links first. | none | **Brief** · STEP-22 r8.3 |
| A Pair ends with no teardown (for example, both sides collected together) | Under STEP-22's rules it ends silently. STEP-22 proposes one `TagUnlinkWarning` per Pair. | warning (proposed) | **Brief** · STEP-22 r8.3, r8.4, r8.7. The warning is proposed in OQ3. |
| `del Wizard` | Removes the *name* `Wizard`. It calls nothing on the Tag. Today the Tag lives on through its members. | None | **On main** (Python's own meaning) |
| A Tag that nobody can reach any more | **STEP-24:** at the next collection, its Field is Ripped, Shapes before Bases. Best effort; failures silent (OQ1 asks again). | none | **Brief** · STEP-24 sections 2 and 3 |
| `with Scope(ari, Wizard):` (on exit) | **main:** Rips only what the Scope applied, in reverse order. A failed Rip on exit is swallowed. | context manager | **On main** · §0.7, §3.2. The swallowing is kit only, `TopKit/lifecycle.py:207-208` (`except TagError: pass`). |
| `with Scope(ari, Wizard):` (on exit) | **S19:** the same, but a failed or refused Rip is reported. | context manager | **Vetting** · S19 · STEP-18 amendment D; STEP-6 rows 4 and 5 (drafted for the Director's confirmation). With STEP-26, a Scope that applied a Base Rips it on exit and the Agent leaves as a spin-off (STEP-26 r8.2). |
| `At_Exit(ari)` | Also run ari's teardowns at normal interpreter exit. | ari | **On main** · §3.2. STEP-22 r8.3 adds: it ends ari's Links too. |
| `Contract.Delete(ari, "Alive")` | Ends one named condition, from a `@Rip` protocol. Membership is untouched. | None | **On main** · §0.7. STEP-20 (PR #27) notes it ends the whole shared name. |
| `@Delete` on a function in a Tag | Removes the visible contribution of that name. | declaration | **On main** · §1.6 |
| `del Enemy[:].hp` | **Today:** deletes a value that `Enemy[:].hp = 10` stored on the Field object; otherwise AttributeError. **STEP-25:** refused, because it reads too much like `del Enemy[:]`. | None, or AttributeError today | **On main (kit only)**. **Brief** · STEP-25 section 7 |
| `del (~Wizard)[:]` | Legal Python, but no kit or STEP gives it a meaning. | TypeError today | **No status**. See section 12. |
| `Close(Wizard)`, `Wizard[:].clear()` | Function or method spellings for a Field Rip. | none | **Set aside** · STEP-24 Alternatives (Brief) |

**Still open.** STEP-24 open question 1 asks where an Agent goes when a teardown fails:
- (a) arrested: kept in the safehouse as a non-member, for every Rip;
- (b) the act decides: a demanded Rip rolls back, an ending arrests;
- (c) out, as the kit does today.

The STEP recommends (a). The Director has not ruled. He said on 2026-10-08: "The safehouse: ends membership first and runs teardowns after is the sensible choice." If (a) is chosen, three S19 rows change: the failed Rip (`del Wizard[ari]`, amendment D), the deletion (`del ari`, amendment E) and the Scope's exit. If (b) is chosen, the S19 deletion row changes.

### Which `del` do I want?

- **One Agent leaves one Tag:** `del Wizard[ari]`.
- **One Agent leaves a Base and keeps the Shape** (STEP-26, Brief): `del Officer[ari]`. Today this is refused; under today's rule, Rip the Shape first.
- **One Tag leaves one Pin:** `del Rare[Wizard]`.
- **One Contact leaves one Link** (Brief): `del charlie.Knows[ruth]`.
- **Everyone leaves one Tag:** `del Wizard[:]` (Brief, not built). Today, write the loop: `for w in list(Wizard[:]): del Wizard[w]`. It stops halfway if a teardown fails, or, under today's rule only, if a member still holds a Shape of Wizard.
- **Only the defective ones leave:** there is no single spelling. Write `for w in list(~Wizard): del Wizard[w]`.
- **An Agent joins for a while, then leaves:** `with Scope(ari, Wizard):`.
- **End one promise, not the membership:** `Contract.Delete(ari, "Alive")`, from the Tag's `@Rip` protocol.
- **Give up on Agents stuck in the safehouse** (S19 only): `del Wizard[...]`, or all of them with `del Tag[...]`.
- **Forget a name in your module:** `del Wizard`. This ends nothing by itself.
- **Do not write** `del Enemy[:].hp` or `del charlie.Knows`. Brief: STEP-25 section 7 refuses the first; STEP-22 r4.3 refuses the second.

## 9. Pins and Flags

A Pin is a Tag applied to Tags. Every basic act (apply, ask, walk, view, Rip) works on it, with a Tag in the Agent's seat.

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `Rare(Wizard)` | Pin the Tag Wizard. | Wizard | **On main** · §1.9 |
| `Wizard in Rare` | **main:** is Wizard pinned now? | bool | **On main** · §1.9 |
| `Wizard in Rare` | **S19:** is Wizard pinned now, and sound? | bool | **Vetting** · S19 · STEP-19 item 4 |
| `Wizard in Rare[:]`, `Wizard in ~Rare` | Pinned at all; pinned and defective. | bool | **On main** · §1.9 |
| `for tag in Rare:`, `Rare[:]`, `~Rare` | Rare's populations. Their members are Tags. | population | **On main** · §0.8, §1.9 |
| `isinstance(Wizard, Rare)` | Was Wizard ever pinned? | bool | **On main** · §1.9 |
| `Rare[Wizard]`, `Wizard.Rare` | The Pin's view of Wizard (section 5). | view | **On main** · §1.9 |
| `Rare - Deprecated` | Pins combine with Pins. | population of Tags | **On main** · FIELDS guide |
| `Wizard.Has_Members` | A pinned Tag's own condition, read by its name. | bool | **On main** · §2.5 (STEP-14 at Vetting) |
| `"Deprecated" in Wizard` (Deprecated is a Flag Pin) | Does Wizard carry the keyword? | bool | **On main** · §1.9 |
| `Keyword(Wizard, "Deprecated")`, `Keyword(Wizard, Deprecated)` | The same question, as a function. | bool | **On main** · §1.9 |
| `Deprecated in Wizard` (the class, on the Tag's side) | Careful: asks whether the class Deprecated is a *member* of Wizard's Field. It is `False`. | bool | **On main** · §1.9 |
| `"Deprecated" in Wizard[:]` | `False`: a Field has no keyword seat. | bool | **On main (kit only)** |
| `f"{Wizard:pins}"` | Wizard's Pins, as text. | str | **On main** · §0.8 |
| `"Undead" in ghoul`, `Undead in ghoul` | Does the Agent carry the keyword, by name or by class? | bool | **On main** · §1.8 |
| `Keyword(ghoul, "Undead")` | The same, as a function. Works on any object. | bool | **On main** · §1.8 |
| `"Undead" in cal`, where cal carries no Flag at all | The Agent has no `in` of its own, so Python refuses. Use `Keyword`. | TypeError | **On main (kit only)** |
| `"Wolf" in howler`, after `@Flag("Wolf", "Lycanthrope")` | A Flag's extra words. | bool | **On main** · §1.8 (STEP-17 at Vetting) |
| `@Flag(["Wolf", "Beast"])` | **main:** refused at the decorator: words must be plain strings. | TagDeclarationError | **On main** · §1.8 |
| `@Flag(["Wolf", "Beast"])`, `@Flag("Wolf", {"Lycan", "Lupus"})` | **S19:** a list or set of strings stands for its words. | declaration | **Vetting** · S19 · STEP-17 item 8 |

Mixing a Pin's population with a Tag's is in section 4. Applying a Pin to an object is in section 1.

## 10. Functions and named failures

TOP keeps functions for queries that need a name (§0.8).

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `Form(Wizard)`, `f"{Wizard:form}"` | Wizard's Bases and Wizard, Base first. | tuple, str | **On main** · §0.8 |
| `Tags(ari)`, `f"{ari:tags}"` | ari's active Tags, in the order applied, without the Bases their Shapes bring. With the cast, `Tags(ari)` is `(Wizard,)`, with no Officer. | tuple, str | **On main** · §0.8 |
| `Outline(ari)`, `f"{ari:outline}"` | ari's Tags as an indented outline. | str | **On main** · §0.8. STEP-26 OQ4 asks how it should show a Base that a spin-off left. |
| `Keyword(x, "Undead", "Flying")` | Does x carry every word? | bool | **On main** · §1.8 |
| `Apply(ari, Wizard, Sworn)` | Apply several Tags, in order. | ari | **On main** · §0.8 |
| `Scope(ari, Wizard)` | Apply for a `with` block; Rip on exit (section 8). | context manager | **On main** · §0.7 |
| `At_Exit(ari)` | Run ari's teardowns at normal exit too (section 8). | ari | **On main** · §3.2 |
| `Contract.Holds(ari)` | Do all ari's promises hold? | bool | **On main** · §2.6 |
| `Contract.Status(ari)` | Each condition by name, `True` or `False`. Never raises. | dict | **On main** · §2.6 |
| `Contract.Postconditions(ari)`, `Contract.Preconditions(ari)`, `Contract.Conditions(ari)` | `True`, or raise the named failure. | bool | **On main** · §2.6 |
| `Contract.Display(ari)`, `f"{ari:contract}"`, `f"{Wizard:contract}"` | The contract, as text. | str | **On main** · §2.6 |
| `Contract.Delete(ari, "Alive")` | End one named condition (section 8). | None | **On main** · §0.7 |
| `except Postcondition.Alive:` | Catch one named check's failure. | exception class | **On main** · §2.6 |
| `TagTriageWarning` | The warning triage gives, one per Agent. | warning class | **Vetting** · S19 · STEP-18 amendment F |
| `TagUnlinkWarning` | A warning for a Pair that ends without its teardowns. It names the Relation and the Contact, never the Link's Agent. | warning class | **Brief** · STEP-22 OQ3 (proposed there) |
| `TagCategoryError` | The Tag Category Failure: a program treats one kind of TOP thing as another. It is a `TagError` and a `TypeError`, so `except TypeError` still catches it. Nothing changes when it is raised. | exception class | **Brief** · STEP-28 · PR #26. Asked for by the Director: ""Category error" should be a type of error in tags. it will come in handy." |
| `Each(...)`, `Where(...)`, `Close(...)`, `Owners(...)` | Functions TOP has not added. | none | **Set aside** (`Each`, `Where`, `Close`) or **Rejected** by the Director (`Owners`): sections 6, 7 and 8 |

## 11. Python's own tools on a population

These are plain Python. They work on main's kit today, because a Tag walks like any collection. Their meaning is Python's, so read the cautions.

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `all(w.level > 3 for w in Wizard)` | Is every sound Wizard above level 3? True over an empty Tag: nobody broke the rule. | bool | **On main** · §0.8 (the walk). The Guide on PR #26 teaches it ("Reading a Tag"). |
| `any(w.level > 3 for w in Wizard)` | Is at least one sound Wizard above level 3? False over an empty Tag. | bool | **On main** · §0.8. The Guide on PR #26 teaches it. |
| `all(Wizard)`, `any(Wizard)` (nothing inside) | Not "is anyone there?". It asks each sound member for its own truth. For most Agents that is the contract, so `all(...)` is True. A host with its own `__bool__` answers for itself, and so does a host with `__len__` while no promise is visible on it: with an empty `Shelf` Agent, `all(Scholar)` is False while `bool(Scholar)` is True. Use `if Scholar:` to ask whether anyone is there. | bool | **On main** (Python's own meaning). The Guide on PR #26 warns about it. |
| `match ari:` with `case Wizard():` | A class pattern calls `isinstance`, which in TOP means "was ever a Wizard". An Agent Ripped from Wizard still matches. To ask "a member now", add a guard: `case Wizard() if ari in Wizard[:]:`. | match | **On main** (Python's own meaning; §0.3 for `isinstance`) |
| `case Wizard(level=lvl) if lvl > 10:` | The same `isinstance` test, then it reads `ari.level`. The same caution. | match | **On main** (Python's own meaning) |
| `match list(Wizard):` with `case []:` | Nobody is sound now. | match | **On main** (Python's own meaning) |
| `match list(Wizard):` with `case [only]:` | Exactly one sound Wizard: iota, "the only one". | match | **On main** (Python's own meaning) |
| `match list(Wizard):` with `case [first, *rest]:` | The first sound Wizard in join order, and the rest: one way to write epsilon, "any one". | match | **On main** (Python's own meaning) |
| `[w] = Fighter[:]` | Unpacking: exactly one member, or a ValueError. With the cast, `w` is cal. `[w] = Wizard` fails: "too many values to unpack (expected 1)". The messages do not mention TOP. | Agent | **On main** (Python's own meaning) |
| `next(iter(Wizard), None)` | The first sound member, or `None` if there is none. It does not check that there is only one. | Agent or None | **On main** (Python's own meaning) |
| `list(Wizard)`, `enumerate(Wizard)` | A frozen list; numbers in join order. Take the list first when you need numbers that do not move. | list, iterator | **On main** · §0.8 |

`all()` and `any()` always return a plain `True` or `False`. Python gives a class no way to change that, so they can never pick members. The Director asked whether they could "work as set selectors". They cannot (probe: no hook exists).

A short example, on the cast. It runs on main, on PR #26 and on S19:

```python
def describe(agent):
    match agent:
        case Wizard() if agent in Wizard[:]:   # a member now
            return "a Wizard now"
        case Wizard():                         # isinstance: was ever a Wizard
            return "was a Wizard once"
        case _:
            return "never a Wizard"

def pick(population):
    match list(population):                    # a frozen list, in join order
        case []:
            return None                        # nobody
        case [only]:
            return only                        # exactly one: iota
        case [first, *rest]:
            return first                       # the first of many: one way to write epsilon

dee = Crew("dee")
Wizard(dee)
del Wizard[dee]                                # dee leaves Wizard

assert describe(ari) == "a Wizard now"
assert describe(dee) == "was a Wizard once"
assert pick(Fighter[:]) is cal                 # cal is the only Fighter
assert pick(Fighter) is None                   # cal is defective, so no Fighter is sound
assert pick(Wizard) is ari                     # ari joined first
```

## 12. Not Python

Python cannot read these. Each row gives the nearest legal spelling.

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `Wizard[]` | Python needs a key inside `[ ]`. Nearest: `Wizard[:]`, the whole Field, or bare `Wizard` for the sound members. The design panel proposes `Wizard[Sound]`. | SyntaxError: invalid syntax | **Not Python** |
| `Wizard[*]` | A star needs a name after it. Nearest: `Wizard[:]`. (`Wizard[*keys]` is legal from Python 3.11, and passes a tuple as the key.) | SyntaxError: Invalid star expression | **Not Python** |
| `if Wizard as w:` | `as` binds a name only after `with`, `except`, `import` and in `case` patterns. Nearest: `if (w := next(iter(Wizard), None)) is not None:` | SyntaxError: invalid syntax | **Not Python** |
| `if (Wizard.can_dance)[0] as w:` | The same reason. Nearest, under the proposals: `if len(dancers) > 0: w = dancers[0]` (see "Proposed"). | SyntaxError: invalid syntax | **Not Python** |
| `for Wizard as w:` | Nearest: `for w in Wizard:` | SyntaxError: invalid syntax | **Not Python** |
| `for Wizard[].level as l:` | Nearest today: `for w in Wizard: l = w.level`. Under STEP-23: `for l in Wizard.level:`. Under the panel's proposal: `for l in Wizard[Sound].level:` | SyntaxError: invalid syntax | **Not Python** |
| `for all(Wizard) as w:` | Nearest: `for w in Wizard:`. `all()` gives one bool, never members. | SyntaxError: cannot assign to function call | **Not Python** |
| `if any(Wizard) as w:` | Nearest: `if len(Wizard) > 0: w = next(iter(Wizard))` | SyntaxError: invalid syntax | **Not Python** |
| `del ~Wizard` | `del` takes a name, an attribute or a subscript. Nearest: `for w in list(~Wizard): del Wizard[w]` | SyntaxError: cannot delete expression | **Not Python** |

Three cautions:
- `del (~Wizard)[:]` *is* legal Python. But no kit and no STEP gives it a meaning, and today it raises TypeError.
- `next(iter(Wizard), None)` quietly takes the first sound member. It does not check that there is only one. In TOP, `None` can never be an Agent (`Wizard(None)` is refused), so `None` safely means "nobody".
- Write the brackets with `:=`. `if w := next(iter(Wizard), None) is not None:` is legal, but binds `w` to a bool.

## 13. Same thing, two spellings

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `Wizard[::]` | Exactly `Wizard[:]`. Python passes the same key, `slice(None, None, None)`, and compiles both to the same instructions (bytecode). `Wizard[::] is Wizard[:]` is `True`. The kit cannot tell them apart, so they can never mean different things. | population | **On main (kit only)** |
| `del Wizard[::]` | Exactly `del Wizard[:]`, for the same reason. | as `del Wizard[:]` | **On main (kit only)** |

The Director asked: "Wizard[::] this one is free?" No: it is already `Wizard[:]`.

Same meaning, but not the same object:
- `Wizard[ari]` and `ari.Wizard` give the same view. `ari.Wizard is Wizard[ari]` is `False`.
- `"Undead" in ghoul`, `Undead in ghoul` and `Keyword(ghoul, "Undead")` ask the same question.
- `Wizard`, `~~Wizard` and `Wizard[:] & Wizard` hold the same members: the sound ones.
- `ari in Wizard` and `ari in Wizard[:]` give the same answer on main. On S19 they differ for a defective ari.

They look alike, but differ:
- `Tag[:]` is always empty. On S19, `Tag[...]` is everyone kept in the safehouse.
- `Wizard[ari]` is a snapshot. On a Link, `charlie.Knows[ruth]` is the live Pair (Brief).
- `del Wizard[:]` Rips everyone (Brief). `del Wizard[:].hp` deletes a name, and STEP-25 refuses it.
- `Enemy.Volley(5)` (an Operation) runs now. `Enemy.Take_Damage(5)` (an Action, under STEP-23) only asks.
- `~Wizard.level` is `~(Wizard.level)`. `(~Wizard).level` reads the defective members.
- `len(f) > 0` asks "anyone?". `any(f)` asks each member's own truth.
- `ari in Wizard` asks "now". `isinstance(ari, Wizard)` and `case Wizard():` ask "ever".

---

## Proposed in today's discussion (2026-10-08)

The Director's sketches started this (his words, verbatim):
- "Wizard[] : sound ones"
- "Wizard[*] any one wizard?"
- "Wizard[0], Wizard[1], ... Wizard[n] : the wizard at the position of the list n while n<=len(Wizard)"
- "Wizard.level makes it so the record looks like a report, an also doesn't individually tell you what is going on. It's a lot of implicit going on there. Maybe we can do a for Wizard[].level as l:"
- "also pure booleans should also be available filters"

A design panel answered: three designers (python-native, algebra-purist, explicit-readable) and one judge. The judge adopted the explicit-readable set, with two parts taken from the others: `P[True]` and `P[False]` from algebra-purist, and the refusal of a shared name through a Link from python-native.

Most rows below are **Proposed (design panel, 2026-10-08; not in a STEP yet)**. Some are recorded in STEP-23's open questions, and those rows say so. No kit has any of it: `from TopKit import Sound` fails with an ImportError today. STEP-23 open question 2 says positions, `Only` and `P[True]` "belong to a STEP of their own".

### The explicit root, and the dot

All three designers agreed: **the dot on a Tag reads only the Tag**, and the members are reached through brackets.

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `Wizard[Sound]` (`Sound` imported from TopKit) | The sound members, named. The same members as bare `Wizard`. Needed only before a dot, or as the target of a write. "Sound" is TOP's own word. | population | **Proposed** (design panel, 2026-10-08) · recorded as STEP-23 OQ2 (Brief) |
| `X[Sound]`, on any population | The sound members of X. | population | **Proposed** · recorded as STEP-23 OQ2 |
| bare `Wizard` in `for`, `len`, `if`, `in`, `\|`, `&`, `-` | Unchanged: the sound members, in join order. | population | **On main** · §0.8; kept by the panel |
| `Wizard.colour` (a Report) | The dot on a Tag reads only the Tag: a Report, an Operation, what a Pin lands, or a Link's Relation. | value | **Proposed** · recorded as STEP-23 OQ2 |
| `Wizard.level` (a name the Tag's Agents have) | Refused, with a hint naming `Wizard[Sound].level` and `Wizard[:].level`. So `hasattr(Wizard, "level")` stays False. | AttributeError | **Proposed** · recorded as STEP-23 OQ2 |
| `Wizard[Sound].level`, `Wizard[Sound].level > 3`, `for level in Wizard[Sound].level:` | A Projection and a Filter rooted on the sound members. | Projection, Filter | **Proposed** · recorded as STEP-23 OQ2 |
| `Wizard[Sound].colour` | The Agents' own `colour`, when the Tag also has a Report `colour`. It replaces `(Wizard[:] & Wizard).colour`, and STEP-23 rule 1.3 goes. | Projection | **Proposed** · recorded as STEP-23 OQ2 |
| `Wizard[Sound].hp = 10`, `(Wizard[Sound].hp < 5).hp = 5` | Write each sound member, all or nothing (with STEP-25). The Director's one-line write over the valid members. | none | **Proposed** · recorded as STEP-23 OQ2 |
| `Wizard.hp = 10` (hp a Record) | Refused, naming `Wizard[Sound].hp = 10`. | error (`TagCategoryError` under STEP-28) | **Proposed** (design panel, 2026-10-08; not in a STEP yet). STEP-28 (Brief) already names the failure. |
| `charlie.Knows[Sound].since` | The sound Pairs' `since`. It replaces `charlie.Knows.since`. | Projection | **Proposed** (design panel, 2026-10-08; not in a STEP yet) |
| `Social.Knows` | Always the Relation. STEP-22 section 9's other routes go. | Relation | **Proposed** (design panel, 2026-10-08; not in a STEP yet) |
| Through a Link, a name both the Pair and the Contact hold | Refused at the walk, naming both spellings. So the answer can never change silently. | error | **Proposed** (design panel, 2026-10-08) · recorded in STEP-23 OQ1, as the panel's answer |

### Picking one member

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `Wizard[n]`, `X[n]` | The Agent at position n now, in join order. On a Tag, positions count the sound members. Valid n runs from 0 to `len - 1`; `-1` is the newest. | Agent; IndexError that names the count now | **Proposed** (design panel, 2026-10-08; not in a STEP yet) |
| `Wizard[0]` | "Any one" (epsilon): the oldest sound member. The order is first in, first out, so a newcomer never moves `[0]`. | Agent, or IndexError | **Proposed** (design panel, 2026-10-08; not in a STEP yet) |
| `X[Only]` (`Only` imported from TopKit) | "The only one" (iota): exactly one member. None or several raise a LookupError subclass that names the members found. | Agent | **Proposed** (design panel, 2026-10-08; not in a STEP yet) |
| `[w] = X` | Iota in Python's own words. It works today (section 11). | Agent, or ValueError | **On main** (Python's own meaning); kept by the panel |
| `Wizard[0].level` | Pick one Agent, then read it. | value, or IndexError at the pick | **Proposed** (design panel, 2026-10-08; not in a STEP yet) |
| `Wizard[:][0]` | The oldest of everyone, sound or broken. | Agent | **Proposed** (design panel, 2026-10-08; not in a STEP yet) |
| `random.choice(list(X))` | One at random, said in words. | Agent, or IndexError | **On main** (Python's own meaning); the panel's advice when "random" is really meant |

At one moment, `Wizard[0]`, `Wizard[Sound][0]` and `list(Wizard)[0]` are the same Agent. `Wizard[:][0]` differs only when an older member is broken. In the judge's demo, after ari breaks, `Wizard[0]` is bo and `Wizard[:][0]` is ari.

### Yes-or-no Projections

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `P[True]`, `P[False]`, for example `Wizard[Sound].can_dance[True]` | The root members whose value **is** True (or **is** False). `None` never matches. Any other value stops the walk and names the member. A missing name follows STEP-23 r1.7. | Filter | **Proposed** (design panel, 2026-10-08; not in a STEP yet) |
| `Wizard.level == True` | Unchanged: Python's own `==`. It keeps level-1 Wizards, because `1 == True` in Python. So the Guide would teach `[True]` for booleans. | Filter | **Brief** · STEP-23 r2.2 |

### Refused, each with a message naming the right spelling

| Spelling | Plain meaning | Result | Status |
| --- | --- | --- | --- |
| `Wizard[ari] = x` | Refused, pointing to `Wizard(ari)`. Today it fails with an unhelpful AttributeError, `__setitem__`. | error | **Proposed** (design panel, 2026-10-08; not in a STEP yet) |
| `Wizard[ari]`, when ari is not a member | Still the view (decided). The miss message names `ari in Wizard[:]`. | TagResolutionError | **Proposed** (design panel, 2026-10-08; not in a STEP yet) (the message) |
| `Wizard[True]`, `Wizard[()]`, `Wizard[a:b]`, `Wizard[a, b]` | Refused. | error | **Proposed** (design panel, 2026-10-08; not in a STEP yet) |
| `P[n]` | A Projection has no positions. The message points to `Wizard[n].name`. | error | **Proposed** (design panel, 2026-10-08; not in a STEP yet) |
| `~P`, a Projection in an operator seat | Refused; the message points to `[True]`. | error | **Proposed** (design panel, 2026-10-08; not in a STEP yet). STEP-23 r1.8 (Brief) already refuses them. |
| `del Wizard[n]`, `del Wizard[Only]` | Deleting by position is refused. | error | **Proposed** (design panel, 2026-10-08; not in a STEP yet) |

### Set aside by the panel

STEP-23 open question 2 lists the first five as "weighed and set aside".

| Spelling | Why | Status |
| --- | --- | --- |
| `Wizard[()]` | Legal, and closest to `Wizard[]`. But it is one shape away from a position, `Wizard[0]`, and both writes succeed silently. | **Set aside** (design panel; STEP-23 OQ2) |
| `Wizard[True]` as the root | `True` is `1` in Python, so a computed bool would pick a position. And an Agent's truth is not always its contract: a host with its own `__bool__` answers for itself, and so does a host with `__len__` while no promise is visible on it. | **Set aside** (design panel; STEP-23 OQ2) |
| `(+Wizard).level` | Python reads `+Wizard.level` as `+(Wizard.level)`. | **Set aside** (design panel; STEP-23 OQ2; also STEP-23 Alternatives) |
| `Wizard["level"]` (string keys) | A key that names an attribute, not a member. | **Set aside** (design panel; STEP-23 OQ2) |
| `Each(Wizard).level` | A function, where TOP prefers the language's own structures. | **Set aside** (design panel; STEP-23 OQ2) |
| `X[Anyone]` | It returns `None` quietly, and takes the Director's word "Anyone?", which he kept for the yes-or-no question. | **Set aside** (the judge) |

### The Director's sketches, as the panel would write them

Proposed spellings: this parses, but no kit runs it.

```python
import random
from TopKit import Sound, Only                 # proposed names: ImportError today

dancers = Wizard[Sound].can_dance[True]        # sound Wizards whose can_dance is True

if len(dancers) > 0:                           # the Director's sketch: if (Wizard.can_dance)[0] as w :
    w = dancers[0]                             # the oldest dancer
    w.Dance()

for w in Wizard[Sound].can_dance[True]:        # the Director's sketch: for Wizard.can_dance as w:
    w.Dance()

cannot_dance = Wizard[Sound].can_dance[False]  # "a valid wizard that cannot dance"
if len(cannot_dance) > 0:
    cannot_dance[0].Practice()

w = dancers[0]                                 # the Director's sketch: w = Wizard.can_dance
                                               # raises IndexError when nobody dances
w = random.choice(list(dancers))               # if "random" is really meant
w = dancers[Only]                              # exactly one dancer, or a LookupError

for level in Wizard[Sound].level:              # the Director's sketch: for Wizard[].level as l:
    print(level)
```

Notes from the panel, to pass on kindly:
- **About `as`:** it binds a name only in `with`, `except`, `import` and `match`.
- **About `~Wizard - Wizard.can_dance`:** it means the broken Wizards. For "cannot dance", use `[False]`.
- **About `assert w`:** it asks w's contract, not whether w exists, and `python -O` removes it. `dancers[0]` already fails loudly when nobody dances.

### Facts that bear on these

Checked with probes on Python 3.13.
- **Positions today.** `Wizard[0]` fails: the key is read as an Agent. No Agent can be an `int`, a `bool` or `None`: they cannot carry TOP state (section 1).
- **Positions, carefully.** `True == 1` in Python, so a position rule must test `type(k) is bool` first. An object with `__index__` can be an Agent (probe), so the rule must test `type(k) is int` and never use `operator.index` or `__index__`. The kit change would go in MetaTag's `__getitem__` (`TopKit/tags.py:212`).
- **Counting from 0.** The Director wrote "n<=len(Wizard)". Python counts from 0, so the last position is `len(Wizard) - 1`.
- **A position is read now.** A population is live. In one demo, `Wizard[1]` went bo, then cy, then bo, while nobody joined or left: bo broke a promise, then was repaired. A position returns an Agent, never a seat that follows. For numbers that do not move, take `list(Wizard)` first, or use `enumerate`.
- **The dot, in the kit.** Records and Actions are plain functions on the Tag's class (on HEAD, `Wizard.spells` gives a function). So refusing `Wizard.level` means intercepting the read. HEAD's `tags.py` has no `__getattr__` today.
- **Iota and the logic we already have.** The Director asked: "what is the difference of the iota and the logic we have already?" `|`, `&`, `-` and Filters answer with sets of zero, one or many Agents. Epsilon (`X[0]`) turns a set into one Agent, if there is one. Iota (`X[Only]`) also promises there is exactly one.
- **Traps for the Guide.**
  - `Wizard[Sound].level > 3 & Sworn` is read as `level > (3 & Sworn)`. It fails loudly. Write `(Wizard[Sound].level > 3) & Sworn`.
  - `~Wizard.rank`, where `rank` is an int Report, is silently `~3`. Write `(~Wizard).rank`.
  - `list(f)` walks a Filter twice, because `list()` asks `len()` first.

### If adopted, these STEPs change

- **STEP-23:** rules 1.1, 1.3 (deleted), 1.5, 1.6, 1.8 and 3.3, the examples, and a new rule for `P[True]` and `P[False]`. Its open questions 1 and 2 are answered.
- **STEP-22:** section 9: `Social.Knows` is always the Relation.
- **STEP-25:** rule 1.2's sound root becomes `Enemy[Sound]`; rule 5.1 gains `charlie.Knows[Sound].since = 2011`; open question 4 closes.
