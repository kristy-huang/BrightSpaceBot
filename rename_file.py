import os
from bs_utilities import BSUtilities
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

    def list_files_local(self, directory):
        flist = []
        for root, dirs, files in os.walk(directory):
            for f in files:
                string = os.path.join(root, f)
                flist.append(string)
        return flist

    # Returns the title and ID of the directory you passed
    def get_folder_id(self, drive, directory):
        fileList = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        # Use this to save all the folders in 'MyDrive'
        folderList = []
        for file in fileList:
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                if file['title'] == directory:
                    return file['title'], file['id']

    def get_files_from_specified_folder(self, drive, directory_id, files):
        string = f"'{directory_id}' in parents and trashed = false"
        fileList = drive.ListFile({'q': string}).GetList()
        subarray = []
        listoffiles = []
        for item in fileList:
            files.append(item)
            if item['mimeType'] != 'application/vnd.google-apps.folder':
                listoffiles.append(item)  # only appending files
            else:
                # subarray.append(item)
                # subarray.append(listoffiles)
                # files.append(subarray)

                self.get_files_from_specified_folder(drive, item["id"], files)

        return files  # returns the file object type from Google

    def rename_file_in_google_drive(self, file_list, old_file_title, new_file_title):
        for file in file_list:
            if file['title'] == old_file_title:
                file['title'] = new_file_title  # Change title of the file
                file.Upload()  # Update metadata
                return

    def get_file_id_gd(self, drive, folder_id, file_name):
        files = self.get_files_from_specified_folder(drive, folder_id)
        for f in files:
            if f.fileTitle == file_name:
                return f.filePath  # the file id


if __name__ == '__main__':
    r = RenameFile()
    f = r.list_files_local("/Users/raveena/Desktop/testing")
    for a in f:
        print(a)
    # id = "1G2Zak1AM5t8v9rX-rXF_zDNjeSrw0ox1"
    # bs = BSUtilities()
    # drive = bs.init_google_auths()
    #
    # f, id = r.list_files_google_id("test")
    # print(f) # searching directory title
    # print(id) # searching directory id
    # files = r.list_all_files_google(drive, id)
    # for f in files:
    #     print(f.fileTitle)  # file name in folder
    #     print(f.filePath)  # file ID in folder
    # file_id = r.get_file_id_gd(drive, id, "Testing document")
    # print(file_id)
    # #r.rename_file_in_gd(drive, file_id, "Modified Text document")
    # request = drive.files().get_media(fileId=file_id)
    # print(request["title"])
    # print(request["id"])

    # print(files)
    # newfile = "modified.png"
    # absolute_path = r.find_file("partial.png", "/Users/raveena/testing")
    # if absolute_path is not None:
    #     print(r.rename_file(absolute_path, newfile))
    # else:
    #     print("File not found")