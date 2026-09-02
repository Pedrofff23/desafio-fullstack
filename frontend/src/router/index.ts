import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '@/layouts/AppLayout.vue'
import { TOKEN_STORAGE_KEY } from '@/utils/storage'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: AppLayout,
      redirect: '/estoque',
      children: [
        { path: 'estoque', name: 'estoque', component: () => import('@/views/EstoqueView.vue') },
        { path: 'usuarios', name: 'usuarios', component: () => import('@/views/UsuariosView.vue') },
        {
          path: 'usuarios/novo',
          name: 'usuario-novo',
          component: () => import('@/views/UsuarioFormView.vue'),
        },
        {
          path: 'usuarios/:id/editar',
          name: 'usuario-editar',
          component: () => import('@/views/UsuarioFormView.vue'),
        },
        { path: 'produtos', name: 'produtos', component: () => import('@/views/ProdutosView.vue') },
        {
          path: 'produtos/novo',
          name: 'produto-novo',
          component: () => import('@/views/ProdutoFormView.vue'),
        },
        {
          path: 'produtos/:id/editar',
          name: 'produto-editar',
          component: () => import('@/views/ProdutoFormView.vue'),
        },
        {
          path: 'fornecedores',
          name: 'fornecedores',
          component: () => import('@/views/FornecedoresView.vue'),
        },
        {
          path: 'movimentacoes/entrada',
          name: 'entrada',
          component: () => import('@/views/EntradaView.vue'),
        },
        {
          path: 'movimentacoes/saida',
          name: 'saida',
          component: () => import('@/views/SaidaView.vue'),
        },
        {
          path: 'movimentacoes/historico',
          name: 'historico',
          component: () => import('@/views/HistoricoView.vue'),
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'nao-encontrada',
      component: () => import('@/views/NotFoundView.vue'),
      meta: { public: true },
    },
  ],
})

router.beforeEach((to) => {
  const authenticated = Boolean(localStorage.getItem(TOKEN_STORAGE_KEY))
  if (!to.meta.public && !authenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && authenticated) return { name: 'estoque' }
  return true
})

export default router
