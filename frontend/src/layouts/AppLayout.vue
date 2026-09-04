<script lang="ts">
import { defineComponent } from 'vue'
import { mapStores } from 'pinia'

import { useAuthStore } from '@/stores/auth'

export default defineComponent({
  name: 'AppLayout',
  data() {
    return {
      drawer: true,
      items: [
        { title: 'Estoque atual', icon: 'mdi-view-dashboard-outline', to: '/estoque' },
        { title: 'Usuários', icon: 'mdi-account-group-outline', to: '/usuarios' },
        { title: 'Produtos e lotes', icon: 'mdi-food-apple-outline', to: '/produtos' },
        { title: 'Fornecedores', icon: 'mdi-truck-outline', to: '/fornecedores' },
        { title: 'Registrar entrada', icon: 'mdi-package-down', to: '/movimentacoes/entrada' },
        { title: 'Registrar saída', icon: 'mdi-package-up', to: '/movimentacoes/saida' },
        { title: 'Histórico', icon: 'mdi-history', to: '/movimentacoes/historico' },
      ],
    }
  },
  computed: {
    ...mapStores(useAuthStore),
  },
  mounted() {
    void this.authStore.restaurarSessao()
  },
  methods: {
    logout() {
      this.authStore.sair()
      void this.$router.replace('/login')
    },
  },
})
</script>

<template>
  <div>
    <v-navigation-drawer v-model="drawer" color="#40066e" theme="dark" width="280">
      <div class="brand-block pa-6">
        <v-avatar color="#560894" rounded="lg" size="44">
          <v-icon icon="mdi-warehouse" />
        </v-avatar>
        <div>
          <div class="text-subtitle-1 font-weight-bold">Estoque</div>
          <div class="text-caption text-medium-emphasis">Gestão de alimentos</div>
        </div>
      </div>

      <v-divider class="mx-4 mb-3" />
      <v-list nav density="comfortable">
        <v-list-item
          v-for="item in items"
          :key="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          :to="item.to"
          rounded="lg"
        />
      </v-list>
    </v-navigation-drawer>

    <v-app-bar color="surface" elevation="0" border="b">
      <v-app-bar-nav-icon aria-label="Alternar menu" @click="drawer = !drawer" />
      <v-spacer />
      <div class="user-summary text-right mr-3">
        <div class="text-body-2 font-weight-medium">{{ authStore.nomeUsuario }}</div>
        <div class="text-caption text-medium-emphasis">{{ authStore.usuario?.email }}</div>
      </div>
      <v-btn icon="mdi-logout" aria-label="Sair" title="Sair" @click="logout" />
    </v-app-bar>

    <v-main>
      <v-container class="pa-4 pa-md-8" fluid>
        <router-view />
      </v-container>
    </v-main>
  </div>
</template>

<style scoped>
.brand-block {
  display: flex;
  align-items: center;
  gap: 14px;
}

@media (max-width: 600px) {
  .user-summary {
    display: none;
  }
}
</style>
