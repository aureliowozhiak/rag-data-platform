#!/bin/bash
# Script de teste da API

API_URL=${API_URL:-http://localhost:8000}

echo "=== Testando RAG Data Platform API ==="
echo ""

# 1. Health Check
echo "1. Health Check..."
curl -s "$API_URL/health" | jq .
echo ""

# 2. Criar documento de teste
echo "2. Criando documento de teste..."
cat > /tmp/test_doc.txt << EOF
Inteligência Artificial (IA) é a capacidade de máquinas simularem inteligência humana.
Machine Learning é um subcampo da IA que permite sistemas aprenderem com dados.
Deep Learning usa redes neurais com múltiplas camadas para aprender representações complexas.
EOF

# 3. Upload
echo "3. Fazendo upload..."
UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/upload" -F "file=@/tmp/test_doc.txt")
echo "$UPLOAD_RESPONSE" | jq .
DOC_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.document_id')
echo "Document ID: $DOC_ID"
echo ""

# 4. Busca Semântica
echo "4. Busca Semântica..."
curl -s -X POST "$API_URL/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "O que é machine learning?",
    "limit": 3,
    "threshold": 0.7
  }' | jq .
echo ""

# 5. RAG
echo "5. Testando RAG..."
curl -s -X POST "$API_URL/rag" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explique o que é deep learning",
    "limit": 2,
    "temperature": 0.7
  }' | jq .
echo ""

# 6. Listar documentos
echo "6. Listando documentos..."
curl -s "$API_URL/documents" | jq .
echo ""

echo "=== Testes concluídos ==="

