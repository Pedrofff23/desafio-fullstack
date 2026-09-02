"""corrigir lock concorrente das saídas

Revision ID: b621d8430f9e
Revises: 7f19c2d842a1
"""

from collections.abc import Sequence

from alembic import op

revision: str = "b621d8430f9e"
down_revision: str | None = "7f19c2d842a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION validar_saldo_saida()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        DECLARE saldo_atual numeric(14, 3);
        BEGIN
            -- O lock precisa ocorrer antes do cálculo. Depois de uma espera,
            -- a consulta seguinte enxerga a saída confirmada pela concorrente.
            PERFORM 1
              FROM registros_entrada
             WHERE id = NEW.entrada_id
             FOR UPDATE;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Entrada % inexistente', NEW.entrada_id;
            END IF;

            SELECT re.quantidade - COALESCE(SUM(rs.quantidade), 0)
              INTO saldo_atual
              FROM registros_entrada re
              LEFT JOIN registros_saida rs
                ON rs.entrada_id = re.id
               AND (TG_OP <> 'UPDATE' OR rs.id <> OLD.id)
             WHERE re.id = NEW.entrada_id
             GROUP BY re.quantidade;

            IF COALESCE(saldo_atual, 0) < NEW.quantidade THEN
                RAISE EXCEPTION 'Saldo insuficiente para a entrada %', NEW.entrada_id;
            END IF;
            RETURN NEW;
        END;
        $$
    """)


def downgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION validar_saldo_saida()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        DECLARE saldo_atual numeric(14, 3);
        BEGIN
            SELECT re.quantidade - COALESCE((
                SELECT SUM(rs.quantidade)
                  FROM registros_saida rs
                 WHERE rs.entrada_id = NEW.entrada_id
                   AND (TG_OP <> 'UPDATE' OR rs.id <> OLD.id)
            ), 0)
              INTO saldo_atual
              FROM registros_entrada re
             WHERE re.id = NEW.entrada_id
             FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Entrada % inexistente', NEW.entrada_id;
            END IF;
            IF COALESCE(saldo_atual, 0) < NEW.quantidade THEN
                RAISE EXCEPTION 'Saldo insuficiente para a entrada %', NEW.entrada_id;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
