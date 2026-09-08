#!/usr/bin/env bash
set -e

# Garante que scripts shell não tenham caracteres CRLF do Windows
sed -i 's/\r$//' scripts/seed_geo.sh 2>/dev/null || true

# Extrai os parâmetros de conexão ou usa padrões
DB_HOST="$(echo "${DATABASE_URL:-}" | sed -E 's|.*@([^:/]+).*|\1|')"
DB_HOST="${DB_HOST:-db}"
DB_PORT="$(echo "${DATABASE_URL:-}" | sed -E 's|.*:([0-9]+)/.*|\1|')"
DB_PORT="${DB_PORT:-5432}"
DB_USER="$(echo "${DATABASE_URL:-}" | sed -E 's|.*//([^:]+):.*|\1|')"
DB_USER="${DB_USER:-estoque}"

# Aguarda o banco de dados estar pronto para aceitar conexões
echo "==> [Entrypoint] Aguardando disponibilidade do PostgreSQL ($DB_HOST:$DB_PORT)..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
  sleep 1
done
echo "==> [Entrypoint] PostgreSQL disponível e aceitando conexões."

# 1. Executa migrations caso AUTO_MIGRATE=true (padrão: true)
if [ "${AUTO_MIGRATE:-true}" = "true" ]; then
  echo "==> [Entrypoint] Aplicando migrations pendentes (Alembic)..."
  alembic upgrade head
fi

# 2. Executa os seeds automáticos se AUTO_SEED=true (padrão: true)
if [ "${AUTO_SEED:-true}" = "true" ]; then
  echo "==> [Entrypoint] AUTO_SEED ativo: iniciando carga dos dados..."
  
  # 2.1. Dados geográficos IBGE (paises, estados, cidades) - idempotente
  echo "==> [Entrypoint] [1/2] Carregando dados geográficos IBGE..."
  bash scripts/seed_geo.sh
  
  # 2.2. Dados de referência (unidades, categorias, alergenos, ingredientes, localizações, admin) - idempotente
  echo "==> [Entrypoint] [2/2] Carregando dados de referência e usuário administrador..."
  python -m scripts.init_db

  # 2.3. Dados de demonstração opcionais via AUTO_SEED_DEMO=true (produtos, lotes, fornecedores, saídas)
  if [ "${AUTO_SEED_DEMO:-false}" = "true" ]; then
    echo "==> [Entrypoint] [Opcional] AUTO_SEED_DEMO ativo: carregando dados de exemplo..."
    python -m scripts.seed_demo
  fi

  echo "==> [Entrypoint] Seeds finalizados com sucesso!"
fi

# Se nenhum comando foi passado ao container, usa o padrão uvicorn
if [ $# -eq 0 ]; then
  set -- uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi

echo "==> [Entrypoint] Iniciando comando principal: $*"
exec "$@"
