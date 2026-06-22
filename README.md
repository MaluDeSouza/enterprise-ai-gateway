# 🛰️ Enterprise AI Gateway (LLM Router)

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)
![Redis](https://img.shields.io/badge/Redis-Vector_Search-DC382D.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Async-4169E1.svg)

O **Enterprise AI Gateway** é um proxy reverso inteligente e assíncrono projetado para resolver os maiores problemas de adoção de IA em grandes corporações: **Vendor Lock-in, Custos Descontrolados e Falta de Resiliência**. 

Em vez de dezenas de aplicações (squads) consumirem APIs da OpenAI ou Anthropic diretamente, todas as requisições passam por este Gateway, que aplica regras de negócio, resiliência e otimização financeira em tempo real.

---

## 🚀 Principais Funcionalidades (Core Features)

* 🛡️ **Circuit Breaker & Fallback:** Padrão de resiliência sênior. Se a OpenAI falhar (Ex: Timeout/503), o circuito "abre" e o tráfego é roteado instantaneamente e de forma transparente para um Fallback (ex: Gemini ou Ollama local).
* 💰 **Semantic Cache (Otimização Extrema):** Intercepta perguntas idênticas ou similares usando *Redis Vector Search*. Se ocorrer um *Cache Hit*, a resposta é devolvida em milissegundos a custo $0.00, poupando a requisição à LLM externa.
* ⚖️ **Policy Engine (Governança):** Define rotas baseadas no "Tenant" (cliente interno). Usuários do plano `Free` são roteados para IAs Open-Source (custo zero), enquanto usuários `Premium` acessam modelos caros (GPT-4).
* ⚡ **Streaming Assíncrono (SSE):** O Gateway atua como um "cano inteligente", utilizando `Server-Sent Events` para repassar tokens assim que são gerados, garantindo baixíssima latência e UX fluida (efeito máquina de escrever).
* 🚦 **Rate Limiting:** Algoritmo *Token Bucket* via script Lua no Redis para limitar requisições abusivas.

---

## 📐 Arquitetura de Software

A arquitetura foi desenhada focando em alta concorrência e Inversão de Dependência (Clean Architecture adaptada):

```mermaid
graph TD
    A[Aplicações Clientes / Streamlit] -->|POST /v1/chat| B(FastAPI Gateway)
    B --> C{Policy Engine & Auth}
    C -->|Busca Regras| D[(Redis: Cache Semântico)]
    D -->|Cache Hit| E[Retorna Resposta: $0.00]
    D -->|Cache Miss| F{Circuit Breaker}
    F -->|OpenAI Ativa| G[Provider: OpenAI]
    F -->|OpenAI Falhou| H[Provider: Gemini / Ollama]
    G --> I[Streaming SSE]
    H --> I[Streaming SSE]
    I --> J[(PostgreSQL: Métricas)]
    I --> A
🛠️ Como executar localmente
Clone o repositório e instale as dependências:
git clone https://github.com/SEU_USUARIO/enterprise_AI_gateway.git
cd enterprise_AI_gateway
python -m venv .venv
source .venv/bin/activate # ou .\.venv\Scripts\activate no Windows
pip install -r requirements.txt
Configuração de Ambiente: Copie o arquivo .env.example para .env e adicione as suas chaves (por padrão, as chaves de teste mockadas funcionarão para simulação):
cp .env.example .env
Suba a infraestrutura (Redis & Postgres):
docker-compose up -d
Inicie o Gateway e o Frontend Simulator:
# Terminal 1: Inicia o Backend FastAPI
uvicorn src.main:app --reload

# Terminal 2: Inicia o App Streamlit (UI)
streamlit run src/frontend/app.py
🧪 Teste de Estresse (Locust)
O projeto inclui um script de Load Testing simulando 100 usuários simultâneos para demonstrar o Circuit Breaker absorvendo impacto em tempo real, mantendo uma taxa de 0% de falhas (200 OK). Execute com: locust -f locustfile.py.