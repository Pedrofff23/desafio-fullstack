<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'PaginationControls',
  props: {
    modelValue: { type: Number, required: true },
    pages: { type: Number, required: true },
    total: { type: Number, required: true },
  },
  emits: ['update:modelValue'],
})
</script>

<template>
  <div class="pagination-wrapper pa-4">
    <span class="text-caption text-medium-emphasis">{{ total }} registro(s)</span>
    <v-pagination
      :model-value="modelValue"
      :length="Math.max(pages, 1)"
      :total-visible="6"
      density="comfortable"
      @update:model-value="$emit('update:modelValue', $event)"
    />
  </div>
</template>

<style scoped>
.pagination-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

@media (max-width: 600px) {
  .pagination-wrapper {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
