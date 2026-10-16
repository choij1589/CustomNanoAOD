# CustomNanoAOD
---

## Enviroment setting
for RunII, use CMSSW\_10\_6\_28.
```bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc7_amd64_gcc700
scram p -n SKNanoMaker_RunII_CMSSW_10_6_28 CMSSW CMSSW_10_6_28
cd SKNanoMaker_CMSSW_10_6_28/src
cmsenv
```

for Run3 NanoAODv15 (2022-2025 data, Summer24 MC), use CMSSW\_15\_0\_22 (el9).
```bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=el9_amd64_gcc12
scram p -n SKNanoMaker_Run3_CMSSW_15_0_22 CMSSW CMSSW_15_0_22
cd SKNanoMaker_Run3_CMSSW_15_0_22/src
cmsenv
```

> All Run3 years are NanoAODv15 (PPD tables in [docs/](docs/)). CMSSW\_15\_0\_22 is the latest 15\_0\_X and covers every 150X requirement:
> - 2022/2023: inputs are MiniAODv4 / 22Sep2023 MiniAOD (no MiniAODv6). The official NanoAODv15 used CMSSW\_15\_0\_15\_patch4 with the extra `run3_nanoAOD_pre142X` era modifier.
> - 2024: >= CMSSW\_15\_0\_2 ([docs/Run3\_2024\_Nano15.md](docs/Run3_2024_Nano15.md))
> - 2025: >= CMSSW\_15\_0\_10, `Run3_2025` era ([docs/Run3\_2025\_Nano15.md](docs/Run3_2025_Nano15.md))
> - Summer24 MC, which PPD recommends also for 2025 and 2026: >= CMSSW\_15\_0\_10
>
> 2026 data needs CMSSW\_16\_0\_X (>= 16\_0\_7, `SCRAM_ARCH=el9_amd64_gcc13`): the prompt MiniAOD is made in 16\_0\_X and the `Run3_2026` era exists only there
> ([docs/Run3\_2026\_Nano15.md](docs/Run3_2026_Nano15.md)).

## Adding custom variables
For example, if you want to change the electron varible, check `PhysicsTools/NanoAOD/python/electrons_cff.py`.
```bash
cd $CMSSW_BASE/src
git cms-init
git cms-merge-topic choij1589:from-CMSSW_15_0_22 # Run3 NanoAODv15
#git cms-merge-topic choij1589:from-CMSSW_13_3_1_patch1 # Run3 Nano v13 (legacy)
#git cms-merge-topic choij1589:from-CMSSW_10_6_27 # Run2

# for post process. Not strictly needed.
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools

# always clean and build
scram b clean; scram b -j 8
```

Custom electron branches added on top of the standard NanoAODv15 `Electron` table.
Names follow the EGM custom nano flavour (`_eleVarsExtra` in `electrons_cff.py`), so they differ from the Nano v13 names.

| NanoAODv15 branch | Nano v13 branch | definition (`pat::Electron`) |
|---|---|---|
| `Electron_superclusterPhi` | `Electron_scPhi` | `superCluster().phi()` |
| `Electron_superclusterEnergy` | `Electron_scE` | `superCluster().energy()` |
| `Electron_DeltaEtaInSC` | `Electron_deltaEtaInSC` | `deltaEtaSuperClusterTrackAtVtx` |
| `Electron_DeltaPhiInSC` | `Electron_deltaPhiInSC` | `deltaPhiSuperClusterTrackAtVtx` |
| `Electron_DeltaPhiInSeed` | `Electron_deltaPhiInSeed` | `deltaPhiSeedClusterTrackAtCalo` |
| `Electron_ecalPFClusIso` | `Electron_ecalPFClusterIso` | `ecalPFClusterIso` |
| `Electron_hcalPFClusIso` | `Electron_hcalPFClusterIso` | `hcalPFClusterIso` |
| `Electron_dr03HcalTowerSumEt` | `Electron_dr03HcalTowerSumEt` | `dr03HcalTowerSumEt` |

`Electron_superclusterEta` (Nano v13 custom `Electron_scEta`) is already in the standard NanoAODv15 content.

Get automized scripts:
```bash
mkdir -p Configuration
git clone git@github.com:choij1589/CustomNanoAOD.git Configuration/CustomNanoAOD
```

## Test job
for Run3, download MiniAODv6 files for the local run (MC: RunIII2024Summer24 DY, DATA: Run2024F EGamma0):
```bash
xrdcp root://cms-xrd-global.cern.ch//store/mc/RunIII2024Summer24MiniAODv6/DYto2L-2Jets_Bin-MLL-50-PTLL-100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/MINIAODSIM/150X_mcRun3_2024_realistic_v2-v3/2520001/918e7d22-fba2-42a8-be6a-1b71370a4919.root .
xrdcp root://cms-xrd-global.cern.ch//store/data/Run2024F/EGamma0/MINIAOD/MINIv6NANOv15-v1/90000/032970b2-ccdb-445e-8268-5b9781d472eb.root .
```

Run cmsDriver.py command with:
```bash
./scripts/runCMSDriverTest-Run3.sh
```
It will make test\_cfg.py (MC) and test\_data\_cfg.py (DATA) configuration files. Run these files to make custom NanoAOD files, named NANOAOD.root and NANOAOD\_data.root
```bash
cmsRun test_cfg.py
cmsRun test_data_cfg.py
```
Check the custom electron branches are in the output:
```bash
python3 -c "import ROOT; t = ROOT.TFile.Open('NANOAOD.root').Get('Events'); print([b.GetName() for b in t.GetListOfBranches() if b.GetName().startswith('Electron_')])"
```

## Running cmsDriver.py
To process MiniAOD to NanoAOD, run `cmsDriver.py`.
```bash
./scripts/runCMSDriver.sh $PREFIX # MC_2024 / DATA_2024
```
It will create `configs/CustomNano_$PREFIX_cfg.py`

## Preparing crab submission scripts
```bash
python3 prepare_crab_submission.py -i $DASFILENAME     # submitting single file
python3 prepare_crab_submission.py -l $FILELIST.txt    # submitting list of files, seperated by line
```
The command will print out submission commands. Follow the instructions to submit the crab jobs. Example of filelist can be found in `SampleLists/`

## Automatic Resubmission
copy `templates/resubmit.sh` in the crab directory. It will check the crab job status and resubmit if there is unfinished jobs.
```bash
cd CRAB/$SUBMISSION_DIR
./resubmit.sh
```
> You can change how many crab jobs to be submitted and resubmitted in parallel, change $NTHREAD variable.
> If the resubmission killed by accident, delete `unfinished.txt` or `unfinished.tmp` and re-run the `resubmit.sh`

## Skimming
**Need Update**
You can use `nano_postproc.py` to skim the nanoAOD files. Check the `keep_and_drop.txt` for the variables you want to keep or drop.
```bash
export PATH=$CMSSW_BASE/bin/slc7_amd64_gcc700:$PATH
nano_postproc.py $PWD NANOAOD.root -b keep_and_drop.txt 
```

## Sources
Official NanoAODv15 production settings (`--step NANO`), from McM and the ReqMgr configs of the DAS datasets.
For 2025/2026 prompt data, the release is from DAS and the conditions from the PPD tables; the era string there is the CMSSW era of that year (T0 config not checked).

| era | campaign | input | release | conditions | era string |
|---|---|---|---|---|---|
| MC 2022 | Run3Summer22NanoAODv15 | Run3Summer22MiniAODv4 | CMSSW\_15\_0\_15\_patch4 | 150X\_mcRun3\_2022\_realistic\_v1 | Run3,run3\_nanoAOD\_pre142X |
| MC 2022EE | Run3Summer22EENanoAODv15 | Run3Summer22EEMiniAODv4 | CMSSW\_15\_0\_15\_patch4 | 150X\_mcRun3\_2022\_realistic\_postEE\_v1 | Run3,run3\_nanoAOD\_pre142X |
| MC 2023 | Run3Summer23NanoAODv15 | Run3Summer23MiniAODv4 | CMSSW\_15\_0\_15\_patch4 | 150X\_mcRun3\_2023\_realistic\_v1 | Run3\_2023,run3\_nanoAOD\_pre142X |
| MC 2023BPix | Run3Summer23BPixNanoAODv15 | Run3Summer23BPixMiniAODv4 | CMSSW\_15\_0\_15\_patch4 | 150X\_mcRun3\_2023\_realistic\_postBPix\_v1 | Run3\_2023,run3\_nanoAOD\_pre142X |
| MC 2024 | RunIII2024Summer24NanoAODv15 | RunIII2024Summer24MiniAODv6 | CMSSW\_15\_0\_2 - 15\_0\_17 | 150X\_mcRun3\_2024\_realistic\_v2 | Run3\_2024 |
| DATA 2022 | Run2022\*-NanoAODv15 | Run2022\*-22Sep2023 MINIAOD | CMSSW\_15\_0\_15\_patch4 | 150X\_dataRun3\_v5 | Run3,run3\_nanoAOD\_pre142X |
| DATA 2023 | Run2023\*-NanoAODv15 | Run2023\*-22Sep2023 MINIAOD | CMSSW\_15\_0\_15\_patch4 | 150X\_dataRun3\_v5 | Run3\_2023,run3\_nanoAOD\_pre142X |
| DATA 2024 | Run2024\*-MINIv6NANOv15 | Run2024\*-PromptReco AOD (PAT,NANO) | CMSSW\_15\_0\_2 | 150X\_dataRun3\_v2 | Run3\_2024 |
| DATA 2025 | Run2025\*-PromptReco (T0) | RAW | CMSSW\_15\_0\_6 - 15\_0\_15\_patch4 | 150X\_dataRun3\_Prompt\_v1 | Run3\_2025 |
| DATA 2026 | Run2026\*-PromptReco (T0) | RAW | CMSSW\_16\_0\_2\_patch1 - 16\_0\_7\_patch1 | 161X\_dataRun3\_Prompt\_v1 | Run3\_2026 |

> For 2024 MC, this repo uses `150X_mcRun3_2024_realistic_v4` as in the PPD Run3 2024 Nano v15 table (Summer24 JECs).
> The central production above used `realistic_v2`, which differs only in JECs. See [docs/Run3\_2024\_Nano15.md](docs/Run3_2024_Nano15.md).

- [2022\_MC](https://cms-pdmv-prod.web.cern.ch/mcm/requests?produce=%2FTTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8%2FRun3Summer22NanoAODv15-150X_mcRun3_2022_realistic_v1-v2%2FNANOAODSIM)
- [2022EE\_MC](https://cms-pdmv-prod.web.cern.ch/mcm/requests?produce=%2FTTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8%2FRun3Summer22EENanoAODv15-150X_mcRun3_2022_realistic_postEE_v1-v3%2FNANOAODSIM)
- [2023\_MC](https://cms-pdmv-prod.web.cern.ch/mcm/requests?produce=%2FTTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8%2FRun3Summer23NanoAODv15-150X_mcRun3_2023_realistic_v1-v2%2FNANOAODSIM)
- [2023BPix\_MC](https://cms-pdmv-prod.web.cern.ch/mcm/requests?produce=%2FTTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8%2FRun3Summer23BPixNanoAODv15-150X_mcRun3_2023_realistic_postBPix_v1-v2%2FNANOAODSIM)
- [2024\_MC](https://cms-pdmv-prod.web.cern.ch/mcm/requests?produce=%2FTTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8%2FRunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3%2FNANOAODSIM)
