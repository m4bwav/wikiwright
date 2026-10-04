---
title: GitHub wiki written and published for wikiwright 0.9.0 (master a809eff)
kind: note
date: 2026-10-03
verified: 2026-10-03
stale_after: 2027-04-03
tags: [wiki, docs, 0.9.0, github]
summary: "the wikiwright wiki's pages, where the working copy is, how every example was verified against a fresh GitHub clone, facts found, inaccuracies in the shipped docs, and how to update the wiki"
---

# GitHub wiki for wikiwright 0.9.0

This folder sits outside the wikiwright repository on purpose: PR #3 (L-148 to L-150 and a CI fix) and others were in review on 2026-10-03, and the run was told not to commit to the main repository. Move these files into `wikiwright/ai-docs/notes/` (with a HANDOFF line and a log entry) when convenient.

## Summary

Written with the wikiwright skill (0.9.0, installed copy was 0.8.0 on this machine; the run followed the source SKILL.md). Nine pages plus sidebar and footer, wiki commit `81bba30` on https://github.com/m4bwav/wikiwright/wiki, pushed over Mark's placeholder Home page (preflight state `placeholder`, plain fast-forward).

- `check --version 0.9.0`: 9 pages, 0 errors, 0 warnings.
- `outputs` (both saved outputs): 66 checked, 0 missing, 7 skipped (hand-run install transcripts, agent prompts, a machine-dependent cachecheck).
- `snippets`: 2 blocks checked, 0 missing, 2 skipped, 3 commands.
- `live`: 9 pages, 0 failures, sidebar and footer render, 26 anchor links to 8 pages, 0 broken.
- everwrite `tells.py --wiki`: 0 strong, 15 weak (long sentences).

Pages: Home, Getting-Started, How-The-Skill-Works, What-The-Helper-Checks, Commands, Recipes, Versions-and-Upgrading, FAQ, Development, _Sidebar, _Footer.

Page set: L-148 `agent-skill-page-set` (on the PR #3 branch, not master): the command-line tool set (Commands), no API reference, one behaviour page for the skill (How-The-Skill-Works) and one for the helper (What-The-Helper-Checks). L-149 `intro-window-crosses-sentence` followed: every output fence is tagged `text` or `console`; no data block after a colon lead-in.

## Where the pages are

`../wikiwright.wiki`, branch `master`, remote https://github.com/m4bwav/wikiwright.wiki.git. LF, no BOM. Backslashes in Commands were written as the placeholder and converted with `unbs` (8).

## How the examples were verified

`2026-10-03-wiki-verify.py CLONE [PYTHON]` takes a fresh `git clone https://github.com/m4bwav/wikiwright.git` (a809eff = v0.9.0), and for each of 35 cases clones it again into a new temp folder, writes the case's fixture files, and runs each command through Git Bash with stdin closed, printing `$ command`, output with stderr merged, and `echo $?`. The scratch clone's path is masked as `<clone>`. Sections are `## label` lines, so `diffout` can compare runs.

Ran on Windows 11 with Python 3.14.6 (`2026-10-03-wiki-verify.out.txt`) and 3.9.25 (`...py39.out.txt`), git 2.55.0, gh 2.100.0, Node 24.18.0. The two outputs differ only in argparse layout (3.9 wraps `...` onto its own line and says "optional arguments"), the registry timestamps and test timing.

Network cases: `registry` (npmjs.org get-title-at-url, nuget.org RandomNameGeneratorLibrary), `preflight` and `live` against m4bwav/everwrite (read only). Download counts and the `read ... UTC` line change every run: the pages show the saved run.

By hand, not in the script:

- `claude plugin marketplace add https://github.com/m4bwav/wikiwright.git`, `claude plugin install wikiwright@wikiwright`, `claude plugin list` (0.9.0, enabled), `claude plugin marketplace update wikiwright`, `claude plugin update wikiwright@wikiwright` ("already at the latest version") in a scratch `CLAUDE_CONFIG_DIR` with Claude Code 2.1.281.
- `claude plugin marketplace add m4bwav/wikiwright` (shorthand) in a fresh config: cloned over HTTPS and succeeded. The SSH host key failure seen in the everwrite run was not reproduced.
- `gh skill install m4bwav/wikiwright wikiwright --dir ghs` (gh 2.100.0): "Using ref v0.9.0 (a809eff1)", installed; frontmatter gains `metadata` (github-path, github-ref refs/tags/v0.9.0, github-repo, github-tree-sha, version).

Not tested: macOS and Linux, Copilot/Codex/Cursor loading the skill, `gh skill install --agent/--scope`, `gh skill update`, uninstall commands, in-session `/plugin` commands, `registry --json`, running a scaffolded script, preflight states `feature-off`, `no-wiki-repo`, `archived`, `other-host`, any non-GitHub host, the eval suite.

## Facts verified while writing (not in the README)

- With `CLAUDE_CONFIG_DIR` 119 characters long, the marketplace clone failed on Windows with "Filename too long" on `ai-docs/decisions/2026-09-28-wikiwright-its-own-plugin-script-checks-model-writes-verify-.md` (92 characters); `core.longpaths=true` fixed it, and a folder one character shorter worked without it.
- `gh skill install` takes the latest release tag (v0.9.0), not `master`.
- The installed `wikiwright@mark-local` on this machine is 0.8.0 (`cachecheck`: 13 differ, 2 missing); the 0.9.0 reinstall did not happen.
- The helper prints its own errors on stdout; only argparse usage errors go to stderr. Exit 2 for usage and environment errors.
- `check` reports the backslash placeholder on any line, code blocks included, so a wiki cannot show the placeholder, and cannot paste `wikiwright.py --help` (its `unbs` line names it). The pages spell it with HTML entities.
- `scaffold` does no registry lookup; it accepts any package, version and type name that match its patterns.
- `outputs --address` default also matched on the wiki's own pages; the outputs-address example shows both behaviours.
- Node suites: 22 tests, 21 pass, 1 skipped on Windows (folder modes). Unit tests 94 OK on 3.14 and 3.9.

## Inaccuracies and gaps in the shipped docs

1. README install: only the clone-then-local-marketplace route; no `claude plugin marketplace add https://github.com/m4bwav/wikiwright.git` form and no `gh skill install` route.
2. README: "Other agents: link or copy `skills/wikiwright` into their skills folder (`~/.claude/skills/`, `~/.agents/skills/`)" names no Copilot folder.
3. README helper list omits `unbs` and `live --no-anchors`; fine as a summary, but `--help` is the only full list.
4. The 92-character ai-docs decision file name can break the plugin clone on Windows under a deep config folder; suggest a shorter name (same issue everwrite has).
5. AGENTS.md says releases run `releasecheck`; README says "tags vX.Y.Z with a GitHub Release each": true, but the README's "What it does" still says "Writing the first five wikis" while page-sets.md counts twelve. Not wrong, dated.

## Updating the wiki later

1. `git -C ../wikiwright.wiki pull --ff-only`.
2. Fresh clone of the new tag; `python 2026-10-03-wiki-verify.py <clone> > new.txt` (and with a 3.9 interpreter). `wikiwright.py diffout 2026-10-03-wiki-verify.out.txt new.txt --skip installed --skip registry --skip dev-tests`.
3. `outputs <wiki> new.txt new39.txt`, `snippets <wiki> 2026-10-03-wiki-verify.py`, `check <wiki> --version <v>`, `tells.py --wiki <wiki>/*.md`.
4. Commit, push, `wikiwright.py live m4bwav/wikiwright <wiki>`.

Pages naming the version or commit: _Footer (0.9.0, a809eff, date), Home (last line), Commands (a809eff, v0.9.0; byte counts of scaffold output; registry transcripts), Versions-and-Upgrading (table, "current version"), Getting-Started (0.9.0 in transcripts, Claude Code 2.1.281, gh 2.100.0, v0.9.0 ref), Development (94 tests, 22 Node tests, next due 2026-10-12, T-20261001-1), How-The-Skill-Works ("as SKILL.md lays it out in 0.9.0", twelve wikis).

## Gotchas

- Bash heredocs turned `\\` into `\` in a Python one-liner again; use script files.
- A ```` four-backtick ```` outer fence lets a page show a fixture page with its own fences; `check`, `outputs` and `snippets` all handle it.

Related: see also the wiki itself, https://github.com/m4bwav/wikiwright/wiki, and the everwrite run this followed, `https://github.com/m4bwav/everwrite/blob/master/ai-docs/notes/2026-10-03-wiki-run/2026-10-03-github-wiki.md`.
