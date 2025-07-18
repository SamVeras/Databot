from config import DISCORD_TOKEN, BOT_PREFIX
import discord
from discord.ext import commands
from cogs.test_commands import TestCommands
from cogs.database_commands import DatabaseCommands
from cogs.admin_commands import AdminCommands
import logging
import signal
import os
import sys
import asyncio


class Lad(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shutdown = False

    async def on_ready(self):
        logging.info(f"[on_ready] Logado como {self.user}.")
        try:
            synced = await self.tree.sync()
            logging.info(f"[on_ready] Sincronizados {len(synced)} comando(s)")
            for synced_command in synced:
                logging.info(f"[on_ready] Comando registrado: {synced_command.name}")
        except Exception as e:
            logging.error(f"[on_ready] Falha ao sincronizar comandos: {e}")

    def restart(self):
        os.execv(sys.executable, ["python"] + sys.argv)

    async def close(self):
        if not self._shutdown:
            self._shutdown = True
            logging.info("[close] Bot está sendo desligado...")
        await super().close()

    async def setup_hook(self):
        for cog in [TestCommands, DatabaseCommands, AdminCommands]:
            await self.add_cog(cog(self))
            logging.info(f"[setup_hook] Cog {cog.__name__} carregado com sucesso.")

    def format_command_log(self, ctx, error=None):
        timestamp = ctx.message.created_at
        command = ctx.command.name
        user = ctx.author
        guild = ctx.guild.name if ctx.guild else "DM"
        channel = ctx.channel.name if hasattr(ctx.channel, "name") else "DM"

        log_msg = f"{command};{user.name}#{user.discriminator};({user.id});{guild};{channel};{timestamp}"

        if error:
            log_msg += f", {error}"
        return log_msg

    async def on_command(self, ctx):
        logging.info(self.format_command_log(ctx))

    async def on_command_error(self, ctx, error):
        logging.error(self.format_command_log(ctx, error))

        msg = None
        if isinstance(error, commands.MissingPermissions):
            msg = "Você não tem permissão para usar este comando."
        elif isinstance(error, commands.CommandNotFound):
            msg = "Comando não encontrado."
        elif isinstance(error, commands.CommandOnCooldown):
            msg = "Este comando está em cooldown. Por favor, tente novamente mais tarde."
        elif isinstance(error, commands.DisabledCommand):
            msg = "Este comando está desabilitado."
        elif isinstance(error, commands.CheckFailure):
            msg = "Você não tem permissão para usar este comando."
        else:
            msg = f"Erro: {error}."

        if msg:
            try:
                await ctx.send(msg)
            except discord.Forbidden:
                logging.warning(f"[on_command_error: {ctx.author.name}] Bot não tem permissão para enviar mensagens neste canal: {ctx.channel.name}.")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)


def signal_handler(signum, frame):
    logging.info(f"[signal_handler] Recebido sinal {signum}, desligando bot...")
    if "bot" in globals():
        asyncio.create_task(bot.close())


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True
intents.presences = True
intents.messages = True

if __name__ == "__main__":
    logging.basicConfig(
        handlers=[
            logging.FileHandler("bot.log", mode="a", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    logging.info("[main] Iniciando bot...")

    if not DISCORD_TOKEN:
        logging.error("[main] DISCORD_TOKEN não encontrado nas variáveis de ambiente.")
        exit(1)

    bot = Lad(command_prefix=BOT_PREFIX, intents=intents)
    logging.info("[main] Bot inicializado com sucesso.")

    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)
    logging.info("[main] Sinais de interrupção registrado.")

    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logging.info("[main] Interrupção do teclado detectada, desligando bot...")
    except Exception as e:
        logging.error(f"[main] Erro inesperado: {e}")
    finally:
        logging.info("[main] Bot desligado.")
