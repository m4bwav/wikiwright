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
- Evidence: draft-only Home run for get-title-at-url, 2026-09-28. Counter-case, same day: the seeded-random-utilities draft-only run cloned its placeholder wiki into a scratchpad path of about 150 characters without error, so the limit depends on the scratchpad's length, not on the scratchpad as such. The rule stands as the safe default.
- Scope: env:windows
- Status: active · helpful 2 · harmful 0 · last_confirmed 2026-09-28

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
- Evidence: this run's work folder `ai-docs/notes/2026-09-28-wiki-home-draft.md`; confirmed by a second seeded-random-utilities draft-only run the same day, where README section anchors (checked for `id="user-content-…"` on the repository page) stood in for the unwritten pages; and by a third such run the same day (same two errors only, seven README anchors all present)
- Scope: skill
- Status: active · helpful 3 · harmful 0 · last_confirmed 2026-09-28

### L-017 · 2026-09-28 · Headless eval runs write to the skill under test and see the session's files (`evals-touch-the-source`)
- Trigger: during T-20260928-3, two action runs (skill arm) followed "capture learnings", read the overlay, which names the skill's source folder, and edited the source LEARNINGS.md (the entry now L-015 and a counter-case on L-016). One action-2 run answered "does the wiki exist" by `git fetch` in the sibling working copy this session had cloned minutes before, instead of preflight (2026-09-28).
- Hypothesis: a headless run has the same filesystem, overlay and plugin paths as the session that launched it, so anything the session made before the suite is part of the case.
- Rule: run the suite from a committed source tree and `git diff` it afterwards; review every eval-written entry (keep, renumber or drop) before committing. Create nothing a case can see (clones, notes, drafts) before the suite runs.
- Evidence: T-20260928-3; `git diff skills/wikiwright/LEARNINGS.md` mid-suite; the a2run1 trace
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
- Scope: env:any
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-022 · 2026-09-28 · Keep machine-dependent text out of a saved verification output (`machine-free-output`)
- Trigger: the seeded-random-utilities script first printed the error for a `Date` seed, whose message contains the date in the local time zone ("GMT-0600 (Central Standard Time)"); a saved output with it would differ on every other machine and fail the diff in update mode (2026-09-28).
- Hypothesis: seeded output is only diffable when nothing else in it depends on the machine (time zone, paths, ports, timings).
- Rule: replace or leave out time-zone text, absolute paths, ports and timings in the saved output; show such values on a page only from a case that prints a stable form.
- Evidence: seeded-random-utilities ai-docs note (Gotchas)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28
