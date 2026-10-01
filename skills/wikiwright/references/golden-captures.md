# Golden captures

Read this when the repository keeps golden captures of old versions (npm `test/golden/`, NuGet `tests/Golden/`): they feed Versions and upgrading.

A repository modernized with package-modernize, or any repository that recorded an old version's behaviour (`test/golden/`, a capture script beside a JSON file), hands Versions and upgrading its best evidence (L-020 `replay-the-golden-capture`):

1. Install the old version from the registry into its own scratch folder and run its capture script there. Compare the result with the golden file case by case. Identical means the recording still stands in for the old version.
2. Run the same capture script against the current published version, changing only what must change (a dependency's version line), and compare again. The differing cases and changed quirks are the upgrade notes; each should match a CHANGELOG entry, and one that does not is a finding.
3. Run any capture of the current version (`capture-2.0.0.cjs`) against the published build.
4. Put the counts and the differing cases on the page. Only read the golden files, never rewrite them.

On seeded-random-utilities: 1.1.4 today matched its recording in 322 of 322 cases, 2.0.0 in 316 (the six were the documented emoji exception), and 2.0.0 its own recording in 150 of 150.

How to compare, for every capture:

- By parsed value, never by bytes. A capture written before package-modernize's template changed holds raw UTF-8, and the current template writes ASCII escapes (`\u00e9`), so the same answer can differ byte for byte.
- Leave the header out (`captured`, the date, and `node`, the version it ran on), and compare `quirks` (the export shape, symbol and proxy cases) apart from the results, with its own count.
- Name each case in the report. Cases without names are reported by index and arguments together (`#37 (1, 'abc', null, 0)`), since an index alone would point at another case if one were ever inserted.

A synchronous capture, from a library that makes no requests, replays against the new major as it is: the same capture script and helpers, copied beside each installed version, with no patches. replace-string-at-position's `capture-1.0.4.cjs` (with `codec.cjs`, 2026-09-30): 1.0.4 today gave 71 of 71 results and 8 of 8 quirks the same; 2.0.0 gave 26 identical and 45 differing (13 now throw `RangeError` and 32 `TypeError`), `ownKeys` gained two exports, and every difference was a CHANGELOG line. The patches below, and the four changes in [npm-requests.md](npm-requests.md#golden-captures-that-record-through-a-proxy-with-tls), are for captures that make requests or write files.

A package that makes requests records its old version against a fixture server of its own (is-an-image-url's `capture-1.0.4.cjs` with `fixture-server.cjs` and `codec.cjs`, L-113 `replay-requesting-capture`). What that needs:

- Copy the capture script and every helper it requires beside each installed version, and install what the capture requires besides the package (is-an-image-url's needed `is-image` and an alias `is-image-300@npm:is-image@3.0.0`).
- Patch only what the new layout breaks, and say which lines on the page: the bin's path (`cli.js` became `dist/cli.mjs`) and a dependency lookup that fails when the new version has none.
- Run it as a child process, one version after the other: it starts its own server and has timing cases. It is a separate server from the wiki script's fixture; the wiki script only reads the JSON it prints.
- Compare three things apart: the answer (return, throw, callback arguments), the timing (callback before or after return) and the request lines. A changed default (asynchronous callbacks) otherwise hides the answer changes among timing changes.

A NuGet capture is a project (`tests/Golden/Capture`) that pins the old version in its `PackageReference` and writes one recording per runtime and OS (`1.0.2.net10.0-windows.json`, `1.0.2.net48-windows.json`). Copy the project to a scratch folder, change only the pinned version for the new one, build once, then run `dotnet run --no-build -f <tfm>` per framework as child processes, and compare each output with the recording for the same runtime and OS, answers and requests apart. The npm patches and the timing dimension above do not apply. Watch the Windows drive letter in file-path cases (the repository's golden test swaps it too), the ambient culture, and the obsolete-member warnings (CS0618, FS0044) the new version prints. On IsImageUrlDotNet, 1.0.2 today and 2.0.0's kept API each matched 117 of 117 answers and 117 of 117 requests on net10.0 (Windows and Linux) and on net48. package-modernize's NuGet capture template records only the method, arguments and result: in that view 1.0.2 on net48 differs from net10.0 in 10 cases, against 50 in the full recordings (L-011 `run-the-old-majors`).

On is-an-image-url: 1.0.4 today matched its recording in 82 of 82 calls and 11 of 11 CLI runs; 2.0.0 gave the same answer in 68, and each of the 14 differences and 5 request changes was a CHANGELOG line.

A capture that records through its own proxy with TLS (markdown-plain-link-replacer's `capture-1.1.16.cjs`, where request 2.88 honoured `HTTP_PROXY` and `HTTPS_PROXY`) replays unchanged against the old version (1.1.16 today: 154 of 154 calls, 18 of 18 CLI runs). Against a `fetch`-based new major it needs a proxy agent installed after the capture sets the variables and a fixture copy that serves tunnelled `http:` in plain HTTP; [npm-requests.md](npm-requests.md#golden-captures-that-record-through-a-proxy-with-tls) has the four changes. When a dependency's new major reads titles or names differently, mask that value and count the cases that differ only there apart: 55 of markdown-plain-link-replacer's 154 did, and the other 41 real differences were each a CHANGELOG line.

## The npm template's golden replay

The golden replay picks its comparator at run time from the golden file's shape. A flag could not: one `--golden` serves both formats package-modernize writes, and the scaffold never reads the repository.

- The synchronous format (unnamed cases with `results`, a header with `quirks`): cases are matched by index, method and encoded arguments. Results are compared by parsed value, never by bytes, since an older capture holds raw UTF-8 where the current capture template writes ASCII escapes. The header's `captured` and `node` are left out; its other fields and each quirk get a line of their own. It usually replays without a patch. For replace-string-at-position it printed 71 of 71 identical against 1.0.4 today. Against 2.0.0 it printed 26 identical and 45 differing (13 now throw RangeError, 32 TypeError), as the eighth run found by hand.
- The network format (named cases with `returned`, `threw`, `calls[].args`, `calls[].sync` and `requests`): answers, timing and requests are three views counted apart (L-113).
- A golden file compared as bytes fails on a capture that only changed its encoding: compare parsed values, as the template's golden replay does.

## Synchronous golden captures

The four changes in [npm-requests.md](npm-requests.md#golden-captures-that-record-through-a-proxy-with-tls) are for captures that make requests. A synchronous capture, which package-modernize writes for every library without requests (unnamed cases, `results`, `quirks`, and `calls` as a count), replays against the new major with no patches: copy the capture and the helpers it requires (`codec.cjs`) beside each installed version and run it as a child process, one version after the other. Compare the results by parsed value, case by case, with the header (`captured`, `node`) left out and `quirks` counted apart; report each differing case by index and arguments, since the cases have no names ("How to compare, for every capture", above). A byte comparison fails for no reason: the older capture holds raw UTF-8, and package-modernize's current template writes ASCII escapes, which changed the bytes of three emoji cases and none of their values.

replace-string-at-position (2026-09-30): 1.0.4 today gave 71 of 71 results the same as `capture-1.0.4.cjs` recorded, with 8 of 8 quirks; 2.0.0 gave 26 identical and 45 differing, and every difference was a CHANGELOG line. The V8 error messages in the 1.0.4 recording held on Node 20.20.2 and 24.18.0. package-modernize's current capture template would have changed four things in that capture (a `manifestPath()` lookup, ASCII escapes, an `async main()` wrapper with the proxy hook, `binPath()` and `dependency()` helpers), none of them needed for the replay.

Related: builds on [page-sets.md](page-sets.md); see also [npm.md](npm.md), [npm-requests.md](npm-requests.md), [nuget.md](nuget.md).
