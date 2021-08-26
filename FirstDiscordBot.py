import discord
from discord.ext import commands
import random
import time
import giphy_client
from giphy_client.rest import ApiException
from tabulate import tabulate
import pandas
import discord_config


# Allows access to the member lists 
intents = discord.Intents.default()
intents.members = True
intents.messages = True

# Registers a command prefix for any following command 
bot = commands.Bot(command_prefix='$', intents = intents)


# User class will keep track of all data linked to each user 
# in the server, including their daily multiplier, timers, coins, 
# and possibly other stats

class User:
	name = ""

	balance = 0
	work_last = 0
	guess_game = False
	guess_number = 0
	guess_turn = 5
	guess_bet = 0

	daily_streak = 0
	last_day = 0

	roulette_game = False
	current_chamber = 0
	loaded = []
	roulette_winnings = 0
	roulette_bet = 0


	def __init__(self, username):
		self.username = username


users = {}
users_created = False
listed_members = []



# Create an instance of the API class
api_instance = giphy_client.DefaultApi()




@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    # users_created = False


async def search_gifs(query):
    try:
    	response = api_instance.gifs_search_get(discord_config.giphy_token, query, limit=3, rating='g')
    	lst = list(response.data)
    	return lst[0].url

    except ApiException as e:
        return "Exception when calling DefaultApi->gifs_search_get: %s\n" % e

async def search_gifs_rand(query):
    try:
    	response = api_instance.gifs_search_get(discord_config.giphy_token, query, limit = 10, rating='g')
    	lst = list(response.data)
    	gif = random.choices(lst)
    	return gif[0].url

    except ApiException as e:
        return "Exception when calling DefaultApi->gifs_search_get: %s\n" % e





@bot.event 
async def on_message(message):

	global users_created
	roll = random.randint(1, 10)

	# Some fun ways for the bot to interact with users automatically
	if "bot" in message.content.lower():
		if message.author.bot:
			return
		if roll < 7:
			await message.channel.send("What you lookin' at")

	elif "i love" in message.content.lower():
		if message.author.bot:
			return
		if roll < 4:
			await message.channel.send("I love you too")

	elif "noice" in message.content.lower():
		gif = await search_gifs('noice')
		await message.channel.send(gif)

	elif "bastard" in message.content.lower():
		if message.author.bot:
			return
		if roll < 7:
			await message.channel.send(":(")

	# Creates user profiles for all members upon the first message
	if users_created == False:
		memberList = message.guild.members
		for i in memberList:
			# print(type(i.nick))
			if i.nick is None:
				users.update({i.id : User(i.name)})
			else:
				users.update({i.id : User(i.nick)})

	users_created = True
	await bot.process_commands(message)



	# The brunt of the code for the games go here after initialization to allow for messages to be read outside of the command
	# Data for the games is tracked in the user object, such as turns and bet amounts
	if users[message.author.id].roulette_game == True:

		if "stop" in message.content.lower():
			await message.channel.send("You win {}!".format(int(users[message.author.id].roulette_winnings)))
			users[message.author.id].balance += int(users[message.author.id].roulette_winnings + users[message.author.id].roulette_bet)
			users[message.author.id].roulette_winnings = 0
			users[message.author.id].roulette_bet = 0
			users[message.author.id].roulette_game = False
			return
		if "continue" in message.content.lower():
			await message.channel.send("You choose to continue and fire the next chamber")
			time.sleep(2)
			if users[message.author.id].loaded[users[message.author.id].current_chamber] == 1:
				await message.channel.send("Sorry, you lost {}".format(int(users[message.author.id].roulette_winnings)))
				users[message.author.id].roulette_game = False
				users[message.author.id].roulette_winnings = 0
				users[message.author.id].roulette_bet = 0
				return
			else:
				new_winnings = int(users[message.author.id].roulette_winnings * (1.15 ** (users[message.author.id].current_chamber + 1)))
				users[message.author.id].roulette_winnings = int(new_winnings)
				users[message.author.id].current_chamber += 1

				if users[message.author.id].current_chamber == 5:
					users[message.author.id].roulette_winnings = int(users[message.author.id].roulette_winnings * 2)
					users[message.author.id].balance += int(users[message.author.id].roulette_winnings + users[message.author.id].roulette_bet)
					await message.channel.send("You pull the trigger and nothing happens. As there is only one round left to have the bullet, you "
						+ "won the game and have earned the maximum amount of {} coins! Congrats!".format(new_winnings * 2))
					users[message.author.id].roulette_winnings = 0
					users[message.author.id].roulette_bet = 0
					users[ctx.author.id].roulette_game = False

					return
				await message.channel.send("You pull the trigger and nothing happens. Reply stop to take your earnings of {} coins or continue to fire the next chamber".format(new_winnings))







	if users[message.author.id].guess_game == True:	

		print(type(message.content))
		if type(int(message.content)) == int:
			if users[message.author.id].guess_turn == 1:
				users[message.author.id].guess_game = False
				await message.channel.send("Sorry, the number was {}. You lost {}".format(users[message.author.id].guess_number, users[message.author.id].guess_bet))
			else:

				response = int(message.content)

				if response > users[message.author.id].guess_number:
					users[message.author.id].guess_turn -= 1
					await message.channel.send("The number is lower than {}. You have {} guesses remaining".format(message.content, users[message.author.id].guess_turn))
				elif users[message.author.id].guess_number > response:
					users[message.author.id].guess_turn -= 1
					await message.channel.send("The number is higher than {}. You have {} guesses remaining".format(message.content, users[message.author.id].guess_turn))
				else:
					users[message.author.id].guess_game = False
					users[message.author.id].balance += users[message.author.id].guess_bet * users[message.author.id].guess_turn 
					await message.channel.send("You got it right! You win {}!".format(users[message.author.id].guess_bet))
				
	





@bot.command(brief = 'Prints a list of member instances to terminal -- testing only')
async def members(ctx):
	memberList = ctx.guild.members
	for i in memberList:
		users.update({i.id: User(i.nick)})
	print(users)

# Replies a random gif from a list associated with the request. Defaults to a dab
@bot.command(brief = 'Replies a gif')
async def gif(ctx, request = "dab"):
	send_gif = await search_gifs_rand(request)
	await ctx.send(send_gif)

# Text command
@bot.command(brief = 'Dabs')
async def dab(ctx):
	await ctx.send('Dab on em !')


@bot.command(brief = "Gives list of members")
async def list_members(ctx):
	print(users)
	for i in users:
		# await ctx.send(users[i])
		print(users[i])
		print(users[i].username)
		listed_members.append(users[i].username)
		# await ctx.send(users[i].name)
	await ctx.send(listed_members)


# Gives coins. Can be done by any user as of now without restriction. May eventually restrict this to certain roles only
@bot.command(brief = 'Gives coins to user')
async def give_coins(ctx, amount = -1, username = "null"):
	if amount < 0:
		await ctx.send("Input an amount greater than zero")
		return
	if username == "null":
		await ctx.send("Input a user to send coins to (ex. @kinghunts)")
		return
	strip_tag = username.replace('@', '')
	strip_encloser_one = strip_tag.replace("<", "")
	strip_encloser_two = strip_encloser_one.replace(">", "")
	person = strip_encloser_two.replace("!", "")
	person_id = int(person)
	print(person_id)
	users[person_id].balance += amount

	await ctx.send("You gave {} {} coins".format(username, amount))



# Gives a user a coin amount per day with multipliers tracked in user object
@bot.command(brief = "Collects daily coins amount", description = "Collects coins for the day with a multiplier given for consecutive days collected")
async def daily(ctx):
	time.sleep(2)
	current_day = time.strftime("%d", time.gmtime())
	print(current_day)
	print(time.gmtime())

	if (int(current_day) - users[ctx.author.id].last_day) == 0:
		await ctx.send("Return tomorrow for your daily award!")
		return
	if (int(current_day) - users[ctx.author.id].last_day) > 1:
		users[ctx.author.id].daily_streak = 0
	users[ctx.author.id].last_day = int(current_day)

	users[ctx.author.id].daily_streak += 1
	if users[ctx.author.id].daily_streak > 28:
		daily_amount = 40
	elif users[ctx.author.id].daily_streak > 21:
		daily_amount = 35
	elif users[ctx.author.id].daily_streak > 14:
		daily_amount = 30
	else:
		daily_amount = 25
	earned_amount = 50 + (daily_amount * users[ctx.author.id].daily_streak)
	users[ctx.author.id].balance += earned_amount
	await ctx.send("You earned {} coins and have a streak of {} days! Come back tomorrow to collect again"
		.format(earned_amount, users[ctx.author.id].daily_streak))




# Similar to daily, but no streaks and on a shorter basis
@bot.command(brief = 'Begins working for coins', description = 'Generates an amount of coins that can be collected after an hour has passed. ' 
	+ 'Doing $work before the hour has passed will let you know how much time is left before collection.')
async def work(ctx):
	current_time = time.time()
	work_time = users[ctx.author.id].work_last

	if work_time == 0:
		users[ctx.author.id].work_last = current_time
		await ctx.send("You started working. Return in an hour to collect your earnings")
	elif current_time - work_time < 3600:
		await ctx.send("Please return in {} minutes to collect your earnings".format(round((3600 - (current_time - work_time)) / 60)))
	else:
		earnings = random.randint(80, 200)
		users[ctx.author.id].balance += earnings
		await ctx.send("You earned {} coins from working. Return in an hour to claim your next paycheck".format(earnings))



# These commands start the games 
@bot.command(brief = 'Starts the guessing game', description = 'Requires a bet amount and starts the guessing game, which generates a number between 1 and 100 to guess' 
	+ ' in five turns. Guessing it earlier will award an additional multiplier on the bet.')
async def guess(ctx, bet = -1):
	if bet < 0:
		await ctx.send("Input a positive bet amount")
		return
	answer = random.randint(1, 100)
	users[ctx.author.id].guess_bet = bet
	if users[ctx.author.id].balance - bet < 0:
		await ctx.send("Sorry, you cannot afford that bet")
	else:
		users[ctx.author.id].balance -= bet
		users[ctx.author.id].guess_game = True
		users[ctx.author.id].guess_turn = 5
		users[ctx.author.id].guess_number = answer
		await ctx.send("You bet {} and start the mysterious machine. You have five attempts to guess the number between 1 and 100. Type your answer".format(bet))


# Unfinished -- may or may not get to
@bot.command(brief = "Starts a game of rock, paper, scissors", description = "Requires bet. Starts a game of rock paper scissors. If you both pick the same"
	+ " choice, you will be given your bet back.")
async def rps(ctx, bet = -1):
	if bet < 0:
		await ctx.send("Please input a positive bet amount")





@bot.command(brief = "Starts a game of roulette", description = "Requires bet. Starts a game of roulette, where a bullet is placed in a random chamber out of six"
	+ " of the virtual revolver. Each turn, you will get the option to try the next chamber with rewards increasing based on how many chambers remain." 
	+ " The fewer chambers remain, the more likely for the bullet to be in one. If you get virtually shot, you lose your earnings and bet.")
async def roulette(ctx, bet = -1):
	if bet < 0:
		await ctx.send("Please input a positive bet amount")
		return
	if users[ctx.author.id].balance - bet < 0:
		await ctx.send("Sorry, you cannot afford that bet")
		return
	users[ctx.author.id].roulette_bet = bet
	users[ctx.author.id].balance -= bet
	users[ctx.author.id].roulette_game = True
	revolver = [0, 0, 0, 0, 0, 0]
	bullet = random.randint(0, 5)
	revolver[bullet] = 1
	users[ctx.author.id].loaded = revolver
	await ctx.send("You bet {} and spin the revolver".format(bet))
	time.sleep(2)

	if revolver[0] == 1:
		await ctx.send("Sorry, you lost {}".format(bet))
		users[ctx.author.id].roulette_game = False
	else:
		users[ctx.author.id].roulette_winnings = int(bet * 1.1)
		users[ctx.author.id].current_chamber = 1
		await ctx.send("You pull the trigger and nothing happens. Reply stop to take your earnings of {} coins or continue to fire the next chamber".format(int(bet * 1.1)))




	


@bot.command(brief = 'Tells you your current coin balance')
async def balance(ctx):
	await ctx.send("You have {} coins".format(users[ctx.author.id].balance))



# TODO -- Seperate lists by server
@bot.command(brief = 'Gives a list of the richest members')
async def richest(ctx):
	rich = {}
	for i in users:
		rich.update({users[i].username : users[i].balance})
	print(rich)
	print("/=========================================")
	print(rich.items())
	
	sorted_rich = sorted(rich.items(), key = lambda x:x[1], reverse = True)
	
	top_ten = list(sorted_rich)[:10]
	df = pandas.DataFrame(top_ten, columns=["Username", "Balance"])
	df.to_string(col_space = 500, justify = {"right"})
	await ctx.send(df)





@bot.command(brief = 'Starts the dice game', description = 'Requires bet. Starts the dice game, which rolls a die for both you and the bot.' 
	+ ' Whoever has the highest roll wins.')
async def dice(ctx, bet = -1):
	if bet < 0:
		await ctx.send("Input a positive bet amount")
		return
	if users[ctx.author.id].balance - bet < 0:
		await ctx.send("Sorry, you cannot afford that bet")
		return
	# print(ctx.author.id)
	account = users.get(ctx.author.id)
	print(account)
	account.balance -= bet
	await ctx.send("You bet {}".format(bet))
	own_roll = random.randint(1, 6)
	bot_roll = random.randint(1, 6)
	time.sleep(2)
	await ctx.send("You roll {}".format(own_roll))
	time.sleep(2)
	await ctx.send("Bot rolls {}".format(bot_roll))
	time.sleep(2)
	if own_roll > bot_roll:
		account.balance += (bet * 2)
		await ctx.send("You win {}!".format(bet))
	elif bot_roll > own_roll:
		account.balance -= bet
		await ctx.send("Sorry, you lose {}".format(bet))
	else:
		account.balance += bet
		await ctx.send("Draw! You get back your bet")





bot.run(discord_config.discord_token)

