import discord, asyncio, sys, traceback, checks, asyncpg, useful, credentialsFile
from discord.ext import commands

def getPrefix(bot, message):
    prefixes = ["pb!", "p!","pokebot!"]
    return commands.when_mentioned_or(*prefixes)(bot, message)

async def run():
    description = "Pokemon Bot High Wycombe! pb!help for commands."
    credentials = credentialsFile.getCredentials()
    db = await asyncpg.create_pool(**credentials)
    await db.execute('''CREATE TABLE IF NOT EXISTS Pokestops(stopID serial PRIMARY KEY,
    name text,
    aliases text,
    mapurl text,
    coord text,
    notes text,
    type text);
    
    CREATE TABLE IF NOT EXISTS Images(imageID serial PRIMARY KEY,
    stopID serial references Pokestops(stopID) ON DELETE CASCADE ON UPDATE CASCADE,
    url text,
    infotext text);
    
    CREATE TABLE IF NOT EXISTS Pokemon(pokedex serial PRIMARY KEY,
    name text,
    infotext text);''')

    bot = Bot(description=description, db=db)
    initial_extensions = ['misc', 'admin', 'pokestop']
    if __name__ == '__main__':
        for extension in initial_extensions:
            try:
                bot.load_extension(extension)
            except Exception as e:
                print('Failed to load extension ' + extension, file=sys.stderr)
                traceback.print_exc()

    try:
        await bot.start(credentialsFile.getToken())
    except KeyboardInterrupt:
        await db.close()
        await bot.logout()

class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            description=kwargs.pop("description"),
            command_prefix=getPrefix
        )

        self.pubquizAnswers = []
        self.db = kwargs.pop("db")
        self.currentColour = -1
        self.outcomes = ["It is certain", "It is decidedly so", "Without a doubt", "Yes - definitely",
                    "You may rely on it",
                    "As I see it, yes", "Most likely", "Outlook good", "Yes", "Signs point to yes",
                    "Reply hazy, try again", "Ask again later", "Better not tell you now",
                    "Cannot predict now", "Concentrate and ask again", "Don't count on it",
                    "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]

    async def on_ready(self):
        print("Username: {0}\nID: {0.id}".format(self.user))
        game = discord.Game("Pokemon Go!")
        await self.change_presence(status=discord.Status.online, activity=game)

    def getcolour(self):
        colours = ["EE1515", "222224", "F0F0F0", "F00000", "F0F0F0"]
        self.currentColour += 1
        if self.currentColour ==  len(colours):
            self.currentColour = 0
        return discord.Colour(int(colours[self.currentColour], 16))

    def conchcolour(self, number):
        if number < 10 and number > -1:
            return discord.Colour(int("00FF00", 16))
        elif number > 9 and number < 15:
            return discord.Colour(int("FFFF00", 16))
        else:
            return discord.Colour(int("FF0000", 16))


loop = asyncio.get_event_loop()
loop.run_until_complete(run())