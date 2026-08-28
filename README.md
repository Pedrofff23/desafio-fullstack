# Plataforma de Gerenciamento de Estoque de Produtos Alimentícios

Aplicação **full stack** para gerenciamento de estoque de produtos alimentícios, com
autenticação JWT, CRUD de usuários e produtos, controle transacional de entradas e
saídas, histórico de auditoria e painel de estoque em tempo real.

> **Desafio Full Stack** — reutilização de um banco PostgreSQL existente, reescrito
> em **migrations versionadas (Alembic)**, com integração dos dados **IBGE** (país,
> estado, cidade) no cadastro de endereços.

---

## 🧱 Stack Tecnológica

| Camada       | Tecnologia                                                         |
|--------------|--------------------------------------------------------------------|
| Frontend     | Vue.js 3 (**Options API**), TypeScript, Vuetify 3, Pinia, Axios    |
| Backend      | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2          |
| Migrations   | Alembic                                                             |
| Banco        | PostgreSQL 16                                                       |
| Contêineres  | Docker + Docker Compose (`db`, `backend`, `frontend`)             |

### Padrões de Arquitetura (obrigatórios)

- **Singleton** — engine e pool de conexões gerenciados em `core/database.py`.
- **Repository Pattern** — acesso a dados desacoplado da regra de negócio (`repositories/`).
- **Service Layer** — regras de negócio e controle transacional (`services/`).
- **Camada de DTO** — Schemas Pydantic no backend (`schemas/`) e interfaces TypeScript no frontend.

---

## 📁 Estrutura do Projeto

```
desafio-fullstack/
├── docker-compose.yml            # 3 serviços: db, backend, frontend
├── .env                          # credenciais/portas do compose (raiz)
├── README.md
├── sql_reference/                # SQL de referência (schema, views, triggers)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini               # configuração do Alembic
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/             # migrations versionadas
│   ├── scripts/
│   │   ├── init_db.py            # seed: unidades, categorias, localizações, admin
│   │   └── seed_geo.sh           # carrega dumps IBGE (paises, estados, cidades)
│   ├── .env.example
│   └── app/
│       ├── main.py               # FastAPI + lifespan (migrations no boot) + CORS
│       ├── core/                 # config, database (Singleton), security (JWT/hash)
│       ├── models/               # SQLAlchemy ORM (mapeia o schema existente)
│       ├── schemas/              # DTOs Pydantic v2
│       ├── repositories/         # Repository Pattern
│       ├── services/             # Service Layer (regras + transações)
│       └── api/
│           ├── deps.py           # autenticação JWT (Bearer) + require_admin
│           └── v1/               # routers: auth, geo, usuarios, produtos, transacoes
└── frontend/                     # Vue 3 (Options API) + Vuetify + Pinia + Axios
```

---

## 🚀 Como Executar (Docker)

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/)

### Passos

```bash
# 1. Suba os containers (db, backend, frontend)
docker compose up --build

# 2. O backend aplica as migrations automaticamente no boot (alembic upgrade head)

# 3. Carregue os dados de referência + usuário admin
docker compose exec backend python -m scripts.init_db

# 4. (Opcional) Carregue os dados geográficos IBGE
docker compose exec backend bash scripts/seed_geo.sh
```

### Serviços

| Serviço | URL                    | Descrição                          |
|---------|------------------------|------------------------------------|
| Frontend| http://localhost:8080  | SPA Vue 3                          |
| Backend | http://localhost:8000  | API FastAPI                        |
| Docs    | http://localhost:8000/docs | Swagger UI interativo           |
| Banco   | localhost:5432         | PostgreSQL 16 (uso do `.env`)      |

> Portas podem ser alteradas via `DB_PORT`, `BACKEND_PORT` e `FRONTEND_PORT` no `.env`.

---

## 🐣 Usuário Administrador

O `init_db.py` cria um administrador inicial:

- **E-mail:** `admin@estoque.com`
- **Senha:** `Admin@12345`

> Altere as credenciais padrão em produção (variáveis `ADMIN_EMAIL` / `ADMIN_PASSWORD`).

---

## 🔌 Endpoints da API (prefixo `/api/v1`)

### Autenticação
| Método | Rota          | Descrição                    |
|--------|---------------|------------------------------|
| POST   | `/auth/login` | Login (e-mail + senha) → JWT |
| GET    | `/auth/me`    | Dados do usuário autenticado |

### Localidades (IBGE)
| Método | Rota                        | Descrição                |
|--------|-----------------------------|--------------------------|
| GET    | `/geo/estados`              | Lista estados (UF)       |
| GET    | `/geo/estados/{id}/cidades` | Lista cidades do estado  |

### Usuários
| Método | Rota              | Descrição                     |
|--------|-------------------|-------------------------------|
| GET    | `/usuarios`       | Lista usuários (paginado)     |
| POST   | `/usuarios`       | Cria usuário (admin)          |
| GET    | `/usuarios/{id}`  | Detalhe do usuário            |
| PUT    | `/usuarios/{id}`  | Edita usuário (admin)         |
| DELETE | `/usuarios/{id}`  | Exclui usuário (soft delete)  |

### Produtos
| Método | Rota                       | Descrição                                  |
|--------|----------------------------|--------------------------------------------|
| GET    | `/produtos/catalogo`      | Unidades, categorias, localizações         |
| GET    | `/produtos`                | Lista produtos (filtros + alertas)         |
| POST   | `/produtos`                | Cria produto                               |
| GET    | `/produtos/{id}`           | Detalhe do produto                         |
| PUT    | `/produtos/{id}`           | Edita produto (admin)                      |
| DELETE | `/produtos/{id}`           | Exclui produto (admin)                     |
| GET    | `/produtos/{id}/lotes`    | Lotes do produto                           |
| POST   | `/produtos/{id}/lotes`    | Cria lote (com data de validade)           |

### Transações de Estoque
| Método | Rota                          | Descrição                        |
|--------|-------------------------------|----------------------------------|
| GET    | `/transacoes/fornecedores`   | Lista fornecedores               |
| POST   | `/transacoes/fornecedores`   | Cria fornecedor                  |
| POST   | `/transacoes/entrada`        | Registra entrada (adiciona saldo)|
| POST   | `/transacoes/saida`          | Registra saída (valida saldo)    |
| GET    | `/transacoes/estoque`        | Estoque atual por produto        |
| GET    | `/transacoes/historico`      | Histórico (filtros + auditoria)  |

> Todos os endpoints, exceto `/auth/login` e `/health`, exigem o token JWT no
> cabeçalho `Authorization: Bearer <token>`.

---

## ⚙️ Funcionalidades (Requisitos)

### Autenticação
- Login com **JWT** e senhas criptografadas (**bcrypt**).
- `/auth/me` para carregar o usuário corrente na SPA.

### CRUD de Usuários
- Cadastro exige **nome, e-mail, contato e endereço** com integração **IBGE**:
  após selecionar o estado, o frontend lista as cidades correspondentes.
- Criação/edição **transacional** em cascata:
  `enderecos` → `contatos` → `funcionarios` → `usuarios`.
- Listagem, edição e exclusão lógica (soft delete).

### CRUD de Produtos
- Código único, nome, categoria, unidade de medida, localização e status.
- **Preço** com máscara de moeda (frontend) e **validade** pertencente ao **lote**.
- Listagem com filtros por **nome, status e intervalo de preço**.
- **Destaques visuais**: validade < 30 dias e estoque baixo/zerado.

### Transações de Estoque (ACID)
- **Entrada**: associa lote + fornecedor + localização + quantidade + custos.
- **Saída**: vinculada a uma entrada; **não permite saldo negativo**.
- **Atomicidade**: movimentações em transação de banco + trigger `validar_saldo_saida`
  que serializa saídas concorrentes.
- **Auditoria**: registra usuário, data/hora e tipo; transações **não podem ser excluídas**.
- **Estoque atual** e **histórico** com filtros por produto, tipo, usuário e período.

---

## 🗄️ Banco de Dados

O schema foi **reescrito em migrations Alembic** (não SQL puro), cobrindo:

- Domínios (e-mail, CEP, telefone, quantidade, valor monetário).
- Tabelas de localidades (IBGE), pessoas, produtos/lotes, movimentações e sessões.
- **Views** de saldo: `estoque_entrada` e `estoque_produto`.
- **Triggers**: `validar_saldo_saida` (saldo sob concorrência) e
  `validar_quantidade_entrada` (integridade de edição).
- **Soft delete** em tabelas protegidas (funcionários, usuários, fornecedores, produtos, lotes).
- **Índices** para performance nas queries mais comuns.

> Os scripts SQL originais ficam em `sql_reference/` como referência.

---

## 🧪 Testes

```bash
# Dentro do container backend
docker compose exec backend pytest -q
```

Os testes usam `pytest-asyncio` e um banco isolado para não afetar dados reais.