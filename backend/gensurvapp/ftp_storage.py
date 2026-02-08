from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from ftplib import FTP
import os

class FTPStorage(Storage):
    def __init__(self, location, base_url, ftp_server, ftp_user, ftp_password):
        self.location = location
        self.base_url = base_url
        self.ftp_server = ftp_server
        self.ftp_user = ftp_user
        self.ftp_password = ftp_password

    def _open(self, name, mode='rb'):
        # Implement open method if needed
        pass

    def _save(self, name, content):
        with FTP(self.ftp_server) as ftp:
            ftp.login(self.ftp_user, self.ftp_password)
            ftp.cwd(self.location)

            filename = os.path.join(self.location, name)
            ftp.storbinary(f'STOR {filename}', content.file)

        return name

    def exists(self, name):
        with FTP(self.ftp_server) as ftp:
            ftp.login(self.ftp_user, self.ftp_password)
            ftp.cwd(self.location)
            files = ftp.nlst()

        return name in files

    def url(self, name):
        return os.path.join(self.base_url, name)

    def delete(self, name):
        with FTP(self.ftp_server) as ftp:
            ftp.login(self.ftp_user, self.ftp_password)
            ftp.cwd(self.location)
            ftp.delete(name)

    def listdir(self, path):
        with FTP(self.ftp_server) as ftp:
            ftp.login(self.ftp_user, self.ftp_password)
            ftp.cwd(self.location)
            files = ftp.nlst()
        return [], files

    def size(self, name):
        # Implement size method if needed
        pass

    def accessed_time(self, name):
        # Implement accessed_time method if needed
        pass

    def created_time(self, name):
        # Implement created_time method if needed
        pass

    def modified_time(self, name):
        # Implement modified_time method if needed
        pass

