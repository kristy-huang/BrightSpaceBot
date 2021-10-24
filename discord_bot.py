# Our discord token is saved in another file for security
from discord.errors import NotFound
from discord_config import config, USERNAME, PIN
import discord
from discord.ext import tasks, commands
import asyncio
from file_storage import *
import datetime
import threading

from bs_utilities import BSUtilities
import threading
from database.db_utilities import DBUtilities


'''
To add the bot to your own server and test it out, copy this URL into your browser
https://discord.com/api/oauth2/authorize?client_id=894695859567083520&permissions=534723950656&scope=bot
 '''

# This will be our discord client. From here we will get our input
client = discord.Client()
channelID = 663863991218733058 #mine!
  # TODO save this in the database - right now this is my (Raveena's) channel

db_config = "./database/db_config.py"
#BS_UTILS = BSUtilities()
DB_UTILS = DBUtilities(db_config)

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
    BS_UTILS.set_session(USERNAME, PIN)

    print("We have logged in as: " + str(client.user))
  
@commands.command()
async def quit(ctx):
    await ctx.send("Shutting down the bot")
    return await client.logout() # this just shuts down the bot.

# looping every day
# change parameter to minutes=1 and see it happen every minute
@tasks.loop(minutes=1)
async def notification_loop():
    #print("called_once_a_day:")
    async def send_notifications():
        #print(datetime.datetime.now().hour)
        message_channel = client.get_channel(channelID)
        dates = BS_UTILS.get_dict_of_discussion_dates()
        #dates = DATES
        string = BS_UTILS.find_upcoming_disc_dates(1, dates)
        string += BS_UTILS.get_notifications_past_24h()

        #print("str: ", string)
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


    # this message will be every single message that enters the server
    # currently saving this info so its easier for us to debug
    username = str(message.author).split('#')[0]
    user_message = str(message.content)
    channel = str(message.channel.name)
    print(f'{username}: {user_message} ({channel}) ({message.channel.id})')

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

    #get upcoming quizzes across all classes
    elif message.content.startswith("get upcoming quizzes"):
        upcoming_quizzes = BS_UTILS.get_upcoming_quizzes()
        #if there are no upcoming quizzes returned, then we report to the user.
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
                output_str = "Course Id:" + str(grade['course_id']) + "- " + grade['assignment_name'] + " " + grade['grade'] + "\n"
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
        #dates = DATES #ONLY FOR DEBUG
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
    
    elif message.content.startswith("update schedule"):

        if message.author.id not in author_id_to_username_map:
            await request_username()
   
        async def everyday():
            new_time = None
            while not new_time:
                new_time = await get_time()


            await message.channel.send(f"{new_time.content}, right?")
            res = await recieve_response()

            if res.content.startswith("y") or res.content.startswith("right"):
                DB_UTILS.add_notifictaion_schedule(author_id_to_username_map[res.author.id], new_time.content, 1 * 24 * 60, res.channel.id, description=7) # 7 = everyday
                #SCHEDULED_HOURS.append(new_hour)
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
                DB_UTILS.add_notifictaion_schedule(author_id_to_username_map[res.author.id], new_time.content, 1 * 24 * 7 * 60, res.channel.id, description=day)
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
            s_times = DB_UTILS.get_notifictaion_schedule_with_description(author_id_to_username_map[message.author.id])
            
            await message.channel.send("How many schedules do you want?")
            res = await recieve_response()

            try:
                freq = int(res.content)
            except ValueError:
                await message.channel.send("Please enter a number")

            curr_len = len(s_times)
            if curr_len < freq:
                await message.channel.send(f"There are currently {len(s_times)} schedules. Do you want to add more?")
                
                res = await recieve_response()
                if res.content.startswith("y") or res.content.startswith("right"):
                    while curr_len < freq:
                        await add_week_or_everyday()
                        curr_len += 1
                        await message.channel.send(f"Do you want to add more?")
                        res = await recieve_response()
                        if res.content.startswith("y") or res.content.startswith("right"):
                            continue
                        break
            else:
                await message.channel.send(f"There are currently more than {freq} scheduled times.")
                

        async def by_class_schedule():
            pass


        await by_amount()

        
    elif message.content.startswith("delete noti"):     
        if message.author.id not in author_id_to_username_map:
            await request_username()

        current_times = DB_UTILS.get_notifictaion_schedule_with_description(author_id_to_username_map[message.author.id])
        
        if not current_times:
            await message.channel.send("You don't have any scheduled times now.")
            return


        async def delete_all():
            await message.channel.send("Are you sure to delete all of your scheduled times?")

            res = await recieve_response()
            if res.content.startswith("y") or res.content.startswith("right"):
                DB_UTILS.clear_notification_schedule(author_id_to_username_map[message.author.id])
                await message.channel.send("Schedule deleted")
            else:
                await message.channel.send(f"No changes are made to your schedule.")
    
        async def delete_some():
            msg = ""
            for i, time in enumerate(current_times):
                msg += f"{i + 1}: {time[0]} {time[1]}\n"
                
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
            await message.channel.send(f"Delete time: {current_times[num][0]} {current_times[num][1]}?")
            
            res = await recieve_response()

            if res.content.startswith("y") or res.content.startswith("right"):
                DB_UTILS.delete_notification_schedule(author_id_to_username_map[message.author.id], current_times[num][0], current_times[num][1])
                
                await message.channel.send("Schedule deleted")
            else:
                await message.channel.send(f"No changes are made to your schedule.")
    
        await delete_some() 
    
    
    elif message.content.startswith("check noti"):
        if message.author.id not in author_id_to_username_map:
            await request_username()

        s_times = DB_UTILS.get_notifictaion_schedule_with_description(author_id_to_username_map[message.author.id])
        if not s_times:
            await message.channel.send("No schedules now!")
        else:
            msg = f"Scheduled times for {author_id_to_username_map[message.author.id]}:\n"
            for hour in s_times:
                msg += f"{hour[0]} {NOT_FREQ_MAP[int(hour[1])].lower()}\n"
                
            await message.channel.send(msg)


    elif message.content.startswith("update class"):
        if message.author.id not in author_id_to_username_map:
            await request_username()

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
                    DB_UTILS.add_class_schedule(author_id_to_username_map[res.author.id], class_name, new_time.content, description=day)
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
            await request_username()

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
