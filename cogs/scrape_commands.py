from discord.ext import commands
import logging
import pymongo
from datetime import timezone
from config import MONGO_URI, BATCH_SIZE
import discord
import asyncio


class ScrapeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if not MONGO_URI:
            logging.error("MONGO_URI não está configurado!")
            raise ValueError("MONGO_URI environment variable is not set")

        logging.info(f"Conectando ao MongoDB: {MONGO_URI[:20]}...")

        self.mongo_client = pymongo.MongoClient(MONGO_URI)
        self.db = self.mongo_client["discord_data"]
        self.collection = self.db["messages"]

        logging.info(f"Conectado ao banco: {self.db.name}, coleção: {self.collection.name}")

    @staticmethod
    async def message_to_dict(message):
        message_dict = {
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
            "jump_url": message.jump_url,
            "channel": {
                "id": message.channel.id,
                "name": message.channel.name,
            },
            "channel_mentions": [
                {"id": channel.id, "name": channel.name} for channel in getattr(message, "channel_mentions", [])
            ],
            "guild": {
                "id": getattr(message.guild, "id", None),
                "name": getattr(message.guild, "name", None),
            },
            "mentions": [{"id": user.id, "name": user.name} for user in message.mentions],
            "mention_roles": [{"id": role.id, "name": role.name} for role in getattr(message, "mention_roles", [])],
            "embeds": [
                {
                    "title": getattr(embed, "title", None),
                    "type": getattr(embed, "type", None),
                    "description": getattr(embed, "description", None),
                    "url": getattr(embed, "url", None),
                    "image": (
                        {
                            "url": getattr(embed.image, "url", None),
                            "width": getattr(embed.image, "width", None),
                            "height": getattr(embed.image, "height", None),
                        }
                        if getattr(embed, "image", None)
                        else None
                    ),
                    "video": (
                        {
                            "url": getattr(embed.video, "url", None),
                            "width": getattr(embed.video, "width", None),
                            "height": getattr(embed.video, "height", None),
                        }
                        if getattr(embed, "video", None)
                        else None
                    ),
                    "thumbnail": (
                        {
                            "url": getattr(embed.thumbnail, "url", None),
                            "width": getattr(embed.thumbnail, "width", None),
                            "height": getattr(embed.thumbnail, "height", None),
                        }
                        if getattr(embed, "thumbnail", None)
                        else None
                    ),
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
            "components": [
                {
                    "type": getattr(component, "type", None),
                    "custom_id": getattr(component, "custom_id", None),
                    "label": getattr(component, "label", None),
                }
                for component in getattr(message, "components", [])
            ],
        }

        if message.reference:
            message_dict["reference"] = {
                "id": message.reference.message_id,
                "channel_id": message.reference.channel_id,
                "guild_id": message.reference.guild_id,
            }
        else:
            message_dict["reference"] = None

        if getattr(message, "poll", None):
            poll = message.poll
            message_dict["poll"] = {
                "question": getattr(poll, "question", None),
                "duration": poll.duration.total_seconds() if poll.duration else None,
                "multiple_choice": getattr(poll, "multiple", None),
                "answers": [
                    {
                        "id": getattr(answer, "id", None),
                        "emoji": (
                            {
                                "id": getattr(answer.emoji, "id", None),
                                "name": getattr(answer.emoji, "name", None),
                                "animated": getattr(answer.emoji, "animated", None),
                                "url": getattr(answer.emoji, "url", None),
                                "string": str(answer.emoji),
                            }
                            if answer.emoji
                            else None
                        ),
                        "text": getattr(answer, "text", None),
                        "count": getattr(answer, "vote_count", None),
                        "victor": getattr(answer, "victor", None),
                        "voters": [{"id": v.id, "name": v.name} async for v in answer.voters()],
                    }
                    for answer in poll.answers
                ],
            }
        else:
            message_dict["poll"] = None

        return message_dict

    @commands.hybrid_command(name="scrape", description="Coletar dados do canal.")
    @commands.has_permissions(administrator=True)
    async def scrape_channel(self, ctx):
        try:
            self.mongo_client.admin.command("ping")
            logging.info("MongoDB connection successful")
        except Exception as e:
            logging.error(f"MongoDB connection failed: {e}")
            await ctx.send(f"Erro de conexão com MongoDB: {e}")
            return

        logging.info(f"Coletando dados do canal {ctx.channel.name}...")
        await ctx.send(f"Coletando dados do canal {ctx.channel.name}...")

        count = 0
        saved_count = 0
        skipped_count = 0
        errors = 0

        existing_ids = {
            doc["id"]: doc.get("edit_date")
            for doc in self.collection.find({"channel.id": ctx.channel.id}, {"id": 1, "edit_date": 1})
        }

        batch = []

        async for message in ctx.channel.history(limit=None, oldest_first=True):
            try:
                existing_edit_date = existing_ids.get(message.id)
                current_edit_date = getattr(message, "edited_at", None)

                if existing_edit_date and existing_edit_date.tzinfo is None:
                    existing_edit_date = existing_edit_date.replace(tzinfo=timezone.utc)

                if existing_edit_date:
                    if current_edit_date and (existing_edit_date is None or current_edit_date > existing_edit_date):
                        message_dict = await self.message_to_dict(message)
                        batch.append(pymongo.UpdateOne({"id": message.id}, {"$set": message_dict}, upsert=True))
                        count += 1
                        saved_count += 1
                        logging.info(f"Atualizada mensagem editada: {message.id}")
                    else:
                        skipped_count += 1
                        count += 1
                    continue

                message_dict = await self.message_to_dict(message)
                batch.append(pymongo.UpdateOne({"id": message.id}, {"$set": message_dict}, upsert=True))
                count += 1

                if len(batch) >= BATCH_SIZE:
                    await asyncio.to_thread(self.collection.bulk_write, batch, ordered=False)
                    batch.clear()
                    logging.info(f"Bulk wrote {BATCH_SIZE} messages...")
                    await asyncio.sleep(0)
            except Exception as e:
                errors += 1
                logging.error(f"Erro ao salvar mensagem {message.id}: {e}")
            if count % 500 == 0:
                logging.info(f"Processadas: {count}, Salvas: {saved_count}, Puladas: {skipped_count}, Erros: {errors}")

        if batch:
            await asyncio.to_thread(self.collection.bulk_write, batch, ordered=False)
            logging.info(f"Bulk wrote final {len(batch)} messages...")

        total_in_db = self.collection.count_documents({})

        logging.info(
            f"Processadas: {count}, Salvas: {saved_count}, Puladas: {skipped_count}, Erros: {errors}, Total no DB: {total_in_db}"
        )
        await ctx.send(
            f"Coleta finalizada.\n**Processadas:** {count}\n**Salvas:** {saved_count}\n**Puladas:** {skipped_count}\n**Erros:** {errors}\n**Total no DB:** {total_in_db}"
        )

    @staticmethod
    async def show_message(message, ctx):
        content = message.get("content_clean") or ""
        author = message["author"]["name"] if message.get("author") else "Desconhecido"
        channel = message["channel"]["name"] if message.get("channel") else "não sei onde"
        jump_url = message.get("jump_url")

        embed = None

        attachments = message.get("attachments", [])
        if attachments:
            embed = discord.Embed()
            for attachment in attachments:
                url = attachment.get("url")
                filename = attachment.get("filename", "")
                if url and filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                    embed.set_image(url=url)
                    break
            for attachment in attachments:
                url = attachment.get("url")
                filename = attachment.get("filename", "")
                if url:
                    embed.add_field(name="Anexo", value=f"[{filename}]({url})", inline=True)
        elif message.get("embeds"):
            embed_data = message["embeds"][0]
            embed = discord.Embed(
                title=embed_data.get("title"),
                description=embed_data.get("description"),
                url=embed_data.get("url"),
            )
            if embed_data.get("image") and embed_data["image"].get("url"):
                embed.set_image(url=embed_data["image"].get("url"))
            if embed_data.get("thumbnail") and embed_data["thumbnail"].get("url"):
                embed.set_thumbnail(url=embed_data["thumbnail"].get("url"))

        await ctx.send(content=f"**{author}** em **#{channel}** disse: {jump_url}\n>>> {content}", embed=embed)

    @commands.hybrid_command(name="show", description="Mostrar uma mensagem específica do banco de dados.")
    async def show_message_id(self, ctx, message_id: int):
        """Mostrar uma mensagem específica do banco de dados."""
        try:
            message = self.collection.find_one({"id": message_id})
            if not message:
                await ctx.send("Mensagem não encontrada no banco de dados.")
                return
            await self.show_message(message, ctx)
        except Exception as e:
            logging.error(f"Erro ao mostrar mensagem específica: {e}")
            await ctx.send("Erro ao tentar buscar uma mensagem específica.")

    @commands.hybrid_command(name="random", description="Mostrar uma mensagem aleatória do banco de dados.")
    async def show_random_message(self, ctx):
        """Mostrar uma mensagem aleatória do banco de dados."""
        try:
            result = self.collection.aggregate([{"$sample": {"size": 1}}])
            message = next(result, None)

            if not message:
                await ctx.send("Nenhuma mensagem encontrada no banco de dados.")
                return

            await self.show_message(message, ctx)

        except Exception as e:
            logging.error(f"Erro ao mostrar mensagem aleatória: {e}")
            await ctx.send("Erro ao tentar buscar uma mensagem aleatória.")

    @commands.hybrid_command(name="randomfix", description="Mostrar uma mensagem fixada aleatória do banco de dados.")
    async def show_random_fix_message(self, ctx):
        try:
            result = self.collection.aggregate([{"$match": {"is_pinned": True}}, {"$sample": {"size": 1}}])
            message = next(result, None)

            if not message:
                await ctx.send("Nenhuma mensagem fixada encontrada no banco de dados.")
                return

            await self.show_message(message, ctx)

        except Exception as e:
            logging.error(f"Erro ao mostrar mensagem fixada aleatória: {e}")
            await ctx.send("Erro ao tentar buscar uma mensagem fixada aleatória.")
