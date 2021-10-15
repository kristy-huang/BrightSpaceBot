# Our discord token is saved in another file for security
from discord_config import config, USERNAME, PIN, DATES
import discord
from discord.ext import tasks
import asyncio
from file_storage import *
from bs_api import BSAPI
from bs_utilities import BSUtilities
from datetime import datetime, timedelta
import threading
from database.db_utilities import DBUtilities


'''
To add the bot to your own server and test it out, copy this URL into your browser
https://discord.com/api/oauth2/authorize?client_id=894695859567083520&permissions=534723950656&scope=bot
 '''

# This will be our discord client. From here we will get our input
client = discord.Client()
channelID = 894700985535058000  # TODO save this in the database - right now this is my (Raveena's) channel
BS_UTILS = BSUtilities()
BS_API = BSAPI()
DB_UTILS = DBUtilities()


# Having the bot log in and be online
@client.event
async def on_ready():
    BS_UTILS.set_session(USERNAME, PIN)
    DB_UTILS.connect_by_config("database/db_config.py")
    print("We have logged in as: " + str(client.user))


SCHEDULED_MINUTES = 1 * 60 * 24
# looping every day
# change parameter to minutes=1 and see it happen every minute
@tasks.loop(minutes=SCHEDULED_MINUTES)
async def called_once_a_day():
    channel = discord.utils.get(client.get_all_channels(), name='specifics')
    message_channel = client.get_channel(channel.id)
    #dates = BS_UTILS.get_dict_of_discussion_dates()
    dates = DATES
    string = BS_UTILS.find_upcoming_disc_dates(1, dates)
    if len(string) == 0:
        ## only for debugging ##
        # string = "No posts due today"
        return
    # send the upcoming discussion due dates
    await message_channel.send(string)
    return


@called_once_a_day.before_loop
async def before():
    await client.wait_until_ready()


called_once_a_day.start()

# This is our input stream for our discord bot
# Every message that comes from the chat server will go through here
@client.event
async def on_message(message):
    # this message will be every single message that enters the server
    # currently saving this info so its easier for us to debug
    username = str(message.author).split('#')[0]
    user_message = str(message.content)
    channel = str(message.channel.name)
    print(f'{username}: {user_message} ({channel})')

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
        await message.channel.send(f'Hello {username}!')
        return
    elif user_message.lower() == 'bye':
        await message.channel.send(f'Bye {username}!')
        return
    # get the current storage path
    elif user_message.lower() == 'current storage location':
        # todo: access database and get the actual value
        storage_path = "Some/default/location"
        await message.channel.send(f'Your current storage location: {storage_path}')
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
                fraction_string, percentage_string = BS_UTILS._bsapi.get_grade(i)
                if len(fraction_string) == 1 or len(percentage_string) == 0:
                    grades[courses[counter]] = 'Not found'
                else:
                    letter = BS_UTILS.get_letter_grade(int(percentage_string.split(" ")[0]))
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

    #get upcoming quizzes across all classes
    elif message.content.startswith("get upcoming quizzes"):
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        upcoming_quizzes = bs_utils.get_upcoming_quizzes()
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
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        grade_updates = bs_utils.get_grade_updates()
        await message.channel.send("Retrieving grades...")
        # if there are no grade updates returned, then we report to the user.
        if len(grade_updates) == 0:
            await message.channel.send("You have no new grade updates.")
            return
        else:
            await message.channel.send("The following assignments have been graded:\n")
            for grade in grade_updates:
                output_str = "Course Id:" + str(grade['course_id']) + "- " + grade['assignment_name'] + " " + grade['grade'] + "\n"
                await message.channel.send(output_str)
       
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
        # dates = DATES ONLY FOR DEBUG
        def check(msg):
            return msg.author == message.author

        # find discussion post deadline for 2 weeks
        string = BS_UTILS.find_upcoming_disc_dates(14, dates)

        if len(string) == 0:
            await message.channel.send("No upcoming posts for the next two weeks. Would you like to look further than 2 weeks?")
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

                #class_grade_tracker = []
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

                for x in range (0, len(course_priority)):
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
          
# Now to actually run the bot!
client.run(config['token'])
