.PHONY: setup run test docker-up docker-down clean

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r backend/requirements.txt
	cp -n .env.example .env || true

run:
	. .venv/bin/activate && cd backend && uvicorn app.main:app --reload --port 8000

test:
	. .venv/bin/activate && cd backend && pytest -q

docker-up:
	cp -n .env.example .env || true
	docker compose up --build

docker-down:
	docker compose down

clean:
	rm -rf .venv backend/.pytest_cache backend/**/__pycache__ storage/migrationmind.db storage/uploads/* storage/outputs/*
