#!/usr/bin/env python3
"""wikiwright helper: the mechanical half of writing a GitHub wiki.

Subcommands
  preflight OWNER/REPO|URL|CLONE [--enable] [--wait SEC] [--clone DIR]
      Is the wiki feature on, does the .wiki.git repository exist, and is it
      only GitHub's placeholder? Optionally switch the feature on, wait and
      re-check, and clone the wiki as a working copy. Gitea and Forgejo
      (--seed creates the wiki through the API with WIKIWRIGHT_TOKEN), GitLab
      and Azure DevOps are told apart by name or API (--kind names one).
  check DIR [--version X] [--partial] [--host KIND]
      Lint a wiki working copy before pushing: page links resolve, anchors
      exist, no wikilinks, LF only, no <BS> placeholders left, sidebar and
      footer present (not with --partial), footer names the version and a
      date, fences balanced, no AI attribution.
  outputs DIR VERIFY_OUTPUT... [--address URL]
      Every block a page presents as output, and every //=> value, must
      appear in the verification script's saved output (the fixture's
      http://127.0.0.1:<port> read as https://example.com).
  live OWNER/REPO|URL DIR [--kind KIND]
      After the push: every page answers 200 (on GitHub Home answers 301 to
      /wiki), and the sidebar and footer text render on the wiki root; on
      Gitea, Forgejo and GitLab the page API must list every page too.
  unbs FILE...
      Replace every <BS> placeholder with a backslash (for pages written
      with a tool that decodes backslash escapes).
  diffout OLD NEW [--skip REGEX]... [--mask REGEX]... [--context N] [--save FILE]
      Compare two runs of a verification script section by section (its
      "## label" lines), with line endings, trailing spaces and local ports
      (127.0.0.1:<digits>, localhost:<digits>) normalised; --skip leaves out
      sections whose label matches, --mask blanks text that differs by
      machine. Prints each changed, added and removed section; --save writes
      the normalised NEW output (for saving over the old one).
  cachecheck [--source DIR] [--cache DIR]
      The installed plugin cache against the source: every tracked file
      under skills/ and .claude-plugin/ compared by SHA-256 (a stale cache
      runs old text, L-012). The cache defaults to wikiwright's installPath
      in ~/.claude/plugins/installed_plugins.json.
  releasecheck X.Y.Z [--root DIR]
      Before tagging: plugin.json, VERSION, SKILL.md's metadata.version and
      evergreen.json name X.Y.Z; CHANGELOG has an entry naming it; TESTS has
      a run the last tag's TESTS did not.

Standard library only, Python 3.9+. Exit 0 when clean, 1 on findings,
2 on usage or environment errors.
"""

import argparse
import difflib
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

VERSION = "0.5.0"
BS = "<BS>"
BACKSLASH = chr(92)
SPECIAL = ("_Sidebar.md", "_Footer.md", "_Header.md", "_sidebar.md")
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

HOSTS = (
    (re.compile(r"(^|\.)gitlab\.", re.I), "GitLab"),
    (re.compile(r"(^|\.)(codeberg\.org|gitea\.|forgejo\.)", re.I), "Gitea or Forgejo"),
    (re.compile(r"(^|\.)(dev\.azure\.com|visualstudio\.com)$", re.I), "Azure DevOps"),
)


def parse_remote(arg):
    """(scheme, host, path) from OWNER/REPO, a remote URL (http, https, ssh, scp-like), or a local clone's
    origin; host keeps its port (127.0.0.1:3107). (None, None, None) when it is none of those."""
    if os.path.isdir(arg):
        p = run(["git", "-C", arg, "remote", "get-url", "origin"])
        if p.returncode != 0:
            return None, None, None
        arg = p.stdout.strip()
    m = re.match(r"^(https?)://(?:[^@/]+@)?([^/]+)/(.+?)(?:\.git)?/?$", arg, re.I)
    if m:
        return m.group(1).lower(), m.group(2).lower(), m.group(3)
    m = re.match(r"^(?:[a-z+]+://)?(?:[^@/]+@)?([^/:]+\.[^/:]+)[:/](.+?)(?:\.git)?/?$", arg, re.I)
    if m:
        host, path = m.group(1).lower(), m.group(2)
        if host == "ssh.dev.azure.com" and path.startswith("v3/"):
            # ssh.dev.azure.com:v3/ORG/PROJECT/REPO is dev.azure.com/ORG/PROJECT/_git/REPO
            parts = path[3:].split("/")
            host, path = "dev.azure.com", "/".join(parts[:2] + ["_git"] + parts[2:])
        return "https", host, path
    if re.match(r"^[\w.-]+/[\w.-]+$", arg):
        return "https", "github.com", arg
    return None, None, None


def resolve_repo(arg):
    """(host, OWNER/REPO) from OWNER/REPO, a remote URL, or a local clone's origin."""
    return parse_remote(arg)[1:]


def host_name(host):
    for pattern, name in HOSTS:
        if pattern.search(host):
            return name
    return "an unknown host"


KINDS = ("github", "gitea", "forgejo", "gitlab", "azure")


def api_get(url, token=None, token_header="Authorization", method="GET", body=None):
    """(status, parsed JSON or None, headers) without following redirects."""
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if token:
        headers[token_header] = ("token " + token) if token_header == "Authorization" else token
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=30) as r:
            text = r.read().decode("utf-8", errors="replace")
            status, hdrs = r.status, r.headers
    except urllib.error.HTTPError as e:
        text, status, hdrs = e.read().decode("utf-8", errors="replace"), e.code, e.headers
    except (urllib.error.URLError, OSError) as e:
        return 0, str(e), {}
    try:
        return status, json.loads(text), hdrs
    except ValueError:
        return status, None, hdrs


def detect_kind(scheme, host):
    """The wiki host kind by name, or by asking its API (anonymous GETs only). Measured 2026-09-29: Gitea
    1.27.3 answers /api/v1/version and 404 to /api/forgejo/v1/version; Forgejo 16.0.5 answers both;
    GitLab answers /api/v4/version with 401 anonymously."""
    name = host.split(":")[0]
    if name in ("github.com", "www.github.com"):
        return "github"
    if name == "codeberg.org" or name.startswith("forgejo."):
        return "forgejo"
    if name.startswith("gitea."):
        return "gitea"
    if name == "gitlab.com" or name.startswith("gitlab."):
        return "gitlab"
    if name == "dev.azure.com" or name.endswith(".visualstudio.com"):
        return "azure"
    base = "%s://%s" % (scheme, host)
    status, data, _ = api_get(base + "/api/forgejo/v1/version")
    if status == 200 and isinstance(data, dict) and data.get("version"):
        return "forgejo"
    status, data, _ = api_get(base + "/api/v1/version")
    if status == 200 and isinstance(data, dict) and data.get("version"):
        return "forgejo" if "+gitea" in str(data["version"]) else "gitea"
    status, _, _ = api_get(base + "/api/v4/version")
    if status == 401:
        return "gitlab"
    return None


def ls_remote_symref(url):
    """(ok, branch HEAD points at or None, [(sha, ref)], error text) for any git URL, never prompting."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    p = subprocess.run(["git", "-c", "credential.helper=", "ls-remote", "--symref", url], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env)
    branch, heads = None, []
    for line in p.stdout.splitlines():
        m = re.match(r"^ref: refs/heads/(\S+)\s+HEAD$", line)
        if m:
            branch = m.group(1)
        elif "\t" in line:
            heads.append(tuple(line.split("\t", 1)))
    return p.returncode == 0, branch, heads, p.stderr.strip()


def first_error(err):
    """git's own error line (Forgejo's ends with a hint line after it)."""
    lines = [line for line in (err or "").splitlines() if line.strip()]
    return next((line for line in lines if line.startswith(("fatal:", "error:"))), lines[0] if lines else "no answer")


def clone_state(url, clone, branch):
    """Clone (or fetch) the wiki and print placeholder or has-pages, as for GitHub."""
    if os.path.exists(clone) and os.listdir(clone):
        print("clone: %s already exists; using it" % clone)
        run(["git", "-C", clone, "fetch", "-q", "origin"], check=True)
    else:
        run(["git", "clone", "-q", url, clone], check=True)
        print("clone: %s" % clone)
    commits = run(["git", "-C", clone, "rev-list", "--count", "origin/" + branch], check=True).stdout.strip()
    files = run(["git", "-C", clone, "ls-tree", "-r", "--name-only", "origin/" + branch], check=True).stdout.splitlines()
    print("commits: %s  files: %d (%s)" % (commits, len(files), ", ".join(files[:12]) + (" ..." if len(files) > 12 else "")))
    if commits == "1" and len(files) == 1 and files[0].lower() in ("home.md", "home.markdown"):
        print("STATE: placeholder (one first page; write the pages in this clone, commit and push to %s)" % branch)
    else:
        print("STATE: has-pages (existing content: read every page first; update, never overwrite)")
    return 0


def cmd_preflight(a):
    scheme, host, repo = parse_remote(a.repo)
    if host is None:
        print("error: %s is not OWNER/REPO, a remote URL or a clone with an origin" % a.repo)
        return 2
    kind = a.kind or detect_kind(scheme, host)
    if kind != "github":
        print("repo: %s on %s (%s)" % (repo, host, kind or "unknown"))
        if kind in ("gitea", "forgejo"):
            return preflight_gitea(a, scheme, host, repo, kind)
        if kind == "gitlab":
            return preflight_gitlab(a, scheme, host, repo)
        if kind == "azure":
            return preflight_azure(a, host, repo)
        print("STATE: other-host (%s, not GitHub, Gitea, Forgejo, GitLab or Azure DevOps by name or API)."
              % host_name(host))
        print("       references/hosts.md lists what each host needs; pass --kind to name it.")
        return 2
    a.repo = repo
    p = run(["gh", "repo", "view", a.repo, "--json", "hasWikiEnabled,visibility,isArchived,defaultBranchRef"])
    if p.returncode != 0:
        print("error: gh repo view failed: " + p.stderr.strip())
        return 2
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
    started = time.monotonic()
    ok, heads, err = ls_remote(a.repo)
    wait = a.wait if a.wait is not None else (60 if enabled_now else 0)
    while not ok and time.monotonic() - started < wait:
        print("ls-remote: missing at %ds" % (time.monotonic() - started))
        time.sleep(min(5, max(0, wait - (time.monotonic() - started))))
        ok, heads, err = ls_remote(a.repo)
    waited = int(time.monotonic() - started)
    if ok and enabled_now:
        print("ls-remote: found %ds after enabling" % waited)
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
        print("STATE: placeholder (only GitHub's first page; write the pages in this clone, commit and push: no force needed)")
    else:
        print("STATE: has-pages (existing content: read every page first; update, never overwrite)")
    return 0


TOKEN_ENV = "WIKIWRIGHT_TOKEN"


def preflight_gitea(a, scheme, host, repo, kind):
    """Gitea and Forgejo, as measured on Gitea 1.27.3 and Forgejo 16.0.5 (2026-09-29): the wiki repository
    does not exist before a first page, a push cannot create it, one POST .../wiki/new with a token does,
    and new wikis are on main (older Codeberg wikis on master)."""
    base, token = "%s://%s" % (scheme, host), os.environ.get(TOKEN_ENV)
    api = "%s/api/v1/repos/%s" % (base, repo)
    status, info, _ = api_get(api, token)
    if status != 200 or not isinstance(info, dict):
        print("error: GET %s answered %s%s" % (api, status, "" if token else
                                                 " (a private repository needs %s)" % TOKEN_ENV))
        return 2
    print("visibility: %s  archived: %s  wiki feature: %s%s" % (
        "private" if info.get("private") else "public", info.get("archived"), info.get("has_wiki"),
        ("  has_wiki_contents: %s" % info["has_wiki_contents"]) if "has_wiki_contents" in info else ""))
    if info.get("archived"):
        print("STATE: archived (unarchive first)")
        return 1
    if not info.get("has_wiki"):
        if not (a.enable and token):
            print("STATE: feature-off (run again with --enable and %s set: PATCH has_wiki)" % TOKEN_ENV)
            return 1
        status, _, _ = api_get(api, token, method="PATCH", body={"has_wiki": True})
        print("wiki feature: switched on (PATCH answered %s)" % status)
    url = "%s/%s.wiki.git" % (base, repo)
    ok, branch, heads, err = ls_remote_symref(url)
    if not ok and a.seed:
        if not token:
            print("error: --seed needs %s (a token that may write the repository)" % TOKEN_ENV)
            return 2
        import base64
        text = base64.b64encode(b"This page is replaced by the first push.\n").decode()
        status, _, _ = api_get(api + "/wiki/new", token, method="POST",
                               body={"title": "Home", "content_base64": text, "message": "Create the wiki"})
        print("seed: POST %s/wiki/new answered %s" % (api, status))
        ok, branch, heads, err = ls_remote_symref(url)
    if not ok:
        print("ls-remote: %s" % first_error(err))
        print("STATE: no-wiki-repo (a push cannot create it on %s; measured 2026-09-29)" % kind)
        print("ACTION: create the first page: run again with --seed and %s set (POST %s/wiki/new), or" % (TOKEN_ENV, api))
        print("        save one in the web UI: %s/%s/wiki/?action=_new" % (base, repo))
        return 1
    branch = branch or info.get("wiki_branch") or "main"
    print("clone URL: %s\nbranch: %s (push here; a push to another branch succeeds and shows nothing)" % (url, branch))
    if not a.clone:
        print("STATE: exists (branch %s; clone it with --clone DIR to see whether it is a placeholder)" % branch)
        return 0
    return clone_state(url, a.clone, branch)


def preflight_gitlab(a, scheme, host, repo):
    """GitLab, measured on gitlab.com anonymously and a local GitLab CE 19.4.1 (2026-09-29): a push to a
    never-used wiki creates it; an enabled empty wiki answers ls-remote with no refs; anonymous project JSON
    has no wiki fields, so the wiki API's status is the anonymous signal."""
    base = "%s://%s" % (scheme, host)
    token = os.environ.get(TOKEN_ENV)
    project = "%s/api/v4/projects/%s" % (base, urllib.request.quote(repo, safe=""))
    status, pages, _ = api_get(project + "/wikis", token, token_header="PRIVATE-TOKEN")
    print("wiki API: %s%s" % (status, (" (%d pages)" % len(pages)) if isinstance(pages, list) else ""))
    url = "%s/%s.wiki.git" % (base, repo)
    ok, branch, heads, err = ls_remote_symref(url)
    if not ok:
        print("ls-remote: %s" % first_error(err))
        print("STATE: not-readable (the wiki is off, members-only or private; with a token, check wiki_access_level)")
        return 1
    if not heads:
        print("clone URL: %s" % url)
        print("STATE: empty-wiki (no pages yet; a push creates it: git init -b main, add the pages, push main)")
        return 0
    branch = branch or "main"
    print("clone URL: %s\nbranch: %s (older gitlab.com wikis are on master, new ones on main)" % (url, branch))
    if not a.clone:
        print("STATE: exists (branch %s)" % branch)
        return 0
    return clone_state(url, a.clone, branch)


def preflight_azure(a, host, repo):
    """Azure DevOps, read anonymously on public projects (2026-09-29): _apis/wiki/wikis lists the wikis
    (count 0 when there is none), each with its branch in versions; a private or missing project answers
    302 to sign-in. Creating a wiki needs an account and was not verified."""
    parts = repo.split("/")
    if host.endswith(".visualstudio.com"):
        parts = [host.split(".")[0]] + parts
    if len(parts) < 2:
        print("error: expected dev.azure.com/ORG/PROJECT[/_git/REPO]")
        return 2
    org, project = parts[0], parts[1]
    api = "https://dev.azure.com/%s/%s/_apis/wiki/wikis?api-version=7.1" % (org, project)
    status, data, _ = api_get(api)
    if status in (302, 401, 203) or status == 0:
        print("STATE: not-readable (%s: not public, or not found; they look the same without an account)" % status)
        return 1
    wikis = (data or {}).get("value") or []
    if not wikis:
        print("STATE: no-wiki (a project administrator creates it: the web UI, az devops wiki create, or REST;")
        print("       needs an account, unverified here)")
        return 1
    for w in wikis:
        versions = ",".join(v.get("version", "?") for v in (w.get("versions") or []))
        print("wiki: %s  type: %s  branch: %s  mappedPath: %s" % (w.get("name"), w.get("type"), versions, w.get("mappedPath")))
    wiki = next((w for w in wikis if w.get("type") == "projectWiki"), wikis[0])
    url = "https://dev.azure.com/%s/%s/_git/%s" % (org, project, wiki.get("name"))
    ok, branch, heads, err = ls_remote_symref(url)
    branch = branch or ((wiki.get("versions") or [{}])[0].get("version")) or "wikiMain"
    print("clone URL: %s\nbranch: %s (read it: wikiMaster and wikiMain both occur)" % (url, branch))
    if not ok:
        print("ls-remote: %s" % first_error(err))
        return 1
    if not a.clone:
        print("STATE: exists (branch %s; pages need a .order entry per folder)" % branch)
        return 0
    return clone_state(url, a.clone, branch)


# ---------------------------------------------------------------- check

def slug(heading, kind="github"):
    """GitHub's heading anchor: lower case, drop punctuation, spaces to hyphens. Forgejo 16.0.5 then
    collapses runs of hyphens (`usage-basic-more` where GitHub and Gitea give `usage-basic--more`)."""
    text = re.sub(r"`([^`]*)`", r"\1", heading.strip())
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.lower()
    text = re.sub(r"[^\w\- ]", "", text)
    text = text.replace(" ", "-")
    return re.sub(r"-{2,}", "-", text) if kind == "forgejo" else text


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


def headings(text, kind="github"):
    # strip_code only to skip fenced blocks: a heading keeps its inline code for the slug, as
    # GitHub's does ("Deno answers `false` for every URL" is #deno-answers-false-for-every-url).
    lines, _ = strip_code(text)
    found, seen = set(), {}
    for stripped, line in zip(lines, text.split(chr(10))):
        m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line) if stripped.strip() else None
        if m:
            s = slug(m.group(1), kind)
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
    kind = a.host
    sidebar = "_sidebar.md" if kind == "gitlab" else "_Sidebar.md"
    pages = sorted(f for f in os.listdir(d) if f.endswith(".md"))
    names = {f[:-3].lower(): f[:-3] for f in pages}
    errors, warnings = [], []

    def err(f, n, msg):
        errors.append("%s:%s: error: %s" % (f, n, msg))

    def warn(f, n, msg):
        warnings.append("%s:%s: warn: %s" % (f, n, msg))

    if "Home.md" not in pages:
        err("Home.md", 0, "missing (the wiki's front page)")
    # Navigation files per host (hosts.md): GitLab reads _sidebar.md and renders no footer (a footer is
    # unverified there); Azure DevOps has neither and orders pages with .order.
    required = {"gitlab": ("_sidebar.md",), "azure": ()}.get(kind, ("_Sidebar.md", "_Footer.md"))
    for special in required:
        if special not in pages and not a.partial:
            err(special, 0, "missing (a draft of a few pages: --partial)")
    if kind == "gitlab" and "_Sidebar.md" in pages:
        err("_Sidebar.md", 0, "GitLab reads _sidebar.md (lower case) and ignores this file")
    if kind in ("gitlab", "azure") and "_Footer.md" in pages:
        warn("_Footer.md", 0, "%s shows no footer; put the version line on Home" % kind)
    if kind == "azure" and not os.path.exists(os.path.join(d, ".order")):
        warn(".order", 0, "missing: Azure DevOps orders pages by .order (one page name per line, no .md)")
    for f in os.listdir(d):
        full = os.path.join(d, f)
        if kind in ("gitea", "forgejo") and f.endswith(".md") and " " in f:
            err(f, 0, "a space in the file name: %s lists the page but cannot open it (measured)" % kind)
        if kind in ("gitea", "forgejo") and os.path.isdir(full) and not f.startswith("."):
            if any(n.endswith(".md") for n in os.listdir(full)):
                err(f, 0, "pages in a folder: %s does not list them (keep the wiki flat)" % kind)
    anchors = {f[:-3].lower(): headings(page_text(os.path.join(d, f))[1], kind) for f in pages}
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
                if kind in ("gitea", "forgejo", "gitlab"):
                    warn(f, n, "wikilink: %s resolves it, but [Text](Page-Name) works on every host" % kind)
                else:
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
                if f == sidebar:
                    linked_from_sidebar.add(key)
    if sidebar in pages:
        for f in pages:
            key = f[:-3].lower()
            if f not in SPECIAL and key not in linked_from_sidebar:
                warn(sidebar, 0, "does not link %s" % f[:-3])
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


def wiki_pages(d):
    return sorted(f[:-3] for f in os.listdir(d) if f.endswith(".md") and f not in SPECIAL)


def render_probes(a, root, sidebar_name="_Sidebar.md"):
    """(failures, lines) for the sidebar and footer text on a rendered page."""
    bad, lines = 0, []
    for special, label in (("_Footer.md", "footer"), (sidebar_name, "sidebar")):
        path = os.path.join(a.dir, special)
        if not os.path.exists(path):
            continue
        md = page_text(path)[1]
        probes = [plain(md.strip().split("\n")[0])[:60]] if label == "footer" else [t for t, _ in LINK.findall(md)][:40]
        # Whitespace ignored: tag boundaries put spaces where the markdown has none ("see Home .").
        flat = "".join(root.split())
        missing = [t for t in probes if t and "".join(t.split()) not in flat]
        lines.append("%s %s renders (%d of %d probes found)%s" % (
            "ok  " if not missing else "FAIL", label, len(probes) - len(missing), len(probes),
            ("; missing: " + ", ".join(missing[:5])) if missing else ""))
        bad += 1 if missing else 0
    return bad, lines


def html_text(body):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", body)).split())


def live_gitea(a, scheme, host, repo, kind):
    """Gitea and Forgejo (measured 2026-09-29): a page answers 200, a missing one 303 to ?action=_pages,
    and every wiki URL answers 200 before a first page exists, so the page API is checked first."""
    base, token = "%s://%s" % (scheme, host), os.environ.get(TOKEN_ENV)
    status, listed, _ = api_get("%s/api/v1/repos/%s/wiki/pages?limit=50" % (base, repo), token)
    titles = {str(p.get("sub_url") or p.get("title")) for p in listed} if isinstance(listed, list) else set()
    print("%s %s page API (%d pages listed)" % ("ok  " if status == 200 else "FAIL", status, len(titles)))
    bad = 0 if status == 200 else 1
    pages = wiki_pages(a.dir)
    for p in pages:
        s, loc, _ = fetch("%s/%s/wiki/%s" % (base, repo, urllib.request.quote(p)))
        good = s == 200 and (not titles or p in titles)
        print("%s %s %s%s" % ("ok  " if good else "FAIL", s, p, (" -> " + loc) if loc else ""))
        bad += 0 if good else 1
    s, _, body = fetch("%s/%s/wiki/" % (base, repo))
    print("%s %s wiki root" % ("ok  " if s == 200 else "FAIL", s))
    bad += 0 if s == 200 else 1
    more, lines = render_probes(a, html_text(body))
    for line in lines:
        print(line)
    print("live: %d pages, %d failures" % (len(pages), bad + more))
    return 1 if bad + more else 0


def live_gitlab(a, scheme, host, repo):
    """GitLab (measured 2026-09-29): page HTML is rendered by JavaScript, so pages are checked through the
    wiki API (anonymous for a public wiki) and the web status; slugs are case-insensitive."""
    base, token = "%s://%s" % (scheme, host), os.environ.get(TOKEN_ENV)
    api = "%s/api/v4/projects/%s/wikis" % (base, urllib.request.quote(repo, safe=""))
    status, listed, _ = api_get(api, token, token_header="PRIVATE-TOKEN")
    slugs = {str(p.get("slug", "")).lower() for p in listed} if isinstance(listed, list) else set()
    print("%s %s wiki API (%d pages listed)" % ("ok  " if status == 200 else "FAIL", status, len(slugs)))
    bad = 0 if status == 200 else 1
    pages = wiki_pages(a.dir)
    for p in pages:
        s, loc, _ = fetch("%s/%s/-/wikis/%s" % (base, repo, urllib.request.quote(p)))
        good = s == 200 and p.lower() in slugs
        print("%s %s %s%s" % ("ok  " if good else "FAIL", s, p, "" if p.lower() in slugs else " (not in the API list)"))
        bad += 0 if good else 1
    if os.path.exists(os.path.join(a.dir, "_sidebar.md")):
        good = "_sidebar" in slugs
        print("%s sidebar (_sidebar in the API list)" % ("ok  " if good else "FAIL"))
        bad += 0 if good else 1
    print("live: %d pages, %d failures" % (len(pages), bad))
    return 1 if bad else 0


def live_azure(a, host, repo):
    """Azure DevOps (read anonymously on public projects, 2026-09-29): a page GET by path answers 200; a
    hyphen in a file name is a space in the page path. The web pages are a JavaScript shell."""
    parts = repo.split("/")
    org, project = parts[0], parts[1]
    wiki = parts[3] if len(parts) > 3 and parts[2] == "_git" else project + ".wiki"
    bad, pages = 0, wiki_pages(a.dir)
    for p in pages:
        url = "https://dev.azure.com/%s/%s/_apis/wiki/wikis/%s/pages?path=%s&api-version=7.1" % (
            org, project, urllib.request.quote(wiki), urllib.request.quote("/" + p.replace("-", " ")))
        s, _, _ = api_get(url)
        print("%s %s %s" % ("ok  " if s == 200 else "FAIL", s, p))
        bad += 0 if s == 200 else 1
    print("live: %d pages, %d failures" % (len(pages), bad))
    return 1 if bad else 0


def cmd_live(a):
    scheme, host, repo = parse_remote(a.repo)
    if host is None:
        print("error: %s is not OWNER/REPO or a remote URL" % a.repo)
        return 2
    kind = a.kind or detect_kind(scheme, host)
    if kind in ("gitea", "forgejo"):
        return live_gitea(a, scheme, host, repo, kind)
    if kind == "gitlab":
        return live_gitlab(a, scheme, host, repo)
    if kind == "azure":
        return live_azure(a, host, repo)
    if kind != "github":
        print("error: %s is not a host live knows (pass --kind)" % host)
        return 2
    a.repo = repo
    base = "https://github.com/%s/wiki" % a.repo
    pages = sorted(f[:-3] for f in os.listdir(a.dir) if f.endswith(".md") and f not in SPECIAL)
    bad = 0
    for p in pages:
        status, loc, _ = fetch("%s/%s" % (base, urllib.request.quote(p)))
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
        # Whitespace ignored: tag boundaries put spaces where the markdown has none ("see Home .").
        flat = "".join(root.split())
        missing = [t for t in probes if t and "".join(t.split()) not in flat]
        print("%s %s renders (%d of %d probes found)%s" % (
            "ok  " if not missing else "FAIL", label, len(probes) - len(missing), len(probes),
            ("; missing: " + ", ".join(missing[:5])) if missing else ""))
        bad += 1 if missing else 0
    print("live: %d pages, %d failures" % (len(pages), bad))
    return 1 if bad else 0


# ---------------------------------------------------------------- outputs

# A prose line that introduces an output block: it ends with a colon, and one of the last six
# words before the colon names what follows as output ("Output:", "`pretty` is:", "gives:",
# "prints, exit code 2:"). Earlier words do not count: "Single-quoted strings are tracked like
# double-quoted ones, so the space inside stays:" introduces an input (L-103).
OUT_WORDS = {
    "output", "outputs", "is", "are", "give", "gives", "gave", "print", "prints", "printed",
    "return", "returns", "returned", "show", "shows", "exit", "exits", "stdout", "stderr", "log",
    "logs", "logged", "answer", "answers", "answered", "received", "result", "results",
    "become", "becomes", "produce", "produces", "yield", "yields"}
ARROW = re.compile(r"(?://|#)\s?=>\s?(.*\S)")
PROMPT = re.compile(r"^(\$|PS>|PS [A-Z]:.*>|>)( |$)")
FIXTURE = re.compile(r"http://127\.0\.0\.1:(?:[0-9]+|<port>)")
PORT = re.compile(r"127\.0\.0\.1:[0-9]+")
FENCE = re.compile(r"^(\s*)(```+|~~~+)\s*([\w+#-]*)")
DIRECTIVE = re.compile(r"^<!--\s*outputs:\s*(?:(skip|check)\b)?\s*(?:node\s*(>=|<=|==|=|<|>)\s*([0-9]+))?.*-->$")
LANGS_OUTPUT = {"text", "txt", "plaintext", "console", "output"}
LANGS_DATA = {"json", "jsonc", "json5", "xml", "html", "yaml", "yml", "csv", "tsv"}
# Fences whose line comments start with '#'; every other fence uses '//'.
LANGS_HASH = {"powershell", "pwsh", "ps1", "ps", "sh", "bash", "shell", "zsh", "python", "py", "ruby", "rb"}
LANGS_POWERSHELL = {"powershell", "pwsh", "ps1", "ps"}
# A trailing comment: code, whitespace, the comment marker, the comment.
TRAILING = {"//": re.compile(r"^(?P<code>.*\S)\s+//\s?(?P<c>.*\S)\s*$"),
            "#": re.compile(r"^(?P<code>.*\S)\s+#\s?(?P<c>.*\S)\s*$")}
# Words before a value in a comment: "// always "Alisa Streets"", "// for example "Prophetstown"".
LEAD = re.compile(r"(?i)^(?:always|gives|prints|returns|is|e\.g\.|for example)[,:]?\s+")
QUOTED = re.compile(r"^(\"[^\"]*\"|'[^']*'|`[^`]*`)$")
# A comment that holds a value rather than words: quoted, JSON-like, a number or a literal.
VALUE = re.compile(r"^(\"[^\"]*\"|'[^']*'|`[^`]*`|\{.*\}|\[.*\]|-?[0-9]+(?:[.,][0-9]+)?|true|false|null|True|False)$")
# The first word of a command someone types; an untagged block that starts with one after a
# code block is probably a command, not output (the hint says to tag its fence).
COMMAND = re.compile(r"^(\$ )?(dotnet|npm|npx|node|pnpm|yarn|bun|deno|git|gh|python3?|pip|type|cat|curl|echo)\b")
FULL_COMMENT = {"//": re.compile(r"^\s*//\s?(?P<c>.*\S)\s*$"), "#": re.compile(r"^\s*#\s?(?P<c>.*\S)\s*$")}
PRINT_CALL = re.compile(
    r"\b(Console\.Write(?:Line)?|printfn|printf|print|console\.(?:log|info|error)|Write-Output|Write-Host|echo|puts)\b")
# A PowerShell line that is neither an assignment nor a cmdlet call outputs its value.
PS_STATEMENT = re.compile(r"^\s*(\$[\w:.]+\s*[-+*/]?=[^=]|[A-Za-z]+-[A-Za-z]+\b)")


def normalise_output(text, address):
    text = text.replace("\r\n", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = FIXTURE.sub("<FIXTURE>", text)
    text = PORT.sub("127.0.0.1:<port>", text)
    if address:
        text = text.replace(address.rstrip("/"), "<FIXTURE>")
    return text


def is_intro(prose):
    tail = prose.rstrip(" )*_`")
    if not tail.endswith(":"):
        # A short connective between an input and its output: "becomes", "gives", "prints".
        words = re.findall(r"[A-Za-z]+", tail)
        return 0 < len(words) <= 3 and words[-1].lower() in OUT_WORDS and not tail.endswith(".")
    words = re.findall(r"[A-Za-z]+", tail[:-1])[-6:]
    return any(w.lower() in OUT_WORDS for w in words)


def fences(text):
    """Every fenced block: start line, language, body, the prose line before it, the
    <!-- outputs: --> directive before it, and whether only blank lines or directives
    separate it from the block before it."""
    items, lines = [], text.split("\n")
    i, prev, directive, scope, adjacent = 0, "", None, None, False
    while i < len(lines):
        m = FENCE.match(lines[i])
        if not m:
            stripped = lines[i].strip()
            d = DIRECTIVE.match(stripped)
            if d and (d.group(1) or d.group(2)):
                directive = d.group(1) or directive
                scope = (d.group(2).replace("==", "="), int(d.group(3))) if d.group(2) else scope
            elif stripped:
                prev, adjacent = stripped, False
            i += 1
            continue
        indent, fence, lang = m.group(1), m.group(2), m.group(3).lower()
        start, body = i + 1, []
        i += 1
        while i < len(lines) and not re.match(r"^\s*" + re.escape(fence[0]) + "{%d,}\\s*$" % len(fence), lines[i]):
            body.append(lines[i][len(indent):] if lines[i].startswith(indent) else lines[i])
            i += 1
        i += 1
        items.append({"start": start, "lang": lang, "body": body, "prev": prev,
                      "directive": directive, "scope": scope, "adjacent": adjacent})
        prev, directive, scope, adjacent = "", None, None, True
    return items


def pairs(first, second):
    """A block followed directly by its output, with nothing but blank lines between: two
    untagged fences or two of one data language (an input and what it becomes, JsonPrettyPrinter's
    Not-a-Validator page), or a code fence and an untagged one (code and what it prints, its
    Serialisation-Helpers page). Tag a command that follows code (```sh), or it reads as output."""
    if not second["adjacent"] or first["lang"] in LANGS_OUTPUT:
        return False
    if first["lang"] == second["lang"]:
        return not first["lang"] or first["lang"] in LANGS_DATA
    return bool(first["lang"]) and first["lang"] not in LANGS_DATA and not second["lang"]


def comment_value(lang, line):
    """(kind, value) for the output a code line shows: 'arrow' for //=> and # =>, 'comment' for a
    value in a comment; None for code or an explanation."""
    a = ARROW.search(line)
    if a:
        return "arrow", a.group(1)
    mark = "#" if lang in LANGS_HASH else "//"
    full = FULL_COMMENT[mark].match(line)
    if full:
        # A comment line of its own shows the value of the line above only when it is a value.
        comment = LEAD.sub("", full.group("c"))
        return ("comment", comment) if VALUE.match(comment) else None
    t = TRAILING[mark].match(line)
    if not t:
        return None
    code, comment = t.group("code"), LEAD.sub("", t.group("c"))
    if VALUE.match(comment) or PRINT_CALL.search(code) or (
            lang in LANGS_POWERSHELL and not PS_STATEMENT.match(code)):
        return "comment", comment
    return None


def comment_run(lang, body):
    """(index of its first line, the uncommented text) for a run of whole-line comments that ends a
    code block after a blank line: the block's output, as RandomNameGenerator's Recipes show it
    (`// Kerry Marrello from La Plena comunidad`). None when the block does not end that way."""
    full = FULL_COMMENT["#" if lang in LANGS_HASH else "//"]
    end = len(body)
    while end and not body[end - 1].strip():
        end -= 1
    first = end
    while first and full.match(body[first - 1]):
        first -= 1
    if first == end or first < 2 or body[first - 1].strip() or not any(b.strip() for b in body[:first - 1]):
        return None
    return first, "\n".join(full.match(b).group("c") for b in body[first:end])


def output_blocks(text):
    """(line, kind, content) for every output a page presents: kind 'block', 'arrow', 'comment'
    or 'skip'.

    A block is output when its fence is text, console or output; when the directive before it is
    <!-- outputs: check -->; when it is untagged or data and the prose line before it introduces
    output; or when it follows its input block directly (see pairs). In every other code block,
    '//=>' and '# =>' values are checked ('arrow'), and so are comments that show a value
    ('comment'): a quoted, JSON-like, numeric or literal comment, on its own line or after code,
    and any trailing comment after a print call or on a PowerShell expression line. A run of
    whole-line comments that ends a code block after a blank line is that block's output."""
    return [found[:3] for found in scoped_output_blocks(text)]


def scoped_output_blocks(text):
    """output_blocks with a fourth item: the block's Node scope from <!-- outputs: node>=22 -->,
    as (operator, major), or None (L-119)."""
    found, items = [], fences(text)
    pair_output = set()
    for k, f in enumerate(items):
        found = [x if len(x) == 4 else x + (items[k - 1]["scope"],) for x in found]
        start, lang, body, directive = f["start"], f["lang"], f["body"], f["directive"]
        is_input = (k not in pair_output and directive != "check" and lang not in LANGS_OUTPUT
                    and k + 1 < len(items) and pairs(f, items[k + 1]))
        if is_input:
            pair_output.add(k + 1)
        is_output = not is_input and (directive == "check" or lang in LANGS_OUTPUT or k in pair_output or (
            directive != "skip" and (not lang or lang in LANGS_DATA) and is_intro(f["prev"])))
        if directive == "skip":
            found.append((start, "skip", "\n".join(body)))
        elif is_output and any(PROMPT.match(b) for b in body):
            # A terminal transcript: check what follows each command, not the commands.
            chunk, chunk_line = [], start
            for n, b in enumerate(body + ["$ "]):
                if PROMPT.match(b):
                    if "\n".join(chunk).strip():
                        found.append((chunk_line, "block", "\n".join(chunk).strip("\n")))
                    chunk, chunk_line = [], start + n + 1
                else:
                    chunk.append(b)
        elif is_output:
            found.append((start, "block", "\n".join(body)))
        elif lang not in LANGS_OUTPUT and not (is_input and not lang):
            run = comment_run(lang, body) if lang else None
            if run:
                found.append((start + run[0] + 1, "block", run[1]))
            for n, b in enumerate(body[:run[0]] if run else body):
                value = comment_value(lang, b)
                if value:
                    found.append((start + n + 1,) + value)
    return [x if len(x) == 4 else x + (items[-1]["scope"],) for x in found]


NODE_LINE = re.compile(r"\bNode v?([0-9]+)\.[0-9]+")


def node_major(text):
    """The Node major a verification output ran on: the first 'Node v24.18.0' in it (the template's
    'installed' line), or None."""
    m = NODE_LINE.search(text)
    return int(m.group(1)) if m else None


def in_scope(scope, major):
    if scope is None:
        return True
    if major is None:
        return False
    op, n = scope
    return {">=": major >= n, "<=": major <= n, "=": major == n, "<": major < n, ">": major > n}[op]


def cmd_outputs(a):
    if not os.path.isdir(a.dir):
        print("error: %s is not a directory" % a.dir)
        return 2
    runs = []
    for path in a.verify:
        with open(path, "rb") as fh:
            text = normalise_output(fh.read().decode("utf-8", errors="replace"), a.address)
        runs.append((a.node if a.node is not None else node_major(text), text))
    views = {}

    def view(scope):
        # The outputs a block may come from: all of them, or those of the Node lines its marker names.
        if scope not in views:
            out = "\n".join(text for major, text in runs if in_scope(scope, major))
            views[scope] = (out, " ".join(out.split()), {line.strip() for line in out.split("\n")})
        return views[scope]

    pages = sorted(f for f in os.listdir(a.dir) if f.endswith(".md") and f not in SPECIAL)
    checked = missing = skipped = 0
    for f in pages:
        text = page_text(os.path.join(a.dir, f))[1].replace("\r\n", "\n")
        for line, kind, content, scope in scoped_output_blocks(text):
            if kind == "skip":
                skipped += 1
                print("%s:%d: skip: marked <!-- outputs: skip -->" % (f, line))
                continue
            want = normalise_output(content, a.address).strip("\n")
            if not want.strip():
                continue
            out, loose, out_lines = view(scope)
            if scope and not any(in_scope(scope, major) for major, _ in runs):
                skipped += 1
                print("%s:%d: skip: node%s%d, and no output given is from that Node" % (f, line, scope[0], scope[1]))
                continue
            checked += 1
            if kind in ("arrow", "comment"):
                # A short value ("2", "true") must be a whole line of the output, or it would match anywhere.
                bare = want[1:-1] if len(want) > 1 and want[0] == want[-1] and want[0] in "'\"`" else want
                if want in out_lines or bare in out_lines or (len(bare) >= 8 and (want in out or bare in out)):
                    continue
            elif want in out:
                continue
            missing += 1
            first = want.strip().split("\n")[0][:70]
            relaid = kind == "block" and " ".join(want.split()) in loose
            hint = " (found with different spacing: the layout differs, L-008)" if relaid else ""
            if kind == "block" and not relaid and COMMAND.match(first):
                hint = " (a command after a code block? tag its fence, for example ```sh)"
            label = {"block": "output block", "arrow": "//=> value", "comment": "comment value"}[kind]
            print("%s:%d: error: %s not in the verify output%s: %s" % (f, line, label, hint, first))
    print("outputs: %d pages, %d outputs checked, %d missing, %d skipped" % (len(pages), checked, missing, skipped))
    return 1 if missing else 0


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


# ---------------------------------------------------------------- diffout

SECTION = re.compile(r"^## (.+)$")
LOCAL_PORT = re.compile(r"\b(localhost|127\.0\.0\.1|\[::1\]):[0-9]+\b")
PREAMBLE = "(before the first section)"


def diff_normalise(text, masks=(), paths=()):
    """LF, no trailing spaces, every local port as <port>, each (path, name) in paths as <name>
    (L-119: a stderr line naming node.exe), then each mask regex as <masked>."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = LOCAL_PORT.sub(lambda m: m.group(1) + ":<port>", text)
    for path, name in paths:
        text = path_pattern(path).sub("<%s>" % name, text)
    for mask in masks:
        text = re.sub(mask, "<masked>", text)
    return text


def path_pattern(path):
    """A local path as printed natively, with forward slashes, or JSON-escaped (doubled backslashes);
    case-insensitive on Windows, where the drive letter's case varies."""
    path = os.path.normpath(path).rstrip("\\/")
    parts = [p for p in re.split(r"[\\/]", path)]
    sep = r"(?:\\\\|\\|/)"
    return re.compile(sep.join(re.escape(p) for p in parts), re.IGNORECASE if os.name == "nt" else 0)


def machine_paths(new):
    """The scratch folder the new output was written in, the temp folder and the home folder,
    longest first so the most specific name wins."""
    found = [(os.path.dirname(os.path.abspath(new)), "scratch"), (tempfile.gettempdir(), "temp"),
             (os.path.expanduser("~"), "home")]
    found = [(p, n) for p, n in found if p and len(os.path.normpath(p)) > 3]
    return sorted(found, key=lambda x: -len(x[0]))


def sections(text):
    """A verification output as [(label, body lines)], split at its '## label' lines; a repeated label gets ' #2'."""
    out, seen = [], {}
    label, body = PREAMBLE, []
    for line in text.split("\n"):
        m = SECTION.match(line)
        if not m:
            body.append(line)
            continue
        if label != PREAMBLE or any(b.strip() for b in body):
            out.append((label, body))
        name = m.group(1).strip()
        seen[name] = seen.get(name, 0) + 1
        label = name if seen[name] == 1 else "%s #%d" % (name, seen[name])
        body = []
    if label != PREAMBLE or any(b.strip() for b in body):
        out.append((label, body))
    # A body's trailing blank lines are the separator before the next section, not output.
    return [(k, v[:len(v) - next((i for i, b in enumerate(reversed(v)) if b.strip()), len(v))]) for k, v in out]


def cmd_diffout(a):
    texts = []
    paths = [] if a.keep_paths else machine_paths(a.new)
    for path in (a.old, a.new):
        try:
            with open(path, "rb") as fh:
                texts.append(diff_normalise(fh.read().decode("utf-8", errors="replace"), a.mask, paths))
        except OSError as e:
            print("error: %s" % e)
            return 2
    skip = [re.compile(s) for s in a.skip]
    old_list, new_list = sections(texts[0]), sections(texts[1])
    old, new = dict(old_list), dict(new_list)
    order = [k for k, _ in old_list] + [k for k, _ in new_list if k not in old]
    same = changed = added = removed = skipped = 0
    for label in order:
        if any(s.search(label) for s in skip):
            skipped += 1
        elif label not in new:
            removed += 1
            print("--- removed: ## %s" % label)
        elif label not in old:
            added += 1
            print("+++ added: ## %s" % label)
            for line in new[label][:8]:
                print("  + " + line)
        elif old[label] == new[label]:
            same += 1
        else:
            changed += 1
            print("*** changed: ## %s" % label)
            for line in difflib.unified_diff(old[label], new[label], lineterm="", n=a.context):
                if not line.startswith(("---", "+++")):
                    print("  " + line)
    if a.save:
        with open(a.save, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(texts[1].rstrip("\n") + "\n")
        print("saved the normalised new output to %s" % a.save)
    print("diffout: %d sections, %d same, %d changed, %d added, %d removed, %d skipped"
          % (len(order), same, changed, added, removed, skipped))
    return 1 if changed or added or removed else 0


# ---------------------------------------------------------------- cachecheck, releasecheck

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SKILL_REL = ("skills", "wikiwright")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked_files(root):
    """Every tracked file under skills/ and .claude-plugin/ (git ls-files), or every file there
    when root is not a git working copy; __pycache__ left out."""
    p = run(["git", "-C", root, "ls-files", "-z", "--", "skills", ".claude-plugin"])
    if p.returncode == 0 and p.stdout:
        files = [f for f in p.stdout.split("\0") if f]
    else:
        files = []
        for top in ("skills", ".claude-plugin"):
            for base, dirs, names in os.walk(os.path.join(root, top)):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                files += [os.path.relpath(os.path.join(base, n), root).replace(os.sep, "/") for n in names]
    return sorted(f for f in files if "__pycache__" not in f and not f.endswith(".pyc"))


def installed_path(name="wikiwright"):
    config = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    try:
        with open(os.path.join(config, "plugins", "installed_plugins.json"), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None, None
    plugins = data.get("plugins", data) if isinstance(data, dict) else {}
    for key, entries in plugins.items():
        if key.split("@")[0] == name and isinstance(entries, list) and entries:
            return entries[0].get("installPath"), key
    return None, None


def cmd_cachecheck(a):
    source = a.source or PLUGIN_ROOT
    cache, key = (a.cache, None) if a.cache else installed_path()
    if not cache or not os.path.isdir(cache):
        print("error: no installed copy found (pass --cache DIR); installed_plugins.json names %s" % (cache or "none"))
        return 2
    if os.path.normcase(os.path.abspath(source)) == os.path.normcase(os.path.abspath(cache)):
        print("error: this is the installed copy; run the source's wikiwright.py or pass --source")
        return 2
    files = tracked_files(source)
    if not files:
        print("error: no files under skills/ or .claude-plugin/ in %s" % source)
        return 2
    print("source: %s\ncache:  %s%s" % (source, cache, ("  (" + key + ")") if key else ""))
    differ, missing = [], []
    for f in files:
        there = os.path.join(cache, *f.split("/"))
        if not os.path.exists(there):
            missing.append(f)
        elif sha256(os.path.join(source, *f.split("/"))) != sha256(there):
            differ.append(f)
    extra = sorted(set(tracked_files(cache)) - set(files))
    for label, items in (("differs", differ), ("missing from the cache", missing), ("only in the cache", extra)):
        for f in items:
            print("%s: %s" % (label, f))
    print("cachecheck: %d files, %d equal, %d differ, %d missing, %d only in the cache" % (
        len(files), len(files) - len(differ) - len(missing), len(differ), len(missing), len(extra)))
    if differ or missing:
        print("       reinstall: claude plugin uninstall %s, then claude plugin install %s (update keeps a "
              "stale copy while the version is unchanged, L-012)" % (key or "wikiwright@<marketplace>",
                                                                     key or "wikiwright@<marketplace>"))
    return 1 if differ or missing or extra else 0


def read_or_empty(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


TEST_ID = re.compile(r"^### (T-[0-9]{8}-[0-9]+)\b", re.M)


def cmd_releasecheck(a):
    root = a.root or PLUGIN_ROOT
    skill = os.path.join(root, *SKILL_REL)
    want = a.release.lstrip("v")
    exact = re.compile(r"(?<![0-9.])" + re.escape(want) + r"(?![0-9.])")
    found = {}
    try:
        found[".claude-plugin/plugin.json version"] = json.loads(
            read_or_empty(os.path.join(root, ".claude-plugin", "plugin.json")) or "{}").get("version")
        found["evergreen.json version"] = json.loads(
            read_or_empty(os.path.join(skill, "evergreen.json")) or "{}").get("version")
    except ValueError as e:
        print("error: %s" % e)
        return 2
    m = re.search(r'^VERSION = "([^"]+)"', read_or_empty(os.path.join(skill, "scripts", "wikiwright.py")), re.M)
    found["wikiwright.py VERSION"] = m.group(1) if m else None
    front = read_or_empty(os.path.join(skill, "SKILL.md")).split("\n---", 1)[0]
    m = re.search(r'^\s+version:\s*"?([^"\s]+)"?\s*$', front, re.M)
    found["SKILL.md metadata.version"] = m.group(1) if m else None
    bad = 0
    for label, value in found.items():
        ok = value == want
        bad += 0 if ok else 1
        print("%s %s: %s" % ("ok  " if ok else "FAIL", label, value))
    entries = [line for line in read_or_empty(os.path.join(skill, "CHANGELOG.md")).split("\n")
               if line.startswith("### C-") and exact.search(line)]
    print("%s CHANGELOG entry naming %s%s" % ("ok  " if entries else "FAIL", want,
                                              (": " + entries[0][4:80]) if entries else ""))
    bad += 0 if entries else 1
    tests_now = set(TEST_ID.findall(read_or_empty(os.path.join(skill, "TESTS.md"))))
    tag = run(["git", "-C", root, "describe", "--tags", "--abbrev=0"]).stdout.strip()
    then = set()
    if tag:
        shown = run(["git", "-C", root, "show", "%s:%s/TESTS.md" % (tag, "/".join(SKILL_REL))])
        then = set(TEST_ID.findall(shown.stdout)) if shown.returncode == 0 else set()
    new = sorted(tests_now - then)
    print("%s TESTS run since %s: %s" % ("ok  " if new else "FAIL", tag or "the start (no tag)",
                                         ", ".join(new) if new else "none"))
    bad += 0 if new else 1
    exists = run(["git", "-C", root, "rev-parse", "-q", "--verify", "refs/tags/v" + want]).returncode == 0
    if exists:
        print("FAIL tag v%s exists already" % want)
        bad += 1
    print("releasecheck %s: %s" % (want, "ready to tag" if not bad else "%d problem(s)" % bad))
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wikiwright.py", description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=VERSION)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preflight", help="wiki feature, wiki repository, placeholder, clone")
    p.add_argument("repo", help="OWNER/REPO (GitHub), a remote URL, or a clone")
    p.add_argument("--enable", action="store_true", help="switch the wiki feature on when it is off")
    p.add_argument("--wait", type=int, help="seconds to keep re-checking ls-remote (default 60 after --enable)")
    p.add_argument("--clone", help="clone the wiki repository here (a sibling <clone>.wiki)")
    p.add_argument("--kind", choices=KINDS, help="the host's kind, when neither its name nor its API tells")
    p.add_argument("--seed", action="store_true",
                   help="Gitea and Forgejo: create the wiki with a first page through the API (needs %s)" % TOKEN_ENV)
    p.set_defaults(fn=cmd_preflight)
    c = sub.add_parser("check", help="lint a wiki working copy")
    c.add_argument("dir")
    c.add_argument("--version", dest="version", help="the package version the footer must name")
    c.add_argument("--partial", action="store_true",
                   help="a draft of some pages: no sidebar or footer required")
    c.add_argument("--host", choices=KINDS, default="github",
                   help="the host's rules: navigation files, wikilinks, anchors, file names (default github)")
    c.set_defaults(fn=cmd_check)
    lv = sub.add_parser("live", help="check the published pages")
    lv.add_argument("repo", help="OWNER/REPO (GitHub) or the repository's URL on another host")
    lv.add_argument("dir", help="the working copy (for the page list, sidebar and footer)")
    lv.add_argument("--kind", choices=KINDS, help="the host's kind, when neither its name nor its API tells")
    lv.set_defaults(fn=cmd_live)
    o = sub.add_parser("outputs", help="every output a page shows appears in the verify output")
    o.add_argument("dir", help="the wiki working copy (or a folder of draft pages)")
    o.add_argument("verify", nargs="+", help="the verification script's saved output (one or more files)")
    o.add_argument("--address", default="https://example.com",
                   help="the address pages show in place of the fixture's http://127.0.0.1:<port> "
                        "(default https://example.com; pass '' for none)")
    o.add_argument("--node", type=int,
                   help="the Node major every output ran on (default: read from each output's 'Node vN' line); "
                        "a block after <!-- outputs: node>=22 --> is checked only against outputs in its range")
    o.set_defaults(fn=cmd_outputs)
    u = sub.add_parser("unbs", help="replace <BS> placeholders with backslashes")
    u.add_argument("files", nargs="+")
    u.set_defaults(fn=cmd_unbs)
    d = sub.add_parser("diffout", help="compare two runs of a verification script, section by section")
    d.add_argument("old", help="the saved output (the repository's *-wiki-verify.out.txt)")
    d.add_argument("new", help="this run's output")
    d.add_argument("--skip", action="append", default=[], help="leave out sections whose label matches this regex")
    d.add_argument("--mask", action="append", default=[], help="replace text matching this regex with <masked>")
    d.add_argument("--context", type=int, default=1, help="unchanged lines around each change (default 1)")
    d.add_argument("--save", help="write the normalised new output here (ports as <port>; the new output's "
                                  "folder, the temp folder and the home folder as <scratch>, <temp>, <home>)")
    d.add_argument("--keep-paths", action="store_true", help="leave local paths as they are")
    d.set_defaults(fn=cmd_diffout)
    cc = sub.add_parser("cachecheck", help="the installed plugin cache against the source, by SHA-256")
    cc.add_argument("--source", help="the plugin's source repository (default: the one holding this script)")
    cc.add_argument("--cache", help="the installed copy (default: installPath of wikiwright@* in "
                                    "~/.claude/plugins/installed_plugins.json)")
    cc.set_defaults(fn=cmd_cachecheck)
    rc = sub.add_parser("releasecheck", help="version fields, CHANGELOG entry and a test run before tagging")
    rc.add_argument("release", help="the version about to be tagged, X.Y.Z")
    rc.add_argument("--root", help="the plugin's repository (default: the one holding this script)")
    rc.set_defaults(fn=cmd_releasecheck)
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure:
        # A cp1252 console cannot print every character an output holds (L-119).
        reconfigure(encoding="utf-8", errors="replace")
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
