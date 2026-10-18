import asyncio

from client import WikiClient, WikiLink


class WikiCompareEngine:
    client: WikiClient

    def __init__(self, client: WikiClient):
        self.client = client

    async def fetch_links(
        self, pageid_1: int, pageid_2: int
    ) -> tuple[list[WikiLink], list[WikiLink]]:
        links_1, links_2 = await asyncio.gather(
            asyncio.to_thread(self.client.fetch_all_links, pageid_1),
            asyncio.to_thread(self.client.fetch_all_links, pageid_2),
        )

        return links_1, links_2

    def compare_links(
        self, article_1: list[WikiLink], article_2: list[WikiLink]
    ) -> tuple[dict[int, WikiLink], list[int]]:
        unified_hashmap: dict[int, WikiLink] = {}
        colisions: list[int] = []

        for link in [*article_1, *article_2]:
            if unified_hashmap.get(link.pageid) is not None:
                colisions.append(link.pageid)

            unified_hashmap[link.pageid] = link

        return unified_hashmap, colisions

    async def compare(
        self, pageid_1: int, pageid_2: int
    ) -> tuple[dict[int, WikiLink], list[int]]:
        link_1, link_2 = await self.fetch_links(pageid_1, pageid_2)

        return self.compare_links(link_1, link_2)
