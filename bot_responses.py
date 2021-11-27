import discord
from database.db_utilities import DBUtilities
from rename_file import RenameFile
from bs_utilities import BSUtilities
from bs_calendar import Calendar
import datetime

DAY_MAP = {
    0: "MO",
    1: "TU",
    2: "WE",
    3: "TH",
    4: "FR",
    5: "SA",
    6: "SU"
}

DAY_MAP_NUM = {
    "MO": 0,
    "TU": 1,
    "WE": 2,
    "TH": 3,
    "FR": 4,
    "SA": 5,
    "SU": 6
}

# This will be a helper class to organize all the responses that the bot will need to provide back to discord
class BotResponses:
    """
    Creating constructor for BotResponse object
    """

    def __init__(self):
        self.message = None
        self.username = None
        self.channel = None
        self.DB_UTILS = DBUtilities('database/db_config.py')
        self.BS_UTILS = None
        self.RN_FILE = RenameFile()
        self.google_drive = None

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

    def set_BS_param(self, BS):
        self.BS_UTILS = BS

    # TODO instead of just checking if its None, check if it needs to be refreshed
    def set_google_drive(self):
        if self.google_drive is None:
            self.google_drive = self.BS_UTILS.init_google_auths()

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
                arr = self.RN_FILE.list_files_local(storage_path)
            else:
                self.set_google_drive()
                folder_name, folder_id = self.RN_FILE.get_folder_id(self.google_drive, storage_path)
                file_list = self.RN_FILE.get_files_from_specified_folder(self.google_drive, folder_id, [])
                arr = []
                for f in file_list:
                    arr.append(f['title'])

            # Crafting response message
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
                self.RN_FILE.rename_file_local(old_path, new_titles[count].strip())
                count = count + 1
        else:
            folder_name, folder_id = self.RN_FILE.get_folder_id(self.google_drive, storage_path)
            file_list = self.RN_FILE.get_files_from_specified_folder(self.google_drive, folder_id, [])
            count = 0
            for num in file_nums:
                # search for the file object
                num = num.strip()
                searched_obj = self.RN_FILE.get_file_obj(file_list, file_list[int(num) - 1]['title'])
                self.RN_FILE.rename_file_in_google_drive(searched_obj, new_titles[count].strip())
                count = count + 1

        return "Rename process successful!"

    def download_files(self, user_response, username):
        # save what courses they want to download files for
        courses = user_response.split(":")[1]
        # see their storage path and location
        sql_command = f"SELECT STORAGE_PATH from PREFERENCES WHERE USERNAME = '{username}';"
        storage_path = self.DB_UTILS._mysql.general_command(sql_command)[0][0]
        sql_command = f"SELECT STORAGE_LOCATION from PREFERENCES WHERE USERNAME = '{username}';"
        storage_location = self.DB_UTILS._mysql.general_command(sql_command)[0][0]
        full_course_name, course_id = self.BS_UTILS.find_course_id_and_fullname(courses)
        if full_course_name is None or course_id is None:
            return "The course specified cannot be found. Please type the name again with more clarity."
        if storage_location != "Local Machine":
            self.set_google_drive()  # setting up the google drive variable
        self.BS_UTILS.download_files(course_id, storage_path, storage_location, self.google_drive, full_course_name)

    def format_days_of_week(self, user_input):
        days = []
        if 'm' in user_input:
            days.append('MO')
        if 'tu' in user_input:
            days.append("TU")
        if 'w' in user_input:
            days.append("WE")
        if 'th' in user_input:
            days.append('TH')
        if 'f' in user_input:
            days.append('FR')
        if 'sa' in user_input:
            days.append('SA')
        if 'su' in user_input:
            days.append('SU')
        result = ''
        for day in days:
            result = result + "," + day
        return result[1:]

    def add_office_hours_to_calendar(self, course_name, instr_name, days, st_time, end_time):
        cal = Calendar()
        event_title = f"OFFICE HOURS: for {course_name}, {instr_name}"
        description = f"Don't forget to attend {instr_name}'s office hours!"

        start = datetime.datetime.utcnow()
        weekday = start.weekday()
        st_hour = int(st_time.partition(":")[0])
        st_min = int(st_time.partition(":")[2])
        start = start.replace(hour=st_hour, minute=st_min)
        start = start.isoformat()

        end = datetime.datetime.utcnow()
        end_hour = int(end_time.partition(":")[0])
        end_min = int(end_time.partition(":")[2])
        end = end.replace(hour=end_hour, minute=end_min)
        end = end.isoformat()

        recurring_event_id = cal.insert_event_recurring(event_title, description, start, end, days)

        # cal.insert_event_recurring creates an event for today. Check if today is a day of week listed in days
        if DAY_MAP[weekday] not in days:
            first_event_id = cal.get_recurring_event(recurring_event_id)['id']
            cal.delete_event(first_event_id)
        return "Office hours successfully added to calendar!"

    def add_discussion_schedule_to_db(self, days):
        formatted_days = self.format_days_of_week(days)
        self.DB_UTILS.add_discussion_schedule(formatted_days)
        return



