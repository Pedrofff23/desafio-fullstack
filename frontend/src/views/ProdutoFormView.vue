<script lang="ts">
import { defineComponent } from 'vue'

import { produtosApi } from '@/api/produtos'
import PageHeader from '@/components/PageHeader.vue'
import type {
  CatalogoProduto,
  Localizacao,
  LoteInput,
  NutrienteInput,
  ProdutoCreate,
  ProdutoUpdate,
} from '@/types/api'
import { getErrorMessage } from '@/utils/errors'

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

function emptyCatalog(): CatalogoProduto {
  return {
    unidades_medida: [],
    categorias: [],
    localizacoes: [],
    ingredientes: [],
    alergenos: [],
  }
}

function emptyNutrient(): NutrienteInput {
  return { nome: '', unidade: '', valor: 0 }
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
      nutrientes: [] as NutrienteInput[],
      ingredienteIds: [] as number[],
      alergenoIds: [] as number[],
      catalog: emptyCatalog(),
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
        this.nutrientes = product.nutrientes.map(({ nome, unidade, valor }) => ({
          nome,
          unidade,
          valor,
        }))
        this.ingredienteIds = product.ingredientes
          .slice()
          .sort((a, b) => a.ordem - b.ordem)
          .map((item) => item.ingrediente_id)
        this.alergenoIds = product.alergenos.map((item) => item.id)
      }
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
    addNutrient() {
      this.nutrientes.push(emptyNutrient())
    },
    removeNutrient(index: number) {
      this.nutrientes.splice(index, 1)
    },
    ingredientName(id: number): string {
      return this.catalog.ingredientes.find((item) => item.id === id)?.nome ?? `Ingrediente ${id}`
    },
    moveIngredient(index: number, direction: -1 | 1) {
      const target = index + direction
      if (target < 0 || target >= this.ingredienteIds.length) return
      const ingredientId = this.ingredienteIds[index]
      if (ingredientId === undefined) return
      this.ingredienteIds.splice(index, 1)
      this.ingredienteIds.splice(target, 0, ingredientId)
    },
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
      if (this.nutrientes.some((item) => !item.nome.trim() || !item.unidade.trim())) {
        this.error = 'Preencha o nome e a unidade de todos os nutrientes.'
        return false
      }
      return true
    },
    async submit() {
      this.error = ''
      if (!this.validate()) return
      this.saving = true
      try {
        const composition = {
          nutrientes: this.nutrientes.map((item) => ({
            nome: item.nome.trim(),
            unidade: item.unidade.trim(),
            valor: Number(item.valor),
          })),
          ingredientes: this.ingredienteIds.map((ingrediente_id, index) => ({
            ingrediente_id,
            ordem: index + 1,
          })),
          alergeno_ids: [...this.alergenoIds],
        }
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
            ...composition,
          }
          await produtosApi.update(this.productId, payload)
        } else {
          const payload: ProdutoCreate = {
            ...this.form,
            preco: Number(this.form.preco),
            lote_inicial: this.includeLot ? this.lot : null,
            ...composition,
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
              :item-title="locationLabel"
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

          <v-col cols="12"><v-divider class="my-2" /></v-col>
          <v-col cols="12">
            <div class="d-flex align-center justify-space-between mb-3">
              <div>
                <div class="text-h6">Informações alimentícias</div>
                <div class="text-body-2 text-medium-emphasis">
                  Ingredientes, alérgenos e valores nutricionais do produto.
                </div>
              </div>
              <v-btn variant="outlined" prepend-icon="mdi-plus" @click="addNutrient">
                Nutriente
              </v-btn>
            </div>
          </v-col>

          <v-col cols="12" md="6">
            <v-autocomplete
              v-model="ingredienteIds"
              :items="catalog.ingredientes"
              item-title="nome"
              item-value="id"
              label="Ingredientes"
              hint="Use as setas abaixo para definir a ordem da composição."
              persistent-hint
              multiple
              chips
              closable-chips
            />
            <v-list v-if="ingredienteIds.length" density="compact" class="mt-2">
              <v-list-item
                v-for="(ingredienteId, index) in ingredienteIds"
                :key="ingredienteId"
                :title="`${index + 1}. ${ingredientName(ingredienteId)}`"
              >
                <template #append>
                  <v-btn
                    icon="mdi-chevron-up"
                    size="x-small"
                    variant="text"
                    title="Mover ingrediente para cima"
                    :disabled="index === 0"
                    @click="moveIngredient(index, -1)"
                  />
                  <v-btn
                    icon="mdi-chevron-down"
                    size="x-small"
                    variant="text"
                    title="Mover ingrediente para baixo"
                    :disabled="index === ingredienteIds.length - 1"
                    @click="moveIngredient(index, 1)"
                  />
                </template>
              </v-list-item>
            </v-list>
          </v-col>
          <v-col cols="12" md="6">
            <v-autocomplete
              v-model="alergenoIds"
              :items="catalog.alergenos"
              item-title="nome"
              item-value="id"
              label="Alérgenos"
              multiple
              chips
              closable-chips
            />
          </v-col>

          <v-col v-if="nutrientes.length === 0" cols="12">
            <v-alert type="info" variant="tonal" density="compact">
              Nenhuma informação nutricional adicionada.
            </v-alert>
          </v-col>
          <template v-for="(nutriente, index) in nutrientes" :key="index">
            <v-col cols="12" md="5">
              <v-text-field v-model.trim="nutriente.nome" label="Nutriente" />
            </v-col>
            <v-col cols="5" md="3">
              <v-text-field v-model.trim="nutriente.unidade" label="Unidade" />
            </v-col>
            <v-col cols="5" md="3">
              <v-text-field
                v-model.number="nutriente.valor"
                type="number"
                min="0"
                step="0.001"
                label="Valor"
              />
            </v-col>
            <v-col cols="2" md="1" class="d-flex align-center justify-end">
              <v-btn
                icon="mdi-delete-outline"
                color="error"
                variant="text"
                title="Remover nutriente"
                @click="removeNutrient(index)"
              />
            </v-col>
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
