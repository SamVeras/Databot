from discord.ext import commands
import logging


class AdminCommands(commands.Cog):

    # ---------------------------------------------------------------------------------------------------------------- #
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ---------------------------------------------------------------------------------------------------------------- #
    @commands.hybrid_command(name="shutdown", description="Desligar o bot")
    @commands.has_permissions(administrator=True)
    async def shutdown(self, ctx: commands.Context) -> None:
        logging.info(f"[shutdown: {ctx.author.name}] Desligando o bot...")
        await ctx.send("Desligando o bot...")
        await self.bot.close()
