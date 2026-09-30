#:package {{PACKAGE_ID}}@{{VERSION}}
#:property PublishAot=false
// wiki-verify for {{PACKAGE_ID}} {{VERSION}}: prints every output the wiki's pages show, run against
// the PUBLISHED package from nuget.org, never the working tree. Keep the filled-in copy in the
// repository as ai-docs/notes/<date>-wiki-verify.cs, and its output beside it as
// ai-docs/notes/<date>-wiki-verify.out.txt with LF line endings (Console.WriteLine writes CRLF on
// Windows: tr -d '\r'), so the next release can run it again and diff (L-019, L-105).
//
// Run it from a folder outside any project cone (a scratch folder; file-based apps pick up
// Directory.Build.props and global.json from parent folders):
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
// here too, through Run(), so their output is in the saved file.
//
// A package that makes requests (HTTP, a web API): read the comment at the top of the first
// "requests" block. A package that makes none: delete both "requests" blocks.
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
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using {{NAMESPACE}};

Console.OutputEncoding = Encoding.UTF8;
var scratch = (string?)AppContext.GetData("EntryPointFileDirectoryPath") ?? Environment.CurrentDirectory;
var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
Masks.Pairs.AddRange([(scratch, "<scratch>"), (Environment.GetEnvironmentVariable("NUGET_PACKAGES") ?? Path.Combine(home, ".nuget", "packages"), "<nuget>"),
    (Path.GetTempPath().TrimEnd(Path.DirectorySeparatorChar), "<temp>"), (home, "<home>")]);

var asm = typeof({{A_PUBLIC_TYPE}}).Assembly;
Show("installed", $"{asm.GetName().Name} {asm.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion?.Split('+')[0]}");

// ===== requests (1 of 2): delete this block and the one at the bottom when the package makes none =====
// Every request goes to StandIn, a proxy on 127.0.0.1 that answers the `.test` host names in `routes`
// (RFC 6761 names that never resolve) and refuses every other host BY ANSWERING: a reply that is not
// HTTP, or 403 to CONNECT. Closing the connection instead makes HttpClient retry (4 GETs or 16 CONNECTs
// on .NET 10, 2 on .NET Framework; L-138). It never opens a socket of its own, and it logs every
// request line with its host. Pages show the `.test` names or label the stand-in; the real hosts are
// never asked (L-116, L-122; references/nuget.md "Packages that make requests").
//
// Request snippets run in child apps, one per build of the package, so a process finds its proxy where
// a user's would: HTTP_PROXY and HTTPS_PROXY on .NET Core and .NET 5+. .NET Framework ignores them, so
// the child sets WebRequest.DefaultWebProxy first; Framework never proxies a loopback address, hence
// `.test` names and never 127.0.0.1 in routes. Restores (the children's builds, dotnet fsi's
// #r "nuget:") run WITHOUT the proxy variables, before the gate (L-137).
// One file, several builds: `#:property TargetFramework=net48` in a file-based app runs .NET Framework
// 4.8 (the package's net46x/net48 build; Windows only), and `net8.0` runs a netstandard2.0 build.
// Requests sent at once arrive in any order: sort their log lines, or print one call per snippet.
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

// The pages' request snippets, exactly as shown; each runs by name in its own child process.
var snippets = new Dictionary<string, string>
{
    // The gate, before any case: the package's default (shared) client and a caller's new HttpClient()
    // must each throw AND be logged by the stand-in exactly once, or the run stops. Replace the calls
    // with the package's request on its default client and on `mine`; both take `url`.
    ["gate"] = """
        foreach (var url in new[] { "http://gate.invalid/", "https://gate.invalid/" })
        {
            Console.WriteLine(url + " default client: " + await Outcome(() => {{DEFAULT_CLIENT_CALL}}));
            using var mine = new HttpClient();
            Console.WriteLine(url + " new HttpClient(): " + await Outcome(() => {{CALLER_CLIENT_CALL}}));
        }
        """,
    // ["getting started: a request"] = """
    //     Console.WriteLine(await ...);
    //     """,
};
var targets = new[] { "net10.0" };   // one per build: "net48" (Windows) for net4x, "net8.0" for netstandard2.0
var children = targets.ToDictionary(t => t, t => BuildChild(scratch, t, snippets));
foreach (var (tfm, child) in children)
{
    var gate = RunSnippet(child, "gate").Split('\n');
    Show($"gate ({tfm})", string.Join("\n", gate));
    if (gate.Count(l => l.Contains(": threw ")) != 4 || gate.Count(l => l.StartsWith("stand-in: ") && l.Contains("gate.invalid")) != 4)
    {
        Console.WriteLine($"GATE FAILED on {tfm}: a call returned, went round the stand-in or was retried. No case ran.");
        Environment.Exit(1);
    }
}

foreach (var (tfm, child) in children)
{
    foreach (var name in snippets.Keys.Where(k => k != "gate"))
    {
        Show($"{name} ({tfm})", RunSnippet(child, name));
    }
}

// An F# snippet that requests: warm fsi's cache without the proxy, then run it under the proxy.
// Run("dotnet", ["fsi", "--quiet", warmFsx], ProxyEnv(null));   // warmFsx holds only the #r line
// Show("getting started: F#", Run("dotnet", ["fsi", "--quiet", fsx], ProxyEnv(standIn)) + "\n" + Seen(standIn.Take()));
Show("stand-in: hosts asked", string.Join("\n", standIn.Hosts));
// ===== end of requests (1 of 2) =====

// ----- the cases: one per example on the wiki, labelled by page -----
// Show("getting started: the first call", ...);
// What a page's code prints with Console.WriteLine, line for line:
// Show("recipes: a loop", Captured(() => { for (var i = 0; i < 3; i++) Console.WriteLine(i); }));
// An unseeded example: print it only when it is a possible answer:
// Possible("home: unseeded examples", ("Prophetstown", SomeGenerator.Names.Contains));
// Errors: Catch() prints the exception type and message the page quotes.
// Show("null input", Catch(() => ...));

// ----- the pages' PowerShell and F# snippets, run as written -----
// var fsx = Path.Combine(Path.GetTempPath(), "wiki-verify.fsx");
// File.WriteAllText(fsx, """
//     #r "nuget: {{PACKAGE_ID}}, {{VERSION}}"
//     ...
//     """);
// Show("getting started: F#", Run("dotnet", ["fsi", "--quiet", fsx]));
// Show("getting started: PowerShell", Run("pwsh", ["-NoProfile", "-NonInteractive", "-Command", """
//     Add-Type -Path "$env:USERPROFILE/.nuget/packages/{{PACKAGE_ID_LOWER}}/{{VERSION}}/lib/netstandard2.0/{{ASSEMBLY}}.dll"
//     ...
//     """]));

static void Show(string label, object? value)
{
    Console.WriteLine($"## {label}");
    Console.WriteLine(Mask(value?.ToString() ?? "<null>"));
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
// line endings. env: a value sets a variable, null removes it (ProxyEnv). Both streams are read at
// once, so a child that writes much to stderr cannot fill that pipe and stall.
static string Run(string file, string[] args, Dictionary<string, string?>? env = null, string? cwd = null)
{
    var info = new ProcessStartInfo(file)
    {
        RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false,
        StandardOutputEncoding = Encoding.UTF8, StandardErrorEncoding = Encoding.UTF8, WorkingDirectory = cwd ?? "",
    };
    foreach (var arg in args)
    {
        info.ArgumentList.Add(arg);
    }

    foreach (var (name, value) in env ?? [])
    {
        if (value is null) info.Environment.Remove(name); else info.Environment[name] = value;
    }

    using var p = Process.Start(info)!;
    var stderr = p.StandardError.ReadToEndAsync();
    var stdout = p.StandardOutput.ReadToEnd();
    p.WaitForExit();
    var text = stdout + (stderr.Result.Length > 0 ? "--- stderr\n" + stderr.Result : "") + (p.ExitCode != 0 ? "--- exit " + p.ExitCode : "");
    return text.Replace("\r\n", "\n").TrimEnd();
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

// Replaces what differs between machines and runs (Masks.Pairs), longest first. On Linux run with a
// distinctive TMPDIR (TMPDIR=/tmp/wiki-verify-tmp): masking a bare /tmp also rewrites content such as
// file:///tmp/a.png.
static string Mask(string text)
{
    foreach (var (from, token) in Masks.Pairs.Where(p => p.Text.Length > 1).OrderByDescending(p => p.Text.Length))
    {
        text = text.Replace(from, token).Replace(from.Replace(Path.DirectorySeparatorChar, '/'), token);
    }

    return text;
}

// ===== requests (2 of 2): the helpers and the stand-in =====
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

// Writes the snippets into a child app for one framework, builds it without the proxy (the restore
// reaches nuget.org) and returns the command that runs it.
static string[] BuildChild(string scratch, string tfm, Dictionary<string, string> snippets)
{
    var dir = Path.Combine(scratch, "children", tfm);
    if (Directory.Exists(dir)) Directory.Delete(dir, true);
    Directory.CreateDirectory(dir);
    var cases = string.Concat(snippets.Select(s => $$"""
            case "{{s.Key}}":
            {
        {{s.Value}}
                break;
            }

        """));
    File.WriteAllText(Path.Combine(dir, "child.cs"), """
        #:package {{PACKAGE_ID}}@{{VERSION}}
        #:property TargetFramework=%TFM%
        #:property PublishAot=false
        #:property LangVersion=latest
        using System;
        using System.Net;
        using System.Net.Http;
        using System.Text;
        using System.Threading.Tasks;
        using {{NAMESPACE}};

        Console.OutputEncoding = Encoding.UTF8;
        #if NETFRAMEWORK
        // .NET Framework ignores HTTP_PROXY: the process's default proxy is set, as machine settings would.
        WebRequest.DefaultWebProxy = new WebProxy(Environment.GetEnvironmentVariable("WIKI_VERIFY_PROXY"));
        #endif
        switch (args[0])
        {
        %CASES%
        }

        static async Task<string> Outcome<T>(Func<Task<T>> call)
        {
            try { return "returned " + await call(); }
            catch (Exception e) { return "threw " + e.GetType().Name; }
        }

        // Trusts only the stand-in's throwaway certificate: for a harness row on an https route.
        static HttpClient StandInClient() => new HttpClient(new HttpClientHandler
        {
            ServerCertificateCustomValidationCallback = (_, cert, _, _) => cert?.GetCertHashString() == Environment.GetEnvironmentVariable("WIKI_VERIFY_THUMBPRINT"),
        });
        """.Replace("%TFM%", tfm).Replace("%CASES%", cases));
    var build = Run("dotnet", ["build", "child.cs", "-o", "bin", "-nologo", "-v:q"], ProxyEnv(null), dir);
    var framework = tfm.StartsWith("net4");
    var output = Path.Combine(dir, "bin", framework ? "child.exe" : "child.dll");
    return File.Exists(output) ? (framework ? [output] : ["dotnet", output]) : throw new Exception($"the {tfm} child did not build:\n{build}");
}

// Runs one snippet under the proxy; prints its output, then the requests the stand-in saw.
string RunSnippet(string[] child, string name)
{
    standIn.Take();
    var output = Run(child[0], [.. child[1..], name], ProxyEnv(standIn), scratch);
    return output + "\n" + Seen(standIn.Take());
}

static string Seen(List<string> requests) => requests.Count == 0 ? "stand-in: no request" : string.Join("\n", requests.Select(r => "stand-in: " + r));

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
// ===== end of requests (2 of 2) =====

// The texts Mask() replaces, with their tokens.
static class Masks
{
    public static readonly List<(string Text, string Token)> Pairs = [];
}
