from django.shortcuts import render, redirect, HttpResponse
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.http import Http404
from .models import TodoItem, Item
from .models import Submission,FileHistory
from .models import SampleFile, UploadedFile, AnalysisResult 
import re
from django.db.models import Q
from .forms import CreateNewList, FileUploadForm ,SearchForm
from .forms import UploadFileForm
from .forms import BulkUploadForm,SingleUploadForm
import os
import csv
import logging
from django.db import connection
import pandas as pd
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from pandas.errors import EmptyDataError
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required, user_passes_test
from storages.backends.sftpstorage import SFTPStorage
from django.core.paginator import Paginator
from django.utils.text import slugify
from .models import user_submission_path
import requests
from io import BytesIO
from django.contrib import messages
from django.core.files.base import ContentFile
import io
from io import TextIOWrapper,StringIO
import json
import time
from datetime import datetime
from collections import Counter
from django.shortcuts import get_object_or_404
from .models import BactopiaResult, PlasmidIdentResult
from django.http import JsonResponse
from pathlib import Path
from django.db.models import Count
from django.db.models import Prefetch
from functools import lru_cache
import shutil
from django.core.files.base import File
from django.core.files import File as DjangoFile
from django.core.mail import send_mail

# Configure logging to a file
logging.basicConfig(filename='bulk_upload.log', level=logging.DEBUG)

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'gensurvapp/home.html', {"TodoItems": TodoItem.objects.all()})
def research(request):
    return render(request, 'gensurvapp/research.html')

def about(request):
    return render(request, 'gensurvapp/about.html')

def impressum(request):
    return render(request, 'gensurvapp/impressum.html')
def datenschutz(request):
    return render(request, 'gensurvapp/datenschutz.html')
def contact(request):
    return render(request, 'gensurvapp/contact.html')
def accessibility(request):
    return render(request, 'gensurvapp/accessibility.html')

    
@login_required
def create(response):
    if response.method == "POST":
        form = CreateNewList(response.POST)
        if form.is_valid():
            n = form.cleaned_data["name"]
            t = TodoItem(name=n)
            t.save()
            response.user.todoitem.add(t)
            return HttpResponseRedirect(f"/{n}/")
    else:
        form = CreateNewList()
    return render(response, 'gensurvapp/create.html', {"form": form})

@login_required
def todos(request):
    items = TodoItem.objects.all()
    return render(request, 'gensurvapp/todos.html', {"todos": items})

@login_required
def index(request, name):
    try:
        ls = TodoItem.objects.get(name=name)
    except TodoItem.DoesNotExist:
        return HttpResponseNotFound("TodoItem with name '%s' does not exist." % name)

    if ls in request.user.todoitem.all():
        if request.method == "POST":
            print(request.POST)
            if request.POST.get("save"):
                for item in ls.item_set.all():
                    if request.POST.get("c" + str(item.id)) == "clicked":
                        item.complete = True
                    else:
                        item.complete = False
                    item.save()
            elif request.POST.get("newItem"):
                txt = request.POST.get("new")
                if len(txt) > 2:
                    ls.item_set.create(text=txt, complete=False)
                else:
                    print("invalid")

        try:
            item = ls.item_set.first()
        except Item.DoesNotExist:
            return HttpResponseNotFound("Item with id 8 does not exist for TodoItem with name '%s'." % name)

        return render(request, 'gensurvapp/list.html', {"ls": ls, "item": item, "TodoItems": TodoItem.objects.all()})
    return render(request, 'gensurvapp/todos.html', {})
@login_required
def instructions(request):
    return render(request, 'gensurvapp/instructions.html')


@login_required
def sample_csv(request):
    sample_data = {
        "Sample Identifier": ["ID1", "ID2"],
        "Isolate Species": ["9606", "9606"],  # NCBI Taxonomy ID
        "Subtype": ["Type1", "Type2"],
        "Collection Date": ["2023-01-01", "2023-01-02"],  # YYYY-MM-DD format
        "Sampling Strategy": ["Surveillance", "Suspected outbreak"],
        "Sample Source": ["Environment", "Human clinical (hospital)"],
        "Collection Method": ["Swab", "Blood culture"],
        "City": ["New York", "Los Angeles"],
        "Postal Code": [10001, 90001],
        "County": ["New York County", "Los Angeles County"],
        "State": ["New York", "California"],
        "Country": ["USA", "USA"],
        "Lab Identifier": ["Lab1", "Lab2"],
        "Sex": ["Male", "Female"],
        "Age Group": ["Adult", "Pediatric"],
        "Country of Putative Exposure": ["USA", "USA"],
        "Sequencing Platform": ["Illumina", "PacBio"],
        "Sequencing Type": ["Whole genome sequencing", "Amplicon sequencing"],
        "Library Preparation Kit": ["Kit1", "Kit2"],
        "Sequencing Chemistry": ["Chemistry1", "Chemistry2"],
    }
    sample_df = pd.DataFrame(sample_data)
    table_html = sample_df.to_html(index=False, classes='table table-striped')
    return render(request, 'gensurvapp/sample_csv.html', {'table_html': table_html})


@login_required
def download_sample_csv(request):
    # Path to the sample metadata CSV file
    csv_file_path = os.path.join(settings.BASE_DIR, 'gensurvapp', 'static', 'sample_metadata.csv')

    # Read the CSV file into a DataFrame
    try:
        sample_df = pd.read_csv(csv_file_path)
    except FileNotFoundError:
        return HttpResponse(f"Error: The file {csv_file_path} does not exist.", status=404)

    # Prepare the response to download the file
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_metadata.csv"'
    sample_df.to_csv(path_or_buf=response, index=False)

    return response

@login_required
def download_antibiotics_csv(request):
    # Path to the antibiotics testing CSV file
    csv_file_path = os.path.join(settings.BASE_DIR, 'gensurvapp', 'static', 'sample_antibiotics.csv')

    # Read the CSV file into a DataFrame
    try:
        antibiotics_df = pd.read_csv(csv_file_path)
    except FileNotFoundError:
        return HttpResponse(f"Error: The file {csv_file_path} does not exist.", status=404)

    # Prepare the response to download the file
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_antibiotics.csv"'
    antibiotics_df.to_csv(path_or_buf=response, index=False)

    return response

def get_max_submission_id():
    with connection.cursor() as cursor:
        cursor.execute("SELECT MAX(id) FROM gensurvapp_submission;")
        row = cursor.fetchone()
    return row[0] if row and row[0] is not None else 0


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


sftp_fs = SFTPStorage()

# MEDIA_ROOT and MEDIA_URL are defined in  settings

local_fs = FileSystemStorage()  # Make sure to save local files with local_fs


# Expected columns and data types for each file type
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


def fetch_taxonomy_name_old(taxonomy_id: str):
    """
    Fetch the Taxonomy Name for a given Taxonomy ID using E-Utilities.

    Parameters:
        taxonomy_id (str): A valid Taxonomy ID.

    Returns:
        tuple: (bool, str) where the boolean indicates success, and the string is the Name or error message.
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db": "taxonomy",
        "id": taxonomy_id,
        "retmode": "json"
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "result" in data and taxonomy_id in data["result"]:
                name = data["result"][taxonomy_id]["scientificname"]
                return True, name
            return False, f"Taxonomy ID {taxonomy_id} not found in NCBI E-Utilities database."
        else:
            return False, f"Unexpected response for Taxonomy ID {taxonomy_id}: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Error fetching Taxonomy Name for ID {taxonomy_id}: {e}"



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
                return True, data["result"][taxonomy_id]["scientificname"]

            return False, f"Taxonomy ID {taxonomy_id} not found in NCBI database."
        
        except requests.exceptions.Timeout:
            logger.warning(f"NCBI API timeout (attempt {attempt + 1}/{retries})")
            time.sleep(5)  # Wait before retrying
        
        except requests.exceptions.RequestException as e:
            logger.error(f"NCBI API error: {e}")
            break  # Stop retrying if it's a different error

    return False, f"NCBI API unreachable. Skipping taxonomy validation for {taxonomy_id}."


VALID_SEX_MAPPING = {
    "m": "male",
    "male": "male",
    "f": "female",
    "female": "female",
    "o": "other",
    "other": "other"
   }
#For the 'Sex' field, you can input any of the following:
#- 'M', 'F', 'male', 'female', or 'other' (case-insensitive).
#The system will standardize these to 'male', 'female', or 'other' automatically.


def validate_sex_field(value):
    """
    Validate and normalize the 'Sex' field.

    - Accepts case-insensitive inputs such as 'M', 'F', 'Male', 'Female', 'O', 'Other'.
    - Maps them to their normalized forms: 'male', 'female', 'other'.
    """
    if not isinstance(value, str):
        return False, "Invalid data type for 'Sex'. Expected a string."

    # Normalize the input by stripping whitespace and converting to lowercase
    normalized_value = value.strip().lower()

    # Check if the normalized value exists in the mapping
    if normalized_value in VALID_SEX_MAPPING:
        return True, VALID_SEX_MAPPING[normalized_value]  # Return normalized value if valid
    else:
        return False, f"Invalid value for 'Sex': {value}. Accepted values are: {', '.join(VALID_SEX_MAPPING.keys())}."


VALID_AGE_GROUPS = {"neonate", "pediatric", "adult", "pensioner","geriatric","elderly"}
#geriatric

def validate_age_group_field(value):
    """
    Validate the 'Age Group' field.

    - Accepts case-insensitive inputs for: 'neonate', 'pediatric', 'adult', 'pensioner'.
    - Does not accept abbreviations like 'N', 'P', etc.
    """
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



VALID_PLATFORMS = {"illumina", "ont", "nanopore", "oxford nanopore","pacbio"}

def validate_sequencing_platform_field(value):
    """
    Validate the 'Sequencing Platform' field.

    - Accepts: Illumina, ONT, Nanopore, PacBio, Other: <Text> (case-insensitive).
    - Rejects unrecognized or incomplete 'Other' values.
    """
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


#improve messages here. want to tell user the addecate format is day month year
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
            #"%m/%d/%Y",#"%m-%d-%Y",
            #"%m.%d.%Y", #"%m/%d/%y",
            #"%m-%d-%y",#"%m.%d.%y"
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
        #"%m/%d/%Y": "mm/dd/YYYY",  # Add American-style formats
        #"%m-%d-%Y": "mm-dd-YYYY",  # Add American-style formats
        #"%m.%d.%Y": "mm.dd.YYYY",  # Add American-style formats
        #"%m/%d/%y": "mm/dd/YY",
        #"%m-%d-%y": "mm-dd-YY",
        #"%m.%d.%y": "mm.dd.YY",
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



# Define validation patterns for "other"
VALID_SAMPLING_STRATEGIES = ["surveillance", "screening","suspected outbreak", "other", "diagnostics"]
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
    content = file.read().decode("utf-8")
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


def fix_trailing_empty_columns_new(file, detected_delimiter):
    """
    Fixes issues with CSV/TSV files exported from Excel or manually edited:
    - Preserves quoted fields that contain commas
    - Removes trailing empty columns
    - Strips surrounding quotes from full fields only
    - Returns cleaned content as a StringIO object
    """
    file.seek(0)
    #content = file.read().decode("utf-8")#this was previous code, check if the new code below works
    content = file.read()

    if isinstance(content, bytes):
        content = content.decode("utf-8")


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

def detect_delimiter(file):
    """
    Detect the delimiter from a set of known delimiters [',', ';', '\t'] by analyzing the entire file.
    """
    try:
        file.seek(0)  # Ensure the file pointer is at the start
        sample = file.read()        
        
        # Decode if the content is binary
        if isinstance(sample, bytes):
            sample = sample.decode('utf-8')
            
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
              -  TODO:`renamed_columns`: (dict) Original and renamed column headers for mismatched columns.
    """
    validation_results = {
        "is_valid": True,
        "missing_columns": [],
        "extra_columns": [],
        "type_mismatches": [],
        "invalid_values": []  # ✅ add this

       # "renamed_columns": {}
    }

    # Normalize column names for case-insensitive comparison
    df.columns = df.columns.str.lower().str.strip()
    normalized_expected_columns = {key.lower().strip(): value for key, value in expected_columns.items()}
    valid_extensions = (".fastq", ".fq", ".bam", ".fastq.gz", ".fq.gz", ".bam.gz", ".bz2", ".xz", ".zip")
    #optionally also log individual types
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
    # --- Global, column-wide transformations/validation ---
    if "collection date" in df.columns:
        logger.debug("📅 Pre-validating 'collection date' column globally")
        
        if pd.api.types.is_datetime64_any_dtype(df["collection date"]):
            logger.debug("→ Column is datetime64; formatting as DD-MM-YYYY")
            df["collection date"] = df["collection date"].dt.strftime("%d-%m-%Y")
        else:
            logger.debug("Column 'Collection Date' is not a datetime object; assuming string format.")
        logger.debug("→ Final collection date values:\n" + df["collection date"].to_string(index=False))


    # Attempt to rename mismatched columns (fuzzy matching)
    #for col in df.columns:
    #    if col not in normalized_expected_columns:
    #        # Try finding a close match
    #        closest_match = next((key for key in normalized_expected_columns if col in key or key in col), None)
    #        if closest_match:
    #            validation_results["renamed_columns"][col] = closest_match
    #            df.rename(columns={col: closest_match}, inplace=True)
    
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
            #non_empty_values = df[column].replace("", pd.NA).dropna()
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
                #df[column] = df[column].astype(str)

                #invalid_mic_values = non_empty_values[
                #    ~non_empty_values.map(lambda x: validate_mic_value(x))
                #]
                #in case emoty vlues reise erorr:
                invalid_mic_values = non_empty_values[
                    ~non_empty_values.map(lambda x: validate_mic_value(str(x)))
                ]

                if not invalid_mic_values.empty:
                    validation_results["is_valid"] = False
                    validation_results["type_mismatches"].append(
                        f"{column}: Invalid MIC values in row(s): {', '.join(map(str, invalid_mic_values.index + 1))}"
                    )

            # Special case for Isolate Species validation
#            if column == "isolate species":
#                logger.debug(f"Isolate Species validation")
#                invalid_ncbi_entries = []
#                for index, value in non_empty_values.items():
#                    is_valid, result = is_valid_ncbi_tax_id_or_name(str(value))
#                    if not is_valid:
#                        invalid_ncbi_entries.append(f"row {index + 1}: {result}")
#                    else:
#                        # Replace Names with corresponding Taxonomy IDs for consistency
#                        df.at[index, column] = result if value != result else value
#
            #    if invalid_ncbi_entries:
            #        validation_results["is_valid"] = False
            #        validation_results["type_mismatches"].append(
            #            f"{column}: Invalid NCBI entries: {'; '.join(invalid_ncbi_entries)}"
            #        )
            #    continue

            # Special case for Sex validation
            if column == "sex":
                invalid_sex_values = []
                for index, value in df[column].dropna().items():
                    is_valid, normalized_or_error = validate_sex_field(value)
                    if not is_valid:
                        invalid_sex_values.append(f"row {index + 1}: {normalized_or_error}")
                if invalid_sex_values:
                    validation_results["is_valid"] = False
                    validation_results["type_mismatches"].append(
                        f"{column}: Invalid values in row(s): {', '.join(map(str, invalid_sex_values))}"
                    )
                continue

            # Special case for Age Group validation
            if column == "age group":
                logger.debug(f"Age Group validation")
                invalid_age_group_values = []
                for index, value in df[column].dropna().items():
                    is_valid, normalized_or_error = validate_age_group_field(value)
                    if not is_valid:
                        invalid_age_group_values.append(f"row {index + 1}: {normalized_or_error}")
                    else:
                        # Normalize valid values
                        df.at[index, column] = normalized_or_error

                if invalid_age_group_values:
                    validation_results["is_valid"] = False
                    validation_results["type_mismatches"].append(
                        f"{column}: Invalid values in row(s): {'; '.join(invalid_age_group_values)}"
                    )
                continue

            # Special case for Sequencing Platform validation
            #if column == "sequencing platform":
            #    logger.debug(f"Starting Sequencing Platform validation")
            #    invalid_platform_values = []
            #    for index, value in df[column].dropna().items():
            #        logger.debug(f"→ Row {index + 1}: Raw value = '{value}'")

            #        is_valid, normalized_or_error = validate_sequencing_platform_field(value)
            #        if not is_valid:
            #            logger.warning(f"✗ Invalid platform at row {index + 1}: Reason = '{normalized_or_error}'")
            #            invalid_platform_values.append(f"row {index + 1}: {normalized_or_error}")
            #        else:
                        # Normalize valid values
            #            logger.debug(f"✓ Valid platform at row {index + 1}: Normalized = '{normalized_or_error}'")
            #            df.at[index, column] = normalized_or_error

            #    logger.debug(f"Ending for loop Sequencing Platform validation")

            #    if invalid_platform_values:
            #        logger.debug(f"invalid_platform_values")

            #        validation_results["is_valid"] = False
            #        validation_results["type_mismatches"].append(
            #            f"{column}: Invalid values in rows: {'; '.join(invalid_platform_values)}"
            #        )
            #    logger.debug(f"Ending Sequencing Platform validation")
            #    continue

            # Special case for Sampling Strategy validation
            if column == "sampling strategy":
                logger.debug(f"Sampling Strategy validation")
                invalid_sampling = non_empty_values[
                    ~non_empty_values.str.lower().isin([v.lower() for v in VALID_SAMPLING_STRATEGIES]) &
                    ~non_empty_values.str.lower().str.match(OTHER_PATTERN)
                ]
                if not invalid_sampling.empty:
                    validation_results["is_valid"] = False
                    validation_results["type_mismatches"].append(
                        f"{column}: Invalid Sampling Strategy in row(s): {', '.join(map(str, invalid_sampling.index + 1))}"
                    )
                continue

            # Special case for Sample Source validation
            if column == "sample source":
                logger.debug(f"Sample Source validation")
                invalid_sources = non_empty_values[
                    ~non_empty_values.str.lower().isin([v.lower() for v in VALID_SAMPLE_SOURCES]) &
                    ~non_empty_values.str.lower().str.match(OTHER_PATTERN)
                ]
                if not invalid_sources.empty:
                    validation_results["is_valid"] = False
                    validation_results["type_mismatches"].append(
                        f"{column}: Invalid Sample Source in rows: {', '.join(map(str, invalid_sources.index + 1))}"
                    )
                continue

            # Special case for Collection Date validation
            if column == "collection date":
                logger.debug(f"Collection Date validation")
                # At this point, all values should be strings
                #detected_format, mismatched_rows = detect_common_date_format(df, column)

                #if detected_format:
                    # If there are mismatched rows, log errors
                #    if mismatched_rows:
                #        logger.debug(f"log1: {column}: Invalid date format in rows: {', '.join(map(str, mismatched_rows))}")
               #         validation_results["is_valid"] = False
               #         validation_results["type_mismatches"].append(
               #             f"{column}: Invalid date format in rows: {', '.join(map(str, mismatched_rows))}"
               #         )
                    
                    # Validate and normalize remaining rows
                for index, value in df[column].items():
                    #is_valid, error_or_normalized_date = validate_and_normalize_date(value, [detected_format])
                    is_valid, error_or_normalized_date = validate_and_normalize_date(str(value).strip())

                    if not is_valid:
                        validation_results["is_valid"] = False
                        validation_results["type_mismatches"].append(
                            f"{column}: row {index + 1}: {error_or_normalized_date}"
                        )
                        logger.debug(f"log: {column}: row {index + 1}: {error_or_normalized_date}")
                    else:
                        # Normalize the valid date to a standard format
                        df.at[index, column] = error_or_normalized_date
                #else:
                    # No common format detected
                #    validation_results["is_valid"] = False
                #    validation_results["type_mismatches"].append(
                #        f"{column}: Could not detect a common date format."
                #    )
                #    logger.debug(f"log3:{column}: Could not detect a common date format.")
                #continue

            # Postal Code validation
            if column == "postal code":
                logger.debug(f"Postal Code Column Before Validation: {df[column].tolist()}")
                invalid_postal_codes = non_empty_values[
                    ~non_empty_values.map(lambda x: str(x).isdigit())  # Check if all values are numeric
                ]
                if not invalid_postal_codes.empty:
                    validation_results["is_valid"] = False
                    validation_results["type_mismatches"].append(
                        f"{column}: Expected numeric values, but found invalid types in rows: "
                        f"{', '.join(map(str, invalid_postal_codes.index + 1))}"
                    )
                continue
            # Special case for NGS validation
            # --- Illumina R1 ---
            if column == "illumina r1":
                logger.debug("Validating Illumina R1 filenames")
                invalid_ext_rows = df[column].dropna().apply(str).apply(
                    lambda x: not any(x.lower().endswith(ext) for ext in valid_extensions)
                )
                if invalid_ext_rows.any():
                    row_nums = (invalid_ext_rows[invalid_ext_rows].index + 1).tolist()
                    validation_results["is_valid"] = False
                    validation_results["type_mismatches"].append(
                        f"{column}: Invalid file extension in rows: {', '.join(map(str, row_nums))}. "
                        f"Expected extensions: {', '.join(valid_extensions)}"
                    )
                continue

            # --- Illumina R2 ---
            if column == "illumina r2":
                logger.debug("Validating Illumina R2 filenames")
                invalid_ext_rows = df[column].dropna().apply(str).apply(
                    lambda x: not any(x.lower().endswith(ext) for ext in valid_extensions)
                )
                if invalid_ext_rows.any():
                    row_nums = (invalid_ext_rows[invalid_ext_rows].index + 1).tolist()
                    validation_results["is_valid"] = False
                    validation_results["type_mismatches"].append(
                        f"{column}: Invalid file extension in rows: {', '.join(map(str, row_nums))}. "
                        f"Expected extensions: {', '.join(valid_extensions)}"
                    )
                continue

            # --- Nanopore ---
            if column == "nanopore":
                logger.debug("Validating Nanopore filenames")
                invalid_ext_rows = df[column].dropna().apply(str).apply(
                    lambda x: not any(x.lower().endswith(ext) for ext in valid_extensions)
                )
                if invalid_ext_rows.any():
                    row_nums = (invalid_ext_rows[invalid_ext_rows].index + 1).tolist()
                    validation_results["is_valid"] = False
                    validation_results["type_mismatches"].append(
                        f"{column}: Invalid file extension in rows: {', '.join(map(str, row_nums))}. "
                        f"Expected extensions: {', '.join(valid_extensions)}"
                    )
                continue

            # --- PacBio ---
            if column == "pacbio":
                logger.debug("Validating PacBio filenames")
                invalid_ext_rows = df[column].dropna().apply(str).apply(
                    lambda x: not any(x.lower().endswith(ext) for ext in valid_extensions)
                )
                if invalid_ext_rows.any():
                    row_nums = (invalid_ext_rows[invalid_ext_rows].index + 1).tolist()
                    validation_results["is_valid"] = False
                    validation_results["type_mismatches"].append(
                        f"{column}: Invalid file extension in rows: {', '.join(map(str, row_nums))}. "
                        f"Expected extensions: {', '.join(valid_extensions)}"
                    )
                continue

    #after loop
    #validate ngs 
    # ✅ Custom validation: Ensure at least one NGS platform field is filled
    all_ngs_fields = ["illumina r1", "illumina r2","nanopore", "pacbio"]
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
            rows_missing = has_ngs_data[~has_ngs_data].index + 1
            validation_results["is_valid"] = False
            validation_results["type_mismatches"].append(
            f"NGS Platform Fields: At least one of 'Illumina R1', 'Nanopore', or 'PacBio' must be filled per row. Missing in rows: {', '.join(map(str, rows_missing))}"
            )

        # ✅ Illumina R2 cannot be filled unless R1 is also filled
        if "illumina r2" in df.columns:
        #    invalid_r2_rows = df[
        #        (df["illumina r2"].notna() & (df["illumina r2"].str.strip() != "")) &
        #        (~df.get("illumina r1", "").notna() | (df["illumina r1"].str.strip() == ""))
        #        ].index + 1
#
        #    if len(invalid_r2_rows) > 0:
 #               validation_results["is_valid"] = False
   #             validation_results["type_mismatches"].append(
    #            f"'Illumina R2' cannot be provided without 'Illumina R1'. Affected rows: {', '.join(map(str, invalid_r2_rows))}"
     #           )
    # 1. make safe, comparable string Series for both columns
            r2 = df["illumina r2"].fillna("").astype(str).str.strip()
            if "illumina r1" in df.columns:
                r1 = df["illumina r1"].fillna("").astype(str).str.strip()
            else:                                      # column truly absent
                r1 = pd.Series([""] * len(df), index=df.index)

            # 2. rows where R2 is present but R1 is empty
            invalid_r2_rows = df[(r2 != "") & (r1 == "")].index + 1

            if len(invalid_r2_rows) > 0:
                validation_results["is_valid"] = False
                validation_results["type_mismatches"].append(
                    "'Illumina R2' cannot be provided without 'Illumina R1'. "
                    f"Affected rows: {', '.join(map(str, invalid_r2_rows))}"
                )


        # ✅ Optional: Only allow one filename per platform field (no semicolons or commas)
            for field in all_ngs_fields:
                if field in df.columns:
                    multiple_file_rows = df[df[field].astype(str).str.contains(r"[,;]", na=False)].index + 1
                    if len(multiple_file_rows) > 0:
                        validation_results["is_valid"] = False
                        validation_results["type_mismatches"].append(
                            f"{field.title()}: Only one filename is allowed per field. Invalid rows: {', '.join(map(str, multiple_file_rows))}"
                        )
                
    logger.debug("Validation Results:\n" + json.dumps(validation_results, indent=4))
    return validation_results


def validate_and_save_csv(file, expected_columns,essential_columns=None):
    """
    Validates and saves a CSV or Excel (.xlsx) file by:
    - Detecting delimiters (For CSV files)
    - Fixing trailing/empty columns and inconsistent quoting (For CSV files)
    - Reading the file into a DataFrame
    - Performing schema and logic validation
    
    Returns:
        tuple: (is_valid: bool, message: str, delimiter: str, dataframe: pd.DataFrame or None)
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
            logger.debug("Detected Excel file. Attempting to read with pandas.")
            df = pd.read_excel(file)
            delimiter = ","  # Placeholder to match return type
            # ✅ Log column data types
            logger.debug("📊 Column data types:\n" + df.dtypes.to_string())
        else:
            # Detect the delimiter
            delimiter = detect_delimiter(file)
            cleaned_file = fix_trailing_empty_columns_new(file, delimiter)
            #logger.debug("Drop unnamed extra columns")
            df = pd.read_csv(cleaned_file, sep=delimiter)

        df.columns = df.columns.str.lower().str.strip()
        logger.debug(f"DataFrame shape after trimming: {df.shape}")
        logger.debug(f"File read into DataFrame successfully:\n{df.head()}")

        #optionally also log individual types
        for col in df.columns:
            logger.debug(f"→ Column '{col}' type: {df[col].dtype}")
        # Row-wise logging for debugging
        for idx, row in df.iterrows():
            logger.debug(f"\n🧾 Row {idx + 1}:")
            for col in df.columns:
                logger.debug(f"• {col.strip()}: {row[col]}")

    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return False, f"Error reading file: {e}", delimiter, None

    # Log all detected column names
    logger.debug(f"Columns detected: {list(df.columns)}")

    # **Print the entire DataFrame to verify parsing**
    logger.debug("\nFull DataFrame content:\n" + df.to_string())

    #  **Log each column separately for better debugging**
    for column in df.columns:
        logger.debug(f"\nColumn: {column}\n{df[column].to_string(index=False)}")

    # Debug: Log values of sequencing file fields if present (case-insensitive)
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in ["illumina r1", "illumina r2", "nanopore", "pacbio"]:
            logger.debug(f"Raw '{col}' column values:\n{df[col].to_string(index=False)}")

    # Debug: Antibiotics Info column if present (case-insensitive)
    for col in df.columns:
        if col.lower().strip() == "antibiotics info":
            logger.debug(f"Raw '{col}' column values:\n{df[col].to_string(index=False)}")

    # Validate the DataFrame using `validate_csv_columns`
    logger.debug("Entering def validate_csv_columns")

    validation_results = validate_csv_columns(df, expected_columns)

    # Separate essential from non-essential issues
    # Check essential columns if provided
    if essential_columns:
        essential_missing = [col for col in validation_results["missing_columns"] if col in [c.lower() for c in essential_columns.keys()]]
        if essential_missing:
            error_messages.append("ERROR: Missing essential mandatory columns:")
            has_errors = True
            for column in essential_missing:
                error_messages.append(f"- {column}")

    # Now handle warnings instead of failing
    # If validation_results still has any issues, return as a warning (not failure and compile messages
    if not validation_results["is_valid"]:
        # Missing mandatory columns
        if validation_results["missing_columns"]:
            warning_messages.append("\nWARNING: Missing mandatory columns for downstream analysis:")
            has_warnings = True
            for column in validation_results["missing_columns"]:
                warning_messages.append(f"- {column}")

        # Extra columns
        if validation_results["extra_columns"]:
            warning_messages.append("\nWARNING: Unexpected extra columns:")
            has_warnings = True
            for column in validation_results["extra_columns"]:
                warning_messages.append(f"- {column}")

        # Type mismatches or other validation issues
        if validation_results["type_mismatches"]:
            warning_messages.append("\nWARNING: Type mismatches or other validation errors:")
            has_warnings = True
            for issue in validation_results["type_mismatches"]:
                warning_messages.append(f"- {issue}")
                
        # Invalid (empty) values in mandatory fields
        if validation_results.get("invalid_values"):
            warning_messages.append("\nWARNING: Empty values in required fields:")
            has_warnings = True
            for issue in validation_results["invalid_values"]:
                warning_messages.append(f"- {issue}")

        # Renamed columns (optional logging, if needed)
        #if validation_results["renamed_columns"]:
        #    renamed_columns = validation_results["renamed_columns"]
        #    logger.info(f"Columns renamed for validation: {renamed_columns}")

        # Combine all messages into a single string with line breaks
    if has_warnings:
        return True, True, "\n".join(warning_messages), delimiter, df
    if has_errors:
        return False, True, "\n".join(error_messages + warning_messages), delimiter, None


    # If validation is successful
    logger.info("Validation successful.")
    #return is_valid: bool, warning: bool, message: str, delimiter: str, dataframe: Optional[pd.DataFrame]
    return True, False, "Validation successful.", delimiter, df


def handle_single_upload(form, user):
    """Process single upload."""
    metadata_file = form.cleaned_data['metadata_file']
    antibiotics_file = form.cleaned_data['antibiotics_file']
    fastq_files = form.cleaned_data['fastq_files']

    # Create submission instance
    submission = Submission.objects.create(user=user, metadata_file=metadata_file, is_bulk_upload=False)

    # Save related files
    SampleFile.objects.create(submission=submission, sample_id="SingleSample", file_type='metadata', file=metadata_file)
    SampleFile.objects.create(submission=submission, sample_id="SingleSample", file_type='antibiotics', file=antibiotics_file)

    for fastq_file in fastq_files:
        SampleFile.objects.create(submission=submission, sample_id="SingleSample", file_type='fastq', file=fastq_file)

    return submission

def handle_bulk_upload(form, user):
    """Process bulk upload."""
    metadata_file = form.cleaned_data['metadata_file']
    antibiotics_files = form.cleaned_data['antibiotics_files']
    fastq_files = form.cleaned_data['fastq_files']

    # Create submission instance
    submission = Submission.objects.create(user=user, metadata_file=metadata_file, is_bulk_upload=True)

    # Parse sample IDs from metadata file
    sample_ids = extract_sample_ids_from_metadata(metadata_file)

    # Match files to sample IDs
    for sample_id in sample_ids:
        matched_antibiotics = [f for f in antibiotics_files if sample_id in f.name]
        matched_fastqs = [f for f in fastq_files if sample_id in f.name]

        if not matched_antibiotics:
            raise ValueError(f"Missing antibiotics file for sample ID: {sample_id}")
        if not matched_fastqs:
            raise ValueError(f"Missing FASTQ files for sample ID: {sample_id}")

        # Save files for each sample ID
        SampleFile.objects.create(
            submission=submission, sample_id=sample_id, file_type='metadata', file=metadata_file
        )
        for antib_file in matched_antibiotics:
            SampleFile.objects.create(
                submission=submission, sample_id=sample_id, file_type='antibiotics', file=antib_file
            )
        for fastq_file in matched_fastqs:
            SampleFile.objects.create(
                submission=submission, sample_id=sample_id, file_type='fastq', file=fastq_file
            )

    return submission

def extract_sample_ids(file):
    """
    Extract sample IDs from the uploaded CSV file.
    """
    try:
        logger.debug(f"Validating file: {getattr(file, 'name', 'Unknown')} (type: {type(file)})")
        file.seek(0)
        # Detect the delimiter
        delimiter = detect_delimiter(file)

        # Read the file into a DataFrame
        df = pd.read_csv(file, sep=delimiter)
        #df = pd.read_csv(file)
        logger.debug(f"File read into DataFrame successfully:\n{df.head()}")

        # Check if the DataFrame is empty
        if df.empty:
            raise ValueError("The uploaded file is empty.")

        # Check if the required column exists
        if 'Sample Identifier' not in df.columns:
            raise ValueError("The file is missing the required 'Sample Identifier' column.")

        # Extract sample IDs, stripping whitespace
        sample_ids = df['Sample Identifier'].dropna().str.strip().tolist()

        # Ensure there are sample IDs
        if not sample_ids:
            raise ValueError("No valid sample IDs found in the 'Sample Identifier' column.")

        logger.debug(f"Extracted Sample IDs: {sample_ids}")
        return sample_ids

    except pd.errors.EmptyDataError:
        error_message = "The file appears to be empty or improperly formatted."
        logger.error(error_message)
        raise ValueError(error_message)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error while extracting sample IDs: {e}")
        raise

def extract_sample_ids_from_metadata(metadata_file):
    """
    Extract sample IDs from the metadata file without prematurely closing it.
    """
    try:
        logger.debug(f"Starting extraction for file: {metadata_file.name} (type: {type(metadata_file)})")

        # Ensure the file pointer is at the start
        metadata_file.seek(0)
        logger.debug("File pointer reset to start.")

        # Read file content safely
        decoded_file = TextIOWrapper(metadata_file, encoding='utf-8').read()
        logger.debug("File read successfully.")

        # Use StringIO to avoid closing the file prematurely
        reader = csv.DictReader(StringIO(decoded_file))
        logger.debug("File after redaer")

        headers = reader.fieldnames
        logger.debug("File after header")

        if not headers:
            raise ValueError("Metadata file has no headers.")

        if 'Sample Identifier' not in headers:
            raise ValueError("Metadata file is missing the required 'Sample Identifier' column.")

        sample_ids = []
        for row in reader:
            sample_id = row.get('Sample Identifier')
            if not sample_id:
                raise ValueError(f"Row missing 'Sample Identifier': {row}")
            sample_ids.append(sample_id.strip())

        logger.debug(f"Extracted Sample IDs: {sample_ids}")

        # Reset pointer if file needs further processing elsewhere
        #metadata_file.seek(0)
        logger.debug(f"after Sample IDs: {sample_ids} before return")

        return sample_ids

    except UnicodeDecodeError as e:
        logger.error(f"File encoding issue: {e}")
        raise ValueError(f"File encoding issue: {str(e)}")

    except csv.Error as e:
        logger.error(f"CSV parsing error: {e}")
        raise ValueError(f"CSV parsing error: {str(e)}")

    except Exception as e:
        logger.error(f"Error in extracting sample IDs: {e}")
        raise ValueError(f"Error in extracting sample IDs: {str(e)}")

# Custom decorator to allow uploads for admins
def admin_only_upload_test(user):
    return user.is_superuser or user.is_staff  # Adjust as needed for specific permissions

def generate_cleaned_file(original_filename, df):
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


@login_required
#@user_passes_test(admin_only_upload_test, login_url='/')  # Redirect non-admin users #comment out if not testing.
def upload_files(request):
    maintenance_message = None
    #maintenance_message = "Upload functionality is temporarily disabled due to maintenance. Please do not upload data until this message is removed."

    # Allow only admins to bypass maintenance mode
    # Block non-admin users if maintenance mode is active
    if not request.user.is_superuser and maintenance_message and request.method == "POST":
        messages.error(request, "Uploads are currently disabled due to maintenance.")
        return redirect('upload_files')
    
    """Handle single and bulk file uploads with validation."""
    single_error_message = None
    single_success_message = None
    bulk_error_message = None
    bulk_success_message = None
    single_form = FileUploadForm()
    bulk_form = BulkUploadForm()
    submission = None
    warning_message = None
    start_time = time.time()
    if request.method == "POST":
        if "single_upload" in request.POST:
            single_form = FileUploadForm(request.POST, request.FILES)
            if single_form.is_valid():
                try:
                    # Extract files from the form
                    metadata_file = single_form.cleaned_data.get('metadata_file')
                    # Logging with safety check
                    if metadata_file:
                        logger.debug(f"Processing uploaded metadata file: {metadata_file.name} (type: {type(metadata_file)})")
                    else:
                        raise ValueError("Metadata file is required but not provided.")  # Explicitly handle missing metadata
                    uploaded_antibiotics_file = single_form.cleaned_data.get('antibiotics_file')
                    if uploaded_antibiotics_file:
                        logger.debug(f"Processing uploaded antibiotics file: {uploaded_antibiotics_file.name} (type: {type(uploaded_antibiotics_file)})")
                    else:
                        logger.debug("No antibiotics file uploaded.")  # Safe to proceed without raising an error
                    fastq_files = request.FILES.getlist('fastq_files')
                    if not fastq_files:
                        raise ValueError(f"At least one sequencing file must be provided.")
                    else:
                        logger.debug(f"Processing {len(fastq_files)} uploaded FASTQ files.")
                        for i, fastq_file in enumerate(fastq_files):
                            logger.debug(f"Processing #${i+1} uploaded FASTQ file: {fastq_file.name} (type: {type(fastq_file)})")
                    # ✅ Validate metadata file . this calls function to fix trail inside
                    #warning: update for "quarentine" or reupload metadata if warnings are found.
                    valid_metadata, metadata_warning, metadata_message, detected_delimiter_meta, metadata_df = validate_and_save_csv(metadata_file, METADATA_COLUMNS,ESSENTIAL_METADATA_COLUMNS)
                    logger.debug(f"Detected delimiter: {detected_delimiter_meta}")

                    if not valid_metadata:
                        # Raise a single exception containing both error and warning messages
                        raise ValueError(f"FATAL:\n{metadata_message}")
                    elif metadata_warning:
                        # No errors, just warnings — show to user but don't stop the process
                        warning_message = f"Warnings in metadata file:\n{metadata_message}"
                        logger.debug(f"Metadata file validated with warnings: {warning_message}")
                    else:
                        # No errors or warnings — proceed with the upload
                        #single_success_message = "Metadata file validated successfully."
                        logger.debug(f"Metadata file validated successfully: {metadata_file.name}")
                
                    # Loaded metadata into a DataFrame for validation
                    logger.debug(f"Loaded metadata file into df: {metadata_file.name} (type: {type(metadata_file)})")
                    if metadata_df.empty:
                        single_error_message = "Metadata file is empty or incorrectly formatted."
                        raise ValueError(single_error_message)
                    # ✅ Normalize column names (fixes unexpected whitespace or case issues)
                    metadata_df.columns = metadata_df.columns.str.lower().str.strip()
                    logger.debug("Normalize column names (fixes unexpected whitespace or case issues")

                    # Extract sample identifier from metadata
                    sample_id = metadata_df.loc[0, "sample identifier"].strip()
                    logger.debug("Extract sample identifier from metadata")

                    ####################################
                    # ✅ Valid file extensions
                    valid_extensions = (".fastq", ".fq", ".bam", ".fastq.gz", ".fq.gz", ".bam.gz", ".bz2", ".xz", ".zip")
                    # ✅ Extract uploaded FASTQ file names
                    uploaded_fastq_files_names = {f.name.strip() for f in fastq_files}
                    logger.debug(f"📁 Uploaded FASTQ filenames: {uploaded_fastq_files_names}")

                    # ✅ Extract sequencing filenames from metadata
                    illumina_r1 = metadata_df.loc[0, "illumina r1"].strip() if "illumina r1" in metadata_df.columns and pd.notna(metadata_df.loc[0, "illumina r1"]) else None
                    illumina_r2 = metadata_df.loc[0, "illumina r2"].strip() if "illumina r2" in metadata_df.columns and pd.notna(metadata_df.loc[0, "illumina r2"]) else None
                    nanopore    = metadata_df.loc[0, "nanopore"].strip()     if "nanopore"    in metadata_df.columns and pd.notna(metadata_df.loc[0, "nanopore"]) else None
                    pacbio      = metadata_df.loc[0, "pacbio"].strip()       if "pacbio"      in metadata_df.columns and pd.notna(metadata_df.loc[0, "pacbio"]) else None

                    # ✅ Build expected FASTQ file list
                    expected_fastq_files = [f for f in [illumina_r1, illumina_r2, nanopore, pacbio] if f]

                    # ✅ Log the metadata parsing results
                    logger.debug("🔍 Checking sequencing files listed in metadata:")
                    logger.debug(f"• Illumina R1: {illumina_r1 or 'None'}")
                    logger.debug(f"• Illumina R2: {illumina_r2 or 'None'}")
                    logger.debug(f"• Nanopore: {nanopore or 'None'}")
                    logger.debug(f"• PacBio: {pacbio or 'None'}")
                    logger.debug(f"📋 Final list of expected FASTQ files: {expected_fastq_files}")

                    # ✅ At least one platform file must be present (excluding Illumina R2 alone)
                    if not any([illumina_r1, nanopore, pacbio]):
                        raise ValueError(f"Sample '{sample_id}': At least one sequencing platform file must be provided (Illumina R1, Nanopore, or PacBio).")

                    # ✅ Illumina R2 is only valid if R1 is present
                    if illumina_r2 and not illumina_r1:
                        raise ValueError(f"Sample '{sample_id}': Illumina R2 file provided without Illumina R1.")

                    # ✅ Validate extensions of expected files
                    for file in expected_fastq_files:
                        if not any(file.lower().endswith(valid_ext) for valid_ext in valid_extensions):
                            raise ValueError(
                                f"Sample '{sample_id}': File '{file}' has an invalid extension.\n"
                                f"Allowed extensions: {', '.join(valid_extensions)}"
                            )
                        logger.debug(f"✅ File '{file}' passed extension check.")
 
                    # ✅ Detect missing files
                    missing_fastq_files = set(expected_fastq_files) - uploaded_fastq_files_names
                    if missing_fastq_files:
                        logger.error(f"❌ Missing FASTQ files: {missing_fastq_files}")
                        raise ValueError(
                            f"Sample '{sample_id}': Some FASTQ files listed in metadata are missing from the upload.\n"
                            f"Missing files: {', '.join(sorted(missing_fastq_files))}\n"
                            f"Expected: {', '.join(expected_fastq_files)}\n"
                            f"Uploaded: {', '.join(uploaded_fastq_files_names)}"
                        )
                    
                    # ✅ Warn about extra files
                    extra_fastq_files = uploaded_fastq_files_names - set(expected_fastq_files)
                    extra_fastq_warning = ""
                    if extra_fastq_files:
                        logger.warning(f"⚠️ Extra FASTQ files detected (ignored): {extra_fastq_files}")
                        extra_fastq_warning = f"⚠️ Warning: Extra FASTQ file(s) were uploaded but ignored: {', '.join(extra_fastq_files)}."

                    # ✅ Confirm presence of each expected file
                    for expected_file in expected_fastq_files:
                        if expected_file not in uploaded_fastq_files_names:
                            raise ValueError(f"Sample '{sample_id}': Expected file '{expected_file}' is not found in uploaded files.")
                        #matched_file = next((f for f in uploaded_fastq_files_names if f.strip() == expected_file), None)
                        #if not matched_file:
                        #    raise ValueError(f"Sample '{sample_id}': Expected sequencing file '{expected_file}' is missing from the uploaded files.")
                        logger.debug(f"🧬 Matched expected file: {expected_file}")

                    # ✅ Log success
                    logger.info(f"✅ Sample '{sample_id}': All expected FASTQ files validated successfully.")
                    ####################################ANTIBIOTICS

                    # Extract antibiotics file name from metadata (if available)
                    antibiotics_file_name = (
                        metadata_df.loc[0, "antibiotics file"].strip()
                        if "antibiotics file" in metadata_df.columns and not metadata_df["antibiotics file"].isna().iloc[0]
                        else None
                    )

                    # Extract antibiotics info from metadata (if available)
                    antibiotics_info = (
                        metadata_df.loc[0, "antibiotics info"].strip()
                        if "antibiotics info" in metadata_df.columns and not metadata_df["antibiotics info"].isna().iloc[0]
                        else None
                    )
                    # ✅ Ensure either 'Antibiotics File' OR 'Antibiotics Info' is provided, but NOT both
                    if antibiotics_file_name and antibiotics_info:
                        logger.error(f"Sample '{sample_id}': Both 'Antibiotics File' and 'Antibiotics Info' are provided, which is not allowed.")
                        raise ValueError(f"Sample '{sample_id}': Both 'Antibiotics File' (metadata) and 'Antibiotics Info' (metadata) cannot be provided simultaneously.")

                    # ✅ Extract expected antibiotics file name from metadata
                    expected_antibiotics_file = (
                        metadata_df.loc[0, "antibiotics file"].strip()
                        if "antibiotics file" in metadata_df.columns and not metadata_df["antibiotics file"].isna().iloc[0]
                        else None
                    )

                    # ✅ Debug logs
                    logger.debug(f"Expected Antibiotics File: {expected_antibiotics_file}")
                    logger.debug(f"Uploaded Antibiotics File: {uploaded_antibiotics_file.name if uploaded_antibiotics_file else 'None'}")

                    # ✅ Handle **missing** antibiotics file
                    if expected_antibiotics_file and not uploaded_antibiotics_file:
                        logger.error(f"Missing expected antibiotics file: {expected_antibiotics_file}")
                        raise ValueError(f"Sample '{sample_id}': Expected antibiotics file '{expected_antibiotics_file}' is missing.")

                    # ✅ Ensure antibiotics file name matches (if applicable)
                    if expected_antibiotics_file and uploaded_antibiotics_file:
                        if uploaded_antibiotics_file.name.strip() != expected_antibiotics_file.strip():
                            logger.error(
                                f"Sample '{sample_id}': Uploaded antibiotics file '{uploaded_antibiotics_file.name}' "
                                f"does not match expected file '{expected_antibiotics_file}' in metadata."
                            )
                            raise ValueError(
                                f"Sample '{sample_id}': Uploaded antibiotics file '{uploaded_antibiotics_file.name}' "
                                f"does not match expected file '{expected_antibiotics_file}' in metadata."
                            )


                    # ✅ Validate the antibiotics file (if provided). This calls function to fix trail delimiters
                    antibiotics_df= pd.DataFrame()
                    ab_warning=None
                    if uploaded_antibiotics_file:
                        valid_antibiotics, ab_warning, antibiotics_message, detected_delimiter_anti, antibiotics_df = validate_and_save_csv(uploaded_antibiotics_file, ANTIBIOTICS_COLUMNS)
                        logger.debug(f"Detected delimiter: {detected_delimiter_anti}")

                        if not valid_antibiotics:
                            logger.error(f"FATAL: Sample '{sample_id}': Antibiotics file validation failed: {antibiotics_message}")
                            raise ValueError(f"FATAL: Sample '{sample_id}': Antibiotics file error: {antibiotics_message}")
                        # ✅ Log successful validation
                        elif ab_warning:
                        # No errors, just warnings — show to user but don't stop the process
                            logger.debug(f"Warnings in antibiotics file:\n{antibiotics_message}")
                        else:
                            logger.info(f"Sample '{sample_id}': Uploaded antibiotics file successfully validated: {uploaded_antibiotics_file.name}")


                    # ✅ Logging for clarity
                    if expected_antibiotics_file:
                        logger.info(f"Sample '{sample_id}': Expected antibiotics file '{expected_antibiotics_file}' listed in metadata but not uploaded.")
                    elif antibiotics_info:
                        logger.info(f"Sample '{sample_id}': Using antibiotics info from metadata: {antibiotics_info}")
                    else:
                        logger.info(f"Sample '{sample_id}': No antibiotics file or info provided.")

#########################
                    # Loaded antibiotics into a DataFrame for validation
                    if antibiotics_df.empty and uploaded_antibiotics_file:
                        raise ValueError("Antibiotics file is empty or incorrectly formatted.")

                    elif not antibiotics_df.empty and uploaded_antibiotics_file:
                        # ✅ Normalize column names (fixes unexpected whitespace or case issues)
                        antibiotics_df.columns = antibiotics_df.columns.str.lower().str.strip()
                        logger.debug("Normalized antibiotics file column names (whitespace and case issues fixed)")
#########################SUBMISION OF FILES
                    
                    # Save the submission and associated files
                    submission = Submission(user=request.user)
                    #if warning_message:
                    if metadata_warning:
                        submission.resubmission_allowed = True
                        submission.metadata_warnings = metadata_message  # or warning_message if you want formatted output
                        #submission.save()#not save twice
                    else:
                        submission.resubmission_allowed = False
                    if ab_warning:
                        submission.antibiotics_warnings = antibiotics_message
                        #logger.debug(f"Warnings in antibiotics file:\n{antibiotics_message}")
                    #if metadata_warning or ab_warning:
                    #    submission.resubmission_allowed = True
                    if extra_fastq_files:
                        submission.extra_fastq_warning = extra_fastq_warning

                    submission.save()

                    # Save metadata file
                    # Generate cleaned file from DataFrame
                    cleaned_file = generate_cleaned_file(metadata_file.name, metadata_df)

                    # Save raw + cleaned metadata file in single UploadedFile row:
                    UploadedFile.objects.create(
                        submission=submission,
                        file=metadata_file,
                        cleaned_file=cleaned_file,
                        file_type="metadata_raw",
                        sample_id=sample_id
                    )


                    # ✅ Save sequencing files based on expected_fastq_files list
                    for expected_file in expected_fastq_files:
                        matched_file = next(
                            (f for f in fastq_files if f.name == expected_file or f.name.startswith(expected_file)),
                            None
                        )

                        if matched_file:
                            UploadedFile.objects.create(
                                submission=submission,
                                file=matched_file,
                                file_type="fastq",
                                sample_id=sample_id
                            )
                            logger.debug(f"📥 Saved FASTQ file: {matched_file.name}")
                        else:
                            logger.warning(f"⚠️ Skipping missing sequencing file: {expected_file} for sample '{sample_id}'")


                    # ✅ Save antibiotics file if present
                    if uploaded_antibiotics_file:
                        # Generate cleaned file from DataFrame
                        #cleaned_antibiotics_csv = antibiotics_df.to_csv(index=False)
                        #cleaned_file = ContentFile(cleaned_antibiotics_csv)
                        #cleaned_file.name = f"cleaned_{uploaded_antibiotics_file.name}"  # optional, for clarity
                        cleaned_file = generate_cleaned_file(uploaded_antibiotics_file.name, antibiotics_df)

                        UploadedFile.objects.create(
                            submission=submission,
                            file=uploaded_antibiotics_file,
                            cleaned_file=cleaned_file,
                            file_type="antibiotics_raw",
                            sample_id=sample_id
                        )

                    else:
                        logger.info(f"Sample '{sample_id}': No antibiotics file provided for submission upload.")

                    #single_success_message = f"Single sample upload successful. {extra_fastq_warning}"
                    single_success_message = f"Single sample upload successful."

                    if warning_message:
                        single_success_message = f"{single_success_message}\n{warning_message}"
                    if extra_fastq_warning:
                        single_success_message = f"{single_success_message}\n{extra_fastq_warning}"

                    
                    logger.info("Single sample upload completed successfully.")

                except ValueError as ve:
                    single_error_message = str(ve)  # Specific validation error message
                    logger.warning(f"Validation error: {single_error_message}")
                except Exception as e:
                    single_error_message = f"An unexpected error occurred: {str(e)}"
                    logger.error(f"Single upload error: {e}", exc_info=True)
            else:
                # Log form errors and notify the user
                single_error_message = "Single upload form is invalid. Please correct the errors below."
                logger.error(f"Form errors: {single_form.errors}")

        elif "bulk_upload" in request.POST:
            bulk_form = BulkUploadForm(request.POST, request.FILES)
            bulk_error_message = None
            metadata_warning_message = ""
            antibiotics_warning_message = ""
            extra_fastq_warning_message = ""

            if bulk_form.is_valid():
                try:
                   # Extract files from the form
                    metadata_file = bulk_form.cleaned_data.get('metadata_file')
                    # Logging with safety check
                    if metadata_file:
                        logger.debug(f"Processing uploaded bulk metadata file: {metadata_file.name} (type: {type(metadata_file)})")
                    else:
                        raise ValueError("Metadata file is required but not provided.")  # Explicitly handle missing metadata
                    uploaded_antibiotics_files = request.FILES.getlist('antibiotics_files')
                    if uploaded_antibiotics_files:
                        logger.debug(f"Processing {len(uploaded_antibiotics_files)} uploaded antibiotics file(s) .")
                        for i, ab_file in enumerate(uploaded_antibiotics_files):
                            logger.debug(f"• Antibiotics file #{i+1}: {ab_file.name} (type: {type(ab_file)})")
                    else:
                        logger.debug("No antibiotics files uploaded.")  # Safe to proceed without raising an error
                    fastq_files = request.FILES.getlist('fastq_files')
                    if not fastq_files:
                        raise ValueError(f"At least one sequencing file must be provided.")
                    else:
                        logger.debug(f"Processing {len(fastq_files)} uploaded FASTQ file(s).")
                        for i, fastq_file in enumerate(fastq_files):
                            logger.debug(f"Processing #${i+1} uploaded FASTQ file: {fastq_file.name} (type: {type(fastq_file)})")
                    
                    # ✅ Validate metadata file . this calls function to fix trail inside
                    valid_metadata, metadata_warning, metadata_message, detected_delimiter_meta, metadata_df = validate_and_save_csv(
                    metadata_file, METADATA_COLUMNS, ESSENTIAL_METADATA_COLUMNS)
                    logger.debug(f"Detected delimiter: {detected_delimiter_meta}")

                    if not valid_metadata:
                        raise ValueError(f"Metadata file error: {metadata_message}")
                    elif metadata_warning:
                        # No errors, just warnings — show to user but don't stop the process
                        #metadata_warning_message += f"{metadata_message}\n" # do i need the + if its one metadata file per bulk submission?
                        metadata_warning_message += f"{metadata_message}\n" 
                        logger.debug(f"Metadata file validated with warnings: {metadata_message}")
                    else:
                        # No errors or warnings — proceed with the upload
                        logger.debug(f"Metadata file validated successfully: {metadata_file.name}")
                    
                    # Loaded metadata into a DataFrame for validation
                    logger.debug(f"Loaded metadata file into df: {metadata_file.name} (type: {type(metadata_file)})")
                    if metadata_df.empty:
                        bulk_error_message = "Metadata file is empty or incorrectly formatted."
                        raise ValueError(bulk_error_message)
                    # ✅ Normalize column names (fixes unexpected whitespace or case issues)
                    metadata_df.columns = metadata_df.columns.str.lower().str.strip()
                    logger.debug("Normalize column names (fixes unexpected whitespace or case issues")

                    ####################################

                    # ✅ Valid file extensions
                    valid_extensions = (".fastq", ".fq", ".bam", ".fastq.gz", ".fq.gz", ".bam.gz", ".bz2", ".xz", ".zip")
                    # ✅ Extract uploaded FASTQ file names
                    uploaded_fastq_files_names = {f.name.strip() for f in fastq_files}
                    extra_fastq_warning = ""

                    logger.debug(f"📁 Uploaded FASTQ filenames: {uploaded_fastq_files_names}")

                    #all_expected_fastq_files = set()
                    matched_fastq_files = set()  # Track which FASTQ files were actually used

                    for idx, row in metadata_df.iterrows():
                        # Extract sample identifier from metadata
                        raw_value = row.get("sample identifier", f"row {idx + 1}")
                        sample_id = str(raw_value).strip()

                        if not sample_id or sample_id.lower() == 'nan':
                            logger.debug(f"Row {idx + 1}: Missing or invalid sample identifier.")
                            raise ValueError(f"Row {idx + 1}: Missing or invalid sample identifier.")

                        logger.debug(f"Extract sample identifier {sample_id} from metadata")

                        # Extract filenames
                        illumina_r1 = row["illumina r1"].strip() if pd.notna(row.get("illumina r1")) else None
                        illumina_r2 = row["illumina r2"].strip() if pd.notna(row.get("illumina r2")) else None
                        nanopore    = row["nanopore"].strip()    if pd.notna(row.get("nanopore")) else None
                        pacbio      = row["pacbio"].strip()      if pd.notna(row.get("pacbio")) else None

                        expected_fastq_files = [f for f in [illumina_r1, illumina_r2, nanopore, pacbio] if f]
                        logger.debug(f"🔬 Sample '{sample_id}' expects FASTQ files: {expected_fastq_files}")

                        logger.debug("🔍 Checking sequencing files listed in metadata:")
                        logger.debug(f"\n🔬 Sample '{sample_id}' expects FASTQ files:")
                        logger.debug(f"• Illumina R1: {illumina_r1 or 'None'}")
                        logger.debug(f"• Illumina R2: {illumina_r2 or 'None'}")
                        logger.debug(f"• Nanopore: {nanopore or 'None'}")
                        logger.debug(f"• PacBio: {pacbio or 'None'}")
                        logger.debug(f"📋 Final list of expected FASTQ files: {expected_fastq_files}")

                        # ✅ At least one platform file must be present (excluding Illumina R2 alone)
                        if not any([illumina_r1, nanopore, pacbio]):
                            raise ValueError(f"Sample '{sample_id}': Must include at least one platform file (Illumina R1, Nanopore, or PacBio).")

                        # Validation: Illumina R2 requires R1
                        if illumina_r2 and not illumina_r1:
                            raise ValueError(f"Sample '{sample_id}': Illumina R2 file provided without Illumina R1.")

                        # Extension check of expected files
                        for file in expected_fastq_files:
                            if not any(file.lower().endswith(valid_ext) for valid_ext in valid_extensions):
                                raise ValueError(
                                    f"Sample '{sample_id}': File '{file}' has an invalid extension.\n"
                                    f"Allowed extensions: {', '.join(valid_extensions)}"
                                )
                            matched_fastq_files.add(file)
                            logger.debug(f"✅ File '{file}' passed extension check.")


                        # ✅ Check for missing files for this sample
                        missing_fastq_files = [f for f in expected_fastq_files if f not in uploaded_fastq_files_names]
                        if missing_fastq_files:
                            logger.error(f"❌ Missing FASTQ files: {missing_fastq_files}")
                            raise ValueError(
                                f"Sample '{sample_id}': Some FASTQ files listed in metadata are missing from the upload.\n"
                                #f"Sample '{sample_id}': Missing FASTQ file(s): {', '.join(missing_fastq_files)}"
                                f"Missing: {', '.join(sorted(missing_fastq_files))}\n"
                                f"Expected: {', '.join(expected_fastq_files)}\n"
                                #f"Uploaded: {', '.join(sorted(uploaded_fastq_files_names
                            )

                        # Log success
                        logger.info(f"✅ Sample '{sample_id}': All expected FASTQ files validated successfully.")


                    # ✅ Warn about extra files. Optional: log and ignore extras
                    extra_fastq_files = uploaded_fastq_files_names - matched_fastq_files
                    extra_fastq_warning = ""

                    if extra_fastq_files:
                        #extra_fastq_warning = f"⚠️ Warning: Extra FASTQ file(s) were uploaded but ignored: {', '.join(sorted(extra_fastq_files))}."
                        extra_fastq_warning_message += f"Extra FASTQ file(s) ignored: {', '.join(sorted(extra_fastq_files))}\n"
                        logger.warning(extra_fastq_warning_message)

                    ###################ANTIBIOTICS FILE VALIDATION 
                            
                    # Extract antibiotics file name from metadata (if available)
                    uploaded_antibiotics_filenames = {f.name.strip(): f for f in uploaded_antibiotics_files}
                    logger.debug(f"📁 Uploaded antibiotics file names: {list(uploaded_antibiotics_filenames.keys())}")

                    # ✅ Iterate over each sample in the metadata
                    for idx, row in metadata_df.iterrows():
                        ab_warning=None
                        # Extract sample identifier from metadata
                        raw_value = row.get("sample identifier", f"row {idx + 1}")
                        sample_id = str(raw_value).strip()

                        if not sample_id or sample_id.lower() == 'nan':
                            logger.debug(f"Row {idx + 1}: Missing or invalid sample identifier.")
                            raise ValueError(f"Row {idx + 1}: Missing or invalid sample identifier.")

                        logger.debug(f"Extract sample identifier {sample_id} from metadata")
                        # ✅ Extract expected antibiotics file name
                        expected_ab_file = row.get("antibiotics file", "")
                        expected_ab_file = expected_ab_file.strip() if pd.notna(expected_ab_file) else None

                        # ✅ Extract antibiotics info string
                        antibiotics_info = row.get("antibiotics info", "")
                        antibiotics_info = antibiotics_info.strip() if pd.notna(antibiotics_info) else None

                        # ✅ Ensure either 'Antibiotics File' OR 'Antibiotics Info' is provided, but NOT both
                        if expected_ab_file and antibiotics_info:
                            logger.error(f"Sample '{sample_id}': Both 'Antibiotics File' (metadata) and 'Antibiotics Info' (metadata) cannot be provided simultaneously.")
                            raise ValueError(f"Sample '{sample_id}': Both 'Antibiotics File' (metadata) and 'Antibiotics Info' (metadata) cannot be provided simultaneously.")
                        # ✅ Debug logs
                        logger.debug(f"\n🧪 Sample '{sample_id}' → Expected antibiotics file: {expected_ab_file or 'None'}")
                        logger.debug(f"  → Metadata antibiotics info: {antibiotics_info or 'None'}")

                        antibiotics_df = pd.DataFrame()

                        if expected_ab_file:
                            uploaded_file = uploaded_antibiotics_filenames.get(expected_ab_file)

                            if not uploaded_file:
                                logger.error(f"❌ Sample '{sample_id}': Expected antibiotics file '{expected_ab_file}' not uploaded.")
                                raise ValueError(f"Sample '{sample_id}': Missing expected antibiotics file '{expected_ab_file}'.")

                            # ✅ Validate the antibiotics file
                            valid, ab_warning, message, delimiter, antibiotics_df = validate_and_save_csv(uploaded_file, ANTIBIOTICS_COLUMNS)
                            logger.debug(f"Detected delimiter: {delimiter}")

                            if not valid:
                                logger.error(f"❌ Sample '{sample_id}': Antibiotics file validation failed: {message}")
                                raise ValueError(f"Sample '{sample_id}': Antibiotics file error: {message}")
                            elif ab_warning:
                                # No errors, just warnings — show to user but don't stop the process
                                ab_message = f"Warnings in antibiotics file:\n{message}"
                                logger.debug(f"Continue with warnings: {ab_message}")
                            else:
                                # ✅ Log success
                                logger.info(f"✅ Sample '{sample_id}': Antibiotics file '{uploaded_file.name}' validated successfully.")

                            # ✅ Normalize headers
                            if not antibiotics_df.empty:
                                antibiotics_df.columns = antibiotics_df.columns.str.lower().str.strip()
                                logger.debug(f"Normalized antibiotics file headers for sample '{sample_id}'.")

                        elif antibiotics_info:
                            logger.info(f"ℹ️ Sample '{sample_id}': Using antibiotics info from metadata.")
                        else:
                            logger.info(f"ℹ️ Sample '{sample_id}': No antibiotics file or info provided.")
#######################################
# If there are errors, skip saving
                    if bulk_error_message:
                        logger.warning(f"Validation errors during bulk upload:\n{bulk_error_message}")
                        raise ValueError(bulk_error_message)

                    # If no errors, proceed with saving
                    # Create a new Submission object
#########################SUBMISION OF FILES

                    # Save the submission and associated files
                    submission = Submission(user=request.user,is_bulk_upload = True)
                    #if warning_message:
                    if metadata_warning_message:
                        submission.resubmission_allowed = True
                        submission.metadata_warnings = metadata_warning_message  # or warning_message if you want formatted output
                        submission.save()
                    else:
                        submission.save()
                        #submission.metadata_warnings = None# do i need to put none or can just remove this line?
                    #    submission.resubmission_allowed = False
                    #if antibiotics_warning_message:
                    #    submission.antibiotics_warnings = antibiotics_warning_message
                        #logger.debug(f"Warnings in antibiotics file:\n{antibiotics_message}")
                    #if extra_fastq_warning_message:
                    #    submission.extra_fastq_warning = extra_fastq_warning_message
                    #submission.save()
                    logger.debug(f"After setting is_bulk_upload: {submission.is_bulk_upload}")

                    # Save the cleaned metadata to Submission.metadata_file
                    #cleaned_metadata_csv = metadata_df.to_csv(index=False)
                    #cleaned_file = ContentFile(cleaned_metadata_csv)
                    #cleaned_file.name = f"cleaned_{metadata_file.name}"  # Optional: clarify it's the cleaned version
                    cleaned_file = generate_cleaned_file(metadata_file.name, metadata_df)

                    #submission.metadata_file.save(cleaned_file.name, cleaned_file, save=True)
                    # Save the metadata file to the submission using FileField
                    #submission.metadata_file.save(metadata_file.name, metadata_file, save=True)

                    # Save raw + cleaned metadata file in single UploadedFile row:
                    UploadedFile.objects.create(
                        submission=submission,
                        file=metadata_file,
                        cleaned_file=cleaned_file,
                        file_type="metadata_raw",
                        sample_id=sample_id
                    )

                    # ✅ Save sequencing files based on expected_fastq_files list
                    for idx, row in metadata_df.iterrows():
                        # Extract sample identifier from metadata
                        raw_value = row.get("sample identifier", f"row {idx + 1}")
                        sample_id = str(raw_value).strip()

                        if not sample_id or sample_id.lower() == 'nan':
                            logger.debug(f"Row {idx + 1}: Missing or invalid sample identifier.")
                            raise ValueError(f"Row {idx + 1}: Missing or invalid sample identifier.")

                        logger.debug(f"Extract sample identifier {sample_id} from metadata")

                        # Extract filenames
                        illumina_r1 = row["illumina r1"].strip() if pd.notna(row.get("illumina r1")) else None
                        illumina_r2 = row["illumina r2"].strip() if pd.notna(row.get("illumina r2")) else None
                        nanopore    = row["nanopore"].strip()    if pd.notna(row.get("nanopore")) else None
                        pacbio      = row["pacbio"].strip()      if pd.notna(row.get("pacbio")) else None

                        expected_fastq_files = [f for f in [illumina_r1, illumina_r2, nanopore, pacbio] if f]

                        logger.debug(f"\n🔬 Sample '{sample_id}' expects FASTQ files:")
                        logger.debug(f"• Illumina R1: {illumina_r1 or 'None'}")
                        logger.debug(f"• Illumina R2: {illumina_r2 or 'None'}")
                        logger.debug(f"• Nanopore: {nanopore or 'None'}")
                        logger.debug(f"• PacBio: {pacbio or 'None'}")
                        logger.debug(f"📋 Final list of expected FASTQ files: {expected_fastq_files}")


                        # Save sequencing files per sample
                        for seq_filename in expected_fastq_files:
                            matched_seq_file = next(
                                (f for f in fastq_files if f.name.strip() == seq_filename.strip()),
                                None
                            )
                            if matched_seq_file:
                                UploadedFile.objects.create(
                                    submission=submission, 
                                    file=matched_seq_file,
                                    file_type="fastq",
                                    sample_id=sample_id
                                )
                                logger.debug(f"Saved sequencing file '{matched_seq_file.name}' for sample '{sample_id}'")
                            else:
                                logger.warning(f"Skipping missing sequencing file: {seq_filename} for sample {sample_id}")

                        # ✅ Extract expected antibiotics file name
                        expected_ab_file = row.get("antibiotics file", "")
                        expected_ab_file = expected_ab_file.strip() if pd.notna(expected_ab_file) else None

                        # ✅ Extract antibiotics info string
                        antibiotics_info = row.get("antibiotics info", "")
                        antibiotics_info = antibiotics_info.strip() if pd.notna(antibiotics_info) else None

                        # ✅ Ensure either 'Antibiotics File' OR 'Antibiotics Info' is provided, but NOT both
                        if expected_ab_file and antibiotics_info:
                            logger.error(f"Sample '{sample_id}': Both 'Antibiotics File' (metadata) and 'Antibiotics Info' (metadata) cannot be provided simultaneously.")
                            raise ValueError(f"Sample '{sample_id}': Both 'Antibiotics File' (metadata) and 'Antibiotics Info' (metadata) cannot be provided simultaneously.")
                        # ✅ Debug logs
                        logger.debug(f"\n🧪 Sample '{sample_id}' → Expected antibiotics file: {expected_ab_file or 'None'}")
                        logger.debug(f"           → Metadata antibiotics info: {antibiotics_info or 'None'}")

                        antibiotics_df = pd.DataFrame()
                        
                        # Save antibiotics file per sample (if available)
                        if expected_ab_file:
                            uploaded_file = uploaded_antibiotics_filenames.get(expected_ab_file)

                            if not uploaded_file:
                                logger.error(f"❌ Sample '{sample_id}': Expected antibiotics file '{expected_ab_file}' not uploaded.")
                                raise ValueError(f"Sample '{sample_id}': Missing expected antibiotics file '{expected_ab_file}'.")

                            # ✅ Validate the antibiotics file
                            valid, ab_warning, message, delimiter, antibiotics_df = validate_and_save_csv(uploaded_file, ANTIBIOTICS_COLUMNS)
                            logger.debug(f"Detected delimiter: {delimiter}")

                            if not valid:
                                logger.error(f"❌ Sample '{sample_id}': Antibiotics file validation failed: {message}")
                                raise ValueError(f"Sample '{sample_id}': Antibiotics file error: {message}")
                            elif ab_warning:
                                antibiotics_warning_message += f"Sample '{sample_id}': {message}\n"

                            # ✅ Log success
                            logger.info(f"✅ Sample '{sample_id}': Antibiotics file '{uploaded_file.name}' validated successfully.")

                            # ✅ Normalize headers
                            if not antibiotics_df.empty:
                                antibiotics_df.columns = antibiotics_df.columns.str.lower().str.strip()
                                logger.debug(f"Normalized antibiotics file headers for sample '{sample_id}'.")
                                logger.debug(f"BULK ANTIBIOTICS FILe: expected={expected_ab_file},  uploaded_file name={uploaded_file.name},for sample {sample_id}")
                                cleaned_file = generate_cleaned_file(uploaded_file.name, antibiotics_df)
                                #cleaned_file = generate_cleaned_file(uploaded_antibiotics_file.name, antibiotics_df) 

                                # Rewind the uploaded_file first (safety!)
                                uploaded_file.seek(0)

                                UploadedFile.objects.create(
                                    submission=submission,
                                    file=uploaded_file,            # Raw uploaded file
                                    cleaned_file=cleaned_file,     # Cleaned CSV
                                    file_type="antibiotics_raw",
                                    sample_id=sample_id
                                )

                                logger.debug(f"✅ Saved antibiotics file anliverd cleaned version for sample '{sample_id}'")
                            else:
                                logger.warning(f"⚠️ Skipping missing antibiotics file: {expected_ab_file} for sample '{sample_id}'")

                        elif antibiotics_info:
                            logger.info(f"ℹ️ Sample '{sample_id}': Using antibiotics info from metadata.")
                        else:
                            logger.info(f"ℹ️ Sample '{sample_id}': No antibiotics file or info provided.")

                    #bulk_success_message = "Bulk upload completed successfully."

                    #if warning_message:
                    if antibiotics_warning_message:
                        submission.antibiotics_warnings = antibiotics_warning_message
                    
                    if extra_fastq_warning_message:
                        submission.extra_fastq_warning = extra_fastq_warning_message
                    submission.save()


                    # Show summarized message to user
                    success_messages = ["Bulk upload completed successfully."]
                    if metadata_warning_message:
                        success_messages.append("⚠️ Metadata file accepted with warnings.")
                    if antibiotics_warning_message:
                        success_messages.append("⚠️ Some antibiotics files accepted with warnings.")
                    if extra_fastq_warning_message:
                        success_messages.append("⚠️ Extra FASTQ files were ignored.")
                    bulk_success_message = "\n".join(success_messages)
                    messages.success(request, bulk_success_message, extra_tags='dashboard') #not sure where will be this used
                    logger.info(f"{bulk_success_message}")
                    #if warning_message:
                    #if metadata_warning:
                    #    bulk_success_message = f"{bulk_success_message}\n{warning_message}"
                    #    logger.info(f"ℹ️ bulk success message warning message: {bulk_success_message}")
                    #if extra_fastq_warning:
                    #    bulk_success_message = f"{bulk_success_message}\n{extra_fastq_warning}"
                    #    logger.info(f"ℹ️ bulk success message extra fastq: {bulk_success_message}")
                    logger.info("Bulk upload completed successfully.")

                except ValueError as ve:
                    bulk_error_message = str(ve)
                    logger.warning(f"Validation error during bulk upload: {bulk_error_message}")
                except Exception as e:
                    bulk_error_message = f"An unexpected error occurred during bulk upload: {str(e)}"
                    logger.error(f"Bulk upload error: {bulk_error_message}", exc_info=True)
                
            else:
                bulk_error_message = f"Bulk upload form is invalid. Please correct the errors below.\n{bulk_form.errors}"
                logger.error(f"Bulk form errors: {bulk_form.errors}")
            
    #finally:
    total_time = time.time() - start_time
    request.session['upload_duration'] = f"{total_time:.2f} seconds"
    logger.info(f"⏱️ Server processing time: {total_time:.2f} seconds")

    
    client_total_upload_time = request.POST.get("client_total_upload_time")
    client_network_delay = request.POST.get("client_network_delay")

    if client_total_upload_time and client_network_delay:
        try:
            client_total = float(client_total_upload_time)
            network_delay = float(client_network_delay)
            

            logger.info(f"✅ Total upload time (client-side): {client_total:.2f}s")
            logger.info(f"📡 Upload + network delay (client-side): {network_delay:.2f}s")
            
            request.session['network_delay'] = f"{network_delay:.2f} seconds"
            request.session['client_total_upload_time'] = f"{client_total:.2f} seconds"

        except Exception as e:
            logger.warning(f"⚠️ Failed to parse client timing info: {e}")

                
    # Render the page with the appropriate messages and forms
    return render(request, 'gensurvapp/upload.html', {
        'single_form': single_form,
        'bulk_form': bulk_form,
        'single_error_message': single_error_message,
        'single_success_message': single_success_message,
        'bulk_error_message': bulk_error_message,
        'bulk_success_message': bulk_success_message,
        'maintenance_message': maintenance_message,  # Pass the message
        "resubmission_allowed": submission.resubmission_allowed if submission else False,
        'submission_id': submission.id if submission else None,
    })


def compare_metadata_with_uploaded_files_single(submission, metadata_df):
    """
    Compares resubmitted metadata with already uploaded files (FASTQ and antibiotics) for this submission.
    Returns: (has_mismatches: bool, mismatch_message: str)
    """
    sample_id = metadata_df.loc[0, "sample identifier"].strip().lower()
    metadata_df.columns = metadata_df.columns.str.lower().str.strip()

    # ✅ Expected files from metadata
    expected_fastq = [
        metadata_df.loc[0, col].strip()
        for col in ["illumina r1", "illumina r2", "nanopore", "pacbio"]
        if col in metadata_df.columns and pd.notna(metadata_df.loc[0, col])
    ]
    expected_ab = (
        metadata_df.loc[0, "antibiotics file"].strip()
        if "antibiotics file" in metadata_df.columns and pd.notna(metadata_df.loc[0, "antibiotics file"])
        else None
    )

    # ✅ Get existing uploaded files
    existing_fastq = submission.uploadedfile_set.filter(file_type="fastq", sample_id=sample_id)
    uploaded_fastq_names = {f.file.name.split("/")[-1] for f in existing_fastq}

    ab_file_obj = submission.uploadedfile_set.filter(file_type="antibiotics", sample_id=sample_id).first()
    ab_file_name = ab_file_obj.file.name.split("/")[-1] if ab_file_obj else None

    # ✅ Compare
    extra = uploaded_fastq_names - set(expected_fastq)
    missing = set(expected_fastq) - uploaded_fastq_names
    ab_mismatch = expected_ab and expected_ab != ab_file_name

    msg = ""
    if missing:
        msg += f"Missing FASTQ files: {', '.join(missing)}\n"
    if extra:
        msg += f"Extra FASTQ files: {', '.join(extra)}\n"
    if ab_mismatch:
        msg += f"Antibiotics file mismatch: expected '{ab_file_name}', found '{expected_ab}.'\n"

    return bool(missing or extra or ab_mismatch), msg


def compare_metadata_with_uploaded_files(submission, metadata_df):
    """
    Compares resubmitted metadata with already uploaded files (FASTQ and antibiotics) for this submission.
    Returns: (has_mismatches: bool, mismatch_message: str)
    """
    metadata_df.columns = metadata_df.columns.str.lower().str.strip()
    mismatches = []

    # Build lookup for uploaded FASTQ files
    uploaded_fastqs = submission.uploadedfile_set.filter(file_type="fastq")
    uploaded_by_sample = {}
    for f in uploaded_fastqs:
        sid = (f.sample_id or "").lower()
        uploaded_by_sample.setdefault(sid, set()).add(f.file.name.split("/")[-1])

    # Build lookup for uploaded antibiotics files → IMPORTANT: use "antibiotics_raw"
    uploaded_ab = {
        (f.sample_id or "").lower(): f.file.name.split("/")[-1]
        for f in submission.uploadedfile_set.filter(file_type="antibiotics_raw")
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

def compare_metadata_with_uploaded_files2(submission, metadata_df):
    """
    Compares resubmitted metadata with already uploaded files (FASTQ and antibiotics) for this submission.
    Returns: (has_mismatches: bool, mismatch_message: str)
    """
    metadata_df.columns = metadata_df.columns.str.lower().str.strip()
    mismatches = []

    # Build lookup for uploaded files: sample_id -> files
    uploaded_fastqs = submission.uploadedfile_set.filter(file_type="fastq")
    uploaded_by_sample = {}
    for f in uploaded_fastqs:
        sid = (f.sample_id or "").lower()
        uploaded_by_sample.setdefault(sid, set()).add(f.file.name.split("/")[-1])

    uploaded_ab = {
        (f.sample_id or "").lower(): f.file.name.split("/")[-1]
        for f in submission.uploadedfile_set.filter(file_type="antibiotics_raw")
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

        uploaded_fastq_names = uploaded_by_sample.get(sample_id, set())
        ab_file_name = uploaded_ab.get(sample_id)

        extra = uploaded_fastq_names - set(expected_fastq)
        missing = set(expected_fastq) - uploaded_fastq_names
        ab_mismatch = expected_ab and expected_ab != ab_file_name

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



def archive_file_to_submission_history1(submission, old_file_field, original_filename, file_type):
    """
    Move a file to: media/submissions/<username>/submission_<id>/history/resubmission_<n>/filename
    """
    username = submission.user.username
    submission_id = submission.pk
    src_path = old_file_field.path

    # Count existing resubmissions for this file_type → gives resubmission number
   #resubmission_count = FileHistory.objects.filter(submission=submission, file_type=f"{file_type}_raw").count() + 1
    resubmission_count = FileHistory.objects.filter(submission=submission, file_type=file_type).count() + 1

    # Build target path
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

    # Return relative path for FileHistory (what goes into the FileField)
    relative_path = os.path.join(
        'submissions',
        username,
        f'submission_{submission_id}',
        'history',
        f'resubmission_{resubmission_count}',
        original_filename
    )

    return relative_path


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


def resubmit_file_view(request, submission_id, file_type):
     # Clear leftover messages (like from dashboard)
    storage = messages.get_messages(request)
    list(storage) # This will consume and clear any old messages

    submission = get_object_or_404(Submission, id=submission_id, user=request.user)
    logger.info(f"file_type1: {file_type}")

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            new_file = form.cleaned_data["file"]
            old = submission.uploadedfile_set.filter(file_type=f"{file_type}_raw").first()
            logger.info(f"file_type2: {file_type}_raw")

            if old:
                # === 1️⃣ Compute resubmission count ONCE ===
                current_resubmission_count = FileHistory.objects.filter(
                    submission=submission,
                    file_type__endswith='_raw'
                ).count() + 1

                # === 2️⃣ Archive raw file ===
                old_file_history_path = archive_file_to_submission_history(
                    submission,
                    old.file,
                    os.path.basename(old.file.name),
                    f"{file_type}_raw",
                    current_resubmission_count
                )

                # === 3️⃣ Archive cleaned file if exists ===
                if old.cleaned_file and old.cleaned_file.name:
                    logger.info(f"OLD CLEANED FILE: {old.cleaned_file.name}")

                    cleaned_file_history_path = archive_file_to_submission_history(
                        submission,
                        old.cleaned_file,
                        os.path.basename(old.cleaned_file.name),
                        f"{file_type}_cleaned",
                        current_resubmission_count
                    )

                    # Remove cleaned_file reference so we can assign new cleaned safely
                    old.cleaned_file.delete(save=False)
                    old.cleaned_file = None
                else:
                    cleaned_file_history_path = None

                # === 4️⃣ Save FileHistory entry ===
                FileHistory.objects.create(
                    submission=submission,
                    file_type=f"{file_type}_raw",
                    old_file=old_file_history_path,
                    cleaned_file=cleaned_file_history_path,
                )

                # === 5️⃣ Update UploadedFile with new raw + new cleaned ===
                old.file = new_file

                # Guard sample_id if corrupted
                if old.sample_id and len(old.sample_id) > 100:
                    logger.warning(f"sample_id too long → trimming: {old.sample_id}")
                    old.sample_id = old.sample_id[:100]

                # === 6️⃣ Validate and generate cleaned file ===
                if file_type == "metadata":
                    valid, warnings, message, delimiter, df = validate_and_save_csv(
                        new_file, METADATA_COLUMNS, ESSENTIAL_METADATA_COLUMNS
                    )
                    logger.info(f"METADATA validation: has warnings?: {warnings}")

                    if valid and df is not None:
                        mismatch, mismatch_msg = compare_metadata_with_uploaded_files(submission, df)
                        sample_id = df.loc[0, "sample identifier"].strip()
                        logger.info(f"###### SAMPLE: {sample_id}")

                        original_sample_ids = list(set([
                            sid for sid in submission.uploadedfile_set.values_list("sample_id", flat=True) if sid
                        ]))
                        stored_sample_ids_lc = [sid.lower() for sid in original_sample_ids]

                        if stored_sample_ids_lc and sample_id.lower() not in stored_sample_ids_lc:
                            messages.error(request, f"Sample Identifier mismatch: '{sample_id}' does not match the sample identifier(s) of the existing uploaded file(s): {', '.join(original_sample_ids)}.\nPlease resubmit a corrected version.")
                            return redirect("resubmit_file", submission_id=submission.id, file_type=file_type)

                        if mismatch:
                            logger.warning(f"Metadata resubmission failed due to file mismatch:\n{mismatch_msg}")
                            messages.error(request, f"Validation failed:\n{mismatch_msg}\nPlease resubmit a corrected version.")
                            return redirect("resubmit_file", submission_id=submission.id, file_type=file_type)

                    #else:  # antibiotics
                    #    valid, warnings, message, delimiter, df = validate_and_save_csv(new_file, ANTIBIOTICS_COLUMNS)
                    #    logger.info(f"ANTIBIOTICS validation: {warnings}")

                    if not valid:
                        messages.error(request, f"Validation failed: {message}")
                        return redirect("resubmit_file", submission_id=submission.id, file_type=file_type)

                    if df is not None:
                        cleaned = generate_cleaned_file(new_file.name, df)
                        old.cleaned_file = cleaned

                # === DEBUG log before save ===
                logger.info(f"DEBUG BEFORE SAVE → file.name={old.file.name}, cleaned_file={(old.cleaned_file.name if old.cleaned_file else 'None')}, sample_id={old.sample_id}, file_type={old.file_type}")

                # === Save updated UploadedFile ===
                old.save()

                logger.info(f"WARNINGS: {warnings}")
                logger.info(f"MESSAGES: {message}")
                logger.info(f"RESUBMISSION ALLOWED before: {submission.resubmission_allowed}")

                if warnings:
                    submission.metadata_warnings = message
                    submission.save()
                    messages.warning(request, "File resubmitted with warnings.")
                else:
                    submission.resubmission_allowed = False
                    submission.metadata_warnings = ""
                    submission.save()
                    messages.success(request, "File resubmitted successfully.")

                # Reset form for next resubmit
                form = UploadFileForm()
                logger.info(f"RESUBMISSION ALLOWED after validation: {submission.resubmission_allowed}")

    else:
        form = UploadFileForm()

    history = FileHistory.objects.filter(submission=submission, file_type=f"{file_type}_raw").order_by("-timestamp")

    return render(request, "gensurvapp/resubmit_file.html", {
        "form": form,
        "submission": submission,
        "file_type": file_type,
        "history": history,
        "can_resubmit": submission.resubmission_allowed,
    })






@login_required
def bulk_upload(request):
    error_message = None
    success_message = None
    columns_data = []

    # Load column information
    column_info_path = os.path.join(settings.BASE_DIR, 'gensurvapp', 'static', 'bulk_upload_info.csv')
    try:
        column_info = pd.read_csv(column_info_path)
        columns_data = column_info.to_dict(orient='records')
    except FileNotFoundError:
        error_message = "Bulk upload column information file is missing."

    if request.method == 'POST':
        try:
            # Ensure 'bulk_file' exists in request.FILES
            if 'bulk_file' not in request.FILES:
                raise ValueError("Please provide a valid bulk upload file.")
            
            bulk_file = request.FILES['bulk_file']  # The uploaded CSV file
            chunk_size = 1000  # Process 1000 rows at a time
            
            for chunk_number, chunk in enumerate(pd.read_csv(bulk_file, chunksize=chunk_size), start=1):
                logging.info(f"Processing chunk {chunk_number}")
                process_chunk(chunk)

            success_message = "Bulk upload completed successfully."

        except ValueError as ve:
            error_message = str(ve)
        except Exception as e:
            error_message = f"An error occurred while processing the bulk upload: {str(e)}"
            logging.error(error_message)

    return render(request, 'gensurvapp/bulk_upload.html', {
        'columns_data': columns_data,
        'error_message': error_message,
        'success_message': success_message,
    })

@login_required
def process_chunk(chunk):
    for index, row in chunk.iterrows():
        try:
            # Process General Metadata file
            general_metadata_file = row['General Metadata File']
            with default_storage.open(general_metadata_file, 'rb') as f:
                general_metadata_df = pd.read_csv(f)
            logging.info(f"Processed General Metadata File: {general_metadata_file}")

            # Process Antibiotics Testing file
            antibiotics_testing_file = row['Antibiotics Testing File']
            with default_storage.open(antibiotics_testing_file, 'rb') as f:
                antibiotics_testing_df = pd.read_csv(f)
            logging.info(f"Processed Antibiotics Testing File: {antibiotics_testing_file}")

            # Process NGS raw data file
            ngs_file = row['NGS File']
            with default_storage.open(ngs_file, 'rb') as f:
                # Do something with the NGS file
                logging.info(f"Processed NGS File: {ngs_file}")

        except EmptyDataError as e:
            error_message = f"Empty or invalid CSV in file: {general_metadata_file if 'general_metadata_file' in locals() else antibiotics_testing_file if 'antibiotics_testing_file' in locals() else ngs_file}. Error: {str(e)}"
            logging.error(f"Row {index} skipped: {error_message}")

        except Exception as e:
            error_message = f"An error occurred while processing the file in row {index}: {str(e)}"
            logging.error(f"Row {index} skipped: {error_message}")


@login_required
def upload_data(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            metadata_file = request.FILES['metadata_file']
            fastq_files = request.FILES.getlist('fastq_files')

            metadata_df = pd.read_csv(metadata_file)
            # Process the uploaded files as needed
            context = {
                'metadata_file': metadata_file.name,
                'metadata_df': metadata_df.to_html(),
                'fastq_files': [f.name for f in fastq_files]
            }
            return render(request, 'gensurvapp/upload_success.html', context)
    else:
        form = FileUploadForm()
    return render(request, 'gensurvapp/upload_data.html', {'form': form})

def detailed_metadata_fields(request):
    return render(request, 'gensurvapp/detailed_metadata_fields.html')


@login_required
def upload(request):
    # Path to the CSV file
    csv_file_path =    os.path.join(settings.BASE_DIR, 'gensurvapp','static', 'sample_metadata.csv')

    columns_data = []
    try:
        with open(csv_file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                columns_data.append(row)
    except FileNotFoundError:
        error_message = f"CSV file not found: {csv_file_path}"
        return render(request, 'gensurvapp/upload.html', {'error_message': error_message})

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Process the uploaded files here
            pass

    else:
        form = FileUploadForm()

    return render(request, 'gensurvapp/upload.html', {'form': form, 'columns_data': columns_data})


@login_required
def search(request):
    query = request.GET.get('query', '')
    results = []
    if query:
        results = TodoItem.objects.filter(
            Q(name__icontains=query) |
            Q(item__text__icontains=query)
        ).distinct()

    return render(request, 'gensurvapp/search.html', {'query': query, 'results': results})
###test
def success_page(request):
    return render(request, 'gensurvapp/success.html')

@login_required
def help_view(request):
   # help_banner_message = "The upload formats are have been updated. Please refer to the documentation once this message is removed."
    help_banner_message = "The upload formats have been updated. Please contact the admin vickycees@gmail.com if you have any questions."

    # Paths to the CSV files
    metadata_csv_path = os.path.join(settings.BASE_DIR, 'gensurvapp', 'static', 'sample_metadata.csv')
    antibiotics_csv_path = os.path.join(settings.BASE_DIR, 'gensurvapp', 'static', 'sample_antibiotics.csv')

    sample_data = []
    antibiotics_data = []
    error_message = None

    try:
        # Read sample metadata CSV file
        with open(metadata_csv_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                sample_data.append(row)

        # Read antibiotics CSV file
        with open(antibiotics_csv_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                antibiotics_data.append(row)
    except FileNotFoundError as e:
        error_message = f"CSV file not found: {str(e)}"

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Process fastq files
                for f in request.FILES.getlist('fastq_files'):
                    print(f"Uploading file: {f.name}")
                    with default_storage.open(f.name, 'wb') as destination:
                        for chunk in f.chunks():
                            destination.write(chunk)  # Write file content as bytes
                    print(f"Saved fastq to FTP: {f.name}")

                # Process metadata file
                metadata_file = request.FILES['metadata_file']
                metadata_file_name = default_storage.save(metadata_file.name, metadata_file)
                print(f"Saved metadata file to FTP: {metadata_file_name}")

                # Process antibiotics file if present
                if 'antibiotics_file' in request.FILES:
                    antibiotics_file = request.FILES['antibiotics_file']
                    antibiotics_file_name = default_storage.save(antibiotics_file.name, antibiotics_file)
                    print(f"Saved antibiotics file to FTP: {antibiotics_file_name}")

                # Prepare the context for successful upload
                context = {
                    'metadata_file': metadata_file_name,
                    'fastq_files': [f.name for f in request.FILES.getlist('fastq_files')],
                    'antibiotics_file': antibiotics_file_name if 'antibiotics_file' in request.FILES else None,
                }

                return render(request, 'gensurvapp/upload_success.html', context)

            except EmptyDataError:
                # Handle the case where the metadata file is empty or invalid
                error_message = "The uploaded metadata file is empty or not a valid CSV."
    else:
        form = FileUploadForm()

    return render(request, 'gensurvapp/help.html', {
        'form': form,
        'sample_data': sample_data,
        'antibiotics_data': antibiotics_data,
        'error_message': error_message,
        'help_banner_message': help_banner_message,
    })

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



@login_required
def request_submission_deletion(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id, user=request.user)

    if submission.deletion_requested:
        messages.info(request, f"You have already requested deletion of submission #{submission.id}.")
        return redirect('dashboard')
    admin_email = settings.ADMINS[0][1] if settings.ADMINS else settings.DEFAULT_FROM_EMAIL
    # Send email to admin...
    send_mail(
        subject=f"🚨 Deletion Request: Submission #{submission.id}",
        message=f"User {request.user.email} has requested deletion of submission #{submission.id}.\n\n"
                f"Submission created at: {submission.created_at}\n"
                f"Bulk upload: {submission.is_bulk_upload}\n"
                f"Submission ID: {submission.id}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[admin_email],
    )

    submission.deletion_requested = True
    submission.save()

    messages.success(request, f"Deletion request for submission #{submission.id} has been sent to the admin.", extra_tags='dashboard')
    return redirect('dashboard')



@login_required
def user_dashboard(request):
    logger.debug("Entering user_dashboard view")
    logger.debug(f"User: {request.user.username}")

    #submissions = Submission.objects.prefetch_related('uploadedfile_set', 'sample_files').filter(user=request.user).order_by('-created_at')
    #sample_files_qs = UploadedFile.objects.filter(file_type__in=["metadata_cleaned", "metadata"])
    sample_files_qs = UploadedFile.objects.filter(file_type__in=["metadata_cleaned", "metadata_raw", "metadata"])

    #antibiotics_files_qs = UploadedFile.objects.filter(file_type="antibiotics")
    antibiotics_files_qs = UploadedFile.objects.filter(file_type__in=["antibiotics", "antibiotics_raw", "antibiotics_cleaned"])

    fastq_files_qs = UploadedFile.objects.filter(file_type="fastq")
    
    query_start = time.time()

    submissions = Submission.objects.prefetch_related(
        Prefetch('sample_files', queryset=sample_files_qs, to_attr='prefetched_sample_files'),
        Prefetch('uploadedfile_set', queryset=antibiotics_files_qs, to_attr='prefetched_antibiotics_files'),
        Prefetch('uploadedfile_set', queryset=fastq_files_qs, to_attr='prefetched_fastq_files')
    ).filter(user=request.user).order_by('-created_at')

    query_elapsed = time.time() - query_start
    logger.debug(f"🏁 Submissions query took {query_elapsed:.4f} seconds")
    logger.debug(f"Fetched {len(submissions)} submissions for user {request.user.username}")
    # Get counts of resubmissions per submission and file type
    history_counts = FileHistory.objects.values("submission_id", "file_type").annotate(count=Count("id"))

    # Convert to dict: {(submission_id, file_type): count}
    history_lookup = {
        (entry["submission_id"], entry["file_type"]): entry["count"]
        for entry in history_counts
    }

    context = []
    overall_start_time = time.time()
    metadata_resub_count = 0
    antibiotics_resub_count = 0

    # Build history_lookup 
    # Build sample_ids once:
    all_sample_ids = set()

    for submission in submissions:
        for fastq_file in submission.uploadedfile_set.filter(file_type="fastq"):
            if fastq_file.sample_id:
                all_sample_ids.add(fastq_file.sample_id)

    # Fetch analysis results in ONE query:
    analysis_results = AnalysisResult.objects.filter(sample__sample_id__in=all_sample_ids).order_by('-completion_date')

    # Build lookup:
    analysis_lookup = {}
    for result in analysis_results:
        sample_id = result.sample.sample_id
        if sample_id not in analysis_lookup:
            analysis_lookup[sample_id] = result.status


    for submission in submissions:
        submission_start = time.time()
        logger.debug(f"▶️ Processing submission ID: {submission.id}")
        logger.debug(f"➡️ is_bulk_upload: {submission.is_bulk_upload}")
        logger.debug(f"➡️ resubmission_allowed: {submission.resubmission_allowed}")

        antibiotics_files = submission.prefetched_antibiotics_files
        fastq_files = submission.prefetched_fastq_files
        sample_files = submission.prefetched_sample_files


        logger.debug(f"🧬 FASTQ count: {len(fastq_files)} | 🧫 Antibiotics file count: {len(antibiotics_files)}")

        # Find cleaned_metadata ONCE here:
        cleaned_metadata = submission.uploadedfile_set.filter(file_type="metadata_cleaned").first()
        if not cleaned_metadata:
            cleaned_metadata = submission.uploadedfile_set.filter(file_type="metadata_raw").first()

        raw_metadata = submission.uploadedfile_set.filter(file_type="metadata_raw").first()
        if cleaned_metadata:
            logger.debug(f"🧼 Cleaned metadata file exists? {'Yes' if cleaned_metadata.cleaned_file else 'No'}")
        else:
            logger.debug(f"🧼 Cleaned metadata file exists? {'No'}")
        logger.debug(f"🧾 Metadata files for submission {submission.id}:")
        logger.debug(f"   - Cleaned: {cleaned_metadata.cleaned_file.name if cleaned_metadata and cleaned_metadata.cleaned_file else 'None'}")
        logger.debug(f"   - Raw: {raw_metadata.file.name if raw_metadata and raw_metadata.file else 'None'}")


                
        ### Timer 1 → grouping fastq_files
        grouping_start = time.time()
        grouped_fastq_files = {}
        sample_analysis_status = {}

        for fastq_file in fastq_files:
            sample_id = fastq_file.sample_id if fastq_file.sample_id else "unknown"
            grouped_fastq_files.setdefault(sample_id, []).append(fastq_file)

            if sample_id != "unknown":
                status = analysis_lookup.get(sample_id, "pending")
                sample_analysis_status[sample_id] = status
        grouping_elapsed = time.time() - grouping_start
        logger.debug(f"⏱ grouping fastq_files took {grouping_elapsed:.4f} seconds")
        
        logger.debug(f"📦 Grouped FASTQ Files: {grouped_fastq_files}")
        logger.debug(f"📊 Sample Analysis Status: {sample_analysis_status}")

        # Single submission metadata parsing
         ### Timer 2 → parse_metadata_sample_ids (only for single submission)
        metadata_sample_ids_elapsed = 0.0
        sample_id = None
        # Antibiotics Info
        antibiotics_info = {}
        # single upload logic
        if not submission.is_bulk_upload:
            logger.debug(f"🧼 Single Cleaned metadata found: {bool(cleaned_metadata)}")

            if cleaned_metadata and cleaned_metadata.file:
                try:
                    metadata_start = time.time()
                    sample_id = cached_parse_metadata_sample_ids(cleaned_metadata.file.path)
                    metadata_sample_ids_elapsed = time.time() - metadata_start
                    logger.debug(f"⏱ cached_parse_metadata_sample_ids took {metadata_sample_ids_elapsed:.4f} seconds")
                    logger.debug(f"📍 Extracted sample_id from metadata: {sample_id}")
                except Exception as e:
                    logger.warning(f"❌ Error parsing sample_id: {e}")

                if sample_id:
                    grouped_fastq_files[sample_id] = list(fastq_files)
                    sample_analysis_status[sample_id] = "pending"
        
            logger.debug("🔎 Attempting to parse antibiotics_info for single upload...")

            if not antibiotics_files:
                logger.debug(f"🧼 Cleaned metadata exists: {bool(cleaned_metadata)}")

                if cleaned_metadata and cleaned_metadata.file:
                    #  Make sure sample_id is parsed before checking
                    #sample_id = sample_id or cached_parse_metadata_sample_ids(cleaned_metadata.file.path)
                    if not sample_id:
                        logger.warning(f"❗ No sample_id could be extracted for submission {submission.id}")

                    logger.debug(f"🔬 Using sample_id for antibiotics info: {sample_id}")

                    if sample_id:
                        try:
                            info = parse_metadata_antibiotics_info(cleaned_metadata.file.path, target_sample_id=sample_id)
                            logger.debug(f"🧪 Antibiotics info extracted for sample {sample_id}: {info}")
                            if info:
                                antibiotics_info = {sample_id: info}
                        except Exception as e:
                            logger.warning(f"❌ Error parsing antibiotics info (single): {e}")
                    else:
                        logger.debug("⚠️ Skipped parsing: sample_id missing after fallback.")
            else:
                logger.debug("⛔ Skipping antibiotics info parse: antibiotics files already exist.")
        
        #elif not submission.is_bulk_upload:
        # bulk upload logic
        else:
            logger.debug(f"🧼 Bulk: Cleaned metadata file found1: {bool(cleaned_metadata)}")
            if cleaned_metadata and cleaned_metadata.file:
                try:
                    logger.debug(f"🧼 Bulk: Cleaned metadata file found2: {bool(cleaned_metadata)}")

                    ### Timer 3 → cached_parse_metadata_antibiotics_info (only for bulk)
                    antibiotics_start = time.time()
                    full_info = cached_parse_metadata_antibiotics_info(cleaned_metadata.file.path)
                    antibiotics_elapsed = time.time() - antibiotics_start
                    logger.debug(f"⏱ cached_parse_metadata_antibiotics_info took {antibiotics_elapsed:.4f} seconds")
                    logger.debug(f"🔍 Parsed antibiotics_info from metadata: {full_info}")
                except Exception as e:
                    logger.warning(f"❌ Error parsing antibiotics info (bulk): {e}")
                    full_info = {}

                sample_ids_with_file = {f.sample_id for f in antibiotics_files if f.file}
                logger.debug(f"📛 Samples with antibiotics files: {sample_ids_with_file}")

                antibiotics_info = {
                    sample_id: info for sample_id, info in full_info.items()
                    if sample_id not in sample_ids_with_file
                }
                logger.debug(f"✅ Final antibiotics_info (bulk): {antibiotics_info}")

        
        metadata_resub_count = history_lookup.get((submission.id, "metadata_raw"), 0)
        antibiotics_resub_count = history_lookup.get((submission.id, "antibiotics_raw"), 0)

        if submission.id == 119:
            for sample in sample_analysis_status:
                sample_analysis_status[sample] = "completed"
                
        # timing
        ###  existing context append + submission timer
        submission_elapsed = time.time() - submission_start
        logger.debug(f"⏱ Submission {submission.id} processed in {submission_elapsed:.4f} seconds")

        context.append({
            'submission': submission,
            'antibiotics_files': antibiotics_files,
            'antibiotics_info': antibiotics_info,
            'grouped_fastq_files': grouped_fastq_files,
            'sample_analysis_status': sample_analysis_status,
            'metadata_resub_count': metadata_resub_count,
            'antibiotics_resub_count': antibiotics_resub_count,
        })

    logger.debug("✅ Finished building dashboard context")
    overall_elapsed = time.time() - overall_start_time
    logger.debug(f"🏁 TOTAL dashboard build time: {overall_elapsed:.4f} seconds")

    return render(request, 'gensurvapp/dashboard.html', {'submissions': context})


@login_required
def dashboard_and_search(request):
    # Ensure related fastq_files are being fetched
    user_submissions = Submission.objects.prefetch_related('fastq_files').filter(user=request.user)

    # Pagination setup
    paginator = Paginator(user_submissions, 10)  # Show 10 submissions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Handle search functionality
    query = request.GET.get('query', '')
    search_results = []
    if query:
        search_results = TodoItem.objects.filter(
            Q(name__icontains=query) |
            Q(item__text__icontains=query)
        ).distinct()

    context = {
        'page_obj': page_obj,  # Pass paginated submissions
        'query': query,
        'search_results': search_results,
    }
    return render(request, 'gensurvapp/dashboard_and_search.html', context)





# View for the list of samples in a submission
def submission_resultsx(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    bactopia_results = BactopiaResult.objects.filter(submission=submission)
    plasmid_ident_results = PlasmidIdentResult.objects.filter(submission=submission)

    # Combine sample IDs from both result types to ensure all samples are shown
    sample_ids = set(bactopia_results.values_list("sample_id", flat=True)) | set(
        plasmid_ident_results.values_list("sample_id", flat=True)
    )

    context = {
        'submission': submission,
        'sample_ids': sample_ids,  # Pass all sample IDs for the menu
    }
    return render(request, 'gensurvapp/submissions/submission_results.html', context)



# View for the list of samples in a submission
def submission_results(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    bactopia_results = BactopiaResult.objects.filter(submission=submission)
    plasmid_ident_results = PlasmidIdentResult.objects.filter(submission=submission)

    # Combine and sort sample IDs from both result types
    sample_ids = sorted(
        set(bactopia_results.values_list("sample_id", flat=True)) | 
        set(plasmid_ident_results.values_list("sample_id", flat=True))
    )

    context = {
        'submission': submission,
        'sample_ids': sample_ids,  # Pass all sample IDs for the menu
    }
    return render(request, 'gensurvapp/submissions/submission_results.html', context)


# View for a specific sample's results


def read_tsv_filex(file_path):
    """Reads a TSV file and returns its content as a list of dictionaries."""
    # Build the full path
    full_path = os.path.join(settings.MEDIA_ROOT, file_path.lstrip('/'))
    logger.debug(f"DEBUG: Attempting to read file: {full_path}")

    if not os.path.exists(full_path):
        logger.debug(f"DEBUG: File does not exist: {full_path}")
        return None

    try:
        with open(full_path, 'r') as tsv_file:
            reader = csv.DictReader(tsv_file, delimiter='\t')
            data = list(reader)
            logger.debug(f"DEBUG: Successfully read {len(data)} rows from {full_path}")
            return data
    except Exception as e:
        logger.error(f"DEBUG: Error reading file {full_path}: {e}")
        return None



def sample_results_detailed_former(request, submission_id, sample_id):
    submission = get_object_or_404(Submission, id=submission_id)
    bactopia_result = BactopiaResult.objects.filter(submission=submission, sample_id=sample_id).first()
    logger.debug(f"DEBUG: bactopia_result read: {bactopia_result}")
    plasmid_ident_result = PlasmidIdentResult.objects.filter(submission=submission, sample_id=sample_id).first()
    logger.debug(f"DEBUG: plasmid_ident_result read: {plasmid_ident_result}")


    amrfinderplus_data = None
    assembly_scan_data = None

    if bactopia_result:
        # Use relative paths to MEDIA_ROOT
        amrfinderplus_path = f"bactopia_results/submission_{submission_id}/{sample_id}/bactopia-runs/bactopia-20241206-082913/merged-results/amrfinderplus.tsv"
        assembly_scan_path = f"bactopia_results/submission_{submission_id}/{sample_id}/bactopia-runs/bactopia-20241206-082913/merged-results/assembly-scan.tsv"

        logger.debug(f"DEBUG: AMRFinderPlus path: {amrfinderplus_path}")
        logger.debug(f"DEBUG: Assembly Scan path: {assembly_scan_path}")
        
        amrfinderplus_data = read_tsv_file(amrfinderplus_path)
        assembly_scan_data = read_tsv_file(assembly_scan_path)

        # Get all FASTA files in the plasmid directory
    plasmid_files = [] 
    plot_files = [] 

    if plasmid_ident_result:
        # Ensure plasmid_ident_result has a directory_path attribute
        plasmident_base_dir = getattr(plasmid_ident_result, 'directory_path', None)
        logger.debug(f"DEBUG: PlasmidIdentResult directory_path: {plasmident_base_dir}")

        if plasmident_base_dir:
            # Remove leading `/media` from directory_path if present
            if plasmident_base_dir.startswith('/media'):
                plasmident_base_dir = plasmident_base_dir[len('/media'):]
            
            # Combine MEDIA_ROOT and corrected directory_path for plasmid fastas
            plasmid_dir_path = Path(settings.MEDIA_ROOT) / plasmident_base_dir.strip('/') / f"{sample_id}/plasmids"
            logger.debug(f"DEBUG: Final plasmid directory path: {plasmid_dir_path}")

            if plasmid_dir_path.exists() and plasmid_dir_path.is_dir():
                plasmid_files = [file.name for file in plasmid_dir_path.glob("*.fasta")]
                logger.debug(f"DEBUG: Found plasmid files: {plasmid_files}")
            else:
                logger.warning(f"WARNING: Plasmid directory does not exist: {plasmid_dir_path}")

            # Combine MEDIA_ROOT and corrected directory_path for plot images
            plot_dir_path = Path(settings.MEDIA_ROOT) / plasmident_base_dir.strip('/') / f"{sample_id}/plots"
            logger.debug(f"DEBUG: Final plot directory path: {plot_dir_path}")

            if plot_dir_path.exists() and plot_dir_path.is_dir():
                plot_files = [file.name for file in plot_dir_path.glob("*.png")]
                logger.debug(f"DEBUG: Found plot files: {plot_files}")
            else:
                logger.warning(f"WARNING: Plot directory does not exist: {plot_dir_path}")


        else:
            logger.warning("WARNING: PlasmidIdentResult does not have a valid directory_path.")


    context = {
        'submission': submission,
        'sample_id': sample_id,
        'bactopia_result': bactopia_result,
        'plasmid_ident_result': plasmid_ident_result,
        'plasmid_files': plasmid_files,
        'plot_files': plot_files,
        'amrfinderplus_data': amrfinderplus_data,
        'assembly_scan_data': assembly_scan_data,
    }
    return context





def read_tsv_file(file_path):
    """Reads a TSV file and returns its content as a list of dictionaries."""
    try:
        with open(file_path, 'r') as tsv_file:
            reader = csv.DictReader(tsv_file, delimiter='\t')
            return list(reader)
    except FileNotFoundError:
        logger.error(f"ERROR: File not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"ERROR: Failed to read file {file_path}: {e}")
        return None

def clean_media_path(base_path):
    """Removes leading /media if present and returns a Path object."""
    if base_path.startswith('/media'):
        base_path = base_path[len('/media'):]
    return Path(settings.MEDIA_ROOT) / base_path.strip('/')


def process_summary_data(summary_data, plot_files):
    """
    Process summary data to compute metrics and filter for rows with AR genes.
    """

    # Debug: Initial data
    logger.debug("DEBUG: Starting process_summary_data.")
    logger.debug(f"DEBUG: Summary data received: {summary_data}")
    logger.debug(f"DEBUG: Plot files received: {plot_files}")

    # Create DataFrame from summary data
    try:
        df = pd.DataFrame(summary_data)
        logger.debug("DEBUG: DataFrame created successfully.")
    except Exception as e:
        logger.error(f"ERROR: Failed to create DataFrame: {e}")
        return None

    # Count unique contigs and AR genes
    try:
        num_contigs = df['contig'].nunique()
        #num_ar_genes = df['ar_genes'].notnull().sum()
        num_ar_genes = df['ar_genes'].apply(lambda x: bool(x) and pd.notnull(x)).sum()

        logger.debug(f"DEBUG: Number of unique contigs: {num_contigs}")
        logger.debug(f"DEBUG: Number of AR genes: {num_ar_genes}")
    except Exception as e:
        logger.error(f"ERROR: Failed to compute contig or AR gene metrics: {e}")
        return None

    # Filter rows with AR genes and sort by contig
    try:
        #ar_genes_df = df[df['ar_genes'].notnull()].sort_values(by='contig')
        ar_genes_df = df[df['ar_genes'].apply(lambda x: pd.notnull(x) and x.strip() != "")].sort_values(by='contig')
        logger.debug(f"DEBUG: Filtered AR genes DataFrame: {ar_genes_df}")
    except Exception as e:
        logger.error(f"ERROR: Failed to filter rows with AR genes: {e}")
        return None

    # Get contigs with AR genes
    try:
        contigs_with_ar_genes = ar_genes_df['contig'].unique()
        logger.debug(f"DEBUG: Contigs with AR genes: {contigs_with_ar_genes}")
    except Exception as e:
        logger.error(f"ERROR: Failed to get contigs with AR genes: {e}")
        return None

    # Filter plot files for contigs with AR genes
    try:
        filtered_plot_files = [
            plot_file for plot_file in plot_files
            if any(contig in plot_file for contig in contigs_with_ar_genes)
        ]
        logger.debug(f"DEBUG: Filtered plot files: {filtered_plot_files}")
    except Exception as e:
        logger.error(f"ERROR: Failed to filter plot files: {e}")
        return None

    # Debug: Final processed data
    processed_data = {
        "num_contigs": num_contigs,
        "num_ar_genes": num_ar_genes,
        "ar_genes_df": ar_genes_df,
        "filtered_plot_files": filtered_plot_files,
    }
    logger.debug(f"DEBUG: Final processed data: {processed_data}")

    return processed_data


def sample_results_detailedprev(request, submission_id, sample_id):
    submission = get_object_or_404(Submission, id=submission_id)
    bactopia_result = BactopiaResult.objects.filter(submission=submission, sample_id=sample_id).first()
    logger.debug(f"DEBUG: bactopia_result read: {bactopia_result}")
    plasmid_ident_result = PlasmidIdentResult.objects.filter(submission=submission, sample_id=sample_id).first()
    logger.debug(f"DEBUG: plasmid_ident_result read: {plasmid_ident_result}")

    amrfinderplus_data = None
    assembly_scan_data = None
    plasmid_files = []
    plot_files = []
    plasmid_summary_data = None
    processed_data = None


    if bactopia_result:
        amrfinderplus_path = Path(settings.MEDIA_ROOT) / f"bactopia_results/submission_{submission_id}/{sample_id}/bactopia-runs/bactopia-20241206-082913/merged-results/amrfinderplus.tsv"
        assembly_scan_path = Path(settings.MEDIA_ROOT) / f"bactopia_results/submission_{submission_id}/{sample_id}/bactopia-runs/bactopia-20241206-082913/merged-results/assembly-scan.tsv"

        logger.debug(f"DEBUG: AMRFinderPlus path: {amrfinderplus_path}")
        logger.debug(f"DEBUG: Assembly Scan path: {assembly_scan_path}")
        
        if amrfinderplus_path.exists():
            amrfinderplus_data = read_tsv_file(amrfinderplus_path)
        else:
            logger.warning(f"WARNING: AMRFinderPlus file does not exist: {amrfinderplus_path}")

        if assembly_scan_path.exists():
            assembly_scan_data = read_tsv_file(assembly_scan_path)
        else:
            logger.warning(f"WARNING: Assembly Scan file does not exist: {assembly_scan_path}")

    if plasmid_ident_result:
        plasmident_base_dir = getattr(plasmid_ident_result, 'directory_path', None)
        logger.debug(f"DEBUG: PlasmidIdentResult directory_path: {plasmident_base_dir}")

        if plasmident_base_dir:
            plasmident_base_dir = clean_media_path(plasmident_base_dir)
            plasmid_dir_path = plasmident_base_dir / f"{sample_id}/plasmids"
            plot_dir_path = plasmident_base_dir / f"{sample_id}/plots"
            plasmid_summary_path = plasmident_base_dir / f"{sample_id}/{sample_id}_summary.csv"

            logger.debug(f"DEBUG: Final plasmid directory path: {plasmid_dir_path}")
            logger.debug(f"DEBUG: Final plot directory path: {plot_dir_path}")
            logger.debug(f"DEBUG: Plasmid summary file path: {plasmid_summary_path}")

            # Collect plasmid FASTA files
            if plasmid_dir_path.exists() and plasmid_dir_path.is_dir():
                plasmid_files = [file.name for file in plasmid_dir_path.glob("*.fasta")]
            else:
                logger.warning(f"WARNING: Plasmid directory does not exist: {plasmid_dir_path}")

            # Collect plot files
            if plot_dir_path.exists() and plot_dir_path.is_dir():
                plot_files = [file.name for file in plot_dir_path.glob("*.png")]
            else:
                logger.warning(f"WARNING: Plot directory does not exist: {plot_dir_path}")

            # Read plasmid summary data
            if plasmid_summary_path.exists():
                try:
                    plasmid_summary_data = read_tsv_file(plasmid_summary_path)
                except Exception as e:
                    logger.error(f"ERROR: Failed to process plasmid_summary_data: {e}")
                try:
                    processed_data = process_summary_data(plasmid_summary_data, plot_files)
                    logger.debug(f"DEBUG: DONE process_summary_data: {processed_data}")
                except Exception as e:
                    logger.error(f"ERROR: Failed process_summary_data: {e}")
            else:
                logger.warning(f"WARNING: Plasmid Summary file does not exist: {plasmid_summary_path}")



        else:
            logger.warning("WARNING: PlasmidIdentResult does not have a valid directory_path.")

    
    context = {
        'submission': submission,
        'sample_id': sample_id,
        'bactopia_result': bactopia_result,
        'plasmid_ident_result': plasmid_ident_result,
        'plasmid_files': plasmid_files,
        'plot_files': plot_files,
        'amrfinderplus_data': amrfinderplus_data,
        'assembly_scan_data': assembly_scan_data,
        'plasmid_summary_data': plasmid_summary_data,
        'processed_data': processed_data,
        'num_contigs': processed_data.get('num_contigs') if processed_data else None,
        'num_ar_genes': processed_data.get('num_ar_genes') if processed_data else None,
        'ar_genes_df': processed_data.get('ar_genes_df') if processed_data else None,
        'filtered_plot_files': processed_data.get('filtered_plot_files') if processed_data else None,
    }
    return context

def sample_results_detailed(request, submission_id, sample_id):
    submission = get_object_or_404(Submission, id=submission_id)
    bactopia_result = BactopiaResult.objects.filter(submission=submission, sample_id=sample_id).first()
    logger.debug(f"DEBUG: bactopia_result read: {bactopia_result}")
    plasmid_ident_result = PlasmidIdentResult.objects.filter(submission=submission, sample_id=sample_id).first()
    logger.debug(f"DEBUG: plasmid_ident_result read: {plasmid_ident_result}")

    amrfinderplus_data = None
    assembly_scan_data = None
    plasmid_files = []
    plot_files = []
    plasmid_summary_data = None
    processed_data = None

    if bactopia_result:
        amrfinderplus_path = Path(settings.MEDIA_ROOT) / f"bactopia_results/submission_{submission_id}/{sample_id}/bactopia-runs/bactopia-20241206-082913/merged-results/amrfinderplus.tsv"
        assembly_scan_path = Path(settings.MEDIA_ROOT) / f"bactopia_results/submission_{submission_id}/{sample_id}/bactopia-runs/bactopia-20241206-082913/merged-results/assembly-scan.tsv"

        logger.debug(f"DEBUG: AMRFinderPlus path: {amrfinderplus_path}")
        logger.debug(f"DEBUG: Assembly Scan path: {assembly_scan_path}")
        
        if amrfinderplus_path.exists():
            amrfinderplus_data = read_tsv_file(amrfinderplus_path)
        else:
            logger.warning(f"WARNING: AMRFinderPlus file does not exist: {amrfinderplus_path}")

        if assembly_scan_path.exists():
            assembly_scan_data = read_tsv_file(assembly_scan_path)
        else:
            logger.warning(f"WARNING: Assembly Scan file does not exist: {assembly_scan_path}")

    if plasmid_ident_result:
        plasmident_base_dir = getattr(plasmid_ident_result, 'directory_path', None)
        logger.debug(f"DEBUG: PlasmidIdentResult directory_path: {plasmident_base_dir}")

        if plasmident_base_dir:
            plasmident_base_dir = clean_media_path(plasmident_base_dir)
            plasmid_dir_path = plasmident_base_dir / f"{sample_id}/plasmids"
            plot_dir_path = plasmident_base_dir / f"{sample_id}/plots"
            plasmid_summary_path = plasmident_base_dir / f"{sample_id}/{sample_id}_summary.csv"

            logger.debug(f"DEBUG: Final plasmid directory path: {plasmid_dir_path}")
            logger.debug(f"DEBUG: Final plot directory path: {plot_dir_path}")
            logger.debug(f"DEBUG: Plasmid summary file path: {plasmid_summary_path}")

            # Collect plasmid FASTA files
            if plasmid_dir_path.exists() and plasmid_dir_path.is_dir():
                plasmid_files = [file.name for file in plasmid_dir_path.glob("*.fasta")]
            else:
                logger.warning(f"WARNING: Plasmid directory does not exist: {plasmid_dir_path}")

            # Collect plot files
            if plot_dir_path.exists() and plot_dir_path.is_dir():
                plot_files = [file.name for file in plot_dir_path.glob("*.png")]
            else:
                logger.warning(f"WARNING: Plot directory does not exist: {plot_dir_path}")

            # Read plasmid summary data
            if plasmid_summary_path.exists():
                try:
                    plasmid_summary_data = read_tsv_file(plasmid_summary_path)
                except Exception as e:
                    logger.error(f"ERROR: Failed to process plasmid_summary_data: {e}")
                try:
                    processed_data = process_summary_data(plasmid_summary_data, plot_files)
                    logger.debug(f"DEBUG: DONE process_summary_data: {processed_data}")
                except Exception as e:
                    logger.error(f"ERROR: Failed process_summary_data: {e}")
            else:
                logger.warning(f"WARNING: Plasmid Summary file does not exist: {plasmid_summary_path}")
        else:
            logger.warning("WARNING: PlasmidIdentResult does not have a valid directory_path.")

    # Convert DataFrame to list of dictionaries for Django templates
    ar_genes_table = (
        processed_data["ar_genes_df"].to_dict(orient="records")
        if processed_data and "ar_genes_df" in processed_data
        else None
    )

    context = {
        'submission': submission,
        'sample_id': sample_id,
        'bactopia_result': bactopia_result,
        'plasmid_ident_result': plasmid_ident_result,
        'plasmid_files': plasmid_files,
        'plot_files': plot_files,
        'amrfinderplus_data': amrfinderplus_data,
        'assembly_scan_data': assembly_scan_data,
        'plasmid_summary_data': plasmid_summary_data,
        'num_contigs': processed_data.get('num_contigs') if processed_data else None,
        'num_ar_genes': processed_data.get('num_ar_genes') if processed_data else None,
        'ar_genes_table': ar_genes_table,
        'filtered_plot_files': processed_data.get('filtered_plot_files') if processed_data else None,
    }
    return context


def sample_results(request, submission_id, sample_id):
    context = sample_results_detailed(request, submission_id, sample_id)
    context['submission_id'] = submission_id  # Ensure submission_id is included
    return render(request, 'gensurvapp/submissions/sample_results.html', context)

def sample_all_results(request, submission_id, sample_id):
    context = sample_results_detailed(request, submission_id, sample_id)
    context['submission_id'] = submission_id  # Ensure submission_id is included
    return render(request, 'gensurvapp/submissions/sample_all_results.html', context)


def fetch_tsv_data(request, file_path):
    """Reads a TSV file and returns its content as JSON."""
    full_path = f"{file_path}"
    try:
        with open(full_path, "r") as tsvfile:
            reader = csv.DictReader(tsvfile, delimiter="\t")
            rows = [row for row in reader]
        return JsonResponse({"data": rows})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



def test_page(request, submission_id, sample_id):
    # Fetch the BactopiaResult for testing
    bactopia_result = BactopiaResult.objects.filter(
        submission_id=submission_id, sample_id=sample_id
    ).first()

    if not bactopia_result:
        raise Http404("BactopiaResult not found")

    context = {
        'bactopia_result': bactopia_result,
        'submission_id': submission_id,  # Ensure submission_id is passed to the template
        'sample_id': sample_id,          # Ensure sample_id is passed to the template
    }

    return render(request, 'gensurvapp/test_page.html', context)


def submission_list(request):
    if request.user.is_authenticated:
        submissions = Submission.objects.filter(user=request.user)
    else:
        submissions = None
    return render(request, 'gensurvapp/submissions/submission_list.html', {'submissions': submissions})


def base_context(request):
    if request.user.is_authenticated:
        submissions = Submission.objects.filter(user=request.user)
    else:
        submissions = None
    return {'submissions': submissions}
