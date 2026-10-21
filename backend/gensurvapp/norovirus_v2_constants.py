"""Schema constants for user-facing Norovirus metadata V2.0.

This schema is intentionally separate from ``NUM_SAR_METADATA_COLUMNS``.
Norovirus V2.0 describes the metadata uploaded by users, while the NUM-SAR
schema describes the downstream RKI/DEMIS representation.

The platform-specific sequencing filenames remain user-facing fields here;
conversion to the downstream RKI file fields is a separate concern.
"""


# DEMIS notificationCategory code used for every Norovirus V2 conversion.
NOROVIRUS_MELDETATBESTAND = "novp"

# Keep partial RKI/NUM-SAR generation frozen until every mandatory target
# field mapping has been agreed and implemented.
NOROVIRUS_RKI_CONVERSION_ENABLED = False


NOROVIRUS_V2_METADATA_COLUMNS = {
    # Sample and isolate information
    "LAB_SEQUENCE_ID": (str, True),
    "SPECIES": (str, True),
    "ISOLATE": (str, False),
    "SUBTYPE": (str, False),
    "Typing_Strategy": (str, False),

    # Sample collection data
    "DATE_OF_SAMPLING": (str, False),
    "ISOLATION_SOURCE": (str, True),
    "Storage Duration": (str, False),
    "County": (str, False),
    "Country": (str, True),

    # Sample collection facility
    "DATE_OF_RECEIVING": (str, True),
    "PRIME_DIAGNOSTIC_LAB.NAME": (str, True),
    "PRIME_DIAGNOSTIC_LAB.EMAIL": (str, True),
    "PRIME_DIAGNOSTIC_LAB.ADDRESS": (str, True),
    "PRIME_DIAGNOSTIC_LAB.CITY": (str, True),
    "PRIME_DIAGNOSTIC_LAB.POSTAL_CODE": (str, True),
    "PRIME_DIAGNOSTIC_LAB.COUNTRY": (str, True),
    "PRIME_DIAGNOSTIC_LAB.FEDERAL_STATE": (str, False),

    # Patient or host details
    "HOST_SEX": (str, False),
    "HOST_BIRTH_MONTH": ((str, int), False),
    "HOST_BIRTH_YEAR": ((str, int), False),
    "Age Group": (str, False),
    "GEOGRAPHIC_LOCATION": (str, False),
    "Patient Status": (str, False),
    "Non patient sample": (str, False),
    "Suspected outbreak": (str, False),

    # Sequencing details
    "SEQUENCING_REASON": (str, True),
    "DATE_OF_SEQUENCING": (str, True),
    "SEQUENCING_LAB.NAME": (str, True),
    "SEQUENCING_LAB.EMAIL": (str, True),
    "SEQUENCING_LAB.ADDRESS": (str, True),
    "SEQUENCING_LAB.CITY": (str, True),
    "SEQUENCING_LAB.POSTAL_CODE": (str, True),
    "SEQUENCING_LAB.COUNTRY": (str, True),
    "SEQUENCING_PLATFORM": (str, True),
    "SEQUENCING_INSTRUMENT": (str, True),
    "Library Preparation Kit": (str, False),
    "ADAPTER": (str, False),
    "NAME_AMP_PROTOCOL": (str, False),
    "PRIMER_SCHEME": (str, False),

    # Uploaded sequencing files
    "Illumina R1": (str, False),
    "Illumina R2": (str, False),
    "Nanopore": (str, False),
    "PacBio": (str, False),

    # Repository information
    "REPOSITORY_NAME": (str, True),
    "REPOSITORY_LINK": (str, False),
    "REPOSITORY_ID": (str, False),
    "UPLOAD_DATE": (str, False),
}


NOROVIRUS_V2_ESSENTIAL_COLUMNS = {
    name: definition
    for name, definition in NOROVIRUS_V2_METADATA_COLUMNS.items()
    if definition[1]
}
