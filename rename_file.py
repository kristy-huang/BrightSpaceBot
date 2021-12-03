import os
from File import File


class RenameFile:

    # given the directory of the storage location (root), sees if there is a file
    def find_file(self, name, directory):
        for root, dirs, files in os.walk(directory):
            if name in files:
                return os.path.join(root, name)  # returns the absolute path
        return None

    # checks if the request file name has the correct path already or not
    # returns True if it contains the correct extension
    def contains_extension(self, file, extension):
        arr = file.rsplit(".", 1)
        if len(arr) == 1:
            # that means there was no extension
            # add the extension to the file name requested
            file = file + "." + extension
            return True, file
        else:
            # it contains the extension
            # check to see if the extension the file path currently has is the right one
            if arr[1] == extension:
                # extensions are same
                return True, file
            else:
                # extensions did not match
                return False, None

    # Renames a file on the local machine
    def rename_file_local(self, oldFileName, newFileName):
        split = oldFileName.rsplit('/', 1)  # splits from last slash from the back
        extension = oldFileName.rsplit(".", 1)[1]  # get the file extension
        status, rename = self.contains_extension(newFileName, extension)
        if not status:
            # the requested path was not valid
            return False
        else:
            new_file_path = os.path.join(split[0], rename)
            os.rename(oldFileName, new_file_path)
            return True

    # Lists all the files in a directory (including files in subdirectories)
    def list_files_local(self, directory):
        flist = []
        for root, dirs, files in os.walk(directory):
            for f in files:
                string = os.path.join(root, f)
                flist.append(string)
        return flist

    ''' GOOGLE DRIVE METHODS '''

    # Returns the title and ID of the directory you passed
    def get_folder_id(self, drive, directory):
        fileList = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        # Use this to save all the folders in 'MyDrive'
        folderList = []
        for file in fileList:
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                if file['title'] == directory:
                    return file['title'], file['id']

    # Returns a list of files that are in a directory
    def get_files_from_specified_folder(self, drive, directory_id, files):
        string = f"'{directory_id}' in parents and trashed = false"
        fileList = drive.ListFile({'q': string}).GetList()
        for item in fileList:
            if item['mimeType'] != 'application/vnd.google-apps.folder':
                files.append(item)
            else:
                self.get_files_from_specified_folder(drive, item["id"], files)

        return files  # returns the file object type from Google

    def get_folders_from_specified_folder(self, drive, directory_id, files):
        string = f"'{directory_id}' in parents and trashed = false"
        fileList = drive.ListFile({'q': string}).GetList()
        for item in fileList:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                files.append(item)
                self.get_folders_from_specified_folder(drive, item["id"], files)

        return files  # returns the file object type from Google

    # Renames a file in google drive
    def rename_file_in_google_drive(self, old_file_obj, new_file_title):
        old_file_obj['title'] = new_file_title # Change title of the file
        old_file_obj.Upload()  # Update metadata

    # Returns a file object based on search title from list of files
    def get_file_obj(self, list_of_files, search_title):
        for file in list_of_files:
            if file['title'] == search_title:
                return file


if __name__ == '__main__':
    path = "/Users/raveena/Desktop/testing"
    path = os.path.join(path, "CS 307")
    print(path)
    os.makedirs(path, exist_ok=True)