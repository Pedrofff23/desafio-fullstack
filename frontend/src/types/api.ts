export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface Estado {
  id: number
  nome: string | null
  uf: string | null
  ibge: number | null
}

export interface Cidade {
  id: number
  nome: string | null
  ibge: number | null
  estado_id: number | null
}

export interface ContatoInput {
  codigo_pais: string
  ddd: string
  numero: string
}

export interface Contato extends ContatoInput {
  id: number
}

export interface EnderecoInput {
  logradouro: string
  numero: string
  complemento: string | null
  cep: string
  bairro: string
  estado_id: number | null
  cidade_id: number | null
}

export interface Endereco extends Omit<EnderecoInput, 'estado_id' | 'cidade_id'> {
  id: number
  cidade: Cidade
}

export interface Funcionario {
  id: number
  nome_completo: string
  data_cadastro: string
  ativo: boolean
  endereco: Endereco
  contato: Contato
}

export interface Usuario {
  id: number
  email: string
  perfil: 'admin' | 'funcionario'
  ativo: boolean
  data_cadastro: string
  funcionario: Funcionario
}

export interface UsuarioCreate {
  nome: string
  email: string
  senha: string
  perfil: 'admin' | 'funcionario'
  contato: ContatoInput
  endereco: EnderecoInput
}

export interface UsuarioUpdate {
  nome?: string
  email?: string
  senha?: string
  perfil?: 'admin' | 'funcionario'
  ativo?: boolean
  contato?: ContatoInput
  endereco?: EnderecoInput
}

export interface UnidadeMedida {
  id: number
  sigla: string
  descricao: string
}

export interface Categoria {
  id: number
  nome: string
  descricao: string | null
}

export interface Localizacao {
  id: number
  prateleira_id: number
  corredor: string
  seccao: string
  prateleira: string
  nivel: number | null
  descricao: string | null
}

export interface Ingrediente {
  id: number
  nome: string
  descricao: string | null
}

export interface Alergeno {
  id: number
  nome: string
  descricao: string | null
}

export interface NutrienteInput {
  nome: string
  unidade: string
  valor: number
}

export interface Nutriente extends NutrienteInput {
  id: number
}

export interface ProdutoIngredienteInput {
  ingrediente_id: number
  ordem: number
}

export interface ProdutoIngrediente extends ProdutoIngredienteInput {
  nome: string
  descricao: string | null
}

export interface CatalogoProduto {
  unidades_medida: UnidadeMedida[]
  categorias: Categoria[]
  localizacoes: Localizacao[]
  ingredientes: Ingrediente[]
  alergenos: Alergeno[]
}

export interface LoteInput {
  numero_lote: string
  data_producao: string
  data_validade: string | null
  ativo: boolean
}

export interface Lote extends LoteInput {
  id: number
  produto_id: number
  quantidade_estoque: number
  status_estoque: 'com_estoque' | 'sem_estoque'
  dias_para_vencer: number | null
  status_validade: LoteValidadeStatus
  localizacoes: LoteLocalizacao[]
}

export interface LoteLocalizacao extends Localizacao {
  quantidade: number
}

export type LoteValidadeStatus = 'normal' | 'validade_proxima' | 'vencido' | 'sem_validade'

export type ProdutoStatus = 'ok' | 'estoque_baixo' | 'zerado'

export interface Produto {
  id: number
  codigo: string
  nome: string
  descricao: string | null
  preco: number
  perecivel: boolean
  unidade_medida_id: number
  categoria_id: number
  localizacao_id: number | null
  ativo: boolean
  unidade_medida: UnidadeMedida | null
  categoria: Categoria | null
  quantidade_estoque: number
  status: ProdutoStatus
  nutrientes: Nutriente[]
  ingredientes: ProdutoIngrediente[]
  alergenos: Alergeno[]
}

export interface ProdutoCreate {
  codigo: string
  nome: string
  descricao: string | null
  preco: number
  perecivel: boolean
  unidade_medida_id: number | null
  categoria_id: number | null
  localizacao_id: number | null
  ativo: boolean
  lote_inicial: LoteInput | null
  nutrientes: NutrienteInput[]
  ingredientes: ProdutoIngredienteInput[]
  alergeno_ids: number[]
}

export interface ProdutoUpdate {
  codigo?: string
  nome?: string
  descricao?: string | null
  preco?: number
  unidade_medida_id?: number
  categoria_id?: number
  localizacao_id?: number
  ativo?: boolean
  nutrientes?: NutrienteInput[]
  ingredientes?: ProdutoIngredienteInput[]
  alergeno_ids?: number[]
}

export interface Fornecedor {
  id: number
  nome_empresa: string
  ativo: boolean
  data_cadastro: string
  contato: Contato
  endereco: Endereco
}

export interface FornecedorCreate {
  nome_empresa: string
  ativo: boolean
  contato: ContatoInput
  endereco: EnderecoInput
}

export interface RegistroEntradaCreate {
  lote_id: number | null
  fornecedor_id: number | null
  localizacao_id: number | null
  quantidade: number
  data_entrada: string | null
  tipo_entrada: string
  observacao: string | null
  preco_custo: number
}

export interface RegistroSaidaCreate {
  entrada_id: number | null
  quantidade: number
  data_saida: string | null
  tipo_saida: string
  preco_venda: number
}

export interface EstoqueProduto {
  produto_id: number
  produto_nome: string
  quantidade: number
}

export interface EstoqueEntrada {
  entrada_id: number
  lote_id: number
  produto_id: number
  fornecedor_id: number
  localizacao_id: number
  quantidade: number
}

export interface Movimento {
  id: number
  tipo: 'entrada' | 'saida'
  tipo_movimento: string
  produto_id: number | null
  produto_nome: string | null
  lote_id: number | null
  quantidade: number
  data_movimento: string
  preco: number | null
  observacao: string | null
  funcionario_id: number | null
  responsavel_email: string | null
}
