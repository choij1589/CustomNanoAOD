# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a CustomNanoAOD framework for CMS (Compact Muon Solenoid) data analysis, designed to create custom NanoAOD files from MiniAOD inputs for both Run2 and Run3 data and Monte Carlo samples. The repository automates the creation of CMSSW configuration files and CRAB submission scripts for large-scale data processing on the CMS computing grid.

## Environment Setup

### Run3 (Current Focus)
For Run3 with Nano v13 (recommended for EGamma mvaNoIso variables):
```bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=el8_amd64_gcc12
scram p -n SKNanoMaker_Run3_CMSSW_13_3_1_patch1 CMSSW CMSSW_13_3_1_patch1
cd SKNanoMaker_Run3_CMSSW_13_3_1_patch1/src
cmsenv
```

### Setup Custom Environment
```bash
cd $CMSSW_BASE/src
git cms-init
git cms-merge-topic choij1589:from-CMSSW_13_3_1_patch1  # Run3 Nano v13
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
scram b clean; scram b -j 8
```

## Core Architecture

### Key Components

1. **Configuration Generation**: Uses `cmsDriver.py` wrapper scripts to generate CMSSW configuration files
2. **CRAB Integration**: Automated CRAB (Computing Resource for Analysis Batch) job submission for grid computing
3. **Sample Management**: Organized dataset lists for different data-taking periods and MC campaigns
4. **Era-specific Processing**: Automatic detection and configuration for different data-taking eras

### Directory Structure

- `configs/`: Generated CMSSW configuration files for different eras
- `scripts/`: Core processing scripts and era-specific parameters
- `templates/`: Template files for CRAB configurations and monitoring scripts
- `SampleLists/`: Dataset lists organized by era (DATA_2022, MC_2023, etc.)
- `CRAB/`: Generated CRAB submission directories with date stamps

## Common Commands

### Generate CMSSW Configuration
```bash
./scripts/runCMSDriver.sh MC_2022      # For MC 2022
./scripts/runCMSDriver.sh DATA_2023    # For Data 2023
```

### Test Local Processing
```bash
./scripts/runCMSDriverTest-Run3.sh     # Generate test configuration
cmsRun test_cfg.py                     # Run local test
```

### CRAB Job Submission
```bash
# Single dataset submission
python3 prepare_crab_submission.py -i /path/to/dataset

# Batch submission from list
python3 prepare_crab_submission.py -l SampleLists/MC_2022.txt

# Execute generated submission script
bash CRAB/YYYYMMDD_PREFIX/submit.sh
```

### Job Monitoring and Resubmission
```bash
cd CRAB/submission_directory
./resubmit.sh  # Automatic monitoring and resubmission of failed jobs
```

## Era Configuration System

The framework uses a two-line configuration system in `scripts/` directory:
- Line 1: Global tag (e.g., `130X_mcRun3_2022_realistic_v5`)
- Line 2: Era string (e.g., `Run3`)

Supported eras:
- **MC**: MC_2016preVFP, MC_2016postVFP, MC_2017, MC_2018, MC_2022, MC_2022EE, MC_2023, MC_2023BPix
- **Data**: DATA_2016preVFP, DATA_2016postVFP, DATA_2017, DATA_2018, DATA_2022, DATA_2022EE, DATA_2023, DATA_2023BPix

## Dataset Management

Dataset lists in `SampleLists/` contain DAS (Data Aggregation System) names for:
- Data samples organized by trigger streams and run periods
- MC samples organized by physics processes and production campaigns
- Automatic era detection based on dataset naming conventions

## CRAB Workflow

1. **Configuration Generation**: `prepare_crab_submission.py` creates CRAB config files
2. **Batch Submission**: Generated `submit.sh` scripts submit multiple jobs in parallel
3. **Monitoring**: `resubmit.sh` checks job status and resubmits failed jobs
4. **Output Management**: Results stored at T3_KR_KNU storage site under `/store/user/username/SKNano`

## Important Notes

- Always run `scram b clean; scram b -j 8` after any CMSSW modifications
- Use appropriate CMSSW version for each era (see README.md for details)  
- The framework automatically handles data/MC detection and applies appropriate configurations
- JSON files (Golden JSONs) are automatically applied for data processing
- Memory allocation is set to 2800MB for CRAB jobs to handle large files
- Extended datasets (with `_ext1`, `_ext2` suffixes) are automatically handled to prevent directory name collisions

## Troubleshooting

- Check global tags and era strings in `scripts/` directory if configuration generation fails
- Verify dataset names using DAS before submission
- Use `crab status -d project_name` to check individual job status
- Failed jobs can be debugged using CRAB log files in project directories