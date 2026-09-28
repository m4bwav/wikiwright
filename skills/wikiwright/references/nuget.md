# NuGet packages: survey and verification

## Registry facts for the survey

nuget.org's JSON API, with `curl --compressed` (the registration index is served gzip-encoded; without the flag the body is gzip bytes). Package ids are lower case in these URLs.

```sh
curl -s --compressed https://api.nuget.org/v3/registration5-gz-semver2/ID/index.json   # versions, listed, published dates, dependency groups
curl -s https://api.nuget.org/v3-flatcontainer/ID/index.json                          # every version
curl -sO https://api.nuget.org/v3-flatcontainer/ID/VERSION/ID.VERSION.nupkg              # the package; unzip -l shows lib/ folders, README, icon
curl -s "https://azuresearch-usnc.nuget.org/query?q=packageid:ID&prerelease=true"      # totalDownloads and per-version downloads
```

Record sizes, target frameworks, dependencies per framework, the listed versions with dates and the downloads, each with the date read.

## The verification program

A .NET 10 file-based app from [../templates/nuget/wiki-verify.template.cs](../templates/nuget/wiki-verify.template.cs), in a folder outside any project cone:

```sh
dotnet run wiki-verify.cs
```

- `#:package ID@VERSION` pins the published package, so the working tree cannot leak in.
- `#:property PublishAot=false` is required whenever reflection runs: .NET 10 file-based apps enable native AOT by default, and reflection-based System.Text.Json then throws `InvalidOperationException: Reflection-based serialization has been disabled` even under `dotnet run` (learn.microsoft.com/dotnet/core/sdk/file-based-apps).
- Two runs of the same file at once contend for its build output. Use separate folders, or `dotnet build` once and then `dotnet run --no-build`.
- A file-based app picks up `Directory.Build.props` and `global.json` from parent folders; the scratchpad avoids both.

Where the wiki shows other languages or hosts, run them too:

- F#: `dotnet fsi script.fsx` with `#r "nuget: ID, VERSION"`.
- PowerShell 7: `Add-Type -Path <the DLL from the nupkg's lib/netX folder>`; note the PowerShell and .NET versions on the page.
- .NET Framework: a net48 project when the package targets netstandard2.0 and the page makes a claim about Framework behaviour (thread safety, `Random` seeding).
- Unity, Xamarin and other hosts that were not run: say "not tested" on the page.

## Traps

- `curl` of `registration5-gz-semver2` needs `--compressed`.
- `dotnet fsi` caches `#r "nuget:"` packages under the user's NuGet folder; a republished version with the same number would need a cache clear (NuGet never republishes a version, so this bites only local feeds).
- An `init`-only property can still be assigned from PowerShell 7 after `::new()`; F# sets it with named arguments on the constructor (`Options(IndentSize = 2)`).

Related: builds on [../SKILL.md](../SKILL.md); see also [page-sets.md](page-sets.md), [npm.md](npm.md).
