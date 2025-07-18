from discord.ext import commands
import logging


class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="restart", description="Reiniciar o bot")
    @commands.has_permissions(administrator=True)
    async def restart(self, ctx: commands.Context) -> None:
        logging.info(f"[restart: {ctx.author.name}] Reiniciando o bot...")
        await ctx.send("Reiniciando o bot...")
        restart = getattr(self.bot, "restart", None)
        if callable(restart):
            restart()
        else:
            await ctx.send("O bot não suporta restart.")
            logging.error(f"[restart: {ctx.author.name}] Bot não suporta restart.")

    @commands.hybrid_command(name="shutdown", description="Desligar o bot")
    @commands.has_permissions(administrator=True)
    async def shutdown(self, ctx: commands.Context) -> None:
        logging.info(f"[shutdown: {ctx.author.name}] Desligando o bot...")
        await ctx.send("Desligando o bot...")
        await self.bot.close()
