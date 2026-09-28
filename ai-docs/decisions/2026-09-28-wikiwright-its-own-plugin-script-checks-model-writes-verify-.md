---
title: "wikiwright: its own plugin, script checks, model writes, verify against the published package"
kind: decision
status: active
date: 2026-09-28
verified: 2026-09-28
stale_after: 2027-03-27
tags: [wiki, design, naming]
summary: why wikiwright is a separate -wright plugin, why the helper is one stdlib script, and why examples come from the published package; read before changing the skill's shape or its name
---

# wikiwright: its own plugin, script checks, model writes, verify against the published package

## Context

Two GitHub wikis (RandomNameGeneratorLibrary and JsonPrettyPrinter, both NuGet) were written by hand on 2026-09-28, and each found errors in the package's shipped docs. The maintainer asked for a public skill that repeats the procedure on any repository, is wired into the package-modernize runs, and keeps its research current (evergreen, tier fast). Working name from the request: wikiwright, after chartwright, threewright and sitewright.

## Decision

A separate public plugin, m4bwav/wikiwright, with one skill. The deterministic steps live in one standard-library Python script (`wikiwright.py`: preflight, check, live, unbs). The judgment steps stay in SKILL.md: the survey, the page set, the writing, what counts as an inaccuracy. Every example on a page comes from a verification script run against the version installed from the registry.

## Reasons

- The name was kept. `m4bwav/wikiwright` was free on 2026-09-28, the -wright family names what the plugin makes, and no conflicting skill of that name was found in the research pass (R-20260928-1).
- A wiki is useful to any repository, not only to a modernized package, so the skill stands alone; package-modernize calls it from its wrap-up.
- The link, anchor, placeholder and live checks are mechanical and were done by eye in the two hand runs; a script makes them cheap and repeatable, on every OS.
- Examples verified against the working tree can describe code users do not have yet. The published package is what readers install.

## Rejected alternatives

- A reference file inside package-modernize: the skill would trigger only for modernization runs, and a wiki for an app or a current package could not use it.
- Publishing from CI with github-wiki-action: pages change with releases, not commits, and the action still needs the first page made by hand. It is pointed at in references/publishing.md as the alternative for repositories that keep a `wiki/` folder.
- A code-to-wiki generator (CodeWiki, DeepWiki): these write architecture docs and run no examples.

## Consequences

- Each release of a package with a wiki runs update mode (package-modernize's wrap-up does this).
- Applications, monorepos and GitLab or Gitea wikis need their own page sets, written only after a run proves them.
- Revisit if GitHub adds a wiki API (the preflight's first-page stop would go away).

Related: see also [../HANDOFF.md](../HANDOFF.md).
