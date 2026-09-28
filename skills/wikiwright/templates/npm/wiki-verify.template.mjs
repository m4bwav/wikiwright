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
// exactly as printed; a page never shows output this script did not produce.
// Network: the package talks only to the local fixture server below, never the internet.

import http from 'node:http';
import {spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
import path from 'node:path';

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
function cli(...args) {
	// The published bin, run with this Node; stdout, stderr and the exit code are all recorded.
	const r = spawnSync(process.execPath, [path.join(pkgDir, binEntry), ...args], {encoding: 'utf8'});
	return `exit ${r.status}\n--- stdout\n${r.stdout}--- stderr\n${r.stderr}`;
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
	show('commands help', cli('--help'));
}

// API reference, behaviour, recipes, FAQ: add a capture() per example here.

server.close();
show('requests the fixture server saw', seen);
