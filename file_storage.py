# This will house the logic for user story 4 (file storage )
import os
import urllib
# Accessing google api
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
# Accessing the data class made
from File import File, StorageTypes


# Since our project is in "testing" phase, you have to manually add test users until you publish the app
# My personal email is the only test user now, but we can add more
def init_google_auths():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # client_secrets.json need to be in the same directory as the script
    drive = GoogleDrive(gauth)
    return drive


# Create a way for the user to communicate the path of choice for storing files
def ask_for_path():
    # For now will have a simple input taken from console. Will replace with bot commands
    storage_path = input("Please type in your storage path: ")
    print(storage_path)
    return storage_path


# Store path of choice in configuration database
def store_path():
    # This will be changed later with actually storing the path in the database
    print("completed..")


# if path not determined by user yet, prompt them to fill one (or just do default downloads path)

# Algorithm to check if path is a valid path
def validate_path_drive(storage_path, drive):
    # checks if inputted path is valid or not for their local machine
    if not os.path.exists(storage_path):
        # check if its a valid google drive folder in root (update later for nested folders)
        folderList = get_all_files_in_google(drive)
        for folder in folderList:
            if folder.fileTitle == storage_path:
                return True
        else:
            return False
    return True


def validate_path_local(storage_path):
    # checks if inputted path is valid or not for their local machine
    if not os.path.exists(storage_path):
        return False
    return True


def upload_to_google_drive(drive, storage_path, file):
    file_to_upload = file
    # finding the folder to upload to
    folders = get_all_files_in_google(drive)
    folder_id = -1
    for folder in folders:
        if folder.fileTitle == storage_path:
            folder_id = folder.filePath
            break
    print(folder_id)
    if folder_id == -1:
        # upload it to the root (My Drive)
        gd_file = drive.CreateFile({'title': file})
    else:
        # currently takes the folder id from browser of url for the folder they want to upload something in
        gd_file = drive.CreateFile({'parents': [{'id': folder_id}]})

    # Read file and set it as the content of this instance.
    gd_file.SetContentFile(file)
    # Upload the file
    gd_file.Upload()
    # handles memory leaks
    gd_file = None


def get_all_files_in_google(drive):
    # only querying files (everything) from the 'MyDrive' root
    fileList = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    # Use this to save all the folders in 'MyDrive'
    folderList = []
    for file in fileList:
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            myFile = File(file['title'], file['id'])
            myFile.storageType = StorageTypes.GOOGLE_DRIVE
            folderList.append(myFile)

    return folderList


# This will be replaced by the actual url
def upload_file_to_local_path(localPath, fileRUL, filename):
    fullfilename = os.path.join(localPath, filename)
    urllib.urlretrieve(fileRUL, fullfilename)


# Prompt options for storage locations when prompting users to specify a location


# Main function
if __name__ == '__main__':
    # Example of what the typical flow would look like when interacting with Bot
    storage_path = ask_for_path()
    drive = init_google_auths()
    return_val = validate_path_drive(storage_path, drive)
    print(return_val)  # for debugging
    # for debugging, just using this default file
    file = "docs/Project Backlog - Team 14 (BrightspaceBot).pdf"

    upload_to_google_drive(drive, storage_path, file)
