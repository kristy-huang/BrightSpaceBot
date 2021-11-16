import discord
from database.db_utilities import DBUtilities
from rename_file import RenameFile
from bs_utilities import BSUtilities

# This will be a helper class to organize all the responses that the bot will need to provide back to discord
class BotResponses:
    """
    Creating constructor for BotResponse object
    """

    def __init__(self):
        self.message = None
        self.username = None
        self.channel = None
        self.DB_UTILS = None

    """
    Setting the message parameter that the discord method passes in for future use
    """

    def set_message_param(self, message):
        self.message = message

    def set_username_param(self, username):
        self.username = username

    def set_channel_param(self, channel):
        self.channel = channel

    def set_DB_param(self, DB):
        self.DB_UTILS = DB

    """
    DEBUGGING Helps see what the discord messages are 
    """

    def print_server_messages(self):
        print(f'{self.username}: {self.message.content} ({self.channel}) ({self.message.channel.id})')

    """
    DEBUGGING Function to test if our bot is working
    """

    def test_hello(self):
        # put your custom message here for the bot to output
        # we would incorporate our chat module here and then craft an appropriate response
        return self.message.channel.send(f'Hello {self.username}!')

    """
    Command: "current storage location"
    Returns: Either the storage path saved in Database or error message saying no storage path saved
    """

    def current_storage(self, username):
        sql = f'SELECT STORAGE_PATH from PREFERENCES WHERE USERNAME = \'{username}\';'
        storage_path = self.DB_UTILS._mysql.general_command(sql)
        if storage_path[0][0] is None:
            return self.message.channel.send('No storage path specified. Type update storage to save something')
        else:
            return self.message.channel.send(f'Current location: {storage_path[0][0]}')

    def check_if_tc_exists(self, request_tc, username):
        sql_command = f"SELECT LIST_OF_TCS FROM PREFERENCES WHERE USERNAME = '{username}';"
        list_of_tcs = self.DB_UTILS._mysql.general_command(sql_command)[0][0]
        if list_of_tcs is None:
            sql_command = f"UPDATE PREFERENCES SET LIST_OF_TCS = 'general' WHERE USERNAME = '{username}';"
            self.DB_UTILS._mysql.general_command(sql_command) # execute command
            sql_command = f"SELECT LIST_OF_TCS FROM PREFERENCES WHERE USERNAME = '{username}';"
            list_of_tcs = self.DB_UTILS._mysql.general_command(sql_command)[0][0]

        array = list_of_tcs.split(",")
        # True = exists, False = doesn't exist
        for a in array:
            if a == request_tc:
                # Then this text channel already exists
                return True
        return False

    def get_downloaded_files(self, username):
        rename = RenameFile()
        # get what type of storage they have
        sql_command = f"SELECT STORAGE_LOCATION FROM PREFERENCES WHERE USERNAME = '{username}';"
        storage_location = self.DB_UTILS._mysql.general_command(sql_command)[0][0]
        if storage_location is None:
            return "No storage type specified in configurations. Please do that first."
        else:
            # get their list of files based on their storage location
            sql_command = f"SELECT STORAGE_PATH FROM PREFERENCES WHERE USERNAME = '{username}';"
            storage_path = self.DB_UTILS._mysql.general_command(sql_command)[0][0]
            if storage_location == 'Local Machine':
                arr = rename.list_files_local(storage_path)
            else:
                bs = BSUtilities()
                drive = bs.init_google_auths()
                arr = rename.list_all_files_google(drive, storage_path)
            response = "List of files downloaded so far: \n"
            count = 1
            for a in arr:
                response = response + str(count) + ". " + a + "\n"
                count = count + 1
            response = response + "Please type <Number> -> <New file name> for the new name you want " \
                                  "to change the files to.\nEX: 1 -> modified.png"
            return response

    # process renaming response ' ## -> "new title" '
    def process_renaming_response(self, username, user_response):
        sql_command = f"SELECT STORAGE_PATH FROM PREFERENCES WHERE USERNAME = '{username}';"
        storage_path = self.DB_UTILS._mysql.general_command(sql_command)[0][0]
        sql_command = f"SELECT STORAGE_LOCATION FROM PREFERENCES WHERE USERNAME = '{username}';"
        storage_type = self.DB_UTILS._mysql.general_command(sql_command)[0][0]
        rename = RenameFile()

        arr = user_response.split("->")
        file_nums = arr[0].split(",")  # list of files they want to rename
        new_titles = arr[1].split(",")  # list of new_titles they have to rename to
        temp = []
        for n in new_titles:
            if n not in temp:
                temp.append(n)
            else:
                return "ERROR: Duplicate name in request."

        if storage_type == "Local Machine":
            files = rename.list_files_local(storage_path)
            count = 0
            for num in file_nums:
                num = num.strip()
                old_path = files[int(num) - 1]
                self.rename_file(old_path, new_titles[count].strip(), storage_type)
                count = count + 1
        return "Rename process successful!"


    def rename_file(self, old_file, new_file, storage_type):
        rename = RenameFile()
        if storage_type == "Local Machine":
            rename.rename_file(old_file, new_file)






# Debugging ...
if __name__ == '__main__':
    sql = DBUtilities("database/db_config.py")
    r = BotResponses()
    r.set_DB_param(sql)
    rows = sql._mysql.general_command("SELECT * FROM PREFERENCES")
    for i in rows:
        print(i)
    r.get_downloaded_files("currymaster")
