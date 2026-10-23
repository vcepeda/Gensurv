#!/bin/bash

root=/mnt/storage/ahcepev1/Gensurv_data_update07102025/Gensurv_data/mellmann
user=mellmann

# auto-detect antibiotics files
antibiotics=$(ls $root/*_Antibiotics.csv 2>/dev/null | tr '\n' ' ')

cd /mnt/storage/ahcepev1/backups/Gensurv/backend

python manage.py server_upload \
    --user $user \
    --metadata $root/Gensurv+RT_BatchUpload_metadata_fixed.csv \
    --fastq-dir $root \
    --antibiotics $antibiotics \
    --type bacteria \
    --bulk
