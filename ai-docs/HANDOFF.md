# Handoff

Updated 2026-09-30 (0.8.0 session). Read this first, then [log.md](log.md) for evidence.

## Current state

- **wikiwright 0.8.0** (tag v0.8.0, GitHub Release; CI on Ubuntu, macOS and Windows; installed wikiwright@mark-local, `wikiwright.py cachecheck` all equal).
  - `wikiwright.py scaffold npm PACKAGE VERSION [--bin] [--requests] [--by-host] [--files] [--golden OLD]` writes the npm verification script filled in and cut to the package's sections (12,722 bytes for a library without requests or files, against the 25,524-byte template), plus a `{"private": true}` package.json when none exists.
  - The npm template's golden section compares both capture formats, chosen from the golden file's shape: the network one (named cases, answers, timing, requests) and package-modernize's synchronous one (cases by index and arguments, results by parsed value, header left out, quirks apart). Helpers are followed from the capture's `require('./...')` lines.
  - `snippet()` takes `dir` (run the same page text against an old version) and a TypeScript matrix: `ext` (.mts, .cts, .ts), `typescript` (a compiler folder such as an alias `typescript6`), `--noEmit` in the flags; it prints `tsc <version>: exit N`. tsc is found by path, since TypeScript 7's exports hide `./bin/tsc` (L-141). TypeScript 7.0.2 refuses `node10` and `esModuleInterop: false` with TS5108 and still emits (references/npm.md).
  - The NuGet template's fsi `.invalid` gate is code, run for real on IsImageUrlDotNet 2.0.0 with two negatives (L-140 `fsi-resolution-cache`: fsi never restores a resolved `#r` set again).
  - `registry` prints last week's downloads per version for npm. The grader writes UTF-8 to a pipe (L-142).
- **Eval suite T-20260930-3: 9/9.** Triggers 9/9 (0/9 without), decoys 0/6; action-1 and action-2 on replace-string-at-position (no forbidden host: it makes no requests), action-2's baseline fails (no wiki check); action-3 on get-title-at-url.
- **Real runs: ten wikis.** The eighth skill run was replace-string-at-position, headless: 9 pages, wiki 21af852, outputs 48/48 on Node 24 and 20, snippets 34/34 (the first npm wiki the gate covers), golden 71/71 on 1.0.4 today and 26 identical against 2.0.0, live 9 pages and 18 anchors clean, repo tests 177/177. Its PR #4 (the note, program and outputs) is open, assigned to the maintainer with `needs-review`: the auto-mode classifier refused the agent's merge.

## Open work, in order

1. **Split the references by package kind.** The eighth run measured that about 60% of npm.md and page-sets.md (43 KB read) did not apply to a library without requests or files; npm.md grew to 27,726 bytes in 0.8.0. Mirror `scaffold`'s sections: a core, then requests, host names, files, golden, read only when the package needs them. Measure before and after.
2. **Next owed wikis** (private inventory): TrailerClipper (and TrailerClipper.Tool, the command-line-tool candidate), CachingServiceWithAOPSupport. Retarget action-1 and action-2 at the next one before its run (L-013): it must have no wiki note; set `FORBID_HOST` only when the package requests a host its README names.
3. **Gates that do not exist yet:** tables hand-copied from output, prose claims, and which output block belongs to which code block (the eighth run's item 12; page-sets.md, "known limits").
4. **Saved npm scripts from before 0.7.1** (get-title-at-url, seeded-random-utilities, is-an-image-url, markdown-plain-link-replacer, stack-exchange-markdown-retriever, format-json-files) run their cases as code, so `snippets` fails their wikis: move the cases into `snippet()` at each one's next update.
5. **package-modernize's npm capture template** should label each case, so a replay can report by name rather than index (the eighth run's item 11c; that skill's repository).
6. **Untested page sets:** application, monorepo, command-line tool. **Hosts:** anchor ids unmeasured on GitLab and Azure DevOps.
7. **Inaccuracies waiting for releases:** replace-string-at-position (seven, its note), IsImageUrlDotNet (eight), format-json-files (nine), stack-exchange-markdown-retriever (six), get-title-at-url (its note's inaccuracy 5).
8. **LEARNINGS.md is over its 200-line budget** (about 220): consolidate at the next release.
9. **evergreen refresh:** wikiwright is due 2026-10-12.

## Gotchas

- Headless eval runs edit the source (L-017); `run-suite.sh` ends with `git status --short`. Grade on evidence, and read the traces with `grade-action.py <run> --digest` (L-122). In 0.8.0 an eval run's edit found a real bug (L-141): review, don't just revert.
- Never `cd` in a shell call: a subagent inherits the session's folder (L-017). Check a shared clone's branch before committing in it.
- The Skill tool serves the SKILL.md read at session start (L-012): real runs go headless (`claude -p`). Eval runs read the skill from the source folder: merge nothing into it while a run is going; build in worktrees and merge after.
- Bash heredocs and a bare `python -` hang or mangle; write Python to a file first (L-001). The Write and Edit tools decode `\u` escapes.
- Never run `wikiwright.py unbs` on SKILL.md or LEARNINGS.md.
- An agent's `gh pr merge` is refused by the auto-mode classifier ("Merge Without Review"): assign the PR to the maintainer with `needs-review`.
