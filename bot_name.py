# This class is for configuring Bot name

# API implementation should be done
import requests
import discord
import json

# We have no access to the Brightspace authentication API
# Therefore, we will test the codes hardcoded and try to login
# to brightspace using duo boilerkey

#
# ...
#

# You might want to find a bad word api instead of a array of strings
NEGATIVE_WORDS=["fuck", "shit"]
failure_msg="Please input a different bot name!"

# Default name is BrightspaceBot
bot_name = "BrightspaceBot"

# function to ask the user for a Bot name
def ask_name (reask: int):

    # reask (0) implies first time asking
    # reask (1) implies reasking name

    name_question = ""

    if reask == 0:
        name_question = "Do you like to give the Bot a name?"
    elif reask == 1:
        name_question = "Do you want to switch the Bot's name?"

    return name_question


def check_bad_word(name: str):
  if any(word in name for word in NEGATIVE_WORDS):
    return True

  # for else case
  return False

# function configuring the Bot name
def name_bot (name: str):
  # check for any bad_words used in the name

  if(check_bad_word(name)): # Bad word names should be rejected
    return 
  else:
    bot_name=name
    reask=ask_name(1)
    change=input(reask + "\nEnter yes/y or no/n:")
    

    


