
------------------------------- Domains -------------------------------
ALTER TABLE estados
    ADD CONSTRAINT fk_estados_paises FOREIGN KEY (pais) REFERENCES paises(id);

ALTER TABLE cidades
    ADD CONSTRAINT fk_cidades_estados FOREIGN KEY (uf) REFERENCES estados(id);

-- Usado em produtos e lotes 
CREATE DOMAIN dom_codigo AS VARCHAR(50) CHECK (VALUE = btrim(VALUE)
    AND VALUE <> '');

-- Usado em produtos, funcionarios e fornecedores
CREATE DOMAIN dom_nome AS VARCHAR(150) CHECK (VALUE = btrim(VALUE)
    AND VALUE <> '');

CREATE DOMAIN dom_email AS VARCHAR(254) CHECK (VALUE = lower(btrim(VALUE))
    AND VALUE ~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$');

CREATE DOMAIN dom_hash_senha AS VARCHAR(255) CHECK (length(VALUE) >= 20);

CREATE DOMAIN dom_cep AS CHAR(8) CHECK (VALUE ~ '^[0-9]{8}$');

-- Internacional 
CREATE DOMAIN dom_ddi AS VARCHAR(4) CHECK (VALUE ~ '^\+[1-9][0-9]{0,2}$');

CREATE DOMAIN dom_ddd AS CHAR(2) CHECK (VALUE ~ '^[0-9]{2}$');

CREATE DOMAIN dom_telefone AS VARCHAR(15) CHECK (VALUE ~ '^[0-9]{8,15}$');

-- Permite até 14 dígitos no total, sendo que 3 são obrigatoriamente decimais
CREATE DOMAIN dom_quantidade AS NUMERIC(14, 3) CHECK (VALUE > 0);

CREATE DOMAIN dom_valor_monetario AS NUMERIC(12, 2) CHECK (VALUE >= 0);

------------------------------- Tabelas -------------------------------

-- GENERATED ALWAYS AS IDENTITY PRIMARY KEY
-- Essa coluna deve ter seus valores gerados automaticamente pelo banco
CREATE TABLE unidades_medida(
    id smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sigla varchar(10) NOT NULL UNIQUE CHECK (sigla = lower(btrim(sigla))),
    descricao varchar(50) NOT NULL UNIQUE
);

CREATE TABLE categorias(
    id smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome varchar(50) NOT NULL UNIQUE,
    descricao varchar(200)
);

CREATE TABLE alergenos(
    id smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome varchar(50) NOT NULL UNIQUE,
    descricao varchar(200)
);

CREATE TABLE ingredientes(
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome varchar(100) NOT NULL UNIQUE,
    descricao varchar(200)
);

-- Não remover paises/estados: enderecos -> cidades -> estados -> paises.
CREATE TABLE enderecos(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    logradouro varchar(150) NOT NULL,
    numero varchar(20) NOT NULL,
    complemento varchar(100),
    cep dom_cep NOT NULL,
    bairro varchar(100) NOT NULL,
    cidade_id integer NOT NULL REFERENCES cidades(id),
    UNIQUE (logradouro, numero, complemento, cep, bairro, cidade_id)
);

CREATE TABLE contatos(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo_pais dom_ddi NOT NULL DEFAULT '+55',
    ddd dom_ddd NOT NULL,
    numero dom_telefone NOT NULL,
    UNIQUE (codigo_pais, ddd, numero)
);

CREATE TABLE funcionarios(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome_completo dom_nome NOT NULL,
    endereco_id bigint NOT NULL REFERENCES enderecos,
    contato_id bigint NOT NULL REFERENCES contatos,
    data_cadastro timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ativo boolean NOT NULL DEFAULT TRUE,
    excluido_em timestamptz,
    excluido_por bigint
);

-- Credenciais ficam somente em usuarios: não duplicar email/senha em funcionarios.
-- 
CREATE TABLE usuarios(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    funcionario_id bigint NOT NULL UNIQUE REFERENCES funcionarios,
    email dom_email NOT NULL UNIQUE,
    senha_hash dom_hash_senha NOT NULL,
    perfil varchar(20) NOT NULL CHECK (perfil IN ('admin', 'funcionario')),
    ativo boolean NOT NULL DEFAULT TRUE,
    data_cadastro timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    excluido_em timestamptz,
    excluido_por bigint CONSTRAINT fk_usuario_excluido_por REFERENCES usuarios(id)
);

ALTER TABLE funcionarios ADD CONSTRAINT fk_funcionario_excluido_por
    FOREIGN KEY (excluido_por) REFERENCES usuarios(id);

CREATE TABLE fornecedores(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome_empresa dom_nome NOT NULL UNIQUE,
    contato_id bigint NOT NULL REFERENCES contatos,
    endereco_id bigint NOT NULL REFERENCES enderecos,
    data_cadastro timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ativo boolean NOT NULL DEFAULT TRUE,
    excluido_em timestamptz,
    excluido_por bigint CONSTRAINT fk_fornecedor_excluido_por REFERENCES usuarios(id)
);

CREATE TABLE corredores(
    id smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome varchar(50) NOT NULL UNIQUE,
    descricao varchar(100)
);

CREATE TABLE seccoes(
    id smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    corredor_id smallint NOT NULL REFERENCES corredores,
    nome varchar(50) NOT NULL,
    descricao varchar(100),
    UNIQUE (corredor_id, nome)
);

CREATE TABLE prateleiras(
    id smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seccao_id smallint NOT NULL REFERENCES seccoes,
    nome varchar(50) NOT NULL,
    nivel smallint CHECK (nivel IS NULL OR nivel > 0),
    descricao varchar(100),
    UNIQUE (seccao_id, nome)
);

-- Prateleira determina seção e corredores; não repetir essas chaves.
CREATE TABLE localizacoes_estoque(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    prateleira_id smallint NOT NULL UNIQUE REFERENCES prateleiras
);

-- Cadastro mestre: atributos de lotes e compra não pertencem ao produtos genérico.
CREATE TABLE produtos(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo dom_codigo NOT NULL UNIQUE,
    nome dom_nome NOT NULL,
    descricao text,
    unidade_medida_id smallint NOT NULL REFERENCES unidades_medida,
    categoria_id smallint NOT NULL REFERENCES categorias,
    localizacao_id bigint NOT NULL REFERENCES localizacoes_estoque,
    data_cadastro timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    funcionario_id bigint NOT NULL REFERENCES funcionarios,
    ativo boolean NOT NULL DEFAULT TRUE,
    excluido_em timestamptz,
    excluido_por bigint CONSTRAINT fk_produto_excluido_por REFERENCES usuarios(id)
);

-- Informação nutricional simplificada: uma linha já contém o nutriente do produto.
CREATE TABLE nutrientes(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    produto_id bigint NOT NULL REFERENCES produtos ON DELETE CASCADE,
    nome varchar(50) NOT NULL,
    unidade varchar(10) NOT NULL,
    valor numeric(10, 3) NOT NULL CHECK (valor >= 0),
    UNIQUE (produto_id, nome)
);

CREATE TABLE produtos_ingredientes(
    produto_id bigint NOT NULL REFERENCES produtos ON DELETE CASCADE,
    ingrediente_id integer NOT NULL REFERENCES ingredientes,
    ordem smallint NOT NULL CHECK (ordem > 0),
    PRIMARY KEY (produto_id, ingrediente_id),
    UNIQUE (produto_id, ordem)
);

CREATE TABLE produtos_alergenos(
    produto_id bigint NOT NULL REFERENCES produtos ON DELETE CASCADE,
    alergeno_id smallint NOT NULL REFERENCES alergenos,
    PRIMARY KEY (produto_id, alergeno_id)
);

-- Validade é propriedade do lotes, não do produtos genérico.
CREATE TABLE lotes(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    produto_id bigint NOT NULL REFERENCES produtos,
    numero_lote dom_codigo NOT NULL,
    data_producao date NOT NULL,
    data_validade date NOT NULL CHECK (data_validade >= data_producao),
    ativo boolean NOT NULL DEFAULT TRUE,
    excluido_em timestamptz,
    excluido_por bigint CONSTRAINT fk_lote_excluido_por REFERENCES usuarios(id),
    UNIQUE (produto_id, numero_lote)
);

-- A entrada preserva fornecedores e custos históricos; o produtos é obtido pelo lotes.
CREATE TABLE registros_entrada(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lote_id bigint NOT NULL REFERENCES lotes,
    fornecedor_id bigint NOT NULL REFERENCES fornecedores,
    localizacao_id bigint NOT NULL REFERENCES localizacoes_estoque,
    quantidade dom_quantidade NOT NULL,
    data_entrada timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    preco_custo dom_valor_monetario NOT NULL,
    preco_sugerido dom_valor_monetario NOT NULL,
    funcionario_id bigint NOT NULL REFERENCES funcionarios
);

-- Quando omitida, usa a localização preferencial cadastrada no produtos.
CREATE OR REPLACE FUNCTION preencher_localizacao_entrada()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.localizacao_id IS NULL THEN
        SELECT p.localizacao_id
          INTO NEW.localizacao_id
          FROM lotes l
          JOIN produtos p ON p.id = l.produto_id
         WHERE l.id = NEW.lote_id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_preencher_localizacao_entrada
    BEFORE INSERT OR UPDATE OF lote_id ON registros_entrada
    FOR EACH ROW
    EXECUTE FUNCTION preencher_localizacao_entrada();

CREATE TABLE registros_saida(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entrada_id bigint NOT NULL REFERENCES registros_entrada,
    quantidade dom_quantidade NOT NULL,
    data_saida timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    preco_venda dom_valor_monetario NOT NULL,
    funcionario_id bigint NOT NULL REFERENCES funcionarios
);

CREATE TABLE sessoes(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id bigint NOT NULL REFERENCES usuarios,
    token varchar(255) NOT NULL UNIQUE,
    data_criacao timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_expiracao timestamptz NOT NULL CHECK (data_expiracao > data_criacao),
    ativa boolean NOT NULL DEFAULT TRUE
);

------------------------------- View -------------------------------

-- Saldo por entrada: preserva fornecedores, custo e localização de origem.
CREATE VIEW estoque_entrada AS
SELECT
    e.id AS entrada_id,
    e.lote_id,
    l.produto_id,
    e.fornecedor_id,
    e.localizacao_id,
    e.quantidade - COALESCE(s.quantidade_saida, 0) AS quantidade
FROM registros_entrada e
    JOIN lotes l ON l.id = e.lote_id
    LEFT JOIN (
        SELECT
            entrada_id,
            SUM(quantidade) AS quantidade_saida
        FROM registros_saida
        GROUP BY entrada_id
    ) s ON s.entrada_id = e.id;

CREATE VIEW estoque_produto AS
SELECT lote_id, produto_id, SUM(quantidade) AS quantidade
FROM estoque_entrada
GROUP BY lote_id, produto_id;

------------------------------- Funcao & triggers -------------------------------

CREATE OR REPLACE FUNCTION validar_saldo_saida()
    RETURNS TRIGGER
    LANGUAGE plpgsql
    AS $$
DECLARE
    saldo_atual numeric(14, 3);
BEGIN
    -- O bloqueio serializa saídas concorrentes da mesma entrada.
    SELECT
        re.quantidade - COALESCE((
            SELECT SUM(rs.quantidade)
            FROM registros_saida rs
            WHERE rs.entrada_id = NEW.entrada_id
              AND (TG_OP <> 'UPDATE' OR rs.id <> OLD.id)
        ), 0)
    INTO
        saldo_atual
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
$$;

CREATE TRIGGER trg_validar_saldo_saida
    BEFORE INSERT OR UPDATE OF entrada_id, quantidade ON registros_saida
    FOR EACH ROW
    EXECUTE FUNCTION validar_saldo_saida();

CREATE OR REPLACE FUNCTION validar_quantidade_entrada()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
DECLARE
    quantidade_vendida numeric(14, 3);
BEGIN
    SELECT COALESCE(SUM(quantidade), 0)
      INTO quantidade_vendida
      FROM registros_saida
     WHERE entrada_id = OLD.id;

    IF NEW.quantidade < quantidade_vendida THEN
        RAISE EXCEPTION 'Quantidade da entrada % não pode ser menor que a quantidade já vendida (%)',
            OLD.id, quantidade_vendida;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validar_quantidade_entrada
    BEFORE UPDATE OF quantidade ON registros_entrada
    FOR EACH ROW
    EXECUTE FUNCTION validar_quantidade_entrada();

------------------------------- Index -------------------------------

CREATE INDEX idx_endereco_cidade ON enderecos(cidade_id);

CREATE INDEX idx_produto_categoria ON produtos(categoria_id);

CREATE INDEX idx_lote_validade ON lotes(data_validade);

CREATE INDEX idx_entrada_data ON registros_entrada(data_entrada);

CREATE INDEX idx_entrada_fornecedor ON registros_entrada(fornecedor_id);

CREATE INDEX idx_entrada_lote ON registros_entrada(lote_id);

CREATE INDEX idx_entrada_localizacao ON registros_entrada(localizacao_id);

CREATE INDEX idx_saida_data ON registros_saida(data_saida);

CREATE INDEX idx_saida_entrada ON registros_saida(entrada_id);

-- Papéis de autorização. Usuários LOGIN devem receber um destes papéis.
DO $$
BEGIN
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_roles
        WHERE
            rolname = 'estoque_admin') THEN
    CREATE ROLE estoque_admin NOLOGIN;
END IF;
    IF NOT EXISTS(
        SELECT
            1
        FROM
            pg_roles
        WHERE
            rolname = 'estoque_operador') THEN
    CREATE ROLE estoque_operador NOLOGIN;
END IF;
END
$$;

GRANT USAGE ON SCHEMA public 
TO 
	estoque_admin, estoque_operador;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public 
TO 
	estoque_admin;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public 
TO 
	estoque_admin;

GRANT SELECT, INSERT, UPDATE ON 
	produtos, lotes, registros_entrada, registros_saida 
TO 
	estoque_operador;

GRANT SELECT ON 
	categorias, unidades_medida, fornecedores, localizacoes_estoque, 
	corredores, seccoes, prateleiras, estoque_entrada, estoque_produto 
TO 
	estoque_operador;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public 
TO 
	estoque_operador;

REVOKE ALL ON sessoes, usuarios FROM estoque_operador;
