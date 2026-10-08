"""Shared fixtures: local app server, chat page object, and agent API mock."""

import threading
from collections.abc import Iterator
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Page

from tests.support import ChatPage, MockAgent

APP_DIR = Path(__file__).resolve().parents[1] / "app"


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    """Serves app/ on a free local port for the whole test session."""
    handler = partial(_QuietHandler, directory=str(APP_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join()


@pytest.fixture
def chat_page(page: Page) -> ChatPage:
    return ChatPage(page)


@pytest.fixture
def mock_agent(page: Page) -> MockAgent:
    return MockAgent(page)
