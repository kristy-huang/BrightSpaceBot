import discord
from database.db_utilities import DBUtilities


# This will be a helper class to organize all the responses that the bot will need to provide back to discord
class BotResponses:
    """
    Creating constructor for BotResponse object
    """

    def __init__(self):
        self.message = None
        self.username = None
        self.channel = None
        self.DB_UTILS = None

    """
    Setting the message parameter that the discord method passes in for future use
    """

    def set_message_param(self, message):
        self.message = message

    def set_username_param(self, username):
        self.username = username

    def set_channel_param(self, channel):
        self.channel = channel

    def set_DB_param(self, DB):
        self.DB_UTILS = DB

    """
    DEBUGGING Helps see what the discord messages are 
    """

    def print_server_messages(self):
        print(f'{self.username}: {self.message.content} ({self.channel}) ({self.message.channel.id})')

    """
    DEBUGGING Function to test if our bot is working
    """

    def test_hello(self):
        # put your custom message here for the bot to output
        # we would incorporate our chat module here and then craft an appropriate response
        return self.message.channel.send(f'Hello {self.username}!')

    """
    Command: "current storage location"
    Returns: Either the storage path saved in Database or error message saying no storage path saved
    """

    def current_storage(self, username):
        sql = f'SELECT STORAGE_PATH from PREFERENCES WHERE USERNAME = \'{username}\';'
        storage_path = self.DB_UTILS._mysql.general_command(sql)
        if storage_path[0][0] is None:
            return self.message.channel.send('No storage path specified. Type update storage to save something')
        else:
            return self.message.channel.send(f'Current location: {storage_path[0][0]}')


# Debugging ...
if __name__ == '__main__':
    sql = DBUtilities()
    sql.connect_by_config("database/db_config.py")
    sql.use_database("BSBOT")
    print(sql.show_table_content("USERS"))
    print(sql.show_table_content("PREFERENCES"))
    print(sql._mysql.general_command("")[0][0])
