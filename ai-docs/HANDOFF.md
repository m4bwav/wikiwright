# Handoff

Updated 2026-09-29 (0.5.0 session). Read this first, then [log.md](log.md) for evidence.

## Current state

- **wikiwright 0.5.0** (tag v0.5.0, GitHub Release; CI green on Ubuntu, macOS and Windows; installed wikiwright@mark-local, `wikiwright.py cachecheck` all files equal).
  - Tools that save tokens: `evals/run-suite.sh` prints one line per run and ends with the source's `git status --short`; `wikiwright.py cachecheck` and `releasecheck X.Y.Z`.
  - `templates/npm/host-fixture.mjs`: the proxy by host name with its CA, a self-tested guard, `runtimeEnv` for Deno and Bun, and node tests in CI.
  - The 0.4.1 fixes: `OLDEST_NODE` copies `node.exe` alone, `diffout` writes UTF-8 and masks paths, `outputs` reads `<!-- outputs: node>=N -->`.
  - Other hosts measured without an account (R-20260929-1): preflight, `check --host` and `live` know Gitea, Forgejo, GitLab and Azure DevOps.
  - SKILL.md Step 4: remote content from a fixture is sample content; never a live recording (L-122).
- **Eval suite T-20260929-2: 9/9 after a tune.** Triggers 9/9 (0/9 without), decoys 0/6. action-2's baseline still fails (discriminating); action-1 and action-3 baselines pass (hinted, and the note teaches update mode). Three retriever runs had requested the real API; after the tune (C-20260929-3), 4/4 are clean.
- **Real runs: seven wikis.** The fifth skill run was stack-exchange-markdown-retriever, headless, with the installed 0.5.0 code.
  - 10 pages, wiki commit 348a628; check 0/0, outputs 93/93, live 10 pages with 0 failures.
  - Golden replay: 90/90 and 20/20 on 1.1.7 today. Node 24.18.0 and 20.20.2 were both run. Repository tests 371/371.
  - The note is that repository's `ai-docs/notes/2026-09-29-github-wiki.md` (PR #23, merged c657a9d).
- **package-modernize** PR #19 merged (`capture-proxy.cjs`, one replayable proxy setup, its L-125). **evergreen-protocol PR #5** is open for review (a suite ends with `git status --short`, its L-025).

## Open work, in order

The next session's prompt (0.6.0 and the format-json-files wiki, covering items 1, 3 and a first local Forgejo wiki) is in the maintainer's private prompts folder: `2026-09-29-wikiwright-0.6-and-format-json-files-kickoff.md`. format-json-files' wiki feature was switched on 2026-09-29; its first page still needs the maintainer's save.

1. **Next owed wikis** (private inventory): format-json-files, replace-string-at-position, then TrailerClipper (and TrailerClipper.Tool, the command-line-tool candidate), IsImageUrlDotNet, CachingServiceWithAOPSupport. Retarget action-1 and action-2 at the next one before its run (L-013): it must have no wiki note.
2. **Untested page sets:** application, monorepo, command-line tool. **Hosts:** no real wiki published on Gitea, Forgejo, GitLab or Azure DevOps yet. Azure DevOps writes need an account (the hosts.md "Still unverified" lines).
3. **get-title-at-url wiki:** How titles are found says the decoder is wrong "on Node 20 and some Node 22 and 24 releases", which is too broad (L-106 update of 2026-09-29, from action-3's drafts). Fix it in update mode.
4. **stack-exchange-markdown-retriever:** six inaccuracies in its shipped docs wait for its next release (its note, "Inaccuracies").
5. **evergreen refresh:** wikiwright is due 2026-10-12. evergreen-protocol PR #5 left LEARNINGS.md over its 200-line budget; consolidate it on merge.

## Gotchas

- Headless eval runs edit the source (L-017); `run-suite.sh` ends with `git status --short`. Review each eval-written entry: T-20260929-2 kept five and rejected L-121.
- The grader cannot see a recorder that requests the real service through the package. Read the traces of runs against a package that calls a fixed service (L-122).
- The Skill tool serves the SKILL.md read at session start (L-012). The fifth run went headless (`claude -p`) so it would read the installed 0.5.0.
- Bash heredocs and a bare `python -` hang or mangle; write Python to a file first (L-001).
- Never run `wikiwright.py unbs` on SKILL.md or LEARNINGS.md.
