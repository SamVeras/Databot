from discord.ext import commands
import logging


class FunCommands(commands.Cog):

    # ---------------------------------------------------------------------------------------------------------------- #
    def __init__(self, bot) -> None:
        self.bot = bot

    # ---------------------------------------------------------------------------------------------------------------- #
    @commands.hybrid_command(name="randomwiki", description="Pegar um link aleatório da Wikipédia.")
    async def random_wikipedia_article(self, ctx: commands.Context, lang: str = "pt"):
        """Envia um artigo aleatório da Wikipédia no idioma especificado, se possível."""
        lang = lang.lower()
        user = ctx.author.name
        logging.info(f"[randomwiki: {user}] Solicitando artigo em '{lang}'")
        # Português, Inglês, Espanhol, Francês, Alemão, Italiano, Japonês, Russo, Chinês e Bósnio
        supported_langs: set[str] = {"pt", "en", "es", "fr", "de", "it", "ja", "ru", "zh", "ba"}

        if lang not in supported_langs:
            e: str = await self.bot.get_random_emoji_string()
            langs: str = f"{', '.join(supported_langs)}"
            logging.warning(f"[randomwiki: {user}] Idioma inválido: '{lang}'")
            await ctx.send(f"{e} O idioma '{lang}' não está na lista de idiomas válidos. ({langs})")
            return

        api_url: str = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "random",
            "rnnamespace": 0,  # artigos principais
            "rnlimit": 1,
            "format": "json",
        }

        import aiohttp
        import urllib.parse as up

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params) as response:
                    if response.status != 200:
                        logging.error(f"[randomwiki: {user}] Falha ao acessar API ({response.status})")
                        await ctx.send(f"{await self.bot.get_random_emoji_string()} Erro ao acesasr a API.")
                        return
                    data = await response.json()

            title: str = data["query"]["random"][0]["title"]
            page_url = f"https://{lang}.wikipedia.org/wiki/{up.quote(title.replace(' ', '_'))}"

            logging.info(f"[randomwiki: {user}] Artigo encontrado: {title} ({page_url})")
            await ctx.send(f"Artigo aleatório: [{title}]({page_url})")

        except Exception as e:
            logging.error(f"[randomwiki: {user}] Erro inesperado: {e}")
            await ctx.send(f"{self.bot.get_random_emoji_string()} Ocorreu erro ao tentar buscar artigo.")
