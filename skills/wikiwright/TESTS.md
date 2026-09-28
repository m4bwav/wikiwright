# Tests: wikiwright

Test runs for [SKILL.md](SKILL.md). Cases live in `evals/evals.json`. A failure that taught something is a lesson in [LEARNINGS.md](LEARNINGS.md); a fix it caused is logged in [CHANGELOG.md](CHANGELOG.md) with `because: T-...`; research it triggered is in [RESEARCH.md](RESEARCH.md); counts and the failing list are in `evergreen.json` under `tests`. Rules: MAINTENANCE.md (testing section) and the plugin's `protocol/TESTING.md`.

A test passes on evidence (a tool call in the trace, a file, a marker, a log line), never on the transcript's claim that something was done.

Entry shape: `### T-YYYYMMDD-n · date · harness · env · passed/total`, then one line per failing case (`id · kind · class · what the evidence showed`), then `led to:` (L-, C-, R- ids or none). Newest first. Budget 150 lines; archive older runs to `TESTS-ARCHIVE.md`.

## Runs

### T-20260928-3 · 2026-09-28 · claude plugin eval 2.1.281 (trigger, decoy) + claude -p stream-json via evals/run-action.sh (action) · Windows 11 native · 8/8
- Setup: plugin uninstalled and reinstalled before the suite; the cached SKILL.md and wikiwright.py hashes equalled the source (96aff148..., a334a1be...). Target of the action cases: m4bwav/seeded-random-utilities, which had only GitHub's placeholder page and no wiki note when the suite ran. Action runs in `%TEMP%/ww3/<run>` (short path, L-016).
- trigger-1 to trigger-3: 9/9 with the plugin, 0/9 without (`claude plugin eval <repo> --trust-plugin --no-publish --case "trigger-*" -j 4`; $1.40). decoy-1, decoy-2: 0/6 in both arms ($0.58). Two `--case` flags in one call ran only the last glob; run triggers and decoys separately.
- action-1 (hinted prompt, now against seeded-random-utilities), 3/3: every trace has `wikiwright.py preflight`, an install of `seeded-random-utilities@2.0.0` (run 1 through `npm --prefix`, which the first evidence regex missed; widened) and `wiki-draft/Home.md`; `wikiwright.py outputs` over the draft and the trace's tool results: every output on the page is in a tool result (1 of 1 in each). Runs 1 and 3 also installed 1.1.4. 1.6 to 2.9 minutes, $0.87 to $1.25 a run.
- action-1 baseline (Skill disallowed): passes every check except the preflight script (it ran `git ls-remote` and `npm install seeded-random-utilities@2.0.0`, and its output is in the trace). The prompt names the method, so the case does not discriminate (L-018).
- action-2 (new, unhinted: "Write a Home page for the GitHub wiki of m4bwav/seeded-random-utilities into ./wiki-draft/Home.md"), 2/2 on the corrected evidence: both skill runs invoked the skill, installed 2.0.0 and ran their example (outputs 1 of 1 found in the trace); run 2 ran preflight, run 1 checked the wiki by `gh repo view` and `git -C <clone>.wiki fetch` in the working copy this session had cloned (L-017), which the first regex did not accept; the evidence now accepts a fetch, pull or ls-remote in a `.wiki` working copy. Baseline 2 runs: neither installed nor ran the package, both pages show the README's example with comments and no output (outputs: 0 checked). The discriminating case.
- outcome-1: 3/3 on the action-1 drafts: no CRLF, no wikilinks, no attribution, every output printed in the trace.
- Side effects: two skill-arm runs edited the source LEARNINGS.md (kept as L-015 and a counter-case on L-016 after review; L-017).
- In use: the second real run (seeded-random-utilities, the same day) was also a test: 9 pages, check 0/0, outputs 41 checked 0 missing, live clean. The Skill tool served the session-start SKILL.md text, so the run followed the edited source by hand (L-012). Lessons L-017 to L-022.
- led to: C-20260928-3, L-015, L-017, L-018, L-012 (update)

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
