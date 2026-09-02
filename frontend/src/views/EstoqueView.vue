<script lang="ts">
import { defineComponent } from 'vue'

import { transacoesApi } from '@/api/transacoes'
import EmptyTableRow from '@/components/EmptyTableRow.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationControls from '@/components/PaginationControls.vue'
import type { EstoqueProduto } from '@/types/api'
import { getErrorMessage } from '@/utils/errors'
import { formatQuantity } from '@/utils/formatters'

export default defineComponent({
  name: 'EstoqueView',
  components: { EmptyTableRow, PageHeader, PaginationControls },
  data() {
    return {
      items: [] as EstoqueProduto[],
      page: 1,
      size: 20,
      pages: 0,
      total: 0,
      loading: false,
      error: '',
    }
  },
  watch: {
    page() {
      void this.load()
    },
  },
  mounted() {
    void this.load()
  },
  methods: {
    formatQuantity,
    async load() {
      this.loading = true
      this.error = ''
      try {
        const response = await transacoesApi.estoque(this.page, this.size)
        this.items = response.items
        this.pages = response.pages
        this.total = response.total
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.loading = false
      }
    },
  },
})
</script>

<template>
  <div>
    <PageHeader title="Estoque atual" subtitle="Saldo consolidado de todos os produtos cadastrados.">
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-refresh" :loading="loading" @click="load">
          Atualizar
        </v-btn>
      </template>
    </PageHeader>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>

    <v-card class="data-card">
      <v-progress-linear v-if="loading" color="primary" indeterminate />
      <v-table>
        <thead>
          <tr>
            <th>Produto</th>
            <th class="text-right">Quantidade disponível</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.produto_id">
            <td class="font-weight-medium">{{ item.produto_nome }}</td>
            <td class="text-right">
              <v-chip :color="item.quantidade <= 0 ? 'error' : 'primary'" variant="tonal">
                {{ formatQuantity(item.quantidade) }}
              </v-chip>
            </td>
          </tr>
          <EmptyTableRow
            v-if="!loading && items.length === 0"
            :columns="2"
            message="Nenhum produto cadastrado."
          />
        </tbody>
      </v-table>
      <v-divider />
      <PaginationControls v-model="page" :pages="pages" :total="total" />
    </v-card>
  </div>
</template>
