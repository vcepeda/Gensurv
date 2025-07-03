# gensurvapp/utils/file_debugger.py
import logging

logger = logging.getLogger(__name__)

class DebugFileWrapper:
    """
    A wrapper around file-like objects to debug file operations such as open, read, seek, and close.
    """
    def __init__(self, file):
        self.file = file
        logger.debug(f"File opened: {getattr(file, 'name', 'Unknown')}")

    def read(self, *args, **kwargs):
        logger.debug(f"Reading file: {getattr(self.file, 'name', 'Unknown')}")
        return self.file.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        logger.debug(f"Seeking file: {getattr(self.file, 'name', 'Unknown')}, args: {args}")
        return self.file.seek(*args, **kwargs)

    def close(self):
        logger.debug(f"File closed: {getattr(self.file, 'name', 'Unknown')}")
        return self.file.close()

    def __del__(self):
        logger.debug(f"File wrapper garbage collected: {getattr(self.file, 'name', 'Unknown')}")
