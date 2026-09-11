<script lang="ts">
import { defineComponent, type PropType } from 'vue';

import ActiveStatusChip from '@/components/ActiveStatusChip.vue';
import ProductStatusChip from '@/components/ProductStatusChip.vue';
import type { CatalogoProduto, Localizacao, Produto, ProdutoIngrediente } from '@/types/api';
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
  data() {
    return {
      tab: 'geral'
    };
  },
  computed: {
    resolvedLocation(): Localizacao | null {
      if (!this.product?.localizacao_id || !this.catalog?.localizacoes) return null;
      return this.catalog.localizacoes.find((item) => item.id === this.product?.localizacao_id) ?? null;
    },
    sortedIngredients(): ProdutoIngrediente[] {
      if (!this.product?.ingredientes) return [];
      return [...this.product.ingredientes].sort((a, b) => a.ordem - b.ordem);
    }
  },
  methods: {
    formatCurrency,
    formatQuantity,
    close() {
      this.$emit('update:modelValue', false);
    }
  }
});
</script>

<template>
  <v-dialog :model-value="modelValue" max-width="880" @update:model-value="$emit('update:modelValue', $event)">
    <v-card class="product-inspection-dialog overflow-hidden" rounded="xl">
      <!-- Loading bar -->
      <v-progress-linear v-if="loading" indeterminate color="primary" />

      <template v-if="product">
        <!-- Hero Header -->
        <div class="product-hero px-6 pt-6 pb-4">
          <div class="d-flex align-start justify-space-between mb-3">
            <div class="d-flex align-center ga-4">
              <v-avatar color="primary" size="56" rounded="lg" class="elevation-2 text-white">
                <v-icon icon="mdi-food-apple-outline" size="32" />
              </v-avatar>
              <div>
                <div class="d-flex align-center ga-2 flex-wrap">
                  <h2 class="text-h5 font-weight-bold text-grey-darken-4 mb-0">{{ product.nome }}</h2>
                  <v-chip size="small" variant="tonal" color="primary" prepend-icon="mdi-barcode" class="font-weight-medium">
                    {{ product.codigo }}
                  </v-chip>
                </div>
                <div class="text-caption text-medium-emphasis mt-1 d-flex align-center ga-2 flex-wrap">
                  <span v-if="product.categoria">
                    <v-icon icon="mdi-shape-outline" size="14" class="mr-1" />
                    {{ product.categoria.nome }}
                  </span>
                  <span v-if="product.unidade_medida">
                    · {{ product.unidade_medida.descricao }} ({{ product.unidade_medida.sigla }})
                  </span>
                </div>
              </div>
            </div>
            <v-btn icon="mdi-close" variant="text" density="comfortable" aria-label="Fechar" @click="close" />
          </div>

          <!-- Status pills row -->
          <div class="d-flex align-center ga-2 flex-wrap">
            <ActiveStatusChip :active="product.ativo" />
            <ProductStatusChip :status="product.status" />
            <v-chip
              size="small"
              variant="tonal"
              :color="product.perecivel ? 'warning' : 'info'"
              :prepend-icon="product.perecivel ? 'mdi-clock-alert-outline' : 'mdi-shield-check-outline'"
            >
              {{ product.perecivel ? 'Perecível (com validade)' : 'Não perecível' }}
            </v-chip>
          </div>
        </div>

        <!-- Quick Stats / Metrics Row -->
        <div class="px-6 py-4 bg-grey-lighten-5 border-y">
          <v-row dense>
            <!-- Preço -->
            <v-col cols="6" sm="3">
              <v-card variant="flat" class="stat-card pa-3 text-center bg-surface">
                <div class="d-flex align-center justify-center ga-1 text-caption text-medium-emphasis mb-1">
                  <v-icon icon="mdi-currency-usd" size="16" color="primary" />
                  <span>Preço Unitário</span>
                </div>
                <div class="text-h6 font-weight-bold text-primary">
                  {{ formatCurrency(product.preco) }}
                </div>
              </v-card>
            </v-col>

            <!-- Saldo em Estoque -->
            <v-col cols="6" sm="3">
              <v-card variant="flat" class="stat-card pa-3 text-center bg-surface">
                <div class="d-flex align-center justify-center ga-1 text-caption text-medium-emphasis mb-1">
                  <v-icon icon="mdi-cube-outline" size="16" :color="product.quantidade_estoque > 0 ? 'success' : 'error'" />
                  <span>Saldo em Estoque</span>
                </div>
                <div class="text-h6 font-weight-bold" :class="product.quantidade_estoque > 0 ? 'text-success' : 'text-error'">
                  {{ formatQuantity(product.quantidade_estoque) }}
                  <span class="text-caption font-weight-regular text-medium-emphasis">
                    {{ product.unidade_medida?.sigla || '' }}
                  </span>
                </div>
              </v-card>
            </v-col>

            <!-- Categoria -->
            <v-col cols="6" sm="3">
              <v-card variant="flat" class="stat-card pa-3 text-center bg-surface">
                <div class="d-flex align-center justify-center ga-1 text-caption text-medium-emphasis mb-1">
                  <v-icon icon="mdi-shape-outline" size="16" color="secondary" />
                  <span>Categoria</span>
                </div>
                <div class="text-subtitle-1 font-weight-bold text-grey-darken-3 text-truncate">
                  {{ product.categoria?.nome || 'Geral' }}
                </div>
              </v-card>
            </v-col>

            <!-- Total de Lotes -->
            <v-col cols="6" sm="3">
              <v-card variant="flat" class="stat-card pa-3 text-center bg-surface">
                <div class="d-flex align-center justify-center ga-1 text-caption text-medium-emphasis mb-1">
                  <v-icon icon="mdi-layers-outline" size="16" color="info" />
                  <span>Lotes Totais</span>
                </div>
                <div class="text-subtitle-1 font-weight-bold text-info">
                  {{ product.total_lotes }} {{ product.total_lotes === 1 ? 'lote' : 'lotes' }}
                </div>
              </v-card>
            </v-col>
          </v-row>
        </div>

        <!-- Navigation Tabs -->
        <v-tabs v-model="tab" color="primary" class="px-6 border-b" density="comfortable">
          <v-tab value="geral" prepend-icon="mdi-information-outline">Geral & Armazenamento</v-tab>
          <v-tab value="composicao" prepend-icon="mdi-food-apple-outline">
            Composição & Alérgenos
            <v-badge v-if="product.alergenos.length" color="error" :content="product.alergenos.length" inline class="ml-1" />
          </v-tab>
          <v-tab value="nutrientes" prepend-icon="mdi-nutrition">
            Tabela Nutricional
            <v-badge v-if="product.nutrientes.length" color="primary" :content="product.nutrientes.length" inline class="ml-1" />
          </v-tab>
        </v-tabs>

        <!-- Tab Content -->
        <v-card-text class="pa-6 bg-grey-lighten-5">
          <v-window v-model="tab">
            <!-- ABA 1: Geral & Armazenamento -->
            <v-window-item value="geral">
              <v-row>
                <!-- Descrição -->
                <v-col cols="12">
                  <v-card variant="outlined" class="section-card bg-surface pa-5">
                    <div class="d-flex align-center ga-2 mb-2">
                      <v-icon icon="mdi-text-box-outline" color="primary" size="20" />
                      <span class="text-subtitle-1 font-weight-bold text-grey-darken-3">Descrição do Produto</span>
                    </div>
                    <p
                      class="text-body-1 text-grey-darken-2 mb-0"
                      :class="{ 'text-medium-emphasis font-italic': !product.descricao }"
                    >
                      {{ product.descricao || 'Nenhuma descrição detalhada informada para este produto.' }}
                    </p>
                  </v-card>
                </v-col>

                <!-- Armazenamento / Localização -->
                <v-col cols="12">
                  <v-card variant="outlined" class="section-card bg-surface pa-5">
                    <div class="d-flex align-center ga-2 mb-4">
                      <v-avatar color="secondary" variant="tonal" size="32" rounded="md">
                        <v-icon icon="mdi-warehouse" size="18" />
                      </v-avatar>
                      <span class="text-subtitle-1 font-weight-bold text-grey-darken-3">Localização Preferencial no Armazém</span>
                    </div>

                    <div v-if="resolvedLocation">
                      <div class="d-flex flex-wrap align-center ga-2 mb-3">
                        <v-chip variant="tonal" color="primary" prepend-icon="mdi-ray-start-arrow">
                          Corredor:
                          <strong>&nbsp;{{ resolvedLocation.corredor }}</strong>
                        </v-chip>
                        <v-chip variant="tonal" color="secondary" prepend-icon="mdi-view-grid-outline">
                          Seção:
                          <strong>&nbsp;{{ resolvedLocation.seccao }}</strong>
                        </v-chip>
                        <v-chip variant="tonal" color="info" prepend-icon="mdi-bookshelf">
                          Prateleira:
                          <strong>&nbsp;{{ resolvedLocation.prateleira }}</strong>
                        </v-chip>
                        <v-chip v-if="resolvedLocation.nivel" variant="tonal" color="warning" prepend-icon="mdi-stairs">
                          Nível:
                          <strong>&nbsp;{{ resolvedLocation.nivel }}</strong>
                        </v-chip>
                      </div>
                      <div v-if="resolvedLocation.descricao" class="text-caption text-medium-emphasis mt-2">
                        {{ resolvedLocation.descricao }}
                      </div>
                    </div>

                    <div v-else class="text-body-2 text-medium-emphasis d-flex align-center ga-2 py-2">
                      <v-icon icon="mdi-map-marker-question-outline" size="20" />
                      Nenhuma localização preferencial configurada para este produto.
                    </div>
                  </v-card>
                </v-col>

                <!-- Dados Técnicos Adicionais -->
                <v-col cols="12">
                  <v-card variant="tonal" color="grey" class="pa-4 rounded-lg bg-surface">
                    <v-row dense>
                      <v-col cols="12" sm="4">
                        <div class="text-caption text-medium-emphasis">Unidade de Medida</div>
                        <div class="text-body-2 font-weight-bold text-grey-darken-3">
                          {{ product.unidade_medida?.descricao || '—' }} ({{ product.unidade_medida?.sigla || '—' }})
                        </div>
                      </v-col>
                      <v-col cols="12" sm="4">
                        <div class="text-caption text-medium-emphasis">Tipo de Perecibilidade</div>
                        <div class="text-body-2 font-weight-bold text-grey-darken-3">
                          {{ product.perecivel ? 'Exige controle de validade em cada lote' : 'Validade indeterminada' }}
                        </div>
                      </v-col>
                      <v-col cols="12" sm="4">
                        <div class="text-caption text-medium-emphasis">Identificador (ID)</div>
                        <div class="text-body-2 font-weight-bold text-grey-darken-3">Registro #{{ product.id }}</div>
                      </v-col>
                    </v-row>
                  </v-card>
                </v-col>
              </v-row>
            </v-window-item>

            <!-- ABA 2: Composição & Alérgenos -->
            <v-window-item value="composicao">
              <!-- Alérgenos -->
              <div class="mb-5">
                <div class="d-flex align-center ga-2 mb-3">
                  <v-icon icon="mdi-alert-decagram-outline" color="warning" size="20" />
                  <span class="text-subtitle-1 font-weight-bold text-grey-darken-3">Alérgenos e Restrições</span>
                </div>

                <v-alert
                  v-if="product.alergenos.length"
                  type="warning"
                  variant="tonal"
                  density="comfortable"
                  class="rounded-lg mb-3"
                >
                  <div class="font-weight-medium mb-2">Atenção: Este produto contém os seguintes alérgenos declarados:</div>
                  <div class="d-flex flex-wrap ga-2">
                    <v-chip
                      v-for="item in product.alergenos"
                      :key="item.id"
                      color="error"
                      variant="flat"
                      size="small"
                      prepend-icon="mdi-alert-circle-outline"
                    >
                      {{ item.nome }}
                    </v-chip>
                  </div>
                </v-alert>

                <v-alert
                  v-else
                  type="success"
                  variant="tonal"
                  density="comfortable"
                  class="rounded-lg mb-3"
                  prepend-icon="mdi-check-circle-outline"
                >
                  Nenhum alérgeno cadastrado para este produto.
                </v-alert>
              </div>

              <!-- Ingredientes -->
              <div>
                <div class="d-flex align-center ga-2 mb-3">
                  <v-icon icon="mdi-format-list-numbered" color="primary" size="20" />
                  <span class="text-subtitle-1 font-weight-bold text-grey-darken-3">Lista de Ingredientes</span>
                  <v-chip size="x-small" variant="tonal" color="primary" class="ml-1 font-weight-medium">
                    {{ sortedIngredients.length }} {{ sortedIngredients.length === 1 ? 'item' : 'itens' }}
                  </v-chip>
                </div>

                <v-card v-if="sortedIngredients.length" variant="outlined" class="section-card bg-surface pa-3">
                  <v-list density="compact">
                    <v-list-item v-for="item in sortedIngredients" :key="item.ingrediente_id" class="px-2 py-1">
                      <template #prepend>
                        <v-avatar color="primary" variant="tonal" size="26" class="mr-3 text-caption font-weight-bold">
                          {{ item.ordem }}
                        </v-avatar>
                      </template>
                      <v-list-item-title class="font-weight-medium text-grey-darken-4">
                        {{ item.nome }}
                      </v-list-item-title>
                      <v-list-item-subtitle v-if="item.descricao" class="text-caption text-medium-emphasis">
                        {{ item.descricao }}
                      </v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-card>

                <v-card v-else variant="flat" class="pa-6 text-center bg-surface border rounded-lg">
                  <v-icon icon="mdi-food-off-outline" size="36" class="text-medium-emphasis mb-2" />
                  <div class="text-body-2 text-medium-emphasis">Nenhum ingrediente cadastrado para este produto.</div>
                </v-card>
              </div>
            </v-window-item>

            <!-- ABA 3: Tabela Nutricional -->
            <v-window-item value="nutrientes">
              <div class="d-flex align-center ga-2 mb-3">
                <v-icon icon="mdi-nutrition" color="primary" size="20" />
                <span class="text-subtitle-1 font-weight-bold text-grey-darken-3">Tabela Nutricional</span>
                <span class="text-caption text-medium-emphasis">(Valores declarados por porção de referência)</span>
              </div>

              <v-card v-if="product.nutrientes.length" variant="outlined" class="section-card bg-surface overflow-hidden">
                <v-table density="comfortable" hover>
                  <thead>
                    <tr class="bg-grey-lighten-4">
                      <th class="text-left font-weight-bold text-grey-darken-4">Nutriente / Componente</th>
                      <th class="text-right font-weight-bold text-grey-darken-4">Quantidade</th>
                      <th class="text-left font-weight-bold text-grey-darken-4">Unidade de Medida</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="nutriente in product.nutrientes" :key="nutriente.id">
                      <td class="font-weight-medium text-grey-darken-3">{{ nutriente.nome }}</td>
                      <td class="text-right font-weight-bold text-primary">{{ formatQuantity(nutriente.valor) }}</td>
                      <td class="text-medium-emphasis">{{ nutriente.unidade }}</td>
                    </tr>
                  </tbody>
                </v-table>
              </v-card>

              <v-card v-else variant="flat" class="pa-8 text-center bg-surface border rounded-lg">
                <v-icon icon="mdi-nutrition" size="40" class="text-medium-emphasis mb-2" />
                <div class="text-body-1 font-weight-medium text-grey-darken-3">Sem informações nutricionais</div>
                <div class="text-caption text-medium-emphasis">Nenhum nutriente foi cadastrado para este produto.</div>
              </v-card>
            </v-window-item>
          </v-window>
        </v-card-text>

        <v-divider />

        <!-- Card Actions -->
        <v-card-actions class="pa-5 bg-surface">
          <v-btn variant="text" color="grey-darken-1" @click="close">Fechar</v-btn>
          <v-spacer />
          <v-btn
            :to="`/produtos/${product.id}/editar`"
            color="primary"
            variant="flat"
            prepend-icon="mdi-pencil-outline"
            @click="close"
          >
            Editar produto
          </v-btn>
        </v-card-actions>
      </template>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.product-hero {
  background: linear-gradient(180deg, rgba(86, 8, 148, 0.05) 0%, rgba(255, 255, 255, 1) 100%);
}

.stat-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.section-card {
  border-color: #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
</style>
