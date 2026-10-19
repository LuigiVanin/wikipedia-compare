from datetime import datetime
from dataclasses import dataclass
import re

from textual.app import App, ComposeResult
from textual.widgets import Digits

from client import WikiClient, WikiItem
from ui import WikiApp
from utils import normalize_text

if __name__ == "__main__":
    WikiApp().run()
