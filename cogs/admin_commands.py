from discord.ext import commands
import logging


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="restart", description="Reiniciar o bot")
    @commands.has_permissions(administrator=True)
    async def restart(self, ctx):
        await ctx.send("Reiniciando o bot...")
        self.bot.restart()
