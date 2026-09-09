<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'SearchFilterCard',
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    label: {
      type: String,
      default: 'Pesquisar'
    },
    placeholder: {
      type: String,
      default: ''
    },
    loading: {
      type: Boolean,
      default: false
    },
    hideClear: {
      type: Boolean,
      default: false
    },
    hideSearchInput: {
      type: Boolean,
      default: false
    },
    grid: {
      type: Boolean,
      default: false
    },
    cols: {
      type: [Number, String],
      default: 12
    },
    md: {
      type: [Number, String],
      default: ''
    }
  },
  emits: ['update:modelValue', 'search', 'clear'],
  computed: {
    searchQuery: {
      get(): string {
        return this.modelValue;
      },
      set(val: string) {
        this.$emit('update:modelValue', val || '');
      }
    },
    computedMd(): number | string {
      if (this.md) return this.md;
      return this.$slots.default ? 4 : 10;
    }
  },
  methods: {
    onSearch() {
      this.$emit('search');
    },
    onClear() {
      this.$emit('update:modelValue', '');
      this.$emit('clear');
    }
  }
});
</script>

<template>
  <v-card class="data-card pa-4 mb-4">
    <v-form @submit.prevent="onSearch">
      <v-row v-if="grid">
        <v-col v-if="!hideSearchInput" :cols="cols" :md="computedMd">
          <v-text-field
            v-model.trim="searchQuery"
            :label="label"
            prepend-inner-icon="mdi-magnify"
            hide-details
            clearable
            @click:clear="onClear"
            @keydown.enter="onSearch"
          />
        </v-col>

        <slot />

        <v-col cols="12" class="d-flex ga-2 align-center justify-end">
          <v-btn
            v-if="!hideClear"
            variant="text"
            title="Limpar filtros"
            @click="onClear"
          >
            Limpar
          </v-btn>
          <v-btn
            color="#560894"
            type="submit"
            prepend-icon="mdi-magnify"
            :loading="loading"
          >
            Filtrar
          </v-btn>
        </v-col>
      </v-row>

      <v-row v-else align="center">
        <v-col v-if="!hideSearchInput" :cols="cols" :md="computedMd">
          <v-text-field
            v-model.trim="searchQuery"
            :label="label"
            prepend-inner-icon="mdi-magnify"
            hide-details
            clearable
            @click:clear="onClear"
            @keydown.enter="onSearch"
          />
        </v-col>

        <slot />

        <v-col cols="12" :md="$slots.default ? 'auto' : 2" class="d-flex ga-1 align-center justify-end ml-auto">
          <v-btn
            icon="mdi-magnify"
            color="#560894"
            type="submit"
            :loading="loading"
            title="Pesquisar"
          />
          <v-btn
            v-if="!hideClear"
            icon="mdi-filter-off-outline"
            variant="text"
            title="Limpar filtros"
            @click="onClear"
          />
        </v-col>
      </v-row>
    </v-form>
  </v-card>
</template>
