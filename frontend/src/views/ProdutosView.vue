<script lang="ts">
import { defineComponent } from 'vue'

import { produtosApi, type ProdutoFilters } from '@/api/produtos'
import ActiveStatusChip from '@/components/ActiveStatusChip.vue'
import EmptyTableRow from '@/components/EmptyTableRow.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationControls from '@/components/PaginationControls.vue'
import ProductStatusChip from '@/components/ProductStatusChip.vue'
import type { Lote, LoteInput, Produto, ProdutoStatus } from '@/types/api'
import { getErrorMessage } from '@/utils/errors'
import { formatCurrency, formatDate, formatQuantity } from '@/utils/formatters'

function emptyLote(): LoteInput {
  return {
    numero_lote: '',
    data_producao: new Date().toISOString().slice(0, 10),
    data_validade: null,
    ativo: true,
  }
}

export default defineComponent({
  name: 'ProdutosView',
  components: {
    ActiveStatusChip,
    EmptyTableRow,
    PageHeader,
    PaginationControls,
    ProductStatusChip,
  },
  data() {
    return {
      items: [] as Produto[],
      filters: {
        nome: '',
        status: null as ProdutoStatus | null,
        preco_min: null as number | null,
        preco_max: null as number | null,
      },
      statusOptions: [
        { title: 'Normal', value: 'ok' },
        { title: 'Validade próxima', value: 'validade_proxima' },
        { title: 'Vencido', value: 'vencido' },
        { title: 'Estoque baixo', value: 'estoque_baixo' },
        { title: 'Sem estoque', value: 'zerado' },
      ],
      page: 1,
      size: 20,
      pages: 0,
      total: 0,
      loading: false,
      error: '',
      success: '',
      lotDialog: false,
      selectedProduct: null as Produto | null,
      lots: [] as Lote[],
      lotForm: emptyLote(),
      lotLoading: false,
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
    formatCurrency,
    formatDate,
    formatQuantity,
    async load() {
      this.loading = true
      this.error = ''
      const params: ProdutoFilters = { page: this.page, size: this.size }
      if (this.filters.nome) params.nome = this.filters.nome
      if (this.filters.status) params.status = this.filters.status
      if (this.filters.preco_min !== null) params.preco_min = this.filters.preco_min
      if (this.filters.preco_max !== null) params.preco_max = this.filters.preco_max
      try {
        const response = await produtosApi.listar(params)
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
      this.filters = { nome: '', status: null, preco_min: null, preco_max: null }
      this.search()
    },
    async remove(produto: Produto) {
      if (!window.confirm(`Deseja excluir o produto ${produto.nome}?`)) return
      this.error = ''
      try {
        await produtosApi.excluir(produto.id)
        this.success = 'Produto excluído com sucesso.'
        await this.load()
      } catch (error) {
        this.error = getErrorMessage(error)
      }
    },
    async openLots(produto: Produto) {
      this.selectedProduct = produto
      this.lotForm = emptyLote()
      this.lotDialog = true
      this.lotLoading = true
      try {
        this.lots = await produtosApi.listarLotes(produto.id)
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.lotLoading = false
      }
    },
    async createLot() {
      if (!this.selectedProduct || !this.lotForm.numero_lote || !this.lotForm.data_producao) {
        this.error = 'Informe o número e a data de produção do lote.'
        return
      }
      if (this.selectedProduct.perecivel && !this.lotForm.data_validade) {
        this.error = 'Produtos perecíveis exigem data de validade.'
        return
      }
      this.lotLoading = true
      this.error = ''
      try {
        await produtosApi.createLote(this.selectedProduct.id, this.lotForm)
        this.lots = await produtosApi.listarLotes(this.selectedProduct.id)
        this.lotForm = emptyLote()
        this.success = 'Lote cadastrado com sucesso.'
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.lotLoading = false
      }
    },
  },
})
</script>

<template>
  <div>
    <PageHeader
      title="Produtos e lotes"
      subtitle="Catálogo, preços, validade e situação do estoque."
    >
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-plus" to="/produtos/novo">Novo produto</v-btn>
      </template>
    </PageHeader>

    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      closable
      class="mb-4"
      @click:close="error = ''"
      >{{ error }}</v-alert
    >
    <v-alert
      v-if="success"
      type="success"
      variant="tonal"
      closable
      class="mb-4"
      @click:close="success = ''"
      >{{ success }}</v-alert
    >

    <v-card class="data-card pa-4 mb-4">
      <v-form @submit.prevent="search">
        <v-row align="center">
          <v-col cols="12" md="4"
            ><v-text-field
              v-model.trim="filters.nome"
              label="Nome do produto"
              hide-details
              clearable
          /></v-col>
          <v-col cols="12" md="3"
            ><v-select
              v-model="filters.status"
              :items="statusOptions"
              label="Status"
              hide-details
              clearable
          /></v-col>
          <v-col cols="6" md="2"
            ><v-text-field
              v-model.number="filters.preco_min"
              type="number"
              min="0"
              step="0.01"
              label="Preço mín."
              hide-details
          /></v-col>
          <v-col cols="6" md="2"
            ><v-text-field
              v-model.number="filters.preco_max"
              type="number"
              min="0"
              step="0.01"
              label="Preço máx."
              hide-details
          /></v-col>
          <v-col cols="12" md="1" class="d-flex ga-1">
            <v-btn icon="mdi-magnify" color="primary" type="submit" title="Pesquisar" />
            <v-btn
              icon="mdi-filter-off-outline"
              variant="text"
              title="Limpar filtros"
              @click="clearFilters"
            />
          </v-col>
        </v-row>
      </v-form>
    </v-card>

    <v-card class="data-card">
      <v-progress-linear v-if="loading" color="primary" indeterminate />
      <v-table>
        <thead>
          <tr>
            <th>Produto</th>
            <th>Preço</th>
            <th>Validade</th>
            <th>Saldo</th>
            <th>Status</th>
            <th class="text-right">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="produto in items" :key="produto.id">
            <td>
              <div class="font-weight-medium">{{ produto.nome }}</div>
              <div class="text-caption text-medium-emphasis">{{ produto.codigo }}</div>
            </td>
            <td>{{ formatCurrency(produto.preco) }}</td>
            <td>{{ formatDate(produto.data_validade) }}</td>
            <td>{{ formatQuantity(produto.quantidade_estoque) }}</td>
            <td><ProductStatusChip :status="produto.status" /></td>
            <td>
              <div class="table-actions">
                <v-btn
                  icon="mdi-package-variant-closed"
                  size="small"
                  variant="text"
                  title="Lotes"
                  @click="openLots(produto)"
                />
                <v-btn
                  :to="`/produtos/${produto.id}/editar`"
                  icon="mdi-pencil-outline"
                  size="small"
                  variant="text"
                  title="Editar"
                />
                <v-btn
                  icon="mdi-delete-outline"
                  size="small"
                  variant="text"
                  color="error"
                  title="Excluir"
                  @click="remove(produto)"
                />
              </div>
            </td>
          </tr>
          <EmptyTableRow
            v-if="!loading && items.length === 0"
            :columns="6"
            message="Nenhum produto encontrado."
          />
        </tbody>
      </v-table>
      <v-divider />
      <PaginationControls v-model="page" :pages="pages" :total="total" />
    </v-card>

    <v-dialog v-model="lotDialog" max-width="760">
      <v-card>
        <v-card-title class="pa-5">Lotes de {{ selectedProduct?.nome }}</v-card-title>
        <v-card-text>
          <v-progress-linear v-if="lotLoading" color="primary" indeterminate class="mb-4" />
          <v-table density="compact" class="mb-5">
            <thead>
              <tr>
                <th>Lote</th>
                <th>Produção</th>
                <th>Validade</th>
                <th>Situação</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="lot in lots" :key="lot.id">
                <td>{{ lot.numero_lote }}</td>
                <td>{{ formatDate(lot.data_producao) }}</td>
                <td>{{ formatDate(lot.data_validade) }}</td>
                <td><ActiveStatusChip :active="lot.ativo" /></td>
              </tr>
              <tr v-if="lots.length === 0">
                <td colspan="4" class="text-center text-medium-emphasis py-4">
                  Nenhum lote cadastrado.
                </td>
              </tr>
            </tbody>
          </v-table>
          <div class="text-subtitle-1 font-weight-bold mb-3">Cadastrar lote</div>
          <v-row>
            <v-col cols="12" md="5"
              ><v-text-field v-model.trim="lotForm.numero_lote" label="Número do lote"
            /></v-col>
            <v-col cols="6" md="3"
              ><v-text-field v-model="lotForm.data_producao" type="date" label="Produção"
            /></v-col>
            <v-col cols="6" md="4"
              ><v-text-field
                v-model="lotForm.data_validade"
                type="date"
                label="Validade"
                :required="selectedProduct?.perecivel"
            /></v-col>
          </v-row>
        </v-card-text>
        <v-card-actions class="pa-5 pt-0"
          ><v-spacer /><v-btn variant="text" @click="lotDialog = false">Fechar</v-btn
          ><v-btn color="primary" :loading="lotLoading" @click="createLot"
            >Cadastrar lote</v-btn
          ></v-card-actions
        >
      </v-card>
    </v-dialog>
  </div>
</template>
