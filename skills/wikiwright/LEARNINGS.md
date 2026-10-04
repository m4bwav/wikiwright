# Learnings: wikiwright

Procedural lessons for [SKILL.md](SKILL.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md (LEARNINGS-FORMAT). Retired and merged entries, and the full text of every entry shortened or merged in the 2026-09-29 and 2026-10-01 consolidations, are in [LEARNINGS-ARCHIVE.md](LEARNINGS-ARCHIVE.md); a promoted entry here keeps its rule and where the rule now lives.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first, by meaning (`evergreen.py search "<the lesson>" --kinds learnings` finds near-duplicates in every registered unit): add / update / retire / none. Trigger and Hypothesis are required. Promote after three confirmations; retire when harmful > helpful.

## Active

L-001 to L-006 were seeded on 2026-09-28 from the two wikis written by hand before this skill existed (RandomNameGeneratorLibrary and JsonPrettyPrinter, both NuGet); their evidence is those repositories' `ai-docs/notes/2026-09-28-github-wiki.md`. L-003 to L-005 are merged into L-002 and L-105.

### L-001 · 2026-09-28 · Pages with backslashes are written with a <BS> placeholder (`backslash-placeholder`)
- Rule: write every backslash that matters in a page as `<BS>`, convert with `wikiwright.py unbs`, and let `check` fail while one remains; count the placeholders before and after. Run unbs on pages only: a file that names the placeholder in prose (this one, SKILL.md) loses the name. Shipped docs written with agent tools can carry the same damage (format-json-files' README).
- Evidence: rule in SKILL.md Step 5 ("Backslashes") and Step 2; scripts/wikiwright.py (unbs, check); DotNetJsonPrettyPrinter note ("Writing-tool note")
- Status: promoted: C-20260928-1 · helpful 2 · harmful 0 · last_confirmed 2026-09-29

### L-002 · 2026-09-28 · The wiki repository exists only after a first page is saved in the web UI (`first-page-click`)
- Rule: GitHub creates the wiki repository only when someone saves a first page in the web UI; enabling the feature does not, and no API can. Run `preflight` (ls-remote, re-checked for 60 seconds after `--enable`) before writing, even for a draft of one page and even when the overlay lists the wiki as owed or done (the overlay says where things live, ls-remote says what exists), and ask for the click in the first message. Clone the placeholder, commit on it and `git push` without force (force only for a working copy begun with `git init`), to the branch ls-remote names (`master` on GitHub). Merges L-003 `wiki-branch-master`, L-010 `placeholder-fast-forward` and L-109 `record-is-not-state`.
- Evidence: rule in SKILL.md Step 1 and Step 7, references/publishing.md; DotNetRandomNameGenerator, get-title-at-url and seeded-random-utilities notes (2026-09-28); T-20260928-4 (1 of 5 runs skipped preflight, L-109)
- Status: promoted: C-20260928-1, C-20260928-2 (L-010), C-20260928-3 (resolved), C-20260928-4 (L-109) · helpful 3 · harmful 0 · last_confirmed 2026-09-28

### L-006 · 2026-09-28 · A markdown table cannot hold multi-line output (`table-cannot-hold-output`)
- Rule: input and output go in paired code blocks; tables only for one-line values (a GitHub table cell is one line, and `<br>` inside code does not break it).
- Evidence: rule in references/page-sets.md (conventions) and SKILL.md Step 5; the JsonPrettyPrinter wiki's Output format page
- Status: promoted: C-20260928-1 · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-007 · 2026-09-28 · Spawn the CLI asynchronously when the fixture server runs in the same process (`async-cli-with-fixture`)
- Rule: spawn the CLI asynchronously when the fixture server runs in the same process (`spawnSync` blocks the server), and close stdin (or write `input`) on every child: a CLI that reads stdin when it gets no argument waits for ever.
- Evidence: rule in templates/npm/wiki-verify.template.mjs (`cli()`, `run()`) and references/npm.md ("The CLI against the fixture"); get-title-at-url and markdown-plain-link-replacer runs
- Status: promoted: C-20260928-2, C-20260929-1 (stdin; marked promoted in the 2026-09-29 consolidation) · helpful 1 · harmful 0 · last_confirmed 2026-09-29

### L-009 · 2026-09-28 · Audit every sentence for its source before the check (`claims-audit`)
- Rule: Step 6 starts with one reread asking, per sentence, which output, source line, changelog entry or registry answer says it; cut what has none. Pages about old versions invite filling gaps from general knowledge.
- Evidence: rule in SKILL.md Step 6; get-title-at-url's first Versions draft (three inferred claims)
- Status: promoted: C-20260928-2 (marked promoted in the 2026-09-29 consolidation) · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-011 · 2026-09-28 · Run the old majors when there is no golden capture (`run-the-old-majors`)
- Rule: Versions and upgrading takes its evidence from runs today, not from the changelog. With a golden capture, replay its script against the old version installed today and against the current one, compare case by case and never rewrite the golden file; a capture that starts its own fixture server runs as a child process per version, with answers, timing and requests compared apart. Without one, install each old major in its own folder and run the same cases. A NuGet capture is a project that pins the old version: copy it, change only the pin, build once, run `--no-build -f <tfm>` per framework, and compare with the recording for the same runtime and OS (IsImageUrlDotNet, 2026-09-29: 117 of 117 answers and requests on three recordings). A synchronous capture replays with no patches; compare by parsed value, not bytes, with the header left out and `quirks` apart. Merges L-020 `replay-the-golden-capture` and L-113 `replay-requesting-capture`.
- Evidence: rule in SKILL.md Step 4, references/golden-captures.md (with "Synchronous golden captures"), references/npm-requests.md (proxy-recorded captures), the npm template's golden section; get-title-at-url, seeded-random-utilities, is-an-image-url, markdown-plain-link-replacer, replace-string-at-position (2026-09-30)
- Status: promoted: C-20260928-2, C-20260928-3 (L-020), C-20260928-4 (L-113), C-20260929-17 (NuGet), C-20260930-9 (synchronous captures) · helpful 3 · harmful 0 · last_confirmed 2026-09-30

### L-012 · 2026-09-28 · A plugin installed mid-session is not invocable; a user-skills junction is, after a delay (`midsession-skill-load`)
- Trigger: after `claude plugin install wikiwright@mark-local` the Skill tool answered "Unknown skill"; a junction in `~/.claude/skills/` became invocable a few seconds later. A second run found the Skill tool serving the SKILL.md text read at session start, even through a fresh junction, and `claude plugin update` keeping a stale cache while the version number was unchanged (Claude Code 2.1.281, Windows, 2026-09-28).
- Hypothesis: the user skills folder is watched with a short debounce; plugins and their SKILL.md text load at session start; the plugin cache is keyed by version.
- Rule: to exercise SKILL.md edits, run headless (`claude -p` reads the files at its own start) or follow the source by hand and say so. Before headless evals of an edited source, `claude plugin uninstall` and `install` again and compare the cached SKILL.md with the source (`wikiwright.py cachecheck`). A junction for a brand-new skill works after the listing shows it; remove it afterwards.
- Evidence: this repository's ai-docs log, 2026-09-28 (both runs); scripts/wikiwright.py (cachecheck)
- Scope: env:claude-code
- Status: active · helpful 2 · harmful 0 · last_confirmed 2026-09-28

### L-016 · 2026-09-28 · A wiki clone into the Claude Code scratchpad fails on Windows (`scratchpad-path-too-long`)
- Trigger: `git clone` of a wiki into the Claude Code scratchpad (a path of about 200 characters) failed with "Filename too long", and with `-c core.longpaths=true --template=` with "'$GIT_DIR' too big" (Windows 11, Git for Windows, 2026-09-28). Clones into scratchpad targets of about 140 to 150 characters worked on four later runs.
- Hypothesis: git's Windows path limit counts the whole `.git` path, so the target path's length decides, not the scratchpad as such.
- Rule: on Windows keep the clone target short: the sibling `<clone>.wiki`, a short temp folder, or a short folder name (`sem.wiki`) in the scratchpad. `git -C <copy> status -sb` plus preflight answer "does it exist" without cloning; for a draft-only request, preflight without `--enable`.
- Update 2026-09-29 (T-20260929-4, an IsImageUrlDotNet Home draft): clones at about 150 characters worked, but `dotnet test` of a repository clone there failed the net48 golden test with `FileLoadException ... nunit.framework ... The filename or extension is too long` while net10.0 passed. Run a repository's own tests from a short path too, or record the failure as environmental.
- Evidence: get-title-at-url draft-only Home run (2026-09-28); counter-cases on seeded-random-utilities, is-an-image-url (twice), markdown-plain-link-replacer and stack-exchange-markdown-retriever runs; evals/run-suite.sh; T-20260929-4 (`ww9/suite`)
- Scope: env:windows
- Status: active · helpful 4 · harmful 0 · last_confirmed 2026-09-29

### L-014 · 2026-09-28 · Replacing the fixture address can change console.log layout (`substitution-changes-layout`)
- Trigger: drafting a get-title-at-url Home page, `console.log(result)` printed `{ title, url, status }` on one line for `https://example.com/` but over four lines for the fixture's `http://127.0.0.1:<port>/` (Node 24.18, 2026-09-28). The same break hit a Recipes `//=>` line on 2026-09-29 (L-131).
- Hypothesis: Node's util.inspect breaks an object over lines once its one-line form passes about 72 characters, so a longer or shorter address changes the layout, not just the text.
- Rule: replace the fixture address with a real-looking one only in output whose layout does not depend on length (JSON with indent, the CLI's `--json`, plain strings); when the page shows one line, print with `util.inspect(value, {breakLength: Infinity})`; or serve the real host names (L-116).
- Evidence: get-title-at-url draft-only Home run (its work folder's `ai-docs/notes/2026-09-28-wiki-home-draft.md` and `home-verify.out.txt`); L-131
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-013 · 2026-09-28 · A skill's own run can teach the baseline; grade on the route, not the location (`baseline-learns-from-run`)
- Rule: point action cases at a repository the skill has not touched (no wiki, no wiki note); give every action case an unhinted twin worded as a user would type it, and treat the hinted one as a regression check; grade verification by the install command in the trace, not by where a file was saved. Merges L-018 `unhinted-action-prompt`.
- Evidence: T-20260928-2, T-20260928-3; evals/evals.json (action-1, action-2); evals/run-action.sh
- Status: promoted: evals/run-action.sh (its header: a target the skill has not touched) and evals/evals.json (hinted and unhinted twins) · helpful 2 · harmful 0 · last_confirmed 2026-10-01

### L-015 · 2026-09-28 · A Home-only draft fails `check` on the sidebar and footer by design (`home-only-check`)
- Rule: for a Home-only draft run `check --partial` (0 errors expected). Leave out links to unwritten pages; link README anchors (checked for `id="user-content-…"` on the repository page), the CHANGELOG, registry and issues instead, and list the planned pages in the note as owed. L-108 `home-only-draft`, which linked them, was rejected.
- Evidence: seeded-random-utilities (three drafts), is-an-image-url and stack-exchange-markdown-retriever (two) Home-only drafts; C-20260928-3 (`--partial`); T-20260928-4
- Status: promoted: C-20260928-3 (`check --partial`, SKILL.md Step 6) · helpful 6 · harmful 0 · last_confirmed 2026-09-29

### L-017 · 2026-09-28 · Headless eval runs write to the skill under test and see the session's files (`evals-touch-the-source`)
- Trigger: in T-20260928-3 two skill runs edited the source LEARNINGS.md (the overlay names the source folder), and one answered "does the wiki exist" from a clone this session had made minutes before. In T-20260929-1 and after the sixth run a stray `skills/wikiwright/package.json` appeared: `npm init -y --prefix <scratch>` writes into the current folder, and a subagent had inherited the session's folder after one `cd` (2026-09-28, 2026-09-29).
- Hypothesis: a headless run or a subagent shares the session's filesystem, overlay, plugin paths and current folder; `npm init` ignores `--prefix` for `package.json`.
- Rule: run the suite from a committed source tree and create nothing a case can see before it runs; afterwards `git status --short` (not only `git diff`), review every eval-written entry (keep, renumber or drop) and delete what runs created. Never `cd` in a shell call; run `npm init` from a script that changes to its own folder, or write `package.json` with the editor. Merges L-134 `npm-init-prefix-cwd`.
- Evidence: T-20260928-3 (the a2run1 trace), T-20260929-1; evals/run-suite.sh; references/npm.md ("The scratch project")
- Scope: skill tests, env:agent-harness
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-09-29

### L-019 · 2026-09-28 · A saved script that does not print the pages' forms cannot re-verify them (`save-the-output-too`)
- Rule: the verification script prints every output in the form the page shows it (`console.log`, a REPL echo, `Console.WriteLine`; never converted by hand) and nothing that depends on the machine (time zones, absolute paths, ports, timings). Its output is saved beside it with the port as `<port>`; `outputs` passes before publishing and again in update mode; output that cannot come from the script carries `<!-- outputs: skip (reason) -->`. Merges L-008 `print-as-the-page-shows` and L-022 `machine-free-output`.
- Evidence: rule in SKILL.md Step 4 and Update mode step 3, references/page-sets-seeded.md, references/npm.md (Traps); get-title-at-url rehearsal (wiki 2807e56), seeded-random-utilities note
- Status: promoted: C-20260928-3 (L-008: C-20260928-2) · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-021 · 2026-09-28 · Deno, Bun, pnpm and yarn run from npm on a machine without them (`runtimes-from-npm`)
- Rule: before writing "not tested" for Deno, Bun, pnpm or yarn, run them from npm (`npm install deno bun`, corepack for pnpm and yarn) and print each tool's version from the script. Yarn 4 examples run through `yarn node`; spawn `.cmd` shims with `shell: true` or the `.exe` directly; pass `RT` as an absolute path; keep Deno's folder away from a `package.json` whose `node_modules` lacks the package; print a runtime snippet's error branch too, so a missing `--allow-net` shows.
- Evidence: rule in SKILL.md Step 4 and references/npm.md ("Other runtimes and package managers"); seven runs, 2026-09-28 to 2026-09-29
- Status: promoted: C-20260928-3 (marked promoted in the 2026-09-29 consolidation) · helpful 7 · harmful 0 · last_confirmed 2026-09-29

### L-104 · 2026-09-28 · Adopting a hand-written wiki: the old program covers only part of the pages (`adopt-unsaved-wiki`)
- Rule: adopting a wiki with no saved output: run its program as it is against the version the footer names (twice), save the output LF-normalised, run `outputs`, fold every missing case into the program (or mark the block skip with a reason), then bump the version; record which pages the program did not cover.
- Evidence: rule in SKILL.md Update mode step 3 and the hand-over paragraph; the JsonPrettyPrinter and RandomNameGeneratorLibrary retrofits
- Status: promoted: C-20260928-4 · helpful 2 · harmful 0 · last_confirmed 2026-09-28

### L-105 · 2026-09-28 · A C# verification program on Windows prints CRLF, and runs on one runtime only (`csharp-verify-program`)
- Rule: a C# verification program is a .NET 10 file-based app with `#:property PublishAot=false` (native AOT is the default and disables reflection-based System.Text.Json); one `dotnet run` per file at a time (or `dotnet build` once and `--no-build`); save its output with LF; take per-runtime facts (.NET Framework) from the repository's golden recordings or a net48 project, and say which runtime an example ran on. Merges L-004 `file-based-app-aot` and L-005 `dotnet-run-contention`.
- Evidence: rule in references/nuget.md and templates/nuget/wiki-verify.template.cs; DotNetJsonPrettyPrinter note and tests/Golden
- Status: promoted: C-20260928-4 (L-004, L-005: C-20260928-1) · helpful 2 · harmful 0 · last_confirmed 2026-09-28

### L-106 · 2026-09-28 · Run the npm verification script on the oldest supported Node too (`oldest-node-run`)
- Rule: run the npm script on the oldest Node line in `engines` too and diff it with the main run; every difference is a claim to scope by version or a case to fix. Use the template's `OLDEST_NODE` (a copied `node.exe` alone in a per-platform folder, first on PATH) and `diffout` (it counts `shell node:` versions and warns on a mix). By hand in Git Bash, put that folder on PATH in POSIX form (`cygpath -u`); `npx` runs its own Node, so run the bin with `process.execPath` too. An unpublished draft is not a fix: compare the live wiki with earlier drafts before starting, and when sibling drafts differ only in scope, merge them. Merges L-118 `oldest-node-path-trap` and L-119 `diffout-first-use`.
- Evidence: rule in SKILL.md Step 4 and Update mode step 3, references/npm.md (the oldest Node), the npm template (`OLDEST_NODE`, `OLDEST_NODE_BIN`), scripts/wikiwright.py (diffout); get-title-at-url's TextDecoder finding (wiki fdca908, 1e449b2)
- Status: promoted: C-20260928-4, C-20260929-1, C-20260929-2 (L-118, L-119), C-20260929-8 · helpful 8 · harmful 0 · last_confirmed 2026-09-30 (the fourth get-title-at-url update hit the Git Bash `C:/` PATH trap again, caught by the `installed` line; T-20260929-4: `C:/` on PATH in Git Bash ran Node 24 as "Node 20" a third time, caught by the `installed` line; two sibling update drafts merged)

### L-107 · 2026-09-28 · Draft-only update: pages to the named folder, everything else beside it, clones untouched (`draft-only-update`)
- Rule: a draft-only request: read the wiki's head with `ls-remote` (preflight without `--enable`), copy only the changed pages into the named folder, check them laid over a scratch copy of the whole wiki, put the script, its outputs, a handoff README and the repository-file drafts (`repo-draft/` with the repository's own paths) beside it, test on a fresh `git clone` of the local clone, and end with `git status` of both clones clean.
- Evidence: rule in SKILL.md Update mode ("A draft-only request"); get-title-at-url and is-an-image-url drafts
- Status: promoted: C-20260929-3 · helpful 8 · harmful 0 · last_confirmed 2026-09-29

### L-110 · 2026-09-28 · NuGet wikis show outputs in comments; 0.2.0's check read none of them (`outputs-in-comments`)
- Rule: `outputs` reads the forms NuGet and hand-written wikis use: an untagged or data block right after its input or code block, a comment value (quoted, JSON-like, a number or literal, after a print call or a PowerShell expression), a closing run of comment lines, and an intro word only within six words of the colon. Pages quote bare-word comment values or write `// =>`, and a command right after a code block gets its fence tag. Tag every output fence `text` and read the "N outputs checked" count, not only the exit code: `outputs` exits 1 when the pages hold code blocks and it recognised no output (a page with none says so with `<!-- outputs: skip (reason) -->`). Merges L-103 `input-output-pairs` and L-136 `zero-checked-passes`.
- Evidence: rule in scripts/wikiwright.py (outputs, `cmd_outputs`) with OutputFormsTests and OutputsTests, SKILL.md Steps 5 and 6, references/nuget.md, references/page-sets.md ("How `wikiwright.py outputs` reads a page"); the JsonPrettyPrinter and RandomNameGeneratorLibrary wikis; an IsImageUrlDotNet eval draft that printed "0 outputs checked" and exited 0 (T-20260929-4, L-136)
- Status: promoted: C-20260928-4, C-20260929-13 (L-136) · helpful 3 · harmful 0 · last_confirmed 2026-09-29

### L-111 · 2026-09-28 · Unseeded examples: print the value after checking it is on its list (`membership-for-random`)
- Rule: an unseeded example is printed only after checking it is on the list its method draws from, labelled so; a random line in a snippet's output becomes a stable placeholder after the same check.
- Evidence: rule in SKILL.md Step 4, references/nuget.md, templates/nuget/wiki-verify.template.cs (`Possible`)
- Status: promoted: C-20260928-4 · helpful 1 · harmful 0 · last_confirmed 2026-09-28

### L-116 · 2026-09-29 · A package that requests by host name through its dependencies: a proxy with TLS, trusted at start (`by-host-name-proxy`)
- Rule: when output derives from the hosts a package requests, serve the fixture under the real host names. Either the host-fixture kit (plain and TLS servers behind a CONNECT proxy routed by port, a throwaway CA, `NO_PROXY` naming the loopback, variables set before each child starts, `runtimeEnv` for Deno and Bun, an npx warm-up, and a socket guard that reads `net.connect()`'s array form and is tested with an `.invalid` host), or a `fetch` wrapper routing by an `x-fixture-url` header when only Node runs and the package calls the global `fetch`. Print one case that shows a lookup reached the fixture. Merges L-112 `fetch-proxy-connect`, L-115 `route-fetch-preload`, L-117 `guard-normalised-args`, L-127 `no-proxy-loopback` and L-129 `kit-first-run`.
- Evidence: rule in SKILL.md Step 4, references/npm-requests.md ("Packages that request by host name through their dependencies"), templates/npm/host-fixture.mjs and tests/host-fixture.test.mjs; markdown-plain-link-replacer and stack-exchange-markdown-retriever runs
- Status: promoted: C-20260928-4 (L-112), C-20260929-1, C-20260929-4 (L-127), C-20260929-5 (L-129) · helpful 2 · harmful 0 · last_confirmed 2026-09-29

### L-120 · 2026-09-29 · A replay that differs on another runtime: bisect the harness first (`bisect-the-harness`)
- Rule: when a replay differs between runtimes or runs, reproduce the smallest case and check the harness (waits between cases, connections closed, request lines counted per case window) before writing a behaviour difference on a page; scope replay counts to the Node line they ran on. A real difference (2.0.0 waits for its timeout where 1.1.7 failed at once) goes on the page as behaviour. Merges L-128 `connect-retry-leak`.
- Evidence: is-an-image-url note (2026-09-29 section), wiki c6d5f1b; stack-exchange-markdown-retriever note and log; package-modernize:L-023
- Status: promoted: C-20261001-4 (golden-captures.md, the bisected 1.1.0-on-net10.0 example) · helpful 2 · harmful 0 · last_confirmed 2026-09-30

### L-122 · 2026-09-29 · Remote content from a fixture is sample content: label it, never record the real answer (`sample-content-not-live`)
- Rule: when the package's output is remote content, the fixture's content is sample content: the page shows what the package printed for the stand-in, says so beside the output and links the real post. No request to the real service, not even one to record it. The grader fails a trace with a curl-like command naming the service's host, a `LIVE=` switch or an unrouted fetch wrapper. Replaces the rejected L-121 `record-once-replay`.
- Evidence: rule in SKILL.md Step 4; TESTS.md T-20260929-2; evals/grade-action.py (`live_requests`, `FETCH_WRAPPER`)
- Status: promoted: C-20260929-3 · helpful 0 · harmful 0 · last_confirmed 2026-09-29

### L-123 · 2026-09-29 · On Gitea and Forgejo a push never creates the wiki; the API's first page does (`api-seeds-gitea-wiki`)
- Rule: on Gitea and Forgejo a push never creates the wiki: `preflight --seed` with `WIKIWRIGHT_TOKEN` (the API's first page) or the maintainer's first page does, then push to the branch `ls-remote --symref` names. A status code cannot tell an empty wiki from a live one (200 for "Welcome to the wiki", 303 for a missing page), so `live` reads the page API and never follows redirects. Anonymous GitLab project JSON has no wiki fields: read the state from `ls-remote` of `PATH.wiki.git` and the wiki API. Merges L-124 `status-is-not-state` and L-126 `gitlab-anonymous-wiki-state`.
- Evidence: rule in references/hosts.md and scripts/wikiwright.py (preflight, live); R-20260929-1
- Status: promoted: C-20260929-4 · helpful 1 · harmful 0 · last_confirmed 2026-09-29

### L-125 · 2026-09-29 · Each host names its navigation files and slugs its anchors its own way (`host-page-rules`)
- Rule: `check --host KIND` applies each host's file rules (navigation file names, wikilinks, spaces and folders on Gitea and Forgejo; no footer, so the version line goes on Home) and its anchor slugs: GitHub keeps a heading's inline code text; Forgejo turns each run of characters other than letters, digits and `_` into one hyphen. Measure a host rule on real pages, not one probe heading, and keep their headings as tests; a wiki meant for two hosts links only to headings whose slugs agree. Merges L-114 `heading-code-slug` and L-135 `forgejo-slug-punctuation`.
- Evidence: rule in references/hosts.md ("Page sets on these hosts", anchors), scripts/wikiwright.py (`slug()`, check), tests/test_wikiwright.py (HeadingAnchorTests, slug cases); R-20260929-1, R-20260929-2
- Status: promoted: C-20260928-4 (L-114), C-20260929-4, C-20260929-9 (L-135) · helpful 1 · harmful 0 · last_confirmed 2026-09-29

### L-130 · 2026-09-29 · A package whose output is files: a fresh scratch tree per case, and the bytes the text hides (`file-writing-package`)
- Rule: a package whose output is files is verified on a fresh copy of the case's tree per case with the file-tree kit, which prints each file's state and its contents before and after under a header of size, UTF-8, BOM, line endings and final newline; pages state those facts in prose. Command examples are transcripts from `term()` with both streams in order, and `cli()` takes `{cwd}`. The kit masks escaped paths and takes hard links, folder modes, `hide` and `limit`. When output contains file paths, run the script on Linux too and show that run on the pages, stating the Windows difference once; a Linux Node comes from the registry (`npm pack node-linux-x64@<v>` and npm with shims, then `OLDEST_NODE_BIN`) or from nodejs.org checked against SHASUMS256; call `wsl.exe` from PowerShell, or set `MSYS_NO_PATHCONV=1` in Git Bash. Merges L-133 `file-tree-first-run` and L-132 `linux-run-for-paths`.
- Evidence: rule in SKILL.md Step 4, references/npm-files.md, templates/npm/file-tree.mjs and tests/file-tree.test.mjs; the format-json-files run (114 outputs), three of its eval drafts and the sixth run (L-132)
- Status: promoted: C-20260929-7, C-20260929-8 (L-133, L-132) · helpful 4 · harmful 0 · last_confirmed 2026-09-29

### L-131 · 2026-09-29 · A recipe's third-party package breaks the page while the documented package stands still (`recipe-deps-drift`)
- Rule: a clean diff proves only the cases already in the script. In update mode install every third-party package a recipe imports, and every tool a page names (`npm view <tool> version`; a new major beside the old under an alias, `typescript7@npm:typescript@7`), at its current `latest`, run the recipe on each Node line the pages name, print the version of every package and tool the pages name (diffout cannot see a drift the script never prints: get-title-at-url's saved script diffed 121 of 121 while its pages named an old TypeScript), and scope a block by the case that printed it (`<!-- outputs: node>=22 -->`); a stand-in proxy must handle both `CONNECT` and absolute-form requests.
- Evidence: rule in SKILL.md Update mode step 3, references/npm.md and npm-requests.md; get-title-at-url's Recipes page (undici 8, wiki 1e449b2); T-20260929-4 action-3-r2: Getting started says it compiles under TypeScript 6 while `npm install typescript` has given 7.0.2 since 2026-07-08, and three update runs diffed clean without noticing (the example compiles under 7.0.2)
- Status: promoted: C-20260929-8, C-20260929-13 (tools), C-20260930-2 (print versions), C-20260930-8 (a TypeScript matrix in `snippet()`) · helpful 5 · harmful 0 · last_confirmed 2026-09-30 (the fourth get-title-at-url update: TypeScript 7.0.2 and 6.0.3 both compile the page's example on Node 20, 22 and 24; wiki a020db1, PR #25. The eighth run: 7.0.2 refuses `node10` and `esModuleInterop: false` with TS5108, so replace-string-at-position's pages scope those setups to TypeScript 6 and earlier; references/npm.md, "The scratch project")

### L-137 · 2026-09-29 · A .NET package's requests reach a stand-in by a different route on each runtime (`dotnet-request-route`)
- Rule: .NET Core and .NET 5+ read `HTTP_PROXY`/`HTTPS_PROXY`; .NET Framework ignores them, so its child sets `WebRequest.DefaultWebProxy`, and since Framework never proxies a loopback address the routes use `.test` names. Restores (child builds, fsi's `#r "nuget:"`) run without the proxy variables, first. The `.invalid` gate runs on every route before any case. The stand-in refuses by answering (a reply that is not HTTP to a GET, 403 to a CONNECT): a closed connection makes HttpClient retry, and the gate expects each call logged exactly once. fsi keeps each resolved `#r`/`#i` set in `~/.packagemanagement/nuget/Cache/<hash>.fsx` and never restores it again (ignoring `NUGET_PACKAGES`), so a skipped warm-up usually goes unseen; keep the warm-up (with a new set the restore goes through the proxy, which NuGet reads, and fails the gate), and to test that path give the script a set never resolved (a new `#i` folder) with empty `NUGET_PACKAGES` and `NUGET_HTTP_CACHE_PATH`. Merges L-138 `refuse-by-answering` and L-140 `fsi-resolution-cache`.
- Evidence: rule in references/nuget-requests.md, references/nuget.md (Traps) and templates/nuget/wiki-verify.template.cs; the seventh run's report ("Request route", ".NET Framework and Linux", "One surprise"): net48 without the `DefaultWebProxy` line failed the gate with "stand-in: no request", and a stand-in that closed instead logged 4 GETs per http call on .NET 10; the fsi scratch variants neg-nowarm (exit 0), neg-nowarm4 (NU1301, GATE FAILED) and pos-coldwarm3 (L-140)
- Status: promoted: C-20260929-15, C-20260930-6 (the fsi route as code; L-140) · helpful 4 · harmful 0 · last_confirmed 2026-09-30

### L-139 · 2026-09-30 · The host prints the page title once; the page must not print it again (`title-printed-once`)
- Rule: a wiki page starts with its first paragraph, never with a heading that repeats the file-name title the host prints, and never puts a heading straight under one with the same words. `check` fails both; the everwrite checker flags them with `--wiki`.
- Evidence: the maintainer's correction on 2026-09-30 (get-title-at-url's Getting started showed "Getting Started" and then "Getting started"; "saying the same thing twice exactly is a mistake most humans wouldn't make"). page-sets.md had allowed it. Rule in SKILL.md Step 5, references/page-sets.md, scripts/wikiwright.py (check), CheckTests; everwrite C-20260930-1
- Status: promoted: C-20260930-4 · helpful 1 · harmful 0 · last_confirmed 2026-09-30

### L-141 · 2026-09-30 · The npm template's tsc lookup throws under TypeScript 7 (`tsc-by-path`)
- Rule: find a package's bin by path (`path.resolve('node_modules', 'typescript', 'bin', 'tsc')`), not with `require.resolve('<pkg>/bin/...')`: a package with an `exports` map hides every subpath it does not list. The template's `runSnippet` is fixed that way.
- Evidence: rule in templates/npm/wiki-verify.template.mjs (`runSnippet`, by path); T-20260930-3 (action-3: ERR_PACKAGE_PATH_NOT_EXPORTED under TypeScript 7.0.2, whose `exports` lists `.`, `./package.json` and `./unstable/*` only)
- Status: promoted: C-20260930-8 (marked promoted in the 2026-10-01 consolidation) · helpful 1 · harmful 0 · last_confirmed 2026-09-30

### L-142 · 2026-09-30 · Every script here that prints outside text writes UTF-8 (`utf8-every-printer`)
- Rule: any script in this repository that prints text it did not write (trace commands, program output, page text) reconfigures stdout and stderr to UTF-8 with replacement at start, and its test runs it as a subprocess with stdout piped and `PYTHONIOENCODING=cp1252`, which reproduces the Windows console on every system.
- Evidence: rule in evals/grade-action.py (`utf8_streams()`) and tests/test_wikiwright.py (`test_grader_digest_writes_utf8_to_a_pipe`, which fails on the 0.7.2 grader); the eighth run's `--digest` crash on Windows; LEARNINGS-ARCHIVE.md (the diffout crash)
- Status: promoted: C-20260930-9 · helpful 1 · harmful 0 · last_confirmed 2026-09-30

### L-144 · 2026-09-30 · A NuGet example that declares types or touches process-wide state runs as its own program (`whole-program-per-example`)
- Rule: hold each example as a whole program, types global, and run it in its own process per config; a config is a framework plus pinned dependency versions (the ends of a declared range: Autofac 6.5.0 and 9.3.4); print each dependency's informational version and the loaded build from `TargetFrameworkAttribute`. A page's file-based app (`#:package` lines) is written as the page shows it, directives included, and run with `dotnet run`; FFMpegCore 5.x needs `#:property PublishAot=false` on the page too. Merges L-143 `page-app-own-directives`.
- Evidence: the CachingServiceWithAOPSupport note and program (2026-09-30, branch wiki-2.0.0), its REPORT items 3 to 5, 7, 8; L-143's T-20261001-1 action-1-r1 draft
- Status: promoted: C-20261001-3 (the template's `children` section, `scaffold nuget --children`, nuget.md) · helpful 2 · harmful 0 · last_confirmed 2026-09-30

### L-145 · 2026-09-30 · Expiry goes on a page only with margins that two runs agree on (`time-margins-two-runs`)
- Rule: show expiry only through what a caller controls (an attribute's lifetime, a default), with margins of at least a second around each boundary; run the whole program twice and compare with `diffout` (56 of 56 sections equal on Windows, 47 of 47 on Linux), say so on the page, and write "not shown" for what has no stable margin (eviction under memory pressure).
- Evidence: CachingServiceWithAOPSupport's How-Results-Are-Cached (wiki cfef18b) and its note; REPORT item 6
- Status: promoted: C-20261001-4 (references/time-and-state.md) · helpful 1 · harmful 0 · last_confirmed 2026-09-30

### L-146 · 2026-09-30 · A package that runs an external program: say which binary ran, and test side effects only through seams (`external-program-seams`)
- Rule: print the program's path and version per runtime and how it was found; make inputs with the program itself (lavfi `testsrc`, `sine`) and show results as ffprobe facts and listings; close every child's stdin; mask addresses with a pattern; reach a side-effect command only through the code's own seams (already installed, stdin redirected without `--yes`, no package manager on PATH) and mark the rest "not tested". The evals fail any system install (`grade-action.py`, `system_installs()`).
- Evidence: the TrailerClipperLib note and program (2026-09-30, branch wiki-2.0.0), REPORT items 3, 5 to 7 and 13; evals/grade-action.py
- Status: promoted: C-20261001-3 (the template's `tool` section, `Term()`, stdin closed, regex masks), C-20261001-4 (references/programs-and-media.md) · helpful 1 · harmful 0 · last_confirmed 2026-09-30

### L-147 · 2026-09-30 · A scratch .NET SDK on Linux without libicu needs invariant mode before its first call (`invariant-before-first-call`)
- Rule: export `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1` before the first `dotnet` call, say on the pages that Linux ran in invariant mode, and mark culture-dependent answers on Linux "not tested". Download the SDK and any program from the projects' own releases, check their published checksums and keep them in the run's scratch, never in the WSL home folder (an eval run left 1.3 GB in `~/wv`, T-20261001-1).
- Evidence: both REPORTs (Linux sections; cs item 10); T-20261001-1
- Status: promoted: C-20261001-3 (nuget.md) · helpful 2 · harmful 0 · last_confirmed 2026-09-30

### L-148 · 2026-10-03 · An agent-skill repository has no tested page set; the command-line tool set fitted (`agent-skill-page-set`)
- Trigger: the everwrite wiki (2026-10-03, wiki a86ebc1), the first wiki for an agent skill and Claude Code plugin rather than a registry package. references/page-sets.md has no set for that kind, so the run chose one by hand.
- Hypothesis: a skill repository behaves like a command-line tool with two behaviours to explain (what the agent does with the skill, and what its bundled script reports), and has no importable API.
- Rule: until a set is tested, start from the command-line tool set (Home, Getting started, Commands, Recipes, Versions and upgrading, FAQ, Development), drop the API reference, and give the skill and its bundled checker or script one behaviour page each (everwrite: How-The-Skill-Works, What-The-Checker-Flags). Getting started covers every install route that was run (`claude plugin` from a marketplace, `gh skill install`) and names the client versions used. Record the set in page-sets.md after a second skill repository confirms it.
- Evidence: everwrite's run record, `ai-docs/notes/2026-10-03-wiki-run/2026-10-03-github-wiki.md` (Summary); https://github.com/m4bwav/everwrite/wiki (9 pages)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-03

### L-149 · 2026-10-03 · `outputs` reads a data block after a colon as output when an output word from the previous sentence falls in the six-word window (`intro-window-crosses-sentence`)
- Trigger: on everwrite's Recipes page a GitHub Actions YAML step followed the lead-in "... a strong hit fails the job because the checker exits 1. The step looks like this:". `is_intro()` takes the last six words before the colon, which reach back past the full stop to "exits", an output word, so the yaml fence (a data fence) was read as expected output and reported missing. The run ended the lead-in with a period and marked the block `<!-- snippets: skip (GitHub Actions YAML, not run for this wiki) -->`; `is_intro()` on the same text with a period returns False (checked 2026-10-03).
- Hypothesis: the window counts words, not words in the last sentence, and data fences (yaml, json, xml) count as output whenever the intro test passes, so a configuration example introduced with a colon is at risk whenever a nearby sentence names an exit code, a log or a result.
- Rule: introduce an input or configuration block with a sentence ending in a period, or put `<!-- outputs: skip (input) -->` before it. Fix in the helper: cut the window at the last sentence end before the colon; a unit test with this lead-in.
- Evidence: everwrite's run record (Gotchas); everwrite wiki Recipes page (wiki a86ebc1); scripts/wikiwright.py (`is_intro()`, `OUT_WORDS`); related to L-110 `outputs-in-comments` (the six-word window, L-103)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-03

### L-150 · 2026-10-04 · A child that exits before reading its stdin crashes the Node helpers with EPIPE on Windows (`stdin-epipe-on-windows`)
- Trigger: PR #3 (docs only) failed CI on windows-latest with Python 3.13 in `test_golden_replay_reads_both_capture_formats`: the generated wiki-verify.mjs died on an unhandled `EPIPE` from `child.stdin.end(input)` in `run()`. The same test passed on windows-latest with 3.9 and on master since 2026-09-30, so it is a race, not a regression.
- Hypothesis: when the child exits before Node flushes its stdin write, Windows reports the closed pipe as EPIPE on the stdin socket; with no 'error' listener Node treats it as uncaught and the whole script exits 1. Linux and macOS usually win the race.
- Rule: every `spawn()` that writes or closes stdin gets `stdin.on('error', ...)` ignoring EPIPE (other errors still throw). Applied in wiki-verify.template.mjs (`run()`, `cli()`), host-fixture.mjs (`child()`) and tests/host-fixture.test.mjs.
- Evidence: Actions run 37173028139 (suite windows-latest, 3.13); fix in C-20261004-1
- Scope: skill (templates/npm)
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-04

### L-151 · 2026-10-03 · Generate a large NuGet API reference from the published DLL, its XML docs and the previous release's DLL (`api-from-published-dll`)
- Trigger: UniverseGenerator 1.0.0 (wiki 170339b) has 84 public types and 763 members; writing the API reference by hand would have been slow and unchecked.
- Rule: reflect over `lib/<tfm>/X.dll` from the downloaded nupkg (a file-based app printing type, member kind, C# signature and XML doc id per line), join the summaries, remarks and `<exception>` tags from the nupkg's `X.xml`, and diff against the same listing of the previous published version for the "Since" column and for "nothing removed or changed" on Versions and upgrading. Strip internal references the XML docs carry (plan IDs). Save the generator beside the wiki note. UniverseGenerator's run: 128 new members, 0 removed, a 936-line page; the 40 members without docs were record constructors, left out.
- Evidence: UniverseGenerator ai-docs/notes/2026-10-03-wiki-api-surface.cs and 2026-10-03-wiki-gen-api.py
- Scope: references/nuget.md (survey), page-sets.md (API reference)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-03

### L-152 · 2026-10-03 · Right after a NuGet push, restore can miss the new version through the HTTP cache (`nuget-http-cache-lag`)
- Trigger: minutes after the flat container listed UniverseGenerator 1.0.0, `dotnet add package UniverseGenerator --version 1.0.0` failed with NU1102 ("Nearest version: 1.0.0-beta.1"), and wrote no PackageReference. An empty `NUGET_PACKAGES` was not enough; NuGet's HTTP cache (`v3-cache`, about 30 minutes) still held the index from the beta.1 checks.
- Rule: for any fresh-consumer check right after a release, set both `NUGET_PACKAGES` and `NUGET_HTTP_CACHE_PATH` to empty scratch folders (or `dotnet nuget locals http-cache --clear`). The file-based verification program's `#:package` restore is subject to the same cache.
- Evidence: UniverseGenerator ai-docs/notes/2026-10-03-stage-4-checklist.md step 7 (the 1.0.0 block)
- Scope: references/nuget.md
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-03
