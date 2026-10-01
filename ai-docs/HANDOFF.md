# Handoff

Updated 2026-10-01 (0.9.0 session). Read this first, then [log.md](log.md) for evidence.

## Current state

- **wikiwright 0.9.0** (committed; tag, Release and reinstall: see the log's last lines for whether they happened, since publishing waited on the maintainer's "run it").
  - References split by package kind (C-20261001-1): cores npm.md, page-sets.md, nuget.md; trait files npm-requests, npm-files, golden-captures, page-sets-cli, page-sets-seeded, nuget-requests, and new in 0.9.0 programs-and-media (an external program, media or binary output, NuGet file writing) and time-and-state (time-dependent output, process-wide state). SKILL.md Steps 3 and 4 route by trait; both real runs opened only their trait files.
  - `scaffold nuget ID VERSION --namespace NS --type T [--children net48,net8.0] [--requests] [--fsharp] [--tool ID:COMMAND]` (C-20261001-3): the NuGet template is in sections; `children` runs each example as a whole program per config (framework plus pinned dependency versions), `tool` installs a dotnet tool into scratch and prints `Term()` transcripts with stdin closed. Scaffolds 10,121 (core) to 34,059 bytes (requests and children).
  - The command-line tool page set is tested (TrailerClipper.Tool, page-sets-cli.md); a library and its tool take both sets in union.
  - `check` no longer calls a heading of proper nouns Title Case (C-20261001-5). The grader reads `dotnet tool install` then the tool run, several package ids and fails any system install; run-action.sh passes deny rules one per argument.
- **Eval suite T-20261001-1: 9/9.** action-1 and action-2 on TrailerClipperLib (both baselines fail), action-3 on get-title-at-url.
- **Real runs: twelve wikis.** Ninth: TrailerClipperLib (11 pages, wiki 72e35c3, outputs 104/104, snippets 37/37, a `tclipper -o <folder>` crash found). Tenth: CachingServiceWithAOPSupport (9 pages, wiki cfef18b, outputs 45/45, snippets 34/34, expiry with margins). Reports: `%TEMP%\ww11\tc\REPORT.md`, `%TEMP%\ww11\cs\REPORT.md`; each repository's note on its `wiki-2.0.0` branch.

## Open work, in order

1. **The requests scaffold is bigger than the old template** (34,059 bytes against 23,932): trim the `children` and `requests` sections or split helpers into a file the scaffold copies beside the program, and measure.
2. **Run items left** (the reports' numbers): a NuGet golden comparator (cs 9; both runs wrote one by hand), per-config Windows/Linux compare (cs 11), `registry --limit` is not found by runs (cs 14: say it in nuget.md), the overlay's npm text read by NuGet runs (cs 15), the note template's dependency matrix and time margins (cs 16), a usage-synopsis output form (tc 12), the everwrite path (tc 14), which file holds an L- ID (cs 13).
3. **Gates that do not exist yet:** tables hand-copied from output, prose claims, which output belongs to which code block.
4. **Saved npm scripts from before 0.7.1** run their cases as code: move them into `snippet()` at each one's next update.
5. **package-modernize's npm capture template** should label each case (that skill's repository).
6. **Untested page sets:** application, website, monorepo. **Hosts:** anchor ids unmeasured on GitLab and Azure DevOps.
7. **Inaccuracies waiting for releases:** TrailerClipperLib (fifteen, including the `-o <folder>` crash), CachingServiceWithAOPSupport (four), replace-string-at-position (seven), IsImageUrlDotNet (eight), format-json-files (nine), stack-exchange-markdown-retriever (six), get-title-at-url (one).
8. **evergreen refresh:** wikiwright is due 2026-10-12.

## Gotchas

- Headless eval runs edit the source (L-017); `run-suite.sh` ends with `git status --short`. Grade on evidence; read traces with `grade-action.py <run> --digest`. An eval run in T-20261001-1 left 1.3 GB in WSL `~/wv`: check the WSL home after Linux runs.
- Never `cd` in a shell call: a subagent inherits the session's folder (L-017). Check a shared clone's branch before committing in it.
- The Skill tool serves the SKILL.md read at session start (L-012): real runs go headless (`claude -p`). Runs read the source folder through the overlay: merge nothing into it while a run is going; build in worktrees and merge after.
- Bash heredocs and a bare `python -` hang (this session did it twice): write Python to a file first (L-001). The Write and Edit tools decode `\u` escapes.
- Never run `wikiwright.py unbs` on SKILL.md or LEARNINGS.md.
- The auto-mode classifier refuses an agent's wiki push ("Create Public Surface") and `gh pr merge` ("Merge Without Review") even with a kickoff's approval: ask the maintainer for an explicit "run it", or assign the PR with `needs-review`.
