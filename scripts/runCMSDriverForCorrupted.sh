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
  cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" --scenario pp \
               --datatier NANOAOD --conditions 130X_dataRun3_PromptAnalysis_v1 --step NANO --era Run3 --python_filename configs/CustomNano_Recover_MuonEG_Run2022F_cfg.py \
               --filein "file:CRAB/20250512_DATA_2022EE/4372c542-7772-4594-b484-fb579e0fdd9d.root" \
               --fileout "file:NANOAOD_566.root" --no_exec --data -n -1 || exit $? ;
  
  cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" --scenario pp \
               --datatier NANOAOD --conditions 130X_dataRun3_PromptAnalysis_v1 --step NANO --era Run3_2023 --python_filename configs/CustomNano_Recover_Muon1_Run2023C_cfg.py \
               --filein "file:CRAB/20250509_DATA_2023/10f0bd36-0f37-4144-8be1-61a0c7109d4f.root" \
               --fileout "file:NANOAOD_1602.root" --no_exec --data -n -1 || exit $? ;
elif [ "$RUN" == "local" ]; then
  cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" --scenario pp \
               --datatier NANOAOD --conditions 130X_dataRun3_PromptAnalysis_v1 --step NANO --era Run3 --python_filename localTest/MuonEG/CustomNano_Recover_Run2022F_T1_US_FNAL_Disk_cfg.py \
               --filein "file:T1_US_FNAL_Disk.root" \
               --fileout "file:NANOAOD_T1_US_FNAL_Disk.root" --no_exec --data -n -1 || exit $? ;
  cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" --scenario pp \
                --datatier NANOAOD --conditions 130X_dataRun3_PromptAnalysis_v1 --step NANO --era Run3 --python_filename localTest/MuonEG/CustomNano_Recover_Run2022F_T2_CCH_CSCS_cfg.py \
                --filein "file:T2_CH_CSCS.root" \
                --fileout "file:NANOAOD_T2_CH_CSCS.root" --no_exec --data -n -1 || exit $? ;
  cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" --scenario pp \
                --datatier NANOAOD --conditions 130X_dataRun3_PromptAnalysis_v1 --step NANO --era Run3_2023 --python_filename localTest/Muon1/CustomNano_Recover_Run2023C_T1_FR_CCIN2P3_Disk_cfg.py \
                --filein "file:T1_FR_CCIN2P3_Disk.root" \
                --fileout "file:T1_FR_CCIN2P3_Disk.root" --no_exec --data -n -1 || exit $? ;
  cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" --scenario pp \
                --datatier NANOAOD --conditions 130X_dataRun3_PromptAnalysis_v1 --step NANO --era Run3_2023 --python_filename localTest/Muon1/CustomNano_Recover_Run2023C_T2_FI_HIP_cfg.py \
                --filein "file:T2_FI_HIP.root" \
                --fileout "file:NANOAOD_T2_FI_HIP.root" --no_exec --data -n -1 || exit $? ;
  cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" --scenario pp \
                --datatier NANOAOD --conditions 130X_dataRun3_PromptAnalysis_v1 --step NANO --era Run3_2023 --python_filename localTest/Muon1/CustomNano_Recover_Run2023C_T2_US_Florida_cfg.py \
                --filein "file:T2_US_Florida.root" \
                --fileout "file:NANOAOD_T2_US_Florida.root" --no_exec --data -n -1 || exit $? ;
else
  echo "Invalid run option. Please use 2, 3, or local."
  exit 1
fi
