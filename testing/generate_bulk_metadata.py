import pandas as pd
import random
import datetime

# Example list of fastq files (replace with your list or read from a directory)
fastq_files = [
    "test1.fastq", "test2.fastq", "test3.fastq", "test4.fastq",
    "test5.fastq", "test6.fastq", "test7.fastq", "test8.fastq"
]

# Metadata template fields
metadata_columns = [
    "sample identifier", "isolate species", "subtype", "collection date",
    "sampling strategy", "sample source", "collection method",
    "city", "postal code", "county", "state", "country", "lab identifier",
    "sex", "age group", "country of putative exposure",
    "sequencing platform", "sequencing type", "library preparation kit",
    "sequencing chemistry", "illumina r1", "illumina r2", "nanopore", "pacbio",
    "antibiotics file", "antibiotics info"
]

# Helper functions
def random_date():
    return random.choice([
        "15/01/23", "2023-02-20", "10.03.2023", "2024-05-12", "01/12/2022"
    ])

def random_sex():
    return random.choice(["male", "female", "other"])

def random_age_group():
    return random.choice(["adult", "pediatric", "elder"])

def generate_metadata_row(sample_id, fastq):
    platform = random.choice(["Nanopore", "PacBio"])
    row = {
        "sample identifier": sample_id,
        "isolate species": random.choice([562, 28901, 83333]),
        "subtype": f"Serovar{random.choice(['A', 'B', 'C'])}",
        "collection date": random_date(),
        "sampling strategy": random.choice(["surveillance", "outbreak", "research"]),
        "sample source": random.choice(["human clinical (hospital)", "animal", "environment"]),
        "collection method": "swab",
        "city": random.choice(["New York", "Los Angeles", "Chicago"]),
        "postal code": random.choice(["10001", "90001", "60601"]),
        "county": random.choice(["CountyA", "CountyB", "CountyC"]),
        "state": random.choice(["New York", "California", "Illinois"]),
        "country": "USA",
        "lab identifier": f"Lab_{sample_id}",
        "sex": random_sex(),
        "age group": random_age_group(),
        "country of putative exposure": "USA",
        "sequencing platform": platform,
        "sequencing type": "whole genome sequencing",
        "library preparation kit": "",
        "sequencing chemistry": "",
        "illumina r1": "",
        "illumina r2": "",
        "nanopore": fastq if platform == "Nanopore" else "",
        "pacbio": fastq if platform == "PacBio" else "",
        "antibiotics file": "",
        "antibiotics info": f"Resistance to {random.randint(3, 10)} bacteria"
    }
    return row

# Generate the metadata rows
rows = []
for idx, fq in enumerate(fastq_files):
    sample_id = f"Sample_{idx + 1:03d}"
    rows.append(generate_metadata_row(sample_id, fq))

# Create DataFrame and export
df = pd.DataFrame(rows, columns=metadata_columns)
output_file = "bulk_metadata.csv"
df.to_csv(output_file, index=False, sep=';')  # Use semicolon as in your example

print(f"✅ Metadata file '{output_file}' created with {len(df)} samples.")

