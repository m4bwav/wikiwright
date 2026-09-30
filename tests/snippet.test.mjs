// Tests for snippet() in skills/wikiwright/templates/npm/wiki-verify.template.mjs. Run from the repository root:
//   node --test tests/snippet.test.mjs
// The template is a whole script, so the test lifts run() and the page-examples section out of it into a module in
// a temporary folder beside a tiny local package. Nothing is installed and nothing leaves the machine.
import assert from 'node:assert/strict';
import {mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {test} from 'node:test';
import {fileURLToPath, pathToFileURL} from 'node:url';

const BS = String.fromCharCode(92);
const template = readFileSync(fileURLToPath(new URL('../skills/wikiwright/templates/npm/wiki-verify.template.mjs', import.meta.url)), 'utf8');
const runStart = template.indexOf('function run(');
const runCode = template.slice(runStart, template.indexOf('\n}\n', runStart) + 3);
const section = template.slice(template.indexOf('// ----- page examples'), template.indexOf('// ----- end of page examples -----'));

const dir = mkdtempSync(path.join(os.tmpdir(), 'snip-'));
test.after(() => {
	process.chdir(os.tmpdir());
	rmSync(dir, {recursive: true, force: true});
});
const files = {
	'node_modules/tiny/package.json': JSON.stringify({name: 'tiny', exports: {import: './index.mjs', require: './index.cjs'}}),
	'node_modules/tiny/index.mjs': "export const greet = name => 'hello ' + name;\n",
	'node_modules/tiny/index.cjs': "exports.greet = name => 'hello ' + name;\n",
	'preload.mjs': 'globalThis.preloaded = true;\n',
	// A stand-in for TypeScript 7: its exports map hides ./bin/tsc, as 7.0.2's does (L-141), and its tsc copies the
	// .mts it is given into --outDir as .mjs.
	'node_modules/typescript/package.json': JSON.stringify({name: 'typescript', version: '7.0.0-stand-in', exports: {'.': './lib.cjs', './package.json': './package.json'}}),
	'node_modules/typescript/lib.cjs': '',
	'node_modules/typescript/bin/tsc': [
		"const {copyFileSync, mkdirSync} = require('node:fs');",
		"const path = require('node:path');",
		'const args = process.argv.slice(2);',
		"const out = args[args.indexOf('--outDir') + 1];",
		'const file = args.at(-1);',
		'mkdirSync(out, {recursive: true});',
		"copyFileSync(file, path.join(out, path.basename(file, '.mts') + '.mjs'));",
		'',
	].join('\n'),
	'tree/.keep': '',
	'helper.mjs': [
		"import {spawn} from 'node:child_process';",
		"import {createRequire} from 'node:module';",
		"import path from 'node:path';",
		"import {mkdirSync, writeFileSync} from 'node:fs';",
		'const require = createRequire(import.meta.url);',
		'const show = (label, value) => console.log(`## ${label}' + BS + 'n${value}' + BS + 'n`);',
		runCode,
		section,
		'export {SNIPPET, prints, runSnippet, snippet};',
		'',
	].join('\n'),
};
for (const [name, text] of Object.entries(files)) {
	mkdirSync(path.dirname(path.join(dir, name)), {recursive: true});
	writeFileSync(path.join(dir, name), text);
}

process.chdir(dir);
const {prints, runSnippet} = await import(pathToFileURL(path.join(dir, 'helper.mjs')).href);

test('an ES module snippet with a backtick, ${ and a backslash runs as the page shows it', async () => {
	// The escaping rule: \\ for a backslash, \` for a backtick, \${ for ${ inside the template literal.
	const out = await runSnippet('esm: escapes', `
import {greet} from 'tiny';

const name = 'wiki';
console.log(\`\${greet(name)}\`, /\\d+/.test('42'));
`);
	assert.equal(out, 'hello wiki true');
	const page = "import {greet} from 'tiny';\n\nconst name = 'wiki';\nconsole.log(`${greet(name)}`, /" + BS + "d+/.test('42'));\n";
	assert.equal(readFileSync(path.join(dir, 'snippets', 'esm-escapes.mjs'), 'utf8'), page);
});

test('a CommonJS snippet prints each //=> statement as the REPL would, one line or several', async () => {
	const out = await runSnippet('cjs: arrows', `
const {greet} = require('tiny');

greet('a');
//=> 'hello a'

greet(
  'b',
);
//=> 'hello b'

const kept = greet('c');
//=> not printed: a declaration
`, {type: 'commonjs'});
	assert.equal(out, "'hello a'\n'hello b'");
	assert.equal(prints("x;\n//=> 1\ny;\n"), "console.log('%O', x);\n//=> 1\ny;\n");
});

test('before, after, replace, env, cwd and Node flags reach the child', async () => {
	const out = await runSnippet('options', `
console.log(greet('https://example.com/'), process.env.WW_SNIPPET, globalThis.preloaded, path.basename(process.cwd()));
`, {
		before: "import {greet} from 'tiny';\nimport path from 'node:path';\n",
		after: "console.log('after');\n",
		replace: {'https://example.com': 'http://127.0.0.1:1'},
		env: {WW_SNIPPET: 'env'},
		cwd: path.join(dir, 'tree'),
		args: ['--import', pathToFileURL(path.join(dir, 'preload.mjs')).href],
	});
	assert.equal(out, 'hello http://127.0.0.1:1/ env true tree\nafter');
});

test('a TypeScript snippet is compiled by the tsc the exports map hides, then run', async () => {
	const out = await runSnippet('ts: greet', `
import {greet} from 'tiny';

console.log(greet('types'));
`, {type: 'typescript'});
	assert.equal(out, 'tsc: exit 0\nhello types');
});

test('stderr and a non-zero exit are printed after stdout', async () => {
	const out = await runSnippet('fails', `
console.log('before the error');
process.exitCode = 3;
console.error('went wrong');
`);
	assert.equal(out, 'before the error\n--- stderr\nwent wrong\nexit 3');
});
