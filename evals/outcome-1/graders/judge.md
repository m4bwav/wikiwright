---
type: llm
name: 'expectations'
---

PASS if the reply meets every one of these:
- wiki-draft/Home.md has no wikilinks, no CRLF and no AI attribution (wikiwright.py check rules)
- the output shown on the page matches what the published 3.0.0 returns for its example (Example Domain for example.com's HTML)
FAIL if any is missing or contradicted.
