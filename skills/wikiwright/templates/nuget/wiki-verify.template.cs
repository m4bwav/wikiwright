#:package {{PACKAGE_ID}}@{{VERSION}}
#:property PublishAot=false
// wiki-verify for {{PACKAGE_ID}} {{VERSION}}: runs every example on the wiki against the
// PUBLISHED package from nuget.org, never the working tree. Keep the filled-in copy in
// the repository as ai-docs/notes/<date>-wiki-verify.cs so the next release can run it.
//
// Run it from a folder outside any project cone (a scratch folder; file-based apps pick
// up Directory.Build.props and global.json from parent folders):
//   dotnet run wiki-verify.cs > wiki-verify.out.txt
//
// PublishAot=false: .NET 10 file-based apps enable native AOT by default, which turns off
// reflection-based System.Text.Json and makes such calls throw even under dotnet run.
// Two copies of this file must not run at once from one folder: they share build output.
//
// Every case prints "## <label>" and then its output. Paste outputs into the pages exactly
// as printed; a page never shows output this program did not produce.
using System;
using System.Reflection;
using System.Text;
using {{NAMESPACE}};

Console.OutputEncoding = Encoding.UTF8;

var asm = typeof({{A_PUBLIC_TYPE}}).Assembly;
Show("installed", $"{asm.GetName().Name} {asm.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion} on .NET {Environment.Version}");

// ----- the cases: one per example on the wiki, labelled by page -----
// Getting started
// Show("getting-started", ...);

// Errors: Catch() prints the exception type and message the page quotes.
// Show("null input", Catch(() => ...));

static void Show(string label, object? value)
{
    Console.WriteLine($"## {label}");
    Console.WriteLine(value?.ToString() ?? "<null>");
    Console.WriteLine();
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
