.PHONY: install test lint format migrate docker-build docker-push

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

test:
	pytest src/tests --cov=src

lint:
	flake8 src
	mypy src

format:
	black src

migrate:
	alembic upgrade head

docker-build:
	docker build -t vecapp/analytics:latest .

docker-push:
	docker push vecapp/analytics:latest

run-dev:
	uvicorn src.main:app --reload

setup-db:
	python scripts/setup_db.py 