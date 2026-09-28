#!/usr/bin/env python3
"""wikiwright helper: the mechanical half of writing a GitHub wiki.

Subcommands
  preflight OWNER/REPO [--enable] [--wait SEC] [--clone DIR]
      Is the wiki feature on, does the .wiki.git repository exist, and is it
      only GitHub's placeholder? Optionally switch the feature on, wait and
      re-check, and clone the wiki as a working copy.
  check DIR [--version X] [--repo OWNER/REPO]
      Lint a wiki working copy before pushing: page links resolve, anchors
      exist, no wikilinks, LF only, no <BS> placeholders left, sidebar and
      footer present, footer names the version and a date, fences balanced,
      no AI attribution.
  live OWNER/REPO DIR
      After the push: every page answers 200 (Home answers 301 to /wiki),
      and the sidebar and footer text render on the wiki root.
  unbs FILE...
      Replace every <BS> placeholder with a backslash (for pages written
      with a tool that decodes backslash escapes).

Standard library only, Python 3.9+. Exit 0 when clean, 1 on findings,
2 on usage or environment errors.
"""

import argparse
import html
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

VERSION = "0.1.0"
BS = "<BS>"
BACKSLASH = chr(92)
SPECIAL = ("_Sidebar.md", "_Footer.md", "_Header.md")
UA = "wikiwright/" + VERSION + " (+https://github.com/m4bwav/wikiwright)"

ATTRIBUTION = re.compile(
    r"co-authored-by:|generated (with|by) (claude|chatgpt|copilot|an? ai)|"
    r"written (with|by) (claude|chatgpt|copilot|an? ai)",
    re.IGNORECASE,
)
LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
DATE = re.compile(r"\b20[0-9]{2}-[01][0-9]-[0-3][0-9]\b")


def run(cmd, check=False):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise SystemExit("error: %s failed: %s" % (" ".join(cmd), p.stderr.strip()))
    return p


def wiki_url(repo):
    return "https://github.com/%s.wiki.git" % repo


def ls_remote(repo):
    p = run(["git", "ls-remote", wiki_url(repo)])
    heads = [line.split("\t") for line in p.stdout.splitlines() if "\t" in line]
    return p.returncode == 0 and bool(heads), heads, p.stderr.strip()


# ---------------------------------------------------------------- preflight

def cmd_preflight(a):
    p = run(["gh", "repo", "view", a.repo, "--json", "hasWikiEnabled,visibility,isArchived,defaultBranchRef"])
    if p.returncode != 0:
        print("error: gh repo view failed: " + p.stderr.strip())
        return 2
    import json
    info = json.loads(p.stdout)
    print("repo: %s  visibility: %s  archived: %s  wiki feature: %s" % (
        a.repo, info.get("visibility"), info.get("isArchived"), info.get("hasWikiEnabled")))
    if info.get("isArchived"):
        print("STATE: archived (a wiki cannot be edited on an archived repository; unarchive first)")
        return 1
    enabled_now = False
    if not info.get("hasWikiEnabled"):
        if not a.enable:
            print("STATE: feature-off (run again with --enable, or: gh repo edit %s --enable-wiki)" % a.repo)
            return 1
        e = run(["gh", "repo", "edit", a.repo, "--enable-wiki"])
        if e.returncode != 0:
            print("error: gh repo edit --enable-wiki failed: " + e.stderr.strip())
            print("       private repositories on a free plan cannot have a wiki")
            return 2
        print("wiki feature: switched on")
        enabled_now = True
    ok, heads, err = ls_remote(a.repo)
    waited = 0
    wait = a.wait if a.wait is not None else (60 if enabled_now else 0)
    while not ok and waited < wait:
        step = min(15, wait - waited)
        time.sleep(step)
        waited += step
        ok, heads, err = ls_remote(a.repo)
    if not ok:
        print("ls-remote: %s (after %ss)" % (err or "no refs", waited))
        print("STATE: no-wiki-repo")
        print("ACTION: the maintainer saves the first page in the web UI (no API exists):")
        print("        https://github.com/%s/wiki/_new  (any text; it is replaced by the push)" % a.repo)
        print("        then run this again. Survey, verify and write the pages meanwhile.")
        return 1
    for sha, ref in heads:
        print("ls-remote: %s %s" % (sha[:7], ref))
    # Only the wiki's default branch goes live (GitHub Docs): take the branch HEAD points at.
    head_sha = next((sha for sha, ref in heads if ref == "HEAD"), None)
    branches = [(sha, ref[11:]) for sha, ref in heads if ref.startswith("refs/heads/")]
    matching = [name for sha, name in branches if sha == head_sha]
    branch = "master" if "master" in matching or not branches else (matching or [branches[0][1]])[0]
    print("branch: %s (push here; only the default branch goes live)" % branch)
    if not a.clone:
        print("STATE: exists (branch %s; clone it with --clone DIR to see whether it is a placeholder)" % branch)
        return 0
    if os.path.exists(a.clone) and os.listdir(a.clone):
        print("clone: %s already exists; using it" % a.clone)
        run(["git", "-C", a.clone, "fetch", "-q", "origin"], check=True)
    else:
        run(["git", "clone", "-q", wiki_url(a.repo), a.clone], check=True)
        print("clone: %s" % a.clone)
    commits = run(["git", "-C", a.clone, "rev-list", "--count", "origin/" + branch], check=True).stdout.strip()
    files = [f for f in run(["git", "-C", a.clone, "ls-tree", "-r", "--name-only", "origin/" + branch], check=True).stdout.splitlines()]
    size = 0
    if files == ["Home.md"]:
        size = os.path.getsize(os.path.join(a.clone, "Home.md"))
    print("commits: %s  files: %d (%s)" % (commits, len(files), ", ".join(files[:12]) + (" ..." if len(files) > 12 else "")))
    if commits == "1" and files == ["Home.md"] and size < 200:
        print("STATE: placeholder (only GitHub's first page; the new pages may replace it, force-push allowed)")
    else:
        print("STATE: has-pages (existing content: read every page first; update, never overwrite)")
    return 0


# ---------------------------------------------------------------- check

def slug(heading):
    """GitHub's heading anchor: lower case, drop punctuation, spaces to hyphens."""
    text = re.sub(r"`([^`]*)`", r"\1", heading.strip())
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def page_text(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    return raw, raw.decode("utf-8", errors="replace")


def strip_code(text):
    """Blank out fenced blocks and inline code, keeping line numbers."""
    out, fence = [], None
    for line in text.split("\n"):
        m = re.match(r"^\s*(```+|~~~+)", line)
        if fence:
            out.append("")
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            continue
        if m:
            fence = m.group(1)
            out.append("")
            continue
        out.append(re.sub(r"`[^`]*`", "``", line))
    return out, fence


def headings(text):
    lines, _ = strip_code(text)
    found, seen = set(), {}
    for line in lines:
        m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m:
            s = slug(m.group(1))
            n = seen.get(s, 0)
            found.add(s if n == 0 else "%s-%d" % (s, n))
            seen[s] = n + 1
    return found


def is_title_case(h):
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]*", h)]
    if len(words) < 3:
        return False
    rest = [w for w in words[1:] if len(w) > 3]
    return len(rest) >= 2 and all(w[0].isupper() and not w.isupper() for w in rest)


def cmd_check(a):
    d = a.dir
    if not os.path.isdir(d):
        print("error: %s is not a directory" % d)
        return 2
    pages = sorted(f for f in os.listdir(d) if f.endswith(".md"))
    names = {f[:-3].lower(): f[:-3] for f in pages}
    errors, warnings = [], []

    def err(f, n, msg):
        errors.append("%s:%s: error: %s" % (f, n, msg))

    def warn(f, n, msg):
        warnings.append("%s:%s: warn: %s" % (f, n, msg))

    if "Home.md" not in pages:
        err("Home.md", 0, "missing (the wiki's front page)")
    for special in ("_Sidebar.md", "_Footer.md"):
        if special not in pages:
            err(special, 0, "missing")
    anchors = {f[:-3].lower(): headings(page_text(os.path.join(d, f))[1]) for f in pages}
    linked_from_sidebar = set()
    for f in pages:
        raw, text = page_text(os.path.join(d, f))
        if b"\r" in raw:
            err(f, 0, "%d carriage returns (wiki pages are LF only)" % raw.count(b"\r"))
        if raw.startswith(b"\xef\xbb\xbf"):
            err(f, 1, "starts with a byte order mark")
        lines, open_fence = strip_code(text)
        if open_fence:
            err(f, 0, "a code fence (%s) is never closed" % open_fence)
        for n, line in enumerate(text.split("\n"), 1):
            if BS in line:
                err(f, n, "<BS> placeholder left (run: wikiwright.py unbs %s)" % f)
            if ATTRIBUTION.search(line):
                err(f, n, "AI attribution: " + ATTRIBUTION.search(line).group(0))
        for n, line in enumerate(lines, 1):
            if "[[" in line and "]]" in line:
                err(f, n, "wikilink; use [Text](Page-Name)")
            m = re.match(r"^#{1,6}\s+(.*)$", line)
            if m and is_title_case(m.group(1)):
                warn(f, n, "heading looks like Title Case; use sentence case: " + m.group(1).strip())
            for text_, target in LINK.findall(line):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("//"):
                    continue
                if target.startswith("/"):
                    warn(f, n, "site-absolute link %s (breaks outside github.com)" % target)
                    continue
                page, _, anchor = target.partition("#")
                if not page:
                    if anchor and anchor.lower() not in anchors.get(f[:-3].lower(), set()):
                        err(f, n, "no heading for #%s on this page" % anchor)
                    continue
                if page.lower().endswith(".md"):
                    err(f, n, "link to %s: drop the .md (wiki links are page names)" % target)
                    page = page[:-3]
                key = page.lower()
                if key not in names:
                    err(f, n, "link to missing page %s" % page)
                    continue
                if names[key] != page:
                    warn(f, n, "link %s differs in case from the file %s.md" % (page, names[key]))
                if anchor and anchor.lower() not in anchors[key]:
                    err(f, n, "no heading for #%s on %s" % (anchor, names[key]))
                if f == "_Sidebar.md":
                    linked_from_sidebar.add(key)
    if "_Sidebar.md" in pages:
        for f in pages:
            key = f[:-3].lower()
            if f not in SPECIAL and key not in linked_from_sidebar:
                warn("_Sidebar.md", 0, "does not link %s" % f[:-3])
    if "_Footer.md" in pages:
        footer = page_text(os.path.join(d, "_Footer.md"))[1]
        if a.version and a.version not in footer:
            err("_Footer.md", 1, "does not name version %s" % a.version)
        if not DATE.search(footer):
            err("_Footer.md", 1, "names no date (YYYY-MM-DD)")
    if a.version:
        for f in ("Home.md",):
            if f in pages and a.version not in page_text(os.path.join(d, f))[1]:
                warn(f, 0, "does not mention version %s" % a.version)
    for line in errors + warnings:
        print(line)
    print("check: %d pages, %d errors, %d warnings" % (len([p for p in pages if p not in SPECIAL]), len(errors), len(warnings)))
    return 1 if errors else 0


# ---------------------------------------------------------------- live

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=30) as r:
            return r.status, r.headers.get("Location"), r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location"), ""


def plain(md):
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    text = re.sub(r"[`*_]", "", text)
    return " ".join(text.split())


def cmd_live(a):
    base = "https://github.com/%s/wiki" % a.repo
    pages = sorted(f[:-3] for f in os.listdir(a.dir) if f.endswith(".md") and f not in SPECIAL)
    bad = 0
    for p in pages:
        status, loc, _ = fetch("%s/%s" % (base, p))
        good = (status == 200) or (p == "Home" and status == 301 and (loc or "").rstrip("/").endswith("/wiki"))
        print("%s %s %s%s" % ("ok  " if good else "FAIL", status, p, (" -> " + loc) if loc else ""))
        bad += 0 if good else 1
    status, _, body = fetch(base)
    root = html.unescape(re.sub(r"<[^>]+>", " ", body))
    root = " ".join(root.split())
    print("%s %s wiki root" % ("ok  " if status == 200 else "FAIL", status))
    bad += 0 if status == 200 else 1
    for special, label in (("_Footer.md", "footer"), ("_Sidebar.md", "sidebar")):
        path = os.path.join(a.dir, special)
        if not os.path.exists(path):
            continue
        md = page_text(path)[1]
        if special == "_Footer.md":
            probes = [plain(md.strip().split("\n")[0])[:60]]
        else:
            probes = [t for t, _ in LINK.findall(md)][:40]
        missing = [t for t in probes if t and t not in root]
        print("%s %s renders (%d of %d probes found)%s" % (
            "ok  " if not missing else "FAIL", label, len(probes) - len(missing), len(probes),
            ("; missing: " + ", ".join(missing[:5])) if missing else ""))
        bad += 1 if missing else 0
    print("live: %d pages, %d failures" % (len(pages), bad))
    return 1 if bad else 0


# ---------------------------------------------------------------- unbs

def cmd_unbs(a):
    total = 0
    for path in a.files:
        with open(path, "rb") as fh:
            raw = fh.read()
        n = raw.count(BS.encode())
        if n:
            with open(path, "wb") as fh:
                fh.write(raw.replace(BS.encode(), BACKSLASH.encode()))
        print("%s: %d replaced" % (path, n))
        total += n
    print("unbs: %d placeholders replaced in %d files" % (total, len(a.files)))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wikiwright.py", description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=VERSION)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preflight", help="wiki feature, wiki repository, placeholder, clone")
    p.add_argument("repo", help="OWNER/REPO")
    p.add_argument("--enable", action="store_true", help="switch the wiki feature on when it is off")
    p.add_argument("--wait", type=int, help="seconds to keep re-checking ls-remote (default 60 after --enable)")
    p.add_argument("--clone", help="clone the wiki repository here (a sibling <clone>.wiki)")
    p.set_defaults(fn=cmd_preflight)
    c = sub.add_parser("check", help="lint a wiki working copy")
    c.add_argument("dir")
    c.add_argument("--version", dest="version", help="the package version the footer must name")
    c.set_defaults(fn=cmd_check)
    lv = sub.add_parser("live", help="check the published pages")
    lv.add_argument("repo", help="OWNER/REPO")
    lv.add_argument("dir", help="the working copy (for the page list, sidebar and footer)")
    lv.set_defaults(fn=cmd_live)
    u = sub.add_parser("unbs", help="replace <BS> placeholders with backslashes")
    u.add_argument("files", nargs="+")
    u.set_defaults(fn=cmd_unbs)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
