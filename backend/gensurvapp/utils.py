import pandas as pd
import os
import csv
import io
import re
import time
import requests
import logging
import shutil
from io import BytesIO, StringIO
from collections import Counter
from datetime import datetime
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from functools import lru_cache
from django.conf import settings


logger = logging.getLogger(__name__)


def decode_file_content(content):
    """
    Decode bytes content with fallback encoding support.
    Tries UTF-8 first, then Latin-1, then Windows-1252.
    """
    if not isinstance(content, bytes):
        return content
    
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    
    # If all fail, use UTF-8 with error replacement
    return content.decode('utf-8', errors='replace')


ESSENTIAL_METADATA_COLUMNS = {
    "Sample Identifier": (str, True),#,#[Unique ID]
    "Isolate Species": (str, True),#[NCBI taxonomy ID] 
    "Collection Date": (str, True),#[Day/Month/Year]
    }
# Expected columns and data types for each file type
METADATA_COLUMNS = {
    "Sample Identifier": (str, True),#,#[Unique ID]
    "Isolate Species": (str, True),#[NCBI taxonomy ID] 
    "Subtype": (str, False),#(e.g. Serovars) [Text]
    "Collection Date": (str, True),#[Day/Month/Year]
    "Sampling Strategy": (str, False),#[surveillance, suspected outbreak, sequencing for diagnostic purposes, other [Text]]
    "Sample Source": (str, True),#[human clinical (hospital), human screening (hospital), human clinical (community), human screening (community), animal, environment, wastewater, air filter, nedical devices,other [Text]]
    "Collection Method": (str, False),#[swab, blood culture, BAL, aspirate, other [Text]]
    "City": (str, True),
    "Postal Code": (int, True),
    "County": (str, False),
    "State": (str, True),
    "Country": (str, True),
    "Lab Identifier": (str, False),#[Unique ID]
    "Sex": (str, False),#[male, female, other [Text]),
    "Age Group": (str, False),#[neonate, pediatric, adult, pensioner, NA]
    "Country of Putative Exposure": (str, False),
    "Sequencing Platform": (str, False),#[Illumina, PacBio, ONT, Other [Text]]
    "Sequencing Type": (str, True),#[whole genome sequencing, amplicon sequencing,metagenome sequencing, ]
    "Library Preparation Kit": (str, False),
    "Sequencing Chemistry": (str, False),
    # Old field, deprecated:
    #"NGS Files": (str, False),
    "Illumina R1":(str, False),
    "Illumina R2":(str, False),
    "Nanopore":(str, False),
    "PacBio":(str, False),
    "Antibiotics File": (str, False),
    "Antibiotics Info": (str, False),

    }
ANTIBIOTICS_COLUMNS = {
    "Testing Method": (str, False),  # Allow only string
    "Tested Antibiotic": (str, True),  # Mandatory string
    "Observed Antibiotic Resistance SIR": (str, True),  # Mandatory string
    "Observed Antibiotic Resistance MIC (mg/L)": ((str, int, float), False),  # Optional, allow str, int, or float
}


def detect_delimiter(file):
    """
    Detect the delimiter from a set of known delimiters [',', ';', '\t'] by analyzing the entire file.
    """
    try:
        file.seek(0)  # Ensure the file pointer is at the start
        sample = file.read()        
        
        # Decode if the content is binary
        if isinstance(sample, bytes):
            sample = decode_file_content(sample)
            
        file.seek(0)  # Reset file pointer after reading

        # Define the set of possible delimiters
        delimiters = [',', ';', '\t']

        # Count occurrences of each delimiter in the file
        delimiter_counts = Counter({d: sample.count(d) for d in delimiters})

        # Get the most common delimiter with the highest count
        most_common_delimiter, count = delimiter_counts.most_common(1)[0]

        if count > 0:
            logger.debug(f"Detected delimiter: {repr(most_common_delimiter)} (count: {count})")
            return most_common_delimiter
        else:
            logger.warning("No common delimiters detected. Defaulting to ','.")
            return ','  # Default to comma if no delimiter is detected
    except Exception as e:
        logger.error(f"Error detecting delimiter: {e}")
        raise ValueError(f"Could not detect delimiter: {e}")


def detect_delimiter_dashboard(file):
    """
    Detect the delimiter from a set of known delimiters [',', ';', '\t'] by analyzing the entire file.
    """
    try:
        file.seek(0)  # Ensure the file pointer is at the start
        sample = file.read() # Read the entire file and decode
        file.seek(0)  # Reset file pointer after reading

        # Define the set of possible delimiters
        delimiters = [',', ';', '\t']

        # Count occurrences of each delimiter in the file
        delimiter_counts = Counter({d: sample.count(d) for d in delimiters})

        # Get the most common delimiter with the highest count
        most_common_delimiter, count = delimiter_counts.most_common(1)[0]

        if count > 0:
            logger.debug(f"Detected delimiter: {repr(most_common_delimiter)} (count: {count})")
            return most_common_delimiter
        else:
            logger.warning("No common delimiters detected. Defaulting to ','.")
            return ','  # Default to comma if no delimiter is detected
    except Exception as e:
        logger.error(f"Error detecting delimiter: {e}")
        raise ValueError(f"Could not detect delimiter: {e}")
    

def fix_trailing_empty_columns_new(file, detected_delimiter):
    """
    Fixes issues with CSV/TSV files exported from Excel or manually edited:
    - Preserves quoted fields that contain commas
    - Removes trailing empty columns
    - Strips surrounding quotes from full fields only
    - Returns cleaned content as a StringIO object
    """
    file.seek(0)
    content = file.read()

    if isinstance(content, bytes):
        content = decode_file_content(content)


    # Read CSV with proper handling of quotes and delimiters
    reader = csv.reader(io.StringIO(content), delimiter=detected_delimiter)
    rows = list(reader)

    if not rows:
        raise ValueError("Metadata file is empty or unreadable.")

    # Clean header to determine expected number of columns
    header = rows[0]
    expected_columns = len([col for col in header if col.strip() != ""])
    
    cleaned_data = io.StringIO()
    writer = csv.writer(cleaned_data, delimiter=detected_delimiter, quoting=csv.QUOTE_MINIMAL)

    # Write cleaned header
    writer.writerow([col.strip() for col in header[:expected_columns]])

    # Clean and write each data row
    for i, row in enumerate(rows[1:], start=2):
        trimmed_row = row[:expected_columns]

        if len(row) > expected_columns:
            logger.warning(f"Trimmed extra columns in row {i}: had {len(row)} columns, expected {expected_columns}")

        # Clean each field: strip full surrounding quotes and whitespace
        cleaned_row = []
        for field in trimmed_row:
            field = field.strip()
            if (field.startswith('"') and field.endswith('"')) or (field.startswith("'") and field.endswith("'")):
                field = field[1:-1]
            cleaned_row.append(field)

        writer.writerow(cleaned_row)

    cleaned_data.seek(0)
    return cleaned_data


def fix_trailing_empty_columns(file, detected_delimiter):
    """
    Fixes issues with CSV/TSV files exported from Excel or manually edited:
    - Normalizes encoding (UTF-8)
    - Preserves quoted fields that contain commas
    - Ensures all rows match the header length
    - Removes trailing empty columns
    - Strips surrounding quotes from entire fields or rows
    - Returns cleaned content as a StringIO object
    """
    file.seek(0)
    content = file.read()
    if isinstance(content, bytes):
        content = decode_file_content(content)
    # Normalize quotes added by Excel (e.g., "value", 'value')
    content = content.replace('"', '').replace("'", '')

    lines = content.splitlines()
    if not lines:
        raise ValueError("Metadata file is empty or unreadable.")

    # Clean header
    header_parts = lines[0].split(detected_delimiter)
    while header_parts and header_parts[-1].strip() == "":
        header_parts.pop()
    expected_columns = len(header_parts)
    cleaned_lines = [detected_delimiter.join(header_parts)]

    # Clean each data row
    for i, line in enumerate(lines[1:], start=2):
        parts = line.split(detected_delimiter)
        if len(parts) > expected_columns:
            trimmed = parts[:expected_columns]
            logger.warning(f"Trimmed extra columns in row {i}: had {len(parts)} columns, expected {expected_columns}")
        else:
            trimmed = parts
        cleaned_lines.append(detected_delimiter.join(trimmed))

    return StringIO("\n".join(cleaned_lines))


def handle_excel_to_csv(file):
    """
    Convert an uploaded Excel file (.xlsx) to a CSV file.
    """
    try:
        # Read the Excel file into a DataFrame
        excel_data = pd.read_excel(file)
        
        # Convert the DataFrame to a CSV string
        csv_buffer = BytesIO()
        excel_data.to_csv(csv_buffer, index=False, encoding='utf-8')
        
        # Return the CSV buffer
        csv_buffer.seek(0)  # Reset buffer pointer
        return csv_buffer
    except Exception as e:
        raise ValueError(f"Failed to convert Excel to CSV: {str(e)}")


def generate_cleaned_file(original_filename, df):
    """
    Generates cleaned CSV/Excel file from DataFrame.
    
    Args:
        original_filename: Original filename to determine type
        df: pandas DataFrame to save
    
    Returns:
        ContentFile with cleaned data
    """
    name_root, ext = os.path.splitext(original_filename)

    if ext.lower() == ".xlsx":
        output = BytesIO()
        df.to_excel(output, index=False)
        cleaned = ContentFile(output.getvalue())
        cleaned.name = f"cleaned_{name_root}.xlsx"
    else:
        cleaned = ContentFile(df.to_csv(index=False))
        cleaned.name = f"cleaned_{name_root}.csv"
    
    return cleaned


def is_valid_ncbi_tax_id_or_name(value: str):
    """
    Validate or convert a Taxonomy ID or Name using the NCBI E-Utilities API.

    Parameters:
        value (str): A Taxonomy ID (numeric) or Name (string) to validate or convert.

    Returns:
        tuple: (bool, str) where the boolean indicates validity and the string provides
               the Taxonomy ID if input is a Name, or Name if input is an ID.
    """
    # Numeric Taxonomy ID handling
    if value.isdigit():
        return fetch_taxonomy_name(value)

    # Name-based query using esearch.fcgi
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "taxonomy",  # Target the taxonomy database
        "term": value,     # Search term: can be Name
        "retmode": "json"  # JSON response format
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "esearchresult" in data and "idlist" in data["esearchresult"]:
                id_list = data["esearchresult"]["idlist"]
                if id_list:
                    taxonomy_id = id_list[0]  # Take the first result
                    return fetch_taxonomy_name(taxonomy_id)
            return False, f"No match found for '{value}' in the NCBI Taxonomy database."
        else:
            return False, f"Unexpected API response for '{value}': {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Error while validating '{value}': {e}"


def fetch_taxonomy_name(taxonomy_id: str, retries=3, timeout=20):
    """Fetch the Taxonomy Name for a given Taxonomy ID using NCBI E-Utilities."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {"db": "taxonomy", "id": taxonomy_id, "retmode": "json"}

    for attempt in range(retries):
        try:
            response = requests.get(base_url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            if "result" in data and taxonomy_id in data["result"]:
                result = data["result"][taxonomy_id]
                # Try different possible keys for the name
                name = result.get("scientificname") or result.get("name") or result.get("commonname") or str(taxonomy_id)
                return True, name

            return False, f"Taxonomy ID {taxonomy_id} not found in NCBI database."
        
        except requests.exceptions.Timeout:
            logger.warning(f"NCBI API timeout (attempt {attempt + 1}/{retries})")
            time.sleep(5)  # Wait before retrying
        
        except (requests.exceptions.RequestException, KeyError) as e:
            logger.error(f"NCBI API error: {e}")
            if attempt == retries - 1:
                break  # Only break on last retry
            time.sleep(3)

    return False, f"NCBI API unreachable. Skipping taxonomy validation for {taxonomy_id}."


def validate_sex_field(value):
    """
    Validate and normalize the 'Sex' field.

    - Accepts case-insensitive inputs such as 'M', 'F', 'Male', 'Female', 'O', 'Other'.
    - Maps them to their normalized forms: 'male', 'female', 'other'.
    """
    from .constants import VALID_SEX_MAPPING
    
    if not isinstance(value, str):
        return False, "Invalid data type for 'Sex'. Expected a string."

    # Normalize the input by stripping whitespace and converting to lowercase
    normalized_value = value.strip().lower()

    # Check if the normalized value exists in the mapping
    if normalized_value in VALID_SEX_MAPPING:
        return True, VALID_SEX_MAPPING[normalized_value]  # Return normalized value if valid
    else:
        return False, f"Invalid value for 'Sex': {value}. Accepted values are: {', '.join(VALID_SEX_MAPPING.keys())}."


def validate_age_group_field(value):
    """
    Validate the 'Age Group' field.

    - Accepts case-insensitive inputs for: 'neonate', 'pediatric', 'adult', 'pensioner'.
    - Does not accept abbreviations like 'N', 'P', etc.
    """
    from .constants import VALID_AGE_GROUPS
    
    if not isinstance(value, str):
        return False, "Invalid data type for 'Age Group'. Expected a string."

    # Normalize the input by stripping whitespace and converting to lowercase
    normalized_value = value.strip().lower()

    # Check if the normalized value is in the valid set
    if normalized_value in VALID_AGE_GROUPS:
        return True, normalized_value  # Return normalized value if valid
    else:
        return False, f"Invalid value for 'Age Group': {value}. Accepted values are: {', '.join(VALID_AGE_GROUPS)}."


def validate_mic_value(value):
    """
    Validate the MIC (Minimum Inhibitory Concentration) value.
    - Accepts numbers prefixed with >=, >, <=, <.
    - Handles both plain numeric values and strings with valid prefixes.
    - Handles both dot (`.`) and comma (`,`) as decimal separators.

    Returns:
        bool: True if valid, False otherwise.
    """
    # Convert numeric types to strings for uniform validation
    if isinstance(value, (int, float)):
        value = str(value)
        logger.debug(f"MIC Validation float int : Input='{value}'")

    if isinstance(value, str):
        logger.debug(f"MIC Validation str : Input='{value}'")

        # Normalize commas to dots
        value = value.replace(",", ".")

        # Regular expression for MIC values with optional prefixes
        pattern = r"^(>=|>|<=|<)?\d+(\.\d+)?$"
        if re.match(pattern, value.strip()):
            logger.debug(f"MIC Validation result: Input='{value}' | Valid=True (Pattern Match)")
            return True

        # Allow plain numbers (no prefixes) as valid
        try:
            float(value)  # Attempt to cast to float
            logger.debug(f"MIC Validation result: Input='{value}' | Valid=True (Plain Number)")
            return True
        except ValueError:
            logger.debug(f"MIC Validation result: Input='{value}' | Valid=False (Invalid Format)")
            return False
    return False  # Invalid type


def validate_sequencing_platform_field(value):
    """
    Validate the 'Sequencing Platform' field.

    - Accepts: Illumina, ONT, Nanopore, PacBio, Other: <Text> (case-insensitive).
    - Rejects unrecognized or incomplete 'Other' values.
    """
    from .constants import VALID_PLATFORMS
    
    if not isinstance(value, str):
        logger.debug(f"⚠️ Non-string value received: {value} ({type(value)})")
        return False, "Invalid data type for 'Sequencing Platform'. Expected a string."

    # Normalize the input
    normalized_value = value.strip().lower()
    logger.debug(f"🧪 Normalized platform value: '{normalized_value}'")

    # Check for standard platforms
    if normalized_value in VALID_PLATFORMS:
        return True, normalized_value.capitalize()  # Return normalized value if valid

    # Check for "Other: <description>" format
    if normalized_value.startswith("other:"):
        description = normalized_value[6:].strip()  # Extract description
        if description:
            return True, value  # Return the original "Other: <description>" value if valid
        else:
            return False, "Invalid value for 'Sequencing Platform': 'Other' requires a description (e.g., 'Other: Custom Platform')."

    return False, f"Invalid value for 'Sequencing Platform': {value}. Accepted values are: Illumina, ONT, Nanopore, PacBio, Other: <Text>."


def detect_common_date_format(df, column, expected_formats=None):
    """
    Detect the most common date format in a column.

    Args:
        df (pd.DataFrame): The DataFrame containing the date column.
        column (str): The column to analyze.
        expected_formats (list, optional): List of allowed formats. Defaults to all.

    Returns:
        str: The most common format detected.
        list: Rows that do not match the most common format.
    """
    if expected_formats is None:
        expected_formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d.%m.%Y",
            "%d/%m/%y",
            "%d-%m-%y",
            "%d.%m.%y",
            "%-d/%-m/%y",
            "%-d-%-m-%y",
            "%-d.%-m.%y",
            "%-d/%-m/%Y",
            "%-d-%-m-%Y",
            "%-d.%-m.%Y",
        ]

    format_counts = Counter()
    mismatched_rows = []

    for index, value in df[column].dropna().items():
        matched_format = None
        for fmt in expected_formats:
            try:
                # Try parsing the date
                datetime.strptime(value, fmt)
                matched_format = fmt
                format_counts[fmt] += 1
                break
            except ValueError:
                continue

        if matched_format is None:
            mismatched_rows.append(index)

    most_common_format = format_counts.most_common(1)
    return most_common_format[0][0] if most_common_format else None, mismatched_rows


def validate_and_normalize_date(date_str, expected_formats=None, debug=False):
    """
    Validate that the date string matches one of the allowed formats and normalize it.

    Args:
        date_str (str): The date string to validate.
        expected_formats (list, optional): List of formats to validate against.
        debug (bool): If True, prints detailed validation steps.

    Returns:
        tuple: (bool, str) indicating whether the date is valid and either the normalized date (if valid) or an error message.
    """
    # Define programmer formats and their user-friendly equivalents
    format_mappings = {
        "%d/%m/%Y": "dd/mm/YYYY",
        "%d-%m-%Y": "dd-mm-YYYY",
        "%d.%m.%Y": "dd.mm.YYYY",
        "%d/%m/%y": "dd/mm/YY",
        "%d-%m-%y": "dd-mm-YY",
        "%d.%m.%y": "dd.mm.YY",
        "%-d/%-m/%y": "d/m/YY",
        "%-d-%-m-%y": "d-m-YY",
        "%-d.%-m.%y": "d.m.YY",
        "%-d/%-m/%Y": "d/m/YYYY",
        "%-d-%-m-%Y": "d-m-YYYY",
        "%-d.%-m.%Y": "d.m.YYYY",
    }

    # Default formats if none provided
    if expected_formats is None:
        expected_formats = list(format_mappings.keys())

    if debug:
        print(f"Validating date string: {date_str}")

    for fmt in expected_formats:
        try:
            # Parse the date
            parsed_date = datetime.strptime(date_str, fmt)
            if debug:
                print(f"Date {date_str} matches format {fmt}")

            # Normalize to ISO 8601 (standard Python datetime string)
            normalized_date = parsed_date.strftime("%Y-%m-%d")
            return True, normalized_date
        except ValueError:
            if debug:
                print(f"Date {date_str} does not match format {fmt}")
            continue

    # If no format matches, return user-friendly error
    user_friendly_formats = [format_mappings.get(fmt, fmt) for fmt in expected_formats]
    return False, (
        f"Invalid date format: '{date_str}'. "
        f"Accepted formats are: {', '.join(user_friendly_formats)} (e.g. '12-04-2024', '1.1.24')"
    )


def validate_csv_columns(df: pd.DataFrame, expected_columns: dict):
    """
    Validates the columns of a CSV file against expected schema.

    Args:
        df (pd.DataFrame): The DataFrame loaded from the CSV file.
        expected_columns (dict): A dictionary defining expected columns, their types, and whether they are mandatory.

    Returns:
        dict: Validation results with keys:
              - `is_valid`: (bool) True if validation passed.
              - `missing_columns`: (list) List of missing mandatory columns.
              - `extra_columns`: (list) List of unexpected columns.
              - `type_mismatches`: (list) Descriptions of type mismatches or validation errors.
              - `invalid_values`: (list) Invalid values in mandatory fields.
    """
    validation_results = {
        "is_valid": True,
        "missing_columns": [],
        "extra_columns": [],
        "type_mismatches": [],
        "invalid_values": []
    }

    # Normalize column names for case-insensitive comparison
    df.columns = df.columns.str.lower().str.strip()
    normalized_expected_columns = {key.lower().strip(): value for key, value in expected_columns.items()}
    valid_extensions = (".fastq", ".fq", ".bam", ".fastq.gz", ".fq.gz", ".bam.gz", ".bz2", ".xz", ".zip")
    
    # Log column types
    for col in df.columns:
        logger.debug(f"→  VALIDATE_CSV_COLUMNS '{col}' type: {df[col].dtype}")
    
    # Row-wise logging for debugging
    for idx, row in df.iterrows():
        logger.debug(f"\n🧾 VALIDATE_CSV_COLUMNS Row {idx + 1}:")
        for col in df.columns:
            logger.debug(f"• {col.strip()}: {row[col]}")

    # Explicitly cast the Postal Code column to int if it exists
    if "postal code" in df.columns:
        try:
            df["postal code"] = df["postal code"].astype(int)
            logger.debug(f"Postal Code Column After Casting: {df['postal code']}")
        except ValueError as e:
            logger.error(f"Failed to convert Postal Code to int: {e}")
            validation_results["is_valid"] = False
            validation_results["type_mismatches"].append(
                "postal code: Could not be converted to integers due to invalid values."
            )
    
    # Explicitly cast the "collection date" column to str if it exists        
    if "collection date" in df.columns:
        logger.debug("📅 Pre-validating 'collection date' column globally")
        
        if pd.api.types.is_datetime64_any_dtype(df["collection date"]):
            logger.debug("→ Column is datetime64; formatting as DD-MM-YYYY")
            df["collection date"] = df["collection date"].dt.strftime("%d-%m-%Y")
        else:
            logger.debug("Column 'Collection Date' is not a datetime object; assuming string format.")
        logger.debug("→ Final collection date values:\n" + df["collection date"].to_string(index=False))

    # Check for missing mandatory columns
    mandatory_columns = [col for col, (_, is_mandatory) in normalized_expected_columns.items() if is_mandatory]
    missing_columns = [col for col in mandatory_columns if col not in df.columns]
    if missing_columns:
        validation_results["is_valid"] = False
        validation_results["missing_columns"] = missing_columns

    # Check for extra columns
    all_expected_columns = set(normalized_expected_columns.keys())
    extra_columns = set(df.columns) - all_expected_columns
    if extra_columns:
        validation_results["is_valid"] = False
        validation_results["extra_columns"] = list(extra_columns)
    
    # Validate each column for type and special rules
    for column, (expected_types, is_mandatory) in normalized_expected_columns.items():
        if column in df.columns:
            # Normalize values by stripping spaces/tabs
            df[column] = df[column].apply(lambda x: str(x).strip() if pd.notnull(x) else x)
            
            # Convert all values to string, strip spaces, then treat blanks and 'nan' as NA
            normalized_col = df[column].astype(str).str.strip().replace(["", "nan", "NaN", "None"], pd.NA)
            non_empty_values = normalized_col.dropna()

            # Check mandatory columns for empty values
            if is_mandatory:
                empty_rows = normalized_col[normalized_col.isna()].index.tolist()

                if empty_rows:
                    logger.debug(f"EMPTY ROWS in '{column}': {empty_rows}")
                    validation_results["is_valid"] = False
                    validation_results["invalid_values"].append(
                        f"{column}: Empty values found in row(s): {', '.join(map(str, normalized_col[normalized_col.isna()].index + 1))}"
                    )

            # Validate non-empty values for optional columns
            if not is_mandatory and not non_empty_values.empty:
                invalid_values = non_empty_values[
                    ~non_empty_values.map(lambda x: isinstance(x, expected_types))
                ]
                if not invalid_values.empty:
                    validation_results["is_valid"] = False
                    validation_results["type_mismatches"].append(
                        f"{column}: Non-empty values must be of type {expected_types}. "
                        f"Invalid values found in row(s): {', '.join(map(str, invalid_values.index + 1))}"
                    )

            # MIC-specific validation
            if column == "observed antibiotic resistance mic (mg/l)":
                logger.debug(f"Special case for MIC validation")
                
                invalid_mic_values = non_empty_values[
                    ~non_empty_values.map(lambda x: validate_mic_value(str(x)))
                ]

                if not invalid_mic_values.empty:
                    validation_results["is_valid"] = False
                    validation_results["type_mismatches"].append(
                        f"{column}: Invalid MIC values found in row(s): {', '.join(map(str, invalid_mic_values.index + 1))}. "
                        f"MIC values must be numeric and may include prefixes like >=, >, <=, <. Examples: 0.5, >=4, <0.125."
                    )

            # Special validations for specific fields
            if column == "sex" and not non_empty_values.empty:
                for idx, val in non_empty_values.items():
                    is_valid, result = validate_sex_field(val)
                    if not is_valid:
                        validation_results["is_valid"] = False
                        validation_results["type_mismatches"].append(f"Row {idx + 1}, Sex: {result}")

            if column == "age group" and not non_empty_values.empty:
                for idx, val in non_empty_values.items():
                    is_valid, result = validate_age_group_field(val)
                    if not is_valid:
                        validation_results["is_valid"] = False
                        validation_results["type_mismatches"].append(f"Row {idx + 1}, Age Group: {result}")

            if column == "sequencing platform" and not non_empty_values.empty:
                for idx, val in non_empty_values.items():
                    is_valid, result = validate_sequencing_platform_field(val)
                    if not is_valid:
                        validation_results["is_valid"] = False
                        validation_results["type_mismatches"].append(f"Row {idx + 1}, Sequencing Platform: {result}")

            if column == "collection date" and not non_empty_values.empty:
                for idx, val in non_empty_values.items():
                    is_valid, result = validate_and_normalize_date(val)
                    if not is_valid:
                        validation_results["is_valid"] = False
                        validation_results["type_mismatches"].append(f"Row {idx + 1}, Collection Date: {result}")

            if column == "isolate species" and not non_empty_values.empty:
                for idx, val in non_empty_values.items():
                    is_valid, result = is_valid_ncbi_tax_id_or_name(val)
                    if not is_valid:
                        validation_results["is_valid"] = False
                        validation_results["type_mismatches"].append(f"Row {idx + 1}, Isolate Species: {result}")

    # Custom validation: Ensure at least one NGS platform field is filled
    all_ngs_fields = ["illumina r1", "illumina r2", "nanopore", "pacbio"]
    available_ngs_fields = [field for field in all_ngs_fields if field in df.columns]
    logger.debug(f"Available NGS fields: {available_ngs_fields}")
    
    if available_ngs_fields:
        ngs_fields = ["illumina r1", "nanopore", "pacbio"]
        has_ngs_data = df.apply(
            lambda row: any(
                field in df.columns and pd.notna(row[field]) and str(row[field]).strip() != ""
                for field in ngs_fields
            ),
            axis=1
        )

        if not has_ngs_data.all():
            missing_rows = has_ngs_data[~has_ngs_data].index + 1
            validation_results["is_valid"] = False
            validation_results["invalid_values"].append(
                f"At least one NGS platform file (Illumina R1, Nanopore, or PacBio) must be provided. "
                f"Missing in row(s): {', '.join(map(str, missing_rows))}"
            )

        # Illumina R2 cannot be filled unless R1 is also filled
        if "illumina r2" in df.columns:
            r2_without_r1 = df[
                (pd.notna(df["illumina r2"])) & (df["illumina r2"].astype(str).str.strip() != "") &
                ((pd.isna(df["illumina r1"])) | (df["illumina r1"].astype(str).str.strip() == ""))
            ]
            if not r2_without_r1.empty:
                invalid_rows = r2_without_r1.index + 1
                validation_results["is_valid"] = False
                validation_results["invalid_values"].append(
                    f"Illumina R2 cannot be provided without Illumina R1. "
                    f"Invalid in row(s): {', '.join(map(str, invalid_rows))}"
                )
                
    logger.debug("Validation Results:\n" + str(validation_results))
    return validation_results


def validate_and_save_csv(file, expected_columns, essential_columns=None):
    """
    Validates and saves a CSV or Excel (.xlsx) file by:
    - Detecting delimiters (For CSV files)
    - Fixing trailing/empty columns and inconsistent quoting (For CSV files)
    - Reading the file into a DataFrame
    - Performing schema and logic validation
    
    Returns:
        tuple: (is_valid: bool, has_warnings: bool, message: str, delimiter: str, dataframe: pd.DataFrame or None)
    """
    logger.debug(f"Validating file: {getattr(file, 'name', 'Unknown')} (type: {type(file)})")

    has_errors = False
    has_warnings = False
    error_messages = []
    warning_messages = []

    ext = os.path.splitext(file.name)[1].lower()

    # Read the file into a DataFrame
    try:
        if ext == ".xlsx":
            # Convert Excel to CSV
            csv_buffer = handle_excel_to_csv(file)
            delimiter = ","
            df = pd.read_csv(csv_buffer, sep=delimiter)
        else:
            # Detect delimiter and clean CSV
            delimiter = detect_delimiter(file)
            cleaned_file = fix_trailing_empty_columns_new(file, delimiter)
            df = pd.read_csv(cleaned_file, sep=delimiter)

        df.columns = df.columns.str.lower().str.strip()

        # Accept short alias for antibiotics SIR column.
        # If users upload a column named only 'SIR', normalize it to the canonical name.
        if "sir" in df.columns and "observed antibiotic resistance sir" not in df.columns:
            df = df.rename(columns={"sir": "observed antibiotic resistance sir"})

        logger.debug(f"DataFrame shape after trimming: {df.shape}")
        logger.debug(f"File read into DataFrame successfully:\n{df.head()}")

        # Log all detected column names
        logger.debug(f"Columns detected: {list(df.columns)}")

        # Print the entire DataFrame to verify parsing
        logger.debug("\nFull DataFrame content:\n" + df.to_string())

        # Log each column separately for better debugging
        for column in df.columns:
            logger.debug(f"\nColumn: {column}\n{df[column].to_string(index=False)}")

    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return False, False, f"Error reading file: {str(e)}", None, None

    # Validate the DataFrame using `validate_csv_columns`
    logger.debug("Entering def validate_csv_columns")

    validation_results = validate_csv_columns(df, expected_columns)

    # Separate essential from non-essential issues
    if essential_columns:
        essential_missing = [col for col in validation_results["missing_columns"] if col in [c.lower() for c in essential_columns.keys()]]
        if essential_missing:
            has_errors = True
            error_messages.append(f"Missing essential columns: {', '.join(essential_missing)}")

    # Handle warnings instead of failing
    if not validation_results["is_valid"]:
        # Missing mandatory columns
        if validation_results["missing_columns"]:
            has_warnings = True
            warning_messages.append(
                f"Missing mandatory columns: {', '.join(validation_results['missing_columns'])}"
            )

        # Extra columns
        if validation_results["extra_columns"]:
            has_warnings = True
            warning_messages.append(
                f"Extra columns detected: {', '.join(validation_results['extra_columns'])}"
            )

        # Type mismatches or other validation issues
        if validation_results["type_mismatches"]:
            has_warnings = True
            warning_messages.append(
                "\n".join(validation_results["type_mismatches"])
            )
                
        # Invalid (empty) values in mandatory fields
        if validation_results.get("invalid_values"):
            has_warnings = True
            warning_messages.append(
                "\n".join(validation_results["invalid_values"])
            )

    # Combine all messages
    if has_warnings:
        return True, True, "\n".join(warning_messages), delimiter, df
    if has_errors:
        return False, False, "\n".join(error_messages), delimiter, None

    # If validation is successful
    logger.info("Validation successful.")
    return True, False, "Validation successful.", delimiter, df

def parse_metadata_sample_ids(metadata_file_path):
    """
    Parse the metadata file for single uploads to extract the first row's Sample Identifier.
    Detects delimiter dynamically.

    Args:
        metadata_file_path (str): Path to the metadata file.

    Returns:
        str: The Sample Identifier from the first row (excluding the header).
    """
    try:
        with default_storage.open(metadata_file_path, 'r') as file:
            # Detect the delimiter dynamically
            delimiter = detect_delimiter_dashboard(file)
            logger.debug(f"Detected delimiter for metadata file {metadata_file_path}: {delimiter}")
            cleaned_file = fix_trailing_empty_columns_new(file, delimiter)

            # Read the file into a DataFrame
            df = pd.read_csv(cleaned_file, sep=delimiter)
            df.columns = df.columns.str.lower().str.strip()  # Normalize column names
            logger.debug(f"Metadata file read into DataFrame successfully:\n{df.head()}")

            # Extract Sample Identifier from the first row after the header
            if 'sample identifier' in df.columns and not df.empty:
                sample_id = df.loc[0, 'sample identifier']
                logger.debug(f"Extracted Sample Identifier: {sample_id}")
                return sample_id
            else:
                logger.error(f"'Sample Identifier' column not found or metadata file is empty: {metadata_file_path}")
                return None

    except Exception as e:
        logger.error(f"Error parsing metadata file {metadata_file_path}: {e}")
        return None

@lru_cache(maxsize=64)  # adjust size if needed
def cached_parse_metadata_antibiotics_info(metadata_path):
    return parse_metadata_antibiotics_info(metadata_path)

@lru_cache(maxsize=128)
def cached_parse_metadata_sample_ids(metadata_path):
    return parse_metadata_sample_ids(metadata_path)

def parse_metadata_antibiotics_info(metadata_path, target_sample_id=None):
    """
    Extracts 'Antibiotics Info' per sample from the metadata file.

    If `target_sample_id` is given, return the string for that sample only.
    If `target_sample_id` is None, return a dict mapping all sample_ids → info.
    """
    try:
        with open(metadata_path, 'r') as file:
            delimiter = detect_delimiter(file)
            cleaned_file = fix_trailing_empty_columns_new(file, delimiter)
            df = pd.read_csv(cleaned_file, sep=delimiter)
            df.columns = df.columns.str.lower().str.strip()

            if "sample identifier" not in df.columns:
                raise ValueError("Metadata missing 'sample identifier' column.")

            if "antibiotics info" not in df.columns:
                return {} if target_sample_id is None else None

            df = df[["sample identifier", "antibiotics info"]].dropna(subset=["sample identifier"])

            # Normalize sample IDs and info
            df["sample identifier"] = df["sample identifier"].astype(str).str.strip()
            df["antibiotics info"] = df["antibiotics info"].astype(str).str.strip()

            # Option 1: Return all as a dict
            if target_sample_id is None:
                return {
                    row["sample identifier"]: row["antibiotics info"]
                    for _, row in df.iterrows()
                    if row["antibiotics info"] and str(row["antibiotics info"]).strip().lower() != "nan"
                }

            # Option 2: Return specific sample info
            sample_row = df[df["sample identifier"] == target_sample_id]
            if not sample_row.empty:
                value = sample_row.iloc[0]["antibiotics info"]
                if pd.notna(value) and str(value).strip().lower() != "nan":
                    return str(value).strip()

    except Exception as e:
        print(f"Error parsing antibiotics info: {e}")

    return {} if target_sample_id is None else None

def admin_only_upload_test(user):
    return user.is_superuser or user.is_staff  

def archive_file_to_submission_history(submission, old_file_field, original_filename, file_type, resubmission_count):
    """
    Move a file to: media/submissions/<username>/submission_<id>/history/resubmission_<n>/filename
    """
    username = submission.user.username
    submission_id = submission.pk
    src_path = old_file_field.path

    # Build target path (same resubmission_count used for raw and cleaned)
    target_path = os.path.join(
        settings.MEDIA_ROOT,
        'submissions',
        username,
        f'submission_{submission_id}',
        'history',
        f'resubmission_{resubmission_count}',
        original_filename
    )

    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    # Move file
    shutil.move(src_path, target_path)

    # Return relative path for FileHistory (what goes into FileField)
    relative_path = os.path.join(
        'submissions',
        username,
        f'submission_{submission_id}',
        'history',
        f'resubmission_{resubmission_count}',
        original_filename
    )

    return relative_path


def compare_metadata_with_uploaded_files(submission, metadata_df):
    """
    Compares resubmitted metadata with already uploaded files (FASTQ and antibiotics) for this submission.
    Returns: (has_mismatches: bool, mismatch_message: str)
    """
    metadata_df.columns = metadata_df.columns.str.lower().str.strip()
    mismatches = []

    # Build lookup for uploaded FASTQ files
    uploaded_fastqs = submission.files.filter(file_type="fastq")
    uploaded_by_sample = {}
    for f in uploaded_fastqs:
        sid = (f.sample_id or "").lower()
        uploaded_by_sample.setdefault(sid, set()).add(f.file.name.split("/")[-1])

    # Build lookup for uploaded antibiotics files → IMPORTANT: use "antibiotics_raw"
    uploaded_ab = {
        (f.sample_id or "").lower(): f.file.name.split("/")[-1]
        for f in submission.files.filter(file_type="antibiotics_raw")
    }

    for idx, row in metadata_df.iterrows():
        sample_id = str(row.get("sample identifier", "")).strip().lower()
        expected_fastq = [
            str(row[col]).strip()
            for col in ["illumina r1", "illumina r2", "nanopore", "pacbio"]
            if col in metadata_df.columns and pd.notna(row[col])
        ]

        expected_ab = (
            str(row["antibiotics file"]).strip()
            if "antibiotics file" in row and pd.notna(row["antibiotics file"])
            else None
        )

        antibiotics_info = (
            str(row["antibiotics info"]).strip()
            if "antibiotics info" in row and pd.notna(row["antibiotics info"])
            else None
        )

        uploaded_fastq_names = uploaded_by_sample.get(sample_id, set())
        ab_file_name = uploaded_ab.get(sample_id)

        # Compare FASTQ files
        extra = uploaded_fastq_names - set(expected_fastq)
        missing = set(expected_fastq) - uploaded_fastq_names

        # Compare antibiotics only if antibiotics file was used (not info)
        ab_mismatch = False
        if expected_ab and not antibiotics_info:
            ab_mismatch = expected_ab != ab_file_name

        # If antibiotics info was used → we do NOT expect a file
        if antibiotics_info and ab_file_name:
            ab_mismatch = True
            expected_ab = None  # we force expected_ab = None in this case to explain the mismatch clearly

        # Aggregate mismatches
        if missing or extra or ab_mismatch:
            msg = f"\nSample '{sample_id}':"
            if missing:
                msg += f"\n  Missing FASTQ files: {', '.join(missing)}"
            if extra:
                msg += f"\n  Extra FASTQ files: {', '.join(extra)}"
            if ab_mismatch:
                msg += f"\n  Antibiotics file mismatch: expected '{expected_ab}', found '{ab_file_name}'"
            mismatches.append(msg)

    if mismatches:
        return True, "\n".join(mismatches)
    return False, ""