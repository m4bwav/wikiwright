# Page sets with a command line

Read this for a library with a command line, a command-line tool, or a package whose output is files on disk. The Library set and the conventions are in [page-sets.md](page-sets.md).

## Library with a command line

Add Commands (`Commands.md`): the usage text as the bin prints it, every flag, exit codes, stdout versus stderr, and real invocations with their real output (run the published bin; for a package that makes requests, against the local fixture server, then show the output with the fixture's address replaced by a real-looking one only when the replacement is stated on the page).

A package whose requests go through its dependencies to the hosts its input names, with output computed from the host (markdown-plain-link-replacer names each link's site), needs the fixture served under the real host names, through a `fetch` wrapper or a proxy with TLS ([npm-requests.md](npm-requests.md#packages-that-request-by-host-name-through-their-dependencies)). Its pages then show real addresses with no substitution, and say once, on Home, that each page was a local copy and list the titles the copies had where an output depends on them. Such a package turns every lookup failure into "left unchanged", so Edge cases and errors needs a section on why a link was left, and the FAQ on proxies and trust; both came from the run, not from the README.

A package whose output is files on disk (format-json-files) took the same set with no new page. What changed was how the pages show output, and what Edge cases and errors covers:

- A file is shown as a "before" block and an "after" block, both printed by the script, and the prose beside them states what the text cannot show: the line endings, the BOM, the final newline, and whether an untouched file was written at all.
- Command examples are terminal transcripts (`$ command`, the merged output, `$ echo $?`), from the template's `term()`, because the order of stdout and stderr is part of what a user sees.
- Paths print with the platform's separator: the pages show the Linux run and say once that Windows prints `\`.
- Edge cases and errors covers the file system as well as the input: encodings and BOMs, CRLF, comments and trailing commas, empty files, read-only files, symbolic and hard links, folders named like files, missing paths, and what a glob is (the shell's, not the package's).

## Command-line tool (a dotnet tool, an npm package that is mostly a bin)

Untested: no run has used this set yet. The first candidate among the maintainer's packages is TrailerClipper.Tool (a dotnet tool, command `tclipper`, in m4bwav/TrailerClipperLib). A sketch: Home, Getting started (install and uninstall, shell completion if any), Commands (one section per command), Configuration (files, environment variables, precedence), Recipes, Versions and upgrading, FAQ, Development.

Related: builds on [page-sets.md](page-sets.md); see also [npm-requests.md](npm-requests.md), [npm-files.md](npm-files.md).
