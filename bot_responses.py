import discord

from database.db_utilities import DBUtilities
from rename_file import RenameFile
from bs_utilities import BSUtilities
from bs_calendar import Calendar
import datetime
import re
from file_storage import *
import asyncio
from file_storage import validate_path_local
from file_storage import move_past_assignments_to_archive

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
        self.db_username = None

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

    def set_db_username(self, db_username):
        self.db_username = db_username

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

    '''
        Check method for waiting client's reply back
        
        Used for client.wait_for('message', check=check, timeout=##)
    '''

    # def check(self, msg):
    #    return msg.author == self.message.author

    def current_storage(self, username):
        sql = f'SELECT STORAGE_PATH from PREFERENCES WHERE USERNAME = \'{username}\';'
        storage_path = self.DB_UTILS._mysql.general_command(sql)
        if storage_path[0][0] is None:
            return self.message.channel.send('No storage path specified. Type update storage to save something')
        else:
            return self.message.channel.send(f'Current location: {storage_path[0][0]}')

    """
        HELPER FUNCTION
        Returns: Whether the text channel has already been created in their server 
    """

    def check_if_tc_exists(self, request_tc, username):
        sql_command = f"SELECT LIST_OF_TCS FROM PREFERENCES WHERE USERNAME = '{username}';"
        list_of_tcs = self.DB_UTILS._mysql.general_command(sql_command)[0][0]
        if list_of_tcs is None:
            sql_command = f"UPDATE PREFERENCES SET LIST_OF_TCS = 'general' WHERE USERNAME = '{username}';"
            self.DB_UTILS._mysql.general_command(sql_command)  # execute command
            sql_command = f"SELECT LIST_OF_TCS FROM PREFERENCES WHERE USERNAME = '{username}';"
            list_of_tcs = self.DB_UTILS._mysql.general_command(sql_command)[0][0]

        array = list_of_tcs.split(",")
        # True = exists, False = doesn't exist
        for a in array:
            if a == request_tc:
                # Then this text channel already exists
                return True
        return False

    """
        HELPER FUNCTION
        Returns: A list of files the user has downloaded in their preferred location
    """

    def get_downloaded_files(self, username, bsu, dbu):
        # get what type of storage they have
        sql_command = f"SELECT STORAGE_LOCATION FROM PREFERENCES WHERE USERNAME = '{username}';"
        storage_location = dbu._mysql.general_command(sql_command)[0][0]
        if storage_location is None:
            return "No storage type specified in configurations. Please do that first.", False
        else:
            # get their list of files based on their storage location
            sql_command = f"SELECT STORAGE_PATH FROM PREFERENCES WHERE USERNAME = '{username}';"
            storage_path = dbu._mysql.general_command(sql_command)[0][0]

            if storage_location == 'Local Machine':
                arr = self.RN_FILE.list_files_local(storage_path)
            else:
                bsu.init_google_auths()
                folder_name, folder_id = self.RN_FILE.get_folder_id(bsu.drive, storage_path)
                file_list = self.RN_FILE.get_files_from_specified_folder(bsu.drive, folder_id, [])
                arr = []
                for f in file_list:
                    arr.append(f['title'])
            if len(arr) == 0:
                return "No files downloaded that you can rename.", False

            # Crafting response message
            response = "List of files downloaded so far: \n"
            count = 1
            for a in arr:
                response = response + str(count) + ". " + a + "\n"
                count = count + 1
            response = response + "Please type <Number> -> <New file name> for the new name you want " \
                                  "to change the files to.\nEX: 1 -> modified.png"
            return response, True

    """
        HELPER FUNCTION
        Processes the renaming response ' ## -> "new title" ' 
    """
    def process_renaming_response(self, username, user_response, bsu):
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
            folder_name, folder_id = self.RN_FILE.get_folder_id(bsu.drive, storage_path)
            file_list = self.RN_FILE.get_files_from_specified_folder(bsu.drive, folder_id, [])
            count = 0
            for num in file_nums:
                # search for the file object
                num = num.strip()
                searched_obj = self.RN_FILE.get_file_obj(file_list, file_list[int(num) - 1]['title'])
                self.RN_FILE.rename_file_in_google_drive(searched_obj, new_titles[count].strip())
                count = count + 1

        return "Rename process successful!"

    """
        Command: "download:<course(s)>"
        Returns: A status message after the bot attempts to download files to their preferred location
    """
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
        return "Files downloaded successfully!"

    """
        HELPER FUNCTION
        Sees if user has set up re-directions to text channels to send message to
    """
    async def send_notification_to_channel(self, message, type_of_notification, message_to_send, username, client):
        # Find if they have a text channel specified for the type of notification
        sql_command = f"SELECT {type_of_notification} FROM PREFERENCES WHERE USERNAME = '{username}';"
        result = self.DB_UTILS._mysql.general_command(sql_command)[0][0]
        # Searching for the channel ID
        if result is not None:
            channel_id = 0
            for channel in message.guild.text_channels:
                result = result.replace(" ", "-")
                if channel.name == result:
                    channel_id = channel.id
                    break
            if channel_id != 0:
                # Send to specified channel from database
                send_message_to_channel = client.get_channel(channel_id)
                await send_message_to_channel.send(message_to_send)
            else:
                # Some mistake came and could not find channel ID, so just go to default chat
                await message.channel.send(message_to_send)
        else:
            # No channel specified in database, so go to normal channel
            await message.channel.send(message_to_send)
        return

    """
        Command: "overall points:<course(s)>"
        Returns: the num/den representation of their grade
    """
    def overall_points(self, message):
        courses = message.content.split(":")[1].split(",")
        IDs = []
        for c in courses:
            course_id = self.BS_UTILS.find_course_id(c)
            IDs.append(course_id)  # getting the list of course IDs

        grades = {}
        tosort = {}
        counter = 0
        for i in IDs:
            if i == -1:
                grades[courses[counter]] = 'Course not recognized'
                tosort[courses[counter]] = 0
            else:
                yourTotal, classTotal = self.BS_UTILS.sum_total_points(i)
                if classTotal == 0:
                    grades[courses[counter]] = "No grades are uploaded for this class."
                    tosort[courses[counter]] = 100
                else:
                    percentage = (yourTotal / classTotal) * 100
                    grades[courses[counter]] = '{num:.2f}/{den:.2f}'.format(num=yourTotal, den=classTotal)
                    tosort[courses[counter]] = percentage
            counter = counter + 1

        sorted_list = dict(sorted(tosort.items(), key=lambda item: item[1]))
        final_string = "Your overall grades are: \n"
        for key, value in sorted_list.items():
            final_string = final_string + key + ": " + str(grades[key]) + "\n"

        return final_string

    """
        Command: "grades:<course(s)>"
        Returns: the letter grade student has in that course
    """
    def get_letter_grade(self, message):
        courses = message.content.split(":")[1].split(",")
        IDs = []
        for c in courses:
            course_id = self.BS_UTILS.find_course_id(c)
            IDs.append(course_id)
        print(IDs)

        grades = {}
        counter = 0
        for i in IDs:
            if i == -1:
                grades[courses[counter]] = 'Not found'
            else:
                fraction_string, percentage = self.BS_UTILS._bsapi.get_grade(i)
                print(fraction_string)
                print(percentage)
                if len(fraction_string) <= 1:
                    yourTotal, classTotal = self.BS_UTILS.sum_total_points(i)
                    if classTotal == 0:
                        grades[courses[counter]] = 'Not found'
                    else:
                        percentage = (yourTotal / classTotal) * 100
                        letter = self.BS_UTILS.get_letter_grade(percentage)
                        grades[courses[counter]] = letter
                else:
                    letter = self.BS_UTILS.get_letter_grade(percentage)
                    grades[courses[counter]] = letter
            counter = counter + 1

        # print(grades)
        grades = dict(sorted(grades.items(), key=lambda item: item[1]))
        # print(grades)
        final_string = "Your grades are: \n"
        for key, value in grades.items():
            final_string = final_string + key.upper() + ": " + value + "\n"

        return final_string

    """
        Command: "redirect notifications"
        Sends a status message if the redirection process was successful or not
    """
    async def redirect_notifications(self, message, client, username):
        await message.channel.send("Here are the notification types you can redirect - Grades, Files, Deadlines.\n"
                                   "Format the response as <Notification Type> - <Text Channel Name>.\n"
                                   "EX: Grades - Grades Notifications")

        # check what type of path they want
        def storage_path(m):
            return m.author == message.author

        # getting the type of redirecting of notification
        try:
            response = await client.wait_for('message', check=storage_path, timeout=30)
        except asyncio.TimeoutError:
            await message.channel.send("taking too long...")
            return

        # split the notification type and desired text channel
        response_array = response.content.split("-")
        category = response_array[0]
        category = category.strip()
        text_channel = response_array[1]
        text_channel = text_channel.strip()
        # Get the database category
        db_category = ""
        if category.lower() == "grades":
            db_category = "GRADES_TC"
        elif category.lower() == 'files':
            db_category = "FILES_TC"
        elif category.lower() == 'deadlines':
            db_category = "DEADLINES_TC"
        else:
            await message.channel.send("Sorry, the notification type you specified is not valid. Please try the "
                                       "process again")
            return

        # TODO get the username from a different way
        sql_command = f"SELECT {db_category} FROM PREFERENCES WHERE USERNAME = '{username}';"
        current_saved_tc = self.DB_UTILS._mysql.general_command(sql_command)[0][0]
        # Check if the channel that is being requested has already been created
        sql_command = f"SELECT LIST_OF_TCS FROM PREFERENCES WHERE USERNAME = '{username}';"
        list_of_tcs = self.DB_UTILS._mysql.general_command(sql_command)[0][0]
        if list_of_tcs is None:
            sql_command = f"UPDATE PREFERENCES SET LIST_OF_TCS = 'general' WHERE USERNAME = '{username}';"
            self.DB_UTILS._mysql.general_command(sql_command)
            sql_command = f"SELECT LIST_OF_TCS FROM PREFERENCES WHERE USERNAME = '{username}';"
            list_of_tcs = self.DB_UTILS._mysql.general_command(sql_command)[0][0]

        array = list_of_tcs.split(",")
        found = False
        for a in array:
            if a == text_channel:
                # Then this text channel already exists
                found = True
        # found, list_of_tcs = BOT_RESPONSES.check_if_tc_exists(current_saved_tc, DB_USERNAME)

        sql_command = f"UPDATE PREFERENCES SET {db_category} = '{text_channel}' WHERE USERNAME = '{username}';"
        self.DB_UTILS._mysql.general_command(sql_command)

        if not found:
            list_of_tcs = list_of_tcs + "," + text_channel
            sql_command = f"UPDATE PREFERENCES SET LIST_OF_TCS = '{list_of_tcs}' WHERE USERNAME = '{username}';"
            self.DB_UTILS._mysql.general_command(sql_command)
            name = 'Text Channels'  # This will go under the default category
            cat = discord.utils.get(message.guild.categories, name=name)
            await message.guild.create_text_channel(text_channel, category=cat)

            channel_id = 0
            for channel in message.guild.text_channels:
                channel_id = channel.id

            await message.channel.send("You successfully moved " + category + " notifications from "
                                       + str(
                current_saved_tc) + " to " + text_channel + ". I will send a message to this "
                                                            "channel to start the thread.")

            send_message_to_channel = client.get_channel(channel_id)
            await send_message_to_channel.send("Hello! This thread will hold notifications about " + category)
            return
        else:
            await message.channel.send("Since this channel already exists, a new channel will not be created. \nYou "
                                       "successfully moved " + category + " notifications from "
                                       + str(current_saved_tc) + " to " + text_channel + ".")
            return

    """
        Command: "where are my notifications?"
        Returns: where the redirections are pointing to currently
    """
    def where_are_my_notifications(self, username):
        sql = f"SELECT GRADES_TC FROM PREFERENCES WHERE USERNAME = '{username}';"
        grades = self.DB_UTILS._mysql.general_command(sql)[0][0]
        if grades is None:
            grades = "Not specified"
        sql = f"SELECT FILES_TC FROM PREFERENCES WHERE USERNAME = '{username}';"
        files = self.DB_UTILS._mysql.general_command(sql)[0][0]
        if files is None:
            files = "Not specified"
        sql = f"SELECT DEADLINES_TC FROM PREFERENCES WHERE USERNAME = '{username}';"
        deadlines = self.DB_UTILS._mysql.general_command(sql)[0][0]
        if deadlines is None:
            deadlines = "Not specified"
        final_string = f"Your notification redirections are saved as the following:\n" \
                       f"GRADES -> {grades}\n" \
                       f"DEADLINES -> {deadlines}\n" \
                       f"FILES -> {files}"
        return final_string

    """
        Command: "update storage"
        Returns: A status message after the bot attempts to update the storage location destination
    """
    async def update_storage(self, message, client, username):
        await message.channel.send("Google Drive or Local Machine?")

        # check what type of path they want
        def storage_path(m):
            return m.author == message.author

        # getting the type of storage location
        try:
            path_type = await client.wait_for('message', check=storage_path, timeout=30)
        except asyncio.TimeoutError:
            await message.channel.send("taking too long...")
            return

        # checking what type of path they are going to save it in
        if path_type.content == "google drive":
            await message.channel.send("What folder from root?")
            # checking to see if path is valid
            try:
                new_storage = await client.wait_for('message', check=storage_path, timeout=30)
                self.set_google_drive()
                return_val = self.BS_UTILS.validate_path_drive(new_storage.content, self.google_drive)
                if not return_val:
                    await message.channel.send("Not a valid path. Try the cycle again.")
                else:
                    # todo add saving mechanism to cloud database

                    sql_type = "UPDATE PREFERENCES SET STORAGE_LOCATION = '{path_type}' WHERE USERNAME = '{f_name}';" \
                        .format(path_type="Google Drive", f_name=username)

                    self.DB_UTILS._mysql.general_command(sql_type)
                    sql_path = "UPDATE PREFERENCES SET STORAGE_PATH = '{path}' WHERE USERNAME = '{f_name}';" \
                        .format(path=new_storage.content, f_name=username)
                    self.DB_UTILS._mysql.general_command(sql_path)

                    await message.channel.send("New path saved")
                return
            except asyncio.TimeoutError:
                await message.channel.send("taking too long...")

        # if the path is local
        elif path_type.content == "local":
            await message.channel.send("Send your local path")
            # checking to see if path is valid (local)
            try:
                new_storage = await client.wait_for('message', check=storage_path, timeout=30)
                return_val = validate_path_local(new_storage.content)
                if not return_val:
                    await message.channel.send("Not a valid path. Try the cycle again.")
                else:
                    # todo add saving mechanism to cloud database

                    sql_type = "UPDATE PREFERENCES SET STORAGE_LOCATION = '{path_type}' WHERE USERNAME = '{f_name}';" \
                        .format(path_type="Local Machine", f_name=username)

                    self.DB_UTILS._mysql.general_command(sql_type)
                    sql_path = "UPDATE PREFERENCES SET STORAGE_PATH = '{path}' WHERE USERNAME = '{f_name}';" \
                        .format(path=new_storage.content, f_name=username)
                    self.DB_UTILS._mysql.general_command(sql_path)
                    await message.channel.send("New path saved")
                return
            except asyncio.TimeoutError:
                await message.channel.send("taking too long...")

        else:
            await message.channel.send("Your input isn't valid")

    def see_if_section_updated(self, courseID, bsu):
        # get current date and time
        todays_date = datetime.datetime.utcnow()
        due_dates = bsu.get_last_mod_from_sections(courseID)
        updated = []
        for section in due_dates:
            module = ""
            topic = ""
            file = ""
            arr = []
            for item in section:

                if item.startswith("MODULE"):
                    module = item
                elif item.startswith("TOPIC:"):
                    topic = item
                elif item.startswith("FILE:"):
                    file = item
                else:
                    date = datetime.fromisoformat(item[:-1])
                    diff = date - todays_date
                    if diff.days == 0:
                        # then it was updated today
                        arr.append(module)
                        arr.append(topic)
                        arr.append(file)
            updated.append(arr)

        new_list = list(filter(None, updated))

        string = ""
        if len(new_list) > 0:
            for subarray in new_list:
                for item in subarray:
                    if len(item) > 0:
                        if item.startswith("MODULE"):
                            string = string + "\n"
                        string = string + item + " "
        return string


    def get_update_section_all(self, bsu):
        classes = bsu.get_classes_enrolled()
        string = ""
        for courseName, courseID in classes.items():
            sub_string = self.see_if_section_updated(courseID, bsu)
            if len(sub_string) > 0:
                string = "Updates for " + courseName + "\n"
                string = string + sub_string + "\n"
        return string



    @staticmethod
    def format_days_of_week(user_input):
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


    def week_to_num(self, user_input):
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
        day_num = ''
        for day in days:
            day_num = day_num + "," + str(DAY_MAP_NUM[day])
        return day_num[1:]

    def format_classes(self, classes, bsu):
        classes = re.split('[^a-zA-Z0-9]+', classes)
        result = ''
        for c in classes:
            course_id = bsu.find_course_ID(c)
            result = result + "," + str(course_id)
        return result[1:]

    def add_office_hours_to_calendar(self, course_name, instr_name, days, st_time, end_time):
        self.DB_UTILS._mysql.create_table('OFFICE_HOURS', 'username VARCHAR(50), '
                                                          'recurring_event_id VARCHAR(255), '
                                                          'event_title VARCHAR(255), '
                                                          'PRIMARY KEY (username, recurring_event_id)')
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

        sql_command = f"SELECT recurring_event_id, event_title from OFFICE_HOURS;"
        event_titles = self.DB_UTILS._mysql.general_command(sql_command)
        for et in event_titles:
            if et[1] == event_title:
                cal.delete_event(et[0])
        # print(event_titles)

        recurring_event_id = cal.insert_event_recurring(event_title, description, start, end, days)
        print(recurring_event_id)
        self.DB_UTILS._mysql.general_command(f"INSERT INTO OFFICE_HOURS (username, recurring_event_id, event_title) "
                                             f"VALUES(\'{self.db_username}\', \'{recurring_event_id}\', \'{event_title}\') "
                                             f"ON DUPLICATE KEY UPDATE event_title=\'{event_title}\'")

        # cal.insert_event_recurring creates an event for today. Check if today is a day of week listed in days
        if DAY_MAP[weekday] not in days:
            first_event_id = cal.get_recurring_event(recurring_event_id)['id']
            cal.delete_event(first_event_id)
        return "Office hours successfully added to calendar!"

    def add_discussion_schedule_to_db(self, username, days, classes, bsu, dbu):
        day_num = self.week_to_num(days)
        formatted_classes = self.format_classes(classes, bsu)
        dbu.add_discussion_schedule(username, day_num, formatted_classes)

    def discussion_remind_to_post(self, username, bsu, dbu):
        reply = '-1'
        days = dbu.get_days_in_discussion_schedule(username)
        full_name = dbu.get_full_name(username)
        classes = dbu.get_classes_in_discussion_schedule(username)
        if str(datetime.datetime.today().weekday()) in days:
            reply = ''
            for course_id in classes:
                forum_ids_names = bsu.get_all_forum_ids_names(course_id)
                for forum_id_name in forum_ids_names:
                    topic_ids_names = bsu.get_all_topic_ids_names(course_id, forum_id_name['id'])
                    for topic_id_name in topic_ids_names:
                        students = bsu.get_students_who_posted(course_id, forum_id_name['id'],
                                                                         topic_id_name['id'])
                        # student hasn't replied to another student or hasn't posted
                        due_date = '-1'
                        if topic_id_name['due_date'] is not None:
                            due_date = datetime.datetime.fromisoformat(topic_id_name['due_date'][:-1])
                            due_date = (due_date - datetime.datetime.utcnow()).days
                        #
                        # # for testing
                        # if topic_id_name['name'] == 'Syllabus, Course Structure, or Other General Course Questions':
                        #     due_date = datetime.datetime.now() + datetime.timedelta(days=-1)
                        #     due_date = (due_date - datetime.datetime.utcnow()).days

                        if students.count(full_name) < 2 and (due_date == '-1' or due_date >= 0):
                            reply = reply + \
                                    f"course:{course_id}->{forum_id_name['name']}->{topic_id_name['name']}\n"
        return reply

    def archive_past_assignments(self, bs_api):
        reply = '-1'
        drive = init_google_auths()
        move_past_assignments_to_archive(drive, bs_api)
        reply = 'success'
        return reply

    def updated_section(self, bsu):
        reply = bsu.get_updated_sections(self.db_username)
        return reply