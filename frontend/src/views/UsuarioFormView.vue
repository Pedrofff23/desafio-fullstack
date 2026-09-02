<script lang="ts">
import { defineComponent } from 'vue'

import { usuariosApi } from '@/api/usuarios'
import AddressFields from '@/components/AddressFields.vue'
import ContactFields from '@/components/ContactFields.vue'
import PageHeader from '@/components/PageHeader.vue'
import type { UsuarioCreate, UsuarioUpdate } from '@/types/api'
import { getErrorMessage } from '@/utils/errors'
import {
  createAddressInput,
  createContactInput,
  normalizeAddressInput,
  normalizeContactInput,
} from '@/utils/formFields'

interface UsuarioFormState extends UsuarioCreate {
  ativo: boolean
}

export default defineComponent({
  name: 'UsuarioFormView',
  components: { AddressFields, ContactFields, PageHeader },
  data() {
    return {
      form: {
        nome: '',
        email: '',
        senha: '',
        perfil: 'funcionario',
        ativo: true,
        contato: createContactInput(),
        endereco: createAddressInput(),
      } as UsuarioFormState,
      loading: false,
      saving: false,
      error: '',
      showPassword: false,
    }
  },
  computed: {
    usuarioId(): number | null {
      const value = Number(this.$route.params.id)
      return Number.isInteger(value) && value > 0 ? value : null
    },
    editing(): boolean {
      return this.usuarioId !== null
    },
    title(): string {
      return this.editing ? 'Editar usuário' : 'Novo usuário'
    },
  },
  mounted() {
    if (this.editing) void this.load()
  },
  methods: {
    async load() {
      if (!this.usuarioId) return
      this.loading = true
      try {
        const usuario = await usuariosApi.get(this.usuarioId)
        this.form = {
          nome: usuario.funcionario.nome_completo,
          email: usuario.email,
          senha: '',
          perfil: usuario.perfil,
          ativo: usuario.ativo,
          contato: createContactInput(usuario.funcionario.contato),
          endereco: createAddressInput({
            logradouro: usuario.funcionario.endereco.logradouro,
            numero: usuario.funcionario.endereco.numero,
            complemento: usuario.funcionario.endereco.complemento,
            cep: usuario.funcionario.endereco.cep,
            bairro: usuario.funcionario.endereco.bairro,
            estado_id: usuario.funcionario.endereco.cidade.estado_id,
            cidade_id: usuario.funcionario.endereco.cidade.id,
          }),
        }
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.loading = false
      }
    },
    validate(): boolean {
      const required = [
        this.form.nome,
        this.form.email,
        this.form.contato.ddd,
        this.form.contato.numero,
        this.form.endereco.logradouro,
        this.form.endereco.numero,
        this.form.endereco.cep,
        this.form.endereco.bairro,
        this.form.endereco.estado_id,
        this.form.endereco.cidade_id,
      ]
      if (required.some((value) => value === '' || value === null)) {
        this.error = 'Preencha todos os campos obrigatórios.'
        return false
      }
      if (!this.editing && this.form.senha.length < 6) {
        this.error = 'A senha deve ter pelo menos 6 caracteres.'
        return false
      }
      return true
    },
    async submit() {
      this.error = ''
      if (!this.validate()) return
      this.saving = true
      try {
        if (this.editing && this.usuarioId) {
          const payload: UsuarioUpdate = {
            nome: this.form.nome,
            email: this.form.email,
            perfil: this.form.perfil,
            ativo: this.form.ativo,
            contato: normalizeContactInput(this.form.contato),
            endereco: normalizeAddressInput(this.form.endereco),
          }
          if (this.form.senha) payload.senha = this.form.senha
          await usuariosApi.update(this.usuarioId, payload)
        } else {
          const payload: UsuarioCreate = {
            nome: this.form.nome,
            email: this.form.email,
            senha: this.form.senha,
            perfil: this.form.perfil,
            contato: normalizeContactInput(this.form.contato),
            endereco: normalizeAddressInput(this.form.endereco),
          }
          await usuariosApi.create(payload)
        }
        await this.$router.push('/usuarios')
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
    <PageHeader :title="title" subtitle="Dados de acesso, contato e endereço do funcionário." />

    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
    <v-progress-linear v-if="loading" color="primary" indeterminate class="mb-4" />

    <v-card v-if="!loading" class="data-card pa-5 pa-md-7">
      <v-form @submit.prevent="submit">
        <v-row>
          <v-col cols="12"
            ><div class="text-subtitle-1 font-weight-bold">Dados do usuário</div></v-col
          >
          <v-col cols="12" md="7">
            <v-text-field v-model.trim="form.nome" label="Nome completo" required />
          </v-col>
          <v-col cols="12" md="5">
            <v-text-field v-model.trim="form.email" type="email" label="E-mail" required />
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="form.senha"
              :type="showPassword ? 'text' : 'password'"
              :label="editing ? 'Nova senha (opcional)' : 'Senha'"
              :append-inner-icon="showPassword ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
              :required="!editing"
              @click:append-inner="showPassword = !showPassword"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-select
              v-model="form.perfil"
              :items="[
                { title: 'Funcionário', value: 'funcionario' },
                { title: 'Administrador', value: 'admin' },
              ]"
              label="Perfil"
            />
          </v-col>
          <v-col v-if="editing" cols="12" md="4">
            <v-switch v-model="form.ativo" color="primary" label="Usuário ativo" inset />
          </v-col>

          <v-col cols="12"><v-divider class="my-2" /></v-col>
          <v-col cols="12"><ContactFields v-model="form.contato" /></v-col>

          <v-col cols="12"><v-divider class="my-2" /></v-col>
          <v-col cols="12">
            <AddressFields v-model="form.endereco" />
          </v-col>
        </v-row>

        <div class="form-actions">
          <v-btn variant="text" to="/usuarios">Cancelar</v-btn>
          <v-btn color="primary" type="submit" :loading="saving">
            {{ editing ? 'Salvar alterações' : 'Cadastrar usuário' }}
          </v-btn>
        </div>
      </v-form>
    </v-card>
  </div>
</template>
