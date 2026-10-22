#!/usr/bin/env bash
# Run from the repo root: bash repro.sh
# Runs the real samples/nano-gpt-data-curation/tests/test.sh, build_train_from_selection.py
# and score.py in a scratch dir, with the absolute paths (/tests, /opt/pool, /logs/verifier,
# /workspace, /tmp) rewritten to point inside it. Two stand-ins, everything else is unchanged:
#  - the pool arrays are built into the Docker image, not in git, so a random pool of the
#    same format is generated and its hashes are written into the scratch SHA256SUMS;
#  - train_nano.py (one H100) is replaced by a stub that writes a fixed heldout_ppl.
#    The values are the task's own anchors from task.toml (random 425.59, reference 367.26).
set -uo pipefail
TASK="$PWD/samples/nano-gpt-data-curation"
R="$(mktemp -d "$PWD/nanogpt-repro.XXXX")"
mkdir -p "$R"/{tests,opt/pool,logs/verifier,workspace/submission,tmp}
cp "$TASK"/tests/* "$R/tests/"
for f in test.sh build_train_from_selection.py score.py; do
  sed -i -e "s#/tests#$R/tests#g" -e "s#/opt/pool#$R/opt/pool#g" -e "s#/logs/verifier#$R/logs/verifier#g" \
         -e "s#/workspace/#$R/workspace/#g" -e "s#/tmp/#$R/tmp/#g" "$R/tests/$f"
done

# stand-in pool: 3000 docs x 4100 tokens (> the 12M-token budget), same layout as build_pool.py
python3 - "$R/opt/pool" <<'PY'
import sys, numpy as np
d, n, L = sys.argv[1], 3000, 4100
np.save(f"{d}/pool_tokens.npy", np.random.default_rng(0).integers(0, 50000, n * (L + 1)).astype(np.uint16))
np.save(f"{d}/pool_meta.npy", np.array([[i * (L + 1), L, 0] for i in range(n)], dtype=np.int64))
PY
{ (cd "$R/opt/pool" && sha256sum pool_tokens.npy pool_meta.npy); grep multi_test.npy "$TASK/tests/SHA256SUMS"; } > "$R/tests/SHA256SUMS"

stub_train() {  # stand-in for train_nano.py: report a fixed held-out perplexity
  cat > "$R/tests/train_nano.py" <<PY
import json, sys
out = sys.argv[sys.argv.index("--out_json") + 1]
json.dump({"heldout_ppl": $1}, open(out, "w")); print("HELDOUT_PPL $1")
PY
}

run() {  # $1 = label, $2 = selection.json content ("" = no file)
  rm -f "$R/workspace/submission/selection.json" "$R/logs/verifier/"*
  [ -n "$2" ] && printf '%s' "$2" > "$R/workspace/submission/selection.json"
  bash "$R/tests/test.sh" > "$R/log.txt" 2>&1
  status=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['status'])" "$R/logs/verifier/result.json")
  printf '%-44s status=%-8s reward.txt=%s\n' "$1" "$status" "$(cat "$R/logs/verifier/reward.txt")"
}

ALL=$(python3 -c "print(list(range(3000)))")
stub_train 425.59; run "fixed selection (stubbed ppl 425.59)" "$ALL"
stub_train 367.26; run "same selection (stubbed ppl 367.26)" "$ALL"
run "no selection.json (agent did nothing)" ""
run "malformed selection.json" "not json"
run "duplicate ids [0, 0]" "[0, 0]"
echo "task.toml direction: $(grep '^direction' "$TASK/task.toml")"
rm -rf "$R"
