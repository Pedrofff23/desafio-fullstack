<script lang="ts">
import { defineComponent } from 'vue';

import { produtosApi, type ProdutoFilters } from '@/api/produtos';
import ActiveStatusChip from '@/components/ActiveStatusChip.vue';
import EmptyTableRow from '@/components/EmptyTableRow.vue';
import LotExpirationChip from '@/components/LotExpirationChip.vue';
import PageHeader from '@/components/PageHeader.vue';
import PaginationControls from '@/components/PaginationControls.vue';
import ProductInspectionDialog from '@/components/ProductInspectionDialog.vue';
import ProductStatusChip from '@/components/ProductStatusChip.vue';
import SearchFilterCard from '@/components/SearchFilterCard.vue';
import type { CatalogoProduto, Lote, LoteInput, LoteValidadeStatus, Produto, ProdutoStatus } from '@/types/api';
import { getErrorMessage } from '@/utils/errors';
import { formatCurrency, formatDate, formatQuantity } from '@/utils/formatters';

type LotFilter = 'todos' | 'com_estoque' | LoteValidadeStatus;

function emptyLote(): LoteInput {
  return {
    numero_lote: '',
    data_producao: new Date().toISOString().slice(0, 10),
    data_validade: null,
    ativo: true
  };
}

export default defineComponent({
  name: 'ProdutosView',
  components: {
    ActiveStatusChip,
    LotExpirationChip,
    PageHeader,
    PaginationControls,
    ProductInspectionDialog,
    ProductStatusChip,
    SearchFilterCard
  },
  data() {
    return {
      items: [] as Produto[],
      filters: {
        nome: '',
        status: null as ProdutoStatus | null,
        preco_min: null as number | null,
        preco_max: null as number | null
      },
      statusOptions: [
        { title: 'Estoque normal', value: 'ok' },
        { title: 'Estoque baixo', value: 'estoque_baixo' },
        { title: 'Sem estoque', value: 'zerado' }
      ],
      headers: [
        { title: 'Produto', key: 'nome', sortable: false },
        { title: 'Preço', key: 'preco', sortable: false },
        { title: 'Quantidade em estoque', key: 'quantidade_estoque', sortable: false },
        { title: 'Lotes', key: 'total_lotes', align: 'center' as const, sortable: false },
        { title: 'Status do estoque', key: 'status', sortable: false },
        { title: 'Ações', key: 'actions', align: 'end' as const, sortable: false }
      ],
      pageSizeOptions: [10, 20, 50, 100],
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
      lotFilter: 'todos' as LotFilter,
      lotFilterOptions: [
        { label: 'Todos', value: 'todos' },
        { label: 'Com estoque', value: 'com_estoque' },
        { label: 'Próximos do vencimento', value: 'validade_proxima' },
        { label: 'Vencidos', value: 'vencido' }
      ] as Array<{ label: string; value: LotFilter }>,
      lotForm: emptyLote(),
      lotLoading: false,
      editingLotId: null as number | null,
      lotPage: 1,
      lotSize: 10,
      inspectDialog: false,
      inspectedProduct: null as Produto | null,
      inspectCatalog: null as CatalogoProduto | null,
      inspectLoading: false
    };
  },
  computed: {
    filteredLots(): Lote[] {
      if (this.lotFilter === 'todos') return this.lots;
      if (this.lotFilter === 'com_estoque') {
        return this.lots.filter((lot) => lot.quantidade_estoque > 0);
      }
      return this.lots.filter((lot) => lot.quantidade_estoque > 0 && lot.status_validade === this.lotFilter);
    },
    lotTotal(): number {
      return this.filteredLots.length;
    },
    lotPages(): number {
      return Math.ceil(this.lotTotal / this.lotSize) || 1;
    },
    paginatedLots(): Lote[] {
      const start = (this.lotPage - 1) * this.lotSize;
      return this.filteredLots.slice(start, start + this.lotSize);
    }
  },
  watch: {
    lotFilter() {
      this.lotPage = 1;
    }
  },
  methods: {
    formatCurrency,
    formatDate,
    formatQuantity,
    lotRowClass(lot: Lote): string {
      if (lot.quantidade_estoque <= 0) return 'lot-row--empty';
      if (lot.status_validade === 'vencido') return 'lot-row--expired';
      if (lot.status_validade === 'validade_proxima') return 'lot-row--expiring';
      return '';
    },
    expirationDays(lot: Lote): string {
      if (lot.quantidade_estoque <= 0) return '—';
      if (lot.dias_para_vencer === null) return '—';
      if (lot.dias_para_vencer < 0) {
        const days = Math.abs(lot.dias_para_vencer);
        return `Vencido há ${days} ${days === 1 ? 'dia' : 'dias'}`;
      }
      if (lot.dias_para_vencer === 0) return 'Vence hoje';
      return `${lot.dias_para_vencer} ${lot.dias_para_vencer === 1 ? 'dia' : 'dias'}`;
    },
    lotLocations(lot: Lote): string {
      if (lot.localizacoes.length === 0) return 'Sem estoque localizado';
      return lot.localizacoes
        .map((location) => {
          const level = location.nivel ? ` / Nível ${location.nivel}` : '';
          return `${location.corredor} / ${location.seccao} / ${location.prateleira}${level} (${formatQuantity(location.quantidade)})`;
        })
        .join('; ');
    },
    async load(page?: number, size?: number) {
      this.loading = true;
      this.error = '';
      if (page !== undefined) this.page = page;
      if (size !== undefined) this.size = size;
      const params: ProdutoFilters = { page: this.page, size: this.size };
      if (this.filters.nome) params.nome = this.filters.nome;
      if (this.filters.status) params.status = this.filters.status;
      if (this.filters.preco_min !== null) params.preco_min = this.filters.preco_min;
      if (this.filters.preco_max !== null) params.preco_max = this.filters.preco_max;
      try {
        const response = await produtosApi.listar(params);
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
      this.filters = { nome: '', status: null, preco_min: null, preco_max: null };
      this.search();
    },
    async remove(produto: Produto) {
      if (!window.confirm(`Deseja excluir o produto ${produto.nome}?`)) return;
      this.error = '';
      try {
        await produtosApi.delete(produto.id);
        this.success = 'Produto excluído com sucesso.';
        await this.load();
      } catch (error) {
        this.error = getErrorMessage(error);
      }
    },
    async openLots(produto: Produto) {
      this.selectedProduct = produto;
      this.lotForm = emptyLote();
      this.lotFilter = 'todos';
      this.lotPage = 1;
      this.lotDialog = true;
      this.lotLoading = true;
      try {
        this.lots = await produtosApi.listarLotes(produto.id);
      } catch (error) {
        this.error = getErrorMessage(error);
      } finally {
        this.lotLoading = false;
      }
    },
    async inspectProduct(produto: Produto) {
      this.inspectDialog = true;
      this.inspectLoading = true;
      try {
        const [detail, catalog] = await Promise.all([produtosApi.get(produto.id), produtosApi.catalogo()]);
        this.inspectedProduct = detail;
        this.inspectCatalog = catalog;
      } catch (error) {
        this.error = getErrorMessage(error);
        this.inspectDialog = false;
      } finally {
        this.inspectLoading = false;
      }
    },
    editLot(lot: Lote) {
      this.editingLotId = lot.id;
      this.lotForm = {
        numero_lote: lot.numero_lote,
        data_producao: lot.data_producao,
        data_validade: lot.data_validade,
        ativo: lot.ativo
      };
    },
    cancelLotEdit() {
      this.editingLotId = null;
      this.lotForm = emptyLote();
    },
    async removeLot(lot: Lote) {
      if (!this.selectedProduct || !window.confirm(`Deseja excluir o lote ${lot.numero_lote}?`)) return;
      this.lotLoading = true;
      this.error = '';
      try {
        await produtosApi.deleteLote(this.selectedProduct.id, lot.id);
        this.lots = await produtosApi.listarLotes(this.selectedProduct.id);
        if (this.lotPage > this.lotPages) {
          this.lotPage = Math.max(this.lotPages, 1);
        }
        this.success = 'Lote excluído com sucesso.';
        await this.load();
      } catch (error) {
        this.error = getErrorMessage(error);
      } finally {
        this.lotLoading = false;
      }
    },
    async createLot() {
      if (!this.selectedProduct || !this.lotForm.numero_lote || !this.lotForm.data_producao) {
        this.error = 'Informe o número e a data de produção do lote.';
        return;
      }
      if (this.selectedProduct.perecivel && !this.lotForm.data_validade) {
        this.error = 'Produtos perecíveis exigem data de validade.';
        return;
      }
      this.lotLoading = true;
      this.error = '';
      try {
        if (this.editingLotId) await produtosApi.updateLote(this.selectedProduct.id, this.editingLotId, this.lotForm);
        else await produtosApi.createLote(this.selectedProduct.id, this.lotForm);
        this.lots = await produtosApi.listarLotes(this.selectedProduct.id);
        if (this.selectedProduct) {
          this.selectedProduct.total_lotes = this.lots.length;
        }
        this.lotForm = emptyLote();
        this.success = this.editingLotId ? 'Lote atualizado com sucesso.' : 'Lote cadastrado com sucesso.';
        this.editingLotId = null;
        await this.load();
      } catch (error) {
        this.error = getErrorMessage(error);
      } finally {
        this.lotLoading = false;
      }
    }
  }
});
</script>

<template>
  <div>
    <PageHeader title="Produtos e lotes" subtitle="Catálogo, preços, validade e situação do estoque.">
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-plus" to="/produtos/novo">Novo produto</v-btn>
      </template>
    </PageHeader>

    <v-alert v-if="error" type="error" variant="tonal" closable class="mb-4" @click:close="error = ''">{{ error }}</v-alert>
    <v-alert v-if="success" type="success" variant="tonal" closable class="mb-4" @click:close="success = ''">
      {{ success }}
    </v-alert>

    <SearchFilterCard
      v-model="filters.nome"
      label="Nome do produto"
      placeholder="Digite o nome do produto..."
      :loading="loading"
      :md="4"
      @search="search"
      @clear="clearFilters"
    >
      <v-col cols="12" md="3">
        <v-select v-model="filters.status" :items="statusOptions" label="Status" hide-details clearable />
      </v-col>
      <v-col cols="6" md="2">
        <v-text-field v-model.number="filters.preco_min" type="number" min="0" step="0.01" label="Preço mín." hide-details />
      </v-col>
      <v-col cols="6" md="2">
        <v-text-field v-model.number="filters.preco_max" type="number" min="0" step="0.01" label="Preço máx." hide-details />
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
        <template #item.nome="{ item }">
          <div class="font-weight-medium">{{ item.nome }}</div>
          <div class="text-caption text-medium-emphasis">{{ item.codigo }}</div>
        </template>

        <template #item.preco="{ item }">
          {{ formatCurrency(item.preco) }}
        </template>

        <template #item.quantidade_estoque="{ item }">
          {{ formatQuantity(item.quantidade_estoque) }}
        </template>

        <template #item.total_lotes="{ item }">
          <v-chip size="small" variant="tonal" :color="item.total_lotes > 0 ? 'primary' : 'grey'">
            {{ item.total_lotes }} {{ item.total_lotes === 1 ? 'lote' : 'lotes' }}
          </v-chip>
        </template>

        <template #item.status="{ item }">
          <ProductStatusChip :status="item.status" />
        </template>

        <template #item.actions="{ item }">
          <div class="d-flex align-center justify-end ga-1">
            <v-btn
              icon="mdi-information-outline"
              size="small"
              variant="text"
              title="Inspecionar produto"
              @click="inspectProduct(item)"
            />
            <v-btn
              icon="mdi-package-variant-closed"
              size="small"
              variant="text"
              title="Visualizar lotes"
              @click="openLots(item)"
            />
            <v-btn
              :to="`/produtos/${item.id}/editar`"
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
              @click="remove(item)"
            />
          </div>
        </template>

        <template #no-data>
          <div class="pa-4 text-center text-medium-emphasis">
            Nenhum produto encontrado.
          </div>
        </template>
      </v-data-table-server>
    </v-card>

    <v-dialog v-model="lotDialog" max-width="1180">
      <v-card>
        <v-card-title class="pa-5">
          Lotes de {{ selectedProduct?.nome }}
          <span class="text-medium-emphasis text-body-1 font-weight-regular">
            ({{ selectedProduct?.total_lotes ?? lots.length }}
            {{ (selectedProduct?.total_lotes ?? lots.length) === 1 ? 'lote' : 'lotes' }})
          </span>
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
          <v-table density="compact" class="mb-5">
            <thead>
              <tr>
                <th>Lote</th>
                <th>Produção</th>
                <th>Validade</th>
                <th>Status da validade</th>
                <th>Prazo</th>
                <th>Saldo</th>
                <th>Localização</th>
                <th>Cadastro</th>
                <th class="text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="lot in paginatedLots" :key="lot.id" :class="lotRowClass(lot)">
                <td>{{ lot.numero_lote }}</td>
                <td>{{ formatDate(lot.data_producao) }}</td>
                <td>{{ formatDate(lot.data_validade) }}</td>
                <td>
                  <span v-if="lot.quantidade_estoque <= 0" class="text-medium-emphasis">—</span>
                  <LotExpirationChip v-else :status="lot.status_validade" />
                </td>
                <td>{{ expirationDays(lot) }}</td>
                <td>
                  <v-chip :color="lot.quantidade_estoque > 0 ? 'primary' : 'grey'" size="small" variant="tonal">
                    {{ formatQuantity(lot.quantidade_estoque) }}
                  </v-chip>
                </td>
                <td class="text-caption">{{ lotLocations(lot) }}</td>
                <td><ActiveStatusChip :active="lot.ativo" /></td>
                <td class="text-right text-no-wrap">
                  <v-btn icon="mdi-pencil-outline" size="small" variant="text" title="Editar lote" @click="editLot(lot)" />
                  <v-btn
                    icon="mdi-delete-outline"
                    color="error"
                    size="small"
                    variant="text"
                    title="Excluir lote"
                    @click="removeLot(lot)"
                  />
                </td>
              </tr>
              <tr v-if="filteredLots.length === 0">
                <td colspan="9" class="text-center text-medium-emphasis py-4">Nenhum lote encontrado para este filtro.</td>
              </tr>
            </tbody>
          </v-table>
          <PaginationControls
            v-if="filteredLots.length > 0"
            v-model="lotPage"
            :pages="lotPages"
            :total="lotTotal"
            class="pa-0 mb-5"
          />
          <div class="text-subtitle-1 font-weight-bold mb-3">{{ editingLotId ? 'Editar lote' : 'Cadastrar lote' }}</div>
          <v-row>
            <v-col cols="12" md="5">
              <v-text-field
                v-model.trim="lotForm.numero_lote"
                label="Número do lote"
                required
                :rules="[(v) => !!v || 'Número do lote é obrigatório']"
              />
            </v-col>
            <v-col cols="6" md="3">
              <v-text-field
                v-model="lotForm.data_producao"
                type="date"
                label="Produção"
                required
                :rules="[(v) => !!v || 'Produção é obrigatória']"
              />
            </v-col>
            <v-col cols="6" md="4">
              <v-text-field
                v-model="lotForm.data_validade"
                type="date"
                label="Validade"
                :required="selectedProduct?.perecivel"
                :rules="selectedProduct?.perecivel ? [(v) => !!v || 'Validade é obrigatória'] : []"
              />
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions class="pa-5 pt-0">
          <v-spacer />
          <v-btn v-if="editingLotId" variant="text" @click="cancelLotEdit">Cancelar edição</v-btn>
          <v-btn variant="text" @click="lotDialog = false">Fechar</v-btn>
          <v-btn color="primary" :loading="lotLoading" @click="createLot">
            {{ editingLotId ? 'Salvar lote' : 'Cadastrar lote' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <ProductInspectionDialog
      v-model="inspectDialog"
      :product="inspectedProduct"
      :catalog="inspectCatalog"
      :loading="inspectLoading"
    />
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
</style>
