# Page sets and page conventions

Which pages a wiki gets, what goes on each, and the rules every page follows. Read after the survey, before writing. The page sets come from eight published wikis, written on 2026-09-28 and 29:

- RandomNameGeneratorLibrary: a .NET library with seeded data.
- JsonPrettyPrinter: a .NET formatter.
- get-title-at-url: an npm library with a CLI.
- seeded-random-utilities: an npm library without a CLI, with seeded output and golden captures of two old versions.
- is-an-image-url: an npm library with a CLI that makes requests, with a golden capture of 1.0.4 that starts its own fixture server.
- markdown-plain-link-replacer (2026-09-29): an npm library with a CLI whose requests go through its dependencies to the hosts its input names, with a golden capture of 1.1.16 that records through its own proxy with TLS.
- stack-exchange-markdown-retriever (2026-09-29): an npm library with a CLI that calls one fixed HTTPS host, served by name through the host-fixture kit, with a golden capture of 1.1.7 recorded through a proxy with TLS; its post texts are sample content, labelled on every page.
- format-json-files (2026-09-29): an npm library with a CLI whose output is files on disk (it rewrites JSON files in place and makes no requests), every case on a fresh scratch tree through the file-tree kit, run on Windows and Linux, with a golden capture of 1.0.6 that builds its own trees.

| Kind | Tested on |
|---|---|
| Library (npm, without a CLI) | seeded-random-utilities |
| Library (NuGet) | RandomNameGeneratorLibrary, JsonPrettyPrinter |
| Library with a command line (npm) | get-title-at-url, is-an-image-url, markdown-plain-link-replacer, stack-exchange-markdown-retriever, format-json-files (fifth run, 2026-09-29: the set held again; the behaviour pages were `How-Links-Are-Replaced`, `How-Markdown-Is-Retrieved` and `How-Files-Are-Formatted`) |
| Deterministic or seeded output | seeded-random-utilities, RandomNameGeneratorLibrary |
| Output is files on disk | format-json-files (the CLI set, with the rules under "Library with a command line") |
| Command-line tool | not yet (the section below is a sketch; candidate: TrailerClipper.Tool, a dotnet tool) |
| Application, website, monorepo | not yet (see the end of this page) |
| Hosts other than GitHub | host mechanics measured 2026-09-29 without an account (Gitea, Forgejo, GitLab; Azure DevOps reads only); one real wiki, format-json-files on a local Forgejo 16.0.5, on 2026-09-29 ([hosts.md](hosts.md)) |

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

A capture that records through its own proxy with TLS (markdown-plain-link-replacer's `capture-1.1.16.cjs`, where request 2.88 honoured `HTTP_PROXY` and `HTTPS_PROXY`) replays unchanged against the old version (1.1.16 today: 154 of 154 calls, 18 of 18 CLI runs). Against a `fetch`-based new major it needs a proxy agent installed after the capture sets the variables and a fixture copy that serves tunnelled `http:` in plain HTTP; [npm.md](npm.md) ("Golden captures that record through a proxy with TLS") has the four changes. When a dependency's new major reads titles or names differently, mask that value and count the cases that differ only there apart: 55 of markdown-plain-link-replacer's 154 did, and the other 41 real differences were each a CHANGELOG line.

## Library with a command line

Add Commands (`Commands.md`): the usage text as the bin prints it, every flag, exit codes, stdout versus stderr, and real invocations with their real output (run the published bin; for a package that makes requests, against the local fixture server, then show the output with the fixture's address replaced by a real-looking one only when the replacement is stated on the page).

A package whose requests go through its dependencies to the hosts its input names, with output computed from the host (markdown-plain-link-replacer names each link's site), needs the fixture served under the real host names, through a `fetch` wrapper or a proxy with TLS ([npm.md](npm.md), "Packages that request by host name through their dependencies"). Its pages then show real addresses with no substitution, and say once, on Home, that each page was a local copy and list the titles the copies had where an output depends on them. Such a package turns every lookup failure into "left unchanged", so Edge cases and errors needs a section on why a link was left, and the FAQ on proxies and trust; both came from the run, not from the README.

A package whose output is files on disk (format-json-files) took the same set with no new page. What changed was how the pages show output, and what Edge cases and errors covers:

- A file is shown as a "before" block and an "after" block, both printed by the script, and the prose beside them states what the text cannot show: the line endings, the BOM, the final newline, and whether an untouched file was written at all.
- Command examples are terminal transcripts (`$ command`, the merged output, `$ echo $?`), from the template's `term()`, because the order of stdout and stderr is part of what a user sees.
- Paths print with the platform's separator: the pages show the Linux run and say once that Windows prints `\`.
- Edge cases and errors covers the file system as well as the input: encodings and BOMs, CRLF, comments and trailing commas, empty files, read-only files, symbolic and hard links, folders named like files, missing paths, and what a glob is (the shell's, not the package's).

## Command-line tool (a dotnet tool, an npm package that is mostly a bin)

Untested: no run has used this set yet. The first candidate among the maintainer's packages is TrailerClipper.Tool (a dotnet tool, command `tclipper`, in m4bwav/TrailerClipperLib). A sketch: Home, Getting started (install and uninstall, shell completion if any), Commands (one section per command), Configuration (files, environment variables, precedence), Recipes, Versions and upgrading, FAQ, Development.

## Not yet covered

An application, a website, a monorepo with several packages and a command-line tool have no tested page set (still lacking as of 0.6.0; the command-line candidate is TrailerClipper.Tool). On GitLab, Gitea, Forgejo and Azure DevOps the page set stays and the navigation files change; [hosts.md](hosts.md) has what was measured and what is unverified. For an application, start from Home, Getting started (run it), Configuration, Architecture, Deploying, FAQ, Development, and record what the run learned in LEARNINGS.md.

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

## How `wikiwright.py outputs` reads a page

It finds every block a page presents as output and every `//=>` value, and reports each one the verification run did not print. It maps the fixture's `http://127.0.0.1:<port>` to `https://example.com` (`--address` changes that; `--address ''` when the pages show real host names).

- **Output blocks.** A block counts as output when:
  - its fence is `text`, `console` or `output`;
  - the line before it ends with a colon and one of the six words before the colon is like "Output", "is", "gives", "prints" or "returns", or it is a short connective such as "becomes";
  - it follows its input block or its code block directly, untagged. A command right after a code block therefore needs its fence tag (```sh).
- **Values in code blocks.** `//=>` and `# =>` values, quoted or JSON-like values in comments, comments after a print call or on a PowerShell expression line, and comment lines that close a block (the NuGet wikis' forms, L-110 `outputs-in-comments`).
- **Transcripts.** Commands in a `$ ` transcript are skipped; what follows each one is checked.
- **Markers** on the line before a block: `<!-- outputs: skip (reason) -->` for output no script can print (npm's install lines with a timing); `<!-- outputs: check -->` to force a block to be read as output; `<!-- outputs: node>=22 -->` (also `<=`, `=`, `<`, `>`, and combined as `check node<22`) for a block true on some Node lines only. A scoped block is checked only against the outputs whose `Node vN` line (the template's `installed` section, or `--node N`) is in range, and skipped when none is (L-119 `diffout-first-use`).

## How `wikiwright.py snippets` reads a page

`outputs` proves where each output came from; `snippets` proves the code above it is the code that ran. Every block fenced `csharp`, `fsharp`, `js`, `ts`, `python`, `powershell` or `sh` must appear in one of the program files as a run of lines. Each line is compared stripped. Blank lines and whole-line comments are left out on both sides, so a snippet indented inside a lambda, `// "True"` on the page, and a lint comment in the program all pass. A trailing comment that shows a value is dropped too. The program is also read with template-literal escapes undone, and each one-line string literal that holds `\n` is read as a snippet of its own. A C# raw string or a PowerShell here-string needs nothing undone, so a page's F# script held in one is found as written. A shell block that only runs commands (`dotnet add package X`, `npm ci`) is counted as a command and not checked; one with a loop, a branch or an assignment is a script and is checked. `<!-- snippets: skip (reason) -->` on the line before a block skips it: use it for a type signature or a declaration that no program runs. When the pages hold code and nothing was checked, it fails, as `outputs` does (L-136 `zero-checked-passes`).

Keep each page's code in the program as the page shows it. The NuGet template runs the F# and PowerShell snippets from raw strings, and IsImageUrlDotNet's program held its C# snippets the same way: all 18 were found. The npm scripts so far load the package with `await import()` and wrap each case in a call of their own. Their pages fail `snippets` until the script holds each snippet as a string it writes to a file and runs, or the page shows the code that ran.

## Sidebar and footer

`_Sidebar.md` groups the pages under short plain-text labels (for example "Using it", "The releases", "Contributing", "Elsewhere") and links every page plus the README, CHANGELOG and registry page. `_Footer.md` is one line:

```
This wiki describes PACKAGE VERSION and was last updated on YYYY-MM-DD. The library is LICENCE licensed. Report problems in the [issues](https://github.com/OWNER/REPO/issues).
```

Starting points: [../templates/pages/](../templates/pages/).

Related: builds on [../SKILL.md](../SKILL.md); see also [publishing.md](publishing.md), [npm.md](npm.md), [nuget.md](nuget.md).
