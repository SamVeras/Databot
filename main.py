from config import DISCORD_TOKEN, BOT_PREFIX, GUILD_ID, MONGO_URI, BULK_SIZE, WORKERS_COUNT, MSG_QUEUE_SIZE, ACTIVITY_MESSAGE
import discord
from discord.ext import commands
import logging
import signal
import asyncio
import types
from bot import Lad


def signal_handler(signum: int, frame: types.FrameType | None) -> None:
    logging.info(f"[signal_handler] Recebido sinal {signum}, desligando bot...")
    if "bot" in globals():
        asyncio.create_task(bot.close())


def unique_timestamp_id() -> str:
    from uuid import uuid4
    from datetime import datetime

    now: str = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id: str = uuid4().hex[:8]

    return f"{now}_{unique_id}"


def setup_logging() -> None:
    import sys
    import os

    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="%",
    )

    stream_handler = logging.StreamHandler(
        stream=sys.stdout,
    )

    file_handler = logging.FileHandler(
        f"logs/databot_{unique_timestamp_id()}.log",
    )

    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[stream_handler, file_handler],
        encoding="utf-8",
    )

    logging.info("[setup_logging] Configuração do logging concluída.")


def check_env_vars() -> None:
    env_vars = {
        DISCORD_TOKEN: "DISCORD_TOKEN",
        BOT_PREFIX: "BOT_PREFIX",
        MONGO_URI: "MONGO_URI",
        GUILD_ID: "GUILD_ID",
        BULK_SIZE: "BULK_SIZE",
        WORKERS_COUNT: "WORKERS_COUNT",
        MSG_QUEUE_SIZE: "MSG_QUEUE_SIZE",
        ACTIVITY_MESSAGE: "ACTIVITY_MESSAGE",
    }

    for var, var_name in env_vars.items():
        if not var:
            logging.error(f"[check_env_vars] {var_name} não encontrado nas variáveis de ambiente.")
            exit(1)
        var_out = str(var)
        if len(var_out) > 8:
            var_out = var_out[:8] + "..."
        logging.info(f"[check_env_vars] {var_name}: {var_out} ")

    logging.info("[check_env_vars] Variáveis de ambiente verificadas.")


if __name__ == "__main__":

    setup_logging()
    logging.info("[main] Verificando variáveis de ambiente...")

    check_env_vars()

    logging.info("[main] Inicializando bot...")
    bot = Lad(
        command_prefix=commands.when_mentioned_or(BOT_PREFIX),
        intents=discord.Intents.all(),
        activity=discord.CustomActivity(ACTIVITY_MESSAGE),
    )
    logging.info("[main] Bot inicializado com sucesso.")

    logging.info("[main] Registrando sinais de interrupção...")
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Terminação do processo
    logging.info("[main] Sinais de interrupção registrado.")

    try:
        logging.info("[main] Iniciando bot...")
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logging.info("[main] Interrupção do teclado detectada, desligando bot...")
    except Exception as e:
        logging.error(f"[main] Erro inesperado: {e}")
    finally:
        logging.info("[main] Bot desligado.")
