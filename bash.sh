#!/bin/bash

# Variables
USER="ahcepev1"
SERVER_IP="imgag.de"
REMOTE_DIR="/mnt/storage/ahcepev1/DBBACKUP_STORAGE/data/"
LOCAL_DIR="/home/ahcepev1/projects/gensurv_project/media/uploads"

# Files to transfer
FILES=(
  "MRGN11289_S43_1.fastq.gz"
  "MRGN11289_S43_2.fastq.gz"
  "MRGN11289_metadata.csv"
  "MRGN11289_antibiotics.csv"
  "Citro00327-240828_1.fastq.gz"
  "Citro00327-240828_2.fastq.gz"
  "citro_meta.xlsx"
  "citro_amr.xlsx"
  "Eco05232-240828_1.fastq.gz"
  "Eco05232-240828_2.fastq.gz"
  "Eco05239-240828_1.fastq.gz"
  "Eco05239-240828_2.fastq.gz"
  "Eco05243-240828_1.fastq.gz"
  "Eco05243-240828_2.fastq.gz"
  "Eco05250-240828_1.fastq.gz"
  "Eco05250-240828_2.fastq.gz"
  "Eco05274-240828_1.fastq.gz"
  "Eco05274-240828_2.fastq.gz"
  "eco_meta.xlsx"
  "eco_amr.xlsx"
  "Kpn02419-240828_1.fastq.gz"
  "Kpn02419-240828_2.fastq.gz"
  "Kpn02421-240828_1.fastq.gz"
  "Kpn02421-240828_2.fastq.gz"
  "Kpn02428-240828_1.fastq.gz"
  "Kpn02428-240828_2.fastq.gz"
  "Kpn02429-240828_1.fastq.gz"
  "Kpn02429-240828_2.fastq.gz"
  "Kpn02438-240828_1.fastq.gz"
  "Kpn02438-240828_2.fastq.gz"
  "Kpn02443-240828_1.fastq.gz"
  "Kpn02443-240828_2.fastq.gz"
  "Kpn02444-240828_1.fastq.gz"
  "Kpn02444-240828_2.fastq.gz"
  "kpn_meta.xlsx"
  "kpn_amr.xlsx"
)

# Loop through each file and transfer it
for FILE in "${FILES[@]}"
do
  scp "$USER@$SERVER_IP:$REMOTE_DIR$FILE" "$LOCAL_DIR"
  if [ $? -eq 0 ]; then
    echo "Successfully transferred $FILE"
  else
    echo "Failed to transfer $FILE"
  fi
done

