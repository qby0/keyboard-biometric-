.PHONY: install dev test lint format docker-build docker-run

install:
	python3 -m pip install -e .

dev:
	python3 -m pip install -r requirements-dev.txt

test:
	pytest -q

lint:
	ruff check src || true

format:
	ruff format src

docker-build:
	docker build -t persona-by-text .

docker-run:
	docker run --rm -it -p 8000:8000 -v $(PWD):/app persona-by-text bash
