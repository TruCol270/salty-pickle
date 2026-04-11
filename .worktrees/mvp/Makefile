.PHONY: dev build test lint migrate db-reset run audit-backend audit-frontend audit

dev:
	docker-compose up

build:
	docker-compose build

test:
	docker-compose run api pytest -v

lint:
	docker-compose run api ruff check .

migrate:
	docker-compose run api alembic upgrade head

db-reset:
	docker-compose run api alembic downgrade base && docker-compose run api alembic upgrade head

run:
	docker-compose up api

audit-backend:
	docker-compose run api pip install bandit && docker-compose run api bandit -r app/ -ll

audit-frontend:
	cd frontend && npm audit

audit: audit-backend audit-frontend
