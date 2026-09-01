#!/usr/bin/env bash
# ============================================================
# Seed dos dados geográficos IBGE (paises, estados, cidades).
# Extrai apenas a seção de dados (COPY ... FROM stdin) de cada dump
# e a carrega via psql. As tabelas já foram criadas pela migration.
# ============================================================
set -euo pipefail

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

for item in "pais.sql:paises" "estado.sql:estados" "cidade.sql:cidades"; do
  fname="${item%%:*}"
  table="${item##*:}"
  FILE="$SQL_DIR/$fname"
  if [ ! -f "$FILE" ]; then
    echo "Arquivo $fname não encontrado; pulando."
    continue
  fi

  has_data="$(psql -tAc "SELECT EXISTS (SELECT 1 FROM $table LIMIT 1)" \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" | tr -d '[:space:]')"
  if [ "$has_data" = "t" ]; then
    echo "Tabela $table já possui dados; pulando carga."
    continue
  fi

  echo "Carregando dados de $fname..."

  tmp_sql="$(mktemp)"
  trap 'rm -f "$tmp_sql"' EXIT

  # Remove CRLF antes de detectar o terminador "\." do bloco COPY.
  awk '
    BEGIN { incopy = 0 }
    { sub(/\r$/, "", $0) }
    /^COPY / { incopy = 1; print "SET search_path TO public;" }
    incopy { print }
    /^\\\.$/ { incopy = 0 }
  ' "$FILE" > "$tmp_sql"

  psql -v ON_ERROR_STOP=1 -h "$DB_HOST" -p "$DB_PORT" \
    -U "$DB_USER" -d "$DB_NAME" -f "$tmp_sql"
  rm -f "$tmp_sql"
  trap - EXIT
done

# COPY informa IDs explicitamente e não avança as sequences SERIAL/BIGSERIAL.
for table in paises estados cidades; do
  psql -v ON_ERROR_STOP=1 -h "$DB_HOST" -p "$DB_PORT" \
    -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT setval(pg_get_serial_sequence('$table', 'id'), COALESCE(MAX(id), 1), true) FROM $table;" \
    >/dev/null
done

echo "=== Seed geográfico concluído ==="
