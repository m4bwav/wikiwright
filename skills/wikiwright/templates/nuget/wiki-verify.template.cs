#:package {{PACKAGE_ID}}@{{VERSION}}
#:property PublishAot=false
// wiki-verify for {{PACKAGE_ID}} {{VERSION}}: prints every output the wiki's pages show, run against
// the PUBLISHED package from nuget.org, never the working tree. Keep the filled-in copy in the
// repository as ai-docs/notes/<date>-wiki-verify.cs, and its output beside it as
// ai-docs/notes/<date>-wiki-verify.out.txt with LF line endings (Console.WriteLine writes CRLF on
// Windows: tr -d '\r'), so the next release can run it again and diff (L-019, L-105).
//
// `wikiwright.py scaffold nuget ID VERSION --namespace NS --type T` writes this file filled in and cut to the
// sections the survey calls for: --children (the pages' examples as whole programs, run in child apps per
// framework and dependency set), --requests (the stand-in proxy and the .invalid gate), --fsharp (dotnet fsi),
// --tool ID:COMMAND (a dotnet tool's install and terminal transcripts). The template is never cut by hand.
//
// Run it from a folder outside any project cone (a scratch folder; file-based apps pick up
// Directory.Build.props and global.json from parent folders), with TEMP and TMP pointing into that folder
// (file-based builds go to <TEMP>/dotnet/runfile otherwise; from Git Bash export them as C:/ paths):
//   dotnet build wiki-verify.cs && dotnet run --no-build wiki-verify.cs > out.txt
// (a first plain `dotnet run` prints its build warnings into out.txt). Two runs must print the
// same thing: no times, paths or random values (L-022, L-111); Show() masks what Masks lists.
//
// PublishAot=false: .NET 10 file-based apps enable native AOT by default, which turns off
// reflection-based System.Text.Json and makes such calls throw even under dotnet run.
// Two copies of this file must not run at once from one folder: they share build output.
//
// Every case prints "## <label>" and then its output. Paste outputs into the pages exactly as
// printed; a page never shows output this program did not produce. A value shown in a code
// comment on a page is quoted (// "Marguerita") or written // => value, so
// `wikiwright.py outputs` can check it (L-110). The page's PowerShell and F# snippets run from
// here too, through Run() and Fsi(), so their output is in the saved file.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Security;
using System.Net.Sockets;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using {{NAMESPACE}};

Console.OutputEncoding = Encoding.UTF8;
var scratch = (string?)AppContext.GetData("EntryPointFileDirectoryPath") ?? Environment.CurrentDirectory;
var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
Masks.Pairs.AddRange([(scratch, "<scratch>"), (Environment.GetEnvironmentVariable("NUGET_PACKAGES") ?? Path.Combine(home, ".nuget", "packages"), "<nuget>"),
    (Path.GetTempPath().TrimEnd(Path.DirectorySeparatorChar), "<temp>"), (home, "<home>")]);
// Text with a shape rather than a fixed value, as a regular expression and its token, masked after the pairs:
// an external program's heap addresses, for example ffmpeg's "[mp3 @ 0x55d0c1a2b3c0]".
// Masks.Patterns.Add((@"@ (0x)?[0-9a-f]{8,16}\]", "@ <address>]"));

// What loaded: the runtime, the package, then each dependency whose version the pages name, by assembly name
// ("Autofac", "Castle.Core"). Installed() prints the informational version, since an assembly version can stay put
// across releases (Castle.Core is 5.0.0.0 in 5.1.1 and 5.2.1), and the framework of the lib folder that loaded, from
// TargetFrameworkAttribute (Assembly.Location is the bin folder a build copied the DLL to). A dependency range the
// package declares is run at its ends: one children config per end (the children section).
string[] dependencies = [];
var asm = typeof({{A_PUBLIC_TYPE}}).Assembly;
Show("installed", RuntimeInformation.FrameworkDescription + "\n"
    + string.Join("\n", new[] { asm }.Concat(dependencies.Select(name => Assembly.Load(name))).Select(Installed)));

// ===== section: children =====
// ----- the pages' examples as whole programs, run in child apps: one set per config, each example in its own process -----
// An example is a whole program as the page shows it: using lines, statements, then the types it declares. The
// types stay global, so a printed type name (a cache key, a container's message) is the page's, with no wrapper
// namespace. Each example is its own file in a child app (#:include), its statements wrapped in a method; examples
// that declare the same type name go to separate child apps. An example that starts with its own #: lines (a
// file-based app on the page) runs as its own app with them (L-143). Every example runs in its own process, so
// process-global state (MemoryCache.Default, a static field, a container) never carries over from another one.
// Children build without the proxy variables, so their restores reach nuget.org.
// A config is a target framework and extra #: lines: "Autofac@9.3.4" adds `#:package Autofac@9.3.4` (the ends of a
// dependency range the package declares, one config each), "{{PACKAGE_ID}}@1.0.1" runs an old version, a line
// starting with #: passes through. "net48" runs .NET Framework 4.8 (Windows only) on the package's net4x or
// netstandard2.0 build, "net8.0" a netstandard2.0 build. A raw string holding """ needs """" around the example.
var configs = new List<Config>
{
    {{CONFIGS}}
};
var examples = new List<Example>
{
    // new("getting started: the first call", """
    //     using {{NAMESPACE}};
    //
    //     Console.WriteLine(new Greeter().Hello());
    //
    //     public class Greeter
    //     {
    //         public string Hello() => "hello";
    //     }
    //     """),
};
Func<Child, string, string> runCase = (child, label) => RunExample(child, label, null, scratch);

// ===== section: requests =====
// Every request goes to StandIn, a proxy on 127.0.0.1 that answers the `.test` host names in `routes`
// (RFC 6761 names that never resolve) and refuses every other host BY ANSWERING: a reply that is not
// HTTP, or 403 to CONNECT. Closing the connection instead makes HttpClient retry (4 GETs or 16 CONNECTs
// on .NET 10, 2 on .NET Framework; L-138). It never opens a socket of its own, and it logs every
// request line with its host. Pages show the `.test` names or label the stand-in; the real hosts are
// never asked (L-116, L-122; references/nuget-requests.md).
//
// The examples run in the children, so a process finds its proxy where a user's would: HTTP_PROXY and
// HTTPS_PROXY on .NET Core and .NET 5+. .NET Framework ignores them, so every child sets
// WebRequest.DefaultWebProxy before its example runs; Framework never proxies a loopback address, hence
// `.test` names and never 127.0.0.1 in routes. Restores (the children's builds, dotnet fsi's
// #r "nuget:") run WITHOUT the proxy variables, before the gate (L-137).
// Requests sent at once arrive in any order: sort their log lines, or print one call per example.
var png = new byte[] { 0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A };
var routes = new Dictionary<string, Answer>
{
    // "scheme://host.test/path" (no query) => status line, content type, body; a redirect sets Location.
    // An https key makes the stand-in accept CONNECT for that host and speak TLS with a throwaway
    // certificate that only StandInClient() in a child trusts (a harness row: label it on the page).
    ["http://api.test/item"] = new("200 OK", "application/json", Encoding.UTF8.GetBytes("""{"id":1}""")),
    ["http://api.test/old"] = new("301 Moved Permanently", Location: "http://api.test/item"),
    ["https://secure.test/item"] = new("200 OK", "image/png", png),
};
using var standIn = new StandIn(routes);
Masks.Pairs.Add((":" + standIn.Port, ":<port>"));
HttpClient.DefaultProxy = new WebProxy(standIn.Url);   // a stray request from this process lands there too

// The gate, before any case: the package's default (shared) client and a caller's new HttpClient() must
// each throw AND be logged by the stand-in exactly once, or the run stops. Replace the calls with the
// package's request on its default client and on `mine`; both take `url`.
examples.Insert(0, new("gate", """
    using System;
    using System.Net.Http;
    using {{NAMESPACE}};

    foreach (var url in new[] { "http://gate.invalid/", "https://gate.invalid/" })
    {
        Console.WriteLine(url + " default client: " + await Outcome(() => {{DEFAULT_CLIENT_CALL}}));
        using var mine = new HttpClient();
        Console.WriteLine(url + " new HttpClient(): " + await Outcome(() => {{CALLER_CLIENT_CALL}}));
    }
    """, Harness: true));
var gateCalls = 4;   // 2 when the package's request takes no HttpClient: delete the `mine` lines in both gates
runCase = RunSnippet;
// ===== end: requests =====
var children = configs.Select(config => BuildChild(scratch, config, examples, dependencies)).ToList();
// ===== section: requests =====
foreach (var child in children)
{
    Gate(child.Name, RunSnippet(child, "gate"), gateCalls);
}

// ===== section: fsharp =====
// ----- F# that requests (dotnet fsi) -----
// fsi resolves a script's #r and #i lines as one set, keeps the answer in ~/.packagemanagement/nuget/Cache
// and never restores that set again. The warm-up (the #r line and a printfn) runs WITHOUT the proxy
// variables: on a fresh machine it downloads the package and FSharp.Core; skipped, the gate's own restore
// meets the stand-in (CONNECT api.nuget.org) and fails the gate. fsi reads HTTP_PROXY and HTTPS_PROXY.
var reference = "#r \"nuget: {{PACKAGE_ID}}, {{VERSION}}\"\n";
Show("fsi restore (no proxy)", Fsi(scratch, "warm", reference + "printfn \"restored\"\n", ProxyEnv(null)));
Gate("dotnet fsi", RunFsx("gate", reference + """
    open System.Net.Http
    open {{NAMESPACE}}

    let outcome (call: unit -> System.Threading.Tasks.Task<'T>) =
        try sprintf "returned %A" (call().GetAwaiter().GetResult()) with e -> "threw " + e.GetType().Name

    for url in [ "http://gate.invalid/"; "https://gate.invalid/" ] do
        printfn "%s default client: %s" url (outcome (fun () -> {{FS_DEFAULT_CLIENT_CALL}}))
        use mine = new HttpClient()
        printfn "%s new HttpClient(): %s" url (outcome (fun () -> {{FS_CALLER_CLIENT_CALL}}))
    """), gateCalls);
// The pages' F# that requests, exactly as shown. #r lines other than `reference` need their own warm-up,
// or their restore fails at the stand-in. An https route from F# (a harness row)
// passes its own client: new HttpClient(new HttpClientHandler(ServerCertificateCustomValidationCallback =
//     fun _ c _ _ -> c.GetCertHashString() = System.Environment.GetEnvironmentVariable "WIKI_VERIFY_THUMBPRINT"))
var fsSnippets = new Dictionary<string, string>
{
    // ["getting started: F#"] = """
    //     #r "nuget: {{PACKAGE_ID}}, {{VERSION}}"
    //     ...
    //     """,
};
foreach (var (name, code) in fsSnippets)
{
    Show($"{name} (fsi)", RunFsx(name, code));
}
// ===== end: fsharp =====
// ===== end: requests =====

foreach (var child in children)
{
    Show($"installed ({child.Name})", RunExample(child, "installed", null, scratch));
    foreach (var example in examples.Where(e => !e.Harness))
    {
        Show($"{example.Label} ({child.Name})", runCase(child, example.Label));
    }
}
// ===== section: requests =====

Show("stand-in: hosts asked", string.Join("\n", standIn.Hosts));
// ===== end: requests =====
// ===== end: children =====

// ----- the cases: one per example on the wiki, labelled by page -----
// Show("getting started: the first call", ...);
// What a page's code prints with Console.WriteLine, line for line:
// Show("recipes: a loop", Captured(() => { for (var i = 0; i < 3; i++) Console.WriteLine(i); }));
// An unseeded example: print it only when it is a possible answer:
// Possible("home: unseeded examples", ("Prophetstown", SomeGenerator.Names.Contains));
// Errors: Catch() prints the exception type and message the page quotes.
// Show("null input", Catch(() => ...));

// ----- the pages' PowerShell and F# snippets, run as written -----
// ===== section: fsharp =====
// Show("getting started: F#", Fsi(scratch, "getting started: F#", """
//     #r "nuget: {{PACKAGE_ID}}, {{VERSION}}"
//     ...
//     """));
// ===== end: fsharp =====
// Show("getting started: PowerShell", Run("pwsh", ["-NoProfile", "-NonInteractive", "-Command", """
//     Add-Type -Path "$env:USERPROFILE/.nuget/packages/{{PACKAGE_ID_LOWER}}/{{VERSION}}/lib/netstandard2.0/<assembly>.dll"
//     ...
//     """]));

// ===== section: tool =====
// ----- the dotnet tool {{TOOL_ID}}: transcripts as the pages show them -----
// Installed from nuget.org into <scratch>/tools with --tool-path, never -g (a global install changes the
// machine), and run by name with that folder first on PATH, as a user's shell would after a global install.
// Term() runs a command line through the shell with stdin closed and prints it as a terminal transcript. Run
// each case in a Fresh() folder and show it with that folder masked as <cwd>. A command with an effect
// outside scratch (an installer option, a system change) runs only through the tool's own seams (already
// installed, not a terminal, no package manager), never with --yes, and the rest is "not tested" on the page.
var toolVersion = "{{VERSION}}";   // the tool package's version, when it is not the library's
var tools = Path.Combine(scratch, "tools");
var dotnetEnv = new Dictionary<string, string?> { ["DOTNET_NOLOGO"] = "1", ["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1" };
var toolEnv = new Dictionary<string, string?>(dotnetEnv) { ["PATH"] = tools + Path.PathSeparator + Environment.GetEnvironmentVariable("PATH") };
foreach (var folder in new[] { tools, tools + "-u" }.Where(Directory.Exists))
{
    Directory.Delete(folder, true);
}

Show("tool: install", Term("dotnet tool install {{TOOL_ID}} --version " + toolVersion + " --tool-path tools", scratch, dotnetEnv));
Show("tool: list", Term("dotnet tool list --tool-path tools", scratch, dotnetEnv));
Run("dotnet", ["tool", "install", "{{TOOL_ID}}", "--version", toolVersion, "--tool-path", "tools-u"], dotnetEnv, scratch);
Show("tool: uninstall", Term("dotnet tool uninstall {{TOOL_ID}} --tool-path tools-u", scratch, dotnetEnv));
Show("tool: the package's files", Listing(Path.Combine(tools, ".store", "{{TOOL_ID}}".ToLowerInvariant(), toolVersion), _ => null));
var help = Fresh(scratch, "commands: help");
Show("commands: help", Term("{{TOOL_COMMAND}} -h", help, toolEnv), (help, "<cwd>"));
// A case with inputs: copy them into its folder, run, then list the folder (describe: ffprobe facts for media).
// var trailer = Fresh(scratch, "commands: a file");
// File.Copy(Path.Combine(scratch, "fixtures", "a.mp3"), Path.Combine(trailer, "a.mp3"));
// Show("commands: a file", Term("{{TOOL_COMMAND}} a.mp3 2000", trailer, toolEnv) + "\n-- the folder afterwards\n" + Listing(trailer), (trailer, "<cwd>"));
// ===== end: tool =====

static void Show(string label, object? value, params (string Text, string Token)[] extra)
{
    Console.WriteLine($"## {label}");
    Console.WriteLine(Mask(value?.ToString() ?? "<null>", extra));
    Console.WriteLine();
}

// Prints each value only when its check passes, one per line, so a page's example of a random
// call is shown to be a possible answer (L-111 `membership-for-random`).
static void Possible(string label, params (string Value, Func<string, bool> OnList)[] cases)
{
    Show(label + " (each checked against the list it comes from)",
        string.Join("\n", cases.Select(c => c.OnList(c.Value) ? c.Value : "NOT ON THE LIST: " + c.Value)));
}

// What the code prints with Console.WriteLine, line for line, LF endings.
static string Captured(Action action)
{
    var original = Console.Out;
    var writer = new StringWriter { NewLine = "\n" };
    Console.SetOut(writer);
    try
    {
        action();
    }
    finally
    {
        Console.SetOut(original);
    }

    return writer.ToString().TrimEnd('\n');
}

// Runs a command (a page's snippet in another host, a child app) and returns what it printed, LF
// line endings. env: a value sets a variable, null removes it (ProxyEnv).
static string Run(string file, string[] args, Dictionary<string, string?>? env = null, string? cwd = null)
{
    var (stdout, stderr, exit) = Start(file, args, env, cwd);
    var err = stderr.Trim();   // fsi pads its warnings and errors with blank lines
    var text = stdout.TrimEnd() + (err.Length > 0 ? "\n--- stderr\n" + err : "") + (exit != 0 ? "\n--- exit " + exit : "");
    return text.Replace("\r\n", "\n").TrimStart('\n');
}

// Starts a process with both output streams read at once (a child that writes much to stderr cannot fill
// that pipe and stall) and stdin redirected and closed at once, so a child that asks reads end of input
// instead of waiting on this program's console. commandLine replaces args (cmd's own quoting, in Term()).
static (string Stdout, string Stderr, int Exit) Start(string file, string[] args, Dictionary<string, string?>? env = null, string? cwd = null, string? commandLine = null)
{
    var info = new ProcessStartInfo(file)
    {
        RedirectStandardInput = true, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false,
        StandardOutputEncoding = Encoding.UTF8, StandardErrorEncoding = Encoding.UTF8, WorkingDirectory = cwd ?? "",
    };
    if (commandLine is not null) info.Arguments = commandLine;
    foreach (var arg in args)
    {
        info.ArgumentList.Add(arg);
    }

    foreach (var (name, value) in env ?? [])
    {
        if (value is null) info.Environment.Remove(name); else info.Environment[name] = value;
    }

    using var p = Process.Start(info)!;
    p.StandardInput.Close();
    var stderr = p.StandardError.ReadToEndAsync();
    var stdout = p.StandardOutput.ReadToEnd();
    p.WaitForExit();
    return (stdout, stderr.Result, p.ExitCode);
}

static string Catch(Func<object?> action)
{
    try
    {
        return "returned: " + (action()?.ToString() ?? "<null>");
    }
    catch (Exception e)
    {
        return $"{e.GetType().Name}: {e.Message}";
    }
}

// Replaces what differs between machines and runs: Masks.Pairs and the call's extra pairs (a case's folder as
// <cwd>), longest first, each also with / separators; then each of Masks.Patterns. On Linux run with a
// distinctive TMPDIR (TMPDIR=/tmp/wiki-verify-tmp): masking a bare /tmp also rewrites content such as
// file:///tmp/a.png.
static string Mask(string text, params (string Text, string Token)[] extra)
{
    foreach (var (from, token) in Masks.Pairs.Concat(extra).Where(p => p.Text.Length > 1).OrderByDescending(p => p.Text.Length))
    {
        text = text.Replace(from, token).Replace(from.Replace(Path.DirectorySeparatorChar, '/'), token);
    }

    foreach (var (pattern, token) in Masks.Patterns)
    {
        text = Regex.Replace(text, pattern, token);
    }

    return text;
}

// "Name informational-version (file F, lib Framework,Version=vX)": see `dependencies` at the top. The file version
// is there for a build that never set an informational version, which then reads 1.0.0 (FFMpegCore 5.0.0.0).
static string Installed(Assembly assembly) => assembly.GetName().Name + " "
    + assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion?.Split('+')[0]
    + " (file " + assembly.GetCustomAttribute<AssemblyFileVersionAttribute>()?.Version
    + ", lib " + (assembly.GetCustomAttribute<TargetFrameworkAttribute>()?.FrameworkName ?? "without a TargetFrameworkAttribute") + ")";

static string Slug(string text) => string.Concat(text.Select(c => char.IsAsciiLetterOrDigit(c) ? c : '-'));
// ===== section: fsharp =====

// Runs an F# script with dotnet fsi from <scratch>/fsx, written with LF endings under a file name made from
// `name`. fsi restores the script's #r "nuget:" lines when it runs.
static string Fsi(string scratch, string name, string code, Dictionary<string, string?>? env = null)
{
    var dir = Directory.CreateDirectory(Path.Combine(scratch, "fsx")).FullName;
    var file = Slug(name) + ".fsx";
    File.WriteAllText(Path.Combine(dir, file), code.Replace("\r\n", "\n") + "\n");
    return Run("dotnet", ["fsi", "--quiet", file], env, dir);
}
// ===== end: fsharp =====
// ===== section: children =====

// Writes a config's examples into child apps under <scratch>/children/<config>, builds each WITHOUT the proxy
// variables and returns the command that runs each example by label, plus "installed" (the runtime and the
// versions that loaded). A child app that does not build stops the run; an example's own app that does not build
// is that example's output.
static Child BuildChild(string scratch, Config config, List<Example> examples, string[] dependencies)
{
    var root = Path.Combine(scratch, "children", Slug(config.Name));
    if (Directory.Exists(root)) Directory.Delete(root, true);
    var lines = (config.Lines ?? []).Select(l => l.StartsWith("#:") ? l : "#:package " + l).ToList();
    var runs = new Dictionary<string, (string[]? Command, string? Error)>();
    var batches = new List<(List<Example> Members, HashSet<string> Types)> { ([], []) };
    foreach (var example in examples)
    {
        var code = example.Code.Replace("\r\n", "\n");
        if (code.Split('\n').Any(l => l.StartsWith("#:")))
        {
            // The page's own file-based app, as written, with the config's lines it does not set itself.
            var named = code.Split('\n').Where(l => l.StartsWith("#:")).Select(l => l.Split('@', '=')[0]).ToHashSet();
            var head = new[] { "#:property TargetFramework=" + config.Framework, "#:property LangVersion=latest" }.Concat(lines)
                .Where(l => !named.Contains(l.Split('@', '=')[0])).Append("#:include harness.cs");
            runs.Add(example.Label, BuildApp(Path.Combine(root, Slug(example.Label)), "app", string.Join("\n", head) + "\n" + code, false));
            continue;
        }

        var types = TypeNames(code);
        var batch = batches.FindIndex(b => !b.Types.Overlaps(types));
        if (batch < 0) batches.Add(([], []));
        batches[batch < 0 ? batches.Count - 1 : batch].Members.Add(example);
        batches[batch < 0 ? batches.Count - 1 : batch].Types.UnionWith(types);
    }

    string[] main = lines.Any(l => l.StartsWith("#:package {{PACKAGE_ID}}@", StringComparison.OrdinalIgnoreCase)) ? [] : ["#:package {{PACKAGE_ID}}@{{VERSION}}"];
    for (var b = 0; b < batches.Count; b++)
    {
        var dir = Path.Combine(root, "b" + b);
        Directory.CreateDirectory(dir);
        var cases = new StringBuilder();
        var includes = new StringBuilder();
        for (var i = 0; i < batches[b].Members.Count; i++)
        {
            var (usings, statements, types) = Split(batches[b].Members[i].Code);
            var scoped = Regex.Match(types, @"^namespace ([\w.]+);[ \t]*$", RegexOptions.Multiline);   // a block, after the wrapper
            types = scoped.Success ? types[..scoped.Index] + "namespace " + scoped.Groups[1].Value + " {" + types[(scoped.Index + scoped.Length)..] + "\n}" : types;
            File.WriteAllText(Path.Combine(dir, $"ex{i}.cs"), $"// example: {batches[b].Members[i].Label}\n{usings}\nstatic class WikiCase{i}\n{{\npublic static async System.Threading.Tasks.Task Run(string[] args)\n{{\n{statements}\n}}\n}}\n{types}\n");
            includes.Append($"#:include ex{i}.cs\n");
            cases.Append($"    case \"{i}\": await WikiCase{i}.Run(args); break;\n");
        }

        var source = string.Join("\n", new[] { "#:property TargetFramework=" + config.Framework, "#:property PublishAot=false", "#:property LangVersion=latest" }
            .Concat(main).Concat(lines).Append("#:include harness.cs")) + "\n" + includes + """
            using System;
            using System.Reflection;
            using System.Runtime.InteropServices;
            using System.Runtime.Versioning;

            switch (args.Length > 0 ? args[0] : "")
            {
                case "installed":
                    Console.WriteLine(RuntimeInformation.FrameworkDescription);
                    Console.WriteLine(Installed(typeof(global::{{NAMESPACE}}.{{A_PUBLIC_TYPE}}).Assembly));
                    foreach (var name in new string[] { %DEPENDENCIES% })
                    {
                        try { Console.WriteLine(Installed(Assembly.Load(name))); }
                        catch (Exception e) { Console.WriteLine(name + ": " + e.GetType().Name); }
                    }

                    break;
            %CASES%    default:
                    Console.WriteLine("no example " + string.Join(" ", args));
                    break;
            }

            static string Installed(Assembly assembly) => assembly.GetName().Name + " "
                + assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion?.Split('+')[0]
                + " (file " + assembly.GetCustomAttribute<AssemblyFileVersionAttribute>()?.Version
                + ", lib " + (assembly.GetCustomAttribute<TargetFrameworkAttribute>()?.FrameworkName ?? "without a TargetFrameworkAttribute") + ")";

            """.Replace("%DEPENDENCIES%", string.Join(", ", dependencies.Select(d => '"' + d + '"'))).Replace("%CASES%", cases.ToString());
        var app = BuildApp(dir, "child", source, true);
        foreach (var (label, key) in batches[b].Members.Select((e, i) => (e.Label, i.ToString())).Prepend(("installed", "installed")).Skip(b == 0 ? 0 : 1))
        {
            runs.Add(label, (app.Command!.Append(key).ToArray(), null));
        }
    }

    return new Child(config.Name, runs);
}

// Writes harness.cs and <name>.cs into dir and builds them; returns the command that runs the app, or the build's
// errors. harness.cs runs first in every child (a module initializer) and holds what the examples may call.
static (string[]? Command, string? Error) BuildApp(string dir, string name, string source, bool mustBuild)
{
    Directory.CreateDirectory(dir);
    File.WriteAllText(Path.Combine(dir, name + ".cs"), source.Replace("\r\n", "\n"));
    File.WriteAllText(Path.Combine(dir, "harness.cs"), """
        global using static WikiHarness;
        using System;
        using System.Net;
        using System.Net.Http;
        using System.Text;
        using System.Threading.Tasks;

        static class WikiHarness
        {
            [System.Runtime.CompilerServices.ModuleInitializer]
            internal static void Start()
            {
                Console.OutputEncoding = Encoding.UTF8;

        """
// ===== section: requests =====
        + """
                #if NETFRAMEWORK
                // .NET Framework ignores HTTP_PROXY: the process's default proxy is set, as machine settings would.
                WebRequest.DefaultWebProxy = new WebProxy(Environment.GetEnvironmentVariable("WIKI_VERIFY_PROXY"));
                #endif

        """
// ===== end: requests =====
        + """
            }

        """
// ===== section: requests =====
        + """
            internal static async Task<string> Outcome<T>(Func<Task<T>> call)
            {
                try { return "returned " + await call(); }
                catch (Exception e) { return "threw " + e.GetType().Name; }
            }

            // Trusts only the stand-in's throwaway certificate: for a harness row on an https route.
            internal static HttpClient StandInClient() => new HttpClient(new HttpClientHandler
            {
                ServerCertificateCustomValidationCallback = (_, cert, _, _) => cert?.GetCertHashString() == Environment.GetEnvironmentVariable("WIKI_VERIFY_THUMBPRINT"),
            });

        """
// ===== end: requests =====
        + """
        }

        #if NETFRAMEWORK
        namespace System.Runtime.CompilerServices
        {
            [AttributeUsage(AttributeTargets.Method, Inherited = false)]
            sealed class ModuleInitializerAttribute : Attribute { }
        }
        #endif

        """);
    var build = Run("dotnet", ["build", name + ".cs", "-o", "bin", "-nologo", "-v:q"], WithoutProxy(), dir);
    var framework = File.ReadAllText(Path.Combine(dir, name + ".cs")).Contains("TargetFramework=net4");
    var output = Path.Combine(dir, "bin", name + (framework ? ".exe" : ".dll"));
    string[] command = framework ? [output] : ["dotnet", output];
    if (File.Exists(output)) return (command, null);
    if (mustBuild) throw new Exception($"the child app in {dir} did not build:\n{build}");
    return (null, "build failed:\n" + string.Join("\n", build.Split('\n').Where(l => l.Contains(": error "))
        .Select(l => Regex.Replace(l.Trim(),@" \[[^\]]*\]$", "")).Distinct()));
}

// Runs one example (or "installed") of a child in its own process.
static string RunExample(Child child, string label, Dictionary<string, string?>? env, string cwd) =>
    !child.Runs.TryGetValue(label, out var run) ? "no example labelled " + label
    : run.Command is null ? run.Error! : Run(run.Command[0], run.Command[1..], env, cwd);

// The environment children build in: no proxy variables, so the restore reaches nuget.org (L-137).
static Dictionary<string, string?> WithoutProxy()
{
    var env = new Dictionary<string, string?> { ["DOTNET_NOLOGO"] = "1", ["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1" };
    foreach (var name in new[] { "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY" })
    {
        env[name] = env[name.ToLowerInvariant()] = null;
    }

    return env;
}

// An example's text in three parts: its using lines; its statements; the types it declares, from the first line
// at the margin that starts a type or a namespace (with the attribute and comment lines just above it).
static (string Usings, string Statements, string Types) Split(string code)
{
    var lines = code.Replace("\r\n", "\n").Split('\n');
    var at = 0;
    while (at < lines.Length && (lines[at].Trim().Length == 0 || lines[at].StartsWith("//")
        || Regex.IsMatch(lines[at], @"^(global )?using (static )?[A-Za-z_][\w.]*( = [\w.<>, ]+)?;\s*$")))
    {
        at++;
    }

    var start = Array.FindIndex(lines, at, l => Regex.IsMatch(l, @"^(\[[^\]]*\]\s*)*((public|internal|file|sealed|static|abstract|partial|readonly|ref|unsafe)\s+)*(class|interface|struct|enum|record|delegate|namespace)\b"));
    start = start < 0 ? lines.Length : start;
    while (start > at && (lines[start - 1].StartsWith("[") || lines[start - 1].StartsWith("//")))
    {
        start--;
    }

    return (string.Join("\n", lines[..at]), string.Join("\n", lines[at..start]), string.Join("\n", lines[start..]));
}

// The names of the types an example declares at the margin: two examples that share one go to separate apps.
static HashSet<string> TypeNames(string code) => Regex.Matches(Split(code).Types,
        @"^(?:\[[^\]]*\]\s*)*(?:(?:public|internal|file|sealed|static|abstract|partial|readonly|ref|unsafe)\s+)*(?:record\s+(?:class\s+|struct\s+)?|class\s+|interface\s+|struct\s+|enum\s+|delegate\s+[^\s(]+\s+)([A-Za-z_]\w*)",
        RegexOptions.Multiline).Select(m => m.Groups[1].Value).ToHashSet();
// ===== end: children =====
// ===== section: tool =====

// A terminal transcript as a page shows it: "$ <command>", what it printed with stdout and stderr merged in the
// order written (2>&1 on the whole line), then "$ echo $?" and the exit code. The line runs through
// cmd /d /s /c on Windows (an unquoted ")" in it ends the group) and /bin/sh -c elsewhere, in cwd, with stdin
// closed: a command that would ask sees no terminal and cannot wait. env: a value sets a variable, null removes it.
static string Term(string command, string cwd, Dictionary<string, string?>? env = null)
{
    var (stdout, stderr, exit) = OperatingSystem.IsWindows()
        ? Start("cmd.exe", [], env, cwd, "/d /s /c \"(" + command + ") 2>&1\"")
        : Start("/bin/sh", ["-c", "{ " + command + "\n} 2>&1"], env, cwd);
    var output = stdout.Replace("\r\n", "\n").TrimEnd('\n');
    return "$ " + command + "\n" + (output.Length > 0 ? output + "\n" : "") + "$ echo $?\n" + exit
        + (stderr.Trim().Length > 0 ? "\n(shell stderr) " + stderr.Trim() : "");
}

// A fresh, empty folder for one case, <scratch>/cases/<label>: copy the case's inputs in, run, list it afterwards.
static string Fresh(string scratch, string label)
{
    var dir = Path.Combine(scratch, "cases", Slug(label));
    if (Directory.Exists(dir)) Directory.Delete(dir, true);
    return Directory.CreateDirectory(dir).FullName;
}

// Every file under a folder, relative with '/', in ordinal order, each with what describe() says of it (default
// its size; null, the name alone; for media, ffprobe's duration and streams, never the bytes).
static string Listing(string dir, Func<string, string?>? describe = null)
{
    var lines = Directory.GetFiles(dir, "*", SearchOption.AllDirectories)
        .Select(f => (Path: f, Name: Path.GetRelativePath(dir, f).Replace(Path.DirectorySeparatorChar, '/')))
        .OrderBy(f => f.Name, StringComparer.Ordinal)
        .Select(f => (describe ?? (p => new FileInfo(p).Length + " bytes"))(f.Path) is { } fact ? f.Name + ": " + fact : f.Name)
        .ToList();
    return lines.Count == 0 ? "(empty)" : string.Join("\n", lines);
}
// ===== end: tool =====
// ===== section: requests =====

// The children's variables: the stand-in as proxy, or (null) no proxy at all, for restores.
static Dictionary<string, string?> ProxyEnv(StandIn? standIn)
{
    var env = new Dictionary<string, string?> { ["WIKI_VERIFY_PROXY"] = standIn?.Url, ["WIKI_VERIFY_THUMBPRINT"] = standIn?.Thumbprint, ["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1" };
    foreach (var name in new[] { "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY" })
    {
        env[name] = env[name.ToLowerInvariant()] = name.StartsWith("HTTP") ? standIn?.Url : null;
    }

    return env;
}

// Runs one example under the proxy; prints its output, then the requests the stand-in saw.
string RunSnippet(Child child, string name)
{
    standIn.Take();
    var output = RunExample(child, name, ProxyEnv(standIn), scratch);
    return output + "\n" + Seen(standIn.Take());
}
// ===== section: fsharp =====

// The same under dotnet fsi: fsi finds the proxy in HTTP_PROXY and HTTPS_PROXY as a .NET 10 child does.
string RunFsx(string name, string code)
{
    standIn.Take();
    var output = Fsi(scratch, name, code, ProxyEnv(standIn));
    return output + "\n" + Seen(standIn.Take());
}
// ===== end: fsharp =====

// Prints a route's gate and stops the run unless each of the `calls` calls threw and the stand-in logged exactly
// `calls` requests, all to gate.invalid (a restore that reached the stand-in fails it too).
static void Gate(string route, string output, int calls)
{
    Show($"gate ({route})", output);
    var lines = output.Split('\n');
    var logged = lines.Where(l => l.StartsWith("stand-in: ") && l.Contains(" -> ")).ToList();
    if (lines.Count(l => l.Contains(": threw ")) != calls || logged.Count != calls || logged.Any(l => !l.Contains("gate.invalid")))
    {
        Console.WriteLine($"GATE FAILED on {route}: a call returned, went round the stand-in or was retried. No case ran.");
        Environment.Exit(1);
    }
}

static string Seen(List<string> requests) => requests.Count == 0 ? "stand-in: no request" : string.Join("\n", requests.Select(r => "stand-in: " + r));
// ===== end: requests =====
// ===== section: children =====

// A config: a target framework and extra #: lines ("Autofac@9.3.4" is a #:package line).
record Config(string Framework, string[]? Lines = null)
{
    public string Name => Lines is { Length: > 0 } ? Framework + " with " + string.Join(", ", Lines) : Framework;
}

// A page's example as a whole program; Harness marks one the harness runs itself (the gate), not a case.
record Example(string Label, string Code, bool Harness = false);

// A config's built apps: the command that runs each example by label, or why its app did not build.
record Child(string Name, Dictionary<string, (string[]? Command, string? Error)> Runs);
// ===== end: children =====
// ===== section: requests =====

record Answer(string Status, string? ContentType = null, byte[]? Body = null, string? Location = null);

// The stand-in proxy: answers `routes`, refuses every other host by answering, never connects out,
// and logs "<request line> -> <answer>" in arrival order.
sealed class StandIn : IDisposable
{
    readonly TcpListener listener = new(IPAddress.Loopback, 0);
    readonly Dictionary<string, Answer> routes;
    readonly X509Certificate2? certificate;
    readonly List<string> log = [];

    public StandIn(Dictionary<string, Answer> routes)
    {
        this.routes = routes;
        var tlsHosts = routes.Keys.Where(k => k.StartsWith("https://")).Select(k => new Uri(k).Host).Distinct().ToList();
        if (tlsHosts.Count > 0)
        {
            using var key = RSA.Create(2048);
            var request = new CertificateRequest("CN=" + tlsHosts[0], key, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);
            var names = new SubjectAlternativeNameBuilder();
            tlsHosts.ForEach(names.AddDnsName);
            request.CertificateExtensions.Add(names.Build());
            using var made = request.CreateSelfSigned(DateTimeOffset.UtcNow.AddDays(-1), DateTimeOffset.UtcNow.AddDays(1));
            certificate = X509CertificateLoader.LoadPkcs12(made.Export(X509ContentType.Pfx), null);   // SslStream on Windows needs a stored key
        }

        listener.Start();
        _ = Task.Run(async () =>
        {
            while (true)
            {
                var client = await listener.AcceptTcpClientAsync();
                _ = Task.Run(() => Handle(client));
            }
        });
    }

    public int Port => ((IPEndPoint)listener.LocalEndpoint).Port;

    public string Url => "http://127.0.0.1:" + Port;

    public string? Thumbprint => certificate?.Thumbprint;

    public SortedSet<string> Hosts { get; } = new(StringComparer.Ordinal);

    public List<string> Take()
    {
        lock (log)
        {
            var copy = new List<string>(log);
            log.Clear();
            return copy;
        }
    }

    void Log(string line, string host)
    {
        lock (log)
        {
            log.Add(line);
            Hosts.Add(host);
        }
    }

    async Task Handle(TcpClient client)
    {
        using var _ = client;
        try
        {
            Stream stream = client.GetStream();
            var parts = (await ReadHead(stream)).Split(' ');
            if (parts.Length < 2) return;
            var (method, target) = (parts[0], parts[1]);
            if (method == "CONNECT")
            {
                var host = target.Split(':')[0];
                if (certificate is null || !routes.Keys.Any(k => k.StartsWith($"https://{host}/")))
                {
                    Log($"CONNECT {target} -> 403 refused", host);
                    await Write(stream, "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n");
                    return;
                }

                await Write(stream, "HTTP/1.1 200 Connection established\r\n\r\n");
                var tls = new SslStream(stream);
                await tls.AuthenticateAsServerAsync(certificate);
                parts = (await ReadHead(tls)).Split(' ');
                (method, target, stream) = (parts[0], $"https://{host}{parts[1]}", tls);
            }

            var uri = Uri.TryCreate(target, UriKind.Absolute, out var u) && u.Scheme.StartsWith("http") ? u : null;
            if (uri is null || !routes.Keys.Any(k => new Uri(k).Host == uri.Host))
            {
                // Not HTTP, so the client fails at once. A closed connection would make HttpClient retry.
                Log($"{method} {target} -> refused", uri?.Host ?? "(not a proxy request)");
                await Write(stream, "REFUSED BY THE STAND-IN\r\n\r\n");
                return;
            }

            var answer = routes.TryGetValue(uri.GetLeftPart(UriPartial.Path), out var a) ? a : new Answer("404 Not Found", "text/plain", Encoding.ASCII.GetBytes("no route"));
            Log($"{method} {target} -> {answer.Status}", uri.Host);
            var body = answer.Body ?? [];
            await Write(stream, $"HTTP/1.1 {answer.Status}\r\n" + (answer.ContentType is null ? "" : $"Content-Type: {answer.ContentType}\r\n")
                + (answer.Location is null ? "" : $"Location: {answer.Location}\r\n") + $"Content-Length: {body.Length}\r\nConnection: close\r\n\r\n");
            if (method != "HEAD") await stream.WriteAsync(body);
            await stream.FlushAsync();
        }
        catch (Exception)
        {
            // A client that gave up (a timeout, a refused certificate) ends here.
        }
    }

    static async Task Write(Stream stream, string text)
    {
        await stream.WriteAsync(Encoding.ASCII.GetBytes(text));
        await stream.FlushAsync();
    }

    // The request line; the rest of the head is read and dropped (log it too when a page shows headers).
    static async Task<string> ReadHead(Stream stream)
    {
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(20));
        var head = new List<byte>();
        var one = new byte[1];
        while (await stream.ReadAsync(one, timeout.Token) == 1)
        {
            head.Add(one[0]);
            if (head.Count >= 4 && head[^1] == 10 && head[^2] == 13 && head[^3] == 10 && head[^4] == 13) break;
        }

        var text = Encoding.ASCII.GetString([.. head]);
        var end = text.IndexOf("\r\n", StringComparison.Ordinal);
        return (end < 0 ? text : text[..end]).Replace(" HTTP/1.1", "");
    }

    public void Dispose()
    {
        listener.Stop();
        certificate?.Dispose();
    }
}
// ===== end: requests =====

// The texts Mask() replaces, with their tokens; Patterns are regular expressions.
static class Masks
{
    public static readonly List<(string Text, string Token)> Pairs = [];
    public static readonly List<(string Pattern, string Token)> Patterns = [];
}
