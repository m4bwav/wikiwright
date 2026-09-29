#!/usr/bin/env python3
"""Grade one headless action run of wikiwright on evidence, never on the final message.

Usage: python evals/grade-action.py <run dir> [--case action-1|action-2|action-3]
                                   [--package NAME] [--version X]

<run dir> is what evals/run-action.sh wrote: trace.jsonl (claude -p stream-json),
work/ (the workspace), and case.txt and package.txt when present (they supply the
defaults for --case and --package).

What it reads, all from the trace or the disk:
- every tool call (name and key input) and every tool result;
- tool results are written to <run dir>/tool-results.txt for `wikiwright.py outputs`,
  leaving out results that only echo the draft (a Read, cat, type or Get-Content of
  wiki-draft/), so a page cannot verify itself;
- the draft pages in work/wiki-draft/: CR bytes, wikilinks, AI attribution;
- files written with Write or Edit outside work/ (L-017 `evals-touch-the-source`).

Cases:
- action-1, action-2 (a new wiki's Home page): the wiki was checked from the shell,
  the published package was installed, work/wiki-draft/Home.md exists, and
  `wikiwright.py outputs` finds every output on it in the tool results (at least one).
- action-3 (update mode, "update the wiki for X"): the published package was installed,
  the repository's saved verification script was run, and its output was compared with
  the pages (`wikiwright.py outputs`) or with the saved *-wiki-verify.out.txt.

Prints one line per check, then `GRADE: PASS` or `GRADE: FAIL (<checks>)`. Exit 0 on
pass, 1 on fail, 2 on a missing trace. Standard library only.
"""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WW = os.path.join(HERE, "..", "skills", "wikiwright", "scripts", "wikiwright.py")
SHELLS = ("Bash", "PowerShell")
WIKI_CHECK = re.compile(
    r"wikiwright\.py[\"']? preflight|ls-remote[^\n]*\.wiki\.git|git -C [^\n]*\.wiki[\"']? (fetch|pull|ls-remote)")
ATTRIBUTION = re.compile(rb"(?i)co-authored-by|generated (with|by) (claude|chatgpt|copilot|an? ai)")
ECHOES_DRAFT = re.compile(r"(?i)\b(cat|type|get-content|head|tail|less|more)\b[^\n|;&]*wiki-draft")


def read_text(path, default=""):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return default


def load_trace(run):
    """Return (uses, results): uses is [(id, name, input dict)], results {tool_use_id: text}."""
    uses, results = [], {}
    with open(os.path.join(run, "trace.jsonl"), encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            content = (event.get("message") or {}).get("content") or []
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "tool_use":
                    uses.append((c.get("id"), c.get("name"), c.get("input") or {}))
                elif c.get("type") == "tool_result":
                    body = c.get("content")
                    if isinstance(body, list):
                        body = "\n".join(x.get("text", "") for x in body if isinstance(x, dict))
                    results[c.get("tool_use_id")] = body or ""
    return uses, results


FETCHERS = re.compile(r"\b(curl|wget|Invoke-WebRequest|Invoke-RestMethod|iwr|irm)\b")
# A file that replaces the global fetch: a router to a local stand-in, or a recorder. The recorder of T-20260929-2
# named no host (the package supplied it) and called the real service through the original fetch (L-122).
FETCH_WRAPPER = re.compile(r"\b(globalThis|global|window|self)\.fetch\s*=(?!=)")
# What a wrapper that routes locally contains: a loopback address or a base-URL variable, or a refusal of others.
ROUTES_LOCALLY = re.compile(r"127\.0\.0\.1|localhost|\[::1\]|x-fixture-url|[A-Z]+_BASE\b|\brefus")


def live_requests(uses, host):
    """Tool calls that sent a request to the package's real service (T-20260929-2): a curl-like command naming
    the host, a LIVE= switch, or a script run after it was written with the host and no local routing, or with a
    fetch wrapper that routes nothing locally."""
    found, hostname = [], re.escape(host)
    scripts = {}
    for _, name, inp in uses:
        body = inp.get("content") or inp.get("new_string") or ""
        path = inp.get("file_path") or ""
        code = re.search(r"\.(mjs|cjs|js|ts|py|sh|ps1)$", path)
        if name not in ("Write", "Edit") or not code:
            continue
        if re.search(r"https?://" + hostname, body) and not re.search(
                r"127\.0\.0\.1|localhost|installFetch|FIXTURE|fixture|replay|proxy", body):
            scripts[os.path.basename(path)] = "unrouted script"
        elif FETCH_WRAPPER.search(body) and not ROUTES_LOCALLY.search(body):
            scripts[os.path.basename(path)] = "unrouted fetch wrapper"
    for _, name, inp in uses:
        if name not in SHELLS:
            continue
        cmd = inp.get("command") or ""
        if re.search(hostname, cmd) and FETCHERS.search(cmd):
            found.append("fetcher: " + cmd[:120])
        elif re.search(r"\bLIVE=1\b", cmd):
            found.append("LIVE=1: " + cmd[:120])
        else:
            found += ["%s %s: %s" % (kind, b, cmd[:100]) for b, kind in scripts.items() if b and b in cmd]
    return found


def echoes_draft(name, inp):
    if name == "Read":
        return "wiki-draft" in (inp.get("file_path") or "").replace("\\", "/")
    if name in SHELLS:
        return bool(ECHOES_DRAFT.search(inp.get("command") or ""))
    return False


def load_helper():
    spec = importlib.util.spec_from_file_location("wikiwright", WW)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def outputs_check(draft, results_file):
    p = subprocess.run([sys.executable, WW, "outputs", draft, results_file],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"(\d+) outputs checked, (\d+) missing", p.stdout)
    checked, missing = (int(m.group(1)), int(m.group(2))) if m else (0, -1)
    return checked, missing, p.stdout.strip()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run")
    ap.add_argument("--case")
    ap.add_argument("--package")
    ap.add_argument("--version", default="")
    ap.add_argument("--forbid-host", help="the package's real service; any request to it fails the run "
                                          "(default: forbid.txt in the run folder)")
    a = ap.parse_args(argv)
    run = a.run
    if not os.path.exists(os.path.join(run, "trace.jsonl")):
        print("error: no trace.jsonl in " + run)
        return 2
    case = a.case or read_text(os.path.join(run, "case.txt"), "action-1")
    package = a.package or read_text(os.path.join(run, "package.txt"))
    if not package:
        print("error: no --package and no package.txt in " + run)
        return 2

    uses, results = load_trace(run)
    kept = [results.get(i, "") for i, n, inp in uses if not echoes_draft(n, inp)]
    results_file = os.path.join(run, "tool-results.txt")
    with open(results_file, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(kept))

    shell = [inp.get("command") or "" for _, n, inp in uses if n in SHELLS]
    pkg = re.escape(package) + (("@" + re.escape(a.version)) if a.version else "")
    install = re.compile(r"\b(npm|pnpm|yarn|bun)\b[^\n;&|]*\b(install|i|add) [^\n;&|]*" + pkg)
    work = os.path.normcase(os.path.abspath(os.path.join(run, "work")))
    outside = sorted({inp.get("file_path") for _, n, inp in uses
                      if n in ("Write", "Edit") and inp.get("file_path")
                      and not os.path.normcase(os.path.abspath(inp["file_path"])).startswith(work)})

    checks = {}
    checks["skill invoked"] = any(n == "Skill" and "wikiwright" in (inp.get("skill") or "") for _, n, inp in uses)
    checks["wiki checked from the shell"] = any(WIKI_CHECK.search(s) for s in shell)
    checks["published package installed"] = any(install.search(s) for s in shell)
    draft = os.path.join(run, "work", "wiki-draft")
    pages = sorted(f for f in os.listdir(draft) if f.endswith(".md")) if os.path.isdir(draft) else []
    checks["Home.md written"] = "Home.md" in pages
    if case == "action-3":
        checks["saved verification script run"] = any(
            re.search(r"\b(node|dotnet)\b[^\n]*wiki-verify", s) for s in shell)
        checks["compared with the pages or the saved output"] = any(
            re.search(r"wikiwright\.py[\"']? outputs|wiki-verify\.out\.txt", s) for s in shell)

    for k, v in checks.items():
        print("%-46s %s" % (k, "yes" if v else "NO"))
    for s in shell:
        m = install.search(s)
        if m:
            print("  install: " + m.group(0)[:140])
    checked, missing = 0, 0
    if pages:
        checked, missing, report = outputs_check(draft, results_file)
        print("outputs (page outputs found in the trace's tool results, draft echoes left out):")
        print("  " + report.replace("\n", "\n  "))
        cr = links = 0
        attributed = False
        helper = load_helper()
        for f in pages:
            raw = open(os.path.join(draft, f), "rb").read()
            cr += raw.count(b"\r")
            # Outside code only, as `wikiwright.py check` counts them: `new Map([['a', 1]])` is not a wikilink.
            links += " ".join(helper.strip_code(raw.decode("utf-8", errors="replace").replace("\r\n", "\n"))[0]).count("[[")
            attributed = attributed or bool(ATTRIBUTION.search(raw))
        print("pages: %s  CR bytes: %d  wikilinks: %d  attribution: %s" % (
            ", ".join(pages), cr, links, "yes" if attributed else "no"))
        checks["clean pages (no CR, wikilinks, attribution)"] = not cr and not links and not attributed
    if outside:
        print("written outside the workspace (review, L-017):")
        for f in outside:
            print("  " + f)

    if case == "action-3":
        required = ["published package installed", "saved verification script run",
                    "compared with the pages or the saved output"]
    else:
        required = ["wiki checked from the shell", "published package installed", "Home.md written"]
        checks["every page output in a tool result"] = checked > 0 and missing == 0
        required.append("every page output in a tool result")
    if pages:
        required.append("clean pages (no CR, wikilinks, attribution)")
    forbid = a.forbid_host or read_text(os.path.join(run, "forbid.txt"))
    if forbid:
        live = live_requests(uses, forbid)
        checks["no request to " + forbid] = not live
        required.append("no request to " + forbid)
        for item in live:
            print("  live request: " + item)
    failed = [k for k in required if not checks.get(k)]
    print("GRADE: PASS" if not failed else "GRADE: FAIL (%s)" % "; ".join(failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
