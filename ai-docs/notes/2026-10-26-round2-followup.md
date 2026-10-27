---
title: Graphics-wiki lessons, explicit transcript sections and 0.9.3 release
kind: note
date: 2026-10-26
verified: 2026-10-26
stale_after: 2027-04-26
tags: [wiki, release, diffout, research]
summary: "0.9.3 release and research evidence; explicit transcript sections fix Markdown payload splitting"
---

# Graphics-wiki follow-up

[PR #25](https://github.com/m4bwav/wikiwright/pull/25) is merged.
[Release 0.9.3](https://github.com/m4bwav/wikiwright/releases/tag/v0.9.3) points at `bfb8563`.
No registry publishing occurred.

diffout now uses explicit `=== label ===` markers when present and retains legacy `## label` recordings.
Two regressions cover Markdown payload headings and duplicate labels. Python: 96 tests pass.
Node: 19 pass, three platform skips, zero failures. Releasecheck passes all version, changelog and test gates.
The description and steps were unchanged, so paid skill evals were not rerun.

The research refresh checked four tracks and four primary pages. Documented GitHub wiki mechanics remain
unchanged. Interval stays 14 days; next due 2026-11-09. L-163 now permits tagged source archives when no asset
exists. L-166 to L-168 cover transcript delimiters, persistent replay scratch and process ownership.

The wiki update retains explicitly dated 0.9.0 recordings and adds the 0.9.3 behavior and release history.
Full historical installer and registry examples were not rerun for this targeted update.
[Wiki](https://github.com/m4bwav/wikiwright/wiki) published at `4df2cdf`: nine pages, zero live failures,
zero broken anchors. Structure passes; 66 recorded outputs checked, zero missing, seven historical skips;
snippets two blocks and three commands, zero missing; prose zero strong findings.

Related: [../INDEX.md](../INDEX.md), [../HANDOFF.md](../HANDOFF.md),
[../../skills/wikiwright/CHANGELOG.md](../../skills/wikiwright/CHANGELOG.md).
