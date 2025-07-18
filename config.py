import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
MONGO_URI = os.getenv("MONGO_URI")
BOT_PREFIX = "~"
BULK_SIZE = int(os.getenv("BULK_SIZE", 500))
WORKERS_COUNT = int(os.getenv("WORKERS_COUNT", 10))
MSG_QUEUE_SIZE = int(os.getenv("MSG_QUEUE_SIZE", 500))
