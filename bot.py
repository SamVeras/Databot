from config import DISCORD_TOKEN, BOT_PREFIX
import discord
from discord.ext import commands
from cogs.test_commands import TestCommands
from cogs.scrape_commands import ScrapeCommands
import logging
import signal
import sys


class Lad(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shutdown = False

    async def on_ready(self):
        logging.info(f"Logado como {self.user}.")
        try:
            synced = await self.tree.sync()
            logging.info(f"Sincronizados {len(synced)} comando(s)")
            for synced_command in synced:
                logging.info(f"Comando registrado: {synced_command.name}")
        except Exception as e:
            logging.error(f"Falha ao sincronizar comandos: {e}")

    async def close(self):
        if not self._shutdown:
            self._shutdown = True
            logging.info("Bot está sendo desligado...")
        await super().close()

    async def setup_hook(self):
        for cog in [TestCommands, ScrapeCommands]:
            await self.add_cog(cog(self))
            logging.info(f"Cog {cog.__name__} carregado com sucesso.")

    async def on_command(self, ctx):
        timestamp = ctx.message.created_at
        command = ctx.command.name
        user = ctx.author
        guild = ctx.guild.name if ctx.guild else "DM"
        channel = ctx.channel.name if hasattr(ctx.channel, "name") else "DM"

        logging.info(
            f"COMANDO: {command} | "
            f"USUARIO: {user.name}#{user.discriminator} ({user.id}) | "
            f"SERVIDOR: {guild} | "
            f"CANAL: {channel} | "
            f"TIMESTAMP: {timestamp}"
        )

    async def on_command_error(self, ctx, error):
        timestamp = ctx.message.created_at
        command = ctx.command.name if ctx.command else "Desconhecido"
        user = ctx.author
        guild = ctx.guild.name if ctx.guild else "DM"
        channel = ctx.channel.name if hasattr(ctx.channel, "name") else "DM"

        logging.error(
            f"COMANDO: {command} | "
            f"USUARIO: {user.name}#{user.discriminator} ({user.id}) | "
            f"SERVIDOR: {guild} | "
            f"CANAL: {channel} | "
            f"TIMESTAMP: {timestamp} | "
            f"ERRO: {error}"
        )

        if isinstance(error, commands.MissingPermissions):
            try:
                await ctx.send("Você não tem permissão para usar este comando.")
            except discord.Forbidden:
                logging.warning("Bot não tem permissão para enviar mensagens neste canal.")
        elif isinstance(error, commands.CommandNotFound):
            try:
                await ctx.send("Comando não encontrado.")
            except discord.Forbidden:
                logging.warning("Bot não tem permissão para enviar mensagens neste canal.")
        else:
            try:
                await ctx.send(f"Erro: {error}.")
            except discord.Forbidden:
                logging.error(f"Erro: {error} (Bot não tem permissão para enviar mensagens neste canal)")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)


def signal_handler(signum, frame):
    logging.info(f"Recebido sinal {signum}, desligando bot...")
    if "bot" in globals():
        import asyncio

        asyncio.create_task(bot.close())


intents = discord.Intents.default()
intents.message_content = True

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Erro: DISCORD_TOKEN não encontrado nas variáveis de ambiente!")
        exit(1)

    bot = Lad(command_prefix=BOT_PREFIX, intents=intents)

    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logging.info("Interrupção do teclado detectada, desligando bot...")
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
    finally:
        logging.info("Bot desligado.")
