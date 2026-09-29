"""Tests for skills/wikiwright/scripts/wikiwright.py (check, unbs, slug).

Run from the repository root: python tests/test_wikiwright.py
The network subcommands (preflight, live) are exercised by the eval suite.
"""

import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "wikiwright", "scripts"))
import wikiwright  # noqa: E402

BACKSLASH = chr(92)

GOOD = {
    "Home.md": "Widget 1.2.0 does one thing.\n\nSee [Getting started](Getting-Started) and [the API](API-Reference#options).\n",
    "Getting-Started.md": "# Getting started\n\n## Install\n\n```sh\nnpm install widget\n```\n",
    "API-Reference.md": "# API reference\n\n## Options\n\nText with `[[not a wikilink]]` in code.\n\n```\n[[also fine]]\n```\n",
    "_Sidebar.md": "[Home](Home)\n\n- [Getting started](Getting-Started)\n- [API reference](API-Reference)\n",
    "_Footer.md": "This wiki describes widget 1.2.0 and was last updated on 2026-09-28.\n",
}


def write(d, files):
    for name, text in files.items():
        with open(os.path.join(d, name), "wb") as fh:
            fh.write(text.encode("utf-8"))


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = wikiwright.main(argv)
    return code, out.getvalue()


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        write(self.d, GOOD)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_clean_wiki_passes(self):
        code, out = run(["check", self.d, "--version", "1.2.0"])
        self.assertEqual(code, 0, out)
        self.assertIn("0 errors", out)

    def test_missing_page_and_anchor(self):
        write(self.d, {"Home.md": "[x](Recipes) and [y](API-Reference#nope) and [z](#here)\n"})
        code, out = run(["check", self.d])
        self.assertEqual(code, 1)
        self.assertIn("missing page Recipes", out)
        self.assertIn("no heading for #nope on API-Reference", out)
        self.assertIn("no heading for #here on this page", out)

    def test_md_suffix_and_wikilink(self):
        write(self.d, {"Home.md": "[x](Getting-Started.md) and [[Getting-Started]]\n"})
        code, out = run(["check", self.d])
        self.assertEqual(code, 1)
        self.assertIn("drop the .md", out)
        self.assertIn("wikilink", out)

    def test_crlf_bs_and_attribution(self):
        write(self.d, {"Home.md": "a\r\nb <BS>n\nCo-Authored-By: Someone\n"})
        code, out = run(["check", self.d])
        self.assertEqual(code, 1)
        self.assertIn("carriage returns", out)
        self.assertIn("<BS> placeholder", out)
        self.assertIn("AI attribution", out)

    def test_footer_version_and_date(self):
        write(self.d, {"_Footer.md": "This wiki describes widget.\n"})
        code, out = run(["check", self.d, "--version", "1.2.0"])
        self.assertEqual(code, 1)
        self.assertIn("does not name version 1.2.0", out)
        self.assertIn("names no date", out)

    def test_missing_sidebar_and_unlisted_page(self):
        os.remove(os.path.join(self.d, "_Sidebar.md"))
        code, out = run(["check", self.d])
        self.assertEqual(code, 1)
        self.assertIn("_Sidebar.md:0: error: missing", out)
        write(self.d, {"_Sidebar.md": "[Home](Home)\n", "FAQ.md": "# FAQ\n"})
        code, out = run(["check", self.d])
        self.assertIn("does not link FAQ", out)

    def test_unclosed_fence_and_title_case(self):
        write(self.d, {"FAQ.md": "# Frequently Asked Questions Here\n\n```js\nopen\n",
                       "_Sidebar.md": GOOD["_Sidebar.md"] + "- [FAQ](FAQ)\n"})
        code, out = run(["check", self.d])
        self.assertEqual(code, 1)
        self.assertIn("never closed", out)
        self.assertIn("Title Case", out)

    def test_duplicate_heading_anchor(self):
        write(self.d, {"FAQ.md": "# FAQ\n\n## Why\n\n## Why\n",
                       "Home.md": "[a](FAQ#why-1)\n",
                       "_Sidebar.md": GOOD["_Sidebar.md"] + "- [FAQ](FAQ)\n"})
        code, out = run(["check", self.d])
        self.assertEqual(code, 0, out)


class SlugTests(unittest.TestCase):
    def test_slugs(self):
        self.assertEqual(wikiwright.slug("Getting started"), "getting-started")
        self.assertEqual(wikiwright.slug("`extractTitle(html, options?)`"), "extracttitlehtml-options")
        self.assertEqual(wikiwright.slug("1.x and 2.x to 3.0.0"), "1x-and-2x-to-300")
        self.assertEqual(wikiwright.slug("What it refuses"), "what-it-refuses")


class UnbsTests(unittest.TestCase):
    def test_replaces_placeholders(self):
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "Page.md")
            with open(p, "wb") as fh:
                fh.write(b"C:<BS>Users and <BS>u00e9\n")
            code, out = run(["unbs", p])
            self.assertEqual(code, 0)
            with open(p, "rb") as fh:
                self.assertEqual(fh.read().decode(), "C:" + BACKSLASH + "Users and " + BACKSLASH + "u00e9\n")
            self.assertIn("2 placeholders", out)
        finally:
            shutil.rmtree(d)


OUTPUT_PAGES = {
    "Home.md": (
        "Roll a die:\n\n```js\nrng.getRandomInteger(1, 7);\n//=> 2\nrng.pick(['a']);\n//=> 'a'\n```\n\n"
        "Output:\n\n```\n[ 1, 3, 4 ]\n```\n\n"
        "A result from the fixture is:\n\n```json\n{\n  \"url\": \"https://example.com/docs\"\n}\n```\n\n"
        "Run it with `node x.mjs`:\n\n```text\ndie roll:      2\n```\n\n"
        "In a terminal:\n\n```console\n$ widget --version\n1.2.0\n\n$ widget nope\nerror: unknown command\n```\n\n"
        "Install it:\n\n```sh\nnpm install widget\n```\n\n"
        "npm prints:\n\n<!-- outputs: skip (npm's own output) -->\n```text\nadded 1 package in 432ms\n```\n"),
}

VERIFY_OUT = (
    "## roll\n2\n'a'\n\n## unique\n[ 1, 3, 4 ]\n\n## fixture\n{\n  \"url\": \"http://127.0.0.1:61234/docs\"\n}\n\n"
    "## run\ndie roll:      2\n\n## cli\nexit 0\n--- stdout\n1.2.0\n--- stderr\n\nexit 1\n--- stdout\n--- stderr\nerror: unknown command\n")


class OutputsTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        write(self.d, OUTPUT_PAGES)
        self.out = os.path.join(self.d, "verify.out.txt")
        with open(self.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(VERIFY_OUT)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_every_output_found(self):
        code, out = run(["outputs", self.d, self.out])
        self.assertEqual(code, 0, out)
        # 2 arrows, the bare block, the json block (the fixture address), the text block, 2 transcript outputs
        self.assertIn("7 outputs checked, 0 missing, 1 skipped", out)

    def test_invented_and_relaid_outputs_fail(self):
        page = OUTPUT_PAGES["Home.md"].replace("//=> 2", "//=> 3").replace("[ 1, 3, 4 ]", "[1, 3, 4]")
        write(self.d, {"Home.md": page})
        code, out = run(["outputs", self.d, self.out])
        self.assertEqual(code, 1)
        self.assertIn("//=> value not in the verify output: 3", out)
        self.assertIn("output block not in the verify output", out)
        self.assertIn("2 missing", out)

    def test_layout_hint_when_only_spacing_differs(self):
        write(self.d, {"Home.md": "Output:\n\n```\ndie roll: 2\n```\n"})
        code, out = run(["outputs", self.d, self.out])
        self.assertEqual(code, 1)
        self.assertIn("layout differs", out)

    def test_address_off_needs_the_fixture_address(self):
        code, out = run(["outputs", self.d, self.out, "--address", ""])
        self.assertEqual(code, 1)
        self.assertIn("1 missing", out)


def blocks(page):
    """What `outputs` checks on one page: [(kind, first line of content)]."""
    return [(kind, content.split("\n")[0]) for _, kind, content in wikiwright.output_blocks(page)]


class OutputFormsTests(unittest.TestCase):
    """The forms the NuGet wikis show output in (0.3.0; L-103), and the ones that are not output."""

    def test_input_block_followed_by_its_output(self):
        # JsonPrettyPrinter's Not-a-Validator page: the intro's "are" is far from the colon.
        page = ("Single-quoted strings are tracked like double-quoted ones, so the space inside stays:\n\n"
                "```\n{'a':'b c'}\n```\n\n```\n{\n    'a': 'b c'\n}\n```\n")
        self.assertEqual(blocks(page), [("block", "{")])

    def test_code_followed_by_its_output(self):
        page = ("```csharp\nthing.ToJson(prettyPrint: true);\n```\n\n```\n{\n    \"Name\": \"Mark\"\n}\n```\n\n"
                "```csharp\nvar x = 1;\n```\n\n```sh\ndotnet run pretty.cs\n```\n")
        self.assertEqual(blocks(page), [("block", "{")])

    def test_intro_word_within_six_words_of_the_colon(self):
        near = "The result's `url` is where the redirects ended:\n\n```json\n{}\n```\n"
        far = "Output of the tool is shown here for a reader to compare:\n\n```\nx\n```\n"
        connective = "```\n{ \"a\" : 1 }\n```\n\nbecomes\n\n```\n{\n    \"a\": 1\n}\n```\n"
        self.assertEqual(blocks(near), [("block", "{}")])
        self.assertEqual(blocks(far), [])
        self.assertEqual(blocks(connective), [("block", "{")])

    def test_values_in_comments(self):
        page = (
            "```csharp\n"
            "Console.WriteLine(people.GenerateRandomFirstAndLastName());  // \"Jon Rohl\"\n"
            "var name = people.GenerateRandomFirstAndLastName();   // always \"Alisa Streets\"\n"
            "Console.WriteLine(places.GenerateRandomPlaceName());  // Boardman\n"
            "printer.PrettyPrint(json, Console.Out);  // straight into any TextWriter\n"
            "var compact = JsonNode.Parse(text)!.ToJsonString();   // {\"a\":[1,2]}\n"
            "new { s = 1 }.ToJson();\n"
            "// {\"s\":1}\n"
            "// a note, not a value\n"
            "```\n\n"
            "```fsharp\nprintfn \"%s\" (people.GenerateRandomFirstAndLastName())   // Alisa Streets\n```\n\n"
            "```powershell\n$o.IndentSize = 2   # sets it\n[X]::LastNames.Count   # 88799\n"
            "Add-Type -Path x.dll   # loads it\n[X]::new() # => Boardman\n```\n\n"
            "```js\nconst a = new Old('level-1');   // 1.1.4\nrng.next(); //=> 2\n```\n")
        self.assertEqual(blocks(page), [
            ("comment", "\"Jon Rohl\""), ("comment", "\"Alisa Streets\""), ("comment", "Boardman"),
            ("comment", "{\"a\":[1,2]}"), ("comment", "{\"s\":1}"), ("comment", "Alisa Streets"),
            ("comment", "88799"), ("arrow", "Boardman"), ("arrow", "2")])

    def test_comment_lines_closing_a_code_block(self):
        page = ("```csharp\nfor (var i = 0; i < 3; i++)\n    Console.WriteLine(Next());\n\n"
                "// Kerry Marrello from La Plena comunidad\n// Iris Velazques from Vanleer\n```\n\n"
                "```csharp\n// Only a comment\n```\n")
        self.assertEqual([(k, c) for _, k, c in wikiwright.output_blocks(page)],
                         [("block", "Kerry Marrello from La Plena comunidad\nIris Velazques from Vanleer")])

    def test_comment_values_are_checked_and_commands_get_a_hint(self):
        d = tempfile.mkdtemp()
        try:
            write(d, {"Getting-Started.md": (
                "```csharp\nConsole.WriteLine(a.Name());   // \"Marguerita\"\nConsole.WriteLine(b.Name());   // \"Ran\"\n```\n\n"
                "```csharp\n#:package Widget@1.2.0\n```\n\n```\ndotnet run names.cs\n```\n")})
            out_file = os.path.join(d, "out.txt")
            with open(out_file, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("## names\nMarguerita\n")
            code, out = run(["outputs", d, out_file])
            self.assertEqual(code, 1)
            self.assertIn("comment value not in the verify output: \"Ran\"", out)
            self.assertIn("tag its fence", out)
            self.assertIn("3 outputs checked, 2 missing", out)
        finally:
            shutil.rmtree(d)


class HostTests(unittest.TestCase):
    def test_resolve_repo(self):
        cases = {
            "m4bwav/widget": ("github.com", "m4bwav/widget"),
            "https://github.com/m4bwav/widget.git": ("github.com", "m4bwav/widget"),
            "git@github.com:m4bwav/widget.git": ("github.com", "m4bwav/widget"),
            "https://gitlab.com/acme/widget": ("gitlab.com", "acme/widget"),
            "git@codeberg.org:knut/foobar.git": ("codeberg.org", "knut/foobar"),
        }
        for arg, want in cases.items():
            self.assertEqual(wikiwright.resolve_repo(arg), want, arg)
        self.assertEqual(wikiwright.resolve_repo("not a repo"), (None, None))

    def test_parse_remote_keeps_ports_and_maps_azure_ssh(self):
        self.assertEqual(wikiwright.parse_remote("http://127.0.0.1:3107/ww7admin/wiki-seeded.git"),
                         ("http", "127.0.0.1:3107", "ww7admin/wiki-seeded"))
        self.assertEqual(wikiwright.parse_remote("git@ssh.dev.azure.com:v3/org/proj/repo"),
                         ("https", "dev.azure.com", "org/proj/_git/repo"))

    def test_kind_by_name_needs_no_request(self):
        for host, kind in (("github.com", "github"), ("codeberg.org", "forgejo"), ("gitlab.com", "gitlab"),
                           ("dev.azure.com", "azure"), ("acme.visualstudio.com", "azure")):
            self.assertEqual(wikiwright.detect_kind("https", host), kind, host)


# ---------------------------------------------------------------- other hosts, against a local fake
# Status codes and bodies as measured on Gitea 1.27.3, Forgejo 16.0.5, gitlab.com and GitLab CE 19.4.1
# (2026-09-29, references/hosts.md). Nothing leaves 127.0.0.1.

import http.server  # noqa: E402
import json  # noqa: E402
import threading  # noqa: E402


class FakeHost:
    def __init__(self, routes):
        self.routes = routes
        self.seen = []
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def answer(self):
                outer.seen.append("%s %s" % (self.command, self.path))
                status, headers, body = outer.routes.get(self.path, (404, {}, "{}"))
                data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
                self.send_response(status)
                for k, v in headers.items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = do_PATCH = answer

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = "http://127.0.0.1:%d" % self.server.server_address[1]

    def close(self):
        self.server.shutdown()
        self.server.server_close()


PAGE_HTML = ('<div class="markup wiki-content-sidebar"><a href="/o/r/wiki/Home">Home</a> '
             '<a href="/o/r/wiki/Getting-Started">Getting started</a></div>'
             '<div class="markup wiki-content-footer">This wiki describes widget 1.2.0.</div>')
GITEA = {
    "/api/v1/version": (200, {}, {"version": "1.27.3"}),
    "/api/v1/repos/o/r": (200, {}, {"has_wiki": True, "private": False, "archived": False}),
    # Before a first page the wiki repository does not exist: Gitea answers info/refs with 500.
    "/o/r.wiki.git/info/refs?service=git-upload-pack": (500, {}, "not found"),
    "/api/v1/repos/o/r/wiki/pages?limit=50": (200, {}, [{"title": "Home", "sub_url": "Home"},
                                                      {"title": "Getting Started", "sub_url": "Getting-Started"}]),
    "/o/r/wiki/Home": (200, {}, PAGE_HTML),
    "/o/r/wiki/Getting-Started": (200, {}, PAGE_HTML),
    "/o/r/wiki/Missing": (303, {"Location": "/o/r/wiki/?action=_pages"}, ""),
    "/o/r/wiki/": (200, {}, PAGE_HTML),
}


class OtherHostTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_gitea_detected_by_api_and_no_wiki_repo_before_a_first_page(self):
        host = FakeHost(GITEA)
        try:
            self.assertEqual(wikiwright.detect_kind("http", host.base[7:]), "gitea")
            code, out = run(["preflight", host.base + "/o/r"])
        finally:
            host.close()
        self.assertEqual(code, 1, out)
        self.assertIn("(gitea)", out)
        self.assertIn("STATE: no-wiki-repo (a push cannot create it on gitea", out)
        self.assertIn("--seed", out)
        self.assertIn("/o/r/wiki/?action=_new", out)

    def test_forgejo_detected_by_its_own_version_route(self):
        host = FakeHost({"/api/forgejo/v1/version": (200, {}, {"version": "16.0.5+gitea-1.22.0"})})
        try:
            self.assertEqual(wikiwright.detect_kind("http", host.base[7:]), "forgejo")
        finally:
            host.close()

    def test_unknown_host_stops(self):
        host = FakeHost({})
        try:
            code, out = run(["preflight", host.base + "/a/b"])
        finally:
            host.close()
        self.assertEqual(code, 2, out)
        self.assertIn("STATE: other-host", out)

    def test_gitea_live_fails_a_missing_page_and_reads_sidebar_and_footer(self):
        write(self.d, {"Home.md": "Widget.\n", "Getting-Started.md": "Go.\n",
                       "_Sidebar.md": "[Home](Home)\n[Getting started](Getting-Started)\n",
                       "_Footer.md": "This wiki describes widget 1.2.0.\n"})
        host = FakeHost(GITEA)
        try:
            code, out = run(["live", host.base + "/o/r", self.d, "--kind", "gitea"])
            self.assertEqual(code, 0, out)
            self.assertIn("ok   200 page API (2 pages listed)", out)
            self.assertIn("ok   sidebar renders (2 of 2 probes found)", out)
            write(self.d, {"Missing.md": "Gone.\n"})
            code, out = run(["live", host.base + "/o/r", self.d, "--kind", "gitea"])
        finally:
            host.close()
        # A missing page answers 303 to the page list, which answers 200: never follow it.
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL 303 Missing -> /o/r/wiki/?action=_pages", out)

    def test_gitlab_live_reads_the_wiki_api(self):
        write(self.d, {"Home.md": "Widget.\n", "_sidebar.md": "[Home](Home)\n"})
        host = FakeHost({"/api/v4/projects/o%2Fr/wikis": (200, {}, [{"slug": "home"}, {"slug": "_sidebar"}]),
                         "/o/r/-/wikis/Home": (200, {}, "<div data-has-custom-sidebar=\"true\"></div>")})
        try:
            code, out = run(["live", host.base + "/o/r", self.d, "--kind", "gitlab"])
        finally:
            host.close()
        self.assertEqual(code, 0, out)
        self.assertIn("ok   sidebar (_sidebar in the API list)", out)


class HostCheckTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_gitea_accepts_wikilinks_and_refuses_spaces_and_folders(self):
        pages = dict(GOOD)
        pages["Home.md"] += "\nAlso [[Getting-Started]].\n"
        pages["Spaced Name.md"] = "x\n"
        write(self.d, pages)
        os.mkdir(os.path.join(self.d, "docs"))
        write(os.path.join(self.d, "docs"), {"Nested.md": "x\n"})
        code, out = run(["check", self.d, "--host", "gitea"])
        self.assertIn("warn: wikilink: gitea resolves it", out)
        self.assertIn("Spaced Name.md:0: error: a space in the file name", out)
        self.assertIn("docs:0: error: pages in a folder", out)
        code, out = run(["check", self.d])
        self.assertIn("error: wikilink; use [Text](Page-Name)", out)

    def test_gitlab_wants_a_lower_case_sidebar_and_no_footer(self):
        write(self.d, GOOD)
        code, out = run(["check", self.d, "--host", "gitlab"])
        self.assertEqual(code, 1, out)
        self.assertIn("_sidebar.md:0: error: missing", out)
        self.assertIn("GitLab reads _sidebar.md (lower case)", out)
        self.assertIn("gitlab shows no footer", out)

    def test_forgejo_collapses_hyphens_in_anchors(self):
        self.assertEqual(wikiwright.slug("Usage (basic) & more"), "usage-basic--more")
        self.assertEqual(wikiwright.slug("Usage (basic) & more", "forgejo"), "usage-basic-more")


class HeadingAnchorTests(unittest.TestCase):
    def test_inline_code_in_a_heading_keeps_its_text(self):
        page = ["# Page", "", "## Deno answers `false` for every URL", "", "```", "## not a heading", "```", ""]
        found = wikiwright.headings(chr(10).join(page))
        self.assertIn("deno-answers-false-for-every-url", found)
        self.assertNotIn("not-a-heading", found)


class PartialCheckTests(unittest.TestCase):
    def test_partial_draft_skips_sidebar_and_footer(self):
        d = tempfile.mkdtemp()
        try:
            write(d, {"Home.md": "Widget 1.2.0.\n"})
            code, out = run(["check", d])
            self.assertEqual(code, 1)
            code, out = run(["check", d, "--version", "1.2.0", "--partial"])
            self.assertEqual(code, 0, out)
        finally:
            shutil.rmtree(d)


OLD_RUN = ("## installed\nwidget@1.2.0 on Node v24.18.0\n\n## home\nfetched http://127.0.0.1:50123/cat\n\n"
           "## api\ntrue\n\n## api\nfalse\n\n## gone later\nx\n")
NEW_RUN = ("## installed\r\nwidget@1.2.0 on Node v20.20.2  \r\n\r\n## home\r\nfetched http://127.0.0.1:61001/cat\r\n\r\n"
           "## api\r\ntrue\r\n\r\n## api\r\nnull\r\n\r\n## new case\r\ny\r\n")


class DiffoutTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.old = os.path.join(self.d, "old.txt")
        self.new = os.path.join(self.d, "new.txt")
        for path, text in ((self.old, OLD_RUN), (self.new, NEW_RUN)):
            with open(path, "wb") as fh:
                fh.write(text.encode("utf-8"))

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_sections_compared_with_ports_and_line_endings_normalised(self):
        code, out = run(["diffout", self.old, self.new])
        self.assertEqual(code, 1, out)
        # The port and CRLF differ only by machine: "home" and the first "api" are the same.
        self.assertIn("*** changed: ## installed", out)
        self.assertIn("*** changed: ## api #2", out)
        self.assertIn("  +null", out)
        self.assertIn("+++ added: ## new case", out)
        self.assertIn("--- removed: ## gone later", out)
        self.assertNotIn("## home", out)
        self.assertIn("diffout: 6 sections, 2 same, 2 changed, 1 added, 1 removed, 0 skipped", out)

    def test_skip_mask_and_save(self):
        saved = os.path.join(self.d, "saved.txt")
        code, out = run(["diffout", self.old, self.new, "--skip", "^(api #2|new case|gone later)$",
                         "--mask", r"Node v[0-9.]+", "--save", saved])
        self.assertEqual(code, 0, out)
        self.assertIn("6 sections, 3 same, 0 changed, 0 added, 0 removed, 3 skipped", out)
        with open(saved, "rb") as fh:
            raw = fh.read()
        self.assertNotIn(b"\r", raw)
        self.assertIn(b"http://127.0.0.1:<port>/cat", raw)

    def test_identical_runs_pass(self):
        code, out = run(["diffout", self.old, self.old])
        self.assertEqual(code, 0, out)

    def test_local_paths_masked_and_saved(self):
        # Node 20's "bad option" line names node.exe in the run's scratch folder (L-119).
        scratch = os.path.join(self.d, "run")
        os.mkdir(scratch)
        new = os.path.join(scratch, "new.txt")
        exe = os.path.join(scratch, "node", "node.exe")
        with open(new, "wb") as fh:
            fh.write((OLD_RUN + "## stderr\n%s: bad option\n%s\n" % (exe, exe.replace(BACKSLASH, BACKSLASH * 2))).encode())
        saved = os.path.join(self.d, "saved.txt")
        code, out = run(["diffout", self.old, new, "--save", saved])
        with open(saved, "rb") as fh:
            raw = fh.read().decode()
        self.assertIn("<scratch>", raw)
        self.assertNotIn(scratch, raw)
        self.assertNotIn(scratch.replace(BACKSLASH, BACKSLASH * 2), raw)
        code, out = run(["diffout", self.old, new, "--save", saved, "--keep-paths"])
        with open(saved, "rb") as fh:
            self.assertIn(exe, fh.read().decode())

    def test_prints_any_character_on_a_legacy_console(self):
        # A C1 character and an arrow crashed diffout on cp1252 (L-119).
        with open(self.new, "wb") as fh:
            fh.write("## api\n\u0085 → 漢\n".encode("utf-8"))
        script = os.path.join(HERE, "..", "skills", "wikiwright", "scripts", "wikiwright.py")
        env = dict(os.environ, PYTHONIOENCODING="cp1252")
        p = subprocess.run([sys.executable, script, "diffout", self.old, self.new], capture_output=True, env=env)
        self.assertEqual(p.returncode, 1, p.stderr)
        self.assertNotIn(b"Traceback", p.stderr)
        self.assertIn("→".encode("utf-8"), p.stdout)


NODE24_OUT = "## installed\nwidget@1.2.0 on Node v24.18.0\n\n## proxy\nNODE_USE_ENV_PROXY=1\n\n## api\ntrue\n"
NODE20_OUT = "## installed\nwidget@1.2.0 on Node v20.20.2\n\n## proxy\nundici preloaded\n\n## api\ntrue\n"
SCOPED_PAGE = ("Answer:\n\n```text\ntrue\n```\n\nOn Node 22 and later:\n\n<!-- outputs: node>=22 -->\n```text\n"
               "NODE_USE_ENV_PROXY=1\n```\n\nOn Node 20:\n\n<!-- outputs: check node<22 (Node 20 only) -->\n"
               "```\nundici preloaded\n```\n")


class OutputsNodeScopeTests(unittest.TestCase):
    """<!-- outputs: node>=22 --> checks a block only against outputs from that Node line (L-119)."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        write(self.d, {"Home.md": SCOPED_PAGE})
        self.o24, self.o20 = os.path.join(self.d, "o24.txt"), os.path.join(self.d, "o20.txt")
        write(self.d, {"o24.txt": NODE24_OUT, "o20.txt": NODE20_OUT})

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_each_output_alone_skips_the_other_lines_blocks(self):
        code, out = run(["outputs", self.d, self.o20])
        self.assertEqual(code, 0, out)
        self.assertIn("2 outputs checked, 0 missing, 1 skipped", out)
        self.assertIn("node>=22, and no output given is from that Node", out)
        code, out = run(["outputs", self.d, self.o24])
        self.assertIn("2 outputs checked, 0 missing, 1 skipped", out)

    def test_both_outputs_check_every_block_against_its_own_line(self):
        code, out = run(["outputs", self.d, self.o24, self.o20])
        self.assertEqual(code, 0, out)
        self.assertIn("3 outputs checked, 0 missing, 0 skipped", out)
        # A Node 20 line shown as Node 22 and later is missing, though the Node 20 output prints it.
        write(self.d, {"Home.md": SCOPED_PAGE.replace("NODE_USE_ENV_PROXY=1\n", "undici preloaded\n")})
        code, out = run(["outputs", self.d, self.o24, self.o20])
        self.assertEqual(code, 1, out)
        self.assertIn("1 missing", out)

    def test_node_flag_overrides_the_installed_line(self):
        code, out = run(["outputs", self.d, self.o20, "--node", "24"])
        self.assertIn("1 missing", out)


TEMPLATES = os.path.join(HERE, "..", "skills", "wikiwright", "templates", "npm")


class TemplateTests(unittest.TestCase):
    """Regressions in the npm template and the host-fixture kit (tests/host-fixture.test.mjs runs the kit)."""

    def read(self, name):
        with open(os.path.join(TEMPLATES, name), encoding="utf-8") as fh:
            return fh.read()

    def test_oldest_node_runs_a_folder_holding_only_node(self):
        # L-118: Git Bash skips the npm node package's bin folder, which also holds a text file named `node`.
        text = self.read("wiki-verify.template.mjs")
        block = text[text.index("if (OLDEST_NODE && !WIKI_VERIFY_CHILD)"):]
        self.assertIn("copyFileSync(", block)
        self.assertIn("PATH: `${alone}${path.delimiter}", block)
        self.assertIn('echo "shell node: $(node --version)"', text)

    def test_by_host_name_imports_the_kit(self):
        text = self.read("wiki-verify.template.mjs")
        self.assertIn("import('./host-fixture.mjs')", text)
        self.assertNotIn("openssl", text.lower().split("by host name")[1].split("----- the cases")[0].replace(
            "host-fixture.mjs", ""))

    def test_golden_views_and_cli_environment(self):
        # L-129: the golden replay counts answers, timing and requests apart; the CLI reaches the kit.
        text = self.read("wiki-verify.template.mjs")
        for view in ("answers:", "timing:", "requests:"):
            self.assertIn(view, text)
        self.assertIn("{cwd, env: {...process.env, ...CLI_ENV, ...env}}", text)
        self.assertIn("CLI_ENV = fx.env;", text)
        kit = self.read("host-fixture.mjs")
        self.assertIn("runtimeEnv", kit)
        self.assertIn("await dispatcher?.close();", kit)

    def test_files_on_disk_import_the_tree_kit(self):
        # L-130: a package that writes files runs each case in a fresh scratch tree; cli() takes a cwd.
        text = self.read("wiki-verify.template.mjs")
        self.assertIn("import('./file-tree.mjs')", text)
        self.assertIn("typeof args.at(-1) === 'object' ? args.pop() : {}", text)
        kit = self.read("file-tree.mjs")
        for name in ("export async function treeCase", "export function describeBytes", "export function showBytes"):
            self.assertIn(name, kit)
        self.assertNotIn("\uFEFF", kit)

    def test_grader_sees_a_recorder_that_names_no_host(self):
        # L-122: a fetch wrapper that passes requests through, then run, is a request to the real service.
        spec = importlib.util.spec_from_file_location(
            "grade_action", os.path.join(HERE, "..", "evals", "grade-action.py"))
        grade = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(grade)
        recorder = ("const original = fetch;\nglobalThis.fetch = async (input, init) => {\n"
                    "  const response = await original(input, init);\n  return response;\n};\n")
        router = ("const original = fetch;\nglobalThis.fetch = (input, init) => original(\n"
                  "  process.env.FIXTURE_BASE + new URL(input).pathname, init);\n")
        uses = [
            (1, "Write", {"file_path": "C:/s/record-live.mjs", "content": recorder}),
            (2, "Write", {"file_path": "C:/s/route.mjs", "content": router}),
            (3, "Write", {"file_path": "C:/s/unused.mjs", "content": recorder}),
            (4, "Bash", {"command": "node --import ./route.mjs verify.mjs"}),
            (5, "Bash", {"command": "node record-live.mjs question scifi 1"}),
        ]
        found = grade.live_requests(uses, "api.example.com")
        self.assertEqual(len(found), 1, found)
        self.assertTrue(found[0].startswith("unrouted fetch wrapper record-live.mjs"), found)
        self.assertEqual(grade.live_requests(uses[1:2] + uses[3:4], "api.example.com"), [])
        # --digest: one line per call worth reading, the recorder marked.
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            grade.digest(tempfile.gettempdir(), uses + [(6, "Bash", {"command": "curl https://api.example.com/x"})])
        out = buf.getvalue()
        self.assertIn("[outside fetch-wrapper UNROUTED] C:/s/record-live.mjs", out)
        self.assertIn("[outside fetch-wrapper] C:/s/route.mjs", out)
        self.assertIn("[fetcher url:api.example.com] curl", out)
        self.assertIn("tools: Bash 3, Write 3", out)
        # Saved outputs a program wrote count as evidence; a file the agent typed with Write does not.
        run = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(run, "work", "v"))
            for name in ("wiki-verify.out.txt", "typed.out.txt", "notes.txt"):
                with open(os.path.join(run, "work", "v", name), "w") as fh:
                    fh.write("x")
            typed = [(1, "Write", {"file_path": os.path.join(run, "work", "v", "typed.out.txt"), "content": "x"})]
            self.assertEqual([os.path.basename(p) for p in grade.saved_outputs(run, typed)], ["wiki-verify.out.txt"])
        finally:
            rmtree(run)

    def test_kit_guard_reads_the_normalised_array(self):
        # L-117: net.connect() passes [options, callback] as one argument.
        self.assertIn("Array.isArray(args[0]) ? args[0][0] : args[0]", self.read("host-fixture.mjs"))


def rmtree(d):
    # git writes its objects read-only, which Windows refuses to delete.
    def writable(fn, path, _):
        os.chmod(path, 0o700)
        fn(path)
    shutil.rmtree(d, onerror=writable)


def git(*args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false",
                           "-c", "tag.gpgsign=false", "-c", "core.autocrlf=false"] + list(args),
                          capture_output=True, text=True, check=True)


def plugin_tree(root, version, tests=("T-20260101-1",), changelog_version=None):
    skill = os.path.join(root, "skills", "wikiwright")
    os.makedirs(os.path.join(skill, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(root, ".claude-plugin"), exist_ok=True)
    files = {
        os.path.join(root, ".claude-plugin", "plugin.json"): '{"name": "wikiwright", "version": "%s"}\n' % version,
        os.path.join(skill, "evergreen.json"): '{"name": "wikiwright", "version": "%s"}\n' % version,
        os.path.join(skill, "scripts", "wikiwright.py"): 'VERSION = "%s"\n' % version,
        os.path.join(skill, "SKILL.md"): '---\nname: wikiwright\nmetadata:\n  version: "%s"\n---\n\n# wikiwright\n' % version,
        os.path.join(skill, "CHANGELOG.md"): "# Changelog\n\n### C-20260101-1 · 2026-01-01 · %s: things\n" % (
            changelog_version or version),
        os.path.join(skill, "TESTS.md"): "# Tests\n\n" + "".join("### %s · 2026-01-01 · x\n" % t for t in tests),
    }
    for path, text in files.items():
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)


class CacheCheckTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.src, self.cache = os.path.join(self.d, "src"), os.path.join(self.d, "cache")
        plugin_tree(self.src, "0.1.0")
        shutil.copytree(self.src, self.cache)

    def tearDown(self):
        rmtree(self.d)

    def test_equal_cache_passes(self):
        code, out = run(["cachecheck", "--source", self.src, "--cache", self.cache])
        self.assertEqual(code, 0, out)
        self.assertIn("6 files, 6 equal, 0 differ, 0 missing, 0 only in the cache", out)

    def test_stale_missing_and_extra_files_fail(self):
        with open(os.path.join(self.src, "skills", "wikiwright", "SKILL.md"), "a") as fh:
            fh.write("new line\n")
        os.remove(os.path.join(self.cache, ".claude-plugin", "plugin.json"))
        with open(os.path.join(self.cache, "skills", "wikiwright", "old.md"), "w") as fh:
            fh.write("gone from the source\n")
        os.makedirs(os.path.join(self.cache, "skills", "wikiwright", "scripts", "__pycache__"))
        code, out = run(["cachecheck", "--source", self.src, "--cache", self.cache])
        self.assertEqual(code, 1, out)
        self.assertIn("differs: skills/wikiwright/SKILL.md", out)
        self.assertIn("missing from the cache: .claude-plugin/plugin.json", out)
        self.assertIn("only in the cache: skills/wikiwright/old.md", out)
        self.assertIn("reinstall", out)

    def test_git_source_compares_tracked_files_only(self):
        git("init", "-q", self.src)
        git("-C", self.src, "add", "-A")
        with open(os.path.join(self.src, "skills", "wikiwright", "package.json"), "w") as fh:
            fh.write("{}\n")  # an eval run's stray file (L-017): untracked, so not compared
        code, out = run(["cachecheck", "--source", self.src, "--cache", self.cache])
        self.assertEqual(code, 0, out)


class ReleaseCheckTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        plugin_tree(self.d, "0.1.0")
        git("init", "-q", self.d)
        git("-C", self.d, "add", "-A")
        git("-C", self.d, "commit", "-q", "-m", "0.1.0")
        git("-C", self.d, "tag", "v0.1.0")

    def tearDown(self):
        rmtree(self.d)

    def test_ready_after_bump_entry_and_run(self):
        plugin_tree(self.d, "0.2.0", tests=("T-20260101-1", "T-20260102-1"))
        code, out = run(["releasecheck", "0.2.0", "--root", self.d])
        self.assertEqual(code, 0, out)
        self.assertIn("TESTS run since v0.1.0: T-20260102-1", out)
        self.assertIn("releasecheck 0.2.0: ready to tag", out)

    def test_missing_run_entry_and_field(self):
        plugin_tree(self.d, "0.2.0", changelog_version="0.1.9")
        with open(os.path.join(self.d, "skills", "wikiwright", "scripts", "wikiwright.py"), "w") as fh:
            fh.write('VERSION = "0.1.0"\n')
        code, out = run(["releasecheck", "0.2.0", "--root", self.d])
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL wikiwright.py VERSION: 0.1.0", out)
        self.assertIn("FAIL CHANGELOG entry naming 0.2.0", out)
        self.assertIn("FAIL TESTS run since v0.1.0: none", out)
        self.assertIn("3 problem(s)", out)

    def test_existing_tag_fails(self):
        code, out = run(["releasecheck", "0.1.0", "--root", self.d])
        self.assertIn("FAIL tag v0.1.0 exists already", out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
