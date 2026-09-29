// Tests for skills/wikiwright/templates/npm/file-tree.mjs. Run from the repository root:
//   node --test tests/file-tree.test.mjs
// Every tree is built under the system temp folder and removed; nothing else is written.
import assert from 'node:assert/strict';
import {existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {test} from 'node:test';
import {describeBytes, showBytes, treeCase} from '../skills/wikiwright/templates/npm/file-tree.mjs';

const BOM = String.fromCharCode(0xFEFF);
const base = mkdtempSync(path.join(os.tmpdir(), 'ft-'));
test.after(() => rmSync(base, {recursive: true, force: true}));

test('describeBytes names the size, encoding, BOM, line endings and final newline', () => {
	assert.equal(describeBytes(Buffer.from('{"a":1}')), '7 bytes, UTF-8, no line breaks');
	assert.equal(describeBytes(Buffer.from(`${BOM}{\r\n"a":1\r\n}\r\n`)), '16 bytes, UTF-8, BOM, CRLF, final newline');
	assert.equal(describeBytes(Buffer.from('{\n"a":1\r\n}')), '10 bytes, UTF-8, mixed line breaks (1 CRLF, 1 LF, 0 CR), no final newline');
	assert.equal(describeBytes(Buffer.from([0x22, 0xE9, 0x22])), '3 bytes, not UTF-8, no line breaks');
	assert.equal(describeBytes(Buffer.from([0xFF, 0xFE, 0x7B, 0x00])), '4 bytes, not UTF-8, UTF-16 BOM, no line breaks');
});

test('showBytes drops CR and the BOM and shows bytes that are not UTF-8', () => {
	assert.equal(showBytes(Buffer.from(`${BOM}{\r\n"a":1\r\n}`)), '{\n"a":1\n}');
	assert.equal(showBytes(Buffer.from([0x22, 0x63, 0xE9, 0x22])), '"c' + String.fromCharCode(92) + 'xE9"');
	assert.equal(showBytes(Buffer.from('"é"')), '"é"');
});

test('a case reports every file by what happened to it, with before and after contents', async () => {
	const out = await treeCase({
		'a.json': '{"a":1}',
		'same.json': '{\n    "a": 1\n}',
		'untouched.json': '[]',
		'gone.json': '{}',
		'crlf.json': `${BOM}{\r\n"a":1\r\n}\r\n`,
		'sub/deep.json': '{"b":2}',
		'empty': {dir: true},
	}, ({at}) => {
		writeFileSync(at('a.json'), '{\n    "a": 1\n}');
		writeFileSync(at('same.json'), readFileSync(at('same.json')));
		writeFileSync(at('crlf.json'), '{\n    "a": 1\n}\n');
		writeFileSync(at('new.json'), '1');
		rmSync(at('gone.json'));
		return 'exit 0';
	}, {base});
	const lines = out.split('\n');
	assert.equal(lines[0], 'exit 0');
	assert.deepEqual(lines.slice(1, 10), [
		'--- files',
		'a.json: changed',
		'crlf.json: changed',
		'gone.json: deleted',
		'new.json: created',
		'same.json: written, same bytes',
		'sub/deep.json: not written',
		'untouched.json: not written',
		'--- a.json before: 7 bytes, UTF-8, no line breaks',
	]);
	assert.match(out, /--- a\.json after: 14 bytes, UTF-8, LF, no final newline\n\{\n {4}"a": 1\n\}/);
	assert.match(out, /--- crlf\.json before: 16 bytes, UTF-8, BOM, CRLF, final newline\n\{\n"a":1\n\}\n/);
	assert.match(out, /--- crlf\.json after: 15 bytes, UTF-8, LF, final newline/);
	assert.match(out, /--- gone\.json before: 2 bytes/);
	assert.match(out, /--- new.json after: 1 byte,/);
	assert.doesNotMatch(out, /same\.json (before|after)/);
	assert.doesNotMatch(out, /untouched\.json (before|after)/);
});

test('each case gets its own copy, and the tree is removed afterwards', async () => {
	let first;
	const spec = {'a.json': '{"a":1}'};
	await treeCase(spec, ({root, at}) => {
		first = root;
		writeFileSync(at('a.json'), 'changed');
	}, {base});
	assert.equal(existsSync(first), false);
	const out = await treeCase(spec, ({at}) => readFileSync(at('a.json'), 'utf8'), {base});
	assert.equal(out.split('\n')[0], '{"a":1}');
});

test('paths of the tree print as <tree>, and chdir runs the case inside it', async () => {
	const before = process.cwd();
	const out = await treeCase({'a.json': '1'}, ({root}) => [process.cwd() === root, root, root.split(path.sep).join('/'), `${root}${path.sep}a.json`].join(' | '), {base, chdir: true});
	assert.equal(process.cwd(), before);
	assert.equal(out.split('\n')[0], 'true | <tree> | <tree> | <tree>' + path.sep + 'a.json');
});

test('a thrown error is the case result, and show prints a file that was not written', async () => {
	const out = await treeCase({'a.json': '{"a":1}'}, () => {
		throw new TypeError('boom');
	}, {base, show: ['a.json']});
	assert.equal(out.split('\n')[0], 'TypeError: boom');
	assert.match(out, /a\.json: not written\n--- a\.json before: 7 bytes, UTF-8, no line breaks\n\{"a":1\}/);
});

test('a read-only file stays read-only in the case and is removed afterwards', async () => {
	let root;
	const out = await treeCase({'locked.json': {content: '{"a":1}', readonly: true}}, ({root: r, at}) => {
		root = r;
		try {
			writeFileSync(at('locked.json'), 'x');
			return 'written';
		} catch (error) {
			return error.code;
		}
	}, {base});
	const running = typeof process.getuid === 'function' && process.getuid() === 0;
	if (!running) {
		assert.match(out.split('\n')[0], /^(EPERM|EACCES)$/);
		assert.match(out, /locked\.json: not written \(read-only\)/);
	}

	assert.equal(existsSync(root), false);
});

test('a folder path as the spec is copied, and a function spec builds the tree', async () => {
	const source = path.join(base, 'fixture-src');
	mkdirSync(path.join(source, 'nested'), {recursive: true});
	writeFileSync(path.join(source, 'nested', 'x.json'), '[1]');
	const copied = await treeCase(source, ({at}) => readFileSync(at('nested/x.json'), 'utf8'), {base});
	assert.equal(copied.split('\n')[0], '[1]');
	assert.equal(readFileSync(path.join(source, 'nested', 'x.json'), 'utf8'), '[1]');
	const built = await treeCase(root => writeFileSync(path.join(root, 'y.json'), '2'), ({at}) => readFileSync(at('y.json'), 'utf8'), {base});
	assert.match(built, /^2\n--- files\ny\.json: not written$/);
});

test('hide leaves a folder out, limit cuts long contents, escaped paths print as <tree>', async () => {
	const out = await treeCase({'a.json': '1', '.git/HEAD': 'ref'}, ({root, at}) => {
		writeFileSync(at('.git/HEAD'), 'other');
		writeFileSync(at('big.json'), 'x'.repeat(50));
		return JSON.stringify(root);
	}, {base, hide: ['.git'], limit: 10});
	assert.doesNotMatch(out, /HEAD/);
	assert.match(out, /--- big\.json after: 50 bytes[^\n]*\nxxxxxxxxxx\n\.\.\. \(40 more characters\)/);
	assert.equal(out.split('\n')[0], '"<tree>"');
});

test('a hard link is a second name for the same file', async () => {
	const out = await treeCase({'a.json': '{"a":1}', 'b.json': {hardlink: 'a.json'}}, ({at}) => {
		writeFileSync(at('a.json'), '2');
	}, {base});
	assert.match(out, /a\.json: changed\nb\.json: changed/);
});

test('a folder mode is set for the case and restored for the removal', {skip: process.platform === 'win32' && 'Windows ignores folder modes'}, async () => {
	let root;
	const out = await treeCase({'locked/x.json': '1', 'locked': {dir: true, mode: 0o000}}, ({root: r, at}) => {
		root = r;
		try {
			readFileSync(at('locked/x.json'));
			return 'read';
		} catch (error) {
			return error.code;
		}
	}, {base});
	if (!(typeof process.getuid === 'function' && process.getuid() === 0)) {
		assert.equal(out.split('\n')[0], 'EACCES');
	}

	assert.equal(existsSync(root), false);
});

test('a symbolic link is listed as a link or as unavailable, never followed', async () => {
	const out = await treeCase({'a.json': '1', 'link.json': {symlink: 'a.json'}}, () => undefined, {base});
	if (out.includes('--- unavailable')) {
		assert.match(out, /--- unavailable: link\.json \(EPERM\)/);
	} else {
		assert.match(out, /link\.json: not written \(symbolic link to a\.json\)/);
	}
});
