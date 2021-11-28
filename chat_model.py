
import asyncio
import datetime
from requests.models import Response
from werkzeug.security import check_password_hash

from thefuzz import fuzz
from thefuzz import process

from bs_utilities import BSUtilities
from Authentication import setup_automation

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
        "switch bot account": ("switch", False),
        "search for student": (self._search_for_student, True),
        "current storage location": (self._current_storage, True),
        "grades": (self._grades, True),
        "get assignment feedback": (self._get_assignment_feedback, True),
        "get upcoming quizzes": (self._get_upcoming_quizzes, True),
        "get newly graded assignments": (self._get_newly_graded_assignments, True),
        "get upcoming discussion": (self._get_upcoming_discussion, True),
        "update notification schedule": (self._update_notification_schedule, True)
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
            self._locks[message.author.id] = False

        if self._debug:
            print("Incoming message: ", message.content, "author: ", message.author, " Locked: ", self._locks[message.author.id])

        if self._locks[message.author.id]:
            if self._debug:
                print("Locked. abort.")
            return

        self._locks[message.author.id] = True 

        # ---- to prevent bot calling itself -----

        if self._author_check(message, client):
            if self._debug:
                print("Message is from the bot it self. Abort. ")
                #print(f"message author: {message.author}. client author: {client.user}")
            self._locks[message.author.id] = False
            return

        # ---- functionalities that does not require the user to login -----

        # (matched string, confidency (out of 100))
        action_tuple = process.extractOne(message.content, self.PHRASES.keys(), scorer=fuzz.token_set_ratio)
        if action_tuple[1] < 50:
            if self._debug:
                print("Confidency lower than 50%. Abort.")
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
            self._locks[message.author.id] = False
            return



        # Run the corresponding function!
        await self.PHRASES[action_tuple[0]][0](message, client)
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
        await message.channel.send("Please enter your username for the bot. If you do not have an account yet, please go to https://brightspacebot.herokuapp.com/ to register an account. ")
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

        await message.channel.send("Logging into BrightSpace...")
        bsu.set_session_auto(self._DB_UTIL, self._id_to_username_map[message.author.id])
        if not bsu.check_connection():
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
        if storage_path[0][0] is None:
            await self.message.channel.send('No storage path specified. Type update storage to save something')
        else:
            await self.message.channel.send(f'Current location: {storage_path[0][0]}')


    async def _grades(self, message, client):

        curr_bs_util = self._id_to_bsu_map[message.author.id]

        await message.channel.send("For which classes?\n")

        res = await self._recieve_response(message, client)
        
        courses = res.content.split(",")

        IDs = []
        for c in courses:
            course_id = curr_bs_util.find_course_id(c)
            IDs.append(course_id)
        #print(IDs)

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
                    grades[courses[counter]] = 'Not found'
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
        return


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

            print(day)
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


