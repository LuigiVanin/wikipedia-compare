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
    Static,
)

from client import WikiClient, WikiItem, WikiLink
from engine import CompareResult, WikiCompareEngine

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


class WikiMain(VerticalGroup):
    def compose(self) -> ComposeResult:

        yield Label("Nenhum artigo buscado para comparar", id="wiki__title")

        loading = LoadingIndicator(id="wiki__loading")
        loading.display = False
        yield loading

        collisions = ListView(id="wiki__collisions")
        collisions.display = False
        yield collisions

    async def show_loading(self, title_1: str, title_2: str) -> None:
        self.query_one("#wiki__title", Label).update(
            f'Buscando links em comum entre "{title_1}" e "{title_2}"...'
        )
        self.query_one("#wiki__loading", LoadingIndicator).display = True

        list_view = self.query_one("#wiki__collisions", ListView)
        list_view.display = False
        await list_view.clear()

    async def show_collisions(
        self, title_1: str, title_2: str, links: list[WikiLink]
    ) -> None:
        self.query_one("#wiki__loading", LoadingIndicator).display = False
        title = self.query_one("#wiki__title", Label)

        if not links:
            title.update(f'Nenhum link em comum entre "{title_1}" e "{title_2}"')
            return

        title.update(f'{len(links)} links em comum entre "{title_1}" e "{title_2}"')

        list_view = self.query_one("#wiki__collisions", ListView)
        await list_view.extend(
            ListItem(Label(link.title, markup=False), id=f"link-{link.pageid}")
            for link in links
        )
        list_view.display = True
        list_view.index = 0
        list_view.focus()

    def show_error(self, error: Exception) -> None:
        self.query_one("#wiki__loading", LoadingIndicator).display = False
        self.query_one("#wiki__title", Label).update(f"Erro ao buscar links: {error}")


class WikiModal(ModalScreen[int | None]):
    pageid: int
    # `title` já é um reactive do Screen no Textual
    article_title: str

    content: str = ""

    BINDINGS = [
        Binding(
            key="escape", action="dismiss", description="Dismiss Modal", priority=True
        ),
    ]

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        pageid: int | None = None,
        title: str | None = None,
    ) -> None:

        super().__init__(name, id, classes)

        if pageid is not None:
            self.pageid = pageid

        self.article_title = title or ""

    def on_mount(self) -> None:
        self.fetch_content()

    @work(thread=True, exclusive=True)
    def fetch_content(self) -> None:
        try:
            self.content = client.fetch_content_text(self.pageid)
        except Exception as error:
            self.app.call_from_thread(self.show_error, error)
            return

        self.app.call_from_thread(self.show_content, self.content)

    def show_content(self, content: str):
        self.query_one("#wiki-modal__loading", LoadingIndicator).display = False

        title = self.query_one("#wiki-modal__title", Label)
        title.update(self.article_title)

        if not content:
            title.update(f'Nenhum conteúdo encontrado para "{self.article_title}"')
            return

        self.query_one("#wiki-modal__content__text", Static).update(content)

        container = self.query_one("#wiki-modal__content", VerticalScroll)
        container.display = True
        container.focus()

    def show_error(self, error: Exception):
        self.query_one("#wiki-modal__loading", LoadingIndicator).display = False
        self.query_one("#wiki-modal__title", Label).update(
            f"Erro ao buscar artigo: {error}"
        )

    def compose(self):
        with Vertical(id="wiki-modal"):
            yield Label(
                f'Buscando artigo "{self.article_title}"...',
                id="wiki-modal__title",
                markup=False,
            )
            yield LoadingIndicator(id="wiki-modal__loading")

            content = VerticalScroll(
                VerticalGroup(Static(id="wiki-modal__content__text", markup=False)),
                id="wiki-modal__content",
            )
            content.display = False
            yield content


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

    collisions: reactive[list[int]] = reactive([])
    links_map: reactive[dict[int, WikiLink]] = reactive({})

    # links_1: list[WikiLink] = []
    # links_2: list[WikiLink] = []

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
    async def reset_data(self):
        self.article_1 = None
        self.article_2 = None
        self.collisions = []
        self.links_map = {}
        self.query_one("#wiki__loading", LoadingIndicator).display = False
        collisions = self.query_one("#wiki__collisions", ListView)
        collisions.display = False
        await collisions.clear()

        self.query_one("#wiki__title", Label).update(
            "Nenhum artigo buscado para comparar"
        )

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

        wiki = self.query_one(WikiMain)
        await wiki.show_loading(article_1.title, article_2.title)

        engine = WikiCompareEngine(client)
        result: CompareResult | None = None

        try:

            result = await engine.compare(article_1.pageid, article_2.pageid)

        except Exception as error:
            wiki.show_error(error)
            self.notify(f"Erro ao buscar links: {error}", severity="error")
            return

        links_1 = [result.links_map[pid] for pid in result.links[article_1.pageid]]
        links_2 = [result.links_map[pid] for pid in result.links[article_2.pageid]]

        self.notify(
            f"{article_1.title}: {len(result.links[article_1.pageid])} links | "
            f"{article_2.title}: {len(result.links[article_2.pageid])} links"
        )

        self.collisions = result.colisions
        self.links_map = result.links_map

        collisions = [result.links_map[pid] for pid in dict.fromkeys(result.colisions)]

        collisions.sort(key=lambda link: link.title)

        await wiki.show_collisions(article_1.title, article_2.title, collisions)

    @on(ListView.Selected, "#wiki__collisions")
    def list_item_select(self, event: ListView.Selected):
        # o id do item é "link-<pageid>" (ids do Textual não podem começar com número)
        selected_pageid = int(cast(str, event.item.id).removeprefix("link-"))
        link = self.links_map[selected_pageid]

        self.push_screen(
            WikiModal(pageid=link.pageid, title=link.title),
            # self.on_select_search_result,
        )

    def compose(self) -> ComposeResult:
        yield WikiHeader(name="app header")
        with VerticalScroll(classes="wiki-main__content-panel"):
            yield WikiMain(name="wiki main", id="wiki-main")


if __name__ == "__main__":
    print("Hello, world!")

    app = WikiApp()
    app.run()
