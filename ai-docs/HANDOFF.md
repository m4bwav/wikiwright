# Handoff

Updated 2026-10-26. See [INDEX.md](INDEX.md) and [log.md](log.md).

## Current work

0.9.3 is released: [PR #25](https://github.com/m4bwav/wikiwright/pull/25) merged at `bfb8563`;
[GitHub release](https://github.com/m4bwav/wikiwright/releases/tag/v0.9.3).
It adds explicit `=== label ===` transcript sections to diffout while keeping legacy `## label` recordings.
Payload Markdown headings no longer split explicit recordings.

The graphics-plugin runs supplied lessons L-166 to L-168: explicit sections, persistent replay scratch and
process ownership before stopping a PID. L-163 now permits a tagged source archive when no release asset exists.
Preflight was already required by L-002 and was confirmed again.

## Verification

- Python suite: 96 tests pass.
- Node suites: 19 pass, 3 platform skips, zero failures.
- Research refreshed 2026-10-26 across four tracks and four primary pages. Documented GitHub wiki mechanics
  remain unchanged; interval 14 days, next due 2026-11-09.
- Skill description and steps unchanged. Paid action/trigger evals were not rerun.

## Next single action

The [wiki](https://github.com/m4bwav/wikiwright/wiki) is published at `4df2cdf`: nine pages live, zero failures.
Refresh the installed plugin from a clean source.
No registry publishing is authorized. Details: [follow-up note](notes/2026-10-26-round2-followup.md).

## Earlier work still deferred

- NuGet requests scaffold size and the remaining items in the 0.9.0 log.
- Gates for prose claims, hand-copied tables and data input blocks (L-165).
- Untested application/monorepo page sets and unmeasured GitLab/Azure DevOps anchors.
- LEARNINGS consolidation, already over its budget before this follow-up.

Related: [../skills/wikiwright/CHANGELOG.md](../skills/wikiwright/CHANGELOG.md),
[../skills/wikiwright/TESTS.md](../skills/wikiwright/TESTS.md).
