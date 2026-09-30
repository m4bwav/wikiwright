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
dotnet build wiki-verify.cs && dotnet run --no-build wiki-verify.cs > out.txt
```

- Build first: a plain first `dotnet run` prints its build warnings into the output.
- `#:package ID@VERSION` pins the published package, so the working tree cannot leak in.
- `#:property PublishAot=false` is required whenever reflection runs: .NET 10 file-based apps enable native AOT by default, and reflection-based System.Text.Json then throws `InvalidOperationException: Reflection-based serialization has been disabled` even under `dotnet run` (learn.microsoft.com/dotnet/core/sdk/file-based-apps).
- Two runs of the same file at once contend for its build output. Use separate folders, or `dotnet build` once and then `dotnet run --no-build`.
- A file-based app picks up `Directory.Build.props` and `global.json` from parent folders; the scratchpad avoids both.
- `Console.WriteLine` writes CRLF on Windows. Save the output with LF (`tr -d '\r'`), so a run on Linux diffs clean (L-105 `csharp-verify-program`).
- Save the program as `ai-docs/notes/<date>-wiki-verify.cs` and its output beside it, as for npm. Two runs must be identical; a random value is printed only after a membership check (L-111 `membership-for-random`).

Where the wiki shows other languages or hosts, run them too, from the program, so their output is in the saved file. The template's `Run()` starts a process with optional environment and working folder, reads both streams at once and returns the output with LF endings; `Mask()` hides local paths and ports.

- F#: the template's `Fsi()` writes the page's snippet to `<scratch>/fsx/<name>.fsx` with LF endings and runs `dotnet fsi --quiet` on it. `#r "nuget: ID, VERSION"` restores when the script runs; a script that requests goes in the template's F# section, whose warm-up restores first without the proxy variables. `Run()` trims the blank lines fsi pads its warnings with.
- PowerShell 7: `Add-Type -Path <the DLL from the nupkg's lib/netX folder>`; note the PowerShell and .NET versions on the page. `pwsh -NoProfile -NonInteractive -Command <the snippet>` runs it as written; after `dotnet run` restored the package, the DLL is in the NuGet cache path the page shows.
- .NET Framework and older builds: a file-based app with `#:property TargetFramework=net48` runs on .NET Framework 4.8 (Windows only) and loads the package's net46x to net48 build. With `net8.0` it loads a netstandard2.0 build. The program writes such children and runs them, so one file covers every build the package ships. Framework's exception messages and HTTP handler differ from .NET 10's; label each output with its runtime.
- Linux in WSL: a user-level `dotnet-install.sh --install-dir <scratch>` needs `bash`, not `sh`. .NET stops at start without libicu: `apt-get download libicu<N>` and `dpkg -x` into scratch, with its `usr/lib/<arch>` folder on `LD_LIBRARY_PATH`, avoid a system package. Invariant globalization mode also starts, but it changes culture-dependent answers. Set a distinctive `TMPDIR`, or masking `/tmp` rewrites content such as `file:///tmp/a.png`.
- Unity, Xamarin and other hosts that were not run: say "not tested" on the page.

## Packages that make requests

The template's two `requests` blocks verify a package that makes HTTP requests without asking any real host; a package that makes none deletes them. First proved on IsImageUrlDotNet 2.0.0 on .NET 10 and .NET Framework 4.8 (2026-09-29).

- `StandIn` is a proxy on 127.0.0.1 that answers the `.test` host names in `routes` from fixed answers. It takes http as absolute-form requests, and https as CONNECT and then TLS with a throwaway certificate that only the test client `StandInClient()` trusts. It never opens a socket of its own and logs each request line with its host.
- It refuses every other host by answering: a reply that is not HTTP, or 403 to CONNECT. A stand-in that closes the connection makes HttpClient retry, 4 GETs or 16 CONNECTs per call on .NET 10 and 2 on .NET Framework (L-138 `refuse-by-answering`).
- The pages' request snippets run in child apps, one per build. .NET Core and .NET 5+ read `HTTP_PROXY` and `HTTPS_PROXY`. .NET Framework ignores them, so the Framework child sets `WebRequest.DefaultWebProxy` before any snippet, and since Framework never proxies a loopback address the routes use `.test` names, never 127.0.0.1 (L-137 `dotnet-request-route`).
- Restores run without the proxy variables: the children's builds, and `dotnet fsi` warmed with a script holding the `#r` line and a `printfn`. fsi resolves a script's `#r` and `#i` lines as one set and keeps the answer in `~/.packagemanagement/nuget/Cache/<hash>.fsx`. It never restores that set again. NuGet's own HTTP cache also answers a repeat download for 30 minutes. So only a set never resolved on the machine needs the network, and a page script with other `#r` lines needs its own warm-up. Without the warm-up that restore goes through the proxy (NuGet reads `HTTPS_PROXY`), meets the stand-in's 403s and fails the gate (tested 2026-09-30 with an empty `NUGET_PACKAGES` and `NUGET_HTTP_CACHE_PATH`).
- The gate comes before any case, on every route (each child, then fsi): the package's default client and a caller's `new HttpClient()` ask `http://gate.invalid/` and `https://gate.invalid/`, so 4 calls, or 2 when the call takes no client (`gateCalls`). `Gate()` checks every route alike: each call must throw, and the stand-in must log exactly that many requests, all to `gate.invalid`, or the program exits 1. A call missing from the log went around the stand-in, a repeated one was retried, and any other host is a restore that reached the stand-in. fsi reads `HTTP_PROXY` and `HTTPS_PROXY` as a .NET 10 child does: run without them, its gate throws 4 times, logs "stand-in: no request" and fails (tested 2026-09-30). The F# section is delimited; a run whose pages hold no F# that requests deletes it.
- An https route from F# is a harness row. It passes its own client, whose handler trusts the stand-in's thumbprint (the template's comment has the F# line). The default client refuses the throwaway certificate, as in C#.
- Pages show the `.test` names or say the stand-in answered, and the real hosts are never asked (L-116 `by-host-name-proxy`, L-122 `sample-content-not-live`). An https row that needed `StandInClient()` says so.
- Requests sent at once arrive in any order: sort their log lines, or print one call per snippet.
- Check the pages with `wikiwright.py outputs --address ''`. The default treats `https://example.com` on a page as the fixture's `127.0.0.1` address, the npm kit's convention, which a `.test` route does not use.

## How the pages show output

C#, F# and PowerShell have no REPL echo, so the NuGet wikis show values in comments. `wikiwright.py outputs` (0.3.0) reads a comment as output when it is quoted (`// "Marguerita"`, `// always "Alisa Streets"`), JSON-like (`// {"a":[1,2]}`), a number or literal, or when it follows a print call (`Console.WriteLine`, `printfn`) or a PowerShell expression (`[X]::LastNames.Count   # 88799`). A run of comment lines closing a code block after a blank line is that block's output, and so is an untagged block right after a code block. A bare word after any other call (`a.Next();  // Marguerita`) reads as an explanation: quote it or write `// => Marguerita`. Tag a command after a code block (```sh), or it reads as output (L-110 `outputs-in-comments`).

## Traps

- `curl` of `registration5-gz-semver2` needs `--compressed`.
- `dotnet fsi` keeps its resolution of each `#r "nuget:"` set in `~/.packagemanagement/nuget/Cache`, and the packages in the user's NuGet folder. A republished version with the same number would need both cleared (NuGet never republishes a version, so this bites only local feeds). While a cache entry exists fsi ignores `NUGET_PACKAGES` for that set.
- Windows 11 with Smart App Control on can refuse a freshly built program or child DLL ("An Application Control policy has blocked this file"). The gate fails closed and prints the message. Rebuilding the same bytes keeps the refusal; a build from another folder, or with any source change, gets new bytes (seen 2026-09-30).
- An `init`-only property can still be assigned from PowerShell 7 after `::new()`; F# sets it with named arguments on the constructor (`Options(IndentSize = 2)`).

Related: builds on [../SKILL.md](../SKILL.md); see also [page-sets.md](page-sets.md), [npm.md](npm.md).
