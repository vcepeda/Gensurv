cd /mnt/storage/ahcepev1/backups/Gensurv/backend

root=/mnt/storage/ahcepev1/Gensurv_data_update07102025/Gensurv_data/SilkePeter
#antibiotics=$(ls $root/Antibiogramme/*.xlsx | grep -v 'gesamt' | tr '\n' ' ')
antibiotics=$(ls $root/Antibiogramme_csv/*.csv | tr '\n' ' ')


python manage.py server_upload \
    --user SilkePeter \
    --metadata $root/Tuebingen_GenSurv_sample_metadata_final.csv \
    --fastq-dir $root \
    --antibiotics $antibiotics \
    --type bacteria \
    --bulk
