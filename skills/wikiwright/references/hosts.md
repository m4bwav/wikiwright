# Wikis on other hosts: GitLab, Gitea and Forgejo, Azure DevOps

**Unverified.** Everything on this page comes from the hosts' own documentation and API descriptions, read on 2026-09-28 (sources at the end). No wikiwright run has written a wiki on any of these hosts yet. The first run on one of them checks each claim it relies on, corrects this page, and records the lesson in [../LEARNINGS.md](../LEARNINGS.md). Until then, treat each host's section as a list of things to check, not a procedure. "Unconfirmed" marks a point the docs did not settle.

`wikiwright.py preflight` handles GitHub only. For any other remote it stops, names the host, and points here.

## Telling the hosts apart

| Remote URL | Host |
|---|---|
| `github.com/OWNER/REPO` | GitHub: [publishing.md](publishing.md) |
| `gitlab.com/...`, or a self-managed host that answers `GET /api/v4/version` (that call needs a token) | GitLab |
| `codeberg.org/...`, or any host whose `GET /api/v1/version` answers without auth; a version like `16.0.0-...+gitea-1.22.0` or a working `/api/forgejo/v1/version` means Forgejo | Gitea or Forgejo |
| `dev.azure.com/ORG/PROJECT/_git/REPO`, `ORG.visualstudio.com`, `ssh.dev.azure.com:v3/ORG/PROJECT/REPO` | Azure DevOps |

## At a glance

| | GitHub (tested) | GitLab | Gitea / Forgejo | Azure DevOps project wiki |
|---|---|---|---|---|
| Stored as | git repository `OWNER/REPO.wiki.git` | a separate git repository; the clone URL is shown under Wiki actions > Clone repository (a `.wiki.git` URL is unconfirmed) | git repository `REPO.wiki.git` (Forgejo docs; Gitea's docs are silent) | git repository `PROJECT.wiki`, at `dev.azure.com/ORG/PROJECT/_git/WIKINAME`, hidden from the Repos list |
| Branch | `master` so far | the instance's or group's default, else `main` | Forgejo: the API's `wiki_branch` (new wikis `main`, older ones `master`); Gitea unconfirmed | `wikiMain` in the concept docs, `wikiMaster` in the REST sample: read it, never assume |
| Exists before a first page | no; only a page saved in the web UI creates it | empty until a page with the path `home` exists; whether a push can create it is unconfirmed | Forgejo prompts for `Home.md` after enabling; `has_wiki_contents` says whether any page was ever made | created by the UI, `az devops wiki create --type projectwiki` or REST `POST _apis/wiki/wikis` (project administrator) |
| File name to title | hyphens shown as spaces | spaces stored as hyphens and shown as spaces; `/` makes folders; a front-matter `title:` overrides | unconfirmed (examples use `Page-1`) | hyphen means space; case-sensitive; no `/ \ #`; path at most 235 characters with the repository URL |
| Links between pages | `[Text](Page-Name)` | `[[Page]]`, `[Text](page-slug)`, `.md` optional, `/` from the root | `[[Home]]`, `[Text](./Page-1/)` | `[Text](/parent/child)`, no `.md` |
| Sidebar and footer | `_Sidebar.md`, `_Footer.md` | a page named `_sidebar` replaces the sidebar; no footer | `_Sidebar.md`, `_Footer.md` (Forgejo docs) | none; a `.order` file per folder sets page order |
| Page API | none | `/projects/:id/wikis` (create, read, update, delete) | `/repos/{owner}/{repo}/wiki/new`, `/wiki/page/{name}`, `/wiki/pages` | `_apis/wiki/wikis/{id}/pages` (updates need the ETag) |
| CLI | none | none (`glab api` only) | `tea wiki` | `az devops wiki` and `az devops wiki page` |
| Feature flag | `hasWikiEnabled` | `wiki_access_level` (`disabled`, `private`, `enabled`) | `has_wiki` (`external_wiki` for an outside wiki) | `GET _apis/wiki/wikis` is empty |

## GitLab

- **Repository.** "Each wiki is a separate Git repository." It has no footer file. A page named `_sidebar` replaces the default sidebar, which otherwise lists pages alphabetically, up to 5,000 of them.
- **Formats.** Markdown (`.md`, `.markdown`, `.mdown`, `.mkd`, `.mkdn`), AsciiDoc and others. Files with unsupported extensions do not display when pushed.
- **Limits.**
  - The 5 MB page limit is enforced in the UI and the API, not on a git push.
  - A file name may be 245 bytes, plus 10 for the extension.
  - Group wikis need Premium or Ultimate.
- **API.**
  - `GET` and `POST /projects/:id/wikis`, and `GET`, `PUT` and `DELETE /projects/:id/wikis/:slug`, with `title`, `content` and `format`.
  - A slug with a folder is URL-encoded (`dir%2Fpage`).
  - Authentication is the `PRIVATE-TOKEN` header.
  - Because there is an API, a GitLab run could skip git entirely. Prefer git anyway, so the working copy and the note work as they do on GitHub.
- The first run on this host checks:
  - Does a push to a fresh wiki create it?
  - Is the clone URL `PROJECT.wiki.git`?
  - Do links without `.md` resolve?
  - Does the sidebar page need the `.md` extension?

## Gitea and Forgejo

- **Repository.** Forgejo's docs: "a separate Git repository", cloned as `REPO.wiki.git` (`git clone git@codeberg.org:knut/foobar.wiki.git`). It holds Markdown files, with `_Sidebar.md` and `_Footer.md`. Files starting with `_` are hidden in the page list. Forgejo's web UI cannot manage images, so they go in with git.
- **API.** The same routes on both, from each host's live swagger:
  - `POST /api/v1/repos/{owner}/{repo}/wiki/new`, with `title`, `content_base64` and `message`.
  - `GET /wiki/pages`.
  - `GET`, `PATCH` and `DELETE /wiki/page/{pageName}`.
  - `GET /wiki/revisions/{pageName}`.

  Content is base64. The repository object carries `has_wiki`; Forgejo also carries `wiki_branch`, `wiki_clone_url` and `wiki_ssh_url`. An administrator can switch wikis off for the whole instance (`DISABLED_REPO_UNITS=repo.wiki`).
- **CLI.** `tea wiki list|view|revisions|create|edit|delete` (tea 0.16.0).
- The first run on this host checks:
  - Gitea's clone URL and branch.
  - Whether a push to an empty wiki works.
  - How a file name maps to a title.
  - Whether `[Text](Page-Name)` links resolve without the `./` and trailing slash.

## Azure DevOps

- **Two kinds of wiki.** The project wiki is a git repository `PROJECT.wiki`, one per project. A code wiki publishes a folder of any repository at a branch, and a project may have several. Both keep `.md` pages and an `.attachments` folder.
- **Page order.** A `.order` file in each folder lists page names, one per line, without `.md`, in the file's case. The first line of the root `.order` is the home page. A pushed page missing from `.order` shows a warning icon (`isNonConformant` in the API). A folder with only subfolders shows blank unless it holds a file.
- **Subpages.** A subpage lives in a folder named like its parent page.
- **Names.**
  - Pages cannot contain `/ \ #`, control characters, or a leading or trailing dot.
  - `: < > * ? | - "` are allowed and URI-encoded (a hyphen becomes `%2D`).
  - Pages are limited to 18 MB and attachments to 19 MB.
- **API.**
  - `PUT .../_apis/wiki/wikis/{wiki}/pages?path=...` creates a page. An update sends `If-Match` with the page's ETag.
  - `POST .../pagesbatch` lists pages.
  - Scope `vso.wiki_write`, api-version 7.1.
  - The API cannot delete a project wiki; deleting its repository does.
  - `az devops wiki page update` needs `--version` (the ETag). The CLI does not support Azure DevOps Server.
- **Caution.** Microsoft's own wiki-file-structure page is marked AI-assisted and mentions GitHub where it means Azure DevOps. Check its details against the REST reference.
- The first run on this host checks:
  - The branch name.
  - Whether a created project wiki has a first page.
  - How `.order` and a Home page interact.
  - Whether plain relative links work beside the documented absolute ones.

## What changes for wikiwright on these hosts

The survey, the verification script, the output check (`wikiwright.py outputs`) and the claims audit do not depend on the host. What changes:

- **Preflight.** Replace `gh repo view` with the host's API or CLI.
- **Link syntax and navigation files.** `wikiwright.py check` knows only GitHub's rules: it flags `[[...]]`, which GitLab and Forgejo accept, and it expects `_Sidebar.md` and `_Footer.md`, which Azure DevOps lacks.
- **The live check.** `wikiwright.py live` fetches `github.com/OWNER/REPO/wiki/...` only.

Until a run proves a host, write the pages, verify them, and push by hand with the host's documented clone URL.

## Sources (read 2026-09-28)

GitLab: docs.gitlab.com/user/project/wiki/, /user/project/wiki/markdown/, /user/project/wiki/group/, /api/wikis/, /api/projects/, /api/version/, /administration/wikis/, /cli/commands/. Forgejo: forgejo.org/docs/latest/user/getting-started/wiki/ (v16.0), codeberg.org/swagger.v1.json, codeberg.org/api/v1/version, codeberg.org/forgejo/forgejo/pulls/2264. Gitea: docs.gitea.com/api/operations/repo-create-wiki-page/ (and the get, edit, delete and list pages), docs.gitea.com/administration/config-cheat-sheet, gitea.com/swagger.v1.json, gitea.com/gitea/tea docs/CLI.md (v0.16.0). Azure DevOps: learn.microsoft.com/azure/devops/project/wiki/ (wiki-file-structure, provisioned-vs-published-wiki, wiki-create-repo, wiki-update-offline, publish-repo-to-wiki, markdown-guidance), learn.microsoft.com/rest/api/azure/devops/wiki/ (pages create-or-update, pages-batch get, wikis create; 7.1), learn.microsoft.com/cli/azure/devops/wiki/page.

Related: builds on [../SKILL.md](../SKILL.md); see also [publishing.md](publishing.md), [page-sets.md](page-sets.md).
