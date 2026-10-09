# Agentic HCM Chatbot Evaluation Framework (Python)

[![AI Agent Evaluation Suite](https://github.com/SAIREDDY-PERSONAL/agentic-qa-mini-project-python/actions/workflows/eval-ci.yml/badge.svg)](https://github.com/SAIREDDY-PERSONAL/agentic-qa-mini-project-python/actions/workflows/eval-ci.yml)

An evaluation framework for an agentic HR chatbot, written in Python. Playwright drives the chat UI and checks which tools the agent called. An LLM judge then scores each reply for groundedness and helpfulness. A TypeScript version of the same framework is at [agentic-qa-mini-project](https://github.com/SAIREDDY-PERSONAL/agentic-qa-mini-project).

Agent replies are non-deterministic, so exact-match assertions don't work well. Each test therefore checks two things:

1. **Behaviour:** did the agent use the expected tool (e.g. `submit_time_off`) with the right arguments?
2. **Quality:** does an LLM judge rate the reply as grounded in the context and tool results, with a score above a set threshold?

## How it works

```
data/eval_dataset.json ──► test_chatbot.py (one parametrized test per case)
                               │
                               ├─ mock_agent ── intercepts /api/agent/run, returns the case's reply + tool calls
                               ├─ chat_page  ── types the prompt into the chat UI, reads the response bubble
                               ├─ assert     ── expected tool was called
                               └─ LLM judge  ── scores the reply (0–10, grounded, helpful, reasoning)
                                                 └─ assert score ≥ min_score, grounded if required
```

- **Chat UI** (`app/index.html`): a minimal chat page that posts to `/api/agent/run` and renders the reply. A session fixture serves it on a free local port.
- **Fixtures** (`tests/conftest.py`, `tests/support.py`): `chat_page` is a page object for the chat UI. `mock_agent` mocks the agent API and records the tool calls it returned. Both build on `pytest-playwright`'s `page` fixture.
- **LLM judge** (`src/agentic_qa/judge.py`): built with LangChain. It returns a verdict validated against a Pydantic model: `score`, `is_grounded`, `is_helpful` and `reasoning`. The provider is picked from your environment: Anthropic Claude if `ANTHROPIC_API_KEY` is set, otherwise OpenAI if `OPENAI_API_KEY` is set, otherwise a local Ollama model.
- **Dataset** (`data/eval_dataset.json`, loaded by `src/agentic_qa/dataset.py`): each case defines the prompt, context, mocked tool calls and their results, the expected tool, a minimum score, and whether the reply must be grounded. Cases are validated with Pydantic when they load.

## Test cases

| ID | Scenario | Prompt | Expected tool | Min score |
|---|---|---|---|---|
| TC_001 | Happy path | "Schedule 3 days off for next week starting Monday." | `submit_time_off` | 7 |
| TC_002 | Insufficient balance | "Request 20 days off for a vacation next month." | `check_leave_balance` | 5 |
| TC_003 | Out of scope | "How do I make a chocolate cake?" | none (should decline) | 5 |

To add a case, add an entry to `eval_dataset.json`. The suite generates one test per entry.

## Running it

Requires Python 3.12+.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
cp .env.example .env    # then add your API key (see below)

pytest                  # run the suite
pytest --html=reports/report.html --self-contained-html   # with an HTML report
ruff check . && mypy    # lint and strict type-check
```

### Configuration

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Use Claude as the judge (preferred) |
| `ANTHROPIC_MODEL` | Judge model, default `claude-haiku-5-5` |
| `ANTHROPIC_WORKSPACE_ID` | Optional Anthropic workspace header |
| `OPENAI_API_KEY` | Use OpenAI `gpt-4o-mini` if no Anthropic key is set |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Local fallback, default `http://localhost:11434` and `llama3.2` |
| `JUDGE_TIMEOUT` | Seconds before a judge request is abandoned, default `120` |

Each test also has a hard 300-second limit (`pytest-timeout`), so a stuck judge call fails the test instead of hanging the suite.

## CI

GitHub Actions (`.github/workflows/eval-ci.yml`) runs on every push and pull request to `main`. It lints with ruff, type-checks with `mypy --strict`, runs the full evaluation suite, and uploads the HTML report as an artifact. A `Jenkinsfile` is also included for running the suite in Jenkins.

## Project structure

```
app/index.html                chat UI under test
data/eval_dataset.json        evaluation cases
src/agentic_qa/dataset.py     case and tool-call models, dataset loader
src/agentic_qa/judge.py       LLM-as-judge evaluator
tests/conftest.py             fixtures: local app server, chat_page, mock_agent
tests/support.py              ChatPage page object and MockAgent
tests/e2e/test_chatbot.py     data-driven evaluation suite
pyproject.toml                dependencies and pytest/ruff/mypy config
.github/workflows/eval-ci.yml CI pipeline
```

## Limitations

- The agent backend is mocked. Replies and tool calls come from the dataset, so the suite tests the evaluation pipeline and UI, not a live model's decisions.
- Each case runs once. Rerunning the same prompt several times to measure consistency is a natural next step.
