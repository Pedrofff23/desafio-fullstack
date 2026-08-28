CREATE OR REPLACE FUNCTION rel_produtos_proximos_vencimento(p_dias INTEGER DEFAULT 30)
RETURNS TABLE (produto_id BIGINT, codigo TEXT, nome_produto TEXT, categoria TEXT, lote_numero TEXT,
 data_validade DATE, dias_restantes INTEGER, quantidade_estoque NUMERIC, unidade TEXT, localizacao TEXT)
LANGUAGE plpgsql STABLE AS $$
BEGIN
 RETURN QUERY
 SELECT p.id,p.codigo::TEXT,p.nome::TEXT,c.nome::TEXT,l.numero_lote::TEXT,l.data_validade,
        l.data_validade-CURRENT_DATE,SUM(ee.quantidade),um.sigla::TEXT,concat_ws(' / ',cr.nome,s.nome,pr.nome)
 FROM estoque_entrada ee JOIN lotes l ON l.id=ee.lote_id JOIN produtos p ON p.id=l.produto_id
 JOIN categorias c ON c.id=p.categoria_id JOIN unidades_medida um ON um.id=p.unidade_medida_id
 JOIN localizacoes_estoque le ON le.id=ee.localizacao_id JOIN prateleiras pr ON pr.id=le.prateleira_id
 JOIN seccoes s ON s.id=pr.seccao_id JOIN corredores cr ON cr.id=s.corredor_id
 WHERE l.data_validade BETWEEN CURRENT_DATE AND CURRENT_DATE+p_dias AND ee.quantidade>0 AND p.ativo AND l.ativo
 GROUP BY p.id,p.codigo,p.nome,c.nome,l.numero_lote,l.data_validade,um.sigla,cr.nome,s.nome,pr.nome
 ORDER BY l.data_validade,p.nome;
END;
$$;

-- Teste: produtos que vencem nos próximos 30 dias.
SELECT * FROM rel_produtos_proximos_vencimento(30);

CREATE OR REPLACE FUNCTION rel_rastreamento_lote(p_numero_lote TEXT)
RETURNS TABLE (produto_id BIGINT,codigo TEXT,nome_produto TEXT,categoria TEXT,quantidade NUMERIC,
 unidade TEXT,localizacao TEXT,data_validade DATE,primeira_entrada TIMESTAMPTZ,fornecedor TEXT)
LANGUAGE sql STABLE AS $$
 SELECT p.id,p.codigo::TEXT,p.nome::TEXT,c.nome::TEXT,SUM(ee.quantidade),um.sigla::TEXT,
        concat_ws(' / ',cr.nome,s.nome,pr.nome),l.data_validade,MIN(re.data_entrada),f.nome_empresa::TEXT
 FROM lotes l JOIN estoque_entrada ee ON ee.lote_id=l.id JOIN registros_entrada re ON re.id=ee.entrada_id
 JOIN fornecedores f ON f.id=re.fornecedor_id JOIN produtos p ON p.id=l.produto_id
 JOIN categorias c ON c.id=p.categoria_id JOIN unidades_medida um ON um.id=p.unidade_medida_id
 JOIN localizacoes_estoque le ON le.id=re.localizacao_id JOIN prateleiras pr ON pr.id=le.prateleira_id
 JOIN seccoes s ON s.id=pr.seccao_id JOIN corredores cr ON cr.id=s.corredor_id
 WHERE l.numero_lote=p_numero_lote AND p.ativo AND l.ativo AND f.ativo
 GROUP BY p.id,p.codigo,p.nome,c.nome,um.sigla,cr.nome,s.nome,pr.nome,l.data_validade,f.nome_empresa
 ORDER BY 7,10;
$$;

-- Teste: rastreamento de um lote existente na massa de exemplo.
SELECT * FROM rel_rastreamento_lote('LOTE2024001A');

CREATE OR REPLACE FUNCTION rel_entradas_periodo(p_data_inicio DATE,p_data_fim DATE)
RETURNS TABLE (entrada_id BIGINT,codigo TEXT,nome_produto TEXT,categoria TEXT,lote_numero TEXT,
 quantidade NUMERIC,unidade TEXT,data_entrada DATE,preco_custo NUMERIC,preco_sugerido NUMERIC,
 valor_total NUMERIC,funcionario TEXT)
LANGUAGE plpgsql STABLE AS $$
BEGIN
 RETURN QUERY
 SELECT re.id,p.codigo::TEXT,p.nome::TEXT,c.nome::TEXT,l.numero_lote::TEXT,re.quantidade::NUMERIC,
        um.sigla::TEXT,re.data_entrada::DATE,re.preco_custo::NUMERIC,re.preco_sugerido::NUMERIC,
        (re.quantidade*re.preco_custo)::NUMERIC,fn.nome_completo::TEXT
 FROM registros_entrada re JOIN lotes l ON l.id=re.lote_id JOIN produtos p ON p.id=l.produto_id
 JOIN categorias c ON c.id=p.categoria_id JOIN unidades_medida um ON um.id=p.unidade_medida_id
 JOIN funcionarios fn ON fn.id=re.funcionario_id
 WHERE re.data_entrada>=p_data_inicio AND re.data_entrada<p_data_fim+1 AND p.ativo AND l.ativo
 ORDER BY re.data_entrada DESC;
END;
$$;

-- Teste: entradas realizadas durante o ano de 2024.
SELECT * FROM rel_entradas_periodo(DATE '2024-01-01', DATE '2024-12-31');

CREATE OR REPLACE FUNCTION rel_lucro_bruto_mensal()
RETURNS TABLE (mes_ano TEXT,total_vendas NUMERIC,total_custo NUMERIC,lucro_bruto NUMERIC,margem_percentual NUMERIC)
LANGUAGE sql STABLE AS $$
 SELECT to_char(rs.data_saida,'YYYY-MM'),ROUND(SUM(rs.quantidade*rs.preco_venda),2),
 ROUND(SUM(rs.quantidade*re.preco_custo),2),ROUND(SUM(rs.quantidade*(rs.preco_venda-re.preco_custo)),2),
 ROUND(SUM(rs.quantidade*(rs.preco_venda-re.preco_custo))/NULLIF(SUM(rs.quantidade*rs.preco_venda),0)*100,2)
 FROM registros_saida rs JOIN registros_entrada re ON re.id=rs.entrada_id GROUP BY 1 ORDER BY 1;
$$;

-- Teste: lucro bruto agrupado por mês.
SELECT * FROM rel_lucro_bruto_mensal();

CREATE OR REPLACE FUNCTION rel_rentabilidade_fornecedor()
RETURNS TABLE (fornecedor_id BIGINT,nome_fornecedor TEXT,total_vendido NUMERIC,total_custo NUMERIC,
 lucro_bruto NUMERIC,margem_percentual NUMERIC)
LANGUAGE sql STABLE AS $$
 SELECT f.id,f.nome_empresa::TEXT,ROUND(SUM(rs.quantidade*rs.preco_venda),2),
 ROUND(SUM(rs.quantidade*re.preco_custo),2),ROUND(SUM(rs.quantidade*(rs.preco_venda-re.preco_custo)),2),
 ROUND(SUM(rs.quantidade*(rs.preco_venda-re.preco_custo))/NULLIF(SUM(rs.quantidade*rs.preco_venda),0)*100,2)
 FROM registros_saida rs JOIN registros_entrada re ON re.id=rs.entrada_id
 JOIN fornecedores f ON f.id=re.fornecedor_id WHERE f.ativo GROUP BY f.id,f.nome_empresa
 ORDER BY SUM(rs.quantidade*(rs.preco_venda-re.preco_custo)) DESC;
$$;

-- Teste: rentabilidade de todos os fornecedores.
SELECT * FROM rel_rentabilidade_fornecedor();

CREATE OR REPLACE FUNCTION rel_historico_compras_fornecedor(p_fornecedor_id BIGINT DEFAULT NULL)
RETURNS TABLE (data_compra DATE,fornecedor TEXT,produto TEXT,categoria TEXT,lote_numero TEXT,
 quantidade NUMERIC,unidade TEXT,preco_custo NUMERIC,preco_sugerido NUMERIC,valor_total NUMERIC,funcionario TEXT)
LANGUAGE sql STABLE AS $$
 SELECT re.data_entrada::DATE,f.nome_empresa::TEXT,p.nome::TEXT,c.nome::TEXT,l.numero_lote::TEXT,
 re.quantidade::NUMERIC,um.sigla::TEXT,re.preco_custo::NUMERIC,re.preco_sugerido::NUMERIC,
 (re.quantidade*re.preco_custo)::NUMERIC,fn.nome_completo::TEXT
 FROM registros_entrada re JOIN fornecedores f ON f.id=re.fornecedor_id JOIN lotes l ON l.id=re.lote_id
 JOIN produtos p ON p.id=l.produto_id JOIN categorias c ON c.id=p.categoria_id
 JOIN unidades_medida um ON um.id=p.unidade_medida_id JOIN funcionarios fn ON fn.id=re.funcionario_id
 WHERE (p_fornecedor_id IS NULL OR f.id=p_fornecedor_id) AND f.ativo AND p.ativo AND l.ativo
 ORDER BY re.data_entrada DESC;
$$;

-- Teste: histórico de todos os fornecedores.
SELECT * FROM rel_historico_compras_fornecedor();

-- Teste opcional: histórico somente do fornecedor de ID 2.
SELECT * FROM rel_historico_compras_fornecedor(2);
