#!/bin/bash
# Script para configurar modelo Ollama

echo "Configurando Ollama..."

# Aguardar Ollama estar pronto
echo "Aguardando Ollama estar disponível..."
until curl -f http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "Aguardando..."
    sleep 2
done

echo "Ollama está pronto!"

# Baixar modelo se não existir
MODEL=${OLLAMA_MODEL:-llama3.2}
echo "Verificando modelo: $MODEL"

if ! docker exec rag-ollama ollama list | grep -q "$MODEL"; then
    echo "Baixando modelo $MODEL..."
    docker exec rag-ollama ollama pull $MODEL
else
    echo "Modelo $MODEL já está disponível"
fi

echo "Configuração concluída!"

