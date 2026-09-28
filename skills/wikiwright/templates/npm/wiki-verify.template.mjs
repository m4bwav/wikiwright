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
// 127.0.0.1:<port>, and check the pages with `wikiwright.py outputs <wiki dir> <that file>`.
// Keep time zones, absolute paths and timings out of the output (L-022).
// Network: the package talks only to the local fixture server below, never the internet.

import http from 'node:http';
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
import path from 'node:path';
import util from 'node:util';
import {copyFileSync, readFileSync, writeFileSync} from 'node:fs';
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

// Runs a page's example as written and prints exactly what its console.log calls print,
// so a page that shows console.log output matches line for line (layout included).
async function example(label, fn) {
	const lines = [];
	const original = console.log;
	console.log = (...args) => lines.push(util.format(...args));
	try {
		await fn();
	} catch (error) {
		lines.push(`${error?.name}: ${error?.message}`);
	} finally {
		console.log = original;
	}

	show(label, lines.join('\n'));
}

// Any other program (a runtime from npm, a package manager, bash, the golden capture), asynchronously,
// with LF line endings. On Windows spawn .cmd shims with shell: true.
function run(file, args, {cwd = process.cwd(), env = {}, shell = false} = {}) {
	return new Promise(resolve => {
		const child = spawn(file, args, {cwd, env: {...process.env, ...env}, shell});
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

async function capture(label, fn) {
	try {
		show(label, await fn());
	} catch (error) {
		show(`${label} (threw)`, `${error?.name}: ${error?.message}`);
	}
}

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

const binEntry = typeof pkg.bin === 'string' ? pkg.bin : pkg.bin && Object.values(pkg.bin)[0];
// The published bin, run with this Node; stdout, stderr and the exit code are all recorded.
// Asynchronous on purpose: spawnSync blocks this process's event loop, and with it the
// fixture server below, so a CLI call against the fixture would hang (L-007).
function cli(...args) {
	return new Promise(resolve => {
		const child = spawn(process.execPath, [path.join(pkgDir, binEntry), ...args]);
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

// ----- the cases: one per example on the wiki, labelled by page -----
// Getting started
await capture('getting-started esm', async () => esm.default?.(`${base}/`));
await capture('getting-started cjs', async () => cjs.default?.(`${base}/`));
if (binEntry) {
	show('commands help', await cli('--help'));
}

// Old majors (Versions and upgrading): install each in its own scratch folder and pass
// V2=<folder> (etc.); load it with createRequire(path.join(folder, 'index.js')) or a file:// import.

// API reference, behaviour, recipes, FAQ: add a capture() per example here.

// ----- golden captures, replayed today (L-020, L-113) -----
// When the repository keeps test/golden/capture-<old>.cjs and <old>.json: set GOLDEN=<the clone's test/golden>
// and OLD=<a folder with PACKAGE@<old> and whatever the capture requires installed>. The capture runs as a
// child process, once against the old version (unchanged) and once here against VERSION (patch only the
// lines the new layout breaks, such as the bin's path, and name them on the page), one after the other.
// Compare the answers, the timing and the request lines apart. The golden file is only read.
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

		// Adapt the keys to the capture's format: here a list of cases with a name.
		const got = new Map(JSON.parse(result.stdout).cases.map(entry => [entry.name, JSON.stringify(entry)]));
		const differing = want.cases.filter(entry => got.get(entry.name) !== JSON.stringify(entry)).map(entry => entry.name);
		show(label, [`${want.cases.length} cases, ${want.cases.length - differing.length} identical to the golden file`, ...differing].join('\n'));
	}
}

server.close();
show('requests the fixture server saw', seen);
