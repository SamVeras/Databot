from discord.ext import commands
import logging
import parsedatetime
import datetime
import discord
import asyncio
import pytz


class TimeCommands(commands.Cog):

    # ---------------------------------------------------------------------------------------------------------------- #
    def __init__(self, bot) -> None:
        self.bot = bot
        self.mongo_client = bot.mongo_client
        self.collection = bot.collections["reminders"]
        self.calendar = parsedatetime.Calendar()

    # ---------------------------------------------------------------------------------------------------------------- #
    @commands.hybrid_command(name="parsetime", description="Testar o parser de datas.")
    async def parsetime(self, ctx: commands.Context, *, time: str) -> None:
        """Testar o parser de datas."""
        try:
            time_struct, status = self.calendar.parse(time)
            dt = datetime.datetime(*time_struct[:6])
            await ctx.send(f"`status: {status}`\n`time: {time}`\n`dt: {dt.strftime('%d/%m/%Y %H:%M:%S')}`")
        except Exception as e:
            logging.error(f"[parsetime] {e}")

    # ---------------------------------------------------------------------------------------------------------------- #
    @commands.hybrid_command(name="remindme", description="Definir um lembrete.")
    async def remindme(self, ctx: commands.Context, time: str, *, reminder: str) -> None:
        """Definir um lembrete."""
        now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
        time_struct, status = self.calendar.parse(time)
        remind_time = datetime.datetime(*time_struct[:6]).astimezone(pytz.timezone("America/Sao_Paulo"))
        logging.info(f"[remindme] now: {now}, remind_time: {remind_time}, status: {status}")

        if not status or remind_time < now:
            if hasattr(ctx, "interaction") and ctx.interaction is not None:
                await ctx.interaction.response.send_message("A data informada é inválida ou já passou.", ephemeral=True)
            else:
                await ctx.send("A data informada é inválida ou já passou.")
            return

        reminder_dict = {
            "user_id": ctx.author.id,  # int
            "message": reminder,  # str
            "remind_at": remind_time.astimezone(pytz.timezone("America/Sao_Paulo")),  # ISODate
            "delivered": False,  # bool
        }

        confirm_message = await ctx.send(
            f"Você quer definir este lembrete?\n" f"**Mensagem:** {reminder}\n" f"**Data/hora:** {remind_time.strftime('%d/%m/%Y %H:%M:%S')}\n"
        )

        try:
            for emoji in ["✅", "❌"]:
                await confirm_message.add_reaction(emoji)
        except discord.Forbidden:
            await ctx.send("Não tenho permissão para adicionar reações a esta mensagem.")
            return

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                user == ctx.author  # usuário correto
                and str(reaction.emoji) in ["✅", "❌"]  # apenas ✅ ou ❌
                and reaction.message.id == confirm_message.id  # mensagem do bot
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await confirm_message.edit(content="Tempo esgotado. Lembrete não definido.")
            return

        if str(reaction.emoji) == "❌":
            await confirm_message.edit(content=confirm_message.content + "\n\n*Lembrete cancelado pelo usuário.*")
            return

        await self.collection.insert_one(reminder_dict)
        ftime = remind_time.astimezone(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
        await confirm_message.clear_reactions()
        await confirm_message.edit(content=confirm_message.content + f"\n\n*Lembrete confirmado e definido para {ftime}.*")
