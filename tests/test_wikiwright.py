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


if __name__ == "__main__":
    unittest.main(verbosity=1)
