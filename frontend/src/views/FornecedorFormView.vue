<script lang="ts">
import { defineComponent } from 'vue';

import { transacoesApi } from '@/api/transacoes';
import AddressFields from '@/components/AddressFields.vue';
import ContactFields from '@/components/ContactFields.vue';
import PageHeader from '@/components/PageHeader.vue';
import type { FornecedorCreate, FornecedorUpdate } from '@/types/api';
import { getErrorMessage } from '@/utils/errors';
import { createAddressInput, createContactInput, normalizeAddressInput, normalizeContactInput } from '@/utils/formFields';
import { scrollToError } from '@/utils/scroll';

function emptyForm(): FornecedorCreate {
  return {
    nome_empresa: '',
    ativo: true,
    contato: createContactInput(),
    endereco: createAddressInput()
  };
}

export default defineComponent({
  name: 'FornecedorFormView',
  components: {
    AddressFields,
    ContactFields,
    PageHeader
  },
  data() {
    return {
      form: emptyForm(),
      loading: false,
      saving: false,
      error: ''
    };
  },
  computed: {
    fornecedorId(): number | null {
      const value = Number(this.$route.params.id);
      return Number.isInteger(value) && value > 0 ? value : null;
    },
    editing(): boolean {
      return this.fornecedorId !== null;
    },
    title(): string {
      return this.editing ? 'Editar fornecedor' : 'Novo fornecedor';
    },
    subtitle(): string {
      return this.editing
        ? 'Atualize os dados cadastrais, contato e endereço da empresa.'
        : 'Cadastre uma nova empresa para registrar entradas no estoque.';
    }
  },
  watch: {
    error(val: string) {
      if (val) {
        void scrollToError(this.$refs.errorAlert as any);
      }
    }
  },
  mounted() {
    if (this.editing) {
      void this.load();
    }
  },
  methods: {
    async load() {
      if (!this.fornecedorId) return;
      this.loading = true;
      this.error = '';
      try {
        const supplier = await transacoesApi.getFornecedor(this.fornecedorId);
        this.form = {
          nome_empresa: supplier.nome_empresa,
          ativo: supplier.ativo,
          contato: createContactInput(supplier.contato),
          endereco: createAddressInput({
            logradouro: supplier.endereco.logradouro,
            numero: supplier.endereco.numero,
            complemento: supplier.endereco.complemento,
            cep: supplier.endereco.cep,
            bairro: supplier.endereco.bairro,
            estado_id: supplier.endereco.cidade.estado_id,
            cidade_id: supplier.endereco.cidade.id
          })
        };
      } catch (error) {
        this.error = getErrorMessage(error);
        void scrollToError(this.$refs.errorAlert as any);
      } finally {
        this.loading = false;
      }
    },
    validate(): boolean {
      if (!this.form.nome_empresa.trim()) {
        this.error = 'O nome da empresa é obrigatório.';
        return false;
      }
      const requiredAddress = [
        this.form.endereco.logradouro,
        this.form.endereco.numero,
        this.form.endereco.cep,
        this.form.endereco.bairro,
        this.form.endereco.estado_id,
        this.form.endereco.cidade_id
      ];
      if (requiredAddress.some((value) => value === '' || value === null)) {
        this.error = 'Preencha todos os campos obrigatórios do endereço.';
        return false;
      }
      return true;
    },
    async submit() {
      this.error = '';
      if (!this.validate()) {
        void scrollToError(this.$refs.errorAlert as any);
        return;
      }
      this.saving = true;
      try {
        const payload: FornecedorCreate = {
          nome_empresa: this.form.nome_empresa.trim(),
          ativo: this.form.ativo,
          contato: normalizeContactInput(this.form.contato),
          endereco: normalizeAddressInput(this.form.endereco)
        };
        if (this.editing && this.fornecedorId) {
          const updatePayload: FornecedorUpdate = {
            nome_empresa: payload.nome_empresa,
            ativo: payload.ativo,
            contato: payload.contato,
            endereco: payload.endereco
          };
          await transacoesApi.updateFornecedor(this.fornecedorId, updatePayload);
        } else {
          await transacoesApi.createFornecedor(payload);
        }
        await this.$router.push('/fornecedores');
      } catch (error) {
        this.error = getErrorMessage(error);
        void scrollToError(this.$refs.errorAlert as any);
      } finally {
        this.saving = false;
      }
    }
  }
});
</script>

<template>
  <div>
    <PageHeader :title="title" :subtitle="subtitle" />

    <v-alert v-if="error" ref="errorAlert" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
    <v-progress-linear v-if="loading" color="primary" indeterminate class="mb-4" />

    <v-card v-if="!loading" class="data-card pa-5 pa-md-7">
      <v-form @submit.prevent="submit">
        <v-row>
          <v-col cols="12">
            <div class="text-subtitle-1 font-weight-bold">Dados da empresa</div>
          </v-col>
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

          <v-col cols="12"><v-divider class="my-2" /></v-col>
          <v-col cols="12">
            <ContactFields v-model="form.contato" />
          </v-col>

          <v-col cols="12"><v-divider class="my-2" /></v-col>
          <v-col cols="12">
            <AddressFields v-model="form.endereco" />
          </v-col>
        </v-row>

        <div class="form-actions">
          <v-btn variant="text" to="/fornecedores">Cancelar</v-btn>
          <v-btn color="primary" type="submit" :loading="saving">
            {{ editing ? 'Salvar alterações' : 'Cadastrar fornecedor' }}
          </v-btn>
        </div>
      </v-form>
    </v-card>
  </div>
</template>
