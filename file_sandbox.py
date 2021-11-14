import os
from bs_utilities import BSUtilities

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

    def rename_file(self, oldFileName, newFileName):
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

    def list_files_local(self, directory):
        for root, dirs, files in os.walk(directory):
            for f in files:
                print(os.path.join(root, f))

    def list_files_google_id(self, id):
        return 0

    def list_files_google(self, drive, directory):
        string = f"'{directory}' in parents"
        fileList = drive.ListFile({'q': string}).GetList()
        files = []
        for item in fileList:
            files.append(item["title"])
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                self.list_files_google(drive, item["id"])

        return files


if __name__ == '__main__':
    r = RenameFile()
    #r.list_files_local("/Users/raveena/Desktop/testing")
    id = "1G2Zak1AM5t8v9rX-rXF_zDNjeSrw0ox1"
    bs = BSUtilities()
    drive = bs.init_google_auths()
    files = r.list_files_google(drive, id)
    print(files)
    # newfile = "modified.png"
    # absolute_path = r.find_file("partial.png", "/Users/raveena/testing")
    # if absolute_path is not None:
    #     print(r.rename_file(absolute_path, newfile))
    # else:
    #     print("File not found")
