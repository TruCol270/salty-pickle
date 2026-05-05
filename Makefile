.PHONY: dev build test lint migrate seed-beta db-reset

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

seed-beta:
	docker-compose run api python -m app.seed

db-reset:
	docker-compose run api alembic downgrade base && docker-compose run api alembic upgrade head

run:
	docker-compose up api
