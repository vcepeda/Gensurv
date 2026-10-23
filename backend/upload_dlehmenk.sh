#!/bin/bash
cd /mnt/storage/ahcepev1/backups/Gensurv/backend

root=/mnt/storage/ahcepev1/Gensurv_data_update07102025/Gensurv_data/dlehmenk

python manage.py server_upload \
    --user dlehmenk \
    --metadata $root/gensurv_ringversuch_metadata.csv \
    --fastq-dir $root \
    --type bacteria \
    --bulk
