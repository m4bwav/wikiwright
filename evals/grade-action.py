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
  the published package was installed (npm, or NuGet: `dotnet add package`, a
  `#:package` file-based app, an F# `#r "nuget:"` script or a scratch project's
  PackageReference, then run or restored), work/wiki-draft/Home.md exists, and
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
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WW = os.path.join(HERE, "..", "skills", "wikiwright", "scripts", "wikiwright.py")
SHELLS = ("Bash", "PowerShell")
# Preflight run directly or through a variable holding the helper's path ($WW="...wikiwright.py"; python $WW
# preflight OWNER/REPO, T-20260929-3); `preflight --help` alone is not a check.
WIKI_CHECK = re.compile(
    r"wikiwright\.py[\"']? preflight|wikiwright\.py[^\n]*\bpreflight [\w.-]+/[\w.-]+"
    r"|ls-remote[^\n]*\.wiki\.git|git -C [^\n]*\.wiki[\"']? (fetch|pull|ls-remote)")
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


DOTNET_SCRIPT = re.compile(r"\.(cs|csx|fs|fsx)$")
# A .NET program that names the host sends a request only through a client call; an offline check of the same URL
# (HasImageExtension("https://example.com/a.png")) does not.
DOTNET_REQUEST = re.compile(r"\bHttpClient\b|\bWebRequest\b|\bGetAsync\b|\bSendAsync\b|UrlAsync\b")


def live_requests(uses, host):
    """Tool calls that sent a request to the package's real service (T-20260929-2): a curl-like command naming
    the host, a LIVE= switch, or a script run after it was written with the host and no local routing, or with a
    fetch wrapper that routes nothing locally. A .NET program (.cs, .fsx) counts only when it also makes a
    client call; its local routing is a handler, a proxy or a loopback address."""
    found, hostname = [], re.escape(host)
    scripts = {}
    for _, name, inp in uses:
        body = inp.get("content") or inp.get("new_string") or ""
        path = inp.get("file_path") or ""
        code = re.search(r"\.(mjs|cjs|js|ts|py|sh|ps1)$", path)
        dotnet = DOTNET_SCRIPT.search(path)
        if name not in ("Write", "Edit") or not (code or dotnet):
            continue
        if dotnet and not DOTNET_REQUEST.search(body):
            continue
        if re.search(r"https?://" + hostname, body) and not re.search(
                r"127\.0\.0\.1|localhost|installFetch|FIXTURE|fixture|replay|proxy|Proxy|Handler\b", body):
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


def installs(uses, package, version=""):
    """Evidence that the published package came from its registry: an npm-family install, `dotnet add package`,
    or a program that pins it (`#:package ID@X` in a file-based app, `#r "nuget: ID"` in an F# script,
    `<PackageReference Include="ID">` in a scratch project) followed by a dotnet run, fsi, build or restore.
    NuGet ids are matched without regard to case. Returns the matching texts, shortest first."""
    pkg = re.escape(package)
    ver = re.escape(version) if version else ""
    npm = re.compile(r"\b(npm|pnpm|yarn|bun)\b[^\n;&|]*\b(install|i|add) [^\n;&|]*" + pkg + (("@" + ver) if ver else ""))
    after = (r"[^\n]*?" + ver) if ver else ""
    add = re.compile(r"(?i)\bdotnet\s+add\b[^\n;&|]*\bpackage\s+" + pkg + r"\b" + after)
    pins = re.compile(r"(?i)#:package\s+" + pkg + r"\b" + (("@" + ver) if ver else "")
                      + r"|#r\s+\"nuget:\s*" + pkg + r"\b" + ((r"\s*,\s*" + ver) if ver else "")
                      + r"|<PackageReference\s+Include=\"" + pkg + "\"" + after)
    runs = re.compile(r"(?i)\bdotnet\s+(run|fsi|build|restore|test)\b")
    found, pinned = [], []
    for _, name, inp in uses:
        if name in ("Write", "Edit"):
            body = inp.get("content") or inp.get("new_string") or ""
            m = pins.search(body)
            if m:
                pinned.append(m.group(0))
            continue
        if name not in SHELLS:
            continue
        cmd = inp.get("command") or ""
        for pattern in (npm, add):
            m = pattern.search(cmd)
            if m:
                found.append(m.group(0))
        m = pins.search(cmd)  # a program written from the shell (a here-string, echo) and run in the same call
        if m:
            pinned.append(m.group(0))
        if pinned and runs.search(cmd):
            found.append("%s, then %s" % (pinned[-1], runs.search(cmd).group(0)))
    return sorted(set(found), key=len)


def saved_outputs(run, uses):
    """Verification outputs a program in the run saved to disk (`*.out.txt` in the workspace or the run's session
    scratchpad) and the Write and Edit tools never touched: a run that sends its script's output to a file and checks
    the page with `wikiwright.py outputs` prints none of it into the trace (T-20260929-3)."""
    work = os.path.abspath(os.path.join(run, "work"))
    typed = {os.path.basename(inp.get("file_path") or "").lower() for _, n, inp in uses if n in ("Write", "Edit")}
    scratch = os.path.join(tempfile.gettempdir(), "claude", re.sub(r"[^A-Za-z0-9]", "-", work))
    found = []
    for root in (work, scratch):
        for folder, _, files in os.walk(root):
            found += [os.path.join(folder, f) for f in files if f.endswith(".out.txt") and f.lower() not in typed]
    return sorted(found)


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


URL_HOST = re.compile(r"https?://([A-Za-z0-9.-]+)")
LOOPBACK = {"127.0.0.1", "localhost"}
SCRATCH = re.compile(r"[A-Za-z]:[\\/][^\s\"']*?[\\/]scratchpad[\\/]|/[^\s\"']*?/scratchpad/")


def digest(run, uses, show_all=False):
    """One line per tool call worth reading when reviewing a trace (L-122): installs, requests, node runs, fetch
    wrappers, git, writes outside the workspace. A 300 KB trace becomes a few KB."""
    work = os.path.normcase(os.path.abspath(os.path.join(run, "work")))
    counts, lines = {}, []
    for n, (_, name, inp) in enumerate(uses, 1):
        counts[name] = counts.get(name, 0) + 1
        flags, text = [], ""
        if name in SHELLS:
            text = inp.get("command") or ""
            hosts = sorted({h for h in URL_HOST.findall(text) if h not in LOOPBACK})
            if FETCHERS.search(text):
                flags.append("fetcher")
            if hosts:
                flags.append("url:" + ",".join(hosts))
            if re.search(r"\b(npm|pnpm|yarn|bun)\b[^\n;&|]*\b(install|i|add|view|pack)\b", text):
                flags.append("npm")
            if re.search(r"(?i)\bdotnet\s+(add\b[^\n;&|]*\bpackage|restore)\b|#:package|#r\s+\"nuget:", text):
                flags.append("nuget")
            if re.search(r"\b(node|npx|deno)\b|\bdotnet\s+(run|fsi|test|exec)\b|\bdotnet\s+\S+\.dll\b", text):
                flags.append("run")
            if re.search(r"\bgit\b|\bgh\b", text):
                flags.append("git")
            if re.search(r"wikiwright\.py", text):
                flags.append("ww")
        elif name in ("Write", "Edit"):
            text = inp.get("file_path") or ""
            body = inp.get("content") or inp.get("new_string") or ""
            if not os.path.normcase(os.path.abspath(text)).startswith(work):
                flags.append("outside")
            if FETCH_WRAPPER.search(body):
                flags.append("fetch-wrapper" + ("" if ROUTES_LOCALLY.search(body) else " UNROUTED"))
            if re.search(r"(?i)#:package\s|#r\s+\"nuget:|<PackageReference\s", body):
                flags.append("nuget")
        elif name == "Skill":
            text, flags = inp.get("skill") or "", ["skill"]
        if flags or show_all:
            one = SCRATCH.sub("<scratch>/", " ".join(text.split()))
            lines.append("%3d %-10s [%s] %s" % (n, name, " ".join(flags), one[:150]))
    print("\n".join(lines))
    print("tools: " + ", ".join("%s %d" % kv for kv in sorted(counts.items())))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run")
    ap.add_argument("--case")
    ap.add_argument("--package")
    ap.add_argument("--version", default="")
    ap.add_argument("--forbid-host", help="the package's real hosts, separated by commas; any request to one "
                                          "fails the run (default: forbid.txt in the run folder)")
    ap.add_argument("--digest", action="store_true", help="print one line per tool call worth reading, not a grade")
    ap.add_argument("--all", action="store_true", help="with --digest, every tool call")
    a = ap.parse_args(argv)
    run = a.run
    if not os.path.exists(os.path.join(run, "trace.jsonl")):
        print("error: no trace.jsonl in " + run)
        return 2
    if a.digest:
        digest(run, load_trace(run)[0], a.all)
        return 0
    case = a.case or read_text(os.path.join(run, "case.txt"), "action-1")
    package = a.package or read_text(os.path.join(run, "package.txt"))
    if not package:
        print("error: no --package and no package.txt in " + run)
        return 2

    uses, results = load_trace(run)
    kept = [results.get(i, "") for i, n, inp in uses if not echoes_draft(n, inp)]
    saved = saved_outputs(run, uses)
    for path in saved:
        with open(path, encoding="utf-8", errors="replace") as fh:
            kept.append(fh.read())
    results_file = os.path.join(run, "tool-results.txt")
    with open(results_file, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(kept))

    shell = [inp.get("command") or "" for _, n, inp in uses if n in SHELLS]
    installed = installs(uses, package, a.version)
    work = os.path.normcase(os.path.abspath(os.path.join(run, "work")))
    outside = sorted({inp.get("file_path") for _, n, inp in uses
                      if n in ("Write", "Edit") and inp.get("file_path")
                      and not os.path.normcase(os.path.abspath(inp["file_path"])).startswith(work)})

    checks = {}
    checks["skill invoked"] = any(n == "Skill" and "wikiwright" in (inp.get("skill") or "") for _, n, inp in uses)
    checks["wiki checked from the shell"] = any(WIKI_CHECK.search(s) for s in shell)
    checks["published package installed"] = bool(installed)
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
    for s in installed[:3]:
        print("  install: " + s[:140])
    checked, missing = 0, 0
    if pages:
        checked, missing, report = outputs_check(draft, results_file)
        print("outputs (page outputs found in the trace's tool results, draft echoes left out, and %d saved "
              "output file(s) no Write or Edit touched):" % len(saved))
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
    for host in [h.strip() for h in forbid.replace("\n", ",").split(",") if h.strip()]:
        live = live_requests(uses, host)
        checks["no request to " + host] = not live
        required.append("no request to " + host)
        for item in live:
            print("  live request: " + item)
    failed = [k for k in required if not checks.get(k)]
    print("GRADE: PASS" if not failed else "GRADE: FAIL (%s)" % "; ".join(failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
