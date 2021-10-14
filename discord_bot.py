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

'''
To add the bot to your own server and test it out, copy this URL into your browser
https://discord.com/api/oauth2/authorize?client_id=894695859567083520&permissions=534723950656&scope=bot
 '''

# This will be our discord client. From here we will get our input
client = discord.Client()
channelID = 894700985535058000  # TODO save this in the database - right now this is my (Raveena's) channel
BS_UTILS = BSUtilities()
BS_API = BSAPI()

# Having the bot log in and be online
@client.event
async def on_ready():
    BS_UTILS.set_session(USERNAME, PIN)
    print("We have logged in as: " + str(client.user))

# looping every day
# change parameter to minutes=1 and see it happen every minute
@tasks.loop(hours=24)
async def called_once_a_day():
    message_channel = client.get_channel(894700985535058000)
    dates = BS_UTILS.get_dict_of_discussion_dates()
    #dates = DATES
    string = BS_UTILS.find_upcoming_disc_dates(1, dates)
    if len(string) == 0:
        ## only for debugging ##
        # string = "No posts due today"
        return
    # send the upcoming discussion due dates
    await message_channel.send(string)


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
            path_type = await client.wait_for('message', check=storage_path, timeout=5.0)
        except asyncio.TimeoutError:
            await message.channel.send("taking too long...")
            return

        # checking what type of path they are going to save it in
        if path_type.content == "google drive":
            await message.channel.send("What folder from root?")
            # checking to see if path is valid
            try:
                new_storage = await client.wait_for('message', check=storage_path, timeout=10)
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
                new_storage = await client.wait_for('message', check=storage_path, timeout=10)
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
    elif message.content.startswith("get grade"):
        # TODO make it so that student can just put the course name
        await message.channel.send("What is the course ID?")

        def check_input(m):
            return m.author == message.author
        # getting the course ID
        try:
            courseID = await client.wait_for('message', check=check_input, timeout=5.0)
        except asyncio.TimeoutError:
            await message.channel.send("taking too long...")
            return
        bs = BSAPI()
        bs.set_session(USERNAME, PIN)
        fraction_string, percentage_string = bs.get_grade(courseID.content)
        bs_utils = BSUtilities()
        letter = bs_utils.get_letter_grade(int(percentage_string.split(" ")[0]))
        final_string = "Your overall fraction for that class is: " + fraction_string + \
                       "\nYour percentage is: " + percentage_string + ". That translate to a " + letter
        await message.channel.send(final_string)
        return

    #get upcoming quizzes across all classes
    elif message.content.startswith("get upcoming quizzes"):
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
        upcoming_quizzes = bs_utils.get_upcoming_quizzes()
        #if there are no upcoming quizzes returned, then we report to the user.
        if not upcoming_quizzes:
            await message.channel.send("You have no upcoming quizzes or exams.")
            return
        else:
            await message.channel.send("You have the following upcoming assessments:\n")
            for quiz in upcoming_quizzes:
                current_quiz = quiz["Name"]
                current_quiz_due_date = quiz["DueDate"]
                output_str = current_quiz + " due " + current_quiz_due_date + "\n"
                await message.channel.send(output_str)
            return

    elif message.content.startswith("get busiest weeks"):
        bs_utils = BSUtilities()
        bs_utils.set_session(USERNAME, PIN)
       
    #changing bot name
    elif message.content.startswith("change bot name"):
        # change value used to check if the user keep wants to change the name of the bot
        # initialized to True
        change=True;

        # check method for waiting client's reply back
        def check(msg):
            return msg.author == message.author

        while(change):
            # ask the user to which name they want to change
            await message.channel.send("To which name do you want to change?")

            # get reply back from the user for bot's name
            try:
                new_name=await client.wait_for('message', check=check);
            except asyncio.TimeoutError:
                await message.channel.send("Timeout ERROR has occured. Please try the query again.")
                return

            # name changed
            await message.guild.me.edit(nick=new_name.content)
            await message.channel.send("My name is now changed!")

            # ask if the user wants to change the name again
            await message.channel.send("Would you like to change my name again? Yes/y or No/n")

            # get reply back from the user if they want to change the bot name again.
            try:
                change_again=await client.wait_for('message', check=check);

                # user does not want to change again
                if change_again.content.lower.startswith('n'):
                    change = False
                elif not change_again.content.lower.startswith('y'):    # user input invalid response
                    await message.channel.send("Invalid response given! Please try the query again.")
            except asyncio.TimeoutError:
                await message.channel.send("Timeout ERROR has occured. Please try the query again.")
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


# Now to actually run the bot!
client.run(config['token'])
