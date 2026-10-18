import asyncio
from dataclasses import dataclass

from client import WikiClient, WikiLink


@dataclass
class CompareResult:
    links_map: dict[int, WikiLink] = {}
    colisions: list[int] = []
    links: dict[int, list[int]] = {}


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
        links_map: dict[int, WikiLink] = {}
        colisions: list[int] = []

        for link in [*article_1, *article_2]:
            if links_map.get(link.pageid) is not None:
                colisions.append(link.pageid)

            links_map[link.pageid] = link

        return links_map, colisions

    async def compare(self, pageid_1: int, pageid_2: int) -> CompareResult:
        link_1, link_2 = await self.fetch_links(pageid_1, pageid_2)

        links_map, colisions = self.compare_links(link_1, link_2)

        return CompareResult(
            links_map,
            colisions,
            links={
                pageid_1: [link.pageid for link in link_1],
                pageid_2: [link.pageid for link in link_2],
            },
        )
