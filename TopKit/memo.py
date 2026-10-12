"""Owner-local Tag memos and snapshots of their changing class namespace.

The lock owns no Tags. A memo may refer back to its owner, leaving a
collectible cycle rather than a global or public-Field lifetime root.
User declaration inspection runs outside the lock, over a copied namespace.
"""

from dataclasses import dataclass
from threading import RLock
from typing import Any


_publication = RLock()


@dataclass(frozen=True, slots=True)
class _Tag_Memo:
    owner: type
    name: str
    value: Any


def _memo_key(tag: type, kind: str) -> str:
    return f"_TOPKIT_{kind}_{id(tag):#x}"


def _memo_of(tag: type, name: str) -> Any:
    memo = vars(tag).get(name)
    if type(memo) is _Tag_Memo and memo.owner is tag and memo.name == name:
        return memo.value
    return None


def _remember_memo(tag: type, name: str, value: Any) -> Any:
    with _publication:
        existing = _memo_of(tag, name)
        if existing is not None:
            return existing
        if all(name not in vars(base) for base in tag.__mro__):
            type.__setattr__(tag, name, _Tag_Memo(tag, name, value))
    return value


def _forget_memo(tag: type, name: str) -> None:
    with _publication:
        if _memo_of(tag, name) is not None:
            type.__delattr__(tag, name)


def _namespace_snapshot(tag: type) -> dict[str, Any]:
    # mappingproxy.copy copies the underlying class dict before user
    # metadata access can yield to another memo reader/publisher.
    with _publication:
        return vars(tag).copy()
