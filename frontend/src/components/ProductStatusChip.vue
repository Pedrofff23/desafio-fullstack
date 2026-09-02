<script lang="ts">
import { defineComponent, type PropType } from 'vue'

import type { ProdutoStatus } from '@/types/api'

const statusMap = {
  ok: { label: 'Normal', color: 'success', icon: 'mdi-check-circle-outline' },
  validade_proxima: {
    label: 'Validade próxima',
    color: 'warning',
    icon: 'mdi-clock-alert-outline',
  },
  vencido: { label: 'Vencido', color: 'error', icon: 'mdi-calendar-remove' },
  estoque_baixo: { label: 'Estoque baixo', color: 'warning', icon: 'mdi-trending-down' },
  zerado: { label: 'Sem estoque', color: 'error', icon: 'mdi-package-variant-remove' },
} as const

export default defineComponent({
  name: 'ProductStatusChip',
  props: {
    status: { type: String as PropType<ProdutoStatus>, required: true },
  },
  computed: {
    config() {
      return statusMap[this.status] ?? statusMap.ok
    },
  },
})
</script>

<template>
  <v-chip :color="config.color" :prepend-icon="config.icon" size="small" variant="tonal">
    {{ config.label }}
  </v-chip>
</template>
