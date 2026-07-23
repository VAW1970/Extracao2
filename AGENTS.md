# AGENTS.md — Extração Contábil (Extracao2)

## Estado Atual do Projeto

**Sistema de Pré-Processamento Contábil** — Django 5.1 + PostgreSQL/Neon + Deploy Vercel

- **Repositório**: https://github.com/VAW1970/Extracao2.git
- **Deploy**: Vercel (extracao2-*.vercel.app)
- **Database**: Neon PostgreSQL (branch `vercel-dev` p/ preview, `production` p/ prod)
- **Storage**: Supabase Storage (bucket `Via.extracao`)
- **LLM**: NVIDIA API via endpoint OpenAI-compatível (`https://integrate.api.nvidia.com/v1`)
  - Texto: `nvidia/nemotron-3-ultra-550b-a55b`
  - Visão: `meta/llama-3.2-90b-vision-instruct`
- **Ollama**: Apenas desenvolvimento local (não roda na Vercel)

---

## Stack Confirmada

| Componente | Tecnologia |
|------------|------------|
| Backend | Django 5.1 (LTS) |
| Database | PostgreSQL via Neon (psycopg v3) |
| Deploy | Vercel Functions (Python) |
| Storage | Supabase Storage (S3-compatível) |
| LLM Provider | NVIDIA API (OpenAI-compatível) |
| Frontend | Django Templates + Bootstrap 5.3 + Chart.js |
| Auth | Custom User Model (`usuarios.Usuario`) |
| Testes | pytest-django + mocks |

---

## Apps Django

| App | Responsabilidade |
|-----|------------------|
| `usuarios` | Custom User Model (`AUTH_USER_MODEL = "usuarios.Usuario"`) |
| `documentos` | `Documento`, `DadosExtraidos` |
| `validacao` | `ValidacaoLog`, `LancamentoPreparado` |
| `dashboard` | DashboardView, ExportCSVView, AjudaView |
| `llm_service` | Pipeline extração, provedores, schemas, admin config |
| `config` | Settings, URLs, Custom AdminSite |

---

## Arquitetura LLM (Provider Pattern)

```
provider_factory.get_llm_provider() 
    → APIProvider (NVIDIA)  # produção
    → OllamaProvider        # dev local apenas
```

- **Interface**: `LLMProviderBase.extrair(conteudo, prompt, schema, is_multimodal) -> dict`
- **Factory**: Lê `LLM_PROVIDER` env var + `LLMConfig` do DB (fallback env vars)
- **Validação**: Pydantic schemas por tipo (`NotaFiscalSchema`, `ContratoSchema`, etc.)
- **Monetário**: `convert_monetary_fields()` converte `Decimal` → `str` p/ JSONField

---

## Pipeline de Extração

1. **Upload** → `Documento` (arquivo no Supabase Storage)
2. **Preprocessamento** → `PDFPreprocessor` / `ImagePreprocessor` / `XMLPreprocessor`
3. **Prompt** → Template por tipo (`prompts/{tipo}.txt`)
4. **LLM Call** → `APIProvider` (NVIDIA) ou `OllamaProvider`
5. **Validação** → Pydantic schema + retry (máx 2 tentativas)
6. **Persistência** → `DadosExtraidos` (JSONField + metadados LLM)
7. **Validação Humana** → Tela lado a lado (documento + dados) → Aprova/Rejeita
8. **Lançamento** → `LancamentoPreparado` (obrigatório: documento, origem, data)
9. **Export** → CSV (apenas status `PENDENTE`)

---

## Configuração de Produção (Vercel)

### Environment Variables (Vercel Dashboard)
```bash
LLM_PROVIDER=api
LLM_API_KEY=<chave NVIDIA>
LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
VISION_LLM_MODEL=meta/llama-3.2-90b-vision-instruct
DATABASE_URL=postgresql://... (pooled)
DATABASE_URL_UNPOOLED=postgresql://... (unpooled p/ migrate)
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service role key>
SUPABASE_BUCKET_NAME=Via.extracao
DJANGO_SECRET_KEY=<secret>
DJANGO_ALLOWED_HOSTS=.vercel.app
```

### Build Command
```json
"buildCommand": "python manage.py collectstatic --noinput"
```
> **Migrações rodam manualmente** com `DATABASE_URL_UNPOOLED`

---

## Admin Customizado

- **Custom AdminSite**: `config.admin_site.ExtracaoAdminSite`
- **Branding**: "Administração — Extração Contábil" / "Painel de Controle"
- **Ordem Sidebar**: Usuários → Documentos → Validação → LLM → Auth
- **Templates**: `templates/admin/base.html` (sem sidebar nativo, cards por app)
- **CSS**: `static/css/admin.css` (Cormorant Garamond + Inter, gold/navy)
- **Design System**: Documentado em `DESIGN.md` (cores, tipografia, componentes, responsividade)

---

## Páginas Principais

| Rota | View | Template |
|------|------|----------|
| `/` | Redirect → `/dashboard/` | - |
| `/dashboard/` | `DashboardView` | `dashboard/index.html` |
| `/dashboard/ajuda/` | `AjudaView` | `dashboard/ajuda.html` |
| `/dashboard/exportar-csv/` | `ExportCSVView` | - |
| `/documentos/` | `DocumentoListView` | `documentos/list.html` |
| `/documentos/novo/` | `DocumentoCreateView` | `documentos/upload.html` |
| `/documentos/<pk>/extrair/` | `extrair_dados` (POST) | - |
| `/validacao/` | `ValidacaoQueueView` | `validacao/queue.html` |
| `/validacao/<pk>/` | `ValidacaoDetailView` | `validacao/detail.html` |
| `/llm/config/` | `LLMConfigView` | `llm_service/config.html` |
| `/admin/` | `ExtracaoAdminSite` | `admin/base.html` |

---

## Testes

```bash
# Rodar testes (mocks LLM/storage)
venv/bin/pytest tests/ -v

# Testes específicos
venv/bin/pytest tests/test_llm_service.py -v
```

- Mocks: `MockProvider`, `MockStorage`
- Sem chamadas reais de rede/API em CI
- 20 testes passando (models + llm_service)

---

## Problemas Conhecidos / Limitações

1. **Timeout Vercel (300s)** — Extrações longas podem estourar. Solução futura: `maxDuration` no `vercel.json` (plano Pro) ou processamento assíncrono
2. **Chart.js via CDN** — `cdn.jsdelivr.net`; em redes restritas, baixar local
3. **Supabase Storage** — Requer `SERVICE_ROLE_KEY` (não anon key)
4. **Admin customizado** — Não usa `django.contrib.admin` padrão; mudanças exigem editar `config/admin_site.py` + `templates/admin/`
5. **XML NF-e** — `XMLPreprocessor` usa `lxml` + fallback `xml.etree` (stdlib) p/ compatibilidade

---

## Documentação de Design

- **DESIGN.md** — Design System completo (cores, tipografia, espaçamento, componentes, responsividade, checklist de implementação)
- **MEMORY.md** — Histórico de ajustes e melhorias para replicação

---

## Comandos Úteis

```bash
# Desenvolvimento local
python manage.py runserver
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser

# Testes
venv/bin/pytest tests/ -v

# Deploy
git push origin main
# Vercel: Redeploy → uncheck "Use existing Build Cache"

# Migrações Neon (manual)
DATABASE_URL_UNPOOLED=... python manage.py migrate
```