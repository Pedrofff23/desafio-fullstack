<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'PageHeader',
  props: {
    title: { type: String, required: true },
    subtitle: { type: String, required: true },
  },
})
</script>

<template>
  <header class="page-header">
    <div>
      <h1 class="page-title">{{ title }}</h1>
      <p class="page-subtitle">{{ subtitle }}</p>
    </div>
    <slot name="actions" />
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.page-title {
  color: #16372c;
  font-size: clamp(1.5rem, 2vw, 2rem);
  font-weight: 700;
  letter-spacing: -0.03em;
}

.page-subtitle {
  color: #64726d;
  margin-top: 4px;
}

@media (max-width: 600px) {
  .page-header {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
