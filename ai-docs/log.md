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
