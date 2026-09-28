# Page sets and page conventions

Which pages a wiki gets, what goes on each, and the rules every page follows. Read after the survey, before writing. The page sets come from five published wikis, all written on 2026-09-28:

- RandomNameGeneratorLibrary: a .NET library with seeded data.
- JsonPrettyPrinter: a .NET formatter.
- get-title-at-url: an npm library with a CLI.
- seeded-random-utilities: an npm library without a CLI, with seeded output and golden captures of two old versions.
- is-an-image-url: an npm library with a CLI that makes requests, with a golden capture of 1.0.4 that starts its own fixture server.

| Kind | Tested on |
|---|---|
| Library (npm, without a CLI) | seeded-random-utilities |
| Library (NuGet) | RandomNameGeneratorLibrary, JsonPrettyPrinter |
| Library with a command line (npm) | get-title-at-url, is-an-image-url (second run: the set held without changes) |
| Deterministic or seeded output | seeded-random-utilities, RandomNameGeneratorLibrary |
| Command-line tool | not yet (the section below is a sketch; candidate: TrailerClipper.Tool, a dotnet tool) |
| Application, website, monorepo | not yet (see the end of this page) |
| Hosts other than GitHub | not yet ([hosts.md](hosts.md) is unverified) |

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
| Versions and upgrading (`Versions-and-Upgrading.md`) | Every release with its date (from the registry), what changed for callers, and a section per old major on moving to the current one, from the CHANGELOG and a golden capture of the old version, or the old major run against the same fixture when there is none (see "Golden captures" below). Whether each old version still installs, whether it is deprecated, and its recent downloads. The same calls on the old and the new version side by side, with their real output. |
| FAQ (`FAQ.md`) | The questions the issues, pull requests, README and survey raise, answered in two to five sentences each, linking the page with the detail. |
| Development (`Development.md`) | Clone, build, test, lint commands, the CI matrix, how a release is made, where the maintainer's notes are (AGENTS.md, ai-docs). |
| Optional: Performance (`Performance-and-Threading.md`) | Only with a benchmark or a thread-safety question to answer: the numbers with the machine and date, what is safe to share. |
| Optional: data sources (`Name-Lists-and-Data-Sources.md`) | Only when the package embeds data: where it comes from, counts, licence, known quirks. |

An npm library without a command line takes exactly the table above: seeded-random-utilities had nine pages, with no Commands page. Its Getting started page ran every install route it names (npm, pnpm, yarn 4, Bun, Deno; see [npm.md](npm.md#other-runtimes-and-package-managers)), both module systems and a TypeScript compile that shows a real type error.

## Deterministic or seeded output

When the same input always gives the same output (a seeded generator, a formatter, embedded name lists), the wiki can promise exact output, and should:

- Name the behaviour page after the promise (`Same-Seed-Same-Sequence.md`, `Reproducible-Names.md`). It says what stays the same across runs, runtimes, module systems and versions, each with the run that showed it, and what breaks the promise (a different order of calls, no seed, another library with the same algorithm names, floating-point functions engines approximate).
- Show how the output is consumed, when that decides reproducibility: how many draws each call takes, and that one extra call moves everything after it.
- Run each example twice and under each runtime the pages name, and compare. Save the script's output: seeded output is identical on every run, so the next release diffs it line by line (L-019 `save-the-output-too`). Keep time zones, paths, ports and timings out of it (L-022 `machine-free-output`).

## Golden captures

A repository modernized with package-modernize, or any repository that recorded an old version's behaviour (`test/golden/`, a capture script beside a JSON file), hands Versions and upgrading its best evidence (L-020 `replay-the-golden-capture`):

1. Install the old version from the registry into its own scratch folder and run its capture script there. Compare the result with the golden file case by case. Identical means the recording still stands in for the old version.
2. Run the same capture script against the current published version, changing only what must change (a dependency's version line), and compare again. The differing cases and changed quirks are the upgrade notes; each should match a CHANGELOG entry, and one that does not is a finding.
3. Run any capture of the current version (`capture-2.0.0.cjs`) against the published build.
4. Put the counts and the differing cases on the page. Only read the golden files, never rewrite them.

On seeded-random-utilities: 1.1.4 today matched its recording in 322 of 322 cases, 2.0.0 in 316 (the six were the documented emoji exception), and 2.0.0 its own recording in 150 of 150.

A package that makes requests records its old version against a fixture server of its own (is-an-image-url's `capture-1.0.4.cjs` with `fixture-server.cjs` and `codec.cjs`, L-113 `replay-requesting-capture`). What that needs:

- Copy the capture script and every helper it requires beside each installed version, and install what the capture requires besides the package (is-an-image-url's needed `is-image` and an alias `is-image-300@npm:is-image@3.0.0`).
- Patch only what the new layout breaks, and say which lines on the page: the bin's path (`cli.js` became `dist/cli.mjs`) and a dependency lookup that fails when the new version has none.
- Run it as a child process, one version after the other: it starts its own server and has timing cases. It is a separate server from the wiki script's fixture; the wiki script only reads the JSON it prints.
- Compare three things apart: the answer (return, throw, callback arguments), the timing (callback before or after return) and the request lines. A changed default (asynchronous callbacks) otherwise hides the answer changes among timing changes.

On is-an-image-url: 1.0.4 today matched its recording in 82 of 82 calls and 11 of 11 CLI runs; 2.0.0 gave the same answer in 68, and each of the 14 differences and 5 request changes was a CHANGELOG line.

## Library with a command line

Add Commands (`Commands.md`): the usage text as the bin prints it, every flag, exit codes, stdout versus stderr, and real invocations with their real output (run the published bin; for a package that makes requests, against the local fixture server, then show the output with the fixture's address replaced by a real-looking one only when the replacement is stated on the page).

## Command-line tool (a dotnet tool, an npm package that is mostly a bin)

Untested: no run has used this set yet. The first candidate among the maintainer's packages is TrailerClipper.Tool (a dotnet tool, command `tclipper`, in m4bwav/TrailerClipperLib). A sketch: Home, Getting started (install and uninstall, shell completion if any), Commands (one section per command), Configuration (files, environment variables, precedence), Recipes, Versions and upgrading, FAQ, Development.

## Not yet covered

An application, a website, a monorepo with several packages, a command-line tool, and hosts other than GitHub have no tested page set (still lacking as of 0.3.0). [hosts.md](hosts.md) collects what the GitLab, Gitea, Forgejo and Azure DevOps docs say, unverified. For an application, start from Home, Getting started (run it), Configuration, Architecture, Deploying, FAQ, Development, and record what the run learned in LEARNINGS.md.

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
