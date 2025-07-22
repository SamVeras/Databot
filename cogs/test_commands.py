from doctest import debug_script
from discord.ext import commands
import logging


class TestCommands(commands.Cog):

    # ---------------------------------------------------------------------------------------------------------------- #
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ---------------------------------------------------------------------------------------------------------------- #
    @commands.hybrid_command(name="ping", description="Testar latência do bot")
    async def ping(self, ctx: commands.Context) -> None:
        logging.info(f"[ping: {ctx.author.name}] Testando latência do bot...")
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")
        logging.info(f"[ping: {ctx.author.name}] Latência do bot: {round(self.bot.latency * 1000)}ms")

    # ---------------------------------------------------------------------------------------------------------------- #
    @commands.hybrid_command(name="teste", description="Testar comando")
    async def teste(self, ctx: commands.Context) -> None:
        logging.info(f"[teste: {ctx.author.name}] Testando comando...")
        await ctx.send("Teste")

    # ---------------------------------------------------------------------------------------------------------------- #
    @commands.hybrid_command(name="repetir", description="Repetir o que o usuário digitar")
    async def repetir(self, ctx: commands.Context, *, mensagem: str) -> None:
        logging.info(f"[repetir: {ctx.author.name}] Repetindo mensagem: {mensagem}")
        await ctx.send(mensagem)

    # ---------------------------------------------------------------------------------------------------------------- #
    @commands.hybrid_command(name="testemoji", description="Testar envio de emoji")
    async def test_emoji(self, ctx: commands.Context, emoji_name: str):
        emoji: str = await self.bot.get_emoji_string(emoji_name)
        await ctx.send(emoji)
