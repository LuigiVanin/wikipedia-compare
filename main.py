from datetime import datetime
from dataclasses import dataclass
import re

from textual.app import App, ComposeResult
from textual.widgets import Digits

from client import WikiClient, WikiItem
from utils import normalize_text

if __name__ == "__main__":
    # Your main code logic here
    print("main entrypoint")

    term = input("Search Wiki:\n> ")
    normalizaed_term = normalize_text(term)

    client = WikiClient(email="luisfvanin3@gmail.com")

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

    responses = client.fetch_all_links(article.pageid)

    for index, response in enumerate(responses):
        print(f"{index}. {response.title}")
