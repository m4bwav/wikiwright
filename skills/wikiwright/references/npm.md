# npm packages: survey and verification

## Registry facts for the survey

Start with the helper. It reads the packument and last week's downloads and prints one fact per line:

```sh
python scripts/wikiwright.py registry PACKAGE --npm   # add --version X for an older version, --json for everything
```

It prints the versions with their dates (same-day releases share a line), dist-tags, and deprecations. For the latest version it prints `engines`, type, main, types, exports and bin, the dependencies, unpacked size and file count, provenance and `gitHead`. It also prints last week's downloads and the time read. On 2026-09-29 it printed about 1.1 KB where the packument came to 76.6 KB (get-title-at-url) and 35.9 KB (format-json-files).

For what it leaves out, and without it:

```sh
npm view PACKAGE --json                      # the full manifest: versions, time, dist-tags, engines, bin, exports
npm pack PACKAGE@VERSION --dry-run --json    # the files inside the published tarball
curl -s https://api.npmjs.org/downloads/range/START:END/PACKAGE   # one entry per day; any START older than 18 months is moved up to 18 months ago without an error (checked 2026-09-28), so all-time totals are not available here
npm ls --all --prefix <scratch>              # the installed dependency tree, from the scratch project below
```

Write each number down with the date it was read. The tarball can hold files the repository does not (and the other way round): read `package.json` from the tarball, not from the clone.

## The scratch project

Outside the repository (the session scratchpad or a temp folder), so the working tree cannot leak in:

```sh
python <skill>/scripts/wikiwright.py scaffold npm PACKAGE VERSION -o <scratch>/wiki-verify.mjs
npm install --prefix <scratch> PACKAGE@VERSION typescript
```

Write `<scratch>/package.json` with the editor first (`{"private": true}` is enough). `npm init -y --prefix <dir>` still writes `package.json` into the current folder, not `<dir>`: a stray `package.json` made Yarn 4 refuse to install in the sixth run, and one landed in the skill's own source folder the same day (L-017). `npm install --prefix` does install into `<dir>`.

`scaffold` writes [../templates/npm/wiki-verify.template.mjs](../templates/npm/wiki-verify.template.mjs) with the package and version filled in and only the sections the package needs, then prints the bytes, the sections kept and what to fill next. Add the cases and run `node wiki-verify.mjs`. The core, always kept:

- checks that the installed version is the one the wiki describes
- imports the package both ways (`import` and `createRequire`) and lists the exports of each, which is the API reference's export list
- `snippet()` and `runSnippet()`, the cases section and the `OLDEST_NODE` rerun

Each flag keeps one section, cut from the template at its `// ===== section: NAME =====` and `// ===== end: NAME =====` lines (they nest, and the template runs unchanged with all of them):

| Flag | Section | For a package that |
|---|---|---|
| `--bin` | `cli()`, `term()` and the `--help` case: runs the published bin with the current Node and records the exit code, stdout and stderr separately | has a bin (the `bin` field of `wikiwright.py registry`). Without the flag, the script stops at start when the installed package has one. |
| `--requests` | the local fixture server, one route per behaviour | makes requests |
| `--by-host` | the host-name kit, switched on (implies `--requests`); copies `host-fixture.mjs` beside the script | requests the hosts its input names |
| `--files` | `inTree()`; copies `file-tree.mjs` beside the script | writes, moves or deletes files |
| `--golden OLD_VERSION` | the golden replay of `capture-OLD_VERSION.cjs` | has golden captures in its repository |

It refuses to overwrite the script or a kit without `--force`. For replace-string-at-position 2.0.0 (no bin, no requests, no files) the script came to 11,197 bytes where the template is 21,140, and the run skipped the copy, two placeholder edits and five section deletions (2026-09-30, C-20260930-7).

Every code block on a page is one `snippet()` in the script, labelled by page. It holds the block as the page shows it, in a template literal, writes it to `snippets/<label>.mjs` (`.cjs`, or `.mts` compiled by the scratch project's `tsc`), runs that file with the script's Node and prints what it printed. So `wikiwright.py snippets` finds every block, and an `OLDEST_NODE` rerun runs the snippets on the old Node too. In the literal, write a backslash as `\\`, a backtick as `` \` `` and `${` as `\${`; `String.raw` would keep the backslash before the last two. The written file swaps the pages' `https://example.com` for the fixture address, and takes `env`, `args` (such as `--import` for a fetch router), `cwd` (a file-tree root) and code to run before or after the page's. A `//=>` line prints the statement above it. For get-title-at-url 3.0.0, five blocks from Getting started and Recipes went into snippets: `snippets` found 5 of 5 and `outputs` 5 of 5, where the earlier script, which ran its cases as its own code, matched none of the five. Checks no page shows (error fields, membership, the golden replay) stay `capture()` or `show()`.

## Rules for requests

A package that fetches, calls back or opens sockets is verified against the local fixture server only, as its own tests do. The internet never produces an output shown on a page: sites change their titles, go down and rate-limit, and the next run of the script would disagree with the page. Where a page wants a familiar URL (`https://example.com/`), show the real call and state that the output shown came from a local fixture serving the same HTML; or keep the page's example on the fixture address.

- A refused connection: listen on a free port, close it, and use that address.
- A proxy recipe: Node's environment proxy support (`NODE_USE_ENV_PROXY=1` or `--use-env-proxy`) tunnels even `http:` URLs with `CONNECT` (Node 24.18.0, 2026-09-28). A stand-in proxy answers `connect` with `HTTP/1.1 200 Connection Established` and hands the socket to the fixture server (`server.emit('connection', socket)`); target an `.invalid` host so the direct request can never leave the machine (L-112 `fetch-proxy-connect`). The stand-in refuses every target but the fixture, so a recipe bug cannot send a request out through it. undici 8's `ProxyAgent` sends an absolute-form `GET http://...` for an `http:` target where undici 7 sends `CONNECT`: handle both (L-131).
- The CLI against the fixture: spawn it asynchronously (L-007), with standard input closed (a CLI that reads stdin when it gets no argument waits for ever on an open pipe). `cli()` records stdout and stderr apart; a page's terminal block comes from the template's `term()`, which prints `$ command`, both streams merged in the order they were written, then `$ echo $?` and the code. Two separate streams lose that order: `--check` printed its list before the skip lines, the reverse of a terminal (the sixth run).

## Packages that request by host name through their dependencies

When the package's requests go through its dependencies to the hosts its input names, and its output is computed from the host (a site name, a domain, a check of the top-level domain), the fixture address cannot stand in for the real one: the page would show `127.0.0.1` where the reader gets `example.com`. Two routes worked (markdown-plain-link-replacer 2.0.0, 2026-09-29):

- **A `fetch` wrapper** that sends every request to the fixture with the meant URL in a header (`x-fixture-url`), loaded in-process or with `node --import` (L-115 `route-fetch-preload`). Light, Node only, and only for a package that calls the global `fetch` at call time. The repository's own test helpers often have one; read them first.
- **A proxy by host name with TLS** (L-116 `by-host-name-proxy`; [../templates/npm/host-fixture.mjs](../templates/npm/host-fixture.mjs), which the template imports: read its header, not its body). Pages are served from a plain server and a TLS server keyed by host and path, behind a stand-in proxy on 127.0.0.1 that answers `CONNECT` and hands the socket to the TLS server for port 443 and to the plain server for any other port. This route also covers Deno, Bun, the package managers and old versions in child processes, and it uses the transport the package really uses. What each runtime needed, measured on 2026-09-29:
  - Node 24.18.0: `NODE_USE_ENV_PROXY=1` with `HTTP_PROXY` and `HTTPS_PROXY`, all read at startup (set them in the child's environment; setting `process.env` later does nothing). Node tunnels `http:` links with `CONNECT host:80` too (L-112).
  - Node 20.20.2: no `NODE_USE_ENV_PROXY`; preload undici's `EnvHttpProxyAgent` (`npm install undici@7`, a two-line `--require` file calling `setGlobalDispatcher(new EnvHttpProxyAgent())`). The script's own process can use undici's `ProxyAgent` with `requestTls: {ca}`.
  - Trust: a throwaway CA and a server certificate it signed (openssl), the CA given as `NODE_EXTRA_CA_CERTS` (Node, Bun; read at startup) and `DENO_CERT` (Deno). Deno 2.9.6 refused one self-signed certificate marked as a CA as the server's own. Without trust, https links fail silently while http links work.
  - Deno 2.9.6 and Bun 1.4.2 read `HTTP_PROXY` and `HTTPS_PROXY` themselves. Deno resolves `npm:` from the `node_modules` of the nearest folder with a `package.json`, so run it where the package is installed, or in a folder with no `package.json` above it (L-021).
  - `NODE_OPTIONS` reads a backslash as an escape: give preload paths with forward slashes.
  - Decide a Node's route with a probe to an `.invalid` host (never a real one), and print one case with the requests the fixture saw, so a silent routing failure cannot pass for the package's behaviour.
- **Guard** every child with a preload that refuses any socket not to 127.0.0.1, reading the options from `Array.isArray(args[0]) ? args[0][0] : args[0]`: `net.connect()` passes its arguments as one array, so a guard reading `args[0].host` stops https but lets plain http reach the internet (L-117 `guard-normalised-args`; it did in the first Node 20 run).

## Packages that write files

A package whose output is files on disk (a formatter, a generator, a renamer) is verified on scratch copies only: never the repository, the user's files or the script's own folder (L-130 `file-writing-package`). Tested on format-json-files 2.0.0 (2026-09-29): 114 page outputs from fresh trees on Windows and Linux, Node 24 and 20, and a golden replay of 1.0.6 (L-133 `file-tree-first-run`).

- **One fresh tree per case.** [../templates/npm/file-tree.mjs](../templates/npm/file-tree.mjs) (`treeCase`, which the template's `inTree()` calls) builds each case's tree in its own folder under `./trees`, runs the case and removes the tree, so no case sees another's rewrite. Read its header, not its body. The repository's test helpers and golden fixtures (`test/helpers/tree.js`, `test/golden/capture-fixtures.cjs`) already name the trees worth showing: reuse their contents instead of inventing new ones.
- **What it prints.** The case's own output (the CLI's transcript, the library's return value), then one line per file: `not written`, `written, same bytes`, `changed`, `created` or `deleted`. Each written file's before and after contents follow, under a header naming what the text cannot show: size, UTF-8 or not, BOM, line endings and final newline. The contents print with CR and the BOM removed, so a page's code block matches them. The page states the header's facts in prose ("the file is written with LF and no final newline").
- **Modification times.** The kit sets a fixed time on every file before the case, so a package that rewrites a file with the same bytes shows `written, same bytes`; one that promises not to touch formatted files is checked by the same line.
- **The paths people pass.** Cover what the source supports: a file, a folder, nested folders, several paths, a glob (the shell expands it, so run it through `shell()` with `{cwd: root}`), a file with another extension, a BOM, CRLF, comments, trailing commas, an empty file, bytes that are not UTF-8, a read-only file, a symbolic link, a missing path. Pass relative paths with the tree as the working directory (`cli('data', {cwd: root})`, or `{chdir: true}` for the library), so the page shows what a user types; the kit prints the tree's absolute path as `<tree>`.
- **Paths follow the platform.** A package that builds paths with `path.join` prints `data\a.json` on Windows and `data/a.json` on Linux and macOS, where most readers are. Run the script on Linux too and show that run on the pages; say the Windows difference in one sentence, from the Windows run, and never swap separators by hand (L-132 `linux-run-for-paths`: three eval runs needed it). On Windows with WSL and no Linux Node, take Node from the registry: `npm pack node-linux-x64@24.18.0 node-linux-x64@20.20.2 npm@11.16.0` into scratch, unpack each (`package/bin/node`), and run with `PATH=<its bin>:<npm shims>:/usr/bin:/bin` so WSL interop's Windows `node` and `npm` are never picked up (nodejs.org's tarballs with `SHASUMS256.txt` also worked, but a registry-only run needs the packages). There is no npx in that PATH, so set `OLDEST_NODE_BIN=<the Node 20 binary>` beside `OLDEST_NODE=20`; the template then writes `wiki-verify.linux.node20.out.txt`. The sixth run's `ai-docs/notes/2026-09-29-linux-run.sh` in format-json-files is a working example. Put the WSL commands in a script file: an inline `bash -c "..."` lost its quoting, Git Bash rewrote `/mnt/c/...` arguments (set `MSYS_NO_PATHCONV=1`), and PowerShell dropped `$PWD` (`wsl --cd <dir> -- env "PATH=..." sh -c "..."` worked).
- **Platforms.** Windows without developer mode refuses file symbolic links (`EPERM`); the kit lists them as unavailable. Run those cases in the Linux run or mark them "not tested on Windows". A read-only file is still writable for root on Linux and macOS. Trees under `/mnt/c` in WSL (drvfs) keep links and read-only files but ignore folder modes, so an unreadable-folder case needs a Linux folder or "not tested".
- **Golden captures that write files.** Of the four changes below, a file-writing capture needs the first two (the bin's path, a dependency lookup that answers `none`), which package-modernize's template already makes. It also needs `TEMP`, `TMP` and `TMPDIR` pointed into scratch, since it builds its trees in `os.tmpdir()`, and views for files rather than requests: what threw, what returned or printed, each file's bytes, which files were written, links, and the CLI's exit code, stdout and stderr lines. Count platform differences apart from package differences: on Linux 1.0.6 wrote through a file link that Windows could not make, and `EACCES` stands where Windows says `EPERM` (format-json-files 1.0.6: 45 of 45 files on Windows today, 44 on Linux).

## Golden captures that record through a proxy with TLS

A capture that routes an old version's requests through its own recording proxy (request 2.88 honours `HTTP_PROXY` and `HTTPS_PROXY`) replays against the old version unchanged. Against a new major that uses `fetch`, the copies needed four changes, none to the cases (markdown-plain-link-replacer 1.1.16 against 2.0.0, 2026-09-29; L-113 `replay-requesting-capture`):

1. the bin's path read from package.json (`cli.js` became `dist/cli.mjs`);
2. a dependency lookup that answers `none` for packages the new major dropped;
3. undici's `EnvHttpProxyAgent` installed right after the capture sets the proxy variables, in the capture and, through `NODE_OPTIONS=--require <file>`, in its CLI children: `NODE_USE_ENV_PROXY=1` alone fails, because the capture sets the variables only once its server listens;
4. a fixture-server copy whose `connect` handler serves ports other than 443 in plain HTTP, because `fetch` tunnels `http:` links too.

`NODE_TLS_REJECT_UNAUTHORIZED=0`, set by the capture at run time, is read per connection and covered the certificate. Compare the answer, the callback timing and the request lists apart, the request lists without the `CONNECT` lines and without how each request arrived; mask link titles when a dependency's new major reads titles differently, and count title-only differences separately. package-modernize's capture template now removes all four: it reads the bin and the dependencies (its C-20260929-1), and `capture-proxy.cjs` sets the proxy variables before the package loads and routes CONNECT by port (its C-20260929-3, L-125). stack-exchange-markdown-retriever's 1.1.7 capture (2026-09-29), which predates both, needed changes 1 to 3; 2.0.0 only tunnels to port 443.

## The oldest Node in engines

Run the whole script again on the oldest Node line in `engines` (L-106 `oldest-node-run`). The template's `OLDEST_NODE=<major>` does it: it asks npx for that Node (`npx -y -p node@<major> node -p process.execPath`), copies the binary alone into `node<major>-alone-<platform>/`, reruns the script with that folder first on PATH (so shells and bins the cases spawn use it too), and saves `wiki-verify.node<major>.out.txt` (`wiki-verify.linux.node<major>.out.txt` off Windows). `OLDEST_NODE_BIN=<binary>` skips npx. The npm `node` package's own bin folder will not do: it also holds a text file named `node`, and Git Bash skips the folder and runs the system Node without a word (L-118 `oldest-node-path-trap`). The template's `shell()` prints `shell node: vN` first in every shell case, so the output shows which Node each one ran. Compare with `wikiwright.py diffout <main output> wiki-verify.node<major>.out.txt`; it counts the `shell node:` lines per output instead of listing each, and warns when one output ran shell cases on two Nodes (the L-118 failure). Every changed section is a page claim to scope by version, or a case to fix. It exits 1 when anything differs, which ends a `&&` chain: that means differences, not an error. Save the second output beside the first in the repository.

## Tools that complement the script

anko/txm checks that a markdown file's code blocks produce the output written beside them, and lycheeverse/lychee checks external links in markdown. Neither installs the published version, so neither replaces the verification script; lychee is worth running over the pages when they link much outside GitHub.

## Other runtimes and package managers

- A machine without them can still run them (checked 2026-09-28, L-021 `runtimes-from-npm`). `npm install deno bun` in a scratch folder gives working binaries in `node_modules/.bin`. Corepack, which ships with Node 24, runs pnpm and yarn: `corepack pnpm@10 add PACKAGE@VERSION`, `corepack yarn@4 add PACKAGE@VERSION`. Set `COREPACK_ENABLE_DOWNLOAD_PROMPT=0`. On Windows spawn the `.cmd` shims with `shell: true`.
- Yarn 4 installs with Plug'n'Play and makes no `node_modules`, so `node script.mjs` fails with `ERR_MODULE_NOT_FOUND`: run `yarn node script.mjs`, and say so on Getting started.
- Deno: `import x from 'npm:PACKAGE@VERSION'`, run with the permissions the package needs (`--allow-net` for requests; a package without I/O ran with none). Run it once without the permission too: with no terminal Deno refuses, and a package that turns request failures into an answer (is-an-image-url) answers `false` with no error, which is worth a FAQ entry. Deno 2.9.6 resolves `npm:` imports from the `node_modules` of the nearest folder with a `package.json`: in a folder whose `node_modules` lacks the package (the `RT` folder of `npm install deno bun`) it refuses them until `deno install`, and in the scratch project where the package is installed it works. Run the Deno case in one of those, or in a folder with no `package.json` above it (2026-09-29, L-021).
- Versions move (2026-09-28): `corepack pnpm` gave pnpm 12.6.0, and `corepack yarn` in a folder without a `packageManager` field gave Yarn 1.22.22, which prints a header and a `Done in 0.12s.` timing; run it with `--silent`. For Yarn 4 set `"packageManager": "yarn@4.18.1"`. Print every tool's version from the script.
- Show an install command without running it only when none of this works, and say which were run.
- TypeScript: compile a small file against the installed types (`npx -p typescript tsc --noEmit --module nodenext --moduleResolution nodenext file.ts`) when the page shows narrowing or type names.

Mark what was run on this machine and what is shown from the package's own docs or CI.

## Traps

- Git Bash on Windows: `npx` and npm scripts need a shell; spawn `npm` through a shell from Node, or run the bin with `process.execPath` as the template does.
- A package whose `exports` omits `./package.json` cannot be `require`d for its version; the template reads the file from `node_modules` directly.
- JSON loses `undefined`, `NaN` and error fields; the template's `inspect()` keeps them visible.
- A page that shows `console.log` output needs the script to print with `console.log` (or `util.inspect`, which is what it calls): the template's `snippet()` runs the page's code and records exactly what its `console.log` calls print (L-008, L-019).
- An error message built from a `Date` contains the local time zone; keep it out of the saved output (L-022). So does an import error's message (absolute paths): print its `code`.
- `tsc --types ''` is refused (`TS6044`); to compile without `@types/node`, point `--typeRoots` at an empty folder.
- The script runs in its own folder when it starts with `process.chdir(path.dirname(fileURLToPath(import.meta.url)))`, so no shell has to `cd` first.

Related: builds on [../SKILL.md](../SKILL.md); see also [page-sets.md](page-sets.md), [nuget.md](nuget.md).
