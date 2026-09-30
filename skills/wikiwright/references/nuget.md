# NuGet packages: survey and verification

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

A .NET 10 file-based app from [../templates/nuget/wiki-verify.template.cs](../templates/nuget/wiki-verify.template.cs), in a folder outside any project cone:

```sh
dotnet run wiki-verify.cs
```

- `#:package ID@VERSION` pins the published package, so the working tree cannot leak in.
- `#:property PublishAot=false` is required whenever reflection runs: .NET 10 file-based apps enable native AOT by default, and reflection-based System.Text.Json then throws `InvalidOperationException: Reflection-based serialization has been disabled` even under `dotnet run` (learn.microsoft.com/dotnet/core/sdk/file-based-apps).
- Two runs of the same file at once contend for its build output. Use separate folders, or `dotnet build` once and then `dotnet run --no-build`.
- A file-based app picks up `Directory.Build.props` and `global.json` from parent folders; the scratchpad avoids both.
- `Console.WriteLine` writes CRLF on Windows. Save the output with LF (`tr -d '\r'`), so a run on Linux diffs clean (L-105 `csharp-verify-program`).
- Save the program as `ai-docs/notes/<date>-wiki-verify.cs` and its output beside it, as for npm. Two runs must be identical; a random value is printed only after a membership check (L-111 `membership-for-random`).

Where the wiki shows other languages or hosts, run them too, from the program, so their output is in the saved file (the template's `Run()` starts a process and returns its output with LF endings):

- F#: `dotnet fsi --quiet script.fsx` with `#r "nuget: ID, VERSION"`; the program writes the page's snippet to a temp `.fsx` first.
- PowerShell 7: `Add-Type -Path <the DLL from the nupkg's lib/netX folder>`; note the PowerShell and .NET versions on the page. `pwsh -NoProfile -NonInteractive -Command <the snippet>` runs it as written; after `dotnet run` restored the package, the DLL is in the NuGet cache path the page shows.
- .NET Framework: a net48 project when the package targets netstandard2.0 and the page makes a claim about Framework behaviour (thread safety, `Random` seeding).
- Unity, Xamarin and other hosts that were not run: say "not tested" on the page.

## How the pages show output

C#, F# and PowerShell have no REPL echo, so the NuGet wikis show values in comments. `wikiwright.py outputs` (0.3.0) reads a comment as output when it is quoted (`// "Marguerita"`, `// always "Alisa Streets"`), JSON-like (`// {"a":[1,2]}`), a number or literal, or when it follows a print call (`Console.WriteLine`, `printfn`) or a PowerShell expression (`[X]::LastNames.Count   # 88799`). A run of comment lines closing a code block after a blank line is that block's output, and so is an untagged block right after a code block. A bare word after any other call (`a.Next();  // Marguerita`) reads as an explanation: quote it or write `// => Marguerita`. Tag a command after a code block (```sh), or it reads as output (L-110 `outputs-in-comments`).

## Traps

- `curl` of `registration5-gz-semver2` needs `--compressed`.
- `dotnet fsi` caches `#r "nuget:"` packages under the user's NuGet folder; a republished version with the same number would need a cache clear (NuGet never republishes a version, so this bites only local feeds).
- An `init`-only property can still be assigned from PowerShell 7 after `::new()`; F# sets it with named arguments on the constructor (`Options(IndentSize = 2)`).

Related: builds on [../SKILL.md](../SKILL.md); see also [page-sets.md](page-sets.md), [npm.md](npm.md).
