"""One execution's Post query: neutral recursive edges and local reuse.

Only a completed verdict is reusable. Reaching the exact Agent/check
already running contributes True without deciding that unfinished check.
Results and their identity guards live only until the outer query ends.
"""

from __future__ import annotations

from asyncio import current_task
from contextvars import ContextVar
from threading import get_ident
from typing import Any
from typing import Callable

try:
    # CPython 3.12–3.14 provide a non-raising probe. Keep the public
    # fallback for other interpreters: synchronous checks need no Task.
    from asyncio.events import _get_running_loop as _running_loop
except ImportError:
    from asyncio import get_running_loop

    def _running_loop() -> Any:
        try:
            return get_running_loop()
        except RuntimeError:
            return None

from .arrest import _arrest_of
from .arrest import _may_act
from .arrest import _safehouse


def _execution() -> tuple[int, Any]:
    loop = _running_loop()
    task = current_task(loop) if loop is not None else None
    return get_ident(), task


class _Session:
    __slots__ = ("active", "owner", "running", "results", "sensitive")

    def __init__(session) -> None:
        session.active = True
        session.owner = _execution()
        session.running: set[tuple[int, int]] = set()
        # Strong identity guards prevent id reuse during this one query.
        # An outcome is (Agent, check, custody, verdict, exception).
        session.results: dict[tuple[int, int], tuple[Any, ...]] = {}
        session.sensitive = False

    def Close(session) -> None:
        session.active = False
        session.running.clear()
        session.results.clear()
        session.owner = None   # a saved Context must not retain its Task


_post_query: ContextVar[_Session | None] = ContextVar(
        "topkit_post_query", default=None,
        )


def _session() -> _Session | None:
    session = _post_query.get()
    owner = None if session is None else session.owner
    if session is not None and session.active and owner is not None:
        thread, task = _execution()
        if owner[0] == thread and owner[1] is task:
            return session
    return None


class _Post_Evaluation:
    __slots__ = ("session", "token", "owns")

    def __enter__(scope) -> _Session:
        scope.session = _session()
        scope.owns = scope.session is None
        if scope.owns:
            scope.session = _Session()
            scope.token = _post_query.set(scope.session)
        return scope.session

    def __exit__(scope, error_type: Any, error: Any, traceback: Any) -> None:
        if scope.owns:
            scope.session.Close()
            _post_query.reset(scope.token)


def _post_evaluation() -> _Post_Evaluation:
    """Share first completed verdicts through one complete Post question."""

    return _Post_Evaluation()


def _taint_post_memo() -> None:
    """A Secret permission probe makes later reads require fresh checks.

    The marker is shared with copied contexts: a protected read there must
    not leave a reusable verdict in the originating query after its door
    closes. Exact recursive edges still contribute the neutral True.
    """

    session = _post_query.get()
    if session is not None and session.active:
        session.sensitive = True
        session.results.clear()


def _post_verdict(
        agent: object,
        check: Callable[..., Any],
        inputs: dict[str, Any],
        evaluate: Callable[[], bool],
        *,
        check_custody: bool = True,
        _query: _Session | None = None,
        ) -> bool:
    """Evaluate one Post, or reuse its first result in this query.

    Authorization is checked before lookup and before return, including a
    cached result. Custody changes invalidate the result. Python writes
    inside a check are the author's responsibility; this is no world snapshot.
    """

    # Complete query entry points may pass the owner they just validated.
    # User-origin nested reads still validate their thread and Task here.
    session = _query if _query is not None else _session()
    if session is None:
        with _post_evaluation() as session:
            return _verdict_in_session(
                    session, agent, check, inputs, evaluate, check_custody,
                    )

    return _verdict_in_session(session, agent, check, inputs, evaluate, check_custody)


def _verdict_in_session(
        session: _Session,
        agent: object,
        check: Callable[..., Any],
        inputs: dict[str, Any],
        evaluate: Callable[[], bool],
        check_custody: bool,
        ) -> bool:

    if check_custody and _safehouse and not _may_act(agent):
        return False

    key = id(agent), id(check)
    if key in session.running:
        return not (check_custody and _safehouse and not _may_act(agent))

    custody = _arrest_of(agent) if _safehouse else None
    saved = None if inputs or session.sensitive else session.results.get(key)
    if (saved is not None and saved[0] is agent and saved[1] is check
            and saved[2] is custody):
        verdict, failure = saved[3], saved[4]
    else:
        session.running.add(key)
        verdict, failure = False, None
        try:
            verdict = evaluate()
        except Exception as error:
            failure = error
        finally:
            session.running.remove(key)

        if (not inputs and not session.sensitive
                and (_arrest_of(agent) if _safehouse else None) is custody):
            session.results[key] = agent, check, custody, verdict, failure

    if check_custody and _safehouse and not _may_act(agent):
        return False
    if failure is not None:
        raise failure
    return verdict
