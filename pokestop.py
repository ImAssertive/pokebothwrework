import discord, asyncio, sys, traceback, checks, inflect, useful, random
from discord.ext import commands


class pokestopCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def info(self, ctx, *, stopname):
        result = await self.searchStops(ctx, stopname)
        if result:
            embed = discord.Embed(title="Menu Loading...", description="Please stand by.", colour=self.bot.getcolour())
            menu = await ctx.channel.send(embed = embed)
            emojis = useful.getInfoMenuEmoji()
            for emoji in range(0,len(emojis)):
                await menu.add_reaction(emojis[emoji])
            query = "SELECT * FROM Images WHERE stopID = $1"
            images = await ctx.bot.db.fetch(query, result["stopid"])
            pageNumber = 1
            await self.menuController(ctx, menu, result, images, pageNumber)
        else:
            await ctx.channel.send(":no_entry: | Pokestop not found.")

    async def searchStops(self, ctx, stopname):
        query = "SELECT * FROM Pokestops"
        results = await ctx.bot.db.fetch(query)
        for result in results:
            if stopname.title() == result["name"].title() or stopname.title() in result["aliases"].split(", "):
                return result
        return False

    async def menuController(self, ctx, menu, result, images, pageNumber):
        if pageNumber == 0:
            pageNumber = len(images) + 1
            await self.menuController(ctx, menu, result, images, pageNumber)
        elif pageNumber == 1:
            await self.infoMainMenu(ctx, menu, result, images, pageNumber)
        elif pageNumber > len(images) + 1:
            pageNumber = 1
            await self.menuController(ctx, menu, result, images, pageNumber)
        else:
            await self.imageMenu(ctx, menu, result, images, pageNumber)

    async def imageMenu(self, ctx, menu, result, images, pageNumber):
        embed = discord.Embed(description="Use the reactions to navigate the menu.", colour=self.bot.getcolour())
        embed.set_image(url=images[pageNumber-2]["url"])
        if images[pageNumber-2]["infotext"]:
            embed.add_field(name="Additional Info:", value=images[pageNumber-2]["infotext"])
        embed.set_footer(text="Page ("+str(pageNumber)+"/"+str(len(images)+1)+")     bot made by Zootopia#0001")
        embed.set_author(icon_url="https://i.imgur.com/eXKzHVr.jpg", name="Image of: " + result["name"])
        await menu.edit(embed=embed)
        options = useful.getInfoMenuEmoji()
        def info_emojis_main_menu(reaction, user):
            return (user == ctx.author) and (str(reaction.emoji) in options)

        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=info_emojis_main_menu, timeout=60.0)
        except asyncio.TimeoutError:
            ctx.channel.send(
                ":no_entry: | **" + ctx.author.display_name + "** The command menu has closed due to inactivity.")
            await menu.delete()
        else:
            await menu.remove_reaction(reaction.emoji, user)
            if str(reaction.emoji) == "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}":
                pageNumber = 1
                await self.menuController(ctx, menu, result, images, pageNumber)
            elif str(reaction.emoji) == "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}":
                pageNumber -= 1
                await self.menuController(ctx, menu, result, images, pageNumber)
            elif str(reaction.emoji) == "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}":
                pageNumber += 1
                await self.menuController(ctx, menu, result, images, pageNumber)
            elif str(reaction.emoji) == "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}":
                pageNumber = len(images) + 1
                await self.menuController(ctx, menu, result, images, pageNumber)

            elif str(reaction.emoji) == "❌":
                closed = await ctx.channel.send(":white_check_mark: | Info closed!")
                await menu.delete()
                await asyncio.sleep(1)
                await closed.delete()

    async def infoMainMenu(self, ctx, menu, result, images, pageNumber):
            embed = discord.Embed(description="Use the reactions to navigate the menu.", colour=self.bot.getcolour(), url=result["mapurl"])
            embed.add_field(name=result["type"].title()+" name:", value=result["name"])
            embed.add_field(name=result["type"].title()+" coordinates:", value=result["coord"])
            embed.add_field(name=result["type"].title()+" notes:", value=result["notes"], inline=False)
            embed.set_footer(text="Page (1/"+str(len(images)+1)+")     bot made by Assertive#0001")
            embed.set_author(icon_url="https://i.imgur.com/eXKzHVr.jpg",name="Here is the information for stop: "+result["name"])
            await menu.edit(embed=embed)
            options = useful.getInfoMenuEmoji()
            def info_emojis_main_menu(reaction, user):
                return (user == ctx.author) and (str(reaction.emoji) in options)
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=info_emojis_main_menu, timeout=60.0)
            except asyncio.TimeoutError:
                await ctx.channel.send(":no_entry: | **" + ctx.author.display_name + "** The command menu has closed due to inactivity.")
                await menu.delete()
            else:
                await menu.remove_reaction(reaction.emoji, user)
                if str(reaction.emoji) == "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}":
                    pageNumber = 1
                    await self.menuController(ctx, menu, result, images, pageNumber)
                elif str(reaction.emoji) == "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}":
                    pageNumber -= 1
                    await self.menuController(ctx, menu, result, images, pageNumber)
                elif str(reaction.emoji) == "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}":
                    pageNumber += 1
                    await self.menuController(ctx, menu, result, images, pageNumber)
                elif str(reaction.emoji) == "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}":
                    pageNumber = len(images) + 1
                    await self.menuController(ctx, menu, result, images, pageNumber)

                elif str(reaction.emoji) == "❌":
                    closed = await ctx.channel.send(":white_check_mark: | Info closed!")
                    await menu.delete()
                    await asyncio.sleep(1)
                    await closed.delete()

    @commands.command()
    @checks.justme()
    async def addimage(self, ctx, *, subText):
        subText = subText.split(" | ")
        stopname = subText[0]
        url = subText[1]
        if "http://" in url == False and "https://" in url == False:
            await ctx.channel.send(":no_entry: | This URL appears to be invalid.")
        else:
            result = await self.searchStops(ctx, stopname)
            if result:
                connection = await self.bot.db.acquire()
                async with connection.transaction():
                    if subText[2]:
                        query = "INSERT INTO Images (stopID, url, infotext) VALUES($1, $2, $3) ON CONFLICT DO NOTHING"
                        await self.bot.db.execute(query, result["stopid"], url, subText[2])
                    else:
                        query = "INSERT INTO Images (stopID, url) VALUES($1, $2) ON CONFLICT DO NOTHING"
                        await self.bot.db.execute(query, result["stopid"], url)
                await self.bot.db.release(connection)
                await ctx.channel.send(":white_check_mark: | Image added!")

            else:
                await ctx.channel.send(":no_entry: | Pokestop not found.")

    @commands.command()
    @checks.justme()
    async def addstop(self, ctx):
        stoptype = "wew"
        await ctx.channel.send(":rotating_light: | Please enter the type of the stop.")
        def check(msg):
            options = ["gym", "pokestop", "stop"]
            return ctx.channel.id == msg.channel.id and msg.author.id == ctx.author.id and msg.content.lower() in options
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
        except asyncio.TimeoutError:
            await ctx.channel.send(":no_entry: | **" + ctx.author.display_name + "** The command window has closed due to inactivity. Please use the addstop command again to restart the proccess.")
        else:
            if msg.content.lower() == "gym":
                stoptype = "gym"
            elif msg.content.lower() == "pokestop" or msg.content.lower() == "stop":
                stoptype = "pokestop"
        if stoptype != "wew":
            timeout = False
            stoptextlist = [[":rotating_light: | Please enter the name of the "+stoptype+".", ""],
                            [":rotating_light: | Please enter any aliases of the " + stoptype + ".", ""],
                            [":rotating_light: | Please enter the url of the map location of the "+stoptype+".", ""],
                            [":rotating_light: | Please enter the map coordanites of the " + stoptype + ".",""],
                            [":rotating_light: | Please enter any additional notes for this "+stoptype+".", ""]]
            for option in stoptextlist:
                entryrequest = await ctx.channel.send(option[0])
                def check(msg):
                    return ctx.channel.id == msg.channel.id and msg.author.id == ctx.author.id
                try:
                    msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                except asyncio.TimeoutError:
                    timeout = True
                    await ctx.channel.send(":no_entry: | **" + ctx.author.display_name + "** The command window has closed due to inactivity. Please use the addstop command again to restart the proccess.")
                    await entryrequest.delete()
                    break
                else:
                    option[1] = msg.content.title()
                    await entryrequest.delete()
            if not timeout:
                embed = discord.Embed(description="Please type confirm to confirm adding to database or cancel to discard.", colour=self.bot.getcolour())
                embed.set_author(icon_url="https://i.imgur.com/eXKzHVr.jpg", name="Here is the information for "+stoptype+": "+stoptextlist[0][1]+".")
                embed.add_field(name=stoptype+" name:", value=stoptextlist[0][1], inline=False)
                embed.add_field(name=stoptype+" aliases:", value=stoptextlist[1][1], inline=False)
                embed.add_field(name=stoptype+" map location url:", value=stoptextlist[2][1], inline=False)
                embed.add_field(name=stoptype+" map coordanites", value=stoptextlist[3][1], inline=False)
                embed.add_field(name=stoptype+" notes", value=stoptextlist[4][1], inline=False)
                embed.set_footer(text="bot made by Zootopia#0001")
                await ctx.channel.send(embed=embed)
                def check(msg):
                    options = ["cancel", "confirm"]
                    return ctx.channel.id == msg.channel.id and msg.author.id == ctx.author.id and msg.content.lower() in options
                try:
                    msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                except asyncio.TimeoutError:
                    await ctx.channel.send(":no_entry: | **" + ctx.author.display_name + "** The command window has closed due to inactivity. Please use the addstop command again to restart the proccess.")
                else:
                    if msg.content.lower() == "cancel":
                        await ctx.channel.send(":white_check_mark: | "+stoptype.title()+" discarded!")
                    elif msg.content.lower() == "confirm":
                        connection = await self.bot.db.acquire()
                        async with connection.transaction():
                            query = "INSERT INTO Pokestops (name, aliases, mapurl, coord, notes, type) VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT DO NOTHING"
                            await self.bot.db.execute(query, stoptextlist[0][1], stoptextlist[1][1], stoptextlist[2][1], stoptextlist[3][1], stoptextlist[4][1], stoptype)
                        await self.bot.db.release(connection)
                        await ctx.channel.send(":white_check_mark: | "+stoptype.title()+" added!")


def setup(bot):
    bot.add_cog(pokestopCog(bot))