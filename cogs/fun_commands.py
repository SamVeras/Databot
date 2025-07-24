from discord.ext import commands
from googlesearch import search, SearchResult
import logging
import discord


class FunCommands(commands.Cog):

    # ---------------------------------------------------------------------------------------------------------------- #
    def __init__(self, bot) -> None:
        self.bot = bot

    # ---------------------------------------------------------------------------------------------------------------- #
    @commands.hybrid_command(name="randomwiki", description="Pegar um link aleatório da Wikipédia.")
    async def random_wikipedia_article(self, ctx: commands.Context, lang: str = "pt"):
        """Envia um artigo aleatório da Wikipédia no idioma especificado, se possível."""
        lang = lang.lower()
        user: str = ctx.author.name
        logging.info(f"[randomwiki: {user}] Solicitando artigo em '{lang}'")
        # Português, Inglês, Espanhol, Francês, Alemão, Italiano, Japonês, Russo, Chinês e Bósnio
        supported_langs: set[str] = {"pt", "en", "es", "fr", "de", "it", "ja", "ru", "zh", "ba"}

        if lang not in supported_langs:
            emoji: str = await self.bot.get_random_emoji_string()
            langs: str = f"{', '.join(supported_langs)}"
            logging.warning(f"[randomwiki: {user}] Idioma inválido: '{lang}'")
            await ctx.send(f"{emoji} O idioma '{lang}' não está na lista de idiomas válidos. ({langs})")
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

    # ---------------------------------------------------------------------------------------------------------------- #
    def google_search_links(self, query: str, num_results: int = 5) -> list[str]:
        logging.info(f"[google_search_links] Query: '{query}'")
        try:
            results_raw = search(query, num_results, safe="off")
            results_string = [str(r) for r in results_raw]
            results_filtered = [r for r in results_string if r.startswith("http")]

            logging.info(f"[google_search_links] Resultados brutos: {results_string}")
            logging.info(f"[google_search_links] Resultados filtrados: {results_filtered}")

            return results_filtered

        except Exception as e:
            logging.error(f"[google_search_links] Erro na busca: {e}")
            return []

    # ---------------------------------------------------------------------------------------------------------------- #
    @commands.hybrid_command(name="lucky", description="I'm feeling lucky! (retorna o primeiro resultado da pesquisa)")
    async def lucky_search(self, ctx: commands.Context, *, query: str):
        user: str = ctx.author.name
        try:
            results = self.google_search_links(query, num_results=5)

            if not results:
                logging.error(f"[lucky_search: {user}] Nada encontrado.")
                await ctx.send("Não encontrei nada.")
                return

            await ctx.send(results[0])

        except Exception as e:
            logging.error(f"[lucky_search: {user}] Erro inesperado: {e}")
            await ctx.send("Erro ao buscar resultado.")

    # ---------------------------------------------------------------------------------------------------------------- #
    @commands.hybrid_command(name="search", description="Pesquisar algo no Google.")
    async def search_stuff(self, ctx: commands.Context, *, query: str):
        user: str = ctx.author.name
        try:
            results = self.google_search_links(query, 13)

            if not results:
                logging.error(f"[search_stuff: {user}] Nada encontrado.")
                await ctx.send("Não encontrei nada...")
                return

            results = results[:10]

            message: str = f"{len(results)} resultados encontrados:\n"
            message += "\n".join(f"{c}. <{r}>" for c, r in enumerate(results))
            await ctx.send(message)

        except Exception as e:
            logging.error(f"[search_stuff: {user}] Erro inesperado: {e}")
            await ctx.send("Erro ao buscar resultado.")
