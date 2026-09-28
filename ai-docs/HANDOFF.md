# Handoff

Updated 2026-09-28 (0.1.0 released). Read this first, then [log.md](log.md) for evidence.

## Current state

- wikiwright 0.1.0: one evergreen skill (`skills/wikiwright/`, tier fast, next due 2026-10-12), the helper `scripts/wikiwright.py` (preflight, check, live, unbs; 10 unit tests, CI on three OSes), references for page sets, publishing, npm and NuGet, templates for the verification scripts, sidebar, footer and the repository note. Public at https://github.com/m4bwav/wikiwright, tag v0.1.0 with a GitHub Release. Installed on the development machine as `wikiwright@mark-local`.
- The name wikiwright was kept (free on GitHub, fits the -wright family, no conflicting skill found); the reasons are in the decision under [decisions/](decisions/).
- First real run: the get-title-at-url wiki (https://github.com/m4bwav/get-title-at-url/wiki, nine pages, wiki commit b271157). How it was made, and what it found wrong in that package's README and CHANGELOG, is in that repository's `ai-docs/notes/2026-09-28-github-wiki.md`. Its lessons are L-007 to L-011 in the skill's LEARNINGS.md.
- Eval suite T-20260928-2: 7/7 (triggers 9/9 against 0/9 without the plugin, decoys 0/6, the action case 3/3). Trigger and decoy cases run with `claude plugin eval . --trust-plugin --no-publish --case "<glob>" -j 4`. The action case needs Bash, so it runs through `evals/run-action.sh`.
- package-modernize (m4bwav/package-modernize) now calls this skill in Phase 7 (C-20260928-5 there).

## Open work, in order

1. Sharpen action-1: point it at a repository with no wiki and no wiki note (L-013). The next owed wiki in the private inventory is a natural target: run it as the case, then record the result.
2. The page sets for an application, a monorepo and GitLab or Gitea wikis are untested; write each only after a run proves it.
3. Open question from the research: does `gh repo edit --enable-wiki` ever create the wiki repository by itself? The next repository with the feature off answers it (preflight re-checks for 60 seconds after enabling). Record the answer in RESEARCH.md.
4. Optional: skill-creator's description optimiser (`run_loop.py`) was not run; the trigger cases already pass 9/9.

## Gotchas

- A plugin installed mid-session is not visible to the Skill tool. To test a fresh edit in the same session, link `skills/wikiwright` into `~/.claude/skills/`, wait for the listing, invoke, then remove the link (L-012).
- Never run `wikiwright.py unbs` on SKILL.md or LEARNINGS.md: they name the `<BS>` placeholder in prose.
- `claude plugin eval` refuses an `--eval-dir` under `skills/`; the case folders live in the root `evals/`.
