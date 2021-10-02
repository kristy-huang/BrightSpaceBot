# This will house the logic for user story 4 (file storage )
import os
# Accessing google api
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from File import File


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
def validate_path(storage_path):
    # checks if inputted path is valid or not for their local machine
    if not os.path.exists(storage_path):
        return False
    return True


def upload_to_google_drive(drive):
    file = "/Users/raveena/Desktop/BrightSpaceBot/docs/Project Backlog - Team 14 (BrightspaceBot).pdf"
    # currently takes the folder id from browser of url for the folder they want to upload something in
    gd_file = drive.CreateFile({'parents': [{'id': '1FHtEwx0GlOzZokqsYfLY4mI85WS9S0i-'}]})
    # Read file and set it as the content of this instance.
    gd_file.SetContentFile(file)
    # Upload the file
    gd_file.Upload()


def get_all_files_in_google(drive):
    # only querying files (everything) from the 'MyDrive' root
    fileList = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    # Use this to save all the folders in 'MyDrive'
    folderList = []
    for file in fileList:
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            myFile = File(file['title'], file['id'])
            check_path = validate_path(myFile.filePath)
            if check_path:
                myFile.storageType = 0
            else:
                myFile.storageType = 1  # in this method it will always be here but I will make this logic better soon
            folderList.append(myFile)

    return folderList


# Prompt options for storage locations when prompting users to specify a location


# Main function
if __name__ == '__main__':
    # storage_path = ask_for_path()
    # validate_path(storage_path)
    # upload_to_google_drive(drive)

    drive = init_google_auths()
    folders = get_all_files_in_google(drive)
    for f in folders:
        print(f.get_info())
