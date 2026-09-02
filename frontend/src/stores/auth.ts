import { defineStore } from 'pinia'

import { authApi } from '@/api/auth'
import type { Usuario } from '@/types/api'
import { TOKEN_STORAGE_KEY, USER_STORAGE_KEY } from '@/utils/storage'

interface AuthState {
  token: string | null
  usuario: Usuario | null
  carregando: boolean
}

function storedUser(): Usuario | null {
  const value = localStorage.getItem(USER_STORAGE_KEY)
  if (!value) return null
  try {
    return JSON.parse(value) as Usuario
  } catch {
    localStorage.removeItem(USER_STORAGE_KEY)
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: localStorage.getItem(TOKEN_STORAGE_KEY),
    usuario: storedUser(),
    carregando: false,
  }),

  getters: {
    autenticado: (state) => Boolean(state.token),
    nomeUsuario: (state) => state.usuario?.funcionario.nome_completo ?? 'Usuário',
  },

  actions: {
    async entrar(email: string, senha: string) {
      this.carregando = true
      try {
        const token = await authApi.login(email, senha)
        this.token = token.access_token
        localStorage.setItem(TOKEN_STORAGE_KEY, token.access_token)
        await this.carregarUsuario()
      } finally {
        this.carregando = false
      }
    },

    async carregarUsuario() {
      if (!this.token) return
      const usuario = await authApi.me()
      this.usuario = usuario
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(usuario))
    },

    async restaurarSessao() {
      if (!this.token || this.carregando) return
      this.carregando = true
      try {
        await this.carregarUsuario()
      } catch {
        this.sair()
      } finally {
        this.carregando = false
      }
    },

    sair() {
      this.token = null
      this.usuario = null
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      localStorage.removeItem(USER_STORAGE_KEY)
    },
  },
})
