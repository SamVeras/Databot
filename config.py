import os
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
MONGO_URI = os.getenv("MONGO_URI")
BOT_PREFIX = "~"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 500))
MSG_QUEUE_SIZE = int(os.getenv("MSG_QUEUE_SIZE", 500))
WORKERS_COUNT = int(os.getenv("WORKERS_COUNT", 10))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 500))
