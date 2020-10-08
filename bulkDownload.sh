#!/bin/bash


if [[ $# -ne 4 ]]; then echo "USAGE: bulkDownload.sh outDir nameRaDecFile numberToDownload numberToSkip"; exit; fi

mkdir $1

# run getGal.py on each galaxy in the file
awk -v num="$3" -v out="$1" -v skip="$4" '{if (NR > num) {exit}; if (NR <= skip) {next}; if (NR > 0) {system("python2 -W ignore getGal.py " $2 " " $3 " " $1 " -out_dir " out " -min_num_stars 15")}}' $2
