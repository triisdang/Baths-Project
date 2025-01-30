import discord
from discord.ext import commands
import os
import random
import requests
import google.generativeai as genai

# Read the token from the file
with open("token.txt", "r") as file:
    token = file.read().strip()  # Replace content in file token.txt with your own token

# Read the Google Gemini API key from the file
with open("tokengemini.txt", "r") as file:
    gemini_api_key = file.read().strip()

# Configure the Google Gemini API
genai.configure(api_key=gemini_api_key)

# Pair emojis
yeah = "<a:animeahhhhh:1334142756934651927>"
alert = "<a:alert:1334142774035087423>"
fling = "<a:fling:1334142789788897352>"
ooooo = "<:ooooo:1334142810986774620>"
doggokek = "<:doggokek:1334142827050831944>"
cutecat = "<:cutecat:1334142840871325777>"
catjam = "<:catjam:1334142860236161135>"
bleh = "<:bleh:1322913813418475622>"
meloncat = "<:meloncat:1322913721697177610>"

# Set up the bot with the necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent

bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to store chat histories
chat_histories = {}

# Function to interact with Google Gemini API
def get_gemini_response(user_id, prompt):
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
    )

    # Get the chat history for the user
    history = chat_histories.get(user_id, [])

    chat_session = model.start_chat(history=history)

    response = chat_session.send_message(prompt)

    # Update the chat history
    history.append({"role": "user", "parts": [prompt]})
    history.append({"role": "model", "parts": [response.text]})
    chat_histories[user_id] = history

    return response.text

# When the bot is ready
@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.listening, name="for help | !cmds")   
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'I am ready! My name is {bot.user}!')

# Test command
@bot.command()
async def hello(ctx):
    print(f'{ctx.author} just executed the hello command.')
    await ctx.send("Hello cc! " + meloncat)

# A command that displays server information
@bot.command()
async def whatisthisserver(ctx):
    print(f'{ctx.author} just executed the whatisthisserver command.')
    await ctx.send(
        f"This is {ctx.guild.name} server, created at {ctx.guild.created_at} and has {ctx.guild.member_count} members!"
    )

# A command that displays the bot's commands
@bot.command()
async def cmds(ctx):
    print(f'{ctx.author} just executed the cmds command.')
    embed = discord.Embed(
        title="Bot Commands",
        description="Here are the commands you can use with this bot " + catjam + " :",
        color=discord.Color.green()
    )
    embed.set_author(name=f"Requested by: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
    embed.add_field(name="!hello", value="Greets the user with 'Hello, world!'", inline=False)
    embed.add_field(name="!whatisthisserver", value="Displays server information.", inline=False)
    embed.add_field(name="!cmds", value="Displays this help message.", inline=False)
    embed.add_field(name="!join", value="Join your voice channel you are in", inline=False)
    embed.add_field(name="!leave", value="Leave voice channel [buggy]", inline=False)
    embed.add_field(name="!play", value="Play an MP3 file in the voice channel [buggy]", inline=False)
    embed.add_field(name="!userinfo", value="View user info of a user (tag them to view).", inline=False)
    embed.add_field(name="FUN COMMANDS", value="Fun commands to try out:", inline=False)
    embed.add_field(name="!steelcredit", value="Try if you dare... (tag your best friend :) )", inline=False)
    embed.add_field(name="!russ", value="Play Russian roulette with friends!", inline=False)
    embed.add_field(name="!ai", value="Talk to Google's Gemini!", inline=False)
    embed.set_footer(text="Bot by Chipoverhere " + cutecat + " [Github](https://github.com/triisdang/DSBOT)", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

# A command that steals social credit
@bot.command()
async def steelcredit(ctx, member: discord.Member = None):
    print(f'{ctx.author} just executed the steelcredit command.')
    if member is None:
        embed = discord.Embed(
            title="Missing Argument",
            description="Please tag a person to steal social credit from.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Usage: !steelcredit @username")
        await ctx.send(embed=embed)
    else:
        socialcredit = discord.File("Images/social.webp", filename="RS.png")
        await ctx.send(
            f"HOLY COW {ctx.author.mention} STEEL 10000M SOCIAL CREDIT FROM {member.mention} !!! " + fling,
            file=socialcredit
        )

# A command that displays user information
@bot.command()
async def userinfo(ctx, member: discord.Member):
    print(f'{ctx.author} just executed the userinfo command.')
    embed = discord.Embed(
        title=f"User Info - {member.display_name}",
        description=f"Here is the information for {member.mention}:",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(name="Username", value=member.name, inline=True)
    embed.add_field(name="Discriminator", value=member.discriminator, inline=True)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Status", value=member.status, inline=True)
    embed.add_field(name="Joined at", value=member.joined_at, inline=True)
    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

# A command to change the bot's status and activity
@bot.command()
async def changestate(ctx, status: str, activity_type: str, *, activity_name: str):
    print(f'{ctx.author} just executed the changestate command.')
    if ctx.author.name == "chipoverhere":
        # Map the status string to discord.Status
        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible
        }

        # Map the activity type string to discord.ActivityType
        activity_type_map = {
            "game": discord.ActivityType.playing,
            "streaming": discord.ActivityType.streaming,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching
        }

        # Get the status and activity type from the maps
        new_status = status_map.get(status.lower())
        new_activity_type = activity_type_map.get(activity_type.lower())

        if new_status is None:
            await ctx.send("Invalid status. Valid options are: online, idle, dnd, invisible.")
            return

        if new_activity_type is None:
            await ctx.send("Invalid activity type. Valid options are: game, streaming, listening, watching.")
            return

        # Set the new presence
        activity = discord.Activity(type=new_activity_type, name=activity_name)
        await bot.change_presence(status=new_status, activity=activity)
        await ctx.send(f"Changed status to {status} and activity to {activity_type} {activity_name}.")
    else:
        await ctx.send("You do not have permission to use this command.")

# Example usage:
# !changestate online game Minecraft
# !changestate idle listening Spotify
# !changestate dnd watching a movie
# !changestate invisible streaming Live Coding https://twitch.tv/yourchannel

# Command to join a voice channel
@bot.command()
async def join(ctx):
    print(f'{ctx.author} just executed the join command.')
    # Check if the user is in a voice channel
    if ctx.author.voice is None:
        await ctx.send("You are not in a voice channel!")
        return

    # Get the voice channel the user is in
    channel = ctx.author.voice.channel

    # Connect to the voice channel
    await channel.connect()
    await ctx.send(f"Joined {channel.name}!")

# Command to play an MP3 file
@bot.command()
async def play(ctx, filename: str):
    print(f'{ctx.author} just executed the play command.')
    if ctx.voice_client is None:
        await ctx.send("I am not in a voice channel! Use !join to make me join a voice channel first.")
        return

    if not os.path.isfile(filename):
        await ctx.send(f"The file {filename} does not exist.")
        return

    source = discord.FFmpegPCMAudio(filename)
    ctx.voice_client.play(source, after=lambda e: print(f"Finished playing: {e}"))
    await ctx.send(f"Now playing: {filename}")

# Command to leave a voice channel
@bot.command()
async def leave(ctx):
    print(f'{ctx.author} just executed the leave command.')
    if ctx.voice_client is None:
        await ctx.send("I am not in a voice channel!")
        return

    await ctx.voice_client.disconnect()
    await ctx.send("Disconnected from the voice channel.")

# Russian Roulette command
class RussianRouletteGame:
    def __init__(self):
        self.players = []
        self.current_player_index = 0
        self.bullet_position = random.randint(0, 5)
        self.current_chamber = 0
        self.game_active = False

    def get_status_embed(self):
        embed = discord.Embed(
            title="Russian Roulette",
            description="The tension rises as the cylinder spins...",
            color=discord.Color.red()
        )

        if not self.game_active and not self.players:
            embed.add_field(name="Status", value="Waiting for players to join...", inline=False)
        elif not self.game_active and self.players:
            players_list = "\n".join([f"• {player.mention}" for player in self.players])
            embed.add_field(name="Players Joined To Death", value=players_list, inline=False)
            embed.add_field(name="Status", value="Waiting for more players or game start", inline=False)
        else:
            players_list = "\n".join([f"• {player.mention}" + (" 🎯" if i == self.current_player_index else "")
                                      for i, player in enumerate(self.players)])
            embed.add_field(name="Players", value=players_list, inline=False)
            embed.add_field(name="Chamber", value=f"{self.current_chamber + 1}/6", inline=True)
            embed.add_field(name="Current Turn", value=self.players[self.current_player_index].mention, inline=True)

        return embed

class RussianRouletteButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.game = RussianRouletteGame()
        self.message = None

    async def update_message(self, interaction: discord.Interaction):
        await interaction.message.edit(embed=self.game.get_status_embed(), view=self)

    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.primary)
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.game.players:
            self.game.players.append(interaction.user)

            if len(self.game.players) >= 2:
                self.children[0].disabled = True
                self.children[1].disabled = False

            await self.update_message(interaction)
            await interaction.response.defer()

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.success, disabled=True)
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.game.players) >= 2:
            self.game.game_active = True
            random.shuffle(self.game.players)
            button.disabled = True
            self.children[2].disabled = False

            await self.update_message(interaction)
            await interaction.response.defer()

    @discord.ui.button(label="Pull Trigger:skull:", style=discord.ButtonStyle.danger, disabled=True)
    async def pull_trigger(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.game.game_active or interaction.user != self.game.players[self.game.current_player_index]:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        if self.game.current_chamber == self.game.bullet_position:
            eliminated_player = self.game.players.pop(self.game.current_player_index)
            self.game.current_player_index %= len(self.game.players)

            if len(self.game.players) == 1:
                self.game.game_active = False
                button.disabled = True
                winner_embed = discord.Embed(
                    title=f"🎉 Game Over!, Call 911 {alert}",
                    description=f"{self.game.players[0].mention} has won the game{doggokek}! {eliminated_player.mention} died! {fling}",
                    color=discord.Color.green()
                )
                await interaction.message.edit(embed=winner_embed, view=None)
                await interaction.response.defer()
                await interaction.channel.send(f"Pov {self.game.players[0].mention} rn :")
                await interaction.channel.send("https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExenlyM2gzbnc2eG5ydnJ3ODlkeGdvZXN1dXg0N3p4NTRlc3ZkdXIzayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/nrpCs0Bwdxp8k9FoPy/giphy.gif")
                return
        else:
            self.game.current_chamber = (self.game.current_chamber + 1) % 6
            self.game.current_player_index = (self.game.current_player_index + 1) % len(self.game.players)

        await self.update_message(interaction)
        await interaction.response.defer()

@bot.command()
async def russ(ctx):
    print(f'{ctx.author} just executed the russ command.')
    view = RussianRouletteButtons()
    await ctx.send(embed=view.game.get_status_embed(), view=view)

# AI command
@bot.command()
async def ai(ctx, *, prompt: str):
    print(f'{ctx.author} just executed the ai command.')
    response = get_gemini_response(ctx.author.id, prompt)
    # Split the response into chunks of 2000 characters
    for i in range(0, len(response), 2000):
        await ctx.send(response[i:i+2000])

# Run the bot using the token you copied earlier
bot.run(token)