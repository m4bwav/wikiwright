// Tests for skills/wikiwright/templates/npm/host-fixture.mjs. Run from the repository root:
//   node --test tests/host-fixture.test.mjs
// Needs openssl 3 on PATH (or OPENSSL) and a Node that honours NODE_USE_ENV_PROXY (24), or undici installed.
// Nothing here reaches the internet: every host is served by the fixture or refused by the guard.
import assert from 'node:assert/strict';
import {spawn, spawnSync} from 'node:child_process';
import {mkdtempSync, rmSync, writeFileSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {test} from 'node:test';
import {startHostFixture} from '../skills/wikiwright/templates/npm/host-fixture.mjs';

const openssl = process.env.OPENSSL || 'openssl';
const hasOpenssl = spawnSync(openssl, ['version'], {encoding: 'utf8'}).stdout?.startsWith('OpenSSL 3');

function run(args, env) {
	return new Promise(resolve => {
		const child = spawn(process.execPath, args, {env: {...process.env, ...env}});
		child.stdin.end();
		let out = '';
		child.stdout.on('data', chunk => {
			out += chunk;
		});
		child.stderr.on('data', chunk => {
			out += chunk;
		});
		child.on('close', code => resolve({code, out: out.trim()}));
	});
}

test('children reach the fixture by host name over https and http, and nothing else', {skip: !hasOpenssl && 'no OpenSSL 3'}, async () => {
	const dir = mkdtempSync(path.join(os.tmpdir(), 'hf-'));
	const fx = await startHostFixture({
		hosts: ['api.example.com'],
		dir: path.join(dir, 'tls'),
		handle(url, request, response) {
			response.writeHead(200, {'content-type': 'application/json'});
			response.end(JSON.stringify({meant: url.href}));
		},
	});
	try {
		assert.match(fx.guardCheck, /refused 4 of 4/);
		// Deno and Bun get the proxy and the CA without the Node preloads (Deno runs --require preloads).
		assert.equal(fx.runtimeEnv.NODE_OPTIONS, undefined);
		assert.equal(fx.runtimeEnv.HTTPS_PROXY, fx.proxyUrl);
		assert.equal(fx.runtimeEnv.DENO_CERT, fx.ca);
		assert.equal(fx.env.NO_PROXY, '127.0.0.1,localhost,::1');
		const script = path.join(dir, 'client.mjs');
		writeFileSync(script, [
			"for (const url of ['https://api.example.com/2.2/questions/1?site=x', 'http://api.example.com/plain', 'https://not-served.test/']) {",
			"  console.log(await fetch(url).then(r => r.text(), e => 'failed: ' + String(e.cause?.message ?? e.message)));",
			'}',
		].join('\n'));
		const {code, out} = await run([script], fx.env);
		assert.equal(code, 0, out);
		const lines = out.split('\n');
		assert.equal(lines[0], '{"meant":"https://api.example.com/2.2/questions/1?site=x"}');
		assert.equal(lines[1], '{"meant":"http://api.example.com/plain"}');
		// A host the certificate does not name fails TLS; it never leaves the machine.
		assert.match(lines[2], /^failed: /);
		assert.deepEqual(fx.seen.slice(0, 2), ['GET https://api.example.com/2.2/questions/1?site=x', 'GET http://api.example.com/plain']);
	} finally {
		await fx.close();
		rmSync(dir, {recursive: true, force: true});
	}
});

test('the guard alone refuses a direct request', {skip: !hasOpenssl && 'no OpenSSL 3'}, async () => {
	const dir = mkdtempSync(path.join(os.tmpdir(), 'hf-'));
	const fx = await startHostFixture({hosts: ['api.example.com'], dir: path.join(dir, 'tls'), handle: (u, q, r) => r.end()});
	try {
		const script = path.join(dir, 'direct.mjs');
		writeFileSync(script, "console.log(await fetch('http://direct.invalid/').then(r => r.status, e => String(e.cause?.message ?? e.message)));\n");
		const {out} = await run([script], {NODE_OPTIONS: fx.env.NODE_OPTIONS.split(' --require')[0], HTTP_PROXY: '', http_proxy: ''});
		assert.match(out, /wiki-verify guard: refused a connection to direct\.invalid:80/);
	} finally {
		await fx.close();
		rmSync(dir, {recursive: true, force: true});
	}
});
