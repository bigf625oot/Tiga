.PHONY: install run lint test clean benchmark

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

lint:
	ruff check .
	ruff format . --check

format:
	ruff format .

test:
	pytest tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

benchmark:
	python -m scripts.benchmark_workflow
