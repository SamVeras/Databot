from discord.ext import commands
import logging
from config import MONGO_URI, MSG_QUEUE_SIZE, WORKERS_COUNT, BATCH_SIZE
import discord
import asyncio
import motor.motor_asyncio
from pymongo import UpdateOne


class DatabaseCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        if not MONGO_URI:
            logging.error("[DatabaseCommands] MONGO_URI não está configurado!")
            raise ValueError("[DatabaseCommands] MONGO_URI environment variable is not set")

        logging.info(f"[DatabaseCommands] Conectando ao MongoDB: {MONGO_URI[:22]}...")

        try:
            self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
            self.db = self.mongo_client["discord_data"]
            self.collection = self.db["messages"]
            logging.info(f"[DatabaseCommands] Conectado ao banco: {self.db.name}, coleção: {self.collection.name}")
        except Exception as e:
            logging.error(f"[DatabaseCommands] Erro ao conectar ao MongoDB: {e}")
            raise ValueError(f"[DatabaseCommands] Erro ao conectar ao MongoDB: {e}")

    @staticmethod
    async def message_to_dict(message: discord.Message) -> dict:
        """Converter uma mensagem para um dicionário."""
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
                "name": getattr(message.channel, "name", None),
            },
            "channel_mentions": [{"id": channel.id, "name": channel.name} for channel in getattr(message, "channel_mentions", [])],
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
                "duration": poll.duration.total_seconds() if poll and getattr(poll, "duration", None) else None,
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
                    for answer in getattr(poll, "answers", [])
                ],
            }
        else:
            message_dict["poll"] = None

        return message_dict

    async def scrape_channel_(self, ctx: commands.Context, silent: bool) -> None:
        """Scrapear um canal."""
        try:
            channel_info = f"{getattr(ctx.channel, 'name', 'unknown')} (ID: {getattr(ctx.channel, 'id', 'unknown')})"
            logging.info(f"[scrape_channel_: {ctx.author.name}] Iniciando scraping no canal: {channel_info}")
            await self.mongo_client.admin.command("ping")
            await self.collection.create_index("id", unique=True)
            logging.info(f"[scrape_channel_: {ctx.author.name}] Conexão com MongoDB estabelecida")
        except Exception as e:
            logging.error(f"[scrape_channel_: {ctx.author.name}] Erro de conexão com MongoDB: {e}")
            if not silent:
                await ctx.send(f"Erro de conexão com MongoDB: {e}")
            return

        async def scraper_worker(message_queue: asyncio.Queue, ready_queue: asyncio.Queue, worker_id: int) -> None:
            logging.info(f"[scraper_worker {worker_id}] Iniciado.")
            processed = 0
            try:
                while True:
                    await asyncio.sleep(0.01)
                    message = await message_queue.get()
                    if message is None:
                        if processed == 0:
                            logging.warning(f"[scraper_worker {worker_id}] Finalizando sem processar nenhuma mensagem.")
                        else:
                            logging.info(f"[scraper_worker {worker_id}] Finalizando com {processed} mensagens processadas.")
                        break
                    try:
                        if processed % 100 == 0:
                            logging.info(f"[scraper_worker {worker_id}] Processadas {processed} mensagens...")
                        data = await self.message_to_dict(message)
                        await ready_queue.put(data)
                        processed += 1
                    except Exception as e:
                        logging.error(f"[scraper_worker {worker_id}] Erro ao processar mensagem {getattr(message, 'id', 'unknown')}: {e}")
            except Exception as e:
                logging.error(f"[scraper_worker {worker_id}] Crashed: {e}")
            logging.info(f"[scraper_worker {worker_id}] Finalizado. Mensagens processadas: {processed}")

        async def mongo_worker() -> None:
            logging.info("[mongo_worker] Iniciado.")
            finished = 0  # Quando todos os workers terminarem, o mongo_worker termina
            inserted = 0
            batch = []
            while True:
                data = await ready_queue.get()
                if data is None:
                    finished += 1  # Um worker terminou
                    if finished >= WORKERS_COUNT:
                        if batch:  # Mongo worker vai parar, mas pode ter algumas mensagens no batch ainda
                            operations = [UpdateOne({"id": d["id"]}, {"$set": d}, upsert=True) for d in batch]
                            if operations:
                                result = await self.collection.bulk_write(operations, ordered=False)
                                inserted += result.upserted_count + result.modified_count
                            batch = []
                        break
                    continue
                # Se não for None, é uma mensagem
                batch.append(data)
                if len(batch) >= BATCH_SIZE:
                    operations = [UpdateOne({"id": d["id"]}, {"$set": d}, upsert=True) for d in batch]
                    if operations:
                        result = await self.collection.bulk_write(operations, ordered=False)
                        inserted += result.upserted_count + result.modified_count
                        logging.info(f"[mongo_worker] Inseridas/atualizadas {len(batch)} mensagens no banco...")
                    batch = []
            # Todos os workers terminaram
            logging.info(f"[mongo_worker] Finalizado. Mensagens inseridas/atualizadas: {inserted}")
            done.set()

        message_queue = asyncio.Queue(MSG_QUEUE_SIZE)  # Queue das mensagens cruas, direto da API do Discord
        ready_queue = asyncio.Queue(MSG_QUEUE_SIZE)  # Queue das mensagens convertidas para dicionário
        done = asyncio.Event()

        workers = [asyncio.create_task(scraper_worker(message_queue, ready_queue, worker_id)) for worker_id in range(WORKERS_COUNT)]
        mongo_task = asyncio.create_task(mongo_worker())

        total_messages = 0
        async for message in ctx.channel.history(limit=None, oldest_first=True):
            await message_queue.put(message)
            total_messages += 1
            if total_messages % 1000 == 0:
                logging.info(f"[scrape_channel_] {total_messages} mensagens já foram recebidas da API...")
        logging.info(f"[scrape_channel_] Total de mensagens recebidas da API: {total_messages}")

        for _ in range(WORKERS_COUNT):
            await message_queue.put(None)

        await asyncio.gather(*workers, return_exceptions=True)  # Aguardar todos os workers terminarem

        for _ in range(WORKERS_COUNT):
            await ready_queue.put(None)

        await done.wait()  # Aguardar o mongo_worker terminar

        logging.info(f"[scrape_channel_] Scraping finalizado para o canal {channel_info}. Total de mensagens: {total_messages}")
        if not silent:
            await ctx.send(f"Coleta de dados em {channel_info} finalizada com sucesso! {total_messages} mensagens coletadas.")
        elif hasattr(ctx, "interaction") and ctx.interaction is not None:
            await ctx.send(f"Coleta de dados em {channel_info} finalizada com sucesso! {total_messages}", ephemeral=True)

    @commands.hybrid_command(name="scrape", description="Coletar dados do canal.")
    @commands.has_permissions(administrator=True)
    async def scrape_channel_loud(self, ctx: commands.Context) -> None:
        cname = getattr(ctx.channel, "name", "desconhecido")
        logging.info(f"[scrape_channel_loud: {ctx.author.name}] Iniciando scraping para o canal {cname}...")
        await ctx.send(f"Iniciando coleta de dados em {cname}")
        await self.scrape_channel_(ctx, silent=False)

    @commands.hybrid_command(name="scrapesilent", description="Coletar dados do canal sem enviar mensagens.")
    @commands.has_permissions(administrator=True)
    async def scrape_channel_silent(self, ctx: commands.Context) -> None:
        cname = getattr(ctx.channel, "name", "desconhecido")
        logging.info(f"[scrape_channel_silent: {ctx.author.name}] Iniciando scraping para o canal {cname}...")
        if hasattr(ctx, "interaction") and ctx.interaction is not None:
            await ctx.interaction.response.send_message(f"Iniciando coleta de dados em {cname}", ephemeral=True)
        await self.scrape_channel_(ctx, silent=True)

    @staticmethod
    async def show_message(msg_id: dict, ctx: commands.Context) -> None:
        """Mostrar uma mensagem específica do banco de dados."""
        logging.info(f"[show_message: {ctx.author.name}] Mostrando mensagem: {msg_id}")

        try:
            content = msg_id.get("content_clean") or ""
            author = msg_id["author"]["name"] if msg_id.get("author") else "Desconhecido"
            channel = msg_id["channel"]["name"] if msg_id.get("channel") else "não sei onde"
            jump_url = msg_id.get("jump_url")
        except Exception as e:
            logging.error(f"[show_message: {ctx.author.name}] Erro ao mostrar mensagem: {e}")
            await ctx.send("Erro ao tentar buscar a mensagem.")
            return

        embed = None

        attachments = msg_id.get("attachments", [])
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
        elif msg_id.get("embeds"):
            embed_data = msg_id["embeds"][0]
            embed = discord.Embed(
                title=embed_data.get("title"),
                description=embed_data.get("description"),
                url=embed_data.get("url"),
            )
            if embed_data.get("image") and embed_data["image"].get("url"):
                embed.set_image(url=embed_data["image"].get("url"))
            if embed_data.get("thumbnail") and embed_data["thumbnail"].get("url"):
                embed.set_thumbnail(url=embed_data["thumbnail"].get("url"))

        logging.info(f"[show_message] Enviando mensagem: {author} em {channel} com o ID {msg_id['id']}: {content[:20]}...")
        message = f"**{author}** em **#{channel}** disse: {jump_url}\n"
        if content.strip():
            message += f">>> {content}\n"
        if embed:
            await ctx.send(content=message, embed=embed)
        else:
            await ctx.send(content=message)

    @commands.hybrid_command(name="show", description="Mostrar uma mensagem específica do banco de dados.")
    async def show_message_id(self, ctx: commands.Context, message_id: int) -> None:
        """Mostrar uma mensagem específica do banco de dados."""
        logging.info(f"[show_message_id: {ctx.author.name}] Mostrando mensagem: {message_id}")
        try:
            message = await self.collection.find_one({"id": message_id})
            if not message:
                await ctx.send("Mensagem não encontrada no banco de dados.")
                return
            logging.info(f"[show_message_id: {ctx.author.name}] Mensagem encontrada: {message['id']}")
            await self.show_message(message, ctx)
        except Exception as e:
            logging.error(f"[show_message_id: {ctx.author.name}] Erro ao mostrar mensagem específica: {e}")
            await ctx.send("Erro ao tentar buscar uma mensagem específica.")

    @commands.hybrid_command(name="random", description="Mostrar uma mensagem aleatória do banco de dados.")
    async def show_random_message(self, ctx: commands.Context) -> None:
        """Mostrar uma mensagem aleatória do banco de dados."""
        logging.info(f"[show_random_message: {ctx.author.name}] Mostrando mensagem aleatória...")
        try:
            cursor = self.collection.aggregate([{"$sample": {"size": 1}}])
            message_list = await cursor.to_list(length=1)
            message = message_list[0] if message_list else None

            if not message:
                await ctx.send("Nenhuma mensagem encontrada no banco de dados.")
                return

            await self.show_message(message, ctx)

        except Exception as e:
            logging.error(f"[show_random_message: {ctx.author.name}] Erro ao mostrar mensagem aleatória: {e}")
            await ctx.send("Erro ao tentar buscar uma mensagem aleatória.")

    @commands.hybrid_command(name="randomfix", description="Mostrar uma mensagem fixada aleatória do banco de dados.")
    async def show_random_fix_message(self, ctx: commands.Context) -> None:
        """Mostrar uma mensagem fixada aleatória do banco de dados."""
        logging.info(f"[show_random_fix_message: {ctx.author.name}] Mostrando mensagem fixada aleatória...")
        try:
            cursor = self.collection.aggregate([{"$match": {"is_pinned": True}}, {"$sample": {"size": 1}}])
            message_list = await cursor.to_list(length=1)
            message = message_list[0] if message_list else None

            if not message:
                await ctx.send("Nenhuma mensagem fixada encontrada no banco de dados.")
                return

            await self.show_message(message, ctx)

        except Exception as e:
            logging.error(f"[show_random_fix_message: {ctx.author.name}] Erro ao mostrar mensagem fixada aleatória: {e}")
            await ctx.send("Erro ao tentar buscar uma mensagem fixada aleatória.")

    @commands.hybrid_command(name="stats", description="Mostrar estatísticas do banco de dados.")
    async def show_stats(self, ctx: commands.Context) -> None:
        """Mostrar estatísticas do banco de dados."""
        logging.info(f"[show_stats: {ctx.author.name}] Mostrando estatísticas do banco de dados...")

        total_messages = await self.collection.count_documents({})
        pipeline = [
            {"$group": {"_id": {"name": "$channel.name"}, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        channel_counts_cursor = self.collection.aggregate(pipeline)
        channel_counts = await channel_counts_cursor.to_list(length=None)

        stats_message = f"**Total de mensagens salvas:** {total_messages}\n"
        if channel_counts:
            i = 1
            for channel in channel_counts:
                channel_name = channel["_id"].get("name", "Desconhecido")
                count = channel["count"]
                stats_message += f"{i}. `#{channel_name}`: {count} mensagens\n"
                i += 1
        else:
            stats_message += "Nenhuma mensagem encontrada por canal. wtf kkk"

        await ctx.send(stats_message)
