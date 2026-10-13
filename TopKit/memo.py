"""Owner-local Tag memos and snapshots of their changing class namespace.

The lock owns no Tags. A memo may refer back to its owner, leaving a
collectible cycle rather than a global or public-Field lifetime root.
User declaration inspection runs outside the lock, over a copied namespace.
"""

from dataclasses import dataclass
from _thread import RLock
from typing import Any


_publication = RLock()
_type_namespace = type.__dict__["__dict__"]
_type_mro = type.__dict__["__mro__"]


@dataclass(frozen=True, slots=True)
class _Tag_Memo:
    owner: type
    name: str
    value: Any


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
        return memo.value
    return None


def _remember_memo(tag: type, name: str, value: Any) -> Any:
    with _publication:
        existing = _memo_of(tag, name)
        if existing is not None:
            return existing
        if not _metaclass_binding(tag, name) and all(
               name not in _class_namespace(base)
               for base in _type_mro.__get__(tag)):
            type.__setattr__(tag, name, _Tag_Memo(tag, name, value))
    return value


def _forget_memo(tag: type, name: str) -> None:
    with _publication:
        if _memo_of(tag, name) is not None and not _metaclass_binding(tag, name):
            type.__delattr__(tag, name)


def _namespace_snapshot(tag: type) -> dict[str, Any]:
    # mappingproxy.copy copies the underlying class dict before user
    # metadata access can yield to another memo reader/publisher.
    with _publication:
        return _class_namespace(tag).copy()
