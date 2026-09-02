import { http } from './http'
import type { PaginatedResponse, Usuario, UsuarioCreate, UsuarioUpdate } from '@/types/api'

export const usuariosApi = {
  async listar(params: {
    page: number
    size: number
    nome?: string
  }): Promise<PaginatedResponse<Usuario>> {
    const { data } = await http.get<PaginatedResponse<Usuario>>('/usuarios', { params })
    return data
  },

  async get(id: number): Promise<Usuario> {
    const { data } = await http.get<Usuario>(`/usuarios/${id}`)
    return data
  },

  async create(payload: UsuarioCreate): Promise<Usuario> {
    const { data } = await http.post<Usuario>('/usuarios', payload)
    return data
  },

  async update(id: number, payload: UsuarioUpdate): Promise<Usuario> {
    const { data } = await http.put<Usuario>(`/usuarios/${id}`, payload)
    return data
  },

  async excluir(id: number): Promise<void> {
    await http.delete(`/usuarios/${id}`)
  },
}
