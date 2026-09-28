# Changelog: wikiwright

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20260928-2 · 2026-09-28 · Lessons of the first run, get-title-at-url (`first-run-lessons`)
- because: L-007 `async-cli-with-fixture`, L-008 `print-as-the-page-shows`, L-009 `claims-audit`, L-010 `placeholder-fast-forward`, L-011 `run-the-old-majors`, L-012 `midsession-skill-load`; the first run of the skill (get-title-at-url 3.0.0 wiki, commit b271157; the repository's ai-docs/notes/2026-09-28-github-wiki.md)
- files: SKILL.md (Step 4: print as the page shows, run the old majors; Step 6: claims audit; Step 7: plain push over a cloned placeholder), references/publishing.md (placeholder row, push step), references/page-sets.md (Versions row), templates/npm/wiki-verify.template.mjs (asynchronous `cli()`, old-major hint), LEARNINGS.md (L-007 to L-012)
- The first real run found one template bug before it bit, one wrong instruction (the force-push), and three inferred sentences in a draft page; each is now a step or a template fix.

### C-20260928-1 · 2026-09-28 · Created as an evergreen unit
- because: user request
- files: SKILL.md, RESEARCH.md, LEARNINGS.md, evergreen.json (skills: also TESTS.md and evals/evals.json)
- Initial version. Tier `fast`, interval 14d. See R-20260928-1 for the research basis; the first test run, for a skill, is logged in TESTS.md.
