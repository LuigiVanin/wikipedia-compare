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
from textual.widgets import Button, Header, Input, Label, Markdown, Placeholder

MARKDOWN_TEMPLATE = """
# Pyhon

template de markdown, server apenas para ser renderizado.
"""


class Wiki(HorizontalGroup):
    def compose(self) -> ComposeResult:

        yield Markdown(MARKDOWN_TEMPLATE, classes="wiki-content")


class SearchModal(ModalScreen[str | None]):
    search_term: str

    BINDINGS = [
        Binding(
            key="escape", action="dismiss", description="Dismiss Modal", priority=True
        )
    ]

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        query: str = "",
    ) -> None:
        super().__init__(name, id, classes)
        self.search_term = query

    def compose(self):
        with Vertical(id="search-modal"):
            yield Label(f"Resultado para {self.query}")
            Markdown(MARKDOWN_TEMPLATE)


class WikiHeader(VerticalGroup):

    def compose(self) -> ComposeResult:
        yield Label("Wiki App", id="title")

        with HorizontalGroup(id="search-box"):
            yield Label("🔎", id="search-box__prefix")
            yield Input(
                placeholder="Insira um artigo para pesquisar...",
                id="search-box__input",
            )


class WikiMain(Horizontal):
    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="wiki-main__content-panel"):
            yield Wiki()

        with VerticalScroll(classes="wiki-main__links-panel"):
            yield Wiki()


class WikiApp(App):
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit App", priority=True),
        Binding(
            key="ctrl+k", action="focus_search", description="Pesquisar", priority=True
        ),
    ]

    CSS_PATH = "./styles/index.tcss"

    def action_focus_search(self) -> None:
        self.query_one("#search-box__input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id != "search-box__input" or not event.value.strip():
            return
        self.push_screen(SearchModal(event.value), self.on_search_result)

    def on_search_result(self, result: str | None) -> None:
        if result:
            self.notify("Artigo selecionado")

    def compose(self) -> ComposeResult:
        yield WikiHeader(name="app header")
        yield WikiMain(name="wiki main", id="wiki-main")


if __name__ == "__main__":
    print("Hello, world!")

    app = WikiApp()
    app.run()
