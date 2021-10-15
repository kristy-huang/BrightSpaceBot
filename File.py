from enum import Enum


class StorageTypes(Enum):
    NONE = 0
    LOCAL_STORAGE = 1
    GOOGLE_DRIVE = 2


class File:
    # Initializing all the components...

    def __init__(self, title, path):
        self.fileTitle = title  # name of the file
        self.filePath = path  # path for either local or ID for google stuff?
        # probably change this with enums to indicate where it will be located?
        # for now, 0 = local, 1 = google drive
        self.storageType = StorageTypes.NONE

    def get_info(self):
        # Mainly for debugging purposes
        info = self.fileTitle + " located at: " + self.filePath + " " + ". Type = " + str(self.storageType)
        return info
