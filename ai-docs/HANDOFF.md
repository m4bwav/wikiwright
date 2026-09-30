# Handoff

Updated 2026-09-30 (0.7.0 and 0.7.1 session). Read this first, then [log.md](log.md) for evidence.

## Current state

- **wikiwright 0.7.2** (tags v0.7.0 to v0.7.2, GitHub Releases; 0.7.2 makes `check` fail a first heading that repeats the page title the host prints, L-139, and the five wikis that did it are fixed; 0.7.1 adds the npm template's `snippet()`, which holds each page block as text and runs it, so `snippets` gates npm wikis too; CI on Ubuntu, macOS and Windows; installed wikiwright@mark-local, `wikiwright.py cachecheck` all equal).
  - NuGet end to end: the NuGet template's `requests` blocks (a stand-in proxy answering `.test` names over http and https, refusal by answering, the `.invalid` gate in every per-framework child, `WebRequest.DefaultWebProxy` for .NET Framework), `Run()` with env and cwd, `Mask()`; references/nuget.md "Packages that make requests", the F# warm-up, net48 as a file-based app, Linux in WSL.
  - New commands: `registry` (the Step 2 registry survey, 9x to 66x smaller than the raw JSON), `snippets` (every C# and F# block on the pages is in the program; a review list for npm scripts). `live` checks every anchor link against the ids the host rendered (GitHub, Gitea, Forgejo). `outputs` fails when the pages hold code and it recognised no output (L-136).
  - LEARNINGS.md consolidated: 503 to 200 lines, the full text in LEARNINGS-ARCHIVE.md.
  - The evals speak NuGet (`dotnet add package`, `#:package`, `#r "nuget:"`, PackageReference), and judge a .NET program's requests on the whole file.
- **Eval suite T-20260929-4: 9/9 after two grader fixes (no skill change).** Triggers 9/9 (0/9 without), decoys 0/6. action-1's baseline now fails too (it requested example.com), so both new-wiki cases discriminate; action-3's baseline passes (L-013).
- **Real runs: nine wikis.** The seventh skill run was IsImageUrlDotNet, headless: 9 pages, wiki 737a3d2, outputs 38/38, snippets 18/18, golden 117/117 on three recordings, live 9 pages and 25 anchors clean. Its PR #10 was merged (d3c1080) by the maintainer; the auto-mode classifier had refused the agent's merge.

## Open work, in order

1. **Next owed wikis** (private inventory): replace-string-at-position, then TrailerClipper (and TrailerClipper.Tool, the command-line-tool candidate), CachingServiceWithAOPSupport. Retarget action-1 and action-2 at the next one before its run (L-013): it must have no wiki note. Set `FORBID_HOST` in run-action.sh to the hosts its README names.
2. **Saved npm scripts from before 0.7.1** (get-title-at-url, seeded-random-utilities, is-an-image-url, markdown-plain-link-replacer, stack-exchange-markdown-retriever, format-json-files) run their cases as code, so `snippets` fails their wikis: move the cases into `snippet()` at each one's next update (0.7.1, C-20260930-1, did the template).
3. **Untested page sets:** application, monorepo, command-line tool. **Hosts:** anchor ids unmeasured on GitLab and Azure DevOps; Gitea and Forgejo checked against a fake server only.
4. **Inaccuracies waiting for releases:** IsImageUrlDotNet (eight, its note), format-json-files (nine), stack-exchange-markdown-retriever (six), get-title-at-url (its note's inaccuracy 5). get-title-at-url's TypeScript 7 wording is fixed on the wiki (a020db1); its PR #25 (the saved script and note) waits for the maintainer's merge.
5. **Not run in 0.7.0:** the NuGet template's `.fsx` gate (a comment example), its Linux path; macOS for any .NET wiki.
6. **evergreen refresh:** wikiwright is due 2026-10-12.

## Gotchas

- Headless eval runs edit the source (L-017); `run-suite.sh` ends with `git status --short`. Grade on evidence, and read the traces with `grade-action.py <run> --digest` (L-122).
- Never `cd` in a shell call: a subagent inherits the session's folder (L-017). Check a shared clone's branch before committing in it: another session may have left it on a merged feature branch.
- The Skill tool serves the SKILL.md read at session start (L-012): real runs go headless (`claude -p`). Eval runs read the skill from the source folder (the overlay points there): merge nothing into it while a run is going.
- Bash heredocs and a bare `python -` hang or mangle; write Python to a file first (L-001). The Write and Edit tools decode `\u` escapes.
- Never run `wikiwright.py unbs` on SKILL.md or LEARNINGS.md.
- An agent's `gh pr merge` can be refused by the auto-mode classifier; ask the maintainer for an explicit "run it".
