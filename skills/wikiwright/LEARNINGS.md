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
- Trigger: on DotNetRandomNameGenerator the first `git push` answered "Repository not found" although `has_wiki` was true; Mark saved a page and the push worked (2026-09-28). On get-title-at-url the same day, a placeholder repository appeared about a minute after `gh repo edit --enable-wiki`.
- Hypothesis: GitHub creates `OWNER/REPO.wiki.git` lazily, on the first page save; no REST or GraphQL call creates a page. Why the enable call was followed by a placeholder on one repository is unknown.
- Rule: run `wikiwright.py preflight` (ls-remote, re-checked for 60 seconds after enabling) before writing; when the repository is missing, ask for the click in the first message and keep working meanwhile. A placeholder-only wiki may be force-pushed over.
- Evidence: DotNetRandomNameGenerator ai-docs note ("How it was published"); SKILL.md Step 1; references/publishing.md
- Scope: skill
- Status: promoted: C-20260928-1 · helpful 2 · harmful 0 · last_confirmed 2026-09-28

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
