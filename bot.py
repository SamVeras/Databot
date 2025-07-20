from config import MONGO_URI, GUILD_ID, REMINDER_CHANNEL_NAME
import discord
from cogs.test_commands import TestCommands
from cogs.database_commands import DatabaseCommands
from cogs.admin_commands import AdminCommands
from cogs.fun_commands import FunCommands
from cogs.time_commands import TimeCommands
import time
import motor.motor_asyncio
from discord.ext import commands
import logging
from datetime import datetime
import asyncio
import random
import pytz

cog_list = [TestCommands, DatabaseCommands, AdminCommands, FunCommands, TimeCommands]


class Lad(commands.Bot):  # Lad = Bot (Lad)rão de Dados :P

    # ---------------------------------------------------------------------------------------------------------------- #
    def __init__(self, *args, **kwargs):
        """Inicializa o bot."""
        super().__init__(*args, **kwargs)
        self._shutdown = False
        self._command_times = {}
        self.reminder_task = None

        if not MONGO_URI:
            logging.error("[on_ready] MONGO_URI não encontrado nas variáveis de ambiente.")
            raise ValueError("[on_ready] MONGO_URI não encontrado nas variáveis de ambiente.")

        logging.info(f"[on_ready] Conectando ao MongoDB: {MONGO_URI[:22]}...")

        try:
            self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI, tz_aware=True, tzinfo=pytz.utc)
            self.db = self.mongo_client["discord_data"]
            self.collections = {
                "reminders": self.db["reminders"],
                "messages": self.db["messages"],
            }
            logging.info(f"[on_ready] Conectado ao MongoDB: {self.db.name}, coleções: {', '.join(self.collections.keys())}")
        except Exception as e:
            logging.error(f"[on_ready] Falha ao conectar ao MongoDB: {e}")
            raise ValueError(f"[on_ready] Falha ao conectar ao MongoDB: {e}")

    # ---------------------------------------------------------------------------------------------------------------- #
    async def on_ready(self) -> None:
        """Executa quando o bot está pronto."""
        logging.info(f"[on_ready] Logado como {self.user}.")

        try:
            synced = await self.tree.sync()
            logging.info(f"[on_ready] Sincronizados {len(synced)} comando(s)")
            for synced_command in synced:
                logging.info(f"[on_ready] Comando registrado: {synced_command.name}")
        except Exception as e:
            logging.error(f"[on_ready] Falha ao sincronizar comandos: {e}")

        if self.reminder_task is None:
            logging.info(f"[on_ready] Iniciando loop de lembretes em #{REMINDER_CHANNEL_NAME}...")
            self.reminder_task = self.loop.create_task(self.reminder_loop(REMINDER_CHANNEL_NAME))

    # ---------------------------------------------------------------------------------------------------------------- #
    async def reminder_loop(self, channel_name: str) -> None:
        """Rotina de lembretes."""
        await self.wait_until_ready()

        def format_time(dt: datetime) -> str:
            return dt.strftime("%d/%m/%Y %H:%M:%S")

        brazil_tz = pytz.timezone("America/Sao_Paulo")

        async def send_reminder(rm: dict, ch: discord.TextChannel) -> None:
            """Envia um lembrete."""
            emoji_string: str = await self.get_random_emoji_string()
            mention: str = f"<@{rm['user_id']}>"
            remind_time: datetime = rm["remind_at"].astimezone(brazil_tz)

            logging.info(f"[reminder_loop] Lembrete: {rm['message']} para {format_time(remind_time)}")

            reminder_message = f"{emoji_string} **Lembrete:** {rm['message']}\n**Data:** {format_time(remind_time)} {mention}"
            await ch.send(reminder_message)
            await self.collections["reminders"].update_one({"_id": rm["_id"]}, {"$set": {"delivered": True}})

        channel: discord.abc.GuildChannel | None = await self.get_channel_by_name(channel_name)
        if not isinstance(channel, discord.TextChannel):
            logging.error(f"[reminder_loop] Canal de lembretes não é um TextChannel: #{channel_name}")
            return

        while not self.is_closed():
            now = datetime.now(brazil_tz)

            reminders = await self.collections["reminders"].find({"remind_at": {"$lte": now}, "delivered": False}).to_list(length=100)

            for reminder in reminders:
                try:
                    await send_reminder(reminder, channel)
                except Exception as e:
                    logging.error(f"[reminder_loop] Erro ao enviar lembrete: {e}")

            await asyncio.sleep(5)

    # ---------------------------------------------------------------------------------------------------------------- #
    async def close(self) -> None:
        """Fecha o bot."""
        if not self._shutdown:
            self._shutdown = True
            logging.info("[close] Bot está sendo desligado...")
        await super().close()

    # ---------------------------------------------------------------------------------------------------------------- #
    async def setup_hook(self) -> None:
        """Configura os cogs do bot."""
        for cog in cog_list:
            await self.add_cog(cog(self))
            logging.info(f"[setup_hook] Cog {cog.__name__} carregado com sucesso.")

    # ---------------------------------------------------------------------------------------------------------------- #
    def format_command_log(self, ctx: commands.Context, error: Exception | None = None) -> str:
        """Formata a mensagem de log para um comando."""
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

    # ---------------------------------------------------------------------------------------------------------------- #
    async def on_command(self, ctx: commands.Context) -> None:
        """Executa quando um comando é executado."""
        self._command_times[ctx.message.id] = time.perf_counter()
        logging.info(self.format_command_log(ctx))

    # ---------------------------------------------------------------------------------------------------------------- #
    async def on_command_completion(self, ctx: commands.Context) -> None:
        """Executa quando um comando é executado com sucesso."""
        start = self._command_times.pop(ctx.message.id, None)
        if start is not None:
            duration = time.perf_counter() - start
            command_name = ctx.command.name if ctx.command else "desconhecido"
            logging.info(f"[{command_name}: {ctx.author.name}] Comando executado em {duration:.3f} segundos.")

    # ---------------------------------------------------------------------------------------------------------------- #
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Executa quando ocorre um erro em um comando."""
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

    # ---------------------------------------------------------------------------------------------------------------- #
    async def get_emoji_string(self, emoji_name: str) -> str:
        """Retorna uma string com o código do emoji, ou o nome do emoji se não achar."""
        try:
            logging.info(f'[get_emoji_string] Buscando emoji: "{emoji_name}"')
            emoji: discord.Emoji | None = await self.get_emoji_by_name(emoji_name)
            if not emoji:
                return f"<:{emoji_name}>"

            return f"<:{emoji.name}:{emoji.id}>"

        except Exception as e:
            logging.error(f'[get_emoji_string] Erro ao buscar emoji: "{emoji_name}" - {e}')
            return f"<:{emoji_name}>"

    # ---------------------------------------------------------------------------------------------------------------- #
    async def get_random_emoji_string(self) -> str:
        """Retorna uma string com um emoji aleatório."""
        try:
            guild: discord.Guild | None = self.get_guild(GUILD_ID)
            if not guild:
                logging.error(f'[get_random_emoji_string] Não encontrado o servidor: "{GUILD_ID}"')
                return ""

            emojis: list[discord.Emoji] = list(guild.emojis)
            if not emojis:
                logging.error(f'[get_random_emoji_string] Nenhum emoji encontrado no servidor: "{guild.name}"')
                return ""

            emoji = random.choice(emojis)
            logging.info(f'[get_random_emoji_string] Emoji aleatório encontrado: "{emoji.name}" com id: "{emoji.id}"')
            return f"<:{emoji.name}:{emoji.id}>"

        except Exception as e:
            logging.error(f'[get_random_emoji_string] Erro ao buscar emoji aleatório: "{e}"')
            return ""

    # ---------------------------------------------------------------------------------------------------------------- #
    async def get_channel_mention(self, channel_name: str, guild_id: int | None = None) -> str:
        """Retorna uma string com o nome do canal."""
        channel: discord.abc.GuildChannel | None = await self.get_channel_by_name(channel_name, guild_id)
        if not channel:
            logging.error(f"[get_channel_mention] Não encontrado o canal: #{channel_name} em {guild_id if guild_id else GUILD_ID}")
            return f"#{channel_name}"
        return f"<#{channel.id}>"

    # ---------------------------------------------------------------------------------------------------------------- #
    async def get_user_mention(self, user_name: str, guild_id: int | None = None) -> str:
        """Retorna uma string com o nome do usuário."""
        user: discord.Member | None = await self.get_member_by_name(user_name, guild_id)
        if not user:
            logging.error(f"[get_user_mention] Não encontrado o usuário: {user_name} em {guild_id if guild_id else GUILD_ID}")
            return f"@{user_name}"
        return f"<@{user.id}>"

    # ---------------------------------------------------------------------------------------------------------------- #
    async def get_channel_by_name(self, channel_name: str, guild_id: int | None = None) -> discord.abc.GuildChannel | None:
        """Retorna um objeto canal pelo nome. (Pode ser um TextChannel, VoiceChannel, CategoryChannel, etc.)"""
        guild: discord.Guild | None = self.get_guild(guild_id) if guild_id else self.get_guild(GUILD_ID)
        # Pega o servidor pelo id, se não for passado, pega o servidor padrão

        if not guild:
            logging.error(f"[get_channel_by_name] Não encontrado o servidor: #{guild_id if guild_id else GUILD_ID}")
            return None

        channel: discord.abc.GuildChannel | None = discord.utils.get(guild.channels, name=channel_name)

        if not channel:
            logging.error(f"[get_channel_by_name] Não encontrado o canal: #{channel_name} em {guild.name}")
            return None

        return channel

    # ---------------------------------------------------------------------------------------------------------------- #
    async def get_emoji_by_name(self, emoji_name: str, guild_id: int | None = None) -> discord.Emoji | None:
        """Retorna um objeto emoji pelo nome."""
        guild: discord.Guild | None = self.get_guild(guild_id) if guild_id else self.get_guild(GUILD_ID)

        if not guild:
            logging.error(f"[get_emoji_by_name] Não encontrado o servidor: #{guild_id if guild_id else GUILD_ID}")
            return None

        emoji: discord.Emoji | None = discord.utils.get(guild.emojis, name=emoji_name)

        if not emoji:
            logging.error(f"[get_emoji_by_name] Não encontrado o emoji: {emoji_name} em {guild.name}")
            return None

        return emoji

    # ---------------------------------------------------------------------------------------------------------------- #
    async def get_member_by_name(self, user_name: str, guild_id: int | None = None) -> discord.Member | None:
        """Retorna um objeto usuário pelo nome. (Pode ser um User, Member, etc.)"""
        guild: discord.Guild | None = self.get_guild(guild_id) if guild_id else self.get_guild(GUILD_ID)

        if not guild:
            logging.error(f"[get_user_by_name] Não encontrado o servidor: #{guild_id if guild_id else GUILD_ID}")
            return None

        user: discord.Member | None = discord.utils.get(guild.members, name=user_name)

        if not user:
            logging.error(f"[get_user_by_name] Não encontrado o usuário: {user_name} em {guild.name}")
            return None

        return user
