<script lang="ts">
import { defineComponent, type PropType } from 'vue'

import { onlyDigits } from '@/utils/formatters'

const currency = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export default defineComponent({
  name: 'CurrencyField',
  props: {
    modelValue: { type: Number as PropType<number | null>, default: null },
  },
  emits: ['update:modelValue'],
  computed: {
    formatted(): string {
      return this.modelValue === null ? '' : currency.format(this.modelValue)
    },
  },
  methods: {
    onInput(event: Event) {
      const input = event.target as HTMLInputElement
      const digits = onlyDigits(input.value)
      const value = digits ? Number(digits) / 100 : null
      input.value = value === null ? '' : currency.format(value)
      this.$emit('update:modelValue', value)
    },
  },
})
</script>

<template>
  <v-text-field :model-value="formatted" inputmode="numeric" prefix="R$" @input.capture="onInput" />
</template>
