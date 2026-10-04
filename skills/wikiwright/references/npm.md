# npm packages: survey and verification

Read this for every npm package. Read also, only when the package needs it: [npm-requests.md](npm-requests.md) (requests, host names, captures recorded through a proxy), [npm-files.md](npm-files.md) (it writes files), [golden-captures.md](golden-captures.md) (golden captures).

## Registry facts for the survey

Start with the helper. It reads the packument and last week's downloads and prints one fact per line:

```sh
python scripts/wikiwright.py registry PACKAGE --npm   # add --version X for an older version, --json for everything
```

It prints the versions with their dates (same-day releases share a line), dist-tags, and deprecations. For the latest version it prints `engines`, type, main, types, exports and bin, the dependencies, unpacked size and file count, provenance and `gitHead`. It also prints last week's downloads, in total and on one line per version, most first (the first eight, then the rest summed, then how many versions had none), which Versions and upgrading needs for each old version, and the time read. The per-version line comes from `api.npmjs.org/versions/<name>/last-week`, which leaves out versions with no downloads and needs a scoped name encoded whole (`%40scope%2Fname`; `@scope/name` answers 404; checked 2026-09-30). On 2026-09-29 it printed about 1.1 KB where the packument came to 76.6 KB (get-title-at-url) and 35.9 KB (format-json-files). The per-version line added 107 bytes for replace-string-at-position (892 to 999) and 170 for get-title-at-url (1,191 to 1,361) on 2026-09-30.

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

`scaffold` also writes `<scratch>/package.json` as `{"private": true}` when the folder has none, and never replaces one. Without it, `npm install` in that folder installs into the nearest parent folder holding a `package.json` or `node_modules` (`npm prefix` in an empty subfolder printed the parent, 2026-09-30). `npm init -y --prefix <dir>` is no substitute: it still writes `package.json` into the current folder, not `<dir>`. A stray `package.json` made Yarn 4 refuse to install in the sixth run, and one landed in the skill's own source folder the same day (L-017). `npm install --prefix` does install into `<dir>`. A second folder for an old version (`OLD`) needs its own `package.json`, written with the editor.

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
| `--golden OLD_VERSION` | the golden replay of `capture-OLD_VERSION.cjs`: copies the capture and every `./` file it requires (read from its `require` lines), runs it against both versions and compares them with the comparator the golden file's shape calls for | has golden captures in its repository |

It refuses to overwrite the script or a kit without `--force`. Measured on replace-string-at-position 2.0.0 (no bin, no requests, no files) on 2026-09-30: with no flags the script is 12,722 bytes where the template is 25,524, and 18,552 with `--golden 1.0.4` (C-20260930-8; the first scaffold, C-20260930-7, wrote 11,197 from 21,140 before the eighth run). A run skips the copy, two placeholder edits and five section deletions.

Every code block on a page is one `snippet()` in the script, labelled by page. It holds the block as the page shows it, in a template literal, writes it to `snippets/<label>.mjs` (`.cjs`, or TypeScript compiled by the scratch project's `tsc`), runs that file with the script's Node and prints what it printed. So `wikiwright.py snippets` finds every block, and an `OLDEST_NODE` rerun runs the snippets on the old Node too. In the literal, write a backslash as `\\`, a backtick as `` \` `` and `${` as `\${`; `String.raw` would keep the backslash before the last two. The written file swaps the pages' `https://example.com` for the fixture address, and takes `env`, `args` (such as `--import` for a fetch router), `cwd` (a file-tree root) and code to run before or after the page's. A `//=>` line prints the statement above it. For get-title-at-url 3.0.0, five blocks from Getting started and Recipes went into snippets: `snippets` found 5 of 5 and `outputs` 5 of 5, where the earlier script, which ran its cases as its own code, matched none of the five. Checks no page shows (error fields, membership, the golden replay) stay `capture()` or `show()`.

Two options let one page text run in more than one setting. `dir` is the folder the file is written to and run from. With `{dir: path.join(OLD, 'snippets')}` the page's own `import` or `require` loads the old version installed in `OLD`, so a Versions page shows the same code against both majors (hold the text in a `const` both calls share). For TypeScript, `type: 'typescript'` takes `ext` (`.mts` by default, `.cts` or `.ts`), `typescript` (the folder in `node_modules` to compile with, such as `typescript6` after `npm install typescript6@npm:typescript@6`) and `tsc` (the flags; with `--noEmit` among them it only type-checks). The output starts `tsc <version>: exit <code>`. A matrix is one `snippet()` per compiler and setup, in a loop over the compiler folders: L-131 asks for the current `latest` and every version a page names.

What a TypeScript page can promise, measured 2026-09-30 with 7.0.2 and 6.0.3 on replace-string-at-position 2.0.0:

- TypeScript 7.0.2 refuses `--moduleResolution node10` and `--esModuleInterop false` with `error TS5108: Option '...' has been removed`, with or without `--ignoreDeprecations 6.0` (or `7.0`), and exits 2. It still writes the JavaScript, so the snippet's output follows the error; a page says the build fails, not that nothing is emitted.
- TypeScript 6.0.3 accepts both with `--ignoreDeprecations 6.0` and refuses `node10` without it (`error TS5107: ... will stop functioning in TypeScript 7.0`). So a page that names `node10` or `esModuleInterop: false` scopes the claim to TypeScript 6 and earlier.
- `nodenext` (`.mts` and `.cts`) and `bundler` compile on both.

## The CLI against the fixture

Spawn it asynchronously (L-007), with standard input closed (a CLI that reads stdin when it gets no argument waits for ever on an open pipe). `cli()` records stdout and stderr apart; a page's terminal block comes from the template's `term()`, which prints `$ command`, both streams merged in the order they were written, then `$ echo $?` and the code. Two separate streams lose that order: `--check` printed its list before the skip lines, the reverse of a terminal (the sixth run).

## The oldest Node in engines

Run the whole script again on the oldest Node line in `engines` (L-106 `oldest-node-run`). The template's `OLDEST_NODE=<version>` does it. Give the exact version, such as `OLDEST_NODE=20.20.2` (`npm view node@20 version` lists that line's releases; take the newest), so npx fetches a pinned package; a bare major also works but takes whatever is newest in that line on the day. It asks npx for that Node (`npx -y -p node@<version> node -p process.execPath`), copies the binary alone into `node<major>-alone-<platform>/`, reruns the script with that folder first on PATH (so shells and bins the cases spawn use it too), and saves `wiki-verify.node<major>.out.txt` (`wiki-verify.linux.node<major>.out.txt` off Windows). `OLDEST_NODE_BIN=<binary>` skips npx. The npx call is one command string with `shell: true` and no argument array. An array beside `shell: true` printed Node 24's DEP0190 warning on every run (2026-09-30, C-20260930-8). The npm `node` package's own bin folder will not do: it also holds a text file named `node`, and Git Bash skips the folder and runs the system Node without a word (L-118 `oldest-node-path-trap`). The template's `shell()` prints `shell node: vN` first in every shell case, so the output shows which Node each one ran. Compare with `wikiwright.py diffout <main output> wiki-verify.node<major>.out.txt`; it counts the `shell node:` lines per output instead of listing each, and warns when one output ran shell cases on two Nodes (the L-118 failure). Every changed section is a page claim to scope by version, or a case to fix. It exits 1 when anything differs, which ends a `&&` chain: that means differences, not an error. Save the second output beside the first in the repository.

## Tools that complement the script

anko/txm checks that a markdown file's code blocks produce the output written beside them, and lycheeverse/lychee checks external links in markdown. Neither installs the published version, so neither replaces the verification script; lychee is worth running over the pages when they link much outside GitHub.

## Other runtimes and package managers

- A machine without them can still run them (checked 2026-09-28, L-021 `runtimes-from-npm`). `npm install deno bun` in a scratch folder gives working binaries in `node_modules/.bin`. Corepack, which ships with Node 24, runs pnpm and yarn: `corepack pnpm@10 add PACKAGE@VERSION`, `corepack yarn@4 add PACKAGE@VERSION`. Set `COREPACK_ENABLE_DOWNLOAD_PROMPT=0`. On Windows spawn the `.cmd` shims with `shell: true`. npm 11.16's `allowScripts` blocks deno's postinstall (`npm warn allow-scripts deno@2.9.6`), and the binary still works through its platform package, an optional dependency (2026-09-30): read the warning as expected, and check with `deno --version`.
- Yarn 4 installs with Plug'n'Play and makes no `node_modules`, so `node script.mjs` fails with `ERR_MODULE_NOT_FOUND`: run `yarn node script.mjs`, and say so on Getting started.
- Deno: `import x from 'npm:PACKAGE@VERSION'`, run with the permissions the package needs (`--allow-net` for requests; a package without I/O ran with none). Run it once without the permission too: with no terminal Deno refuses, and a package that turns request failures into an answer (is-an-image-url) answers `false` with no error, which is worth a FAQ entry. Deno 2.9.6 resolves `npm:` imports from the `node_modules` of the nearest folder with a `package.json`: in a folder whose `node_modules` lacks the package (the `RT` folder of `npm install deno bun`) it refuses them until `deno install`, and in the scratch project where the package is installed it works. Run the Deno case in one of those, or in a folder with no `package.json` above it (2026-09-29, L-021).
- Versions move (2026-09-28): `corepack pnpm` gave pnpm 12.6.0, and `corepack yarn` in a folder without a `packageManager` field gave Yarn 1.22.22, which prints a header and a `Done in 0.12s.` timing; run it with `--silent`. For Yarn 4 set `"packageManager": "yarn@4.18.1"`. Print every tool's version from the script.
- Show an install command without running it only when none of this works, and say which were run.
- TypeScript: compile a small file against the installed types (`npx -p typescript@7.0.2 tsc --noEmit --module nodenext --moduleResolution nodenext file.ts`) when the page shows narrowing or type names.

Mark what was run on this machine and what is shown from the package's own docs or CI.

## Traps

- Git Bash on Windows: `npx` and npm scripts need a shell; spawn `npm` through a shell from Node as one command string (`run('npm ls', [], {shell: true})`), or run the bin with `process.execPath` as the template does. An argument array with `shell: true` works but prints DEP0190 on Node 24.
- A package whose `exports` omits `./package.json` cannot be `require`d for its version; the template reads the file from `node_modules` directly.
- JSON loses `undefined`, `NaN` and error fields; the template's `inspect()` keeps them visible.
- A page that shows `console.log` output needs the script to print with `console.log` (or `util.inspect`, which is what it calls): the template's `snippet()` runs the page's code and records exactly what its `console.log` calls print (L-008, L-019).
- An error message built from a `Date` contains the local time zone; keep it out of the saved output (L-022). So does an import error's message (absolute paths): print its `code`.
- `tsc --types ''` is refused (`TS6044`); to compile without `@types/node`, point `--typeRoots` at an empty folder.
- The script runs in its own folder when it starts with `process.chdir(path.dirname(fileURLToPath(import.meta.url)))`, so no shell has to `cd` first.

Related: builds on [../SKILL.md](../SKILL.md); see also [npm-requests.md](npm-requests.md), [npm-files.md](npm-files.md), [golden-captures.md](golden-captures.md), [page-sets.md](page-sets.md), [nuget.md](nuget.md).
