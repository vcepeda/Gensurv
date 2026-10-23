cd /mnt/storage/ahcepev1/backups/Gensurv/backend

root=/mnt/storage/ahcepev1/Gensurv_data_update07102025/Gensurv_data/SandraReuter

python manage.py server_upload \
    --user SandraReuter \
    --metadata $root/FR_metadata_fixed.tsv \
    --fastq-dir $root \
    --type bacteria \
    --bulk
