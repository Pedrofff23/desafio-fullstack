<script lang="ts">
import { defineComponent, type PropType } from 'vue'

import type { LoteValidadeStatus } from '@/types/api'

const statusMap = {
  normal: { label: 'Normal', color: 'success', icon: 'mdi-calendar-check-outline' },
  validade_proxima: {
    label: 'Próximo do vencimento',
    color: 'warning',
    icon: 'mdi-clock-alert-outline',
  },
  vencido: { label: 'Vencido', color: 'error', icon: 'mdi-calendar-remove' },
  sem_validade: { label: 'Sem validade', color: 'grey', icon: 'mdi-calendar-blank-outline' },
} as const

export default defineComponent({
  name: 'LotExpirationChip',
  props: {
    status: { type: String as PropType<LoteValidadeStatus>, required: true },
  },
  computed: {
    config() {
      return statusMap[this.status]
    },
  },
})
</script>

<template>
  <v-chip :color="config.color" :prepend-icon="config.icon" size="small" variant="tonal">
    {{ config.label }}
  </v-chip>
</template>
