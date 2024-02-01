
# === Module section === #

import discord # Discord API
from discord.ext import commands # Discord commands
from dotenv import load_dotenv, find_dotenv # Handling environment's variables.
from os import getenv as ENV # As the retriever of the environment's variables.
import re # Regexp
from bs4 import BeautifulSoup # Handling the Input and Output of the website and script.
import httpx # Handling request
import asyncio as io # Asynchronous operation
load_dotenv(find_dotenv()) # Load the .env

# === Bot's configuration section === #

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# Set up the bot.
bot = commands.Bot(command_prefix='>', intents=intents)

# === Variable section === #
matchURL = "https://genius.com/{Artist}-{Title}-lyrics" # This is a regexp pattern.
stop_singing = False

# === Bot's commands section === #

# If you want to know the bot is working or not, run this command, or ">ping". If it reply 'pong', then it's working.
@bot.command()
async def ping(ctx):
    await ctx.send('pong')

async def GET_SONG_LYRIC(Artist, Title):
    # Convert to equivalent URL match. In this case,
    # the Artist param only expect a capitalized letter and the whitespace replaced by '-'
    # the Title param only expect a lowercase letter and the whitespace replaced by '-'
    Artist = Artist.replace(' ', '-').capitalize()
    Title = Title.replace(' ', '-').lower()
    
    # Substitue the Artist and Title variable to the {Artist} and {Title}
    url = matchURL.format(Artist=Artist, Title=Title)

    try:
        async with httpx.AsyncClient() as client:
            # GET req to the URL
            response = await client.get(url)

            # If it is successful (the GET req), then we can continue the script
            if response.status_code == 200:
                # Return the webpage content as a whole.
                Body = response.text
                soup = BeautifulSoup(Body, 'html.parser') 
                lyric_div = soup.find(class_='Lyrics__Container-sc-1ynbvzw-1 kUgSbL') # The lyric container
                each_lyric = lyric_div.get_text() # Get all content inside the lyric container
                
                #TODO: Improvise this regexp part, so it's more efficient.
                #! Okay, this regexp part might be confusing. So let me tell what each line really does!
                
                #? This regexp pattern removes every word that is inside a []. Example, [Intro], [Chorus]
                each_lyric = re.sub(r'\[.*?\]', '', each_lyric)
                
                #? This regexp pattern makes every word that is inside a () into a lowercase word. Example, (Go) becomes (go)
                #? The reason why I did this, is because the next regexp pattern actually broke the lyric order.
                each_lyric = re.sub(r'\((.*?)\)', lambda x: x.group().lower(), each_lyric)
                
                #? This regexp pattern split the string only when an uppercase letter is followed by a lowercase letter
                each_lyric = re.split('(?=[A-Z])', each_lyric)
                
                #? Final touching, this one simply remove the first element that contains nothing
                each_lyric = each_lyric[1:len(each_lyric)]
                
                
                return each_lyric
                
                # Below code for testing.
                # for n, i in enumerate(each_lyric):
                #     print('[',n+1,']', i)
            else:
                # Else, we send a failed status code.
                print(f"Failed, status code: {response.status_code}\nDid you type a proper artist and song? Some music may doesn't exist!")
    except Exception as e:
        # If there's an error occured, please report it to the git issue.
        print(f"Error: {e}")

#TODO: Improvise this. So, not only user can sing through text, but also through a VC.
#TODO: Add a score. That see how well is user typing the lyrics.
# The `>sing` command. Accept 3 parameters
# Param 1: Artist  => Arist of the song/music
# Param 2: Title => Name of song/music
# Param 3: Delay => Timeout or delay of each lyric continuation.
# Param 4 (Default: True): Together => Whether if bot should sing it by itself, or with you
@bot.command()
async def sing(ctx, artist: str, title: str, delay: int, together: str='1'):
    await ctx.channel.send(f'**Music name:** {title}\n**By:** {artist}\n**Sing together: {together}**\n**Timeout (delay): {delay}')
    await ctx.message.delete()  # Delete the user's message
    # Act as a toggler.
    global stop_singing
    stop_singing = False
    # Get the song's lyrics
    song = await GET_SONG_LYRIC(artist, title)

    if (together == '1'):
        for i in range(0, len(song), 2):  # Skip lyric by jumping each element by 2. Example, a,c,e,g instead of a,b,c,d,e,f,g
            if stop_singing:
                break
            await ctx.send(song[i])  # Bot sings
            try:
                # Wait for the user's message for up to 'delay' seconds
                msg = await bot.wait_for('message', timeout=delay)
            except io.TimeoutError:
                # If the user doesn't respond in time, stop the lyric from continuing.
                await ctx.send('**No lyric continuation retrieved. Shutting down lyric\'s continuation**')
                break
             
    elif (together == '0'):
        # Loop through each lyric
        for lyric in song:
            # Chat the lyric
            await ctx.send(lyric)

            # Delay
            await io.sleep(delay)
    else:
        await ctx.send('''**Are you sure you type the correct command?**
Command: >sing [ARTIST:str] [MUSIC_NAME:str] [DELAY:int] [SING_TOGETHER: 1 | 0] ''')

# This command control the command `>sing`, so you can stop the command.
@bot.command()
async def stop(ctx):
    global stop_singing
    stop_singing = True

bot.run(ENV("BOT_TOKEN"))

