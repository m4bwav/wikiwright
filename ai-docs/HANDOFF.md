# Handoff

Updated 2026-09-28 (0.2.0 released; package-modernize pull request #12 merged the matching Phase 6 and Phase 7 lines). Read this first, then [log.md](log.md) for evidence.

## Current state

- **wikiwright 0.2.0.** The helper has a new `outputs` subcommand: every page output must be in the verification script's saved output. It also has preflight host detection with `STATE: other-host`, and `check --partial`. `references/hosts.md` covers GitLab, Gitea and Forgejo, and Azure DevOps, unverified. The page sets add "npm library without a CLI", "deterministic or seeded output" and golden captures. Update mode diffs against a saved output. 17 unit tests, CI on three systems. Public at https://github.com/m4bwav/wikiwright, tag v0.2.0 with a GitHub Release. Installed as `wikiwright@mark-local`, with the cache hash checked against the source.
- **The enable-wiki question is answered.** `gh repo edit --enable-wiki` does not create the wiki repository; only a first page saved in the web UI does (RESEARCH.md, publishing.md, L-002).
- **Real runs.** Four wikis in all. The second skill run was seeded-random-utilities: 9 pages, wiki commit 7980d4b, notes in that repository's `ai-docs/notes/2026-09-28-github-wiki.md`. The update-mode rehearsal on get-title-at-url fixed its script and two pages (wiki commit 2807e56).
- **Eval suite T-20260928-3: 8/8.**
  - Triggers: 9/9 with the plugin, 0/9 without. Decoys: 0/6.
  - action-1 (hinted): 3/3, but the baseline also passes.
  - action-2 (unhinted, new): 2/2, and the baseline never installs or runs the package. It is the case that discriminates.
  - outcome-1: 3/3.
  - Commands: trigger and decoy cases with `claude plugin eval <repo> --trust-plugin --no-publish --case "<glob>" -j 4` (one `--case` per call). Action cases with `CASE=action-2 bash evals/run-action.sh <short out dir> [baseline]`.

## Open work, in order

1. **Retarget the action cases before the next suite run.** seeded-random-utilities now has a wiki note, so the baseline can learn from it (L-013). Set `REPO` in `evals/run-action.sh` and the prompts in `evals/evals.json` and `evals/action-1/prompt.md` to the next owed repository with no wiki note. Clone nothing a case can see before the suite (L-017).
2. **Next owed wikis**, from the private inventory's "Wikis" section: is-an-image-url, stack-exchange-markdown-retriever, format-json-files, markdown-plain-link-replacer (npm with a CLI), then TrailerClipper, replace-string-at-position, IsImageUrlDotNet, CachingServiceWithAOPSupport.
3. **Untested page sets:** an application, a monorepo, a command-line tool. **Untested hosts:** GitLab, Gitea and Forgejo, Azure DevOps (hosts.md). Write a set only after a run proves it.
4. **Retrofit the earlier wikis** to the saved-output rule. The NuGet wikis (RandomNameGeneratorLibrary, JsonPrettyPrinter) have no saved `*-wiki-verify.out.txt`, so update mode there must first run the script against the current version and fix every `outputs` finding (SKILL.md, Update mode).
5. **Optional:** skill-creator's description optimiser was not run; triggers are at 9/9.

## Gotchas

- The Skill tool serves the SKILL.md text read at session start, even through a junction to the edited source (L-012). Follow the source by hand in the same session, or test headless.
- Headless eval runs edit the source LEARNINGS.md and see the session's clones. Diff after the suite (L-017).
- Never run `wikiwright.py unbs` on SKILL.md or LEARNINGS.md: they name the `<BS>` placeholder in prose.
- `claude plugin eval` refuses an `--eval-dir` under `skills/`; the case folders live in the root `evals/`.
- Bash heredocs with apostrophes fail, and `\\` becomes `\`. Write Python edit scripts to a scratch file with the Write tool.
