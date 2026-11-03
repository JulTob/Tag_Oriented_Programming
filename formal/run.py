#!/usr/bin/env python3
"""Run every TLA+ model under formal/ and compare with its `\\* expect:` line.

Usage (from the repo root):
    python3 formal/run.py [AREA[/MODULE] ...] [--quick] [--list] [--only-current]
                          [--keep] [--timeout S] [--no-colour] [--root DIR]

Discovers formal/*/*.cfg, runs each with TLC (pinned tla2tools.jar v1.7.4)
in a fresh temp dir, and compares the outcome with the cfg's `\\* expect:` line:
    \\* expect: ok | \\* expect: violates <Name> | \\* expect: deadlock

Exit status: 0 iff every cfg matched its expectation, 1 if any FAILED,
2 on environment errors (no Java, no jar, offline download).
Stdlib only, Python 3.12+.
"""

import argparse
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

JAR_VERSION = "1.7.4"
JAR_URL = (
    "https://github.com/tlaplus/tlaplus/releases/download/"
    "v1.7.4/tla2tools.jar"
)
JAR_SHA256 = (
    "936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88"
)
JAR_CACHE = os.path.join(
    os.path.expanduser("~"), ".cache", "topkit-formal",
    "tla2tools-%s.jar" % JAR_VERSION,
)
DEFAULT_TIMEOUT = 300.0

USE_COLOUR = False


def paint(text, code):
    if USE_COLOUR:
        return "\033[%sm%s\033[0m" % (code, text)
    return text


def die_env(msg):
    print("run.py: environment error: %s" % msg, file=sys.stderr)
    sys.exit(2)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_java():
    java = os.environ.get("JAVA", "java")
    try:
        proc = subprocess.run(
            [java, "-version"], capture_output=True, text=True, timeout=30
        )
    except (FileNotFoundError, OSError):
        die_env(
            "no Java executable at %r (set $JAVA or put java >= 17 on PATH)"
            % java
        )
    out = (proc.stderr or "") + (proc.stdout or "")
    match = re.search(r'version\s+"(\d+)(?:\.(\d+))?', out)
    if not match:
        die_env("cannot parse `java -version` output: %r" % out.strip()[:200])
    if match.group(1) == "1":
        major = int(match.group(2))
    else:
        major = int(match.group(1))
    if major < 17:
        die_env(
            "Java major version %d < 17 (need 17+ for tla2tools %s); "
            "set $JAVA to a newer java" % (major, JAR_VERSION)
        )
    return java


def find_jar():
    env = os.environ.get("TLA2TOOLS")
    if env:
        if not os.path.isfile(env):
            die_env("$TLA2TOOLS=%r does not exist" % env)
        return env
    if os.path.isfile(JAR_CACHE):
        if sha256_of(JAR_CACHE) == JAR_SHA256:
            return JAR_CACHE
        print(
            "run.py: cached jar failed checksum, re-downloading: %s" % JAR_CACHE,
            file=sys.stderr,
        )
    os.makedirs(os.path.dirname(JAR_CACHE), exist_ok=True)
    tmp = "%s.tmp-%d" % (JAR_CACHE, os.getpid())
    try:
        with urllib.request.urlopen(JAR_URL, timeout=60) as resp:
            with open(tmp, "wb") as f:
                shutil.copyfileobj(resp, f)
    except Exception as exc:  # offline, DNS, HTTP errors, ...
        try:
            os.unlink(tmp)
        except OSError:
            pass
        die_env(
            "cannot download tla2tools.jar v%s from %s (%s: %s); "
            "set $TLA2TOOLS to a local copy" % (JAR_VERSION, JAR_URL,
                                                type(exc).__name__, exc)
        )
    if sha256_of(tmp) != JAR_SHA256:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        die_env("downloaded jar failed sha256 verification; refusing to use it")
    os.replace(tmp, JAR_CACHE)  # atomic publish
    return JAR_CACHE


def discover(root):
    """Return sorted [(area, cfg_path)] for root/*/*.cfg."""
    found = []
    for area in sorted(os.listdir(root)):
        adir = os.path.join(root, area)
        if area.startswith(".") or not os.path.isdir(adir):
            continue
        for fn in sorted(os.listdir(adir)):
            if fn.endswith(".cfg"):
                full = os.path.join(adir, fn)
                if os.path.isfile(full):
                    found.append((area, full))
    return found


def parse_expect(cfg_text):
    """Return 'ok' | 'violates <Name>' | 'deadlock' | None.

    None covers both a missing `\\* expect:` line and an unparseable value;
    the caller reports which via expect_note().
    """
    match = re.search(r"\\\*\s*expect:\s*([^\n]+)", cfg_text)
    if not match:
        return None
    value = match.group(1).strip()
    if re.fullmatch(r"ok", value):
        return "ok"
    if re.fullmatch(r"deadlock", value):
        return "deadlock"
    viol = re.fullmatch(r"violates\s+(\S+)", value)
    if viol:
        return "violates " + viol.group(1).rstrip(".,;:") + ""
    return None


def expect_note(cfg_text):
    match = re.search(r"\\\*\s*expect:\s*([^\n]+)", cfg_text)
    if not match:
        return "add `\\* expect:` (ok | violates <Name>) to the cfg"
    return "bad `\\* expect:` value %r (want ok | violates <Name> | deadlock)" % (
        match.group(1).strip()
    )


def resolve_tla(adir, cfg_path):
    """Map Demo.cfg / Demo.quick.cfg / Demo_break.cfg -> (Demo.tla, Demo).

    Longest existing <Prefix>.tla where Prefix is the cfg stem up to the
    first '.', trimmed at the last '_' until a .tla exists.
    """
    stem = os.path.basename(cfg_path)[:-len(".cfg")]
    prefix = stem.split(".")[0]
    while True:
        if os.path.isfile(os.path.join(adir, prefix + ".tla")):
            return prefix + ".tla", prefix
        if "_" in prefix:
            prefix = prefix.rsplit("_", 1)[0]
            continue
        return None, stem.split(".")[0]


def cfg_kind(cfg_path):
    fn = os.path.basename(cfg_path)
    if fn.endswith(".quick.cfg"):
        return "quick"
    first = fn[:-len(".cfg")].split(".")[0]
    if "_" in first:
        return "variant"
    return "base"


def apply_quick(all_cfgs, adirs, quick):
    """Without --quick drop *.quick.cfg; with --quick a <Mod>.quick.cfg
    replaces <Mod>.cfg when both exist. Variants always run."""
    if not quick:
        return [c for c in all_cfgs if cfg_kind(c[1]) != "quick"]
    by_key = {}
    for area, cfg in all_cfgs:
        tla_file, mod = resolve_tla(adirs[area], cfg)
        key = (area, mod, cfg_kind(cfg) in ("base", "quick"))
        by_key.setdefault(key, []).append((area, cfg))
    keep_ids = set()
    for (area, mod, is_baseish), group in by_key.items():
        if not is_baseish:
            for item in group:
                keep_ids.add(item[1])
            continue
        quicks = [c for _, c in group if c[1].endswith(".quick.cfg")]
        if quicks:
            for item in group:
                if item[1] in quicks:
                    keep_ids.add(item[1])
        else:
            for item in group:
                keep_ids.add(item[1])
    return [c for c in all_cfgs if c[1] in keep_ids]


def selected(area, mod, stem, sels):
    if not sels:
        return True
    for sel in sels:
        parts = sel.split("/")
        if len(parts) == 1 and parts[0] == area:
            return True
        if (
            len(parts) == 2
            and parts[0] == area
            and parts[1] in (mod, stem, stem.split(".")[0])
        ):
            return True
    return False


# ---------------- TLC output parsing ----------------

INVARIANT_RE = re.compile(r"Error:\s+Invariant\s+(\S+)\s+is violated\.")
ACTION_RE = re.compile(r"Error:\s+Action property\s+(\S+)\s+is violated\.")
TEMPORAL_RE = re.compile(r"Temporal properties were violated")
DEADLOCK_RE = re.compile(r"Deadlock reached")
NOERROR_RE = re.compile(
    r"Model checking completed\. No error has been found\."
)
STATES_RE = re.compile(
    r"([\d,]+)\s+states generated,\s+([\d,]+)\s+distinct states found"
)
DEPTH_RE = re.compile(r"depth of the complete state graph search is\s+(\d+)")
STATE_HDR_RE = re.compile(r"^State (\d+):\s*<(.*)>\s*$")
ERROR_LINE_RE = re.compile(r"(?i)error|exception|parse|failed|violat|deadlock")
PROPERTY_RE = re.compile(r"(?m)^\s*PROPERTY\s+([A-Za-z_][A-Za-z0-9_']*)")


def clean_name(raw):
    return raw.strip().rstrip(".,;:") + ""


def determine_got(proc_text, exit_code, cfg_text, expected):
    """Return (got, error_lines) where got is one of ok | violates <N> |
    deadlock | error | timeout (timeout never returned here).

    TLC stops at the FIRST violated invariant and names exactly one; got
    is that single name, matched exactly against `violates X` (no
    among-set semantics: each _break.cfg lists only its target invariant).
    """
    invariants = [clean_name(n) for n in INVARIANT_RE.findall(proc_text)]
    actions = [clean_name(n) for n in ACTION_RE.findall(proc_text)]
    reported = invariants + actions
    if reported:
        return "violates " + reported[0], []
    if TEMPORAL_RE.search(proc_text):
        props = PROPERTY_RE.findall(cfg_text or "")
        if expected and expected.startswith("violates "):
            want = expected.split(" ", 1)[1]
            if want in props:
                return "violates " + want, []
        if len(props) == 1:
            return "violates " + props[0], []
        return "violates Temporal", []
    if DEADLOCK_RE.search(proc_text):
        return "deadlock", []
    if NOERROR_RE.search(proc_text) and exit_code == 0:
        return "ok", []
    lines = [
        ln for ln in proc_text.splitlines() if ERROR_LINE_RE.search(ln)
    ]
    if not lines:
        lines = proc_text.strip().splitlines()[-15:]
    return "error", lines[:15]


def parse_trace(proc_text):
    """Parse the first error-trace state sequence.

    Returns [(action, [(var, value)])] including the initial state first;
    callers diff steps against states[0]. Multi-line values: continuation
    lines (not starting with `/\\ ` or `var =`) are joined into the
    current value.
    """
    headers = []  # (lineno, num, inner)
    lines = proc_text.splitlines()
    for i, ln in enumerate(lines):
        m = STATE_HDR_RE.match(ln.strip())
        if m:
            headers.append((i, int(m.group(1)), m.group(2)))
    if not headers:
        return []
    # First contiguous run starting at State 1 (else the first run).
    run = []
    collecting = False
    want = 1
    for h in headers:
        _, num, _ = h
        if not collecting:
            if num == 1:
                collecting = True
                run.append(h)
                want = 2
        else:
            if num == want:
                run.append(h)
                want += 1
            else:
                break
    if not collecting:
        run = headers[:1]
        # still parse bindings for context but mark all as one state
    states = []
    for idx, (lineno, _num, inner) in enumerate(run):
        end = run[idx + 1][0] if idx + 1 < len(run) else len(lines)
        bindings = []
        cur_var, cur_val = None, ""
        def flush():
            if cur_var is not None:
                bindings.append((cur_var, " ".join(cur_val.split())))
        for ln in lines[lineno + 1:end]:
            s = ln.strip()
            if not s:
                continue
            # End of the trace: TLC footer / progress lines.
            if re.match(r"^(Error:|Finished|Running|Parsing|Progress|TLC2? |\d[\d,]* states generated|The depth|Computed |Model checking )", s):
                break
            if s.startswith("/\\ "):
                flush()
                body = s[3:]
                if "=" in body:
                    var, _, val = body.partition("=")
                    cur_var, cur_val = var.strip(), val.strip()
                else:
                    cur_var, cur_val = body.strip(), ""
            elif re.match(r"^[A-Za-z_][A-Za-z0-9_']*\s*=", s):
                # Default (non -tool) TLC format: `var = value`.
                flush()
                var, _, val = s.partition("=")
                cur_var, cur_val = var.strip(), val.strip()
            elif cur_var is not None and not STATE_HDR_RE.match(s):
                # Multi-line value: join continuation lines.
                cur_val += " " + s
            else:
                break
        flush()
        action = re.sub(r"\s+line\s+\d+.*$", "", inner).strip()
        states.append((action, bindings))
    if not states:
        return []
    return states  # states[0] is the initial state; steps are states[1:]
...


def load_step_words(area, adir):
    path = os.path.join(adir, "words.py")
    if not os.path.isfile(path):
        return {}
    try:
        spec = importlib.util.spec_from_file_location(
            "topkit_words_%s" % re.sub(r"\W", "_", area), path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        words = getattr(module, "STEP_WORDS", {})
        if isinstance(words, dict):
            return {str(k): str(v) for k, v in words.items()}
    except Exception as exc:
        print("  (warning: ignoring %s/words.py: %s)" % (area, exc))
    return {}


def short(text, limit=160):
    text = " ".join(str(text).split())
    if len(text) > limit:
        return text[: limit - 1] + "\u2026"
    return text


def print_trace(states, step_words, indent="    "):
    if not states:
        return
    prev = {var: val for var, val in states[0][1]}
    steps = states[1:]
    if not steps:
        print("%s(no steps past the initial state)" % indent)
        return
    for num, (action, bindings) in enumerate(steps, 1):
        cur = {var: val for var, val in bindings}
        changed = [
            (var, prev.get(var), val)
            for var, val in bindings
            if prev.get(var, "\0") != val
        ]
        sentence = None
        if action in step_words:
            try:
                sentence = step_words[action].format(
                    action=action,
                    **{v: cur.get(v, "") for v in cur},
                )
            except Exception:
                sentence = None
        if sentence is not None:
            print("%s%d. %s" % (indent, num, sentence))
        else:
            if changed:
                detail = ", ".join(
                    "%s = %s" % (var, short(val))
                    if old is None or len(" ".join((old or "").split())) > 80
                    else "%s: %s -> %s" % (var, short(old), short(val))
                    for var, old, val in changed
                )
            else:
                detail = "(no variables changed)"
            print("%s%d. %s: %s" % (indent, num, action, detail))
        prev = cur


# ---------------- running ----------------

def run_one(java, jar, area, adir, cfg_path, tla_file, mod,
            timeout, keep, step_words):
    cfg_base = os.path.basename(cfg_path)
    tmp = tempfile.mkdtemp(prefix="topkit-%s-%s-" % (area, mod))
    with open(cfg_path) as f:
        cfg_text = f.read()
    expected = parse_expect(cfg_text)
    # Stage files: the .tla, the cfg, and sibling helper modules.
    shutil.copy(os.path.join(adir, tla_file), os.path.join(tmp, tla_file))
    shutil.copy(cfg_path, os.path.join(tmp, cfg_base))
    for fn in sorted(os.listdir(adir)):
        if fn.endswith(".tla") and fn != tla_file:
            shutil.copy(os.path.join(adir, fn), os.path.join(tmp, fn))
    cmd = [
        java, "-XX:+UseParallelGC", "-cp", jar, "tlc2.TLC",
        "-workers", "1", "-fp", "0", "-lncheck", "final",
        "-metadir", os.path.join(tmp, "states"),
        "-config", cfg_base, tla_file,
    ]
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, cwd=tmp, capture_output=True, text=True, timeout=timeout
        )
        elapsed = time.monotonic() - start
        combined = (proc.stdout or "") + (proc.stderr or "")
        got, error_lines = determine_got(
            combined, proc.returncode, cfg_text, expected
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - start
        combined = ""
        if exc.stdout:
            combined += exc.stdout.decode(errors="replace") \
                if isinstance(exc.stdout, bytes) else exc.stdout
        if exc.stderr:
            combined += exc.stderr.decode(errors="replace") \
                if isinstance(exc.stderr, bytes) else exc.stderr
        got, error_lines = "timeout", []
    states, depth = "?", "?"
    m = None
    for m in STATES_RE.finditer(combined):
        pass
    if m:
        states = m.group(2).replace(",", "")
    d = None
    for d in DEPTH_RE.finditer(combined):
        pass
    if d:
        depth = d.group(1)

    if expected is None:
        matched = False
        note = expect_note(cfg_text)
    else:
        matched = (got == expected)
        note = ""
    status = paint("OK", "32;1") if matched else paint("FAILED", "31;1")
    line = "%s  %s/%s  expected %s  got %s  states=%s depth=%s %.1fs" % (
        status, area, cfg_base, expected or "(none)", got,
        states, depth, elapsed,
    )
    if note:
        line += "  << %s >>" % note
    print(line)

    if got.startswith("violates "):
        name = got.split(" ", 1)[1]
        steps = parse_trace(combined)
        if matched:
            print("  finding %s/%s: violates %s (as expected)"
                  % (area, cfg_base, name))
            if steps:
                print_trace(steps, step_words)
            else:
                print("    (no counterexample trace parsed)")
        else:
            print(paint(
                "  COUNTEREXAMPLE (UNEXPECTED) %s/%s: expected %s got %s"
                % (area, cfg_base, expected or "(none)", got), "31;1"))
            if steps:
                print_trace(steps, step_words)
            else:
                print("    (no counterexample trace parsed)")
    elif got == "error":
        print("  --- TLC errors (%s/%s) ---" % (area, cfg_base))
        for ln in error_lines:
            print("  | " + ln.rstrip())
    elif got == "timeout":
        print("  TIMEOUT after %.0fs (%s/%s)" % (timeout, area, cfg_base))

    if keep:
        print("  kept %s" % tmp)
    else:
        shutil.rmtree(tmp, ignore_errors=True)
    return matched


def main(argv=None):
    global USE_COLOUR
    here = os.path.dirname(os.path.abspath(__file__))
    default_root = here  # run.py lives inside formal/
    ap = argparse.ArgumentParser(
        description="Run every TLA+ model under formal/ and check "
                    "each `\\* expect:` line."
    )
    ap.add_argument("select", nargs="*",
                    help="optional AREA or AREA/MODULE filters")
    ap.add_argument("--quick", action="store_true",
                    help="use <Module>.quick.cfg instead of <Module>.cfg "
                         "when it exists")
    ap.add_argument("--list", action="store_true",
                    help="print discovered cfgs and expectations, do not run")
    ap.add_argument("--only-current", action="store_true",
                    help="skip broken-variant (_<break>) and _fixed cfgs")
    ap.add_argument("--keep", action="store_true",
                    help="keep per-cfg temp dirs and print their paths")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                    help="seconds per cfg (default %.0f)" % DEFAULT_TIMEOUT)
    ap.add_argument("--no-colour", action="store_true",
                    help="disable ANSI colours")
    ap.add_argument("--root", default=default_root,
                    help="directory to scan instead of formal/")
    args = ap.parse_args(argv)

    USE_COLOUR = (
        not args.no_colour
        and os.environ.get("NO_COLOR") is None
        and sys.stdout.isatty()
    )

    root = args.root
    if not os.path.isdir(root):
        die_env("root directory %r does not exist" % root)
    adirs = {
        area: os.path.join(root, area)
        for area in os.listdir(root)
        if os.path.isdir(os.path.join(root, area))
        and not area.startswith(".")
    }
    all_cfgs = discover(root)
    all_cfgs = apply_quick(all_cfgs, adirs, args.quick)
    if args.only_current:
        all_cfgs = [c for c in all_cfgs if cfg_kind(c[1]) != "variant"]

    rows = []
    for area, cfg in all_cfgs:
        adir = adirs[area]
        tla_file, mod = resolve_tla(adir, cfg)
        stem = os.path.basename(cfg)[:-len(".cfg")]
        if not selected(area, mod, stem, args.select):
            continue
        rows.append((area, cfg, tla_file, mod))

    if not rows:
        if args.select:
            print("run.py: no cfgs match selection %r" % (args.select,),
                  file=sys.stderr)
            sys.exit(2)
        print("0 models run, 0 matched expectation, 0 FAILED")
        return 0

    if args.list:
        for area, cfg, tla_file, mod in rows:
            with open(cfg) as f:
                cfg_text = f.read()
            expected = parse_expect(cfg_text)
            print("%s/%s  expect %s  tla %s  %s" % (
                area, os.path.basename(cfg),
                expected or "MISSING (%s)" % expect_note(cfg_text),
                tla_file or "UNRESOLVED (no <Prefix>.tla found)",
                cfg_kind(cfg),
            ))
        return 0

    for sel in args.select:
        if "/" in sel:
            want_area, _ = sel.split("/", 1)
            if want_area not in adirs:
                print("run.py: unknown area %r" % want_area, file=sys.stderr)
                sys.exit(2)
        elif sel not in adirs:
            print("run.py: unknown area %r" % sel, file=sys.stderr)
            sys.exit(2)

    java = find_java()
    jar = find_jar()

    words_cache = {}
    matched = 0
    for area, cfg, tla_file, mod in rows:
        if tla_file is None:
            cfg_base = os.path.basename(cfg)
            with open(cfg) as f:
                cfg_text = f.read()
            expected = parse_expect(cfg_text)
            print("%s  %s/%s  expected %s  got error  states=? depth=? 0.0s"
                  % (paint("FAILED", "31;1"), area, cfg_base,
                     expected or "(none)"))
            print("  --- config error: no <Prefix>.tla found for %s/%s ---"
                  % (area, cfg_base))
            continue
        if area not in words_cache:
            words_cache[area] = load_step_words(area, adirs[area])
        ok = run_one(java, jar, area, adirs[area], cfg, tla_file, mod,
                     args.timeout, args.keep, words_cache[area])
        matched += bool(ok)

    total = len(rows)
    failed = total - matched
    print("%d models run, %d matched expectation, %d FAILED"
          % (total, matched, failed))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
