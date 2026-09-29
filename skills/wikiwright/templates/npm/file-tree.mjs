// file-tree: a fresh scratch copy of a fixture tree for every case of a package whose output is files on disk
// (a formatter, a code generator, a renamer), so no case sees another's rewrite and nothing touches the
// repository or the user's files (wikiwright L-130 `file-writing-package`, references/npm.md "Packages that
// write files"). Copy this file beside wiki-verify.mjs, in the scratch project and in the repository's
// ai-docs/notes/ (as <date>-file-tree.mjs).
//
//   import {treeCase} from './file-tree.mjs';
//   show('commands: a folder', await treeCase({
//     'data/a.json': '{"a":1}',                           // a string is written as UTF-8
//     'data/bom.json': '\uFEFF{"a":1}',                   // a BOM, CRLF, anything: the string's exact bytes
//     'data/latin1.json': Buffer.from([0x22, 0xe9, 0x22]), // raw bytes
//     'data/locked.json': {content: '{"a":1}', readonly: true},
//     'data/link.json': {symlink: 'a.json'},              // a file link ('dir' or 'junction' with type)
//     'empty': {dir: true},
//   }, ({root, at}) => cli('data', {cwd: root})));       // or run(), shell(), or the library in-process
//
// A spec may also be the path of a folder to copy (a repository's fixtures), or a function that builds the tree
// in the root it is given. Every file gets a fixed modification time first, so a rewrite that keeps the bytes
// still shows. After the case it prints what the case returned (a string as is, anything else as JSON), then one
// line per file: `not written`, `written, same bytes`, `changed`, `created` or `deleted`, and then the before and
// after contents of each file that was written, each under a header that names what the text cannot show:
// its size, the BOM, the line endings and the final newline (`--- data/a.json after: 18 bytes, UTF-8, LF, no
// final newline`). The contents print with CR and the BOM removed, so a page's code block matches them; bytes
// that are not UTF-8 print as \xNN. The tree's absolute path prints as <tree>.
// Options: {chdir: true} runs the case with the tree as the working directory (for the library with relative
// paths); {show: ['x.json']} prints those files' contents even when not written; {keep: true} keeps the tree.
// Windows without developer mode refuses file symbolic links (EPERM): the output lists them as unavailable. A
// read-only file stays writable for root on Linux and macOS, so its case proves nothing under sudo.
import {
	chmodSync,
	cpSync,
	lstatSync,
	mkdirSync,
	mkdtempSync,
	readdirSync,
	readFileSync,
	readlinkSync,
	rmSync,
	symlinkSync,
	utimesSync,
	writeFileSync,
} from 'node:fs';
import path from 'node:path';

const FIXED_TIME = new Date('2001-01-01T00:00:00Z');
let counter = 0;

function build(root, spec) {
	const unavailable = [];
	if (typeof spec === 'string') {
		cpSync(spec, root, {recursive: true, verbatimSymlinks: true});
		return unavailable;
	}

	for (const [relative, value] of Object.entries(spec)) {
		const file = path.join(root, ...relative.split('/'));
		mkdirSync(path.dirname(file), {recursive: true});
		if (typeof value === 'string' || value instanceof Uint8Array) {
			writeFileSync(file, value);
		} else if (value.dir) {
			mkdirSync(file, {recursive: true});
		} else if (value.symlink) {
			try {
				symlinkSync(value.symlink, file, value.type ?? 'file');
			} catch (error) {
				unavailable.push(`${relative} (${error.code})`);
			}
		} else {
			writeFileSync(file, value.content);
			if (value.readonly) {
				chmodSync(file, 0o444);
			}
		}
	}

	return unavailable;
}

// Every entry under root: relative path with '/', and its kind, bytes and time.
function snapshot(root) {
	const entries = new Map();
	const walk = directory => {
		for (const name of readdirSync(directory).sort()) {
			const full = path.join(directory, name);
			const relative = path.relative(root, full).split(path.sep).join('/');
			const stat = lstatSync(full);
			if (stat.isSymbolicLink()) {
				entries.set(relative, {kind: 'link', target: readlinkSync(full)});
			} else if (stat.isDirectory()) {
				entries.set(relative, {kind: 'dir'});
				walk(full);
			} else {
				entries.set(relative, {kind: 'file', bytes: readFileSync(full), mtime: stat.mtimeMs, mode: stat.mode});
			}
		}
	};

	walk(root);
	return entries;
}

function settle(root, entries) {
	for (const [relative, entry] of entries) {
		if (entry.kind === 'file') {
			utimesSync(path.join(root, ...relative.split('/')), FIXED_TIME, FIXED_TIME);
			entry.mtime = lstatSync(path.join(root, ...relative.split('/'))).mtimeMs;
		}
	}
}

/**
The facts about a file's bytes that its text cannot show: `18 bytes, UTF-8, BOM, CRLF, final newline`.
*/
export function describeBytes(bytes) {
	const facts = [`${bytes.length} ${bytes.length === 1 ? 'byte' : 'bytes'}`];
	let utf8 = true;
	try {
		new TextDecoder('utf-8', {fatal: true}).decode(bytes);
	} catch {
		utf8 = false;
	}

	facts.push(utf8 ? 'UTF-8' : 'not UTF-8');
	if (bytes[0] === 0xEF && bytes[1] === 0xBB && bytes[2] === 0xBF) {
		facts.push('BOM');
	} else if ((bytes[0] === 0xFF && bytes[1] === 0xFE) || (bytes[0] === 0xFE && bytes[1] === 0xFF)) {
		facts.push('UTF-16 BOM');
	}

	const text = bytes.toString('latin1');
	const crlf = (text.match(/\r\n/g) ?? []).length;
	const lf = (text.match(/\n/g) ?? []).length - crlf;
	const cr = (text.match(/\r(?!\n)/g) ?? []).length;
	const kinds = [crlf && 'CRLF', lf && 'LF', cr && 'CR'].filter(Boolean);
	if (kinds.length === 0) {
		facts.push('no line breaks');
	} else {
		facts.push(kinds.length === 1 ? kinds[0] : `mixed line breaks (${crlf} CRLF, ${lf} LF, ${cr} CR)`);
		facts.push(/[\r\n]$/.test(text) ? 'final newline' : 'no final newline');
	}

	return facts.join(', ');
}

/**
The text of a file as a page shows it: CR and a UTF-8 BOM removed, bytes that are not UTF-8 as \xNN.
*/
export function showBytes(bytes) {
	let body = bytes;
	if (body[0] === 0xEF && body[1] === 0xBB && body[2] === 0xBF) {
		body = body.subarray(3);
	}

	let text;
	try {
		text = new TextDecoder('utf-8', {fatal: true}).decode(body);
	} catch {
		text = '';
		for (let i = 0; i < body.length;) {
			const size = body[i] < 0x80 ? 1 : body[i] >= 0xF0 ? 4 : body[i] >= 0xE0 ? 3 : body[i] >= 0xC2 ? 2 : 0;
			let char;
			if (size > 0) {
				try {
					char = new TextDecoder('utf-8', {fatal: true}).decode(body.subarray(i, i + size));
				} catch {}
			}

			if (char === undefined) {
				text += `\\x${body[i].toString(16).toUpperCase().padStart(2, '0')}`;
				i++;
			} else {
				text += char;
				i += size;
			}
		}
	}

	return text.replaceAll('\r\n', '\n').replaceAll('\r', '\n');
}

function stringify(value) {
	return typeof value === 'string' ? value : JSON.stringify(value, (key, v) => {
		if (v === undefined) {
			return '<undefined>';
		}

		if (v instanceof Error) {
			return {name: v.name, message: v.message, ...v};
		}

		return v;
	}, 2);
}

/**
Builds a fresh tree from `spec` in a new folder under `base` (default: `trees` beside the calling script's working
directory), runs `fn({root, at})`, and returns the printout described at the top of this file.
*/
export async function treeCase(spec, fn, {base = 'trees', chdir = false, show = [], keep = false} = {}) {
	mkdirSync(base, {recursive: true});
	const root = mkdtempSync(path.join(path.resolve(base), `t${++counter}-`));
	const at = relative => path.join(root, ...relative.split('/'));
	const unavailable = typeof spec === 'function' ? (await spec(root), []) : build(root, spec);
	const before = snapshot(root);
	settle(root, before);
	const previous = process.cwd();
	let result;
	try {
		if (chdir) {
			process.chdir(root);
		}

		result = await fn({root, at});
	} catch (error) {
		result = `${error?.name}: ${error?.message}`;
	} finally {
		process.chdir(previous);
	}

	const after = snapshot(root);
	const lines = [];
	if (result !== undefined) {
		lines.push(stringify(result));
	}

	if (unavailable.length > 0) {
		lines.push(`--- unavailable: ${unavailable.join(', ')}`);
	}

	lines.push('--- files');
	const contents = [];
	const names = [...new Set([...before.keys(), ...after.keys()])].sort();
	for (const name of names) {
		const old = before.get(name);
		const now = after.get(name);
		if (old?.kind === 'dir' || now?.kind === 'dir') {
			if (!old || !now) {
				lines.push(`${name}/: ${old ? 'deleted' : 'created'} (folder)`);
			}

			continue;
		}

		if (old?.kind === 'link' || now?.kind === 'link') {
			const state = !now ? 'deleted' : !old ? 'created' : old.target === now.target ? 'not written' : 'changed';
			lines.push(`${name}: ${state} (symbolic link to ${(now ?? old).target})`);
			continue;
		}

		let state;
		if (!old) {
			state = 'created';
		} else if (!now) {
			state = 'deleted';
		} else if (!old.bytes.equals(now.bytes)) {
			state = 'changed';
		} else {
			state = old.mtime === now.mtime ? 'not written' : 'written, same bytes';
		}

		const readonly = (now ?? old).mode !== undefined && ((now ?? old).mode & 0o222) === 0 ? ' (read-only)' : '';
		lines.push(`${name}: ${state}${readonly}`);
		const written = state === 'changed' || state === 'created' || state === 'deleted';
		if (written || show.includes(name)) {
			if (old) {
				contents.push(`--- ${name} before: ${describeBytes(old.bytes)}`, showBytes(old.bytes));
			}

			if (now && written) {
				contents.push(`--- ${name} after: ${describeBytes(now.bytes)}`, showBytes(now.bytes));
			}
		}
	}

	if (!keep) {
		for (const [name, entry] of after) {
			if (entry.kind === 'file' && (entry.mode & 0o222) === 0) {
				chmodSync(at(name), 0o666);
			}
		}

		rmSync(root, {recursive: true, force: true});
	}

	const text = [...lines, ...contents].join('\n');
	// The tree's path as the case printed it, with either separator, and relative to the working directory.
	return [root, root.split(path.sep).join('/'), path.relative(previous, root)]
		.filter(form => form.length > 0)
		.reduce((out, form) => out.replaceAll(form, '<tree>'), text);
}
