from discord.ext import commands
import logging
import pymongo
from datetime import datetime
from config import MONGO_URI


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
                    "title": embed.title,
                    "type": getattr(embed.type, "name", str(embed.type)) if embed.type else None,
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
            message_dict["poll"] = None

        return message_dict

    @commands.hybrid_command(name="scrape", description="Coletar dados do canal.")
    @commands.has_permissions(administrator=True)
    async def scrape_channel(self, ctx):
        """Coletar dados do canal e guarda em um arquivo."""
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

        async for message in ctx.channel.history(limit=None, oldest_first=True):
            try:
                existing = self.collection.find_one({"id": message.id})
                if existing:
                    existing_edit_date = existing.get("edit_date")
                    current_edit_date = getattr(message, "edited_at", None)

                    if current_edit_date and (existing_edit_date is None or current_edit_date > existing_edit_date):
                        message_dict = await self.message_to_dict(message)
                        result = self.collection.update_one({"id": message.id}, {"$set": message_dict}, upsert=True)
                        count += 1
                        saved_count += 1
                        logging.info(f"Atualizada mensagem editada: {message.id}")
                    else:
                        skipped_count += 1
                        count += 1
                    continue

                message_dict = await self.message_to_dict(message)
                result = self.collection.update_one({"id": message.id}, {"$set": message_dict}, upsert=True)
                count += 1
                if result.modified_count > 0 or result.upserted_id:
                    saved_count += 1
            except Exception as e:
                errors += 1
                logging.error(f"Erro ao salvar mensagem {message.id}: {e}")
            if count % 500 == 0:
                logging.info(f"Processadas: {count}, Salvas: {saved_count}, Puladas: {skipped_count}, Erros: {errors}")

        total_in_db = self.collection.count_documents({})

        logging.info(
            f"Processadas: {count}, Salvas: {saved_count}, Puladas: {skipped_count}, Erros: {errors}, Total no DB: {total_in_db}"
        )
        await ctx.send(
            f"Coleta finalizada.\n**Processadas:** {count}\n**Salvas:** {saved_count}\n**Puladas:** {skipped_count}\n**Erros:** {errors}\n**Total no DB:** {total_in_db}"
        )

    @commands.hybrid_command(name="dbstatus", description="Verificar status do banco de dados.")
    @commands.has_permissions(administrator=True)
    async def db_status(self, ctx):
        """Verificar se o MongoDB está funcionando e quantos documentos existem."""
        try:
            self.mongo_client.admin.command("ping")
            total_docs = self.collection.count_documents({})
            sample = list(self.collection.find().limit(1))

            status_msg = f"**MongoDB conectado**\n**Documentos:** {total_docs}"

            if sample:
                latest_doc = sample[0]
                status_msg += f"\n**Último documento:** {latest_doc.get('id', 'N/A')}"
                status_msg += f"\n**Autor:** {latest_doc.get('author', {}).get('name', 'N/A')}"

            await ctx.send(status_msg)

        except Exception as e:
            logging.error(f"Erro ao verificar DB: {e}")
            await ctx.send(f"**Erro de conexão:** {e}")

    @commands.hybrid_command(name="random", description="Mostrar uma mensagem aleatória do banco de dados.")
    async def show_random_message(self, ctx):
        """Mostrar uma mensagem aleatória do banco de dados."""
        try:
            result = self.collection.aggregate([{"$sample": {"size": 1}}])
            message = next(result, None)

            if not message:
                await ctx.send("Nenhuma mensagem encontrada no banco de dados.")
                return

            content = message.get("content_clean") or "[sem conteúdo]"
            author = message["author"]["name"] if message.get("author") else "Desconhecido"
            channel = message["channel"]["name"] if message.get("channel") else "não sei onde"
            jump_url = message.get("jump_url")
            await ctx.send(f"**{author}** em **#{channel}** disse: {jump_url}\n>>> {content}")

        except Exception as e:
            logging.error(f"Erro ao mostrar mensagem aleatória: {e}")
            await ctx.send("Erro ao tentar buscar uma mensagem aleatória.")

    # @commands.hybrid_command(name="showdata", description="Mostrar alguns dados salvos no banco.")
    # @commands.has_permissions(administrator=True)
    # async def show_data(self, ctx):
    #     """Mostrar alguns exemplos de dados salvos no MongoDB."""
    #     try:
    #         docs = list(self.collection.find().limit(5))

    #         if not docs:
    #             await ctx.send("**Nenhum dado encontrado no banco.**")
    #             return

    #         response = "**Dados salvos no MongoDB:**\n\n"

    #         for i, doc in enumerate(docs, 1):
    #             author_name = doc.get("author", {}).get("name", "Unknown")
    #             content = doc.get("content_clean", "")[:100]
    #             msg_id = doc.get("id", "N/A")

    #             response += f"**{i}.** ID: {msg_id}\n"
    #             response += f"**Autor:** {author_name}\n"
    #             response += f"**Conteúdo:** {content}...\n\n"

    #         await ctx.send(response)

    #     except Exception as e:
    #         logging.error(f"Erro ao mostrar dados: {e}")
    #         await ctx.send(f"**Erro:** {e}")
