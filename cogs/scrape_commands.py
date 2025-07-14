from discord.ext import commands
import csv
from datetime import datetime
import os


class ScrapeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="scrape", description="Coletar dados")
    @commands.has_permissions(administrator=True)
    async def scrape(self, ctx):
        channel = ctx.channel
        guild = ctx.guild
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraped_data_{guild.name}_{channel.name}_{timestamp}.csv"
        filename = "".join(c for c in filename if c.isalnum() or c in (" ", "-", "_", ".")).rstrip()

        os.makedirs("scraped_data", exist_ok=True)
        filepath = os.path.join("scraped_data", filename)

        print(f"Iniciando coleta de dados do canal {channel.name}...")
        await ctx.send(f"Iniciando coleta de dados do canal {channel.name}...")

        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=[
                    "timestamp",
                    "author_id",
                    "author_name",
                    "author_discriminator",
                    "message_id",
                    "content",
                    "channel_name",
                    "guild_name",
                ],
            )
            writer.writeheader()

            message_count = 0
            async for message in channel.history(limit=None, oldest_first=True):
                content = message.content.replace('"', '""')
                content = message.content.replace("\n", "\\n")

                writer.writerow(
                    {
                        "timestamp": message.created_at.isoformat(),
                        "author_id": message.author.id,
                        "author_name": message.author.name,
                        "author_discriminator": message.author.discriminator,
                        "message_id": message.id,
                        "content": content,
                        "channel_name": channel.name,
                        "guild_name": guild.name,
                    }
                )
                message_count += 1

                if message_count % 100 == 0:
                    print(f"{message_count} mensagens processadas...")

        print(f"{message_count} mensagens salvas em {filepath}.")
        await ctx.send(f"{message_count} mensagens salvas em {filepath}.")
