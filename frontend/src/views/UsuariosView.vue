<script lang="ts">
import { defineComponent } from 'vue';

import { usuariosApi } from '@/api/usuarios';
import ActiveStatusChip from '@/components/ActiveStatusChip.vue';
import PageHeader from '@/components/PageHeader.vue';
import SearchFilterCard from '@/components/SearchFilterCard.vue';
import type { Usuario } from '@/types/api';
import { getErrorMessage } from '@/utils/errors';
import { formatContact } from '@/utils/formatters';
import { scrollToError } from '@/utils/scroll';

export default defineComponent({
  name: 'UsuariosView',
  components: { ActiveStatusChip, PageHeader, SearchFilterCard },
  data() {
    return {
      items: [] as Usuario[],
      nome: '',
      headers: [
        { title: 'Nome', key: 'nome', sortable: false },
        { title: 'E-mail', key: 'email', sortable: false },
        { title: 'Contato', key: 'contato', sortable: false },
        { title: 'Perfil', key: 'perfil', sortable: false },
        { title: 'Situação', key: 'ativo', sortable: false },
        { title: 'Ações', key: 'actions', align: 'end' as const, sortable: false }
      ],
      pageSizeOptions: [10, 20, 50, 100],
      page: 1,
      size: 20,
      pages: 0,
      total: 0,
      loading: false,
      error: '',
      success: ''
    };
  },
  watch: {
    error(val: string) {
      if (val) {
        void scrollToError(this.$refs.errorAlert as any);
      }
    }
  },
  methods: {
    formatContact,
    async load(page?: number, size?: number) {
      this.loading = true;
      this.error = '';
      if (page !== undefined) this.page = page;
      if (size !== undefined) this.size = size;
      try {
        const response = await usuariosApi.listar({
          page: this.page,
          size: this.size,
          nome: this.nome || undefined
        });
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
      this.nome = '';
      this.search();
    },
    async remove(usuario: Usuario) {
      const confirmed = window.confirm(`Deseja excluir o usuário ${usuario.funcionario.nome_completo}?`);
      if (!confirmed) return;
      this.error = '';
      this.success = '';
      try {
        await usuariosApi.delete(usuario.id);
        this.success = 'Usuário excluído com sucesso.';
        await this.load();
      } catch (error) {
        this.error = getErrorMessage(error);
        void scrollToError(this.$refs.errorAlert as any);
      }
    }
  }
});
</script>

<template>
  <div>
    <PageHeader title="Usuários" subtitle="Pessoas autorizadas a operar o sistema.">
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-account-plus-outline" to="/usuarios/novo">Novo usuário</v-btn>
      </template>
    </PageHeader>

    <v-alert v-if="error" ref="errorAlert" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
    <v-alert v-if="success" type="success" variant="tonal" closable class="mb-4" @click:close="success = ''">
      {{ success }}
    </v-alert>

    <SearchFilterCard
      v-model="nome"
      label="Pesquisar por nome"
      placeholder="Digite o nome do usuário..."
      :loading="loading"
      @search="search"
      @clear="clearFilters"
    />

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
          <span class="font-weight-medium">{{ item.funcionario.nome_completo }}</span>
        </template>

        <template #item.email="{ item }">
          {{ item.email }}
        </template>

        <template #item.contato="{ item }">
          {{ formatContact(item.funcionario.contato) }}
        </template>

        <template #item.perfil="{ item }">
          <v-chip size="small" variant="tonal">{{ item.perfil }}</v-chip>
        </template>

        <template #item.ativo="{ item }">
          <ActiveStatusChip :active="item.ativo" />
        </template>

        <template #item.actions="{ item }">
          <div class="table-actions">
            <v-btn :to="`/usuarios/${item.id}/editar`" icon="mdi-pencil-outline" size="small" variant="text" title="Editar" />
            <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error" title="Excluir" @click="remove(item)" />
          </div>
        </template>

        <template #no-data>
          <div class="pa-4 text-center text-medium-emphasis">Nenhum usuário encontrado.</div>
        </template>
      </v-data-table-server>
    </v-card>
  </div>
</template>
