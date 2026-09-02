import { http } from './http'
import type {
  EstoqueEntrada,
  EstoqueProduto,
  Fornecedor,
  FornecedorCreate,
  Movimento,
  PaginatedResponse,
  RegistroEntradaCreate,
  RegistroSaidaCreate,
} from '@/types/api'

export interface HistoricoFilters {
  page: number
  size: number
  produto_id?: number
  tipo?: 'entrada' | 'saida'
  funcionario_id?: number
  quantidade?: number
  data_inicio?: string
  data_fim?: string
}

export const transacoesApi = {
  async fornecedores(): Promise<Fornecedor[]> {
    const { data } = await http.get<Fornecedor[]>('/transacoes/fornecedores')
    return data
  },

  async createFornecedor(payload: FornecedorCreate): Promise<Fornecedor> {
    const { data } = await http.post<Fornecedor>('/transacoes/fornecedores', payload)
    return data
  },

  async registrarEntrada(payload: RegistroEntradaCreate): Promise<void> {
    await http.post('/transacoes/entrada', payload)
  },

  async entradasDisponiveis(produtoId?: number): Promise<EstoqueEntrada[]> {
    const { data } = await http.get<EstoqueEntrada[]>('/transacoes/entradas-disponiveis', {
      params: produtoId ? { produto_id: produtoId } : undefined,
    })
    return data
  },

  async registrarSaida(payload: RegistroSaidaCreate): Promise<void> {
    await http.post('/transacoes/saida', payload)
  },

  async estoque(page: number, size: number): Promise<PaginatedResponse<EstoqueProduto>> {
    const { data } = await http.get<PaginatedResponse<EstoqueProduto>>('/transacoes/estoque', {
      params: { page, size },
    })
    return data
  },

  async historico(params: HistoricoFilters): Promise<PaginatedResponse<Movimento>> {
    const { data } = await http.get<PaginatedResponse<Movimento>>('/transacoes/historico', {
      params,
    })
    return data
  },
}
