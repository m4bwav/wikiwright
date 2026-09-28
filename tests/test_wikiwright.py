"""Tests for skills/wikiwright/scripts/wikiwright.py (check, unbs, slug).

Run from the repository root: python tests/test_wikiwright.py
The network subcommands (preflight, live) are exercised by the eval suite.
"""

import contextlib
import io
import os
import shutil
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

    def test_other_hosts_stop_with_a_clear_state(self):
        for url, name in (("https://gitlab.com/a/b", "GitLab"), ("https://codeberg.org/a/b", "Gitea or Forgejo"),
                          ("https://dev.azure.com/o/p/_git/r", "Azure DevOps"), ("https://git.example.org/a/b", "unknown host")):
            code, out = run(["preflight", url])
            self.assertEqual(code, 2, url)
            self.assertIn("STATE: other-host", out)
            self.assertIn(name, out)
            self.assertIn("references/hosts.md", out)


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


if __name__ == "__main__":
    unittest.main(verbosity=1)
