<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ActiveStatusChip',
  props: {
    active: { type: Boolean, required: true },
  },
})
</script>

<template>
  <v-chip :color="active ? 'success' : 'default'" size="small" variant="tonal">
    {{ active ? 'Ativo' : 'Inativo' }}
  </v-chip>
</template>
