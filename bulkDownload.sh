#!/bin/bash

if [[ $# -eq 0 ]]; then
    echo "USAGE: bulkDownload.sh NAME_RA_DEC_FILE"
    exit 1
fi

awk '{if (NR > 100) {exit} if (NR > 1) {system("python2 -W ignore getGal.py " $2 " " $3 " " $1 " -out_dir testing")}}' $1

#python2 getGal.py 206.167045572 -0.358781446426291 1237648704050168000 
#python2 getGal.py 194.971220988529 -1.1488918446243 1237648702971511000
#python2 getGal.py 168.263522609602 -0.84092437562662 1237648720151839000 


