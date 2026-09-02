<script lang="ts">
import { defineComponent } from 'vue'

import { produtosApi } from '@/api/produtos'
import PageHeader from '@/components/PageHeader.vue'
import type { CatalogoProduto, LoteInput, ProdutoCreate, ProdutoUpdate } from '@/types/api'
import { getErrorMessage } from '@/utils/errors'

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

export default defineComponent({
  name: 'ProdutoFormView',
  components: { PageHeader },
  data() {
    return {
      form: {
        codigo: '',
        nome: '',
        descricao: null as string | null,
        preco: 0,
        perecivel: false,
        unidade_medida_id: null as number | null,
        categoria_id: null as number | null,
        localizacao_id: null as number | null,
        ativo: true,
      },
      includeLot: false,
      lot: {
        numero_lote: '',
        data_producao: today(),
        data_validade: null,
        ativo: true,
      } as LoteInput,
      catalog: { unidades_medida: [], categorias: [], localizacoes: [] } as CatalogoProduto,
      loading: true,
      saving: false,
      error: '',
    }
  },
  computed: {
    productId(): number | null {
      const value = Number(this.$route.params.id)
      return Number.isInteger(value) && value > 0 ? value : null
    },
    editing(): boolean {
      return this.productId !== null
    },
    title(): string {
      return this.editing ? 'Editar produto' : 'Novo produto'
    },
  },
  watch: {
    'form.perecivel'(value: boolean) {
      if (value && !this.editing) this.includeLot = true
    },
  },
  async mounted() {
    try {
      this.catalog = await produtosApi.catalogo()
      if (this.editing && this.productId) {
        const product = await produtosApi.get(this.productId)
        this.form = {
          codigo: product.codigo,
          nome: product.nome,
          descricao: product.descricao,
          preco: product.preco,
          perecivel: product.perecivel,
          unidade_medida_id: product.unidade_medida_id,
          categoria_id: product.categoria_id,
          localizacao_id: product.localizacao_id,
          ativo: product.ativo,
        }
      }
    } catch (error) {
      this.error = getErrorMessage(error)
    } finally {
      this.loading = false
    }
  },
  methods: {
    validate(): boolean {
      if (
        !this.form.codigo ||
        !this.form.nome ||
        !this.form.unidade_medida_id ||
        !this.form.categoria_id ||
        !this.form.localizacao_id
      ) {
        this.error = 'Preencha todos os campos obrigatórios.'
        return false
      }
      if (this.form.preco < 0) {
        this.error = 'O preço não pode ser negativo.'
        return false
      }
      if (!this.editing && this.includeLot && (!this.lot.numero_lote || !this.lot.data_producao)) {
        this.error = 'Informe o número e a produção do lote inicial.'
        return false
      }
      if (!this.editing && this.form.perecivel && !this.lot.data_validade) {
        this.error = 'Produto perecível exige lote inicial com validade.'
        return false
      }
      return true
    },
    async submit() {
      this.error = ''
      if (!this.validate()) return
      this.saving = true
      try {
        if (this.editing && this.productId) {
          const payload: ProdutoUpdate = {
            codigo: this.form.codigo,
            nome: this.form.nome,
            descricao: this.form.descricao,
            preco: Number(this.form.preco),
            unidade_medida_id: this.form.unidade_medida_id!,
            categoria_id: this.form.categoria_id!,
            localizacao_id: this.form.localizacao_id!,
            ativo: this.form.ativo,
          }
          await produtosApi.update(this.productId, payload)
        } else {
          const payload: ProdutoCreate = {
            ...this.form,
            preco: Number(this.form.preco),
            lote_inicial: this.includeLot ? this.lot : null,
          }
          await produtosApi.create(payload)
        }
        await this.$router.push('/produtos')
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
    <PageHeader :title="title" subtitle="Dados comerciais, classificação e armazenamento." />
    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
    <v-progress-linear v-if="loading" color="primary" indeterminate />
    <v-card v-else class="data-card pa-5 pa-md-7">
      <v-form @submit.prevent="submit">
        <v-row>
          <v-col cols="12" md="4"
            ><v-text-field v-model.trim="form.codigo" label="Código" required
          /></v-col>
          <v-col cols="12" md="8"
            ><v-text-field v-model.trim="form.nome" label="Nome do produto" required
          /></v-col>
          <v-col cols="12"
            ><v-textarea v-model="form.descricao" label="Descrição" rows="2"
          /></v-col>
          <v-col cols="12" md="4"
            ><v-text-field
              v-model.number="form.preco"
              type="number"
              min="0"
              step="0.01"
              prefix="R$"
              label="Preço atual"
              required
          /></v-col>
          <v-col cols="12" md="4"
            ><v-select
              v-model="form.unidade_medida_id"
              :items="catalog.unidades_medida"
              item-title="descricao"
              item-value="id"
              label="Unidade de medida"
              required
          /></v-col>
          <v-col cols="12" md="4"
            ><v-select
              v-model="form.categoria_id"
              :items="catalog.categorias"
              item-title="nome"
              item-value="id"
              label="Categoria"
              required
          /></v-col>
          <v-col cols="12" md="4"
            ><v-select
              v-model="form.localizacao_id"
              :items="catalog.localizacoes"
              :item-title="(item) => `Localização ${item.id} · Prateleira ${item.prateleira_id}`"
              item-value="id"
              label="Localização preferencial"
              required
          /></v-col>
          <v-col cols="6" md="4"
            ><v-switch
              v-model="form.perecivel"
              color="primary"
              label="Produto perecível"
              inset
              :disabled="editing"
          /></v-col>
          <v-col cols="6" md="4"
            ><v-switch v-model="form.ativo" color="primary" label="Produto ativo" inset
          /></v-col>

          <template v-if="!editing">
            <v-col cols="12"><v-divider class="my-2" /></v-col>
            <v-col cols="12"
              ><v-switch
                v-model="includeLot"
                color="primary"
                label="Cadastrar lote inicial"
                inset
                :disabled="form.perecivel"
            /></v-col>
            <template v-if="includeLot">
              <v-col cols="12" md="5"
                ><v-text-field v-model.trim="lot.numero_lote" label="Número do lote" required
              /></v-col>
              <v-col cols="6" md="3"
                ><v-text-field v-model="lot.data_producao" type="date" label="Produção" required
              /></v-col>
              <v-col cols="6" md="4"
                ><v-text-field
                  v-model="lot.data_validade"
                  type="date"
                  label="Validade"
                  :required="form.perecivel"
              /></v-col>
            </template>
          </template>
        </v-row>
        <div class="form-actions">
          <v-btn variant="text" to="/produtos">Cancelar</v-btn
          ><v-btn color="primary" type="submit" :loading="saving">{{
            editing ? 'Salvar alterações' : 'Cadastrar produto'
          }}</v-btn>
        </div>
      </v-form>
    </v-card>
  </div>
</template>
