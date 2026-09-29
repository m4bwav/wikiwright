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
// Network: the package talks only to the local fixture server below, never the internet. A package whose
// requests go to the hosts its input names, with output computed from the host, uses the "by host name"
// section instead of fixture addresses (references/npm.md, L-116).
// OLDEST_NODE=<major> reruns everything under the oldest Node in engines (the last section, L-106); compare
// the two outputs, and a new release's output with the saved one, with `wikiwright.py diffout OLD NEW`.

import http from 'node:http';
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
import path from 'node:path';
import util from 'node:util';
import {copyFileSync, mkdirSync, readFileSync, writeFileSync} from 'node:fs';
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

// ----- by host name (delete unless the package requests the hosts its input names, L-116) -----
// Pages are served under their real host names: a plain server and a TLS server behind a stand-in proxy that
// answers CONNECT (Node tunnels http: too) and routes by port. Every runtime trusts only a throwaway CA made
// here. Children get `routed` as their environment; this process routes its own fetch through undici
// (npm install undici@7). A preloaded guard refuses any socket not to 127.0.0.1. Worked example, with Deno,
// Bun, package managers and an old version: markdown-plain-link-replacer ai-docs/notes/2026-09-29-wiki-verify.mjs.
const BY_HOST_NAME = false;
let routed = {};
// Servers the end of the script closes, or the process (and the OLDEST_NODE rerun) never exits.
const closers = [];
if (BY_HOST_NAME) {
	const {spawnSync} = await import('node:child_process');
	const https = await import('node:https');
	const tls = await import('node:tls');
	const HOSTS = ['example.com', '*.example.com']; // every host a page names
	mkdirSync('tls', {recursive: true});
	for (const args of [
		['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'tls/ca-key.pem', '-out', 'tls/ca.pem', '-days', '2', '-subj', '/CN=wiki-verify CA',
			'-addext', 'basicConstraints=critical,CA:TRUE', '-addext', 'keyUsage=critical,keyCertSign'],
		['req', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'tls/key.pem', '-out', 'tls/server.csr', '-subj', '/CN=wiki-verify fixture',
			'-addext', `subjectAltName=${HOSTS.map(host => `DNS:${host}`).join(',')}`],
		// Deno's TLS refuses a self-signed certificate marked as a CA as the server's own: sign a separate one.
		['x509', '-req', '-in', 'tls/server.csr', '-CA', 'tls/ca.pem', '-CAkey', 'tls/ca-key.pem', '-set_serial', '1', '-days', '2', '-copy_extensions', 'copyall', '-out', 'tls/cert.pem'],
	]) {
		const made = spawnSync(process.env.OPENSSL || 'openssl', args, {encoding: 'utf8', env: {...process.env, MSYS_NO_PATHCONV: '1'}});
		if (made.status !== 0) {
			throw new Error(`openssl failed: ${made.stderr || made.error}`);
		}
	}

	const ca = path.resolve('tls/ca.pem');
	// Route by host and path: serve() looks up request.headers.host; add pages to it the way `routes` does.
	const serve = (request, response) => server.emit('request', request, response);
	const secure = https.createServer({key: readFileSync('tls/key.pem'), cert: readFileSync('tls/cert.pem')}, serve);
	const proxy = http.createServer(serve);
	proxy.on('connect', (request, socket) => {
		socket.write('HTTP/1.1 200 Connection Established\r\n\r\n');
		(request.url.endsWith(':443') ? secure : server).emit('connection', socket);
	});
	await new Promise(resolve => {
		proxy.listen(0, '127.0.0.1', resolve);
	});
	const proxyUrl = `http://127.0.0.1:${proxy.address().port}`;
	closers.push(proxy, secure);
	// net.connect() passes its arguments as one array: read the options from inside it (L-117).
	writeFileSync('guard.cjs', "'use strict';\nconst net = require('node:net');\nconst connect = net.Socket.prototype.connect;\nnet.Socket.prototype.connect = function (...args) {\n\tconst first = Array.isArray(args[0]) ? args[0][0] : args[0];\n\tconst o = typeof first === 'object' && first !== null ? first : {port: first, host: args[1]};\n\tif (!o.path && !['127.0.0.1', 'localhost', '::1', undefined].includes(o.host)) {\n\t\tthrow new Error('wiki-verify guard: refused a connection to ' + o.host + ':' + o.port);\n\t}\n\treturn Reflect.apply(connect, this, args);\n};\n");
	writeFileSync('route.cjs', "'use strict';\nconst {setGlobalDispatcher, EnvHttpProxyAgent} = require('undici');\nsetGlobalDispatcher(new EnvHttpProxyAgent());\n");
	// NODE_OPTIONS reads a backslash as an escape: forward slashes.
	const preload = file => `--require "${path.resolve(file).split(path.sep).join('/')}"`;
	const routeEnv = {HTTP_PROXY: proxyUrl, HTTPS_PROXY: proxyUrl, NO_PROXY: '', NODE_EXTRA_CA_CERTS: ca, DENO_CERT: ca, NODE_OPTIONS: preload('guard.cjs')};
	// Node 24 honours NODE_USE_ENV_PROXY=1 (read at startup); Node 20 does not, so its children preload undici. The
	// probe's host is .invalid, so a probe that skipped the proxy cannot leave the machine.
	writeFileSync('probe.mjs', "console.log(await fetch('http://wiki-verify.invalid/').then(r => r.status, e => e.message));\n");
	const probe = await run(process.execPath, ['probe.mjs'], {env: {...routeEnv, NODE_USE_ENV_PROXY: '1'}});
	routed = /^\d+$/.test(probe.stdout.trim()) ? {...routeEnv, NODE_USE_ENV_PROXY: '1'} : {...routeEnv, NODE_OPTIONS: `${preload('guard.cjs')} ${preload('route.cjs')}`};
	show('lookups reach the fixture through', routed.NODE_USE_ENV_PROXY ? 'NODE_USE_ENV_PROXY=1' : 'undici EnvHttpProxyAgent preloaded');
	require('./guard.cjs');
	const {setGlobalDispatcher, ProxyAgent} = require('undici');
	setGlobalDispatcher(new ProxyAgent({uri: proxyUrl, requestTls: {ca: [...tls.rootCertificates, readFileSync(ca, 'utf8')]}}));
	// Children: run(process.execPath, ['example.mjs'], {env: routed}). Print one case with the requests the
	// fixture saw, so a routing failure cannot pass for "the link was left".
}

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

		// Adapt the keys to the capture's format: here a list of cases with a name.
		const got = new Map(JSON.parse(result.stdout).cases.map(entry => [entry.name, JSON.stringify(entry)]));
		const differing = want.cases.filter(entry => got.get(entry.name) !== JSON.stringify(entry)).map(entry => entry.name);
		show(label, [`${want.cases.length} cases, ${want.cases.length - differing.length} identical to the golden file`, ...differing].join('\n'));
	}
}

// ----- the oldest Node line in engines (L-106) -----
// OLDEST_NODE=<major> reruns this whole script under that Node (downloaded by npx), with its folder first on
// PATH so the shells and bins the cases spawn use it too, and saves that run as wiki-verify.node<major>.out.txt.
// Compare with `wikiwright.py diffout <this run's output> wiki-verify.node<major>.out.txt`: every difference is
// a page claim to scope by version. Save both outputs in the repository.
const {OLDEST_NODE, WIKI_VERIFY_CHILD} = process.env;
if (OLDEST_NODE && !WIKI_VERIFY_CHILD) {
	const found = await run('npx', ['-y', '-p', `node@${OLDEST_NODE}`, 'node', '-p', 'process.execPath'], {shell: process.platform === 'win32', env: {NODE_OPTIONS: ''}});
	const oldNode = found.stdout.trim().split('\n').at(-1);
	const rerun = await run(oldNode, [fileURLToPath(import.meta.url)], {env: {WIKI_VERIFY_CHILD: '1', PATH: `${path.dirname(oldNode)}${path.delimiter}${process.env.PATH}`}});
	writeFileSync(`wiki-verify.node${OLDEST_NODE}.out.txt`, rerun.stdout);
	show(`oldest node: node@${OLDEST_NODE}`, `${(await run(oldNode, ['--version'])).stdout.trim()}, exit ${rerun.code}, output saved as wiki-verify.node${OLDEST_NODE}.out.txt`);
}

for (const each of [server, ...closers]) {
	each.closeAllConnections?.();
	each.close();
}

show('requests the fixture server saw', seen);
