from discord.ext import commands


class TestCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Testar latência do bot")
    async def ping(self, ctx):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.hybrid_command(name="teste", description="Testar comando")
    async def teste(self, ctx):
        await ctx.send("Teste")

    @commands.hybrid_command(name="repetir", description="Repetir o que o usuário digitar")
    async def repetir(self, ctx, *, mensagem: str):
        await ctx.send(mensagem)

    @commands.hybrid_command(name="admintest", description="Testar permissões")
    @commands.has_permissions(administrator=True)
    async def admintest(self, ctx):
        await ctx.send("Comando admin executado!")

    @commands.hybrid_command(name="nonadmintest", description="Testar permissões")
    @commands.has_permissions(administrator=False)
    async def nonadmintest(self, ctx):
        await ctx.send("Comando nonadmin executado!")
