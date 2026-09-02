# Frontend — Gerenciamento de Estoque

SPA construída com Vue 3, TypeScript, Options API, Vuetify 3, Vue Router, Pinia
e Axios.

## Desenvolvimento local

Com o backend disponível em `http://localhost:8000`:

```bash
npm install
npm run dev
```

O Vite encaminha requisições iniciadas por `/api` ao backend. A aplicação fica
disponível em `http://localhost:5173`.

## Validação

```bash
npm run type-check
npm run lint
npm run test:unit
npm run build
```

Copie `.env.example` para `.env` apenas se precisar substituir a URL base da
API. No desenvolvimento e no Docker, o valor padrão `/api/v1` é suficiente.
