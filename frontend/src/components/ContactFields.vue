<script lang="ts">
import { defineComponent, type PropType } from 'vue'

import type { ContatoInput } from '@/types/api'
import { formatPhoneInput, onlyDigits } from '@/utils/formatters'

export default defineComponent({
  name: 'ContactFields',
  props: {
    modelValue: {
      type: Object as PropType<ContatoInput>,
      required: true,
    },
  },
  emits: ['update:modelValue'],
  methods: {
    update(field: keyof ContatoInput, value: unknown) {
      this.$emit('update:modelValue', {
        ...this.modelValue,
        [field]: String(value ?? ''),
      })
    },
    normalizeDdd() {
      this.update('ddd', onlyDigits(this.modelValue.ddd).slice(0, 2))
    },
    onPhoneInput(value: unknown) {
      this.update('numero', formatPhoneInput(String(value ?? '')))
    },
    normalizePhone() {
      this.update('numero', formatPhoneInput(this.modelValue.numero))
    },
  },
})
</script>

<template>
  <v-row>
    <v-col cols="12">
      <div class="text-subtitle-1 font-weight-bold">Contato</div>
    </v-col>
    <v-col cols="12" md="3">
      <v-text-field
        :model-value="modelValue.codigo_pais"
        label="Código do país"
        required
        @update:model-value="update('codigo_pais', $event)"
      />
    </v-col>
    <v-col cols="12" md="3">
      <v-text-field
        :model-value="modelValue.ddd"
        label="DDD"
        inputmode="numeric"
        maxlength="2"
        required
        @update:model-value="update('ddd', $event)"
        @blur="normalizeDdd"
      />
    </v-col>
    <v-col cols="12" md="6">
      <v-text-field
        :model-value="modelValue.numero"
        label="Telefone"
        inputmode="numeric"
        maxlength="10"
        hint="Ex.: 99999-9999 ou 4444-4444"
        persistent-hint
        required
        @update:model-value="onPhoneInput"
        @blur="normalizePhone"
      />
    </v-col>
  </v-row>
</template>
