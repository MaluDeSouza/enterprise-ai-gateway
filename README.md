# 🛰️ Enterprise AI Gateway (LLM Router)

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)
![Redis](https://img.shields.io/badge/Redis-Vector_Search-DC382D.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Async-4169E1.svg)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-DLP_Engine-red.svg)

O **Enterprise AI Gateway** é um proxy reverso inteligente e assíncrono projetado para resolver os maiores gargalos de adoção de IA em grandes corporações: **Vazamento de Dados (PII), Vendor Lock-in e Custos Descontrolados**. 

Em vez de dezenas de aplicações consumirem APIs da OpenAI ou Anthropic diretamente, todo o tráfego passa por esta malha central, que aplica políticas de governança, resiliência e injeção de contexto em tempo real.

---

## 🚀 Principais Funcionalidades (Core Features)

* 🛡️ **DLP Scanner (Data Loss Prevention):** Interceptação ativa via Regex e extração em RAM (PyMuPDF). Impede que dados sensíveis (CPFs, Cartões, Contratos) vazem para provedores públicos, tanto no texto do prompt quanto dentro de anexos Base64.
* 🧠 **Context Injection:** Extrai textos de documentos seguros e injeta dinamicamente no prompt do usuário antes do envio, estabelecendo a fundação para arquiteturas RAG avançadas.
* 💰 **Semantic Cache:** Intercepta perguntas similares usando *Redis Vector Search*. Se ocorrer um *Cache Hit* (>80% de similaridade), a resposta é devolvida em milissegundos a custo $0.00.
* 🔄 **Circuit Breaker & Failover:** Padrão de resiliência corporativo. Se a API primária falhar, o circuito abre e roteia o tráfego de forma transparente para um modelo de Fallback.
* ⚡ **Streaming Assíncrono (SSE):** O Gateway atua como um "cano inteligente", utilizando `Server-Sent Events` para repassar tokens assim que são gerados (latência ultra-baixa).
* 📊 **Observabilidade Corporativa:** Logs estruturados em JSON e métricas de economia/latência expostas nativamente para Prometheus.

---

## 📸 Provas de Conceito (Showcase)

**1. Prevenção de Vazamento de Dados (DLP em Ação)**
O Gateway bloqueia instantaneamente requisições contendo PII, seja no texto livre ou dentro de PDFs anexados, retornando o status HTTP apropriado.
![Bloqueio de Texto Sensível](docs/img/TESTE_PII_FRONT.png)
![Bloqueio de PDF Sensível](docs/img/teste_anexo_pdf_dados_expostos.png)

**2. Injeção de Contexto (Documentos Mascarados)**
Quando um documento "limpo" (sem PII) é enviado, o Gateway extrai o conteúdo e alimenta a LLM, permitindo respostas precisas baseadas no arquivo.
![Sucesso com PDF Mascarado](docs/img/teste_anexo_pdf_mascarados_frontend.png)

**3. Telemetria e Logs Estruturados (Visão do Backend)**
Monitoramento detalhado evidenciando o motor de Similaridade Vetorial (Cache Hit/Miss) e a interceptação de segurança no nível HTTP.
![Logs de Segurança 406](docs/img/teste_PII_LOG.png)
![Logs do Cache Semântico](docs/img/metricas_terminal_uvicorn.png)
![Exportação Prometheus](docs/img/metricas.png)

---

## 📐 Arquitetura de Software

Arquitetura assíncrona focada em alta concorrência e Inversão de Dependência:


```mermaid
graph TD
    A[Aplicações Clientes / UI] -->|POST /v1/chat + Base64| B(FastAPI Gateway)
    B --> C{Auth & DLP Scanner}
    C -->|Vazamento Detectado| D[Retorna HTTP 406]
    C -->|Tráfego Limpo| E[(Redis: Cache Semântico)]
    E -->|Cache Hit| F[Retorna Resposta: $0.00]
    E -->|Cache Miss| G{Circuit Breaker}
    G -->|Provedor Ativo| H[Provider: Principal]
    G -->|Provedor Falhou| I[Provider: Fallback]
    H --> J[Streaming SSE]
    I --> J[Streaming SSE]
    J --> K[(Postgres/Prometheus: Métricas)]
    J --> A
```
🛠️ Como executar localmente
Clone o repositório e instale as dependências:

Bash
git clone [https://github.com/SEU_USUARIO/enterprise_AI_gateway.git](https://github.com/SEU_USUARIO/enterprise_AI_gateway.git)
cd enterprise_AI_gateway
python -m venv .venv
source .venv/bin/activate # ou .\.venv\Scripts\activate no Windows
pip install -r requirements.txt
Configuração de Ambiente:

Bash
cp .env.example .env
Suba a infraestrutura (Redis & Postgres) e inicie os serviços:

Bash
docker-compose up -d

# Terminal 1: Inicia o Backend FastAPI
uvicorn src.main:app --reload

# Terminal 2: Inicia o App Streamlit (Simulador UI)
streamlit run src/frontend/app.py