.PHONY: help install generate-data test test-unit test-integration run-backend run-frontend run-pipelines clean docker-up docker-down

help:
	@echo "Enterprise Real-Time Data Intelligence Platform"
	@echo "Available commands:"
	@echo "  make install         - Install python dependencies"
	@echo "  make generate-data   - Run synthetic data generator (historical transactions)"
	@echo "  make run-pipelines   - Execute Medallion ETL pipeline (Bronze -> Silver -> Gold)"
	@echo "  make run-backend     - Start FastAPI backend server"
	@echo "  make run-frontend    - Start React Vite frontend"
	@echo "  make test            - Run all pytest test suites"
	@echo "  make docker-up       - Start all Docker Compose services"
	@echo "  make docker-down     - Stop Docker Compose services"

install:
	pip install -r requirements.txt

generate-data:
	python scripts/generate_data.py --records 100000

run-pipelines:
	python scripts/run_all_pipelines.py

run-backend:
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	rm -rf data/bronze/* data/silver/* data/gold/* data/quarantine/* __pycache__ .pytest_cache
