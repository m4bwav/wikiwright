# wikiwright

An agent skill that writes a repository's GitHub wiki from the repository and its package registry, runs every example on the published package, and publishes the pages. It also updates the wiki when a new version comes out. Works with Agent Skills (`SKILL.md`) in Claude Code and any agent that reads them.

A README has to stay short because it ships inside the package. A wiki can hold what the README leaves out:

- the exact behaviour contract
- every error and its message
- recipes
- the upgrade path from each old major
- answers to the questions in the issues
- how the project is built and released

wikiwright writes those pages from the source, tests, changelog, issues and registry data. Every example's output comes from the version users install, never from the working tree. Writing the first five wikis this way turned up mistakes in each package's shipped README or changelog; the skill lists such mistakes for the maintainer instead of repeating them.

## What it does

1. A preflight checks that the wiki feature is on (it can switch it on), that the `OWNER/REPO.wiki.git` repository exists, and whether it holds only GitHub's placeholder. GitHub creates that repository only when someone saves a first page in the web UI: switching the feature on does not (tested 2026-09-28), and there is no API for it. When the page is missing, the skill asks for that one click at the start and keeps working meanwhile.
2. The survey reads the README, CHANGELOG, AGENTS.md, source, tests, CI workflows, releases, issues and pull requests, `ai-docs/` notes, and the registry (versions and dates, downloads, package contents, dependencies).
3. A verification script installs the published version into a scratch folder and runs every example the pages will show. For npm that covers ESM, CommonJS and the CLI, with a local fixture server for packages that make requests, served under the real host names through a local proxy with a throwaway certificate when the package's output depends on the host. The whole script runs again on the oldest Node in `engines`. For NuGet it is a .NET 10 file-based app that also runs the pages' F# and PowerShell snippets, runs itself once per target framework (.NET Framework 4.8 included), and, for a package that makes requests, answers them from a stand-in proxy on 127.0.0.1 after checking that a request to an `.invalid` host fails there. A random example is printed only after a check that it is a possible answer, so the output is the same on every run. Deno, Bun, pnpm and yarn run from npm when they are not installed. When the repository keeps golden captures of old versions, their capture scripts are replayed against the old and the new version, including captures that start their own test server. The script and its output are kept in the repository so the next release can run it again and diff.
4. The pages follow the set for the repository's kind. A library gets Home, Getting started, API reference, a behaviour page, edge cases and errors, Recipes, Versions and upgrading, FAQ and Development, and a library with a CLI adds Commands. Every wiki gets a sidebar and a footer that names the version and the date.
5. Before publishing, `wikiwright.py check` covers links, anchors, line endings, leftover placeholders, the sidebar and footer, and AI attribution. `wikiwright.py outputs` finds every block a page presents as output (after an intro line, right after its input or code block, or in a `text` or `console` fence), every `//=>` value and every value shown in a code comment, and reports each one the verification run did not print. `wikiwright.py snippets` looks for each code block on the pages in the verification program, so the code a page shows is the code that ran. Then the skill pushes the pages, and `wikiwright.py live` confirms every page answers and the sidebar and footer render.
6. The run records a note in the repository's `ai-docs/notes/` with the pages, the verified facts, the inaccuracies found and the update procedure for the next release.

Update mode ("update the wiki for 2.4.0") re-runs the saved verification script on the new version, compares its output with the saved one section by section (`wikiwright.py diffout`), and fixes the pages that changed. A wiki written before the script was saved is adopted first: the script is completed (or written) until every page output is in its output.

Tested page sets: npm libraries with and without a CLI (the CLI set five times), NuGet libraries, packages with seeded or deterministic output, a package whose output is files on disk, and a command-line tool (a dotnet tool shipped beside its library, which runs ffmpeg and writes media files). A NuGet library whose output depends on time (a cache's lifetimes) was shown with margins two runs agree on. Applications, websites and monorepos have no tested page set yet. On Gitea, Forgejo, GitLab and Azure DevOps, `preflight`, `check --host` and `live` follow what was measured on 2026-09-29 without an account (local Gitea, Forgejo and GitLab CE instances, and anonymous reads of public wikis); what needs an account is marked unverified in `references/hosts.md`, and one real wiki has been published there so far, on a local Forgejo.

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
python skills/wikiwright/scripts/wikiwright.py registry PACKAGE        # npm or NuGet facts, one per line
python skills/wikiwright/scripts/wikiwright.py scaffold npm PACKAGE 1.2.0 -o <scratch>/wiki-verify.mjs   # the npm verification script, cut to size
python skills/wikiwright/scripts/wikiwright.py scaffold nuget ID 1.2.0 --namespace NS --type T --children net48   # the NuGet program, cut to size
python skills/wikiwright/scripts/wikiwright.py check ../REPO.wiki --version 1.2.0
python skills/wikiwright/scripts/wikiwright.py outputs ../REPO.wiki ai-docs/notes/<date>-wiki-verify.out.txt
python skills/wikiwright/scripts/wikiwright.py snippets ../REPO.wiki ai-docs/notes/<date>-wiki-verify.cs
python skills/wikiwright/scripts/wikiwright.py diffout ai-docs/notes/<date>-wiki-verify.out.txt new-run.out.txt
python skills/wikiwright/scripts/wikiwright.py live OWNER/REPO ../REPO.wiki
```

Two more help the skill's own upkeep: `cachecheck` compares the installed plugin with the source by SHA-256, and `releasecheck X.Y.Z` checks the version fields, the CHANGELOG entry and a test run before a tag. `evals/run-suite.sh` runs the action cases with and without the skill and prints one line per run, and `evals/grade-action.py <run> --digest` prints one line per tool call worth reading in a run's trace.

For packages whose requests go to fixed hosts or to the hosts their input names, `templates/npm/host-fixture.mjs` serves local pages under the real host names. It uses a proxy on 127.0.0.1, a throwaway CA and a socket guard that it tests first, so no example reaches the internet.

For packages whose output is files on disk, `templates/npm/file-tree.mjs` gives every case a fresh scratch copy of its fixture tree. It prints each written file before and after, with its size, BOM, line endings and final newline, so no example touches a real file.

## Private overlay

Your own values stay out of this repository: where your clones live, identities, and a list of which repositories have a wiki and which still owe one. Put them in a markdown file and point the skill at it with the environment variable `WIKIWRIGHT_OVERLAY`, or place it at `~/.wikiwright/OVERLAY.md`. The overlay wins over the defaults.

## Evergreen

The skill keeps its research current on a schedule (tier fast): GitHub's wiki rules, the registries' APIs and the tools for checking doc examples are re-checked from primary sources, and every change is logged with its reason in [CHANGELOG.md](skills/wikiwright/CHANGELOG.md). The research basis is in [RESEARCH.md](skills/wikiwright/RESEARCH.md); the lessons from real runs are in [LEARNINGS.md](skills/wikiwright/LEARNINGS.md).

## Privacy

wikiwright collects nothing for itself: there is no wikiwright server, account or telemetry. The skill is instructions for your agent, and the helper script runs on your machine. The work does go online, because a wiki is written from public registry data and published to your repository. These are the routes, and each one runs only when the step that needs it runs.

GitHub, as you. The preflight runs `gh repo view` and, when you ask for it, `gh repo edit --enable-wiki`, using your own `gh` login. `git` checks, clones and pushes the `OWNER/REPO.wiki.git` repository with your own git credentials, and the survey reads the repository's issues, pull requests and releases through `gh`. The pages it pushes are public on a public repository. `wikiwright.py live` then fetches the published wiki pages from github.com without credentials.

Package registries, anonymously. `wikiwright.py registry` reads package facts from registry.npmjs.org and api.npmjs.org (download counts), or from api.nuget.org and NuGet's search service. The verification step installs the published package from npm or nuget.org into a scratch folder and may fetch tools the same way: `npx` downloads a pinned Node or TypeScript (`node@20.20.2`, `typescript@7.0.2`), Corepack fetches pnpm or Yarn, and `dotnet` restores NuGet packages or installs a dotnet tool into the scratch folder. When the package under test makes requests, the templates answer them from a fixture server on 127.0.0.1, so its examples do not reach the internet. A package whose own job is to download something (a media tool fetching ffmpeg, say) does that when its examples run, and a runtime the machine lacks, such as the .NET SDK, comes from its vendor's site if you agree to install it.

Other wiki hosts, only when you name one. For Gitea, Forgejo, GitLab or Azure DevOps the script calls that host's API at the address you give it, and sends the token in the environment variable `WIKIWRIGHT_TOKEN` when it is set. That variable is the only credential the script reads itself. It also reads `WIKIWRIGHT_OVERLAY` (the path of your private overlay) and `CLAUDE_CONFIG_DIR` (to find the installed plugin for `cachecheck`). It never reads your npm or NuGet tokens and never publishes a package.

Research refresh. When the skill's research is due, the agent runs web searches and fetches public documentation with its own web tools, and may run `npx skills@1.7.0 find` for install counts on skills.sh. Those requests carry search terms about wikis and registries, not your code.

What is kept: the wiki pages in the wiki repository, and in your repository's `ai-docs/notes/` the verification script, its output and a note on how to update the wiki at the next release. Scratch folders are yours to delete. Whatever your AI app does with the conversation is covered by that app's own privacy policy.

## Versioning

Semantic versions; tags `vX.Y.Z` with a GitHub Release each. MIT licence, see [LICENSE](LICENSE).
