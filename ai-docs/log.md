# Log

Append-only. One line per operation: `## [YYYY-MM-DD] op | title` where op is one of add, update, supersede, verify, verify-failed, prune, handoff, index. Newest at the bottom. Never edited, only appended; this is the history the entries themselves do not carry.

## [2026-09-28] init | scaffolded
## [2026-09-28] add | decision: wikiwright: its own plugin, script checks, model writes, verify against the published package
## [2026-09-28] add | skill drafted (skill-creator guidance, everwrite prose), helper wikiwright.py with 10 tests, references and templates; evergreen layer (tier fast); research pass R-20260928-1 (no wiki API, first page by hand, no competing skill)
## [2026-09-28] add | public repo m4bwav/wikiwright created; marketplace entry mark-local and install wikiwright@mark-local; ~/.wikiwright junction to the private overlay folder
## [2026-09-28] run | first run on get-title-at-url through a temporary ~/.claude/skills junction (plugin not visible mid-session): preflight placeholder, 9 pages verified against published 3.0.0 (70 fixture requests), check 0/0, everwrite 0 strong, pushed b271157 (fast-forward), live 9 pages ok, sidebar and footer render; 4 README/CHANGELOG inaccuracies in that repo's note
## [2026-09-28] update | C-20260928-2 first-run lessons L-007 to L-011 (async CLI spawn in the template, print as the page shows, claims audit, no force over a cloned placeholder, run the old majors)
## [2026-09-28] verify | T-20260928-2 7/7: triggers 9/9 vs 0/9 without plugin, decoys 0/6 (claude plugin eval, $1.98), action 3/3 headless on corrected evidence; baseline also verifies (L-013); cost about $4 for the action arm
## [2026-09-28] handoff | 0.1.0 release; open work in HANDOFF.md
## [2026-09-28] index | rebuilt (1 entries)
## [2026-09-28] verify | T-20260928-3 8/8: triggers 9/9 vs 0/9, decoys 0/6 ($1.98); action-1 against seeded-random-utilities 3/3 but its baseline passes too; new unhinted action-2 2/2 with both baselines never installing the package; outcome-1 3/3; two skill-arm runs edited the source LEARNINGS.md (L-017)
## [2026-09-28] update | enable-wiki answered: gh repo edit --enable-wiki at 19:25:33 UTC, wiki repository still missing at 61 s; Mark's first-page save 19:27:28 (ef61124) seen by ls-remote at 19:27:39; get-title-at-url's d652d15 was a click too
## [2026-09-28] add | second real run: seeded-random-utilities wiki, 9 pages, wiki commit 7980d4b, outputs 41 checked 0 missing, golden replay 322/322 (1.1.4 today) and 316/322 (2.0.0), note in that repository
## [2026-09-28] verify | update-mode rehearsal on get-title-at-url 3.0.0: saved script clean, 5 page outputs never printed in the pages' form; script fixed, Recipes line and npm skip marker (wiki 2807e56), output saved; outputs 30 checked 0 missing
## [2026-09-28] add | 0.2.0: wikiwright.py outputs, preflight other-host and elapsed seconds, check --partial, references/hosts.md (unverified), page sets for npm without a CLI, seeded output and golden captures, update mode diffs a saved output; L-016 renumbered from the duplicate L-013, L-017 to L-022
## [2026-09-28] index | rebuilt (1 entries)
