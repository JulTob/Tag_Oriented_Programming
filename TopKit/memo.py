"""Owner-local Tag memos and snapshots of their changing class namespace.

The lock owns no Tags. A memo may refer back to its owner, leaving a
collectible cycle rather than a global or public-Field lifetime root.
User declaration inspection runs outside the lock, over a copied namespace.
"""

from dataclasses import dataclass
from threading import RLock
from typing import Any


_publication = RLock()
_type_namespace = type.__dict__["__dict__"]
_type_mro = type.__dict__["__mro__"]
_type_bases = type.__dict__["__bases__"]


@dataclass(slots=True)
class _Memo_Payload:
    value: Any


@dataclass(frozen=True, slots=True)
class _Tag_Memo:
    owner: type
    name: str
    payload: _Memo_Payload


def _memo_key(tag: type, kind: str) -> str:
    return f"_TOPKIT_{kind}_{id(tag):#x}"


def _class_namespace(tag: type) -> Any:
    # vars/type.__getattribute__ can still evaluate a metaclass property.
    return _type_namespace.__get__(tag)


def _metaclass_binding(tag: type, name: str) -> bool:
    return any(name in _class_namespace(base)
               for base in _type_mro.__get__(type(tag)))


def _memo_of(tag: type, name: str) -> Any:
    # A physical read never evaluates a metaclass descriptor, so the warm
    # path needs no metaclass walk; publication and invalidation check it
    # before assigning or deleting through the type.
    memo = _class_namespace(tag).get(name)
    if type(memo) is _Tag_Memo and memo.owner is tag and memo.name == name:
        return memo.payload.value
    return None


def _remember_memo(tag: type, name: str, value: Any) -> Any:
    with _publication:
        existing = _memo_of(tag, name)
        if existing is not None:
            return existing
        if _metaclass_binding(tag, name):
            return value
        memo = _class_namespace(tag).get(name)
        if type(memo) is _Tag_Memo and memo.owner is tag and memo.name == name:
            # A retired owner-local wrapper may remain behind a program
            # descriptor. Once that collision is gone, reuse it only if
            # no Base has acquired a binding at the same key.
            if all(name not in _class_namespace(base)
                   for base in _type_mro.__get__(tag)[1:]):
                memo.payload.value = value
        elif all(name not in _class_namespace(base)
                 for base in _type_mro.__get__(tag)):
            type.__setattr__(tag, name, _Tag_Memo(tag, name, _Memo_Payload(value)))
    return value


def _forget_memo(tag: type, name: str) -> None:
    with _publication:
        memo = _class_namespace(tag).get(name)
        if type(memo) is _Tag_Memo and memo.owner is tag and memo.name == name:
            # Retire the value even when deleting the class binding would
            # call a program's metaclass descriptor. A later warm read
            # must miss, and the old scan must release its references.
            memo.payload.value = None
            # Releasing the old value may run a finalizer or weakref
            # callback that replaces the class binding. Delete only the
            # same wrapper we just retired.
            if (not _metaclass_binding(tag, name)
                    and _class_namespace(tag).get(name) is memo):
                type.__delattr__(tag, name)


def _namespace_snapshot(tag: type) -> dict[str, Any]:
    # mappingproxy.copy copies the underlying class dict before user
    # metadata access can yield to another memo reader/publisher.
    with _publication:
        return _class_namespace(tag).copy()
