<script lang="ts">
import { defineComponent } from 'vue'

import { produtosApi } from '@/api/produtos'
import { transacoesApi } from '@/api/transacoes'
import ActiveStatusChip from '@/components/ActiveStatusChip.vue'
import EmptyTableRow from '@/components/EmptyTableRow.vue'
import LotExpirationChip from '@/components/LotExpirationChip.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationControls from '@/components/PaginationControls.vue'
import type { EstoqueProduto, Lote, LoteValidadeStatus } from '@/types/api'
import { getErrorMessage } from '@/utils/errors'
import { formatDate, formatQuantity } from '@/utils/formatters'

type LotFilter = 'todos' | 'com_estoque' | LoteValidadeStatus

export default defineComponent({
  name: 'EstoqueView',
  components: {
    ActiveStatusChip,
    EmptyTableRow,
    LotExpirationChip,
    PageHeader,
    PaginationControls,
  },
  data() {
    return {
      items: [] as EstoqueProduto[],
      page: 1,
      size: 20,
      pages: 0,
      total: 0,
      loading: false,
      error: '',
      lotDialog: false,
      lotLoading: false,
      selectedProduct: null as EstoqueProduto | null,
      lots: [] as Lote[],
      lotFilter: 'todos' as LotFilter,
      lotFilterOptions: [
        { label: 'Todos', value: 'todos' },
        { label: 'Com estoque', value: 'com_estoque' },
        { label: 'Próximos do vencimento', value: 'validade_proxima' },
        { label: 'Vencidos', value: 'vencido' },
      ] as Array<{ label: string; value: LotFilter }>,
    }
  },
  computed: {
    filteredLots(): Lote[] {
      if (this.lotFilter === 'todos') return this.lots
      if (this.lotFilter === 'com_estoque') {
        return this.lots.filter((lot) => lot.status_estoque === 'com_estoque')
      }
      return this.lots.filter((lot) => lot.status_validade === this.lotFilter)
    },
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
    formatDate,
    formatQuantity,
    lotRowClass(lot: Lote): string {
      if (lot.status_estoque === 'sem_estoque') return 'lot-row--empty'
      if (lot.status_validade === 'vencido') return 'lot-row--expired'
      if (lot.status_validade === 'validade_proxima') return 'lot-row--expiring'
      return ''
    },
    expirationDays(lot: Lote): string {
      if (lot.dias_para_vencer === null) return '—'
      if (lot.dias_para_vencer < 0) {
        const days = Math.abs(lot.dias_para_vencer)
        return `Vencido há ${days} ${days === 1 ? 'dia' : 'dias'}`
      }
      if (lot.dias_para_vencer === 0) return 'Vence hoje'
      return `${lot.dias_para_vencer} ${lot.dias_para_vencer === 1 ? 'dia' : 'dias'}`
    },
    lotLocations(lot: Lote): string {
      if (lot.localizacoes.length === 0) return 'Sem estoque localizado'
      return lot.localizacoes
        .map((location) => {
          const level = location.nivel ? ` / Nível ${location.nivel}` : ''
          const description = location.descricao ? ` · ${location.descricao}` : ''
          return `${location.corredor} / ${location.seccao} / ${location.prateleira}${level}${description} (${formatQuantity(location.quantidade)})`
        })
        .join('; ')
    },
    async openLots(item: EstoqueProduto) {
      this.selectedProduct = item
      this.lots = []
      this.lotFilter = 'todos'
      this.lotDialog = true
      await this.loadLots()
    },
    async loadLots() {
      if (!this.selectedProduct) return
      this.lotLoading = true
      this.error = ''
      try {
        this.lots = await produtosApi.listarLotes(this.selectedProduct.produto_id)
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.lotLoading = false
      }
    },
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
    <PageHeader
      title="Estoque atual"
      subtitle="Saldo consolidado dos produtos e inspeção completa dos seus lotes."
    >
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
            <th class="text-right">Lotes</th>
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
            <td class="text-right">
              <v-btn
                prepend-icon="mdi-package-variant-closed"
                size="small"
                variant="tonal"
                @click="openLots(item)"
              >
                Visualizar lotes
              </v-btn>
            </td>
          </tr>
          <EmptyTableRow
            v-if="!loading && items.length === 0"
            :columns="3"
            message="Nenhum produto cadastrado."
          />
        </tbody>
      </v-table>
      <v-divider />
      <PaginationControls v-model="page" :pages="pages" :total="total" />
    </v-card>

    <v-dialog v-model="lotDialog" max-width="1280">
      <v-card>
        <v-card-title class="d-flex align-center pa-5">
          <div>
            <div>Lotes de {{ selectedProduct?.produto_nome }}</div>
            <div class="text-caption text-medium-emphasis font-weight-regular">
              Saldo total do produto: {{ formatQuantity(selectedProduct?.quantidade) }}
            </div>
          </div>
          <v-spacer />
          <v-btn
            icon="mdi-refresh"
            size="small"
            variant="text"
            title="Atualizar lotes"
            :loading="lotLoading"
            @click="loadLots"
          />
        </v-card-title>
        <v-card-text>
          <v-progress-linear v-if="lotLoading" color="primary" indeterminate class="mb-4" />

          <div class="d-flex flex-wrap ga-2 mb-4">
            <v-btn
              v-for="option in lotFilterOptions"
              :key="option.value"
              size="small"
              :variant="lotFilter === option.value ? 'flat' : 'outlined'"
              :color="lotFilter === option.value ? 'primary' : undefined"
              @click="lotFilter = option.value"
            >
              {{ option.label }}
            </v-btn>
          </div>

          <v-table density="compact">
            <thead>
              <tr>
                <th>Lote</th>
                <th>Produção</th>
                <th>Validade</th>
                <th>Status da validade</th>
                <th>Prazo</th>
                <th>Saldo</th>
                <th>Status do estoque</th>
                <th>Localização e saldo</th>
                <th>Cadastro</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="lot in filteredLots" :key="lot.id" :class="lotRowClass(lot)">
                <td>
                  <div class="font-weight-medium">{{ lot.numero_lote }}</div>
                  <div class="text-caption text-medium-emphasis">ID {{ lot.id }}</div>
                </td>
                <td>{{ formatDate(lot.data_producao) }}</td>
                <td>{{ formatDate(lot.data_validade) }}</td>
                <td><LotExpirationChip :status="lot.status_validade" /></td>
                <td>{{ expirationDays(lot) }}</td>
                <td>{{ formatQuantity(lot.quantidade_estoque) }}</td>
                <td>
                  <v-chip
                    :color="lot.status_estoque === 'com_estoque' ? 'primary' : 'grey'"
                    size="small"
                    variant="tonal"
                  >
                    {{ lot.status_estoque === 'com_estoque' ? 'Com estoque' : 'Sem estoque' }}
                  </v-chip>
                </td>
                <td class="text-caption lot-location">{{ lotLocations(lot) }}</td>
                <td><ActiveStatusChip :active="lot.ativo" /></td>
              </tr>
              <tr v-if="!lotLoading && filteredLots.length === 0">
                <td colspan="9" class="text-center text-medium-emphasis py-6">
                  Nenhum lote encontrado para este filtro.
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
        <v-card-actions class="pa-5 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="lotDialog = false">Fechar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.lot-row--expired {
  background-color: rgba(211, 47, 47, 0.08);
}

.lot-row--expiring {
  background-color: rgba(251, 140, 0, 0.1);
}

.lot-row--empty {
  opacity: 0.68;
}

.lot-location {
  min-width: 220px;
  white-space: normal;
}
</style>
