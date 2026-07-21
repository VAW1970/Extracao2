# Extracão Contábil

Sistema de **Extração via LLM e Pré-Lançamento Contábil** — Django + PostgreSQL (Neon) + Vercel.

Recebe documentos contábeis/fiscais (PDF, imagem, XML), extrai dados via LLM, e permite validação humana antes de lançamento.

## 🚀 Quick Start (Desenvolvimento Local)

### 1. Clone e setup

```bash
git clone <repository-url>
cd Extracao2
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 2. Configure variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env com suas configurações
```

### 3. Execute migrações e inicie o servidor

```bash
python manage.py migrate
python manage.py createsuperuser  # Crie um usuário admin
python manage.py runserver
```

Acesse: http://localhost:8000

## 📦 Configuração do Banco (Neon)

1. Crie um projeto no [Neon](https://neon.tech)
2. Obtenha as strings de conexão:
   - **Pooled** (`DATABASE_URL`): para tráfego da aplicação
   - **Unpooled** (`DATABASE_URL_UNPOOLED`): para migrações
3. Configure no `.env`:

```
DATABASE_URL=postgresql://user:pass@ep-xxx-pooler.us-east-2.aws.neon.tech/dbname?sslmode=require
DATABASE_URL_UNPOOLED=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require
```

## 🤖 Configuração do LLM

### Desenvolvimento Local — Ollama

1. Instale o [Ollama](https://ollama.ai)
2. Execute: `ollama serve`
3. Configure no `.env`:

```
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
```

### Produção (Vercel) — API Externa

1. Obtenha uma chave de API (OpenAI, Anthropic, etc.)
2. Configure no `.env`:

```
LLM_PROVIDER=api
LLM_API_KEY=sua-chave-aqui
LLM_MODEL=gpt-4o
```

> ⚠️ Ollama **NÃO** funciona em produção na Vercel (requer processo persistente).

## 🌐 Deploy na Vercel

1. Conecte o repositório à Vercel
2. Configure as variáveis de ambiente no painel da Vercel
3. O deploy é automático — a Vercel detecta o Django via `manage.py`

### Variáveis de ambiente obrigatórias na Vercel:

| Variável | Descrição |
|---|---|
| `DJANGO_SECRET_KEY` | Chave secreta do Django |
| `DATABASE_URL` | String de conexão pooled (Neon) |
| `DATABASE_URL_UNPOOLED` | String de conexão direta (migrações) |
| `LLM_PROVIDER` | `api` (produção) |
| `LLM_API_KEY` | Chave da API do LLM |
| `LLM_MODEL` | Nome do modelo |

## 🧪 Testes

```bash
pytest                    # Rodar todos os testes
pytest --cov              # Com cobertura
pytest tests/test_models.py  # Apenas testes de models
```

## 📁 Estrutura do Projeto

```
Extracao2/
├── config/              # Settings Django
├── apps/
│   ├── usuarios/        # Custom User Model
│   ├── documentos/      # Upload e gestão de documentos
│   ├── validacao/       # Validação humana
│   ├── dashboard/       # Dashboard e exportação
│   └── llm_service/     # Camada de abstração LLM
├── prompts/             # Templates de prompt por tipo
├── schemas/             # Schemas de validação JSON
├── templates/           # Templates HTML
├── static/              # Arquivos estáticos (CSS)
└── tests/               # Testes automatizados
```

## 📋 Tipos de Documento Suportados

| Tipo | Formatos | Campos Extraídos |
|---|---|---|
| Nota Fiscal | PDF, XML, Imagem | número, série, CNPJ, data, valor, itens, chave_acesso |
| Contrato | PDF, Imagem | partes, objeto, valor, vigência, pagamento |
| Demonstrativo | PDF, Imagem | período, categorias, débito/crédito, saldo |
| Boleto | PDF, Imagem | linha_digitável, valor, vencimento, beneficiário, pagador |

## 🔒 Regras de Segurança

- Chaves de API **nunca** hardcoded — apenas variáveis de ambiente
- Saída do LLM **sempre** validada contra schema antes de persistir
- Valores monetários **sempre** em Decimal
- Arquivos originais imutáveis
- `AUTH_USER_MODEL` definido antes da primeira migração

## 📄 Licença

Proprietário — Uso interno.
