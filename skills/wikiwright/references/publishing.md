# Publishing a GitHub wiki

How the wiki repository comes to exist, how the working copy is kept, and how a push is checked. Facts verified on 2026-09-28 on three repositories.

## The wiki is a git repository

Every GitHub repository with the wiki feature on can have a second repository at `https://github.com/OWNER/REPO.wiki.git`. Each page is one markdown file in its root; `_Sidebar.md` and `_Footer.md` are shown on every page. All three wikis written so far came on branch `master`, whatever the main repository uses; GitHub's docs say only pushes to the wiki's default branch go live, so push to the branch `ls-remote` reports as `HEAD`. There is no REST or GraphQL API for wiki pages (community discussions still ask for one on 2026-09-28): git is the only way in for an agent. GitHub's docs also say the repository can be cloned only once a first page exists on GitHub.

## Preflight states

`scripts/wikiwright.py preflight OWNER/REPO --enable --clone <dir>` reports one of:

| STATE | Meaning | What to do |
|---|---|---|
| `feature-off` | `hasWikiEnabled` is false | Rerun with `--enable` (it runs `gh repo edit OWNER/REPO --enable-wiki` and re-checks for 60 seconds). Private repositories on a free plan cannot have a wiki. |
| `no-wiki-repo` | The feature is on, but `git ls-remote` finds no repository | Ask the maintainer, in the first message, to save any first page at `https://github.com/OWNER/REPO/wiki/_new`. Nothing else can create it. Survey, verify and write the pages while waiting, then run preflight again. |
| `placeholder` | One commit with only a short `Home.md` (GitHub's "Welcome to the REPO wiki!") | Clone, write the pages over it, commit and `git push`: the placeholder is an ancestor, so the push fast-forwards (get-title-at-url, 2026-09-28). A working copy started with `git init` instead needs `--force-with-lease`, which is fine while the only content is the placeholder. |
| `has-pages` | Real content exists | Read every page first. Update in place; never force-push, never delete a page without the maintainer's OK. |
| `archived` | The repository is archived | Stop and ask. |

What happened in the three runs: RandomNameGeneratorLibrary had the feature on and no repository until Mark saved a page (placeholder commit 8543ca6, then force-pushed over). JsonPrettyPrinter already had a saved placeholder (3542d9a), so a normal push worked. On get-title-at-url the feature was off; a minute after `gh repo edit --enable-wiki`, `ls-remote` answered with a placeholder commit (d652d15, "Initial Home page", authored by the maintainer). Whether the enable call creates the repository or something else did is not known, so preflight re-checks after enabling and asks for the click only when the repository is still missing.

## The working copy

Clone the wiki as a sibling of the repository's clone, named `<clone>.wiki`, so it stays outside the repository and next to it: `D:\code\widget` gets `D:\code\widget.wiki`. It is its own git repository with remote `origin` pointing at the `.wiki.git` URL. The repository's `ai-docs` note names its path.

## Push and check

1. `python scripts/wikiwright.py check <wiki dir> --version X` exits 0.
2. The everwrite checker, when installed, reports 0 strong: `python <everwrite>/scripts/tells.py <wiki dir>/*.md`.
3. Commit in the wiki working copy with a message naming the version and the pages, no AI attribution, then `git push`.
4. `python scripts/wikiwright.py live OWNER/REPO <wiki dir>`: every page answers 200 (Home answers 301 to `/wiki`; a missing page answers 302), and the sidebar and footer text appear on the wiki root. GitHub can take a few seconds after a push; rerun once before calling a failure.

## Publishing from CI instead

A repository that keeps its pages in a folder (for example `wiki/`) can publish them on every push with Andrew-Chen-Wang/github-wiki-action (it also strips `.md` from links and needs `contents: write`; its README repeats that the first page must be made by hand). This skill pushes from the working copy instead, because the pages change with releases rather than commits; point the maintainer at the action when they want the pages reviewed in pull requests.

## Updating later

Pull first (`git -C <wiki dir> pull --ff-only`): someone may have edited a page in the web UI, which commits to the same repository.

Related: builds on [../SKILL.md](../SKILL.md); see also [page-sets.md](page-sets.md).
