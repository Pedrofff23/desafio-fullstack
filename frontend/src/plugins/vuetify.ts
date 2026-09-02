import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

import { createVuetify } from 'vuetify'
import { pt } from 'vuetify/locale'

export default createVuetify({
  locale: {
    locale: 'pt',
    fallback: 'en',
    messages: { pt },
  },
  theme: {
    defaultTheme: 'estoqueTheme',
    themes: {
      estoqueTheme: {
        dark: false,
        colors: {
          primary: '#176B52',
          secondary: '#D98B3A',
          background: '#F4F7F5',
          surface: '#FFFFFF',
          error: '#B42318',
          warning: '#B54708',
          success: '#067647',
          info: '#175CD3',
        },
      },
    },
  },
  defaults: {
    VBtn: { rounded: 'lg' },
    VCard: { rounded: 'xl', elevation: 0 },
    VTextField: { variant: 'outlined', density: 'comfortable' },
    VSelect: { variant: 'outlined', density: 'comfortable' },
    VAutocomplete: { variant: 'outlined', density: 'comfortable' },
  },
})
