# DESIGN.md — Design System Extração Contábil

Guia completo do design system para replicação em outros projetos.

---

## 🎨 Paleta de Cores

### Cores Primárias
```css
--admin-navy: #1B2838;        /* Azul marinho escuro - headers, texto principal */
--admin-navy-light: #2A3F54;  /* Variante mais clara - hover, cards */
--admin-gold: #C9A84C;        /* Dourado - accent, botões primários, links */
--admin-gold-light: #D4B866;  /* Dourado hover */
```

### Cores de Fundo/Neutras
```css
--admin-paper: #F5F0E8;       /* Bege claro - background principal */
--admin-ink: #2D2820;         /* Quase preto - texto corpo */
--admin-ink-light: #6B5F50;   /* Texto secundário, labels */
```

### Cores Semânticas
```css
--admin-success: #16A34A;     /* Verde - validado, ok */
--admin-warning: #F59E0B;     /* Amarelo - pendente, revisão */
--admin-danger: #DC2626;      /* Vermelho - rejeitado, erro */
--admin-info: #3B82F6;        /* Azul - info, exportado */
```

### Aplicação por Contexto

| Elemento | Cor |
|----------|-----|
| Header admin | `--admin-navy` |
| Botão primário | `--admin-gold` bg + `--admin-navy` text |
| Link | `--admin-gold` |
| Card header | `--admin-paper` bg + `--admin-navy` text + border `--admin-gold` 15% |
| Badge pendente | `--admin-warning` 12% bg + `--admin-warning` dark text |
| Badge validado | `--admin-success` 12% bg + `--admin-success` dark text |
| Badge rejeitado | `--admin-danger` 12% bg + `--admin-danger` dark text |
| Input focus | `--admin-gold` border + 3px ring 15% |
| Hover card | `--admin-shadow-lg` + border `--admin-gold` 30% |

---

## 🔤 Tipografia

### Fontes
```css
/* Display / Headings */
font-family: 'Cormorant Garamond', serif;
weights: 500, 600, 700;

/* UI / Body */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
weights: 300, 400, 500, 600;
```

### Google Fonts Import
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
```

### Escala Tipográfica
| Uso | Fonte | Tamanho | Peso |
|-----|-------|---------|------|
| Brand logo | Cormorant | 1.5rem | 600 |
| Page title (h1) | Cormorant | 1.75rem | 600 |
| Card title (h3) | Cormorant | 1.25rem | 600 |
| Module card name | Cormorant | 1.25rem | 600 |
| Body text | Inter | 0.875rem | 400 |
| Label / small | Inter | 0.75-0.8125rem | 500 |
| Badge | Inter | 0.7rem | 600 (uppercase) |
| Table header | Inter | 0.75rem | 600 (uppercase, letter-spacing 0.05em) |
| Code/mono | monospace | 0.8125rem | 400 |

---

## 📏 Espaçamento

### Sistema Base: 4px (0.25rem)
```css
--space-xs: 0.25rem;   /* 4px */
--space-sm: 0.5rem;    /* 8px */
--space-md: 1rem;      /* 16px */
--space-lg: 1.5rem;    /* 24px */
--space-xl: 2rem;      /* 32px */
--space-2xl: 3rem;     /* 48px */
```

### Aplicação
| Contexto | Espaçamento |
|----------|-------------|
| Card padding | `--space-lg` (1.5rem) |
| Card header padding | `--space-md` `--space-xl` (1rem 1.5rem) |
| Section gap | `--space-lg` (1.5rem) |
| Grid gap | `--space-lg` (1.5rem) |
| Input padding | `--space-sm` `--space-md` (0.625rem 0.875rem) |
| Button padding | `--space-sm` `--space-md` (0.5rem 1rem) |
| Badge padding | 0.25rem 0.625rem |
| Table cell padding | 1rem |

---

## 📦 Componentes

### 1. Botões

#### Primário (Gold)
```css
.admin-btn-gold {
  background: var(--admin-gold);
  color: var(--admin-navy);
  border: none;
}
.admin-btn-gold:hover {
  background: var(--admin-gold-light);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(201,168,76,0.3);
}
```

#### Secundário (Navy)
```css
.admin-btn-navy {
  background: var(--admin-navy);
  color: #fff;
}
```

#### Outline
```css
.admin-btn-outline {
  background: transparent;
  border: 1px solid var(--admin-ink-light);
  color: var(--admin-ink);
}
```

#### Tamanhos
| Classe | Padding | Font-size |
|--------|---------|-----------|
| `.admin-btn` | 0.5rem 1rem | 0.8125rem |
| `.admin-btn-sm` | 0.375rem 0.75rem | 0.75rem |

---

### 2. Cards

#### Card Base
```css
.admin-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  border: none;
  transition: all 0.2s ease;
}
.admin-card:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}
```

#### Card Header
```css
.admin-card-header {
  background: var(--admin-paper);
  border-bottom: 1px solid rgba(201,168,76,0.15);
  padding: 1rem 1.5rem;
  color: var(--admin-navy);
  font-weight: 600;
  display: flex; align-items: center; gap: 0.5rem;
}
.admin-card-header i { color: var(--admin-gold); }
```

---

### 3. Badges

```css
.admin-badge {
  display: inline-flex; align-items: center; gap: 0.25rem;
  padding: 0.25rem 0.625rem;
  border-radius: 50px;
  font-size: 0.7rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
}

/* Variantes */
.admin-badge-pendente    { background: rgba(245,158,11,0.12); color: #B45309; }
.admin-badge-validado    { background: rgba(22,163,74,0.12);  color: #15803D; }
.admin-badge-rejeitado   { background: rgba(220,38,38,0.12);  color: #B91C1C; }
.admin-badge-precisa-revisao { background: rgba(245,158,11,0.12); color: #B45309; }
.admin-badge-ok          { background: rgba(22,163,74,0.12);  color: #15803D; }
.admin-badge-exportado   { background: rgba(59,130,246,0.12); color: #2563EB; }
```

---

### 4. Formulários

```css
.admin-form-label {
  font-weight: 500; color: var(--admin-ink);
  margin-bottom: 0.375rem; font-size: 0.875rem;
}

.admin-form-control {
  border-radius: 6px;
  border: 1px solid rgba(45,40,32,0.15);
  padding: 0.625rem 0.875rem; font-size: 0.875rem;
  background: #fff;
}
.admin-form-control:focus {
  border-color: var(--admin-gold);
  box-shadow: 0 0 0 3px rgba(201,168,76,0.15);
  outline: none;
}

.admin-form-select {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3e%3cpath fill='none' stroke='%236B5F50' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M2 5l6 6 6-6'/%3e%3c/svg%3e");
  background-position: right 0.75rem center;
  background-size: 16px 12px;
}
```

---

### 5. Tabelas

```css
.admin-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }

.admin-table th {
  background: var(--admin-paper);
  color: var(--admin-ink-light);
  font-weight: 600; font-size: 0.75rem;
  text-transform: uppercase; letter-spacing: 0.05em;
  padding: 0.875rem 1rem;
  border-bottom: 2px solid rgba(201,168,76,0.15);
  text-align: left;
}

.admin-table td {
  padding: 1rem; border-bottom: 1px solid rgba(45,40,32,0.06);
  vertical-align: middle;
}
.admin-table tbody tr:hover { background: rgba(201,168,76,0.03); }
```

---

### 6. Header Admin

```css
.admin-header {
  background: var(--admin-navy);
  padding: 1rem 0;
  position: sticky; top: 0; z-index: 100;
  box-shadow: var(--admin-shadow);
}

.admin-brand-link { color: #fff; display: flex; align-items: center; gap: 0.75rem; }
.admin-brand-icon { font-size: 1.75rem; color: var(--admin-gold); }
.admin-brand-text { font-size: 1.5rem; font-weight: 600; letter-spacing: 0.02em; }
.admin-brand-sub { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em;
  color: rgba(255,255,255,0.6); background: rgba(255,255,255,0.1);
  padding: 0.125rem 0.5rem; border-radius: 4px; font-weight: 500; }
```

---

### 7. Module Cards (Index Admin)

```css
.admin-module-card {
  background: #fff; border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  border: 1px solid rgba(45,40,32,0.06);
  padding: 1.5rem; text-decoration: none; color: inherit;
  display: flex; flex-direction: column; height: 100%;
  transition: all 0.2s ease;
}
.admin-module-card:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  transform: translateY(-2px); border-color: rgba(201,168,76,0.3);
}

.admin-module-icon {
  width: 48px; height: 48px; border-radius: 12px;
  background: linear-gradient(135deg, var(--admin-gold) 0%, var(--admin-gold-light) 100%);
  display: flex; align-items: center; justify-content: center;
  color: var(--admin-navy); font-size: 1.25rem; margin-bottom: 1rem;
}

.admin-module-name { font-family: 'Cormorant Garamond', serif;
  font-size: 1.25rem; font-weight: 600; color: var(--admin-navy); margin-bottom: 0.5rem; }
```

---

## 📱 Responsividade

### Breakpoints
```css
/* Mobile first - Bootstrap 5.3 breakpoints */
@media (max-width: 575.98px) { /* xs */ }
@media (max-width: 767.98px) { /* sm */ }
@media (max-width: 991.98px) { /* md */ }
@media (max-width: 1199.98px) { /* lg */ }
@media (min-width: 1200px) { /* xl */ }
```

### Ajustes Mobile (≤767px)
```css
.admin-brand-text { font-size: 1.25rem; }
.admin-brand-sub { display: none; }
.admin-nav-link span { display: none; }
.admin-toolbar { flex-direction: column; align-items: stretch; }
.admin-toolbar-input { min-width: 100%; }
.admin-table { font-size: 0.8125rem; }
.admin-table th, .admin-table td { padding: 0.625rem 0.75rem; }
```

---

## 🌫️ Sombras

```css
--admin-shadow: 0 2px 8px rgba(0,0,0,0.08);
--admin-shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
```

---

## 🔄 Transições

```css
--admin-transition: all 0.2s ease;
/* Aplicar em: cards, botões, links, inputs, badges, table rows */
```

---

## 📋 Checklist de Implementação em Novo Projeto

- [ ] Adicionar Google Fonts (Cormorant Garamond + Inter)
- [ ] Definir CSS Custom Properties (cores, espaçamento, sombras)
- [ ] Criar `admin.css` com componentes acima
- [ ] Sobrescrever `templates/admin/base.html` (sem sidebar nativo)
- [ ] Configurar `AdminSite` customizado com ordenação de apps
- [ ] Registrar models no `AdminSite` customizado
- [ ] Adicionar `base.html` principal com sidebar do projeto
- [ ] Incluir Bootstrap 5.3 + Bootstrap Icons via CDN
- [ ] Testar responsividade em mobile/tablet/desktop
- [ ] Verificar contraste (WCAG AA mínimo)

---

## 📁 Estrutura de Arquivos de Design

```
static/
├── css/
│   ├── main.css      # Projeto principal (sidebar, dashboard, forms)
│   └── admin.css     # Admin customizado (este design system)
templates/
├── base.html         # Layout principal com sidebar do projeto
├── admin/
│   └── base.html     # Admin customizado (sem sidebar Django)
config/
└── admin_site.py     # ExtracaoAdminSite com ordenação
```

---

## 🎯 Princípios de Design

1. **Clareza sobre decoração** — Interface limpa, foco na informação
2. **Hierarquia visual clara** — Cormorant para títulos, Inter para UI
3. **Feedback imediato** — Hover/focus/active states em tudo interativo
4. **Consistência semântica** — Cores iguais = mesmo significado
5. **Acessibilidade** — Contraste ≥ 4.5:1, focus visible, labels associados
6. **Performance** — CSS nativo, sem build step, CDN para fonts/icons