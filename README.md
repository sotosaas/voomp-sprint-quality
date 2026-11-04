# Sprint Quality Dashboard — Voomp

Dashboard para rastreamento de qualidade de entrega por sprint, identificando cards com sub-bugs e ranking de desenvolvedores.

🚀 **Deploy:** [sprintquality.streamlit.app](https://sprintquality.streamlit.app)

## Arquitetura

```
voomp-sprint-quality/
├── app.py                      # Entry point (minimal)
├── src/
│   ├── config.py               # Configuration with dataclasses
│   ├── models/                 # Domain models (pure data)
│   │   ├── issue.py            # Issue, SubBug
│   │   ├── sprint.py           # Sprint
│   │   └── metrics.py          # DevMetrics, SprintMetrics, etc.
│   ├── services/               # Business logic
│   │   ├── jira_api.py         # Low-level HTTP client
│   │   ├── jira_service.py     # Jira operations orchestration
│   │   └── metrics_service.py  # Metrics computation
│   ├── repositories/           # Data persistence
│   │   └── cache_repository.py # File-based cache
│   └── ui/                     # Presentation layer
│       ├── styles.py           # CSS centralized
│       ├── icons.py            # SVG icons (Greenn design)
│       ├── components/         # Reusable UI components
│       │   ├── sidebar.py
│       │   ├── metric_cards.py
│       │   ├── charts.py
│       │   └── tables.py
│       └── pages/              # Page compositions
│           ├── dashboard.py    # Sprint analysis
│           └── overview.py     # 30-day comparison
├── .streamlit/
│   └── config.toml             # Streamlit theme
├── requirements.txt
└── .env.example
```

### Princípios de Design

- **Separation of Concerns**: Cada módulo tem uma única responsabilidade
- **Dependency Injection**: Services recebem dependências via construtor
- **Dataclasses**: Models são imutáveis (frozen=True) quando possível
- **Type Hints**: Tipagem completa para melhor IDE support
- **Caching**: Cache em dois níveis (Streamlit + filesystem)

## Instalação Local

```bash
# Clone o repositório
git clone https://github.com/sotosaas/voomp-sprint-quality.git
cd voomp-sprint-quality

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows

# Instale as dependências
pip install -r requirements.txt

# Configure as credenciais
cp .env.example .env
# Edite .env com suas credenciais Jira
```

## Configuração

### Variáveis de Ambiente

| Variável | Descrição |
|----------|-----------|
| `JIRA_URL` | URL do Jira (ex: `https://cogna.atlassian.net`) |
| `JIRA_EMAIL` | Email da conta Jira |
| `JIRA_API_TOKEN` | Token de API Jira |

### Obter Token de API

1. Acesse [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Clique em "Create API token"
3. Dê um nome (ex: "Sprint Quality Dashboard")
4. Copie o token gerado

## Execução

```bash
streamlit run app.py
```

Acesse: http://localhost:8501

## Features

- **Dashboard por Sprint**: Análise detalhada de cards e bugs por sprint
- **Ranking de Desenvolvedores**: Score de qualidade (cards ÷ bugs + 1)
- **Tendência de Qualidade**: Evolução ao longo das sprints
- **Visão Geral**: Comparativo de 30 dias entre todos os produtos
- **Cache Inteligente**: 15 min em arquivo + 30 min no Streamlit

## Produtos Monitorados

| Projeto | Nome | Descrição |
|---------|------|-----------|
| VADM | Admin | Painel administrativo |
| VPLY | Play | Plataforma de vídeos |
| VMPG | Meios de Pagamento | Sistema de pagamentos |
| VSUS | Sustentação | Suporte e manutenção |
| VBEP | Backoffice ERP | Sistema financeiro |

## Deploy no Streamlit Cloud

1. Fork/push para GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte o repositório
4. Configure secrets:

```toml
# .streamlit/secrets.toml (NÃO commitar!)
JIRA_URL = "https://cogna.atlassian.net"
JIRA_EMAIL = "seu-email@empresa.com"
JIRA_API_TOKEN = "seu-token-aqui"
```

## Licença

Uso interno Voomp/Cogna.
