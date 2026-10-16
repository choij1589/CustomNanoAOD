#!/bin/bash
# Run missing filter efficiency calculations in parallel and merge results

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CALC="$BASE_DIR/scripts/calculateFilterEff.py"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# Missing datasets: "era|dataset_path"
declare -a MISSING=(
  "2016preVFP|/TTToHcToWAToMuMu_MHc-160_MA-35_MultiLepFilter_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL16MiniAODAPVv2-106X_mcRun2_asymptotic_preVFP_v11-v2/MINIAODSIM"
  "2016preVFP|/TTToHcToWAToMuMu_MHc-160_MA-95_MultiLepFilter_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL16MiniAODAPVv2-106X_mcRun2_asymptotic_preVFP_v11-v2/MINIAODSIM"
  "2016postVFP|/TTToHcToWAToMuMu_MHc-160_MA-30_MultiLepFilter_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL16MiniAODv2-106X_mcRun2_asymptotic_v17-v2/MINIAODSIM"
  "2016postVFP|/TTToHcToWAToMuMu_MHc-160_MA-40_MultiLepFilter_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL16MiniAODv2-106X_mcRun2_asymptotic_v17-v2/MINIAODSIM"
  "2016postVFP|/TTToHcToWAToMuMu_MHc-160_MA-135_MultiLepFilter_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL16MiniAODv2-106X_mcRun2_asymptotic_v17-v2/MINIAODSIM"
  "2018|/TTToHcToWAToMuMu_MHc-115_MA-87_MultiLepFilter_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v3/MINIAODSIM"
)

declare -a PIDS=()
declare -a ERAS=()
declare -a DATASETS=()

echo "Starting ${#MISSING[@]} parallel jobs..."
echo "========================================"

for entry in "${MISSING[@]}"; do
    era="${entry%%|*}"
    dataset="${entry##*|}"
    process=$(echo "$dataset" | grep -oP 'TTToHcToWAToMuMu_MHc-\d+_MA-?\d+')
    logfile="$LOG_DIR/${era}_${process}.log"

    echo "Submitting: $process ($era)"
    python3 "$CALC" --era "$era" --sample "$dataset" > "$logfile" 2>&1 &
    PIDS+=($!)
    ERAS+=("$era")
    DATASETS+=("$dataset")
done

echo "========================================"
echo "All jobs submitted. Waiting for completion..."
echo ""

# Wait for all jobs and report status
FAILED=()
for i in "${!PIDS[@]}"; do
    pid=${PIDS[$i]}
    era=${ERAS[$i]}
    dataset=${DATASETS[$i]}
    process=$(echo "$dataset" | grep -oP 'TTToHcToWAToMuMu_MHc-\d+_MA-?\d+')
    wait "$pid"
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "DONE:   $process ($era)"
    else
        echo "FAILED: $process ($era) — see logs/${era}_${process}.log"
        FAILED+=("$i")
    fi
done

echo ""
echo "========================================"
echo "Merging results into era JSON files..."
echo "========================================"

python3 - <<'PYEOF'
import json, re
from pathlib import Path

base = Path('/home/choij/local/workspace/SKNanoMaker_Run2_CMSSW_10_6_28/src/Configuration/CustomNanoAOD/FilterEff')

missing = [
    ("2016preVFP", "TTToHcToWAToMuMu_MHc-160_MA-35"),
    ("2016preVFP", "TTToHcToWAToMuMu_MHc-160_MA-95"),
    ("2016postVFP", "TTToHcToWAToMuMu_MHc-160_MA-30"),
    ("2016postVFP", "TTToHcToWAToMuMu_MHc-160_MA-40"),
    ("2016postVFP", "TTToHcToWAToMuMu_MHc-160_MA-135"),
    ("2018", "TTToHcToWAToMuMu_MHc-115_MA-87"),
]

for era, process in missing:
    sample_file = base / f'sample_{era}_{process}.json'
    results_file = base / f'results_{era}.json'

    if not sample_file.exists():
        print(f"  SKIP: {sample_file.name} not found (job may have failed)")
        continue

    with open(sample_file) as f:
        sample_data = json.load(f)

    if process not in sample_data:
        print(f"  SKIP: {process} not in {sample_file.name}")
        continue

    with open(results_file) as f:
        results = json.load(f)

    results[process] = sample_data[process]

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    eff = sample_data[process]['filter_efficiency']
    err = sample_data[process]['filter_efficiency_error']
    print(f"  MERGED: {process} ({era}): {eff:.4f} +- {err:.4f}")

PYEOF

echo ""
if [ ${#FAILED[@]} -eq 0 ]; then
    echo "All done! Check FilterEff/results_<era>.json for updated values."
else
    echo "Warning: ${#FAILED[@]} job(s) failed. Check logs/ for details."
fi
