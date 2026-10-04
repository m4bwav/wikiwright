---
name: wikiwright
description: "Write or update a repository's GitHub wiki from the repository and its registry: survey the README, changelog, source, tests, issues and registry data, verify every example against the published package (npm or NuGet), write the page set for the repository's kind (Home, Getting started, API reference, behaviour, errors, Recipes, Commands, Versions and upgrading, FAQ, Development) with a sidebar and footer, push the .wiki.git repository and check every page is live. Use whenever the user asks to write, fill out, generate, create or update a wiki for a repo or package ('write a wiki for this repo', 'fill out the GitHub wiki', 'update the wiki for 2.4.0', 'wiki pages for my library', 'the wiki is empty'), or a package-modernize run reaches its wiki step. Also for 'refresh wikiwright' and 'is wikiwright stale'. Not for the README alone, a docs site (GitHub Pages, Docusaurus), an Obsidian vault (obsidian-notes) or ai-docs (everlast)."
metadata:
  version: "0.9.1"
---

# wikiwright

Writes a GitHub wiki that says what the README cannot: the exact behaviour, every error, recipes, the upgrade path from each old version, answers to the questions people ask, and how the project is built, with every example's output produced by the published package. Then it publishes the wiki and records how to update it at the next release. The runs it was built from are listed in [references/page-sets.md](references/page-sets.md).

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

`<clone>.wiki` is a sibling of the repository's clone (`D:\code\widget` gets `D:\code\widget.wiki`). OWNER/REPO may also be a remote URL or the clone's path. Run it even for a draft of one page, and even when the overlay lists the wiki as owed or done: the list is a record, ls-remote is the state (L-109 `record-is-not-state`). The states and what each needs are in [references/publishing.md](references/publishing.md). The one that needs a person: `no-wiki-repo`. GitHub creates the wiki repository only when someone saves a first page in the web UI; switching the feature on does not create it (tested 2026-09-28: still missing 61 seconds after `--enable`, present 11 seconds after the maintainer's save), and no API can. Ask the maintainer for that click **in your first message**, give them the `/wiki/_new` URL, and carry on with Steps 2 to 6 while they do it; run preflight again before Step 7. `has-pages` means someone wrote pages already: read them all and update in place. Gitea, Forgejo, GitLab and Azure DevOps remotes get their own preflight (measured 2026-09-29 without an account; no real wiki published there yet): on Gitea and Forgejo a push cannot create the wiki, so `--seed` with `WIKIWRIGHT_TOKEN` or the maintainer's first page does; on GitLab the first push does. Read [references/hosts.md](references/hosts.md) before writing, pass `--host KIND` to `check`, and tell the user what is still unverified there.

## Step 2: survey

Read, in the clone: README, CHANGELOG, AGENTS.md and CLAUDE.md, `ai-docs/` (HANDOFF, notes, decisions, plans), every source file of the public surface, the tests (they state the behaviour precisely), the CI workflows (the matrix is the support claim), `package.json` or the project file. From GitHub: releases and tags (`gh release list`, `git tag`), issues and pull requests open and closed (`gh issue list --state all`, `gh pr list --state all`): the questions people asked become FAQ entries. From the registry: versions with dates, downloads, the published package's files and metadata, its dependency tree. Start with `WW registry NAME` (one fact per line in place of the raw JSON); the other commands are in the registry's core reference, which every run reads: [references/npm.md](references/npm.md) or [references/nuget.md](references/nuget.md). Read the published package itself, since it can differ from the repository.

Keep a running list of two things from here to the end, because they are half of what the run is worth: **facts the README does not state**, and **places where the shipped docs are wrong** (both earlier runs found several: a README claim about comments that the printer breaks, a changelog escape that System.Text.Json never writes, a thread-safety sentence true on one runtime only). Docs written with agent tools can carry L-001's damage: format-json-files' README says `"é"` is written as `"é"`, where it meant the six-character escape; look for an example that says nothing because an escape was decoded.

## Step 3: choose the page set

Pick the set for the repository's kind from [references/page-sets.md](references/page-sets.md): a library (with or without a command line: a CLI adds Commands), a library whose output is seeded or deterministic (adds a reproducibility page), or a command-line tool. Add [references/page-sets-cli.md](references/page-sets-cli.md) for a command line, a command-line tool or files on disk, and [references/page-sets-seeded.md](references/page-sets-seeded.md) for seeded output. A repository that ships a library and its tool takes both sets in union, with the two-package footer and sidebar in page-sets.md. Name the behaviour page after what the package does (`Output-Format`, `How-Titles-Are-Chosen`). Add a performance or data-source page only when there is a benchmark or embedded data to describe. An application or a monorepo has no tested set yet: say so, use the fallback there and record the lessons. On another host the set stays; its navigation files and names change ([references/hosts.md](references/hosts.md), "Page sets on these hosts").

## Step 4: verify every example against the published package

Before an example goes on a page, run it against the **published** version, installed from the registry into a scratch folder outside the repository, never against the working tree (the wiki documents what users install, and the tree may be ahead). Templates: [templates/npm/wiki-verify.template.mjs](templates/npm/wiki-verify.template.mjs) (ESM, CommonJS, the bin, a local fixture server) and [templates/nuget/wiki-verify.template.cs](templates/nuget/wiki-verify.template.cs) (a .NET 10 file-based app; `#:property PublishAot=false` is required, see the reference). Start with the helper, never the template: `WW scaffold npm PACKAGE VERSION`, adding `--bin`, `--requests`, `--by-host`, `--files` or `--golden OLD_VERSION`, or `WW scaffold nuget ID VERSION --namespace NS --type T`, adding `--children net48,net8.0` (whole-program examples, other frameworks, the ends of a dependency range), `--requests`, `--fsharp` or `--tool ID:COMMAND`, for what the survey found. It writes the template filled in and cut to those sections. Open only the references the survey's traits call for: requests, [references/npm-requests.md](references/npm-requests.md) or [references/nuget-requests.md](references/nuget-requests.md); files written by an npm package, [references/npm-files.md](references/npm-files.md); an external program the package runs, media or other binary output, or files written by a NuGet package, [references/programs-and-media.md](references/programs-and-media.md); output that depends on time or on state that outlives a call (a cache, a static, a container), [references/time-and-state.md](references/time-and-state.md); golden captures, [references/golden-captures.md](references/golden-captures.md). Each example is one labelled case that holds the page's code as the page shows it and runs it (npm: `snippet()`); paste outputs exactly as printed.

- A package that makes requests is verified against a local fixture server, never the internet, as its own tests are. When it requests fixed hosts or the hosts its input names, serve the fixture under the real host names with [templates/npm/host-fixture.mjs](templates/npm/host-fixture.mjs) (a proxy with a throwaway CA; it guards every child against sockets that leave 127.0.0.1 and tests the guard first, L-116 `by-host-name-proxy`, L-117 `guard-normalised-args`), or with a `fetch` wrapper when only Node runs and the package calls the global `fetch` (read the repository's test helpers first). A .NET package uses the NuGet template's `requests` section (`scaffold nuget --requests`): a stand-in proxy answering `.test` names, and the `.invalid` gate on every framework (L-137 `dotnet-request-route`).
- A package that writes files is verified on a fresh scratch copy of a fixture tree per case, never on the repository or the user's files. [templates/npm/file-tree.mjs](templates/npm/file-tree.mjs) builds the copy, runs the case and prints each written file before and after, with the facts its text hides: BOM, line endings, final newline. Output that holds file paths is run on Linux too, and the pages show that run (L-132 `linux-run-for-paths`). On .NET there is no kit: copy the case's folders fresh and mask each case's folder as `<cwd>`.
- When the package's output is the remote content itself (a post's markdown, a page's title), the fixture's content is sample content: the page shows what the package printed for the local stand-in, says so next to the output, and links the real post for comparison. Never request the real service, not even once to record an answer for replay: a run cannot see the maintainer's quota or terms (L-122 `sample-content-not-live`).
- Every runtime, language, package manager or host the pages show (F#, PowerShell, Deno, Bun, pnpm, yarn, .NET Framework) is run or marked "not tested" on the page. Deno and Bun install from npm and corepack runs pnpm and yarn, so a machine without them can still run them ([references/npm.md](references/npm.md), L-021 `runtimes-from-npm`).
- Print each output in the form the page shows it: a page that shows `console.log` output needs the script to print with `console.log`, not JSON (L-008 `print-as-the-page-shows`).
- Run the npm script on the oldest Node line in `engines` too: `OLDEST_NODE=<exact version>` (20.20.2, pinned) in the template reruns it under that Node and saves its output (read its `installed` line and each shell case's `shell node:` line), and `WW diffout <main output> <oldest output>` lists the sections that differ. Scope each difference by version on the page (L-106 `oldest-node-run`, L-118 `oldest-node-path-trap`). Save both outputs. A line not run is "not tested" in the note.
- Snippets for another host on a page (PowerShell, F#, a shell loop, another runtime) are run from the script as written, as a child process, and their output printed; the NuGet template's `Run()` and the npm template's `run()` do this.
- An unseeded or random example cannot be printed again. Print it only after checking it is a possible answer (on the list its method draws from) and label the case so; a random line in a snippet's output becomes a stable placeholder after the same check (L-111 `membership-for-random`).
- For Versions and upgrading, install each old major in its own scratch folder and run the same fixture cases against it, unless a golden capture of it already exists (L-011 `run-the-old-majors`). A version that no longer installs or imports is a finding.
- Every output the pages show comes from this script, including ones shown in a different form (`console.log` layout, a REPL `//=>` line, headers as request lines): add a case that prints that form rather than converting by hand. Output that cannot come from it (npm's own install lines, with a timing) is marked on the page with `<!-- outputs: skip (reason) -->`.
- Save the filled-in script in the repository as `ai-docs/notes/<date>-wiki-verify.<ext>`, and its output beside it as `<date>-wiki-verify.out.txt` with the fixture port replaced by `<port>`, so the next release can run it again and diff.
- Seeded or deterministic output: run each example twice, and in each module system and runtime the pages name, and compare; the wiki can then promise the exact output. When the repository keeps golden captures of old versions (`test/golden/`, or a NuGet capture project in `tests/Golden/` run per framework), they feed Versions and upgrading: compare the old version run today with its capture, never trust either alone. Compare by parsed value, never bytes, with the header (`captured`, `node`) left out and `quirks` apart; a capture that makes requests runs as a child process, one version after the other (L-113 `replay-requesting-capture`; the rest is in [references/golden-captures.md](references/golden-captures.md)).
- Run the repository's own tests once too; the counts go in the note.

## Step 5: write the pages

Conventions (full list in [references/page-sets.md](references/page-sets.md)):

- File names hyphenated with a capital per word (`Getting-Started.md`).
- Sentence-case headings, and no first heading that repeats the page title: the host already prints the file name above the page (L-139 `title-printed-once`).
- Links as `[Recipes](Recipes)`: no wikilinks, no `.md`.
- Input and output in paired code blocks, with real output only. A value shown in a code comment is quoted (`// "Marguerita"`) or written `// => value`; a command right after a code block gets its fence tag (```sh), or `outputs` reads it as that block's output.
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
WW outputs <wiki dir> <the saved wiki-verify.out.txt> [--address '' when the pages show real host names]
WW snippets <wiki dir> <the saved wiki-verify program>
python <everwrite>/scripts/tells.py <wiki dir>/*.md
```

`check` must exit 0. It covers page links and anchors, wikilinks, CRLF, `<BS>` leftovers, sidebar and footer, unclosed fences and attribution (`--partial` for a draft of a few pages without sidebar and footer). `outputs` must exit 0: every block a page presents as output, and every `//=>` value, must be in the saved output; tag output fences `text`, since pages with code blocks and no output it recognises fail (L-136 `zero-checked-passes`). Give it the oldest Node's output too; a block true on some Node lines only gets `<!-- outputs: node>=22 -->` before it. How it tells output from input, and its other markers (`skip`, `check`), are in [references/page-sets.md](references/page-sets.md) ("How `wikiwright.py outputs` reads a page"); values in comments on NuGet pages, in [references/nuget.md](references/nuget.md) ("How the pages show output"). `snippets` must exit 0: every code block is in the program as the page shows it (both templates hold each one as text they run), or marked `<!-- snippets: skip (reason) -->`. An npm script saved before 0.7.1 runs its cases as its own code: move each into a `snippet()` when the wiki is next updated. The prose checker must report 0 strong findings; judge weak ones (quoted error messages are fine).

## Step 7: publish

Run preflight again if it was `no-wiki-repo`. In the wiki working copy: commit (message names the version and the pages), then `git push`. Pages committed on top of the cloned placeholder make a plain fast-forward; `git push --force-with-lease origin master` is needed only when the working copy was started with `git init` instead of a clone (L-010 `placeholder-fast-forward`). Wiki repositories use `master`. Then:

```
WW live OWNER/REPO <wiki dir>
```

Every page must answer 200 (Home 301 to `/wiki`), and the sidebar and footer must render on the root. Every `Page#anchor` link must find its heading's id on the rendered page: a slug right on one host can be wrong on another (L-135 `forgejo-slug-punctuation`; `--no-anchors` skips it). Rerun once after a few seconds before calling a failure.

## Step 8: record

In the repository, write `ai-docs/notes/<date>-github-wiki.md` from [templates/wiki-note.template.md](templates/wiki-note.template.md), next to the verification script and its saved output. It holds the pages, the working-copy path, how the wiki was published and how the examples were verified. It also lists the facts the README lacks, the numbered inaccuracies, and the update procedure with the pages that name the version. Add a line to `ai-docs/HANDOFF.md` and a log entry (everlast: `everlast.py` or `ai-docs/log.md`), then commit and push the repository (a run told to commit and not push says so in the note and the report, and whoever pushes runs `live`). Leave the README and CHANGELOG as they are unless asked. They ship inside the package and reach the registry page only with a release, so list the inaccuracies for the maintainer; they get fixed on request or in the next release. When the overlay keeps a list of wikis, move this repository to done.

## Hand-over with package-modernize

**Hand-over between package-modernize and wikiwright** (the same text is in both skills). A package-modernize run reaches the wiki in Phase 7: after the release is verified from the registry, or, in a retrofit without a release, against the latest published version. A wiki that exists takes wikiwright's Update mode; a hand-written wiki without a saved verification output is adopted first (run its program against the version its footer names, save the output, fix every `outputs` finding), then updated. Versions and upgrading takes its evidence from the repository's golden recordings: `test/golden/` (npm), or `tests/Golden/` with the old versions' recordings per runtime and OS and the capture project that made them, plus compare reports in `tests/Golden/upgrade/` where a run wrote them (NuGet), each replayed or compared today, never trusted alone. Inaccuracies the wiki finds in the shipped README or CHANGELOG go to the kickoff prompt's corrections and to HANDOFF.md for the next release. The repository's `ai-docs/notes/<date>-github-wiki.md` records the program, its saved output and the pages that name the version.

## Update mode

1. Read the repository's wiki note; `git -C <wiki dir> pull --ff-only`.
2. Read the CHANGELOG entries since the version the footer names; survey the new version on the registry.
3. Bump the version in the verification script, run it against the new published version (old-major folders and `OLDEST_NODE` included), and compare with the saved output: `WW diffout <saved *-wiki-verify.out.txt> <new output>` normalises line endings and ports and prints every changed, added and removed section, exiting 1 when anything differs (`--skip` for sections that print tool versions, `--save` writes the normalised new output to save over the old). Every difference is a page to fix. A clean diff proves only the cases already in the script: install every third-party package a recipe imports, and every tool a page names (a compiler, a runtime), at its current `latest`, run the recipe on each Node line the pages name, and print its versions (undici 8 broke get-title-at-url's proxy recipe while 3.0.0 stood still; its pages still named TypeScript 6 after 7 shipped; print each tool's version, since diffout sees only what the script prints, L-131 `recipe-deps-drift`). Then `WW outputs <wiki dir> <new output>` lists every page output the new run no longer prints. Save the new output over the old (`diffout --save` masks ports and local paths). A wiki with no saved output (made before 0.2.0, or by hand) is adopted first: run its program, or one written from the template, against the version the footer names, and fix every `outputs` finding by printing the page's form, correcting the page, or a `<!-- outputs: skip (reason) -->` block (L-019 `save-the-output-too`, L-104 `adopt-unsaved-wiki`).
4. Update the pages that name the version (the note lists them), Versions and upgrading, the API reference for new or changed members (with the new version as "introduced in"), and the footer's version and date.
5. Steps 6 to 8, with the note updated rather than replaced and a new log entry.

A draft-only request ("put the pages in ./wiki-draft/, don't push or commit"): the changed pages go to that folder, and the note, HANDOFF and log changes go beside it under `repo-draft/` with the repository's own paths. The repository and wiki clones stay untouched; test on a fresh clone (L-107 `draft-only-update`).

## Output

One message at the end: the wiki URL and commit, the page list, the live check line, the facts the README lacks (short), the inaccuracies found in the shipped docs (numbered, with where), and anything not tested. At a stop (the first-page click): what is needed, the URL, and what continues meanwhile.

## While working: capture learnings

If the user corrects you, the same error happens twice, a workaround is found, or an environment fact is discovered, write it to [LEARNINGS.md](LEARNINGS.md) now (when the request forbids editing the skill, list it in the report instead), and wherever an ID is cited add a two-to-four-word code name after it, for example L-001 `backslash-placeholder`. Check existing entries first: add, update, retire, or nothing. A lesson about a registry goes into its reference with the date. If a learning proves a claim above wrong, fix it here, log it in [CHANGELOG.md](CHANGELOG.md), and set `contradiction` in `evergreen.json`.

## Maintenance

This skill is evergreen (topic: GitHub wiki mechanics and writing library documentation whose examples are verified against the published package; tier `fast`, interval set by `evergreen.json`). Files: `evergreen.json` (state), [RESEARCH.md](RESEARCH.md) (findings and the four-track search plan), [CHANGELOG.md](CHANGELOG.md) (every change, with reasons), [LEARNINGS.md](LEARNINGS.md) (lessons, seeded from the first three wikis), [TESTS.md](TESTS.md) and `evals/evals.json` (the cases that prove it and the runs). Protocol: [MAINTENANCE.md](MAINTENANCE.md), a self-contained copy for machines without the evergreen plugin. Refresh with `evergreen-refresh`; test with `evergreen-test`; fix a failure with `evergreen-tune`. Each run of the skill is also a test of it: what it got wrong goes to LEARNINGS.md the same day.
