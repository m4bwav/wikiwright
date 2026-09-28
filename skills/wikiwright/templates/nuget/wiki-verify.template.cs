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
//   dotnet run wiki-verify.cs > out.txt
// Two runs must print the same thing: no times, paths or random values (L-022, L-111).
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
using System;
using System.Linq;
using System.Reflection;
using System.Text;
using {{NAMESPACE}};

Console.OutputEncoding = Encoding.UTF8;

var asm = typeof({{A_PUBLIC_TYPE}}).Assembly;
Show("installed", $"{asm.GetName().Name} {asm.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion?.Split('+')[0]}");

// ----- the cases: one per example on the wiki, labelled by page -----
// Show("getting started: the first call", ...);
// What a page's code prints with Console.WriteLine, line for line:
// Show("recipes: a loop", Captured(() => { for (var i = 0; i < 3; i++) Console.WriteLine(i); }));
// An unseeded example: print it only when it is a possible answer:
// Possible("home: unseeded examples", ("Prophetstown", SomeGenerator.Names.Contains));
// Errors: Catch() prints the exception type and message the page quotes.
// Show("null input", Catch(() => ...));

// ----- the pages' PowerShell and F# snippets, run as written -----
// var fsx = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "wiki-verify.fsx");
// System.IO.File.WriteAllText(fsx, """
//     #r "nuget: {{PACKAGE_ID}}, {{VERSION}}"
//     ...
//     """);
// Show("getting started: F#", Run("dotnet", "fsi", "--quiet", fsx));
// Show("getting started: PowerShell", Run("pwsh", "-NoProfile", "-NonInteractive", "-Command", """
//     Add-Type -Path "$env:USERPROFILE/.nuget/packages/{{PACKAGE_ID_LOWER}}/{{VERSION}}/lib/netstandard2.0/{{ASSEMBLY}}.dll"
//     ...
//     """));

static void Show(string label, object? value)
{
    Console.WriteLine($"## {label}");
    Console.WriteLine(value?.ToString() ?? "<null>");
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
    var writer = new System.IO.StringWriter { NewLine = "\n" };
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

// Runs a page's snippet in another host and returns what it printed, LF line endings.
static string Run(string file, params string[] args)
{
    var info = new System.Diagnostics.ProcessStartInfo(file) { RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false };
    foreach (var arg in args)
    {
        info.ArgumentList.Add(arg);
    }

    using var p = System.Diagnostics.Process.Start(info)!;
    var stdout = p.StandardOutput.ReadToEnd();
    var stderr = p.StandardError.ReadToEnd();
    p.WaitForExit();
    var text = stdout + (stderr.Length > 0 ? "--- stderr\n" + stderr : "") + (p.ExitCode != 0 ? "--- exit " + p.ExitCode : "");
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
