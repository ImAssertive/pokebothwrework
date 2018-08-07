import discord, asyncio, sys, traceback, checks, inflect, useful, random
from discord.ext import commands

class adminCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = "exit", aliases =['quit'], hidden = True)
    @checks.justme()
    async def exit(self, ctx):
        thanos = random.randint(1,5)
        if thanos == 1:
            await ctx.channel.send("Assertive I dont feel so good...")
        if thanos == 2:
            await ctx.channel.send("Why...")
        if thanos == 3:
            await ctx.channel.send(":wave: Goodbye.")
        if thanos == 4:
            await ctx.channel.send("Faster, Bambi! Don't look back! Keep running! Keep running!")
        if thanos == 5:
            await ctx.channel.send("The horror. The horror.")
        await self.bot.db.close()
        await self.bot.logout()
        sys.exit()

def setup(bot):
    bot.add_cog(adminCog(bot))