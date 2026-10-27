# Handoff

Updated 2026-10-26. See [INDEX.md](INDEX.md) and [log.md](log.md).

## Current work

0.9.4 is released: [PR #27](https://github.com/m4bwav/wikiwright/pull/27) merged at `a302891`;
[GitHub release](https://github.com/m4bwav/wikiwright/releases/tag/v0.9.4). It closes issue #10: diffout
accepts `=== label` markers without the closing `===` (editwright's verifier format). Bare `=` lines are not
markers. On editwright's 2026-10-08/09 recordings the split went from 8 sections to 58 (57 cases + preamble).

0.9.3 ([PR #25](https://github.com/m4bwav/wikiwright/pull/25), `bfb8563`) added `=== label ===` sections and
lessons L-166 to L-168.

## Verification

- Python suite: 97 tests pass. Node: 19 pass, 3 platform skips. CI matrix (3 OS x Python 3.9/3.13) passed.
- Wiki updated at `c1f579e`: check 0 errors, live 9 pages / 26 anchors, 0 failures.
- Local mark-local install refreshed to 0.9.4; 30 skill files hash-match.
- Research next due 2026-11-09. Paid action/trigger evals not rerun (description and steps unchanged).

## Next single action

Nothing owed. No registry publishing is authorized.

## Earlier work still deferred

- NuGet requests scaffold size and the remaining items in the 0.9.0 log.
- Gates for prose claims, hand-copied tables and data input blocks (L-165).
- Untested application/monorepo page sets and unmeasured GitLab/Azure DevOps anchors.
- LEARNINGS consolidation, already over its budget before this follow-up.

Related: [../skills/wikiwright/CHANGELOG.md](../skills/wikiwright/CHANGELOG.md),
[../skills/wikiwright/TESTS.md](../skills/wikiwright/TESTS.md).
