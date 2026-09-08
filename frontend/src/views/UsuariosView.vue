<script lang="ts">
import { defineComponent } from 'vue'

import { usuariosApi } from '@/api/usuarios'
import ActiveStatusChip from '@/components/ActiveStatusChip.vue'
import EmptyTableRow from '@/components/EmptyTableRow.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationControls from '@/components/PaginationControls.vue'
import type { Usuario } from '@/types/api'
import { getErrorMessage } from '@/utils/errors'
import { formatContact } from '@/utils/formatters'

export default defineComponent({
  name: 'UsuariosView',
  components: { ActiveStatusChip, EmptyTableRow, PageHeader, PaginationControls },
  data() {
    return {
      items: [] as Usuario[],
      nome: '',
      page: 1,
      size: 20,
      pages: 0,
      total: 0,
      loading: false,
      error: '',
      success: '',
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
    formatContact,
    async load() {
      this.loading = true
      this.error = ''
      try {
        const response = await usuariosApi.listar({
          page: this.page,
          size: this.size,
          nome: this.nome || undefined,
        })
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
      this.nome = ''
      this.search()
    },
    async remove(usuario: Usuario) {
      const confirmed = window.confirm(
        `Deseja excluir o usuário ${usuario.funcionario.nome_completo}?`,
      )
      if (!confirmed) return
      this.error = ''
      this.success = ''
      try {
        await usuariosApi.excluir(usuario.id)
        this.success = 'Usuário excluído com sucesso.'
        await this.load()
      } catch (error) {
        this.error = getErrorMessage(error)
      }
    },
  },
})
</script>

<template>
  <div>
    <PageHeader title="Usuários" subtitle="Pessoas autorizadas a operar o sistema.">
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-account-plus-outline" to="/usuarios/novo">
          Novo usuário
        </v-btn>
      </template>
    </PageHeader>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
    <v-alert
      v-if="success"
      type="success"
      variant="tonal"
      closable
      class="mb-4"
      @click:close="success = ''"
    >
      {{ success }}
    </v-alert>

    <v-card class="data-card mb-4 pa-4">
      <v-form @submit.prevent="search">
        <div class="d-flex flex-column flex-md-row ga-3 align-md-center">
          <v-text-field
            v-model.trim="nome"
            label="Pesquisar por nome"
            prepend-inner-icon="mdi-magnify"
            hide-details
            clearable
          />
          <v-btn color="#560894" type="submit" :loading="loading">Pesquisar</v-btn>
          <v-btn variant="text" @click="clearFilters">Limpar</v-btn>
        </div>
      </v-form>
    </v-card>

    <v-card class="data-card">
      <v-progress-linear v-if="loading" color="primary" indeterminate />
      <v-table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>E-mail</th>
            <th>Contato</th>
            <th>Perfil</th>
            <th>Situação</th>
            <th class="text-right">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="usuario in items" :key="usuario.id">
            <td class="font-weight-medium">{{ usuario.funcionario.nome_completo }}</td>
            <td>{{ usuario.email }}</td>
            <td>{{ formatContact(usuario.funcionario.contato) }}</td>
            <td>
              <v-chip size="small" variant="tonal">{{ usuario.perfil }}</v-chip>
            </td>
            <td><ActiveStatusChip :active="usuario.ativo" /></td>
            <td>
              <div class="table-actions">
                <v-btn
                  :to="`/usuarios/${usuario.id}/editar`"
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
                  @click="remove(usuario)"
                />
              </div>
            </td>
          </tr>
          <EmptyTableRow
            v-if="!loading && items.length === 0"
            :columns="6"
            message="Nenhum usuário encontrado."
          />
        </tbody>
      </v-table>
      <v-divider />
      <PaginationControls v-model="page" :pages="pages" :total="total" />
    </v-card>
  </div>
</template>
