import os
import shutil
from django.conf import settings

def copy_file_to_history(source_file_path, target_filename=None):
    """
    Copy a file from source_file_path to media/history/ and return relative path to use in FileField.

    Args:
        source_file_path (str): Full path to source file (MEDIA_ROOT/...)
        target_filename (str, optional): Filename to use in history/. If None, will use basename of source.

    Returns:
        str: Relative path to history/filename.ext
    """
    media_root = settings.MEDIA_ROOT
    history_dir = os.path.join(media_root, 'history')

    # Create history folder if missing
    os.makedirs(history_dir, exist_ok=True)

    # Determine target filename
    if target_filename is None:
        target_filename = os.path.basename(source_file_path)

    target_path = os.path.join(history_dir, target_filename)

    # Actually copy file
    shutil.copy2(source_file_path, target_path)

    # Return relative path (relative to MEDIA_ROOT) to store in FileField
    return os.path.join('history', target_filename)

