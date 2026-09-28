#!/usr/bin/env bash
# One headless run of wikiwright's action-1 case (claude plugin eval refuses Bash cases on
# native Windows). Usage: evals/run-action.sh <out-dir> [baseline]
# Writes <out-dir>/trace.jsonl (stream-json), <out-dir>/work/ (the workspace), <out-dir>/exit.txt.
# The baseline arm disallows the Skill tool. git push and git commit are disallowed in both.
set -u
OUT="$1"
mkdir -p "$OUT/work"
PROMPT="Draft the Home page of a GitHub wiki for m4bwav/get-title-at-url in ./wiki-draft/Home.md, with a working example and its real output. Check whether the repo's wiki exists first. Don't push or commit anything anywhere."
DENY="Bash(git push:*) Bash(git commit:*) PowerShell(git push:*) PowerShell(git commit:*)"
if [ "${2:-}" = "baseline" ]; then
  DENY="$DENY Skill"
fi
(cd "$OUT/work" && claude -p "$PROMPT" --output-format stream-json --verbose \
  --allowedTools "Bash Read Write Edit Glob Grep Skill PowerShell WebFetch" \
  --disallowedTools $DENY > "$OUT/trace.jsonl" 2> "$OUT/stderr.txt")
echo "exit $?" > "$OUT/exit.txt"
