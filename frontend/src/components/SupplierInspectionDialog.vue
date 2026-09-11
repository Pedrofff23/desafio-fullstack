<script lang="ts">
import { defineComponent, type PropType } from 'vue';

import ActiveStatusChip from '@/components/ActiveStatusChip.vue';
import type { Fornecedor } from '@/types/api';
import { formatCepInput, formatContact, formatDateTime } from '@/utils/formatters';

export default defineComponent({
  name: 'SupplierInspectionDialog',
  components: { ActiveStatusChip },
  props: {
    modelValue: { type: Boolean, required: true },
    supplier: { type: Object as PropType<Fornecedor | null>, default: null },
    loading: { type: Boolean, default: false }
  },
  emits: ['update:modelValue', 'edit'],
  data() {
    return {
      copied: false,
      copyTimeout: null as ReturnType<typeof setTimeout> | null
    };
  },
  computed: {
    companyInitials(): string {
      const name = this.supplier?.nome_empresa?.trim();
      if (!name) return 'FO';
      const words = name.split(/\s+/).filter(Boolean);
      const first = words[0];
      if (!first) return 'FO';
      if (words.length === 1) return first.slice(0, 2).toUpperCase();
      const second = words[1] ?? '';
      return `${first[0] || ''}${second[0] || ''}`.toUpperCase() || 'FO';
    },
    rawPhone(): string {
      if (!this.supplier?.contato) return '';
      const c = this.supplier.contato;
      const cc = c.codigo_pais ? `+${c.codigo_pais.replace(/\D/g, '')}` : '';
      const ddd = c.ddd ? c.ddd.replace(/\D/g, '') : '';
      const num = c.numero ? c.numero.replace(/\D/g, '') : '';
      return `${cc}${ddd}${num}`;
    }
  },
  beforeUnmount() {
    if (this.copyTimeout) {
      clearTimeout(this.copyTimeout);
    }
  },
  methods: {
    formatContact,
    formatDateTime,
    formatCepInput,
    close() {
      this.$emit('update:modelValue', false);
    },
    onEdit() {
      if (this.supplier) {
        this.close();
        this.$emit('edit', this.supplier);
      }
    },
    async copyPhone() {
      if (!this.supplier?.contato) return;
      const text = this.formatContact(this.supplier.contato);
      if (!text || text === '—') return;

      try {
        if (navigator?.clipboard?.writeText) {
          await navigator.clipboard.writeText(text);
        } else {
          const textarea = document.createElement('textarea');
          textarea.value = text;
          document.body.appendChild(textarea);
          textarea.select();
          document.execCommand('copy');
          document.body.removeChild(textarea);
        }
        this.copied = true;
        if (this.copyTimeout) clearTimeout(this.copyTimeout);
        this.copyTimeout = setTimeout(() => {
          this.copied = false;
        }, 2500);
      } catch {
        // Silently fail if clipboard permission is denied
      }
    }
  }
});
</script>

<template>
  <v-dialog :model-value="modelValue" max-width="720" @update:model-value="$emit('update:modelValue', $event)">
    <v-card class="supplier-inspection-dialog overflow-hidden" rounded="xl">
      <!-- Loading indicator -->
      <v-progress-linear v-if="loading" indeterminate color="primary" />

      <template v-if="supplier">
        <!-- Hero Header -->
        <div class="supplier-hero px-6 pt-6 pb-5">
          <div class="d-flex align-start justify-space-between mb-4">
            <div class="d-flex align-center ga-4">
              <v-avatar color="primary" size="56" rounded="lg" class="elevation-2 text-white font-weight-bold text-h6">
                {{ companyInitials }}
              </v-avatar>
              <div>
                <div class="d-flex align-center ga-2 flex-wrap">
                  <h2 class="text-h5 font-weight-bold text-grey-darken-4 mb-0">{{ supplier.nome_empresa }}</h2>
                  <v-chip size="x-small" variant="tonal" color="primary" class="font-weight-medium">ID #{{ supplier.id }}</v-chip>
                </div>
                <div class="text-caption text-medium-emphasis mt-1 d-flex align-center ga-2 flex-wrap">
                  <span class="d-inline-flex align-center ga-1">
                    <v-icon icon="mdi-calendar-clock-outline" size="14" />
                    Cadastrado em {{ formatDateTime(supplier.data_cadastro) }}
                  </span>
                </div>
              </div>
            </div>
            <v-btn icon="mdi-close" variant="text" density="comfortable" aria-label="Fechar" @click="close" />
          </div>

          <!-- Status row -->
          <div class="d-flex align-center ga-2 flex-wrap">
            <ActiveStatusChip :active="supplier.ativo" />
            <v-chip
              size="small"
              variant="tonal"
              :color="supplier.ativo ? 'success' : 'default'"
              :prepend-icon="supplier.ativo ? 'mdi-truck-check-outline' : 'mdi-truck-remove-outline'"
            >
              {{ supplier.ativo ? 'Habilitado para entradas' : 'Inativo para compras' }}
            </v-chip>
          </div>
        </div>

        <v-divider />

        <!-- Body content with cards -->
        <v-card-text class="pa-6 bg-grey-lighten-5">
          <v-row>
            <!-- Card Contato -->
            <v-col cols="12">
              <v-card variant="outlined" class="info-section-card bg-surface pa-5">
                <div class="section-title d-flex align-center ga-2 mb-3">
                  <v-avatar color="primary" variant="tonal" size="32" rounded="md">
                    <v-icon icon="mdi-phone-outline" size="18" />
                  </v-avatar>
                  <span class="text-subtitle-1 font-weight-bold text-grey-darken-3">Contato Comercial</span>
                </div>

                <div class="d-flex flex-wrap align-center justify-space-between ga-3 pt-1">
                  <div class="contact-value-box">
                    <div class="text-caption text-medium-emphasis">Telefone / WhatsApp</div>
                    <div class="text-h6 font-weight-bold text-grey-darken-4">
                      {{ formatContact(supplier.contato) }}
                    </div>
                  </div>

                  <div class="d-flex align-center ga-2">
                    <v-btn
                      v-if="supplier.contato?.numero"
                      size="small"
                      variant="tonal"
                      :color="copied ? 'success' : 'primary'"
                      :prepend-icon="copied ? 'mdi-check' : 'mdi-content-copy'"
                      @click="copyPhone"
                    >
                      {{ copied ? 'Copiado!' : 'Copiar telefone' }}
                    </v-btn>
                    <v-btn
                      v-if="rawPhone"
                      :href="`tel:${rawPhone}`"
                      tag="a"
                      size="small"
                      variant="outlined"
                      color="primary"
                      prepend-icon="mdi-phone-outgoing"
                    >
                      Ligar
                    </v-btn>
                  </div>
                </div>

                <div
                  v-if="supplier.contato?.ddd || supplier.contato?.codigo_pais"
                  class="mt-3 pt-3 border-t d-flex ga-4 text-caption text-medium-emphasis"
                >
                  <span>
                    <strong>Código País:</strong>
                    +{{ supplier.contato?.codigo_pais || '55' }}
                  </span>
                  <span>
                    <strong>DDD:</strong>
                    {{ supplier.contato?.ddd || '—' }}
                  </span>
                </div>
              </v-card>
            </v-col>

            <!-- Card Endereço -->
            <v-col cols="12">
              <v-card variant="outlined" class="info-section-card bg-surface pa-5">
                <div class="section-title d-flex align-center ga-2 mb-4">
                  <v-avatar color="secondary" variant="tonal" size="32" rounded="md">
                    <v-icon icon="mdi-map-marker-radius-outline" size="18" />
                  </v-avatar>
                  <span class="text-subtitle-1 font-weight-bold text-grey-darken-3">Endereço & Localização</span>
                </div>

                <v-row dense>
                  <v-col cols="12" sm="8">
                    <div class="text-caption text-medium-emphasis">Logradouro e Número</div>
                    <div class="text-body-1 font-weight-medium text-grey-darken-4">
                      {{ supplier.endereco.logradouro }}, {{ supplier.endereco.numero }}
                    </div>
                  </v-col>

                  <v-col cols="12" sm="4">
                    <div class="text-caption text-medium-emphasis">CEP</div>
                    <div class="text-body-1 font-weight-medium text-grey-darken-4">
                      <v-chip size="small" variant="tonal" color="secondary" prepend-icon="mdi-mailbox-outline">
                        {{ formatCepInput(supplier.endereco.cep) }}
                      </v-chip>
                    </div>
                  </v-col>

                  <v-col v-if="supplier.endereco.complemento" cols="12">
                    <div class="text-caption text-medium-emphasis">Complemento</div>
                    <div class="text-body-2 text-grey-darken-3">{{ supplier.endereco.complemento }}</div>
                  </v-col>

                  <v-col cols="12" sm="6" class="mt-2">
                    <div class="text-caption text-medium-emphasis">Bairro</div>
                    <div class="text-body-2 font-weight-medium text-grey-darken-3">{{ supplier.endereco.bairro }}</div>
                  </v-col>

                  <v-col cols="12" sm="6" class="mt-2">
                    <div class="text-caption text-medium-emphasis">Cidade / UF</div>
                    <div class="text-body-2 font-weight-medium text-grey-darken-3 d-flex align-center ga-1">
                      <v-icon icon="mdi-city-variant-outline" size="16" class="text-medium-emphasis" />
                      {{ supplier.endereco.cidade.nome }}
                    </div>
                  </v-col>
                </v-row>
              </v-card>
            </v-col>

            <!-- Card Operacional -->
            <v-col cols="12">
              <v-card variant="tonal" :color="supplier.ativo ? 'primary' : 'grey'" class="pa-4 rounded-lg">
                <div class="d-flex align-center ga-3">
                  <v-icon :icon="supplier.ativo ? 'mdi-shield-check-outline' : 'mdi-alert-circle-outline'" size="24" />
                  <div>
                    <div class="text-subtitle-2 font-weight-bold">
                      {{ supplier.ativo ? 'Parceiro Regular' : 'Fornecedor Desativado' }}
                    </div>
                    <div class="text-caption">
                      {{
                        supplier.ativo
                          ? 'Este fornecedor está elegível para fornecimento de mercadorias no registro de novas entradas.'
                          : 'Este fornecedor está inativo e não deve receber novos pedidos até regularização.'
                      }}
                    </div>
                  </div>
                </div>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>

        <v-divider />

        <!-- Modal Actions -->
        <v-card-actions class="pa-5 bg-surface">
          <v-btn variant="text" color="grey-darken-1" @click="close">Fechar</v-btn>
          <v-spacer />
          <v-btn color="primary" prepend-icon="mdi-pencil-outline" variant="flat" @click="onEdit">Editar fornecedor</v-btn>
          <v-btn
            :to="`/fornecedores/${supplier.id}/editar`"
            color="primary"
            prepend-icon="mdi-pencil-outline"
            variant="flat"
            @click="close"
          >
            Editar fornecedor
          </v-btn>
        </v-card-actions>
      </template>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.supplier-hero {
  background: linear-gradient(180deg, rgba(86, 8, 148, 0.05) 0%, rgba(255, 255, 255, 1) 100%);
}

.info-section-card {
  border-color: #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.contact-value-box {
  min-width: 200px;
}
</style>
