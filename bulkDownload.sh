#!/bin/bash

[[ $# -ne 3 ]] && echo "USAGE: bulkDownload.sh outDir nameRaDecFile numberToDownload"; exit

# run getGal.py on each galaxy in the file
awk "{if (NR >= $3) {exit} if (NR > 1) {system(\"python2 -W ignore getGal.py \" $2 \" \" $3 \" \" $1 \" -out_dir $1 -min_num_stars 20\")}}" $2
