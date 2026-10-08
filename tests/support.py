"""Page object for the chat UI and a mock for the agent API."""

from playwright.sync_api import Locator, Page, Route, expect

from agentic_qa.dataset import ToolCall


class ChatPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.input: Locator = page.get_by_test_id("chat-input")
        self.send_button: Locator = page.get_by_test_id("send-button")
        self.responses: Locator = page.get_by_test_id("chatbot-response")

    def goto(self) -> None:
        self.page.goto("/")
        expect(self.input).to_be_visible()

    def send(self, prompt: str) -> None:
        self.input.fill(prompt)
        self.send_button.click()

    def last_response_text(self, timeout: float = 15_000) -> str:
        """Waits for the latest response bubble and returns its text."""
        bubble = self.responses.last
        expect(bubble).to_be_visible(timeout=timeout)
        return bubble.inner_text()


class MockAgent:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.tool_calls: list[ToolCall] = []

    def respond_with(self, reply: str, tool_calls: list[ToolCall]) -> None:
        """Intercepts the agent API and fulfills it with the given reply/tool calls."""
        self.tool_calls = tool_calls
        body = {
            "reply": reply,
            "toolCalls": [tc.model_dump(by_alias=True, exclude_none=True) for tc in tool_calls],
        }

        def handle(route: Route) -> None:
            route.fulfill(status=200, json=body)

        self.page.route("**/api/agent/run*", handle)
