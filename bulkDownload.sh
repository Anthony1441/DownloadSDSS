#!/bin/bash


if [[ $# -ne 3 ]]; then echo "USAGE: bulkDownload.sh outDir nameRaDecFile numberToDownload"; exit; fi

mkdir $1

# run getGal.py on each galaxy in the file
awk -v num="$3" -v out="$1" '{if (NR > 402) {exit} if (NR > 401) {system("python2 -W ignore getGal.py " $2 " " $3 " " $1 " -out_dir " out " -min_num_stars 15")}}' $2
