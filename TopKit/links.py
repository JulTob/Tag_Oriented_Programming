"""Independent Links: one actual Tag per owner, one Pair per Contact.

Relation syntax and contextual seats live in ``link_forms``. This module
builds their ordinary TOP Tags; the existing transaction and lifecycle
machinery remains responsible for Gains, contracts and Rip.
"""

from __future__ import annotations

from asyncio import CancelledError
from collections.abc import Coroutine
from contextlib import contextmanager
from contextlib import ExitStack
from contextvars import ContextVar
from inspect import Parameter
from inspect import getattr_static
from typing import Any
from weakref import ref

from .arrest import _arrest_of
from .arrest import _hold_lazy_result
from .arrest import _require_available
from .arrest import _rip_door
from .access import _refuse_host_truth
from .contracts import _holds_for_population
from .declarations import Report
from .declarations import _ACTION_CHAIN
from .declarations import _CONSTANT
from .declarations import _KIND
from .declarations import _MISSING
from .declarations import _PUBLIC
from .declarations import _RIP
from .declarations import _SECRET
from .declarations import _TOOL
from .declarations import _UNDERLAY
from .declarations import _has_flag
from .declarations import _declarations_of
from .declarations import _invalidate_declarations
from .declarations import _is_private
from .declarations import _kind_of
from .declarations import _signature_of
from .errors import TagArrestedAccessError
from .errors import TagCompositionError
from .errors import TagDeclarationError
from .errors import TagResolutionError
from .errors import TagPostconditionError
from .errors import TagTargetError
from .errors import TaggingFailure
from .fields import FIELD_SEAT
from .fields import _Field
from .fields import _field_of
from .lazy_guard import _guard_lazy_result
from .lazy_guard import _lazy_kind_of
from .lazy_guard import _register_lazy_proxy_types
from .lifecycle import _rip
from .lifecycle import _rip_field
from .overlay import _remove_post_application
from .overlay import _require_membership
from .observations import _refuse_observed_act
from .post_queries import _post_evaluation
from .link_forms import _Captured_Header
from .link_forms import _Header_Meta
from .link_forms import _Link_Header
from .link_forms import agent as _agent_seat
from .link_forms import contact as _contact_seat
from .state import _Line
from .state import _host_bindings_of
from .state import _is_composing
from .state import _async_doors
from .state import _namespace_of
from .state import _restore_host_bindings
from .state import _runtime_type_for
from .state import _set_runtime_type
from .state import _state_for
from .state import _state_of
from .tags import MetaTag
from .tags import Tag
from .transactions import _apply
from .transactions import _actualize
from .transactions import _inspect
from .transactions import _require_sound_source


_RECORD = "_topkit_link_record"
_PAIR_ENDS = "_TOPKIT_PAIR_ENDS"
_MACHINERY = frozenset((
        "__module__", "__qualname__", "__doc__", "__dict__", "__weakref__",
        "__firstlineno__", "__static_attributes__", "__classcell__",
        "__annotations__", "__annotate__", "__orig_bases__", "__type_params__",
        ))
_MARKS = (_KIND, _UNDERLAY, _RIP, _SECRET, _PUBLIC, _CONSTANT, _TOOL,
          _ACTION_CHAIN)
_current_pairs: ContextVar[tuple[_Ends, ...]] = ContextVar(
        "topkit_current_link_pairs", default=(),
        )


def _seat_value(value: Any) -> Any:
    """A direct contextual seat result denotes its actual protocol object."""
    return value._current() if value is _agent_seat or value is _contact_seat else value


class _Link_Coordinate:
    """A concrete Link selection, without owning its Agent or declaring Tag."""

    __slots__ = ("owner", "tag", "name")

    def __init__(coordinate, owner: object, tag: type, name: str) -> None:
        coordinate.owner = ref(owner)
        coordinate.tag = ref(tag)
        coordinate.name = str.__str__(name)

    def Resolve(coordinate) -> type:
        owner, tag = coordinate.owner(), coordinate.tag()
        state = None if owner is None else _state_of(owner)
        held = None if state is None or tag is None else state.owned_links.get(
                (id(tag), coordinate.name),
                )
        if held is None or held[0] is not tag:
            raise TagResolutionError(
                    f"the Agent no longer holds this {coordinate.name} Link"
                    )
        return held[1]


class _Pair:
    """The private Agent on which a Link's relationship Gains are composed."""

    def __repr__(pair) -> str:
        ends = object.__getattribute__(pair, "__dict__").get(_PAIR_ENDS)
        return f"<{ends.data.name if ends is not None else 'Link'} Pair>"


class _Ends:
    __slots__ = ("owner", "contact", "data", "held", "ended", "pair", "admitted",
                 "dying_contact")

    def __init__(ends, owner: object, contact: object, data: _Link_Data) -> None:
        ends.owner = ref(owner)
        ends.contact = ref(contact)
        ends.data = data
        ends.held: tuple[object, object] | None = None
        ends.ended = False
        ends.pair: Any = None
        ends.admitted = False
        ends.dying_contact: object | None = None

    def Resolve(ends) -> tuple[object, object]:
        if ends.held is not None:
            return ends.held
        owner = ends.owner()
        if owner is None:
            owner = ends.data.dying
        contact = ends.contact()
        if owner is None or contact is None or ends.ended:
            raise TagResolutionError("this Link Pair has ended")
        return owner, contact


def _ends_of(pair: object) -> _Ends:
    return object.__getattribute__(pair, "__dict__")[_PAIR_ENDS]


class _Link_Data:
    __slots__ = ("name", "owner", "relation", "pairs", "pair_tag", "link",
                 "running", "ending", "ended", "dying", "handle_token",
                 "contact_tokens", "__weakref__")

    def __init__(data, owner: object, name: str, relation: object) -> None:
        data.name = str.__str__(name)
        data.owner = ref(owner)
        data.relation = relation
        data.pairs: dict[int, _Pair] = {}
        data.pair_tag: type | None = None
        data.link: Any = None
        data.running: set[int] = set()
        data.ending = False
        data.ended = False
        data.dying: object | None = None
        data.handle_token = object()
        data.contact_tokens: dict[int, tuple[Any, object]] = {}

    def Contact_Token(data, contact: object) -> object:
        """Stable handle identity without hashing or owning the Contact."""
        key = id(contact)
        held = data.contact_tokens.get(key)
        if held is not None and held[0]() is contact:
            return held[1]
        data_reference = ref(data)

        def Expired(expired: Any) -> None:
            current_data = data_reference()
            if current_data is None:
                return
            current = current_data.contact_tokens.get(key)
            if current is not None and current[0] is expired:
                current_data.contact_tokens.pop(key)

        token = object()
        data.contact_tokens[key] = ref(contact, Expired), token
        return token

    def Pair(data, contact: object, *, leaving: bool = False) -> _Pair | None:
        pair = data.pairs.get(id(contact))
        if pair is None:
            return None
        ends = _ends_of(pair)
        if ends.contact() is contact or (
                ends.held is not None and ends.held[1] is contact
                ) or (leaving and ends.contact() is None):
            return pair
        return None

    def New(data, owner: object, contact: object) -> _Pair:
        pair = _Pair()
        ends = _Ends(owner, contact, data)
        ends.pair = ref(pair)
        data_reference, pair_reference = ref(data), ref(pair)
        key = id(contact)

        def Expired(expired: Any) -> None:
            current_data, current_pair = data_reference(), pair_reference()
            if current_data is None or current_pair is None:
                return
            current_ends = _ends_of(current_pair)
            if (current_ends.contact is expired and not current_ends.admitted
                    and current_data.pairs.get(key) is current_pair):
                current_data.pairs.pop(key)
                current_ends.ended = True
                pair_state = _state_of(current_pair)
                if pair_state is not None:
                    pair_state.rips.clear()

        ends.contact = ref(contact, Expired)
        object.__getattribute__(pair, "__dict__")[_PAIR_ENDS] = ends
        data.pairs[id(contact)] = pair
        return pair

    def End(data, contact: object, pair: _Pair) -> None:
        if data.pairs.get(id(contact)) is pair:
            data.pairs.pop(id(contact))
        elif contact is None:
            for key, pending in tuple(data.pairs.items()):
                if pending is pair:
                    data.pairs.pop(key)
                    break
        _ends_of(pair).ended = True
        state = _state_of(pair)
        if state is not None:
            state.rips.clear()
        _ends_of(pair).dying_contact = None
        if data.ending and not data.pairs:
            data.dying, data.ending, data.ended = None, False, True


class _Link_Field(_Field):
    def __init__(field, data: _Link_Data) -> None:
        super().__init__()
        field.data = data

    def _Holds(field, contact: object) -> bool:
        pair = field.data.Pair(contact)
        with _post_evaluation():
            return (
                    pair is not None
                    and _holds_for_population(contact)
                    and _holds_for_population(pair)
                    )

    def _Free(field, contact: object) -> bool:
        pair = field.data.Pair(contact)
        return _arrest_of(contact) is None and (
                pair is None or _arrest_of(pair) is None
                )

    def _Inspect(field, contact: object) -> None:
        pair = _current_pair(field.data.link(), contact)
        _inspect(pair)


class _Link_Meta(_Header_Meta):
    """Actual Links keep ordinary Tag population and contract syntax."""

    def __new__(meta, name, bases, namespace, **kwargs):
        _refuse_observed_act("create a Link declaration")
        if any(base is _Link_Header or isinstance(base, _Link_Meta) for base in bases):
            if kwargs:
                raise TagDeclarationError("a Link Form does not accept class keywords")
            return _Captured_Header(name, namespace.get("__orig_bases__", bases), namespace)
        return MetaTag.__new__(meta, name, bases, namespace, **kwargs)

    def __call__(link, contact: object = _MISSING, /, **inputs: Any) -> object:
        from .link_forms import _resolve_seat

        contact = _resolve_seat(contact)
        if contact is _MISSING:
            raise TypeError(f"{link.__name__} links a Contact: {link.__name__}(contact)")
        return _link(link, contact, inputs)

    def __contains__(link, contact: object) -> bool:
        from .link_forms import _resolve_seat

        contact = _resolve_seat(contact)
        if isinstance(contact, str):
            return super().__contains__(contact)
        field = _field_of(link)
        return (contact in field and field._Free(contact)
                and field._Holds(contact) and contact in field
                and field._Free(contact))

    def __getitem__(link, contact: object) -> Any:
        from .link_forms import _resolve_seat

        contact = _resolve_seat(contact)
        if contact is Ellipsis:
            return super().__getitem__(contact)
        if isinstance(contact, slice):
            return super().__getitem__(contact)
        _current_pair(link, contact)
        return _Pair_View(link, contact)

    def __delitem__(link, contact: object) -> None:
        from .link_forms import _resolve_seat

        contact = _resolve_seat(contact)
        if isinstance(contact, slice):
            if contact != slice(None):
                raise TypeError("Link[:] is the whole Field")
            from .lifecycle import _rip_field

            _rip_field(link)
            return
        _rip(contact, link)


def _data_of(link: type) -> _Link_Data:
    return type.__dict__["__dict__"].__get__(link)[_RECORD]


def _grant(
        agent: object,
        state: Any,
        tag: type,
        name: str,
        relation: object,
        ) -> type:
    """Acquire an independent Link at one declaration-ordered Gaining."""
    key = id(tag), name
    held = state.owned_links.get(key)
    if held is None or held[0] is not tag:
        link = _new_link(agent, tag, name, relation)
        state.owned_links[key] = tag, link
    else:
        link = held[1]
    state.links[name] = link
    return link


def _new_link(owner: object, tag: type, name: str, relation: object) -> type:
    data = _Link_Data(owner, name, relation)
    namespace: dict[str, Any] = {
            "__module__": relation.namespace.get("__module__", tag.__module__),
            "__qualname__": f"{tag.__qualname__}.{name}",
            "__doc__": relation.namespace.get("__doc__"),
            FIELD_SEAT: _Link_Field(data),
            _RECORD: data,
            "_topkit_link_coordinate": _Link_Coordinate(owner, tag, name),
            }
    pair_namespace: dict[str, Any] = {
            "__module__": namespace["__module__"],
            "__qualname__": f"{namespace['__qualname__']}.Pair",
            }
    public: list[tuple[str, Any]] = []
    for member_name, member in relation.namespace.items():
        if member_name in _MACHINERY or _is_private(member_name):
            continue
        if isinstance(member, Report):
            report = Report(_tag_function(member.builder, data, member_name))
            report.public = member.public
            namespace[member_name] = report
        elif isinstance(member, (classmethod, staticmethod)):
            if isinstance(member, classmethod):
                namespace[member_name] = classmethod(
                        _tag_function(member.__func__, data, member_name),
                        )
            else:
                namespace[member_name] = member
        elif callable(member):
            pair_namespace[member_name] = _adapt(member, member_name)
            if _has_flag(member, _PUBLIC):
                kind = _kind_of(member)
                if kind not in (None, "action", "record") or _has_flag(member, _RIP):
                    raise TagDeclarationError(
                            f"{name}.{member_name}: only Pair Actions and Records"
                            " can be published onto Contacts"
                            )
                public.append((member_name, member))
        else:
            namespace[member_name] = member
    data.pair_tag = MetaTag(f"{name}_Pair", (Tag,), pair_namespace)
    link = _Link_Meta(name, (Tag,), namespace)
    data.link = ref(link)
    for member_name, member in public:
        if _kind_of(member) == "record":
            line = _Pair_Record_Line(link, member_name)
        else:
            line = _pair_action_line(link, member_name)
        if _has_flag(member, _CONSTANT):
            # Publication exposes the same protected Gain. A Report's
            # declaration marks live on its builder, as in ordinary Tags.
            setattr(line.builder if isinstance(line, Report) else line, _CONSTANT, True)
        type.__setattr__(link, member_name, line)
        if isinstance(line, Report):
            line.__set_name__(link, member_name)
    if public:
        _invalidate_declarations(link)
    return link


def _adapt(function: Any, name: str) -> Any:
    original = _signature_of(function)
    parameters = tuple(original.parameters.values())
    positional = tuple(
            parameter for parameter in parameters
            if parameter.kind in (Parameter.POSITIONAL_ONLY,
                                  Parameter.POSITIONAL_OR_KEYWORD)
            )
    if len(positional) == 1:
        raise TagDeclarationError(
                f"Link protocol {name!r} declares both Agent and Contact seats"
                " or uses the contextual seats without positional parameters"
                )
    take_seats = len(positional) >= 2
    step_result = (
            _kind_of(function) in (None, "action")
            and not _has_flag(function, _RIP)
            )
    ripping = _has_flag(function, _RIP)

    def Adapted(pair: object, *args: Any, **kwargs: Any) -> Any:
        ends = _ends_of(pair)
        owner, contact = ends.Resolve()
        values = (owner, contact) if take_seats else ()
        with _during(ends, ripping=ripping):
            result = _seat_value(function(*values, *args, **kwargs))
        return _stepped(result, ends) if step_result else result

    Adapted.__name__ = str.__str__(name)
    Adapted.__qualname__ = str.__str__(name)
    Adapted.__signature__ = original.replace(parameters=(
            Parameter("_pair", Parameter.POSITIONAL_ONLY),
            *(parameters[2:] if take_seats else parameters),
            ))
    for mark in _MARKS:
        value = getattr_static(function, mark, _MISSING)
        if value is not _MISSING:
            setattr(Adapted, mark, value)
    return Adapted


class _Tag_Ends:
    """Execution context for a Report or Operation owned by an actual Link."""

    __slots__ = ("data",)

    def __init__(ends, data: _Link_Data) -> None:
        ends.data = data

    def Resolve(ends) -> tuple[object, None]:
        owner = ends.data.owner()
        if owner is None:
            owner = ends.data.dying
        if owner is None or ends.data.ended:
            raise TagResolutionError("this Link's Agent no longer exists")
        return owner, None


def _tag_function(function: Any, data: _Link_Data, name: str) -> Any:
    original = _signature_of(function)
    positional = sum(
            parameter.kind in (Parameter.POSITIONAL_ONLY,
                               Parameter.POSITIONAL_OR_KEYWORD)
            for parameter in original.parameters.values()
            )
    ends = _Tag_Ends(data)
    secret_operation = (
            _kind_of(function) == "operation" and _has_flag(function, _SECRET)
            )

    def On_Tag(link: type, *args: Any, **kwargs: Any) -> Any:
        if secret_operation:
            _require_owner_door(data, name)
        with _during(ends):
            result = _seat_value(function(*((link,) if positional else ()), *args, **kwargs))
        if _kind_of(function) == "operation":
            result = _stepped(result, ends)
            if secret_operation:
                result = _secret_result(result, data, name)
        return result

    On_Tag.__name__ = str.__str__(name)
    On_Tag.__qualname__ = str.__str__(name)
    On_Tag.__signature__ = original if positional else original.replace(parameters=(
            Parameter("_link", Parameter.POSITIONAL_ONLY),
            *original.parameters.values(),
            ))
    for mark in _MARKS:
        value = getattr_static(function, mark, _MISSING)
        if value is not _MISSING:
            setattr(On_Tag, mark, value)
    return On_Tag


@contextmanager
def _during(ends: _Ends, *, ripping: bool = False):
    """A Link's code has its owner's door, not its Contact's authority."""
    from .link_forms import _seat_context

    owner, contact = ends.Resolve()
    pair = ends.pair() if isinstance(ends, _Ends) else None
    subjects = tuple(subject for subject in (owner, contact, pair) if subject is not None)
    with ExitStack() as custody:
        if isinstance(ends, _Operation_Ends):
            custody.enter_context(ends.Credential())
        if ripping:
            for subject in subjects:
                custody.enter_context(_rip_door(subject))
        else:
            for subject in subjects:
                _require_available(subject, "Link protocol")
            ends.Resolve()   # a retry may have ended this very Pair
        with _during_seats(ends, owner, contact):
            try:
                yield
            except (StopIteration, StopAsyncIteration):
                # A generator/coroutine completion can carry a value too.
                # Its terminal result needs the same custody boundary as
                # an ordinary yield or synchronous return.
                if not ripping:
                    for subject in subjects:
                        _require_available(subject, "Link protocol result")
                raise
            else:
                if not ripping:
                    for subject in subjects:
                        _require_available(subject, "Link protocol result")


@contextmanager
def _during_seats(ends: _Ends, owner: object, contact: object):
    from .link_forms import _seat_context
    owner_state = _state_of(owner)
    contacts = (
            tuple(_field_of(ends.data.link()))
            if isinstance(ends, _Tag_Ends) else (contact,)
            )
    saved = []
    for target in contacts:
        contact_state = _state_of(target)
        if target is not owner and contact_state is not None:
            saved.append((contact_state, contact_state.composing))
            contact_state.composing = 0
    # Async authority is execution-local; hiding it requires no changes to
    # shared capabilities held by an independently running task.
    token = _async_doors.set(tuple(
            door for door in _async_doors.get()
            if door.active and all(door.state is not state for state, _ in saved)
            ))
    pairs_token = _current_pairs.set(
            (*_current_pairs.get(), ends)
            if isinstance(ends, _Ends) else _current_pairs.get(),
            )
    if owner_state is not None:
        owner_state.composing += 1
    try:
        with _seat_context(owner, contact):
            yield
    finally:
        if owner_state is not None:
            owner_state.composing -= 1
        for state, composing in saved:
            state.composing = composing
        _current_pairs.reset(pairs_token)
        _async_doors.reset(token)


def _stepped(result: Any, ends: _Ends) -> Any:
    kind = _lazy_kind_of(result)
    if kind == 0:
        return _Generator(result, ends)
    if kind == 1:
        return _Coroutine(result, ends)
    if kind == 2:
        return _Async_Generator(result, ends)
    return result


def _park_result(ends: _Ends, source: Any, hold = _hold_lazy_result) -> None:
    """Do not let an abandoned continuation finalize during Rip custody."""
    try:
        owner, contact = ends.Resolve()
    except Exception:
        return
    for subject in (owner, contact):
        if subject is not None:
            hold(subject, source)
    if isinstance(ends, _Ends):
        pair = ends.pair()
        if pair is not None:
            hold(pair, source)
    elif isinstance(ends, _Operation_Ends):
        pair = ends.data.Pair(contact)
        if pair is not None:
            hold(pair, source)


class _Generator:
    __slots__ = ("native", "ends", "__name__", "__qualname__")

    def __init__(result, native: Any, ends: _Ends) -> None:
        result.native, result.ends = native, ends
        result.__name__ = getattr(native, "__name__", "<Link continuation>")
        result.__qualname__ = getattr(native, "__qualname__", result.__name__)

    def __iter__(result):
        return result

    def __next__(result):
        return result.send(None)

    def _resume(result, method, *args, _cancellation=None):
        entered = False
        try:
            with _during(result.ends):
                entered = True
                try:
                    return _seat_value(method(*args))
                except StopIteration as stopped:
                    value = _seat_value(stopped.value)
                    if value is not stopped.value:
                        raise StopIteration(value) from None
                    raise
        except TagArrestedAccessError:
            _park_result(result.ends, result.native)
            if not entered and _cancellation is not None:
                raise _cancellation from None
            raise
        except BaseException:
            # Park before returning control to the caller: cyclic GC may
            # already schedule the native finalizer before a proxy's own
            # __del__ runs. Destructor-only custody is too late.
            _park_result(result.ends, result.native)
            raise

    def send(result, value):
        return result._resume(result.native.send, value)

    def throw(result, *args):
        return result._resume(result.native.throw, *args)

    def close(result):
        return result._resume(result.native.close)

    def __del__(result, park = _park_result):
        park(result.ends, result.native)


class _Coroutine(_Generator, Coroutine):
    def __await__(result):
        return result

    def throw(result, *args):
        cancellation = args[0] if args else None
        if cancellation is CancelledError:
            cancellation = CancelledError()
        elif not issubclass(type(cancellation), CancelledError):
            cancellation = None
        return result._resume(result.native.throw, *args, _cancellation=cancellation)


class _Async_Generator:
    __slots__ = ("native", "ends", "__name__", "__qualname__")

    def __init__(result, native: Any, ends: _Ends) -> None:
        result.native, result.ends = native, ends
        result.__name__ = getattr(native, "__name__", "<Link continuation>")
        result.__qualname__ = getattr(native, "__qualname__", result.__name__)

    def __aiter__(result):
        return result

    def __anext__(result):
        return result.asend(None)

    def _start(result, method, *args):
        with _during(result.ends):
            return _Coroutine(method(*args), result.ends)

    def asend(result, value):
        return result._start(result.native.asend, value)

    def athrow(result, *args):
        return result._start(result.native.athrow, *args)

    def aclose(result):
        return result._start(result.native.aclose)

    def __del__(result, park = _park_result):
        park(result.ends, result.native)


_register_lazy_proxy_types(_Generator, _Coroutine, _Async_Generator)


def _link(link: type, contact: object, inputs: dict[str, Any]) -> object:
    _refuse_observed_act("link a Contact")
    from .link_forms import _resolve_header
    from .link_forms import _seat_context

    data = _data_of(link)
    owner = data.owner()
    if owner is None or data.ended or data.ending:
        raise TagResolutionError("this Link's Agent no longer exists")
    _require_available(owner, "Link Tagging")
    _require_available(contact, "Link Tagging")
    if contact in _field_of(link):
        return contact
    if contact is None or isinstance(contact, type):
        raise TagCompositionError("a Link Contact must be an object, not None or a class")
    _refuse_host_truth(contact)
    if _namespace_of(contact) is None:
        raise TagCompositionError("a Link Contact must support TOP instance storage")
    try:
        ref(contact)
    except TypeError as error:
        raise TagCompositionError("Link Contacts must support weak references") from error
    if id(contact) in data.running:
        return contact
    _require_sound_source(contact, link)
    data.running.add(id(contact))
    pair = None
    try:
        with _seat_context(owner, contact):
            for underlay in _resolve_header(data.relation, owner, contact):
                underlay(contact, **inputs)
        pair = data.Pair(contact)
        if pair is None:
            pair = data.New(owner, contact)

        def Admit_Contact() -> None:
            # This completes the already-started Link attempt. Training
            # may have changed the Contact's Posts, so its source is not
            # judged a second time as though this were a new Tagging.
            _apply(contact, link, {}, check_source=False, check_posts=False)
            state = _state_of(contact)
            state.rips[link] = ((data.name, _unlink_hook(link, pair)),)
            _ends_of(pair).admitted = True

        _apply(
                pair, data.pair_tag, inputs,
                before_gains=lambda: _prepare_contact(contact, link),
                after_training=Admit_Contact,
                post_inspector=lambda: _inspect_link(pair, contact),
                )
    except BaseException:
        if pair is not None and contact not in _field_of(link):
            _withdraw_pair_admission(pair, data.pair_tag)
        raise
    finally:
        data.running.remove(id(contact))
    return contact


def _inspect_link(pair: _Pair, contact: object) -> None:
    """One final diagnostic covers both sides of a Link credential."""
    failures = []
    with _post_evaluation():
        for receiver in (pair, contact):
            try:
                _inspect(receiver)
            except TagPostconditionError as failure:
                failures.append(failure)
    if len(failures) == 1:
        raise failures.pop()
    if failures:
        names = tuple(name for failure in failures
                      for name in getattr(failure, "failed_posts", (failure.name,)))
        details = tuple(str(failure) for failure in failures)
        notes = tuple(note for failure in failures
                      for note in getattr(failure, "__notes__", ()))
        failures.clear()
        failures.append(TaggingFailure(names, details))
        for note in notes:
            BaseException.add_note(failures[0], note)
        raise failures.pop()


def _withdraw_pair_admission(pair: _Pair, tag: type) -> None:
    """An unfinished Link has acquired Gains, but no admitted Contract."""
    state = _state_of(pair)
    if state is None or tag not in state.active:
        return
    state.active.remove(tag)
    state.ever.discard(tag)
    state.words = None
    state.snapshots.pop(tag, None)
    state.rips.pop(tag, None)
    _field_of(tag)._Remove(pair)
    acquired = state.post_applications.pop(tag, None)
    if acquired is not None:
        application, names = acquired
        changed = _remove_post_application(
                state, application, keep_constants=False, names=names,
                )
        if changed:
            next_type = _runtime_type_for(state)
            if type(pair) is not next_type:
                _set_runtime_type(pair, next_type)


def _prepare_contact(contact: object, link: type) -> None:
    """Validate the Contact's host representation after the Pair's Gate.

    The real Contact must accept TOP's mechanical representation before
    relationship training can perform effects. No Field membership or Link
    publication is installed here.
    """
    entry_state = _state_of(contact)
    entry_host = _host_bindings_of(contact) if entry_state is None else None
    previous_arrestable = entry_state.arrestable if entry_state is not None else False
    try:
        state = _state_for(contact)
        # A Contact always receives the Link's saved Unlink protocol, even
        # when its own Tags supplied no Rip. Prepare that custody boundary
        # before any relationship training runs.
        state.arrestable = True
        _actualize(contact, state, link, _declarations_of(link).header)
    except BaseException as error:
        if entry_state is not None:
            entry_state.arrestable = previous_arrestable
        if entry_host is not None:
            _restore_host_bindings(contact, entry_host)
        if isinstance(error, TagCompositionError) and not isinstance(error, TagTargetError):
            raise TagTargetError(
                    f"{link.__name__}: this Contact is not a valid Target for linking"
                    ) from (error.__cause__ if error.__cause__ is not None else error)
        raise


def _unlink_hook(link: type, pair: _Pair):
    def Unlink(contact: object) -> None:
        from .rip_runs import _pending_run
        state = _state_of(contact)
        if (_pending_run(contact, link) is None and state is not None
                and any(active is link for active in state.active)):
            # Host finalization invokes saved callbacks directly. Route a
            # Link's callback through its Contact application first: a
            # failing Pair teardown must keep visible Contact custody too,
            # even if GC has already cleared the Contact's weak Field seat.
            state.rips[link] = ((link.__name__, Unlink),)
            _rip(contact, link)
            return
        _leave(link, contact, pair)

    return Unlink


def _leave(link: type, contact: object, pair: _Pair | None = None) -> None:
    data = _data_of(link)
    if pair is None:
        pair = data.Pair(contact, leaving=True)
    if pair is None:
        return
    ends = _ends_of(pair)
    # Cyclic finalization can clear the owner's weak reference before its
    # failed Rip is retried. The saved application still owns its cleanup
    # seats; losing the public owner must not silently discard that work.
    owner = ends.held[0] if ends.held is not None else data.owner()
    if owner is None:
        owner = data.dying
    if owner is None:
        # In a collected owner/Contact cycle, weak references to both have
        # already been cleared. Contact finalization may arrive first.
        # Its saved run keeps this seat until owner finalization supplies
        # the other one; silently ending here would skip the Rip entirely.
        ends.dying_contact = contact
        raise TagResolutionError("this Link is awaiting its owner's cleanup seat")
    ends.held = owner, contact
    ends.dying_contact = None
    if data.pairs.get(id(contact)) is pair:
        data.pairs.pop(id(contact))
    completed = False
    try:
        state = _state_of(pair)
        from .rip_runs import _pending_run
        if state is not None and (
                data.pair_tag in state.active
                or _pending_run(pair, data.pair_tag) is not None
                ):
            _rip(pair, data.pair_tag)
        completed = True
    finally:
        # A teardown may deliberately reLink this Contact, creating a fresh
        # Pair. Failed old cleanup keeps its own endpoints and Gains until
        # its saved protocol succeeds; it must never consume the new Pair.
        if completed:
            data.End(contact, pair)
            ends.held = None


def _current_pair(link: type, contact: object) -> _Pair:
    data = _data_of(link)
    owner = data.owner()
    if owner is None:
        owner = data.dying
    if owner is not None:
        _require_available(owner, "Link Pair view")
    _require_available(contact, "Link Pair view")
    if contact in _field_of(link):
        pair = data.Pair(contact)
        if pair is not None:
            _require_available(pair, "Link Pair view")
            return pair
    else:
        # Only this Pair's own running protocol can inspect its earlier
        # Gains before admission or during its Rip after Field removal.
        for ends in reversed(_current_pairs.get()):
            if ends.data is data and ends.Resolve()[1] is contact:
                pair = ends.pair()
                if pair is not None:
                    return pair
    raise TagResolutionError(f"the Contact is not admitted to {link.__name__}")


class _Pair_View:
    """A soft call to the same actual Link and Contact, never a Pair copy."""

    __slots__ = ("_link", "_contact")

    def __init__(view, link: type, contact: object) -> None:
        object.__setattr__(view, "_link", ref(link))
        object.__setattr__(view, "_contact", ref(contact))

    def _current(view) -> _Pair:
        link = object.__getattribute__(view, "_link")()
        contact = object.__getattribute__(view, "_contact")()
        if link is None or contact is None:
            raise TagResolutionError("the Link or Contact of this Pair view has ended")
        return _current_pair(link, contact)

    def __getattr__(view, name: str) -> Any:
        pair = view._current()
        state = _state_of(pair)
        if name in state.actions:
            with _pair_access(pair, name):
                getattr(pair, name)   # validate the current Secret/deletion boundary
            return _Pair_Call(view, name, name in state.secrets)
        link = object.__getattribute__(view, "_link")()
        # A failed initializer registers no Record, but a later repair can
        # still create its ordinary Python binding on this Pair.
        if (name in state.records or name in state.postconditions or name in state.deleted
                or name in _namespace_of(pair)):
            with _pair_access(pair, name):
                return getattr(pair, name)
        # Reports stay values of the Link. An Operation read through this
        # live view keeps the same Pair credential when called later.
        declaration = getattr_static(link, name, _MISSING)
        if type(declaration) is _Pair_Record_Line:
            return declaration.Read(object.__getattribute__(view, "_contact")())
        if _kind_of(declaration) == "operation":
            secret = _has_flag(declaration, _SECRET)
            if secret:
                _require_owner_door(_data_of(link), name)
            return _Pair_Operation(view, name, secret)
        return getattr(link, name)

    def __setattr__(view, name: str, value: Any) -> None:
        pair = view._current()
        with _pair_access(pair, name):
            setattr(pair, name, value)

    def __delattr__(view, name: str) -> None:
        pair = view._current()
        with _pair_access(pair, name):
            delattr(pair, name)

    def __bool__(view) -> bool:
        return bool(view._current())

    def __rmatmul__(view, name: object) -> Any:
        if not isinstance(name, str):
            return NotImplemented
        pair = view._current()
        link = object.__getattribute__(view, "_link")()
        try:
            with _pair_access(pair, name):
                present = name @ pair
        except AttributeError:
            return False
        declaration = getattr_static(link, name, _MISSING)
        if _kind_of(declaration) == "operation" and _has_flag(declaration, _SECRET):
            try:
                _require_owner_door(_data_of(link), name)
            except AttributeError:
                return False
        return present or (
                declaration is not _MISSING
                and type(declaration) is not _Pair_Record_Line
                )

    def __repr__(view) -> str:
        return "<live Link Pair view>"


class _Pair_Call:
    __slots__ = ("view", "name", "secret", "_key")

    def __init__(call, view: _Pair_View, name: str, secret: bool) -> None:
        call.view, call.name, call.secret = view, name, secret
        link = object.__getattribute__(view, "_link")()
        contact = object.__getattribute__(view, "_contact")()
        data = _data_of(link)
        call._key = data.handle_token, data.Contact_Token(contact), str.__str__(name)

    def __call__(call, *args: Any, **kwargs: Any) -> Any:
        pair = call.view._current()
        secret = call.secret or call.name in _state_of(pair).secrets
        with _pair_access(pair, call.name, secret=call.secret):
            result = getattr(pair, call.name)(*args, **kwargs)
        return (_secret_result(result, _ends_of(pair).data, call.name)
                if secret else result)

    @property
    def __name__(call) -> str:
        return call.name

    @property
    def __self__(call) -> _Pair_View:
        return call.view

    @property
    def __func__(call) -> Any:
        pair = call.view._current()
        with _pair_access(pair, call.name, secret=call.secret):
            return getattr(pair, call.name).__func__

    @property
    def __signature__(call) -> Any:
        signature = _signature_of(call.__func__)
        return signature.replace(parameters=tuple(signature.parameters.values())[1:])

    def __eq__(call, other: object) -> Any:
        if type(other) is not type(call):
            return NotImplemented
        return (
                call._key[0] is other._key[0]
                and call._key[1] is other._key[1]
                and call._key[2] == other._key[2]
                )

    def __hash__(call) -> int:
        return hash(call._key)

    def __repr__(call) -> str:
        return f"<live Pair Action {call.name}>"


class _Operation_Ends(_Tag_Ends):
    """A Tag Operation reached through one live Pair view."""

    __slots__ = ("view", "name", "secret")

    def __init__(ends, view: _Pair_View, name: str, secret: bool) -> None:
        view._current()
        link = object.__getattribute__(view, "_link")()
        super().__init__(_data_of(link))
        ends.view, ends.name, ends.secret = view, name, secret

    def Resolve(ends) -> tuple[object, object]:
        owner, _ = super().Resolve()
        contact = object.__getattribute__(ends.view, "_contact")()
        if contact is None:
            raise TagResolutionError("the Contact of this Pair view has ended")
        return owner, contact

    def Check(ends) -> None:
        ends.view._current()
        link = ends.data.link()
        _require_available(link, "Link-view Operation")
        declaration = getattr_static(link, ends.name, _MISSING)
        if _kind_of(declaration) != "operation":
            raise AttributeError(f"{ends.name!r} is no longer an Operation")
        if ends.secret or _has_flag(declaration, _SECRET):
            _require_owner_door(ends.data, ends.name)
        _owner, contact = ends.Resolve()
        if ends.name in _state_of(contact).snapshots[link].actions:
            _require_membership(contact, link, ends.name, "Operation")
        ends.view._current()

    @contextmanager
    def Credential(ends):
        ends.Check()
        try:
            yield
        except (StopIteration, StopAsyncIteration):
            ends.Check()
            raise
        else:
            ends.Check()


class _Pair_Operation(_Pair_Call):
    __slots__ = ()

    def __call__(call, *args: Any, **kwargs: Any) -> Any:
        ends = _Operation_Ends(call.view, call.name, call.secret)
        with _during(ends):
            _owner, contact = ends.Resolve()
            link = ends.data.link()
            operation = getattr(link, call.name)
            public = call.name in _state_of(contact).snapshots[link].actions
            result = operation(*((contact,) if public else ()), *args, **kwargs)
        return _stepped(result, ends)

    @property
    def __func__(call) -> Any:
        ends = _Operation_Ends(call.view, call.name, call.secret)
        ends.Check()
        return getattr(ends.data.link(), call.name).__func__

    @property
    def __signature__(call) -> Any:
        ends = _Operation_Ends(call.view, call.name, call.secret)
        ends.Check()
        _owner, contact = ends.Resolve()
        link = ends.data.link()
        signature = _signature_of(getattr(link, call.name))
        if call.name in _state_of(contact).snapshots[link].actions:
            signature = signature.replace(parameters=tuple(signature.parameters.values())[1:])
        return signature

    def __repr__(call) -> str:
        return f"<live Pair-view Operation {call.name}>"


def _require_owner_door(data: _Link_Data, name: str) -> None:
    owner = data.owner()
    if owner is None:
        owner = data.dying
    state = None if owner is None else _state_of(owner)
    if state is None or not _is_composing(state):
        raise AttributeError(
                f"{name!r} is a Secret of this Link's Agent; its door is closed"
                )


def _secret_result(result: Any, data: _Link_Data, name: str) -> Any:
    """A captured Secret continuation needs its caller's current owner door."""
    owner = data.owner()
    if owner is None:
        owner = data.dying

    def Authorize(receiver: object, act: str) -> None:
        _require_available(receiver, act)
        _require_owner_door(data, name)

    return _guard_lazy_result(result, owner, "Secret Link continuation", Authorize)


@contextmanager
def _pair_access(pair: _Pair, name: str, *, secret: bool = False):
    state = _state_of(pair)
    needed = secret or name in state.secrets
    if needed:
        _require_owner_door(_ends_of(pair).data, name)
        state.composing += 1
    try:
        yield
    finally:
        if needed:
            state.composing -= 1


def _pair_action_line(link: type, name: str):
    reference = ref(link)

    def Line(contact: object, *args: Any, **kwargs: Any) -> Any:
        actual = reference()
        if actual is None:
            raise TagResolutionError("this published Link no longer exists")
        _require_membership(contact, actual, name, "Action")
        return getattr(_current_pair(actual, contact), name)(*args, **kwargs)

    Line.__name__ = name
    return Line


class _Pair_Record_Line(Report, _Line):
    def __init__(line, link: type, name: str) -> None:
        Report.__init__(line, lambda tag: None)
        line.public = True
        line.link, line.name = ref(link), name

    def __get__(line, instance: object, owner: type | None = None) -> Any:
        return line

    def Read(line, contact: object) -> Any:
        link = line.link()
        if link is None:
            raise TagResolutionError("this published Link no longer exists")
        return getattr(_current_pair(link, contact), line.name)

    def Present(line, contact: object) -> bool:
        link = line.link()
        return (link is not None and contact in _field_of(link)
                and line.name @ _current_pair(link, contact))


def _end_links(agent: object) -> None:
    """End owned Links during Agent finalization, with its live owner seat."""
    state = _state_of(agent)
    if state is None:
        return
    links = []
    seen = set()
    for _tag, link in state.owned_links.values():
        if id(link) not in seen:
            seen.add(id(link))
            links.append(link)
    interrupted: BaseException | None = None
    for link in links:
        data = _data_of(link)
        data.dying, data.ending = agent, True
        try:
            contacts = []
            for pair in tuple(data.pairs.values()):
                ends = _ends_of(pair)
                if not ends.admitted:
                    # A refused Link never admitted a Contact. There is
                    # no Contact membership whose finalizer can follow.
                    target = ends.contact()
                    data.End(target, pair)
                    continue
                target = ends.dying_contact
                if target is not None and all(target is not held for held in contacts):
                    contacts.append(target)
            # Ending an owner ends each actual Link as a whole Field,
            # with the same revocation boundary as explicit del Link[:].
            # A failed callback leaves the other saved runs in custody.
            _rip_field(link)
            for contact in contacts:
                _rip(contact, link)
        except Exception:
            pass   # saved work remains visible for an explicit retry
        except BaseException as error:
            interrupted = interrupted or error
        finally:
            # A cyclic Contact's weak Field seat can disappear before its
            # finalizer arrives. Keep only the finalizing owner's seat for
            # those admitted Pairs; the last Contact handoff releases it.
            if not data.pairs:
                data.dying, data.ending, data.ended = None, False, True
    if interrupted is not None:
        raise interrupted
