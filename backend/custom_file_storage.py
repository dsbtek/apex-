from django.core.files.storage import FileSystemStorage

class CustomFileStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        return name

    def _save(self, name, content):
        if self.exists(name):
            return name
        return super(CustomFileStorage,self)._save(name, content)
        