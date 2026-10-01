# Page sets with a command line

Read this for a library with a command line, a command-line tool, or a package whose output is files on disk. The Library set and the conventions are in [page-sets.md](page-sets.md).

## Library with a command line

Add Commands (`Commands.md`): the usage text as the bin prints it, every flag, exit codes, stdout versus stderr, and real invocations with their real output (run the published bin; for a package that makes requests, against the local fixture server, then show the output with the fixture's address replaced by a real-looking one only when the replacement is stated on the page).

A package whose requests go through its dependencies to the hosts its input names, with output computed from the host (markdown-plain-link-replacer names each link's site), needs the fixture served under the real host names, through a `fetch` wrapper or a proxy with TLS ([npm-requests.md](npm-requests.md#packages-that-request-by-host-name-through-their-dependencies)). Its pages then show real addresses with no substitution, and say once, on Home, that each page was a local copy and list the titles the copies had where an output depends on them. Such a package turns every lookup failure into "left unchanged", so Edge cases and errors needs a section on why a link was left, and the FAQ on proxies and trust; both came from the run, not from the README.

A package whose output is files on disk (format-json-files) took the same set with no new page. What changed was how the pages show output, and what Edge cases and errors covers:

- A file is shown as a "before" block and an "after" block, both printed by the script, and the prose beside them states what the text cannot show: the line endings, the BOM, the final newline, and whether an untouched file was written at all.
- Command examples are terminal transcripts (`$ command`, the merged output, `$ echo $?`), from the template's `term()`, because the order of stdout and stderr is part of what a user sees.
- Paths print with the platform's separator: the pages show the Linux run and say once that Windows prints `\`. The exception is a package with a runtime or an old version that runs only on Windows (TrailerClipper's .NET Framework 4.8 build, and 1.x, which was Windows only): its pages showed the Windows run and said once that on Linux the separators are `/`.
- Edge cases and errors covers the file system as well as the input: encodings and BOMs, CRLF, comments and trailing commas, empty files, read-only files, symbolic and hard links, folders named like files, missing paths, and what a glob is (the shell's, not the package's).

## Command-line tool (a dotnet tool, an npm package that is mostly a bin)

Tested on TrailerClipper.Tool (2026-09-30): the dotnet tool `tclipper`, published beside the TrailerClipper library from one repository (m4bwav/TrailerClipperLib). The tool runs ffmpeg and writes media files, so its run also read [programs-and-media.md](programs-and-media.md). No npm package that is mostly a bin has used the set yet.

| Page (file) | What it holds |
|---|---|
| Home (`Home.md`) | What it does and is not, both packages with their versions, both install lines, the smallest example with its output and the folder afterwards, one line per page. |
| Getting started (`Getting-Started.md`) | What runs where; installing the library, the external program and the tool; the first call; uninstalling. |
| Commands (`Commands.md`) | The usage synopsis, an options table, one section per task with real transcripts, arguments it cannot use, which stream each message goes to, an exit-code table, and each side-effect command. |
| Configuration (`Configuration.md`) | Settings files (format, writing, the sample, reading), where the external program is looked for, which wins, how the tool differs, and a precedence table. |
| Recipes, Versions and upgrading, FAQ, Development | As in the Library set. |

A repository that ships a library and its tool takes the union with the Library set: API reference, the behaviour page (`How-Files-Are-Clipped.md`) and Errors and edge cases came from there, for eleven pages. The sketch this set replaced lacked these:

- **Install and uninstall.** Run the install into a tool path in scratch (`dotnet tool install TrailerClipper.Tool --version 2.0.0 --tool-path tools`), then `dotnet tool list --tool-path tools`, and uninstall from a second tool path. Never run `-g`: the page shows the global form and says it was not run. List the package's contents from the installed tool's store (`tools/net10.0/any/`, ten files: the tool carries its own copy of the library and FFMpegCore), since `registry` prints only a count for a tool's `tools/` folder. A tool with no `--version` says so on the page and points at `dotnet tool list`.
- **Shell completion** gets a section only when the tool has it; `tclipper` has none, and its pages do not mention it.
- **Configuration** covers how the tool finds an external program it runs: an option, an environment variable, PATH and known install folders, which one wins (shown by a case with two folders), and where the tool differs from the library (`tclipper` has no option for the folder, so the variable is the way). Say how each run found the program.
- **Side-effect commands** (an installer such as `--install-ffmpeg`, a delete) are verified only through the code's own seams, never for real: the paths that stop before acting (already installed, exit 0; standard input not a terminal and no `--yes`, exit 1; no package manager on PATH, exit 1). The commands it would run come from the source, and the page says so. The real install, its question and `--yes` are marked "not tested". Run every command with standard input closed, so none can ask, and make the program refuse a case that passes `--yes`.
- **Transcripts on .NET.** The NuGet template has no `term()`: the run wrote one that runs each command through `cmd /d /s /c "... 2>&1"` or `/bin/sh -c "... 2>&1"` on a fresh folder, then prints `$ echo $?` and the exit code, and a second runner with the streams apart to say which stream each line goes to.
- **Paths.** TrailerClipper's pages showed the Windows run, by the exception above, and the Linux run's differences (the exit code of a crash, the ffmpeg folder) beside it.

Related: builds on [page-sets.md](page-sets.md); see also [npm-requests.md](npm-requests.md), [npm-files.md](npm-files.md), [programs-and-media.md](programs-and-media.md).
