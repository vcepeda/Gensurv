cd /mnt/storage/ahcepev1/backups/Gensurv/backend

root=/mnt/storage/ahcepev1/Gensurv_data_update07102025/Gensurv_data/ClaudiaStein
antibiotics=$(ls $root/files/Antibiotics/*.csv | tr '\n' ' ')

python manage.py server_upload \
    --user ClaudiaStein \
    --metadata $root/Metadata_upload_Gensurv_UKJ_final.csv \
    --fastq-dir $root \
    --antibiotics $antibiotics \
    --type bacteria \
    --bulk