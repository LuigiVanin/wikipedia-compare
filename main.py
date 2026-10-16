from dataclasses import dataclass
from datetime import datetime
import re
import unicodedata
import requests

from textual.app import App, ComposeResult
from textual.widgets import Digits


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.strip().lower())
    text = "".join(c for c in text if not unicodedata.combining(c))

    text = re.sub(r"[^a-z0-9\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


class ClockApp(App):
    CSS = """
    Screen { align: center middle; }
    Digits { width: auto; }
    """

    def compose(self) -> ComposeResult:
        yield Digits("")

    def on_ready(self) -> None:
        self.update_clock()
        self.set_interval(1, self.update_clock)

    def update_clock(self) -> None:
        clock = datetime.now().time()
        self.query_one(Digits).update(f"{clock:%T}")


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

    headers = {"User-Agent": "ap2-playground/0.1 (luisfvanin3@gmail.com)"}
    BASE_URL = "https://pt.wikipedia.org/w/api.php"

    def raw_search(self, query: str) -> requests.Response:

        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 3,
            "format": "json",
        }

        response = requests.get(self.BASE_URL, params=params, headers=self.headers)

        return response

    def search(self, query: str = "") -> list[WikiItem]:
        response = self.raw_search(query)

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

    def raw_fetch_links(self, pageid: int) -> requests.Response:

        params = {
            "action": "query",
            "format": "json",
            "pageids": pageid,
            "generator": "links",
            "gplnamespace": 0,
            "gpllimit": 100,
        }

        response = requests.get(self.BASE_URL, params=params, headers=self.headers)

        return response


if __name__ == "__main__":
    # Your main code logic here
    print("main entrypoint")

    term = input("Search Wiki:\n> ")
    normalizaed_term = normalize_text(term)

    client = WikiClient()

    found_articles = client.search(term)

    if len(found_articles) == 0:
        print("Wiki Not Found Try Another Rerm")

    wiki: None | WikiItem = None

    for article in found_articles:
        if normalize_text(article.title) == normalizaed_term:
            wiki = article
            break

    if wiki is None:

        while True:
            print("Choose from results:")

            for index, article in enumerate(found_articles):
                print(f"{index+1}. {article.title}")

            print(f"{0}. None of them")

            raw_selected_index = input("> ").strip()
            selected_index = int(raw_selected_index)

            if selected_index.is_integer() and (
                selected_index >= 0 or selected_index < len(found_articles)
            ):
                if selected_index == 0:
                    continue

                wiki = found_articles[selected_index - 1]
                break

    print(f"selected Wiki: {wiki.title}")

    print(f"Fetch its relations?")

    answer = input("y(yes) / n(no)\n> ")

    if not re.compile(r"y(es)?", re.IGNORECASE).fullmatch(answer):
        print("END OF THE PROGRAM")
        exit()

    response = client.raw_fetch_links(article.pageid)

    print(response.json())
    # app = ClockApp()
    # app.run()
