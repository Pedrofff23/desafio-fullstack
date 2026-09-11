<script lang="ts">
import { defineComponent } from 'vue';

import { transacoesApi } from '@/api/transacoes';
import ActiveStatusChip from '@/components/ActiveStatusChip.vue';
import PageHeader from '@/components/PageHeader.vue';
import SearchFilterCard from '@/components/SearchFilterCard.vue';
import SupplierInspectionDialog from '@/components/SupplierInspectionDialog.vue';
import type { Fornecedor } from '@/types/api';
import { getErrorMessage } from '@/utils/errors';
import { formatContact, formatDateTime } from '@/utils/formatters';
import { scrollToError } from '@/utils/scroll';

export default defineComponent({
  name: 'FornecedoresView',
  components: {
    ActiveStatusChip,
    PageHeader,
    SearchFilterCard,
    SupplierInspectionDialog
  },
  data() {
    return {
      items: [] as Fornecedor[],
      searchQuery: '',
      headers: [
        { title: 'Empresa', key: 'nome_empresa', sortable: false },
        { title: 'Contato', key: 'contato', sortable: false },
        { title: 'Cidade', key: 'cidade', sortable: false },
        { title: 'Situação', key: 'ativo', sortable: false },
        { title: 'Ações', key: 'actions', align: 'end' as const, sortable: false }
      ],
      pageSizeOptions: [10, 20, 50, 100],
      page: 1,
      size: 20,
      inspectDialog: false,
      selected: null as Fornecedor | null,
      loading: false,
      error: '',
      success: ''
    };
  },
  computed: {
    filteredItems(): Fornecedor[] {
      if (!this.searchQuery.trim()) return this.items;
      const query = this.searchQuery.toLowerCase().trim();
      return this.items.filter((item) => {
        const empresa = item.nome_empresa.toLowerCase();
        const cidade = item.endereco?.cidade?.nome?.toLowerCase() || '';
        const tel = `${item.contato?.ddd || ''}${item.contato?.numero || ''}`;
        return empresa.includes(query) || cidade.includes(query) || tel.includes(query);
      });
    }
  },
  watch: {
    searchQuery() {
      this.page = 1;
    },
    error(val: string) {
      if (val) {
        void scrollToError(this.$refs.pageErrorAlert as any);
      }
    }
  },
  mounted() {
    void this.load();
  },
  methods: {
    formatContact,
    formatDateTime,
    async load() {
      this.loading = true;
      this.error = '';
      try {
        this.items = await transacoesApi.fornecedores();
      } catch (error) {
        this.error = getErrorMessage(error);
      } finally {
        this.loading = false;
      }
    },
    search() {
      this.page = 1;
    },
    clearFilters() {
      this.searchQuery = '';
      this.page = 1;
    },
    inspect(supplier: Fornecedor) {
      this.selected = supplier;
      this.inspectDialog = true;
    },
    async remove(supplier: Fornecedor) {
      const confirmed = window.confirm(`Deseja excluir o fornecedor ${supplier.nome_empresa}?`);
      if (!confirmed) return;
      this.error = '';
      this.success = '';
      try {
        await transacoesApi.deleteFornecedor(supplier.id);
        this.success = 'Fornecedor excluído com sucesso.';
        await this.load();
      } catch (error) {
        this.error = getErrorMessage(error);
      }
    }
  }
});
</script>

<template>
  <div>
    <PageHeader title="Fornecedores" subtitle="Empresas disponíveis para registrar entradas.">
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-plus" to="/fornecedores/novo">Novo fornecedor</v-btn>
      </template>
    </PageHeader>
    <v-alert v-if="error" ref="pageErrorAlert" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
    <v-alert v-if="success" type="success" variant="tonal" closable class="mb-4" @click:close="success = ''">
      {{ success }}
    </v-alert>

    <SearchFilterCard
      v-model="searchQuery"
      label="Pesquisar fornecedor"
      placeholder="Nome da empresa, cidade ou telefone..."
      :loading="loading"
      @search="search"
      @clear="clearFilters"
    />

    <v-card class="data-card">
      <v-data-table
        v-model:page="page"
        v-model:items-per-page="size"
        :headers="headers"
        :items="filteredItems"
        :loading="loading"
        :items-per-page-options="pageSizeOptions"
        items-per-page-text="Itens por página:"
      >
        <template #item.nome_empresa="{ item }">
          <span class="font-weight-medium">{{ item.nome_empresa }}</span>
        </template>

        <template #item.contato="{ item }">
          {{ formatContact(item.contato) }}
        </template>

        <template #item.cidade="{ item }">
          {{ item.endereco.cidade.nome }}
        </template>

        <template #item.ativo="{ item }">
          <ActiveStatusChip :active="item.ativo" />
        </template>

        <template #item.actions="{ item }">
          <div class="d-flex align-center justify-end ga-1">
            <v-btn
              icon="mdi-information-outline"
              size="small"
              variant="text"
              title="Inspecionar fornecedor"
              @click="inspect(item)"
            />
            <v-btn
              icon="mdi-pencil-outline"
              size="small"
              variant="text"
              title="Editar fornecedor"
              :to="`/fornecedores/${item.id}/editar`"
            />
            <v-btn
              icon="mdi-delete-outline"
              color="error"
              size="small"
              variant="text"
              title="Excluir fornecedor"
              @click="remove(item)"
            />
          </div>
        </template>

        <template #no-data>
          <div class="pa-4 text-center text-medium-emphasis">
            {{ searchQuery ? 'Nenhum fornecedor encontrado para a pesquisa.' : 'Nenhum fornecedor cadastrado.' }}
          </div>
        </template>
      </v-data-table>
    </v-card>

    <SupplierInspectionDialog v-model="inspectDialog" :supplier="selected" />
  </div>
</template>
