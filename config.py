import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # int token
GUILD_ID = int(os.getenv("GUILD_ID"))  # int token
MONGO_URI = os.getenv("MONGO_URI")  # mongodb://localhost:27017
BOT_PREFIX = os.getenv("BOT_PREFIX")  # "~"
BULK_SIZE = int(os.getenv("BULK_SIZE"))  # 500
WORKERS_COUNT = int(os.getenv("WORKERS_COUNT"))  # 10
MSG_QUEUE_SIZE = int(os.getenv("MSG_QUEUE_SIZE"))  # 500
REMINDER_CHANNEL_NAME = os.getenv("REMINDER_CHANNEL_NAME")  # "lembretes"
