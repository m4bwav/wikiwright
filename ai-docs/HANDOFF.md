# Handoff

Updated 2026-09-28 (0.3.0 session). Read this first, then [log.md](log.md) for evidence.

## Current state

- **wikiwright 0.3.0.** `outputs` reads the forms the NuGet wikis show output in: input and output pairs, code followed by its output, values in comments, closing comment runs, `# =>`. The intro word must sit within six words of the colon, and a command read as output gets a hint. `check` keeps inline code in heading anchors. Update mode says how to adopt a wiki written before its script was saved. Step 4 covers other hosts' snippets, random examples (membership check), golden captures with their own fixture server, and the oldest Node. Both templates carry the helpers. 24 unit tests.
- **Real runs.** Five wikis. The third skill run was is-an-image-url: 10 pages, wiki commit 8861236, outputs 40/40, golden replay 82/82 on 1.0.4 today. Its note is in that repository's `ai-docs/notes/2026-09-28-github-wiki.md` (PR #26, merged 77a42a2).
- **Retrofits done.** JsonPrettyPrinter: wiki a8c5574; its program, output and note are on branch `v3-retrofit` (e74b09b, inside that repository's open PR #8). RandomNameGeneratorLibrary: wiki f0bb65b; a new program and output, PR #18 merged 8ab575e.
- **Eval suite T-20260928-4: 8/9.** Triggers 9/9 (0/9 without), decoys 0/6. action-1 2/2 (baseline passes, hinted). action-2 1/2: one run skipped preflight (fallback), reproduced 0/3, so flaky. action-3 (new, update mode) 2/2, and its baseline passes too, because the note teaches the procedure. `tests.failing` still lists action-2, pending the re-measure below.
- Commands: `claude plugin eval <repo> --trust-plugin --no-publish --case "<glob>" -j 4` (one `--case` per call); `CASE=action-2 bash evals/run-action.sh <short out dir> [baseline]`, which ends with `evals/grade-action.py`'s grade.

## Open work, in order

The next session's prompt (0.4.0 and the markdown-plain-link-replacer wiki, covering items 1 to 3 and 7 below) is in the maintainer's private prompts folder: `2026-09-28-wikiwright-0.4-and-markdown-plain-link-replacer-kickoff.md`.

1. **action-2 stays in `tests.failing`.** Re-measured with 0.3.0 (T-20260928-5): preflight ran in 2 of 2, but run 1 showed an output its trace never printed, and the target now has a wiki. Retarget (item 2), rerun the suite, then clear it.
2. **Retarget the action cases again** before the next suite. is-an-image-url now has a wiki note (L-013). Next owed with no note: stack-exchange-markdown-retriever.
3. **get-title-at-url wiki, found by the action-3 eval runs.** Recipes' "decode the bytes with the right `TextDecoder` first" is wrong on Node 20.20.2 and 24.13.0 (L-106). Fix it with update mode; the drafts were in the eval work folders, now gone.
4. **Next owed wikis** (private inventory): stack-exchange-markdown-retriever, format-json-files, markdown-plain-link-replacer (npm with a CLI), then TrailerClipper, replace-string-at-position, IsImageUrlDotNet, CachingServiceWithAOPSupport.
5. **Untested page sets:** application, monorepo, command-line tool (candidate: TrailerClipper.Tool, a dotnet tool, command `tclipper`). **Untested hosts:** GitLab, Gitea and Forgejo, Azure DevOps.
6. **JsonPrettyPrinter wiki to 3.0.2** after that repository's PR #8 merges and 3.0.2 releases (its HANDOFF item 6).
7. is-an-image-url's script ran on Node 24.18.0 only; L-106 says to run the oldest Node in `engines` (20) too at the next update.

## Gotchas

- Headless eval runs edit the source LEARNINGS.md (L-017): `git diff` after every suite and after tune runs. On 2026-09-28 they wrote L-106 to L-108; L-108 was rejected (it contradicts L-015).
- The Skill tool serves the SKILL.md read at session start (L-012). Headless runs read the installed cache, but references and scripts come from the source path the overlay names, so don't edit those while a suite runs.
- Bash heredocs turn `\n` into a newline and a bare `python -` opens a REPL that hangs. Write Python edit scripts to a file with the Write tool (L-001).
- Never run `wikiwright.py unbs` on SKILL.md or LEARNINGS.md.
