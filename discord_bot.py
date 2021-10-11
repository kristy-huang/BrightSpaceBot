# Our discord token is saved in another file for security
from discord_config import config
import discord

'''
To add the bot to your own server and test it out, copy this URL into your browser
https://discord.com/api/oauth2/authorize?client_id=894695859567083520&permissions=534723950656&scope=bot
 '''

# This will be our discord client. From here we will get our input
client = discord.Client()


# Having the bot log in and be online
@client.event
async def on_ready():
    print("We have logged in as: " + str(client.user))


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

    # setting up a basic 'hello' command so you get this gist of it
    if user_message.lower() == 'hello':
        # put your custom message here for the bot to output
        # we would incorporate our chat module here and then craft an appropriate response
        await message.channel.send(f'Hello {username}!')
        return
    elif user_message.lower() == 'bye':
        await message.channel.send(f'Bye {username}!')
        return

    #should I call the determineTask() function here? Before this if clause? Or just set the task type to Request in the if clause below? 
    
    if 'upcoming quiz' in message.content:
        newTask = Task()
        newRequest = Request(newTask)
        upcomingQuizzes [] = newRequest.getUpcomingQuizzes();    ##research how to import other files in python!
        
    
    # Maybe in reality we want to have the message be passed through chat module and it returns what type of
    # request they are intending. From there we call the methods from the scripts we have written.

    # Lets say that we want the bot to only respond to a specific text channel in a server named 'todo'
    # Make sure this channel exists tho first!
    # I think there is a slight bug when I put sentences but we can revisit that later
    if message.channel.name == 'specifics':
        if user_message.lower() == 'im bored':
            await message.channel.send("You should probably study...")
            return


# Now to actually run the bot!
client.run(config['token'])
