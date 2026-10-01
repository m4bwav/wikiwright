#!/usr/bin/env bash
# One headless run of a wikiwright action case, ending with its grade (claude plugin eval
# refuses Bash cases on native Windows). Usage: evals/run-action.sh <out-dir> [baseline]
#
# CASE picks the case (default action-1):
#   action-1  hinted new-wiki Home page ("with a working example and its real output")
#   action-2  unhinted new-wiki Home page (what a user would type)
#   action-3  unhinted update mode ("update the wiki for X") against a repository whose wiki
#             and ai-docs wiki note exist; pages go to ./wiki-draft, nothing is pushed
# REPO is the repository (default m4bwav/TrailerClipperLib for action-1 and action-2, which must
# be one the skill has not touched: no wiki pages and no ai-docs wiki note, or the baseline
# learns the method from the repository, L-013 `baseline-learns-from-run`; default
# m4bwav/get-title-at-url for action-3). UVERSION is action-3's version (default 3.0.0).
#
# Writes <out-dir>/trace.jsonl (stream-json), <out-dir>/work/ (the workspace),
# <out-dir>/exit.txt, and <out-dir>/grade.txt from evals/grade-action.py.
# On Windows keep <out-dir> short (not the session scratchpad): a clone under a long path fails
# (L-016 `scratchpad-path-too-long`). Headless runs share the filesystem with the session that
# starts them: git diff the skill source and the target repository afterwards (L-017).
# The baseline arm disallows the Skill tool. git push and git commit are disallowed in both.
set -u
OUT="$1"
CASE="${CASE:-action-1}"
if [ "$CASE" = "action-3" ]; then
  REPO="${REPO:-m4bwav/get-title-at-url}"
  UVERSION="${UVERSION:-3.0.0}"
else
  REPO="${REPO:-m4bwav/TrailerClipperLib}"
fi
# The package ids the grader accepts an install of (comma-separated) and the tool packages' commands (ID:COMMAND):
# a repository's name is not always its package's.
case "$REPO" in
  */TrailerClipperLib) PACKAGE="${PACKAGE:-TrailerClipper,TrailerClipper.Tool}"; TOOL="${TOOL:-TrailerClipper.Tool:tclipper}" ;;
  */CachingServiceWithAOPSupport) PACKAGE="${PACKAGE:-CachingServiceWithAOPSupport}" ;;
esac
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT/work"
case "$CASE" in
  action-2) PROMPT="Write a Home page for the GitHub wiki of $REPO into ./wiki-draft/Home.md. Don't push or commit anything anywhere." ;;
  action-3) PROMPT="Update the GitHub wiki of $REPO for $UVERSION. Put every page you change in ./wiki-draft/ and don't push or commit anything anywhere." ;;
  *) PROMPT="Draft the Home page of a GitHub wiki for $REPO in ./wiki-draft/Home.md, with a working example and its real output. Check whether the repo's wiki exists first. Don't push or commit anything anywhere." ;;
esac
# One array element per rule: the rules hold spaces, and an unquoted string split them into fragments (before 0.9.0).
DENY=("Bash(git push:*)" "Bash(git commit:*)" "PowerShell(git push:*)" "PowerShell(git commit:*)")
# No system packages and no global tools (the grader fails them too; a child process is beyond these rules).
DENY+=("Bash(winget:*)" "PowerShell(winget:*)" "Bash(dotnet tool install -g:*)" "Bash(dotnet tool install --global:*)")
DENY+=("PowerShell(dotnet tool install -g:*)" "PowerShell(dotnet tool install --global:*)")
if [ "${2:-}" = "baseline" ]; then
  DENY+=("Skill")
fi
echo "$PROMPT" > "$OUT/prompt.txt"
echo "$CASE" > "$OUT/case.txt"
echo "${PACKAGE:-${REPO##*/}}" > "$OUT/package.txt"
[ -n "${TOOL:-}" ] && echo "$TOOL" > "$OUT/tool.txt"
# The package's real hosts, which no run may call (the grader fails a run that does, T-20260929-2): the service a
# package calls, or the hosts its README's examples name (comma-separated). None for a package that makes no
# requests: replace-string-at-position's README names https://example.com only as text inside a string, and
# forbidding it would fail a script that pastes that example as an "unrouted script". TrailerClipperLib's README
# names no host (it runs a local ffmpeg; `--install-ffmpeg` runs a package manager, which the grader fails apart).
case "$REPO" in
  */stack-exchange-markdown-retriever) FORBID_HOST="${FORBID_HOST:-api.stackexchange.com}" ;;
  */IsImageUrlDotNet) FORBID_HOST="${FORBID_HOST:-example.com}" ;;
esac
[ -n "${FORBID_HOST:-}" ] && echo "$FORBID_HOST" > "$OUT/forbid.txt"
(cd "$OUT/work" && claude -p "$PROMPT" --output-format stream-json --verbose \
  --allowedTools "Bash Read Write Edit Glob Grep Skill PowerShell WebFetch" \
  --disallowedTools "${DENY[@]}" > "$OUT/trace.jsonl" 2> "$OUT/stderr.txt")
echo "exit $?" > "$OUT/exit.txt"
python "$HERE/grade-action.py" "$OUT" | tee "$OUT/grade.txt"
