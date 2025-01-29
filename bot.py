import discord
from discord.ext import commands

token = "MTMyMjkxMzU3MDYxMDIyMTEzMA.GsSV2a.cTraUWbcefv5rTpXX1Isi-A1XbA_eISbVIlNUc"

# Pair emojis
fling = "<:fling:1334142789788897352>"
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

# When the bot is ready
@bot.event
async def on_ready():
    print(f'I am ready! My name is {bot.user}!')

# Test command
@bot.command()
async def hello(ctx):
    await ctx.send("Hello cc! " + meloncat)

# A command that displays server information
@bot.command()
async def whatisthiserver(ctx):
    await ctx.send(
        f"This is {ctx.guild.name} server, created at {ctx.guild.created_at} and has {ctx.guild.member_count} members!"
    )

# A command that displays the bot's commands
@bot.command()
async def cmds(ctx):
    embed = discord.Embed(
        title="Bot Commands",
        description="Here are the commands you can use with this bot " + catjam + " :",
        color=discord.Color.green()
    )
    embed.set_author(name=f"Requested by: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
    embed.add_field(name="!hello", value="Greets the user with 'Hello, world!'", inline=False)
    embed.add_field(name="!whatisthiserver", value="Displays server information.", inline=False)
    embed.add_field(name="!cmds", value="Displays this help message.", inline=False)
    embed.add_field(name="!userinfo", value="View user info of a user (tag them to view).", inline=False)
    embed.add_field(name="FUN COMMANDS", value="Fun commands to try out:", inline=False)
    embed.add_field(name="!steelcredit", value="Try if you dare... (tag your best friend :) )", inline=False)
    embed.set_footer(text="Bot by Chipoverhere " + cutecat)
    await ctx.send(embed=embed)

# A command that steals social credit
@bot.command()
async def steelcredit(ctx, member: discord.Member = None):
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

# Run the bot using the token you copied earlier
bot.run(token)