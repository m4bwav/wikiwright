# Changelog: wikiwright

Every change to [SKILL.md](SKILL.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20260928-3 · 2026-09-28 · 0.2.0: output check, enable-wiki answer, golden captures, update-mode fixes, other hosts (`output-check-and-second-run`)
- because: user request (wikiwright 0.2.0 kickoff); the second run (seeded-random-utilities 2.0.0 wiki, commit 7980d4b); the update-mode rehearsal on get-title-at-url (wiki commit 2807e56); T-20260928-3; R-20260928-2; L-002 (resolved), L-012 (update), L-015, L-017 to L-022
- files: scripts/wikiwright.py (outputs, preflight host detection and elapsed seconds, check --partial, placeholder message); tests/test_wikiwright.py (17 tests); SKILL.md (Step 1, Step 3, Step 4, Step 6, Step 8, Update mode, intro); references/hosts.md (new); references/publishing.md (the four runs, the enable answer); references/page-sets.md (tested kinds table, npm library without a CLI, deterministic output, golden captures); references/npm.md (runtimes from npm, yarn Plug'n'Play, console.log form, time zones); templates/npm/wiki-verify.template.mjs (`example()`, saved output); templates/wiki-note.template.md (saved output, outputs step); evals (action-1 against seeded-random-utilities, new action-2, run-action.sh parameterised by REPO and CASE); LEARNINGS.md (duplicate L-013 renumbered to L-016; L-017 to L-022)
- What changed and why:
  - `wikiwright.py outputs <wiki dir> <verify output>` finds every block a page presents as output (a `text`, `console` or `output` fence, or an untagged or data fence after "Output:", "is:", "gives", "prints" and the like; `$ ` transcripts checked per command; `//=>` values matched as whole lines) and reports each one missing from the verification output, reading the fixture's `http://127.0.0.1:<port>` as `https://example.com`. It makes L-008 and L-009 checkable. On its first real use it found five page outputs on the published get-title-at-url wiki that the saved script never printed in the pages' form (L-019).
  - Update mode now diffs against a saved output. The rehearsal showed the old procedure ("compare with the pages") had no saved output and could not notice hand-converted outputs.
  - Preflight answers the open question: enabling the wiki does not create the repository (61 seconds without it, then 11 seconds after the maintainer's first-page save). It prints elapsed seconds, takes a URL or a clone, and stops with `STATE: other-host` for GitLab, Gitea, Forgejo, Azure DevOps or an unknown host instead of failing inside `gh`. The placeholder line no longer says "force-push allowed" (L-010).
  - Page sets record "npm library without a CLI" and "deterministic or seeded output" as tested, and say how a golden capture feeds Versions and upgrading (replay the capture script against the old and new versions, L-020).
  - `check --partial` for a draft of a few pages (L-015). references/hosts.md from primary docs, marked unverified; applications and monorepos are still listed as lacking.

### C-20260928-2 · 2026-09-28 · Lessons of the first run, get-title-at-url (`first-run-lessons`)
- because: L-007 `async-cli-with-fixture`, L-008 `print-as-the-page-shows`, L-009 `claims-audit`, L-010 `placeholder-fast-forward`, L-011 `run-the-old-majors`, L-012 `midsession-skill-load`; the first run of the skill (get-title-at-url 3.0.0 wiki, commit b271157; the repository's ai-docs/notes/2026-09-28-github-wiki.md)
- files: SKILL.md (Step 4: print as the page shows, run the old majors; Step 6: claims audit; Step 7: plain push over a cloned placeholder), references/publishing.md (placeholder row, push step), references/page-sets.md (Versions row), templates/npm/wiki-verify.template.mjs (asynchronous `cli()`, old-major hint), LEARNINGS.md (L-007 to L-012)
- The first real run found one template bug before it bit, one wrong instruction (the force-push), and three inferred sentences in a draft page; each is now a step or a template fix.

### C-20260928-1 · 2026-09-28 · Created as an evergreen unit
- because: user request
- files: SKILL.md, RESEARCH.md, LEARNINGS.md, evergreen.json (skills: also TESTS.md and evals/evals.json)
- Initial version. Tier `fast`, interval 14d. See R-20260928-1 for the research basis; the first test run, for a skill, is logged in TESTS.md.
