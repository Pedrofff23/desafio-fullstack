<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({ name: 'NotFoundView' })
</script>

<template>
  <v-main>
    <v-container class="fill-height text-center">
      <div class="mx-auto">
        <v-icon color="primary" icon="mdi-map-marker-question-outline" size="72" />
        <h1 class="text-h3 font-weight-bold mt-4">Página não encontrada</h1>
        <p class="text-medium-emphasis my-4">O endereço informado não existe.</p>
        <v-btn color="primary" to="/estoque">Voltar ao estoque</v-btn>
      </div>
    </v-container>
  </v-main>
</template>
