<script lang="ts">
import { defineComponent } from 'vue'

import { transacoesApi } from '@/api/transacoes'
import ActiveStatusChip from '@/components/ActiveStatusChip.vue'
import AddressFields from '@/components/AddressFields.vue'
import ContactFields from '@/components/ContactFields.vue'
import EmptyTableRow from '@/components/EmptyTableRow.vue'
import PageHeader from '@/components/PageHeader.vue'
import type { Fornecedor, FornecedorCreate } from '@/types/api'
import { getErrorMessage } from '@/utils/errors'
import { formatContact } from '@/utils/formatters'
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
  components: { ActiveStatusChip, AddressFields, ContactFields, EmptyTableRow, PageHeader },
  data() {
    return {
      items: [] as Fornecedor[],
      form: emptyForm(),
      dialog: false,
      loading: false,
      saving: false,
      error: '',
      success: '',
    }
  },
  mounted() {
    void this.load()
  },
  methods: {
    formatContact,
    async load() {
      this.loading = true
      try {
        this.items = await transacoesApi.fornecedores()
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.loading = false
      }
    },
    openForm() {
      this.form = emptyForm()
      this.error = ''
      this.dialog = true
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
        await transacoesApi.createFornecedor({
          ...this.form,
          contato: normalizeContactInput(this.form.contato),
          endereco: normalizeAddressInput(this.form.endereco),
        })
        this.dialog = false
        this.success = 'Fornecedor cadastrado com sucesso.'
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
          </tr>
        </thead>
        <tbody>
          <tr v-for="supplier in items" :key="supplier.id">
            <td class="font-weight-medium">{{ supplier.nome_empresa }}</td>
            <td>{{ formatContact(supplier.contato) }}</td>
            <td>{{ supplier.endereco.cidade.nome }}</td>
            <td><ActiveStatusChip :active="supplier.ativo" /></td>
          </tr>
          <EmptyTableRow
            v-if="!loading && items.length === 0"
            :columns="4"
            message="Nenhum fornecedor cadastrado."
          />
        </tbody>
      </v-table>
    </v-card>

    <v-dialog v-model="dialog" max-width="900" persistent>
      <v-card>
        <v-card-title class="pa-5">Novo fornecedor</v-card-title>
        <v-card-text>
          <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
          <v-form @submit.prevent="submit">
            <v-row>
              <v-col cols="12" md="8"
                ><v-text-field v-model.trim="form.nome_empresa" label="Nome da empresa" required
              /></v-col>
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
            >Cadastrar</v-btn
          ></v-card-actions
        >
      </v-card>
    </v-dialog>
  </div>
</template>
