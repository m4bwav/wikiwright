# Wikis on other hosts: Gitea and Forgejo, GitLab, Azure DevOps

Measured on 2026-09-29 without an account (R-20260929-1). Gitea 1.27.3 and Forgejo 16.0.5 ran as local instances with a local admin user, and GitLab CE 19.4.1 ran locally in WSL. The public hosts were read anonymously: Codeberg (`dnkl/foot`), gitlab.com (`gitlab-org/gitlab-runner`, `Remmina/Remmina`, `graphviz/graphviz`, `wireshark/wireshark`) and Azure DevOps (`powershell/PowerShell`, `dnceng-public/public`). **Verified** marks a measured claim; **unverified** marks what needs an account or a write the measurement could not make. The first real wiki on one of them went to a local Forgejo 16.0.5 on 2026-09-29: format-json-files' ten pages, seeded, pushed, checked and live-checked (R-20260929-2); Gitea, GitLab and Azure DevOps still have none.

`wikiwright.py` knows these hosts. `preflight` tells them apart by name (`codeberg.org`, `gitlab.com`, `dev.azure.com`) or by asking the API; `--kind` names one when neither works. `check --host KIND` applies the host's rules, and `live` checks the published pages through each host's API as well as the web.

## Telling the hosts apart (verified)

| Answer | Host |
|---|---|
| `GET /api/forgejo/v1/version` 200 (`16.0.5+gitea-1.22.0`) | Forgejo (Codeberg: `16.0.0-dev-...+gitea-1.22.0`) |
| `GET /api/v1/version` 200 without `+gitea`, `/api/forgejo/v1/version` 404 | Gitea |
| `GET /api/v4/version` 401 anonymously | GitLab |
| `dev.azure.com/ORG/PROJECT[/_git/REPO]`, `ORG.visualstudio.com`, `ssh.dev.azure.com:v3/ORG/PROJECT/REPO` | Azure DevOps (only the first form was seen answering) |

## At a glance

| | GitHub | Gitea / Forgejo | GitLab | Azure DevOps project wiki |
|---|---|---|---|---|
| Stored as | `OWNER/REPO.wiki.git` | `OWNER/REPO.wiki.git` | `PATH.wiki.git` | git repository `PROJECT.wiki`, hidden from the repository list; its wiki id equals its repository id |
| Branch | `master` so far | new wikis `main` (Codeberg's older ones `master`); read `ls-remote --symref`, or Forgejo's `wiki_branch` | new wikis `main`, older gitlab.com ones `master` | read it: `PowerShell.wiki` is on `wikiMaster`; whether new wikis use `wikiMain` is unverified |
| Before a first page | no repository; only a page saved in the web UI creates it | no repository (Gitea's `info/refs` answers 500, Forgejo's an empty advertisement); a push is refused; one `POST /api/v1/repos/{o}/{r}/wiki/new` with a token creates it | the repository answers with no refs, and a push creates the wiki (local CE) | `_apis/wiki/wikis` answers `count: 0`; creating one needs a project administrator (unverified) |
| Sidebar, footer | `_Sidebar.md`, `_Footer.md` | the same names; both render on every page; neither is hidden from the page list or the API | `_sidebar.md` only (an extensionless `_sidebar` is ignored); no footer seen (unverified) | none; `.order` per folder |
| Links | `[Text](Page-Name)` | `[Text](Page-Name)`, `./Page-Name`, `Page-Name.md`, `[[Page-Name]]` and `[[Text\|Page-Name]]` all resolve | `[[Page]]`, `Page`, `Page.md`, `/Page`; a bare `Page` resolves from the wiki root even inside a folder | unverified |
| Heading anchors | `usage-basic--more` | ids `user-content-...`; Gitea slugs like GitHub; Forgejo turns each run of punctuation and spaces into one hyphen and trims the ends (`usage-basic-more`, `1.0.6` as `1-0-6`, `--check` as `check`; 99 of 99 ids on a published wiki) | unverified | unverified |
| A page | 200 (Home 301 to `/wiki`) | 200, Home 200 without a redirect; page paths are case-sensitive | 200; slugs are case-insensitive | the REST page GET 200; the web page is a JavaScript shell |
| A missing page | 302 | 303 to `?action=_pages`, which answers 200 | 404 | 404 |
| Page API | none | `GET .../wiki/pages`, `.../wiki/page/{name}` (anonymous for a public repository; 404 before a first page) | `GET /projects/:id/wikis` anonymous for a public wiki; anonymous project JSON has no wiki fields | `GET _apis/wiki/wikis/{wiki}/pages?path=...` and `POST .../pagesbatch`, anonymous for a public project |

## Gitea and Forgejo

- **A push never creates the wiki.** Before a first page, `git ls-remote` fails on both hosts, and a push of a fresh repository is refused on `main` and on `master`. One authenticated `POST /api/v1/repos/{o}/{r}/wiki/new` (`title`, `content_base64`, `message`) creates it. After that, a clone and a push work, a push updates pages, and a force-push of an unrelated history replaces the seed. `wikiwright.py preflight URL --seed`, with a token in `WIKIWRIGHT_TOKEN`, does the POST; the seed page is one commit on `main`, and the pages go on top of it as a plain fast-forward. Push with `git -c http.extraHeader="Authorization: Basic <base64 of user:token>" push`, which keeps the token out of the remote URL and `.git/config` (2026-09-29). Without a token, the maintainer saves a first page at `/{o}/{r}/wiki/?action=_new`. The web UI's first-page flow was not exercised (no browser session).
- **Branch.** New wikis are on `main`. Pushing the other branch succeeds and shows nothing, so take the branch from `ls-remote --symref`. Forgejo also has `wiki_branch`, `wiki_clone_url` and `has_wiki_contents`, but reports them even for a repository whose wiki is off; `has_wiki` is the flag to trust. Gitea 1.27.3's repository object has only `has_wiki`.
- **Every wiki URL answers 200 before a first page** ("Welcome to the wiki"). A status check therefore cannot tell an empty wiki from a live one; `live` reads the page API first, which answers 404 until a page exists.
- **File names.** Hyphens show as spaces. A file named with a literal space appears in the list but cannot be opened. A file in a folder is not listed (Gitea 404, Forgejo 500). Keep the wiki flat and hyphenated; `check --host gitea` flags both.
- **Private repositories.** The API answers 404 anonymously and 200 with a token. The web pages answer 404 even with a token header, so a live check of a private wiki needs the API (not built).
- Still unverified: SSH URLs (SSH was off on both instances), `tea wiki`, and what a signed-in writer sees for a missing page.

## GitLab

- **Wiki states, as an anonymous caller sees them.** A readable wiki answers git 200, the wiki API 200 and the web 200. An enabled but empty wiki answers `ls-remote` with no refs (exit 0), the API with `[]`, and the web with "This wiki doesn't have any content yet". A disabled or members-only wiki answers git 401 and the API 403 or 404. `GET /api/v4/version` needs a token (401).
- **Creation.** A push to a never-used wiki creates it, on `main` or `master` (local CE 19.4.1). A first page made through the API or UI also commits `.gitlab/redirects.yml`, which maps renamed slugs to new ones for the web (not the API). Keep it when pushing.
- **Names and formats.**
  - Pages made in the UI or API store spaces as hyphens. A pushed file keeps its space.
  - A front-matter `title` changes the web heading, not the API title.
  - A pushed `.txt` file is listed and displayed.
- **Sidebar.** `_sidebar.md` (or `.markdown`) replaces the sidebar. The page HTML is rendered by JavaScript: the page carries `data-has-custom-sidebar` and a `data-content-api` URL. `live` therefore checks `_sidebar` in the API list, not the HTML.
- Still unverified: a footer, the 5 MB page limit and name limits, PUT and DELETE through the API, a group's default branch (group wikis need a paid tier), and gitlab.com's behaviour on a push to a new wiki (measured on local CE only).

## Azure DevOps

- **Reads.** A public project answers `_apis/wiki/wikis`, page GETs (with an `ETag`), `pagesbatch` and `git ls-remote` of the wiki repository anonymously. A private project and a missing one answer the same way, with a 302 to sign-in. Listing an organisation's projects needs sign-in even when they are public.
- **Structure.**
  - A project wiki is `PROJECT.wiki` on the branch its `versions` name.
  - A code wiki publishes a folder (`mappedPath`) of another repository.
  - A hyphen in a file name is a space in the page path, and page paths are case-sensitive.
  - `.order` files hold hyphenated names without `.md`. A page missing from `.order` got order 2147483647; no `isNonConformant` field was seen.
- Still unverified, because they need an account: creating a wiki and its branch name today, the home page and `.order` rules on a new wiki, link forms between pages, updating a page with `If-Match`, `az devops wiki`, attachments and deletion. There is no local substitute: Azure DevOps Server is not free to run.

## Page sets on these hosts (notes for the first run)

The page set for the repository's kind does not change; the navigation and names do.

- **Gitea and Forgejo.** Use the same pages, `_Sidebar.md` and `_Footer.md` as on GitHub. The sidebar and footer are pages of their own there (`/wiki/_Sidebar` answers 200, and both are in the page list and the page API under their file names), and Forgejo adds a table of contents of each page's headings. Anchors to headings with punctuation (`1.0.6`, `1.x`, `report's`, `(path, options?)`) differ from GitHub's: `check --host forgejo` finds them; a wiki meant for both hosts links only to headings whose slugs agree. Page paths are case-sensitive (`/wiki/getting-started` is missing), and `/wiki/Home` answers 200 where GitHub redirects. Seed the wiki (`--seed`) before the first push, and push to the branch preflight names.
- **GitLab.** Name the sidebar `_sidebar.md`. There is no footer, so put the "this wiki describes VERSION, updated DATE" line at the end of Home. Keep pages flat or link with `/Page` from the root.
- **Azure DevOps.** Neither a sidebar nor a footer exists: write a `.order` file listing the pages (Home first), and put the version line on Home. Links between pages are unverified; prefer `/Page-Name` as the docs show and check them after the push.

## Sources

Measurements (2026-09-29): the session's host notes, summarised in [../RESEARCH.md](../RESEARCH.md) R-20260929-1. Docs read on 2026-09-28: docs.gitlab.com/user/project/wiki/ and /api/wikis/, forgejo.org/docs/latest/user/getting-started/wiki/, docs.gitea.com/api/, learn.microsoft.com/azure/devops/project/wiki/ and the wiki REST reference (7.1).

Related: builds on [../SKILL.md](../SKILL.md); see also [publishing.md](publishing.md), [page-sets.md](page-sets.md).
