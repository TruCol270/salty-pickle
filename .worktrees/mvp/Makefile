.PHONY: dev build test lint migrate db-reset

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
	docker-compose run api alembic downgrade base && alembic upgrade head

run:
	docker-compose up api
