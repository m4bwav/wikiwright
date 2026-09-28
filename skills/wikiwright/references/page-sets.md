# Page sets and page conventions

Which pages a wiki gets, what goes on each, and the rules every page follows. Read after the survey, before writing. The page sets come from three published wikis: a .NET library with seeded data (RandomNameGeneratorLibrary, 2026-09-28), a .NET formatter (JsonPrettyPrinter, 2026-09-28) and an npm library with a CLI (get-title-at-url, 2026-09-28).

## Why a wiki beside the README

The README is the package's shop window: it ships inside the package and the registry shows it, so it stays short and changes only with a release. The wiki has no size limit and changes without a release, so it holds what the README leaves out:

- the exact behaviour contract
- every error with its message
- recipes
- the upgrade path from each old major
- the answers to questions people ask
- how to build and release the project

Every page earns its place with facts the README does not have. A page that only restates the README is cut.

## Library

| Page (file) | What it holds |
|---|---|
| Home (`Home.md`) | One paragraph on what it does and what it is not, the install line, the smallest real example with its real output, one line per page saying when to read it, links to the README, CHANGELOG, registry page and issues, the current version and its date. |
| Getting started (`Getting-Started.md`) | Every way to install it (each package manager and runtime the package supports, a script or notebook route where the ecosystem has one), each module system or language that can call it, the types, and the first call with its output. |
| API reference (`API-Reference.md`) | Every public export, type, member, option and error, with what it returns, what it throws or reports, and the version that introduced it when later than the first version on the page. Tables for members, a code block per signature that needs one. |
| The behaviour or output contract (named for the package: `Output-Format.md`, `How-Titles-Are-Chosen.md`, `Reproducible-Names.md`) | The exact rules the output follows, stated so a reader can predict any answer; what the package never changes; each rule with a verified example. |
| Edge cases and errors (`Not-a-Validator.md`, `Errors-and-Edge-Cases.md`) | Odd inputs and what comes back for each, every error with its exact message, what the package refuses to do and why. |
| Recipes (`Recipes.md`) | Real tasks: files, HTTP, tests, logging, framework integration, other languages. Each recipe runs as shown. |
| Versions and upgrading (`Versions-and-Upgrading.md`) | Every release with its date (from the registry), what changed for callers, and a section per old major on moving to the current one, from the CHANGELOG and a golden capture of the old version, or the old major run against the same fixture when there is none. Whether each old version still installs, whether it is deprecated, and its recent downloads. |
| FAQ (`FAQ.md`) | The questions the issues, pull requests, README and survey raise, answered in two to five sentences each, linking the page with the detail. |
| Development (`Development.md`) | Clone, build, test, lint commands, the CI matrix, how a release is made, where the maintainer's notes are (AGENTS.md, ai-docs). |
| Optional: Performance (`Performance-and-Threading.md`) | Only with a benchmark or a thread-safety question to answer: the numbers with the machine and date, what is safe to share. |
| Optional: data sources (`Name-Lists-and-Data-Sources.md`) | Only when the package embeds data: where it comes from, counts, licence, known quirks. |

## Library with a command line

Add Commands (`Commands.md`): the usage text as the bin prints it, every flag, exit codes, stdout versus stderr, and real invocations with their real output (run the published bin; for a package that makes requests, against the local fixture server, then show the output with the fixture's address replaced by a real-looking one only when the replacement is stated on the page).

## Command-line tool (a dotnet tool, an npm package that is mostly a bin)

Home, Getting started (install and uninstall, shell completion if any), Commands (one section per command), Configuration (files, environment variables, precedence), Recipes, Versions and upgrading, FAQ, Development.

## Not yet covered

An application, a website, a monorepo with several packages, and hosts other than GitHub (GitLab and Gitea wikis are also git repositories, with other page rules) have no tested page set. For an application, start from Home, Getting started (run it), Configuration, Architecture, Deploying, FAQ, Development, and record what the run learned in LEARNINGS.md.

## Conventions every page follows

- File names: words joined by hyphens, a capital on each word (`Getting-Started.md`), because GitHub shows the file name with spaces as the page title. Page URLs are case-insensitive, but links should match the file name exactly. A title cannot contain these characters: backslash, `/ : * ? " < > |` (GitHub Docs, "Adding or editing wiki pages").
- Headings in sentence case. The page title comes from the file name, so a page starts with its first paragraph or a `#` heading that repeats the title in sentence case; pick one pattern per wiki.
- Links between pages are plain markdown with the page name: `[Recipes](Recipes)`, `[the errors](API-Reference#errors)`. No wikilinks (`[[Page]]`), no `.md` suffix, no site-absolute paths.
- Examples show their real output, produced by the verification script against the published package. Input and output go in paired code blocks ("`pretty` is:" and then the block): a markdown table cannot hold multi-line output.
- Anything not run says so: "not tested" beside the platform or runtime, never an implied yes (JsonPrettyPrinter's Unity row).
- Versions: the API reference names the version that introduced each member later than the page's baseline; the footer names the current version and the date the wiki was last updated.
- Numbers from the registry (downloads, sizes, dates) carry the date they were read.
- LF line endings, UTF-8 without a byte order mark.
- No AI attribution in pages or wiki commits.
- Prose is checked with the everwrite checker when it is installed (`tells.py *.md`); zero strong findings.

## Sidebar and footer

`_Sidebar.md` groups the pages under short plain-text labels (for example "Using it", "The releases", "Contributing", "Elsewhere") and links every page plus the README, CHANGELOG and registry page. `_Footer.md` is one line:

```
This wiki describes PACKAGE VERSION and was last updated on YYYY-MM-DD. The library is LICENCE licensed. Report problems in the [issues](https://github.com/OWNER/REPO/issues).
```

Starting points: [../templates/pages/](../templates/pages/).

Related: builds on [../SKILL.md](../SKILL.md); see also [publishing.md](publishing.md), [npm.md](npm.md), [nuget.md](nuget.md).
