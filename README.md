# RAG Data Platform

Plataforma completa de dados para RAG (Retrieval Augmented Generation), totalmente containerizada com Docker Compose. Este projeto demonstra uma arquitetura completa de ingestão, indexação vetorial, busca semântica e geração de respostas usando LLMs locais.

## 📋 Índice

- [Arquitetura](#arquitetura)
- [O que é RAG?](#o-que-é-rag)
- [O que são Embeddings?](#o-que-são-embeddings)
- [Stack Tecnológica](#stack-tecnológica)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar](#como-executar)
- [Testando a API](#testando-a-api)
- [Exemplos de Uso](#exemplos-de-uso)
- [Escalabilidade](#escalabilidade)

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAG Data Platform                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Cliente    │──────│  FastAPI     │──────│  PostgreSQL  │
│   (curl/UI)  │      │   (API)      │      │  + pgvector  │
└──────────────┘      └──────┬───────┘      └──────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
            ┌───────▼──────┐  ┌───────▼──────┐
            │    MinIO     │  │    Ollama    │
            │ (Storage)    │  │    (LLM)     │
            └──────────────┘  └──────────────┘
                    │
            ┌───────▼──────┐
            │  Ingestão    │
            │  Service     │
            └──────────────┘

Fluxo de Dados:
1. Upload → MinIO (armazenamento)
2. Extração → Texto do documento
3. Embedding → Vector (384 dim)
4. Indexação → PostgreSQL + pgvector
5. Busca → Similaridade vetorial
6. RAG → Contexto + LLM → Resposta
```

### Componentes

- **FastAPI**: API REST para upload, busca e RAG
- **PostgreSQL + pgvector**: Banco de dados vetorial para busca semântica
- **MinIO**: Armazenamento de objetos (S3-compatible) para documentos
- **Ollama**: LLM local para geração de respostas
- **Serviço de Ingestão**: Monitora diretório e processa arquivos automaticamente
- **Embeddings Service**: Gera embeddings usando sentence-transformers

## 🤖 O que é RAG?

**RAG (Retrieval Augmented Generation)** é uma técnica que combina busca de informações com geração de texto usando LLMs.

### Como Funciona:

1. **Retrieval (Busca)**: Quando o usuário faz uma pergunta, o sistema busca documentos relevantes usando busca semântica (similaridade de embeddings)
2. **Augmentation (Aumento)**: Os documentos encontrados são usados como contexto
3. **Generation (Geração)**: O LLM recebe a pergunta + contexto e gera uma resposta baseada nas informações encontradas

### Vantagens:

- ✅ Respostas baseadas em documentos específicos (não apenas conhecimento do modelo)
- ✅ Reduz alucinações (o modelo tem contexto real)
- ✅ Permite atualizar conhecimento sem retreinar o modelo
- ✅ Rastreabilidade (sabe de onde veio a informação)

## 🔢 O que são Embeddings?

**Embeddings** são representações numéricas (vetores) de texto que capturam significado semântico.

### Características:

- Textos similares em significado têm embeddings próximos no espaço vetorial
- Permitem busca por significado, não apenas palavras-chave
- Dimensão típica: 384, 768, 1536 (dependendo do modelo)

### Exemplo:

```
"O que é machine learning?" → [0.23, -0.45, 0.67, ...] (384 números)
"O que é aprendizado de máquina?" → [0.25, -0.43, 0.65, ...] (muito similar!)
"Qual é a receita do bolo?" → [0.12, 0.89, -0.34, ...] (muito diferente!)
```

### Busca Vetorial:

Usando **similaridade de cosseno**, encontramos documentos com embeddings mais próximos à query:

```
similaridade = cos(θ) = (A · B) / (||A|| × ||B||)
```

## 🛠️ Stack Tecnológica

| Componente | Tecnologia | Versão | Propósito |
|------------|-----------|--------|-----------|
| API | FastAPI | 0.104+ | API REST assíncrona |
| Banco | PostgreSQL | 16 | Banco relacional |
| Vetores | pgvector | latest | Extensão para busca vetorial |
| Storage | MinIO | latest | Armazenamento S3-compatible |
| LLM | Ollama | latest | LLM local (Llama, Mistral, etc) |
| Embeddings | sentence-transformers | 2.2+ | Modelo all-MiniLM-L6-v2 |
| Ingestão | Python + watchdog | 3.11 | Monitoramento de arquivos |

## 📁 Estrutura do Projeto

```
rag-data-platform/
├── api/                      # Serviço FastAPI
│   ├── main.py              # Endpoints principais
│   ├── database.py          # Configuração PostgreSQL
│   ├── minio_client.py      # Cliente MinIO
│   ├── embeddings_service.py # Geração de embeddings
│   ├── rag_service.py       # Serviço RAG com Ollama
│   ├── document_service.py  # Processamento de documentos
│   ├── requirements.txt     # Dependências Python
│   └── Dockerfile           # Container da API
│
├── ingestion/               # Serviço de ingestão
│   ├── ingestion_service.py # Monitor de arquivos
│   ├── requirements.txt     # Dependências
│   └── Dockerfile           # Container de ingestão
│
├── embeddings/              # Módulo de embeddings (referência)
│   └── __init__.py
│
├── docker/                  # Configurações Docker
│   └── postgres/
│       └── init.sql         # Script de inicialização DB
│
├── data/                    # Diretório para documentos
│   └── .gitkeep
│
├── docker-compose.yml       # Orquestração de serviços
├── .gitignore              # Arquivos ignorados
└── README.md               # Este arquivo
```

## 🚀 Como Executar

### Pré-requisitos

- Docker Desktop (ou Docker + Docker Compose)
- 8GB+ RAM recomendado (para Ollama)
- Portas disponíveis: 8000, 5432, 9000, 9001, 11434

### Passo 1: Clonar/Baixar o Projeto

```bash
cd rag-data-platform
```

### Passo 2: Iniciar os Serviços

```bash
docker compose up -d
```

Este comando irá:
- ✅ Baixar todas as imagens necessárias
- ✅ Criar volumes persistentes
- ✅ Inicializar PostgreSQL com pgvector
- ✅ Configurar MinIO
- ✅ Iniciar Ollama
- ✅ Subir API FastAPI
- ✅ Iniciar serviço de ingestão

### Passo 3: Aguardar Inicialização

Aguarde alguns minutos para:
- PostgreSQL inicializar
- Ollama baixar o modelo (na primeira execução)
- API carregar o modelo de embeddings

### Passo 4: Verificar Saúde dos Serviços

```bash
# Health check da API
curl http://localhost:8000/health

# Verificar logs
docker compose logs -f api
```

### Passo 5: Baixar Modelo Ollama (se necessário)

Na primeira execução, você pode precisar baixar o modelo:

```bash
docker exec -it rag-ollama ollama pull llama3.2
```

Ou use outro modelo: `mistral`, `llama2`, `codellama`, etc.

## 🧪 Testando a API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Resposta esperada:**
```json
{
  "status": "ok",
  "database": "healthy",
  "services": {
    "embeddings": "ready",
    "rag": "ready"
  }
}
```

### 2. Upload de Documento

```bash
# Criar arquivo de teste
echo "Machine Learning é uma área da inteligência artificial que permite aos computadores aprenderem com dados sem serem explicitamente programados. Existem três tipos principais: aprendizado supervisionado, não supervisionado e por reforço." > documento.txt

# Upload
curl -X POST "http://localhost:8000/upload" \
  -F "file=@documento.txt"
```

**Resposta esperada:**
```json
{
  "message": "Documento processado com sucesso",
  "document_id": 1,
  "filename": "documento.txt",
  "file_path": "uuid-xxxxx.txt",
  "content_length": 245
}
```

### 3. Busca Semântica

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "O que é aprendizado de máquina?",
    "limit": 5,
    "threshold": 0.7
  }'
```

**Resposta esperada:**
```json
[
  {
    "id": 1,
    "filename": "documento.txt",
    "content": "Machine Learning é uma área...",
    "similarity": 0.92,
    "metadata": {
      "file_size": 245,
      "file_type": ".txt"
    }
  }
]
```

### 4. RAG (Pergunta com Resposta Gerada)

```bash
curl -X POST "http://localhost:8000/rag" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quais são os tipos de machine learning?",
    "limit": 3,
    "temperature": 0.7
  }'
```

**Resposta esperada:**
```json
{
  "answer": "Baseado no contexto fornecido, existem três tipos principais de machine learning: aprendizado supervisionado, não supervisionado e por reforço...",
  "sources": [
    {
      "id": 1,
      "filename": "documento.txt",
      "content": "Machine Learning é uma área...",
      "similarity": 0.95
    }
  ],
  "query": "Quais são os tipos de machine learning?"
}
```

### 5. Listar Documentos

```bash
curl http://localhost:8000/documents
```

## 📚 Exemplos de Uso

### Exemplo Completo: Pipeline RAG

```bash
# 1. Criar múltiplos documentos
cat > doc1.txt << EOF
Python é uma linguagem de programação de alto nível, interpretada e de propósito geral.
Foi criada por Guido van Rossum e lançada em 1991.
Python é conhecida por sua sintaxe simples e legibilidade.
EOF

cat > doc2.txt << EOF
FastAPI é um framework web moderno e rápido para Python.
É baseado em type hints e suporta async/await nativamente.
FastAPI é uma das frameworks mais rápidas disponíveis.
EOF

# 2. Upload dos documentos
curl -X POST "http://localhost:8000/upload" -F "file=@doc1.txt"
curl -X POST "http://localhost:8000/upload" -F "file=@doc2.txt"

# 3. Buscar informações sobre Python
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Quem criou Python?", "limit": 3}'

# 4. Fazer pergunta usando RAG
curl -X POST "http://localhost:8000/rag" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Me explique o que é FastAPI e suas características principais",
    "limit": 2
  }'
```

### Usando o Serviço de Ingestão

O serviço de ingestão monitora o diretório `/data` (mapeado para `./data` localmente):

```bash
# Copiar arquivo para o diretório monitorado
cp documento.txt ./data/

# O serviço detectará automaticamente e processará o arquivo
# Ver logs:
docker compose logs -f ingestion
```

### Acessar Interfaces Web

- **FastAPI Docs**: http://localhost:8000/docs (Swagger UI)
- **MinIO Console**: http://localhost:9001 (usuário: minioadmin, senha: minioadmin)

## 📈 Escalabilidade

### Horizontal Scaling

#### 1. API FastAPI

```yaml
# docker-compose.yml
api:
  deploy:
    replicas: 3
  # Adicionar load balancer (nginx/traefik)
```

#### 2. PostgreSQL

- **Read Replicas**: Para distribuir leituras
- **Connection Pooling**: PgBouncer ou pgpool
- **Sharding**: Particionar por tenant/categoria

#### 3. MinIO

- **Distributed Mode**: Múltiplos nós para alta disponibilidade
- **CDN**: CloudFront/Cloudflare para distribuição

#### 4. Ollama

- **Multiple Instances**: Balancear requisições
- **GPU Clustering**: Para modelos maiores
- **Caching**: Redis para respostas frequentes

### Otimizações

#### 1. Embeddings

```python
# Usar modelos mais eficientes
- all-MiniLM-L6-v2 (384 dim) - atual
- all-mpnet-base-v2 (768 dim) - melhor qualidade
- BGE-large (1024 dim) - máxima qualidade
```

#### 2. Busca Vetorial

```sql
-- Ajustar parâmetros HNSW
CREATE INDEX documents_embedding_idx ON documents 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

#### 3. Cache

- **Redis**: Cache de embeddings e respostas RAG
- **CDN**: Para documentos estáticos

#### 4. Processamento Assíncrono

- **Celery/RQ**: Processar embeddings em background
- **Kafka/RabbitMQ**: Fila de ingestão

### Arquitetura Escalada

```
                    ┌─────────────┐
                    │ Load Balancer│
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │ API 1   │       │ API 2   │       │ API 3   │
   └────┬────┘       └────┬────┘       └────┬────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │  PG     │       │  PG     │       │  PG     │
   │ Master  │◄──────│ Replica │       │ Replica │
   └─────────┘       └─────────┘       └─────────┘
```

## 🔧 Configurações Avançadas

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz:

```env
# PostgreSQL
POSTGRES_USER=raguser
POSTGRES_PASSWORD=ragpass
POSTGRES_DB=ragdb

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_BUCKET=documents

# Ollama
OLLAMA_MODEL=llama3.2

# Embeddings
EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Modelos Ollama Disponíveis

```bash
# Listar modelos
docker exec rag-ollama ollama list

# Baixar outros modelos
docker exec rag-ollama ollama pull mistral
docker exec rag-ollama ollama pull codellama
docker exec rag-ollama ollama pull llama2
```

## 🐛 Troubleshooting

### Problema: Ollama não responde

```bash
# Verificar se o modelo está disponível
docker exec rag-ollama ollama list

# Baixar modelo
docker exec rag-ollama ollama pull llama3.2

# Ver logs
docker compose logs ollama
```

### Problema: Erro de conexão com PostgreSQL

```bash
# Verificar se o banco está rodando
docker compose ps postgres

# Ver logs
docker compose logs postgres

# Conectar manualmente
docker exec -it rag-postgres psql -U raguser -d ragdb
```

### Problema: MinIO não acessível

```bash
# Verificar bucket
docker exec rag-minio mc ls minio/

# Criar bucket manualmente
docker exec rag-minio mc mb minio/documents
```

## 📝 Licença

Este projeto é um exemplo educacional. Sinta-se livre para usar e modificar.

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se livre para abrir issues e pull requests.

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no repositório.

---

**Desenvolvido com ❤️ para demonstrar arquitetura RAG completa e containerizada**
