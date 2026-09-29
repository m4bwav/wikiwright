# Learnings: wikiwright

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md (LEARNINGS-FORMAT). Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first, by meaning (`evergreen.py search "<the lesson>" --kinds learnings` finds near-duplicates in every registered unit): add / update / retire / none. Trigger and Hypothesis are required. Promote after three confirmations; retire when harmful > helpful.

## Active

The first six entries were seeded on 2026-09-28 from the two wikis written by hand before this skill existed (RandomNameGeneratorLibrary and JsonPrettyPrinter, both NuGet); their evidence is those repositories' `ai-docs/notes/2026-09-28-github-wiki.md`. Each rule is already in SKILL.md or a reference, which the Status line names.

### L-001 · 2026-09-28 · Pages with backslashes are written with a <BS> placeholder (`backslash-placeholder`)
- Trigger: while writing the JsonPrettyPrinter wiki, the harness's Write tool decoded `\u003C` in a page into `<`, and shell heredocs dropped single backslashes (2026-09-28). While this entry was being written, a Python string in a heredoc turned the same escape into `<` again (2026-09-28); the same trap cost the package-modernize runs several times (its L-058, L-091, L-102).
- Hypothesis: the tool layer unescapes JSON-style escapes in file content before writing, and the shell treats a backslash as an escape even in quoted heredocs.
- Rule: write every backslash that matters as `<BS>`, convert with `wikiwright.py unbs`, and let `wikiwright.py check` fail while any `<BS>` remains; count the placeholders before and after. Run unbs only on pages: a file that names the placeholder in prose (this one, SKILL.md) loses the name.
- Evidence: DotNetJsonPrettyPrinter ai-docs note ("Writing-tool note"); SKILL.md Step 5; scripts/wikiwright.py (unbs, check)
- Scope: env:agent-harness
- Status: promoted: C-20260928-1 · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-002 · 2026-09-28 · The wiki repository exists only after a first page is saved in the web UI (`first-page-click`)
- Trigger: on DotNetRandomNameGenerator the first `git push` answered "Repository not found" although `has_wiki` was true; Mark saved a page and the push worked (2026-09-28). On get-title-at-url the same day, a placeholder repository appeared about a minute after `gh repo edit --enable-wiki`. Answered on seeded-random-utilities the same day: after `--enable` at 19:25:33 UTC, ls-remote every 5 seconds still found nothing at 61 seconds; Mark saved the first page at 19:27:28 (commit `ef61124`, "Initial Home page", his authorship) and ls-remote saw it at 19:27:39. get-title-at-url's placeholder `d652d15` carries the same message, the web UI's default, so it was a click too.
- Hypothesis: GitHub creates `OWNER/REPO.wiki.git` lazily, on the first page save; no REST or GraphQL call creates a page. Enabling the feature never creates it (resolved 2026-09-28).
- Rule: run `wikiwright.py preflight` (ls-remote, re-checked for 60 seconds after enabling) before writing; when the repository is missing, ask for the click in the first message and keep working meanwhile. Pages committed on the cloned placeholder push without force (L-010).
- Evidence: DotNetRandomNameGenerator ai-docs note ("How it was published"); seeded-random-utilities ai-docs note of 2026-09-28 ("How it was published"); SKILL.md Step 1; references/publishing.md; RESEARCH.md (Current understanding)
- Scope: skill
- Status: promoted: C-20260928-1 · helpful 3 · harmful 0 · last_confirmed 2026-09-28

### L-003 · 2026-09-28 · GitHub wiki repositories use the branch master (`wiki-branch-master`)
- Trigger: both wiki clones came with `master` although the default of new repositories is `main` (2026-09-28).
- Hypothesis: the wiki backend (Gollum) still creates `master`.
- Rule: push to `master`; `wikiwright.py preflight` reads the branch from ls-remote rather than assuming.
- Evidence: both ai-docs notes ("Gotchas"); references/publishing.md
- Scope: skill
- Status: promoted: C-20260928-1 · helpful 2 · harmful 0 · last_confirmed 2026-09-28

### L-004 · 2026-09-28 · .NET 10 file-based apps need PublishAot=false for reflection (`file-based-app-aot`)
- Trigger: the JsonPrettyPrinter verification program threw "Reflection-based serialization has been disabled for this application" under plain `dotnet run` (2026-09-28).
- Hypothesis: file-based apps turn on native AOT by default, which disables reflection-based System.Text.Json even when not publishing.
- Rule: the NuGet template carries `#:property PublishAot=false`.
- Evidence: DotNetJsonPrettyPrinter ai-docs note; learn.microsoft.com/dotnet/core/sdk/file-based-apps; templates/nuget/wiki-verify.template.cs
- Scope: skill
- Status: promoted: C-20260928-1 · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-005 · 2026-09-28 · Two dotnet runs of one file-based app contend for its build output (`dotnet-run-contention`)
- Trigger: running the same verification file twice in parallel failed with locked build output (2026-09-28).
- Hypothesis: a file-based app builds into one per-file folder under the temp directory.
- Rule: one run at a time per file, or separate folders, or `dotnet build` once and `dotnet run --no-build`.
- Evidence: DotNetJsonPrettyPrinter ai-docs note ("Gotchas"); references/nuget.md
- Scope: skill
- Status: promoted: C-20260928-1 · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-006 · 2026-09-28 · A markdown table cannot hold multi-line output (`table-cannot-hold-output`)
- Trigger: examples whose output spans lines (pretty-printed JSON) broke the tables they were first written in (2026-09-28).
- Hypothesis: a GitHub markdown table cell is one line; `<br>` inside code does not render as a line break.
- Rule: input and output go in paired code blocks; tables only for one-line values.
- Evidence: the JsonPrettyPrinter wiki's Output format page; references/page-sets.md (conventions)
- Scope: skill
- Status: promoted: C-20260928-1 · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-007 · 2026-09-28 · Spawn the CLI asynchronously when the fixture server runs in the same process (`async-cli-with-fixture`)
- Trigger: the npm template's `cli()` used `spawnSync`; in the first run (get-title-at-url, 2026-09-28) every CLI case against the in-process fixture server would have hung, because the parent's event loop, which serves the fixture, was blocked. Caught before the run; the run's script used `spawn`.
- Hypothesis: `spawnSync` blocks the whole Node process, including its HTTP server.
- Rule: the template spawns the bin asynchronously and awaits it.
- Evidence: templates/npm/wiki-verify.template.mjs (cli), C-20260928-2; get-title-at-url ai-docs note (Gotchas)
- Update 2026-09-29 (markdown-plain-link-replacer): a CLI that reads standard input when it gets no argument waits for ever on a spawned child's open pipe; the golden capture's no-argument case was killed after 15 seconds. The template's `run()` now closes stdin (or writes `input`) on every child.
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-008 · 2026-09-28 · Print outputs in the form the page shows them (`print-as-the-page-shows`)
- Trigger: the first run's script printed an array as JSON while the Recipes page showed `console.log` output; a one-line guess of Node's formatting was wrong (Node breaks the array over lines). Checked before the push (2026-09-28).
- Hypothesis: two printers of the same value differ in layout, and a guessed layout is an invented output.
- Rule: when a page shows `console.log` (or `Console.WriteLine`, or a REPL echo), the script prints that way; never convert by hand.
- Evidence: SKILL.md Step 4, C-20260928-2
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-009 · 2026-09-28 · Audit every sentence for its source before the check (`claims-audit`)
- Trigger: the first draft of get-title-at-url's Versions page said 2.x needed "Node 14 and up", that axios decoded pages as UTF-8, and mapped AxiosError codes to the new ones; none came from the survey or a run (2.0.0 has no `engines` field). Caught on a reread and removed (2026-09-28).
- Hypothesis: a page about old versions invites filling gaps from general knowledge of the old dependencies.
- Rule: Step 6 starts with one reread asking, per sentence, which output, source line, changelog entry or registry answer says it; cut what has none.
- Evidence: SKILL.md Step 6, C-20260928-2
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-010 · 2026-09-28 · Pages committed on a cloned placeholder push without force (`placeholder-fast-forward`)
- Trigger: publishing.md said to force-push over a placeholder; on get-title-at-url the push of pages committed on the cloned placeholder was a plain fast-forward (`d652d15..b271157`, 2026-09-28). The RandomNameGenerator run needed force only because its working copy began with `git init`.
- Hypothesis: the placeholder commit is an ancestor of a clone's new commits.
- Rule: clone, commit, `git push`; force only for a working copy that did not start as a clone.
- Evidence: SKILL.md Step 7, references/publishing.md, C-20260928-2
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-011 · 2026-09-28 · Run the old majors when there is no golden capture (`run-the-old-majors`)
- Trigger: get-title-at-url was modernized before golden captures existed, so the Versions page had only the CHANGELOG. Installing 2.0.0 and 1.1.8 in their own scratch folders and running the fixture cases showed that 2.0.0 cannot be imported at all since cheerio 1.0.0 and how 1.1.8's callback reports a 404 (`error === 404`), neither in any shipped doc (2026-09-28).
- Hypothesis: a changelog records intent at release time; installing the old version today shows what users get today.
- Rule: Step 4 installs each old major the Versions page discusses and runs the same cases, unless a golden capture exists.
- Evidence: SKILL.md Step 4, references/page-sets.md (Versions row), C-20260928-2; get-title-at-url ai-docs note
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-012 · 2026-09-28 · A plugin installed mid-session is not invocable; a user-skills junction is, after a delay (`midsession-skill-load`)
- Trigger: after `claude plugin install wikiwright@mark-local` the Skill tool answered "Unknown skill" for `wikiwright:wikiwright`, and at first also for a junction in `~/.claude/skills/wikiwright`; a few seconds later the listing showed `wikiwright` and the junction invocation worked (Claude Code 2.1.281, Windows, 2026-09-28).
- Hypothesis: Claude Code watches the user skills folder and reloads it with a short debounce; plugins load at session start.
- Rule: to test a freshly written skill in the same session, link its folder into `~/.claude/skills/`, wait for the listing to show it, invoke, then remove the link so it does not duplicate the plugin. Headless evals (`claude -p`) see the installed plugin, which is a cached copy: `claude plugin update` keeps a stale cache while the version number is unchanged (it said "already at the latest version (0.1.0)" over the commit of the first install), so after editing the source, `claude plugin uninstall` and `install` again, then compare the cached SKILL.md's hash with the source (2026-09-28). Second run, same day: with the plugin installed from a directory marketplace before the session began, the Skill tool served the SKILL.md text read at session start, even through a fresh junction to the edited source and with the source folder as the base directory; the edits made earlier in the session were missing. The references and script it points to are read from disk, so they were current. Rule: when a same-session run must exercise SKILL.md edits, follow the source file by hand and say so, or run it headless (`claude -p` reads the files at its own start).
- Evidence: this repository's ai-docs log, 2026-09-28 (both runs)
- Scope: env:claude-code
- Status: active · helpful 2 · harmful 0 · last_confirmed 2026-09-28

### L-016 · 2026-09-28 · A wiki clone into the Claude Code scratchpad fails on Windows (`scratchpad-path-too-long`)
- Trigger: `git clone https://github.com/m4bwav/get-title-at-url.wiki.git <scratchpad>/wiki` failed with "Filename too long" on `.git/hooks/applypatch-msg.sample`; retrying with `-c core.longpaths=true --template=` failed with "'$GIT_DIR' too big". The session scratchpad path was about 200 characters (Windows 11, Git for Windows, 2026-09-28). Preflight without `--clone` worked, and so did `npm install` of a package with no dependencies in the same folder.
- Hypothesis: git's Windows path limit counts the whole `.git` path; the scratchpad leaves too little room.
- Rule: on Windows, clone or inspect the wiki at a short path (the sibling `<clone>.wiki`, or a short temp folder) and not under the scratchpad. When a working copy already exists, `git -C <it> status -sb` plus preflight answer "does it exist" without cloning. For a draft-only request, preflight without `--enable`: it only reads.
- Evidence: draft-only Home run for get-title-at-url, 2026-09-28. Counter-case, same day: the seeded-random-utilities draft-only run cloned its placeholder wiki into a scratchpad path of about 150 characters without error, so the limit depends on the scratchpad's length, not on the scratchpad as such. The rule stands as the safe default. Followed again on the is-an-image-url draft-only Home run the same day: the read-only clone went to a short sibling of the work folder and succeeded. A second is-an-image-url draft the same day cloned by `preflight --clone` into the scratchpad (a target path of about 150 characters) without error. A stack-exchange-markdown-retriever draft on 2026-09-29 cloned with plain `git clone` into `<scratchpad>\sem.wiki` (about 140 characters) without error: keep the target folder name short.
- Scope: env:windows
- Status: active · helpful 3 · harmful 0 · last_confirmed 2026-09-28

### L-014 · 2026-09-28 · Replacing the fixture address can change console.log layout (`substitution-changes-layout`)
- Trigger: drafting a new get-title-at-url Home page, `console.log(result)` printed `{ title, url, status }` on one line for `https://example.com/` but over four lines for the fixture's `http://127.0.0.1:<port>/` (Node 24.18, 2026-09-28).
- Hypothesis: Node's util.inspect breaks an object onto several lines once its one-line form passes about 72 characters, so a longer or shorter address changes the layout, not just the text.
- Rule: when a page shows the fixture address replaced by a real-looking one, only do so in output whose layout does not depend on length (JSON.stringify with indent, the CLI's `--json`, plain strings), or pick an example whose printed output does not contain the address.
- Evidence: draft-only Home run for get-title-at-url (its work folder's `ai-docs/notes/2026-09-28-wiki-home-draft.md` and `home-verify.out.txt`), 2026-09-28
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-013 · 2026-09-28 · A skill's own run can teach the baseline; grade on the route, not the location (`baseline-learns-from-run`)
- Trigger: T-20260928-2's action baseline verified its example like the skill, because the first real run had left `ai-docs/notes/2026-09-28-github-wiki.md` in the repository the case names; and the first grading looked for the verification script in the workspace, where the skill correctly does not put it without a clone (2026-09-28).
- Hypothesis: a case against a live repository measures the repository's docs as much as the skill; a file-location check encodes one run's layout.
- Rule: point action cases at a repository the skill has not touched (no wiki, no wiki note); grade verification by the install command in the trace, not by where the script was saved.
- Evidence: T-20260928-2, evals/evals.json action-1 (baseline and evidence)
- Scope: skill tests
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-015 · 2026-09-28 · A Home-only draft fails `check` on the sidebar and footer by design (`home-only-check`)
- Trigger: `WW check wiki-draft --version 2.0.0` on a folder holding only Home.md exited 1 with `_Sidebar.md:0: error: missing` and `_Footer.md:0: error: missing`, and nothing else (seeded-random-utilities draft-only run, 2026-09-28).
- Hypothesis: `check` assumes a full page set; a draft of one page cannot pass it without extra files nobody asked for.
- Rule: for a draft of Home alone, run `check`, accept exactly those two errors, and say so in the report. Leave out links to pages that do not exist yet, since a published Home with them would show red "create page" links. Link the README, CHANGELOG, registry and issues instead, and name the missing per-page lines as work for the full wiki. Since 0.2.0, `check --partial` skips the sidebar and footer requirement (C-20260928-3).
- Evidence: this run's work folder `ai-docs/notes/2026-09-28-wiki-home-draft.md`; confirmed by a second seeded-random-utilities draft-only run the same day, where README section anchors (checked for `id="user-content-…"` on the repository page) stood in for the unwritten pages; and by a third such run the same day (same two errors only, seven README anchors all present); and by an is-an-image-url draft-only run the same day, where `check --partial` exited 0 and five README anchors stood in for the unwritten pages
- Scope: skill
- Status: active · helpful 6 · harmful 0 · last_confirmed 2026-09-29 (stack-exchange-markdown-retriever Home-only draft: `check --partial` 0 errors; README anchors `#readme`, `#behaviour-at-the-edges`, `#migrating-from-1x` checked on the repository page; a second such draft the same day, also 0 errors, with a `--partial` Home and every output in the saved run, 9 of 9)

### L-017 · 2026-09-28 · Headless eval runs write to the skill under test and see the session's files (`evals-touch-the-source`)
- Trigger: during T-20260928-3, two action runs (skill arm) followed "capture learnings", read the overlay, which names the skill's source folder, and edited the source LEARNINGS.md (the entry now L-015 and a counter-case on L-016). One action-2 run answered "does the wiki exist" by `git fetch` in the sibling working copy this session had cloned minutes before, instead of preflight (2026-09-28).
- Hypothesis: a headless run has the same filesystem, overlay and plugin paths as the session that launched it, so anything the session made before the suite is part of the case.
- Rule: run the suite from a committed source tree and `git diff` it afterwards; review every eval-written entry (keep, renumber or drop) before committing. Create nothing a case can see (clones, notes, drafts) before the suite runs.
- Evidence: T-20260928-3; `git diff skills/wikiwright/LEARNINGS.md` mid-suite; the a2run1 trace
- Update 2026-09-29 (T-20260929-1): besides learnings and a reference line, an eval run left `skills/wikiwright/package.json` from an `npm init -y` in the skill's source folder. `git status` (not only `git diff`) after the suite shows untracked files; delete what a run created.
- Scope: skill tests
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-018 · 2026-09-28 · An action prompt that names the method cannot tell the arms apart (`unhinted-action-prompt`)
- Trigger: action-1 asks for "a working example and its real output" and to "check whether the repo's wiki exists first"; against a repository with no wiki note the baseline still ran `git ls-remote` and `npm install seeded-random-utilities@2.0.0`. action-2, which asks only for "a Home page for the GitHub wiki", split the arms: both skill runs installed and ran the package, and neither baseline installed anything; both baselines showed the README's example with comments instead of output (2026-09-28).
- Hypothesis: a capable model follows a method the prompt spells out; the skill's value is supplying the method when the user does not.
- Rule: every action case gets an unhinted twin whose prompt is what a user would type; grade both, and treat the hinted case as a regression check only.
- Evidence: T-20260928-3 (action-1 baseline passes; action-2 baselines 0/2 on the install)
- Scope: skill tests
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-019 · 2026-09-28 · A saved script that does not print the pages' forms cannot re-verify them (`save-the-output-too`)
- Trigger: update-mode rehearsal on get-title-at-url: the saved verification script ran clean against 3.0.0, but five outputs on the pages were not in its output: three converted by hand from JSON to the `console.log` or REPL form, headers rewritten as request lines, and npm's install output that never came from the script. The first run's note said "compare with the pages" and saved no output to diff against (2026-09-28).
- Hypothesis: converting an output by hand after the run (the L-008 fix applied at write time) leaves the script one step behind the page; without a saved output, update mode has nothing to diff.
- Rule: the script prints every output in the pages' form; its output is saved beside it with the fixture port replaced; `wikiwright.py outputs` passes before publishing and again in update mode; output that cannot come from the script carries `<!-- outputs: skip (reason) -->`.
- Evidence: get-title-at-url ai-docs note ("Rehearsed 2026-09-28"), wiki commit 2807e56; C-20260928-3
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-020 · 2026-09-28 · Replay the repository's golden capture script against the old and the new version (`replay-the-golden-capture`)
- Trigger: seeded-random-utilities keeps `test/golden/capture-1.1.4.cjs` and its output. Running that script today against 1.1.4 from npm (322 of 322 identical) and against 2.0.0 with one line patched (316 of 322; the six are the documented emoji exception, and the recorded quirks differ exactly as the CHANGELOG says) gave the Versions page evidence no changelog could (2026-09-28).
- Hypothesis: a golden capture is a test the old version passes by construction; re-running it shows both that the old version still behaves as recorded and where the new one departs.
- Rule: when a repository has golden captures, replay each capture script against the old version installed today and against the current one, compare case by case with the file, and put the counts and the differing cases on Versions and upgrading. Never rewrite the golden file.
- Evidence: seeded-random-utilities wiki (Versions and upgrading) and its ai-docs note; references/page-sets.md (Versions row)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-021 · 2026-09-28 · Deno, Bun, pnpm and yarn run from npm on a machine without them (`runtimes-from-npm`)
- Trigger: the overlay says Bun and Deno are not installed on the development machine; `npm install deno bun` in a scratch folder gave working binaries (Deno 2.9.6, Bun 1.4.2), and corepack ran pnpm 10.34.5 and yarn 4.18.1, so Getting started could say "run" for all four. Yarn 4 installs with Plug'n'Play: `node script.mjs` failed with ERR_MODULE_NOT_FOUND and `yarn node script.mjs` worked (2026-09-28).
- Hypothesis: both runtimes publish platform binaries as npm packages; corepack ships with Node 24.
- Rule: before writing "not tested" for a runtime or package manager, try the npm route; with yarn 4 run the example through `yarn node`. Spawn the `.cmd` shims with `shell: true` on Windows.
- Evidence: seeded-random-utilities wiki (Getting started); references/npm.md
- Update 2026-09-28 (get-title-at-url draft run): versions move. `corepack pnpm` downloaded pnpm 12.6.0, and `corepack yarn` in a folder with no `packageManager` field ran Yarn 1.22.22, not 4. `corepack use yarn@4` gave 4.18.1 with Plug'n'Play again. Print each tool's version from the script rather than copying it from here. The `.exe` files are `node_modules/bun/bin/bun.exe` and `node_modules/@deno/win32-x64/deno.exe`; spawn those directly.
- Update 2026-09-28 (fourth is-an-image-url Home-only draft): npm 11.16 ends `npm install deno bun` with `npm warn allow-scripts ... Run npm approve-scripts`. The warning does not mean the install failed: `deno --version` (2.9.6) and `bun --version` (1.4.2) worked from `node_modules/.bin` without approving anything, and the script's Deno and Bun sections matched the saved output. Check the versions before you approve scripts.
- Update 2026-09-29 (get-title-at-url draft run): Deno 2.9.6 ignores `npm:` auto-download when a `package.json` sits in the folder or above it. With the Deno folder inside the `RT` folder (which has `package.json` and `node_modules` from `npm install deno bun`), `deno run --allow-net title.ts` exited 1 with "Could not find a matching package for 'npm:...' in the node_modules directory ... run `deno install`". A sibling folder (`<RT>-deno`) with nothing above it worked. Put the Deno case outside RT. The failure is worth a line on Getting started, because readers run the snippet inside Node projects. Reviewed 2026-09-29 (T-20260929-1), narrowed: with a `package.json` in the folder or above, Deno resolves `npm:` from that folder's `node_modules`, and the RT folder did not have the package. The markdown-plain-link-replacer run ran Deno from its scratch project, where the package was installed, and it worked.
- Scope: env:any
- Update 2026-09-29 (fifth get-title-at-url update draft): confirmed as written: `corepack yarn` gave 1.22.22 and `corepack yarn@4.18.1 add` gave Plug'n'Play; `npm install deno bun` worked despite the allow-scripts warning; the Deno case in a fresh folder with no package.json above it worked, and the page now carries the package.json failure. A script run with a relative `RT` broke every spawned Bun and Deno command, because each case runs in its own folder: pass `RT` as an absolute path.
- Update 2026-09-29 (sixth get-title-at-url draft): all four confirmed again (pnpm 10.34.5 through `corepack pnpm@10`, Yarn 4.18.1 from a `packageManager` field, Bun 1.4.2, Deno 2.9.6). Two Deno facts printed by the script: with no terminal and no `--allow-net`, Deno does not prompt, and a package that catches fetch errors resolves with them (here `NETWORK_ERROR`, `Requires net access to "<host>:<port>"`). The package.json failure is fixed by `npm install <package>` in that folder: the same `deno run` then worked.
- Status: active · helpful 6 · harmful 0 · last_confirmed 2026-09-29

### L-022 · 2026-09-28 · Keep machine-dependent text out of a saved verification output (`machine-free-output`)
- Trigger: the seeded-random-utilities script first printed the error for a `Date` seed, whose message contains the date in the local time zone ("GMT-0600 (Central Standard Time)"); a saved output with it would differ on every other machine and fail the diff in update mode (2026-09-28).
- Hypothesis: seeded output is only diffable when nothing else in it depends on the machine (time zone, paths, ports, timings).
- Rule: replace or leave out time-zone text, absolute paths, ports and timings in the saved output; show such values on a page only from a case that prints a stable form.
- Evidence: seeded-random-utilities ai-docs note (Gotchas)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-103 · 2026-09-28 · `outputs` misses input and output pairs, and reads "is" or "are" anywhere as an output intro (`input-output-pairs`)
- Trigger: the first update of a hand-written NuGet wiki (JsonPrettyPrinter) ran the saved C# program against 3.0.1 and `WW outputs`: 6 findings, all of them input blocks (Not-a-Validator's "Single-quoted strings are tracked like double-quoted ones, so the space inside stays:" matched because OUT_INTRO accepts its word anywhere before the colon), while the output block right after each input block was never checked, because `prev` is reset after every fence and nothing introduces the second block (2026-09-28).
- Hypothesis: the npm wikis put a prose line before every output; a page that shows input and output as two adjacent fences is invisible to the check, and the loose intro pattern then points at the wrong block.
- Rule: until the helper is fixed, mark such pages by hand: `<!-- outputs: skip (input) -->` before the input block and `<!-- outputs: check -->` before the output block. Fix in the helper: the intro word must be among the last few words before the colon, and an untagged or data fence that follows an input fence with no prose between is output; unit tests for both.
- Evidence: DotNetJsonPrettyPrinter.wiki c6b285c, Not-a-Validator.md lines 21 to 92; `WW outputs` run of 2026-09-28 (6 checked, 6 missing)
- Scope: skill (scripts/wikiwright.py outputs, SKILL.md Step 6)
- Status: promoted: C-20260928-4 (the helper reads input and output pairs, code followed by its output, and an intro word only within six words of the colon; tests in OutputFormsTests). Confirmed on the retrofit: 0.2.0 checked 6 blocks of JsonPrettyPrinter's wiki, all inputs; 0.3.0 checks 21, all outputs · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-104 · 2026-09-28 · Adopting a hand-written wiki: the old program covers only part of the pages (`adopt-unsaved-wiki`)
- Trigger: JsonPrettyPrinter's wiki (written by hand before 0.2.0) kept its verification program but not its output, and its note says two smaller runs (serializer escaping, the comment-stripping recipe, JsonNode.DeepEquals, the stdin filter) were never saved; the program printed 354 lines, identical over two runs, and some pages' outputs cannot come from it (2026-09-28).
- Hypothesis: Update mode step 3 assumes the program is complete; a hand-written wiki's program is whatever the writer kept.
- Rule: adopting a wiki with no saved output: run the program as it is against the version the footer names (twice), save the output LF-normalised, run `outputs`, then fold every missing case into the program (or mark the block skip with a reason) before bumping the version. Record in the note which pages the program did not cover.
- Evidence: DotNetJsonPrettyPrinter ai-docs/notes/2026-09-28-github-wiki.md (How the examples were verified); this run's output
- Scope: skill (SKILL.md Update mode, step 3)
- Status: promoted: C-20260928-4 (SKILL.md Update mode, adopting a wiki written before 0.2.0; applied to both NuGet wikis the same day: JsonPrettyPrinter's program gained 9 page outputs and the F# and PowerShell runs, RandomNameGeneratorLibrary got its first program) · helpful 2 · harmful 0 · last_confirmed 2026-09-28

### L-105 · 2026-09-28 · A C# verification program on Windows prints CRLF, and runs on one runtime only (`csharp-verify-program`)
- Trigger: the JsonPrettyPrinter program (a .NET 10 file-based app with `#:property PublishAot=false`) printed 189 carriage returns through Console.WriteLine; `outputs` normalises them, but a saved output with CR would diff against a Linux run. The package's golden capture showed that `ToJson` answers differently on .NET Framework (0.1 as 0.10000000000000001), which a net10.0-only file-based app cannot show (2026-09-28).
- Hypothesis: the npm template writes LF; the C# one inherits Console's platform newline. A multi-runtime package needs its page claims checked per runtime.
- Rule: save the output with LF (normalise before saving); for a package whose answers differ by runtime, take the per-runtime facts from the repository's golden recordings (package-modernize keeps one per runtime under tests/Golden) or run a net48 console project, and say on the page which runtime an example ran on.
- Evidence: this run's scratch output (CR count 189); DotNetJsonPrettyPrinter tests/Golden/3.0.1.net48-windows.json vs net10.0
- Scope: skill (references/nuget.md, templates/nuget/wiki-verify.template.cs)
- Status: promoted: C-20260928-4 (both retrofits saved LF output; references/nuget.md and the NuGet template say so) · helpful 2 · harmful 0 · last_confirmed 2026-09-28

### L-106 · 2026-09-28 · Run the npm verification script on the oldest supported Node too (`oldest-node-run`)
- Trigger: updating get-title-at-url's wiki for an unchanged 3.0.0, the saved script matched its saved output on Node 24.18, the only Node it had ever run on. Run on Node 20.20.2 and 24.13.0, one case differed: a recipe that decodes with the runtime's `TextDecoder('windows-1252')` printed C1 controls. Recipes had told readers to "decode the bytes with the right `TextDecoder` first", which is wrong on those Nodes (2026-09-28).
- Hypothesis: advice that hands work to the runtime (decoders, `Intl`, `fetch`, crypto) is only as true as the runtime; one Node run hides that. The same pattern as L-105 on .NET.
- Rule: in Step 4 and update mode, also run the script on the oldest Node line in `engines` (and any release range the repository's notes call buggy), and diff against the main run. `npx -y -p node@<v> node` downloads one; put that `node.exe` first on `PATH` for any case that spawns a shell, because through npx's shim the shell's `node` fails (get-title-at-url's bash loop printed `(no title)` for every URL). Every difference is a page claim to scope by version or a case to fix.
- Evidence: get-title-at-url update run of 2026-09-28 afternoon (drafts in the session work folder, `wiki-verify.node20.out.txt`); the repository's TextDecoder solution entry
- Update 2026-09-29 (markdown-plain-link-replacer, the first new wiki run on two Node lines): made mechanical in 0.4.0. The npm template's `OLDEST_NODE=<major>` reruns the whole script under that Node with its folder first on PATH and saves `wiki-verify.node<major>.out.txt`; `wikiwright.py diffout` compares it. The two runs differed only in the routing line and the `NODE_USE_ENV_PROXY` recipe (Node 20.20.2 has no such variable), which the Recipes page scopes by version.
- Scope: skill (SKILL.md Step 4, Update mode step 3; references/npm.md)
- Status: active · helpful 5 · harmful 0 · last_confirmed 2026-09-29 (fifth draft: the live wiki at 2807e56 still carried the wrong advice; the saved script plus a code-point case showed it again on 20.20.2. Earlier drafts were found under the eval work folders and compared before writing, then every claim was re-run rather than copied. Fourth draft: the Recipes fix from the third draft had never been published, and the live wiki still carried the wrong advice; reproduced again on 20.20.2. `node_modules/.bin/node` from the `node` package fails in Git Bash with "This: command not found", because npm 11 blocks the package's install script. `node_modules/node/bin/node.exe` works without approving anything.)
- Update 2026-09-29: an unpublished draft is not a fix. When earlier drafts exist for the same wiki, compare the live wiki with them (or with this file's evidence) before you start, and carry their fixes forward.
- Update 2026-09-29 (sixth get-title-at-url draft): the live wiki at `fdca908` had the Recipes fix, but How titles are found still said the decoder was wrong "on Node 20 and some Node 22 and 24 releases". That is too broad: 20.0 to 20.18.2 are right, and only the one-shot `decode()` is affected. A sibling draft (`ww7/suite/action-3-r1`) had already fixed it with the Node issue and pull request. This run carried that wording forward after checking both links with `gh api`. The CHANGELOG's "Node 20's own decoder gets them wrong" has the same breadth; it went to the note as inaccuracy 5.

### L-107 · 2026-09-28 · Draft-only update: pages to the named folder, everything else beside it, clones untouched (`draft-only-update`)
- Trigger: "update the wiki for 3.0.0; put every changed page in ./wiki-draft/; don't push or commit anything anywhere". The wiki already named 3.0.0. Update mode assumes `pull --ff-only`, writing in the wiki working copy, committing, pushing and committing the repository's note (2026-09-28).
- Hypothesis: the user wants a reviewable diff, not a live change. The run is still worth doing when the version is unchanged: re-verification (L-106) and the npm route for untested tools (L-021) found three pages to fix.
- Rule: with a no-commit constraint, read the wiki's remote head with `git ls-remote` instead of pulling. Copy only the pages that change into the named folder and edit them there. Check with `check`, `outputs` and the prose checker on a scratch copy of the whole wiki with the drafts laid over it, since `--partial` would miss links to unchanged pages. Put the updated script, its outputs and a handoff README (publish steps, note changes, new inaccuracies) in a sibling folder, not in the pages folder. Run the repository's tests on a `git archive HEAD` export so the clone stays clean. End with `git status` in both clones.
- Evidence: session work folder `wiki-draft/` and `wiki-draft-notes/README.md` (get-title-at-url, 2026-09-28)
- Update 2026-09-28 (second is-an-image-url Home-only draft): in PowerShell, `git archive HEAD | tar -x -C C:\...` fails. Git's GNU tar reads `C:` as a remote host ("Cannot open"), and git reports "The pipe is being closed". `git archive --format=zip -o <x>.zip HEAD` followed by `Expand-Archive` works. On that export, `npm ci` and `npm test` ran from the scratchpad (377 of 377 passed).
- Scope: skill (SKILL.md Update mode)
- Update 2026-09-28 (fourth is-an-image-url Home-only draft, `has-pages`): the same layout worked for a single page. The draft laid over a scratch copy of the live wiki gave `check` 0 errors, anchors into FAQ and Versions and upgrading included. The saved script, rerun with `RT` and `V104`, matched the saved output line for line in every section it ran. The repository's tests were not run, because the Home page quotes no test count.
- Update 2026-09-29 (third get-title-at-url update draft): `git clone -q <the local clone's path> <scratch>/repo-test` is a simpler clean copy than `git archive` on Windows: no tar and no zip, and it leaves the source clone untouched. `npm ci` and `npm test` passed there (186 of 186). The drafts of the repository files went under `repo-draft/` with the repository's own paths (`ai-docs/notes/...`, `ai-docs/HANDOFF.md`, `ai-docs/log.md`), so they can be copied over as they are. `git diff` from the scratch wiki clone went beside the pages folder as `wiki-draft.diff`.
- Update 2026-09-29 (fourth get-title-at-url update draft): the run followed SKILL.md's Update mode and did not read this entry first, because SKILL.md never mentions a draft-only variant. It appended the update record to the repository clone's `ai-docs/notes/...-github-wiki.md` and `ai-docs/log.md` (uncommitted) before finding L-107. It then copied both files to `repo-draft/` and restored them with `git checkout --`; both clones ended clean. With helpful now at 5, this rule is overdue for promotion into SKILL.md Update mode, together with a line telling update runs to read LEARNINGS.md first.
- Update 2026-09-29 (sixth get-title-at-url update draft, work folder `action-3-r2`): again SKILL.md alone was followed and this entry was found only after the pages were written. The run still landed on the same layout unprompted: preflight `--clone` into the scratchpad, tests on a `git clone --branch v3.0.0` copy, and repository files under `repo-draft/`. It carried a sibling draft's better How-titles wording forward (L-106) only after finding the drafts late. Both clones were left clean. The promotion into SKILL.md Update mode, with "read LEARNINGS.md first", is now the most repeated miss in this file.
- Status: promoted: C-20260929-3 (SKILL.md Update mode, "A draft-only request") · helpful 7 · harmful 0 · last_confirmed 2026-09-29 (get-title-at-url sixth draft: same layout; both clones left clean)

### L-108 · 2026-09-28 · A Home-only draft links to pages that do not exist yet (`home-only-draft`)
- Trigger: "write a Home page for m4bwav/is-an-image-url into ./wiki-draft/Home.md; don't push or commit". Preflight said `exists`, and a scratch clone showed the placeholder. The Home table in page-sets.md asks for one line per page, so Home linked the nine planned pages, and `check --partial` reported 9 "link to missing page" errors and nothing else (2026-09-28).
- Hypothesis: `--partial` skips the sidebar and footer checks but still resolves links. A Home page written before the rest of the set can't pass `check` and shouldn't be made to: without its page list it is useless as a hub.
- Rule: with a Home-only request, choose the page set first (Step 3) and link the planned pages by their final file names. Run `check --partial` and confirm that every error is a planned-page link. List those pages in the handoff note as still owed, and don't publish Home until they exist. Clone the wiki into the scratchpad for preflight, not into the sibling folder.
- Evidence: session work folder `wiki-draft/Home.md` and `wiki-draft-notes/README.md` (is-an-image-url, 2026-09-28)
- Conflict 2026-09-28 (second is-an-image-url Home-only draft): this rule contradicts L-015 `home-only-check`, which says to leave out links to pages that don't exist yet and link README anchors instead. That run followed L-015. The user asked for one page, and a Home without red links can replace the placeholder at once. The planned page set went into the handoff note as the per-page lines still owed. `check --partial` exited 0. Settle the two entries into one rule at the next consolidation. A likely split: L-015 when Home may be published on its own, this entry when the full set follows in the same run.
- Update 2026-09-28 (third is-an-image-url Home-only draft): by then the full wiki was live (commit `8861236`, 10 pages), so this was `has-pages`, not a placeholder. `check --partial` on the draft folder gave 14 "link to missing page" errors for pages that did exist. The same draft laid over a scratch copy of the live wiki (L-107's method) passed with 0 errors, anchors included. When the pages exist, check that way and treat `--partial` errors as noise. Rerunning the saved verification script with no `RT`/`PM`/`V104`/`GOLDEN` differed from the saved output only in those skipped sections.
- Scope: skill (SKILL.md Step 6; references/page-sets.md Home row)
- Status: rejected on review 2026-09-28 (T-20260928-4): L-015 stands. A Home that may be published at once must not link pages that do not exist (red "create page" links), and L-016 keeps clones out of the scratchpad. Written by a headless eval run (L-017); kept here as the record of the conflict · helpful 0 · harmful 1 · last_confirmed 2026-09-28

### L-109 · 2026-09-28 · The overlay's list of wikis is a record, not the wiki's state (`record-is-not-state`)
- Trigger: T-20260928-4 action-2 run 1 (unhinted Home page for is-an-image-url) invoked the skill, read the overlay and the inventory's "Wikis" row ("owed"), and never ran preflight or any ls-remote; the other skill run did. Reproduced 0 of 3 in fresh contexts (tune runs), so flaky: 1 of 5 runs in all (2026-09-28).
- Hypothesis: a row saying "owed" reads like an answer to "does the wiki exist?", so Step 1 looks already done; the placeholder a maintainer saved minutes earlier is invisible to the record.
- Rule: Step 1 runs even for a draft of one page and even when the overlay says owed or done; the overlay tells where things live, ls-remote tells what exists.
- Evidence: T-20260928-4 (a2run1 trace; tune1 to tune3 traces); SKILL.md Step 1
- Scope: skill (SKILL.md Step 1)
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-09-28

### L-110 · 2026-09-28 · NuGet wikis show outputs in comments; 0.2.0's check read none of them (`outputs-in-comments`)
- Trigger: bringing the RandomNameGeneratorLibrary wiki under the saved-output rule, `outputs` 0.2.0 found 0 of its 28 outputs: they are shown as `// "Marguerita"`, `// always "Alisa Streets"`, F# `// Boardman`, PowerShell `# 88799`, and as comment lines closing a code block (`// Kerry Marrello from La Plena comunidad`); only `//=>` was read. JsonPrettyPrinter's showed `// {"a":[1,2]}` and code followed directly by its untagged output (2026-09-28).
- Hypothesis: C#, F# and PowerShell have no REPL echo convention; writers put the value in a comment, quoted, after a print call, or in a closing comment run.
- Rule: the helper reads a comment value when it is quoted, JSON-like, a number or a literal, or follows a print call or a PowerShell expression, and a closing run of comment lines as the block's output; bare words after other calls stay explanations, so pages quote such values or write `// =>`. Commands after a code block get a fence tag (```sh), or they read as output.
- Evidence: labs/DotNetRandomNameGenerator ai-docs note ("Brought under the saved-output rule"), wiki f0bb65b; labs/DotNetJsonPrettyPrinter wiki a8c5574; tests OutputFormsTests
- Scope: skill (scripts/wikiwright.py outputs; SKILL.md Step 6; references/nuget.md)
- Status: promoted: C-20260928-4 · helpful 2 · harmful 0 · last_confirmed 2026-09-28

### L-111 · 2026-09-28 · Unseeded examples: print the value after checking it is on its list (`membership-for-random`)
- Trigger: RandomNameGeneratorLibrary's Home and Getting started show unseeded answers ("for example "Prophetstown""); no run can print them again, so a saved output cannot contain them, and skipping them would leave 11 values unverified (2026-09-28).
- Hypothesis: for a random draw the claim a page makes is "this is a possible answer", which a membership check proves.
- Rule: the program prints each unseeded example only after checking it is on the list the method draws from (NOT ON THE LIST otherwise), labelled as such; a snippet whose first line is random prints a stable placeholder after the same check, so the saved output stays identical between runs (L-022).
- Evidence: labs/DotNetRandomNameGenerator ai-docs/notes/2026-09-28-wiki-verify.cs (`Possible`); templates/nuget/wiki-verify.template.cs
- Scope: skill (templates, SKILL.md Step 4)
- Status: promoted: C-20260928-4 · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-112 · 2026-09-28 · Node's environment proxy tunnels http: with CONNECT (`fetch-proxy-connect`)
- Trigger: verifying a proxy recipe for is-an-image-url, a child run with `NODE_USE_ENV_PROXY=1 HTTP_PROXY=<stand-in>` printed `false` and never exited: the stand-in got `CONNECT images.invalid:80`, which a plain `http.createServer` does not answer (Node 24.18.0, 2026-09-28).
- Hypothesis: Node's built-in proxy support for fetch uses CONNECT tunnels for every target.
- Rule: a stand-in proxy answers `connect` with `200 Connection Established` and hands the socket to the fixture server (`server.emit('connection', socket)`); use an `.invalid` host so the direct attempt can never reach the internet.
- Evidence: is-an-image-url ai-docs/notes/2026-09-28-wiki-verify.mjs (proxy section); references/npm.md
- Scope: env:node (references/npm.md)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-113 · 2026-09-28 · A golden capture with its own fixture server is replayed as a child process (`replay-requesting-capture`)
- Trigger: is-an-image-url's `test/golden/capture-1.0.4.cjs` starts its own `fixture-server.cjs`, requires `codec.cjs` and `is-image-300`, and hard-codes 1.0.4's `cli.js` and dependency list; it was the first replay for a package that makes requests (2026-09-28).
- Hypothesis: the capture is a self-contained program; the wiki script only needs its JSON.
- Rule: copy the capture and its helpers beside each installed version, patch only the lines the new layout breaks (the CLI path, a dependency lookup that tolerates missing packages), run each version as a child process one after the other (timing cases), and compare the answer, the callback timing and the request lines apart. 1.0.4 today: 82 of 82 identical; 2.0.0: 68 of 82 answers, the 14 others each a CHANGELOG line.
- Evidence: is-an-image-url ai-docs note ("How the examples were verified"); templates/npm/wiki-verify.template.mjs (golden replay section)
- Update 2026-09-29 (markdown-plain-link-replacer, the first replay through a recording proxy with TLS): 1.1.16 today 154 of 154 calls and 18 of 18 CLI runs identical. 2.0.0 needed four patched copies: the bin from package.json, a tolerant dependency lookup, undici's `EnvHttpProxyAgent` installed after the capture sets the proxy variables (in the capture and through `NODE_OPTIONS=--require` in its CLI children; `NODE_USE_ENV_PROXY=1` alone fails because Node reads the variables at startup), and a fixture copy that serves `CONNECT host:80` in plain HTTP (Node and undici tunnel http links). `NODE_TLS_REJECT_UNAUTHORIZED=0`, set by the capture at run time, is read per connection and covered the certificate. Compare request lists without the CONNECT lines and without how each request arrived; mask link titles when a dependency's new major reads titles differently (55 calls differed only there). package-modernize C-20260929-1 makes future captures replay without the first two patches.
- Scope: skill (templates, references/page-sets.md)
- Status: promoted: C-20260928-4 · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-114 · 2026-09-28 · `check` slugged headings with their inline code blanked (`heading-code-slug`)
- Trigger: `check` on the is-an-image-url wiki reported "no heading for #deno-answers-false-for-every-url" although FAQ has "## Deno answers `false` for every URL"; `headings()` read the line after `strip_code`, which blanks inline code (2026-09-28).
- Hypothesis: strip_code exists to skip fences and code spans in links; GitHub's anchor keeps the code text.
- Rule: fixed: headings are matched on the original line, with strip_code used only to skip fenced blocks; test HeadingAnchorTests.
- Evidence: C-20260928-4; tests/test_wikiwright.py
- Scope: skill (scripts/wikiwright.py check)
- Status: promoted: C-20260928-4 · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-115 · 2026-09-29 · Route fetch to the fixture by header when output derives from the host (`route-fetch-preload`)
- Trigger: drafting a Home page for markdown-plain-link-replacer 2.0.0. Its default output is `"[title](url)", *source*`, where `source` is the link's registrable domain. For a fixture link `http://127.0.0.1:<port>/` the source is `127.0.0.1`, so mapping the address to `https://example.com` (what `outputs` does) would still leave a wrong `*127.0.0.1*` on the page (2026-09-29).
- Hypothesis: address substitution only works when nothing in the output is computed from the host. A package that names the site, groups by domain or checks the TLD needs the real URL to reach it.
- Rule: run each example as a child process with `node --import ./route-fetch.mjs`, a preload that wraps `globalThis.fetch`. The wrapper sends every request to the fixture's base URL with the URL it meant in an `x-fixture-url` header, and the fixture routes by that header. Pages then show real URLs and real host-derived values exactly as printed, with no substitution. This only works when the package calls the global `fetch` at call time. The repository's own `test/helpers/web.js` did the same, so read the test helpers before building the fixture. State on the page that the pages were fixtures shaped like the real sites.
- Evidence: session work folder `wiki-draft-notes/` (route-fetch.mjs, wiki-verify.mjs, wiki-verify.out.txt; markdown-plain-link-replacer, 2026-09-29). Same output on Node 24.18 and 20.20. The scratchpad clone of the placeholder wiki (a path of about 150 characters) worked again, a further counter-case to L-016 (the entry said L-013; corrected on review).
- Scope: skill (templates/npm/wiki-verify.template.mjs fixture section; SKILL.md Step 4)
- Update 2026-09-29 (second markdown-plain-link-replacer Home-only draft): the library cases need no child process. Calling the same wrapper in-process, before the first call, worked on Node 24.18.0 and 20.20.2 (via `npx -y node@20`). The page's `npx markdown-plain-link-replacer "..."` ran as written through a shell with `NODE_OPTIONS=--import <file URL of route-fetch.mjs>` and `FIXTURE_BASE`, so the command shown is the command verified. The fixture server's request log is the evidence for "never requested" claims (the markdown link and the code span made no request). Evidence: the work folder's `ai-docs/notes/2026-09-29-wiki-verify.mjs` and `.out.txt`.
- Review 2026-09-29 (T-20260929-1): written by headless eval runs (L-017); kept. The real run the same day took the other route, a proxy by host name with TLS (L-116), because it also covers Deno, Bun, the package managers and the 1.1.16 child processes, and exercises the transport the package really uses; the header wrapper is the lighter choice when only Node runs and the package calls the global `fetch`.
- Status: active · helpful 2 · harmful 0 · last_confirmed 2026-09-29

### L-116 · 2026-09-29 · A package that requests by host name through its dependencies: a proxy with TLS, trusted at start (`by-host-name-proxy`)
- Trigger: markdown-plain-link-replacer 2.0.0 looks each link up through get-title-at-url and is-an-image-url with the runtime's `fetch`, and its output names the link's site, so the fixture address cannot stand in for the real one (L-115). The fourth run served every page under its real host name behind a stand-in proxy. Measured (2026-09-29): Node 24.18.0's `fetch` uses `HTTP_PROXY`/`HTTPS_PROXY` only with `NODE_USE_ENV_PROXY=1`, and reads both at startup (setting them in `process.env` later did nothing); Node 20.20.2 has no such variable, and undici 7.30.0's `EnvHttpProxyAgent` preloaded with `--require` worked on both; `NODE_EXTRA_CA_CERTS` is read at startup too, so 1.1.16's examples ran as a child; Deno 2.9.6 and Bun 1.4.2 read the proxy variables themselves (`DENO_CERT`, `NODE_EXTRA_CA_CERTS` for the CA); Deno's TLS refused a single self-signed certificate marked as a CA as the server's own, so the script makes a throwaway CA and a server certificate it signs; `NODE_OPTIONS` read `C:\...\guard.cjs` with the backslashes dropped, so preload paths go in with forward slashes; an untrusted certificate leaves https links unchanged silently.
- Hypothesis: every runtime has its own switch for proxies and trust, and most read it once at startup; a package that swallows lookup failures turns every routing mistake into "the link was left", which looks like behaviour.
- Rule: the npm template's "by host name" section: serve pages keyed by host and path from a plain and a TLS server behind a CONNECT proxy that routes by port (443 to TLS, any other to plain), make a CA and a server certificate with openssl, set the variables before each child starts, pick Node's route by a probe to an `.invalid` host, and guard every child (L-117). Print one case that shows a lookup reached the fixture (the request list) so a silent routing failure cannot pass for behaviour.
- Evidence: markdown-plain-link-replacer ai-docs/notes/2026-09-29-wiki-verify.mjs and its outputs (Node 24.18.0 and 20.20.2 identical apart from the routing line and the `NODE_USE_ENV_PROXY` recipe)
- Scope: skill (templates/npm/wiki-verify.template.mjs, references/npm.md, references/page-sets.md, SKILL.md Step 4)
- Status: promoted: C-20260929-1 · helpful 1 · harmful 0 · last_confirmed 2026-09-29

### L-117 · 2026-09-29 · A socket guard must read the options `net.connect()` passes inside an array (`guard-normalised-args`)
- Trigger: the fourth run's guard (the golden capture's form: wrap `net.Socket.prototype.connect`, throw unless `args[0].host` is 127.0.0.1) refused `https.get` but not `fetch('http://example.com/')`, which answered 200 from the real site on Node 20.20.2 and 24.18.0. Before the fix, a route probe and a few plain http lookups in the first Node 20 run reached example.com and starwars.wikia.com; no page output came from them (2026-09-29).
- Hypothesis: `net.connect()` calls `socket.connect()` with its arguments normalised into one array, `[options, callback]`; `tls.connect()` passes an options object.
- Rule: read `Array.isArray(args[0]) ? args[0][0] : args[0]`; probe with an `.invalid` host, never a real one; test the guard once (an `.invalid` request must fail with the guard's message, not `ENOTFOUND`). package-modernize carries the same fix for captures (its L-124).
- Evidence: markdown-plain-link-replacer ai-docs/notes/2026-09-29-wiki-verify.mjs (guard.cjs) and its note (Gotchas); package-modernize pull request #16
- Scope: skill (templates/npm/wiki-verify.template.mjs, references/npm.md)
- Status: promoted: C-20260929-1 · helpful 1 · harmful 0 · last_confirmed 2026-09-29

### L-118 · 2026-09-29 · In Git Bash, the npm `node` package's bin folder does not put its Node first (`oldest-node-path-trap`)
- Trigger: the get-title-at-url and is-an-image-url Node 20 runs (a subagent of the 0.4.0 session): the npm `node` package's `bin` folder holds a text file named `node` beside `node.exe`, so Git Bash skips that folder and a shell case run with it first on PATH used the system Node 24 without a warning (2026-09-29).
- Hypothesis: bash resolves `node` to the first file of that name and passes over the text file; Windows finds `node.exe` directly. The 0.4.0 template's `OLDEST_NODE` section puts exactly that folder first, so its shell cases can run on the wrong Node.
- Rule: copy `node.exe` alone into a scratch folder and put that first on PATH; print `node --version` from inside each shell case, and read the `installed` line of every rerun. Open work for 0.4.1: make the template do this. The markdown-plain-link-replacer Node 20 output's bash-loop section may have run on Node 24 (its output was the same either way).
- Evidence: the subagent's report of 2026-09-29; get-title-at-url and is-an-image-url notes (dated sections of 2026-09-29)
- Scope: skill (templates/npm/wiki-verify.template.mjs OLDEST_NODE, references/npm.md)
- Status: promoted: C-20260929-2 (the template copies the binary alone; `shell()` prints the Node) · helpful 2 · harmful 0 · last_confirmed 2026-09-29
- Addendum 2026-09-29 (get-title-at-url update-mode run, driven by hand from Git Bash): the copied folder must also go on PATH in POSIX form. `PATH="C:/.../node20:$PATH"` splits at the drive letter's colon, and the run silently used Node 24.18.0 again; `PATH="$(cygpath -u "$dir"):$PATH"` ran 20.20.2. The `installed` line caught it. Confirmed 2026-09-29 (sixth get-title-at-url draft): the same `C:/` PATH entry ran Node 24.18.0 again, and `diffout` against the saved Node 20 output showed the `installed` line changed. The template's `OLDEST_NODE` avoids it; a hand-driven run from Git Bash does not.
- Addendum 2026-09-29 (stack-exchange-markdown-retriever Home-only draft): the template's PATH fix does not reach `npx`. On Windows `npx.cmd` runs the `node.exe` installed beside it (Node 24.18.0 here), not the first `node` on PATH, so a page's `npx <bin> ...` case in the `OLDEST_NODE` rerun still ran on Node 24. Run the bin once more with `process.execPath` (`node --import <preload> <pkg>/<bin> ...`) so the oldest line really runs the command; the draft's `2026-09-29-wiki-verify.mjs` does.

### L-119 · 2026-09-29 · diffout gaps found on its first use (`diffout-first-use`)
- Trigger: the same Node 20 runs: `diffout` crashed with UnicodeEncodeError on a cp1252 console when an output held C1 characters (worked with `PYTHONIOENCODING=utf-8`); `--save` normalises ports but not local paths in stderr lines (Node 20's "bad option" line names `node.exe`); and `outputs` cannot mark a block as true on one Node line only, so a Node-24-only block reports missing against the Node 20 output (2026-09-29).
- Hypothesis: the helper printed with the console's encoding; the saved-output rules (L-022) were applied to ports only.
- Rule: until 0.4.1, run diffout with `PYTHONIOENCODING=utf-8` and mask paths with `--mask`; check pages against the main output and read the oldest-Node diff by hand. 0.4.1: reconfigure stdout to UTF-8 with replacement, mask the user's home and temp paths on `--save`, and a `<!-- outputs: node>=N -->` marker or a per-output list.
- Evidence: the subagent's report of 2026-09-29
- Scope: skill (scripts/wikiwright.py diffout, outputs)
- Status: promoted: C-20260929-2 (UTF-8 stdout, path masks, `<!-- outputs: node>=N -->`) · helpful 1 · harmful 0 · last_confirmed 2026-09-29

### L-120 · 2026-09-29 · A replay that differs on another runtime: bisect the harness first (`bisect-the-harness`)
- Trigger: is-an-image-url's golden replay of 2.0.0 gave 65/45/64 on Node 20.20.2 against 68/45/77 on Node 24.18.0. Bisected to `capture-1.0.4.cjs`: it calls `dropConnections()` after every case without the 30 ms wait the repository's functional test has, so Node 20's fetch reused a dead socket, got ECONNRESET and 13 calls answered false (2026-09-29; package-modernize L-023 knew the trap).
- Hypothesis: a capture written for the old version carries no workarounds for the new one's transport.
- Rule: when a replay differs between runtimes, reproduce the smallest case and check the harness before writing a behaviour difference on a page; scope the page's replay counts to the Node line they ran on.
- Evidence: is-an-image-url ai-docs/notes/2026-09-28-github-wiki.md (dated section of 2026-09-29), wiki c6d5f1b
- Scope: skill (references/page-sets.md golden replay)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-29

### L-121 · 2026-09-29 · When the output is remote content, record one live answer and replay it (`record-once-replay`)
- Trigger: a Home-only draft for stack-exchange-markdown-retriever 2.0.0 asked for "a working example and its real output". The package's output is the post's markdown, and the repository's fixture serves made-up markdown under the README's example id (127968), so fixture output on the page would not be what a reader gets (2026-09-29).
- Hypothesis: "never the internet" protects reproducibility and quotas; it did not foresee a package whose whole output is the remote content. L-014 and L-115 fix the address in the output, not the content.
- Rule: make one live request through the published package with a `fetch` wrapper that saves the raw answer (URL, status, date, body), then replay that recording from a local server in the verification script, refusing every other origin. Date the output on the page ("as the API returned it on DATE; posts can be edited"), save the recording and the recorder with the script, and re-record before an update. Keep live requests to the pages' examples (one here) and within the API's quota.
- Evidence: session work folder `repo-draft/ai-docs/notes/` (record-live.mjs, live-scifi-question-127968.json, 2026-09-29-wiki-verify.mjs; outputs identical on Node 20.20.2 and 24.18.0). Confirmed by a second Home-only draft the same day (`wiki-draft/verify/`): curl-recorded answers replayed through the repository's own `test/helpers/api.js` wrapper, and a `LIVE=1` case showed the library example and the page's `npx` command identical to the recording. A repository's ESM helper copied into a scratch project without `"type": "module"` fails with `SyntaxError: Unexpected token 'export'`: copy it as `.mjs` and change the import in `cli-preload.mjs` to match.
- Update 2026-09-29 (third Home-only draft, work folder `ai-docs/notes/2026-09-29-wiki-verify/`): the run first verified against the repository's fixture and wrote its made-up text onto the page, and only found this entry while checking LEARNINGS.md before Step 8. That was the same miss L-107 records: SKILL.md Step 4 still says "never the internet" with no pointer here. The redo recorded three answers with curl (the question on `site=scifi` and on the domain form, and a missing id), then served them from a local server keyed by exact path and query. The `"type": "module"` fix was a `helpers/package.json` rather than renaming. Node 20.20.2 and 24.18.0 matched. With helpful at 3, promote this into Step 4 and have Step 2 read LEARNINGS.md.
- Scope: skill (SKILL.md Step 4 network rule; templates/npm/wiki-verify.template.mjs)
- Review 2026-09-29 (T-20260929-2): written by eval runs (L-017). The problem is real: the fixture serves made-up markdown under the README's real id, so an unlabelled output misleads. The route is rejected. Recording a live answer is a request to the real service, which Step 4 forbids, and which the maintainer forbade for this package's wiki. Three of the six skill runs sent between one and four such requests. L-122 has the replacement rule.
- Status: rejected (T-20260929-2; replaced by L-122) · helpful 0 · harmful 1 · last_confirmed 2026-09-29

### L-122 · 2026-09-29 · Remote content from a fixture is sample content: label it, never record the real answer (`sample-content-not-live`)
- Trigger: T-20260929-2, action-1 and action-2 against stack-exchange-markdown-retriever 2.0.0. Its output is a post's markdown, and the repository's fixture serves made-up markdown under real ids (127968 is a real scifi question). Three of six skill runs sent requests to api.stackexchange.com to put "real output" on the page. action-1-r1 used a recorder through the published package, action-1-r2 made four curl calls and `LIVE=1` cases, action-2-r1 made three curl calls. They wrote L-121 to justify it (2026-09-29).
- Hypothesis: Step 4 said "never the internet", but nothing covered a fixture whose content is invented. The runs weighed "real output" above the network rule, and the grader looked only at installs and outputs.
- Rule: the page shows what the package printed for the local stand-in, says next to the output that it came from a stand-in serving sample content, and links the real post. No request to the real service, not even one to record. The grader takes the service's host (`forbid.txt`, `--forbid-host`) and fails a run whose trace has a curl-like command naming it or a `LIVE=` switch. A recorder run through the package names no host, so read its trace as well.
- Evidence: TESTS.md T-20260929-2 (traces in the run folders); evals/grade-action.py `live_requests`
- Scope: skill (SKILL.md Step 4), skill tests
- Status: promoted: C-20260929-3 · helpful 0 · harmful 0 · last_confirmed 2026-09-29

### L-123 · 2026-09-29 · On Gitea and Forgejo a push never creates the wiki; the API's first page does (`api-seeds-gitea-wiki`)
- Trigger: measuring the hosts for 0.5.0. On Gitea 1.27.3 and Forgejo 16.0.5, `git push` of a fresh wiki repository was refused on `main` and on `master`: Gitea's `info/refs` answered 500, Forgejo's an empty advertisement. `POST /api/v1/repos/{o}/{r}/wiki/new` with a token answered 201, and git worked from then on (2026-09-29).
- Hypothesis: both hosts create the wiki's git repository only in their page-writing code path, so the first page has to go through the web UI or the API.
- Rule: preflight reports `no-wiki-repo` with two ways out: `--seed` with `WIKIWRIGHT_TOKEN` (the API POST), or the maintainer's first page at `/{o}/{r}/wiki/?action=_new`. After that, push to the branch `ls-remote --symref` names (new wikis `main`). Unlike GitHub, no browser is needed.
- Evidence: R-20260929-1; `preflight --seed` against both local instances (201, then `STATE: exists`)
- Scope: skill (references/hosts.md, scripts/wikiwright.py preflight)
- Status: promoted: C-20260929-4 · helpful 1 · harmful 0 · last_confirmed 2026-09-29

### L-124 · 2026-09-29 · A status code alone cannot tell an empty Gitea wiki from a live one (`status-is-not-state`)
- Trigger: on both hosts every wiki URL answered 200 before a first page existed ("Welcome to the wiki"), and a missing page answered 303 to `?action=_pages`, which answers 200. A checker that follows redirects, or looks only at status codes, passes a wiki that is not there (2026-09-29).
- Hypothesis: the hosts render an empty state or the page list instead of an error.
- Rule: `live` reads the page API first (404 until a page exists) and requires each page in its list, never follows redirects, and treats 303 as missing. GitLab's page HTML is rendered by JavaScript, so the same rule applies there: its wiki API decides.
- Evidence: R-20260929-1; `live` against the local instances failed the unreachable `Spaced Name` page with 303, and passed Codeberg's `dnkl/foot` (3 pages, sidebar and footer found)
- Scope: skill (scripts/wikiwright.py live)
- Status: promoted: C-20260929-4 · helpful 1 · harmful 0 · last_confirmed 2026-09-29

### L-125 · 2026-09-29 · Each host names its navigation files and slugs its anchors its own way (`host-page-rules`)
- Trigger: the hosts differ from GitHub where `check` had hard rules. GitLab reads `_sidebar.md` in lower case and ignores an extensionless `_sidebar`, and shows no footer. Gitea and Forgejo resolve wikilinks, but a file name with a space is listed and unreachable, and a file in a folder is not listed. Forgejo collapses repeated hyphens in anchors (`usage-basic-more`, where GitHub and Gitea give `usage-basic--more`). Azure DevOps has neither sidebar nor footer and orders pages by `.order` (2026-09-29).
- Hypothesis: the page set carries over; the file conventions do not.
- Rule: `check --host KIND` applies them: navigation files per host, wikilinks a warning on the hosts that resolve them, spaces and folders an error on Gitea and Forgejo, Forgejo's anchor slug. Put the version line on Home where there is no footer.
- Evidence: R-20260929-1; `check --host gitea` and `--host forgejo` on clones of the local `wiki-seeded` wikis
- Scope: skill (scripts/wikiwright.py check, references/hosts.md "Page sets on these hosts")
- Status: promoted: C-20260929-4 · helpful 1 · harmful 0 · last_confirmed 2026-09-29

### L-126 · 2026-09-29 · Anonymous GitLab project JSON has no wiki fields (`gitlab-anonymous-wiki-state`)
- Trigger: hosts.md said to read `wiki_access_level` to see whether a GitLab wiki is on. Anonymously, `GET /api/v4/projects/:path` returns no wiki field at all, on gitlab.com and on a local CE; with a token it has `wiki_access_level` and `wiki_enabled` (2026-09-29).
- Hypothesis: GitLab hides feature settings from callers without a role.
- Rule: without a token, read the wiki's state from `ls-remote` of `PATH.wiki.git` (refs: readable; no refs: enabled and empty, a push creates it; 401: off or members-only) and the wiki API's status. Preflight does this.
- Evidence: R-20260929-1 (gitlab-runner, graphviz, gitlab-org/gitlab, inkscape; local CE)
- Scope: skill (scripts/wikiwright.py preflight, references/hosts.md)
- Status: promoted: C-20260929-4 · helpful 1 · harmful 0 · last_confirmed 2026-09-29

### L-127 · 2026-09-29 · A stand-in proxy needs NO_PROXY to name the loopback (`no-proxy-loopback`)
- Trigger: package-modernize's replayable capture setup (its PR #19, L-125) found that with `NO_PROXY` empty, Node 24.18.0's own proxy support under `NODE_USE_ENV_PROXY=1` also sent request 2.88's connection to the stand-in proxy through the proxy, and the recorded request lines changed. wikiwright's host-fixture kit set `NO_PROXY=''` too, and this run replays 1.1.7 (request 2.88) as a child (2026-09-29).
- Hypothesis: an empty `NO_PROXY` proxies even connections to 127.0.0.1, the proxy's own address.
- Rule: the kit sets `NO_PROXY` and `no_proxy` to `127.0.0.1,localhost,::1`. The page hosts are real names, so they still go through the proxy.
- Evidence: package-modernize L-125 and its self-test (fails two checks with `NO_PROXY` empty); tests/host-fixture.test.mjs passed after the change
- Scope: skill (templates/npm/host-fixture.mjs)
- Status: promoted: C-20260929-4 · helpful 1 · harmful 0 · last_confirmed 2026-09-29 (the fifth run's 1.1.7 replay through the kit: 90 of 90 request lines identical)

### L-128 · 2026-09-29 · Behind a proxy that drops CONNECT, fetch retries until its timeout (`connect-retry-leak`)
- Trigger: the fifth run's golden replay of stack-exchange-markdown-retriever's `capture-1.1.7.cjs` against 2.0.0. In the case "connection dropped during the tunnel", 1.1.7 (request 2.88) failed at once, but 2.0.0's fetch sent CONNECT again and again until the call's timeout: more than 100 CONNECTs in 2 seconds, and about 18,000 in 5 seconds in a side probe. No callback came within the capture's 10 seconds, and late retries landed in the next CLI case's request list, so the count of identical CLI request lines moved between runs (16 or 17 of 20) (2026-09-29).
- Hypothesis: undici treats a closed tunnel socket as a retryable connection failure and has no backoff, so the loop ends only at the abort.
- Rule: in a replay, count request lines per case window and expect leakage after a dropped-tunnel case. Put the difference on the page as behaviour (2.0.0 waits for its timeout where 1.1.7 failed at once), and do not treat the moving count as a Node-line difference. A capture or script should close the case's connections and wait before the next case.
- Evidence: stack-exchange-markdown-retriever ai-docs/notes/2026-09-29-github-wiki.md and its log (the hang-up finding); the run's report
- Scope: skill (templates/npm/host-fixture.mjs header, references/page-sets.md golden replay)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-29

### L-129 · 2026-09-29 · The host-fixture kit's first run: runtimes, npx, the CLI's environment and the agent's sockets (`kit-first-run`)
- Trigger: the fifth real run used `templates/npm/host-fixture.mjs` for the first time and reported six gaps (2026-09-29).
  1. Deno 2.9.6 runs `--require` preloads from `NODE_OPTIONS`: on the Node 20 route it loaded the undici preload and died on an env permission.
  2. The guard reaches Node children only; the run gated Deno and Bun with an `.invalid` fetch through the proxy.
  3. The template's `cli()` took no environment, so the CLI could not reach the kit.
  4. `npx` under the kit's environment gave npm itself the guard and the proxy; it needed a warm-up with a plain environment, then `--offline`.
  5. `routeThisProcess()`'s ProxyAgent kept the process alive, and there was no way to close it.
  6. The template's golden section compared whole entries, mixing answers, timing and requests.
- Hypothesis: the kit was extracted from a run that used Node children only through `fx.env`; each runtime reads the environment its own way.
- Rule: the kit returns `runtimeEnv` (without `NODE_OPTIONS`) for Deno and Bun, documents the `.invalid` gate and the npx warm-up, and closes its agent in `close()`. The template's `cli()` takes `CLI_ENV` (set to `fx.env`), and the golden section counts answers, timing and requests apart.
- Evidence: the fifth run's report (items 2 to 7); stack-exchange-markdown-retriever ai-docs/notes/2026-09-29-wiki-verify.mjs; tests/host-fixture.test.mjs (runtimeEnv)
- Scope: skill (templates/npm/host-fixture.mjs, templates/npm/wiki-verify.template.mjs)
- Status: promoted: C-20260929-5 · helpful 1 · harmful 0 · last_confirmed 2026-09-29
