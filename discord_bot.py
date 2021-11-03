# Our discord token is saved in another file for security
from discord_config import config, USERNAME, PIN
import discord
from discord.ext import tasks, commands
import asyncio
from file_storage import *
import datetime
import re

from bs_utilities import BSUtilities
import threading
from database.db_utilities import DBUtilities

'''
To add the bot to your own server and test it out, copy this URL into your browser
https://discord.com/api/oauth2/authorize?client_id=894695859567083520&permissions=534723950656&scope=bot
 '''

# This will be our discord client. From here we will get our input
client = discord.Client()
channelID = 663863991218733058  # mine!
# TODO save this in the database - right now this is my (Raveena's) channel

db_config = "./database/db_config.py"
BS_UTILS = BSUtilities()
DB_UTILS = DBUtilities(db_config)

author_id_to_username_map = {}


# Having the bot log in and be online
@client.event
async def on_ready():
    BS_UTILS.set_session(USERNAME, PIN)

    print("We have logged in as: " + str(client.user))


@commands.command()
async def quit(ctx):
    await ctx.send("Shutting down the bot")
    return await client.logout()  # this just shuts down the bot.


# looping every day
# change parameter to minutes=1 and see it happen every minute
@tasks.loop(minutes=1)
async def notification_loop():
    if not SCHEDULED_HOURS:
        return

    # print("called_once_a_day:")
    async def send_notifications():
        # print(datetime.datetime.now().hour)
        message_channel = client.get_channel(channelID)
        dates = BS_UTILS.get_dict_of_discussion_dates()
        # dates = DATES
        string = BS_UTILS.find_upcoming_disc_dates(1, dates)
        string += BS_UTILS.get_notifications_past_24h()

        # print("str: ", string)
        if len(string) == 0:
            ## only for debugging ##
            string = "No posts today"
        # send the upcoming discussion due dates
        await message_channel.send(string)
        return

    for s_hour in SCHEDULED_HOURS:
        now = datetime.datetime.now()
        next_notification = datetime.datetime.combine(now.date(), s_hour)
        if next_notification.hour == now.hour and next_notification.minute == now.minute:
            await send_notifications()


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
    username = str(message.author).split('#')[0]
    user_message = str(message.content)
    channel = str(message.channel.name)
    print(f'{username}: {user_message} ({channel}) ({message.channel.id})')

    # just so that bot does not respond back to itself
    if message.author == client.user:
        return

    # test gate to prevent multiple responses from the bot to the user
    # guild_members = message.guild.members
    # if message.author not in guild_members:
    #    return

    # Lets say that we want the bot to only respond to a specific text channel in a server named 'todo'
    if message.channel.name == 'specifics':
        if user_message.lower() == 'im bored':
            await message.channel.send("You should probably study...")
            return

    # setting up a basic 'hello' command so you get this gist of it
    if user_message.lower() == 'hello':
        # put your custom message here for the bot to output
        # we would incorporate our chat module here and then craft an appropriate response
        await message.channel.send(f'Hello {username}!')
        return
    elif user_message.lower() == 'bye':
        await message.channel.send(f'Bye {username}!')
        return
    # get the current storage path
    elif user_message.lower() == 'current storage location':
        # todo: access database and get the actual value

        storage_path = DB_UTILS._mysql.general_command("SELECT STORAGE_PATH from USERS WHERE FIRST_NAME = 'Raveena';")
        if storage_path[0][0] is None:
            await message.channel.send('No storage path specified. Type update storage to save something')
        else:
            await message.channel.send(f'Current location: {storage_path[0][0]}')
        return

    # update the current storage path (used starts with so they can type update storage destination or path)
    elif message.content.startswith('update storage'):
        await message.channel.send("Google Drive or Local?")

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
                    sql_type = "UPDATE USERS SET Storage_method = '{path_type}' WHERE first_name = '{f_name}';" \
                        .format(path_type="GDRIVE", f_name=username.split(" ")[0])
                    DB_UTILS._mysql.general_command(sql_type)
                    sql_path = "UPDATE USERS SET Storage_path = '{path}' WHERE first_name = '{f_name}';" \
                        .format(path=new_storage.content, f_name=username.split(" ")[0])
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
                    sql_type = "UPDATE USERS SET Storage_method = '{path_type}' WHERE first_name = '{f_name}';" \
                        .format(path_type="LOCAL", f_name=username.split(" ")[0])
                    DB_UTILS._mysql.general_command(sql_type)
                    sql_path = "UPDATE USERS SET Storage_path = '{path}' WHERE first_name = '{f_name}';" \
                        .format(path=new_storage.content, f_name=username.split(" ")[0])
                    DB_UTILS._mysql.general_command(sql_path)
                    await message.channel.send("New path saved")
                return
            except asyncio.TimeoutError:
                await message.channel.send("taking too long...")

        else:
            await message.channel.send("Your input isn't valid")


    # get a grade for a class
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

    # get feedback on assignment.
    elif message.content.startswith("get assignment feedback"):
        await message.channel.send("Please provide the Course name (for ex, NUTR 303) \n")
        def author_check(m):
            return m.author == message.author
        course_name = await client.wait_for('message', check=author_check)
        await message.channel.send("Please provide the full assignment name (for ex, 'Recitation Assignment 1')\n")
        assignment_name = await client.wait_for('message', check=author_check)
        feedback = BS_UTILS.get_assignment_feedback(course_name, assignment_name)
        
        if feedback.__contains__("ERROR") or feedback.__contains__("BOT REPORT"):
            await message.channel.send(feedback)
        else:
            await message.channel.send("Feedback from Grader: \n")
            await message.channel.send(feedback)
        
        return

    #enable the user to search for a specific student in a class.
    elif message.content.startswith("search for student"):
        await message.channel.send("Please provide the course in which you want to search \n")
        def author_check(m):
            return m.author == message.author
        course_name = await client.wait_for('message', check=author_check)
        await message.channel.send("Please provide the full name (First Name + Last Name, e.g 'Shaun Thomas') of the student you would like to search for.\n")
        student_name = await client.wait_for('message', check=author_check)

        course_name_str = str(course_name.content)
        student_name_str = str(student_name.content)

        output = BS_UTILS.search_for_student_in_class(course_name, student_name)

        #if BS_UTILS.search_for_student_in_class(course_name, student_name):
        if output:
            await message.channel.send(student_name_str + " is a student in " + course_name_str)
        else:
            await message.channel.send(student_name_str + " is not a student in " + course_name_str)
        

        #print(course_name)
        #print(student_name)
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
        global SCHEDULED_HOURS

        def check(msg):
            return msg.author == message.author

        async def recieve_response():
            try:
                res = await client.wait_for('message', check=check)
            except asyncio.TimeoutError:
                await message.channel.send("Timed out.")
                return None
            return res

        async def request_username():
            await message.channel.send("What is your username?")
            username = await recieve_response()
            author_id_to_username_map[username.author.id] = username.content

        async def naive_change():

            while True:
                await message.channel.send("What time? (e.g. 09: 12, 10:00, 23:24)")

                new_time = await recieve_response()
                if not new_time:
                    return

                try:
                    h = int(new_time.content[:2])
                    m = int(new_time.content[3:])
                except ValueError:
                    await message.channel.send("Please re-enter your time as the format given.")
                    continue

                if h < 0 or h > 23 or m < 0 or m > 59:
                    await message.channel.send("Please re-enter your time as the format given.")
                    continue

                new_hour = datetime.time(h, m, 0)
                break

            await message.channel.send(
                f"Do you want to add this time to your schedule, or you want notifications only for this time?")
            res = await recieve_response()

            res = res.content
            add = False
            if "add" in res:
                add = True

            await message.channel.send(f"{new_time.content}, right?")
            res = await recieve_response()

            if res.content.startswith("y") or res.content.startswith("right"):
                if res.author.id not in author_id_to_username_map:
                    await request_username()

                if add:
                    print(author_id_to_username_map)
                    DB_UTILS.add_notifictaion_schedule(author_id_to_username_map[res.author.id], new_time.content)
                    # SCHEDULED_HOURS.append(new_hour)
                else:
                    SCHEDULED_HOURS = [new_hour]

                await message.channel.send(f"Schedule changed.")
            else:
                await message.channel.send(f"No changes are made to your schedule.")

        await naive_change()

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
        storage_path = DB_UTILS._mysql.general_command("SELECT STORAGE_PATH from USERS WHERE FIRST_NAME = 'Raveena';")
        storage_type = DB_UTILS._mysql.general_command("SELECT STORAGE_METHOD from USERS WHERE FIRST_NAME = 'Raveena';")
        course_id = BS_UTILS.find_course_id(course)
        if storage_path[0][0] is not None:
            BS_UTILS.download_files(course_id, storage_path[0][0], storage_type[0][0])
            await message.channel.send("Files downloaded successfully!")
            return
        else:
            await message.channel.send("Files not downloaded successfully")
            return

    # returning user course priority by either grade or upcoming events
    elif message.content.startswith("course priority"):

        def check(msg):
            return msg.author == message.author

        # ask user for pick grade or by due date
        await message.channel.send("Please pick between grade or due dates for prioritizing your courses.")

        try:
            priority_option = await client.wait_for('message', check=check)

            if priority_option.content.startswith("grade"):
                # api call for grades
                await message.channel.send("Setting course priority by grade ...")

                priority = BS_UTILS.get_sorted_grades()[0]
                missing = BS_UTILS.get_sorted_grades()[1]

                suggested_course_priority = ""
                for x in range(0, len(priority)):
                    suggested_course_priority += priority[x]
                    if not x == len(priority) - 1:
                        suggested_course_priority += " >> "

                found_missing_grade_courses = ""
                for x in range(0, len(missing)):
                    found_missing_grade_courses += missing[x]
                    if not x == len(missing) - 1:
                        found_missing_grade_courses += " , "

                await message.channel.send("The suggested course priority is:\n" + suggested_course_priority)
                await message.channel.send("There are some courses that miss final grades:\n"
                                           + found_missing_grade_courses)

            elif priority_option.content.startswith("due dates"):
                # api call for due dates
                await message.channel.send("Setting course priority by upcoming due dates ...")

                due_dates = BS_UTILS.get_course_by_duedate()

                await message.channel.send("Sorry we are adjusting function at the moment, please try it next time")
            else:
                await message.channel.send("Invalid response given! Please try the query again.")
                return

        except asyncio.TimeoutError:
            await message.channel.send("Timeout ERROR has occurred. Please try the query again.")
            return

        return

    elif message.content.startswith("course link"):
        # get user course urls in advance
        user_course_urls = BS_UTILS.get_course_url()

        # bot asks user for specific input
        await message.channel.send("Which course link do you need? Type \'All\' or specific course links")
        await message.channel.send("ex) CS 180,CS 240 or All")
        reply_back = ""
        cannot_find_courses = ""

        # check function for client.wait_for
        def check(msg):
            return msg.author == message.author

        try:
            # get user reply back
            user_reply = await client.wait_for('message', check=check, timeout=60)

            # different user_request options
            # 'All'
            if user_reply.content.startswith("All"):
                reply_back += "The followings are the links to course homepages\n"
                for course_name, course_url in user_course_urls.items():
                    reply_back += "{course_name}: {url}\n".format(course_name=course_name,
                                                                url=course_url)
            else:
                user_requests = user_reply.content.split(",")
                for requested_course in user_requests:
                    for course_name, course_url in user_course_urls.items():
                        if requested_course in course_name:
                            reply_back += "{course_name}: {url}\n".format(course_name=course_name,
                                                                url=course_url)
                        continue
                    if requested_course not in reply_back:
                        cannot_find_courses += "{course_name}\t".format(course_name=requested_course)

            # send the reply back
            if not reply_back == "":
                await message.channel.send(reply_back)
                if not cannot_find_courses == "":
                    await message.channel.send("These are courses that I couldn't find:")
                    await message.channel.send(cannot_find_courses)
            else:
                await message.channel.send("Sorry, we couldn't find the matching courses.")
                await message.channel.send("Please check if they are valid courses.")

                # home page vary by campus location
                # West Lafayette: 6824
                # Fort Wayne: 6822
                # Northwest: 6823
                await message.channel.send("Here is the home page default link: https://purdue.brightspace.com/d2l/home")
                # user_info = BS_UTILS._bsapi.get_user_info()
                # print(user_info)
                return

        except asyncio.TimeoutError:
            await message.channel.send("Timeout ERROR has occurred. Please try the query again.")
        return

# Now to actually run the bot!
client.run(config['token'])
