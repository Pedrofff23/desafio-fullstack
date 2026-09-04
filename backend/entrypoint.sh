#!/usr/bin/env bash
set -e

# Aguarda ou executa migrations caso AUTO_MIGRATE=true
if [ "${AUTO_MIGRATE:-true}" = "true" ]; then
  echo "==> [Entrypoint] Verificando e aplicando migrations pendentes (Alembic)..."
  alembic upgrade head
fi

# Executa os seeds automáticos se AUTO_SEED=true
if [ "${AUTO_SEED:-false}" = "true" ]; then
  echo "==> [Entrypoint] AUTO_SEED ativo: verificando seeds da base de dados..."
  
  # 1. Dados geográficos IBGE (paises, estados, cidades) - idempotente
  bash scripts/seed_geo.sh
  
  # 2. Dados de referência (unidades, categorias, admin) - idempotente
  python -m scripts.init_db

  # 3. Dados de demonstração (opcional via AUTO_SEED_DEMO=true)
  if [ "${AUTO_SEED_DEMO:-false}" = "true" ]; then
    echo "==> [Entrypoint] AUTO_SEED_DEMO ativo: carregando dados de exemplo..."
    python -m scripts.seed_demo
  fi

  echo "==> [Entrypoint] Seeds finalizados com sucesso!"
fi

# Executa o comando principal (uvicorn)
exec "$@"
