import asyncio
import logging
from webserver import keep_alive
import aiohttp
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
import lxml

intents = discord.Intents.default()

# Initiate logging
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

bot = commands.Bot(command_prefix="&", intents=intents)
bot.remove_command("help")


@bot.event
async def on_ready():
	print("Successfully logged in to discord.")


@bot.command()
async def help(ctx):
	# Rewrote help command and overrode default implementation.
	# This way, the help commmand looks slightly nicer, and sends
	# information to the author's DM, rather than clogging up
	# server channels with a one-message help command.
	# Realistically, it doesn't even need to be implemented, but here
	# we are. So... DM it is.
	embed = discord.Embed(
	    title="Help Page",
	    description="This bot is a NationStates API recruitment client. Only "
	    "those with express permission can use it.\n\n**Command "
	    "Structure**\n&recruit {Client Key} {Telegram ID} {Secret "
	    "Key}{Your NS Nation} {number of telegrams} {region}",
	)
	await ctx.author.send(embed=embed)
	await ctx.send("Check your DMs!")


@bot.command()
async def recruit(ctx):
	def check(m):
		chk = False
		if m.author == ctx.author and m.author.bot is not True:
			chk = True
		return chk

	# Get client information
	await ctx.send("Please enter your client key")
	client = await bot.wait_for("message", check=check)
	await ctx.send("Please enter your TGID")
	tgid = await bot.wait_for("message", check=check)
	await ctx.send("Please enter your secret key")
	skey = await bot.wait_for("message", check=check)
	await ctx.send(
	    "Please enter a useragent. This should ideally be your main nation on nationstates.net"
	)
	uagent = await bot.wait_for("message", check=check)
	await ctx.send("Please enter the number of telegrams you wish to send")
	numtgs = await bot.wait_for("message", check=check)
	await ctx.send("Please enter the region you wish to recruit for")
	reg = await bot.wait_for("message", check=check)

	authring = {
	    "client": client.content,
	    "tgid": tgid.content,
	    "secret key": skey.content,
	    "user agent": uagent.content,
	    "number": int(numtgs.content),
	    "region": reg.content,
	}

	lim = 12
	await ctx.channel.purge(limit=lim)

	i = 0
	while i < int(numtgs.content):
		headers = {"User-Agent": authring["user agent"]}
		async with aiohttp.ClientSession() as session:
			async with session.get(
			    "https://www.nationstates.net/cgi-bin/api.cgi?q=newnations",
			    headers=headers) as req:
				entry = await req.text()
				soup = BeautifulSoup(entry, "lxml")
				natlist = soup.newnations.string
				r_list = natlist.split(",")
				for new in r_list[:5]:
					async with session.get(
					    f"https://nationstates.net/cgi-bin/api.cgi?nation={new}&q=tgcanrecruit",
					    headers=headers) as que:
						queue = await que.text()
						
					canrec_soup = BeautifulSoup(queue, "lxml")
					val = canrec_soup.tgcanrecruit.string
					if int(val) == 0:
						await session.get(
						    f"https://nationstates.net/cgi-bin/api.cgi?a=sendTG&"
						    f"client={authring['client']}&tgid={authring['tgid']}&key="
						    f"{authring['secret key']}&to={new}")
						await ctx.send(
						    "Telegram sent... waiting for API limit to expire."
						)
						await asyncio.sleep(180)
					else:
						await asyncio.sleep(0.6)
						await ctx.send(
						    "Target unable to be recruited. Moving to next one..."
						)
	i = i + 1


keep_alive()

