#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
PRINT_OUTPUT=0
ALGORITHM="SJF"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --print-output) PRINT_OUTPUT=1; shift ;;
    --algorithm) [[ $# -ge 2 ]] || { echo "Missing value for --algorithm"; exit 2; }; ALGORITHM="${2^^}"; shift 2 ;;
    --algorithm=*) ALGORITHM="${1#*=}"; ALGORITHM="${ALGORITHM^^}"; shift ;;
    *) echo "Unknown option: $1"; echo "Usage: ./run.sh [--algorithm SJF] [--print-output]"; exit 2 ;;
  esac
done
if [[ "$ALGORITHM" != "SJF" ]]; then echo "This project runs SJF only. Use --algorithm SJF or omit the flag."; exit 2; fi
export SIM_ALGORITHM="SJF"
echo "[1/5] Building CloudSim project..."
mvn -q -DskipTests clean package
rm -rf results
mkdir -p results
echo "[2/5] Running SJF simulation..."
JAVA_ARGS=()
if [[ "$PRINT_OUTPUT" == "1" ]]; then JAVA_ARGS+=("-Dexec.args=--print-output"); fi
mvn -q exec:java "${JAVA_ARGS[@]}" > simulation.log 2>&1
if [[ "$PRINT_OUTPUT" == "1" ]]; then
  echo "Detailed output for the representative 1,000-cloudlet run:"
  awk '/^================ OUTPUT ================/{show=1} show{print} /^==========================================/{show=0}' simulation.log
fi
grep -E 'Completed [0-9]+ SJF simulation runs|Results:' simulation.log
echo "[3/5] Validating results..."
python3 scripts/validate_results.py
echo "[4/5] Generating per-dry-run and overall charts..."
python3 scripts/plot_results.py
echo "[5/5] Finished. Results are in: $PROJECT_DIR/results"
