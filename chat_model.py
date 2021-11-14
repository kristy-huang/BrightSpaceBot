
import asyncio

from thefuzz import fuzz
from thefuzz import process


# A class to parse user commands, and run matching functionalities.
#
# Developer instructions:
# To show debug information: 
#   set debug=True when initializing an NLPAction object
# To add a command / function match:
#   1. Implement a function in the NLPAction class.
#   2. Add the mapping from a command to the function in self.PHRASES in __init__,
#      in the format of "command": function. Please see __init__ for some examples.


class NLPAction():
    
    # Paramerters:
    # BS_UTIL: BSUtilities object. Does not need to be connected to BrightSpace!
    # DB_UTIL: DBUtilities object. Needs to be connected to a database!
    # debug: bool. Shows debug messages if set to true. 

    def __init__(self, BS_UTIL, DB_UTIL, debug = False):
        self.PHRASES = {
        "hello": self._say_hello,
        "hi": self._say_hello,
        "bye": self._say_good_bye,
        "change bot name": self._change_bot_name
        }

        self.BS_UTIL = BS_UTIL
        self.DB_UTIL = DB_UTIL
        self._debug = debug
        
    
    # Identifies what the user wants to do from an incoming message, and call 
    # functions that can solve their porblems.
    # 
    # message: the message object recieved from the user. (Not a string)
    # client: the client object

    async def process_command(self, message, client):
        if  self._author_check(message, client):
            if self._debug:
                print("Message is from the bot it self. Abort. ")
                print(f"message author: {message.author}. client author: {client.user}")

            return

        # (matched string, confidency (out of 100))
        action_tuple = process.extractOne(message.content, self.PHRASES.keys(), scorer=fuzz.token_set_ratio)
        if action_tuple[1] < 50:
            if self._debug:
                print("Confidency lower than 50%. Abort.")
            return 

        # Run the corresponding function!
        await self.PHRASES[action_tuple[0]](message, client)


    # Returns true if the message is same as the "client" -> The bot?
    def _author_check(self, message, client):
        return message.author == client.user


    def _get_username_from_message(self, message):
        return str(message.author).split('#')[0]


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
            if change_again.content.startswith('No'):
                change = False
                await message.channel.send("Thank you for changing my name!")
            elif not change_again.content.startswith('Yes'):  # user input invalid response
                await message.channel.send("Invalid response given! Please try the query again.")
                return





    
