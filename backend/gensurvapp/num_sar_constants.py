"""
Constants for NUM-SAR metadata validation.

These are intentionally separate from gensurvapp.constants, which currently
contains the Gensurv metadata and antibiotics schema.
"""

NUM_SAR_SUBMISSION_TYPES = {
    "num-sar_bacteria",
    "num-sar_virus",
}

# DEMIS CodeSystem NotificationCategory, version 2.3.1, dated 2026-01-19.
# Source: https://simplifier.net/rki.demis.laboratory/notificationCategory/~overview
# The CodeSystem is case-insensitive; values are normalized to lowercase before validation.
VALID_MELDETATBESTAND_CODES = {
    "abvp", "acbp", "adep", "advp", "astp", "banp", "bobp", "borp",
    "bovp", "bpsp", "brup", "camp", "caup", "chlp", "chtp", "ckvp",
    "clop", "cltp", "corp", "coxp", "cryp", "cvdp", "cvsp", "cymp",
    "denp", "eahp", "ebcp", "ebvp", "echp", "ecop", "ehcp", "etvp",
    "frtp", "fsvp", "gbsp", "gfvp", "gilp", "havp", "hbvp", "hcvp",
    "hdvp", "hevp", "hfap", "hinp", "hivp", "htvp", "invp", "legp",
    "lepp", "lisp", "lsvp", "mbvp", "mpmp", "mpvp", "mpxp", "mrap",
    "mrsp", "msvp", "mylp", "mytp", "ncvp", "negp", "neip", "novp",
    "opxp", "pinp", "pkvp", "plap", "povp", "pvbp", "rbvp", "ricp",
    "rsvp", "rtvp", "ruvp", "salp", "ship", "spap", "spnp", "spyp",
    "styp", "toxp", "trip", "trpp", "vchp", "vzvp", "wbkp", "wnvp",
    "yenp", "ypsp", "zkvp",
}

NUM_SAR_ESSENTIAL_METADATA_COLUMNS = {
    "LAB_SEQUENCE_ID": (str, True),
    "MELDETATBESTAND": (str, True),
    "SPECIES_CODE": (str, True),
    "SEQUENCING_REASON": (str, True),
    "ISOLATION SOURCE_CODE = SAMPLE_TYPE": ((str, int, float), True),
    "DATE_OF_RECEIVING": (str, True),
    "PRIME_DIAGNOSTIC_LAB.CITY": (str, True),
    "PRIME_DIAGNOSTIC_LAB.POSTAL_CODE": ((str, int), True),
    "PRIME_DIAGNOSTIC_LAB.COUNTRY": (str, True),
    "SEQUENCING_LAB.DEMIS_LAB_ID": (str, True),
    "SEQUENCING_LAB.NAME": (str, True),
    "SEQUENCING_LAB.EMAIL": (str, True),
    "SEQUENCING_LAB.ADDRESS": (str, True),
    "SEQUENCING_LAB.CITY": (str, True),
    "SEQUENCING_LAB.POSTAL_CODE": ((str, int), True),
    "SEQUENCING_LAB.COUNTRY": (str, True),
    "REPOSITORY_NAME": (str, True),
    "UPLOAD_STATUS": (str, True),
    "DATE_OF_SEQUENCING": (str, True),
    "SEQUENCING_PLATFORM": (str, True),
    "SEQUENCING_STRATEGY": (str, True),
    "SEQUENCING_INSTRUMENT": (str, True),
    "FILE_1_SHA256SUM": (str, True),
    "FILE_1_NAME": (str, True),
}

NUM_SAR_METADATA_COLUMNS = {
    **NUM_SAR_ESSENTIAL_METADATA_COLUMNS,
    "SPECIES": (str, False),
    "ISOLATE": (str, False),
    "Subtype": (str, False),
    "Typing strategy": (str, False),
    "DATE_OF_SAMPLING": (str, False),
    "ISOLATION SOURCE": (str, False),
    "Storage duration": (str, False),
    "County": (str, False),
    "PRIME_DIAGNOSTIC_LAB.FEDERAL_STATE": (str, False),
    "Country": (str, True),
    "HOST_SEX": (str, False),
    "Age Group": (str, False),
    "HOST_BIRTH_MONTH": ((str, int), False),
    "HOST_BIRTH_YEAR": ((str, int), False),
    "Patient status": (str, False),
    "Non patient sample": (str, False),
    "suspected outbreak": (str, False),
    "Library Preparation Kit": (str, False),
    "NAME_AMP_PROTOCOL": (str, False),
    "FILE_2_SHA256SUM": (str, False),
    "FILE_2_NAME": (str, False),
}