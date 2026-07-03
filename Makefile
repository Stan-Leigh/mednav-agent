.PHONY: install playground custom-playground run test

install:
	uv sync

playground:
	uv run adk web app --host 127.0.0.1 --port 18081 --reload_agents

custom-playground:
	uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000 --reload



run:
	uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000 --reload

test:
	uv run pytest
