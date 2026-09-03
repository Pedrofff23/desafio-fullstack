<script lang="ts">
import { defineComponent } from 'vue'

import { produtosApi } from '@/api/produtos'
import { transacoesApi, type HistoricoFilters } from '@/api/transacoes'
import { usuariosApi } from '@/api/usuarios'
import EmptyTableRow from '@/components/EmptyTableRow.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationControls from '@/components/PaginationControls.vue'
import type { Movimento, Produto, Usuario } from '@/types/api'
import { getErrorMessage } from '@/utils/errors'
import { formatCurrency, formatDateTime, formatQuantity } from '@/utils/formatters'

export default defineComponent({
  name: 'HistoricoView',
  components: { EmptyTableRow, PageHeader, PaginationControls },
  data() {
    return {
      items: [] as Movimento[],
      products: [] as Produto[],
      users: [] as Usuario[],
      filters: {
        produto_id: null as number | null,
        tipo: null as 'entrada' | 'saida' | null,
        funcionario_id: null as number | null,
        quantidade: null as number | null,
        data_inicio: '',
        data_fim: '',
      },
      page: 1,
      size: 20,
      pages: 0,
      total: 0,
      loading: false,
      error: '',
    }
  },
  computed: {
    userOptions(): Array<{ title: string; value: number }> {
      return this.users.map((user) => ({
        title: `${user.funcionario.nome_completo} · ${user.email}`,
        value: user.funcionario.id,
      }))
    },
  },
  watch: {
    page() {
      void this.load()
    },
  },
  async mounted() {
    try {
      const [products, users] = await Promise.all([
        produtosApi.listar({ page: 1, size: 100 }),
        usuariosApi.listar({ page: 1, size: 100 }),
      ])
      this.products = products.items
      this.users = users.items
      await this.load()
    } catch (error) {
      this.error = getErrorMessage(error)
    }
  },
  methods: {
    formatCurrency,
    formatDateTime,
    formatQuantity,
    async load() {
      this.loading = true
      this.error = ''
      const params: HistoricoFilters = { page: this.page, size: this.size }
      if (this.filters.produto_id) params.produto_id = this.filters.produto_id
      if (this.filters.tipo) params.tipo = this.filters.tipo
      if (this.filters.funcionario_id) params.funcionario_id = this.filters.funcionario_id
      if (this.filters.quantidade !== null) params.quantidade = this.filters.quantidade
      if (this.filters.data_inicio) params.data_inicio = `${this.filters.data_inicio}T00:00:00`
      if (this.filters.data_fim) params.data_fim = `${this.filters.data_fim}T23:59:59`
      try {
        const response = await transacoesApi.historico(params)
        this.items = response.items
        this.pages = response.pages
        this.total = response.total
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.loading = false
      }
    },
    search() {
      if (this.page === 1) void this.load()
      else this.page = 1
    },
    clearFilters() {
      this.filters = {
        produto_id: null,
        tipo: null,
        funcionario_id: null,
        quantidade: null,
        data_inicio: '',
        data_fim: '',
      }
      this.search()
    },
  },
})
</script>

<template>
  <div>
    <PageHeader
      title="Histórico de movimentações"
      subtitle="Auditoria de entradas e saídas, sem alteração ou exclusão."
    />
    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>

    <v-card class="data-card pa-4 mb-4">
      <v-form @submit.prevent="search">
        <v-row>
          <v-col cols="12" md="4"
            ><v-autocomplete
              v-model="filters.produto_id"
              :items="products"
              item-title="nome"
              item-value="id"
              label="Produto"
              clearable
              hide-details
          /></v-col>
          <v-col cols="6" md="2"
            ><v-select
              v-model="filters.tipo"
              :items="[
                { title: 'Entrada', value: 'entrada' },
                { title: 'Saída', value: 'saida' },
              ]"
              label="Movimento"
              clearable
              hide-details
          /></v-col>
          <v-col cols="6" md="2"
            ><v-text-field
              v-model.number="filters.quantidade"
              type="number"
              min="0.001"
              step="0.001"
              label="Quantidade"
              hide-details
          /></v-col>
          <v-col cols="12" md="4"
            ><v-autocomplete
              v-model="filters.funcionario_id"
              :items="userOptions"
              label="Responsável"
              clearable
              hide-details
          /></v-col>
          <v-col cols="6" md="3"
            ><v-text-field
              v-model="filters.data_inicio"
              type="date"
              label="Data inicial"
              hide-details
          /></v-col>
          <v-col cols="6" md="3"
            ><v-text-field v-model="filters.data_fim" type="date" label="Data final" hide-details
          /></v-col>
          <v-col cols="12" md="6" class="d-flex justify-end ga-2"
            ><v-btn variant="text" @click="clearFilters">Limpar</v-btn
            ><v-btn color="primary" prepend-icon="mdi-magnify" type="submit">Filtrar</v-btn></v-col
          >
        </v-row>
      </v-form>
    </v-card>

    <v-card class="data-card">
      <v-progress-linear v-if="loading" color="primary" indeterminate />
      <v-table>
        <thead>
          <tr>
            <th>Data</th>
            <th>Movimento</th>
            <th>Produto</th>
            <th>Quantidade</th>
            <th>Preço da movimentação</th>
            <th>Responsável</th>
            <th>Observação</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="movement in items" :key="`${movement.tipo}-${movement.id}`">
            <td>{{ formatDateTime(movement.data_movimento) }}</td>
            <td>
              <v-chip
                :color="movement.tipo === 'entrada' ? 'success' : 'warning'"
                size="small"
                variant="tonal"
                :prepend-icon="movement.tipo === 'entrada' ? 'mdi-package-down' : 'mdi-package-up'"
                >{{ movement.tipo_movimento }}</v-chip
              >
            </td>
            <td>{{ movement.produto_nome ?? '—' }}</td>
            <td>{{ formatQuantity(movement.quantidade) }}</td>
            <td>
              <div>{{ formatCurrency(movement.preco) }}</div>
              <div class="text-caption text-medium-emphasis">
                {{ movement.tipo === 'entrada' ? 'Custo da entrada' : 'Preço da venda' }}
              </div>
            </td>
            <td>{{ movement.responsavel_email ?? '—' }}</td>
            <td>{{ movement.observacao ?? '—' }}</td>
          </tr>
          <EmptyTableRow
            v-if="!loading && items.length === 0"
            :columns="7"
            message="Nenhuma movimentação encontrada."
          />
        </tbody>
      </v-table>
      <v-divider />
      <PaginationControls v-model="page" :pages="pages" :total="total" />
    </v-card>
  </div>
</template>
