#!/bin/bash
echo "${$(realpath Makefile)%/*}" > location.txt
mv location.txt ./seq_data/location.txt
