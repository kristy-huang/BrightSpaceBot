
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
        "search for student": self._search_for_student
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
        # one login lock per user!
        self._login_locks = {}

        self._debug = debug
        
    
    # Identifies what the user wants to do from an incoming message, and call 
    # functions that can solve their porblems.
    # 
    # message: the message object recieved from the user. (Not a string)
    # client: the client object

    async def process_command(self, message, client):
        if self._author_check(message, client):
            if self._debug:
                print("Message is from the bot it self. Abort. ")
                print(f"message author: {message.author}. client author: {client.user}")

            return

        await self._request_bot_username_password_if_necessary(message, client)
        if not self._login_locks[message.author.id]:
            self._login_locks[message.author.id] = True
            status = await self._setup_auto_if_necessary(message, client)
            self._login_locks[message.author.id] = False

            if not status:
                return

        # (matched string, confidency (out of 100))
        action_tuple = process.extractOne(message.content, self.PHRASES.keys(), scorer=fuzz.token_set_ratio)
        if action_tuple[1] < 50:
            if self._debug:
                print("Confidency lower than 50%. Abort.")
            return 

        # Run the corresponding function!
        await self.PHRASES[action_tuple[0]](message, client)


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
        self._login_locks[username.author.id] = False

        return True


    async def _request_bot_username_password_if_necessary(self, message, client):
        if message.author.id not in self._id_to_username_map:
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
    
