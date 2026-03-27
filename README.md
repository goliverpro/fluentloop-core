# fluentloop-core

Backend do FluentLoop — Python + FastAPI.

Orquestra as chamadas para Claude (LLM), Azure Speech (STT + pronúncia) e OpenAI TTS.

## Stack

- **Python 3.12** + **FastAPI**
- **Supabase** — banco de dados, auth e storage
- **Claude (Anthropic)** — LLM para conversação
- **Azure Speech** — STT + avaliação de pronúncia
- **OpenAI TTS** — síntese de voz
- **Stripe** — pagamentos
- **slowapi** — rate limiting

## Setup

```bash
# 1. Clonar o repositório
git clone https://github.com/goliverpro/fluentloop-core.git
cd fluentloop-core

# 2. Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Preencher .env com suas chaves

# 5. Rodar o servidor
uvicorn app.main:app --reload
```

Acesse: `http://localhost:8000/docs`

## Estrutura

```
app/
├── main.py          # Entry point, middlewares, routers
├── config.py        # Settings via pydantic-settings
├── db/
│   └── supabase.py  # Cliente Supabase singleton
├── middleware/
│   └── auth.py      # Validação de JWT
├── routers/         # Endpoints por domínio
│   ├── users.py
│   ├── sessions.py
│   ├── chat.py      # SSE streaming com Claude
│   ├── speech.py    # STT + TTS
│   ├── scenarios.py
│   └── billing.py   # Stripe
├── services/        # Lógica de negócio e integrações
└── models/          # Schemas Pydantic
```

## Rodando localmente (Git Bash / Windows)

Se o ambiente virtual já estiver criado, não é necessário ativar — chame o uvicorn diretamente:

```bash
cd /c/Users/gabri/Documents/IA/fluentloop-core
.venv/Scripts/uvicorn app.main:app --reload
```

Acesse: `http://localhost:8000/docs`

## Documentação

Documentação completa do projeto: [fluentloop-docs](https://github.com/goliverpro/fluentloop-docs)
