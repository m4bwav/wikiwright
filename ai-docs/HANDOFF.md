# Handoff

Updated 2026-09-29 (0.4.0 session). Read this first, then [log.md](log.md) for evidence.

## Current state

- **wikiwright 0.4.0** (tag v0.4.0, GitHub Release, CI green on Ubuntu, macOS and Windows; installed wikiwright@mark-local, 21 cached files equal to the source). New: `wikiwright.py diffout` (update mode's section-by-section diff), `OLDEST_NODE` in the npm template (L-106 made mechanical), a "by host name" template section for packages that request the hosts their input names (proxy with a throwaway CA, L-116), the fixed socket guard (L-117), captures recorded through a proxy with TLS (references/npm.md). 27 unit tests.
- **Real runs.** Six wikis. The fourth skill run was markdown-plain-link-replacer: 10 pages, wiki commit ab33614, outputs 55/55, live clean, golden replay 154/154 and 18/18 on 1.1.16, script on Node 24.18.0 and 20.20.2. Its note is that repository's `ai-docs/notes/2026-09-29-github-wiki.md` (PR #13, merged 55a714c).
- **get-title-at-url** (open work 3 of 0.3.0): its Recipes' `TextDecoder('windows-1252')` advice fixed in update mode, both Node lines run; see that repository's wiki note (dated section of 2026-09-29) and log. **is-an-image-url** ran on Node 20; the diff is in its note.
- **Eval suite T-20260929-1: 9/9.** Triggers 9/9 (0/9 without), decoys 0/6. action-1 2/2 (baseline passes, hinted), action-2 2/2 (baseline fails: discriminating; cleared from `tests.failing`), action-3 2/2 (baseline passes: the note teaches update mode).
- **package-modernize**: PR #15 (capture template replays against the next major, C-20260929-1, L-123) and PR #16 (the guard, C-20260929-2, L-124), both merged.
- Commands: `claude plugin eval <repo> --trust-plugin --no-publish --case "<glob>" -j 4` (one `--case` per call); `CASE=action-2 bash evals/run-action.sh <short out dir> [baseline]`, which ends with `evals/grade-action.py`'s grade.

## Open work, in order

The next session's prompt (0.5.0, other hosts verified without an account, and the stack-exchange-markdown-retriever wiki, covering items 0 to 3 below) is in the maintainer's private prompts folder: `2026-09-29-wikiwright-0.5-and-stack-exchange-markdown-retriever-kickoff.md`.

0. **0.4.1 fixes from the first uses of 0.4.0** (L-118, L-119): `OLDEST_NODE` must put a folder holding only `node.exe` first on PATH (Git Bash skips the npm `node` package's bin folder and runs the system Node silently); `diffout` must reconfigure stdout to UTF-8 and mask home and temp paths on `--save`; `outputs` needs a way to scope a block to a Node line. Each with a test and a CHANGELOG entry.
1. **Retarget the action cases** before the next suite: markdown-plain-link-replacer now has a wiki note (L-013). Next owed with no note: stack-exchange-markdown-retriever (npm with a CLI, one fixed HTTPS host: a good second test of the "by host name" section).
2. **Next owed wikis** (private inventory): stack-exchange-markdown-retriever, format-json-files, replace-string-at-position, then TrailerClipper (and TrailerClipper.Tool, the command-line-tool candidate), IsImageUrlDotNet, CachingServiceWithAOPSupport.
3. **Untested page sets:** application, monorepo, command-line tool (candidate: TrailerClipper.Tool, command `tclipper`). **Untested hosts:** GitLab, Gitea and Forgejo, Azure DevOps.
4. **evergreen refresh**: the session-start hook listed other units as due; wikiwright itself is due 2026-10-12.
5. markdown-plain-link-replacer's doc inaccuracies wait for its next release (its HANDOFF lists them); `next` on npm points to the deprecated 2.0.0-beta.1 (Mark's).

## Gotchas

- Headless eval runs edit the source (L-017): `git status` and `git diff` after every suite; on 2026-09-29 they also left an untracked `package.json` in the skill folder.
- The Skill tool serves the SKILL.md read at session start (L-012). Headless runs read the installed cache, but references and scripts come from the source path, so don't edit those while a suite runs.
- Bash heredocs turn `\n` into a newline and a bare `python -` opens a REPL that hangs (it happened again on 2026-09-29). Write Python edit scripts to a file with the Write tool (L-001).
- `NODE_OPTIONS` drops backslashes: preload paths with forward slashes. A guard reading `args[0].host` lets plain http through (L-117).
- Never run `wikiwright.py unbs` on SKILL.md or LEARNINGS.md.
