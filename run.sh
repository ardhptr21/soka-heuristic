#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

PRINT_OUTPUT=0
SHOW_INFO=0
KEEP_PREVIOUS=0
# ALL runs the complete comparison; one or more comma-separated names limit the batch.
ALGORITHM="ALL"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --print-output) PRINT_OUTPUT=1; shift ;;
    --show-info) SHOW_INFO=1; shift ;;
    --keep-previous) KEEP_PREVIOUS=1; shift ;;
    --algorithm)
      [[ $# -ge 2 ]] || { echo "Missing value for --algorithm"; exit 2; }
      ALGORITHM="${2^^}"; shift 2 ;;
    --algorithm=*) ALGORITHM="${1#*=}"; ALGORITHM="${ALGORITHM^^}"; shift ;;
    *) echo "Unknown option: $1"; echo "Usage: ./run.sh [--algorithm NAME[,NAME...]] [--print-output] [--show-info] [--keep-previous]"; exit 2 ;;
  esac
done

IFS=',' read -ra SELECTED_ALGORITHMS <<< "$ALGORITHM"
if [[ "$ALGORITHM" == *ALL* && "$ALGORITHM" != "ALL" ]]; then
  echo "ALL cannot be combined with another algorithm."; exit 2
fi
if [[ "$ALGORITHM" != "ALL" ]]; then
  for selected in "${SELECTED_ALGORITHMS[@]}"; do
    case "$selected" in
      ROUND_ROBIN|MIN_MIN|SJF|MULTI_OBJECTIVE) ;;
      *) echo "Unknown algorithm: $selected"; echo "Use ALL, ROUND_ROBIN, MIN_MIN, SJF, or MULTI_OBJECTIVE."; exit 2 ;;
    esac
  done
fi
export SIM_ALGORITHM="$ALGORITHM"

# Build, simulate, validate, and generate the charts as one repeatable workflow.
echo "[1/5] Building CloudSim project..."
mvn -q -DskipTests clean package

if [[ -d results ]]; then
  if [[ "$KEEP_PREVIOUS" == "1" ]]; then
    backup="results_previous_$(date +%Y%m%d_%H%M%S)"
    mv results "$backup"
    echo "Previous results moved to $backup"
  else
    rm -rf results
  fi
fi
mkdir -p results

echo "[2/5] Running simulation..."
JAVA_ARGS=()
EXEC_ARGS=""
if [[ "$PRINT_OUTPUT" == "1" ]]; then
  EXEC_ARGS="--print-output"
fi
if [[ "$ALGORITHM" != "ALL" ]]; then
  EXEC_ARGS="${EXEC_ARGS:+$EXEC_ARGS }--algorithm=$ALGORITHM"
fi
if [[ -n "$EXEC_ARGS" ]]; then JAVA_ARGS+=("-Dexec.args=$EXEC_ARGS"); fi
if [[ "$SHOW_INFO" == "1" ]]; then
  echo "Raw CloudSim INFO output enabled."
  mvn -q exec:java "${JAVA_ARGS[@]}" | tee simulation.log
else
  mvn -q exec:java "${JAVA_ARGS[@]}" > simulation.log 2>&1
  if [[ "$PRINT_OUTPUT" == "1" ]]; then
    echo "Detailed output for representative runs:"
    awk '/^================ OUTPUT ================/{show=1} show{print} /^==========================================/{show=0}' simulation.log
  fi
  grep -E 'Completed [0-9]+ simulation runs|Results:' simulation.log | tail -n 2
fi

echo "[3/5] Validating results..."
python3 scripts/validate_results.py

echo "[4/5] Generating charts..."
python3 scripts/plot_results.py --algorithm "$ALGORITHM"

echo "[5/5] Finished. Results are in: $PROJECT_DIR/results"
