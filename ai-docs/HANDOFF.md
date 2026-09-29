# Handoff

Updated 2026-09-29 (0.6.0 session). Read this first, then [log.md](log.md) for evidence.

## Current state

- **wikiwright 0.6.0** (tag v0.6.0, GitHub Release; CI green on Ubuntu, macOS and Windows; installed wikiwright@mark-local, `wikiwright.py cachecheck` 23 of 23 equal).
  - Files on disk: `templates/npm/file-tree.mjs` gives every case a fresh scratch tree and prints each written file before and after with its bytes' facts; the template's `inTree()`, `term()` (a page transcript), `OLDEST_NODE_BIN`, and a per-platform Node folder.
  - The grader: an unrouted `fetch` wrapper counts as a request to the real service; saved `*.out.txt` files count as evidence; preflight through a variable counts; `--digest` prints one line per tool call worth reading.
  - `diffout` counts `shell node:` lines per output and warns when one output ran on two Nodes (L-118).
  - Forgejo's anchor slug matches a published wiki (99 of 99 ids).
- **Eval suite T-20260929-3: 9/9 after two grader fixes (no skill change).** Triggers 9/9 (0/9 without), decoys 0/6. action-2's baseline still fails (discriminating).
- **Real runs: eight wikis.** The sixth skill run was format-json-files, headless: 10 pages, wiki c9f5fe5, outputs 114/114, live clean, PR #4 merged. The same pages were published on a local Forgejo as the first real wiki on another host, then removed (R-20260929-2).
- get-title-at-url's wiki had its third update (wiki 1e449b2, PR #24): the decoder claim and the proxy recipe (undici 8).

## Open work, in order

The next session's prompt (0.7.0 and the IsImageUrlDotNet wiki: the evals taught NuGet, `live` checking anchors, LEARNINGS consolidated) is in the maintainer's private prompts folder: `2026-09-29-wikiwright-0.7-and-isimageurldotnet-kickoff.md`.

1. **Next owed wikis** (private inventory): replace-string-at-position, then TrailerClipper (and TrailerClipper.Tool, the command-line-tool candidate), IsImageUrlDotNet, CachingServiceWithAOPSupport. Retarget action-1 and action-2 at the next one before its run (L-013): it must have no wiki note.
2. **`live` checks anchors: done on branch `ww07-live-anchors` (C-20260929-11), not yet merged.** Every `Page#anchor` link must find `id="user-content-..."` on the rendered page (GitHub, Gitea, Forgejo); GitLab and Azure DevOps say "not checked: id form unmeasured". No extra requests on the two real wikis measured.
3. **Untested page sets:** application, monorepo, command-line tool. **Hosts:** one real wiki on Forgejo; none on Gitea, GitLab or Azure DevOps (writes there need an account).
4. **format-json-files:** nine inaccuracies in its shipped docs wait for its next release (its note, "Inaccuracies"). stack-exchange-markdown-retriever's six still wait too. get-title-at-url's CHANGELOG sentence on the decoder is its note's inaccuracy 5.
5. **evergreen refresh:** wikiwright is due 2026-10-12. evergreen-protocol PR #5 left LEARNINGS.md over its budget; LEARNINGS.md is 500 lines: consolidate.

## Gotchas

- Headless eval runs edit the source (L-017); `run-suite.sh` ends with `git status --short`. Grade on evidence, and read the traces with `grade-action.py <run> --digest` (L-122).
- Never `cd` in a shell call: a subagent inherits the session's folder, and `npm init -y --prefix` writes `package.json` into it (L-134).
- The Skill tool serves the SKILL.md read at session start (L-012): real runs go headless (`claude -p`).
- Bash heredocs and a bare `python -` hang or mangle; write Python to a file first (L-001). The Write and Edit tools decode `\u` escapes.
- Never run `wikiwright.py unbs` on SKILL.md or LEARNINGS.md.
