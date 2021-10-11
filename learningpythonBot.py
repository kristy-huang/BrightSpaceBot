import discord
import random

TOKEN = 'ODk2OTQyNTc1Mzk3NzgxNTM0.YWOc3g.cAMfOGi2VBOVuSgesrA8U7Zdn_M'

client = discord.Client()

@client.event
async def on_ready(): 
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    username = str(message.author).split('#')[0]
    user_message = str(message.content)
    channel = str(message.channel.name)
    print(f'{username}: {user_message} ({channel})')

    if message.author == client.user:
        return

    if message.channel.name == 'mistah-dj-queue':
        if user_message.lower() == 'hello':
            await message.channel.send(f'Hello {username}!')
            return
        elif user_message.lower() == 'bye':
            await message.channel.send(f'See you later {username}!')
            return
        elif user_message.lower() == 'random number?':
            response = f'This is your random number: {random.randrange(100)}'
            await message.channel.send(response)
            return


client.run(TOKEN)