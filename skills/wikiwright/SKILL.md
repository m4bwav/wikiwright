---
name: wikiwright
description: "Write or update a repository's GitHub wiki from the repository and its registry: survey the README, changelog, source, tests, issues and registry data, verify every example against the published package (npm or NuGet), write the page set for the repository's kind (Home, Getting started, API reference, behaviour, errors, Recipes, Commands, Versions and upgrading, FAQ, Development) with a sidebar and footer, push the .wiki.git repository and check every page is live. Use whenever the user asks to write, fill out, generate, create or update a wiki for a repo or package ('write a wiki for this repo', 'fill out the GitHub wiki', 'update the wiki for 2.4.0', 'wiki pages for my library', 'the wiki is empty'), or a package-modernize run reaches its wiki step. Also for 'refresh wikiwright' and 'is wikiwright stale'. Not for the README alone, a docs site (GitHub Pages, Docusaurus), an Obsidian vault (obsidian-notes) or ai-docs (everlast)."
metadata:
  version: "0.1.0"
---

# wikiwright

Writes a GitHub wiki that says what the README cannot: the exact behaviour, every error, recipes, the upgrade path from each old version, answers to the questions people ask, and how the project is built, with every example's output produced by the published package. Then it publishes the wiki and records how to update it at the next release. Built from three runs: RandomNameGeneratorLibrary and JsonPrettyPrinter (NuGet) and get-title-at-url (npm with a CLI), all on 2026-09-28.

`WW` below means `python "<this folder>/scripts/wikiwright.py"` (`python3` on macOS and Linux; standard library only).

## Step 0: freshness and the overlay

Read `evergreen.json` next to this file. If `contradiction` is set or today is on or after `next_due`, say so in one line, do the task, then refresh (`evergreen-refresh`) in the same session. If `tests.failing` is non-empty, say so in one line and run `evergreen-tune` after the task.

Then look for the maintainer's private overlay: the file named by `WIKIWRIGHT_OVERLAY`, else `~/.wikiwright/OVERLAY.md` (open it with the Read tool at its full path; the folder is often a junction, which globbing skips). It holds identities, where clones live and a list of wikis done and owed; it wins over the defaults here. Without one, the defaults stand.

## Two modes

A new wiki, where the repository has none or only GitHub's placeholder, takes Steps 1 to 8. An update for a release ("update the wiki for 2.4.0"), where the wiki exists and the repository's `ai-docs/notes/*-github-wiki.md` says how it was made, follows "Update mode" below.

## Step 1: preflight (first, before any writing)

```
WW preflight OWNER/REPO --enable --clone <clone>.wiki
```

`<clone>.wiki` is a sibling of the repository's clone (`D:\code\widget` gets `D:\code\widget.wiki`). The states and what each needs are in [references/publishing.md](references/publishing.md). The one that needs a person: `no-wiki-repo`. GitHub creates the wiki repository only when someone saves a first page in the web UI, and no API can do it. Ask the maintainer for that click **in your first message**, give them the `/wiki/_new` URL, and carry on with Steps 2 to 6 while they do it; run preflight again before Step 7. `has-pages` means someone wrote pages already: read them all and update in place.

## Step 2: survey

Read, in the clone: README, CHANGELOG, AGENTS.md and CLAUDE.md, `ai-docs/` (HANDOFF, notes, decisions, plans), every source file of the public surface, the tests (they state the behaviour precisely), the CI workflows (the matrix is the support claim), `package.json` or the project file. From GitHub: releases and tags (`gh release list`, `git tag`), issues and pull requests open and closed (`gh issue list --state all`, `gh pr list --state all`): the questions people asked become FAQ entries. From the registry: versions with dates, downloads, the published package's files and metadata, its dependency tree. The commands per registry are in [references/npm.md](references/npm.md) and [references/nuget.md](references/nuget.md). Read the published package itself, since it can differ from the repository.

Keep a running list of two things from here to the end, because they are half of what the run is worth: **facts the README does not state**, and **places where the shipped docs are wrong** (both earlier runs found several: a README claim about comments that the printer breaks, a changelog escape that System.Text.Json never writes, a thread-safety sentence true on one runtime only).

## Step 3: choose the page set

Pick the set for the repository's kind from [references/page-sets.md](references/page-sets.md): a library, a library with a command line (adds Commands), or a command-line tool. Name the behaviour page after what the package does (`Output-Format`, `How-Titles-Are-Chosen`). Add a performance or data-source page only when there is a benchmark or embedded data to describe. An application, a monorepo or a non-GitHub host has no tested set yet: say so, use the fallback there and record the lessons.

## Step 4: verify every example against the published package

Before an example goes on a page, run it against the **published** version, installed from the registry into a scratch folder outside the repository, never against the working tree (the wiki documents what users install, and the tree may be ahead). Templates: [templates/npm/wiki-verify.template.mjs](templates/npm/wiki-verify.template.mjs) (ESM, CommonJS, the bin, a local fixture server) and [templates/nuget/wiki-verify.template.cs](templates/nuget/wiki-verify.template.cs) (a .NET 10 file-based app; `#:property PublishAot=false` is required, see the reference). Each example is one labelled case; paste outputs exactly as printed.

- A package that makes requests is verified against a local fixture server, never the internet, as its own tests are.
- Every runtime, language or host the pages show (F#, PowerShell, Deno, Bun, .NET Framework) is run or marked "not tested" on the page.
- Print each output in the form the page shows it: a page that shows `console.log` output needs the script to print with `console.log`, not JSON (L-008 `print-as-the-page-shows`).
- For Versions and upgrading, install each old major in its own scratch folder and run the same fixture cases against it, unless a golden capture of it already exists (L-011 `run-the-old-majors`). A version that no longer installs or imports is a finding.
- Save the filled-in script in the repository as `ai-docs/notes/<date>-wiki-verify.<ext>` so the next release can run it again.
- Run the repository's own tests once too; the counts go in the note.

## Step 5: write the pages

Conventions (full list in [references/page-sets.md](references/page-sets.md)):

- File names hyphenated with a capital per word (`Getting-Started.md`).
- Sentence-case headings.
- Links as `[Recipes](Recipes)`: no wikilinks, no `.md`.
- Input and output in paired code blocks, with real output only.
- The version that introduced each member in the API reference.
- "Not tested" where nothing ran.
- LF line endings.
- No AI attribution in pages or commits.

Start the sidebar and footer from [templates/pages/](templates/pages/); the footer names the version and today's date. Write prose with the everwrite skill when it is installed: every page is read by people.

Say on each page only what the survey or the verification showed, and put the facts the README lacks where a reader looks for them: edge cases and errors on their page, questions from issues in the FAQ, the upgrade path in Versions and upgrading.

**Backslashes.** Some agent file-writing tools decode `\u` escapes and shell heredocs drop backslashes (L-001 `backslash-placeholder`). Write every backslash in a page as `<BS>` when it would otherwise be mangled (regular expressions, Windows paths, JSON escapes), then run `WW unbs <files>`. `WW check` fails while any `<BS>` remains.

## Step 6: check

First reread every page once with one question per sentence: which script output, source line, changelog entry or registry answer says this? Cut or rewrite every sentence with no answer. The first npm run caught three inferred claims this way (L-009 `claims-audit`).

```
WW check <wiki dir> --version X
python <everwrite>/scripts/tells.py <wiki dir>/*.md
```

`check` must exit 0. It covers page links and anchors, wikilinks, CRLF, `<BS>` leftovers, sidebar and footer, unclosed fences and attribution. The prose checker must report 0 strong findings; judge weak ones (quoted error messages are fine).

## Step 7: publish

Run preflight again if it was `no-wiki-repo`. In the wiki working copy: commit (message names the version and the pages), then `git push`. Pages committed on top of the cloned placeholder make a plain fast-forward; `git push --force-with-lease origin master` is needed only when the working copy was started with `git init` instead of a clone (L-010 `placeholder-fast-forward`). Wiki repositories use `master`. Then:

```
WW live OWNER/REPO <wiki dir>
```

Every page must answer 200 (Home 301 to `/wiki`), and the sidebar and footer must render on the root. Rerun once after a few seconds before calling a failure.

## Step 8: record

In the repository, write `ai-docs/notes/<date>-github-wiki.md` from [templates/wiki-note.template.md](templates/wiki-note.template.md). It holds the pages, the working-copy path, how the wiki was published and how the examples were verified. It also lists the facts the README lacks, the numbered inaccuracies, and the update procedure with the pages that name the version. Add a line to `ai-docs/HANDOFF.md` and a log entry (everlast: `everlast.py` or `ai-docs/log.md`), then commit and push the repository. Leave the README and CHANGELOG as they are unless asked. They ship inside the package and reach the registry page only with a release, so list the inaccuracies for the maintainer; they get fixed on request or in the next release. When the overlay keeps a list of wikis, move this repository to done.

## Update mode

1. Read the repository's wiki note; `git -C <wiki dir> pull --ff-only`.
2. Read the CHANGELOG entries since the version the footer names; survey the new version on the registry.
3. Bump the version in the verification script, run it against the new published version, and diff its output with the previous run's; every difference is a page to fix.
4. Update the pages that name the version (the note lists them), Versions and upgrading, the API reference for new or changed members (with the new version as "introduced in"), and the footer's version and date.
5. Steps 6 to 8, with the note updated rather than replaced and a new log entry.

## Output

One message at the end: the wiki URL and commit, the page list, the live check line, the facts the README lacks (short), the inaccuracies found in the shipped docs (numbered, with where), and anything not tested. At a stop (the first-page click): what is needed, the URL, and what continues meanwhile.

## While working: capture learnings

If the user corrects you, the same error happens twice, a workaround is found, or an environment fact is discovered, write it to [LEARNINGS.md](LEARNINGS.md) now, and wherever an ID is cited add a two-to-four-word code name after it, for example L-001 `backslash-placeholder`. Check existing entries first: add, update, retire, or nothing. A lesson about a registry goes into its reference with the date. If a learning proves a claim above wrong, fix it here, log it in [CHANGELOG.md](CHANGELOG.md), and set `contradiction` in `evergreen.json`.

## Maintenance

This skill is evergreen (topic: GitHub wiki mechanics and writing library documentation whose examples are verified against the published package; tier `fast`, interval set by `evergreen.json`). Files: `evergreen.json` (state), [RESEARCH.md](RESEARCH.md) (findings and the four-track search plan), [CHANGELOG.md](CHANGELOG.md) (every change, with reasons), [LEARNINGS.md](LEARNINGS.md) (lessons, seeded from the first three wikis), [TESTS.md](TESTS.md) and `evals/evals.json` (the cases that prove it and the runs). Protocol: [MAINTENANCE.md](MAINTENANCE.md), a self-contained copy for machines without the evergreen plugin. Refresh with `evergreen-refresh`; test with `evergreen-test`; fix a failure with `evergreen-tune`. Each run of the skill is also a test of it: what it got wrong goes to LEARNINGS.md the same day.
