<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'EmptyTableRow',
  props: {
    columns: { type: Number, required: true },
    message: { type: String, required: true },
  },
})
</script>

<template>
  <tr>
    <td :colspan="columns" class="text-center text-medium-emphasis py-8">
      {{ message }}
    </td>
  </tr>
</template>
