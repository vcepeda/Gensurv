#!/bin/bash
# dominikschneider's data is laid out differently from the other users:
# it's 4 separate submissions carried over from the old server, each already
# in its own folder with its own metadata/antibiotics/fastq set (submission
# IDs 338, 364, 365, 366 there - unrelated to this server's IDs). Uploads
# each one separately instead of as one bulk folder.
cd /mnt/storage/ahcepev1/backups/Gensurv/backend

root=/mnt/storage/ahcepev1/Gensurv_data_update07102025/Gensurv_data/dominikschneider

for sub in submission_338 submission_364 submission_365 submission_366; do
    dir=$root/$sub
    metadata=$(ls $dir/sample_metadata*.csv 2>/dev/null | grep -v '/cleaned_' | head -1)
    antibiotics=$(ls $dir/*antibiotics.csv 2>/dev/null | grep -v '/cleaned_' | tr '\n' ' ')

    echo "=== Uploading $sub (metadata: $metadata) ==="
    python manage.py server_upload \
        --user dominikschneider \
        --metadata "$metadata" \
        --fastq-dir "$dir" \
        --antibiotics $antibiotics \
        --type bacteria \
        --bulk
done
