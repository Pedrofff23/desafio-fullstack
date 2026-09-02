import { http } from './http'
import type { TokenResponse, Usuario } from '@/types/api'

export const authApi = {
  async login(email: string, senha: string): Promise<TokenResponse> {
    const { data } = await http.post<TokenResponse>('/auth/login', { email, senha })
    return data
  },

  async me(): Promise<Usuario> {
    const { data } = await http.get<Usuario>('/auth/me')
    return data
  },
}
