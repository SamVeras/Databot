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
        msg_dict = {
            "id": message.id,
            "type": message.type.value,
            "tts": message.tts,
            "flags": message.flags.value,
            "mention_everyone": getattr(message, "mention_everyone", False),
            "webhook_id": getattr(message, "webhook_id", None),
            "author": {
                "id": message.author.id,
                "name": message.author.name,
            },
            "content_raw": message.content,
            "content_clean": message.clean_content,
            "creation_date": message.created_at,
            "edit_date": getattr(message, "edited_at", None),
            "is_pinned": message.pinned,
            "channel": {
                "id": message.channel.id,
                "name": message.channel.name,
            },
            "channel_mentions": getattr(message, "channel_mentions", []),
            "guild": {
                "id": getattr(message.guild, "id", None),
                "name": getattr(message.guild, "name", None),
            },
            "mentions": [{"id": user.id, "name": user.name} for user in message.mentions],
            "mention_roles": getattr(message, "mention_roles", []),
            "embeds": [
                {
                    "title": embed.title,
                    "type": embed.type.name,
                    "description": embed.description,
                    "url": embed.url,
                }
                for embed in message.embeds
            ],
            "attachments": [
                {
                    "id": attach.id,
                    "url": attach.url,
                    "proxy_url": attach.proxy_url,
                    "filename": attach.filename,
                    "content_type": attach.content_type,
                    "spoiler": attach.is_spoiler(),
                    "size": attach.size,
                    "width": getattr(attach, "width", None),
                    "height": getattr(attach, "height", None),
                    "duration_secs": getattr(attach, "duration_secs", None),
                }
                for attach in message.attachments
            ],
            "reactions": [{"emoji": str(react.emoji), "count": react.count} for react in message.reactions],
            "stickers": [
                {
                    "id": sticker.id,
                    "name": sticker.name,
                    "url": getattr(sticker, "url", None),
                    "format": getattr(sticker, "format", None),
                }
                for sticker in message.stickers
            ],
            "components": getattr(message, "components", []),
        }

        if message.reference:
            msg_dict["reference"] = {
                "id": message.reference.message_id,
                "channel_id": message.reference.channel_id,
                "guild_id": message.reference.guild_id,
            }
        else:
            msg_dict["reference"] = None

        if getattr(message, "poll", None):
            poll = message.poll
            msg_dict["poll"] = {
                "question": getattr(poll, "question", None),
                "duration": getattr(poll, "duration", None),
                "multiple_choice": getattr(poll, "multiple", None),
                "answers": [
                    {
                        "id": getattr(answer, "id", None),
                        "emoji": getattr(answer, "emoji", None),
                        "text": getattr(answer, "text", None),
                        "count": getattr(answer, "vote_count", None),
                        "victor": getattr(answer, "victor", None),
                        "voters": [{"id": v.id, "name": v.name} async for v in answer.voters()],
                    }
                    for answer in poll.answers
                ],
            }
        else:
            msg_dict["poll"] = None

        return msg_dict

    @commands.hybrid_command(name="scrape", description="Coletar dados do canal.")
    @commands.has_permissions(administrator=True)
    async def scrape_channel(self, ctx):
        """Coletar dados do canal e guarda em um arquivo."""
        logging.info(f"Coletando dados do canal {ctx.channel.name}...")
        await ctx.send(f"Coletando dados do canal {ctx.channel.name}...")

        count = 0
        async for message in ctx.channel.history(limit=50, oldest_first=True):
            msg_dict = await self.message_to_dict(message)
            self.collection.update_one({"id": message.id}, {"$set": msg_dict}, upsert=True)
            count += 1

        logging.info(f"{count} mensagens salvas no MongoDB.")
        await ctx.send(f"✅ Coleta finalizada. **{count} mensagens** salvas no banco de dados.")
