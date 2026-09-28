---
title: GitHub wiki written and published for {{VERSION}}
kind: note
date: {{DATE}}
verified: {{DATE}}
stale_after: {{DATE_PLUS_6_MONTHS}}
tags: [wiki, docs, {{VERSION}}, github]
summary: "the wiki's pages, where their git working copy is, how every example was verified against the published {{VERSION}} package, the facts found on the way, the inaccuracies in the shipped docs, and how to update the wiki; read before touching the wiki or the README sentences listed under inaccuracies"
---

# GitHub wiki for {{VERSION}}

## Summary

What was asked, what was written (page count), what it was written from, how the examples were verified, the wiki commit, and the result of the live check and the prose checker.

Pages: ...

## Where the pages are

`{{WIKI_DIR}}` (a sibling of this clone, outside this repository), branch `master`, remote `origin` = `https://github.com/{{OWNER}}/{{REPO}}.wiki.git`. Files: ... Plain markdown links between pages (`[Recipes](Recipes)`), no wikilinks, LF line endings.

## How it was published

Preflight state (feature-off, no-wiki-repo, placeholder or has-pages), what was done about it, the push (plain or over the placeholder), the wiki commit, and `wikiwright.py live` output in one line.

## Updating the wiki later

1. `git -C {{WIKI_DIR}} pull --ff-only`, then edit the pages. Page names are the file names with hyphens; links are `[Text](Page-Name)`.
2. Re-verify: bump the version in `{{VERIFY_FILE}}` (next to this note), run it from a scratch folder outside the repository ({{VERIFY_COMMAND}}, with every folder or variable the old-version and runtime sections need), and save its output. Replace `127.0.0.1:<digits>` with `127.0.0.1:<port>` and diff it with `{{VERIFY_OUT}}` beside this note: every difference is a page to fix. Save the new output over it.
3. `python <wikiwright>/scripts/wikiwright.py outputs {{WIKI_DIR}} <new output>` (every page output must be in it), then `wikiwright.py check {{WIKI_DIR}} --version <new>` and the everwrite checker.
4. Commit, `git push`, then `wikiwright.py live {{OWNER}}/{{REPO}} {{WIKI_DIR}}`. When a release changes the version, the pages that name it are: ...

## How the examples were verified

The script and its saved output, the package version it installed, the runtimes, package managers and hosts run, the old versions installed and any golden capture replayed (cases identical, cases differing), and what was not run (marked "not tested" on the pages). The `wikiwright.py outputs` line. The repository's own tests, when run, with their counts.

## Facts verified while writing (not in the README)

- ...

## Inaccuracies found in the shipped docs

Numbered; each with where it is (README, CHANGELOG, XML docs, package metadata), what it says, what is true, the evidence, and whether it is fixed or waits for the next release (a README inside the package reaches the registry page only with a release).

1. ...

## Gotchas

- ...

Related: see also [../HANDOFF.md](../HANDOFF.md), [../log.md](../log.md).
