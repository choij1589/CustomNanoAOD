from CRABClient.UserUtilities import config, getUsername

config = config()
### General configuration
config.General.workArea        = '[WORKAREA]'
config.General.requestName     = '[REQUESTNAME]'
config.General.transferOutputs = True
config.General.transferLogs    = False

### JobType configuration
config.JobType.psetName        = '[PSETNAME]'
config.JobType.pluginName      = 'Analysis'
config.JobType.maxMemoryMB     = 2800
config.JobType.allowUndistributedCMSSW = False

### Data configuration
config.Data.inputDataset       = '[INPUTDATASET]'
config.Data.lumiMask           = '[LUMIMASK]'
config.Data.inputDBS           = 'global'
config.Data.splitting          = 'FileBased'
config.Data.unitsPerJob        = 1
config.Data.outLFNDirBase      = '/store/user/%s/SKNano' % (getUsername())
config.Data.publication        = False

### Site configuration
config.Site.storageSite       = 'T3_KR_KNU'
