INSERT INTO unidades_medida (sigla, descricao) VALUES
    ('kg',  'Quilograma'),
    ('g',   'Grama'),
    ('mg',  'Miligrama'),
    ('kcal','Quilocaloria'),
    ('l',   'Litro'),
    ('ml',  'Mililitro'),
    ('un',  'Unidade'),
    ('cx',  'Caixa'),
    ('fr',  'Frasco'),
    ('pct', 'Pacote');

INSERT INTO categorias (nome, descricao) VALUES
    ('Laticínios',  'Produtos derivados de leite'),
    ('Bebidas',     'Bebidas e refrigerantes'),
    ('Carnes',      'Carnes bovina, frango, suína, etc.'),
    ('Hortifrúti',  'Frutas, verduras e hortaliças'),
    ('Padaria',     'Pães, bolos e produtos de padaria'),
    ('Limpeza',     'Produtos de limpeza e higiene'),
    ('Congelados',  'Produtos congelados'),
    ('Enlatados',   'Produtos enlatados e conservas'),
    ('Doces',       'Doces e confeitarias'),
    ('Bebidas Alcoólicas', 'Cervejas, vinhos e destilados');

INSERT INTO alergenos (nome, descricao) VALUES
    ('Glúten',        'Encontrado em trigo, centeio, cevada, entre outros'),
    ('Lactose',       'Encontrada no leite e derivados'),
    ('Soja',          'Encontrada em produtos de soja e derivados'),
    ('Nozes',         'Encontradas em nozes, castanhas e amêndoas'),
    ('Ovos',          'Encontrados em ovos de galinha e derivados'),
    ('Frutos do Mar', 'Crustáceos e moluscos'),
    ('Cenoura',       'Alergia a cenoura (OGM ou alérgico)');

INSERT INTO ingredientes (nome, descricao) VALUES
    ('Leite',              'Leite de vaca integral'),
    ('Açúcar',             'Açúcar refinado'),
    ('Farinha de Trigo',   'Farinha de trigo comum'),
    ('Ovos',               'Ovos de galinha caipiras'),
    ('Fermento',           'Fermento químico em pó'),
    ('Óleo Vegetal',       'Óleo de soja ou canola'),
    ('Água',               'Água potável'),
    ('Sal',                'Sal comum refinado');

-- ============================================================
-- Part 2: Stock location hierarchy (corredores -> seccoes -> prateleiras -> localizacoes_estoque)
-- ============================================================

INSERT INTO corredores (nome, descricao) VALUES
    ('A', 'Corredor de bebidas'),
    ('B', 'Corredor de alimentos secos'),
    ('C', 'Corredor de laticínios e refrigerados'),
    ('D', 'Corredor de produtos de limpeza');

INSERT INTO seccoes (corredor_id, nome, descricao) VALUES
    (1, '1', 'Seção de refrigerantes'),
    (1, '2', 'Seção de cervejas'),
    (3, '1', 'Seção de leites'),
    (3, '2', 'Seção de iogurtes'),
    (4, '1', 'Seção de produtos de limpeza');

INSERT INTO prateleiras (seccao_id, nome, nivel, descricao) VALUES
    (1, 'A1', 1, 'Prateleira superior de refrigerantes'),
    (1, 'A2', 2, 'Prateleira inferior de refrigerantes'),
    (2, 'B1', 1, 'Prateleira de cervejas geladas'),
    (3, 'C1', 1, 'Prateleira de leites'),
    (3, 'C2', 2, 'Prateleira de iogurtes'),
    (5, 'D1', 1, 'Prateleira de limpeza');

INSERT INTO localizacoes_estoque (prateleira_id) VALUES
    (1), (2), (3), (4), (5), (6);

INSERT INTO enderecos (logradouro, numero, complemento, cep, bairro, cidade_id)
VALUES ('SGAN 912', '340', 'Conjunto A', '70830000', 'Asa Norte',
        (SELECT id FROM cidades WHERE nome = 'Brasília' LIMIT 1));

INSERT INTO enderecos (logradouro, numero, complemento, cep, bairro, cidade_id)
VALUES ('Rua dos Aimorés', '250', 'Casa 4', '30241000', 'Savassi',
        (SELECT id FROM cidades WHERE ibge = 3106200));

INSERT INTO enderecos (logradouro, numero, complemento, cep, bairro, cidade_id)
VALUES ('Avenida Paulista', '1842', NULL, '01310000', 'Bela Vista',
        (SELECT id FROM cidades WHERE ibge = 3550308));

INSERT INTO enderecos (logradouro, numero, complemento, cep, bairro, cidade_id)
VALUES ('Rua das Flores', '741', 'Andar 2', '90044000', 'Centro',
        (SELECT id FROM cidades WHERE ibge = 4314902));
