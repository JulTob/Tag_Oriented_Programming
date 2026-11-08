"""Diagrams: an Agent's Geometry, or a Tag's Form, drawn as Mermaid.

``Diagram`` returns Mermaid flowchart text and ``Save`` writes it to ``.mmd``
files; both need nothing outside the standard library. ``Save(...,
image="svg")`` or ``image="png"`` also draws each file with
mermaid-rs-renderer, through the optional ``mmdr`` package:
``pip install "topkit[diagram]"``.

Each Tag box lists the Contributions and conditions the Tag declares itself.
An arrow runs from a Base to its Shape, in Forming order. On an Agent, the
host points at each Tag without an active Base, a broken Postcondition is
marked, and Ripped Tags stay as dashed boxes. On a Tag, its Pins hang from it.

A diagram with more Tags than ``limit`` is divided by code: each family of
Tags joined through Bases goes to the module that declares its top Base,
and each part is named for its module. The limit is soft; a family is
never split, and only a module still above the limit is split, between
families, into ``module (2)`` and so on.
"""

from __future__ import annotations

import re
import sys
from os import PathLike
from pathlib import Path

from .contracts import Contract
from .declarations import _UNDERLAY
from .declarations import _declarations_of
from .declarations import _has_flag
from .declarations import _is_pin
from .geometry import _direct_bases
from .geometry import _form_of
from .geometry import _is_tag
from .state import _name_of
from .state import _state_of


LIMIT = 40
_HOST = None
_ESCAPES = {
        "#": "#35;",
        '"': "#quot;",
        "<": "#lt;",
        ">": "#gt;",
        "\n": " ",
        }
# Strokes and text only, no fills: a fill fixed for a light page leaves the
# theme's text unreadable on a dark one, and the reverse.
_STYLES = {
        "host": "stroke-width:3px",
        "pin": "stroke:#d4a017,stroke-width:2px",
        "broken": "stroke:#e5484d,stroke-width:3px,color:#e5484d",
        "ripped": "stroke:#8b8b8b,stroke-dasharray:6 3,color:#8b8b8b",
        }


def _text(
        text: str,
        ) -> str:
    return "".join(_ESCAPES.get(c, c) for c in text)


def _members(
        tag: type,
        broken: set[str],
        ) -> list[str]:
    """One line for each kind of declaration the Tag makes itself."""

    found = _declarations_of(tag)
    rips = set(found.rips)

    def name(member: str, function: object = None, public: bool = False) -> str:
        marks = []

        if function is not None and _has_flag(function, _UNDERLAY):
            marks.append("underlay")
        if member in found.secrets:
            marks.append("secret")
        if public or member in found.published:
            marks.append("public")
        if member in found.constants:
            marks.append("constant")
        if member in found.tools:
            marks.append("tool")

        return f"{member} ({', '.join(marks)})" if marks else member

    def post(member: str, function: object) -> str:
        shown = name(member, function)
        return f"{shown} BROKEN" if member in broken else shown

    kinds = (
            ("Pre", [name(n, f) for n, f in found.preconditions]),
            ("Post", [post(n, f) for n, f in found.postconditions]),
            ("Imprint", [name(n, f) for n, f in found.imprints]),
            ("Record", [name(n, f) for n, f in found.records]),
            ("Action", [name(n, f) for n, f in found.actions if n not in rips]),
            ("Rip", [name(n, f) for n, f in found.actions if n in rips]),
            ("Delete", [name(n) for n in found.deletions]),
            ("Report", [name(n, None, p) for n, _, p in found.reports]),
            ("Operation", [name(n, f, p) for n, f, p in found.operations]),
            )

    return [
            f"{kind}: {', '.join(names)}"
            for kind, names in kinds
            if names
            ]


class _Graph:
    """What one diagram draws, before it is divided into parts."""

    def __init__(
            self,
            subject: object,
            ) -> None:
        self.host = _name_of(subject)
        self.has_host = not _is_tag(subject)
        self.tags: list[type] = []
        self.carried: set[type] = set()
        self.ripped: set[type] = set()
        # (source, Shape, label); source is _HOST for the host.
        self.arrows: list[tuple[object, type, str | None]] = []

        if _is_tag(subject):
            form = _form_of(subject)
            self.tags.extend(form)

            for tag in form:
                self.arrows.extend(
                        (base, tag, None)
                        for base in _direct_bases(tag)
                        if base in form
                        )

        state = _state_of(subject)
        active = list(state.active) if state is not None else []
        ripped = (
                sorted(state.ever - set(active), key=lambda t: t.__name__)
                if state is not None else []
                )
        # A Post name is checked once, on the latest Layer that declares it.
        # A Ripped Tag can still hold one: a Constant Post outlives its Rip.
        self.broken: dict[type, set[str]] = {}
        verdicts = Contract.Status(subject) if state is not None else {}

        for name, holds in verdicts.items():
            for tag in [*reversed(active), *ripped]:
                if not holds and any(n == name for n, _ in _declarations_of(tag).postconditions):
                    self.broken.setdefault(tag, set()).add(name)
                    break

        source = _HOST if self.has_host else subject
        carry = None if self.has_host else "pins"

        # A Base Ripped and applied again comes after its Shape in `active`,
        # so Bases are looked up in the whole active set, not in the order.
        self.carried.update(active)

        for tag in active:
            self._add(tag)
            bases = [base for base in _direct_bases(tag) if base in self.carried]
            self.arrows.extend((base, tag, None) for base in bases)

            if not bases:
                self.arrows.append((source, tag, carry))

        for tag in ripped:
            self._add(tag)
            self.ripped.add(tag)
            self.arrows.append((source, tag, "ripped"))

    def _add(
            self,
            tag: type,
            ) -> None:
        if tag not in self.tags:
            self.tags.append(tag)

    def parts(
            self,
            limit: int,
            ) -> tuple[list[list[type]], list[str]]:
        """The parts and their names. Up to ``limit`` Tags draw as one part,
        named for the host. Above it, each family of Tags joined through
        Bases goes to the module that declares its top Base, and each
        module is one part, named for the module. The limit is soft: a
        module above it is split between families, never inside one, and
        its later parts are numbered: ``module (2)``."""

        if len(self.tags) <= limit:
            return [list(self.tags)], [self.host]

        root = {tag: tag for tag in self.tags}

        def find(tag: type) -> type:
            while root[tag] is not tag:
                root[tag] = root[root[tag]]
                tag = root[tag]
            return tag

        # Every arrow but the host's joins a family, so no arrow is cut:
        # a Tag's own drawing, Form and Pins, is one family.
        for source, shape, _ in self.arrows:
            if source is not _HOST:
                root[find(source)] = find(shape)

        families: dict[type, list[type]] = {}
        for tag in self.tags:
            families.setdefault(find(tag), []).append(tag)

        modules: dict[str, list[list[type]]] = {}
        for family in families.values():
            modules.setdefault(_module_of(family[0]), []).append(family)

        parts: list[list[type]] = []
        names: list[str] = []

        for module, members in modules.items():
            count = 0
            part: list[type] = []

            for family in [*members, None]:
                if part and (family is None or len(part) + len(family) > limit):
                    count += 1
                    parts.append(part)
                    names.append(module if count == 1 else f"{module} ({count})")
                    part = []

                if family is not None:
                    part.extend(family)

        if len(parts) == 1:                    # one family: nothing to divide
            names = [self.host]

        return parts, names


def _module_of(
        tag: type,
        ) -> str:
    """The module that declares a Tag; a script by its file name."""

    module = tag.__module__

    if module == "__main__":
        script = getattr(sys.modules.get(module), "__file__", None)

        if script:
            return Path(script).stem

    return module


def _draw(
        graph: _Graph,
        parts: list[list[type]],
        names: list[str],
        index: int,
        direction: str,
        ) -> str:
    ids: dict[object, str] = {tag: f"t{i}" for i, tag in enumerate(graph.tags)}
    ids[_HOST] = "host"
    drawn = set(parts[index])
    lines = [f"flowchart {direction}"]
    classes = []

    if graph.has_host:
        head = _text(graph.host)

        if len(parts) > 1:
            # In the box, not a title: not every renderer draws Mermaid titles.
            head += f"<br>{_text(names[index])}"

        lines.append(f'  host["{head}"]')
        classes.append("  class host host")

    for tag in parts[index]:
        members = _members(tag, graph.broken.get(tag, set()))
        label = "<br>".join(_text(line) for line in [tag.__name__, *members])
        lines.append(f'  {ids[tag]}["{label}"]')

        if tag in graph.broken:                # a broken promise outranks a Rip
            classes.append(f"  class {ids[tag]} broken")
        elif tag in graph.ripped:
            classes.append(f"  class {ids[tag]} ripped")
        elif _is_pin(tag):
            classes.append(f"  class {ids[tag]} pin")

    for source, shape, label in graph.arrows:
        if shape in drawn:
            arrow = f"-.->|{label}|" if label else "-->"
            lines.append(f"  {ids[source]} {arrow} {ids[shape]}")

    used = {line.rsplit(" ", 1)[1] for line in classes}
    lines.extend(
            f"  classDef {name} {style}"
            for name, style in _STYLES.items()
            if name in used
            )
    lines.extend(classes)

    return "\n".join(lines) + "\n"


def Diagram(
        subject: object,
        *,
        limit: int = LIMIT,
        direction: str = "TD",
        ) -> dict[str, str]:
    """Mermaid flowcharts of an Agent's Geometry or a Tag's Form, by name.

    One flowchart, named for the subject; or, with more than ``limit``
    Tags, one for each module that declares them, named for the module."""

    if limit < 1:
        raise ValueError("a diagram part holds at least one Tag")

    graph = _Graph(subject)
    parts, names = graph.parts(limit)

    return {
            names[index]: _draw(graph, parts, names, index, direction)
            for index in range(len(parts))
            }


_IMAGES = ("svg", "png")


def Save(
        subject: object,
        path: str | PathLike[str],
        *,
        limit: int = LIMIT,
        direction: str = "TD",
        image: str | None = None,
        ) -> tuple[Path, ...]:
    """Write ``Diagram(subject)`` as Mermaid files, ``<stem>.mmd``.

    One part is written to ``path`` with the suffix ``.mmd``; several parts
    beside it, each named ``<stem>-<part name>.mmd``, with characters other
    than letters, digits, ``_`` and ``-`` made ``_``. ``image="svg"`` or
    ``image="png"`` also draws each part beside its Mermaid file with
    mermaid-rs-renderer, through the optional ``mmdr`` package
    (``pip install "topkit[diagram]"``). Returns the written paths."""

    if image is not None and image not in _IMAGES:
        raise ValueError(f"image is one of {', '.join(_IMAGES)}, or None")

    draw = None

    if image is not None:
        try:
            import mmdr
        except ImportError as error:
            raise ImportError(
                    f"image={image!r} draws with mermaid-rs-renderer through the"
                    ' optional mmdr package: pip install "topkit[diagram]".'
                    " Without image=, Save writes the Mermaid files alone."
                    ) from error

        def draw(text: str, out: Path) -> None:
            drawn = mmdr.render(text, backend="mermaid-rs-renderer")

            if image == "svg":
                out.write_text(drawn.svg(), encoding="utf-8")
            else:
                out.write_bytes(drawn.png())

    diagrams = Diagram(
            subject,
            limit=limit,
            direction=direction,
            )
    path = Path(path)
    stems: list[str] = []
    written: list[Path] = []

    for name, text in diagrams.items():
        stem = path.stem

        if len(diagrams) > 1:
            # Distinct names can share a slug ("game.feats" and "game_feats").
            slug = re.sub(r"[^\w-]+", "_", name).strip("_") or "part"
            stem = f"{path.stem}-{slug}"
            count = 1

            while stem in stems:
                count += 1
                stem = f"{path.stem}-{slug}-{count}"

        stems.append(stem)
        source = path.with_name(f"{stem}.mmd")
        source.write_text(text, encoding="utf-8")
        written.append(source)

        if draw is not None:
            out = path.with_name(f"{stem}.{image}")
            draw(text, out)
            written.append(out)

    return tuple(written)
