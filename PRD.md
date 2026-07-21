# PRD — Sistema de Extração via LLM e Pré-Lançamento Contábil
## (Django + PostgreSQL/Neon + Deploy na Vercel)

**Versão:** 1.0
**Status:** Rascunho para início de desenvolvimento
**Última atualização:** 20/07/2026

---

## 1. Visão Geral

O **Sistema de Extração via LLM e Pré-Lançamento Contábil** é uma aplicação
**Django**, com banco de dados **PostgreSQL hospedado na Neon**, implantada
na **Vercel** (Vercel Functions, runtime Python com suporte nativo a
Django). O sistema recebe documentos contábeis/fiscais (PDF, imagem, XML) e
utiliza um **LLM** — local via **Ollama** em desenvolvimento, ou via **API
de provedor externo** em produção — para extrair dados automaticamente,
guiado por templates de prompt específicos por tipo de documento.

O sistema **não substitui** um ERP contábil e **não realiza lançamentos
automáticos**. Toda saída do LLM passa por validação estrutural automática
e, em seguida, por validação humana antes de ser considerada pronta para
lançamento.

---

## 2. Problema a Resolver

Além do problema original (lançamento manual lento, sujeito a erro, sem
rastreabilidade), esta versão do projeto introduz um requisito adicional:
a aplicação precisa rodar em um ambiente **serverless** (Vercel), o que
muda decisões de arquitetura que seriam triviais em um servidor tradicional
— armazenamento de arquivos, duração de processamento, gerenciamento de
conexões de banco e viabilidade de rodar um LLM local.

---

## 3. Objetivos do Produto

| Objetivo | Métrica de sucesso |
|---|---|
| Extrair dados de documentos com tolerância a variação de layout | Taxa de extração bem-sucedida na 1ª tentativa por tipo de documento |
| Rodar de forma confiável no ambiente serverless da Vercel | Deploy de produção estável, sem erros de timeout ou perda de arquivos |
| Permitir flexibilidade entre Ollama (dev) e API externa (produção) | Alternância de provedor via configuração, sem alteração de código |
| Garantir que saída de IA nunca seja tratada como verdade absoluta | 100% das extrações passam por validação de schema + validação humana |
| Garantir rastreabilidade de todo lançamento | 100% dos lançamentos com origem, data, documento de referência e modelo/provedor registrados |
| Usar corretamente o banco Neon em ambiente serverless | Nenhum erro de esgotamento de conexões (connection pool exhausted) em produção |

---

## 4. Personas

- **Usuário Operacional:** faz upload dos documentos e realiza a validação
  inicial dos dados extraídos pelo LLM.
- **Usuário Validador/Supervisor:** revisa lançamentos preparados, corrige
  divergências, aprova para exportação, acompanha uso/custo de LLM.
- **Administrador do Sistema:** configura provedor de LLM, variáveis de
  ambiente na Vercel, storage e conexão com o banco Neon.
- **(Futuro) Sistema Contábil Externo:** consumidor dos dados exportados
  (fora do escopo desta fase).

---

## 5. Escopo

### 5.1 Dentro do escopo (v1)
- Aplicação Django organizada em apps, com custom user model definido desde
  o início do projeto.
- Banco de dados PostgreSQL via Neon (conexão pooled para runtime, direta
  para migrações).
- Upload de documentos em PDF, imagem (JPG/PNG) e XML, com armazenamento
  externo (Vercel Blob ou S3-compatível) — nunca dependente apenas do
  filesystem local em produção.
- Fluxo de upload direto do cliente para o storage quando o arquivo exceder
  4.5MB (limite de corpo de requisição de função serverless).
- Extração de dados via LLM (Ollama em dev / API externa em produção), com
  suporte a modelos multimodais para imagens e PDFs escaneados (em vez de
  OCR local via Tesseract).
- Templates de prompt e schemas de validação por tipo de documento.
- Validação estrutural automática da saída do LLM (schema + retry
  limitado, respeitando o `maxDuration` da função serverless).
- Tela de validação humana com edição de campos e auditoria de alterações.
- Registro obrigatório de origem, data, documento de referência e
  provedor/modelo de LLM utilizado em todo lançamento preparado.
- Dashboard de controle de entradas, incluindo painel de uso de LLM.
- Exportação de lançamentos validados em CSV.
- Deploy funcional na Vercel, com variáveis de ambiente configuradas e
  banco conectado à Neon.

### 5.2 Fora do escopo (v1)
- Integração automática/API com sistemas contábeis externos (ERP).
- Fine-tuning ou treinamento de modelo próprio.
- Orquestração multi-agente ou cadeias complexas de prompts.
- Gestão avançada de permissões/perfis de usuário (RBAC completo).
- Aplicativo mobile nativo.
- Detecção de fraude/documentos adulterados.
- Processamento assíncrono via fila externa (Celery/worker dedicado) — caso
  o tempo de extração ultrapasse os limites de duração de função mesmo
  configurados, isso deve ser reavaliado como v2 (ex.: uso de Vercel
  Workflows para tarefas de duração ilimitada).
- Uso de branch dedicada da Neon por Preview Deployment (recomendado, mas
  tratado como melhoria de processo, não requisito obrigatório de v1).

---

## 6. Requisitos Funcionais

### RF01 — Upload de Documentos
O sistema deve permitir upload de arquivos PDF, JPG, PNG e XML. Arquivos até
4.5MB podem ser enviados diretamente ao backend; arquivos maiores devem
usar upload direto do cliente para o storage externo.

### RF02 — Pré-processamento de Documentos
O sistema deve extrair texto de PDF (`pdfplumber`) e estrutura de XML
(`lxml`). Para imagens e PDFs escaneados, deve preparar o conteúdo para
envio direto a um LLM multimodal, sem depender de OCR local via Tesseract.

### RF03 — Extração via LLM
O sistema deve enviar o conteúdo pré-processado, junto com um template de
prompt específico do tipo de documento, ao provedor de LLM configurado
(Ollama em dev, API externa em produção), solicitando resposta em JSON.

### RF04 — Validação Estrutural da Saída do LLM
O sistema deve validar a resposta do LLM contra o schema esperado. Em caso
de falha, deve reenviar com feedback de erro (retry limitado, respeitando
o tempo máximo de execução da função) e, ao esgotar tentativas, marcar o
documento como `precisa_revisao=True`.

### RF05 — Configuração de Provedor de LLM
O sistema deve permitir alternar entre Ollama (dev) e provedor de API
externo (produção) por configuração, sem alteração de código.

### RF06 — Validação Humana
O sistema deve exibir o documento original lado a lado com os dados
extraídos, permitindo edição manual, aprovação ou rejeição, com auditoria.

### RF07 — Registro de Lançamento Preparado
Todo lançamento aprovado deve gerar um registro `LancamentoPreparado` com
origem, data e referência ao documento original — campos obrigatórios.

### RF08 — Dashboard de Controle
O sistema deve exibir totais por tipo/status, linha do tempo, filtros,
tabela detalhada e painel de uso de LLM.

### RF09 — Exportação
O sistema deve permitir exportar lançamentos validados em CSV.

### RF10 — Autenticação
O sistema deve exigir login (custom user model do Django) para acessar
upload, validação e dashboard.

### RF11 — Configuração de Banco e Storage
O sistema deve usar a conexão pooled da Neon para tráfego de aplicação, e
armazenamento externo (Blob/S3-compatível) para arquivos, configuráveis via
variáveis de ambiente na Vercel.

---

## 7. Requisitos Não Funcionais

| Categoria | Requisito |
|---|---|
| Segurança | Chaves de API e credenciais de banco nunca hardcoded — apenas via variáveis de ambiente da Vercel |
| Privacidade | Uso de Ollama local restrito a desenvolvimento; produção usa API externa, com escolha de provedor documentada |
| Confiabilidade | Arquivos originais imutáveis, armazenados em serviço externo — nunca dependentes apenas do filesystem efêmero da função serverless |
| Confiabilidade | Saída do LLM nunca é persistida sem validação de schema |
| Resiliência | Retry de extração limitado, compatível com `maxDuration` da função Vercel |
| Performance | Conexões ao banco Neon usam string pooled; `CONN_MAX_AGE` configurado de forma conservadora |
| Precisão | Valores monetários sempre em `Decimal` |
| Extensibilidade | Novo tipo de documento e novo provedor de LLM adicionáveis via configuração/interface, sem alterar o núcleo |
| Observabilidade | Logging estruturado de erros de extração, falhas de parsing e falhas de comunicação com LLM, sem vazar dados sensíveis |
| Testabilidade | Testes automatizados com mocks de LLM e de storage — nenhuma chamada real de rede/API em CI |
| Portabilidade | `AUTH_USER_MODEL` customizado definido antes da primeira migração |
| Deploy | Aplicação reconhecida automaticamente pela Vercel como projeto Django (zero-config) |

---

## 8. Arquitetura Técnica

### 8.1 Stack
- **Backend:** Django (versão estável mais recente com suporte LTS)
- **Banco/Driver:** PostgreSQL via Neon, `psycopg` (v3)
- **Configuração:** `django-environ` (variáveis de ambiente)
- **Pré-processamento:**
  - PDF texto: `pdfplumber` (100% Python, compatível com runtime serverless)
  - XML: `lxml`
  - Imagem / PDF escaneado: envio direto a LLM multimodal (sem dependência
    de binário Tesseract)
- **Integração LLM:**
  - `OllamaProvider` (uso restrito a desenvolvimento local)
  - `APIProvider` (obrigatório em produção)
  - Validação estrutural: `pydantic` ou `jsonschema`
- **Storage de arquivos:** `django-storages` + Vercel Blob (ou
  S3-compatível) em produção; `FileSystemStorage` padrão em desenvolvimento
- **Frontend:** Django Templates + Bootstrap, Chart.js
- **Formulários:** Django Forms / ModelForms
- **Autenticação:** sistema nativo do Django, com custom user model
- **Arquivos estáticos:** `collectstatic` executado automaticamente no
  build da Vercel (servido via CDN); `WhiteNoise` em desenvolvimento local
- **Testes:** pytest-django + mocks de LLM/storage

### 8.2 Estrutura de Diretórios (proposta)
```
projeto/
├── manage.py
├── vercel.json                  # configuração de maxDuration por rota
├── pyproject.toml               # define versão do Python
├── requirements.txt
├── .env.example
├── config/                      # settings do projeto Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── usuarios/                # custom user model (AUTH_USER_MODEL)
│   ├── documentos/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── storage.py           # abstração local/Blob
│   ├── validacao/
│   │   ├── models.py
│   │   └── views.py
│   ├── dashboard/
│   │   └── views.py
│   └── llm_service/
│       ├── provider_base.py     # interface LLMProviderBase
│       ├── ollama_provider.py
│       ├── api_provider.py
│       ├── provider_factory.py
│       ├── preprocessamento/
│       │   ├── pdf_preprocessor.py
│       │   └── xml_preprocessor.py
│       └── validacao_schema.py
├── prompts/                     # templates de prompt por tipo de documento
│   ├── nota_fiscal.txt
│   ├── contrato.txt
│   ├── demonstrativo.txt
│   └── boleto.txt
├── schemas/                     # schemas de validação por tipo
│   ├── nota_fiscal.json
│   ├── contrato.json
│   ├── demonstrativo.json
│   └── boleto.json
├── templates/
│   ├── documentos/
│   ├── validacao/
│   └── dashboard/
├── static/
└── tests/
```

### 8.3 Fluxo Geral
```
Upload (direto ao backend ≤4.5MB, ou direto ao storage se maior) →
Registro Documento (arquivo em storage externo) →
Pré-processamento (texto de PDF/XML, ou imagem para LLM multimodal) →
Seleção de provider (Ollama em dev / API em produção) →
Montagem do prompt → Chamada ao LLM → Validação estrutural (schema) →
  ├─ válido → Registro DadosExtraidos
  └─ inválido → retry (limite N, dentro do maxDuration) → esgotado →
     precisa_revisao=True
→ Tela de Validação (edição humana) → Aprovação →
LancamentoPreparado (origem + data + referência) →
Dashboard (incl. uso de LLM) → Exportação CSV
```

### 8.4 Arquitetura de Deploy (Vercel + Neon)
```
┌─────────────────────────────────────────────────────────┐
│                      Vercel (Fluid Compute)               │
│  ┌───────────────────────────────────────────────────┐   │
│  │  Django (detecção zero-config via manage.py)        │  │
│  │  maxDuration configurado por rota crítica (extração) │ │
│  └───────────────────────────────────────────────────┘   │
│              │                          │                 │
│      DATABASE_URL (pooled)      BLOB_READ_WRITE_TOKEN     │
│              │                          │                 │
└──────────────┼──────────────────────────┼─────────────────┘
               ▼                          ▼
        ┌─────────────┐          ┌──────────────────┐
        │  Neon        │          │  Vercel Blob      │
        │  PostgreSQL  │          │  Storage           │
        │  (pooled +   │          │  (arquivos         │
        │   unpooled)  │          │   originais)       │
        └─────────────┘          └──────────────────┘
```

### 8.5 Considerações Específicas de Deploy
- **Detecção automática:** a Vercel identifica o projeto Django ao
  encontrar `manage.py` e lê `WSGI_APPLICATION`/`DJANGO_SETTINGS_MODULE`;
  não é necessário configurar `builds`/`routes` manualmente no
  `vercel.json` para o funcionamento básico.
- **Duração de função:** padrão de 300s (Fluid Compute); pode ser
  estendida via `maxDuration` (até 800s em planos Pro/Enterprise, até 1800s
  em beta). Rotas de extração via LLM devem ter `maxDuration` configurado
  explicitamente.
- **Upload de arquivos:** requisições diretas ao backend têm limite de
  4.5MB; arquivos maiores exigem fluxo de upload direto do cliente para o
  Blob Storage.
- **Banco de dados:** usar `DATABASE_URL` (pooled) para a aplicação e
  `DATABASE_URL_UNPOOLED` (direta) apenas para migrações ou ferramentas
  administrativas.
- **Variáveis de ambiente:** configuradas no painel da Vercel; usar
  `vercel env pull` para sincronizar localmente.
- **Tamanho do bundle:** limite padrão de 500MB — evitar dependências
  pesadas desnecessárias (ex.: bibliotecas de OCR local).

---

## 9. Modelo de Dados (Django ORM)

### 9.1 `Usuario` (custom user model)
| Campo | Tipo | Observação |
|---|---|---|
| — | `AbstractUser` (ou `AbstractBaseUser`) | Definido em `apps/usuarios`, configurado em `AUTH_USER_MODEL` **antes da primeira migração** |

### 9.2 `Documento`
| Campo | Tipo | Obrigatório | Observação |
|---|---|---|---|
| id | AutoField (PK) | Sim | |
| tipo_documento | CharField (choices) | Sim | nota_fiscal, contrato, demonstrativo, boleto |
| formato_arquivo | CharField (choices) | Sim | pdf, imagem, xml |
| arquivo_original | FileField | Sim | aponta para storage backend (local/Blob) |
| origem | CharField | Sim | upload_manual, e-mail, api (futuro) |
| data_upload | DateTimeField (auto_now_add) | Sim | |
| status | CharField (choices) | Sim | pendente, validado, rejeitado |

### 9.3 `DadosExtraidos`
| Campo | Tipo | Obrigatório | Observação |
|---|---|---|---|
| id | AutoField (PK) | Sim | |
| documento | ForeignKey → Documento | Sim | |
| campos_extraidos | JSONField | Sim | nativo PostgreSQL/JSONB |
| provedor_llm_utilizado | CharField (choices) | Sim | ollama, api |
| modelo_llm_utilizado | CharField | Sim | |
| tempo_resposta_ms | IntegerField | Não | |
| tokens_utilizados | IntegerField | Não | |
| tentativas_realizadas | IntegerField | Sim | |
| precisa_revisao | BooleanField | Sim | |
| resposta_bruta_llm | TextField | Não | apenas em caso de falha |
| data_extracao | DateTimeField (auto_now_add) | Sim | |

### 9.4 `ValidacaoLog`
| Campo | Tipo | Obrigatório |
|---|---|---|
| id | AutoField (PK) | Sim |
| documento | ForeignKey → Documento | Sim |
| usuario_validador | ForeignKey → Usuario | Sim |
| data_validacao | DateTimeField (auto_now_add) | Sim |
| alteracoes_realizadas | JSONField | Não |
| decisao | CharField (choices) | Sim | aprovado, rejeitado |

### 9.5 `LancamentoPreparado`
| Campo | Tipo | Obrigatório |
|---|---|---|
| id | AutoField (PK) | Sim |
| documento | ForeignKey → Documento | **Sim (null=False)** |
| origem | CharField | **Sim (null=False)** |
| data | DateField | **Sim (null=False)** |
| dados_finais | JSONField | Sim |
| status_exportacao | CharField (choices) | Sim | pendente, exportado |

---

## 10. Templates de Prompt e Schemas por Tipo de Documento

Mesma estrutura já validada na versão anterior (arquivos de prompt em
`prompts/` e schemas em `schemas/`, desacoplados do código):

| Tipo | Formatos suportados | Campos mínimos |
|---|---|---|
| Nota Fiscal | PDF, XML, imagem | número, série, CNPJ emitente/destinatário, data emissão, valor total, itens, chave de acesso |
| Contrato | PDF, imagem | partes envolvidas, objeto, valor, vigência (início/fim), forma de pagamento |
| Demonstrativo | PDF, imagem | período de referência, categoria/conta, valores (débito/crédito), saldo |
| Boleto | PDF, imagem | linha digitável, valor, vencimento, beneficiário, pagador |

Para imagem/PDF escaneado, o prompt inclui a imagem diretamente (entrada
multimodal), em vez de texto pré-extraído via OCR.

---

## 11. Regras de Negócio Críticas

1. Nenhum lançamento (`LancamentoPreparado`) pode existir sem origem, data e
   referência ao documento original.
2. Arquivos originais são imutáveis e armazenados em serviço externo
   (Vercel Blob/S3-compatível) em produção — nunca apenas em disco local.
3. Nenhum dado é enviado automaticamente a sistemas externos.
4. Todo valor monetário é tratado como `Decimal`.
5. A saída do LLM NUNCA é persistida sem validação de schema.
6. Retries de extração têm limite máximo, compatível com o `maxDuration`
   da função serverless.
7. Ollama é restrito a desenvolvimento local; produção exige API externa.
8. Toda alteração manual é registrada em `ValidacaoLog`.
9. Um documento só gera `LancamentoPreparado` após aprovação humana.
10. Conexões ao banco Neon usam a string pooled para tráfego de aplicação.
11. `AUTH_USER_MODEL` customizado deve ser definido antes da primeira
    migração.
12. Imagens e PDFs escaneados são processados via LLM multimodal, não via
    OCR local dependente de binário (Tesseract).

---

## 12. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Chamada de LLM/OCR excede o `maxDuration` da função serverless | Timeout (504) | Configurar `maxDuration` explicitamente nas rotas de extração; limitar retries; considerar Vercel Workflows caso o processamento seja consistentemente longo |
| Upload de documento grande excede limite de 4.5MB | Falha de upload | Implementar fluxo de upload direto do cliente para o storage externo |
| Cold start do banco Neon (scale-to-zero) | Latência na primeira requisição após inatividade | Avaliar manter uma unidade de computação mínima ativa, se a latência for crítica |
| Esgotamento de conexões de banco (connection pool exhausted) | Erros de conexão em produção | Usar sempre a string pooled (`DATABASE_URL`) e `CONN_MAX_AGE` conservador |
| `pytesseract`/Tesseract indisponível no runtime da Vercel | Falha de extração de imagens/PDFs escaneados | Usar LLM multimodal em vez de OCR local para esse caminho |
| LLM "alucina" valores plausíveis, mas incorretos | Erro contábil silencioso | Validação humana obrigatória antes de qualquer lançamento |
| Exposição de dados sensíveis a provedor de API externo (obrigatório em produção) | Risco de LGPD | Documentar política de retenção do provedor escolhido; minimizar dados enviados quando possível |
| Bundle da aplicação excede limite de tamanho | Falha de deploy | Evitar dependências pesadas/desnecessárias (ex.: bibliotecas de OCR local) |

---

## 13. Glossário

- **LLM:** Large Language Model.
- **Ollama:** ferramenta para rodar LLMs localmente.
- **Multimodal:** modelo capaz de processar texto e imagem na mesma
  entrada.
- **Fluid Compute:** modelo de execução de funções da Vercel, com cobrança
  por CPU ativa e suporte a durações mais longas.
- **Pooled connection:** conexão de banco através de um pooler (ex.:
  PgBouncer), recomendada para ambientes serverless com muitas conexões
  concorrentes.
- **Scale-to-zero:** capacidade do Neon de "desligar" o compute do banco
  quando inativo, reduzindo custo, ao custo de latência na retomada.
- **NF-e:** Nota Fiscal Eletrônica.
- **LGPD:** Lei Geral de Proteção de Dados (Brasil).
- **Lançamento preparado:** registro pronto para ser levado ao sistema
  contábil externo, mas ainda não integrado automaticamente.

---

## 14. Plano de Sprints (Checklist de Desenvolvimento)

> Cada sprint deve ser concluída em ordem, pois há dependência técnica entre elas.
> Marque `[x]` ao concluir cada tarefa.

### Sprint 0 — Setup e Fundação do Projeto Django
- [ ] Criar repositório Git e projeto Django (`django-admin startproject config .`)
- [ ] Criar apps: `usuarios`, `documentos`, `validacao`, `dashboard`, `llm_service`
- [ ] Definir versão do Python via `pyproject.toml` (ou `.python-version`), compatível com o runtime da Vercel
- [ ] Configurar `requirements.txt` inicial (Django, psycopg, django-environ, pydantic, django-storages)
- [ ] Criar `.env.example` com variáveis necessárias (`DJANGO_SECRET_KEY`, `DATABASE_URL`, `DATABASE_URL_UNPOOLED`, `LLM_PROVIDER`, `OLLAMA_HOST`, `OLLAMA_MODEL`, `LLM_API_KEY`, `LLM_MODEL`, `EXTRACTION_MAX_RETRIES`, `BLOB_READ_WRITE_TOKEN`)
- [ ] Configurar `django-environ` em `settings.py` para carregar variáveis de ambiente
- [ ] Configurar logging estruturado (evitando log de dados sensíveis)
- [ ] Criar `README.md` inicial com instruções de setup
- [ ] Configurar pytest-django e estrutura de testes
- [ ] Configurar `.gitignore` (venv, `__pycache__`, `.env`, arquivos de mídia locais)

### Sprint 1 — Custom User Model e Modelagem de Dados
- [ ] Criar `Usuario` (custom user model) no app `usuarios`, estendendo `AbstractUser`
- [ ] Configurar `AUTH_USER_MODEL` em `settings.py` **antes de qualquer migração**
- [ ] Criar model `Documento` (tipo_documento, formato_arquivo, arquivo_original, origem, data_upload, status)
- [ ] Criar model `DadosExtraidos` (documento FK, campos_extraidos JSONField, provedor_llm_utilizado, modelo_llm_utilizado, tempo_resposta_ms, tokens_utilizados, tentativas_realizadas, precisa_revisao, resposta_bruta_llm, data_extracao)
- [ ] Criar model `ValidacaoLog` (documento FK, usuario_validador FK, data_validacao, alteracoes_realizadas JSONField, decisao)
- [ ] Criar model `LancamentoPreparado` (documento FK null=False, origem null=False, data null=False, dados_finais JSONField, status_exportacao)
- [ ] Definir choices (tipo_documento, formato_arquivo, status_documento, provedor_llm, decisao, status_exportacao)
- [ ] Escrever testes unitários dos models (criação, constraints null=False, relacionamentos)
- [ ] Criar fixtures/seed de dados para desenvolvimento local

### Sprint 2 — Configuração do Banco de Dados Neon
- [ ] Criar projeto no Neon e obter as strings de conexão pooled e unpooled
- [ ] Configurar `DATABASES` em `settings.py` usando `DATABASE_URL` (pooled) via `django-environ`
- [ ] Configurar `CONN_MAX_AGE=0` (ou valor conservador) para compatibilidade com ambiente serverless
- [ ] Documentar quando usar `DATABASE_URL_UNPOOLED` (migrações/ferramentas administrativas)
- [ ] Gerar e aplicar migrations iniciais contra o banco Neon
- [ ] Validar conexão local via `.env` apontando para o banco Neon (ou Postgres local para desenvolvimento offline)
- [ ] Escrever teste de smoke de conexão com o banco

### Sprint 3 — Autenticação
- [ ] Configurar views de login/logout usando o sistema de autenticação nativo do Django
- [ ] Criar templates de login
- [ ] Criar comando de management para criar usuário administrador inicial
- [ ] Proteger views de upload, validação e dashboard com `@login_required` (ou `LoginRequiredMixin`)
- [ ] Escrever testes de autenticação (login válido, inválido, acesso negado sem login)

### Sprint 4 — Armazenamento de Arquivos (Storage Backend)
- [ ] Implementar abstração de storage: `FileSystemStorage` para desenvolvimento local
- [ ] Configurar `django-storages` com backend para Vercel Blob (ou S3-compatível) para produção
- [ ] Configurar `DEFAULT_FILE_STORAGE`/`STORAGES` para alternar entre backends via variável de ambiente
- [ ] Implementar endpoint para geração de token de upload direto do cliente (para arquivos >4.5MB)
- [ ] Garantir que arquivos originais nunca sejam sobrescritos (nomes únicos/imutabilidade)
- [ ] Escrever testes de storage usando mocks (sem chamadas reais ao Blob em CI)

### Sprint 5 — Upload de Documentos
- [ ] Criar views/forms de upload no app `documentos`
- [ ] Implementar fluxo de upload direto ao backend para arquivos ≤4.5MB
- [ ] Implementar fluxo de upload direto ao storage para arquivos maiores
- [ ] Implementar validação de tipo de arquivo (PDF, PNG, JPG, XML) e tamanho máximo
- [ ] Persistir registro `Documento` com origem = `upload_manual`
- [ ] Criar tela de listagem de documentos enviados com filtro por status
- [ ] Implementar soft delete (marcação lógica, sem excluir arquivo do storage)
- [ ] Escrever testes de upload (arquivo válido, tipo inválido, tamanho excedido, fluxo direto ao storage)

### Sprint 6 — Camada de Abstração de LLM (Provider Pattern)
- [ ] Criar interface `LLMProviderBase` com método `extrair(conteudo_documento, prompt_template, schema_esperado) -> dict`, com suporte a entrada multimodal
- [ ] Implementar `OllamaProvider` (uso restrito a desenvolvimento local, incluindo suporte a modelo de visão)
- [ ] Implementar `APIProvider` (obrigatório em produção, com suporte a modelos multimodais)
- [ ] Implementar `ProviderFactory` que seleciona o provider ativo com base em `LLM_PROVIDER`, bloqueando Ollama fora do ambiente de desenvolvimento
- [ ] Implementar `MockProvider` para uso exclusivo em testes
- [ ] Garantir que nenhuma chave de API seja logada ou exposta em mensagens de erro
- [ ] Escrever testes da camada de LLM usando `MockProvider`

### Sprint 7 — Pré-processamento de Documentos
- [ ] Implementar `pdf_preprocessor.py` (extração de texto via `pdfplumber`)
- [ ] Implementar lógica de detecção de PDF sem texto extraível (candidato a envio como imagem para LLM multimodal)
- [ ] Implementar `xml_preprocessor.py` (parsing via `lxml`)
- [ ] Implementar preparação de imagem para envio multimodal (sem dependência de OCR local)
- [ ] Padronizar saída de todos os preprocessors em um formato comum
- [ ] Escrever testes de pré-processamento com arquivos de exemplo (fixtures) para cada formato

### Sprint 8 — Templates de Prompt e Schemas de Validação
- [ ] Criar templates de prompt (`prompts/nota_fiscal.txt`, `contrato.txt`, `demonstrativo.txt`, `boleto.txt`), com variante para entrada multimodal
- [ ] Criar schemas de validação (`schemas/nota_fiscal.json`, `contrato.json`, `demonstrativo.json`, `boleto.json`)
- [ ] Implementar carregador de templates/schemas
- [ ] Escrever testes do carregador (template/schema válido, ausente, mal formatado)

### Sprint 9 — Extração via LLM e Validação Estrutural
- [ ] Implementar serviço de extração que orquestra: pré-processamento → montagem do prompt → chamada ao provider → validação
- [ ] Implementar validação da resposta do LLM contra o schema esperado (`pydantic`/`jsonschema`)
- [ ] Implementar lógica de retry com feedback de erro ao LLM, respeitando `EXTRACTION_MAX_RETRIES` e o `maxDuration` da função
- [ ] Implementar conversão explícita e validada de campos monetários para `Decimal`
- [ ] Implementar marcação automática `precisa_revisao=True` ao esgotar tentativas
- [ ] Registrar provedor, modelo, tempo de resposta, tokens e tentativas em `DadosExtraidos`
- [ ] Integrar o serviço de extração ao fluxo pós-upload
- [ ] Escrever testes de extração ponta a ponta usando `MockProvider`

### Sprint 10 — Fluxo de Validação Humana
- [ ] Criar views do app `validacao`
- [ ] Criar tela de fila de documentos pendentes (priorizando `precisa_revisao`)
- [ ] Criar tela de validação com preview do documento original e campos extraídos lado a lado
- [ ] Implementar formulário de edição de campos extraídos (Django Forms)
- [ ] Implementar ação "Aprovar" (gera `LancamentoPreparado`, grava `ValidacaoLog`)
- [ ] Implementar ação "Rejeitar" (marca documento como rejeitado, exige motivo)
- [ ] Implementar cálculo e registro do diff entre dados extraídos e dados validados
- [ ] Escrever testes do fluxo completo (aprovação, rejeição, edição, auditoria)

### Sprint 11 — Dashboard de Controle
- [ ] Criar views do app `dashboard`
- [ ] Implementar cards de totais (documentos por status e por tipo)
- [ ] Implementar gráfico de linha do tempo com Chart.js
- [ ] Implementar filtros por intervalo de datas, tipo de documento e status
- [ ] Implementar painel de uso de LLM (provedor/modelo mais utilizado, taxa de sucesso, taxa de `precisa_revisao`)
- [ ] Implementar tabela detalhada de lançamentos preparados com paginação
- [ ] Escrever testes das queries de agregação do dashboard

### Sprint 12 — Exportação
- [ ] Implementar exportação de lançamentos validados em CSV
- [ ] Implementar atualização de `status_exportacao` após exportação
- [ ] Documentar estrutura do CSV exportado
- [ ] Escrever testes de exportação

### Sprint 13 — Deploy na Vercel com Neon
- [ ] Configurar `vercel.json` com `maxDuration` para as rotas de extração (upload/processamento)
- [ ] Configurar variáveis de ambiente no painel da Vercel (banco, storage, LLM)
- [ ] Validar detecção automática do projeto Django pela Vercel (zero-config)
- [ ] Configurar build para rodar `collectstatic` corretamente
- [ ] Conectar o projeto ao Neon via integração da Vercel (ou configuração manual das strings de conexão)
- [ ] Testar deploy de preview e validar que a aplicação conecta corretamente ao banco e ao storage
- [ ] Validar upload de arquivo grande (>4.5MB) em produção via fluxo direto ao storage
- [ ] Validar extração via provedor de API externo em produção (Ollama não disponível nesse ambiente)
- [ ] Documentar o processo de deploy no README

### Sprint 14 — Segurança, Qualidade e Documentação Final
- [ ] Revisar tratamento de erros e páginas customizadas (404, 500)
- [ ] Revisar logging de erros de extração e falhas de comunicação com LLM (sem vazamento de dados sensíveis)
- [ ] Validar que nenhuma chave de API ou string de conexão está hardcoded ou versionada no repositório
- [ ] Rodar cobertura de testes (`pytest --cov`) e cobrir eventuais lacunas
- [ ] Revisar checklist de conformidade com as Regras de Negócio Críticas (seção 11)
- [ ] Finalizar `README.md` com instruções completas de setup local, configuração de Neon/Blob/LLM e deploy na Vercel
- [ ] Documentar guia de extensibilidade: "Como adicionar um novo tipo de documento" e "Como adicionar um novo provedor de LLM"
- [ ] Revisão final de UX das telas de upload, validação e dashboard

---

## 15. Critérios de Aceite do Projeto (Definition of Done)

- [ ] Aplicação roda localmente via `python manage.py runserver` sem erros.
- [ ] Deploy de produção na Vercel funciona, conectado ao banco Neon (via conexão pooled) e ao storage externo.
- [ ] Upload e extração via LLM funcionam para os 4 tipos de documento, com Ollama em dev e provedor de API em produção.
- [ ] Uploads maiores que 4.5MB funcionam via fluxo direto ao storage.
- [ ] Respostas inválidas do LLM são tratadas com retry limitado, dentro do `maxDuration` configurado — nunca com dado incorreto persistido silenciosamente.
- [ ] Fluxo de validação humana funciona com auditoria completa.
- [ ] Todo `LancamentoPreparado` possui origem, data e documento de referência preenchidos.
- [ ] Dashboard exibe dados reais, incluindo painel de uso de LLM.
- [ ] Exportação CSV gera arquivo consistente com os dados validados.
- [ ] Suíte de testes automatizados passa integralmente, sem depender de chamadas reais de rede/API/storage.
- [ ] README permite configurar Neon, storage, provedor de LLM e fazer o deploy do zero.
