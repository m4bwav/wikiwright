# Research: wikiwright

Findings that back [SKILL.md](SKILL.md). Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); procedural lessons live in [LEARNINGS.md](LEARNINGS.md); test runs and their evidence in [TESTS.md](TESTS.md); schedule and state in `evergreen.json`. Protocol: MAINTENANCE.md.

Topic: GitHub wiki mechanics (the .wiki.git repository, page and sidebar rules, no page API, first-page creation) and writing library documentation whose examples are verified against the published package (npm, NuGet), plus agent tools that generate repository docs. Tier `fast`. Last refresh 2026-09-28; next due 2026-10-12.

## Current understanding

- A GitHub wiki is a separate git repository, `OWNER/REPO.wiki.git`, one markdown file per page, with `_Sidebar.md` and `_Footer.md` shown on every page. Only pushes to its default branch go live (GitHub Docs, "Adding or editing wiki pages"); all three wikis seen so far use `master`. Confidence: high.
- There is no REST or GraphQL API for wiki pages on 2026-09-28; community discussions (#153222, #169854) still ask for one. Git is the only route for an agent. Confidence: high (R-20260928-1).
- The wiki repository exists only after a first page is saved in the web UI: GitHub Docs ("once you've created an initial page on GitHub, you can clone"), Andrew-Chen-Wang/github-wiki-action's README ("You must create a dummy page manually!") and the RandomNameGeneratorLibrary run agree. Switching the feature on does not create it (tested 2026-09-28 on seeded-random-utilities: `gh repo edit --enable-wiki` at 19:25:33 UTC, `git ls-remote` every 5 seconds still "Repository not found" at 61 seconds; the maintainer's first-page save at 19:27:28 made commit ef61124 "Initial Home page", seen by ls-remote at 19:27:39). get-title-at-url's placeholder d652d15 has the same message, the web UI's default, so it was a click too. Confidence: high.
- Page URLs are case-insensitive; a missing page answers 302, Home answers 301 to `/wiki`; the wiki root's HTML carries the sidebar in `wiki-rightbar` and the footer in `#wiki-footer`. Titles may not contain the characters backslash, `/ : * ? " < > |`. Confidence: high (probed 2026-09-28; GitHub Docs).
- No existing skill, plugin or tool publishes to a GitHub wiki and verifies examples against the published package. Code-to-wiki generators (CodeWiki, ACL 2026 Findings, 1.7k stars; Devin's DeepWiki; deepwiki-open; OpenDeepWiki) write architecture docs from source and run no examples. github-wiki-action and spenserblack/actions-wiki publish a folder to the wiki from CI. Confidence: medium (search-based, R-20260928-1).
- Checking doc examples: markdown-doctest (JS fences), anko/txm (output annotations, any language), SimonCropp/MarkdownSnippets 28.4.2 (.NET snippets pulled from compiled code), lychee (links). None installs the published version from the registry, which is the check this skill adds. Confidence: medium.
- .NET 10 file-based apps enable native AOT by default, so reflection-based System.Text.Json needs `#:property PublishAot=false` (learn.microsoft.com/dotnet/core/sdk/file-based-apps). Confidence: high (seen in use 2026-09-28).
- npm's downloads range API moves any start older than 18 months up to 18 months ago, silently (checked 2026-09-28). Confidence: high.

## Open questions

- Answered 2026-09-28: `gh repo edit --enable-wiki` does not create the wiki repository by itself; get-title-at-url's placeholder d652d15 was a first-page save (see Current understanding).
- Does a wiki whose default branch is not `master` exist in practice, and does it render pushes to it?
- Page sets for an application, a monorepo and a command-line tool are untested. Answered 2026-09-29 without an account (R-20260929-1): a push creates a GitLab wiki (local CE) but never a Gitea or Forgejo one (the API's `wiki/new` does), and new wikis there use `main`. Still open, since it needs an account: the branch of a new Azure DevOps wiki (the one public sample is on `wikiMaster`), its link forms, and a real publish on any of the four hosts.

## Search plan

Four tracks; every refresh runs at least one query on each (scope each to the period since the last refresh; add the year). Protocol §4 explains the tracks and how tooling, practice and testing findings are judged.

Subject (the goal and the latest thinking on reaching it):

- `site:docs.github.com wiki` (About wikis; Adding or editing wiki pages; Creating a footer or sidebar; Changing access permissions) and `site:github.blog/changelog wiki <year>`
- `gh api` search of community discussions for "wiki api" (the discussion pages 404 without authentication)
- `"file-based apps" dotnet PublishAot site:learn.microsoft.com` and npm registry API changes (`api.npmjs.org downloads` docs)

Tooling (skills, plugins, MCP servers, scripts, knowledge graphs built for this subject):

- `path:SKILL.md "github wiki"` on GitHub code search (plain "wiki" returns personal LLM-wiki skills), sorted by recently updated; `npx skills find "github wiki"` and skills.sh for install counts
- `https://registry.modelcontextprotocol.io/v0/servers?search=github wiki`; fallback `"github wiki" mcp server site:glama.ai OR site:pulsemcp.com`
- `"github wiki" skill OR plugin OR "mcp server" <year> site:github.com`
- Most used: skills.sh weekly and 24-hour installs for `github wiki` (never all-time; exclude meta and installer skills); `anthropics/claude-plugins-official` and `claude-plugins-community` searched for `github wiki` (record the tier)
- Practitioner test on every candidate: commit in the last 90 days, issues answered, no bundled `*.test.*` or `conftest.py` from an unknown author, author has other work in the area, ships `evals/` or paired results; `path:SKILL.md "github wiki" evals OR benchmark`
- Provenance tiebreaker: which model and reasoning setting wrote each candidate (`evals.json` / frontmatter `model`, README or changelog credit, commit messages); prefer the latest frontier model at its highest reasoning setting, read over inferred
- Supersession sweep: `"github wiki" skill deprecated OR superseded OR archived <year>`; archive flag on every tool already listed here

Most discussed and the converged thinking (comment volume over points; what the most-used and most-discussed sources agree on becomes a claim in Current understanding):

- `hn.algolia.com/api/v1/search_by_date?query=github wiki` and `site:reddit.com/r/ClaudeAI OR r/ClaudeCode "github wiki" <month>`
- OpenAlex `works?search=github wiki agent&sort=cited_by_count:desc&filter=from_publication_date:<last check>`; the two most-cited through Semantic Scholar

Practice (how others use AI agents on this goal, and everything in between):

- `"how I use" OR "my workflow" "github wiki" "claude code" OR codex OR cursor <year>`
- `site:arxiv.org "github wiki" agent "case study" OR empirical OR telemetry <year>`
- `"github wiki" site:simonwillison.net OR site:latent.space OR site:anthropic.com/engineering <year>`; hn.algolia.com `"github wiki" agent` sorted by date

Testing (how work on this subject is verified, and how skills for it are tuned):

- `"github wiki" verify OR validate OR "smoke test" OR checker agent <year>` (what evidence shows the job was done)
- `path:SKILL.md "github wiki" test OR eval OR evals` on GitHub; `"github wiki" evals OR "eval suite" OR regression "agent skill" <year>`
- `site:arxiv.org "github wiki" agent evaluation OR benchmark <year>`; promptfoo, Inspect or DeepEval docs for assertion types that fit this subject

Best sources (primary first): docs.github.com wiki pages; github.blog changelog month pages; the github-wiki-action README and issues; FSoft-AI4Code/CodeWiki; learn.microsoft.com file-based apps; the npm registry API docs. Sources that proved noisy: claudecodeguides and getclaudeskills SEO guides; "wiki skill" searches without "github".

## Findings log

Newest first. One entry per material finding; a quiet refresh gets one entry saying so. `Track` is subject, tooling, practice, or testing.

### R-20260929-1 · 2026-09-29 · Other hosts measured without an account: Gitea, Forgejo, GitLab, Azure DevOps
- Summary: two subagents measured every docs-only claim in references/hosts.md. **Gitea 1.27.3** (Windows binary) and **Forgejo 16.0.5** (Linux binary in WSL) ran locally with a local admin user.
  - Neither has a wiki repository before a first page, and a push is refused on `main` and `master`. `POST /api/v1/repos/{o}/{r}/wiki/new` with a token creates the wiki; after that git works.
  - New wikis are on `main`. `_Sidebar.md` and `_Footer.md` render and are not hidden (Forgejo's docs say they are).
  - A missing page answers 303 to `?action=_pages`; every URL answers 200 before a first page.
  - Links: `[[...]]`, `./Page` and `Page.md` resolve. Forgejo collapses repeated hyphens in anchors.
  - The page API answers anonymously for public repositories. Codeberg (`dnkl/foot`, `master`) matched.
  **GitLab**, from anonymous gitlab.com reads and a local **GitLab CE 19.4.1**:
  - `.wiki.git` works, and a push creates a never-used wiki. New wikis are on `main`, older gitlab.com ones on `master`.
  - Anonymous project JSON has no wiki fields. The sidebar needs `_sidebar.md`, and a bare link resolves from the wiki root.
  - A first page made through the API adds `.gitlab/redirects.yml`. Slugs are case-insensitive, and page HTML is rendered client-side.
  **Azure DevOps**, anonymous reads of public projects:
  - The project wiki is the hidden repository `PROJECT.wiki`, on `wikiMaster` in the one sample. `count: 0` means no wiki; `.order` files exist; page GETs carry an ETag.
  - Private and missing projects both answer 302 to sign-in. Creating and editing need an account and stay unverified.
  The new `preflight`, `check --host` and `live` then ran against the local instances (no-wiki-repo, has-pages, `--seed` answering 201), Codeberg, gitlab.com and Azure DevOps; every result matched the measurements. Raw evidence stayed in the session's scratch folder; the tests carry the status codes as fixtures.
- Track: subject, tooling
- Sources: local instances (dl.gitea.com/gitea/1.27.3, codeberg.org/forgejo/forgejo/releases v16.0.5, packages.gitlab.com gitlab-ce 19.4.1); anonymous reads of codeberg.org/dnkl/foot, gitlab.com/gitlab-org/gitlab-runner, gitlab.com/Remmina/Remmina, gitlab.com/graphviz/graphviz, gitlab.com/wireshark/wireshark, dev.azure.com/powershell/PowerShell, dev.azure.com/dnceng-public/public
- Magnitude: 0.6 (every other-host claim now measured or marked unverified; three contradicted the docs: `_` files are not hidden on Forgejo, GitLab's anonymous project JSON has no wiki fields, a pushed GitLab file keeps its spaces; preflight, check and live learned four hosts)
- Applied: C-20260929-4 (references/hosts.md rewritten; wikiwright.py preflight, check --host, live; L-123 to L-127)

### R-20260928-2 · 2026-09-28 · Wikis on GitLab, Gitea/Forgejo and Azure DevOps; enabling a GitHub wiki creates nothing
- Summary: a research pass over primary docs only (a subagent, about 40 pages and two live swagger files) for the hosts other than GitHub. GitLab: each wiki a separate git repository, clone URL from the UI, branch the instance default else `main`, a `_sidebar` page and no footer, a full wiki REST API (`/projects/:id/wikis`), no glab wiki command, `wiki_access_level` on the project. Gitea and Forgejo: `REPO.wiki.git`, `_Sidebar.md` and `_Footer.md` (Forgejo docs), the same REST routes on both (`/repos/{owner}/{repo}/wiki/new`, `/wiki/page/{name}`), `tea wiki`, Forgejo's `wiki_branch` field (new wikis `main`). Azure DevOps: project wiki repository `PROJECT.wiki`, page order from `.order` files, no sidebar or footer, pages REST API with ETags, `az devops wiki page`, branch `wikiMain` or `wikiMaster` depending on the page read. Gaps the docs leave: whether a push creates a GitLab or Gitea wiki, Gitea's clone URL and branch, file-name to title rules on Gitea. Also this session's test of the open question: enabling the GitHub wiki feature did not create the repository in 61 seconds; the first-page save did, within 11 seconds.
- Track: subject
- Sources: https://docs.gitlab.com/user/project/wiki/, https://docs.gitlab.com/api/wikis/, https://forgejo.org/docs/latest/user/getting-started/wiki/, https://codeberg.org/swagger.v1.json, https://gitea.com/swagger.v1.json, https://docs.gitea.com/api/operations/repo-create-wiki-page/, https://learn.microsoft.com/en-us/azure/devops/project/wiki/wiki-file-structure, https://learn.microsoft.com/en-us/rest/api/azure/devops/wiki/pages/create-or-update?view=azure-devops-rest-7.1, https://learn.microsoft.com/en-us/cli/azure/devops/wiki/page (full list in references/hosts.md)
- Magnitude: 0.3 (a new reference; the enable answer closes an open question and changes no rule, since preflight already asked for the click when the repository was missing)
- Applied: C-20260928-3 (references/hosts.md; preflight `other-host`; publishing.md and SKILL.md Step 1 state the enable answer)

### R-20260928-1 · 2026-09-28 · Initial research: no wiki API, first page by hand, no competing skill
- Summary: four tracks, 8 searches and 4 fetches by the evergreen-researcher. Subject: GitHub Docs confirm clone-after-first-page, only-default-branch-goes-live and the forbidden title characters; no wiki API in 2026. Tooling: github-wiki-action (111 stars, Apache-2.0; README says the first page is manual; issue #95 of 2026-09-14 says v5 lags its README) and actions-wiki publish folders from CI; CodeWiki, DeepWiki, deepwiki-open, OpenDeepWiki and deepwiki-by-cc generate architecture wikis without running examples; no `.wiki.git` publishing skill that verifies examples was found. Practice: 2026 guides describe read-the-source-then-generate; no data on wrong examples in agent-written docs. Testing: markdown-doctest, txm, MarkdownSnippets 28.4.2 (2026-07-28), lychee. Plus the facts measured while writing the skill: missing page 302, Home 301, sidebar and footer markers in the root HTML, the npm range API's silent 18-month clamp. skills.sh and the MCP registry were not checked in this pass.
- Track: subject, tooling, practice, testing
- Sources: https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages, https://github.com/orgs/community/discussions/169854, https://github.com/Andrew-Chen-Wang/github-wiki-action, https://github.com/FSoft-AI4Code/CodeWiki, https://github.com/anko/txm, https://github.com/SimonCropp/MarkdownSnippets/releases, https://github.com/lycheeverse/lychee
- Magnitude: n/a (initial; the largest finding would be 0.3)
- Applied: C-20260928-1 (references/publishing.md: default branch, no API, CI alternative; references/page-sets.md: forbidden characters; references/npm.md: complementary tools, range clamp)
