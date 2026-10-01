# NuGet packages: survey and verification

Read this for every NuGet package; one that makes HTTP requests also takes [nuget-requests.md](nuget-requests.md).

## Registry facts for the survey

Start with the helper. It reads the registration index (gzip-decoded, paged indexes followed), the search service and the latest `.nupkg`, and prints one fact per line:

```sh
python scripts/wikiwright.py registry ID --nuget     # add --version X for an older package, --json for everything
```

It prints every version with its published date, listed or not, downloads, deprecation (reasons, message, alternate package) and vulnerabilities. For the latest version it prints the `.nupkg` size, the README and icon, the nuspec's license and repository commit, each `lib/` and `ref/` folder with its files, and the dependency groups per framework. The last line gives the time read. On 2026-09-29 it printed about 1.5 KB where the raw JSON and zip listing came to 13.7 KB (IsImageUrlDotNet) and 20.4 KB (JsonPrettyPrinter). Copy the numbers and the time read into the notes.

Without the helper, use nuget.org's JSON API with `curl --compressed`: the registration index is served gzip-encoded, and without the flag the body is gzip bytes. Ids are lower case in these URLs.

```sh
curl -s --compressed https://api.nuget.org/v3/registration5-gz-semver2/ID/index.json   # versions, listed, dates, deprecation, dependency groups
curl -s "https://azuresearch-usnc.nuget.org/query?q=packageid:ID&prerelease=true"      # downloads
curl -sO https://api.nuget.org/v3-flatcontainer/ID/VERSION/ID.VERSION.nupkg              # unzip -l: lib/ folders, README, icon
```

## The verification program

A .NET 10 file-based app from [../templates/nuget/wiki-verify.template.cs](../templates/nuget/wiki-verify.template.cs). Start with the helper, which writes the template filled in and cut to the sections the survey calls for, so the template is never read or cut by hand; then build and run it in a scratch folder outside any project cone:

```sh
python scripts/wikiwright.py scaffold nuget ID VERSION --namespace NS --type T -o <scratch>/wiki-verify.cs
dotnet build wiki-verify.cs && dotnet run --no-build wiki-verify.cs > out.txt
```

| Flag | Section | Add it when |
|---|---|---|
| (none) | core: `Show`, `Captured`, `Catch`, `Possible`, `Run`, `Mask`, `Installed`, the `installed` lines | always |
| `--children net48,net8.0` | children: the pages' examples as whole programs in child apps, one set per config, net10.0 always | an example declares types, prints type names, or touches process-global state, or the pages name another framework or a dependency range |
| `--requests` | requests: the stand-in proxy and the `.invalid` gate (keeps children) | the package makes HTTP requests ([nuget-requests.md](nuget-requests.md)) |
| `--fsharp` | fsharp: `Fsi()`, and with `--requests` the F# gate | the pages show F# |
| `--tool ID:COMMAND` | tool: install into scratch, list, uninstall, the package's files, `Term()`, `Fresh()`, `Listing()` | the repository ships a dotnet tool |

Measured 2026-10-01 against the 42,477-byte template: the core alone is 10,199 bytes, with `--fsharp` 10,883, with `--tool` 14,650, with `--children net48,net8.0` 22,833, with `--requests --children net48` 34,245, with every section 41,548.

- Build first: a plain first `dotnet run` prints its build warnings into the output.
- `#:package ID@VERSION` pins the published package, so the working tree cannot leak in.
- `#:property PublishAot=false` is required whenever reflection runs: .NET 10 file-based apps enable native AOT by default, and reflection-based System.Text.Json then throws `InvalidOperationException: Reflection-based serialization has been disabled` even under `dotnet run` (learn.microsoft.com/dotnet/core/sdk/file-based-apps).
- Two runs of the same file at once contend for its build output. Use separate folders, or `dotnet build` once and then `dotnet run --no-build`.
- A file-based app picks up `Directory.Build.props` and `global.json` from parent folders; the scratchpad avoids both.
- File-based apps build under `%TEMP%\dotnet\runfile` (`$TMPDIR/dotnet/runfile` on Linux), outside scratch, unless TEMP and TMP point into the scratch folder for the build and the run (2026-09-30). From Git Bash export them as `C:/...` paths: an unquoted `C:\...` loses its backslashes (2026-09-30).
- `Console.WriteLine` writes CRLF on Windows. Save the output with LF (`tr -d '\r'`), so a run on Linux diffs clean (L-105 `csharp-verify-program`).
- Save the program as `ai-docs/notes/<date>-wiki-verify.cs` and its output beside it, as for npm. Two runs must be identical; a random value is printed only after a membership check (L-111 `membership-for-random`).

What loaded: the `installed` section prints the runtime, the package and each assembly named in `dependencies`, with its informational version, its file version and the framework of the lib folder it loaded from, and every child prints the same for its config.

- Print each dependency's informational version, not its assembly version: Castle.Core is 5.0.0.0 in both 5.1.1 and 5.2.1 (2026-09-30). The file version is printed beside it because a build that never set an informational version reports 1.0.0 (FFMpegCore, file 5.0.0.0, 2026-10-01).
- `Assembly.Location` points at the child's `bin` folder, where the build copied the DLL, so it cannot say which lib folder NuGet chose; `TargetFrameworkAttribute` can (2026-09-30).
- When the package declares a dependency range (Autofac 6.5 to 9), run its ends: one children config per end, such as `new("net10.0", ["Autofac@9.3.4"])`, and scope any difference on the page by that version (2026-09-30).

The children section runs the pages' C# as the pages show it (2026-10-01, proved on CachingServiceWithAOPSupport 2.0.0 on net10.0, net8.0 and net48):

- Each example is a whole program: using lines, statements, then the types it declares. It becomes its own file in a child app (`#:include`, which SDK 10.0.401 supports), its statements wrapped in a method and its types kept global, so a type name the output prints is the page's (`Shelf;Find;...`, not `Ex9.Shelf`). Examples that declare the same type name go to separate child apps.
- Every example runs in its own process, so process-global state (`MemoryCache.Default`, a static field, a container) never carries over from one example to the next (2026-09-30).
- A config is a target framework and extra `#:` lines: `"Autofac@9.3.4"` becomes `#:package Autofac@9.3.4`, `"ID@1.0.1"` runs an old version, a line starting with `#:` passes through. `net48` runs .NET Framework 4.8 (Windows only) on the package's net4x or netstandard2.0 build, `net8.0` a netstandard2.0 build. Framework's exception messages and HTTP handler differ from .NET 10's; the output labels each case with its config.
- A page example that is a file-based app with its own `#:` lines runs as its own app with those lines, and only the config's lines it does not set itself are added. FFMpegCore's examples need the page's own `#:property PublishAot=false` (L-143 `page-app-own-directives`). An app that does not build prints its errors as the output.
- Children build without the proxy variables, so their restores reach nuget.org, also under `--requests`.

Where the wiki shows other languages or hosts, run them too, from the program, so their output is in the saved file. The template's `Run()` starts a process with optional environment and working folder, reads both streams at once, closes stdin at once (a child that would ask reads end of input) and returns the output with LF endings. `Mask()` hides local paths and ports, the regular expressions in `Masks.Patterns` (ffmpeg's `[mp3 @ 0x...]` heap addresses), and the extra pairs a call passes, such as a case's folder as `<cwd>`.

- F#: the template's `Fsi()` writes the page's snippet to `<scratch>/fsx/<name>.fsx` with LF endings and runs `dotnet fsi --quiet` on it. `#r "nuget: ID, VERSION"` restores when the script runs; a script that requests goes in the F# gate's section, whose warm-up restores first without the proxy variables. `Run()` trims the blank lines fsi pads its warnings with.
- PowerShell 7: `Add-Type -Path <the DLL from the nupkg's lib/netX folder>`; note the PowerShell and .NET versions on the page. `pwsh -NoProfile -NonInteractive -Command <the snippet>` runs it as written; after `dotnet run` restored the package, the DLL is in the NuGet cache path the page shows.
- A dotnet tool (`--tool ID:COMMAND`): installed with `dotnet tool install ID --version V --tool-path tools` in scratch, never `-g`, listed with `dotnet tool list --tool-path tools`, uninstalled from a second folder, and its package's files listed from `tools/.store`. Each command the pages show runs by name with that folder first on `PATH`, in a `Fresh()` folder masked as `<cwd>`, through `Term()`: `cmd /d /s /c` on Windows or `/bin/sh -c` elsewhere, stdin closed, printed as `$ command`, the merged output in the order written, `$ echo $?` and the exit code, like npm's `term()`. A command with an effect outside scratch (`--install-ffmpeg`) runs only through the tool's own seams, never with `--yes` (2026-10-01, proved on TrailerClipper.Tool 2.0.0: `tclipper -h`, and one clip of a 3-second `ffmpeg -f lavfi -i sine=d=3` tone).
- Linux in WSL: a user-level `dotnet-install.sh --install-dir <scratch>` needs `bash`, not `sh`. .NET stops at start without libicu. Set `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1` before the first `dotnet` call, since the SDK's own `dotnet --info` fails fast without it (2026-09-30); invariant mode changes culture-dependent answers, so say so on the page. `apt-get download libicu<N>` and `dpkg -x` into scratch, with its `usr/lib/<arch>` folder on `LD_LIBRARY_PATH`, avoid a system package, but the download asks the distribution's mirror, which a run's rules may forbid. Set a distinctive `TMPDIR`, or masking `/tmp` rewrites content such as `file:///tmp/a.png`.
- Unity, Xamarin and other hosts that were not run: say "not tested" on the page.

## How the pages show output

C#, F# and PowerShell have no REPL echo, so the NuGet wikis show values in comments. `wikiwright.py outputs` (0.3.0) reads a comment as output when it is quoted (`// "Marguerita"`, `// always "Alisa Streets"`), JSON-like (`// {"a":[1,2]}`), a number or literal, or when it follows a print call (`Console.WriteLine`, `printfn`) or a PowerShell expression (`[X]::LastNames.Count   # 88799`). A run of comment lines closing a code block after a blank line is that block's output, and so is an untagged block right after a code block. A bare word after any other call (`a.Next();  // Marguerita`) reads as an explanation: quote it or write `// => Marguerita`. Tag a command after a code block (```sh), or it reads as output (L-110 `outputs-in-comments`).

## Traps

- `curl` of `registration5-gz-semver2` needs `--compressed`.
- `dotnet fsi` keeps its resolution of each `#r "nuget:"` set in `~/.packagemanagement/nuget/Cache`, and the packages in the user's NuGet folder. A republished version with the same number would need both cleared (NuGet never republishes a version, so this bites only local feeds). While a cache entry exists fsi ignores `NUGET_PACKAGES` for that set.
- Windows 11 with Smart App Control on can refuse a freshly built program or child DLL ("An Application Control policy has blocked this file"). The gate fails closed and prints the message. Rebuilding the same bytes keeps the refusal; a build from another folder, or with any source change, gets new bytes (seen 2026-09-30). `#:property Deterministic=false` in the program, or as a children config's line, gives new bytes on every build; it cleared a refused Autofac 9.3.4 child and a refused program (2026-10-01).
- An `init`-only property can still be assigned from PowerShell 7 after `::new()`; F# sets it with named arguments on the constructor (`Options(IndentSize = 2)`).

Related: builds on [../SKILL.md](../SKILL.md); see also [nuget-requests.md](nuget-requests.md), [golden-captures.md](golden-captures.md), [page-sets.md](page-sets.md), [npm.md](npm.md).
