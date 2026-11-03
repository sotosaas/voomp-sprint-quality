# Voomp Sprint Quality Dashboard

Dashboard local para acompanhar a qualidade das entregas de sprint por produto,
integrado ao Jira Cloud via API Token pessoal.

---

## Funcionalidades

| Página | O que mostra |
|--------|-------------|
| **Sprint Analysis** | Filtro por produto e sprint · KPIs · tabela de cards · ranking de devs · cards com mais bugs · tendência por sprint |
| **Visão Geral** | Resumo dos últimos 30 dias de todos os produtos side-by-side · ranking geral de qualidade |

---

## Requisitos

- Python 3.11+
- Acesso ao Jira Cloud da Cogna com um API Token pessoal

---

## Instalação

```powershell
# 1. Entre na pasta do projeto
cd "C:\Users\matheus.soto\Desktop\Voomp-Workspace\voomp-sprint-quality"

# 2. Crie e ative o ambiente virtual
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> **Nota:** Se o PowerShell bloquear a ativação do venv com erro de política de execução,
> use sempre o Python do venv diretamente: `.\.venv\Scripts\python.exe`

---

## Configuração

```powershell
copy .env.example .env
# Edite o .env com suas credenciais
```

Conteúdo do `.env`:

```env
JIRA_URL=https://cogna.atlassian.net
JIRA_EMAIL=seu.email@cogna.com.br
JIRA_API_TOKEN=seu_token_aqui
```

Gere seu token em: https://id.atlassian.com/manage-profile/security/api-tokens

---

## Rodando

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Acesse em: **http://localhost:8501**

---

## Testando a conexão com o Jira

```powershell
.\.venv\Scripts\python.exe jira_client.py
```

Saída esperada:

```
✅ Conectado como: Seu Nome (seu.email@cogna.com.br)

Chave  Nome no Jira                             Produto (config)
----------------------------------------------------------------------
  VADM  ...                                      Admin  ✅
  VPLY  ...                                      Play  ✅
  VMPG  ...                                      Meios de Pagamento  ✅
  VSUS  ...                                      Sustentação  ✅
  VBEP  ...                                      Backoffice ERP  ✅
```

---

## Projetos configurados

| Chave | Produto | Cor |
|-------|---------|-----|
| VADM  | Admin | 🔵 |
| VPLY  | Play | 🟢 |
| VMPG  | Meios de Pagamento | 🩷 |
| VSUS  | Sustentação | 🟠 |
| VBEP  | Backoffice ERP | 🟣 |

---

## Estrutura do projeto

```
voomp-sprint-quality/
├── .env                    # Suas credenciais (não versionar)
├── .env.example            # Template de credenciais
├── .gitignore
├── requirements.txt
├── config.py               # Variáveis de ambiente e mapeamento de projetos
├── jira_client.py          # Wrapper da API Jira (boards, sprints, issues)
├── data_processor.py       # Métricas, cache TTL, DataFrames
├── app.py                  # Dashboard principal (Sprint Analysis)
├── pages/
│   └── 01_Visão_Geral.py  # Página de visão geral dos últimos 30 dias
└── .cache/                 # Cache local de respostas da API (auto-gerado)
```

---

## Cache

Dados são cacheados localmente por **15 minutos** para evitar chamadas excessivas ao Jira.
Use o botão **"🔄 Atualizar dados"** na sidebar para forçar uma atualização imediata.

---

## Definições

| Termo | Definição |
|-------|-----------|
| **Card entregue** | Issue com status `Em produção` na sprint selecionada |
| **Sub-bug** | Sub-tarefa do tipo `Sub-bug` vinculada ao card pai |
| **Quality Score** | `cards_entregues / (sub_bugs + 1)` — quanto maior, melhor |
| **Taxa de bug** | % de cards que geraram pelo menos 1 sub-bug |
