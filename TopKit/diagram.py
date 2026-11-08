"""Diagrams: an Agent's Geometry, or a Tag's Form, drawn as Mermaid or
Graphviz.

``Diagram`` returns chart text and ``Save`` writes it to files: Mermaid
``.mmd`` by default, or Graphviz ``.dot`` with ``format="graphviz"``; both
need nothing outside the standard library. ``Save(..., image="svg")`` or
``image="png"`` also draws each file: Mermaid with merman, through the
optional ``mmdr`` package (``pip install "topkit[diagram]"``), Graphviz with
its ``dot`` command.

Each Tag box lists the Contributions and conditions the Tag declares itself.
An arrow runs from a Base to its Shape, in Forming order. On an Agent, the
host points at each Tag without an active Base, a broken Postcondition is
marked, and Ripped Tags stay as dashed boxes. On a Tag, its Pins hang from
it. When a chart holds Tags of several modules, each module is a box.

A diagram with more Tags than ``limit`` is divided by code: each family of
Tags joined through Bases goes to the module that declares its top Base,
and each part is named for its module. The limit is soft; a family is
never split, so one family larger than the limit stays one chart, and only
a module still above the limit is split, between families, into
``module (2)`` and so on.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from os import PathLike
from pathlib import Path

from .contracts import Contract
from .declarations import _UNDERLAY
from .declarations import _declarations_of
from .declarations import _has_flag
from .declarations import _is_flag
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
_HTML_ESCAPES = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "\n": " ",
        }
# Mermaid: strokes and text only, no fills. A .mmd is drawn in the viewer's
# theme, and a fill fixed for a light page leaves a dark theme's text
# unreadable, and the reverse.
_MERMAID_STYLES = {
        "host": "stroke-width:3px",
        "pin": "stroke:#d4a017,stroke-width:2px",
        "flag": "stroke:#0d9488,stroke-width:2px",
        "broken": "stroke:#e5484d,stroke-width:3px,color:#e5484d",
        "ripped": "stroke:#8b8b8b,stroke-dasharray:6 3,color:#8b8b8b",
        "module": "fill:none,stroke:#94a3b8,stroke-dasharray:4 4",
        }
# What a Tag is picks its box: rounded for a Tag, a hexagon for a Pin, a
# flag for a Flag.
_MERMAID_SHAPES = {
        "tag": ("(", ")"),
        "pin": ("{{", "}}"),
        "flag": (">", "]"),
        }
# Graphviz draws its own page, so the look is fixed: soft lines, rounded boxes.
_RANKDIR = {"TD": "TB"}
_FONT = 'fontname="Helvetica,Arial,sans-serif"'
_DOT_GRAPH = f"{_FONT}, nodesep=0.3, ranksep=0.45, fontsize=11"
_DOT_NODE = f'shape=box, style=rounded, {_FONT}, fontsize=11, color="#64748b", margin="0.16,0.07"'
_DOT_EDGE = f'{_FONT}, fontsize=9, color="#64748b", fontcolor="#64748b", arrowsize=0.7'
_DOT_SHAPES = {
        "tag": "shape=box",
        "pin": "shape=hexagon",
        "flag": "shape=cds",
        }
_DOT_LOOKS = {
        "host": 'penwidth=2.2, color="#334155"',
        "pin": 'color="#d4a017", penwidth=1.6',
        "flag": 'color="#0d9488", penwidth=1.6',
        "broken": 'color="#e5484d", fontcolor="#e5484d", penwidth=2',
        "ripped": 'style="rounded,dashed", color="#8b8b8b", fontcolor="#8b8b8b"',
        "module": 'style="rounded,dashed", color="#94a3b8", fontcolor="#64748b"',
        }
# Each member kind by what it does: checks, state, behaviour.
_DOT_MEMBER_COLORS = {
        "Pre": "#2563eb",
        "Post": "#2563eb",
        "Imprint": "#2563eb",
        "Record": "#059669",
        "Report": "#059669",
        "Action": "#7c3aed",
        "Operation": "#7c3aed",
        "Rip": "#7c3aed",
        "Delete": "#7c3aed",
        }


def _text(
        text: str,
        ) -> str:
    return "".join(_ESCAPES.get(c, c) for c in text)


def _members(
        tag: type,
        broken: set[str],
        ) -> list[tuple[str, str]]:
    """``(kind, names)`` for each kind of declaration the Tag makes itself."""

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
            (kind, ", ".join(names))
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
                sorted(
                        state.ever - set(active),
                        key=lambda t: (t.__name__, t.__module__, t.__qualname__),
                        )
                if state is not None else []
                )
        # A Post name is checked once, on its latest Layer. A Constant Post
        # outlives its Tag's Rip, so that Layer's Tag may be a Ripped one.
        self.broken: dict[type, set[str]] = {}
        verdicts = Contract.Status(subject) if state is not None else {}

        for name, holds in verdicts.items():
            layers = state.post_layers.get(name, ())

            if not holds and layers:
                self.broken.setdefault(layers[-1].tag, set()).add(name)

        source = _HOST if self.has_host else subject
        carry = None if self.has_host else "pins"
        live = set(active)
        # Base-first, even after a Base was Ripped and Tagged again: then it
        # comes after its Shape in `active`. A family then starts at its top
        # Base, whose module it goes to.
        forming = dict.fromkeys(t for tag in active for t in _form_of(tag) if t in live)

        for tag in forming:
            self._add(tag)
            self.carried.add(tag)
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


def _kind(
        tag: type,
        ) -> str:
    """What a Tag is, which picks its box's shape: a Pin, a Flag or a Tag."""

    if _is_pin(tag):
        return "pin"
    if _is_flag(tag):
        return "flag"
    return "tag"


def _look(
        graph: _Graph,
        tag: type,
        ) -> str | None:
    """The one mark a Tag box's lines carry: a broken promise outranks a
    Rip, and either outranks the color of a Pin or a Flag."""

    if tag in graph.broken:
        return "broken"
    if tag in graph.ripped:
        return "ripped"
    kind = _kind(tag)
    return kind if kind != "tag" else None


def _by_module(
        part: list[type],
        ) -> dict[str, list[type]]:
    """The part's Tags under the module that declares each one."""

    modules: dict[str, list[type]] = {}

    for tag in part:
        modules.setdefault(_module_of(tag), []).append(tag)

    return modules


def _mermaid(
        graph: _Graph,
        part: list[type],
        name: str | None,
        direction: str,
        ) -> str:
    ids: dict[object, str] = {tag: f"t{i}" for i, tag in enumerate(graph.tags)}
    ids[_HOST] = "host"
    lines = [f"flowchart {direction}"]
    classes = []

    if graph.has_host:
        # The part's name in the box, not a title: not every renderer
        # draws Mermaid titles.
        head = _text(graph.host) + (f"<br>{_text(name)}" if name else "")
        lines.append(f'  host(["{head}"])')
        classes.append("  class host host")

    modules = _by_module(part)
    boxed = len(modules) > 1

    for number, (module, tags) in enumerate(modules.items()):
        indent = "    " if boxed else "  "

        if boxed:
            lines.append(f'  subgraph m{number}["{_text(module)}"]')

        for tag in tags:
            members = _members(tag, graph.broken.get(tag, set()))
            label = "<br>".join([
                    _text(tag.__name__),
                    *(_text(f"{kind}: {names}") for kind, names in members),
                    ])
            opening, closing = _MERMAID_SHAPES[_kind(tag)]
            lines.append(f'{indent}{ids[tag]}{opening}"{label}"{closing}')
            look = _look(graph, tag)

            if look:
                classes.append(f"  class {ids[tag]} {look}")

        if boxed:
            lines.append("  end")
            classes.append(f"  class m{number} module")

    drawn = set(part)

    for source, shape, label in graph.arrows:
        if shape in drawn:
            arrow = f"-.->|{label}|" if label else "-->"
            lines.append(f"  {ids[source]} {arrow} {ids[shape]}")

    used = {line.rsplit(" ", 1)[1] for line in classes}
    lines.extend(
            f"  classDef {look} {style}"
            for look, style in _MERMAID_STYLES.items()
            if look in used
            )
    lines.extend(classes)

    return "\n".join(lines) + "\n"


def _html(
        text: str,
        ) -> str:
    return "".join(_HTML_ESCAPES.get(c, c) for c in text)


def _quoted(
        text: str,
        ) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def _graphviz(
        graph: _Graph,
        part: list[type],
        name: str | None,
        direction: str,
        ) -> str:
    ids: dict[object, str] = {tag: f"t{i}" for i, tag in enumerate(graph.tags)}
    ids[_HOST] = "host"
    small = '<FONT POINT-SIZE="9">{}</FONT>'
    lines = [
            f"digraph {_quoted(name or graph.host)} {{",
            f"  graph [rankdir={_RANKDIR.get(direction, direction)}, {_DOT_GRAPH}];",
            f"  node [{_DOT_NODE}];",
            f"  edge [{_DOT_EDGE}];",
            ]

    if graph.has_host:
        head = _html(graph.host) + (f"<BR/>{small.format(_html(name))}" if name else "")
        lines.append(f"  host [label=<{head}>, {_DOT_LOOKS['host']}];")

    modules = _by_module(part)
    boxed = len(modules) > 1

    for number, (module, tags) in enumerate(modules.items()):
        indent = "    " if boxed else "  "

        if boxed:
            lines.append(f"  subgraph cluster_{number} {{")
            lines.append(f"    graph [label={_quoted(module)}, {_DOT_LOOKS['module']}];")

        for tag in tags:
            look = _look(graph, tag)
            # A broken or Ripped box speaks in one color; others color each
            # member kind by what it does.
            plain = look in ("broken", "ripped")
            members = _members(tag, graph.broken.get(tag, set()))
            label = "<BR/>".join([
                    _html(tag.__name__),
                    *(
                        small.format(
                                (_html(kind) if plain
                                 else f'<FONT COLOR="{_DOT_MEMBER_COLORS[kind]}">{_html(kind)}</FONT>')
                                + f": {_html(names)}"
                                )
                        for kind, names in members
                        ),
                    ])
            looks = [_DOT_SHAPES[_kind(tag)], *([_DOT_LOOKS[look]] if look else [])]
            lines.append(f"{indent}{ids[tag]} [label=<{label}>, {', '.join(looks)}];")

        if boxed:
            lines.append("  }")

    drawn = set(part)

    for source, shape, label in graph.arrows:
        if shape in drawn:
            extra = f" [style=dashed, label={_quoted(f' {label} ')}]" if label else ""
            lines.append(f"  {ids[source]} -> {ids[shape]}{extra};")

    lines.append("}")

    return "\n".join(lines) + "\n"


_FORMATS = {
        "mermaid": (_mermaid, ".mmd"),
        "graphviz": (_graphviz, ".dot"),
        }
_IMAGES = ("svg", "png")


def Diagram(
        subject: object,
        *,
        limit: int = LIMIT,
        direction: str = "TD",
        format: str = "mermaid",
        ) -> dict[str, str]:
    """Charts of an Agent's Geometry or a Tag's Form, by name: Mermaid
    flowcharts, or Graphviz DOT with ``format="graphviz"``.

    One chart, named for the subject; or, with more than ``limit`` Tags,
    one for each module that declares them, named for the module. Inside a
    chart, the Tags of each module sit in a box named for it."""

    if limit < 1:
        raise ValueError("a diagram part holds at least one Tag")

    if format not in _FORMATS:
        raise ValueError(f"format is one of {', '.join(_FORMATS)}")

    draw = _FORMATS[format][0]
    graph = _Graph(subject)
    parts, names = graph.parts(limit)
    divided = len(parts) > 1

    return {
            names[index]: draw(graph, parts[index], names[index] if divided else None, direction)
            for index in range(len(parts))
            }


def _painter(
        format: str,
        image: str,
        ):
    """A function that draws one chart's text to ``image`` bytes."""

    if format == "graphviz":
        dot = shutil.which("dot")

        if dot is None:
            raise FileNotFoundError(
                    f"image={image!r} with format='graphviz' draws with Graphviz's"
                    " dot command; install Graphviz (https://graphviz.org/download/)."
                    " Without image=, Save writes the .dot files alone."
                    )

        def paint(text: str) -> bytes:
            done = subprocess.run(
                    [dot, f"-T{image}"],
                    input=text.encode("utf-8"),
                    capture_output=True,
                    check=False,
                    )

            if done.returncode != 0:
                raise RuntimeError(f"dot could not draw the chart: {done.stderr.decode().strip()}")

            return done.stdout

        return paint

    try:
        import mmdr
    except ImportError as error:
        raise ImportError(
                f"image={image!r} draws with merman through the optional mmdr"
                ' package: pip install "topkit[diagram]". Without image=, Save'
                " writes the Mermaid files alone."
                ) from error

    def paint(text: str) -> bytes:
        drawn = mmdr.render(text, backend="merman")
        return drawn.svg().encode("utf-8") if image == "svg" else drawn.png()

    return paint


def Save(
        subject: object,
        path: str | PathLike[str],
        *,
        limit: int = LIMIT,
        direction: str = "TD",
        format: str = "mermaid",
        image: str | None = None,
        ) -> tuple[Path, ...]:
    """Write ``Diagram(subject)`` as text files: Mermaid ``.mmd``, or
    Graphviz ``.dot`` with ``format="graphviz"``.

    One part is written to ``path`` with that suffix; several parts beside
    it, each named ``<stem>-<part name>``, with characters other than
    letters, digits, ``_`` and ``-`` made ``_``. ``image="svg"`` or
    ``image="png"`` also draws each part beside its text file: Mermaid with
    merman, through the optional ``mmdr`` package
    (``pip install "topkit[diagram]"``); Graphviz with its ``dot`` command.
    Returns the written paths."""

    if format not in _FORMATS:
        raise ValueError(f"format is one of {', '.join(_FORMATS)}")

    if image is not None and image not in _IMAGES:
        raise ValueError(f"image is one of {', '.join(_IMAGES)}, or None")

    paint = _painter(format, image) if image is not None else None
    diagrams = Diagram(
            subject,
            limit=limit,
            direction=direction,
            format=format,
            )
    suffix = _FORMATS[format][1]
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
        source = path.with_name(f"{stem}{suffix}")
        source.write_text(text, encoding="utf-8")
        written.append(source)

        if paint is not None:
            out = path.with_name(f"{stem}.{image}")
            out.write_bytes(paint(text))
            written.append(out)

    return tuple(written)
