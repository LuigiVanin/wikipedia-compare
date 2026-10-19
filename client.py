from dataclasses import dataclass

import requests


@dataclass
class Params:
    action: str
    list: str
    srsearch: str
    srlimit: int
    format: str

    generator: str
    gplnamespace: int
    gpllimit: int


class WikiItem:
    title: str
    pageid: int
    size: int
    wordcount: int
    snippet: str

    def __init__(
        self,
        title: str,
        pageid: int,
        size: int,
        wordcount: int,
        snippet: str,
    ) -> None:
        self.title = title
        self.pageid = pageid
        self.size = size
        self.wordcount = wordcount
        self.snippet = snippet


class WikiLink:
    title: str
    pageid: int

    def __init__(self, title: str, pageid: int) -> None:
        self.title = title
        self.pageid = pageid


# class WikiLink:


class WikiClient:
    email: str
    header: str

    def __init__(self, email: str) -> None:
        self.email = email
        self.headers = {"User-Agent": f"ap2-playground/0.1 ({self.email})"}

    BASE_URL = "https://pt.wikipedia.org/w/api.php"

    def raw_search(self, query: str, limit: int = 3) -> requests.Response:

        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
        }

        response = requests.get(self.BASE_URL, params=params, headers=self.headers)

        return response

    def search(self, query: str = "", limit: int = 3) -> list[WikiItem]:
        response = self.raw_search(query, limit)

        raw_results = response.json()["query"]["search"]

        print(raw_results)

        results: list[WikiItem] = []

        for r in raw_results:
            results.append(
                WikiItem(
                    title=r["title"],
                    pageid=r["pageid"],
                    size=r["size"],
                    wordcount=r["wordcount"],
                    snippet=r["snippet"],
                )
            )

        return results

    def raw_fetch_links(
        self, pageid: int, cont: dict | None = None
    ) -> requests.Response:

        params = {
            "action": "query",
            "format": "json",
            "pageids": pageid,
            "generator": "links",
            "gplnamespace": 0,
            "gpllimit": 500,
            **(cont or {}),
        }

        response = requests.get(self.BASE_URL, params=params, headers=self.headers)

        return response

    def fetch_all_links(self, pageid: int):
        links: list[WikiLink] = []
        cont: dict | None = None

        while True:
            data = self.raw_fetch_links(pageid, cont).json()

            for page in data["query"]["pages"].values():
                if "missing" not in page:
                    links.append(WikiLink(title=page["title"], pageid=page["pageid"]))

            if "continue" not in data:
                return links

            cont = data["continue"]

    def fetch_content_text(self, pageid: int) -> str:
        params = {
            "action": "query",
            "format": "json",
            "formatversion": 2,
            "prop": "extracts",
            "explaintext": 1,
            "pageids": pageid,
        }

        response = requests.get(self.BASE_URL, params=params, headers=self.headers)

        return response.json()["query"]["pages"][0].get("extract", "")
