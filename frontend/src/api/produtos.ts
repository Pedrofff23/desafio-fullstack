import { http } from './http'
import type {
  CatalogoProduto,
  Lote,
  LoteInput,
  PaginatedResponse,
  Produto,
  ProdutoCreate,
  ProdutoStatus,
  ProdutoUpdate,
} from '@/types/api'

export interface ProdutoFilters {
  page: number
  size: number
  nome?: string
  status?: ProdutoStatus
  preco_min?: number
  preco_max?: number
}

export const produtosApi = {
  async catalogo(): Promise<CatalogoProduto> {
    const { data } = await http.get<CatalogoProduto>('/produtos/catalogo')
    return data
  },

  async listar(params: ProdutoFilters): Promise<PaginatedResponse<Produto>> {
    const { data } = await http.get<PaginatedResponse<Produto>>('/produtos', { params })
    return data
  },

  async get(id: number): Promise<Produto> {
    const { data } = await http.get<Produto>(`/produtos/${id}`)
    return data
  },

  async create(payload: ProdutoCreate): Promise<Produto> {
    const { data } = await http.post<Produto>('/produtos', payload)
    return data
  },

  async update(id: number, payload: ProdutoUpdate): Promise<Produto> {
    const { data } = await http.put<Produto>(`/produtos/${id}`, payload)
    return data
  },

  async excluir(id: number): Promise<void> {
    await http.delete(`/produtos/${id}`)
  },

  async listarLotes(produtoId: number): Promise<Lote[]> {
    const { data } = await http.get<Lote[]>(`/produtos/${produtoId}/lotes`)
    return data
  },

  async createLote(produtoId: number, payload: LoteInput): Promise<Lote> {
    const { data } = await http.post<Lote>(`/produtos/${produtoId}/lotes`, payload)
    return data
  },
}
