# gensurvapp/templatetags/custom_tags.py
from django import template
import os
from pathlib import Path
from glob import glob

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def dict_get(dictionary, key):
    """Fetch a value from a dictionary safely."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def plasmid_files(directory, pattern):
    """Return a list of files matching the given pattern in the directory."""
    base_path = os.path.join(directory, pattern)
    return glob(base_path)

@register.filter
def basename(file_path):
    """Extract the base name of a file from its path."""
    return os.path.basename(file_path)

@register.filter
def sample_ids_from(files):
    return [f.sample_id for f in files if f.sample_id]

@register.filter
def get_file(file_queryset, file_type):
    return file_queryset.filter(file_type=file_type).first()

@register.filter
def get_sample_file(file_queryset, sample_id):
    """
    Return the first file from file_queryset with matching sample_id.
    """
    return next((f for f in file_queryset if f.sample_id == sample_id), None)

@register.filter
def union(a, b):
    """
    Return the union of two lists or dict keys.
    Usage: list_a|union:list_b
    """
    if hasattr(a, 'keys'):
        a = list(a.keys())
    if hasattr(b, 'keys'):
        b = list(b.keys())
    return sorted(set(a) | set(b))

