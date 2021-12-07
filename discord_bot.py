# Our discord token is saved in another file for security
from hashlib import new
from os import execv
from discord.errors import NotFound
from discord_config import config, USERNAME, PIN
import discord
from discord.ext import tasks, commands
import asyncio
from file_storage import *
import datetime
import time
from bs_utilities import BSUtilities
from database.db_utilities import DBUtilities
from bot_responses import BotResponses
from bs_calendar import Calendar
from Authentication import setup_automation
from werkzeug.security import generate_password_hash

from chat_model import NLPAction

'''
To add the bot to your own server and test it out, copy this URL into your browser
https://discord.com/api/oauth2/authorize?client_id=894695859567083520&permissions=534992387152&scope=bot
 '''

DEBUG = True

# This will be our discord client. From here we will get our input
client = discord.Client()

channelID = 663863991218733058  # mine!
# TODO save this in the database - right now this is my (Raveena's) channel)
BOT_RESPONSES = BotResponses()

db_config = "./database/db_config.py"
DB_UTILS = DBUtilities(db_config)

nlpa = NLPAction(DB_UTILS, debug=DEBUG)

# Having the bot log in and be online
@client.event
async def on_ready():
    pass


@commands.command()
async def quit(ctx):
    await ctx.send("Shutting down the bot")
    return await client.logout()  # this just shuts down the bot.



@tasks.loop(minutes=1)
async def minute_loop():
    print("minute loop")
    await nlpa.send_notifications(client)
    await nlpa.download_files_by_schedule()
    


@minute_loop.before_loop
async def minute_loop_before():
    await client.wait_until_ready()



@tasks.loop(minutes=24 * 60)
#@tasks.loop(minutes=1)
async def day_loop():
    await nlpa.sync_calendar()
    await nlpa.sync_calendar_quiz()


@day_loop.before_loop
async def day_loop_before():
    await client.wait_until_ready()


minute_loop.start()
day_loop.start()

# This is our input stream for our discord bot
# Every message that comes from the chat server will go through here
@client.event
async def on_message(message):
    await nlpa.process_command(message, client)



# Now to actually run the bot!
client.run(config['token'])