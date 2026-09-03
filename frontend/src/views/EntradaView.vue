<script lang="ts">
import { defineComponent } from 'vue'

import { produtosApi } from '@/api/produtos'
import { transacoesApi } from '@/api/transacoes'
import PageHeader from '@/components/PageHeader.vue'
import type {
  CatalogoProduto,
  Fornecedor,
  Localizacao,
  Lote,
  LoteInput,
  Produto,
  RegistroEntradaCreate,
} from '@/types/api'
import { getErrorMessage } from '@/utils/errors'
import { toIsoDateTime } from '@/utils/formatters'

function emptyForm(): RegistroEntradaCreate {
  return {
    lote_id: null,
    fornecedor_id: null,
    localizacao_id: null,
    quantidade: 1,
    data_entrada: null,
    tipo_entrada: 'compra',
    observacao: null,
    preco_custo: 0,
  }
}

function emptyLotForm(): LoteInput {
  return {
    numero_lote: '',
    data_producao: new Date().toISOString().slice(0, 10),
    data_validade: null,
    ativo: true,
  }
}

export default defineComponent({
  name: 'EntradaView',
  components: { PageHeader },
  data() {
    return {
      products: [] as Produto[],
      suppliers: [] as Fornecedor[],
      lots: [] as Lote[],
      catalog: {
        unidades_medida: [],
        categorias: [],
        localizacoes: [],
        ingredientes: [],
        alergenos: [],
      } as CatalogoProduto,
      productId: null as number | null,
      form: emptyForm(),
      transactionDate: '',
      loading: true,
      loadingLots: false,
      saving: false,
      error: '',
      success: '',
      newLotDialog: false,
      newLotLoading: false,
      newLotError: '',
      newLotForm: emptyLotForm(),
    }
  },
  computed: {
    selectedProduct(): Produto | undefined {
      return this.products.find((p) => p.id === this.productId)
    },
  },
  watch: {
    productId(value: number | null) {
      this.form.lote_id = null
      if (value) {
        void this.loadLots(value)
      } else this.lots = []
    },
  },
  async mounted() {
    try {
      const [products, suppliers, catalog] = await Promise.all([
        produtosApi.listar({ page: 1, size: 100 }),
        transacoesApi.fornecedores(),
        produtosApi.catalogo(),
      ])
      this.products = products.items.filter((item) => item.ativo)
      this.suppliers = suppliers.filter((item) => item.ativo)
      this.catalog = catalog
    } catch (error) {
      this.error = getErrorMessage(error)
    } finally {
      this.loading = false
    }
  },
  methods: {
    locationLabel(location: Localizacao): string {
      const level = location.nivel ? ` / Nível ${location.nivel}` : ''
      return `${location.corredor} / ${location.seccao} / ${location.prateleira}${level}`
    },
    async loadLots(productId: number) {
      this.loadingLots = true
      try {
        this.lots = (await produtosApi.listarLotes(productId)).filter((item) => item.ativo)
      } catch (error) {
        this.error = getErrorMessage(error)
      } finally {
        this.loadingLots = false
      }
    },
    openNewLotDialog() {
      if (!this.productId) return
      this.newLotForm = emptyLotForm()
      this.newLotError = ''
      this.newLotDialog = true
    },
    async createNewLot() {
      if (
        !this.productId ||
        !this.newLotForm.numero_lote.trim() ||
        !this.newLotForm.data_producao
      ) {
        this.newLotError = 'Informe o número e a data de produção do lote.'
        return
      }
      if (this.selectedProduct?.perecivel && !this.newLotForm.data_validade) {
        this.newLotError = 'Produtos perecíveis exigem data de validade.'
        return
      }
      this.newLotLoading = true
      this.newLotError = ''
      try {
        const created = await produtosApi.createLote(this.productId, {
          ...this.newLotForm,
          numero_lote: this.newLotForm.numero_lote.trim(),
        })
        await this.loadLots(this.productId)
        this.form.lote_id = created.id
        this.newLotDialog = false
        this.success = `Lote "${created.numero_lote}" cadastrado e selecionado com sucesso.`
      } catch (error) {
        this.newLotError = getErrorMessage(error)
      } finally {
        this.newLotLoading = false
      }
    },
    async submit() {
      this.error = ''
      this.success = ''
      if (
        !this.productId ||
        !this.form.lote_id ||
        !this.form.fornecedor_id ||
        this.form.quantidade <= 0
      ) {
        this.error = 'Selecione produto, lote e fornecedor e informe uma quantidade válida.'
        return
      }
      this.saving = true
      try {
        await transacoesApi.registrarEntrada({
          ...this.form,
          quantidade: Number(this.form.quantidade),
          preco_custo: Number(this.form.preco_custo),
          data_entrada: toIsoDateTime(this.transactionDate),
          observacao: this.form.observacao || null,
        })
        this.form = emptyForm()
        this.productId = null
        this.transactionDate = ''
        this.success = 'Entrada registrada com sucesso.'
      } catch (error) {
        this.error = getErrorMessage(error)
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
      title="Registrar entrada"
      subtitle="Adicione itens ao estoque com origem, lote e custo rastreáveis."
    />
    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
    <v-alert
      v-if="success"
      type="success"
      variant="tonal"
      closable
      class="mb-4"
      @click:close="success = ''"
      >{{ success }}</v-alert
    >
    <v-progress-linear v-if="loading" color="primary" indeterminate />
    <v-card v-else class="data-card pa-5 pa-md-7">
      <v-form @submit.prevent="submit">
        <v-row>
          <v-col cols="12" md="6"
            ><v-autocomplete
              v-model="productId"
              :items="products"
              item-title="nome"
              item-value="id"
              label="Produto"
              required
          /></v-col>
          <v-col cols="12" md="6">
            <div class="d-flex align-start ga-2">
              <v-select
                v-model="form.lote_id"
                :items="lots"
                item-title="numero_lote"
                item-value="id"
                label="Lote"
                :loading="loadingLots"
                :disabled="!productId"
                required
                class="flex-grow-1"
                hide-details="auto"
              />
              <v-btn
                color="secondary"
                variant="tonal"
                prepend-icon="mdi-plus"
                :disabled="!productId"
                height="56"
                title="Cadastrar novo lote para este produto"
                @click="openNewLotDialog"
              >
                Novo lote
              </v-btn>
            </div>
            <v-alert
              v-if="productId && !loadingLots && lots.length === 0"
              type="info"
              variant="tonal"
              density="compact"
              class="mt-2"
            >
              Nenhum lote cadastrado para este produto.
              <a
                href="javascript:void(0)"
                class="font-weight-bold ml-1 text-decoration-underline"
                @click="openNewLotDialog"
              >
                Cadastrar lote agora
              </a>
            </v-alert>
          </v-col>
          <v-col cols="12" md="6"
            ><v-autocomplete
              v-model="form.fornecedor_id"
              :items="suppliers"
              item-title="nome_empresa"
              item-value="id"
              label="Fornecedor"
              required
          /></v-col>
          <v-col cols="12" md="6"
            ><v-select
              v-model="form.localizacao_id"
              :items="catalog.localizacoes"
              :item-title="locationLabel"
              item-value="id"
              label="Localização (opcional)"
              clearable
              hint="Vazia: usa a localização preferencial do produto"
              persistent-hint
          /></v-col>
          <v-col cols="12" md="3"
            ><v-text-field
              v-model.number="form.quantidade"
              type="number"
              min="0.001"
              step="0.001"
              label="Quantidade"
              required
          /></v-col>
          <v-col cols="12" md="3"
            ><v-text-field
              v-model="transactionDate"
              type="datetime-local"
              label="Data e hora (opcional)"
          /></v-col>
          <v-col cols="12" md="3"
            ><v-text-field v-model.trim="form.tipo_entrada" label="Tipo de entrada" required
          /></v-col>
          <v-col cols="6" md="3"
            ><v-text-field
              v-model.number="form.preco_custo"
              type="number"
              min="0"
              step="0.01"
              prefix="R$"
              label="Preço de custo"
              required
          /></v-col>
          <v-col cols="12" md="9"
            ><v-textarea v-model="form.observacao" label="Observação" rows="2" maxlength="500"
          /></v-col>
        </v-row>
        <div class="form-actions">
          <v-btn variant="text" to="/estoque">Cancelar</v-btn
          ><v-btn color="primary" prepend-icon="mdi-package-down" type="submit" :loading="saving"
            >Registrar entrada</v-btn
          >
        </div>
      </v-form>
    </v-card>

    <v-dialog v-model="newLotDialog" max-width="560">
      <v-card>
        <v-card-title class="pa-5 pb-3">
          <div>
            <div class="text-h6 font-weight-bold">Novo lote de entrada</div>
            <div class="text-caption text-medium-emphasis">
              Produto: {{ selectedProduct?.nome }} ({{ selectedProduct?.codigo }})
            </div>
          </div>
        </v-card-title>
        <v-card-text class="pt-0">
          <v-alert v-if="newLotError" type="error" variant="tonal" density="compact" class="mb-4">
            {{ newLotError }}
          </v-alert>

          <v-alert
            v-if="selectedProduct?.perecivel"
            type="warning"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            Este produto é perecível. A data de validade é obrigatória.
          </v-alert>

          <v-row>
            <v-col cols="12">
              <v-text-field v-model.trim="newLotForm.numero_lote" label="Número do lote" required />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="newLotForm.data_producao"
                type="date"
                label="Data de fabricação / produção"
                required
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="newLotForm.data_validade"
                type="date"
                label="Data de validade"
                :required="selectedProduct?.perecivel"
              />
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions class="pa-5 pt-0">
          <v-spacer />
          <v-btn variant="text" :disabled="newLotLoading" @click="newLotDialog = false">
            Cancelar
          </v-btn>
          <v-btn
            color="primary"
            prepend-icon="mdi-check"
            :loading="newLotLoading"
            @click="createNewLot"
          >
            Cadastrar e selecionar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
