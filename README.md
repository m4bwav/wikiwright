# wikiwright

An agent skill that writes a repository's GitHub wiki from the repository and its package registry, runs every example on the published package, and publishes the pages. It also updates the wiki when a new version comes out. Works with Agent Skills (`SKILL.md`) in Claude Code and any agent that reads them.

A README has to stay short because it ships inside the package. A wiki can hold what the README leaves out:

- the exact behaviour contract
- every error and its message
- recipes
- the upgrade path from each old major
- answers to the questions in the issues
- how the project is built and released

wikiwright writes those pages from the source, tests, changelog, issues and registry data. Every example's output comes from the version users install, never from the working tree. Writing the first three wikis this way turned up mistakes in each package's shipped README or changelog; the skill lists such mistakes for the maintainer instead of repeating them.

## What it does

1. A preflight checks that the wiki feature is on (it can switch it on), that the `OWNER/REPO.wiki.git` repository exists, and whether it holds only GitHub's placeholder. GitHub creates that repository only when someone saves a first page in the web UI, and there is no API for it. When the page is missing, the skill asks for that one click at the start and keeps working meanwhile.
2. The survey reads the README, CHANGELOG, AGENTS.md, source, tests, CI workflows, releases, issues and pull requests, `ai-docs/` notes, and the registry (versions and dates, downloads, package contents, dependencies).
3. A verification script installs the published version into a scratch folder and runs every example the pages will show. For npm that covers ESM, CommonJS and the CLI, with a local fixture server for packages that make requests. For NuGet it is a .NET 10 file-based app, plus F# and PowerShell where the pages show them. The script is kept in the repository so the next release can run it again.
4. The pages follow the set for the repository's kind. A library gets Home, Getting started, API reference, a behaviour page, edge cases and errors, Recipes, Versions and upgrading, FAQ and Development, and a library with a CLI adds Commands. Every wiki gets a sidebar and a footer that names the version and the date.
5. Before publishing, `wikiwright.py check` covers links, anchors, line endings, leftover placeholders, the sidebar and footer, and AI attribution. Then the skill pushes the pages, and `wikiwright.py live` confirms every page answers and the sidebar and footer render.
6. The run records a note in the repository's `ai-docs/notes/` with the pages, the verified facts, the inaccuracies found and the update procedure for the next release.

Update mode ("update the wiki for 2.4.0") re-runs the saved verification script on the new version and fixes the pages that changed.

Tested page sets: an npm library with a CLI, and NuGet libraries. Applications, monorepos and other wiki hosts (GitLab, Gitea) have no tested page set yet.

## Install

Claude Code, from a clone:

```
git clone https://github.com/m4bwav/wikiwright
claude plugin marketplace add ./wikiwright
claude plugin install wikiwright@wikiwright
```

If you keep several local plugins in one marketplace, add an entry with `"source": "./wikiwright"` to that marketplace's `.claude-plugin/marketplace.json` and install `wikiwright@<that marketplace>`. Other agents: link or copy `skills/wikiwright` into their skills folder (`~/.claude/skills/`, `~/.agents/skills/`).

The helper script needs Python 3.9 or newer, `git`, and the GitHub CLI (`gh`) logged in for the preflight:

```
python skills/wikiwright/scripts/wikiwright.py preflight OWNER/REPO --enable --clone ../REPO.wiki
python skills/wikiwright/scripts/wikiwright.py check ../REPO.wiki --version 1.2.0
python skills/wikiwright/scripts/wikiwright.py live OWNER/REPO ../REPO.wiki
```

## Private overlay

Your own values stay out of this repository: where your clones live, identities, and a list of which repositories have a wiki and which still owe one. Put them in a markdown file and point the skill at it with the environment variable `WIKIWRIGHT_OVERLAY`, or place it at `~/.wikiwright/OVERLAY.md`. The overlay wins over the defaults.

## Evergreen

The skill keeps its research current on a schedule (tier fast): GitHub's wiki rules, the registries' APIs and the tools for checking doc examples are re-checked from primary sources, and every change is logged with its reason in [CHANGELOG.md](skills/wikiwright/CHANGELOG.md). The research basis is in [RESEARCH.md](skills/wikiwright/RESEARCH.md); the lessons from real runs are in [LEARNINGS.md](skills/wikiwright/LEARNINGS.md).

## Versioning

Semantic versions; tags `vX.Y.Z` with a GitHub Release each. MIT licence, see [LICENSE](LICENSE).
