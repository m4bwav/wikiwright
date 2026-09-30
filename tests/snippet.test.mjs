// Tests for snippet() in skills/wikiwright/templates/npm/wiki-verify.template.mjs. Run from the repository root:
//   node --test tests/snippet.test.mjs
// The template is a whole script, so the test lifts run() and the page-examples section out of it into a module in
// a temporary folder beside a tiny local package. Nothing is installed and nothing leaves the machine.
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
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
// A stand-in for a TypeScript compiler in node_modules/<folder>: its exports map hides ./bin/tsc, as 7.0.2's does
// (L-141); its tsc prints `checked <file>` for --noEmit and otherwise copies the file into --outDir as what tsc emits.
const standInTsc = (folder, version) => ({
	[`node_modules/${folder}/package.json`]: JSON.stringify({name: 'typescript', version, exports: {'.': './lib.cjs', './package.json': './package.json'}}),
	[`node_modules/${folder}/lib.cjs`]: '',
	[`node_modules/${folder}/bin/tsc`]: [
		"const {copyFileSync, mkdirSync} = require('node:fs');",
		"const path = require('node:path');",
		'const args = process.argv.slice(2);',
		'const file = args.at(-1);',
		"if (args.includes('--noEmit')) {",
		"	console.log('checked ' + path.basename(file));",
		'	process.exit(0);',
		'}',
		"const out = args[args.indexOf('--outDir') + 1];",
		"const ext = path.extname(file);",
		'mkdirSync(out, {recursive: true});',
		"copyFileSync(file, path.join(out, path.basename(file, ext) + {'.mts': '.mjs', '.cts': '.cjs', '.ts': '.js'}[ext]));",
		'',
	].join('\n'),
});
const files = {
	'node_modules/tiny/package.json': JSON.stringify({name: 'tiny', exports: {import: './index.mjs', require: './index.cjs'}}),
	'node_modules/tiny/index.mjs': "export const greet = name => 'hello ' + name;\n",
	'node_modules/tiny/index.cjs': "exports.greet = name => 'hello ' + name;\n",
	// An old version of tiny, installed in its own folder as OLD is.
	'old/node_modules/tiny/package.json': JSON.stringify({name: 'tiny', exports: {import: './index.mjs', require: './index.cjs'}}),
	'old/node_modules/tiny/index.mjs': "export const greet = name => 'hi ' + name;\n",
	'old/node_modules/tiny/index.cjs': "exports.greet = name => 'hi ' + name;\n",
	'preload.mjs': 'globalThis.preloaded = true;\n',
	...standInTsc('typescript', '7.0.0-stand-in'),
	...standInTsc('typescript6', '6.0.0-stand-in'),
	'tree/.keep': '',
	'helper.mjs': [
		"import {spawn} from 'node:child_process';",
		"import {createRequire} from 'node:module';",
		"import path from 'node:path';",
		"import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';",
		'const require = createRequire(import.meta.url);',
		'const show = (label, value) => console.log(`## ${label}' + BS + 'n${value}' + BS + 'n`);',
		runCode,
		section,
		'export {SNIPPET, prints, run, runSnippet, snippet};',
		'',
	].join('\n'),
};
for (const [name, text] of Object.entries(files)) {
	mkdirSync(path.dirname(path.join(dir, name)), {recursive: true});
	writeFileSync(path.join(dir, name), text);
}

process.chdir(dir);
const {prints, run, runSnippet} = await import(pathToFileURL(path.join(dir, 'helper.mjs')).href);

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
	assert.equal(out, 'tsc 7.0.0-stand-in: exit 0\nhello types');
});

test('the TypeScript matrix: the extension, the compiler folder and --noEmit', async () => {
	// Item 5 of the eighth run: .cts and .ts, a compiler installed under an alias, a type-check-only setup.
	const cts = await runSnippet('ts: cts', `
const {greet} = require('tiny');

console.log(greet('cts'));
`, {type: 'typescript', ext: '.cts', typescript: 'typescript6'});
	assert.equal(cts, 'tsc 6.0.0-stand-in: exit 0\nhello cts');
	assert.ok(readFileSync(path.join(dir, 'snippets', 'tsc', 'ts-cts.cjs'), 'utf8').includes("greet('cts')"));
	const ts = await runSnippet('ts: plain', `
const {greet} = require('tiny');

console.log(greet('ts'));
`, {type: 'typescript', ext: '.ts'});
	assert.equal(ts, 'tsc 7.0.0-stand-in: exit 0\nhello ts');
	const checked = await runSnippet('ts: check only', `
import {greet} from 'tiny';
`, {type: 'typescript', typescript: 'typescript6', tsc: ['--noEmit']});
	assert.equal(checked, 'tsc 6.0.0-stand-in: exit 0\nchecked ts-check-only.mts');
});

test('dir runs the same page text against the old version installed in another folder', async () => {
	// Item 4 of the eighth run: the page's own import resolves from the folder the file is written to.
	const page = `
import {greet} from 'tiny';

console.log(greet('page'));
`;
	assert.equal(await runSnippet('versions', page), 'hello page');
	assert.equal(await runSnippet('versions', page, {dir: path.join(dir, 'old', 'snippets')}), 'hi page');
	assert.equal(await runSnippet('versions ts', page, {type: 'typescript', dir: path.join(dir, 'old', 'snippets')}), 'tsc 7.0.0-stand-in: exit 0\nhi page');
	assert.ok(readFileSync(path.join(dir, 'old', 'snippets', 'tsc', 'versions-ts.mjs'), 'utf8'));
});

test('the OLDEST_NODE npx call is one command string with shell: true, which prints no DEP0190', () => {
	// Item 8 of the eighth run: an args array beside shell: true prints DEP0190 on Node 24.
	const call = template.slice(template.indexOf('const found = OLDEST_NODE_BIN'));
	assert.match(call.split('\n')[0], /run\(`npx -y -p node@\$\{OLDEST_NODE\} node -p process\.execPath`, \[\], \{shell: true,/);
	const stderrOf = form => spawnSync(process.execPath, ['--input-type=module', '-e', `
const {run} = await import(${JSON.stringify(pathToFileURL(path.join(dir, 'helper.mjs')).href)});
const result = await run(${form});
console.log(result.stdout.trim());
`], {cwd: dir, encoding: 'utf8'});
	const plain = stderrOf("'node -p 6*7', [], {shell: true}");
	assert.equal(plain.stdout.trim(), '42');
	assert.doesNotMatch(plain.stderr, /DEP0190/);
	if (Number(process.versions.node.split('.')[0]) >= 24) {
		// The control: the form the template used before does print it, so the check above can fail.
		assert.match(stderrOf("'node', ['-p', '6*7'], {shell: true}").stderr, /DEP0190/);
	}
});

test('stderr and a non-zero exit are printed after stdout', async () => {
	const out = await runSnippet('fails', `
console.log('before the error');
process.exitCode = 3;
console.error('went wrong');
`);
	assert.equal(out, 'before the error\n--- stderr\nwent wrong\nexit 3');
});
