🛰️ Enterprise AI Gateway (LLM Router)
Documento de Arquitetura, Visão Geral e Guia de Execução

Status: Projeto 100% Concluído (Fases 1 a 6 executadas).
Stack Principal: Python 3.11+, FastAPI, AsyncIO, Redis (Vector Search), PostgreSQL, SQLAlchemy (Async), Docker, PyMuPDF/Regex (DLP).

📑 1. O Problema Real de Produção vs. A Solução
O Problema (A Dor da Enterprise)
As grandes empresas estão sofrendo com a descentralização do consumo de IA. Cada squad consome APIs da OpenAI ou Anthropic diretamente, gerando:

Vendor Lock-in & Instabilidade: Se o provedor principal cai, o produto da empresa para.

Custos Incontroláveis: Requisições repetidas gastam tokens caríssimos toda vez. Usuários abusivos estouram o orçamento sem rastreabilidade.

Vazamento de Dados Sensíveis (PII): Funcionários anexam contratos reais ou colam CPFs e cartões de crédito em prompts, enviando dados sigilosos para provedores públicos e ferindo leis de proteção (LGPD/GDPR).

A Solução (O Gateway)
Um proxy reverso inteligente e de alta performance que centraliza todo o tráfego de LLMs. Ele gerencia resiliência de forma transparente (failover automatizado), reduz custos em tempo real via cache semântico e impõe Governança Estrita: bloqueia vazamentos de dados na origem (DLP em textos e anexos) e audita o consumo por Tenant através de um Policy Engine.

📐 2. Arquitetura de Software e Fluxo de Dados
O gateway opera de forma 100% assíncrona para garantir baixíssima latência. Abaixo está o fluxo de uma requisição trafegando pela malha de segurança e roteamento:

Snippet de código
graph TD
    A[Aplicação Cliente] -->|1. POST /v1/chat + Anexo Base64| B(FastAPI Gateway)
    B -->|2. Validar Token/Tenant| C{Auth & Policy Engine}
    C -->|Inválido| D[Retorna 401/403]
    C -->|Válido: Inicia Verificação| DLP{DLP Scanner - PII Check}
    DLP -->|Vazamento (Texto ou PDF)| ERRO[Retorna HTTP 406]
    DLP -->|Limpo + Context Injection| E[Redis Cache]
    E -->|3. Verifica Cache Semântico| F{Decisão de Roteamento}
    F -->|Hit no Cache| G[Retorna Resposta: Custo Zero]
    F -->|Miss: Roteia para Provedor| H{Circuit Breaker Status}
    H -->|Primário Ativo| I[Provider: Principal]
    H -->|Primário Caído| J[Provider Fallback: Secundário/Local]
    I -->|4. Stream SSE| B
    J -->|4. Stream SSE| B
    B -->|5. Grava Logs/Métricas| K[PostgreSQL Async / Prometheus]
    B -->|6. Retorna Stream HTTP| A
🗂️ 3. Organização de Diretórios (The Enterprise Layout)
A arquitetura de pastas segue padrões de inversão de dependência (Clean Architecture / Domain-Driven Design adaptado):

Plaintext
ai-gateway/
├── docker/
│   ├── docker-compose.yml
│   └── Dockerfile
├── docs/
│   └── architecture.md
├── src/
│   ├── main.py                 # Inicialização do FastAPI e Middlewares
│   ├── config.py               # Pydantic BaseSettings 
│   ├── auth/                   # Autenticação de Tenants e API Keys
│   ├── core/                   # Motores centrais da aplicação
│   │   ├── circuit_breaker.py  # Estado de saúde dos provedores
│   │   ├── policy_engine.py    # Motor de regras de roteamento
│   │   ├── database.py         # Conexão assíncrona PostgreSQL
│   │   └── dlp_scanner.py      # Cão de Guarda (Data Loss Prevention via Regex/PyMuPDF)
│   ├── cache/                  # Cache Semântico (Redis Vector Search)
│   ├── rate_limit/             # Limitador via Token Bucket no Redis
│   ├── providers/              # Abstração de provedores (Inversão de Dependência)
│   │   ├── base.py
│   │   ├── openai.py
│   │   └── gemini.py
│   ├── metrics/                # Observabilidade corporativa
│   │   ├── logger.py           # Configuração Structlog (JSON Logs estruturados)
│   │   └── collector.py        # Prometheus Engine (Economia, Latência, Contadores)
│   └── api/                    
│       ├── v1/chat.py          # Rota principal (Interceptação DLP, Injeção e Roteamento)
│       └── schemas.py          # Contratos Pydantic (Suporte a Documentos Base64)
├── src/frontend/
│   └── app.py                  # Simulador Visual Streamlit com File Uploader
└── requirements.txt
🗺️ 4. O Mapa de Execução (Roadmap Concluído)
Fase 1: Fundação Estrutural. Proxy Base & Async Stream pass-through (SSE).

Fase 2: Resiliência Sênior. Circuit Breaker, Exponential Backoff & Failover dinâmico.

Fase 3: Governança e BD. Proteção de Infra, Row-Level Security no Postgres e Policy Engine por Tenant.

Fase 4: Otimização Extrema. Interceptação de similaridade via Semantic Cache no Redis.

Fase 5: Observabilidade. Structlog JSON, exposição de métricas via Prometheus e simulação de estresse (Locust).

Fase 6: Governança de PII e Segurança de Anexos (DLP).

Implementação do scanner local por Regex interceptando CPFs, Cartões e Documentos.

Alteração de contratos Pydantic para aceitação de binários em base64.

Extração em RAM (PyMuPDF) e bloqueio imediato (HTTP 406) de anexos confidenciais, protegendo a camada de rede externa.

📓 5. Diário de Bordo: Instruções de Emergência (Troubleshooting)
"O Streaming assíncrono (SSE) está quebrando ou travando o servidor."
Verifique se a instância do httpx.AsyncClient() está sendo gerada corretamente por requisição ou usando um pool global. Nunca use chamadas síncronas (client.post()) dentro de uma rota async def. O padrão correto é await client.stream(...).

"O DLP Scanner está gerando erro de leitura no PDF (Crash no servidor)."
Se o FastAPI retornar erro 500 ao processar um anexo, valide o bloco do fitz.open(stream=...). Se o payload base64 for corrompido pelo front-end ou tiver caracteres invisíveis, a decodificação falha. Sempre use o bloco try/except na extração retornando um bloqueio preventivo (True para PII) caso o arquivo seja ilegível.

"O Gateway barra minha requisição no front-end antes mesmo do log aparecer no backend."
Cuidado com espaços extras no envio do header HTTP. No front-end (app.py), garanta que a Chave API passa por um .strip() na formatação do Bearer Token. O protocolo HTTP rejeita sumariamente headers com espaços residuais, simulando uma queda ("Gateway offline") quando, na verdade, o request sequer foi montado.