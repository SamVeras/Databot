from discord.ext import commands
import logging


class FunCommands(commands.Cog):

    # ---------------------------------------------------------------------------------------------------------------- #
    def __init__(self, bot) -> None:
        self.bot = bot
