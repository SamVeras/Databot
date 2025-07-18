from config import DISCORD_TOKEN, BOT_PREFIX, GUILD_ID, MONGO_URI, BULK_SIZE, WORKERS_COUNT, MSG_QUEUE_SIZE
import discord
from discord.ext import commands
import logging
import signal
import asyncio
import types
from bot import Lad


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)


def signal_handler(signum: int, frame: types.FrameType | None) -> None:
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

    if not GUILD_ID:
        logging.error("[main] GUILD_ID não encontrado nas variáveis de ambiente.")
        exit(1)

    if not DISCORD_TOKEN:
        logging.error("[main] DISCORD_TOKEN não encontrado nas variáveis de ambiente.")
        exit(1)

    if not MONGO_URI:
        logging.error("[main] MONGO_URI não encontrado nas variáveis de ambiente.")
        exit(1)

    conf_msg = f"GUILD_ID: {GUILD_ID}, MONGO_URI: {MONGO_URI[:22]}..., BULK_SIZE: {BULK_SIZE}, WORKERS_COUNT: {WORKERS_COUNT}, MSG_QUEUE_SIZE: {MSG_QUEUE_SIZE}"
    logging.info(f"[main] {conf_msg}")

    bot = Lad(command_prefix=commands.when_mentioned_or(BOT_PREFIX), intents=intents)
    logging.info("[main] Bot inicializado com sucesso.")

    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Terminação do processo
    logging.info("[main] Sinais de interrupção registrado.")

    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logging.info("[main] Interrupção do teclado detectada, desligando bot...")
    except Exception as e:
        logging.error(f"[main] Erro inesperado: {e}")
    finally:
        logging.info("[main] Bot desligado.")
