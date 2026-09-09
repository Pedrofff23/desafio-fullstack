<script lang="ts">
import { defineComponent, type PropType } from 'vue';

import ActiveStatusChip from '@/components/ActiveStatusChip.vue';
import ProductStatusChip from '@/components/ProductStatusChip.vue';
import type { CatalogoProduto, Produto } from '@/types/api';
import { formatCurrency, formatQuantity } from '@/utils/formatters';

export default defineComponent({
  name: 'ProductInspectionDialog',
  components: { ActiveStatusChip, ProductStatusChip },
  props: {
    modelValue: { type: Boolean, required: true },
    product: { type: Object as PropType<Produto | null>, default: null },
    catalog: { type: Object as PropType<CatalogoProduto | null>, default: null },
    loading: { type: Boolean, default: false }
  },
  emits: ['update:modelValue'],
  methods: {
    formatCurrency,
    formatQuantity,
    close() {
      this.$emit('update:modelValue', false);
    },
    locationLabel(): string {
      const location = this.catalog?.localizacoes.find((item) => item.id === this.product?.localizacao_id);
      if (!location) return '—';
      const level = location.nivel ? ` / Nível ${location.nivel}` : '';
      return `${location.corredor} / ${location.seccao} / ${location.prateleira}${level}`;
    }
  }
});
</script>

<template>
  <v-dialog :model-value="modelValue" max-width="900" @update:model-value="$emit('update:modelValue', $event)">
    <v-card>
      <v-card-title class="d-flex align-center pa-5">
        Informações do produto
        <v-spacer />
        <v-btn icon="mdi-close" variant="text" @click="close" />
      </v-card-title>
      <v-progress-linear v-if="loading" indeterminate color="primary" />
      <v-card-text v-if="product" class="px-5">
        <v-row>
          <v-col cols="12" md="8">
            <strong>{{ product.nome }}</strong>
            <div class="text-medium-emphasis">Código {{ product.codigo }}</div>
          </v-col>
          <v-col cols="6" md="2"><ActiveStatusChip :active="product.ativo" /></v-col>
          <v-col cols="6" md="2"><ProductStatusChip :status="product.status" /></v-col>
          <v-col cols="12">{{ product.descricao || 'Sem descrição.' }}</v-col>
          <v-col cols="6" md="3">
            <div class="text-caption">Preço</div>
            {{ formatCurrency(product.preco) }}
          </v-col>
          <v-col cols="6" md="3">
            <div class="text-caption">Saldo</div>
            {{ formatQuantity(product.quantidade_estoque) }}
          </v-col>
          <v-col cols="6" md="3">
            <div class="text-caption">Categoria</div>
            {{ product.categoria?.nome ?? '—' }}
          </v-col>
          <v-col cols="6" md="3">
            <div class="text-caption">Unidade</div>
            {{ product.unidade_medida?.descricao ?? '—' }}
          </v-col>
          <v-col cols="12">
            <div class="text-caption">Localização preferencial</div>
            {{ locationLabel() }}
          </v-col>
          <v-col cols="12"><v-divider /></v-col>
          <v-col cols="12" md="4">
            <div class="text-subtitle-2">Ingredientes</div>
            <div v-if="!product.ingredientes.length">—</div>
            <div v-for="item in [...product.ingredientes].sort((a, b) => a.ordem - b.ordem)" :key="item.ingrediente_id">
              {{ item.ordem }}. {{ item.nome }}
            </div>
          </v-col>
          <v-col cols="12" md="4">
            <div class="text-subtitle-2">Alérgenos</div>
            <div>{{ product.alergenos.map((item) => item.nome).join(', ') || '—' }}</div>
          </v-col>
          <v-col cols="12" md="4">
            <div class="text-subtitle-2">Nutrientes</div>
            <div v-if="!product.nutrientes.length">—</div>
            <div v-for="item in product.nutrientes" :key="item.id">
              {{ item.nome }}: {{ formatQuantity(item.valor) }} {{ item.unidade }}
            </div>
          </v-col>
        </v-row>
      </v-card-text>
      <v-card-actions class="pa-5">
        <v-spacer />
        <v-btn variant="text" @click="close">Fechar</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
