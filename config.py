import os
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
MONGO_URI = os.getenv("MONGO_URI")
BOT_PREFIX = "~"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 500))
