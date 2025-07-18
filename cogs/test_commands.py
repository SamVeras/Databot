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
    @commands.hybrid_command(name="admintest", description="Testar permissões")
    @commands.has_permissions(administrator=True)
    async def admintest(self, ctx: commands.Context) -> None:
        logging.info(f"[admintest: {ctx.author.name}] Testando comando admin...")
        await ctx.send("Comando admin executado!")

    # ---------------------------------------------------------------------------------------------------------------- #
    @commands.hybrid_command(name="nonadmintest", description="Testar permissões")
    @commands.has_permissions(administrator=False)
    async def nonadmintest(self, ctx: commands.Context) -> None:
        logging.info(f"[nonadmintest: {ctx.author.name}] Testando comando nonadmin...")
        await ctx.send("Comando nonadmin executado!")
