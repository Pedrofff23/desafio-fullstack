# Plataforma de Gerenciamento de Estoque de Produtos Alimentícios

Aplicação full stack, atualmente em desenvolvimento, para gerenciamento de
usuários, produtos alimentícios e movimentações de estoque.

O backend está estruturado com FastAPI, SQLAlchemy assíncrono e PostgreSQL. O
frontend com Vue 3, TypeScript, Options API, Pinia e Vuetify.

## Stack definida

| Camada | Tecnologia |
|---|---|
| Frontend | Vue.js 3, TypeScript, Options API, Vuetify 3, Pinia e Axios |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 assíncrono e Pydantic 2 |
| Banco de dados | PostgreSQL 16 |
| Migrations | Alembic |
| Containers | Docker e Docker Compose |

## Padrões obrigatórios

- **Singleton:** engine e pool de conexões em `backend/app/core/database.py`.
- **Repository Pattern:** acesso ao banco em `backend/app/repositories/`.
- **Service Layer:** regras de negócio em `backend/app/services/`.
- **DTO:** schemas Pydantic em `backend/app/schemas/` e, futuramente, interfaces
  TypeScript no frontend.

## Executar o backend atual com Docker

### Pré-requisitos

- Docker;
- Docker Compose.

### 1. Criar o arquivo de ambiente

No PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
```

Troque o valor de `SECRET_KEY` em `backend/.env` antes de usar o projeto fora de
um ambiente local de desenvolvimento.

### 2. Iniciar somente banco e backend

Enquanto o frontend não existe, informe explicitamente os dois serviços:

```bash
docker compose up --build db backend
```

O backend tenta executar `alembic upgrade head` durante a inicialização.

### 3. Carregar os dados geográficos

Os dados geográficos precisam ser carregados antes da criação do administrador,
pois o funcionário exige uma cidade válida:

```bash
docker compose exec backend bash scripts/seed_geo.sh
```

### 4. Carregar referências e criar o administrador

```bash
docker compose exec backend python -m scripts.init_db
```

### 5. Carregar dados de demonstração (opcional)

```bash
docker compose exec backend python -m scripts.seed_demo
```

## Serviços disponíveis no estado atual

| Serviço | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| PostgreSQL | localhost:5432 |

O frontend será disponibilizado em `http://localhost:8080` quando a fase 4 for
concluída.

## Administrador inicial

O script `scripts.init_db` cria, por padrão:

- e-mail: `admin@estoque.com`;
- senha: `Admin@12345`.

As credenciais podem ser alteradas pelas variáveis `ADMIN_EMAIL`,
`ADMIN_PASSWORD` e `ADMIN_NOME`.

O perfil de administrador é mantido no banco, mas não restringe as operações da
aplicação. Qualquer usuário autenticado poderá realizar alterações no sistema.

## Endpoints atuais

Todas as rotas abaixo usam o prefixo `/api/v1`.

### Autenticação

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/login` | Retorna um token JWT |
| GET | `/auth/me` | Retorna o usuário autenticado |

### Localidades

| Método | Rota | Descrição |
|---|---|---|
| GET | `/geo/estados` | Lista estados |
| GET | `/geo/estados/{id}/cidades` | Lista cidades do estado |

### Usuários

| Método | Rota | Descrição |
|---|---|---|
| GET | `/usuarios` | Lista usuários com paginação |
| POST | `/usuarios` | Cria usuário |
| GET | `/usuarios/{id}` | Consulta usuário |
| PUT | `/usuarios/{id}` | Atualiza usuário |
| DELETE | `/usuarios/{id}` | Realiza exclusão lógica |

### Produtos e lotes

| Método | Rota | Descrição |
|---|---|---|
| GET | `/produtos/catalogo` | Lista unidades, categorias e localizações |
| GET | `/produtos` | Lista produtos com paginação |
| POST | `/produtos` | Cria produto |
| GET | `/produtos/{id}` | Consulta produto |
| PUT | `/produtos/{id}` | Atualiza produto |
| DELETE | `/produtos/{id}` | Realiza exclusão lógica |
| GET | `/produtos/{id}/lotes` | Lista lotes do produto |
| POST | `/produtos/{id}/lotes` | Cria lote |

### Fornecedores e estoque

| Método | Rota | Descrição |
|---|---|---|
| GET | `/transacoes/fornecedores` | Lista fornecedores |
| POST | `/transacoes/fornecedores` | Cria fornecedor |
| POST | `/transacoes/entrada` | Registra entrada |
| POST | `/transacoes/saida` | Registra saída |
| GET | `/transacoes/estoque` | Consulta estoque atual |
| GET | `/transacoes/historico` | Consulta histórico |

Com exceção de `/auth/login` e `/health`, os endpoints exigem o cabeçalho:

```text
Authorization: Bearer <token>
```

## Banco de dados

A migration atual cria as tabelas principais, as views `estoque_entrada` e
`estoque_produto`, além do trigger `validar_saldo_saida`, que bloqueia saídas
concorrentes acima do saldo disponível.

Os arquivos SQL são referência do banco anterior; a aplicação deve criar e
evoluir sua estrutura por migrations Alembic.

## Testes

As dependências `pytest` e `pytest-asyncio` já estão declaradas, mas a suíte de
testes ainda não foi implementada. A criação dos testes essenciais faz parte da
fase 3.

Quando os testes forem adicionados, o comando previsto dentro do container será:

```bash
docker compose exec backend pytest -q
```

Os testes de estoque deverão usar PostgreSQL, pois o projeto depende de views,
funções e triggers específicas desse banco.

## Próximas etapas

1. Concluir e testar o backend conforme a fase 3.
2. Criar o frontend Vue/Vuetify conforme a fase 4.
3. Validar os três containers e revisar a documentação final.
