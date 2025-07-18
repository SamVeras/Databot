from config import MONGO_URI, GUILD_ID
import discord
import os
import sys
from cogs.test_commands import TestCommands
from cogs.database_commands import DatabaseCommands
from cogs.admin_commands import AdminCommands
from cogs.fun_commands import FunCommands
import time
import motor.motor_asyncio
from discord.ext import commands
import logging


class Lad(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shutdown = False
        self._command_times = {}
        # self.reminder_task = None

        if not MONGO_URI:
            logging.error("[on_ready] MONGO_URI não encontrado nas variáveis de ambiente.")
            raise ValueError("[on_ready] MONGO_URI não encontrado nas variáveis de ambiente.")

        logging.info(f"[on_ready] Conectando ao MongoDB: {MONGO_URI[:22]}...")

        try:
            self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
            self.db = self.mongo_client["discord_data"]
            self.collections = {
                "reminders": self.db["reminders"],
                "messages": self.db["messages"],
            }
            logging.info(f"[on_ready] Conectado ao MongoDB: {self.db.name}, coleções: {', '.join(self.collections.keys())}")
        except Exception as e:
            logging.error(f"[on_ready] Falha ao conectar ao MongoDB: {e}")
            raise ValueError(f"[on_ready] Falha ao conectar ao MongoDB: {e}")

    async def on_ready(self) -> None:
        logging.info(f"[on_ready] Logado como {self.user}.")

        try:
            synced = await self.tree.sync()
            logging.info(f"[on_ready] Sincronizados {len(synced)} comando(s)")
            for synced_command in synced:
                logging.info(f"[on_ready] Comando registrado: {synced_command.name}")
        except Exception as e:
            logging.error(f"[on_ready] Falha ao sincronizar comandos: {e}")

    def restart(self) -> None:
        os.execv(sys.executable, ["python"] + sys.argv)

    async def close(self) -> None:
        if not self._shutdown:
            self._shutdown = True
            logging.info("[close] Bot está sendo desligado...")
        await super().close()

    async def setup_hook(self) -> None:
        for cog in [TestCommands, DatabaseCommands, AdminCommands, FunCommands]:
            await self.add_cog(cog(self))
            logging.info(f"[setup_hook] Cog {cog.__name__} carregado com sucesso.")

    def format_command_log(self, ctx: commands.Context, error: Exception | None = None) -> str:
        timestamp = ctx.message.created_at
        command = ctx.command.name if ctx.command else "desconhecido"
        user = ctx.author
        guild = ctx.guild.name if ctx.guild else "DM"
        guild_id = ctx.guild.id if ctx.guild else "desconhecido"
        channel = getattr(ctx.channel, "name", "DM")
        channel_id = getattr(ctx.channel, "id", "desconhecido")

        log_msg = f"[{command}: {user.name}#{user.discriminator} ({user.id})] {guild} ({guild_id}) / #{channel} ({channel_id}) @ {timestamp}"

        if error:
            log_msg += f' "{error}"'
        return log_msg

    async def on_command(self, ctx: commands.Context) -> None:
        self._command_times[ctx.message.id] = time.perf_counter()
        logging.info(self.format_command_log(ctx))

    async def on_command_completion(self, ctx: commands.Context) -> None:
        start = self._command_times.pop(ctx.message.id, None)
        if start is not None:
            duration = time.perf_counter() - start
            command_name = ctx.command.name if ctx.command else "desconhecido"
            logging.info(f"[{command_name}: {ctx.author.name}] Comando executado em {duration:.3f} segundos.")

    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        start = self._command_times.pop(ctx.message.id, None)
        if start is not None:
            duration = time.perf_counter() - start
            command_name = ctx.command.name if ctx.command else "desconhecido"
            logging.info(f"[{command_name}: {ctx.author.name}] Comando executado, com erro, em {duration:.3f} segundos.")

        logging.error(self.format_command_log(ctx, error))

        msg = None
        match error:
            case commands.MissingPermissions:
                msg = "Você não tem permissão para usar este comando."
            case commands.CommandNotFound:
                msg = "Comando não encontrado."
            case commands.CommandOnCooldown:
                msg = "Este comando está em cooldown. Por favor, tente novamente mais tarde."
            case commands.DisabledCommand:
                msg = "Este comando está desabilitado."
            case commands.CheckFailure:
                msg = "Você não tem permissão para usar este comando."
            case _:
                msg = f"Erro: {error}."

        if msg:
            try:
                await ctx.send(msg)
            except discord.Forbidden:
                cname = getattr(ctx.channel, "name", "desconhecido")
                logging.warning(f"[on_command_error: {ctx.author.name}] Bot não tem permissão para enviar mensagens neste canal: #{cname}.")

    async def get_emoji_string(self, emoji: str) -> str:
        """Retorna uma string com o código do emoji, ou o nome do emoji se não achar."""
        try:
            logging.info(f'[get_emoji_string] Buscando emoji: "{emoji}"')
            guild = self.get_guild(GUILD_ID)
            if not guild:
                logging.info(f'[get_emoji_string] Não encontrado servidor: "{GUILD_ID}"')
                return f"<:{emoji}>"

            for e in guild.emojis:
                if e.name == emoji:
                    logging.info(f'[get_emoji_string] Encontrado emoji em "{guild.name}": "{e.name}" com id: "{e.id}"')
                    return f"<:{e.name}:{e.id}>"

            logging.info(f'[get_emoji_string] Não encontrado emoji em "{guild.name}": "{emoji}"')
            return f"<:{emoji}>"

        except Exception as e:
            logging.error(f'[get_emoji_string] Erro ao buscar emoji: "{emoji}" - {e}')
            return f"<:{emoji}>"
