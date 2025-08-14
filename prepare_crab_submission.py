import os
import re
import argparse
from datetime import datetime
parser = argparse.ArgumentParser()
parser.add_argument("--inputDataset", "-i", type=str, default="", help="input dataset as DBS name")
parser.add_argument("--inputList", "-l", type=str, default="", help="list of input dataset list, in textfile")
parser.add_argument("--workArea", "-a", type=str, default="crab_projects", help="name of crab work area")
parser.add_argument("--pilot", action="store_true", default=False)
args = parser.parse_args()

## Check if arguments are valid
if args.inputDataset and args.inputList:
    raise ValueError("Both inputDataset and inputList are given. Please choose one")
elif args.inputDataset:
    print(f"Running on dataset: {args.inputDataset}")
elif args.inputList:
    print(f"Running on dataset list: {args.inputList}")
else:
    raise ValueError("No input dataset is given")


def parseDatasetList(inputList):
    with open(inputList, 'r') as f:
        datasets = f.readlines()
    datasets = [d.strip() for d in datasets]
    datasets = [d for d in datasets if d] # Remove empty lines
    datasets = [d for d in datasets if not d.startswith("#")] # Remove comments
    return datasets

def getRequestInfoFrom(dataset):
    prefix = ""
    lumiMask = ""
    if "RunIISummer20UL16MiniAODAPVv2" in dataset:
        prefix = "MC_2016preVFP"
    elif "RunIISummer20UL16MiniAODv2" in dataset:
        prefix = "MC_2016postVFP"
    elif "RunIISummer20UL17MiniAODv2" in dataset:
        prefix = "MC_2017"
    elif "RunIISummer20UL18MiniAODv2" in dataset:
        prefix = "MC_2018"
    elif "Run3Summer22MiniAODv4" in dataset:
        prefix = "MC_2022"
    elif "Run3Summer22EEMiniAODv4" in dataset:
        prefix = "MC_2022EE"
    elif "Run3Summer23MiniAODv4" in dataset:
        prefix = "MC_2023"
    elif "Run3Summer23BPixMiniAODv4" in dataset:
        prefix = "MC_2023BPix"
    elif "HIPM_UL2016_MiniAODv2" in dataset:
        prefix = "DATA_2016preVFP"
        lumiMask = "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions16/13TeV/Legacy_2016/Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt"
    elif "UL2016_MiniAODv2" in dataset:
        prefix = "DATA_2016postVFP"
        lumiMask = "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions16/13TeV/Legacy_2016/Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt"
    elif "UL2017_MiniAODv2" in dataset:
        prefix = "DATA_2017"
        lumiMask = "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions17/13TeV/Legacy_2017/Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt"
    elif "UL2018_MiniAODv2" in dataset:
        prefix = "DATA_2018"
        lumiMask = "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions18/13TeV/Legacy_2018/Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt"
    elif re.search(r"2022.*22Sep2023*", dataset):
        if "22C" in dataset or "22D" in dataset or "22E" in dataset:
            prefix = "DATA_2022"
        elif "22F" in dataset or "22G" in dataset:
            prefix = "DATA_2022EE"
        else:
            raise NameError(f"Wrong dataset name {dataset}")
        lumiMask = "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions22/Cert_Collisions2022_355100_362760_Golden.json"
    elif "Run2023C" in dataset:
        prefix = "DATA_2023"
        lumiMask = "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions23/Cert_Collisions2023_366442_370790_Golden.json"
    elif "Run2023D" in dataset:
        prefix = "DATA_2023BPix"
        lumiMask = "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions23/Cert_Collisions2023_366442_370790_Golden.json"
    else:
        raise ValueError(f"Cannot parse era from dataset: {dataset}")
    
    if "MC" in prefix:
        info = dataset.split('/')
        physics_process = info[1]
        conditions_part = info[2]
        
        # Extract extension information if present (e.g., _ext1, _ext2)
        ext_suffix = ""
        if "_ext" in conditions_part:
            ext_parts = conditions_part.split("_ext")
            if len(ext_parts) > 1:
                ext_number = ext_parts[1].split("-")[0]  # Extract number after _ext
                ext_suffix = f"_ext{ext_number}"
        
        request_name = f"{prefix}_{physics_process}{ext_suffix}"
    else:
        info = dataset.split('/')
        pd = info[1]
        era = info[2].split('-')[0]
        request_name = f"{prefix}_{pd}_{era}"
        if "2023" in prefix:
            version_suffix = info[2].split('_')[1].split('-')[0]
            request_name += f"_{version_suffix}"
    print("Dataset:", dataset)
    print("prefix:", prefix)
    print("lumiMask:", lumiMask)
    print("Request name:", request_name)
    return prefix, lumiMask, request_name

## Check if the working directory exists
BASEDIR = os.getcwd()
DATE = datetime.now().strftime("%Y%m%d")
# Create a unique directory name based on input dataset or list
if args.inputDataset:
    prefix, lumiMask, request_name = getRequestInfoFrom(args.inputDataset)
    WORKDIR = f"{BASEDIR}/CRAB/{DATE}_{prefix}"
elif args.inputList:
    list_name = os.path.basename(args.inputList).replace('.txt', '')
    WORKDIR = f"{BASEDIR}/CRAB/{DATE}_{list_name}"
else:
    WORKDIR = f"{BASEDIR}/CRAB/{DATE}"
try:
    os.makedirs(WORKDIR, exist_ok=True)
except FileExistsError:
    raise FileExistsError(f"Directory {WORKDIR} already exists. Please remove it before submission.")


## Prepere crab submission scripts
if args.inputDataset:
    print("Submitting CRAB job for dataset:", args.inputDataset)
    prefix, lumiMask, request_name = getRequestInfoFrom(args.inputDataset)
    if lumiMask is None:
        lumiMask = ""
    
    with open(f"{BASEDIR}/templates/crab_config.py", "r") as f:
        template = f.read()
    template = template.replace("[WORKAREA]", args.workArea)
    template = template.replace("[REQUESTNAME]", request_name)
    template = template.replace("[PSETNAME]", f"{BASEDIR}/configs/CustomNano_{prefix}_cfg.py")
    template = template.replace("[INPUTDATASET]", args.inputDataset)
    template = template.replace("[LUMIMASK]", lumiMask)

    with open(f"{WORKDIR}/crab_config_{request_name}.py", "w") as f:
        f.write(template)

    print(f"Crab submission script is saved to {WORKDIR}/crab_config_{request_name}.py")
    print(f"Run `crab submit -c crab_config_{request_name}.py` to submit the job.")
    
if args.inputList:
    datasets = parseDatasetList(args.inputList)
    request_names = []
    if args.pilot:
        datasets = datasets[:1]
    for dataset in datasets:
        print("Submitting CRAB job for dataset:", dataset)
        prefix, lumiMask, request_name = getRequestInfoFrom(dataset)
        if lumiMask is None:
            lumiMask = ""
        
        with open(f"{BASEDIR}/templates/crab_config.py", "r") as f:
            template = f.read()
        template = template.replace("[WORKAREA]", args.workArea)
        template = template.replace("[REQUESTNAME]", request_name)
        template = template.replace("[PSETNAME]", f"{BASEDIR}/configs/CustomNano_{prefix}_cfg.py")
        template = template.replace("[INPUTDATASET]", dataset)
        template = template.replace("[LUMIMASK]", lumiMask)

        with open(f"{WORKDIR}/crab_config_{request_name}.py", "w") as f:
            f.write(template)
        request_names.append(request_name)

    print(f"Crab submission scripts are saved to {WORKDIR}")
    print("Run the following command to submit all jobs in parallel:")
    # Create a submission script
    with open(f"{WORKDIR}/submit.sh", "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write("# Auto-generated submission script\n")
        f.write(f"cd {WORKDIR}\n\n")
        f.write("# Submit crab jobs in parallel (8 at a time)\n")
        f.write("echo \\\n")
        for i, name in enumerate(request_names):
            if i < len(request_names) - 1:
                f.write(f"  \"crab_config_{name}.py\" \\\n")
            else:
                f.write(f"  \"crab_config_{name}.py\" | xargs -P8 -n1 crab submit -c\n")
    
    # Make the script executable
    import os
    os.chmod(f"{WORKDIR}/submit.sh", 0o755)
    
    print(f"Submission script created at {WORKDIR}/submit.sh")
    print(f"Run 'bash {WORKDIR}/submit.sh' to submit all jobs in parallel")

