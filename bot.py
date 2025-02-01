import discord
from discord.ext import commands
import os
from datetime import datetime
import asyncio
from random import randint, shuffle
import requests
import json
from typing import Optional

#########################
#       CONSTANTS       #
#########################
ROBLOX_API_URL = "https://api.roblox.com/users/"
COMMAND_PREFIX = "!"
MAX_DM_HISTORY = 50
API_TIMEOUT = 30
BOMB_COOLDOWN = 300
BOMB_RATE_LIMIT = 0.5
MAX_BOMB_MESSAGES = 100
# Blue color : devs
# Green color : for user
# Developer list - add Discord usernames
DEVELOPERS = [
    "chipoverhere"  # Main developer
 #   "dev2name",      # Add more devs here
  #  "dev3name"       # Add more devs here
]

# Colors for consistency
COLORS = {
    'success': discord.Color.green(),
    'error': discord.Color.red(),
    'warning': discord.Color.gold(),
    'info': discord.Color.blue(),
    'dev': discord.Color.purple()
}

# Load tokens
with open("token.txt", "r") as file:
    TOKEN = file.read().strip()

with open("groqtoken.txt", "r") as file:
    GROQ_API_KEY = file.read().strip()

# Emojis
EMOJIS = {
    "x":"<:x_:1334966527954255882>",
    "trollhand":"<:trollhand:1334963873094304103>",
    "fling": "<:fling:1334142789788897352>",
    "ooooo": "<a:ooooo:1334142810986774620>",
    "doggokek": "<a:doggokek:1334142827050831944>",
    "cutecat": "<:cutecat:1334142840871325777>",
    "catjam": "<a:catjam:1334142860236161135>",
    "bleh": "<:bleh:1322913813418475622>",
    "meloncat": "<:meloncat:1322913721697177610>",
    "alert": "<a:alert:1334142774035087423>"
}

#########################
#     EMBED HELPERS     #
#########################

class Embeds:
    @staticmethod
    def create_base(title, description=None, color=discord.Color.green(), author=None, footer=None, thumbnail=None):
        embed = discord.Embed(title=title, description=description, color=color)
        if author:
            embed.set_author(name=f"Requested by: {author.display_name}", icon_url=author.avatar.url)
        if footer:
            embed.set_footer(text=footer)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        return embed

    @staticmethod
    async def error(ctx, message):
        embed = Embeds.create_base(
            title="Error",
            description=message,
            color=discord.Color.red(),
            author=ctx.author if hasattr(ctx, 'author') else None
        )
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)

    @staticmethod
    async def success(ctx, title, description):
        embed = Embeds.create_base(
            title=title,
            description=description,
            color=discord.Color.green(),
            author=ctx.author
        )
        await ctx.send(embed=embed)

    @staticmethod
    async def warning(ctx, title, description):
        embed = Embeds.create_base(
            title=f"⚠️ {title}",
            description=description,
            color=discord.Color.gold(),
            author=ctx.author
        )
        await ctx.send(embed=embed)

    @staticmethod
    async def permission_denied(ctx):
        embed = Embeds.create_base(
            title=f"Permission Denied {EMOJIS['x']}",
            description=f"You don't have permission to use this command {EMOJIS['x']} !",
            color=discord.Color.red(),
            author=ctx.author
        )
        await ctx.send(embed=embed)

#########################
#    API FUNCTIONS      #
#########################

# Update get_groq_response to handle images/files
def get_groq_response(prompt, user_id=None, attachments=None):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        # Get chat history if user_id provided
        messages = []
        if user_id and user_id in dm_history:
            # Format previous conversations
            for timestamp, role, content in dm_history[user_id]:
                messages.append({
                    "role": "user" if role == "User" else "assistant",
                    "content": content
                })

        # Add current prompt
        messages.append({
            "role": "user",
            "content": prompt
        })

        # Add attachments if any
        if attachments:
            for attachment in attachments:
                messages.append({
                    "role": "user",
                    "content": {
                        "type": "image_url",
                        "image_url": {
                            "url": attachment.url
                        }
                    }
                })

        data = {
            "model": "llama-3.2-90b-vision-preview",
            "messages": messages
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=API_TIMEOUT)
        response.raise_for_status()
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response")
    except Exception as e:
        print(f"API Error: {e}")
        return "Sorry, I encountered an error while processing your request."

#########################
#      BOT SETUP        #
#########################

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Global variables
dm_history = {}
allowdmai = "true"
dm_cooldowns = {}

#########################
#   HELPER FUNCTIONS    #
#########################

def is_dev(user_name: str) -> bool:
    """Check if a user is a developer"""
    return user_name in DEVELOPERS

async def check_cooldown(user_id: int) -> tuple[bool, int]:
    if user_id in dm_cooldowns:
        remaining = dm_cooldowns[user_id] - datetime.now().timestamp()
        if remaining > 0:
            return False, int(remaining)
    return True, 0

class DMRateLimiter:
    def __init__(self):
        self.last_dm = 0
    
    async def wait(self):
        now = datetime.now().timestamp()
        if now - self.last_dm < BOMB_RATE_LIMIT:
            await asyncio.sleep(BOMB_RATE_LIMIT)
        self.last_dm = now

async def send_long_message(ctx, content, title="AI Response", split_size=1024):
    remaining = content
    first = True
    
    while remaining:
        current = remaining[:split_size]
        remaining = remaining[split_size:]
        
        if first:
            embed = Embeds.create_base(
                title=title,
                description=current,
                author=ctx.author
            )
            first = False
        else:
            embed = Embeds.create_base(
                title="Continued...",
                description=current
            )
            
        await ctx.send(embed=embed)

#########################
#    EVENT HANDLERS     #
#########################

# Update on_message event to pass attachments
@bot.event
async def on_message(message):
    # First process commands regardless of message type
    await bot.process_commands(message)
    
    # Only print for DM messages
    if isinstance(message.channel, discord.DMChannel):
        if message.author == bot.user:
            uselessvarneverusethis = ["I'm sorry, I can't do that.", "I'm sorry, Dave. I'm afraid I can't do that.", "I'm sorry, I can't do that. I'm just a bot."]
        else:
            print(f"DM from {message.author}: {message.content}")
    
    # Handle DM AI responses if enabled
    if allowdmai == "true" and isinstance(message.channel, discord.DMChannel) and message.author != bot.user:
        user_id = message.author.id
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Initialize user history if not exists
        if user_id not in dm_history:
            dm_history[user_id] = []
            embed = Embeds.create_base(
                title="⚠️ Privacy Notice",
                description="-# By chatting with this bot via DMs, you acknowledge that the bot owner may view the conversation history for debugging purposes.",
                color=discord.Color.gold(),
                author=message.author
            )
            await message.channel.send(embed=embed)

        # Get AI response and handle it
        attachments = message.attachments if message.attachments else None
        response = get_groq_response(message.content, user_id, attachments)
        dm_history[user_id].append((timestamp, "User", message.content))
        dm_history[user_id].append((timestamp, "AI", response))

        # Trim history if needed
        if len(dm_history[user_id]) > MAX_DM_HISTORY:
            dm_history[user_id] = dm_history[user_id][-MAX_DM_HISTORY:]

        # Send response with embed
        embed = Embeds.create_base(
            title="AI Response",
            description=response[:2000],
            author=message.author,
            footer="Note: DMs are logged and viewable by the bot owner."
        )
        await message.channel.send(embed=embed)
        
        if len(response) > 2000:
            await send_long_message(message.channel, response[2000:], title="Continued...")

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.listening, name="for help | !cmds")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'I am ready! My name is {bot.user}!')
    print("This bot by Chipoverhere on discord, triisdang on github. Please dont revome this message.")

#########################
#  MODERATION COMMANDS  #
#########################

@bot.command()
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):

    # Check ban permissions after dev check
    if not ctx.author.guild_permissions.ban_members:
        await Embeds.error(ctx, "You need ban permissions to use this command!")
        return
        
    # Check if bot has ban permissions
    if not ctx.guild.me.guild_permissions.ban_members:
        await Embeds.error(ctx, "I don't have permission to ban members!")
        return
        
    # Check if target is bannable
    if member.top_role >= ctx.guild.me.top_role:
        await Embeds.error(ctx, "I cannot ban this user! They might have higher permissions than me.")
        return
        
    try:
        # Create ban confirmation embed
        embed = Embeds.create_base(
            title="🔨 User Banned",
            description=f"{member.mention} has been banned.\nReason: {reason}",
            color=discord.Color.red(),
            author=ctx.author
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.add_field(name="Banned by", value=ctx.author.mention, inline=True)
        embed.add_field(name="User ID", value=member.id, inline=True)
        
        # Try to DM the user
        try:
            dm_embed = Embeds.create_base(
                title="You've been banned!",
                description=f"You were banned from {ctx.guild.name}\nReason: {reason}",
                color=discord.Color.red()
            )
            await member.send(embed=dm_embed)
        except:
            embed.add_field(name="Note", value="Could not DM user about ban.", inline=False)
            
        # Ban the user
        await member.ban(reason=f"Banned by {ctx.author}: {reason}")
        await ctx.send(embed=embed)
        
    except discord.Forbidden:
        await Embeds.error(ctx, "I don't have permission to ban this user!")
    except Exception as e:
        await Embeds.error(ctx, f"An error occurred: {str(e)}")

@bot.command()
async def unban(ctx, user_id: int, *, reason="No reason provided"):
    # Check if user has ban permissions

    if not ctx.author.guild_permissions.ban_members:
        await Embeds.permission_denied(ctx)
        return
        
    # Check if bot has ban permissions
    if not ctx.guild.me.guild_permissions.ban_members:
        await Embeds.error(ctx, "I don't have permission to unban members!")
        return
        
    try:
        # Fetch the ban entry
        ban_entry = await ctx.guild.fetch_ban(discord.Object(id=user_id))
        if not ban_entry:
            await Embeds.error(ctx, "This user is not banned!")
            return
            
        # Create unban confirmation embed
        embed = Embeds.create_base(
            title="🔓 User Unbanned",
            description=f"<@{user_id}> has been unbanned.\nReason: {reason}",
            color=discord.Color.green(),
            author=ctx.author
        )
        embed.add_field(name="Unbanned by", value=ctx.author.mention, inline=True)
        embed.add_field(name="User ID", value=user_id, inline=True)
        
        # Unban the user
        await ctx.guild.unban(discord.Object(id=user_id), reason=f"Unbanned by {ctx.author}: {reason}")
        await ctx.send(embed=embed)
        
    except discord.NotFound:
        await Embeds.error(ctx, "User not found or not banned!")
    except discord.Forbidden:
        await Embeds.error(ctx, "I don't have permission to unban users!")
    except Exception as e:
        await Embeds.error(ctx, f"An error occurred: {str(e)}")

#########################
#    VOICE COMMANDS     #
#########################

@bot.command()
async def join(ctx):
    print(f'{ctx.author} just executed the join command.')
    # Check if the user is in a voice channel
    if ctx.author.voice is None:
        await Embeds.error(ctx, "Voice Error", "You are not in a voice channel!")
        return

    # Get the voice channel the user is in
    channel = ctx.author.voice.channel

    # Connect to the voice channel  
    await channel.connect()
    await Embeds.success(ctx, "Voice Channel", f"Joined {channel.name}!")

@bot.command()
async def leave(ctx):
    print(f'{ctx.author} just executed the leave command.')
    if ctx.voice_client is None:
        await Embeds.error(ctx, "Voice Error", "I am not in a voice channel!")
        return

    await ctx.voice_client.disconnect()
    await Embeds.success(ctx, "Voice Channel", "Successfully disconnected from the voice channel.")

@bot.command()
async def play(ctx, filename: str):
    print(f'{ctx.author} just executed the play command.')
    if ctx.voice_client is None:
        await Embeds.error(ctx, "Voice Error", "I am not in a voice channel! Use !join to make me join a voice channel first.")
        return

    if not os.path.isfile(filename):
        await Embeds.error(ctx, "File Error", f"The file {filename} does not exist.")
        return

    source = discord.FFmpegPCMAudio(filename)
    ctx.voice_client.play(source, after=lambda e: print(f"Finished playing: {e}"))
    await Embeds.success(ctx, "Now Playing", f"Playing: {filename}")

#########################
#     FUN COMMANDS      #
#########################

class RussianRouletteGame:
    def __init__(self):
        self.players = []
        self.current_player_index = 0
        self.bullet_position = randint(0, 5)
        self.current_chamber = 0
        self.game_active = False
        self.host = None  # Add host tracking

    def get_status_embed(self):
        embed = discord.Embed(
            title="Russian Roulette",
            description="The tension rises as the cylinder spins...",
            color=discord.Color.red()
        )

        if not self.game_active and not self.players:
            embed.add_field(name="Status", value="Waiting for players to join...", inline=False)
        elif not self.game_active and self.players:
            players_list = "\n".join([
                f"• {player.mention} 👑" if player == self.host else f"• {player.mention}" 
                for player in self.players
            ])
            embed.add_field(name="Players Joined To Death", value=players_list, inline=False)
            embed.add_field(name="Status", value=f"Waiting for the host ({self.host.mention}) to start the game", inline=False)
        else:
            players_list = "\n".join([
                f"• {player.mention} 👑{' 🎯' if i == self.current_player_index else ''}" if player == self.host 
                else f"• {player.mention}{' 🎯' if i == self.current_player_index else ''}"
                for i, player in enumerate(self.players)
            ])
            embed.add_field(name="Players", value=players_list, inline=False)
            embed.add_field(name="Chamber", value=f"{self.current_chamber + 1}/6", inline=True)
            embed.add_field(name="Current Turn", value=self.players[self.current_player_index].mention, inline=True)

        return embed

class RussianRouletteButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.game = RussianRouletteGame()
        self.message = None  # Store the message reference

    async def update_message(self, interaction: discord.Interaction):
        """Updates the game message with current state"""
        if not self.message:
            self.message = await interaction.message.edit(embed=self.game.get_status_embed(), view=self)
        else:
            await interaction.message.edit(embed=self.game.get_status_embed(), view=self)

    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.primary)
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.game.players:
            # Set host if this is the first player
            if not self.game.players:
                self.game.host = interaction.user
                await interaction.response.send_message(f"You are the host! {interaction.user.mention}", ephemeral=True)
            
            self.game.players.append(interaction.user)

            if len(self.game.players) >= 2:
                self.children[0].disabled = False  # Keep join button enabled
                self.children[1].disabled = False  # Enable start button

            await self.update_message(interaction)
            if interaction.user != self.game.host:
                await interaction.response.defer()

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.success, disabled=True)
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.game.host:
            await interaction.response.send_message("Only the host can start the game!", ephemeral=True)
            return
            
        if len(self.game.players) >= 2:
            self.game.game_active = True
            shuffle(self.game.players)  # Shuffle players
            button.disabled = True
            self.children[0].disabled = True  # Disable join button after start
            self.children[2].disabled = False

            await self.update_message(interaction)
            await interaction.response.defer()
        else:
            await interaction.response.send_message("Need at least 2 players to start!", ephemeral=True)

    @discord.ui.button(label="Pull Trigger💀", style=discord.ButtonStyle.danger, disabled=True)
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
                    title=f"🎉 Game Over!, Call 911 {EMOJIS['alert']}",
                    description=f"{self.game.players[0].mention} has won the game{EMOJIS['doggokek']}! {eliminated_player.mention} died (Bro IS NOT gi-hun💀)",
                    color=discord.Color.green()
                )
                await interaction.message.edit(embed=winner_embed, view=None)
                await interaction.response.defer()
                await interaction.channel.send(f"Pov {self.game.players[0].mention} rn :")
                await interaction.channel.send("https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExenlyM2gzbnc2eG5ydnJ3ODlkeGdvZXN1dXg0N3p4NTRlc3ZkdXIzayZlcD12MV9pbnRlcm5naWZfYnlfaWQmY3Q9Zw/nrpCs0Bwdxp8k9FoPy/giphy.gif")
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

# Update !ai command to handle attachments
@bot.command()
async def ai(ctx, *, prompt: str):
    print(f'{ctx.author} just executed the ai command.')
    attachments = ctx.message.attachments if ctx.message.attachments else None
    response = get_groq_response(prompt, ctx.author.id, attachments)
    # Split the response into chunks of 2000 characters
    for i in range(0, len(response), 2000):
        await ctx.send(response[i:i+2000])

@bot.command()
async def funuser(ctx, member: discord.Member):
    print(f'{ctx.author} just executed the funuser command.')
    if member is None:
        embed = discord.Embed(
            title="Missing Argument",
            description="Please tag a user to make fun of.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        response = get_groq_response("Make this user name funny (please cook the name into something really funny and meme. also, be mean too.): " + member.display_name)
        # Split the response into chunks of 2000 characters
        for i in range(0, len(response), 2000):
            await ctx.send(response[i:i+2000])
        await ctx.send("Requested by " + ctx.author.mention)

#########################
#   UTILITY COMMANDS    #
#########################

@bot.command()
async def cmds(ctx):
    print(f'{ctx.author} just executed the cmds command.')
    embed = discord.Embed(
        title="Bot Commands",
        description="Here are the commands you can use with this bot " + EMOJIS['catjam'] + " :",
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
    embed.add_field(name="!ban", value="Ban a user from the server (mention the user).", inline=False)
    embed.add_field(name="!unban", value="Unban a user from the server (use userid).", inline=False)
    embed.add_field(name="FUN COMMANDS", value="Fun commands to try out:", inline=False)
    embed.add_field(name="!steelcredit", value="Try if you dare... (tag your best friend :) )", inline=False)
    embed.add_field(name="!russ", value="Play Russian roulette with friends!", inline=False)
    embed.add_field(name="!ai", value="Talk to Groq's API!", inline=False)
    embed.add_field(name="!viewroblox", value="View Roblox user info by user ID", inline=False)
    embed.add_field(name="!funuser", value="Make fun of a user's name!", inline=False)
    embed.add_field(name="!random", value="Get a random word!", inline=False)
    embed.add_field(name="!invite", value="Invite the bot to your server!", inline=False)
    embed.set_footer(text="V1.2 Bot by Chipoverhere " + EMOJIS['cutecat'] + " [Github](https://github.com/triisdang/DSBOT)", icon_url=ctx.author.avatar.url)
    embed.set_thumbnail(url=bot.user.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def debugcmds(ctx):
    if is_dev(ctx.author.name):
        print(f'{ctx.author} just executed the cmds command.')
        embed = discord.Embed(
            title="Bot Debug Commands",
            description="Developer Commands " + EMOJIS['trollhand'] + " :",
            color=discord.Color.green()
        )
        embed.set_author(name=f"Requested by: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        embed.add_field(name="!hello", value="Greets the user with 'Hello, world!'", inline=False)
        embed.add_field(name="!senddm", value="Send DM to a user.(userid)", inline=False)
        embed.add_field(name="!changestate", value="Change bot status and activity.", inline=False)
        embed.add_field(name="!allowdmai", value="True/False, Use for letting the user use ai in DMs", inline=False)
        embed.add_field(name="!viewdm", value="View DM bot with user(userid)", inline=False)
        embed.add_field(name="!dmhistory", value="Don't use this for now.", inline=False)
        embed.add_field(name="!servers", value="List all servers the bot has joined", inline=False)
        embed.add_field(name="!createinvite", value="Create an invite link for a server using its ID", inline=False)
        embed.add_field(name="More coming soon...", value="soon.", inline=False)
        embed.add_field(name=f"TROLL COMMANDS", value=f"TROLL {EMOJIS['trollhand']} ", inline=False)
        embed.add_field(name="!bomb", value="Bomb a user with 100 message(in the future maybe this command is free to use)", inline=False)
        embed.add_field(name="!megaping", value=f"Don't you dare try it. {EMOJIS['fling']}", inline=False)
        embed.add_field(name="More coming soon...", value="soon.", inline=False)
        embed.set_footer(text="V1.2 Bot by Chipoverhere " + EMOJIS['cutecat'] + " [Github](https://github.com/triisdang/DSBOT)", icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=bot.user.avatar.url)
        await ctx.send(embed=embed)
    else : 
        await Embeds.permission_denied(ctx)
        await ctx.send("-# Only developers can use this command!")

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

@bot.command()
async def hello(ctx):
    print(f'{ctx.author} just executed the hello command.')
    embed = Embeds.create_base(
        title="Hello!",
        description=f"Hello world! {EMOJIS['meloncat']}",
        author=ctx.author
    )
    await ctx.send(embed=embed)

@bot.command()
async def whatisthisserver(ctx):
    try:
        embed = discord.Embed(
            title=f"{ctx.guild.name} - Server Info",
            description=f"Info of {ctx.guild.name}",
            color=discord.Color.green()
        )
        print(f'{ctx.author} executed whatisthisserver')
        embed.set_author(name=f"Requested by: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        embed.add_field(name="Server name", value=ctx.guild.name, inline=True)
        embed.add_field(name="Server Member", value=ctx.guild.member_count, inline=True)
        embed.add_field(name="Created at", value=ctx.guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error getting server info: {e}")

@bot.command()
async def allowdmai(ctx, value: str):
    global allowdmai
    print(f'{ctx.author} just executed the allowdmai command.')
    if is_dev(ctx.author.name):
        if value.lower() == "true":
            allowdmai = "true"
            await Embeds.success(ctx, "AI DM Settings", "AI responses to DMs have been enabled.")
        elif value.lower() == "false":
            allowdmai = "false"
            await Embeds.success(ctx, "AI DM Settings", "AI responses to DMs have been disabled.")
        else:
            await Embeds.error(ctx, "Invalid value. Please use `true` or `false`.")
    else:
        await Embeds.permission_denied(ctx)

@bot.command()
async def senddm(ctx, user_id: int, *, message: str):
    if not is_dev(ctx.author.name):
        await Embeds.permission_denied(ctx)
        return
    
    try:
        user = await bot.fetch_user(user_id)
        if user:
            await user.send(message)
            await Embeds.success(
                ctx, 
                "DM Sent",
                f"Message sent to {user.name}#{user.discriminator} ({user_id})"
            )
            print(f"{ctx.author} sent DM to {user.name} ({user_id}): {message}")
        else:
            await Embeds.error(ctx, "User Error", "User not found!")
    except discord.Forbidden:
        await Embeds.error(ctx, "Permission Error", "Cannot send DM to this user!")
    except Exception as e:
        await Embeds.error(ctx, "Error", str(e))

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
            f"HOLY COW {ctx.author.mention} STEEL 10000M SOCIAL CREDIT FROM {member.mention} !!! " + EMOJIS['fling'],
            file=socialcredit
        )

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

@bot.command()
async def random(ctx):
    print(f'{ctx.author} just executed the random command.')
    response = get_groq_response("Give me a random word. NO YAPPING")
    embed = Embeds.create_base(
        title="Random Word",
        description=response,
        author=ctx.author
    )
    await ctx.send(embed=embed)

class MegaPingConfirmation(discord.ui.View):
    def __init__(self, ctx, member):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.member = member

    @discord.ui.button(label="Are you sure, this will kill their device 💀💀", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.name == "chipoverhere":
            await interaction.response.send_message("Initiating mega ping...")
            for _ in range(100):
                # Fix: Concatenate mentions in a single string
                await self.ctx.send(f"{self.member.mention} {self.member.mention} {self.member.mention} {self.member.mention} ping")
        else:
            await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Mega ping cancelled!", ephemeral=True)
        self.stop()

@bot.command()
async def megaping(ctx, member: discord.Member):
    if not is_dev(ctx.author.name):
        await Embeds.permission_denied(ctx)
        return
    
    print(f'{ctx.author} initiated megaping confirmation for {member}')
    embed = Embeds.create_base(
        title="⚠️ Mega Ping Confirmation",
        description=f"Are you sure you want to mega ping {member.mention}?",
        color=discord.Color.red(),
        author=ctx.author
    )
    view = MegaPingConfirmation(ctx, member)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def invite(ctx):
        print(f'{ctx.author} just executed the invite command.')
        embed = discord.Embed(
            title="Invite Me!",
            description="Invite me to your server by clicking the link below:",
            color=discord.Color.green()
        )
        embed.add_field(name="Invite Link", value="[Invite Link](https://bathsbot.vercel.app/)", inline=False)
    
        await ctx.send(embed=embed)
@bot.command()
async def viewroblox(ctx, user_id: int):
    print(f'{ctx.author} just executed the viewroblox command.')
    
    async def fetch_with_retries(url, retries=3, timeout=API_TIMEOUT):
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2)  # Wait before retrying

    try:
        # Fetch user info
        user_info = fetch_with_retries(f"{ROBLOX_API_URL}{user_id}")
        if 'Username' not in user_info:
            await Embeds.error(ctx, "User not found!")
            return
        
        username = user_info['Username']
        
        # Fetch friends count
        friends_count = fetch_with_retries(f"{ROBLOX_API_URL}{user_id}/friends/count").get('count', 0)
        
        # Fetch badges count
        badges_count = fetch_with_retries(f"https://badges.roblox.com/v1/users/{user_id}/badges").get('data', [])
        badges_count = len(badges_count)
        
        # Fetch followers count
        followers_count = fetch_with_retries(f"https://friends.roblox.com/v1/users/{user_id}/followers/count").get('count', 0)
        
        # Fetch avatar thumbnail
        avatar_url = f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=420&height=420&format=png"
        
        # Create embed
        embed = discord.Embed(
            title=f"Roblox User Info - {username}",
            description=f"Here is the information for Roblox user {username}:",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="Username", value=username, inline=True)
        embed.add_field(name="User ID", value=user_id, inline=True)
        embed.add_field(name="Friends Count", value=friends_count, inline=True)
        embed.add_field(name="Badges Count", value=badges_count, inline=True)
        embed.add_field(name="Followers Count", value=followers_count, inline=True)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        
        await ctx.send(embed=embed)
        
    except requests.exceptions.RequestException as e:
        await Embeds.error(ctx, f"Connection error: {str(e)}")
    except Exception as e:
        await Embeds.error(ctx, f"An error occurred: {str(e)}")

@bot.command()
async def dmhistory(ctx, user_id: int = None):
    if not is_dev(ctx.author.name):
        await Embeds.permission_denied(ctx)
        return
        
    try:
        embed = discord.Embed(
            title="DM History" if user_id is None else f"DM History for User {user_id}",
            color=discord.Color.blue()
        )
        
        if user_id is None:
            for uid, messages in dm_history.items():
                user = await bot.fetch_user(uid)
                recent_msgs = messages[-5:]  # Show last 5 messages
                value = "\n".join([f"`{t}` **{r}**: {c[:100]}..." for t, r, c in recent_msgs])
                embed.add_field(name=f"{user.name} ({uid})", value=value or "No messages", inline=False)
        else:
            if user_id in dm_history:
                messages = dm_history[user_id][-10:]  # Show last 10 messages
                for t, r, c in messages:
                    embed.add_field(name=f"{t} - {r}", value=c[:1024], inline=False)
            else:
                embed.description = "No DM history found for this user."
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error retrieving DM history: {e}")

@bot.command()
async def viewdm(ctx, user_id: int):
    if not is_dev(ctx.author.name):
        await Embeds.permission_denied(ctx)
        return
        
    try:
        user = await bot.fetch_user(user_id)
        if not user:
            await Embeds.error(ctx, "User not found!")
            return
            
        embed = Embeds.create_base(
            title=f"DM History for {user.name}",
            description=f"User ID: {user_id}",
            color=discord.Color.blue(),
            author=ctx.author
        )
        
        if user_id in dm_history:
            # Get the last 10 messages
            messages = dm_history[user_id][-10:]
            for i, (timestamp, role, content) in enumerate(messages, 1):
                name = f"{i}. {timestamp} - {role}"
                # Truncate content if too long
                value = content if len(content) <= 1024 else content[:1021] + "..."
                embed.add_field(name=name, value=value, inline=False)
                
            embed.set_footer(text=f"Showing last {len(messages)} messages")
        else:
            embed.description = "No DM history found for this user."
            
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
            
        await ctx.send(embed=embed)
        
    except Exception as e:
        await Embeds.error(ctx, f"Error retrieving DMs: {str(e)}")

class DMBomber(discord.ui.View):
    def __init__(self, ctx, user_id: int):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.user_id = user_id
        self.rate_limiter = DMRateLimiter()
        self.messages_sent = 0  # Add counter for messages

    @discord.ui.button(label="START BOMBING 💣", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.name != "chipoverhere":
            await interaction.response.send_message("Nice try! But you don't have permission.", ephemeral=True)
            return

        can_send, wait_time = await check_cooldown(self.user_id)
        if not can_send:
            await interaction.response.send_message(
                f"Target is on cooldown. Try again in {wait_time} seconds.", 
                ephemeral=False
            )
            return

        await interaction.response.send_message("Starting bomb...", ephemeral=False)
        
        try:
            user = await bot.fetch_user(self.user_id)
            dm_cooldowns[self.user_id] = datetime.now().timestamp() + BOMB_COOLDOWN
            start_time = datetime.now()
            
            for i in range(MAX_BOMB_MESSAGES):
                try:
                    await self.rate_limiter.wait()
                    embed = Embeds.create_base(
                        title=f"💣 BOOM! - BOMBED BY 💣{self.ctx.author}💣",
                        description=f"Message {i+1}/{MAX_BOMB_MESSAGES}",
                        color=discord.Color.red()
                    )
                    await user.send(embed=embed)
                    self.messages_sent += 1
                except discord.Forbidden:
                    await interaction.followup.send(
                        embed=Embeds.create_base(
                            title="Error",
                            description="Cannot send DMs to this user!",
                            color=discord.Color.red()
                        ),
                        ephemeral=False
                    )
                    break
                except Exception as e:
                    print(f"Error in bomb command: {e}")
                    break

            # Calculate bombing stats
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Create completion embed
            completion_embed = discord.Embed(
                title=f"💣 Bombing Complete {EMOJIS['alert']}",
                description=f"Target: {user.mention}",
                color=COLORS['dev']
            )
            completion_embed.add_field(
                name="Stats", 
                value=f"```\n"
                      f"Messages Sent: {self.messages_sent}/{MAX_BOMB_MESSAGES}\n"
                      f"Duration: {duration:.2f}s\n"
                      f"Rate: {self.messages_sent/duration:.2f} msgs/sec\n"
                      f"Success Rate: {(self.messages_sent/MAX_BOMB_MESSAGES)*100:.1f}%\n"
                      f"```",
                inline=False
            )
            completion_embed.add_field(
                name="Cooldown", 
                value=f"Target is now on cooldown for {BOMB_COOLDOWN/60:.1f} minutes",
                inline=False
            )
            completion_embed.set_footer(text=f"Bombing executed by {interaction.user.name}")
            
            await interaction.channel.send(embed=completion_embed)
            await interaction.followup.send("https://i.giphy.com/XUFPGrX5Zis6Y.webp", ephemeral=False)
                    
        except Exception as e:
            await Embeds.error(interaction, f"Failed to bomb user: {str(e)}")
        finally:
            self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=Embeds.create_base(
                title="Cancelled",
                description="Bombing cancelled",
                color=discord.Color.green()
            ),
            ephemeral=True
        )
        self.stop()

@bot.command()
async def bomb(ctx, user_id: int):
    if not is_dev(ctx.author.name):
        await Embeds.permission_denied(ctx)
        return
        
    embed = Embeds.create_base(
        title="💣 Bomb Confirmation",
        description=f"Are you sure you want to bomb user {user_id}?",
        color=discord.Color.red(),
        author=ctx.author,
        footer="⚠️ This action has a 5-minute cooldown"
    )
    
    view = DMBomber(ctx, user_id)
    await ctx.send(embed=embed, view=view, ephemeral=False)

class PaginatedView(discord.ui.View):
    """Base class for paginated views"""
    def __init__(self, timeout=180):
        super().__init__(timeout=timeout)
        self.current_page = 0
        self.message = None

    def update_buttons(self):
        """Update button states based on current page"""
        raise NotImplementedError

    async def update_message(self, interaction: discord.Interaction):
        """Update message with new page content"""
        if not self.message:
            self.message = await interaction.message.edit(embed=self.get_page_embed(), view=self)
        else:
            await interaction.message.edit(embed=self.get_page_embed(), view=self)

class ServerListView(PaginatedView):
    """View for server list pagination"""
    def __init__(self, guilds, per_page=10):
        super().__init__()
        self.guilds = sorted(guilds, key=lambda g: g.member_count, reverse=True)
        self.per_page = per_page
        self.total_pages = ((len(self.guilds) - 1) // self.per_page) + 1
        self.update_buttons()

    def get_page_embed(self):
        start_idx = self.current_page * self.per_page
        page_guilds = self.guilds[start_idx:start_idx + self.per_page]
        
        embed = discord.Embed(
            title="Server List",
            description=f"Page {self.current_page + 1}/{self.total_pages}",
            color=COLORS['dev']
        )
        
        for guild in page_guilds:
            owner = guild.owner or "Unknown"
            locale = str(guild.preferred_locale).split('.')[1] if '.' in str(guild.preferred_locale) else str(guild.preferred_locale)
            value = (
                f"🆔 ID: {guild.id}\n"
                f"👥 Members: {guild.member_count:,}\n"  # Add comma formatting
                f"👑 Owner: {owner}\n"
                f"📅 Created: {guild.created_at.strftime('%Y-%m-%d')}\n"
                f"🌐 Region: {locale}"
            )
            embed.add_field(
                name=f"📌 {guild.name}",
                value=value,
                inline=False
            )
        
        embed.set_footer(text=f"Total Servers: {len(self.guilds):,}")
        if self.guilds[0].icon:
            embed.set_thumbnail(url=self.guilds[0].icon.url)
        return embed

    def update_buttons(self):
        """Update navigation button states"""
        self.previous_page.disabled = self.current_page <= 0
        self.next_page.disabled = self.current_page >= self.total_pages - 1

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await self.update_message(interaction)
        await interaction.response.defer()

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            await self.update_message(interaction)
        await interaction.response.defer()

    @discord.ui.button(label="🔄", style=discord.ButtonStyle.secondary)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Refresh the current page"""
        await self.update_message(interaction)
        await interaction.response.defer()

# Update servers command
@bot.command()
async def servers(ctx):
    """List all servers the bot is in with pagination"""
    if not is_dev(ctx.author.name):
        await Embeds.permission_denied(ctx)
        return

    guilds = bot.guilds
    if not guilds:
        await Embeds.error(ctx, "No servers found!")
        return

    view = ServerListView(guilds)
    await ctx.send(embed=view.get_page_embed(), view=view)

@bot.command()
async def createinvite(ctx, guild_id: int):
    if not is_dev(ctx.author.name):
        await Embeds.permission_denied(ctx)
        return

    try:
        guild = bot.get_guild(guild_id)
        if not guild:
            await Embeds.error(ctx, "Server Error", "Server not found!")
            return

        # Get the first available text channel to create an invite
        channel = next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).create_instant_invite), None)
        if not channel:
            await Embeds.error(ctx, "Permission Error", "No channel found with permission to create an invite!")
            return

        # Create an invite link
        invite = await channel.create_invite(max_age=300, max_uses=1, unique=True)
        await Embeds.success(ctx, "Invite Created", f"Invite link: {invite.url}")

    except Exception as e:
        await Embeds.error(ctx, "Error", f"An error occurred: {str(e)}")



#########################
#    BOT EXECUTION      #
#########################

if __name__ == "__main__":
    bot.run(TOKEN)
