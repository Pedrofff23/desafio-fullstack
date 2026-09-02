<script lang="ts">
import { defineComponent, type PropType } from 'vue'

import { geoApi } from '@/api/geo'
import type { Cidade, EnderecoInput, Estado } from '@/types/api'
import { getErrorMessage } from '@/utils/errors'
import { formatCepInput } from '@/utils/formatters'

export default defineComponent({
  name: 'AddressFields',
  props: {
    modelValue: {
      type: Object as PropType<EnderecoInput>,
      required: true,
    },
  },
  emits: ['update:modelValue'],
  data() {
    return {
      localAddress: {
        ...this.modelValue,
        cep: formatCepInput(this.modelValue.cep),
      } as EnderecoInput,
      estados: [] as Estado[],
      cidades: [] as Cidade[],
      loadingStates: false,
      loadingCities: false,
      error: '',
    }
  },
  watch: {
    modelValue: {
      deep: true,
      handler(value: EnderecoInput) {
        if (JSON.stringify(value) !== JSON.stringify(this.localAddress)) {
          this.localAddress = { ...value, cep: formatCepInput(value.cep) }
        }
      },
    },
    localAddress: {
      deep: true,
      handler(value: EnderecoInput) {
        this.$emit('update:modelValue', { ...value })
      },
    },
    'localAddress.estado_id'(value: number | null, previous: number | null) {
      if (value !== previous) {
        this.localAddress.cidade_id = null
        if (value) void this.loadCities(value)
        else this.cidades = []
      }
    },
  },
  async mounted() {
    this.loadingStates = true
    try {
      this.estados = await geoApi.estados()
      if (this.localAddress.estado_id) await this.loadCities(this.localAddress.estado_id)
    } catch (error) {
      this.error = getErrorMessage(error)
    } finally {
      this.loadingStates = false
    }
  },
  methods: {
    async loadCities(estadoId: number) {
      this.loadingCities = true
      try {
        this.cidades = await geoApi.cidades(estadoId)
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.loadingCities = false
      }
    },
    normalizeCep() {
      this.localAddress.cep = formatCepInput(this.localAddress.cep)
    },
  },
})
</script>

<template>
  <v-row>
    <v-col cols="12">
      <div class="text-subtitle-1 font-weight-bold">Endereço</div>
    </v-col>
    <v-col cols="12" md="6">
      <v-select
        v-model="localAddress.estado_id"
        :items="estados"
        item-title="nome"
        item-value="id"
        label="Estado"
        :loading="loadingStates"
        required
      />
    </v-col>
    <v-col cols="12" md="6">
      <v-autocomplete
        v-model="localAddress.cidade_id"
        :items="cidades"
        item-title="nome"
        item-value="id"
        label="Cidade"
        :loading="loadingCities"
        :disabled="!localAddress.estado_id"
        required
      />
    </v-col>
    <v-col cols="12" md="8">
      <v-text-field v-model="localAddress.logradouro" label="Logradouro" required />
    </v-col>
    <v-col cols="12" md="4">
      <v-text-field v-model="localAddress.numero" label="Número" required />
    </v-col>
    <v-col cols="12" md="6">
      <v-text-field v-model="localAddress.bairro" label="Bairro" required />
    </v-col>
    <v-col cols="12" md="6">
      <v-text-field
        v-model="localAddress.cep"
        label="CEP"
        maxlength="9"
        hint="Formato 00000-000"
        required
        @blur="normalizeCep"
      />
    </v-col>
    <v-col cols="12">
      <v-text-field v-model="localAddress.complemento" label="Complemento" />
    </v-col>
    <v-col v-if="error" cols="12">
      <v-alert type="error" variant="tonal" closable @click:close="error = ''">
        {{ error }}
      </v-alert>
    </v-col>
  </v-row>
</template>
