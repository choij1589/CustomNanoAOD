cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
        --datatier NANOAOD --conditions 106X_dataRun2_v35 --step NANO --era Run2_2018,run2_nanoAOD_106Xv2 --python_filename configs/CustomNano_Recover_EGamma2018D_cfg.py \
        --filein "file:CRAB/20250411_DATA_2018/crab_projects/EGamma_Run2018D_347.root" \
        --fileout "file:NANOAOD_347.root" --no_exec --data -n -1 || exit $?

cmsDriver.py --eventcontent NANOAOD --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
        --datatier NANOAOD --conditions 106X_dataRun2_v35 --step NANO --era Run2_2018,run2_nanoAOD_106Xv2 --python_filename configs/CustomNano_Recover_SingleMuon2018D_cfg.py \
        --filein "file:CRAB/20250411_DATA_2018/crab_projects/SingleMuon_Run2018D_3288.root" \
        --fileout "file:NANOAOD_3288.root" --no_exec --data -n -1 || exit $?

