cd /mnt/storage/ahcepev1/backups/Gensurv/backend

root=/mnt/storage/ahcepev1/Gensurv_data_update07102025/Gensurv_data/sgatermann

python manage.py server_upload \
    --user sgatermann \
    --metadata $root/MetaData_fixed.csv \
    --fastq-dir $root \
    --type bacteria \
    --bulk
