from discord.ext import commands
import logging
from bot import Lad


class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="restart", description="Reiniciar o bot")
    @commands.has_permissions(administrator=True)
    async def restart(self, ctx: commands.Context) -> None:
        logging.info(f"[restart: {ctx.author.name}] Reiniciando o bot...")
        await ctx.send("Reiniciando o bot...")
        if isinstance(self.bot, Lad):  # restart é um método específico do nosso bot
            self.bot.restart()
        else:
            await ctx.send("O bot não é o bot certo.")
            logging.error(f"[restart: {ctx.author.name}] Bot não é instance do bot Lad.")

    @commands.hybrid_command(name="shutdown", description="Desligar o bot")
    @commands.has_permissions(administrator=True)
    async def shutdown(self, ctx: commands.Context) -> None:
        logging.info(f"[shutdown: {ctx.author.name}] Desligando o bot...")
        await ctx.send("Desligando o bot...")
        await self.bot.close()
