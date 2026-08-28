
INSERT INTO contatos (codigo_pais, ddd, numero) VALUES
 ('+55','61','32115500'), ('+55','31','33998877'), ('+55','11','99887766'), ('+55','51','34567890');

INSERT INTO funcionarios (nome_completo,endereco_id,contato_id,data_cadastro) VALUES
 ('João Silva',1,1,'2024-01-15 08:00:00-03'), ('Maria Santos',2,2,'2024-02-20 09:30:00-03'),
 ('Pedro Costa',3,3,'2024-03-10 14:00:00-03'), ('Ana Oliveira',4,4,'2024-01-05 07:00:00-03');
 
INSERT INTO usuarios (funcionario_id,email,senha_hash,perfil,data_cadastro) VALUES
 (1,'joao.silva@mercado.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxEBhHZea8hP0H47vU09CZ2dnG','admin','2024-01-15 08:00:00-03'),
 (2,'maria.santos@mercado.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxEBhHZea8hP0H47vU09CZ2dnG','funcionario','2024-02-20 09:30:00-03'),
 (3,'pedro.costa@mercado.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxEBhHZea8hP0H47vU09CZ2dnG','funcionario','2024-03-10 14:00:00-03'),
 (4,'ana.oliveira@mercado.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxEBhHZea8hP0H47vU09CZ2dnG','funcionario','2024-01-05 07:00:00-03');

INSERT INTO fornecedores (nome_empresa,contato_id,endereco_id,data_cadastro) VALUES
 ('Bebidas São Paulo Ltda',3,3,'2023-12-01 10:00:00-03'),
 ('Laticínios Mineiros S.A.',2,2,'2023-11-15 11:00:00-03'),
 ('Frigorífico Sul Carnes Ltda',4,4,'2023-10-20 09:00:00-03'),
 ('Hortifrúti Fresh Delivery',1,1,'2024-01-10 08:30:00-03');

INSERT INTO produtos (codigo,nome,descricao,unidade_medida_id,categoria_id,localizacao_id,data_cadastro,funcionario_id) VALUES
 ('PROD001','Leite Integral','Leite de vaca integral pasteurizado 1L',(SELECT id FROM unidades_medida WHERE sigla='l'),(SELECT id FROM categorias WHERE nome='Laticínios'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=4),'2024-01-15 09:00:00-03',1),
 ('PROD002','Iogurte Natural','Iogurte natural sem sabor 500g',(SELECT id FROM unidades_medida WHERE sigla='un'),(SELECT id FROM categorias WHERE nome='Laticínios'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=5),'2024-01-20 10:30:00-03',2),
 ('PROD003','Refrigerante de Cola 2L','Refrigerante de cola 2 litros',(SELECT id FROM unidades_medida WHERE sigla='l'),(SELECT id FROM categorias WHERE nome='Bebidas'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=1),'2024-02-05 14:00:00-03',3),
 ('PROD004','Pão Francês','Pão francês fresco unidade',(SELECT id FROM unidades_medida WHERE sigla='un'),(SELECT id FROM categorias WHERE nome='Padaria'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=6),'2024-03-12 06:00:00-03',4),
 ('PROD005','Carne Bovina','Carne bovina alcatra congelada por kg',(SELECT id FROM unidades_medida WHERE sigla='kg'),(SELECT id FROM categorias WHERE nome='Carnes'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=2),'2024-02-18 11:00:00-03',2),
 ('PROD006','Leite sem Lactose','Leite sem lactose 1L',(SELECT id FROM unidades_medida WHERE sigla='l'),(SELECT id FROM categorias WHERE nome='Laticínios'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=4),'2024-02-20 09:00:00-03',3),
 ('PROD007','Ovo de Galinha','Ovos de galinha caipira caixa 12 unidades',(SELECT id FROM unidades_medida WHERE sigla='cx'),(SELECT id FROM categorias WHERE nome='Hortifrúti'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=2),'2024-03-10 07:00:00-03',4),
 ('PROD008','Cerveja Pilsen 6pk','Cerveja Pilsen 6 pack 330ml cada',(SELECT id FROM unidades_medida WHERE sigla='pct'),(SELECT id FROM categorias WHERE nome='Bebidas Alcoólicas'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=3),'2024-02-25 16:00:00-03',1);

INSERT INTO lotes (produto_id,numero_lote,data_producao,data_validade) VALUES
 ((SELECT id FROM produtos WHERE codigo='PROD001'),'LOTE2024001A','2024-01-10','2024-04-10'),
 ((SELECT id FROM produtos WHERE codigo='PROD002'),'LOTE2024001B','2024-01-15','2024-04-15'),
 ((SELECT id FROM produtos WHERE codigo='PROD003'),'LOTE2024002A','2024-02-01','2024-05-01'),
 ((SELECT id FROM produtos WHERE codigo='PROD004'),'LOTE2024003A','2024-03-05','2024-06-05'),
 ((SELECT id FROM produtos WHERE codigo='PROD005'),'LOTE2024004B','2024-02-15','2024-05-15'),
 ((SELECT id FROM produtos WHERE codigo='PROD006'),'LOTENEAR30DIAS','2024-02-20','2024-03-20'),
 ((SELECT id FROM produtos WHERE codigo='PROD007'),'LOTE2024003B','2024-03-10','2024-06-10'),
 ((SELECT id FROM produtos WHERE codigo='PROD008'),'LOTE2024005A','2024-03-15','2024-06-15');

INSERT INTO nutrientes (produto_id,nome,unidade,valor) VALUES
 ((SELECT id FROM produtos WHERE codigo='PROD001'),'Energia (Calorias)','kcal',640),
 ((SELECT id FROM produtos WHERE codigo='PROD001'),'Proteína','g',32),
 ((SELECT id FROM produtos WHERE codigo='PROD003'),'Carboidrato','g',110);
INSERT INTO produtos_ingredientes (produto_id,ingrediente_id,ordem) VALUES
 ((SELECT id FROM produtos WHERE codigo='PROD001'),(SELECT id FROM ingredientes WHERE nome='Leite'),1),
 ((SELECT id FROM produtos WHERE codigo='PROD003'),(SELECT id FROM ingredientes WHERE nome='Água'),1),
 ((SELECT id FROM produtos WHERE codigo='PROD003'),(SELECT id FROM ingredientes WHERE nome='Açúcar'),2),
 ((SELECT id FROM produtos WHERE codigo='PROD004'),(SELECT id FROM ingredientes WHERE nome='Farinha de Trigo'),1);
INSERT INTO produtos_alergenos (produto_id,alergeno_id) VALUES
 ((SELECT id FROM produtos WHERE codigo='PROD001'),(SELECT id FROM alergenos WHERE nome='Lactose')),
 ((SELECT id FROM produtos WHERE codigo='PROD004'),(SELECT id FROM alergenos WHERE nome='Glúten')),
 ((SELECT id FROM produtos WHERE codigo='PROD007'),(SELECT id FROM alergenos WHERE nome='Ovos'));

INSERT INTO registros_entrada (lote_id,fornecedor_id,quantidade,data_entrada,preco_custo,preco_sugerido,funcionario_id) VALUES
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024001A'),2,50,'2024-01-15 09:00:00-03',3.50,5.90,1),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024001B'),2,80,'2024-01-20 10:30:00-03',2.80,4.90,2),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024002A'),1,120,'2024-02-05 14:00:00-03',7.50,12.90,3),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024004B'),3,50,'2024-02-18 11:00:00-03',18.90,32.90,2),
 ((SELECT id FROM lotes WHERE numero_lote='LOTENEAR30DIAS'),2,20,'2024-02-20 09:00:00-03',4.20,7.50,3),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024005A'),1,60,'2024-02-25 16:00:00-03',12.00,22.90,1),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024003A'),4,200,'2024-03-12 06:00:00-03',0.45,1.20,4),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024003B'),4,40,'2024-03-10 07:00:00-03',6.00,11.90,4);
INSERT INTO registros_saida (entrada_id,quantidade,data_saida,preco_venda,funcionario_id) VALUES
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024001A'),15,'2024-01-20 14:30:00-03',5.90,2),((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024001A'),20,'2024-02-10 09:15:00-03',5.90,3),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024001B'),30,'2024-01-25 11:00:00-03',4.90,2),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024002A'),50,'2024-02-15 16:45:00-03',12.90,1),((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024002A'),30,'2024-02-28 10:20:00-03',12.90,4),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024004B'),12,'2024-02-25 13:00:00-03',32.90,2),((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024004B'),15,'2024-03-05 15:30:00-03',32.90,3),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTENEAR30DIAS'),8,'2024-02-25 08:00:00-03',7.50,4),((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTENEAR30DIAS'),10,'2024-03-10 11:45:00-03',7.50,1),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024005A'),25,'2024-03-15 19:00:00-03',22.90,4),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024003A'),150,'2024-03-13 07:30:00-03',1.20,4),((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024003A'),40,'2024-03-14 08:00:00-03',1.20,1),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024003B'),20,'2024-03-11 08:30:00-03',11.90,1),((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024003B'),15,'2024-03-12 09:15:00-03',11.90,4);

-- Produtos adicionais, com lotes e movimentações para enriquecer os relatórios.
INSERT INTO produtos (codigo,nome,descricao,unidade_medida_id,categoria_id,localizacao_id,data_cadastro,funcionario_id) VALUES
 ('PROD009','Arroz Branco 5kg','Arroz branco tipo 1, pacote de 5 kg',(SELECT id FROM unidades_medida WHERE sigla='pct'),(SELECT id FROM categorias WHERE nome='Enlatados'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=2),'2024-03-18 09:00:00-03',1),
 ('PROD010','Feijão Carioca 1kg','Feijão carioca selecionado, pacote de 1 kg',(SELECT id FROM unidades_medida WHERE sigla='pct'),(SELECT id FROM categorias WHERE nome='Enlatados'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=2),'2024-03-18 09:10:00-03',1),
 ('PROD011','Milho Verde em Conserva','Lata de milho verde 170 g',(SELECT id FROM unidades_medida WHERE sigla='un'),(SELECT id FROM categorias WHERE nome='Enlatados'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=2),'2024-03-19 10:00:00-03',2),
 ('PROD012','Batata Frita Congelada','Batata palito congelada, pacote de 1,5 kg',(SELECT id FROM unidades_medida WHERE sigla='pct'),(SELECT id FROM categorias WHERE nome='Congelados'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=5),'2024-03-19 10:20:00-03',2),
 ('PROD013','Sorvete de Chocolate','Sorvete de chocolate, pote de 1,5 L',(SELECT id FROM unidades_medida WHERE sigla='un'),(SELECT id FROM categorias WHERE nome='Congelados'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=5),'2024-03-20 11:00:00-03',3),
 ('PROD014','Banana Prata','Banana prata vendida por quilograma',(SELECT id FROM unidades_medida WHERE sigla='kg'),(SELECT id FROM categorias WHERE nome='Hortifrúti'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=6),'2024-03-20 11:20:00-03',3),
 ('PROD015','Maçã Gala','Maçã gala vendida por quilograma',(SELECT id FROM unidades_medida WHERE sigla='kg'),(SELECT id FROM categorias WHERE nome='Hortifrúti'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=6),'2024-03-20 11:30:00-03',3),
 ('PROD016','Chocolate ao Leite','Barra de chocolate ao leite 90 g',(SELECT id FROM unidades_medida WHERE sigla='un'),(SELECT id FROM categorias WHERE nome='Doces'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=2),'2024-03-21 08:00:00-03',4),
 ('PROD017','Biscoito Recheado','Biscoito recheado sabor chocolate 140 g',(SELECT id FROM unidades_medida WHERE sigla='pct'),(SELECT id FROM categorias WHERE nome='Doces'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=2),'2024-03-21 08:10:00-03',4),
 ('PROD018','Água Sanitária 1L','Água sanitária para limpeza doméstica, frasco de 1 L',(SELECT id FROM unidades_medida WHERE sigla='fr'),(SELECT id FROM categorias WHERE nome='Limpeza'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=6),'2024-03-21 08:20:00-03',4);

INSERT INTO lotes (produto_id,numero_lote,data_producao,data_validade) VALUES
 ((SELECT id FROM produtos WHERE codigo='PROD009'),'LOTE2024006A','2024-02-10','2025-02-10'),
 ((SELECT id FROM produtos WHERE codigo='PROD010'),'LOTE2024006B','2024-02-12','2025-02-12'),
 ((SELECT id FROM produtos WHERE codigo='PROD011'),'LOTE2024006C','2024-01-20','2026-01-20'),
 ((SELECT id FROM produtos WHERE codigo='PROD012'),'LOTE2024007A','2024-03-01','2025-03-01'),
 ((SELECT id FROM produtos WHERE codigo='PROD013'),'LOTE2024007B','2024-03-05','2025-03-05'),
 ((SELECT id FROM produtos WHERE codigo='PROD014'),'LOTE2024008A','2024-03-18','2024-04-05'),
 ((SELECT id FROM produtos WHERE codigo='PROD015'),'LOTE2024008B','2024-03-18','2024-04-15'),
 ((SELECT id FROM produtos WHERE codigo='PROD016'),'LOTE2024009A','2024-02-01','2025-02-01'),
 ((SELECT id FROM produtos WHERE codigo='PROD017'),'LOTE2024009B','2024-02-05','2025-02-05'),
 ((SELECT id FROM produtos WHERE codigo='PROD018'),'LOTE2024010A','2024-03-10','2025-03-10');

INSERT INTO registros_entrada (lote_id,fornecedor_id,quantidade,data_entrada,preco_custo,preco_sugerido,funcionario_id) VALUES
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024006A'),4,40,'2024-03-18 09:30:00-03',18.50,26.90,1),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024006B'),4,80,'2024-03-18 09:40:00-03',5.20,8.90,1),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024006C'),4,96,'2024-03-19 10:30:00-03',2.40,4.50,2),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024007A'),2,30,'2024-03-19 10:45:00-03',14.00,22.90,2),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024007B'),2,24,'2024-03-20 11:15:00-03',16.50,29.90,3),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024008A'),4,35,'2024-03-20 11:40:00-03',3.80,6.99,3),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024008B'),4,28,'2024-03-20 11:50:00-03',5.90,10.99,3),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024009A'),1,60,'2024-03-21 08:30:00-03',3.10,6.50,4),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024009B'),1,72,'2024-03-21 08:40:00-03',2.20,4.90,4),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE2024010A'),1,48,'2024-03-21 08:50:00-03',2.80,5.50,4);

INSERT INTO registros_saida (entrada_id,quantidade,data_saida,preco_venda,funcionario_id) VALUES
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024006A'),12,'2024-03-22 14:00:00-03',26.90,1),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024006B'),25,'2024-03-22 14:10:00-03',8.90,2),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024006C'),30,'2024-03-22 14:20:00-03',4.50,2),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024007A'),8,'2024-03-23 15:00:00-03',22.90,3),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024007B'),5,'2024-03-23 15:10:00-03',29.90,3),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024008A'),14,'2024-03-22 09:00:00-03',6.99,4),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024008B'),10,'2024-03-22 09:10:00-03',10.99,4),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024009A'),20,'2024-03-24 16:00:00-03',6.50,1),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024009B'),18,'2024-03-24 16:10:00-03',4.90,1),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE2024010A'),15,'2024-03-24 16:20:00-03',5.50,1);

-- Demonstração do relatório de vencimento: as validades são relativas à data da carga.
INSERT INTO produtos (codigo,nome,descricao,unidade_medida_id,categoria_id,localizacao_id,data_cadastro,funcionario_id) VALUES
 ('PROD019','Queijo Muçarela Fatiado','Queijo muçarela fatiado, embalagem de 200 g',(SELECT id FROM unidades_medida WHERE sigla='pct'),(SELECT id FROM categorias WHERE nome='Laticínios'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=4),CURRENT_TIMESTAMP,1),
 ('PROD020','Iogurte de Morango','Iogurte sabor morango, pote de 170 g',(SELECT id FROM unidades_medida WHERE sigla='un'),(SELECT id FROM categorias WHERE nome='Laticínios'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=5),CURRENT_TIMESTAMP,2),
 ('PROD021','Peito de Frango Congelado','Peito de frango congelado, pacote de 1 kg',(SELECT id FROM unidades_medida WHERE sigla='kg'),(SELECT id FROM categorias WHERE nome='Congelados'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=5),CURRENT_TIMESTAMP,3),
 ('PROD022','Suco de Laranja Integral','Suco de laranja integral, garrafa de 1 L',(SELECT id FROM unidades_medida WHERE sigla='l'),(SELECT id FROM categorias WHERE nome='Bebidas'),(SELECT id FROM localizacoes_estoque WHERE prateleira_id=1),CURRENT_TIMESTAMP,4);

INSERT INTO lotes (produto_id,numero_lote,data_producao,data_validade) VALUES
 ((SELECT id FROM produtos WHERE codigo='PROD019'),'LOTE-DEMO-05-DIAS',CURRENT_DATE-20,CURRENT_DATE+5),
 ((SELECT id FROM produtos WHERE codigo='PROD020'),'LOTE-DEMO-12-DIAS',CURRENT_DATE-10,CURRENT_DATE+12),
 ((SELECT id FROM produtos WHERE codigo='PROD021'),'LOTE-DEMO-20-DIAS',CURRENT_DATE-15,CURRENT_DATE+20),
 ((SELECT id FROM produtos WHERE codigo='PROD022'),'LOTE-DEMO-28-DIAS',CURRENT_DATE-7,CURRENT_DATE+28);

INSERT INTO registros_entrada (lote_id,fornecedor_id,quantidade,data_entrada,preco_custo,preco_sugerido,funcionario_id) VALUES
 ((SELECT id FROM lotes WHERE numero_lote='LOTE-DEMO-05-DIAS'),2,30,CURRENT_TIMESTAMP,8.50,14.90,1),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE-DEMO-12-DIAS'),2,48,CURRENT_TIMESTAMP,2.20,4.50,2),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE-DEMO-20-DIAS'),3,25,CURRENT_TIMESTAMP,17.80,29.90,3),
 ((SELECT id FROM lotes WHERE numero_lote='LOTE-DEMO-28-DIAS'),1,36,CURRENT_TIMESTAMP,5.40,9.90,4);

INSERT INTO registros_saida (entrada_id,quantidade,data_saida,preco_venda,funcionario_id) VALUES
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE-DEMO-05-DIAS'),6,CURRENT_TIMESTAMP,14.90,1),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE-DEMO-12-DIAS'),10,CURRENT_TIMESTAMP,4.50,2),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE-DEMO-20-DIAS'),4,CURRENT_TIMESTAMP,29.90,3),
 ((SELECT re.id FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id WHERE l.numero_lote='LOTE-DEMO-28-DIAS'),8,CURRENT_TIMESTAMP,9.90,4);
