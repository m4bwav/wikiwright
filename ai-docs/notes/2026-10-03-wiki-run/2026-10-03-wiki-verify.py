"""Runs every example on the wikiwright wiki against a fresh clone of github.com/m4bwav/wikiwright.

Usage: python 2026-10-03-wiki-verify.py CLONE_DIR [PYTHON]
CLONE_DIR is a fresh `git clone https://github.com/m4bwav/wikiwright.git` at origin/master, never a working copy.
PYTHON (optional) is the interpreter that stands in for `python` in every command (to run on 3.9).
Each case makes a new scratch folder, clones CLONE_DIR into <scratch>/wikiwright, writes the case's files there,
then runs each command through bash with stdin closed, printing `$ command`, its output with stderr merged,
and the exit code when the case asks for `echo $?`. The clone's path prints as <clone>.
The registry, preflight and live cases read npmjs.org, nuget.org and github.com; nothing is written there.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CLONE = Path(sys.argv[1]).resolve()
PY = sys.argv[2] if len(sys.argv) > 2 else None
BASH = shutil.which("bash") or "C:/Program Files/Git/bin/bash.exe"
CR = chr(13)
PH = "<" + "BS" + ">"

# ---------------------------------------------------------------- fixtures

DRAFT_HOME = """\
# Home

Widget 1.2.0 sorts words. Read [[Getting Started]] first.

See [the API](API-Reference.md), [Recipes](Recipes) and [the options](Getting-Started#options).

## Sorting Words Quickly
"""

DRAFT_START = "Install it with pip." + CR + "\n"

PARTIAL_HOME = """\
Widget 1.2.0 sorts words. See [Recipes](Recipes).
"""

PARTIAL_RECIPES = """\
Sort a list with `sorted()`.
"""

SORT_PAGE = """\
Widget sorts words.

```python
words = ["pear", "fig", "apple"]
print(sorted(words))
```

It prints:

```text
['apple', 'fig', 'pear']
```

Install it first.

```sh
pip install widget
```
"""

SORT_PAGE_CHANGED = """\
Widget sorts words.

```python
words = ["pear", "fig", "apple"]
print(sorted(words, reverse=True))
```

It prints:

```text
['pear', 'fig', 'apple']
```
"""

CODE_ONLY_PAGE = """\
Widget sorts words.

```python
print(sorted(["pear", "fig", "apple"]))
```
"""

ADDRESS_PAGE = """\
Fetching the page prints:

```text
https://example.com/ answered 200
```
"""

SORT_OUT = """\
## home-sort
['apple', 'fig', 'pear']
"""

ADDRESS_OUT = """\
## fetch
http://127.0.0.1:4321/ answered 200
"""

SORT_PROGRAM = """\
# wiki-verify.py: runs every example on the pages
words = ["pear", "fig", "apple"]
print(sorted(words))
"""

SIDEBAR = "[Home](Home)\n"
FOOTER = "This wiki describes widget 1.2.0 and was last updated on 2026-10-03.\n"
FOOTER_NO_DATE = "This wiki describes widget 1.2.0.\n"

OLD_OUT = """\
## installed
Python 3.9.25
## home-sort
['apple', 'fig', 'pear']
## server
listening on 127.0.0.1:50123
"""

NEW_OUT = """\
## installed
Python 3.14.6
## home-sort
['apple', 'fig', 'pear']
## server
listening on 127.0.0.1:61007
## home-reverse
['pear', 'fig', 'apple']
"""

REGEX_PAGE = "Match digits with `" + PH + "d+`.\n"

GATE = """\
#!/bin/sh
# check-wiki.sh: the three offline gates on a wiki working copy, stopping at the first that fails
W=skills/wikiwright/scripts/wikiwright.py
WIKI=$1
python "$W" check "$WIKI" --version "$2" &&
python "$W" outputs "$WIKI" notes/wiki-verify.out.txt &&
python "$W" snippets "$WIKI" notes/wiki-verify.py
"""

GATE_FILES = {"check-wiki.sh": GATE, "wiki/Home.md": "Widget 1.2.0.\n\n" + SORT_PAGE, "wiki/_Sidebar.md": SIDEBAR,
              "wiki/_Footer.md": FOOTER, "notes/wiki-verify.out.txt": SORT_OUT, "notes/wiki-verify.py": SORT_PROGRAM}

W = "python skills/wikiwright/scripts/wikiwright.py"

CASES = [
    # ---- Home and Getting started
    ("home-check", {}, [
        W + " check tests/fixtures/good-wiki --version 1.2.0",
        "echo $?"]),
    ("start-version", {}, [W + " --version"]),
    # ---- Commands: the program
    ("cmd-help", {}, [W + " --help"]),
    ("cmd-no-command", {}, [W, "echo $?"]),
    ("cmd-unknown-command", {}, [W + " publish", "echo $?"]),
    ("cmd-streams", {}, [
        W + " publish 2>/dev/null",
        "echo $?",
        W + " check nowhere 2>/dev/null",
        "echo $?"]),
    # ---- check
    ("check-draft", {"draft-wiki/Home.md": DRAFT_HOME, "draft-wiki/Getting-Started.md": DRAFT_START,
                     "draft-wiki/_Sidebar.md": SIDEBAR, "draft-wiki/_Footer.md": FOOTER_NO_DATE}, [
        W + " check draft-wiki --version 1.2.0",
        "echo $?"]),
    ("check-partial", {"draft/Home.md": PARTIAL_HOME, "draft/Recipes.md": PARTIAL_RECIPES}, [
        W + " check draft",
        W + " check draft --partial",
        "echo $?"]),
    ("check-version", {}, [
        W + " check tests/fixtures/good-wiki --version 1.3.0",
        "echo $?"]),
    ("check-host", {}, [
        W + " check tests/fixtures/good-wiki --host gitlab",
        W + " check tests/fixtures/good-wiki --host forgejo"]),
    ("check-not-a-folder", {}, [W + " check nowhere", "echo $?"]),
    # ---- outputs
    ("outputs-pass", {"pages/Home.md": SORT_PAGE, "wiki-verify.out.txt": SORT_OUT}, [
        W + " outputs pages wiki-verify.out.txt",
        "echo $?"]),
    ("outputs-missing", {"pages/Home.md": SORT_PAGE_CHANGED, "wiki-verify.out.txt": SORT_OUT}, [
        W + " outputs pages wiki-verify.out.txt",
        "echo $?"]),
    ("outputs-none-read", {"pages/Home.md": CODE_ONLY_PAGE, "wiki-verify.out.txt": SORT_OUT}, [
        W + " outputs pages wiki-verify.out.txt",
        "echo $?"]),
    ("outputs-address", {"pages/Fetch.md": ADDRESS_PAGE, "wiki-verify.out.txt": ADDRESS_OUT}, [
        W + " outputs pages wiki-verify.out.txt",
        W + " outputs pages wiki-verify.out.txt --address ''",
        "echo $?"]),
    # ---- snippets
    ("snippets-pass", {"pages/Home.md": SORT_PAGE, "wiki-verify.py": SORT_PROGRAM}, [
        W + " snippets pages wiki-verify.py",
        "echo $?"]),
    ("snippets-missing", {"pages/Home.md": SORT_PAGE_CHANGED, "wiki-verify.py": SORT_PROGRAM}, [
        W + " snippets pages wiki-verify.py",
        "echo $?"]),
    # ---- unbs
    ("unbs", {"pages/Regex.md": REGEX_PAGE}, [
        W + " unbs pages/Regex.md",
        "cat pages/Regex.md"]),
    # ---- diffout
    ("diffout", {"old.txt": OLD_OUT, "new.txt": NEW_OUT}, [
        W + " diffout old.txt new.txt",
        "echo $?",
        W + " diffout old.txt new.txt --skip installed --save saved.txt",
        "cat saved.txt"]),
    # ---- scaffold
    ("scaffold-npm", {}, [
        W + " scaffold npm get-title-at-url 3.0.0 --bin -o verify/wiki-verify.mjs",
        "ls verify",
        W + " scaffold npm get-title-at-url 3.0.0 --bin -o verify/wiki-verify.mjs",
        "echo $?"]),
    ("scaffold-nuget", {}, [
        W + " scaffold nuget RandomNameGeneratorLibrary 2.3.0 --namespace RandomNameGeneratorLibrary"
            " --type PersonNameGenerator --children net48 -o verify/wiki-verify.cs"]),
    ("scaffold-wrong-flag", {}, [
        W + " scaffold npm get-title-at-url 3.0.0 --fsharp",
        "echo $?"]),
    # ---- registry (network: npmjs.org and nuget.org)
    ("registry-npm", {}, [W + " registry get-title-at-url --limit 3"]),
    ("registry-nuget", {}, [W + " registry RandomNameGeneratorLibrary --limit 3 --no-nupkg"]),
    # ---- preflight and live (network: github.com, read only)
    ("preflight-and-live", {}, [
        W + " preflight m4bwav/everwrite",
        W + " preflight m4bwav/everwrite --clone everwrite.wiki",
        W + " live m4bwav/everwrite everwrite.wiki",
        "echo $?"]),
    ("preflight-not-a-repo", {}, [W + " preflight nowhere", "echo $?"]),
    # ---- releasecheck and cachecheck
    ("releasecheck", {}, [
        W + " releasecheck 0.9.0",
        "echo $?",
        W + " releasecheck 1.0.0"]),
    ("cachecheck", {}, [
        "mkdir cache && cp -r .claude-plugin skills cache/",
        "echo changed >> cache/skills/wikiwright/SKILL.md",
        W + " cachecheck --cache cache",
        "echo $?"]),
    # ---- Recipes
    ("recipe-gate", GATE_FILES, [
        "sh check-wiki.sh wiki 1.2.0",
        "echo $?",
        "sh check-wiki.sh wiki 1.3.0",
        "echo $?"]),
    # ---- Development
    ("dev-tests", {}, [
        "python tests/test_wikiwright.py 2>&1 | tail -3",
        "node --test tests/host-fixture.test.mjs tests/file-tree.test.mjs tests/snippet.test.mjs"
        " | grep -E ' (tests|pass|fail|skipped) [0-9]'"]),
]


def run_case(label, files, commands):
    print("## %s" % label)
    work = Path(tempfile.mkdtemp(prefix="ww-"))
    clone = work / "wikiwright"
    try:
        subprocess.run(["git", "clone", "-q", str(CLONE), str(clone)], check=True)
        for name, text in files.items():
            path = clone / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))
        env = dict(os.environ, PYTHONUTF8="1")
        if PY:
            env["PATH"] = str(Path(PY).parent) + os.pathsep + env["PATH"]
        rc = 0
        masks = sorted({str(clone), clone.as_posix(), str(clone.resolve()), clone.resolve().as_posix()}, key=len,
                       reverse=True)
        for line in commands:
            print("$ " + line)
            if line == "echo $?":
                print(rc)
                continue
            p = subprocess.run([BASH, "-c", "{ " + line + "; } 2>&1"], cwd=clone, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE)
            out = p.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
            for m in masks:
                out = out.replace(m, "<clone>")
            sys.stdout.write(out)
            rc = p.returncode
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    print("## installed")
    print("clone: %s" % subprocess.run(["git", "-C", str(CLONE), "log", "--format=%h %ad", "--date=short", "-1"],
                                         stdout=subprocess.PIPE).stdout.decode().strip())
    for tool in ([PY or "python", "--version"], ["git", "--version"], ["gh", "--version"], ["node", "--version"]):
        v = subprocess.run(tool, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(v.stdout.decode().strip().split("\n")[0])
    for case in CASES:
        run_case(*case)


main()
