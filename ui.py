import asyncio
from dataclasses import dataclass
from typing import cast

from textual import on, work
from textual.reactive import reactive
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
    VerticalScroll,
)
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Label,
    ListItem,
    ListView,
    LoadingIndicator,
    Markdown,
)

from client import WikiClient, WikiItem, WikiLink

SEARCH_LIMIT = 5

MARKDOWN_TEMPLATE = """
# Pyhon

template de markdown, server apenas para ser renderizado.
"""

client = WikiClient(email="luisfvanin3@gmail.com")


@dataclass
class SearchSelection:
    item: WikiItem
    input_id: str


class Wiki(HorizontalGroup):
    def compose(self) -> ComposeResult:

        yield Label("Nenhum artigo buscado para comparar")

        # yield Markdown(MARKDOWN_TEMPLATE, classes="wiki-content")


class SearchModal(ModalScreen[SearchSelection | None]):
    search_term: str
    # `loading` já é um reactive do Textual (desabilita o widget quando True)
    searching: bool = True
    results: list[WikiItem] = []
    input_id: str

    BINDINGS = [
        Binding(
            key="escape", action="dismiss", description="Dismiss Modal", priority=True
        ),
        Binding(
            key="enter",
            action="select",
            description="Select Search Item",
            priority=True,
        ),
    ]

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        query: str = "",
        input_id: str = "",
    ) -> None:
        super().__init__(name, id, classes)
        self.search_term = query
        self.input_id = input_id

    def action_select(self) -> None:
        if self.searching or not self.results:
            return

        index = self.query_one("#search-modal__results", ListView).index
        if index is not None:
            self.dismiss(SearchSelection(self.results[index], input_id=self.input_id))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.action_select()

    def on_mount(self) -> None:
        self.search_articles()

    @work(thread=True, exclusive=True)
    def search_articles(self) -> None:
        try:
            results = client.search(self.search_term, limit=SEARCH_LIMIT)
        except Exception as error:
            self.app.call_from_thread(self.show_error, error)
            return

        self.app.call_from_thread(self.show_results, results)

    async def show_results(self, results: list[WikiItem]) -> None:
        self.searching = False
        self.results = results
        self.query_one("#search-modal__loading", LoadingIndicator).display = False
        title = self.query_one("#search-modal__title", Label)

        if not results:
            title.update(f'Nenhum artigo encontrado para "{self.search_term}"')
            return

        title.update(f'Resultado para "{self.search_term}"')

        list_view = self.query_one("#search-modal__results", ListView)
        await list_view.extend(
            ListItem(Label(item.title, markup=False)) for item in results
        )
        list_view.display = True
        list_view.index = 0
        list_view.focus()

    def show_error(self, error: Exception) -> None:
        self.searching = False
        self.query_one("#search-modal__loading", LoadingIndicator).display = False
        self.query_one("#search-modal__title", Label).update(
            f"Erro ao buscar artigos: {error}"
        )

    def compose(self):
        with Vertical(id="search-modal"):
            yield Label(
                f'Buscando artigos para "{self.search_term}"...',
                id="search-modal__title",
                markup=False,
            )
            yield LoadingIndicator(id="search-modal__loading")

            results = ListView(id="search-modal__results")
            results.display = False
            yield results


class WikiHeader(VerticalGroup):

    def compose(self) -> ComposeResult:

        with HorizontalGroup(classes="search-box", id="search-box--1"):
            yield Label("🔎", classes="search-box__prefix")
            yield Input(
                placeholder="Insira um artigo para pesquisar e pressione ENTER...",
                classes="search-box__input",
                id="search-box__input--1",
            )
            # yield Label("✅", classes="search-box__suffix")
            yield Label("🚫", classes="search-box__suffix")

        yield Label("Comparativo com:", id="title")

        with HorizontalGroup(classes="search-box", id="search-box--2"):
            yield Label("🔎", classes="search-box__prefix")
            yield Input(
                placeholder="Insira um artigo para comparar e pressione ENTER...",
                classes="search-box__input",
                id="search-box__input--2",
            )
            # yield Label("✅", classes="search-box__suffix")
            yield Label("🚫", classes="search-box__suffix")

        with HorizontalGroup(id="header-actions"):
            yield Button("Resetar", id="header-actions__reset")
            yield Button("Comparar", id="header-actions__comparer")


class WikiMain(Horizontal):
    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="wiki-main__content-panel"):
            yield Wiki()


class WikiApp(App):
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit App", priority=True),
        Binding(
            key="ctrl+k", action="focus_search", description="Pesquisar", priority=True
        ),
    ]

    CSS_PATH = "./styles/index.tcss"

    article_1: reactive[WikiItem | None] = reactive(None)
    article_2: reactive[WikiItem | None] = reactive(None)

    links_1: list[WikiLink] = []
    links_2: list[WikiLink] = []

    def action_focus_search(self) -> None:
        self.query_one("#search-box__input--1", Input).focus()

    def on_input_submitted(self, event: Input.Submitted):
        if not event.value.strip():
            return
        if event.input.id == "search-box__input--1":
            self.push_screen(
                SearchModal(query=event.value, input_id="search-box__input--1"),
                self.on_select_search_result,
            )
        if event.input.id == "search-box__input--2":
            self.push_screen(
                SearchModal(query=event.value, input_id="search-box__input--2"),
                self.on_select_search_result,
            )

    def on_select_search_result(self, result: SearchSelection | None) -> None:
        if result:
            article_title = ""
            article_title = result.item.title

            if result.input_id == "search-box__input--1":
                self.article_1 = result.item
            if result.input_id == "search-box__input--2":
                self.article_2 = result.item

            element = self.query_one(f"#{result.input_id}", Input)
            element.value = article_title
            self.notify(f"Artigo selecionado: {result.item.title}")

    def watch_article_1(self, item: WikiItem | None) -> None:
        self._set_status("#search-box--1", item)

    def watch_article_2(self, item: WikiItem | None) -> None:
        self._set_status("#search-box--2", item)

    def _set_status(self, box: str, item: WikiItem | None) -> None:
        self.query_one(f"{box} .search-box__suffix", Label).update(
            "✅" if item else "🚫"
        )

    @on(Button.Pressed, "#header-actions__reset")
    def reset_data(self):
        self.article_1 = None
        self.article_2 = None

        for i in range(0, 2):
            element = self.query_one(f"#search-box__input--{i+1}", Input)
            element.clear()

            if i == 0:
                element.focus()

    @on(Button.Pressed, "#header-actions__comparer")
    def comparer_articles(self):
        if not self.article_1 or not self.article_2:
            self.notify(
                "É necessário pesquisar ambos os itens para realizar a comparação",
                severity="error",
            )
            return

        self.fetch_articles_links(self.article_1, self.article_2)

    @work(exclusive=True, group="compare")
    async def fetch_articles_links(
        self, article_1: WikiItem, article_2: WikiItem
    ) -> None:
        self.notify("Buscando links dos artigos...")

        # o client é síncrono (requests), então cada chamada roda em uma thread
        # e o gather aguarda as duas em paralelo
        try:
            self.links_1, self.links_2 = await asyncio.gather(
                asyncio.to_thread(client.fetch_all_links, article_1.pageid),
                asyncio.to_thread(client.fetch_all_links, article_2.pageid),
            )
        except Exception as error:
            self.notify(f"Erro ao buscar links: {error}", severity="error")
            return

        self.notify(
            f"{article_1.title}: {len(self.links_1)} links | "
            f"{article_2.title}: {len(self.links_2)} links"
        )

    def compose(self) -> ComposeResult:
        yield WikiHeader(name="app header")
        yield WikiMain(name="wiki main", id="wiki-main")


if __name__ == "__main__":
    print("Hello, world!")

    app = WikiApp()
    app.run()
