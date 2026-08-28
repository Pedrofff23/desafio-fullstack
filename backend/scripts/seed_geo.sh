#!/bin/bash
# ============================================================
# Seed dos dados geográficos IBGE (paises, estados, cidades).
# Extrai apenas a seção de dados (COPY ... FROM stdin) de cada dump
# e a carrega via psql. As tabelas já foram criadas pela migration.
# ============================================================
set -u

: "${DATABASE_URL:=postgresql+asyncpg://estoque:estoque123@db:5432/gerenciamento_estoque}"

PSQL_URL="${DATABASE_URL/postgresql+asyncpg:/postgresql:}"
DB_HOST="$(echo "$PSQL_URL" | sed -E 's|.*@([^:/]+).*|\1|')"
DB_PORT="$(echo "$PSQL_URL" | sed -E 's|.*:([0-9]+)/.*|\1|')"
DB_USER="$(echo "$PSQL_URL" | sed -E 's|.*//([^:]+):.*|\1|')"
DB_PASS="$(echo "$PSQL_URL" | sed -E 's|.*:([^@]+)@.*|\1|')"
DB_NAME="$(echo "$PSQL_URL" | sed -E 's|.*/([^/]+)$|\1|')"

export PGPASSWORD="$DB_PASS"
SQL_DIR="${SQL_REF_DIR:-/app/sql_reference}"

echo "=== Seed geográfico IBGE ==="
echo "Host: $DB_HOST:$DB_PORT  DB: $DB_NAME  User: $DB_USER"

for fname in pais.sql estado.sql cidade.sql; do
  FILE="$SQL_DIR/$fname"
  if [ ! -f "$FILE" ]; then
    echo "Arquivo $fname não encontrado; pulando."
    continue
  fi
  echo "Carregando dados de $fname..."

  # Extrai blocos "COPY <tabela> (...) FROM stdin;" ... "\."
  # e os executa via psql. Ajusta o search_path para public.
  awk '
    BEGIN { incopy = 0 }
    /^COPY / { incopy = 1; print "SET search_path TO public;" }
    incopy { print }
    /^\\\.$/ { incopy = 0 }
  ' "$FILE" | \
    psql -v ON_ERROR_STOP=0 -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" 2>&1 | \
    grep -E "ERROR|COPY [0-9]+" | grep -v "already exists" || true
done

echo "=== Seed geográfico concluído ==="