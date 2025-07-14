from config import DISCORD_TOKEN, BOT_PREFIX
import discord
from discord.ext import commands
from cogs.test_commands import TestCommands
from cogs.scrape_commands import ScrapeCommands


class Lad(commands.Bot):
    async def on_ready(self):
        print(f"Logado como {self.user}.")
        try:
            synced = await self.tree.sync()
            print(f"Sincronizados {len(synced)} comando(s)")
            for synced_command in synced:
                print(f"Comando registrado: {synced_command.name}")
        except Exception as e:
            print(f"Falha ao sincronizar comandos: {e}")

    async def setup_hook(self):
        for cog in [TestCommands, ScrapeCommands]:
            await self.add_cog(cog(self))
            print(f"Cog {cog.__name__} carregado com sucesso.")

    async def on_command_completion(self, ctx):
        timestamp = ctx.message.created_at
        command = ctx.command.name
        user = ctx.author
        guild = ctx.guild.name if ctx.guild else "DM"
        channel = ctx.channel.name if hasattr(ctx.channel, "name") else "DM"

        print(
            f"COMANDO: {command}",
            f"USUARIO: {user.name}#{user.discriminator} ({user.id})",
            f"SERVIDOR: {guild}",
            f"CANAL: {channel}",
            f"TIMESTAMP: {timestamp}",
            sep=" | ",
        )

    async def on_command_error(self, ctx, error):
        timestamp = ctx.message.created_at
        command = ctx.command.name if ctx.command else "Desconhecido"
        user = ctx.author
        guild = ctx.guild.name if ctx.guild else "DM"
        channel = ctx.channel.name if hasattr(ctx.channel, "name") else "DM"

        print(
            f"COMANDO: {command}",
            f"USUARIO: {user.name}#{user.discriminator} ({user.id})",
            f"SERVIDOR: {guild}",
            f"CANAL: {channel}",
            f"TIMESTAMP: {timestamp}",
            f"ERRO: {error}",
            sep=" | ",
        )

        if isinstance(error, commands.MissingPermissions):
            try:
                await ctx.send("Você não tem permissão para usar este comando.")
            except discord.Forbidden:
                print("Bot não tem permissão para enviar mensagens neste canal.")
        elif isinstance(error, commands.CommandNotFound):
            try:
                await ctx.send("Comando não encontrado.")
            except discord.Forbidden:
                print("Bot não tem permissão para enviar mensagens neste canal.")
        else:
            try:
                await ctx.send(f"Erro: {error}.")
            except discord.Forbidden:
                print(f"Erro: {error} (Bot não tem permissão para enviar mensagens neste canal)")


intents = discord.Intents.default()
intents.message_content = True

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Erro: DISCORD_TOKEN não encontrado nas variáveis de ambiente!")
        exit(1)

    bot = Lad(command_prefix=BOT_PREFIX, intents=intents)
    bot.run(DISCORD_TOKEN)
