#!/bin/bash
SAMPLELIST=$1

# filter out empty lines and comments
cat $SAMPLELIST | grep -v -e '^$' -e '^#' > ${SAMPLELIST/txt/tmp}

checkDAS() {
    local SAMPLE=$1
    RESULT=$(dasgoclient -query="dataset=$SAMPLE" 2>/dev/null)
    if [[ -z "$RESULT" ]]; then
        echo "Sample does not exist: $SAMPLE"
    else
        echo "Sample exists: $SAMPLE"
    fi
}
export -f checkDAS
parallel checkDAS ::: `cat ${SAMPLELIST/txt/tmp}`
rm ${SAMPLELIST/txt/tmp}