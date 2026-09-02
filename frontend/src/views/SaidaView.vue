<script lang="ts">
import { defineComponent } from 'vue'

import { produtosApi } from '@/api/produtos'
import { transacoesApi } from '@/api/transacoes'
import PageHeader from '@/components/PageHeader.vue'
import type { EstoqueEntrada, Lote, Produto, RegistroSaidaCreate } from '@/types/api'
import { getErrorMessage } from '@/utils/errors'
import { formatQuantity, toIsoDateTime } from '@/utils/formatters'

function emptyForm(): RegistroSaidaCreate {
  return { entrada_id: null, quantidade: 1, data_saida: null, tipo_saida: 'venda', preco_venda: 0 }
}

export default defineComponent({
  name: 'SaidaView',
  components: { PageHeader },
  data() {
    return {
      products: [] as Produto[],
      lots: [] as Lote[],
      entries: [] as EstoqueEntrada[],
      productId: null as number | null,
      form: emptyForm(),
      transactionDate: '',
      loading: true,
      loadingEntries: false,
      saving: false,
      error: '',
      success: '',
    }
  },
  computed: {
    selectedEntry(): EstoqueEntrada | undefined {
      return this.entries.find((item) => item.entrada_id === this.form.entrada_id)
    },
  },
  watch: {
    productId(value: number | null) {
      this.form.entrada_id = null
      if (value) {
        const product = this.products.find((item) => item.id === value)
        if (product) this.form.preco_venda = product.preco
        void this.loadEntries(value)
      } else {
        this.entries = []
        this.lots = []
      }
    },
  },
  async mounted() {
    try {
      const response = await produtosApi.listar({ page: 1, size: 100 })
      this.products = response.items.filter((item) => item.ativo && item.quantidade_estoque > 0)
    } catch (error) {
      this.error = getErrorMessage(error)
    } finally {
      this.loading = false
    }
  },
  methods: {
    formatQuantity,
    entryLabel(entry: EstoqueEntrada): string {
      const lot = this.lots.find((item) => item.id === entry.lote_id)
      return `Entrada #${entry.entrada_id} · Lote ${lot?.numero_lote ?? entry.lote_id} · Saldo ${formatQuantity(entry.quantidade)}`
    },
    async loadEntries(productId: number) {
      this.loadingEntries = true
      this.error = ''
      try {
        const [entries, lots] = await Promise.all([
          transacoesApi.entradasDisponiveis(productId),
          produtosApi.listarLotes(productId),
        ])
        this.entries = entries
        this.lots = lots
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.loadingEntries = false
      }
    },
    async submit() {
      this.error = ''
      this.success = ''
      if (!this.productId || !this.form.entrada_id || this.form.quantidade <= 0) {
        this.error = 'Selecione o produto e a entrada e informe uma quantidade válida.'
        return
      }
      if (this.selectedEntry && this.form.quantidade > this.selectedEntry.quantidade) {
        this.error = `Saldo insuficiente. Disponível: ${formatQuantity(this.selectedEntry.quantidade)}.`
        return
      }
      this.saving = true
      try {
        await transacoesApi.registrarSaida({
          ...this.form,
          quantidade: Number(this.form.quantidade),
          preco_venda: Number(this.form.preco_venda),
          data_saida: toIsoDateTime(this.transactionDate),
        })
        this.form = emptyForm()
        this.productId = null
        this.transactionDate = ''
        this.success = 'Saída registrada com sucesso.'
      } catch (error) {
        this.error = getErrorMessage(error)
        if (this.productId) await this.loadEntries(this.productId)
      } finally {
        this.saving = false
      }
    },
  },
})
</script>

<template>
  <div>
    <PageHeader
      title="Registrar saída"
      subtitle="Retire itens de uma entrada que ainda possui saldo disponível."
    />
    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
    <v-alert
      v-if="success"
      type="success"
      variant="tonal"
      closable
      class="mb-4"
      @click:close="success = ''"
    >
      {{ success }}
    </v-alert>
    <v-progress-linear v-if="loading" color="primary" indeterminate />
    <v-card v-else class="data-card pa-5 pa-md-7">
      <v-form @submit.prevent="submit">
        <v-row>
          <v-col cols="12" md="6">
            <v-autocomplete
              v-model="productId"
              :items="products"
              item-title="nome"
              item-value="id"
              label="Produto com estoque"
              required
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-select
              v-model="form.entrada_id"
              :items="entries"
              :item-title="entryLabel"
              item-value="entrada_id"
              label="Entrada de origem"
              :loading="loadingEntries"
              :disabled="!productId"
              required
            />
            <v-alert
              v-if="productId && !loadingEntries && entries.length === 0"
              type="warning"
              variant="tonal"
              density="compact"
              >Nenhuma entrada com saldo disponível.
            </v-alert>
          </v-col>
          <v-col v-if="selectedEntry" cols="12">
            <v-alert type="info" variant="tonal" density="compact">
              Saldo disponível nesta entrada:
              <strong>{{ formatQuantity(selectedEntry.quantidade) }}</strong>
            </v-alert>
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model.number="form.quantidade"
              type="number"
              min="0.001"
              :max="selectedEntry?.quantidade"
              step="0.001"
              label="Quantidade"
              required
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="transactionDate"
              type="datetime-local"
              label="Data e hora (opcional)"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field v-model.trim="form.tipo_saida" label="Tipo de saída" required />
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model.number="form.preco_venda"
              type="number"
              min="0"
              step="0.01"
              prefix="R$"
              label="Preço de venda"
              required
            />
          </v-col>
        </v-row>
        <div class="form-actions">
          <v-btn variant="text" to="/estoque">Cancelar</v-btn>
          <v-btn color="primary" prepend-icon="mdi-package-up" type="submit" :loading="saving">
            Registrar saída
          </v-btn>
        </div>
      </v-form>
    </v-card>
  </div>
</template>
