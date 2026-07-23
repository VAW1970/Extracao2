# MEMORY.md — Extração Contábil (Extracao2)

Registro de ajustes, correções e melhorias implementadas no projeto para referência futura e replicação em outros projetos.

---

## 📋 Visão Geral do Projeto

**Sistema de Pré-Processamento Contábil** — Django + PostgreSQL (Neon) + Deploy Vercel

- **Objetivo**: Upload de documentos (PDF, imagem, XML) → Extração via LLM (NVIDIA API) → Validação humana → Lançamento preparado (CSV)
- **Stack**: Django 5.1, PostgreSQL/Neon, Vercel (serverless), Supabase Storage, NVIDIA API (Nemotron-3-Ultra + Llama-3.2-90B-Vision)
- **Apps**: `usuarios`, `documentos`, `validacao`, `dashboard`, `llm_service`, `config`

---

## 🔧 Ajustes e Melhorias por Categoria

### 1. LLM / Extração de Dados

| Commit | Descrição |
|--------|-----------|
| `d69ded6` | Migração de LM Studio (local) para **NVIDIA API** (Nemotron-3-Ultra + Llama-3.2-90B-Vision) |
| `5a2e25d` | Correção dos nomes exatos dos modelos NVIDIA (`nvidia/nemotron-3-ultra-550b-a55b`, `meta/llama-3.2-90b-vision-instruct`) |
| `a2061ea` | `provider_factory` importando `APIProvider` genérico (compatível OpenAI) |
| `a5a0ce2` | Provedor NVIDIA via env vars (`LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`) |
| `9494845` | Página Config LLM mostra valores reais (DB + fallback env vars) + aviso quando usa env vars |
| `0d22ee0` | `.env` e `.env.example` atualizados com config NVIDIA + Supabase |

**Arquivos-chave**:
- `apps/llm_service/provider_factory.py` — factory com fallback DB/env
- `apps/llm_service/api_provider.py` — provedor genérico OpenAI-compatível
- `apps/llm_service/services.py` — pipeline extração (preprocess → LLM → valida → persiste)
- `apps/llm_service/validacao_schema.py` — schemas Pydantic + `convert_monetary_fields` (Decimal→string p/ JSON)
- `apps/llm_service/preprocessamento/xml_preprocessor.py` — suporte lxml + fallback stdlib (nsmap)

### 2. Decimal / JSON Serialization

| Commit | Descrição |
|--------|-----------|
| `1c2566b` | `convert_monetary_fields` converte `Decimal` → `string` antes de salvar no `JSONField` |
| Testes | `tests/test_llm_service.py::TestConvertMonetaryFields` — 4 testes passando |

### 3. Dashboard / Gráficos

| Commit | Descrição |
|--------|-----------|
| `80c957c` | `timeline_labels/values` (últimos 30 dias) + `por_tipo` restaurados no context |
| `ce486d1` | `try/catch` + `console.error` + `min-height` nos containers Chart.js |
| `1513e1c` | Divs de erro visíveis se Chart.js falhar + logs de debug |

**Template**: `templates/dashboard/index.html` — Chart.js via CDN, gráficos de linha (timeline) e donut (tipos)

### 4. Página de Ajuda

| Commit | Descrição |
|--------|-----------|
| `2d36b47` | `AjudaView` em `/dashboard/ajuda/` com 9 seções + FAQ acordeão |

**Template**: `templates/dashboard/ajuda.html` — sidebar link adicionado em `base.html`

### 5. Admin Customizado

| Commit | Descrição |
|--------|-----------|
| `efb1df0` / `e6747e6` | `UsuarioAdmin`, `DocumentoAdmin`, `DadosExtraidosAdmin`, `LLMConfigAdmin`, `ValidacaoLogAdmin`, `LancamentoPreparadoAdmin` com fieldsets, ordering, filtros |
| `1428037` / `72cc241` | **Custom AdminSite** (`ExtracaoAdminSite`) com branding + ordenação: Usuários → Documentos → Validação → LLM → Auth |
| `72cc241` | `templates/admin/base.html` — remove sidebar nativo, usa header customizado + cards por app |
| `72cc241` | `static/css/admin.css` — estilo completo (Cormorant Garamond + Inter, gold/navy) |

**Arquivos**:
- `config/admin_site.py` — `ExtracaoAdminSite` + registro manual de todos os models
- `config/urls.py` — usa `admin_site.urls`
- Apps: `admin.py` sem `@admin.register`, classes exportadas p/ registro manual

### 5. Deploy / Vercel / Neon

| Commit | Descrição |
|--------|-----------|
| `65c1a0b` | `buildCommand` apenas `collectstatic` (migrações manuais) |
| `vercel.json` | `maxDuration` não configurado (padrão 300s) — extrações longas podem estourar |
| Neon | `DATABASE_URL` (pooled) p/ app; `DATABASE_URL_UNPOOLED` p/ migrações |

**Variáveis Vercel (Production)**:
```
LLM_PROVIDER=api
LLM_API_KEY=...
LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
VISION_LLM_MODEL=meta/llama-3.2-90b-vision-instruct
DATABASE_URL=postgresql://... (pooled)
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_BUCKET_NAME=Via.extracao
DJANGO_SECRET_KEY=...
DJANGO_ALLOWED_HOSTS=*.vercel.app
```

### 6. Storage / Upload

- **Supabase Storage** (produção) — `django-storages` + `S3Boto3Storage` customizado
- Upload direto client-side p/ arquivos > 4.5MB (limite Vercel)
- `apps/storage_backends.py` — backend customizado

### 7. XML Preprocessing (NF-e)

| Commit | Descrição |
|--------|-----------|
| `e99785c` | `XMLPreprocessor` tenta `lxml` primeiro, cai p/ `xml.etree.ElementTree` (stdlib) — resolve erro `nsmap` |

---

## 📁 Estrutura de Arquivos Relevantes

```
├── config/
│   ├── settings.py          # Django settings (env via django-environ)
│   ├── urls.py              # URLs raiz (usa admin_site.urls)
│   ├── admin_site.py        # ExtracaoAdminSite + registro models
│   └── apps.py              # ExtracaoConfig (ready() p/ admin branding)
├── apps/
│   ├── usuarios/            # Custom User (AbstractUser)
│   ├── documentos/          # Documento, DadosExtraidos
│   ├── validacao/           # ValidacaoLog, LancamentoPreparado
│   ├── dashboard/           # DashboardView, ExportCSVView, AjudaView
│   └── llm_service/
│       ├── api_provider.py          # APIProvider (OpenAI-compat)
│       ├── provider_factory.py      # get_llm_provider()
│       ├── services.py              # Pipeline extração
│       ├── validacao_schema.py      # Pydantic schemas + convert_monetary_fields
│       ├── preprocessamento/
│       │   ├── pdf_preprocessor.py
│       │   ├── image_preprocessor.py
│       │   └── xml_preprocessor.py  # lxml + fallback stdlib
│       ├── admin.py                 # Classes admin (sem @register)
│       └── views.py                 # Config LLM + test connection
├── templates/
│   ├── base.html              # Layout principal (sidebar projeto)
│   ├── admin/base.html        # Admin custom (sem sidebar Django)
│   ├── dashboard/
│   │   ├── index.html         # Dashboard + Chart.js
│   │   └── ajuda.html         # Página ajuda
│   └── llm_service/config.html
├── static/css/
│   ├── main.css               # Projeto principal
│   └── admin.css              # Admin customizado
├── vercel.json                # Build config
├── requirements.txt
└── .env.example               # Template variáveis
```

---

## ⚠️ Pontos de Atenção / Dívida Técnica

1. **Timeout Vercel (300s)** — Extrações de PDF/imagem grandes podem estourar. Solução: `maxDuration` no `vercel.json` (plano Pro) ou processamento assíncrono (Celery/RQ + Redis)
2. **Migrações Neon** — Rodar manualmente: `DATABASE_URL_UNPOOLED` + `python manage.py migrate`
3. **Chart.js CDN** — Carrega de `cdn.jsdelivr.net`; em ambiente restrito, baixar local
4. **Supabase Storage** — Requer `SUPABASE_SERVICE_ROLE_KEY` (não anon key) p/ upload server-side
5. **Admin customizado** — Não usa `django.contrib.admin` padrão; mudanças no admin exigem editar `config/admin_site.py` + `templates/admin/`

---

## 🚀 Checklist Deploy Nova Instância

- [ ] Clone repo
- [ ] `cp .env.example .env` + preencher variáveis
- [ ] `python -m venv venv && venv/bin/pip install -r requirements.txt`
- [ ] `python manage.py migrate` (local SQLite ou Postgres)
- [ ] `python manage.py createsuperuser`
- [ ] `python manage.py collectstatic`
- [ ] Push GitHub → Import Vercel
- [ ] Vercel: Add Environment Variables (todas do `.env.example`)
- [ ] Vercel: Deploy → Redeploy sem cache
- [ ] Neon: Run migrations com `DATABASE_URL_UNPOOLED`
- [ ] Testar: Upload → Extração → Validação → Export CSV

---

## 📝 Referências de Commits Principais

| Hash | Mensagem |
|------|----------|
| `72cc241` | Custom admin site com sidebar ordenado |
| `2d36b47` | Página ajuda (AjudaView) |
| `9494845` | Config LLM mostra valores reais + aviso env vars |
| `e99785c` | XML fallback stdlib (nsmap) |
| `1c2566b` | Decimal→string p/ JSON |
| `d69ded6` | Migração LM Studio → NVIDIA API |
| `65c1a0b` | Build sem migrate |