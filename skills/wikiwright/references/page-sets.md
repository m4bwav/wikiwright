# Page sets and page conventions

Which pages a wiki gets, what goes on each, and the rules every page follows. Read after the survey, before writing. The page sets come from twelve wikis, written from 2026-09-28 to 30:

- RandomNameGeneratorLibrary: a .NET library with seeded data.
- JsonPrettyPrinter: a .NET formatter.
- get-title-at-url: an npm library with a CLI.
- seeded-random-utilities: an npm library without a CLI, with seeded output and golden captures of two old versions.
- is-an-image-url: an npm library with a CLI that makes requests, with a golden capture of 1.0.4 that starts its own fixture server.
- markdown-plain-link-replacer (2026-09-29): an npm library with a CLI whose requests go through its dependencies to the hosts its input names, with a golden capture of 1.1.16 that records through its own proxy with TLS.
- stack-exchange-markdown-retriever (2026-09-29): an npm library with a CLI that calls one fixed HTTPS host, served by name through the host-fixture kit, with a golden capture of 1.1.7 recorded through a proxy with TLS; its post texts are sample content, labelled on every page.
- format-json-files (2026-09-29): an npm library with a CLI whose output is files on disk (it rewrites JSON files in place and makes no requests), every case on a fresh scratch tree through the file-tree kit, run on Windows and Linux, with a golden capture of 1.0.6 that builds its own trees.
- IsImageUrlDotNet (2026-09-29): an F# NuGet library called from C# and F#, whose online check makes requests (through a stand-in proxy answering `.test` names, labelled on the pages), run on net10.0, .NET Framework 4.8 and net8.0 on Windows and net10.0 on Linux, with golden recordings of 1.0.2 per runtime and OS from a capture project.
- replace-string-at-position (2026-09-30): the second npm library without a CLI, with no requests and a synchronous golden capture of 1.0.4; the first npm wiki gated by `snippets`. The run committed the wiki and left the push to the maintainer.
- TrailerClipperLib (2026-09-30): a NuGet library and the dotnet tool `tclipper` from one repository, both running ffmpeg and writing media files; the first wiki with a command-line tool, run on net10.0, .NET 8 and .NET Framework 4.8 on Windows and net10.0 on Linux, with a golden recording of 1.1.0.
- CachingServiceWithAOPSupport (2026-09-30): a NuGet library for Autofac and Castle whose output depends on time (cached results expire) and on a store shared by the whole process, run at both ends of its Autofac range, with golden recordings of 1.0.1 per runtime.

| Kind | Tested on |
|---|---|
| Library (npm, without a CLI) | seeded-random-utilities; replace-string-at-position (2026-09-30: nine pages, the behaviour page `How-Text-Is-Replaced`) |
| Library (NuGet) | RandomNameGeneratorLibrary, JsonPrettyPrinter (written by hand, then retrofitted); IsImageUrlDotNet (2026-09-29, the first written by the skill from Step 1, and the first .NET package that makes requests: the same set, the behaviour page `How-Urls-Are-Checked`); CachingServiceWithAOPSupport (2026-09-30: nine pages, the behaviour page `How-Results-Are-Cached`, with [time-and-state.md](time-and-state.md)) |
| Library with a command line (npm) | get-title-at-url, is-an-image-url, markdown-plain-link-replacer, stack-exchange-markdown-retriever, format-json-files (fifth run, 2026-09-29: the set held again; the behaviour pages were `How-Links-Are-Replaced`, `How-Markdown-Is-Retrieved` and `How-Files-Are-Formatted`) |
| Deterministic or seeded output | seeded-random-utilities, RandomNameGeneratorLibrary ([page-sets-seeded.md](page-sets-seeded.md)) |
| Output is files on disk | format-json-files (the CLI set, with the rules in [page-sets-cli.md](page-sets-cli.md)); TrailerClipper (media files, [programs-and-media.md](programs-and-media.md)) |
| Command-line tool | TrailerClipper.Tool (2026-09-30: the set in [page-sets-cli.md](page-sets-cli.md), in union with its library's, eleven pages) |
| Application, website, monorepo | not yet (see the end of this page) |
| Hosts other than GitHub | host mechanics measured 2026-09-29 without an account (Gitea, Forgejo, GitLab; Azure DevOps reads only); one real wiki, format-json-files on a local Forgejo 16.0.5, on 2026-09-29 ([hosts.md](hosts.md)) |

Beside this page, read only what the package needs:

- [page-sets-cli.md](page-sets-cli.md): a command line, a command-line tool, or files on disk
- [page-sets-seeded.md](page-sets-seeded.md): seeded or deterministic output
- [golden-captures.md](golden-captures.md): golden captures of old versions (npm and NuGet)
- [programs-and-media.md](programs-and-media.md): the package runs an external program, or its output is media or other binary files
- [time-and-state.md](time-and-state.md): output depends on time, or on state that outlives a call (a cache, a static, a container)

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
| Versions and upgrading (`Versions-and-Upgrading.md`) | Every release with its date (from the registry), what changed for callers, and a section per old major on moving to the current one, from the CHANGELOG and a golden capture of the old version, or the old major run against the same fixture when there is none (see [golden-captures.md](golden-captures.md)). Whether each old version still installs, whether it is deprecated, and its recent downloads. The same calls on the old and the new version side by side, with their real output. |
| FAQ (`FAQ.md`) | The questions the issues, pull requests, README and survey raise, answered in two to five sentences each, linking the page with the detail. |
| Development (`Development.md`) | Clone, build, test, lint commands, the CI matrix, how a release is made, where the maintainer's notes are (AGENTS.md, ai-docs). |
| Optional: Performance (`Performance-and-Threading.md`) | Only with a benchmark or a thread-safety question to answer: the numbers with the machine and date, what is safe to share. |
| Optional: data sources (`Name-Lists-and-Data-Sources.md`) | Only when the package embeds data: where it comes from, counts, licence, known quirks. |

An npm library without a command line takes exactly the table above: seeded-random-utilities had nine pages, with no Commands page. Its Getting started page ran every install route it names (npm, pnpm, yarn 4, Bun, Deno; see [npm.md](npm.md#other-runtimes-and-package-managers)), both module systems and a TypeScript compile that shows a real type error. replace-string-at-position (2026-09-30) took the same nine pages, with the behaviour page `How-Text-Is-Replaced`. It was the first npm wiki gated by `snippets`: 34 blocks, each held in the program as text. On a copy of the pages with four code blocks and one `//=>` value changed, `snippets` caught 4 of the 4 code changes, and `outputs` caught none of them, only the changed value.

A known limit of the gates: neither checks prose, a table hand-copied from the output (a Versions table of old answers, a table of error messages), or which output belongs to which code block. `outputs` finds each output somewhere in the run, and `snippets` accepts a page block that is part of a longer snippet. The replace-string-at-position run wrote two wrong prose claims that only Step 6's reread caught. Reread the tables against the output line by line.

## Not yet covered

An application, a website and a monorepo with several packages have no tested page set (still lacking on 2026-09-30, after the twelfth wiki). One repository with a library and its tool is covered: the [command-line tool set](page-sets-cli.md#command-line-tool-a-dotnet-tool-an-npm-package-that-is-mostly-a-bin) and the two-package rule in the [conventions](#conventions-every-page-follows). On GitLab, Gitea, Forgejo and Azure DevOps the page set stays and the navigation files change; [hosts.md](hosts.md) has what was measured and what is unverified. For an application, start from Home, Getting started (run it), Configuration, Architecture, Deploying, FAQ, Development, and record what the run learned in LEARNINGS.md.

## Conventions every page follows

- File names: words joined by hyphens, a capital on each word (`Getting-Started.md`), because GitHub shows the file name with spaces as the page title. Page URLs are case-insensitive, but links should match the file name exactly. A title cannot contain these characters: backslash, `/ : * ? " < > |` (GitHub Docs, "Adding or editing wiki pages").
- Headings in sentence case. The host prints the file name as the page title, so a page starts with its first paragraph, never a `#` heading that repeats the title: `Getting-Started.md` opening with `# Getting started` shows the title twice, one line under the other. Never put a heading straight under one with the same words either. `check` fails both (L-139 `title-printed-once`). Home is titled "Home", so a `#` heading naming the package there is not a repeat.
- Links between pages are plain markdown with the page name: `[Recipes](Recipes)`, `[the errors](API-Reference#errors)`. No wikilinks (`[[Page]]`), no `.md` suffix, no site-absolute paths.
- Examples show their real output, produced by the verification script against the published package. Input and output go in paired code blocks ("`pretty` is:" and then the block): a markdown table cannot hold multi-line output.
- Anything not run says so: "not tested" beside the platform or runtime, never an implied yes (JsonPrettyPrinter's Unity row).
- Versions: the API reference names the version that introduced each member later than the page's baseline; the footer names the current version and the date the wiki was last updated.
- Numbers from the registry (downloads, sizes, dates) carry the date they were read.
- Two packages from one repository (a library and its tool): the footer names both packages and their versions ("This wiki describes TrailerClipper and TrailerClipper.Tool 2.0.0 ... Both packages are MIT licensed."), the sidebar links both registry pages, and `WW registry` runs once per package. `check --version` takes one version, which served here since both were 2.0.0.
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
- **Markers** on the line before a block: `<!-- outputs: skip (reason) -->` for output no script can print (npm's install lines with a timing); `<!-- outputs: check -->` to force a block to be read as output; `<!-- outputs: node>=22 -->` (also `<=`, `=`, `<`, `>`, and combined as `check node<22`) for a block true on some Node lines only. A scoped block is checked only against the outputs whose `Node vN` line (the template's `installed` section, or `--node N`) is in range, and skipped when none is (L-119 `diffout-first-use`). A usage synopsis fenced `text` reads as output: mark it `<!-- outputs: skip (usage synopsis) -->`, as TrailerClipper's Commands page did.

## How `wikiwright.py snippets` reads a page

`outputs` proves where each output came from; `snippets` proves the code above it is the code that ran. Every block fenced `csharp`, `fsharp`, `js`, `ts`, `python`, `powershell` or `sh` must appear in one of the program files as a run of lines. Each line is compared stripped. Blank lines and whole-line comments are left out on both sides, so a snippet indented inside a lambda, `// "True"` on the page, and a lint comment in the program all pass. A trailing comment that shows a value is dropped too. The program is also read with template-literal escapes undone, and each one-line string literal that holds `\n` is read as a snippet of its own. A C# raw string or a PowerShell here-string needs nothing undone, so a page's F# script held in one is found as written. A shell block that only runs commands (`dotnet add package X`, `npm ci`) is counted as a command and not checked; one with a loop, a branch or an assignment is a script and is checked. `<!-- snippets: skip (reason) -->` on the line before a block skips it: use it for a type signature or a declaration that no program runs. When the pages hold code and nothing was checked, it fails, as `outputs` does (L-136 `zero-checked-passes`).

Keep each page's code in the program as the page shows it. The NuGet template runs the F# and PowerShell snippets from raw strings, and IsImageUrlDotNet's program held its C# snippets the same way: all 18 were found. The npm template's `snippet()` does the same from a template literal ([npm.md](npm.md), "The scratch project"). npm scripts saved before 0.7.1 load the package with `await import()` and wrap each case in a call of their own, so their pages fail `snippets` until the cases move into `snippet()`.

## Sidebar and footer

`_Sidebar.md` groups the pages under short plain-text labels (for example "Using it", "The releases", "Contributing", "Elsewhere") and links every page plus the README, CHANGELOG and registry page. A library with a command line adds `- [Commands](Commands)` after the behaviour page; `check` fails a page the sidebar leaves out. `_Footer.md` is one line:

```
This wiki describes PACKAGE VERSION and was last updated on YYYY-MM-DD. The library is LICENCE licensed. Report problems in the [issues](https://github.com/OWNER/REPO/issues). On REGISTRY: [PACKAGE](REGISTRY_URL).
```

The last sentence links the package's registry page, so it is on every page and not only in the sidebar; a repository that publishes several packages, or to several registries, names each ("On NuGet: [TrailerClipper](https://www.nuget.org/packages/TrailerClipper) and [TrailerClipper.Tool](https://www.nuget.org/packages/TrailerClipper.Tool)."). A plugin or skill that a catalog lists (the Claude directory, awesome-copilot, the Cursor Marketplace) adds one more sentence once the listing is live: "Listed in the [Claude directory](https://claude.ai/directory) as Everwrite." (the Claude directory has no public page per plugin, checked 2026-10-09). Update mode adds both to a footer that lacks them (user request, 2026-10-09).

Starting points: [../templates/pages/](../templates/pages/).

Related: builds on [../SKILL.md](../SKILL.md); see also [page-sets-cli.md](page-sets-cli.md), [page-sets-seeded.md](page-sets-seeded.md), [golden-captures.md](golden-captures.md), [programs-and-media.md](programs-and-media.md), [time-and-state.md](time-and-state.md), [publishing.md](publishing.md), [npm.md](npm.md), [nuget.md](nuget.md).
