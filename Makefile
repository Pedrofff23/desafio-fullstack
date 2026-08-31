.PHONY: help up down restart logs ps db-shell db-check db-seed db-seed-geo db-seed-all backend-shell backend-test uv-sync uv-run

# Default target: show help
help:
	@echo "=============================================================================="
	@echo "Commands available for Desafio Fullstack"
	@echo "=============================================================================="
	@echo "Docker Lifecycle:"
	@echo "  make up             - Start containers (db and backend) in background"
	@echo "  make build          - Build and start containers"
	@echo "  make down           - Stop all containers"
	@echo "  make restart        - Restart containers"
	@echo "  make logs           - View logs from all services"
	@echo "  make ps             - View status of running containers"
	@echo ""
	@echo "Database & Migrations:"
	@echo "  make db-shell       - Open interactive psql shell in the database"
	@echo "  make db-check       - Check migration status and table row counts"
	@echo "  make db-seed        - Seed reference data (units, categories, admin user)"
	@echo "  make db-seed-geo    - Seed IBGE geo data (countries, states, cities)"
	@echo "  make db-seed-all    - Run all seeds (seed_geo + init_db)"
	@echo ""
	@echo "Backend (Docker / Local):"
	@echo "  make backend-shell  - Open bash shell inside backend container"
	@echo "  make backend-test   - Run pytest inside backend container"
	@echo "  make uv-sync        - Run uv sync locally in backend directory"
	@echo "  make uv-run         - Run FastAPI locally with uv and hot reload"
	@echo "=============================================================================="

# --- Docker Lifecycle ---
up:
	docker compose up -d db backend

build:
	docker compose up --build -d db backend

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

ps:
	docker compose ps

# --- Database & Seeds ---
db-shell:
	docker compose exec -it db psql -U estoque -d gerenciamento_estoque

db-check:
	@docker compose exec db psql -U estoque -d gerenciamento_estoque -c "\
	SELECT version_num AS migration_version FROM alembic_version;\
	SELECT 'usuarios' AS table_name, count(*) AS total_rows FROM usuarios\
	UNION ALL SELECT 'categorias', count(*) FROM categorias\
	UNION ALL SELECT 'unidades_medida', count(*) FROM unidades_medida\
	UNION ALL SELECT 'produtos', count(*) FROM produtos\
	UNION ALL SELECT 'paises', count(*) FROM paises\
	UNION ALL SELECT 'estados', count(*) FROM estados\
	UNION ALL SELECT 'cidades', count(*) FROM cidades;"

db-seed:
	docker compose exec backend python -m scripts.init_db

db-seed-geo:
	docker compose exec backend bash scripts/seed_geo.sh

db-seed-all: db-seed-geo db-seed

# --- Backend Operations ---
backend-shell:
	docker compose exec -it backend bash

backend-test:
	docker compose exec backend pytest

uv-sync:
	cd backend && uv sync

uv-run:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
