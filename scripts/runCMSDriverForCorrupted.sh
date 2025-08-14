#!/bin/bash
RUN=$1

if [ "$RUN" == 2 ]; then
  cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
               --datatier NANOAOD --conditions 106X_dataRun2_v35 --step NANO --era Run2_2018,run2_nanoAOD_106Xv2 --python_filename configs/CustomNano_Recover_EGamma2018D_cfg.py \
               --filein "file:CRAB/20250411_DATA_2018/crab_projects/EGamma_Run2018D_347.root" \
               --fileout "file:NANOAOD_347.root" --no_exec --data -n -1 || exit $?

  cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
               --datatier NANOAOD --conditions 106X_dataRun2_v35 --step NANO --era Run2_2018,run2_nanoAOD_106Xv2 --python_filename configs/CustomNano_Recover_SingleMuon2018D_cfg.py \
               --filein "file:CRAB/20250411_DATA_2018/crab_projects/SingleMuon_Run2018D_3288.root" \
               --fileout "file:NANOAOD_3288.root" --no_exec --data -n -1 || exit $?
elif [ "$RUN" == 3 ]; then
  # Run2022F, MuonEG
  cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" --scenario pp \
               --datatier NANOAOD --conditions 130X_dataRun3_PromptAnalysis_v1 --step NANO --era Run3 --python_filename configs/CustomNano_Recover_MuonEG_Run2022F_0_cfg.py \
               --filein "file:FailedJobs/Run2022F/MuonEG/4372c542-7772-4594-b484-fb579e0fdd9d.root" \
               --fileout "file:FailedJobs/Run2022F/MuonEG/NANOAOD_590.root" --nThreads 8 --no_exec --data -n -1 || exit $? ;

  # Run2023C, Muon0_v3
  cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" --scenario pp \
               --datatier NANOAOD --conditions 130X_dataRun3_PromptAnalysis_v1 --step NANO --era Run3_2023 --python_filename configs/CustomNano_Recover_Muon0_v3_Run2023C_0_cfg.py \
               --filein "file:FailedJobs/Run2023C/Muon0_v3/20ef0111-3b5e-4ecf-ac21-6c7a3b8edc83.root" \
               --fileout "file:FailedJobs/Run2023C/Muon0_v3/NANOAOD_71.root" --no_exec --data -n -1 || exit $? ;

  cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" --scenario pp \
               --datatier NANOAOD --conditions 130X_dataRun3_PromptAnalysis_v1 --step NANO --era Run3_2023 --python_filename configs/CustomNano_Recover_Muon0_v3_Run2023C_1_cfg.py \
               --filein "file:FailedJobs/Run2023C/Muon0_v3/d24e24d9-1bcb-4af4-9c44-219df3c628eb.root" \
               --fileout "file:FailedJobs/Run2023C/Muon0_v3/NANOAOD_25.root" --no_exec --data -n -1 || exit $? ;

  # Run2023C, Muon1_v4
  cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" --scenario pp \
               --datatier NANOAOD --conditions 130X_dataRun3_PromptAnalysis_v1 --step NANO --era Run3_2023 --python_filename configs/CustomNano_Recover_Muon1_v4_Run2023C_0_cfg.py \
               --filein "file:FailedJobs/Run2023C/Muon1_v4/10f0bd36-0f37-4144-8be1-61a0c7109d4f.root" \
               --fileout "file:FailedJobs/Run2023C/Muon1_v4/NANOAOD_1256.root" --nThreads 8 --no_exec --data -n -1 || exit $? ;
else
  echo "Invalid run option. Please use 2, 3, or local."
  exit 1
fi
