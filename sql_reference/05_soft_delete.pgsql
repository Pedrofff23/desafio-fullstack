-- =============================================================================
-- Exclusão lógica (soft delete)
-- Execute este arquivo após 01_schema.pgsql no DBeaver.
-- Tabelas protegidas: funcionarios, usuarios, fornecedores, produtos e lotes.
-- Movimentações não são excluíveis para preservar a auditoria.
-- =============================================================================

-- As alterações abaixo permitem executar o arquivo também em uma base já criada.
ALTER TABLE funcionarios ADD COLUMN IF NOT EXISTS excluido_em TIMESTAMPTZ;
ALTER TABLE funcionarios ADD COLUMN IF NOT EXISTS excluido_por BIGINT;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS excluido_em TIMESTAMPTZ;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS excluido_por BIGINT;
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS excluido_em TIMESTAMPTZ;
ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS excluido_por BIGINT;
ALTER TABLE produtos ADD COLUMN IF NOT EXISTS excluido_em TIMESTAMPTZ;
ALTER TABLE produtos ADD COLUMN IF NOT EXISTS excluido_por BIGINT;
ALTER TABLE lotes ADD COLUMN IF NOT EXISTS excluido_em TIMESTAMPTZ;
ALTER TABLE lotes ADD COLUMN IF NOT EXISTS excluido_por BIGINT;

ALTER TABLE funcionarios DROP CONSTRAINT IF EXISTS fk_funcionario_excluido_por;
ALTER TABLE funcionarios ADD CONSTRAINT fk_funcionario_excluido_por
    FOREIGN KEY (excluido_por) REFERENCES usuarios(id);
ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS fk_usuario_excluido_por;
ALTER TABLE usuarios ADD CONSTRAINT fk_usuario_excluido_por
    FOREIGN KEY (excluido_por) REFERENCES usuarios(id);
ALTER TABLE fornecedores DROP CONSTRAINT IF EXISTS fk_fornecedor_excluido_por;
ALTER TABLE fornecedores ADD CONSTRAINT fk_fornecedor_excluido_por
    FOREIGN KEY (excluido_por) REFERENCES usuarios(id);
ALTER TABLE produtos DROP CONSTRAINT IF EXISTS fk_produto_excluido_por;
ALTER TABLE produtos ADD CONSTRAINT fk_produto_excluido_por
    FOREIGN KEY (excluido_por) REFERENCES usuarios(id);
ALTER TABLE lotes DROP CONSTRAINT IF EXISTS fk_lote_excluido_por;
ALTER TABLE lotes ADD CONSTRAINT fk_lote_excluido_por
    FOREIGN KEY (excluido_por) REFERENCES usuarios(id);

CREATE OR REPLACE FUNCTION soft_delete_ativo()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Informe o usuário responsável antes do DELETE, se aplicável:
    -- SET LOCAL app.usuario_id = '1';
    EXECUTE format(
        'UPDATE ONLY %s
            SET ativo = FALSE,
                excluido_em = CURRENT_TIMESTAMP,
                excluido_por = NULLIF(current_setting(''app.usuario_id'', true), '''')::BIGINT
          WHERE ctid = $1',
        TG_RELID::regclass
    ) USING OLD.ctid;

    -- Cancela a exclusão física.
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_soft_delete_funcionario ON funcionarios;
CREATE TRIGGER trg_soft_delete_funcionario
BEFORE DELETE ON funcionarios
FOR EACH ROW EXECUTE FUNCTION soft_delete_ativo();

DROP TRIGGER IF EXISTS trg_soft_delete_usuario ON usuarios;
CREATE TRIGGER trg_soft_delete_usuario
BEFORE DELETE ON usuarios
FOR EACH ROW EXECUTE FUNCTION soft_delete_ativo();

DROP TRIGGER IF EXISTS trg_soft_delete_fornecedor ON fornecedores;
CREATE TRIGGER trg_soft_delete_fornecedor
BEFORE DELETE ON fornecedores
FOR EACH ROW EXECUTE FUNCTION soft_delete_ativo();

DROP TRIGGER IF EXISTS trg_soft_delete_produto ON produtos;
CREATE TRIGGER trg_soft_delete_produto
BEFORE DELETE ON produtos
FOR EACH ROW EXECUTE FUNCTION soft_delete_ativo();

DROP TRIGGER IF EXISTS trg_soft_delete_lote ON lotes;
CREATE TRIGGER trg_soft_delete_lote
BEFORE DELETE ON lotes
FOR EACH ROW EXECUTE FUNCTION soft_delete_ativo();

-- Exemplo:
-- BEGIN;
-- SET LOCAL app.usuario_id = '1';
-- DELETE FROM produtos WHERE produto_id = 1;
-- COMMIT;
--
-- SELECT produto_id, nome, ativo, excluido_em, excluido_por
-- FROM produtos;
