// wiki-verify for {{PACKAGE}}@{{VERSION}}: runs every example on the wiki against the
// PUBLISHED package, never the working tree. Keep the filled-in copy in the repository
// as ai-docs/notes/<date>-wiki-verify.mjs so the next release can run it again.
//
// Run it from a scratch folder outside the repository:
//   npm init -y
//   npm install {{PACKAGE}}@{{VERSION}}
//   node wiki-verify.mjs > wiki-verify.out.txt
//
// Every case prints "## <label>" and then its output. Paste outputs into the pages
// exactly as printed; a page never shows output this script did not produce, and never
// one converted by hand (a JSON value retyped as console.log shows it): add a case that
// prints the page's form instead (L-008, L-019). Save the output beside this file as
// ai-docs/notes/<date>-wiki-verify.out.txt with 127.0.0.1:<digits> replaced by
// 127.0.0.1:<port>, and check the pages with `wikiwright.py outputs <wiki dir> <that file>`. Each code block on
// a page is here as the page shows it, in a snippet(): check with `wikiwright.py snippets <wiki dir> <this file>`.
// Keep time zones, absolute paths and timings out of the output (L-022).
// ===== section: requests =====
// Network: the package talks only to the local fixture server below, never the internet. A package whose
// requests go to the hosts its input names, with output computed from the host, uses the "by host name"
// section instead of fixture addresses (references/npm.md, L-116).
// ===== end: requests =====
// OLDEST_NODE=<major> reruns everything under the oldest Node in engines (the last section, L-106); compare
// the two outputs, and a new release's output with the saved one, with `wikiwright.py diffout OLD NEW`.

// ===== section: requests =====
import http from 'node:http';
// ===== end: requests =====
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
import path from 'node:path';
import {chmodSync, copyFileSync, mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';

// Everything runs in this file's folder, so no shell needs to change directory first.
process.chdir(path.dirname(fileURLToPath(import.meta.url)));

const PACKAGE = '{{PACKAGE}}';
const VERSION = '{{VERSION}}';
const require = createRequire(import.meta.url);

function show(label, value) {
	console.log(`## ${label}`);
	console.log(typeof value === 'string' ? value : inspect(value));
	console.log();
}

function inspect(value) {
	// JSON with the cases JSON loses kept visible: undefined, errors, NaN.
	return JSON.stringify(value, (key, v) => {
		if (v === undefined) {
			return '<undefined>';
		}

		if (v instanceof Error) {
			return {name: v.name, message: v.message, ...v};
		}

		if (typeof v === 'number' && !Number.isFinite(v)) {
			return String(v);
		}

		return v;
	}, 2);
}

// Any other program (a runtime from npm, a package manager, bash, the golden capture), asynchronously,
// with LF line endings. On Windows spawn .cmd shims with shell: true. Standard input is closed (or gets
// `input`): a CLI that reads stdin when it has no argument would otherwise wait for ever (L-007).
function run(file, args, {cwd = process.cwd(), env = {}, shell = false, input = ''} = {}) {
	return new Promise(resolve => {
		const child = spawn(file, args, {cwd, env: {...process.env, ...env}, shell});
		child.stdin.end(input);
		let stdout = '';
		let stderr = '';
		child.stdout.on('data', chunk => {
			stdout += chunk;
		});
		child.stderr.on('data', chunk => {
			stderr += chunk;
		});
		child.on('close', code => {
			resolve({code, stdout: stdout.replaceAll('\r\n', '\n'), stderr: stderr.replaceAll('\r\n', '\n')});
		});
	});
}

// A shell snippet as a page shows it (BASH=<Git Bash's bash.exe> on Windows), printing first the Node it ran on,
// so an OLDEST_NODE rerun that picked up the system Node shows it (L-118).
function shell(script, options = {}) {
	return run(process.env.BASH || 'bash', ['-c', `echo "shell node: $(node --version)"; ${script}`], options);
}

// ===== section: bin =====
// A terminal transcript as a page shows it: `$ command`, what it printed with stdout and stderr merged in the order
// they were written (2>&1 into one pipe; cli() keeps them apart), then `$ echo $?` and the exit code. Put
// node_modules/.bin first on PATH (env) to run the bin by name, as a user or an npm script would.
const quote = text => `'${text.replaceAll("'", "'\\''")}'`;
async function term(command, options = {}) {
	const result = await shell(`printf '%s\\n' ${quote(`$ ${command}`)}\n{ ${command}\n} 2>&1\nprintf '$ echo $?\\n%s\\n' "$?"`, options);
	return result.stdout.replace(/\n$/, '') + (result.stderr ? `\n(shell stderr) ${result.stderr}` : '');
}
// ===== end: bin =====

async function capture(label, fn) {
	try {
		show(label, await fn());
	} catch (error) {
		show(`${label} (threw)`, `${error?.name}: ${error?.message}`);
	}
}

// ----- page examples, held as the text the page shows -----
// snippet() writes a page's code block to ./snippets/<label>.mjs (.cjs, .mts), runs it as a child with this Node
// (so OLDEST_NODE covers it) and prints what it printed: stdout, then stderr, then a non-zero exit code. The
// program holds every block as the page shows it, so `wikiwright.py snippets` finds each one. Start the template
// literal with a newline and close it on a line of its own. Inside it write each \ as \\, each ` as \` and each
// ${ as \${ (snippets reads the program with those three undone). Not String.raw: it keeps the \ before ` and ${.
// A //=> line prints the statement just above it as the REPL does (console.log('%O', ...)); a statement over
// several lines ends with its closing bracket at its first line's indent.
// Options: type 'module', 'commonjs' or 'typescript' (compiled by the scratch project's tsc, npm install
// typescript; `tsc` holds the flags, and its exit code prints first); before and after, code around the page's
// (the import the page left out, a call to the function it only defines); runtime and args (another program, or
// Node flags such as ['--import', path.resolve('route.mjs')]); env; cwd (a file-tree root: the file stays in
// ./snippets so its import resolves); replace, text swapped in the written file only. SNIPPET holds defaults the
// fixture sections set. runSnippet() returns the text instead of printing it, for inTree().
const SNIPPET = {replace: {}, env: {}};
const lead = line => line.match(/^\s*/)[0];
function prints(code) {
	const lines = code.split('\n');
	for (let end = 0; end < lines.length - 1; end++) {
		if (!/^\s*\/\/ ?=>/.test(lines[end + 1]) || !lines[end].trimEnd().endsWith(';')) {
			continue;
		}

		const indent = lead(lines[end]);
		let start = end;
		while (/^[)\]}]/.test(lines[end].trim()) && start > 0 && (start === end || !lines[start].trim() || lead(lines[start]) !== indent)) {
			start--;
		}

		if (!/^(const|let|var|import|export|return|if|for|while)\b/.test(lines[start].trim())) {
			lines[start] = `${indent}console.log('%O', ${lines[start].slice(indent.length)}`;
			lines[end] = lines[end].replace(/;\s*$/, ');');
		}
	}

	return lines.join('\n');
}

async function runSnippet(label, code, {type = 'module', before = '', after = '', runtime = process.execPath, args = [], env = {}, cwd = process.cwd(), replace = SNIPPET.replace, tsc = ['--strict', '--module', 'nodenext', '--moduleResolution', 'nodenext', '--target', 'es2022']} = {}) {
	const name = label.toLowerCase().replaceAll(/[^a-z\d]+/g, '-');
	let file = path.resolve('snippets', name + {module: '.mjs', commonjs: '.cjs', typescript: '.mts'}[type]);
	let text = before + prints(code.replace(/^\n/, '')) + after;
	for (const [from, to] of Object.entries(replace)) {
		text = text.replaceAll(from, to);
	}

	mkdirSync(path.dirname(file), {recursive: true});
	writeFileSync(file, text);
	let out = '';
	if (type === 'typescript' && runtime === process.execPath) {
		const built = await run(runtime, [require.resolve('typescript/bin/tsc'), ...tsc, '--outDir', 'snippets/tsc', path.relative('.', file)]);
		out = `tsc: exit ${built.code}\n${built.stdout}`;
		file = path.resolve('snippets', 'tsc', `${name}.mjs`);
	}

	const result = await run(runtime, [...args, file], {cwd, env: {...SNIPPET.env, ...env}});
	return out + result.stdout.replace(/\n$/, '') + (result.stderr ? `\n--- stderr\n${result.stderr.replace(/\n$/, '')}` : '') + (result.code ? `\nexit ${result.code}` : '');
}

async function snippet(label, code, options) {
	show(label, await runSnippet(label, code, options));
}
// ----- end of page examples -----

// ----- the installed package: version, both module systems, the bin -----
const pkgDir = path.join(process.cwd(), 'node_modules', ...PACKAGE.split('/'));
const pkg = JSON.parse(readFileSync(path.join(pkgDir, 'package.json'), 'utf8'));
if (pkg.version !== VERSION) {
	throw new Error(`installed ${pkg.version}, expected ${VERSION}`);
}

show('installed', `${PACKAGE}@${pkg.version} on Node ${process.version}`);
const esm = await import(PACKAGE);
const cjs = require(PACKAGE);
show('esm exports', Object.keys(esm).sort());
show('cjs exports', Object.keys(cjs).sort());

// ===== section: bin =====
const binEntry = typeof pkg.bin === 'string' ? pkg.bin : pkg.bin && Object.values(pkg.bin)[0];
// The published bin, run with this Node; stdout, stderr and the exit code are all recorded.
// Asynchronous on purpose: spawnSync blocks this process's event loop, and with it the
// fixture server below, so a CLI call against the fixture would hang (L-007). CLI_ENV reaches the fixture by host
// name: set it to fx.env when the kit is in use. A last argument that is an object gives the options:
// cli('--check', '.', {cwd: root}) runs in a scratch tree (the "files on disk" section).
let CLI_ENV = {};
function cli(...args) {
	const {cwd = process.cwd(), env = {}} = typeof args.at(-1) === 'object' ? args.pop() : {};
	return new Promise(resolve => {
		const child = spawn(process.execPath, [path.join(pkgDir, binEntry), ...args], {cwd, env: {...process.env, ...CLI_ENV, ...env}});
		child.stdin.end();
		let stdout = '';
		let stderr = '';
		child.stdout.on('data', chunk => {
			stdout += chunk;
		});
		child.stderr.on('data', chunk => {
			stderr += chunk;
		});
		child.on('close', code => {
			resolve(`exit ${code}\n--- stdout\n${stdout}--- stderr\n${stderr}`);
		});
	});
}
// ===== end: bin =====

// A package with a bin needs cli(), which `wikiwright.py scaffold` keeps only with --bin.
if (pkg.bin && typeof cli === 'undefined') {
	throw new Error('the package has a bin: run wikiwright.py scaffold again with --bin');
}

// ===== section: requests =====
// ----- local fixture server (delete when the package makes no requests) -----
// One route per behaviour the wiki shows. Add routes; never call a real site.
const routes = {
	'/'(request, response) {
		response.writeHead(200, {'content-type': 'text/html; charset=utf-8'});
		response.end('<!doctype html><title>Fixture page</title>');
	},
};
const seen = [];
const server = http.createServer((request, response) => {
	seen.push(`${request.method} ${request.url}`);
	const route = routes[new URL(request.url, 'http://x').pathname];
	if (route) {
		route(request, response);
	} else {
		response.writeHead(404, {'content-type': 'text/plain'});
		response.end('not found');
	}
});
await new Promise(resolve => {
	server.listen(0, '127.0.0.1', resolve);
});
const base = `http://127.0.0.1:${server.address().port}`;
// Pages show the fixture as https://example.com (outputs maps it back); the files snippet() writes use the fixture.
SNIPPET.replace = {'https://example.com': base};

// Servers the end of the script closes, or the process (and the OLDEST_NODE rerun) never exits.
const closers = [];
// ===== end: requests =====

// ===== section: by-host =====
// ----- by host name (delete unless the package requests the hosts its input names, L-116) -----
// Copy ../host-fixture.mjs beside this script (and into the repository's ai-docs/notes/ with it). It serves
// `handle` under the real host names through a proxy with a throwaway CA, guards every child against sockets
// that leave 127.0.0.1 and tests the guard first (L-117). Children run with {env: fx.env}; this process's
// fetch needs fx.routeThisProcess() (npm install undici@7). Print fx.seen in one case, so a routing failure
// cannot pass for behaviour. A package that calls the global fetch at call time, run in Node only, can use a
// fetch wrapper instead (L-115); read the repository's test helpers first, they often have one.
let fx;
if (false) {
	const {startHostFixture} = await import('./host-fixture.mjs');
	fx = await startHostFixture({hosts: ['example.com'], handle: (url, request, response) => server.emit('request', request, response)});
	show('guard', fx.guardCheck);
	show('lookups reach the fixture through', fx.route);
	closers.push(fx);
// ===== section: bin =====
	CLI_ENV = fx.env;
// ===== end: bin =====
	SNIPPET.env = fx.env;
	SNIPPET.replace = {};
}
// ===== end: by-host =====

// ===== section: files =====
// ----- files on disk (delete unless the package writes, moves or deletes files, L-130) -----
// Copy ../file-tree.mjs beside this script (and into the repository's ai-docs/notes/ with it). Every case gets a
// fresh scratch copy of its tree under ./trees, so no case sees another's rewrite and nothing touches the
// repository or the user's files. It prints what the case returned, one line per file (not written, written with
// the same bytes, changed, created, deleted) and each written file's before and after contents under a header
// naming its size, BOM, line endings and final newline, which the text cannot show. A page shows a file as its
// "before" and "after" blocks and states those facts in prose. Read its header for links, read-only files, a
// folder to copy and the library run in-process ({chdir: true}).
async function inTree(label, spec, fn, options) {
	const {treeCase} = await import('./file-tree.mjs');
	show(label, await treeCase(spec, fn, options));
}
// ===== section: bin =====
// await inTree('commands: a folder', {'data/a.json': '{"a":1}'}, ({root}) => cli('data', {cwd: root}));
// ===== end: bin =====
// await inTree('api: report', {'a.json': '{"a":1}'}, () => esm.default('a.json'), {chdir: true});
// await inTree('recipes: a folder', {'a.json': '{"a":1}'}, ({root}) => runSnippet('recipes: a folder', `
// <the page's code>
// `, {cwd: root}));
// ===== end: files =====

// ----- the cases: one per example on the wiki, labelled by page -----
// Every code block a page shows is a snippet() holding it as the page shows it; capture() and show() are for checks
// no page shows (errors, membership, the golden replay).
// Getting started
// ===== section: example =====
await snippet('getting-started esm', `
import pkg from '{{PACKAGE}}';

console.log(await pkg('https://example.com/'));
`);
await snippet('getting-started cjs', `
const pkg = require('{{PACKAGE}}');

pkg('https://example.com/').then(result => {
  console.log(result);
});
`, {type: 'commonjs'});
// ===== end: example =====
// ===== section: bin =====
if (binEntry) {
	show('commands help', await cli('--help'));
}
// ===== end: bin =====

// Old majors (Versions and upgrading): install each in its own scratch folder and pass
// V2=<folder> (etc.); load it with createRequire(path.join(folder, 'index.js')) or a file:// import.

// API reference, behaviour, recipes, FAQ: a snippet() per code block here.

// ===== section: golden =====
// ----- golden captures, replayed today (L-020, L-113) -----
// When the repository keeps test/golden/capture-<old>.cjs and <old>.json: set GOLDEN=<the clone's test/golden>
// and OLD=<a folder with PACKAGE@<old> and whatever the capture requires installed>. The capture runs as a
// child process, once against the old version (unchanged) and once here against VERSION (patch only the
// lines the new layout breaks, such as the bin's path, and name them on the page), one after the other.
// Compare the answers, the timing and the request lines apart. The golden file is only read. A capture that writes
// files needs TEMP, TMP and TMPDIR pointed into scratch and views for files instead (references/npm.md, "Packages
// that write files").
// A capture that records through its own proxy with TLS, replayed against a fetch-based major, also needs
// undici's EnvHttpProxyAgent after it sets the proxy variables and a fixture copy that serves CONNECT to
// port 80 in plain HTTP (references/npm.md, "Golden captures that record through a proxy with TLS").
const {GOLDEN, OLD} = process.env;
if (GOLDEN && OLD) {
	const CAPTURE = 'capture-{{OLD_VERSION}}.cjs';
	const HELPERS = []; // the files the capture requires, such as 'codec.cjs', 'fixture-server.cjs'
	for (const file of [CAPTURE, ...HELPERS]) {
		copyFileSync(path.join(GOLDEN, file), path.join(OLD, file));
		copyFileSync(path.join(GOLDEN, file), file);
	}

	const patched = readFileSync(CAPTURE, 'utf8'); // .replaceAll(<old layout>, <new layout>)
	writeFileSync(`now-${CAPTURE}`, patched);
	const want = JSON.parse(readFileSync(path.join(GOLDEN, '{{OLD_VERSION}}.json'), 'utf8'));
	for (const [label, result] of [
		['golden: {{OLD_VERSION}} today', await run(process.execPath, [CAPTURE], {cwd: OLD})],
		[`golden: ${VERSION}`, await run(process.execPath, [`now-${CAPTURE}`])],
	]) {
		if (result.code !== 0) {
			show(label, `capture failed, exit ${result.code}\n${result.stderr.split('\n').slice(0, 5).join('\n')}`);
			continue;
		}

		// Compare the answers, the callback timing and the requests apart (L-113). Adapt the three views to the
		// capture's format: here cases with a name, `returned`/`threw`/`calls[].args` answers, `calls[].sync`
		// timing and `requests`.
		const views = {
			answers: entry => [entry.returned, entry.threw, entry.calls?.map(call => call.args), entry.uncaught],
			timing: entry => entry.calls?.map(call => call.sync),
			requests: entry => entry.requests,
		};
		const got = new Map(JSON.parse(result.stdout).cases.map(entry => [entry.name, entry]));
		const lines = [`${want.cases.length} cases`];
		for (const [view, pick] of Object.entries(views)) {
			const differing = want.cases.filter(entry => JSON.stringify(pick(got.get(entry.name) ?? {})) !== JSON.stringify(pick(entry)));
			lines.push(`${view}: ${want.cases.length - differing.length} identical${differing.length > 0 ? `; differ: ${differing.map(entry => entry.name).join(' | ')}` : ''}`);
		}

		show(label, lines.join('\n'));
	}
}
// ===== end: golden =====

// ----- the oldest Node line in engines (L-106) -----
// OLDEST_NODE=<major> reruns this whole script under that Node (downloaded by npx) and saves that run as
// wiki-verify.node<major>.out.txt. The Node binary is copied alone into its own folder, which goes first on PATH
// so the shells and bins the cases spawn use it too: the npm node package's bin folder also holds a text file
// named `node`, and Git Bash skips that folder and runs the system Node without a word (L-118). Every shell case
// prints the Node it ran (`node --version` inside the shell). On Windows `npx.cmd` runs the node.exe installed
// beside it, whatever PATH says: run a page's `npx <bin>` case once more as `cli()` does, with process.execPath. Compare with `wikiwright.py diffout <this run's
// output> wiki-verify.node<major>.out.txt`: every difference is a page claim to scope by version, and a block
// true on one line only gets <!-- outputs: node>=N --> on the page. Save both outputs in the repository.
// OLDEST_NODE_BIN=<a node binary> uses that binary instead of npx (a Linux run with Node from the registry and no npm).
// The folder is named per platform: a Windows run and a WSL run in one scratch folder once shared it, and the Linux
// `node` beside node.exe made Git Bash skip it and run the system Node in every shell case (L-118, a second way in).
const {OLDEST_NODE, OLDEST_NODE_BIN, WIKI_VERIFY_CHILD} = process.env;
if (OLDEST_NODE && !WIKI_VERIFY_CHILD) {
	const found = OLDEST_NODE_BIN || (await run('npx', ['-y', '-p', `node@${OLDEST_NODE}`, 'node', '-p', 'process.execPath'], {shell: process.platform === 'win32', env: {NODE_OPTIONS: ''}})).stdout.trim().split('\n').at(-1);
	const alone = path.resolve(`node${OLDEST_NODE}-alone-${process.platform}`);
	mkdirSync(alone, {recursive: true});
	const oldNode = path.join(alone, path.basename(found));
	copyFileSync(found, oldNode);
	chmodSync(oldNode, 0o755);
	const outName = `wiki-verify.${process.platform === 'win32' ? '' : 'linux.'}node${OLDEST_NODE}.out.txt`;
	const rerun = await run(oldNode, [fileURLToPath(import.meta.url)], {env: {WIKI_VERIFY_CHILD: '1', PATH: `${alone}${path.delimiter}${process.env.PATH}`}});
	writeFileSync(outName, rerun.stdout + (rerun.stderr ? `## stderr of the run\n${rerun.stderr}\n` : ''));
	show(`oldest node: node@${OLDEST_NODE}`, `${(await run(oldNode, ['--version'])).stdout.trim()}, exit ${rerun.code}, output saved as ${outName}`);
}

// ===== section: requests =====
for (const each of [server, ...closers]) {
	each.closeAllConnections?.();
	each.close();
}

show('requests the fixture server saw', seen);
// ===== end: requests =====
