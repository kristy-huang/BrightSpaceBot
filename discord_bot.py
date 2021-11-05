# Our discord token is saved in another file for security
from discord_config import config, USERNAME, PIN
import discord
from discord.ext import tasks, commands
import asyncio
from file_storage import *
import datetime
from bs_api import BSAPI
from bs_utilities import BSUtilities
from database.db_utilities import DBUtilities
from bot_responses import BotResponses
from bs_calendar import Calendar

'''
To add the bot to your own server and test it out, copy this URL into your browser
https://discord.com/api/oauth2/authorize?client_id=894695859567083520&permissions=534992387152&scope=bot
 '''

# This will be our discord client. From here we will get our input
client = discord.Client()
channelID = 663863991218733058  # mine!
# TODO save this in the database - right now this is my (Raveena's) channel
BS_UTILS = BSUtilities()
BS_API = BSAPI()
DB_UTILS = DBUtilities()
BOT_RESPONSES = BotResponses()

SCHEDULED_HOURS = []
DB_USERNAME = 'currymaster'

# Having the bot log in and be online
@client.event
async def on_ready():
    BS_UTILS.set_session(USERNAME, PIN)
    DB_UTILS.connect_by_config("database/db_config.py")
    DB_UTILS.use_database("BSBOT")

    BOT_RESPONSES.set_DB_param(DB_UTILS)
    print("We have logged in as: " + str(client.user))


@commands.command()
async def quit(ctx):
    await ctx.send("Shutting down the bot")
    return await client.logout()  # this just shuts down the bot.


# looping every day
# change parameter to minutes=1 and see it happen every minute
@tasks.loop(hours=1)
async def notification_loop():
    #  Syncing the calendar daily (so it can get the correct changes)
    classes = BS_UTILS.get_classes_enrolled()
    #classes = {"EAPS": "336112"}
    for courseName, courseID in classes.items():
        assignment_list = BS_UTILS._bsapi.get_upcoming_assignments(courseID)
        due = BS_UTILS.process_upcoming_dates(assignment_list)
        if len(due) != 0:
            # actually dates that are upcoming
            cal = Calendar()
            # loop through all the upcoming assignments
            for assignment in due:
                # Check if the event exists first by searching by name
                event_title = f"ASSIGNMENT DUE: {assignment[0]} ({courseID})"
                description = f"{assignment[0]} for {courseName} is due. Don't forget to submit it!"
                search_result, end_time = cal.get_event_from_name(event_title)
                date = datetime.datetime.fromisoformat(assignment[1][:-1])
                end = date.isoformat()
                start = (date - datetime.timedelta(hours=1)).isoformat()
                print("End date from search: " + str(end_time))
                if search_result != -1:
                    # it has already been added to the calendar
                    # see if the end times are different
                    if end_time != end:
                        # the due date has been updated, so delete the old event
                        cal.delete_event(search_result)
                        cal.insert_event(event_title, description, start, end)
                else:
                    # has not been added to calendar, so add normally
                    # inserting event
                    cal.insert_event(event_title, description, start, end)


    print("inserting into calendar is finished...")

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

    # if not SCHEDULED_HOURS:
    #     return

    # print("called_once_a_day:")
    #async def send_notifications():
    # print(datetime.datetime.now().hour)
    message_channel = client.get_channel(channelID)
    dates = BS_UTILS.get_dict_of_discussion_dates()
    # dates = DATES
    string = BS_UTILS.find_upcoming_disc_dates(1, dates)
    string += BS_UTILS.get_notifications_past_24h()

    # Check if the user has a designated text channel for deadline notifications to be sent
    # print("str: ", string)

    # Check if the database has a value for the deadlines text channel

    channel_id = 0
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
        # send the upcoming discussion due dates
        if channel_id != 0:
            send_message_to_channel = client.get_channel(channel_id)
            await send_message_to_channel.send(string)
        else:
            await message_channel.send(string)
    else:
        if len(string) == 0:
            ## only for debugging ##
            string = "No posts today"
        # send the upcoming discussion due dates
        await message_channel.send(string)
    return

    # for s_hour in SCHEDULED_HOURS:
    #     now = datetime.datetime.now()
    #     next_notification = datetime.datetime.combine(now.date(), s_hour)
    #     if next_notification.hour == now.hour and next_notification.minute == now.minute:
    #         await send_notifications()






# TODO: stop notifying immediately after running program.
@notification_loop.before_loop
async def notification_before():
    await client.wait_until_ready()


notification_loop.start()


# This is our input stream for our discord bot
# Every message that comes from the chat server will go through here
@client.event
async def on_message(message):
    global SCHEDULED_HOURS
    # this message will be every single message that enters the server
    # currently saving this info so its easier for us to debug
    BOT_RESPONSES.set_message_param(message)
    BOT_RESPONSES.set_username_param(str(message.author).split('#')[0])
    BOT_RESPONSES.set_channel_param(str(message.channel.name))
    BOT_RESPONSES.print_server_messages()

    username = str(message.author).split('#')[0]
    user_message = str(message.content)
    channel = str(message.channel.name)
    # print(f'{username}: {user_message} ({channel}) ({message.channel.id})')

    # just so that bot does not respond back to itself
    if message.author == client.user:
        return

    # Lets say that we want the bot to only respond to a specific text channel in a server named 'todo'
    if message.channel.name == 'specifics':
        if user_message.lower() == 'im bored':
            await message.channel.send("You should probably study...")
            return

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
        # todo: access database and get the actual value

        # storage_path = DB_UTILS._mysql.general_command("SELECT STORAGE_PATH from USERS WHERE FIRST_NAME = 'Raveena';")
        # if storage_path[0][0] is None:
        #     await message.channel.send('No storage path specified. Type update storage to save something')
        # else:
        #     await message.channel.send(f'Current location: {storage_path[0][0]}')
        # return
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

        print(grades)
        grades = dict(sorted(grades.items(), key=lambda item: item[1]))
        print(grades)
        final_string = "Your grades are: \n"
        for key, value in grades.items():
            final_string = final_string + key.upper() + ": " + value + "\n"

        await message.channel.send(final_string)
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
        await message.channel.send("Authorizing...")
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        await message.channel.send("Retrieving grades...")
        grade_updates = bs_utils.get_grade_updates()
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
                await message.channel.send("Timeout ERROR has occured. Please try the query again.")
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
        def check(msg):
            return msg.author == message.author

        await message.channel.send("What time? (e.g. 09: 12, 10:00, 23:24)")
        try:
            new_time = await client.wait_for('message', check=check)
        except asyncio.TimeoutError:
            await message.channel.send("Timed out.")
            return

        try:
            h = int(new_time.content[:2])
            m = int(new_time.content[3:])

            if h < 0 or h > 23 or m < 0 or m > 59:
                await message.channel.send("Please re-enter your time as the format given.")
                return

            new_hour = datetime.time(h, m, 0)
        except ValueError:
            await message.channel.send("Please re-enter your time as the format given.")
            return

        await message.channel.send(
            f"Do you want to add this time to your schedule, or you want notifications only for this time?")

        try:
            res = await client.wait_for('message', check=check)
        except asyncio.TimeoutError:
            await message.channel.send("Timed out.")
            return

        res = res.content
        add = False
        if "add" in res:
            add = True

        await message.channel.send(f"{new_time.content}, right?")
        try:
            res = await client.wait_for('message', check=check)
        except asyncio.TimeoutError:
            await message.channel.send("Timed out.")
            return

        res = res.content
        if res.startswith("y") or res.startswith("right"):

            if add:
                SCHEDULED_HOURS.append(new_hour)
            else:
                SCHEDULED_HOURS = [new_hour]

            await message.channel.send(f"Changed.")
        else:
            await message.channel.send(f"No changes are made to your schedule.")


    elif message.content.startswith("check notification schedule"):
        if not SCHEDULED_HOURS:
            await message.channel.send("No schedules now!")
        else:
            msg = ""
            for hour in SCHEDULED_HOURS:
                msg += f"{hour}\n"

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
    elif message.content.startswith("course priority"):

        def check(msg):
            return msg.author == message.author

        # list of courses in preferred priority
        course_priority = []

        # ask user for pick grade or by due date
        await message.channel.send("Please pick between grade or due dates for prioritizing your courses.")

        try:
            priority_option = await client.wait_for('message', check=check)

            if priority_option.content.startswith("grade"):
                # api call for grades
                await message.channel.send("Setting course priority by grade ...")

                # get user's enrolled classes
                user_classes = BS_UTILS.get_classes_enrolled()
                class_names = []
                class_ids = []
                grades_tuple = []
                for name, course_id in user_classes.items():
                    class_names.append(name)
                    class_ids.append(course_id)
                    grades_tuple.append(BS_UTILS._bsapi.get_grade(course_id))

                grades_frac = []
                for t in grades_tuple:
                    if not t[0] == '':
                        nums_str = t[0].split('/')
                        grade_frac = float(nums_str[0]) / float(nums_str[1])
                        grades_frac.append(grade_frac)
                    else:
                        grades_frac.append(0)

                # print(class_names)
                # print(grades_frac)

                # class_grade_tracker = []
                # for x in range(0, len(class_names)):
                #   class_grade_tracker.append((grades_frac[x], class_names[x]))

                sorted_grade_frac = sorted(grades_frac)

                # print(sorted_grade_frac)

                for x in sorted_grade_frac:
                    if not x == 0:
                        index = grades_frac.index(x)
                        course_name = class_names[index]
                        course_priority.append(course_name)

                # print(course_priority)

                suggested_course_priority = ""

                for x in range(0, len(course_priority)):
                    suggested_course_priority += course_priority[x]
                    if not x == len(course_priority) - 1:
                        suggested_course_priority += " >> "

                await message.channel.send("The suggested course priority is:\n" + suggested_course_priority)

            elif priority_option.content.startswith("due dates"):
                # api call for due dates
                await message.channel.send("Setting course priority by upcoming due dates ...")
                await message.channel.send("Sorry we are adjusting function at the moment, please try it next time")
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
        #found, list_of_tcs = BOT_RESPONSES.check_if_tc_exists(current_saved_tc, DB_USERNAME)

        sql_command = f"UPDATE PREFERENCES SET {db_category} = '{text_channel}' WHERE USERNAME = '{DB_USERNAME}';"
        DB_UTILS._mysql.general_command(sql_command)
        print(DB_UTILS.show_table_content("PREFERENCES"))

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
                                       + str(current_saved_tc) + " to " + text_channel + ". I will send a message to this "
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
        # Syncing quizzes to the calendar daily (so it can get the correct changes)
        quizzes = BS_UTILS.get_all_upcoming_quizzes()
        for quiz in quizzes:
            cal = Calendar()
            event_title = f"QUIZ DUE: {quiz['quiz_name']} ({quiz['course_id']})"
            description = f"{quiz['quiz_name']} for {quiz['course_name']} is due. Don't forget to submit it!"
            date = datetime.datetime.fromisoformat(quiz['due_date'][:-1])
            end = date.isoformat()
            start = (date - datetime.timedelta(hours=1)).isoformat()
            event_id, end_time = cal.get_event_from_name(event_title)
            # event has already been created in google calendar
            if event_id == -1:
                # insert new event to calendar
                cal.insert_event(event_title, description, start, end)
            # event has not been created
            else:
                # if end time has changed, update the event
                if end_time != end:
                    # await message.channel.send(end_time)
                    # await message.channel.send(end)
                    cal.delete_event(event_id)
                    cal.insert_event(event_title, description, start, end)
                else:
                    await message.channel.send("No new quizzes found.")
        await message.channel.send("Quiz deadlines added/updated to calendar!")
        return

# Now to actually run the bot!
client.run(config['token'])
