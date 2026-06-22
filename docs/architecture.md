🛰️ Enterprise AI Gateway (LLM Router)
Documento de Arquitetura, Visão Geral e Guia de Execução
Status: Planejamento e Arquitetura Base completados.
Stack Principal: Python 3.11+, FastAPI, AsyncIO, Redis (Vector Search), PostgreSQL, SQLAlchemy (Async), Docker.

📑 1. O Problema Real de Produção vs. A Solução
O Problema (A Dor da Enterprise)
As grandes empresas estão sofrendo com a descentralização do consumo de IA. Cada squad consome APIs da OpenAI/Anthropic direto, gerando:

Vendor Lock-in & Instabilidade: Se a OpenAI cai, o produto da empresa para.

Custos Incontroláveis: Requisições repetidas ("Qual o CNPJ da empresa?") gastam tokens caríssimos toda vez. Usuários abusivos estouram o orçamento.

Falta de Governança: O Board de Segurança não sabe quais dados estão sendo enviados para fora e quanto cada cliente interno está gastando.

A Solução (O Gateway)
Um proxy reverso inteligente de alta performance que centraliza todo o tráfego de LLMs. As aplicações da empresa só conversam com o Enterprise AI Gateway. Ele gerencia resiliência (se um cai, outro assume), reduz custos em tempo real (cache semântico e roteamento inteligente por complexidade) e impõe limites estritos de segurança e orçamento por Tenant/Usuário através de um Policy Engine.

📐 2. Arquitetura de Software e Fluxo de Dados
O gateway opera de forma assíncrona para garantir baixa latência. Abaixo está o fluxo de uma requisição trafegando pelo sistema:

Snippet de código
graph TD
    A[Aplicação Cliente] -->|1. Requisição POST /v1/chat| B(FastAPI Gateway)
    B -->|2. Validar Token/Tenant| C{Auth & Policy Engine}
    C -->|Inválido| D[Retorna 401/403]
    C -->|Válido: Busca Regras| E[Redis Cache]
    E -->|3. Verifica Rate Limit & Cache Semântico| F{Decisão de Roteamento}
    F -->|Hit no Cache| G[Retorna Resposta do Redis]
    F -->|Miss: Roteia para Provedor| H{Circuit Breaker Status}
    H -->|OpenAI Ativa| I[Provider: OpenAI]
    H -->|OpenAI Caída| J[Provider Fallback: Gemini/Ollama]
    I -->|4. Stream SSE| B
    J -->|4. Stream SSE| B
    B -->|5. Grava Métricas/Custos| K[PostgreSQL Async / Prometheus]
    B -->|6. Retorna Stream HTTP| A
🗂️ 3. Organização de Diretórios (The Enterprise Layout)
Esta estrutura segue rigorosamente os padrões de inversão de dependência e separação de conceitos (Clean Architecture / Domain-Driven Design adaptado):

Plaintext
ai-gateway/
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── prometheus.yml
├── docs/
│   └── architecture.md
├── src/
│   ├── __init__.py
│   ├── main.py                 # Inicialização do FastAPI e Middlewares
│   ├── config.py               # Pydantic BaseSettings (Variaveis de ambiente)
│   │
│   ├── auth/                   # Autenticação de Tenants e API Keys
│   │   ├── dependencies.py
│   │   └── models.py
│   │
│   ├── core/                   # Padrões de resiliência e motores centrais
│   │   ├── circuit_breaker.py  # Estado de saúde dos provedores
│   │   ├── policy_engine.py    # Motor de regras de roteamento
│   │   └── database.py         # Conexão assíncrona PostgreSQL/SQLAlchemy
│   │
│   ├── cache/                  # Cache Semântico (Redis Vector Search)
│   │   ├── manager.py
│   │   └── embeddings.py
│   │
│   ├── rate_limit/             # Limitador por tokens/requisições (Redis Token Bucket)
│   │   └── limiter.py
│   │
│   ├── providers/              # Abstração de provedores (Inversão de Dependência)
│   │   ├── base.py             # Classe abstrata BaseProvider
│   │   ├── openai.py
│   │   ├── gemini.py
│   │   └── ollama.py
│   │
│   ├── metrics/                # Prometheus Engine & Logs Estruturados
│   │   ├── logger.py           # Configuração Structlog
│   │   └── collector.py
│   │
│   └── api/                    # Rotas e Schemas de entrada/saída
│       ├── v1/
│       │   ├── chat.py         # Rota principal de roteamento de Chat
│       │   └── tenants.py      # Gerenciamento de clientes
│       └── schemas.py          # Validação estrita Pydantic V2
│
├── tests/
│   ├── conftest.py
│   ├── test_gateway.py
│   └── test_rate_limit.py
├── requirements.txt
└── README.md
🗺️ 4. O Mapa de Execução Semanal (As Ondas do MVP)
Aqui está a sua linha do tempo. Risque cada etapa concluída. Não avance para a próxima fase sem testar a anterior.

Fase 1: Fundação Estrutural, Proxy Base & Async Stream (Dias 1 a 3)
[ ] Setup do Ambiente: Criar a estrutura de pastas, configurar o Dockerfile e o docker-compose.yml inicial (FastAPI + Redis + PostgreSQL).

[ ] Camada de Provedores Absoluta: Criar providers/base.py definindo o protocolo assíncrono padrão (async def generate_stream(...)). Implementar os wrappers da OpenAI e do Ollama herdando dessa base usando httpx.AsyncClient.

[ ] O Core do Proxy: Criar a rota POST /v1/chat/completions recebendo um payload idêntico ao da OpenAI (padrão de mercado). Garantir que o FastAPI faça o stream pass-through usando StreamingResponse via Server-Sent Events (SSE).

Fase 2: Resiliência Sênior - Circuit Breaker & Fallback (Dias 4 a 6)
[ ] Mecanismo de Retry: Implementar política de retentativas assíncronas com exponential backoff (ex: falhou a primeira tentativa, tenta de novo em 1s, depois 2s).

[ ] Circuit Breaker State Machine: Criar uma classe na pasta core/ que monitora falhas de requisições por provedor. Se a OpenAI retornar erro 3 vezes seguidas, o circuito muda para OPEN por 60 segundos.

[ ] Roteador Dinâmico (Failover): Modificar a rota principal para que, se o circuito da OpenAI estiver aberto, o gateway intercepte a requisição em tempo de execução e a direcione transparentemente para o Ollama local ou Gemini.

Fase 3: Governança, Proteção de Infra e Policy Engine (Dias 7 a 9)
[ ] Row-Level Security (RLS) no Postgres: Modelar as tabelas de Tenants e UsageLogs. Configurar o banco para isolar os dados usando RLS nativo, garantindo auditoria segura de consumo.

[ ] Token Rate Limiting com Redis: Escrever o script Lua para Redis que executa o algoritmo Token Bucket. O gateway deve deduzir os tokens consumidos (estimados no input e validados no output do stream) do saldo em tempo real do Tenant.

[ ] O Policy Engine: Criar as regras de decisão. Se o payload contiver um prompt simples ou o Tenant for da camada "Free", direcionar para o modelo local (Ollama/Gemma). Se for "Premium", rotear para modelos sêniores.

Fase 4: Otimização Extrema - Cache Semântico (Dias 10 a 12)
[ ] Integração Vector Search: Configurar o módulo de busca vetorial do Redis.

[ ] Pipeline de Embeddings: Criar um microsserviço interno ou helper que gera embeddings rápidos das perguntas recebidas.

[ ] Mecanismo de Hit/Miss: Antes de bater nos provedores, fazer uma busca por similaridade de cosseno no Redis. Se a similaridade for maior que 92%, interceptar o fluxo e cuspir a resposta salva diretamente do cache, gerando custo zero.

Fase 5: Observabilidade e O Visual do Portfólio (Dias 13 a 14)
[ ] Logs Estruturados: Substituir os prints nativos por structlog em JSON para simular um ambiente de produção que joga logs para o Datadog/ElasticSearch.

[ ] Prometheus Metrics: Expor latência por provedor, contagem de erros 5xx e contadores de economia financeira.

[ ] O Showroom do GitHub: Escrever o README monumental, adicionar diagramas de arquitetura em Mermaid e criar um script com o Locust para simular um teste de estresse de 100 requisições simultâneas forçando o Circuit Breaker a agir em tempo real.

📓 5. Diário de Bordo: Instruções de Emergência (Leia quando estiver travada)
"Estou perdida no código, o que eu faço agora?"

Pare. Abra o arquivo src/api/v1/chat.py. Ele é o coração do projeto.

Identifique qual middleware ou serviço falhou: foi na validação de entrada (Pydantic), no controle de fluxo (Redis/Rate limit) ou no consumo externo (Providers)?

Lembre-se: O Gateway é apenas um cano inteligente. O dado entra, é avaliado, é modificado e é repassado.

"O Streaming assíncrono (SSE) está quebrando ou travando o servidor."

Verifique se você está instanciando o httpx.AsyncClient() corretamente por requisição ou usando um pool global (preferível). Nunca use client.post() síncrono dentro de uma rota async def. Use await client.stream(...).

"Como testar o Circuit Breaker sem derrubar minha internet?"

No seu provedor mock ou nas variáveis de ambiente, mude a URL da OpenAI para um endereço inválido ([https://api.openai.invalid](https://api.openai.invalid)). Force o erro de DNS e observe se o seu código captura a exceção, abre o circuito e joga a requisição para o bloco do Ollama de forma automática.