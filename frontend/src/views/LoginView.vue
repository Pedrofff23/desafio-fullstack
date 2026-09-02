<script lang="ts">
import { defineComponent } from 'vue'
import { mapStores } from 'pinia'

import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/utils/errors'

export default defineComponent({
  name: 'LoginView',
  data() {
    return {
      email: '',
      senha: '',
      showPassword: false,
      error: '',
    }
  },
  computed: {
    ...mapStores(useAuthStore),
  },
  methods: {
    async submit() {
      this.error = ''
      if (!this.email || !this.senha) {
        this.error = 'Informe e-mail e senha.'
        return
      }
      try {
        await this.authStore.entrar(this.email, this.senha)
        const redirect =
          typeof this.$route.query.redirect === 'string' ? this.$route.query.redirect : '/estoque'
        await this.$router.replace(redirect)
      } catch (error) {
        this.error = getErrorMessage(error)
      }
    },
  },
})
</script>

<template>
  <v-main class="login-page">
    <v-container class="fill-height pa-4">
      <v-row align="center" justify="center">
        <v-col cols="12" sm="9" md="6" lg="4">
          <v-card class="login-card pa-6 pa-md-9">
            <div class="d-flex align-center ga-3 mb-7">
              <v-avatar color="primary" rounded="lg" size="52">
                <v-icon icon="mdi-warehouse" size="28" />
              </v-avatar>
              <div>
                <div class="text-h5 font-weight-bold">Estoque Vivo</div>
                <div class="text-body-2 text-medium-emphasis">Gestão clara e confiável</div>
              </div>
            </div>

            <h1 class="text-h4 font-weight-bold mb-2">Boas-vindas</h1>
            <p class="text-body-1 text-medium-emphasis mb-7">
              Entre para acompanhar produtos e movimentações.
            </p>

            <v-alert v-if="error" type="error" variant="tonal" class="mb-5">
              {{ error }}
            </v-alert>

            <v-form @submit.prevent="submit">
              <v-text-field
                v-model.trim="email"
                type="email"
                label="E-mail"
                prepend-inner-icon="mdi-email-outline"
                autocomplete="email"
                required
              />
              <v-text-field
                v-model="senha"
                :type="showPassword ? 'text' : 'password'"
                label="Senha"
                prepend-inner-icon="mdi-lock-outline"
                :append-inner-icon="showPassword ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
                autocomplete="current-password"
                required
                @click:append-inner="showPassword = !showPassword"
              />
              <v-btn
                block
                color="primary"
                size="large"
                type="submit"
                :loading="authStore.carregando"
              >
                Entrar
              </v-btn>
            </v-form>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </v-main>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 15% 15%, rgba(217, 139, 58, 0.22), transparent 28%),
    linear-gradient(135deg, #0b3026, #176b52 60%, #2c856b);
}

.login-card {
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow: 0 28px 70px rgba(4, 31, 23, 0.28) !important;
}
</style>
