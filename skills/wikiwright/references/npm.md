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

- A refused connection: listen on a free port, close it, and use that address.
- A proxy recipe: Node's environment proxy support (`NODE_USE_ENV_PROXY=1` or `--use-env-proxy`) tunnels even `http:` URLs with `CONNECT` (Node 24.18.0, 2026-09-28). A stand-in proxy answers `connect` with `HTTP/1.1 200 Connection Established` and hands the socket to the fixture server (`server.emit('connection', socket)`); target an `.invalid` host so the direct request can never leave the machine (L-112 `fetch-proxy-connect`).
- The CLI against the fixture: spawn it asynchronously (L-007), and print a transcript form (stdout, stderr, then the exit code on its own line) so a page's `$ cmd; echo $?` block is checkable.

## Tools that complement the script

anko/txm checks that a markdown file's code blocks produce the output written beside them, and lycheeverse/lychee checks external links in markdown. Neither installs the published version, so neither replaces the verification script; lychee is worth running over the pages when they link much outside GitHub.

## Other runtimes and package managers

- A machine without them can still run them (checked 2026-09-28, L-021 `runtimes-from-npm`). `npm install deno bun` in a scratch folder gives working binaries in `node_modules/.bin`. Corepack, which ships with Node 24, runs pnpm and yarn: `corepack pnpm@10 add PACKAGE@VERSION`, `corepack yarn@4 add PACKAGE@VERSION`. Set `COREPACK_ENABLE_DOWNLOAD_PROMPT=0`. On Windows spawn the `.cmd` shims with `shell: true`.
- Yarn 4 installs with Plug'n'Play and makes no `node_modules`, so `node script.mjs` fails with `ERR_MODULE_NOT_FOUND`: run `yarn node script.mjs`, and say so on Getting started.
- Deno: `import x from 'npm:PACKAGE@VERSION'`, run with the permissions the package needs (`--allow-net` for requests; a package without I/O ran with none). Run it once without the permission too: with no terminal Deno refuses, and a package that turns request failures into an answer (is-an-image-url) answers `false` with no error, which is worth a FAQ entry.
- Versions move (2026-09-28): `corepack pnpm` gave pnpm 12.6.0, and `corepack yarn` in a folder without a `packageManager` field gave Yarn 1.22.22, which prints a header and a `Done in 0.12s.` timing; run it with `--silent`. For Yarn 4 set `"packageManager": "yarn@4.18.1"`. Print every tool's version from the script.
- Show an install command without running it only when none of this works, and say which were run.
- TypeScript: compile a small file against the installed types (`npx -p typescript tsc --noEmit --module nodenext --moduleResolution nodenext file.ts`) when the page shows narrowing or type names.

Mark what was run on this machine and what is shown from the package's own docs or CI.

## Traps

- Git Bash on Windows: `npx` and npm scripts need a shell; spawn `npm` through a shell from Node, or run the bin with `process.execPath` as the template does.
- A package whose `exports` omits `./package.json` cannot be `require`d for its version; the template reads the file from `node_modules` directly.
- JSON loses `undefined`, `NaN` and error fields; the template's `inspect()` keeps them visible.
- A page that shows `console.log` output needs the script to print with `console.log` (or `util.inspect`, which is what it calls): the template's `example()` runs the page's code and records exactly what its `console.log` calls print (L-008, L-019).
- An error message built from a `Date` contains the local time zone; keep it out of the saved output (L-022). So does an import error's message (absolute paths): print its `code`.
- `tsc --types ''` is refused (`TS6044`); to compile without `@types/node`, point `--typeRoots` at an empty folder.
- The script runs in its own folder when it starts with `process.chdir(path.dirname(fileURLToPath(import.meta.url)))`, so no shell has to `cd` first.

Related: builds on [../SKILL.md](../SKILL.md); see also [page-sets.md](page-sets.md), [nuget.md](nuget.md).
