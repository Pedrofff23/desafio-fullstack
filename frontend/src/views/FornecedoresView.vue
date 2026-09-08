<script lang="ts">
import { defineComponent } from 'vue'

import { transacoesApi } from '@/api/transacoes'
import ActiveStatusChip from '@/components/ActiveStatusChip.vue'
import AddressFields from '@/components/AddressFields.vue'
import ContactFields from '@/components/ContactFields.vue'
import EmptyTableRow from '@/components/EmptyTableRow.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationControls from '@/components/PaginationControls.vue'
import type { Fornecedor, FornecedorCreate } from '@/types/api'
import { getErrorMessage } from '@/utils/errors'
import { formatContact, formatDateTime } from '@/utils/formatters'
import {
  createAddressInput,
  createContactInput,
  normalizeAddressInput,
  normalizeContactInput,
} from '@/utils/formFields'

function emptyForm(): FornecedorCreate {
  return {
    nome_empresa: '',
    ativo: true,
    contato: createContactInput(),
    endereco: createAddressInput(),
  }
}

export default defineComponent({
  name: 'FornecedoresView',
  components: {
    ActiveStatusChip,
    AddressFields,
    ContactFields,
    EmptyTableRow,
    PageHeader,
    PaginationControls,
  },
  data() {
    return {
      items: [] as Fornecedor[],
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
      success: '',
    }
  },
  computed: {
    total(): number {
      return this.items.length
    },
    pages(): number {
      return Math.ceil(this.total / this.size) || 1
    },
    paginatedItems(): Fornecedor[] {
      const start = (this.page - 1) * this.size
      return this.items.slice(start, start + this.size)
    },
  },
  mounted() {
    void this.load()
  },
  methods: {
    formatContact,
    formatDateTime,
    async load() {
      this.loading = true
      try {
        this.items = await transacoesApi.fornecedores()
        if (this.page > this.pages) {
          this.page = Math.max(this.pages, 1)
        }
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.loading = false
      }
    },
    openForm() {
      this.form = emptyForm()
      this.editingId = null
      this.error = ''
      this.dialog = true
    },
    inspect(supplier: Fornecedor) {
      this.selected = supplier
      this.inspectDialog = true
    },
    edit(supplier: Fornecedor) {
      this.editingId = supplier.id
      this.form = {
        nome_empresa: supplier.nome_empresa,
        ativo: supplier.ativo,
        contato: createContactInput(supplier.contato),
        endereco: createAddressInput({
          ...supplier.endereco,
          estado_id: supplier.endereco.cidade.estado_id,
          cidade_id: supplier.endereco.cidade.id,
        }),
      }
      this.error = ''
      this.dialog = true
    },
    async remove(supplier: Fornecedor) {
      if (!window.confirm(`Deseja excluir o fornecedor ${supplier.nome_empresa}?`)) return
      this.error = ''
      try {
        await transacoesApi.deleteFornecedor(supplier.id)
        this.success = 'Fornecedor excluído com sucesso.'
        await this.load()
      } catch (error) {
        this.error = getErrorMessage(error)
      }
    },
    async submit() {
      if (
        !this.form.nome_empresa ||
        !this.form.contato.ddd ||
        !this.form.contato.numero ||
        !this.form.endereco.estado_id ||
        !this.form.endereco.cidade_id
      ) {
        this.error = 'Preencha todos os campos obrigatórios.'
        return
      }
      this.saving = true
      this.error = ''
      try {
        const payload = {
          ...this.form,
          contato: normalizeContactInput(this.form.contato),
          endereco: normalizeAddressInput(this.form.endereco),
        }
        if (this.editingId) await transacoesApi.updateFornecedor(this.editingId, payload)
        else await transacoesApi.createFornecedor(payload)
        this.dialog = false
        this.success = this.editingId
          ? 'Fornecedor atualizado com sucesso.'
          : 'Fornecedor cadastrado com sucesso.'
        await this.load()
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.saving = false
      }
    },
  },
})
</script>

<template>
  <div>
    <PageHeader title="Fornecedores" subtitle="Empresas disponíveis para registrar entradas.">
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openForm"> Novo fornecedor </v-btn>
      </template>
    </PageHeader>
    <v-alert v-if="error && !dialog" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
    <v-alert
      v-if="success"
      type="success"
      variant="tonal"
      closable
      class="mb-4"
      @click:close="success = ''"
      >{{ success }}</v-alert
    >

    <v-card class="data-card">
      <v-progress-linear v-if="loading" color="primary" indeterminate />
      <v-table>
        <thead>
          <tr>
            <th>Empresa</th>
            <th>Contato</th>
            <th>Cidade</th>
            <th>Situação</th>
            <th class="text-right">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="supplier in paginatedItems" :key="supplier.id">
            <td class="font-weight-medium">{{ supplier.nome_empresa }}</td>
            <td>{{ formatContact(supplier.contato) }}</td>
            <td>{{ supplier.endereco.cidade.nome }}</td>
            <td><ActiveStatusChip :active="supplier.ativo" /></td>
            <td class="text-right text-no-wrap">
              <v-btn icon="mdi-information-outline" size="small" variant="text" title="Inspecionar fornecedor" @click="inspect(supplier)" />
              <v-btn icon="mdi-pencil-outline" size="small" variant="text" title="Editar fornecedor" @click="edit(supplier)" />
              <v-btn icon="mdi-delete-outline" color="error" size="small" variant="text" title="Excluir fornecedor" @click="remove(supplier)" />
            </td>
          </tr>
          <EmptyTableRow
            v-if="!loading && items.length === 0"
            :columns="5"
            message="Nenhum fornecedor cadastrado."
          />
        </tbody>
      </v-table>
      <v-divider />
      <PaginationControls v-model="page" :pages="pages" :total="total" />
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
              <v-col cols="12" md="4"
                ><v-switch v-model="form.ativo" color="primary" label="Fornecedor ativo" inset
              /></v-col>
              <v-col cols="12"><ContactFields v-model="form.contato" /></v-col>
              <v-col cols="12"><v-divider class="my-2" /></v-col>
              <v-col cols="12"><AddressFields v-model="form.endereco" /></v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions class="pa-5 pt-0"
          ><v-spacer /><v-btn variant="text" @click="dialog = false">Cancelar</v-btn
          ><v-btn color="primary" :loading="saving" @click="submit"
            >{{ editingId ? 'Salvar alterações' : 'Cadastrar' }}</v-btn
          ></v-card-actions
        >
      </v-card>
    </v-dialog>

    <v-dialog v-model="inspectDialog" max-width="700">
      <v-card v-if="selected">
        <v-card-title class="d-flex align-center pa-5">Fornecedor<v-spacer /><v-btn icon="mdi-close" variant="text" @click="inspectDialog = false" /></v-card-title>
        <v-card-text class="px-5">
          <v-row>
            <v-col cols="12" md="8"><div class="text-caption">Empresa</div><strong>{{ selected.nome_empresa }}</strong></v-col>
            <v-col cols="12" md="4"><ActiveStatusChip :active="selected.ativo" /></v-col>
            <v-col cols="12" md="6"><div class="text-caption">Contato</div>{{ formatContact(selected.contato) }}</v-col>
            <v-col cols="12" md="6"><div class="text-caption">Cadastro</div>{{ formatDateTime(selected.data_cadastro) }}</v-col>
            <v-col cols="12"><v-divider /></v-col>
            <v-col cols="12"><div class="text-caption">Endereço</div>{{ selected.endereco.logradouro }}, {{ selected.endereco.numero }}<template v-if="selected.endereco.complemento"> · {{ selected.endereco.complemento }}</template><br />{{ selected.endereco.bairro }} · CEP {{ selected.endereco.cep }}<br />{{ selected.endereco.cidade.nome }}</v-col>
          </v-row>
        </v-card-text>
        <v-card-actions class="pa-5"><v-spacer /><v-btn variant="text" @click="inspectDialog = false">Fechar</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
