# AGENTS.md

Rules for any AI agent (Claude Code, Copilot, Cursor, Codex, Gemini CLI) working in this repository. `CLAUDE.md` imports this file and `.github/copilot-instructions.md` points here.

## What this is

A cross-agent plugin with one skill, `skills/wikiwright/`: SKILL.md (the eight steps and update mode), `references/` (page sets, publishing, npm, NuGet), `templates/` (verification scripts, sidebar, footer, the ai-docs note), the single-file helper `scripts/wikiwright.py` (preflight, check, live, unbs), and the evergreen companions (RESEARCH, CHANGELOG, LEARNINGS, TESTS, MAINTENANCE, `evergreen.json`, `evals/`). Tests are in `tests/`. Handoff notes, decisions and the log are under `ai-docs/` (start with `ai-docs/HANDOFF.md`).

## Rules

- `wikiwright.py` stays one standard-library Python file (3.9 or newer) that runs on Windows, macOS and Linux. Every change to it has a test in `tests/test_wikiwright.py`; run `python tests/test_wikiwright.py` from the repository root before committing. CI runs it on the three systems.
- The skill is an evergreen unit. Before editing it read `skills/wikiwright/evergreen.json`; if `next_due` has passed or `contradiction` is set, say so and refresh after the task (`evergreen-refresh`, or `skills/wikiwright/MAINTENANCE.md`). Every change is logged in `skills/wikiwright/CHANGELOG.md` with its reason; lessons from real runs go to `LEARNINGS.md` with a code name.
- Research beats recall: GitHub's wiki behaviour and the registries' APIs change without notice. Every claim about them in the skill carries the date it was checked or an `R-` entry.
- A release bumps the version in `.claude-plugin/plugin.json`, `VERSION` in `wikiwright.py`, `metadata.version` in SKILL.md and `version` in `evergreen.json` together, then tags `vX.Y.Z` and publishes a GitHub Release with the CHANGELOG entry as notes.
- This is a public repository. Nothing in it names a person other than the author credit and the maintainers of public packages the skill was tested on, a machine, an absolute path on someone's machine, a private project, or a credential. Machine paths and identities belong in the user's private overlay.
- Prose people read (README, SKILL.md, references) is checked with the everwrite checker when it is available: `python <everwrite>/scripts/tells.py <files>`, zero strong findings.
- Never run `wikiwright.py unbs` on a file that names the `<BS>` placeholder in prose (SKILL.md, LEARNINGS.md): it replaces the name too (L-001 `backslash-placeholder`).
- No AI attribution anywhere: no Co-Authored-By trailers, no "generated with" lines in commits, pull requests, releases or files.

## everlast (session knowledge, load on demand)

- `ai-docs/INDEX.md` lists what past sessions learned here (solutions with verified commands, decisions with reasons, plans). At the start of a task, scan it and open only the entries whose title or tags match; read `ai-docs/HANDOFF.md` when continuing unfinished work (everlast-resume skill).
- Before finishing a task that hit a dead end, verified a non-obvious command, made a design choice, or taught you something about the user, record it (everlast-capture skill, or `everlast.py note` / `handoff`); rewrite `HANDOFF.md` when work is left unfinished. Say "nothing to record" when that is true.
- Anything naming a person, an internal host or name, a credential, or an opinion about people goes to the private sidecar (`--private`), never here. Lessons about the user or this machine go to the user tier (`--user`).
- Link documents together with relative markdown links: every markdown folder has an index that links its files, every entry links its index and the entries it builds on (a `Related:` line). No wikilinks in the repo.
