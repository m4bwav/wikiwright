# npm packages: survey and verification

## Registry facts for the survey

```sh
npm view PACKAGE --json                      # versions, time (publish date per version), dist-tags, engines, bin, exports
npm view PACKAGE@VERSION dist --json         # tarball size, unpackedSize, fileCount, integrity, attestations
npm pack PACKAGE@VERSION --dry-run --json    # the files inside the published tarball
curl -s https://api.npmjs.org/downloads/point/last-month/PACKAGE
curl -s https://api.npmjs.org/downloads/range/START:END/PACKAGE   # one entry per day; any START older than 18 months is moved up to 18 months ago without an error (checked 2026-09-28), so all-time totals are not available here
npm ls --all --prefix <scratch>              # the installed dependency tree, from the scratch project below
```

Write each number down with the date it was read. The tarball can hold files the repository does not (and the other way round): read `package.json` from the tarball, not from the clone.

## The scratch project

Outside the repository (the session scratchpad or a temp folder), so the working tree cannot leak in:

```sh
npm init -y
npm install PACKAGE@VERSION
```

Copy [../templates/npm/wiki-verify.template.mjs](../templates/npm/wiki-verify.template.mjs) in, fill in the cases, run `node wiki-verify.mjs`. The template:

- checks that the installed version is the one the wiki describes
- imports the package both ways (`import` and `createRequire`) and lists the exports of each, which is the API reference's export list
- runs the published bin with the current Node and records the exit code, stdout and stderr separately
- starts a local fixture server with one route per behaviour, for packages that make requests

Every example on a page is one `capture()` or `show()` in the script, labelled by page.

## Rules for requests

A package that fetches, calls back or opens sockets is verified against the local fixture server only, as its own tests do. The internet never produces an output shown on a page: sites change their titles, go down and rate-limit, and the next run of the script would disagree with the page. Where a page wants a familiar URL (`https://example.com/`), show the real call and state that the output shown came from a local fixture serving the same HTML; or keep the page's example on the fixture address.

## Tools that complement the script

anko/txm checks that a markdown file's code blocks produce the output written beside them, and lycheeverse/lychee checks external links in markdown. Neither installs the published version, so neither replaces the verification script; lychee is worth running over the pages when they link much outside GitHub.

## Other runtimes and package managers

- pnpm, yarn and Bun install commands are standard; show them without running when those tools are not installed, and say which were run.
- Deno: `import x from 'npm:PACKAGE'`, run with the permissions the package needs (`--allow-net`).
- TypeScript: compile a small file against the installed types (`npx -p typescript tsc --noEmit --module nodenext --moduleResolution nodenext file.ts`) when the page shows narrowing or type names.

Mark what was run on this machine and what is shown from the package's own docs or CI.

## Traps

- Git Bash on Windows: `npx` and npm scripts need a shell; spawn `npm` through a shell from Node, or run the bin with `process.execPath` as the template does.
- A package whose `exports` omits `./package.json` cannot be `require`d for its version; the template reads the file from `node_modules` directly.
- JSON loses `undefined`, `NaN` and error fields; the template's `inspect()` keeps them visible.

Related: builds on [../SKILL.md](../SKILL.md); see also [page-sets.md](page-sets.md), [nuget.md](nuget.md).
