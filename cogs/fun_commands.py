from discord.ext import commands
import logging


class FunCommands(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="remindme", description="Definir um lembrete.")
    async def remindme(self, ctx: commands.Context, time: str, *, reminder: str) -> None:
        """Definir um lembrete."""
        try:
            emoji = await self.bot.get_emoji_string("bastardo")
            await ctx.send(f"Sinto muito, mas esse comando nem existe ainda. {emoji}")
        except:
            pass
