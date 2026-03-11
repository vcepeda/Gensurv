"""
Constants for metadata and antibiotics file validation.
Extracted from views.py for better maintainability and reusability.
"""

# Essential columns required for all submissions
ESSENTIAL_METADATA_COLUMNS = {
    "Sample Identifier": (str, True),  # [Unique ID]
    "Isolate Species": (str, True),     # [NCBI taxonomy ID]
    "Collection Date": (str, True),     # [Day/Month/Year]
}

# Full metadata columns schema
METADATA_COLUMNS = {
    "Sample Identifier": (str, True),    # [Unique ID]
    "Isolate Species": (str, True),      # [NCBI taxonomy ID]
    "Subtype": (str, False),             # (e.g. Serovars) [Text]
    "Collection Date": (str, True),      # [Day/Month/Year]
    "Sampling Strategy": (str, False),   # [surveillance, suspected outbreak, sequencing for diagnostic purposes, other [Text]]
    "Sample Source": (str, True),        # [human clinical (hospital), human screening (hospital), human clinical (community), human screening (community), animal, environment, wastewater, air filter, medical devices, other [Text]]
    "Collection Method": (str, False),   # [swab, blood culture, BAL, aspirate, other [Text]]
    "City": (str, True),
    "Postal Code": (int, True),
    "County": (str, False),
    "State": (str, True),
    "Country": (str, True),
    "Lab Identifier": (str, False),      # [Unique ID]
    "Sex": (str, False),                 # [male, female, other [Text]]
    "Age Group": (str, False),           # [neonate, pediatric, adult, pensioner, NA]
    "Country of Putative Exposure": (str, False),
    "Sequencing Platform": (str, False), # [Illumina, PacBio, ONT, Other [Text]]
    "Sequencing Type": (str, True),      # [whole genome sequencing, amplicon sequencing, metagenome sequencing]
    "Library Preparation Kit": (str, False),
    "Sequencing Chemistry": (str, False),
    # Old field, deprecated:
    # "NGS Files": (str, False),
    "Illumina R1": (str, False),
    "Illumina R2": (str, False),
    "Nanopore": (str, False),
    "PacBio": (str, False),
    "Antibiotics File": (str, False),
    "Antibiotics Info": (str, False),
}

# Antibiotics columns schema
ANTIBIOTICS_COLUMNS = {
    "Testing Method": (str, False),  # Allow only string
    "Tested Antibiotic": (str, True),  # Mandatory string
    "Observed Antibiotic Resistance SIR": (str, True),  # Mandatory string
    "Observed Antibiotic Resistance MIC (mg/L)": ((str, int, float), False),  # Optional, allow str, int, or float
}

# Sex field validation mapping
VALID_SEX_MAPPING = {
    "m": "male",
    "male": "male",
    "f": "female",
    "female": "female",
    "o": "other",
    "other": "other"
}

# Age group validation
VALID_AGE_GROUPS = {"neonate", "pediatric", "adult", "pensioner", "geriatric", "elderly"}

# Sequencing platform validation
VALID_PLATFORMS = {"illumina", "ont", "nanopore", "oxford nanopore", "pacbio"}

# Sampling strategy validation
VALID_SAMPLING_STRATEGIES = ["surveillance", "screening", "suspected outbreak", "other", "diagnostics"]

# Sample source validation
VALID_SAMPLE_SOURCES = [
    "human clinical (hospital)",
    "human screening (hospital)",
    "human clinical (community)",
    "human screening (community)",
    "human clinical",
    "human",
    "human screening",
    "screening",
    "animal",
    "environment",
    "wastewater",
    "air filter",
    "medical devices",
    "other"
]

# Regular expression to match "other" with optional text
OTHER_PATTERN = r"^other(\s*:\s*.+)?$"