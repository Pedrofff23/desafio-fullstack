# Plataforma de Gerenciamento de Estoque de Produtos Alimentícios

Aplicação full stack, para gerenciamento de
usuários, produtos alimentícios e movimentações de estoque.

## Stack definida

| Camada         | Tecnologia                                                  |
| -------------- | ----------------------------------------------------------- |
| Frontend       | Vue.js 3, TypeScript, Options API, Vuetify 3, Pinia e Axios |
| Backend        | Python 3.12, FastAPI, SQLAlchemy 2 assíncrono e Pydantic 2  |
| Banco de dados | PostgreSQL 16                                               |
| Migrations     | Alembic                                                     |
| Containers     | Docker e Docker Compose                                     |

## Padrões obrigatórios

- **Singleton:** engine e pool de conexões em `backend/app/core/database.py`.
- **Repository Pattern:** acesso ao banco em `backend/app/repositories/`.
- **Service Layer:** regras de negócio em `backend/app/services/`.
- **DTO:** schemas Pydantic em `backend/app/schemas/` e, futuramente, interfaces
  TypeScript no frontend.

## Executar a aplicação com Docker

O Docker Compose inicia três serviços independentes:

```text
Navegador → frontend (Nginx, porta 8080) → backend (FastAPI, porta 8000) → db (PostgreSQL, porta 5432)
```

O Nginx entrega a SPA (Single Page Application) e encaminha chamadas iniciadas por `/api/` ao backend. Por isso, as rotas do Vue continuam acessíveis mesmo após atualizar diretamente a página no navegador.

### Pré-requisitos

- Docker Desktop ou Docker Engine com Docker Compose;
- portas `8080`, `8000` e `5432` livres, ou valores alternativos configurados
  nas variáveis de ambiente abaixo.
- Para executar o backend fora do Docker: [uv](https://docs.astral.sh/uv/).

### 1. Criar o arquivo de ambiente

No PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
```

Troque o valor de `SECRET_KEY` em `backend/.env` antes de usar o projeto fora de
um ambiente local de desenvolvimento.

### 2. Construir e iniciar banco, backend e frontend

```bash
docker compose up --build -d
```

O backend executa `alembic upgrade head` durante a inicialização. Aguarde o
status saudável do banco e do backend antes de carregar os dados:

```bash
docker compose ps
docker compose logs -f backend
```

Para encerrar a visualização dos logs, use `Ctrl+C`; os containers continuam em
execução.

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

### Acessar os serviços

| Serviço      | Endereço                     |
| ------------ | ---------------------------- |
| Frontend     | http://localhost:8080        |
| API          | http://localhost:8000        |
| Swagger      | http://localhost:8000/docs   |
| Health check | http://localhost:8000/health |
| PostgreSQL   | `localhost:5432`             |

### Variáveis de ambiente do Compose

Os valores abaixo possuem defaults para desenvolvimento local. Você pode criá-los
em um arquivo `.env` na raiz do projeto ou defini-los no terminal antes de subir
os containers.

| Variável            |                  Padrão | Uso                           |
| ------------------- | ----------------------: | ----------------------------- |
| `POSTGRES_USER`     |               `estoque` | Usuário do PostgreSQL         |
| `POSTGRES_PASSWORD` |            `estoque123` | Senha do PostgreSQL           |
| `POSTGRES_DB`       | `gerenciamento_estoque` | Nome do banco                 |
| `DB_PORT`           |                  `5432` | Porta exposta pelo PostgreSQL |
| `BACKEND_PORT`      |                  `8000` | Porta exposta pela API        |
| `FRONTEND_PORT`     |                  `8080` | Porta exposta pelo Nginx      |

As configurações da aplicação, incluindo `SECRET_KEY`, ficam em
`backend/.env`, criado a partir de `backend/.env.example` no passo 1.

### Operação e recuperação

O volume nomeado `db_data` preserva os dados do PostgreSQL entre reinicializações.
Para apagar completamente o banco local, use o comando abaixo **somente quando
os dados puderem ser descartados**:

```bash
make db-clean
make up
make db-seed-all
```

Após essa limpeza, execute `make db-seed-all` apenas depois de `make up` deixar
o backend disponível.

## Comandos do Makefile

Se o `make` estiver instalado no ambiente, os comandos abaixo simplificam as
operações mais comuns. Execute `make help` para ver essa lista no terminal.

| Comando                 | Descrição                                                     |
| ----------------------- | ------------------------------------------------------------- |
| `make help`             | Exibe todos os comandos disponíveis.                          |
| `make up`               | Inicia banco, backend e frontend em segundo plano.            |
| `make build`            | Reconstrói e inicia os três serviços.                         |
| `make down`             | Para os containers do projeto.                                |
| `make restart`          | Reinicia os containers.                                       |
| `make logs`             | Acompanha os logs de todos os serviços.                       |
| `make ps`               | Mostra o estado dos containers.                               |
| `make db-shell`         | Abre o `psql` interativo no banco.                            |
| `make db-check`         | Mostra a migration aplicada e contagens básicas das tabelas.  |
| `make db-seed-geo`      | Carrega países, estados e cidades do IBGE.                    |
| `make db-seed`          | Carrega dados de referência e o administrador inicial.        |
| `make db-seed-all`      | Executa `db-seed-geo` e `db-seed`, nessa ordem.               |
| `make backend-shell`    | Abre um shell no container do backend.                        |
| `make backend-test`     | Executa os testes do backend no container.                    |
| `make uv-sync`          | Instala dependências locais do backend com `uv`.              |
| `make uv-run`           | Inicia a API localmente com `uv` e recarregamento automático. |
| `make frontend-install` | Instala as dependências do frontend com npm.                  |
| `make frontend-dev`     | Inicia o frontend local com Vite.                             |
| `make frontend-test`    | Executa type-check, lint e testes unitários do frontend.      |
| `make frontend-build`   | Gera o build de produção do frontend.                         |

### Dependências locais com uv

O backend usa `pyproject.toml` e `uv.lock` como fonte de dependências. Para
instalar exatamente as versões registradas no lockfile e iniciar a API fora do
Docker:

```bash
make uv-sync
make uv-run
```

Para adicionar ou atualizar dependências, execute dentro de `backend`:

```bash
uv add nome-do-pacote
uv add --group dev nome-do-pacote-de-desenvolvimento
uv lock
```

### Frontend local

Com o backend disponível na porta 8000:

```bash
make frontend-install
make frontend-dev
```

O servidor Vite encaminha `/api` para o backend. A aplicação local fica em
`http://localhost:5173`.

## Serviços disponíveis

| Serviço         | URL                          |
| --------------- | ---------------------------- |
| API             | http://localhost:8000        |
| Swagger         | http://localhost:8000/docs   |
| Health check    | http://localhost:8000/health |
| Frontend Docker | http://localhost:8080        |
| Frontend Vite   | http://localhost:5173        |
| PostgreSQL      | localhost:5432               |

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

| Método | Rota          | Descrição                     |
| ------ | ------------- | ----------------------------- |
| POST   | `/auth/login` | Retorna um token JWT          |
| GET    | `/auth/me`    | Retorna o usuário autenticado |

### Localidades

| Método | Rota                        | Descrição               |
| ------ | --------------------------- | ----------------------- |
| GET    | `/geo/estados`              | Lista estados           |
| GET    | `/geo/estados/{id}/cidades` | Lista cidades do estado |

### Usuários

| Método | Rota             | Descrição                    |
| ------ | ---------------- | ---------------------------- |
| GET    | `/usuarios`      | Lista usuários com paginação |
| POST   | `/usuarios`      | Cria usuário                 |
| GET    | `/usuarios/{id}` | Consulta usuário             |
| PUT    | `/usuarios/{id}` | Atualiza usuário             |
| DELETE | `/usuarios/{id}` | Realiza exclusão lógica      |

### Produtos e lotes

| Método | Rota                   | Descrição                                                                    |
| ------ | ---------------------- | ---------------------------------------------------------------------------- |
| GET    | `/produtos/catalogo`   | Lista unidades, categorias, localizações completas, ingredientes e alérgenos |
| GET    | `/produtos`            | Lista com filtros de nome, status e preço                                    |
| POST   | `/produtos`            | Cria produto, composição alimentícia e lote inicial opcional                 |
| GET    | `/produtos/{id}`       | Consulta produto e composição alimentícia                                    |
| PUT    | `/produtos/{id}`       | Atualiza produto e composição alimentícia                                    |
| DELETE | `/produtos/{id}`       | Realiza exclusão lógica                                                      |
| GET    | `/produtos/{id}/lotes` | Lista todos os lotes com validade, saldo e localizações                      |
| POST   | `/produtos/{id}/lotes` | Cria lote                                                                    |

### Fornecedores e estoque

| Método | Rota                               | Descrição                                        |
| ------ | ---------------------------------- | ------------------------------------------------ |
| GET    | `/transacoes/fornecedores`         | Lista fornecedores                               |
| POST   | `/transacoes/fornecedores`         | Cria fornecedor com contato e endereço           |
| POST   | `/transacoes/entrada`              | Registra entrada, custo, tipo, data e observação |
| POST   | `/transacoes/saida`                | Registra saída, validando o saldo                |
| GET    | `/transacoes/entradas-disponiveis` | Lista entradas com saldo para registrar saídas   |
| GET    | `/transacoes/estoque`              | Consulta estoque atual                           |
| GET    | `/transacoes/historico`            | Histórico com filtros e auditoria                |

Com exceção de `/auth/login` e `/health`, os endpoints exigem o cabeçalho:

```text
Authorization: Bearer <token>
```

## Banco de dados

As migrations criam as tabelas do SQL de referência, os campos de preço,
perecibilidade e tipos de movimentação, além das views `estoque_entrada` e
`estoque_produto`. O schema usa tipos PostgreSQL nativos e `CHECK constraints`;
não depende de `DOMAINs` personalizados.

Os triggers do PostgreSQL:

- impedem saídas concorrentes acima do saldo disponível;
- impedem reduzir uma entrada abaixo da quantidade já retirada;
- preenchem a localização da entrada com a localização preferencial do produto;
- impedem excluir registros de entrada e saída.

Os arquivos SQL são referência do banco anterior; a aplicação deve criar e
evoluir sua estrutura por migrations Alembic.

### Validade e lotes

A validade pertence exclusivamente a `lotes`. O produto não armazena nem expõe
uma validade agregada. A consulta de lotes devolve todos os lotes não excluídos
do produto e calcula individualmente:

- quantidade disponível;
- dias até o vencimento;
- status de validade;
- localizações que ainda possuem saldo.

Os saldos são derivados das entradas e saídas registradas; não existe uma coluna
de saldo duplicada em `produtos` ou `lotes`.

### Preços

- `produtos.preco` é o preço atual usado no CRUD, na listagem e nos filtros;
- `registros_entrada.preco_custo` é o custo histórico apresentado nas entradas;
- `registros_saida.preco_venda` é o preço praticado na saída;
- `registros_entrada.preco_sugerido` permanece somente como coluna interna do
  banco base e é preenchido pelo backend com o preço atual do produto. Esse
  campo não faz parte do formulário nem dos DTOs públicos da API.

## Testes

A suíte cria um banco PostgreSQL temporário, aplica todas as migrations e valida
autenticação, usuários, fornecedores, produtos, filtros, movimentações,
concorrência de saídas e imutabilidade do histórico.

Com banco e backend em execução:

```bash
docker compose exec backend pytest -q
```

Para validar o frontend:

```bash
cd frontend
npm run type-check
npm run lint
npm run test:unit
npm run build
```
