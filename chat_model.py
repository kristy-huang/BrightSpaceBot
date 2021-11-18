
import asyncio
from bs_utilities import BSUtilities

from thefuzz import fuzz
from thefuzz import process

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
#      in the format of "command": function. Please see __init__ for some examples.
# To decide yes or no:
#   use function self._decide_yes_or_no(message)


class NLPAction():
    
    # Paramerters:
    # DB_UTIL: DBUtilities object. Needs to be connected to a database.
    # debug: bool. Shows debug messages if set to true. 

    def __init__(self, DB_UTIL, debug = False):

        # "command" for each functionality.
        self.PHRASES = {
        "hello": self._say_hello,
        "hi": self._say_hello,
        "bye": self._say_good_bye,
        "change bot name": self._change_bot_name,
        "change your name": self._change_bot_name,
        "search for student": self._search_for_student,
        "current storage location": self._current_storage,
        "grades": self._grades,
        "get assignment feedback": self._get_assignment_feedback,
        "get upcoming quizzes": self._get_upcoming_quizzes
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
        if message.author.id not in self._locks:
            self._locks[message.author.id] = False

        if self._locks[message.author.id]:
            return

        self._locks[message.author.id] = True 

        if self._author_check(message, client):
            if self._debug:
                print("Message is from the bot it self. Abort. ")
                print(f"message author: {message.author}. client author: {client.user}")
            self._locks[message.author.id] = False
            return

        await self._request_bot_username_password_if_necessary(message, client)
        status = await self._setup_auto_if_necessary(message, client)

        if not status:
            self._locks[message.author.id] = False
            return

        # (matched string, confidency (out of 100))
        action_tuple = process.extractOne(message.content, self.PHRASES.keys(), scorer=fuzz.token_set_ratio)
        if action_tuple[1] < 50:
            if self._debug:
                print("Confidency lower than 50%. Abort.")
            self._locks[message.author.id] = False
            return 

        # Run the corresponding function!
        await self.PHRASES[action_tuple[0]](message, client)
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


    
    # ----- Login to discord bot & BrightSpace Functions -----


    # Maps the current user's id to an username. Also sets up a login lock.
    # Returns True when login succeeds, False when fails. 
    # Currently only has the case when succeeds. 

    async def _request_bot_username_password(self, message, client):
        await message.channel.send("Please enter your username for BrightSpace Bot.")
        username = await self._recieve_response(message, client)
        self._id_to_username_map[username.author.id] = username.content

        return True


    async def _request_bot_username_password_if_necessary(self, message, client):
        if message.author.id not in self._id_to_username_map:
            await self._request_bot_username_password(message, client)
        elif self._id_to_username_map[message.author.id] == "":
            await self._request_bot_username_password(message, client)


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
        if user_id in self._id_to_bsu_map:
            return True

        # TODO: ask if the user wants to change their username -> ???
        #await message.channel.send(f"Seems like your username: {self._id_to_username_map[user_id]} is not connected to BS yet!\n")

        db_res = self._DB_UTIL.get_bs_username_pin(self._id_to_username_map[message.author.id])
        if not db_res or not db_res[0][0]:
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
            self._id_to_bsu_map[user_id] = bsu
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




