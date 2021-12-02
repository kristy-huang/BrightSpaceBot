# Our discord token is saved in another file for security
from hashlib import new
from os import execv
from discord.errors import NotFound
from discord_config import config, USERNAME, PIN
import discord
from discord.ext import tasks, commands
import asyncio
from file_storage import *
import datetime
from bs_api import BSAPI
import time
from bs_utilities import BSUtilities
from database.db_utilities import DBUtilities
from bot_responses import BotResponses
from bs_calendar import Calendar
from Authentication import setup_automation
from werkzeug.security import generate_password_hash
from database.mysql_database import MySQLDatabase

'''
To add the bot to your own server and test it out, copy this URL into your browser
https://discord.com/api/oauth2/authorize?client_id=894695859567083520&permissions=534992387152&scope=bot
 '''

# This will be our discord client. From here we will get our input
client = discord.Client()

channelID = 663863991218733058  # mine!
# TODO save this in the database - right now this is my (Raveena's) channel)
BS_API = BSAPI()

SCHEDULED_HOURS = []
DB_USERNAME = 'currymaster'

db_config = "./database/db_config.py"
BS_UTILS = BSUtilities()
DB_UTILS = DBUtilities(db_config)
BOT_RESPONSES = BotResponses()
BOT_RESPONSES.set_DB_param(DB_UTILS)
BOT_RESPONSES.set_BS_param(BS_UTILS)

author_id_to_username_map = {}
NOT_FREQ_MAP = {
    0: "EVERY MONDAY",
    1: "EVERY TUESDAY",
    2: "EVERY WEDNSDAY",
    3: "EVERY THURSDAY",
    4: "EVERY FRIDAY",
    5: "EVERY SATURDAY",
    6: "EVERY SUNDAY",
    7: "EVERYDAY"
}


# Having the bot log in and be online
@client.event
async def on_ready():
    pass


@commands.command()
async def quit(ctx):
    await ctx.send("Shutting down the bot")
    return await client.logout()  # this just shuts down the bot.


# looping every day
# change parameter to minutes=1 and see it happen every minute
@tasks.loop(minutes=1)
async def notification_loop():
    if not BS_UTILS.check_connection():
        return

    #  Syncing the calendar daily (so it can get the correct changes)
    # classes = BS_UTILS.get_classes_enrolled()
    # # classes = {"EAPS": "336112"}
    # for courseName, courseID in classes.items():
    #     assignment_list = BS_UTILS._bsapi.get_upcoming_assignments(courseID)
    #     due = BS_UTILS.process_upcoming_dates(assignment_list)
    #     if len(due) != 0:
    #         # actually dates that are upcoming
    #         cal = Calendar()
    #         # loop through all the upcoming assignments
    #         for assignment in due:
    #             # Check if the event exists first by searching by name
    #             event_title = f"ASSIGNMENT DUE: {assignment[0]} ({courseID})"
    #             description = f"{assignment[0]} for {courseName} is due. Don't forget to submit it!"
    #             search_result, end_time = cal.get_event_from_name(event_title)
    #             date = datetime.datetime.fromisoformat(assignment[1][:-1])
    #             end = date.isoformat()
    #             start = (date - datetime.timedelta(hours=1)).isoformat()
    #             print("End date from search: " + str(end_time))
    #             if search_result != -1:
    #                 # it has already been added to the calendar
    #                 # see if the end times are different
    #                 if end_time != end:
    #                     # the due date has been updated, so delete the old event
    #                     cal.delete_event(search_result)
    #                     cal.insert_event(event_title, description, start, end)
    #             else:
    #                 # has not been added to calendar, so add normally
    #                 # inserting event
    #                 cal.insert_event(event_title, description, start, end)
    #
    # print("inserting into calendar is finished...")
    #
    # # Syncing quizzes to the calendar daily (so it can get the correct changes)
    # quizzes = BS_UTILS.get_all_upcoming_quizzes()
    # for quiz in quizzes:
    #     cal = Calendar()
    #     event_title = f"QUIZ DUE: {quiz['quiz_name']} ({quiz['course_id']})"
    #     description = f"{quiz['quiz_name']} for {quiz['course_name']} is due. Don't forget to submit it!"
    #     date = datetime.datetime.fromisoformat(quiz['due_date'][:-1])
    #     end = date.isoformat()
    #     start = (date - datetime.timedelta(hours=1)).isoformat()
    #     event_id, end_time = cal.get_event_from_name(event_title)
    #     # event has already been created in google calendar
    #     if event_id == -1:
    #         # insert new event to calendar
    #         cal.insert_event(event_title, description, start, end)
    #     # event has not been created
    #     else:
    #         # if end time has changed, update the event
    #         if end_time != end:
    #             cal.delete_event(event_id)
    #             cal.insert_event(event_title, description, start, end)
    #
    # print("inserting into calendar is finished...")

    # print("called_once_a_day:")
    # async def send_notifications():
    # print(datetime.datetime.now().hour)
    message_channel = client.get_channel(channelID)
    dates = BS_UTILS.get_dict_of_discussion_dates()
    # dates = DATES
    string = BS_UTILS.find_upcoming_disc_dates(1, dates)
    string += BS_UTILS.get_notifications_past_24h()

    # Check if the user has a designated text channel for deadline notifications to be sent
    # print("str: ", string)

    # Check if the database has a value for the deadlines text channel

    channel_id = channelID
    print("hello...")
    sql_command = f"SELECT DEADLINES_TC FROM PREFERENCES WHERE USERNAME = '{DB_USERNAME}';"
    sql_result = DB_UTILS._mysql.general_command(sql_command)[0][0]
    if sql_result is not None:
        for c in client.get_all_channels():
            sql_result = sql_result.replace(" ", "-")
            if c.name == sql_result:
                channel_id = c.id
                break

        if len(string) == 0:
            ## only for debugging ##
            string = "No posts today"

    response = BOT_RESPONSES.discussion_remind_to_post(BOT_RESPONSES.db_username)
    string += "Reminder to reply to the following discussions: "
    if response != '-1':
        string += response

    # print("called_once_a_day:")
    async def send_notifications(string, channel_id, types):
        message_channel = client.get_channel(channel_id)
        print(channel_id, message_channel)

        if types[0] == "1":
            dates = BS_UTILS.get_dict_of_discussion_dates()
            # dates = DATES
            string += BS_UTILS.find_upcoming_disc_dates(1, dates)
        if types[1] == "1":
            string += BS_UTILS.get_notifications_past_24h()
        if types[2] == "1":
            string += BS_UTILS.get_events_by_type_past_24h(1)  # Reminder
        if types[3] == "1":
            string += BS_UTILS.get_events_by_type_past_24h(6)  # DueDate

        # replace course id's with course names:

        courses = BS_UTILS.get_classes_enrolled()
        for course in courses.keys():
            curr_course_id = courses[course]
            curr_course_id = str(curr_course_id)
            if curr_course_id in string:
                string = string.replace(curr_course_id, course)

        # print("str: ", string)

        if len(string) == 0:
            ## only for debugging ##
            string = "No posts today"
        # send the upcoming discussion due dates

        await message_channel.send(string[:2000])
        return

    '''if not BS_UTILS.check_connection():
        message_channel = client.get_channel(channel_id)
        await message_channel.send("Connection to BS lost. Attempting to reconnect to BS...")
        BS_UTILS.set_session_auto(DB_UTILS, author_id_to_username_map[message.author.id])
    '''

    now = datetime.datetime.now()
    time_string = now.strftime("%H:%M")
    weekday = now.weekday()

    schedules = DB_UTILS.get_notifictaion_schedule_by_time(time_string, weekday)

    for schedule in schedules:

        types = schedule[2]
        if not types:
            types = "1111"
        # print("int id", channel_id)
        await send_notifications(string, channel_id, types)


# TODO: stop notifying immediately after running program.
@notification_loop.before_loop
async def notification_before():
    await client.wait_until_ready()


notification_loop.start()
login_lock = False

# This is our input stream for our discord bot
# Every message that comes from the chat server will go through here
@client.event
async def on_message(message):
    # just so that bot does not respond back to itself
    if message.author == client.user:
        return

    # this message will be every single message that enters the server
    # currently saving this info so its easier for us to debug
    BOT_RESPONSES.set_message_param(message)
    BOT_RESPONSES.set_username_param(str(message.author).split('#')[0])
    BOT_RESPONSES.set_channel_param(str(message.channel.name))
    BOT_RESPONSES.print_server_messages()

    username = str(message.author).split('#')[0]
    user_message = str(message.content)
    channel = str(message.channel.name)
    channelID = message.channel.id
    
    print(f'{username}: {user_message} ({channel}) ({message.channel.id})')

    def check(msg):
        return msg.author == message.author

    async def recieve_response():
        try:
            res = await client.wait_for('message', check=check)
        except asyncio.TimeoutError:
            await message.channel.send("Timed out.")
            return None
        return res

    async def request_username_password():
        await message.channel.send("What is your username?")
        username = await recieve_response()
        author_id_to_username_map[username.author.id] = username.content
        BOT_RESPONSES.set_db_username(username.content)

    def get_weekday(msg):
        msg = msg.lower()
        if "mon" in msg:
            return 0
        elif "tue" in msg:
            return 1
        elif "wed" in msg:
            return 2
        elif "thur" in msg:
            return 3
        elif "fri" in msg:
            return 4
        elif "sat" in msg:
            return 5
        elif "sun" in msg:
            return 6

        return -1

    def parse_time(string):
        time = datetime.datetime.strptime(string, "%H:%M")
        return time

    def time_to_string(time):
        time_str = time.strftime("%H:%M")
        return time_str

    async def get_time():
        await message.channel.send("What time? (e.g. 09: 12, 10:00, 23:24)")

        new_time = await recieve_response()
        if not new_time:
            return

        if len(new_time.content) != 5 or new_time.content[2] != ":":
            await message.channel.send("Please re-enter your time as the format given.")
            return None

        try:
            h = int(new_time.content[:2])
            m = int(new_time.content[3:])
        except ValueError:
            await message.channel.send("Please re-enter your time as the format given.")
            return None

        if h < 0 or h > 23 or m < 0 or m > 59:
            await message.channel.send("Please re-enter your time as the format given.")
            return None

        return new_time

    async def connect_bs_to_discord():
        await message.channel.send("boilerkey url...")

        res = await recieve_response()
        url = res.content
        await message.channel.send("bs username")
        res = await recieve_response()
        bs_username = res.content
        await message.channel.send("bs 4 digit pin")
        res = await recieve_response()
        bs_pin = res.content
        status = setup_automation(DB_UTILS, author_id_to_username_map[message.author.id], bs_username, bs_pin, url)

    async def delete_noti_all():
        await message.channel.send("Are you sure to delete all of your scheduled times?")

        res = await recieve_response()
        if res.content.startswith("y") or res.content.startswith("right"):
            DB_UTILS.clear_notification_schedule(author_id_to_username_map[message.author.id])
            await message.channel.send("Schedule deleted")
        else:
            await message.channel.send(f"No changes are made to your schedule.")

    async def delete_noti_some(current_times):
        msg = ""
        for i, time in enumerate(current_times):
            msg += f"{i + 1}: {time[0]} {NOT_FREQ_MAP[int(time[1])].lower()}\n"

        await message.channel.send("Which time do you want to delete?")
        await message.channel.send(msg)

        while True:
            res = await recieve_response()

            try:
                num = int(res.content)
            except ValueError:
                await message.channel.send(f"Please choose a number between 1 ~ {i + 1}")
                continue

            if num not in range(1, i + 2):
                await message.channel.send(f"Please choose a number between 1 ~ {i + 1}")
                continue

            break

        num -= 1
        await message.channel.send(f"Delete time: {current_times[num][0]} {NOT_FREQ_MAP[int(current_times[num][1])]}?")

        res = await recieve_response()

        if res.content.startswith("y") or res.content.startswith("right"):
            DB_UTILS.delete_notification_schedule(author_id_to_username_map[message.author.id], current_times[num][0],
                                                  current_times[num][1])

            await message.channel.send("Schedule deleted")
        else:
            await message.channel.send(f"No changes are made to your schedule.")

    if message.author.id not in author_id_to_username_map:
        await request_username_password()

    # TODO: might have problems with this lock when multiple users are using....
    global login_lock
    if not (BS_UTILS.session_exists() and BS_UTILS.check_connection()) and not login_lock:
        login_lock = True

        db_res = DB_UTILS.get_bs_username_pin(author_id_to_username_map[message.author.id])

        while not db_res or not db_res[0][0]:
            await message.channel.send("Setting up auto login...")
            await connect_bs_to_discord()
            db_res = DB_UTILS.get_bs_username_pin(author_id_to_username_map[message.author.id])
            if not db_res or not db_res[0][0]:
                await message.channel.send("BrightSpace setup failed. please check your cridentials!")
                login_lock = False
                return

        await message.channel.send("Logging in to BrightSpace...")
        BS_UTILS.set_session_auto(DB_UTILS, author_id_to_username_map[message.author.id])

        if BS_UTILS.check_connection():
            await message.channel.send("Login successed!")

        while not BS_UTILS.check_connection():
            await message.channel.send(
                "Connection failed. Please check your internet connect and cridentials. \n Do you want to reset your BS cridentials, or retry to login?")
            res = await recieve_response()
            if "retry" in res.content:
                await message.channel.send("Logging in to BrightSpace...")
                BS_UTILS.set_session_auto(DB_UTILS, author_id_to_username_map[message.author.id])
            elif "reset" in res.content:
                await message.channel.send("Setting up auto login...")
                await connect_bs_to_discord()
                await message.channel.send("Logging in to BrightSpace...")
                BS_UTILS.set_session_auto(DB_UTILS, author_id_to_username_map[message.author.id])
            else:
                await message.channel.send("See you next time...")
                login_lock = False
                return

        login_lock = False


    elif not BS_UTILS.check_connection() and login_lock:
        return

    if not BS_UTILS.check_connection():
        await message.channel.send("Connection to BS lost. Attempting to reconnect to BS...")
        BS_UTILS.set_session_auto(DB_UTILS, author_id_to_username_map[message.author.id])

    # test gate to prevent multiple responses from the bot to the user
    # guild_members = message.guild.members
    # if message.author not in guild_members:
    #    return

    # Lets say that we want the bot to only respond to a specific text channel in a server named 'todo'
    if message.channel.name == 'specifics':
        if user_message.lower() == 'im bored':
            await message.channel.send("You should probably study...")
            return

    '''
    start of discord commands below
    '''
    # setting up a basic 'hello' command so you get this gist of it
    if user_message.lower() == 'hello':
        # put your custom message here for the bot to output
        # we would incorporate our chat module here and then craft an appropriate response
        # await message.channel.send(f'Hello {username}!')
        # return
        await BOT_RESPONSES.test_hello()
        return

    elif user_message.lower() == 'bye':
        await message.channel.send(f'Bye {username}!')
        return
    # get the current storage path
    elif user_message.lower() == 'current storage location':
        await BOT_RESPONSES.current_storage(DB_USERNAME)
        return

    # update the current storage path (used starts with so they can type update storage destination or path)
    elif message.content.startswith('update storage'):
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
                drive = init_google_auths()
                return_val = validate_path_drive(new_storage.content, drive)
                if not return_val:
                    await message.channel.send("Not a valid path. Try the cycle again.")
                else:
                    # todo add saving mechanism to cloud database

                    sql_type = "UPDATE PREFERENCES SET STORAGE_LOCATION = '{path_type}' WHERE USERNAME = '{f_name}';" \
                        .format(path_type="Google Drive", f_name=DB_USERNAME)

                    DB_UTILS._mysql.general_command(sql_type)
                    sql_path = "UPDATE PREFERENCES SET STORAGE_PATH = '{path}' WHERE USERNAME = '{f_name}';" \
                        .format(path=new_storage.content, f_name=DB_USERNAME)
                    DB_UTILS._mysql.general_command(sql_path)

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
                        .format(path_type="Local Machine", f_name=DB_USERNAME)

                    DB_UTILS._mysql.general_command(sql_type)
                    sql_path = "UPDATE PREFERENCES SET STORAGE_PATH = '{path}' WHERE USERNAME = '{f_name}';" \
                        .format(path=new_storage.content, f_name=DB_USERNAME)
                    DB_UTILS._mysql.general_command(sql_path)
                    await message.channel.send("New path saved")
                return
            except asyncio.TimeoutError:
                await message.channel.send("taking too long...")

        else:
            await message.channel.send("Your input isn't valid")

    # get a letter grade for a class
    elif message.content.startswith("grades:"):
        courses = message.content.split(":")[1].split(",")
        IDs = []
        for c in courses:
            course_id = BS_UTILS.find_course_id(c)
            IDs.append(course_id)
        print(IDs)

        grades = {}
        counter = 0
        for i in IDs:
            if i == -1:
                grades[courses[counter]] = 'Not found'
            else:
                fraction_string, percentage = BS_UTILS._bsapi.get_grade(i)
                print(fraction_string)
                print(percentage)
                if len(fraction_string) <= 1:
                    grades[courses[counter]] = 'Not found'
                else:
                    letter = BS_UTILS.get_letter_grade(percentage)
                    grades[courses[counter]] = letter
            counter = counter + 1

        # print(grades)
        grades = dict(sorted(grades.items(), key=lambda item: item[1]))
        # print(grades)
        final_string = "Your grades are: \n"
        for key, value in grades.items():
            final_string = final_string + key.upper() + ": " + value + "\n"

        await message.channel.send(final_string)
        return


    elif message.content.startswith("get assignment feedback"):
        await message.channel.send("Please provide the Course name (for ex, NUTR 303) \n")

        def author_check(m):
            return m.author == message.author

        course_name = await client.wait_for('message', check=author_check)
        await message.channel.send("Please provide the full assignment name (for ex, 'Recitation Assignment 1')\n")
        assignment_name = await client.wait_for('message', check=author_check)

        course_name_str = str(course_name.content)  # converting it here for unit tests
        assignment_name_str = str(assignment_name.content)  # converting it here for unit tests

        feedback = BS_UTILS.get_assignment_feedback(course_name_str, assignment_name_str)

        if feedback.__contains__("ERROR") or feedback.__contains__("BOT REPORT"):
            await message.channel.send(feedback)
        else:
            await message.channel.send("Feedback from Grader: \n")
            await message.channel.send(feedback)

        return

    # enable the user to search for a specific student in a class.
    elif message.content.startswith("search for student"):
        await message.channel.send("Please provide the course in which you want to search \n")

        def author_check(m):
            return m.author == message.author

        course_name = await client.wait_for('message', check=author_check)
        await message.channel.send(
            "Please provide the full name (First Name + Last Name, e.g 'Shaun Thomas') of the student you would like to search for.\n")
        student_name = await client.wait_for('message', check=author_check)

        course_name_str = str(course_name.content)
        student_name_str = str(student_name.content)

        output = BS_UTILS.search_for_student_in_class(course_name_str, student_name_str)

        if output:
            await message.channel.send(student_name_str + " is a student in " + course_name_str)
        elif output == False:
            course_id = BS_UTILS.find_course_ID(course_name_str)
            if course_id is None:
                await message.channel.send(
                    "ERROR: Please make sure the course you have specified is spelled correctly and is a course that you are currently enrolled in.")
            else:
                await message.channel.send(student_name_str + " is not a student in " + course_name_str)

        return


    # get upcoming quizzes across all classes
    elif message.content.startswith("get upcoming quizzes"):
        upcoming_quizzes = BS_UTILS.get_upcoming_quizzes()
        # if there are no upcoming quizzes returned, then we report to the user.
        if not upcoming_quizzes:
            await message.channel.send("You have no upcoming quizzes or exams.")
            return
        else:
            await message.channel.send("You have the following upcoming assessments:\n")
            for quiz in upcoming_quizzes:
                course_name = quiz
                current_quiz = upcoming_quizzes[quiz]
                current_quiz_name = current_quiz["Name"]
                current_quiz_due_date = current_quiz["DueDate"]
                output_str = course_name + " - " + current_quiz_name + " due " + current_quiz_due_date + "\n"
                await message.channel.send(output_str)
            return

    elif message.content.startswith("get busiest weeks"):
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)

    elif message.content.startswith("get newly graded assignments"):
        await message.channel.send("Retrieving grades...")
        grade_updates = BS_UTILS.get_grade_updates()
        # if there are no grade updates returned, then we report to the user.
        if len(grade_updates) == 0:
            await message.channel.send("You have no new grade updates.")
            return
        else:
            await message.channel.send("The following assignments have been graded:\n")
            for grade in grade_updates:
                output_str = "Course Id:" + str(grade['course_id']) + "- " + grade['assignment_name'] + " " + grade[
                    'grade'] + "\n"
                await message.channel.send(output_str)
            return

    # changing bot name
    elif message.content.startswith("change bot name"):

        # change value used to check if the user keep wants to change the name of the bot
        # initialized to True

        change = True
        valid_change_response = True

        # check method for waiting client's reply back
        def check(msg):
            return msg.author == message.author

        while change:
            # ask the user to which name they want to change
            await message.channel.send("To which name do you want to change?")

            # get reply back from the user for bot's name
            try:
                new_name = await client.wait_for('message', check=check)
            except asyncio.TimeoutError:
                await message.channel.send("Timeout ERROR has occurred. Please try the query again.")
                return

            # name changed message.
            await message.guild.me.edit(nick=new_name.content)
            await message.channel.send("My name is now changed!")

            # ask if the user wants to change the name again
            await message.channel.send("Would you like to change my name again? Yes or No")

            # get reply back from the user if they want to change the bot name again.
            try:
                change_again = await client.wait_for('message', check=check)

                # user does not want to change again
                if change_again.content.startswith('No'):
                    change = False
                    await message.channel.send("Thank you for changing my name!")
                elif not change_again.content.startswith('Yes'):  # user input invalid response
                    await message.channel.send("Invalid response given! Please try the query again.")
                    return
            except asyncio.TimeoutError:
                await message.channel.send("Timeout ERROR has occurred. Please try the query again.")
                return

    elif message.content.startswith("upcoming discussion"):
        # dictionary of class_name, [list of dates]
        dates = BS_UTILS.get_dict_of_discussion_dates()

        # dates = DATES #ONLY FOR DEBUG
        def check(msg):
            return msg.author == message.author

        # find discussion post deadline for 2 weeks
        string = BS_UTILS.find_upcoming_disc_dates(14, dates)

        if len(string) == 0:
            await message.channel.send(
                "No upcoming posts for the next two weeks. Would you like to look further than 2 weeks?")
            try:
                response = await client.wait_for('message', check=check, timeout=30)
            except asyncio.TimeoutError:
                await message.channel.send("taking too long...")
                return
            # they want to see everything
            if response.content.startswith("yes"):
                string = BS_UTILS.find_upcoming_disc_dates(0, dates)
                if len(string) == 0:
                    await message.channel.send("No upcoming posts.")
                else:
                    await message.channel.send(string)
                return
            # don't want to see anything
            else:
                await message.channel.send("Okay, sounds good!")
                return
        else:
            await message.channel.send(string)
            return

    elif message.content.startswith("update schedule"):

        async def everyday():
            new_time = None
            while not new_time:
                new_time = await get_time()

            await message.channel.send(f"{new_time.content}, right?")
            res = await recieve_response()

            if res.content.startswith("y") or res.content.startswith("right"):
                DB_UTILS.add_notifictaion_schedule(author_id_to_username_map[res.author.id], new_time.content,
                                                   1 * 24 * 60, res.channel.id, description=7)  # 7 = everyday
                # SCHEDULED_HOURS.append(new_hour)
                await message.channel.send(f"Schedule changed.")
            else:
                await message.channel.send(f"No changes are made to your schedule.")

        async def every_week():
            await message.channel.send("Which week day?")
            while True:
                res = await recieve_response()
                day = get_weekday(res.content)
                if day == -1:
                    await message.channel.send("Please choose from Mon/Tues/Wed/Thurs/Fri/Sat/Sun")
                    continue
                break

            new_time = None
            while not new_time:
                new_time = await get_time()

            day_str = NOT_FREQ_MAP[day]
            await message.channel.send(f"{new_time.content} for {day_str.lower()}?")
            res = await recieve_response()
            if res.content.startswith("y") or res.content.startswith("right"):
                DB_UTILS.add_notifictaion_schedule(author_id_to_username_map[res.author.id], new_time.content,
                                                   1 * 24 * 7 * 60, res.channel.id, description=day)
                await message.channel.send(f"Schedule changed.")
            else:
                await message.channel.send(f"No changes are made to your schedule.")

        async def add_week_or_everyday():
            await message.channel.send(f"Do you want to be notified everyday, or by a specific weekday?")
            res = await recieve_response()
            if "every" in res.content:
                await everyday()
            else:
                await every_week()

        async def by_amount():
            def calculate_notis_each_week(schedules):
                notifications = 0
                for schedule in schedules:
                    weekday = schedule[1]
                    if weekday == '7':
                        notifications += 7
                    else:
                        notifications += 1
                return notifications

            await message.channel.send("How many notifications do you want every week?")
            res = await recieve_response()

            while True:
                try:
                    freq = int(res.content)
                except ValueError:
                    await message.channel.send("Please enter a number")
                    continue
                break

            s_times = DB_UTILS.get_notifictaion_schedule_with_description(author_id_to_username_map[message.author.id])
            curr_len = calculate_notis_each_week(s_times)

            if curr_len < freq:
                while curr_len < freq:
                    await message.channel.send(f"There are currently {curr_len} schedules. ")

                    await message.channel.send(f"Do you want to add more?")

                    res = await recieve_response()
                    if res.content.startswith("y") or res.content.startswith("right"):
                        if freq - curr_len < 7:
                            # await message.channel.send(f"Adding schedules every day will e")
                            await every_week()
                        else:
                            await add_week_or_everyday()
                        s_times = DB_UTILS.get_notifictaion_schedule_with_description(
                            author_id_to_username_map[message.author.id])
                        curr_len = calculate_notis_each_week(s_times)
                        continue
                    await message.channel.send(f"Understood. Have a nice day.")
                    break
            elif curr_len > freq:
                while curr_len > freq:
                    await message.channel.send(
                        f"There are currently {curr_len} scheduled times. No new schedules will be added.\nDo you want to delete any schedules?")
                    res = await recieve_response()
                    if res.content.startswith("y") or res.content.startswith("right"):
                        current_times = DB_UTILS.get_notifictaion_schedule_with_description(
                            author_id_to_username_map[message.author.id])
                        await delete_noti_some(current_times)

                        s_times = DB_UTILS.get_notifictaion_schedule_with_description(
                            author_id_to_username_map[message.author.id])
                        curr_len = calculate_notis_each_week(s_times)

                        if curr_len <= freq:
                            break

                        await message.channel.send(f"Do you want to delete more?")

                        res = await recieve_response()
                        if res.content.startswith("y") or res.content.startswith("right"):
                            continue
                    await message.channel.send(f"Understood. Have a nice day.")
                    break
            else:
                await message.channel.send(f"You already have {freq} schedules.")

        async def by_class_schedule():
            scheduled_classes = DB_UTILS.get_classes_in_schedule(author_id_to_username_map[message.author.id])
            if not scheduled_classes:
                await message.channel.send("You don't have any scheduled classes.")
                return

            msg = "Which class do you want to recieve notifications before?\n\n"
            msg += "List of classes:\n"
            for i, c in enumerate(scheduled_classes):
                msg += f"{i + 1}. {c}\n"

            await message.channel.send(msg)

            while True:
                res = await recieve_response()

                try:
                    num = int(res.content)
                except ValueError:
                    await message.channel.send(f"Please choose a number between 1 ~ {i + 1}")
                    continue

                if num not in range(1, i + 2):
                    await message.channel.send(f"Please choose a number between 1 ~ {i + 1}")
                    continue

                break

            class_name = scheduled_classes[num - 1]

            await message.channel.send("How many minutes before class?")
            while True:
                res = await recieve_response()
                try:
                    mins = int(res.content)
                except ValueError:
                    await message.channel.send("Please enter a number")
                    continue
                break

            scheduled_classes = DB_UTILS.get_class_schedule_with_description(
                author_id_to_username_map[message.author.id])
            # print(scheduled_classes)
            for c in scheduled_classes:
                # print(c[0])
                if c[0] != class_name:
                    continue

                time_str = c[1]
                time = parse_time(time_str)
                time = time - datetime.timedelta(minutes=mins)
                new_time_str = time_to_string(time)

                DB_UTILS.add_notifictaion_schedule(author_id_to_username_map[message.author.id], new_time_str,
                                                   1 * 60 * 24 * 7, res.channel.id, c[2])

            await message.channel.send("Schedule modified.")

        async def check_replace(noti_func):
            await message.channel.send(f"Do you want to add to your current schedule or build a brand new one?")

            res = await recieve_response()
            if "new" in res.content:
                curr_username = author_id_to_username_map[message.author.id]

                # moves all old schedules to a temp username
                temp_username = curr_username + "_temp"
                DB_UTILS.change_username("NOTIFICATION_SCHEDULE", curr_username, temp_username)

                await noti_func()

                old_schedules = DB_UTILS.get_notifictaion_schedule_with_description(temp_username)
                msg = "Old schedules:\n"
                for i, time in enumerate(old_schedules):
                    msg += f"{i + 1}: {time[0]} {NOT_FREQ_MAP[int(time[1])].lower()}\n"

                new_schedules = DB_UTILS.get_notifictaion_schedule_with_description(curr_username)
                msg += "\nNew schedules:\n"
                for i, time in enumerate(new_schedules):
                    msg += f"{i + 1}: {time[0]} {NOT_FREQ_MAP[int(time[1])].lower()}\n"

                msg += "\nDo you want to replace your old schedule with the new one?"
                await message.channel.send(msg)

                res = await recieve_response()
                if res.content.startswith("y") or res.content.startswith("right"):
                    DB_UTILS.clear_notification_schedule(temp_username)
                else:
                    DB_UTILS.clear_notification_schedule(curr_username)
                    DB_UTILS.change_username("NOTIFICATION_SCHEDULE", temp_username, curr_username)

                await message.channel.send("Finished. Please check your schedule with \"check notifications\"")
            else:
                await noti_func()

        await message.channel.send(
            "Do you want your notification to be sent every day, every week, by a specific amount, or according to your class schedule?")

        res = await recieve_response()
        if "day" in res.content:
            await check_replace(everyday)
        elif "week" in res.content:
            await check_replace(every_week)
        elif "amount" in res.content:
            await check_replace(by_amount)
        elif "class" in res.content:
            await check_replace(by_class_schedule)
        else:
            await message.channel.send("I am not sure about what you want to do")
            return

    elif message.content.startswith("update type"):
        current_times = DB_UTILS.get_notifictaion_schedule_with_description(
            author_id_to_username_map[message.author.id])

        if not current_times:
            await message.channel.send("You don't have any scheduled times now.")
            return

        msg = ""
        for i, time in enumerate(current_times):
            msg += f"{i + 1}: {time[0]} {NOT_FREQ_MAP[int(time[1])].lower()}\n"

        await message.channel.send("Which time do you want to change?")
        await message.channel.send(msg)

        while True:
            res = await recieve_response()

            try:
                num = int(res.content)
            except ValueError:
                await message.channel.send(f"Please choose a number between 1 ~ {i + 1}")
                continue

            if num not in range(1, i + 2):
                await message.channel.send(f"Please choose a number between 1 ~ {i + 1}")
                continue

            break

        new_types = ['0', '0', '0', '0']
        await message.channel.send(f"Discussions?")
        res = await recieve_response()
        if res.content.startswith("y") or res.content.startswith("right"):
            new_types[0] = '1'

        await message.channel.send(f"Announcements?")
        res = await recieve_response()
        if res.content.startswith("y") or res.content.startswith("right"):
            new_types[1] = '1'

        await message.channel.send(f"Reminders?")
        res = await recieve_response()
        if res.content.startswith("y") or res.content.startswith("right"):
            new_types[2] = '1'

        await message.channel.send(f"Due dates?")
        res = await recieve_response()
        if res.content.startswith("y") or res.content.startswith("right"):
            new_types[3] = '1'

        new_types = "".join(new_types)
        num -= 1
        await message.channel.send(f"Change time: {current_times[num][0]} {current_times[num][1]}'s types?")

        res = await recieve_response()

        if res.content.startswith("y") or res.content.startswith("right"):
            DB_UTILS.update_notification_schedule_types(author_id_to_username_map[message.author.id],
                                                        current_times[num][0], current_times[num][1], new_types)

            await message.channel.send("Type updated")
        else:
            await message.channel.send(f"No changes are made to your schedule.")

    elif message.content.startswith("delete noti"):
        if message.author.id not in author_id_to_username_map:
            await request_username_password()

        current_times = DB_UTILS.get_notifictaion_schedule_with_description(
            author_id_to_username_map[message.author.id])

        if not current_times:
            await message.channel.send("You don't have any scheduled times now.")
            return

        await message.channel.send("Do you want to delete all scheduled times or specific times?")

        res = await recieve_response()
        if "all" in res.content:
            await delete_noti_all()
        else:
            await delete_noti_some(current_times)


    elif message.content.startswith("check noti"):
        if message.author.id not in author_id_to_username_map:
            await request_username_password()

        s_times = DB_UTILS.get_notifictaion_schedule_with_description(author_id_to_username_map[message.author.id])
        if not s_times:
            await message.channel.send("No schedules now!")
        else:
            msg = f"Scheduled times for {author_id_to_username_map[message.author.id]}:\n"
            for hour in s_times:
                msg += f"{hour[0]} {NOT_FREQ_MAP[int(hour[1])].lower()}\n"

            await message.channel.send(msg)

    elif message.content.startswith("add class"):
        while True:
            await message.channel.send("What is the class name?")
            res = await recieve_response()
            class_name = res.content

            while True:
                await message.channel.send("Which week day?")
                while True:
                    res = await recieve_response()
                    day = get_weekday(res.content)
                    if day == -1:
                        await message.channel.send("Please choose from Mon/Tues/Wed/Thurs/Fri/Sat/Sun")
                        continue
                    break

                new_time = None
                while not new_time:
                    new_time = await get_time()

                day_str = NOT_FREQ_MAP[day]
                await message.channel.send(f"{new_time.content} for {day_str.lower()}?")
                res = await recieve_response()
                if res.content.startswith("y") or res.content.startswith("right"):
                    DB_UTILS.add_class_schedule(author_id_to_username_map[res.author.id], class_name, new_time.content,
                                                description=day)
                    await message.channel.send(f"Schedule changed.")
                else:
                    await message.channel.send(f"No changes are made to your schedule.")

                await message.channel.send(f"Do you want to add another time for this class?")
                res = await recieve_response()
                if res.content.startswith("y") or res.content.startswith("right"):
                    continue
                break

            await message.channel.send(f"Do you want to add another class?")
            res = await recieve_response()
            if res.content.startswith("y") or res.content.startswith("right"):
                continue
            break

    elif message.content.startswith("check class"):
        if message.author.id not in author_id_to_username_map:
            await request_username_password()

        c_times = DB_UTILS.get_class_schedule_with_description(author_id_to_username_map[message.author.id])

        if not c_times:
            await message.channel.send("No schedules now!")
        else:
            msg = f"Scheduled classes for {author_id_to_username_map[message.author.id]}:\n"
            for hour in c_times:
                msg += f"{hour[0]} {hour[1]} {NOT_FREQ_MAP[int(hour[2])].lower()}\n"

            await message.channel.send(msg)

    elif message.content.startswith("download: "):
        course = message.content.split(":")[1]
        sql_command = f"SELECT STORAGE_PATH from PREFERENCES WHERE USERNAME = '{DB_USERNAME}';"
        storage_path = DB_UTILS._mysql.general_command(sql_command)
        sql_command = f"SELECT STORAGE_LOCATION from PREFERENCES WHERE USERNAME = '{DB_USERNAME}';"
        storage_type = DB_UTILS._mysql.general_command(sql_command)
        course_id = BS_UTILS.find_course_id(course)
        if storage_path[0][0] is not None:
            BS_UTILS.download_files(course_id, storage_path[0][0], storage_type[0][0])
            # Check if they specified a place to have file related notifications
            sql_command = f"SELECT FILES_TC FROM PREFERENCES WHERE USERNAME = '{DB_USERNAME}';"
            result = DB_UTILS._mysql.general_command(sql_command)[0][0]
            print(result)
            # if so, redirect message to that channel
            if result is not None:
                # get the channel ID
                channel_id = 0
                for channel in message.guild.text_channels:
                    result = result.replace(" ", "-")
                    if channel.name == result:
                        channel_id = channel.id
                        break
                if channel_id != 0:
                    send_message_to_channel = client.get_channel(channel_id)
                    await send_message_to_channel.send("Files downloaded successfully!")
                else:
                    # Some mistake came and could not find channel ID, so just go to default chat
                    await message.channel.send("Files downloaded successfully!")
            else:
                # else go to normal channel
                await message.channel.send("Files downloaded successfully!")
            return
        else:
            sql_command = f"SELECT FILES_TC IN PREFERENCES WHERE USERNAME = '{DB_USERNAME}';"
            result = DB_UTILS._mysql.general_command(sql_command)
            print(result)
            # if so, redirect message to that channel
            if result is not None:
                # get the channel ID
                channel_id = 0
                for channel in message.guild.text_channels:
                    result = result.replace(" ", "-")
                    if channel.name == result:
                        channel_id = channel.id
                        break
                if channel_id != 0:
                    send_message_to_channel = client.get_channel(channel_id)
                    await send_message_to_channel.send("Files not downloaded successfully.")
                else:
                    # Some mistake came and could not find channel ID, so just go to default chat
                    await message.channel.send("Files not downloaded successfully.")
            else:
                # else go to normal channel
                await message.channel.send("Files not downloaded successfully.")
            return

    # returning user course priority by either grade or upcoming events
    elif message.content.startswith("get course priority"):
        # reply backs to the user
        suggested_course_priority = ""
        found_missing_info_courses = ""

        def check(m):
            return m.author == message.author

        # ask user for pick grade or by due date
        await message.channel.send("Please pick between grade or due dates for prioritizing your courses.")

        try:
            priority_option = await client.wait_for('message', check=check)

            if priority_option.content.startswith("grade"):
                # api call for grades
                await message.channel.send("Setting course priority by grade ...")

                priority = BS_UTILS.get_sorted_grades()[0]
                missing = BS_UTILS.get_sorted_grades()[1]

                for x in range(0, len(priority)):
                    suggested_course_priority += priority[x]
                    if not x == len(priority) - 1:
                        suggested_course_priority += " << "

                for x in range(0, len(missing)):
                    found_missing_info_courses += missing[x]
                    if not x == len(missing) - 1:
                        found_missing_info_courses += " , "

                await message.channel.send("The suggested course priority is (highest grade << lowest grade):\n"
                                           + suggested_course_priority)
                await message.channel.send("There are some courses that miss final grades:\n"
                                           + found_missing_info_courses)

            elif priority_option.content.startswith("due dates"):
                # api call for due dates
                await message.channel.send("Setting course priority by upcoming due dates ...")

                priority = BS_UTILS.get_course_by_due_date()[0]
                event_missing = BS_UTILS.get_course_by_due_date()[1]

                for x in range(0, len(priority)):
                    suggested_course_priority += priority[x]['Course Name']
                    if not x == len(priority) - 1:
                        suggested_course_priority += " >> "

                for x in range(0, len(event_missing)):
                    found_missing_info_courses += event_missing[x]['Course Name']
                    if not x == len(event_missing) - 1:
                        found_missing_info_courses += ", "

                await message.channel.send("The suggested course priority is (earliest >> latest):\n" +
                                           suggested_course_priority)
                await message.channel.send("There are some courses that have no upcoming due dates:\n" +
                                           found_missing_info_courses)
            else:
                await message.channel.send("Invalid response given! Please try the query again.")
                return

        except asyncio.TimeoutError:
            await message.channel.send("Timeout ERROR has occurred. Please try the query again.")
            return

        return

        # get a letter grade for a class
    elif message.content.startswith("overall points:"):
        courses = message.content.split(":")[1].split(",")
        IDs = []
        for c in courses:
            course_id = BS_UTILS.find_course_id(c)
            IDs.append(course_id)  # getting the list of course IDs
        print(IDs)

        grades = {}
        tosort = {}
        counter = 0
        for i in IDs:
            if i == -1:
                grades[courses[counter]] = 'Course not recognized'
                tosort[courses[counter]] = 0
            else:
                yourTotal, classTotal = BS_UTILS.sum_total_points(i)
                if classTotal == 0:
                    grades[courses[counter]] = "No grades are uploaded for this class."
                    tosort[courses[counter]] = 100
                else:
                    percentage = (yourTotal / classTotal) * 100
                    grades[courses[counter]] = '{num:.2f}/{den:.2f}'.format(num=yourTotal, den=classTotal)
                    tosort[courses[counter]] = percentage
            counter = counter + 1

        print(grades)
        print(tosort)
        sorted_list = dict(sorted(tosort.items(), key=lambda item: item[1]))
        print(grades)
        print(sorted_list)
        final_string = "Your overall grades are: \n"
        for key, value in sorted_list.items():
            final_string = final_string + key + ": " + str(grades[key]) + "\n"

        # See if the user specified a grades text channel
        sql_command = f"SELECT GRADES_TC FROM PREFERENCES WHERE USERNAME = '{DB_USERNAME}';"
        result = DB_UTILS._mysql.general_command(sql_command)[0][0]
        print(result)
        # if so, redirect message to that channel
        if result is not None:
            # get the channel ID
            channel_id = 0
            for channel in message.guild.text_channels:
                result = result.replace(" ", "-")
                if channel.name == result:
                    print("found it")
                    channel_id = channel.id
                    break
            if channel_id != 0:
                send_message_to_channel = client.get_channel(channel_id)
                await send_message_to_channel.send(final_string)

            else:
                # Some mistake came and could not find channel ID, so just go to default chat
                await message.channel.send(final_string)
        else:
            # else go to normal channel
            await message.channel.send(final_string)

        return

    # redirecting notifications
    elif message.content.startswith("redirect notifications"):
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
        print(category.lower())
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
        sql_command = f"SELECT {db_category} FROM PREFERENCES WHERE USERNAME = '{DB_USERNAME}';"
        current_saved_tc = DB_UTILS._mysql.general_command(sql_command)[0][0]
        # Check if the channel that is being requested has already been created
        sql_command = f"SELECT LIST_OF_TCS FROM PREFERENCES WHERE USERNAME = '{DB_USERNAME}';"
        list_of_tcs = DB_UTILS._mysql.general_command(sql_command)[0][0]
        if list_of_tcs is None:
            sql_command = f"UPDATE PREFERENCES SET LIST_OF_TCS = 'general' WHERE USERNAME = '{DB_USERNAME}';"
            DB_UTILS._mysql.general_command(sql_command)
            sql_command = f"SELECT LIST_OF_TCS FROM PREFERENCES WHERE USERNAME = '{DB_USERNAME}';"
            list_of_tcs = DB_UTILS._mysql.general_command(sql_command)[0][0]

        array = list_of_tcs.split(",")
        found = False
        for a in array:
            if a == text_channel:
                # Then this text channel already exists
                found = True
        # found, list_of_tcs = BOT_RESPONSES.check_if_tc_exists(current_saved_tc, DB_USERNAME)

        sql_command = f"UPDATE PREFERENCES SET {db_category} = '{text_channel}' WHERE USERNAME = '{DB_USERNAME}';"
        DB_UTILS._mysql.general_command(sql_command)

        if not found:
            list_of_tcs = list_of_tcs + "," + text_channel
            sql_command = f"UPDATE PREFERENCES SET LIST_OF_TCS = '{list_of_tcs}' WHERE USERNAME = '{DB_USERNAME}';"
            DB_UTILS._mysql.general_command(sql_command)
            name = 'Text Channels'  # This will go under the default category
            cat = discord.utils.get(message.guild.categories, name=name)
            await message.guild.create_text_channel(text_channel, category=cat)

            channel_id = 0
            for channel in message.guild.text_channels:
                print(channel)
                print(channel.id)
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


    elif message.content.startswith("where are my notifications?"):
        sql = f"SELECT GRADES_TC FROM PREFERENCES WHERE USERNAME = '{DB_USERNAME}';"
        grades = DB_UTILS._mysql.general_command(sql)[0][0]
        if grades is None:
            grades = "Not specified"
        sql = f"SELECT FILES_TC FROM PREFERENCES WHERE USERNAME = '{DB_USERNAME}';"
        files = DB_UTILS._mysql.general_command(sql)[0][0]
        if files is None:
            files = "Not specified"
        sql = f"SELECT DEADLINES_TC FROM PREFERENCES WHERE USERNAME = '{DB_USERNAME}';"
        deadlines = DB_UTILS._mysql.general_command(sql)[0][0]
        if deadlines is None:
            deadlines = "Not specified"
        final_string = f"Your notification redirections are saved as the following:\n" \
                       f"GRADES -> {grades}\n" \
                       f"DEADLINES -> {deadlines}\n" \
                       f"FILES -> {files}"
        await message.channel.send(final_string)

    elif message.content.startswith("add quiz due dates to calendar"):
        await message.channel.send("Retrieving quizzes...")
        quizzes = BS_UTILS.get_all_upcoming_quizzes()
        for quiz in quizzes:
            cal = Calendar()
            event_title = f"QUIZ DUE: {quiz['quiz_name']} ({quiz['course_id']})"
            description = f"{quiz['quiz_name']} for {quiz['course_name']} is due. Don't forget to submit it!"
            date = datetime.datetime.fromisoformat(quiz['due_date'][:-1])
            end = date.isoformat()
            start = (date - datetime.timedelta(hours=1)).isoformat()
            event_id, end_time = cal.get_event_from_name(event_title)
            # event hasn't been created in google calendar
            if event_id == -1:
                # insert new event to calendar
                cal.insert_event(event_title, description, start, end)
            # event has already been created
            else:
                # if end time has changed, update the event
                if end_time != end:
                    cal.delete_event(event_id)
                    cal.insert_event(event_title, description, start, end)
                else:
                    await message.channel.send("No new quizzes found.")
        await message.channel.send("Quiz deadlines added/updated to calendar!")
        return

    elif message.content.startswith("get course link"):
        # get user course urls in advance
        user_course_urls = BS_UTILS.get_course_url()

        # bot asks user for specific input
        await message.channel.send("Which course link do you need? Type \'All\' or specific course links")
        await message.channel.send("ex) All or CS 180, CS 240")
        reply_back = ""
        cannot_find_courses = ""

        # check function for client.wait_for
        def check(m):
            return m.author == message.author

        try:
            # get user reply back
            user_reply = await client.wait_for('message', check=check, timeout=60)

            # different user_request options
            # 'All'
            if user_reply.content.lower().startswith("all"):
                for course_name, course_url in user_course_urls.items():
                    reply_back += "{course_name}: {url}\n".format(course_name=course_name,
                                                                  url=course_url)
            else:
                user_requests = user_reply.content.split(", ")
                for requested_course in user_requests:
                    for course_name, course_url in user_course_urls.items():
                        if requested_course.upper() in course_name:
                            reply_back += "{course_name}: {url}\n".format(course_name=course_name,
                                                                          url=course_url)
                        continue
                    if requested_course.upper() not in reply_back:
                        cannot_find_courses += "{course_name}\t".format(course_name=requested_course)

            # send the reply back
            if not reply_back == "":
                await message.channel.send("The followings are the links to your course homepages\n")
                await message.channel.send(reply_back)
                if not cannot_find_courses == "":
                    await message.channel.send("These are courses that I couldn't find:")
                    await message.channel.send(cannot_find_courses)
                    await message.channel.send("Please check if they are your valid course(s)")
            else:
                await message.channel.send("Sorry, we couldn't find the matching courses.")
                await message.channel.send("Please check if they are your valid course(s).")
                # home page vary by campus location
                # West Lafayette: 6824
                # Fort Wayne: 6822
                # Northwest: 6823
                await message.channel.send("Here is the home page default link: " +
                                           "https://purdue.brightspace.com/d2l/home/6824")
                return

        except asyncio.TimeoutError:
            await message.channel.send("Timeout ERROR has occurred. Please try the query again.")
        return

    elif message.content.startswith("get upcoming assignments"):
        # get today's date
        today = datetime.datetime.utcnow()

        # user start and end time set to today for default
        user_start_time = today
        user_end_time = today

        # user requested event list
        event_list = []

        await message.channel.send(
            "Which time period of assignments/exams do you need? Please type one of the options:")
        await message.channel.send("\'Tomorrow\' or \'Next week\' or \'Next month\' or \'mm/dd/yy - mm/dd/yy\'")

        # check function for client.wait_for
        def check(m):
            return m.author == message.author

        try:
            # get user response back
            user_reply = await client.wait_for('message', check=check, timeout=120)

            # different user options
            if user_reply.content.lower() == "tomorrow":
                user_end_time = today + datetime.timedelta(days=1)
            elif user_reply.content.lower() == "next week":
                user_end_time = today + datetime.timedelta(days=7)
            elif user_reply.content.lower() == "next month":
                user_end_time = today + datetime.timedelta(days=31)
            # elif user_reply.content.lower() == "semester":
            #    user_end_time = today + datetime.timedelta(days=122)
            else:
                user_requested_time = user_reply.content.split(" - ")
                try:
                    user_start_time = datetime.datetime.strptime(user_requested_time[0], "%m/%d/%y")
                    user_end_time = datetime.datetime.strptime(user_requested_time[1], "%m/%d/%y")

                    if user_end_time < user_start_time:
                        await message.channel.send("Given time interval is invalid. Please try the query again")
                        return

                    if user_start_time < today:
                        user_start_time = today
                except:
                    await message.channel.send("Given option is invalid. Please try the query again")
                    return

            await message.channel.send("Finding your events ...")
            event_list = BS_UTILS.get_upcoming_events(user_start_time, user_end_time)

            event_list_to_str = ""
            for event in event_list:
                event_list_to_str += "[{due_date}] {name}: {title}".format(due_date=event['Due Date'],
                                                                           name=event['Course Name'],
                                                                           title=event['Event Name'])
                event_list_to_str += "\n"

            await message.channel.send("These are your upcoming assignments/exams:\n" + event_list_to_str)
        except asyncio.TimeoutError:
            await message.channel.send("Timeout ERROR has occurred. Please try the query again.")
        return

    elif message.content.startswith("suggest course study"):
        # check function for client.wait_for
        def check(m):
            return m.author == message.author

        await message.channel.send("What order would you like for suggestions?\n" +
                                   "\'grade, deadline\' or \'deadline, grade\'")

        try:
            user_response = await client.wait_for('message', check=check, timeout=60)

            # default order value
            order = 0

            # user_requested_order = user_response.content.split(", ")
            if user_response.content.lower() == "grade, deadline":
                order = 1
            elif user_response.content.lower() == "deadline, grade":
                order = 2

            await message.channel.send("Creating suggestions...")
            if order != 0:
                focus_suggestion = BS_UTILS.get_focus_suggestion(order)[0]
                lack_info = BS_UTILS.get_focus_suggestion(order)[1]

                reply = ""
                for x in range(0, len(focus_suggestion)):
                    reply += "{course_name}".format(course_name=focus_suggestion[x])
                    if x != len(focus_suggestion) - 1:
                        reply += " << "

                lack_reply = ""
                for x in range(0, len(lack_info)):
                    lack_reply += "{course_name}[{reason}]".format(course_name=lack_info[x]['Course Name'],
                                                                   reason=lack_info[x]['Lack'])
                    if x != len(lack_info) - 1:
                        lack_reply += ", "

                await message.channel.send("Here is your suggested classes to focus more(focus less << focus more):\n"
                                           + reply)
                await message.channel.send("There are some courses that lack info:\n" + lack_reply)
            else:
                await message.channel.send("Invalid order was given. Please try the query again")
                return
        except asyncio.TimeoutError:
            await message.channel.send("Timeout ERROR has occurred. Please try the query again")

        return
    elif message.content.startswith("add office hours to calendar"):
        await message.channel.send("Please input the course name")
        try:
            course_name = await client.wait_for('message', check=check, timeout=60)
            course_name = course_name.content.lower()

            await message.channel.send("Please input the instructor name")
            instr_name = ''
            try:
                instr_name = await client.wait_for('message', check=check, timeout=60)
                instr_name = instr_name.content.lower()
            except asyncio.TimeoutError:
                await message.channel.send("Timeout ERROR has occurred. Please try the query again")

            await message.channel.send("Please input office hour days")
            days = ''
            try:
                days = await client.wait_for('message', check=check, timeout=60)
                days = days.content.lower()
                days = BOT_RESPONSES.format_days_of_week(days)
            except asyncio.TimeoutError:
                await message.channel.send("Timeout ERROR has occurred. Please try the query again")

            await message.channel.send("Please input office hour start time. ie 13:30")
            st_time = ''
            try:
                st_time = await client.wait_for('message', check=check, timeout=60)
                st_time = st_time.content.lower()
            except asyncio.TimeoutError:
                await message.channel.send("Timeout ERROR has occurred. Please try the query again")

            await message.channel.send("Please input office hour end time. ie 14:30")
            end_time = ''
            try:
                end_time = await client.wait_for('message', check=check, timeout=60)
                end_time = end_time.content.lower()
            except asyncio.TimeoutError:
                await message.channel.send("Timeout ERROR has occurred. Please try the query again")

            response = BOT_RESPONSES.add_office_hours_to_calendar(course_name, instr_name, days, st_time, end_time)
            await message.channel.send(response)
        except asyncio.TimeoutError:
            await message.channel.send("Timeout ERROR has occurred. Please try the query again")
        return

    elif message.content.startswith("rename file"):
        # list out the files that they can rename
        response = BOT_RESPONSES.get_downloaded_files(DB_USERNAME)

        def check(m):
            return m.author == message.author

        await message.channel.send(response)
        try:
            user_response = await client.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await message.channel.send("Time error has occurred. Please try the query again")
            return
        response = BOT_RESPONSES.process_renaming_response(DB_USERNAME, user_response.content)
        await message.channel.send(response)
        return

    elif message.content.startswith("!D:"):
        BOT_RESPONSES.download_files(message.content, DB_USERNAME)

    elif message.content.startswith("add discussion schedule"):
        await message.channel.send('What day(s) do you want discussion reminders sent each week?')
        days = await recieve_response()
        username = author_id_to_username_map[days.author.id]
        days = days.content.lower()
        await message.channel.send("Which class's discussions do you want to add to the schedule?")
        classes = await recieve_response()
        classes = classes.content.lower()
        BOT_RESPONSES.add_discussion_schedule_to_db(username, days, classes)
        return

    elif message.content.startswith("check discussion schedule"):
        response = BOT_RESPONSES.discussion_remind_to_post(BOT_RESPONSES.db_username)
        await message.channel.send("Reminder to reply to the following discussions: ")
        if response != '-1':
            await message.channel.send(response)
        return

# Now to actually run the bot!
client.run(config['token'])
