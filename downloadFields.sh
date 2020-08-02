#!/bin/bash

if [[ $# -eq 0 ]]; then
    echo "USAGE: downloadFields RA DEC outdir"
    exit 1
fi

wget -O - -o /dev/null "https://dr12.sdss.org/fields/raDec?ra=$1&dec=$2" | awk '/bz2/ {print}' | grep -o '".*"' | sed 's;^";https://dr12.sdss.org;g' | sed 's;";;g' | xargs -n1 wget -P $3

bzip2 -d $3/*
