import { http } from './http'
import type { Cidade, Estado } from '@/types/api'

export const geoApi = {
  async estados(): Promise<Estado[]> {
    const { data } = await http.get<Estado[]>('/geo/estados')
    return data
  },

  async cidades(estadoId: number): Promise<Cidade[]> {
    const { data } = await http.get<Cidade[]>(`/geo/estados/${estadoId}/cidades`)
    return data
  },
}
