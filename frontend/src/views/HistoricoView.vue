<script lang="ts">
import { defineComponent } from 'vue';

import { listAllPages } from '@/api/pagination';
import { produtosApi } from '@/api/produtos';
import { transacoesApi, type HistoricoFilters } from '@/api/transacoes';
import { usuariosApi } from '@/api/usuarios';
import PageHeader from '@/components/PageHeader.vue';
import SearchFilterCard from '@/components/SearchFilterCard.vue';
import type { Movimento, Produto, Usuario } from '@/types/api';
import { getErrorMessage } from '@/utils/errors';
import { formatCurrency, formatDateTime, formatQuantity } from '@/utils/formatters';
import { scrollToError } from '@/utils/scroll';

export default defineComponent({
  name: 'HistoricoView',
  components: { PageHeader, SearchFilterCard },
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
        data_fim: ''
      },
      headers: [
        { title: 'Data', key: 'data_movimento', sortable: false },
        { title: 'Movimento', key: 'tipo_movimento', sortable: false },
        { title: 'Produto', key: 'produto_nome', sortable: false },
        { title: 'Quantidade', key: 'quantidade', sortable: false },
        { title: 'Preço da movimentação', key: 'preco', sortable: false },
        { title: 'Responsável', key: 'responsavel_email', sortable: false },
        { title: 'Observação', key: 'observacao', sortable: false }
      ],
      pageSizeOptions: [10, 20, 50, 100],
      page: 1,
      size: 20,
      pages: 0,
      total: 0,
      loading: false,
      error: ''
    };
  },
  computed: {
    userOptions(): Array<{ title: string; value: number }> {
      return this.users.map((user) => ({
        title: `${user.funcionario.nome_completo} · ${user.email}`,
        value: user.funcionario.id
      }));
    }
  },
  watch: {
    error(val: string) {
      if (val) {
        void scrollToError(this.$refs.errorAlert as any);
      }
    }
  },
  async mounted() {
    try {
      const [products, users] = await Promise.all([listAllPages(produtosApi.listar), listAllPages(usuariosApi.listar)]);
      this.products = products;
      this.users = users;
    } catch (error) {
      this.error = getErrorMessage(error);
    }
  },
  methods: {
    formatCurrency,
    formatDateTime,
    formatQuantity,
    async load(page?: number, size?: number) {
      this.loading = true;
      this.error = '';
      if (page !== undefined) this.page = page;
      if (size !== undefined) this.size = size;
      const params: HistoricoFilters = { page: this.page, size: this.size };
      if (this.filters.produto_id) params.produto_id = this.filters.produto_id;
      if (this.filters.tipo) params.tipo = this.filters.tipo;
      if (this.filters.funcionario_id) params.funcionario_id = this.filters.funcionario_id;
      if (this.filters.quantidade !== null) params.quantidade = this.filters.quantidade;
      if (this.filters.data_inicio) params.data_inicio = `${this.filters.data_inicio}T00:00:00`;
      if (this.filters.data_fim) params.data_fim = `${this.filters.data_fim}T23:59:59`;
      try {
        const response = await transacoesApi.historico(params);
        this.items = response.items;
        this.pages = response.pages;
        this.total = response.total;
      } catch (error) {
        this.error = getErrorMessage(error);
      } finally {
        this.loading = false;
      }
    },
    onOptionsUpdate(options: { page: number; itemsPerPage: number }) {
      void this.load(options.page, options.itemsPerPage);
    },
    search() {
      this.page = 1;
      void this.load(1, this.size);
    },
    clearFilters() {
      this.filters = {
        produto_id: null,
        tipo: null,
        funcionario_id: null,
        quantidade: null,
        data_inicio: '',
        data_fim: ''
      };
      this.search();
    }
  }
});
</script>

<template>
  <div>
    <PageHeader title="Histórico de movimentações" subtitle="Auditoria de entradas e saídas, sem alteração ou exclusão." />
    <v-alert v-if="error" ref="errorAlert" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>

    <SearchFilterCard grid hide-search-input :loading="loading" @search="search" @clear="clearFilters">
      <v-col cols="12" md="4">
        <v-autocomplete
          v-model="filters.produto_id"
          :items="products"
          item-title="nome"
          item-value="id"
          label="Produto"
          clearable
          hide-details
        />
      </v-col>
      <v-col cols="6" md="2">
        <v-select
          v-model="filters.tipo"
          :items="[
            { title: 'Entrada', value: 'entrada' },
            { title: 'Saída', value: 'saida' }
          ]"
          label="Movimento"
          clearable
          hide-details
        />
      </v-col>
      <v-col cols="6" md="2">
        <v-text-field
          v-model.number="filters.quantidade"
          type="number"
          min="0.001"
          step="0.001"
          label="Quantidade"
          hide-details
        />
      </v-col>
      <v-col cols="12" md="4">
        <v-autocomplete v-model="filters.funcionario_id" :items="userOptions" label="Responsável" clearable hide-details />
      </v-col>
      <v-col cols="6" md="3">
        <v-text-field v-model="filters.data_inicio" type="date" label="Data inicial" hide-details />
      </v-col>
      <v-col cols="6" md="3">
        <v-text-field v-model="filters.data_fim" type="date" label="Data final" hide-details />
      </v-col>
    </SearchFilterCard>

    <v-card class="data-card">
      <v-data-table-server
        v-model:page="page"
        v-model:items-per-page="size"
        :headers="headers"
        :items="items"
        :items-length="total"
        :loading="loading"
        :items-per-page-options="pageSizeOptions"
        items-per-page-text="Itens por página:"
        @update:options="onOptionsUpdate"
      >
        <template #item.data_movimento="{ item }">
          {{ formatDateTime(item.data_movimento) }}
        </template>

        <template #item.tipo_movimento="{ item }">
          <v-chip
            :color="item.tipo === 'entrada' ? 'success' : 'warning'"
            size="small"
            variant="tonal"
            :prepend-icon="item.tipo === 'entrada' ? 'mdi-package-down' : 'mdi-package-up'"
          >
            {{ item.tipo_movimento }}
          </v-chip>
        </template>

        <template #item.produto_nome="{ item }">
          {{ item.produto_nome ?? '—' }}
        </template>

        <template #item.quantidade="{ item }">
          {{ formatQuantity(item.quantidade) }}
        </template>

        <template #item.preco="{ item }">
          <div>{{ formatCurrency(item.preco) }}</div>
          <div class="text-caption text-medium-emphasis">
            {{ item.tipo === 'entrada' ? 'Custo da entrada' : 'Preço da venda' }}
          </div>
        </template>

        <template #item.responsavel_email="{ item }">
          {{ item.responsavel_email ?? '—' }}
        </template>

        <template #item.observacao="{ item }">
          {{ item.observacao ?? '—' }}
        </template>

        <template #no-data>
          <div class="pa-4 text-center text-medium-emphasis">Nenhuma movimentação encontrada.</div>
        </template>
      </v-data-table-server>
    </v-card>
  </div>
</template>
