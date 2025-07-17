from discord.ext import commands
import logging
import pymongo
from datetime import datetime
from config import MONGO_URI


class ScrapeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = pymongo.MongoClient(MONGO_URI)
        self.db = self.mongo_client["discord_data"]
        self.collection = self.db["messages"]

    @staticmethod
    async def message_to_dict(message):
        return {
            "id": getattr(message, "id", None),
            "author": ({"id": message.author.id, "name": message.author.name}),
            "content_raw": message.content,
            "content_clean": message.clean_content,
            "creation_date": message.created_at,
            "edit_date": getattr(message, "edited_at", None),
            "is_pinned": message.pinned,
            "channel": {
                "id": getattr(message.channel, "id", None),
                "name": getattr(message.channel, "name", None),
            },
            "guild": {
                "id": getattr(message.guild, "id", None),
                "name": getattr(message.guild, "name", None),
            },
            "reference": (
                {
                    "id": getattr(message.reference, "message_id", None),
                    "channel_id": getattr(message.reference, "channel_id", None),
                    "guild_id": getattr(message.reference, "guild_id", None),
                }
            ),
            "embeds": [
                {
                    "title": embed.title,
                    "type": embed.type,
                    "description": embed.description,
                    "url": embed.url,
                }
                for embed in message.embeds
            ],
            "reactions": [
                {
                    "emoji": reaction.emoji,
                    "count": reaction.count,
                }
                for reaction in message.reactions
            ],
            "mentions": [
                {
                    "id": user.id,
                    "name": user.name,
                }
                for user in message.mentions
            ],
            "mentions_roles": [
                {
                    "id": role.id,
                    "name": role.name,
                    "color": getattr(role.color, "value", None),
                }
                for role in message.role_mentions
            ],
            "stickers": [
                {
                    "id": sticker.id,
                    "name": sticker.name,
                    "url": getattr(sticker, "url", None),
                    "format": getattr(sticker, "format", None),
                }
                for sticker in message.stickers
            ],
            "attachments": [
                {
                    "id": attachment.id,
                    "url": getattr(attachment, "url", None),
                    "filename": getattr(attachment, "filename", None),
                    "content_type": getattr(attachment, "content_type", None),
                    "spoiler": attachment.is_spoiler(),
                    "size": getattr(attachment, "size", None),
                    "width": getattr(attachment, "width", None),
                    "height": getattr(attachment, "height", None),
                    "duration_secs": getattr(attachment, "duration_secs", None),
                }
                for attachment in message.attachments
            ],
            "poll": (
                {
                    "question": getattr(message.poll, "question", None),  # str
                    "duration": getattr(message.poll, "duration", None),  # datetime.timedelta
                    "multiple_choice": getattr(message.poll, "multiple", None),  # bool
                    "answers": [
                        {
                            "id": getattr(answer, "id", None),  # int
                            "emoji": getattr(answer, "emoji", None),  # str
                            "text": getattr(answer, "text", None),  # str
                            "count": getattr(answer, "vote_count", None),  # int
                            "victor": getattr(answer, "victor", None),  # bool
                            "voters": [
                                {
                                    "id": getattr(voter, "id", None),  # int
                                    "name": getattr(voter, "name", None),  # str
                                }
                                async for voter in answer.voters()
                            ],  # list
                        }
                        for answer in message.poll.answers
                    ],
                }
                if hasattr(message, "poll") and message.poll
                else None
            ),
        }

    @commands.hybrid_command(name="scrape", description="Coletar dados do canal.")
    @commands.has_permissions(administrator=True)
    async def scrape_channel(self, ctx):
        """Coletar dados do canal e guarda em um arquivo."""
        logging.info(f"Coletando dados do canal {ctx.channel.name}...")
        await ctx.send(f"Coletando dados do canal {ctx.channel.name}...")
        # to-do, fazer depois
        pass
