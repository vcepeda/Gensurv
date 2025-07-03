import csv
import os
from django.conf import settings
from django.shortcuts import render

def upload(request):
    # Path to the CSV file
    csv_file_path = os.path.join(settings.STATIC_ROOT, 'sample_metadata.csv')

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

