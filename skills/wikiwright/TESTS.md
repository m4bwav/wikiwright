# Tests: wikiwright

Test runs for [SKILL.md](SKILL.md). Cases live in `evals/evals.json`. A failure that taught something is a lesson in [LEARNINGS.md](LEARNINGS.md); a fix it caused is logged in [CHANGELOG.md](CHANGELOG.md) with `because: T-...`; research it triggered is in [RESEARCH.md](RESEARCH.md); counts and the failing list are in `evergreen.json` under `tests`. Rules: MAINTENANCE.md (testing section) and the plugin's `protocol/TESTING.md`.

A test passes on evidence (a tool call in the trace, a file, a marker, a log line), never on the transcript's claim that something was done.

Entry shape: `### T-YYYYMMDD-n · date · harness · env · passed/total`, then one line per failing case (`id · kind · class · what the evidence showed`), then `led to:` (L-, C-, R- ids or none). Newest first. Budget 150 lines; archive older runs to `TESTS-ARCHIVE.md`.

## Runs

### T-20260928-2 · 2026-09-28 · claude plugin eval 2.1.281 (trigger, decoy) + claude -p stream-json (action, outcome) · Windows 11 native · 7/7
- trigger-1 to trigger-3: 9/9 runs invoked `wikiwright` with the plugin, 0/9 in the no-plugin arm (`claude plugin eval . --trust-plugin --no-publish --case "trigger-*" -j 4`; $1.41). Case folders in the repository's root `evals/` (plugin eval refuses an `--eval-dir` inside `skills/`).
- decoy-1 (README), decoy-2 (CHANGELOG entry): 0/6 invocations in either arm ($0.57).
- action-1: 3/3 on the evidence as corrected after the run: a Bash call to `wikiwright.py preflight` in every trace, `wiki-draft/Home.md` written, and `npm install get-title-at-url@3.0.0` in every trace (2.3 to 2.5 minutes, about $1.05 a run; `evals/run-action.sh` in the repository root, with `--disallowedTools "Bash(git push:*) Bash(git commit:*)"`). The first grading also asked for a `*wiki-verify*` file in the workspace; the skill correctly kept the script in its session scratchpad because the workspace held no clone, so that check was a harness error, not a skill failure. Run 2 verified a different example (a docs page and a 404), so "Example Domain" was not required.
- outcome-1: 3/3: no CRLF, no wikilinks, no attribution in the three drafts; every output came from a run in the trace.
- Baseline (Skill disallowed, one run): it checked the wiki with `gh repo view` and also verified its example with `npm install get-title-at-url@3.0.0`, because it read the repository's new `ai-docs/notes/2026-09-28-github-wiki.md`. The first real run changed what the baseline can learn; action-1 is non-discriminating except for the preflight script. Sharpen it against a repository with no wiki and no wiki note.
- Version under test: the installed plugin cache held the commit of the first install (fdb68bd, the SKILL.md before C-20260928-2), so the suite exercised the pre-lesson text; the references and script the runs called came from the source path. Reinstalled after the run (L-012). Rerun the suite at the next edit.
- Second platform: untested elsewhere (the helper's unit tests run on Ubuntu, macOS and Windows in CI).
- In use: the first real run (get-title-at-url, 2026-09-28) was also a test: invoked through a user-skills junction (L-012), 9 pages published, live check clean; lessons L-007 to L-011.
- led to: C-20260928-2, L-012, L-013

### T-20260928-1 · 2026-09-28 · scaffold · skill · 0/0
- Suite scaffolded by evergreen init; replaced by T-20260928-2.
- led to: none
