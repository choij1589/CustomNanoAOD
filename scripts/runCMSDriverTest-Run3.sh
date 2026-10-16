#!/bin/bash
# Local test: MiniAODv6 -> NanoAODv15 (CMSSW_15_0_22)
# conditions / era follow the PPD Run3 2024 Nano v15 table (docs/Run3_2024_Nano15.md)

# MC: /DYto2L-2Jets_Bin-MLL-50-PTLL-100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v3/MINIAODSIM
cmsDriver.py --eventcontent NANOAODSIM --customise Configuration/DataProcessing/Utils.addMonitoring --datatier NANOAODSIM --conditions 150X_mcRun3_2024_realistic_v4 --step NANO --scenario pp --era Run3_2024 --python_filename test_cfg.py --filein "file:918e7d22-fba2-42a8-be6a-1b71370a4919.root" --fileout "file:NANOAOD.root" --no_exec --mc -n 100

# DATA: /EGamma0/Run2024F-MINIv6NANOv15-v1/MINIAOD
cmsDriver.py --eventcontent NANOAOD --customise Configuration/DataProcessing/Utils.addMonitoring --datatier NANOAOD --conditions 150X_dataRun3_v2 --step NANO --scenario pp --era Run3_2024 --python_filename test_data_cfg.py --filein "file:032970b2-ccdb-445e-8268-5b9781d472eb.root" --fileout "file:NANOAOD_data.root" --no_exec --data -n 100
