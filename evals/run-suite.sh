#!/usr/bin/env bash
# The action half of the eval suite, one run at a time, printing one line per run so a suite costs the
# calling session a few hundred tokens instead of every grade (the full grades stay in each run's grade.txt).
# Usage: evals/run-suite.sh <out-root> [case:skill-runs:baseline-runs ...]
#   default plan: action-1:2:1 action-2:2:1 action-3:2:1
# Env: TARGETS  the local clones of the case repositories, separated by ';' (their sibling <clone>.wiki is
#               watched: one that appears during a run is moved aside into <out-root>/moved/, one that existed is
#               reported when its status or HEAD changes); REPO, UVERSION as for run-action.sh.
# After each run: the targets' `git status --short` line count. At the end: `git status --short` of the plugin
# source, since headless runs write to it (L-017 `evals-touch-the-source`: learnings, references, a stray
# package.json). Review every line before committing.
# Keep <out-root> short on Windows (L-016).
set -u
ROOT="$1"
shift
PLAN="${*:-action-1:2:1 action-2:2:1 action-3:2:1}"
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$(cd "$HERE/.." && pwd)"
RUNNER="${RUN_ACTION:-$HERE/run-action.sh}"  # a stub can stand in, to test this driver
mkdir -p "$ROOT/moved"
IFS=';' read -r -a TARGET_LIST <<< "${TARGETS:-}"
declare -A HAD_WIKI WIKI_HEAD
for t in "${TARGET_LIST[@]}"; do
  [ -z "$t" ] && continue
  if [ -d "$t.wiki" ]; then
    HAD_WIKI[$t]=1
    WIKI_HEAD[$t]="$(git -C "$t.wiki" rev-parse HEAD 2>/dev/null)"
  fi
done

after_run() {
  local name="$1" notes=""
  for t in "${TARGET_LIST[@]}"; do
    [ -z "$t" ] && continue
    local base
    base="$(basename "$t")"
    if [ -d "$t.wiki" ] && [ -z "${HAD_WIKI[$t]:-}" ]; then
      mv "$t.wiki" "$ROOT/moved/$name-$base.wiki" && notes="$notes moved:$base.wiki"
    elif [ -n "${HAD_WIKI[$t]:-}" ]; then
      local head dirty
      head="$(git -C "$t.wiki" rev-parse HEAD 2>/dev/null)"
      dirty="$(git -C "$t.wiki" status --short 2>/dev/null | wc -l)"
      [ "$head" != "${WIKI_HEAD[$t]}" ] && notes="$notes $base.wiki-HEAD-moved"
      [ "$dirty" -gt 0 ] && notes="$notes $base.wiki-dirty:$dirty"
    fi
    local changed
    changed="$(git -C "$t" status --short 2>/dev/null | wc -l)"
    notes="$notes $base:$changed"
  done
  echo "$notes"
}

# Cost and minutes from the trace's result event.
trace_stats() {
  python -c "
import json, sys
cost = ms = None
for line in open(sys.argv[1], encoding='utf-8', errors='replace'):
    try:
        e = json.loads(line)
    except ValueError:
        continue
    if e.get('type') == 'result':
        cost, ms = e.get('total_cost_usd'), e.get('duration_ms')
print('\$%.2f %.1fmin' % (cost or 0, (ms or 0) / 60000))
" "$1" 2>/dev/null || echo "? ?"
}

echo "suite: $PLAN -> $ROOT"
for item in $PLAN; do
  IFS=':' read -r case skill base <<< "$item"
  for arm in skill baseline; do
    n=$([ "$arm" = skill ] && echo "${skill:-2}" || echo "${base:-1}")
    for ((i = 1; i <= n; i++)); do
      name="$case-$([ "$arm" = skill ] && echo r || echo b)$i"
      out="$ROOT/$name"
      if [ -f "$out/grade.txt" ]; then
        echo "$name: done before, $(tail -1 "$out/grade.txt")"
        continue
      fi
      if [ "$arm" = skill ]; then
        CASE="$case" bash "$RUNNER" "$out" > /dev/null 2>&1
      else
        CASE="$case" bash "$RUNNER" "$out" baseline > /dev/null 2>&1
      fi
      grade="$(tail -1 "$out/grade.txt" 2>/dev/null || echo 'no grade')"
      echo "$name ($arm): $grade | $(trace_stats "$out/trace.jsonl") | targets$(after_run "$name")"
    done
  done
done
echo "plugin source, git status --short (eval-written files, L-017):"
git -C "$SRC" status --short | sed 's/^/  /'
echo "suite done"
