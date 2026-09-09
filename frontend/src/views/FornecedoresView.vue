<script lang="ts">
import { defineComponent } from 'vue';

import { transacoesApi } from '@/api/transacoes';
import ActiveStatusChip from '@/components/ActiveStatusChip.vue';
import AddressFields from '@/components/AddressFields.vue';
import ContactFields from '@/components/ContactFields.vue';
import PageHeader from '@/components/PageHeader.vue';
import SearchFilterCard from '@/components/SearchFilterCard.vue';
import type { Fornecedor, FornecedorCreate } from '@/types/api';
import { getErrorMessage } from '@/utils/errors';
import { formatContact, formatDateTime } from '@/utils/formatters';
import { createAddressInput, createContactInput, normalizeAddressInput, normalizeContactInput } from '@/utils/formFields';

function emptyForm(): FornecedorCreate {
  return {
    nome_empresa: '',
    ativo: true,
    contato: createContactInput(),
    endereco: createAddressInput()
  };
}

export default defineComponent({
  name: 'FornecedoresView',
  components: {
    ActiveStatusChip,
    AddressFields,
    ContactFields,
    PageHeader,
    SearchFilterCard
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
      form: emptyForm(),
      dialog: false,
      inspectDialog: false,
      selected: null as Fornecedor | null,
      editingId: null as number | null,
      loading: false,
      saving: false,
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
    openForm() {
      this.editingId = null;
      this.form = emptyForm();
      this.dialog = true;
    },
    inspect(supplier: Fornecedor) {
      this.selected = supplier;
      this.inspectDialog = true;
    },
    edit(supplier: Fornecedor) {
      this.editingId = supplier.id;
      this.form = {
        nome_empresa: supplier.nome_empresa,
        ativo: supplier.ativo,
        contato: createContactInput(supplier.contato),
        endereco: createAddressInput(supplier.endereco)
      };
      this.dialog = true;
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
    },
    async submit() {
      if (!this.form.nome_empresa.trim()) {
        this.error = 'O nome da empresa é obrigatório.';
        return;
      }
      this.saving = true;
      this.error = '';
      this.success = '';
      try {
        const payload: FornecedorCreate = {
          nome_empresa: this.form.nome_empresa.trim(),
          ativo: this.form.ativo,
          contato: normalizeContactInput(this.form.contato),
          endereco: normalizeAddressInput(this.form.endereco)
        };
        if (this.editingId) {
          await transacoesApi.updateFornecedor(this.editingId, payload);
          this.success = 'Fornecedor atualizado com sucesso.';
        } else {
          await transacoesApi.createFornecedor(payload);
          this.success = 'Fornecedor cadastrado com sucesso.';
        }
        this.dialog = false;
        await this.load();
      } catch (error) {
        this.error = getErrorMessage(error);
      } finally {
        this.saving = false;
      }
    }
  }
});
</script>

<template>
  <div>
    <PageHeader title="Fornecedores" subtitle="Empresas disponíveis para registrar entradas.">
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openForm">Novo fornecedor</v-btn>
      </template>
    </PageHeader>
    <v-alert v-if="error && !dialog" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
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
            <v-btn icon="mdi-pencil-outline" size="small" variant="text" title="Editar fornecedor" @click="edit(item)" />
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

    <v-dialog v-model="dialog" max-width="900" persistent>
      <v-card>
        <v-card-title class="pa-5">{{ editingId ? 'Editar fornecedor' : 'Novo fornecedor' }}</v-card-title>
        <v-card-text>
          <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
          <v-form @submit.prevent="submit">
            <v-row>
              <v-col cols="12" md="8">
                <v-text-field
                  v-model.trim="form.nome_empresa"
                  label="Nome da empresa"
                  required
                  :rules="[(v) => !!v || 'Nome da empresa é obrigatório']"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-switch v-model="form.ativo" color="primary" label="Fornecedor ativo" inset />
              </v-col>
              <v-col cols="12"><ContactFields v-model="form.contato" /></v-col>
              <v-col cols="12"><v-divider class="my-2" /></v-col>
              <v-col cols="12"><AddressFields v-model="form.endereco" /></v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions class="pa-5 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="dialog = false">Cancelar</v-btn>
          <v-btn color="primary" :loading="saving" @click="submit">
            {{ editingId ? 'Salvar alterações' : 'Cadastrar' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="inspectDialog" max-width="700">
      <v-card v-if="selected">
        <v-card-title class="d-flex align-center pa-5">
          Fornecedor
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="inspectDialog = false" />
        </v-card-title>
        <v-card-text class="px-5">
          <v-row>
            <v-col cols="12" md="8">
              <div class="text-caption">Empresa</div>
              <strong>{{ selected.nome_empresa }}</strong>
            </v-col>
            <v-col cols="12" md="4">
              <ActiveStatusChip :active="selected.ativo" />
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption">Contato</div>
              {{ formatContact(selected.contato) }}
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption">Cadastro</div>
              {{ formatDateTime(selected.data_cadastro) }}
            </v-col>
            <v-col cols="12"><v-divider /></v-col>
            <v-col cols="12">
              <div class="text-caption">Endereço</div>
              {{ selected.endereco.logradouro }}, {{ selected.endereco.numero }}
              <template v-if="selected.endereco.complemento">· {{ selected.endereco.complemento }}</template>
              <br />
              {{ selected.endereco.bairro }} · CEP {{ selected.endereco.cep }}
              <br />
              {{ selected.endereco.cidade.nome }}
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions class="pa-5">
          <v-spacer />
          <v-btn variant="text" @click="inspectDialog = false">Fechar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
