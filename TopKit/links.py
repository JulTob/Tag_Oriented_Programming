"""Links: a Tag of one's own (STEP-SPEC-22).

A two-place statement, *Charlie knows Ruth*, is a family of one-place
statements, one for each Agent in the first place. So a Tag may grant
each of its Agents a Tag of its own, a **Link**::

    class Social(Tag):

        @Link
        class Knows(Tag):                         # the Relation: a template

            @Record
            def since(agent, contact, *, since=None):
                return since


    Social(charlie)
    charlie.Knows(ruth, since=2010)               # Ruth is Charlie's Contact
    ruth in charlie.Knows                         # True; ruth in bob.Knows is not
    charlie.Knows[ruth].since                     # 2010: the Pair's Record

How the kit builds it, from parts it already has:

- **The Link** is a real Tag, built for one Agent at the Parts of the
  declaring Tag. Its Field holds the Contacts, so membership, history,
  the algebra and Rip are the kit's own. It holds only the Relation's
  Tag-scope members (Reports and Operations) and the lines the Relation
  publishes onto Contacts (``@Public``).
- **The Pair** is a hidden Agent. It is tagged with the Relation's *Pair
  Tag*: the Relation's Actions, Records, conditions, Imprints and
  teardowns, each adapted to the two seats ``(agent, contact)``. So the
  Pair's gate, Parts, Write, Quality, Underlays, secrets and contract
  truth are the kit's own too.
- **Nothing lands on the Contact** but membership and what the Relation
  publishes. Her own Tags, Outline and contract never name a Link.
"""

from __future__ import annotations

from functools import partial
from inspect import signature
from typing import Any
from typing import Callable
from weakref import WeakKeyDictionary
import weakref

from . import tags as tags_module
from .declarations import STATE
from .declarations import Report
from .declarations import _FLAG
from .declarations import _LINK
from .declarations import _MISSING
from .declarations import _PUBLIC
from .declarations import _RELATION
from .declarations import _UNDERLAY
from .declarations import _has_flag
from .declarations import _is_dunder
from .declarations import _is_pin
from .declarations import _is_private
from .declarations import _is_relation
from .declarations import _kind_of
from .declarations import _mark_flag
from .declarations import _parameters_of
from .declarations import _scan_cache
from .errors import TagCompositionError
from .errors import TagDeclarationError
from .errors import TagResolutionError
from .errors import TagRogueAccessError
from .geometry import _form_of
from .geometry import _is_tag
from .geometry import _requiring_shapes
from .lifecycle import _rip
from .overlay import _require_membership
from .state import _Line
from .state import _State
from .state import _namespace_of
from .state import _state_of
from .tags import MetaTag
from .tags import Tag
from .transactions import _Call_Boundary
from .transactions import _apply_form
from .transactions import _capture
from .transactions import _current_boundary
from .transactions import _gate_form
from .transactions import _hand_over
from .transactions import _imprint
from .transactions import _inspect
from .transactions import _rollback_to
from .transactions import _undo


Function = Callable[..., Any]

_PAIR_ENDS = "_TOPKIT_PAIR"   # in a Pair's dictionary: who it joins, out of public reach

_CLASS_MACHINERY = frozenset((
        "__module__",
        "__qualname__",
        "__doc__",
        "__dict__",
        "__weakref__",
        "__firstlineno__",
        "__static_attributes__",
        "__classcell__",
        "__annotations__",
        "__annotate__",
        "__orig_bases__",
        "__type_params__",
        ))

_TAKES_INPUTS = frozenset((
        "record",
        "precondition",
        "postcondition",
        "condition",
        "imprint",
        ))


# ------------------------------------------------------------------
# Declaring a Relation
# ------------------------------------------------------------------


def Link(
        relation: type,
        ) -> type:
    """Mark a Tag declared in another Tag's body as a **Relation**: every
    Agent of the declaring Tag receives a Link of its own, a Tag held
    under the declaration's name. Its functions take the Link's Agent and
    the Contact, in that order::

        class Social(Tag):

            @Link
            class Knows(Tag):

                @Pre
                def Not_Oneself(agent, contact):
                    return contact is not agent
    """

    _check_relation(relation)

    for name, member in relation.__dict__.items():
        _check_seats(
                relation,
                name,
                member,
                )

    type.__setattr__(
            relation,
            _RELATION,
            True,
            )

    return relation


def _check_relation(
        relation: Any,
        ) -> None:
    """A Relation is a Tag whose Bases are Relations, and never a Pin
    (STEP-SPEC-22 rules 2.5 and 2.8)."""

    if not _is_tag(relation):
        raise TagDeclarationError(
                "@Link marks a Tag class declared in another Tag's body:"
                " @Link class Knows(Tag)"
                )

    if _is_pin(relation):
        raise TagDeclarationError(
                f"{relation.__name__} is a Pin; a Relation never is: Links"
                " between Tags need their own receiver rule (§1.9)"
                )

    for base in relation.__bases__:
        if _is_tag(base) and not _is_relation(base):
            raise TagDeclarationError(
                    f"{relation.__name__}: its Base {base.__name__} is an"
                    " ordinary Tag, which would be written on every Contact"
                    " without a word; a Relation's Bases are Relations, and a"
                    f" Link that Tags its Contact says so in an Imprint,"
                    f" {base.__name__}(contact)"
                    )


def _is_pair_member(
        name: str,
        member: Any,
        ) -> bool:
    """What a Relation declares for the Pair: everything callable that is
    not Tag scope (Reports, Operations) and not class machinery."""

    if _is_private(name) or name in _CLASS_MACHINERY:
        return False

    if isinstance(member, (Report, classmethod, staticmethod, type)):
        return False

    return callable(member)


def _check_seats(
        relation: type,
        name: str,
        member: Any,
        ) -> None:
    """Both seats, always (STEP-SPEC-22 rule 3.3): the Agent and the
    Contact, by position, the Contact without a default."""

    if isinstance(member, type) and not _is_private(name) and name not in _CLASS_MACHINERY:
        raise TagDeclarationError(
                f"{relation.__name__}.{name}: a class in a Relation's body has"
                " no seat; declare Relations in the declaring Tag's body"
                )

    if not _is_pair_member(name, member) or _kind_of(member) == "delete":
        return

    function = getattr(
            member,
            "__func__",
            member,
            )
    spec = _parameters_of(function)
    underlay = _has_flag(function, _UNDERLAY)
    needed = 3 if underlay else 2
    contact_has_default = len(spec.named) >= 2 and spec.named[1][1]

    if spec.positional < needed or contact_has_default:
        seats = "agent, contact, underlay" if underlay else "agent, contact"

        raise TagDeclarationError(
                f"{relation.__name__}.{name}: a Link's function for the Pair"
                " takes the Agent and the Contact, in that order, the Contact"
                f" without a default: def {name}({seats})"
                )


# ------------------------------------------------------------------
# The Pair Tag of a Relation
# ------------------------------------------------------------------


_pair_tags: "WeakKeyDictionary[type, type]" = WeakKeyDictionary()


def _pair_tag(
        relation: type,
        ) -> type:
    """The Tag a Pair receives from ``relation``: the Relation's Pair-scope
    declarations, each adapted to the two seats, with the Pair Tags of
    the Relation's own Bases as its Bases. One per Relation, shared by
    every Agent's Link: the Pair carries who it joins."""

    cached = _pair_tags.get(relation)

    if cached is not None:
        return cached

    bases = tuple(
            _pair_tag(base)
            for base in relation.__bases__
            if _is_relation(base)
            ) or (Tag,)
    namespace: dict[str, Any] = {
            "__module__": relation.__module__,
            "__qualname__": relation.__qualname__,
            "__doc__": relation.__doc__,
            }

    for name, member in relation.__dict__.items():
        if not _is_pair_member(name, member):
            continue

        if _kind_of(member) == "delete":
            namespace[name] = member
        else:
            namespace[name] = _two_seats(member)

    pair_tag = MetaTag(
            relation.__name__,
            bases,
            namespace,
            )
    words = relation.__dict__.get(_FLAG)

    if words is not None:
        _mark_flag(
                pair_tag,
                words,
                )   # a Flag Link answers its words on the Pair, never on the Contact

    _pair_tags[relation] = pair_tag

    return pair_tag


def _two_seats(
        member: Any,
) -> Function:
    """Adapt ``def f(agent, contact, ...)`` to the kit's one receiver, the
    Pair. The adapted function shows the kit the seats after the Contact
    (a stored value or an Underlay, then inputs by name), and calls ``f``
    with the Link's Agent and the Contact. It runs inside the Agent's
    composition door (rule 3.6); the Pair's door is the kit's."""

    function = getattr(
            member,
            "__func__",
            member,
            )
    parameters = list(signature(function).parameters.values())
    seats = {
            parameters[0].name,
            parameters[1].name,
            }
    kind = _kind_of(function)
    spec = _parameters_of(function)

    if spec.positional >= 3 and (kind == "record" or _has_flag(function, _UNDERLAY)):
        seats.add(parameters[2].name)   # the stored value, or the Underlay

    def Two_Seats(
            pair: object,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        agent, contact = _ends_of(pair)
        state = _state_of(agent)

        if state is None:
            return function(
                    agent,
                    contact,
                    *args,
                    **kwargs,
                    )

        state.composing += 1   # the Link is the Agent's code about a Pair

        try:
            return function(
                    agent,
                    contact,
                    *args,
                    **kwargs,
                    )
        finally:
            state.composing -= 1

    Two_Seats.__signature__ = signature(function).replace(
            parameters=[parameters[0], *parameters[2:]],
            )
    Two_Seats.__name__ = function.__name__
    Two_Seats.__qualname__ = function.__qualname__
    Two_Seats.__doc__ = function.__doc__
    Two_Seats.__module__ = function.__module__

    for key, value in vars(function).items():
        if key.startswith("__topkit_"):
            setattr(
                    Two_Seats,
                    key,
                    value,
                    )   # the declaration's marks: kind, Underlay, Secret, Constant, Tool

    Two_Seats._topkit_seats = frozenset(seats)

    return Two_Seats


# ------------------------------------------------------------------
# The Pair
# ------------------------------------------------------------------


class Pair:
    """One Agent and one Contact, linked: what a Link gives, held for the
    Link's Agent and read through the Link, ``charlie.Knows[ruth]``.

    Nothing public on a Pair names the Agent: its functions receive the
    Agent in their first seat, and that is the Link's own code."""

    def __repr__(
            pair,
            ) -> str:
        ends = object.__getattribute__(pair, "__dict__").get(_PAIR_ENDS)
        name = ends.name if ends is not None else "Link"

        return f"<{name} Pair>"


class _Ends:
    """Who a Pair joins, held weakly: a Link never keeps its Agent alive,
    and a Field never keeps a Contact alive."""

    __slots__ = (
            "agent",
            "contact",
            "family",
            "name",
            "held",
            )

    def __init__(
            ends,
            agent: object,
            contact: object,
            family: "_Family",
            name: str,
            forget: Callable[..., None],
            ) -> None:
        ends.agent = weakref.ref(agent)
        ends.contact = weakref.ref(contact, forget)
        ends.family = family
        ends.name = name
        ends.held = None   # both ends, held strongly only while teardowns run


def _ends_of(
        pair: object,
        ) -> tuple[object, object]:
    ends: _Ends = object.__getattribute__(pair, "__dict__")[_PAIR_ENDS]

    if ends.held is not None:
        return ends.held

    agent = ends.agent()
    contact = ends.contact()

    if agent is None:
        agent = ends.family.dying   # the finalizer of the Link's Agent fills the first seat

    if agent is None or contact is None:
        raise ReferenceError(
                f"this {ends.name} Pair's Agent or Contact no longer exists"
                )

    return agent, contact


class _Family:
    """The Links of one Agent that share Pairs: a Link and its Base Links
    hold one Pair for each Contact (rule 5.3). Independent Links of one
    Agent are separate families."""

    __slots__ = (
            "pairs",
            "links",
            "dying",
            "__weakref__",
            )

    def __init__(
            family,
            ) -> None:
        family.pairs: dict[int, Pair] = {}
        family.links: list[weakref.ref] = []
        family.dying: object | None = None

    def Pair_Of(
            family,
            contact: object,
            leaving: bool = False,
            ) -> Pair | None:
        """The Pair of a live Contact. ``leaving`` is her own teardown,
        inside her finalizer: in a reference cycle the language has
        already cleared her weak references, but she is still in hand and
        her identity is still hers, so her Pair is still found (rule 7.4)."""

        pair = family.pairs.get(id(contact))

        if pair is None:
            return None

        ends = object.__getattribute__(pair, "__dict__")[_PAIR_ENDS]
        live = ends.contact()

        if live is contact:
            return pair

        if ends.held is not None and ends.held[1] is contact:
            return pair

        if leaving and live is None:
            return pair

        return None

    def New_Pair(
            family,
            agent: object,
            contact: object,
            name: str,
            ) -> Pair:
        pair = Pair()
        key = id(contact)
        forget = partial(
                _forget_pair,
                weakref.ref(family),
                key,
                )
        object.__getattribute__(pair, "__dict__")[_PAIR_ENDS] = _Ends(
                agent,
                contact,
                family,
                name,
                forget,
                )
        family.pairs[key] = pair

        return pair

    def End(
            family,
            contact: object,
            ) -> None:
        pair = family.Pair_Of(
                contact,
                leaving=True,
                )

        if pair is None:
            return

        del family.pairs[id(contact)]
        state = _state_of(pair)

        if state is not None:
            state.rips.clear()   # its teardowns ran, or end silently; never again at collection (rule 8.5)

    def Links(
            family,
            ) -> list[type]:
        return [
                link
                for reference in family.links
                if (link := reference()) is not None
                ]


def _forget_pair(
        family_reference: weakref.ref,
        key: int,
        expired: weakref.ref,
        ) -> None:
    """A Contact's weak reference is cleared. Her Pair stays until her
    finalizer's teardown ends it, even in a reference cycle, where the
    language clears weak references before any finalizer runs (rule
    7.4). Her identity cannot be reused before that teardown: an object
    is freed only after its finalizer. At interpreter exit no finalizer
    runs, and nothing reads the Pair again."""

    return None


# ------------------------------------------------------------------
# One Agent's Link
# ------------------------------------------------------------------


class _Link_Record:
    """What the kit keeps about one Agent's Link, out of public reach."""

    __slots__ = (
            "name",
            "agent",
            "layers",
            "family",
            "hook",
            "ending",
            "ended",
            "pair_form",
            )

    def __init__(
            record,
            name: str,
            agent: object,
            layers: list[type],
            family: _Family,
            ) -> None:
        record.name = name
        record.agent = weakref.ref(agent)
        record.layers = layers
        record.family = family
        record.hook = None
        record.ending = False
        record.ended = False
        record.pair_form = None   # the Pair Tags a linking gives, once computed


_RECORD = "_topkit_link_record"   # on the Link class itself: read on every Pair lookup


def _record_of(
        link: type,
        ) -> _Link_Record:
    return link.__dict__[_RECORD]


def _grant(
        agent: object,
        state: _State,
        declarations: Any,
        ) -> None:
    """At the Parts of a declaring Tag (rule 4.1): build each Link the
    Agent does not hold yet, or extend a held one with a new Layer (rule
    4.6). The Link is stored under the Relation's name, read-only."""

    namespace = _namespace_of(agent)

    for name, _relation in declarations.links:
        link, layers = state.links[name]

        if link is None:
            link = _new_link(
                    agent,
                    state,
                    name,
                    layers,
                    )
            state.links[name] = (
                    link,
                    layers,
                    )
        else:
            record = _record_of(link)
            added = [
                    relation
                    for relation in layers
                    if relation not in record.layers
                    ]

            if added:
                _extend(
                        link,
                        record,
                        added,
                        )

        namespace[name] = link


def _new_link(
        agent: object,
        state: _State,
        name: str,
        layers: tuple[type, ...],
        ) -> type:
    """A distinct Tag for this Agent (rule 4.2), with this Agent's own
    Links as its Bases (rule 2.4)."""

    bases = _base_links(
            state,
            layers,
            )
    namespace: dict[str, Any] = {
            "__module__": layers[0].__module__,
            "__qualname__": layers[0].__qualname__,
            "__doc__": layers[0].__doc__,
            _LINK: True,
            }

    for relation in layers:
        namespace.update(_tag_scope_of(relation))

    tags_module._making_link += 1

    try:
        link = MetaTag(
                name,
                tuple(bases) or (Tag,),
                namespace,
                )
    finally:
        tags_module._making_link -= 1

    family = _family_for(bases)
    record = _Link_Record(
            name,
            agent,
            list(layers),
            family,
            )
    type.__setattr__(
            link,
            _RECORD,
            record,
            )   # the record holds its Agent weakly, so the Link never keeps it alive
    family.links.append(weakref.ref(link))

    for relation in layers:
        _publish_lines(
                link,
                relation,
                )

    return link


def _base_links(
        state: _State,
        layers: tuple[type, ...],
        ) -> list[type]:
    """The Agent's own Links for the Relations its Relations extend under
    other names: Charlie's Trusts is a Shape of Charlie's Knows."""

    bases: list[type] = []

    for relation in layers:
        for base in relation.__bases__:
            if not _is_relation(base) or base in layers:
                continue

            held = _link_holding(
                    state,
                    base,
                    )

            if held is None:
                raise TagCompositionError(
                        f"{relation.__name__} extends {base.__name__}, a Link"
                        " this Agent does not hold"
                        )

            if held not in bases:
                bases.append(held)

    return [
            base
            for base in bases
            if not any(
                    other is not base and issubclass(other, base)
                    for other in bases
                    )
            ]   # only the leaves: a consistent order for the language


def _link_holding(
        state: _State,
        relation: type,
        ) -> type | None:
    for link, layers in state.links.values():
        if link is not None and relation in layers:
            return link

    return None


def _family_for(
        bases: list[type],
        ) -> _Family:
    """A Link joins the family of its Base Links; a Link with none starts
    its own. Base Links from separate families are joined into one, after
    checking that no Contact holds a Pair in two of them. The join is
    undone with the call if it rolls back (§0.6)."""

    families: list[_Family] = []

    for base in bases:
        for member in _form_of(base):
            family = _record_of(member).family

            if family not in families:
                families.append(family)

    if not families:
        return _Family()

    _refuse_shared_contacts(families)
    kept = families[0]
    joins = [
            _join(
                    kept,
                    other,
                    )
            for other in families[1:]
            ]
    boundary = _current_boundary.get()

    if joins and boundary is not None:
        boundary.undo.append(partial(
                _split,
                kept,
                joins,
                ))

    return kept


def _refuse_shared_contacts(
        families: list[_Family],
        ) -> None:
    """Two families joined would give one Contact two Pairs: refused,
    before anything is joined."""

    seen: set[int] = set()

    for family in families:
        if seen & family.pairs.keys():
            raise TagCompositionError(
                    "this Link would join Links that hold separate Pairs for"
                    " one Contact; unlink her from one of them first"
                    )

        seen.update(family.pairs)


def _join(
        kept: _Family,
        other: _Family,
        ) -> tuple[_Family, dict[int, Pair], list[type], int]:
    """Move ``other``'s Pairs and Links into ``kept``. Returns what
    ``_split`` needs to move them back."""

    moved_pairs = dict(other.pairs)
    moved_links = other.Links()
    links_before = len(kept.links)

    for pair in moved_pairs.values():
        object.__getattribute__(pair, "__dict__")[_PAIR_ENDS].family = kept

    kept.pairs.update(moved_pairs)
    other.pairs.clear()

    for link in moved_links:
        _record_of(link).family = kept
        kept.links.append(weakref.ref(link))

    return (
            other,
            moved_pairs,
            moved_links,
            links_before,
            )


def _split(
        kept: _Family,
        joins: list[tuple[_Family, dict[int, Pair], list[type], int]],
        ) -> None:
    """Undo ``_join``, latest first: each family gets back its own Pairs
    and Links."""

    for other, moved_pairs, moved_links, links_before in reversed(joins):
        for key, pair in moved_pairs.items():
            if kept.pairs.get(key) is pair:
                del kept.pairs[key]
                other.pairs[key] = pair
                object.__getattribute__(pair, "__dict__")[_PAIR_ENDS].family = other

        for link in moved_links:
            _record_of(link).family = other
            _record_of(link).pair_form = None

        del kept.links[links_before:]

    _forget_pair_forms(kept)


def _tag_scope_of(
        relation: type,
        ) -> dict[str, Any]:
    """The Relation's Reports and Operations: they belong to the Link
    itself, one Link per Agent (rule 2.3), ``def capacity(link)``."""

    members: dict[str, Any] = {}

    for name, member in relation.__dict__.items():
        if _is_private(name) or name in _CLASS_MACHINERY:
            continue

        if isinstance(member, Report):
            copy = Report(member.builder)   # one Report per Link: each builds for its own Link
            copy.public = member.public
            members[name] = copy
        elif isinstance(member, classmethod) and _kind_of(member) == "operation":
            members[name] = member

    return members


def _publish_lines(
        link: type,
        relation: type,
        ) -> None:
    """``@Public`` Pair members are seen by the Contact (rule 2.7): each
    becomes a line on the Link, which the Contact receives at linking.
    ``ruth.Greet()`` runs the Pair's ``Greet(charlie, ruth)``."""

    for name, member in relation.__dict__.items():
        if not _is_pair_member(name, member) or not _has_flag(member, _PUBLIC):
            continue

        if _kind_of(member) == "record":
            line: Any = _Pair_Record_Line(
                    link,
                    name,
                    )
            type.__setattr__(link, name, line)
            line.__set_name__(link, name)
        else:
            type.__setattr__(
                    link,
                    name,
                    _line_action(
                            link,
                            name,
                            ),
                    )

    _scan_cache.pop(link, None)


def _line_action(
        link: type,
        name: str,
        ) -> Function:
    link_reference = weakref.ref(link)

    def Line(
            contact: object,
            *args: Any,
            **kwargs: Any,
            ) -> Any:
        pair = _line_pair(
                link_reference,
                contact,
                name,
                "Pair Action",
                )
        state = _state_of(contact)
        opened = state.composing
        state.composing = 0   # the Contact's door stays shut on every path (rule 3.6)

        try:
            return getattr(pair, name)(
                    *args,
                    **kwargs,
                    )
        finally:
            state.composing = opened

    Line.__name__ = name
    Line.__qualname__ = f"{link.__qualname__}.{name}"
    Line.__doc__ = f"A line from a {link.__name__} Pair: its {name}."

    return Line


def _line_pair(
        link_reference: weakref.ref,
        contact: object,
        name: str,
        kind: str,
        ) -> Pair:
    """The Pair a line reaches. A published member answers members only
    (§1.5): once unlinked, the line raises a Rogue Access Failure."""

    link = link_reference()

    if link is None:
        raise TagRogueAccessError(
                f"{name!r} was published by a Link that no longer exists"
                )

    _require_membership(
            contact,
            link,
            name,
            kind,
            )
    pair = _record_of(link).family.Pair_Of(contact)

    if pair is None:
        raise TagRogueAccessError(
                f"{name!r} is a published {kind} of {link.__name__}; this"
                " Contact holds no Pair of it"
                )

    return pair


def _no_builder(
        link: type,
        ) -> None:
    return None


class _Pair_Record_Line(Report, _Line):
    """A ``@Public`` Pair Record, read on the Contact: read-only there,
    and read live from her Pair."""

    def __init__(
            line,
            link: type,
            name: str,
            ) -> None:
        Report.__init__(
                line,
                _no_builder,
                )
        line.public = True
        line.__name__ = name
        line._link = weakref.ref(link)
        line._member = name

    def __get__(
            line,
            instance: object,
            owner: type | None = None,
            ) -> Any:
        return line   # on the Link itself it is a line, not a value

    def Read(
            line,
            contact: object,
            ) -> Any:
        pair = _line_pair(
                line._link,
                contact,
                line._member,
                "Pair Record",
                )

        return getattr(
                pair,
                line._member,
                )

    def __repr__(
            line,
            ) -> str:
        return (
                f"<Pair Record {line._member}: read it on a Pair,"
                f" agent.Link[contact].{line._member}>"
                )


# ------------------------------------------------------------------
# Extending a held Link (rule 4.6)
# ------------------------------------------------------------------


def _extend(
        link: type,
        record: _Link_Record,
        added: list[type],
        ) -> None:
    """A Shape of the declaring Tag extends a held Link with new Layers.

    Inside the Agent's call, as a tagging of every Pair the Link holds:
    every Pair's gate and Parts now (one refusal refuses the whole call,
    nothing changed); their Imprints and promises after the Agent's
    Commit. Linkings made after that get every Layer."""

    boundary = _current_boundary.get()
    field = link.__dict__["_topkit_field"]
    pairs = [
            pair
            for contact in field
            if (pair := record.family.Pair_Of(contact)) is not None
            ]
    form = _pair_tags_of(added)
    entries = [
            (
                pair,
                _capture(pair),
                )
            for pair in pairs
            ]
    previous_layers = list(record.layers)
    previous_members = {
            name: link.__dict__.get(name, _MISSING)
            for relation in added
            for name in (*_tag_scope_of(relation), *_published_names(relation))
            }
    written: list[tuple[Pair, list[Any]]] = []

    def Undo() -> None:
        for pair, entry in reversed(entries):
            _rollback_to(
                    pair,
                    entry,
                    )

        record.layers[:] = previous_layers
        _forget_pair_forms(record.family)

        for name, value in previous_members.items():
            if value is _MISSING:
                if name in link.__dict__:
                    type.__delattr__(link, name)
            else:
                type.__setattr__(link, name, value)

        _scan_cache.pop(link, None)

    try:
        record.layers.extend(added)
        _forget_pair_forms(record.family)

        for relation in added:
            for name, member in _tag_scope_of(relation).items():
                type.__setattr__(link, name, member)

                if isinstance(member, Report):
                    member.__set_name__(link, name)

            _publish_lines(
                    link,
                    relation,
                    )

        for pair in pairs:
            _gate_form(
                    pair,
                    form,
                    {},
                    )   # every Pair's gate first: one refusal refuses the whole call

        for pair in pairs:
            deferred: list[Any] = []
            _apply_form(
                    pair,
                    form,
                    {},
                    deferred,
                    gated=True,
                    )
            written.append(
                    (
                        pair,
                        deferred,
                        )
                    )
    except BaseException:
        Undo()
        raise

    def Write() -> None:
        _write_all(
                written,
                {},
                )

    if boundary is None:
        Write()
        return

    boundary.undo.append(Undo)
    boundary.writes.append(Write)


def _published_names(
        relation: type,
        ) -> list[str]:
    return [
            name
            for name, member in relation.__dict__.items()
            if _is_pair_member(name, member) and _has_flag(member, _PUBLIC)
            ]


def _pair_tags_of(
        relations: list[type],
        ) -> list[type]:
    """The Pair Tags for ``relations``, Bases first, each once."""

    form: list[type] = []

    for relation in relations:
        for pair_tag in _form_of(_pair_tag(relation)):
            if pair_tag not in form:
                form.append(pair_tag)

    return form


def _pair_form(
        link: type,
) -> list[type]:
    """Every Pair Tag a linking through ``link`` gives: the Layers of each
    Link in its Form, Bases first (rules 5.2 and 5.3). Kept on the record
    until a Layer is added to any Link of the family."""

    record = _record_of(link)

    if record.pair_form is not None:
        return record.pair_form

    relations: list[type] = []

    for member in _form_of(link):
        for relation in _record_of(member).layers:
            if relation not in relations:
                relations.append(relation)

    record.pair_form = _pair_tags_of(relations)

    return record.pair_form


def _forget_pair_forms(
        family: "_Family",
        ) -> None:
    for link in family.Links():
        _record_of(link).pair_form = None


def _write_all(
        written: list[tuple[Pair, list[Any]]],
        inputs: dict[str, Any],
        ) -> None:
    """Every Pair's Imprints, then every Pair's promises; the first
    failure is raised, and the Layers stay."""

    first: BaseException | None = None

    for pair, deferred in written:
        try:
            _write(
                    pair,
                    deferred,
                    inputs,
                    )
        except Exception as error:
            first = first or error

    for pair, _deferred in written:
        try:
            _inspect(pair)
        except Exception as error:
            first = first or error

    try:
        if first is not None:
            raise first
    finally:
        first = None   # never keep Agents alive through a traceback that holds this frame


def _write(
        pair: Pair,
        deferred: list[Any],
        inputs: dict[str, Any],
        ) -> None:
    state = _state_of(pair)
    state.composing += 1

    try:
        for declarations in deferred:
            _imprint(
                    pair,
                    declarations,
                    inputs,
                    )
    finally:
        state.composing -= 1


# ------------------------------------------------------------------
# Linking (rule 5.1)
# ------------------------------------------------------------------


def _link(
        link: type,
        contact: object,
        inputs: dict[str, Any],
        ) -> object:
    """``charlie.Knows(ruth, **inputs)``: a tagging of the Contact, with
    the Pair as receiver. The Pair's gate; the Pair's Records; the Contact
    enters the Link's Field; the Pair's Imprints; the Pair's promises and
    the Contact's own. A failure up to her entry changes nothing; after
    it, the failure raises and the linking stays."""

    record = _record_of(link)
    agent = _agent_of(
            link,
            record,
            )
    _refuse_contact(
            link,
            contact,
            )
    contact_state = _state_of(contact)
    pending = [
            member
            for member in _form_of(link)
            if contact_state is None or member not in contact_state.active
            ]

    if not pending:
        return contact   # reapplying is a no-op (rule 5.4)

    form = _pair_form(link)
    _refuse_inputs_in_seats(
            form,
            inputs,
            )
    family = record.family
    pair = family.Pair_Of(contact)
    created = pair is None

    if created:
        pair = family.New_Pair(
                agent,
                contact,
                record.name,
                )

    outer = _current_boundary.get()   # a call this linking is part of (rule 5.6)
    local = _Call_Boundary()   # nested linkings made at the Pair's Parts report here
    pair_entry = _capture(pair)
    contact_entry = _capture(contact) if outer is not None else None
    deferred: list[Any] = []

    def Drop_Pair() -> None:
        _rollback_to(
                pair,
                pair_entry,
                )   # a new Pair loses its state, so its teardowns never run (rule 8.5)

        if created and family.pairs.get(id(contact)) is pair:
            del family.pairs[id(contact)]

    token = _current_boundary.set(local)

    try:
        try:
            _apply_form(
                    pair,
                    form,
                    inputs,
                    deferred,
                    )
            _apply_form(
                    contact,
                    pending,
                    {},
                    [],
                    )   # a refusal rolls the Contact back by itself
        except BaseException:
            try:
                _undo(local)   # what the Pair's Parts linked, latest first
            finally:
                Drop_Pair()

            raise
    finally:
        _current_boundary.reset(token)

    _hook(
            contact,
            pending,
            )

    if outer is not None:
        def Undo() -> None:
            _rollback_to(
                    contact,
                    contact_entry,
                    )
            Drop_Pair()

        _hand_over(
                local,
                outer,
                )
        outer.undo.append(Undo)

    _write(
            pair,
            deferred,
            inputs,
            )
    _inspect(pair)
    _inspect(contact)

    return contact


def _agent_of(
        link: type,
        record: _Link_Record,
        ) -> object:
    if record.ending:
        raise TagCompositionError(
                f"this {link.__name__} is ending with its Agent; nothing is"
                " linked through it now"
                )

    agent = record.agent()

    if agent is None or record.ended:
        raise TagCompositionError(
                f"this {link.__name__}'s Agent no longer exists; nothing is"
                " linked through it"
                )

    return agent


def _refuse_contact(
        link: type,
        contact: object,
        ) -> None:
    if contact is None:
        raise TagCompositionError(
                f"{link.__name__} links a Contact: an object, never None"
                )

    if isinstance(contact, type):
        raise TagCompositionError(
                f"{link.__name__} links objects, not classes; Links between"
                " Tags need their own receiver rule"
                )

    if _namespace_of(contact) is None:
        raise TagCompositionError(
                f"{type(contact).__name__} cannot carry TOP state (no instance"
                f" dictionary), so it cannot be a Contact of {link.__name__}"
                )

    try:
        weakref.ref(contact)
    except TypeError as error:
        raise TagCompositionError(
                "Contacts must support weak references: a Link's Field never"
                " keeps its Contacts alive"
                ) from error


def _refuse_inputs_in_seats(
        form: list[type],
        inputs: dict[str, Any],
        ) -> None:
    """An input never fills a seat (rule 3.4)."""

    if not inputs:
        return

    for pair_tag in form:
        for name, seats in _seats_of(pair_tag):
            taken = sorted(seats & inputs.keys())

            if taken:
                raise TagDeclarationError(
                        f"{pair_tag.__qualname__}.{name}: the input"
                        f" {taken[0]!r} is named like one of its seats; take"
                        " inputs by name after `*`:"
                        f" def {name}(agent, contact, *, {taken[0]})"
                        )


_seats: "WeakKeyDictionary[type, tuple[tuple[str, frozenset[str]], ...]]" = WeakKeyDictionary()


def _seats_of(
        pair_tag: type,
        ) -> tuple[tuple[str, frozenset[str]], ...]:
    """The seats of each Pair function that takes inputs, by name."""

    cached = _seats.get(pair_tag)

    if cached is None:
        cached = tuple(
                (
                    name,
                    member._topkit_seats,
                    )
                for name, member in pair_tag.__dict__.items()
                if _kind_of(member) in _TAKES_INPUTS
                and hasattr(member, "_topkit_seats")
                )
        _seats[pair_tag] = cached

    return cached


def _hook(
        contact: object,
        links: list[type],
) -> None:
    """Each Link the Contact entered gets its teardown on her: leaving it,
    by Rip or by her deletion, runs the Pair's teardowns (rules 8.1, 8.4).
    It is a teardown and not an Action: nothing callable lands on her."""

    state = _state_of(contact)

    for link in links:
        record = _record_of(link)

        if record.hook is None:
            record.hook = _leaving(link)

        state.rips[link] = (record.hook,)


def _leaving(
        link: type,
        ) -> Function:
    """The Contact's teardown for one Link. It holds the Link strongly:
    in a reference cycle the language clears weak references before any
    finalizer runs, and the Link already keys this teardown on her."""

    def Unlink(
            contact: object,
            ) -> None:
        _leave(
                link,
                contact,
                )

    Unlink.__name__ = "Unlink"

    return Unlink


# ------------------------------------------------------------------
# The Pair, read through the Link (rule 7.1)
# ------------------------------------------------------------------


def _pair_of(
        link: type,
        contact: object,
        ) -> Pair:
    """``charlie.Knows[ruth]``: the Pair, live. It needs a linking, not
    active membership: it lives until the Link's teardowns have run."""

    record = link.__dict__.get(_RECORD)
    pair = None if record is None else record.family.Pair_Of(contact)

    if pair is None:
        raise TagResolutionError(
                f"{type(contact).__name__} is not a Contact of this"
                f" {link.__name__}; it holds no Pair of hers"
                )

    return pair


def _contact_holds(
        link: type,
        ) -> Callable[[object], bool]:
    """The sound Contacts: those whose own contract holds and whose Pair
    holds (rule 7.3). A broken Pair never makes her defective elsewhere."""

    from .contracts import _holds

    record = _record_of(link)

    def Holds(
            contact: object,
            ) -> bool:
        if not _holds(contact):
            return False

        pair = record.family.Pair_Of(contact)

        return pair is None or _holds(pair)

    return Holds


# ------------------------------------------------------------------
# Ending (section 8)
# ------------------------------------------------------------------


def _leave(
        link: type,
        contact: object,
        ) -> None:
    """One Contact leaves one Link: the Pair's teardowns of that Link's
    Layers run with ``(agent, contact)``. Then the Pair ends, unless
    another Link of the same family still holds her (rule 8.1): what the
    Ripped Link gave the Pair stays on it, sticky. When the Link's Agent
    cannot be reached, the Pair ends silently (rule 8.4)."""

    record = _record_of(link)
    family = record.family
    pair = family.Pair_Of(
            contact,
            leaving=True,
            )

    if pair is None:
        return

    state = _state_of(contact)
    agent = record.agent()

    if agent is None:
        agent = family.dying

    if agent is None:
        family.End(contact)
        return

    ends: _Ends = object.__getattribute__(pair, "__dict__")[_PAIR_ENDS]
    pair_state = _state_of(pair)
    first: BaseException | None = None
    ends.held = (
            agent,
            contact,
            )
    opened = state.composing
    state.composing = 0   # her door stays shut, even inside her own finalizer (rule 3.6)

    try:
        for relation in reversed(record.layers):
            pair_tag = _pair_tag(relation)

            if pair_state is None or pair_tag not in pair_state.active:
                continue

            try:
                _rip(
                        pair,
                        pair_tag,
                        )   # runs that Layer's teardowns, with the Pair
            except TagCompositionError as error:
                first = first or error
    finally:
        ends.held = None
        state.composing = opened

    if not _still_held(
            family,
            state,
            ):
        family.End(contact)   # asked after the teardowns: one may have linked her again (rule 5.7)

    try:
        if first is not None:
            raise first
    finally:
        first = None   # never keep Agents alive through a traceback that holds this frame


def _still_held(
        family: _Family,
        state: _State,
        ) -> bool:
    """A Link of the family still holds her: active, with its teardown
    still due on her."""

    return any(
            link in state.active
            and link in state.rips
            for link in family.Links()
            )


def _unlink_all(
        link: type,
        key: slice,
        ) -> None:
    """``del charlie.Knows[:]``: unlink every Contact (rule 8.2). Refused,
    nothing changed, while a Shape Link still holds any of them (§0.7);
    every teardown runs, and the first failure is raised after."""

    if key != slice(None):
        raise TypeError(
                "Link[:] is the whole Field; positional slices have no"
                " meaning for a population"
                )

    contacts = list(link.__dict__["_topkit_field"])
    held = [
            contact
            for contact in contacts
            if _requiring_shapes(link, _state_of(contact).active)
            ]

    if held:
        raise TagCompositionError(
                f"{link.__name__} is required by an active Shape Link for"
                f" {len(held)} of its Contacts; unlink them from the Shape"
                " first"
                )

    first: BaseException | None = None

    for contact in contacts:
        if link not in _state_of(contact).active:
            continue   # an earlier Contact's teardown already unlinked her

        try:
            _rip(
                    contact,
                    link,
                    )
        except TagCompositionError as error:
            first = first or error

    contacts = held = None   # the Contacts are not ours to keep

    try:
        if first is not None:
            raise first
    finally:
        first = None   # never keep Agents alive through a traceback that holds this frame


def _own_records(
        state: _State,
        ) -> list[_Link_Record]:
    """The records of the Agent's own Links, Shape Links first."""

    records = []

    for name in reversed(list(state.links)):
        link = state.links[name][0]

        if link is None:
            continue

        record = link.__dict__.get(_RECORD)

        if record is not None and not record.ended:
            records.append(record)

    return records


def _begin_ending(
        agent: object,
        state: _State,
        ) -> None:
    """The Agent's finalizer holds it: from now on it fills the first seat
    of its own Links, even when the language has already cleared every
    weak reference to it (a reference cycle, rule 8.3). Its own
    teardowns, its exits from Links that hold it included, run next."""

    for record in _own_records(state):
        record.family.dying = agent


def _end_links(
        agent: object,
        state: _State,
        ) -> None:
    """The Agent's deletion ends its Links (rule 8.3): after its own
    teardowns, each Link's Field is Ripped, Shape Links before their
    Bases, with the dying Agent in the first seat. Best effort, as every
    teardown at deletion is (§3.2). Linking through them is refused from
    then on."""

    records = _own_records(state)

    try:
        for record in records:
            record.family.dying = agent
            record.ending = True

        for name in reversed(list(state.links)):
            link = state.links[name][0]

            if link is None or link.__dict__.get(_RECORD) not in records:
                continue

            for contact in list(link.__dict__["_topkit_field"]):
                try:
                    _rip(
                            contact,
                            link,
                            )
                except Exception:
                    pass
    finally:
        for record in records:
            record.family.dying = None
            record.ending = False
            record.ended = True


__all__ = [
        "Link",
        ]
