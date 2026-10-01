# Deterministic or seeded output

Read this for a package whose output is seeded or deterministic; it adds to the Library set in [page-sets.md](page-sets.md#library).

When the same input always gives the same output (a seeded generator, a formatter, embedded name lists), the wiki can promise exact output, and should:

- Name the behaviour page after the promise (`Same-Seed-Same-Sequence.md`, `Reproducible-Names.md`). It says what stays the same across runs, runtimes, module systems and versions, each with the run that showed it, and what breaks the promise (a different order of calls, no seed, another library with the same algorithm names, floating-point functions engines approximate).
- Show how the output is consumed, when that decides reproducibility: how many draws each call takes, and that one extra call moves everything after it.
- Run each example twice and under each runtime the pages name, and compare. Save the script's output: seeded output is identical on every run, so the next release diffs it line by line (L-019 `save-the-output-too`). Keep time zones, paths, ports and timings out of it (L-022 `machine-free-output`).

Related: builds on [page-sets.md](page-sets.md); see also [golden-captures.md](golden-captures.md).
