#!/usr/bin/env bash
# One headless run of wikiwright's action-1 case (claude plugin eval refuses Bash cases on
# native Windows). Usage: evals/run-action.sh <out-dir> [baseline]
# The repository comes from REPO (default m4bwav/seeded-random-utilities): point it at one the
# skill has not touched, with no wiki pages and no ai-docs wiki note, or the baseline learns the
# method from the repository (L-013 `baseline-learns-from-run`).
# Writes <out-dir>/trace.jsonl (stream-json), <out-dir>/work/ (the workspace), <out-dir>/exit.txt.
# On Windows keep <out-dir> short (not the session scratchpad): a clone under a long path fails
# (L-016 `scratchpad-path-too-long`).
# The baseline arm disallows the Skill tool. git push and git commit are disallowed in both.
set -u
OUT="$1"
REPO="${REPO:-m4bwav/seeded-random-utilities}"
mkdir -p "$OUT/work"
case "${CASE:-action-1}" in
  action-2) PROMPT="Write a Home page for the GitHub wiki of $REPO into ./wiki-draft/Home.md. Don't push or commit anything anywhere." ;;
  *) PROMPT="Draft the Home page of a GitHub wiki for $REPO in ./wiki-draft/Home.md, with a working example and its real output. Check whether the repo's wiki exists first. Don't push or commit anything anywhere." ;;
esac
DENY="Bash(git push:*) Bash(git commit:*) PowerShell(git push:*) PowerShell(git commit:*)"
if [ "${2:-}" = "baseline" ]; then
  DENY="$DENY Skill"
fi
echo "$PROMPT" > "$OUT/prompt.txt"
(cd "$OUT/work" && claude -p "$PROMPT" --output-format stream-json --verbose \
  --allowedTools "Bash Read Write Edit Glob Grep Skill PowerShell WebFetch" \
  --disallowedTools $DENY > "$OUT/trace.jsonl" 2> "$OUT/stderr.txt")
echo "exit $?" > "$OUT/exit.txt"
