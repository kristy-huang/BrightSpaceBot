
import asyncio
from ctypes import c_longdouble
import datetime
from urllib.parse import scheme_chars
from discord.ext.commands.converter import clean_content
from discord.ext.commands.errors import UserNotFound
from requests.models import Response
from werkzeug.security import check_password_hash
import discord

from thefuzz import fuzz
from thefuzz import process

from bs_utilities import BSUtilities
from bs_calendar import Calendar
from Authentication import setup_automation
from file_storage import validate_path_local
from bot_responses import BotResponses

# A class to parse user commands, and run matching functionalities.
#
# Developer instructions:
# To show debug information: 
#   set debug=True when initializing an NLPAction object
# To add a command / function match:
#   1. Implement a function in the NLPAction class. The interface should be:
#      await def <function name>(self, message, client)
#   2. Add the mapping from a command to the function in self.PHRASES in __init__,
#      in the format of "command": (function, needs_to_login). Please see __init__ for some examples.
# To decide yes or no:
#   use function self._decide_yes_or_no(message)


class NLPAction():
    
    # Paramerters:
    # DB_UTIL: DBUtilities object. Needs to be connected to a database.
    # debug: bool. Shows debug messages if set to true. 

    def __init__(self, DB_UTIL, debug = False):

        # "command" for each functionality.
        # if the 2nd entry is false, it means the user does not need to login to 
        # brightspace / the bot to use this function. e.g. saying hello

        self.PHRASES = {
        "hello": (self._say_hello, False),
        "hi": (self._say_hello, False),
        "bye": (self._say_good_bye, False),
        "change bot name": (self._change_bot_name, False),
        "change your name": (self._change_bot_name, False),
        #"switch bot account": ("switch", False), # Does not work and I don't want to fix it
        "search for student": (self._search_for_student, True),
        "current storage location": (self._current_storage, True),
        "check storage": (self._current_storage, True),
        "grades": (self._grades, True),
        "get assignment feedback": (self._get_assignment_feedback, True),
        "get upcoming quizzes": (self._get_upcoming_quizzes, True),
        "get newly graded assignments": (self._get_newly_graded_assignments, True),
        "get upcoming discussion": (self._get_upcoming_discussion, True),
        "update notification schedule": (self._update_notification_schedule, True),
        "add notification schedule": (self._update_notification_schedule, True),
        "delete notification schedule": (self._delete_notification_schedule, True),
        "check notification schedule": (self._check_nofication_schedule, True),
        "get notification schedule": (self._check_nofication_schedule, True),
        "update class schedule": (self._update_class_schedule, True),
        "add class schedule": (self._update_class_schedule, True),
        "check class schedule": (self._check_class_schedule, True),
        "get class schedule": (self._check_class_schedule, True),
        "update download schedule": (self._update_download_schedule, True),
        "add download schedule": (self._update_download_schedule, True),
        "check download schedule": (self._check_download_schedule, True),
        "get download schedule": (self._check_download_schedule, True),
        "delete download schedule": (self._delete_download_schedule, True),
        "download files": (self._download_files_asking, True),
        "update storage": (self._update_storage, True),
        "delete download schedule": (self._delete_download_schedule, True),
        "get course priority": (self._get_course_priority, True),
        "overall points": (self._overall_points, True),
        "overall grades": (self._overall_points, True),
        "get overall points": (self._overall_points, True),
        "get overall grades": (self._overall_points, True),
        "redirect notifications": (self._redirect_notifications, True),
        "notification location": (self._notification_location, True),
        "add quiz due dates to calendar": (self._add_quiz_due_dates_to_calendar, True),
        "get course link": (self._get_course_link, True),
        "get upcoming assignments": (self._get_upcoming_assignments, True),
        "suggest course study": (self._suggest_course_study, True),
        "add office hours to calendar": (self._add_office_hours_to_calendar, True),
        "rename file": (self._rename_file, True),
        "add discussion schedule": (self._add_discussion_schedule, True),
        "check discussion schedule": (self._check_discussion_schedule, True),
        # "archive": (self._archive, True), # Only works on one machine
        "check update section": (self._check_update_section, True),
        "configuration setting": (self._configuration_setting, True),
        "login": (self._login_empty, True)
        }

        # 1 = yes, 0 = no
        self.YES_NO_PHRASES = {
            "yes": 1, 
            "true":1,
            "yup": 1,
            "yeah": 1,
            "right": 1,
            "correct": 1,
            "no": 0,
            "false": 0,
            "nope": 0
        }

        self._NOT_FREQ_MAP = {
            0: "EVERY MONDAY",
            1: "EVERY TUESDAY",
            2: "EVERY WEDNSDAY",
            3: "EVERY THURSDAY",
            4: "EVERY FRIDAY",
            5: "EVERY SATURDAY",
            6: "EVERY SUNDAY",
            7: "EVERYDAY"
        }

        # maps an user's discord user id to an username. (The username used as a key in db) 
        self._id_to_username_map = {}
        # maps an user's discord user id to a bsutility object
        self._id_to_bsu_map = {}

        self._DB_UTIL = DB_UTIL
        self._br = BotResponses()

        # one lock per user! -> only 1 command will be processed each time 
        # (to prevent calling other functions when the bot is processing one function)
        self._locks = {}

        self._debug = debug
        
    
    # Identifies what the user wants to do from an incoming message, and call 
    # functions that can solve their porblems.
    # 
    # message: the message object recieved from the user. (Not a string)
    # client: the client object

    async def process_command(self, message, client):

        # ---- to prevent calling multiple functions -----
        
        if message.author.id not in self._locks:
            if self._debug:
                print(f"Added new lock: {message.author}")
            self._locks[message.author.id] = False

        if self._debug:
            print("Incoming message: ", message.content, "author: ", message.author, " Locked: ", self._locks[message.author.id])

        if self._locks[message.author.id]:
            '''if self._debug:
                print("Locked. abort.")'''
            return

        self._locks[message.author.id] = True 

        # ---- to prevent bot calling itself -----

        if self._author_check(message, client):
            '''if self._debug:
                print("Message is from the bot it self. Abort. ")'''
                #print(f"message author: {message.author}. client author: {client.user}")
            self._locks[message.author.id] = False
            return

        # ---- functionalities that does not require the user to login -----

        # (matched string, confidency (out of 100))
        action_tuple = process.extractOne(message.content, self.PHRASES.keys(), scorer=fuzz.token_set_ratio)
        if action_tuple[1] < 50:
            if self._debug:
                print("Confidency lower than 50%. Abort.")
            
            await message.channel.send("I am not sure what you are talking about.")

            self._locks[message.author.id] = False
            return 

        if not self.PHRASES[action_tuple[0]][1]:

            # Special case: user wants to switch his/her account
            if self.PHRASES[action_tuple[0]][0] == "switch":
                res = await self._request_bot_username_password(message, client)
                if not res:
                    await message.channel.send("Bot login failed. Please check your credentials!")
            else:
                await self.PHRASES[action_tuple[0]][0](message, client)
            self._locks[message.author.id] = False
            return

        # ---- to setup the bot account and login -----

        status = await self._request_bot_username_password_if_necessary(message, client)
        if not status:
            await message.channel.send("Bot login failed. Please check your credentials!")
            self._locks[message.author.id] = False
            return

        status = await self._setup_auto_if_necessary(message, client)
        
        if not status:
            await message.channel.send("Bot login failed. Please check your credentials!")
            self._locks[message.author.id] = False
            return

        # Run the corresponding function!
        try:
            await self.PHRASES[action_tuple[0]][0](message, client)
        except Exception as e:
            self._locks[message.author.id] = False
            await message.channel.send("Some sort of error happened in my brain. Sorry, my bad! UWU")
            
            if self._debug:
                print(e)


        if self._debug:
            print("--- reached the end of process request. Will be unlocking ---")
        self._locks[message.author.id] = False


    # ----- Helpers -----

    # Returns true if the message is same as the "client" -> The bot?
    def _author_check(self, message, client):
        return message.author == client.user


    def _get_username_from_message(self, message):
        return str(message.author).split('#')[0]


    # Decides if the user is saying yes or no. Returns true if the user is saying yes,
    # and no if the user is saying no.
    #
    # yes_no_message: a message object. Not a string!

    def _decide_yes_or_no(self, yes_no_message):
        yes_no_tuple = process.extractOne(yes_no_message.content, self.YES_NO_PHRASES.keys(), scorer=fuzz.token_set_ratio)
        return self.YES_NO_PHRASES[yes_no_tuple[0]]


    # Decides if the user onput is closer to <option1> or <option2>
    #
    # options2 (list of str): possible commands to decide which one the input is closer. 
    # user_command (str): user input
    # returns: (int) the index of the closest response. if Confidentiality is lower 
    #          than 50, -1 is returned.
    
    def _get_closer_response(self, options, user_command):
        tup = process.extractOne(user_command, options, scorer=fuzz.token_set_ratio)
        #print(tup)
        if tup[1] < 50:
            return -1
        return options.index(tup[0])
        
        

    # waits for a respond from the user(s)
    # Returns: a response object

    async def _recieve_response(self, message, client):
        def check(msg):
            return msg.author == message.author

        try:
            res = await client.wait_for('message', check=check)
        except asyncio.TimeoutError:
            await message.channel.send("Timed out.")
            return None
        return res


    # Asks the user to input a time and returns a response object
    # if the entered time is legit.
    #
    # message: a message object from discord!
    async def get_time(self, message, client):
        await message.channel.send("What time? (e.g. 09: 12, 10:00, 23:24)")

        new_time = await self._recieve_response(message, client)
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


    # Returns an int representing the entered weekday.
    # returns -1 if not matched to any of the weekdays.
    #
    # msg: str

    async def get_weekday(self, msg):
        msg = msg.lower()

        weekdays = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6
        }

        option = process.extractOne(msg, weekdays.keys(), scorer=fuzz.token_set_ratio)
        if option[1] > 50:
            print("weekday returned ", weekdays[option[0]])
            return weekdays[option[0]]
        return -1


    def parse_time(string):
        time = datetime.datetime.strptime(string, "%H:%M")
        return time


    def time_to_string(time):
        time_str = datetime.datetime.strftime("%H:%M")
        return time_str


    # ----- Login to discord bot & BrightSpace Functions -----


    # Maps the current user's id to an username. Also sets up a login lock.
    # Returns True when login succeeds, False when fails. 
    # Currently only has the case when succeeds. 

    async def _request_bot_username_password(self, message, client):
        #print("_request_bot_username_password")
        await message.channel.send("Please enter your username for the bot. If you do not have an account yet, please visit https://brightspace-bot.herokuapp.com// to register an account. ")
        username = await self._recieve_response(message, client)
        name_pass = self._DB_UTIL.get_username_password(username.content)
        if not name_pass or not name_pass[0][0]:
            return False

        await message.channel.send("Please enter your password for the bot.")
        password = await self._recieve_response(message, client)
        if self._check_discord_bot_password(password.content, name_pass[0][1]):
            self._id_to_username_map[username.author.id] = username.content

            return True
        return False


    # checks if <password> equals a hashed password. 
    def _check_discord_bot_password(self, password, pass_hashed):
        if self._debug:
            print("_check_discord_bot_password:", password, pass_hashed)
        if not password:
            return False
        return check_password_hash(pass_hashed, password)


    # Returns True if the login success or does not need to login 
    async def _request_bot_username_password_if_necessary(self, message, client):
        if message.author.id not in self._id_to_username_map:
            return await self._request_bot_username_password(message, client)
        elif self._id_to_username_map[message.author.id] == "":
            return await self._request_bot_username_password(message, client)
        return True


    async def _login_if_necessary(self, message, bsu):
        if bsu.check_connection():
            return True

        if message:
            await message.channel.send("Logging into BrightSpace...")
        bsu.set_session_auto(self._DB_UTIL, self._id_to_username_map[message.author.id])
        if not bsu.check_connection():
            if message:
                await message.channel.send("BrightSpace login failed. please check your cridentials!")
            return False

        return True


    async def _setup_auto_if_necessary(self, message, client):
        user_id = message.author.id
        if user_id in self._id_to_bsu_map and self._id_to_bsu_map[user_id]:
            return True


        db_res = self._DB_UTIL.get_bs_username_pin(self._id_to_username_map[message.author.id])
        if not db_res or not db_res[0][0]:
            await message.channel.send(f"Seems like your username: {self._id_to_username_map[user_id]} is not connected to BrightSpace yet! Do you want to connect your account to BirghtSpace, or switch an account?\n")
            res = await self._recieve_response(message, client)

            option = self._get_closer_response(["connect account", "switch account"], res.content)
            if option == 1:
                status = await self._request_bot_username_password(message, client)
                if not status:
                    await message.channel.send("Login failed, please check your credentials.")
                    return
                db_res = self._DB_UTIL.get_bs_username_pin(self._id_to_username_map[message.author.id])
                if db_res and db_res[0][0]:
                    bsu = BSUtilities()
                    if await self._login_if_necessary(message, bsu):
                        self._id_to_bsu_map[message.author.id] = bsu
                        return True

            await message.channel.send("please get a boilerkey url and send it to me.")
            res = await self._recieve_response(message, client)
            url = res.content
            await message.channel.send("bs username")
            res = await self._recieve_response(message, client)
            bs_username = res.content
            await message.channel.send("bs 4 digit pin")
            res = await self._recieve_response(message, client)
            bs_pin = res.content
            status = setup_automation(self._DB_UTIL, self._id_to_username_map[message.author.id], bs_username, bs_pin, url )

            db_res = self._DB_UTIL.get_bs_username_pin(self._id_to_username_map[message.author.id])
            if not db_res or not db_res[0][0]:
                await message.channel.send("BrightSpace setup failed. please check your cridentials!")
                return False

        # Login

        bsu = BSUtilities()
        if await self._login_if_necessary(message, bsu):
            self._id_to_bsu_map[message.author.id] = bsu
            return True
        return False
        
        
    async def _login_to_bs_if_necessary(self, message, client):
        user_id = message.author.id
        if user_id not in self._id_to_bsu_map:
            if self._debug:
                print("Why is the program trying to login to bs before a bsu object is created?")

            return False
        
        user_bsu = self._id_to_bsu_map[user_id]
        try:
            while not user_bsu.check_connection():
                user_bsu.set_session_auto(self._DB_UTIL, self._id_to_username_map[user_id])
        except asyncio.TimeoutError:
            print(f"Login to bs: timed out. User: {self._id_to_username_map[user_id]}")
    
    

    # ----- functionalities -----


    async def _say_hello(self, message, client):
        if self._debug:
            print("Say hello - start of function")

        username = self._get_username_from_message(message)
        await message.channel.send(f'Hello {username}!')


    async def _say_good_bye(self, message, client):
        if self._debug:
            print("Say good bye - start of function")

        username = self._get_username_from_message(message)
        await message.channel.send(f'Bye {username}!')


    async def _change_bot_name(self, message, client):
        # change value used to check if the user keep wants to change the name of the bot
        # initialized to True

        change = True
        valid_change_response = True


        while change:
            # ask the user to which name they want to change
            await message.channel.send("To which name do you want to change?")

            response = await self._recieve_response(message, client)

            # name changed message.
            await message.guild.me.edit(nick=response.content)
            await message.channel.send("My name is now changed!")

            # ask if the user wants to change the name again
            await message.channel.send("Would you like to change my name again? Yes or No")

            # get reply back from the user if they want to change the bot name again.
            change_again = await self._recieve_response(message, client)


                # user does not want to change again
            if not self._decide_yes_or_no(change_again):
                change = False
                await message.channel.send("Thank you for changing my name!")
            

    async def _search_for_student(self, message, client):
        await message.channel.send("Please provide the course in which you want to search \n")

        course_name = await self._recieve_response(message, client)
        await message.channel.send(
            "Please provide the full name (First Name + Last Name, e.g 'Shaun Thomas') of the student you would like to search for.\n")
        
        student_name = await self._recieve_response(message, client)

        course_name_str = str(course_name.content)
        student_name_str = str(student_name.content)

        user_id = message.author.id
        curr_bs_util = self._id_to_bsu_map[user_id]
        output = curr_bs_util.search_for_student_in_class(course_name_str, student_name_str)

        if output:
            await message.channel.send(student_name_str + " is a student in " + course_name_str)
        elif output == False:
            course_id = curr_bs_util.find_course_ID(course_name_str)
            if course_id is None:
                await message.channel.send(
                    "ERROR: Please make sure the course you have specified is spelled correctly and is a course that you are currently enrolled in.")
            else:
                await message.channel.send(student_name_str + " is not a student in " + course_name_str)

        return
    

    async def _current_storage(self, message, client):
        username = self._id_to_username_map[message.author.id]
        sql = f'SELECT STORAGE_PATH from PREFERENCES WHERE USERNAME = \'{username}\';'
        storage_path = self._DB_UTIL._mysql.general_command(sql)
        if not storage_path or not storage_path[0][0]:
            await message.channel.send('No storage path specified. Type update storage to save something')
        else:
            await message.channel.send(f'Current location: {storage_path[0][0]}')


    async def _grades(self, message, client):

        curr_bs_util = self._id_to_bsu_map[message.author.id]

        await message.channel.send("Please enter the courses you want to check with a comma. \n (e.g. cs180,cs182)")
        
        res = await self._recieve_response(message, client)
        courses = res.content.strip().split(",")

        IDs = []
        print("Courses:", courses)
        for c in courses:
            course_id = curr_bs_util.find_course_ID(c)
            IDs.append(course_id)

        grades = {}
        counter = 0
        for i in IDs:
            if i == -1:
                grades[courses[counter]] = 'Not found'
            else:
                fraction_string, percentage = curr_bs_util._bsapi.get_grade(i)
                #print(fraction_string)
                #print(percentage)
                if len(fraction_string) <= 1:
                    yourTotal, classTotal = curr_bs_util.sum_total_points(i)
                    if classTotal == 0:
                        grades[courses[counter]] = 'Not found'
                    else:
                        percentage = (yourTotal / classTotal) * 100
                        letter = curr_bs_util.get_letter_grade(percentage)
                        grades[courses[counter]] = letter
                else:
                    letter = curr_bs_util.get_letter_grade(percentage)
                    grades[courses[counter]] = letter
            counter = counter + 1

        # print(grades)
        grades = dict(sorted(grades.items(), key=lambda item: item[1]))
        # print(grades)
        final_string = "Your grades are: \n"
        for key, value in grades.items():
            final_string = final_string + key.upper() + ": " + value + "\n"

        await message.channel.send(final_string)


    async def _get_assignment_feedback(self, message, client):
        await message.channel.send("Please provide the Course name (for ex, NUTR 303) \n")
        course_name = await self._recieve_response(message, client)
        await message.channel.send("Please provide the full assignment name (for ex, 'Recitation Assignment 1')\n")
        assignment_name = await self._recieve_response(message, client)

        #print(course_name)
        #print(assignment_name)
        course_name_str = str(course_name.content)  # converting it here for unit tests
        assignment_name_str = str(assignment_name.content)  # converting it here for unit tests

        curr_bs_util = self._id_to_bsu_map[message.author.id]
        feedback = curr_bs_util.get_assignment_feedback(course_name_str, assignment_name_str)

        if feedback.__contains__("ERROR") or feedback.__contains__("BOT REPORT"):
            await message.channel.send(feedback)
        else:
            await message.channel.send(f"Feedback from Grader: \n{feedback}")
        return


    async def _get_upcoming_quizzes(self, message, client):

        curr_bs_util = self._id_to_bsu_map[message.author.id]
        upcoming_quizzes = curr_bs_util.get_upcoming_quizzes()
        # if there are no upcoming quizzes returned, then we report to the user.
        if not upcoming_quizzes:
            await message.channel.send("You have no upcoming quizzes or exams.")
        else:
            await message.channel.send("You have the following upcoming assessments:\n")
            for quiz in upcoming_quizzes:
                course_name = quiz
                current_quiz = upcoming_quizzes[quiz]
                current_quiz_name = current_quiz["Name"]
                current_quiz_due_date = current_quiz["DueDate"]
                output_str = course_name + " - " + current_quiz_name + " due " + current_quiz_due_date + "\n"
                await message.channel.send(output_str)


    async def _get_newly_graded_assignments(self, message, client):
        curr_bs_util = self._id_to_bsu_map[message.author.id]
        await message.channel.send("Retrieving grades...")
        grade_updates = curr_bs_util.get_grade_updates()
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


    async def _get_upcoming_discussion(self, message, client):
        curr_bs_util = self._id_to_bsu_map[message.author.id]

        # dictionary of class_name, [list of dates]
        dates = curr_bs_util.get_dict_of_discussion_dates()

        # dates = DATES #ONLY FOR DEBUG

        # find discussion post deadline for 2 weeks
        string = curr_bs_util.find_upcoming_disc_dates(14, dates)

        if len(string) == 0:
            await message.channel.send("No upcoming posts for the next two weeks. Would you like to look further than 2 weeks?")
            response = await self._recieve_response(message, client)

            # they want to see everything
            if self._decide_yes_or_no(response):
                string = curr_bs_util.find_upcoming_disc_dates(0, dates)
                if len(string) == 0:
                    await message.channel.send("No upcoming posts.")
                else:
                    await message.channel.send(string)
                return
            # don't want to see anything
            else:
                await message.channel.send("Okay, sounds good!")
        else:
            await message.channel.send(string)


    async def _update_notification_schedule(self, message, client):
        
        async def everyday():
            new_time = None
            while not new_time:
                new_time = await self.get_time(message, client)

            await message.channel.send(f"{new_time.content}, right?")
            res = await self._recieve_response(message, client)

            if res.content.startswith("y") or res.content.startswith("right"):
                self._DB_UTIL.add_notifictaion_schedule(self._id_to_username_map[res.author.id], new_time.content,
                                                1 * 24 * 60, res.channel.id, description=7)  # 7 = everyday
                # SCHEDULED_HOURS.append(new_hour)
                await message.channel.send(f"Schedule changed.")
            else:
                await message.channel.send(f"No changes are made to your schedule.")

        async def every_week():
            await message.channel.send("Which week day?")
            while True:
                res = await self._recieve_response(message, client)
                day = await self.get_weekday(res.content)
                if day == -1:
                    await message.channel.send("Please choose from Mon/Tues/Wed/Thurs/Fri/Sat/Sun")
                    continue
                break

            new_time = None
            while not new_time:
                new_time = await self.get_time(message, client)

            day_str = self._NOT_FREQ_MAP[day]
            await message.channel.send(f"{new_time.content} for {day_str.lower()}?")
            res = await self._recieve_response(message, client)
            if res.content.startswith("y") or res.content.startswith("right"):
                self._DB_UTIL.add_notifictaion_schedule(self._id_to_username_map[res.author.id], new_time.content,
                                                1 * 24 * 7 * 60, res.channel.id, description=day)
                await message.channel.send(f"Schedule changed.")
            else:
                await message.channel.send(f"No changes are made to your schedule.")

        async def add_week_or_everyday():
            await message.channel.send(f"Do you want to be notified everyday, or by a specific weekday?")
            res = await self._recieve_response(message, client)
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
            res = await self._recieve_response(message, client)


            while True:
                try:
                    freq = int(res.content)
                except ValueError:
                    await message.channel.send("Please enter a number")
                    continue
                break

            s_times = self._DB_UTIL.get_notifictaion_schedule_with_description(self._id_to_username_map[message.author.id])
            curr_len = calculate_notis_each_week(s_times)

            if curr_len < freq:
                while curr_len < freq:
                    await message.channel.send(f"There are currently {curr_len} schedules. ")
                    
                    
                    await message.channel.send(f"Do you want to add more?")
                    
                    res = await self._recieve_response(message, client)
                    if self._decide_yes_or_no(res):
                        if freq - curr_len < 7:
                            #await message.channel.send(f"Adding schedules every day will e")
                            await every_week()
                        else:
                            await add_week_or_everyday()
                        s_times = self._DB_UTIL.get_notifictaion_schedule_with_description(self._id_to_username_map[message.author.id])
                        curr_len = calculate_notis_each_week(s_times)
                        continue
                    await message.channel.send(f"Understood. Have a nice day.")
                    break
            elif curr_len > freq:
                while curr_len > freq:
                    await message.channel.send(f"There are currently {curr_len} scheduled times. No new schedules will be added.\nDo you want to delete any schedules?")
                    res = await self._recieve_response(message, client)
                    if self._decide_yes_or_no(res):
                        current_times = self._DB_UTIL.get_notifictaion_schedule_with_description(self._id_to_username_map[message.author.id])
                        await self._delete_noti_some(message, client, current_times)
                        
                        s_times = self._DB_UTIL.get_notifictaion_schedule_with_description(self._id_to_username_map[message.author.id])
                        curr_len = calculate_notis_each_week(s_times)
                        
                        if curr_len <= freq:
                            break

                        await message.channel.send(f"Do you want to delete more?")
                        
                        res = await self._recieve_response(message, client)
                        if res.content.startswith("y") or res.content.startswith("right"):
                            continue
                    await message.channel.send(f"Understood. Have a nice day.")
                    break
            else:
                await message.channel.send(f"You already have {freq} schedules.")

        async def by_class_schedule():
            scheduled_classes = self._DB_UTIL.get_classes_in_schedule(self._id_to_username_map[message.author.id])
            if not scheduled_classes:
                await message.channel.send("You don't have any scheduled classes.")
                return

            msg = "Which class do you want to recieve notifications before?\n\n"
            msg += "List of classes:\n"
            for i, c in enumerate(scheduled_classes):
                msg += f"{i + 1}. {c}\n"

            await message.channel.send(msg)

            while True:
                res = await self._recieve_response(message, client)

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
                res = await self._recieve_response(message, client)
                try:
                    mins = int(res.content)
                except ValueError:
                    await message.channel.send("Please enter a number")
                    continue
                break

            scheduled_classes = self._DB_UTIL.get_class_schedule_with_description(
                self._id_to_username_map[message.author.id])
            # print(scheduled_classes)
            for c in scheduled_classes:
                # print(c[0])
                if c[0] != class_name:
                    continue

                time_str = c[1]
                time = self.parse_time(time_str)
                time = time - datetime.timedelta(minutes=mins)
                new_time_str = self.time_to_string(time)

                self._DB_UTIL.add_notifictaion_schedule(self._id_to_username_map[message.author.id], new_time_str,
                                                1 * 60 * 24 * 7, res.channel.id, c[2])

            await message.channel.send("Schedule modified.")

        async def check_replace(noti_func):
            await message.channel.send(f"Do you want to add to your current schedule or build a brand new one?")

            res = await self._recieve_response(message, client)
            if "new" in res.content:
                curr_username = self._id_to_username_map[message.author.id]

                # moves all old schedules to a temp username
                temp_username = curr_username + "_temp"
                self._DB_UTIL.change_username("NOTIFICATION_SCHEDULE", curr_username, temp_username)

                await noti_func()

                old_schedules = self._DB_UTIL.get_notifictaion_schedule_with_description(temp_username)
                msg = "Old schedules:\n"
                for i, time in enumerate(old_schedules):
                    msg += f"{i + 1}: {time[0]} {self._NOT_FREQ_MAP[int(time[1])].lower()}\n"
                    

                new_schedules = self._DB_UTIL.get_notifictaion_schedule_with_description(curr_username)
                msg += "\nNew schedules:\n"
                for i, time in enumerate(new_schedules):
                    msg += f"{i + 1}: {time[0]} {self._NOT_FREQ_MAP[int(time[1])].lower()}\n"

                msg += "\nDo you want to replace your old schedule with the new one?"
                await message.channel.send(msg)

                res = await self._recieve_response(message, client)
                if self._decide_yes_or_no(res):
                    self._DB_UTIL.clear_notification_schedule(temp_username)
                else:
                    self._DB_UTIL.clear_notification_schedule(curr_username)
                    self._DB_UTIL.change_username("NOTIFICATION_SCHEDULE", temp_username, curr_username)

                await message.channel.send("Finished. Please check your schedule with \"check notifications\"")
            else:
                await noti_func()

        await message.channel.send(
            "Do you want your notification to be sent every day, every week, by a specific amount, or according to your class schedule?")

        res = await self._recieve_response(message, client)
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


    async def _update_notification_type(self, message, client):
        current_times = self._DB_UTIL.get_notifictaion_schedule_with_description(
            self._id_to_username_map[message.author.id])

        if not current_times:
            await message.channel.send("You don't have any scheduled times now.")
            return

        msg = ""
        for i, time in enumerate(current_times):
            msg += f"{i + 1}: {time[0]} {self._NOT_FREQ_MAP[int(time[1])].lower()}\n"
            

        await message.channel.send("Which time do you want to change?")
        await message.channel.send(msg)

        while True:
            res = await self.recieve_response(message, client)

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
        res = await self._recieve_response(message, client)
        if res.content.startswith("y") or res.content.startswith("right"):
            new_types[0] = '1'

        await message.channel.send(f"Announcements?")
        res = await self._recieve_response(message, client)
        if res.content.startswith("y") or res.content.startswith("right"):
            new_types[1] = '1'

        await message.channel.send(f"Reminders?")
        res = await self._recieve_response(message, client)
        if res.content.startswith("y") or res.content.startswith("right"):
            new_types[2] = '1'

        await message.channel.send(f"Due dates?")
        res = await self._recieve_response(message, client)
        if res.content.startswith("y") or res.content.startswith("right"):
            new_types[3] = '1'

        new_types = "".join(new_types)
        num -= 1
        await message.channel.send(f"Change time: {current_times[num][0]} {current_times[num][1]}'s types?")

        res = await self._recieve_response(message, client)

        if res.content.startswith("y") or res.content.startswith("right"):
            self._DB_UTIL.update_notification_schedule_types(self._id_to_username_map[message.author.id],
                                                        current_times[num][0], current_times[num][1], new_types)

            await message.channel.send("Type updated")
        else:
            await message.channel.send(f"No changes are made to your schedule.")

    # helper function. will not be called directly be a user command. 
    async def _delete_noti_all(self, message, client):
        await message.channel.send("Are you sure to delete all of your scheduled times?")

        res = await self._recieve_response(message, client)
        if self._decide_yes_or_no(res):
            self._DB_UTIL.clear_notification_schedule(self._id_to_username_map[message.author.id])
            await message.channel.send("Schedule deleted")
        else:
            await message.channel.send(f"No changes are made to your schedule.")


    # helper function. will not be called directly be a user command. 
    async def _delete_noti_some(self, message, client, current_times):
        msg = ""
        for i, time in enumerate(current_times):
            msg += f"{i + 1}: {time[0]} {self._NOT_FREQ_MAP[int(time[1])].lower()}\n"
            
        await message.channel.send("Which time do you want to delete?")
        await message.channel.send(msg)

        while True:
            res = await self._recieve_response(message, client)

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
        await message.channel.send(f"Delete time: {current_times[num][0]} {self._NOT_FREQ_MAP[int(current_times[num][1])]}?")
        
        res = await self._recieve_response(message, client)

        if self._decide_yes_or_no(res):
            self._DB_UTIL.delete_notification_schedule(self._id_to_username_map[message.author.id], current_times[num][0], current_times[num][1])
            
            await message.channel.send("Schedule deleted")
        else:
            await message.channel.send(f"No changes are made to your schedule.")


    async def _delete_notification_schedule(self, message, client):
            current_times = self._DB_UTIL.get_notifictaion_schedule_with_description(
                self._id_to_username_map[message.author.id])

            if not current_times:
                await message.channel.send("You don't have any scheduled times now.")
                return

            await message.channel.send("Do you want to delete all scheduled times or specific times?")

            res = await self._recieve_response(message, client)
            if self._get_closer_response(["all", "some"],res.content) == 0:
                await self._delete_noti_all(message, client) 
            else:
                await self._delete_noti_some(message, client, current_times)


    async def _check_nofication_schedule(self, message, client):

            s_times = self._DB_UTIL.get_notifictaion_schedule_with_description(self._id_to_username_map[message.author.id])
            if not s_times:
                await message.channel.send("No schedules now!")
            else:
                msg = f"Scheduled times for {self._id_to_username_map[message.author.id]}:\n"
                for hour in s_times:
                    msg += f"{hour[0]} {self._NOT_FREQ_MAP[int(hour[1])].lower()}\n"

                await message.channel.send(msg)


    async def _update_class_schedule(self, message, client):
            while True:
                await message.channel.send("What is the class name?")
                res = await self._recieve_response(message, client)
                class_name = res.content

                while True:
                    await message.channel.send("Which week day?")
                    while True:
                        res = await self._recieve_response(message, client)
                        day = await self.get_weekday(res.content)
                        if day == -1:
                            await message.channel.send("Please choose from Mon/Tues/Wed/Thurs/Fri/Sat/Sun")
                            continue
                        break

                    new_time = None
                    while not new_time:
                        new_time = await self.get_time(message, client)

                    day_str = self._NOT_FREQ_MAP[day]
                    await message.channel.send(f"{new_time.content} for {day_str.lower()}?")
                    res = await self._recieve_response(message, client)
                    if self._decide_yes_or_no(res):
                        self._DB_UTIL.add_class_schedule(self._id_to_username_map[res.author.id], class_name, new_time.content,
                                                    description=day)
                        await message.channel.send(f"Schedule changed.")
                    else:
                        await message.channel.send(f"No changes are made to your schedule.")

                    await message.channel.send(f"Do you want to add another time for this class?")
                    res = await self._recieve_response(message, client)
                    if self._decide_yes_or_no(res):
                        continue
                    break

                await message.channel.send(f"Do you want to add another class?")
                res = await self._recieve_response(message, client)
                if self._decide_yes_or_no(res):
                    continue
                
                await message.channel.send(f"Understood. Have a nice day.")
                break


    async def _check_class_schedule(self, message, client):
            c_times = self._DB_UTIL.get_class_schedule_with_description(self._id_to_username_map[message.author.id])

            if not c_times:
                await message.channel.send("No schedules now!")
            else:
                msg = f"Scheduled classes for {self._id_to_username_map[message.author.id]}:\n"
                for hour in c_times:
                    msg += f"{hour[0]} {hour[1]} {self._NOT_FREQ_MAP[int(hour[2])].lower()}\n"

                await message.channel.send(msg)

    
    async def _update_download_schedule(self, message, client):
        #await message.channel.send(f"What time every day do you want your files to be downloaded?")
        new_time = None
        while not new_time:
            new_time = await self.get_time(message, client)

        await message.channel.send(f"What type of files? (Videos, pdf, slides, or all)")
        res = await self._recieve_response(message, client)
        option = self._get_closer_response(["videos", "pdf", "slides", "ppt", "all"],
                                           res.content)

        if option == 0:
            type = "video"
        elif option == 1:
            type = "pdf"
        elif option == 2 or option == 3:
            type = "slides"
        else:
            type = "all"


        await message.channel.send(f"Add to {new_time.content}, right?")
        res = await self._recieve_response(message, client)

        if self._decide_yes_or_no(res):
            self._DB_UTIL.add_download_shcedule(self._id_to_username_map[res.author.id], new_time.content,
                                                type, 7, message.author.id)  # 7 = everyday
            # SCHEDULED_HOURS.append(new_hour)
            await message.channel.send(f"Schedule changed.")
        else:
            await message.channel.send(f"No changes are made to your schedule.")


    async def _check_download_schedule(self, message, client):

        s_times = self._DB_UTIL.get_download_schedule(self._id_to_username_map[message.author.id])
        if not s_times:
            await message.channel.send("No downloading schedules now!")
        else:
            msg = f"Scheduled download times for {self._id_to_username_map[message.author.id]}:\n"
            for hour in s_times:
                msg += f"{hour[0]} {self._NOT_FREQ_MAP[int(hour[1])].lower()}\n"

            await message.channel.send(msg)


    async def _download_files_asking(self, message, client):
        username = self._id_to_username_map[message.author.id]
        bsu = self._id_to_bsu_map[message.author.id]

        await message.channel.send("For what class do you want to download?")
        res = await self._recieve_response(message, client)
        
        # save what courses they want to download files for
        courses = res.content
        full_course_name, course_id = bsu.find_course_id_and_fullname(courses)
        if not full_course_name or not course_id:
            await message.channel.send("The course specified cannot be found. Please type the name again with more clarity.")
            return 

        await message.channel.send("Start downloading...")

        await self._download_files(username, bsu, course_id, full_course_name)

        await message.channel.send(f"{full_course_name}: Files downloaded successfully!")


    async def _download_files_without_asking(self, user_id, course_id, course_name):
        username = self._id_to_username_map[user_id]
        bsu = self._id_to_bsu_map[user_id]
        
        await self._download_files(username, bsu, course_id, course_name)


    async def _download_files(self, username, bsu, course_id, full_course_name):
        # see their storage path and location
        sql_command = f"SELECT STORAGE_PATH from PREFERENCES WHERE USERNAME = '{username}';"
        storage_path = self._DB_UTIL._mysql.general_command(sql_command)
        sql_command = f"SELECT STORAGE_LOCATION from PREFERENCES WHERE USERNAME = '{username}';"
        storage_location = self._DB_UTIL._mysql.general_command(sql_command)
        
        storage_location = "Local Machine" if not storage_location or not storage_location[0][0] else storage_location[0][0]
        storage_path = "./downloads/" if not storage_path or not storage_path[0][0] else storage_path[0][0]


        if storage_location != "Local Machine" and not bsu.drive:
            bsu.drive = bsu.init_google_auths()

        bsu.download_files(course_id, storage_path, storage_location, full_course_name)


    async def _update_storage(self, message, client):
        await message.channel.send("Google Drive or Local Machine?")

        # getting the type of storage location
        path_type = await self._recieve_response(message, client)

        options = ["google drive", "Local Machine"]
        selection = self._get_closer_response(options, path_type.content)

        bsu = self._id_to_bsu_map[message.author.id]
        username = self._id_to_username_map[message.author.id]

        # checking what type of path they are going to save it in
        if selection == 0: # Google drive
            bsu.init_google_auths()

            await message.channel.send("What folder from root?")

            # checking to see if path is valid
            new_storage = await self._recieve_response(message, client)

            return_val = bsu.validate_path_drive(new_storage.content, bsu.drive)
            
            if not return_val:
                await message.channel.send("Not a valid path. Try the cycle again.")
                return
            
            # todo add saving mechanism to cloud database

            sql_type = "INSERT INTO PREFERENCES (USERNAME, STORAGE_LOCATION) VALUES (\"{f_name}\",\"{path_type}\") ON DUPLICATE KEY UPDATE STORAGE_LOCATION=\"{path_type}\"" \
                .format(path_type="Google Drive", f_name=username)
            self._DB_UTIL._mysql.general_command(sql_type)
            
            sql_path = "INSERT INTO PREFERENCES (USERNAME,STORAGE_PATH) VALUES (\"{f_name}\",\"{path}\") ON DUPLICATE KEY UPDATE STORAGE_PATH=\"{path}\"" \
                .format(path=new_storage.content, f_name=username)
            self._DB_UTIL._mysql.general_command(sql_path)

            await message.channel.send("New path saved")
            return

        # if the path is local
        elif selection == 1: # local
            await message.channel.send("Send your local path")
            # checking to see if path is valid (local)
            new_storage = await self._recieve_response(message, client)
            return_val = validate_path_local(new_storage.content)
            if not return_val:
                await message.channel.send("Not a valid path. Try the cycle again.")
            else:
                # todo add saving mechanism to cloud database

                sql_type = "UPDATE PREFERENCES SET STORAGE_LOCATION = '{path_type}' WHERE USERNAME = '{f_name}';" \
                    .format(path_type="Local Machine", f_name=username)
                self._DB_UTIL._mysql.general_command(sql_type)

                sql_path = "UPDATE PREFERENCES SET STORAGE_PATH = '{path}' WHERE USERNAME = '{f_name}';" \
                    .format(path=new_storage.content, f_name=username)
                self._DB_UTIL._mysql.general_command(sql_path)
                await message.channel.send("New path saved")
            return
        else:
            await message.channel.send("Your input isn't valid")


    async def _delete_download_schedule(self, message, client):
        current_times = self._DB_UTIL.get_download_schedule(self._id_to_username_map[message.author.id])

        if not current_times:
            await message.channel.send("You don't have any scheduled times now.")
            return

        await message.channel.send("Do you want to delete all scheduled times?")

        res = await self._recieve_response(message, client)
        if self._decide_yes_or_no(res):
            self._DB_UTIL.clear_download_schedule(self._id_to_username_map[message.author.id])
        await message.channel.send("Schedule deleted.")


    async def _get_course_priority(self, message, client):
        bsu = self._id_to_bsu_map[message.author.id]
        # reply backs to the user
        suggested_course_priority = ""
        found_missing_info_courses = ""

        # ask user for pick grade or by due date
        await message.channel.send("Please pick between grade or due dates for prioritizing your courses.")

        priority_option = await self._recieve_response(message, client)

        if priority_option.content.startswith("grade"):
            # api call for grades
            await message.channel.send("Setting course priority by grade ...")

            priority = bsu.get_sorted_grades()[0]
            missing = bsu.get_sorted_grades()[1]

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


    async def _overall_points(self, message, client):
        bsu = self._id_to_bsu_map[message.author.id]
        username = self._id_to_username_map[message.author.id]

        await message.channel.send("Please enter the courses you want to check with a comma. \n (e.g. cs180,cs182)")
        
        res = await self._recieve_response(message, client)
        courses = res.content.strip().split(",")
        
        IDs = []
        for c in courses:
            course_id = bsu.find_course_ID(c)
            IDs.append(course_id)  # getting the list of course IDs
        #print(IDs)

        grades = {}
        tosort = {}
        counter = 0
        for i in IDs:
            if i == -1:
                grades[courses[counter]] = 'Course not recognized'
                tosort[courses[counter]] = 0
            else:
                yourTotal, classTotal = bsu.sum_total_points(i)
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

        # See if the user specified a grades text channel
        sql_command = f"SELECT GRADES_TC FROM PREFERENCES WHERE USERNAME = '{username}';"
        result = self._DB_UTIL._mysql.general_command(sql_command)[0][0]
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


    async def _redirect_notifications(self, message, client):
        username = self._id_to_username_map[message.author.id]
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
        #print(category.lower())
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
        current_saved_tc = self._DB_UTIL._mysql.general_command(sql_command)[0][0]
        # Check if the channel that is being requested has already been created
        sql_command = f"SELECT LIST_OF_TCS FROM PREFERENCES WHERE USERNAME = '{username}';"
        list_of_tcs = self._DB_UTIL._mysql.general_command(sql_command)[0][0]
        if list_of_tcs is None:
            sql_command = f"UPDATE PREFERENCES SET LIST_OF_TCS = 'general' WHERE USERNAME = '{username}';"
            self._DB_UTIL._mysql.general_command(sql_command)
            sql_command = f"SELECT LIST_OF_TCS FROM PREFERENCES WHERE USERNAME = '{username}';"
            list_of_tcs = self._DB_UTIL._mysql.general_command(sql_command)[0][0]

        array = list_of_tcs.split(",")
        found = False
        for a in array:
            if a == text_channel:
                # Then this text channel already exists
                found = True
        # found, list_of_tcs = BOT_RESPONSES.check_if_tc_exists(current_saved_tc, DB_USERNAME)

        sql_command = f"UPDATE PREFERENCES SET {db_category} = '{text_channel}' WHERE USERNAME = '{username}';"
        self._DB_UTIL._mysql.general_command(sql_command)

        if not found:
            list_of_tcs = list_of_tcs + "," + text_channel
            sql_command = f"UPDATE PREFERENCES SET LIST_OF_TCS = '{list_of_tcs}' WHERE USERNAME = '{username}';"
            self._DB_UTIL._mysql.general_command(sql_command)
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


    async def _notification_location(self, message, client):
        username = self._id_to_username_map[message.author.id]

        sql = f"SELECT GRADES_TC FROM PREFERENCES WHERE USERNAME = '{username}';"
        grades = self._DB_UTIL._mysql.general_command(sql)[0][0]
        if grades is None:
            grades = "Not specified"
        sql = f"SELECT FILES_TC FROM PREFERENCES WHERE USERNAME = '{username}';"
        files = self._DB_UTIL._mysql.general_command(sql)[0][0]
        if files is None:
            files = "Not specified"
        sql = f"SELECT DEADLINES_TC FROM PREFERENCES WHERE USERNAME = '{username}';"
        deadlines = self._DB_UTIL._mysql.general_command(sql)[0][0]
        if deadlines is None:
            deadlines = "Not specified"
        final_string = f"Your notification redirections are saved as the following:\n" \
                    f"GRADES -> {grades}\n" \
                    f"DEADLINES -> {deadlines}\n" \
                    f"FILES -> {files}"
        await message.channel.send(final_string)
    

    async def _add_quiz_due_dates_to_calendar(self, message, client):
        bsu = self._id_to_bsu_map[message.author.id]
        username = self._id_to_username_map[message.author.id]

        await message.channel.send("Retrieving quizzes...")
        # Syncing quizzes to the calendar daily (so it can get the correct changes)
        quizzes = bsu.get_all_upcoming_quizzes()
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


    async def _get_course_link(self, message, client):
        bsu = self._id_to_bsu_map[message.author.id]
        username = self._id_to_username_map[message.author.id]

        user_course_urls = bsu.get_course_url()

        # bot asks user for specific input
        await message.channel.send("Which course link do you need? Type \'All\' or specific course links")
        await message.channel.send("ex) All or CS 180, CS 240")
        reply_back = ""
        cannot_find_courses = ""

        try:
            # get user reply back
            user_reply = await self._recieve_response(message, client)

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


    async def _get_upcoming_assignments(self, message, client):
        bsu = self._id_to_bsu_map[message.author.id]
        username = self._id_to_username_map[message.author.id]

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


        # get user response back
        user_reply = await self._recieve_response(message, client)

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
        event_list = bsu.get_upcoming_events(user_start_time, user_end_time)

        event_list_to_str = ""
        for event in event_list:
            event_list_to_str += "[{due_date}] {name}: {title}".format(due_date=event['Due Date'],
                                                                    name=event['Course Name'],
                                                                    title=event['Event Name'])
            event_list_to_str += "\n"

        await message.channel.send("These are your upcoming assignments/exams:\n" + event_list_to_str)


    async def _suggest_course_study(self, message, client):
        # check function for client.wait_for
        bsu = self._id_to_bsu_map[message.author.id]
        username = self._id_to_username_map[message.author.id]

        await message.channel.send("What order would you like for suggestions?\n" +
                                "\'grade, deadline\' or \'deadline, grade\'")

        try:
            user_response = await self._recieve_response(message, client)

            # default order value
            order = 0

            # user_requested_order = user_response.content.split(", ")
            if user_response.content.lower() == "grade, deadline":
                order = 1
            elif user_response.content.lower() == "deadline, grade":
                order = 2

            await message.channel.send("Creating suggestions...")
            if order != 0:
                focus_suggestion = bsu.get_focus_suggestion(order)[0]
                lack_info = bsu.get_focus_suggestion(order)[1]

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


    async def _add_office_hours_to_calendar(self, message, client):
        await message.channel.send("Please input the course name")
        course_name = await self._recieve_response(message, client)
        course_name = course_name.content.lower()

        await message.channel.send("Please input the instructor name")
        instr_name = await self._recieve_response(message, client)
        instr_name = instr_name.content.lower()

        await message.channel.send("Please input office hour days")
        days = await self._recieve_response(message, client)
        days = days.content.lower()
        days = BotResponses.format_days_of_week(days)

        await message.channel.send("Please input office hour start time. ie 13:30")
        st_time = await self._recieve_response(message, client)
        st_time = st_time.content.lower()

        await message.channel.send("Please input office hour end time. ie 14:30")
        end_time = await self._recieve_response(message, client)
        end_time = end_time.content.lower()

        response = self._recieve_response(message, client).add_office_hours_to_calendar(course_name, instr_name, days, st_time, end_time)
        await message.channel.send(response)
        return


    # An empty function to login the user ...!
    async def _login_empty(self, message, client):
        await message.channel.send("You are logged in to BrightSpace!")


    # ----------------------------------


    async def _rename_file(self, message, client):
        bsu = self._id_to_bsu_map[message.author.id]
        username = self._id_to_username_map[message.author.id]

        # list out the files that they can rename1
        response, status = self._br.get_downloaded_files(username, bsu, self._DB_UTIL)
        if status == False:
            await message.channel.send(response)
            return

        res_str = response
        while res_str:
            await message.channel.send(res_str[:2000])
            res_str = res_str[2000:]
        user_response = await self._recieve_response(message, client)

        response = self._br.process_renaming_response(username, user_response.content, bsu)
        await message.channel.send(response)
        return


    async def _add_discussion_schedule(self, message, client):
        bsu = self._id_to_bsu_map[message.author.id]
        username = self._id_to_username_map[message.author.id]

        await message.channel.send('What day(s) do you want discussion reminders sent each week?')
        days = await self._recieve_response(message, client)
        days = days.content.lower()

        await message.channel.send("Which class's discussions do you want to add to the schedule?")
        classes = await self._recieve_response(message, client)
        classes = classes.content.lower()

        self._br.add_discussion_schedule_to_db(username, days, classes, bsu, self._DB_UTIL)
        await message.channel.send("Added. ")
 

    async def _check_discussion_schedule(self, message, client):
        bsu = self._id_to_bsu_map[message.author.id]
        username = self._id_to_username_map[message.author.id]

        response = self._br.discussion_remind_to_post(username, bsu, self._DB_UTIL)
        await message.channel.send("Reminder to reply to the following discussions: ")
        if response != '-1':
            await message.channel.send(response)
        return


    async def _archive(self, message, client):
        bsu = self._id_to_bsu_map[message.author.id]
        username = self._id_to_username_map[message.author.id]

        response = self._br.archive_past_assignments(bsu._bsapi)
        if response != '-1':
            await message.channel.send(response)


    async def _check_update_section(self, message, client):
        bsu = self._id_to_bsu_map[message.author.id]

        response = self._br.updated_section(bsu)
        await message.channel.send(response)


    async def _configuration_setting(self, message, client):
        # Bot configuration includes:
        # 1 BrightSpace configuration
        # 1.1 Notification
        # 1.2 Download location
        #
        # 2 Bot configuration
        # 2.1 Notification
        # 2.2 Bot name
        #
        # 3 Default setting
        # 3.1 Default mode: set everything to default
        # 3.2 Change default: allow user to save their own default

        # Ask for specific configuration

        bsu = self._id_to_bsu_map[message.author.id]
        username = self._id_to_username_map[message.author.id]

        await message.channel.send("Please select a configuration you would like to change:\n" +
                                   "[1] Download location\n"
                                   "[2] BrightSpaceBot Notification\n[3] Change Bot name\n"
                                   "[4] Set configuration to default\n")


        try:
            user_choice = await self._recieve_response(message, client)
            user_choice = user_choice.content

            user_subchoice = ""

            if user_choice.startswith("1"):
                # download location change
                await message.channel.send("Please confirm option selection by typing \"update storage\" to continue")
                return
            elif user_choice.startswith("2"):
                # Notification Setting
                await message.channel.send("Would you like to \"check notifications\", "
                                           "\"check notification setting\", \"update schedule\"?")
                return
            elif user_choice.startswith("3"):
                # Bot name change
                await message.channel.send("Please confirm option selection by typing \"change bot name\" to continue")
                return

            elif user_choice.startswith("4"):
                # Set to Default
                await message.channel.send("Are you sure that you want to set every custom changes to default?\n"
                                           "This includes notification setting, local drive location, "
                                           " and the bot name.\n"
                                           "Yes / No")
                default_change = await self._recieve_response(message, client)
                default_change = default_change.content
                if default_change.lower() == "yes":
                    # set to default
                    self._DB_UTIL.clear_notification_schedule(username)
                    # Bot name
                    await message.guild.me.edit(nick="BrightSpace Bot")
                    await message.channel.send("Everything is set to default now!")
                elif not default_change.lower() == "no":
                    await message.channel.send("Given option is invalid. Please try the query from the beginning!")
            else:
                await message.channel.send("Given option is invalid. Please try the query again!")

        except asyncio.TimeoutError:
            await message.channel.send("Timeout Error has occurred. Please try the query again!")



    # ----- recurring events -----


    async def sync_calendar(self):

        # Sync calendar for every user!
        # Each BS_UTILS represents one user.
        for BS_UTILS in self._id_to_bsu_map.values():

            # Checks if the user is connected to BS before proceeding.
            if not self._login_if_necessary(None, BS_UTILS):
                if self._debug:
                    print("sync calendar classes: login to bs failed.")
                continue

            classes = BS_UTILS.get_classes_enrolled()
            #classes = {"EAPS": "336154"}  # IN TEST MODE
            print("CALENDAR STUFF")
            for courseName, courseID in classes.items():
                assignment_list = BS_UTILS._bsapi.get_upcoming_assignments(courseID)
                due = BS_UTILS.process_upcoming_dates(assignment_list)
                if len(due) != 0:
                    # loop through all the upcoming assignments
                    cal = Calendar()
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

                print("DISCUSSION STUFF")
                # Now adding dicussions
                discussion_list = BS_UTILS.get_discussion_due_dates_TEST()  # IN TEST MODE
                #discussion_list = BS_UTILS.get_discussion_due_dates(courseID)
                due = BS_UTILS.process_upcoming_dates(discussion_list)
                if len(due) != 0:
                    cal = Calendar()
                    for disc in due:
                        event_title = f"DISCUSSION POST DUE: {disc[0]} ({courseID})"
                        description = f"{disc[0]} for {courseName} is due. Don't forget to submit it!"
                        search_result, end_time = cal.get_event_from_name(event_title)
                        print("Search result: " + str(search_result))
                        date = datetime.datetime.fromisoformat(disc[1][:-1])
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


    async def sync_calendar_quiz(self):
        # Sync calendar for every user!
        # Each BS_UTILS represents one user.
        for BS_UTILS in self._id_to_bsu_map.values():

            # Checks if the user is connected to BS before proceeding.
            if not self._login_if_necessary(None, BS_UTILS):
                if self._debug:
                    print("sync calendar classes: login to bs failed.")
                continue

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
                        cal.delete_event(event_id)
                        cal.insert_event(event_title, description, start, end)

    async def send_notifications(self, client):
        async def send_notifications(string, BS_UTILS, channel_id, types):
            message_channel = client.get_channel(channel_id)
            #print(channel_id, message_channel)

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


            # send the upcoming discussion due dates
            # TODO: use a loop to send the full message. 

            if not string:
                await message_channel.send("No notifications.")
            while string:
                await message_channel.send(string[:2000])
                string = string[2000:]
        
        now = datetime.datetime.now()
        time_string = now.strftime("%H:%M")
        weekday = now.weekday()

        schedules = self._DB_UTIL.get_notifictaion_schedule_by_time(time_string, weekday)
        
        for schedule in schedules:
            username = schedule[0]
            # The default channel!
            channel_id = int(schedule[1])
            types = schedule[2]
            if not types:
                types = "1111"

            # Check if the user wants another channel
            sql_command = f"SELECT DEADLINES_TC FROM PREFERENCES WHERE USERNAME = '{username}';"
            sql_result = self._DB_UTIL._mysql.general_command(sql_command)
            if sql_result and sql_result[0][0]:
                sql_result = sql_result[0][0]
                for c in client.get_all_channels():
                    sql_result = sql_result.replace(" ", "-")
                    if c.name == sql_result:
                        channel_id = c.id
                        break

            user_id = -1
            for ids in self._id_to_username_map:
                if self._id_to_username_map[ids] == username:
                    user_id = ids
                    break
            if user_id == -1:
                continue

            BS_UTILS = self._id_to_bsu_map[user_id]

            '''section_updated = self._br.get_update_section_all(BS_UTILS)
            if len(section_updated) > 0:
                string += "\n " + section_updated'''


            if not self._login_if_necessary(None, BS_UTILS):
                if self._debug:
                    print("send_notifications: login to bs failed.")
                continue

            dates = BS_UTILS.get_dict_of_discussion_dates()
            string = BS_UTILS.find_upcoming_disc_dates(1, dates)
            string += BS_UTILS.get_notifications_past_24h()

            await send_notifications(string, BS_UTILS, channel_id, types)
    '''
        async def send_notifications(self, client):
            async def send_notifications(string, BS_UTILS, channel_id, types):
                message_channel = client.get_channel(channel_id)
                #print(channel_id, message_channel)

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

                section_updated = self._br.get_update_section_all(BS_UTILS)
                if len(section_updated) > 0:
                    string += " " + section_updated

                # send the upcoming discussion due dates
                # TODO: use a loop to send the full message. 

                if not string:
                    await message_channel.send("No notifications.")
                while string:
                    await message_channel.send(string[:2000])
                    string = string[2000:]
            
            
            def get_discussions(dates, bsu):
                #dates = bsu.get_discussion_due_dates_TEST()
                print("dates for discussion:", dates)
                string = bsu.find_upcoming_disc_dates(1, dates)

                # SEEING IF A SECTION HAS BEEN UPDATED / ADDED


                return string



            now = datetime.datetime.now()
            time_string = now.strftime("%H:%M")
            weekday = now.weekday()

            schedules = self._DB_UTIL.get_notifictaion_schedule_by_time(time_string, weekday)

            print("Schdules for notification loop:", schedules)
            for schedule in schedules:
                username = schedule[0]
                # The default channel!
                channel_id = int(schedule[1])
                types = schedule[2]
                if not types:
                    types = "1111"

                # Check if the user wants another channel
                sql_command = f"SELECT DEADLINES_TC FROM PREFERENCES WHERE USERNAME = '{username}';"
                sql_result = self._DB_UTIL._mysql.general_command(sql_command)
                if sql_result and sql_result[0][0]:
                    sql_result = sql_result.replace(" ", "-")
                    for c in client.get_all_channels():
                        if c.name == sql_result:
                            channel_id = c.id
                            break

                user_id = -1
                for ids in self._id_to_username_map:
                    if self._id_to_username_map[ids] == username:
                        user_id = ids
                        break
                if user_id == -1:
                    continue

                BS_UTILS = self._id_to_bsu_map[user_id]
                if not await self._login_if_necessary(None, BS_UTILS):
                    if self._debug:
                        print("send_notifications: login to bs failed.")
                    continue

                dates = BS_UTILS.get_dict_of_discussion_dates()
                string = BS_UTILS.find_upcoming_disc_dates(1, dates)
                string += BS_UTILS.get_notifications_past_24h()

                print("notifi")
                await send_notifications(string, BS_UTILS, channel_id, types)
    '''

    async def download_files_by_schedule(self):
        now = datetime.datetime.now()
        time_string = now.strftime("%H:%M")

        schedules = self._DB_UTIL.get_download_schedule_by_time(time_string)
        #print(schedules)
        for schedule in schedules:
            user_id = schedule[0]
            type = schedule[1]
            bsu = self._id_to_bsu_map[user_id]
            username = self._id_to_username_map[user_id]
            print(f"Download schedule activated for {username} ... !")
        
            courses = bsu.get_classes_enrolled()
            for course_name in courses.keys():
                print("downloading course: ", course_name)
                await self._download_files_without_asking(user_id, courses[course_name], course_name)

