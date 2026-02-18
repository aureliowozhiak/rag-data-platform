"""
Serviço RAG (Retrieval Augmented Generation) usando Ollama
"""

import httpx
import os
from typing import Optional


class RAGService:
    """Serviço para geração de respostas usando RAG com Ollama"""
    
    def __init__(self, base_url: str = None, model: str = None):
        """
        Inicializar serviço RAG
        
        Args:
            base_url: URL base do Ollama (ex: http://ollama:11434)
            model: Nome do modelo a usar (ex: llama3.2)
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.client = httpx.AsyncClient(timeout=120.0)  # Timeout maior para LLM
    
    async def generate_response(
        self,
        query: str,
        context: str,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> str:
        """
        Gerar resposta usando RAG
        
        Args:
            query: Pergunta do usuário
            context: Contexto retornado pela busca semântica
            temperature: Temperatura para geração (0.0-1.0)
            max_tokens: Número máximo de tokens na resposta
            
        Returns:
            Resposta gerada pelo LLM
        """
        # Construir prompt RAG
        prompt = self._build_rag_prompt(query, context)

        payload_generate = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            # 1) Tentar endpoint clássico /api/generate
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload_generate,
            )

            # Se o servidor não conhecer /api/generate (404),
            # fazemos fallback automático para /api/chat
            if response.status_code == 404:
                payload_chat = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                }
                response = await self.client.post(
                    f"{self.base_url}/api/chat",
                    json=payload_chat,
                )

            response.raise_for_status()
            result = response.json()

            # Estrutura típica de /api/generate
            if "response" in result and isinstance(result["response"], str):
                return result["response"]

            # Estrutura típica de /api/chat
            message = result.get("message") or {}
            if isinstance(message, dict) and isinstance(
                message.get("content"), str
            ):
                return message["content"]

            # Fallback simples
            return str(result)
        
        except httpx.HTTPError as e:
            raise Exception(f"Erro ao chamar Ollama: {e}")
        except Exception as e:
            raise Exception(f"Erro ao gerar resposta: {e}")
    
    def _build_rag_prompt(self, query: str, context: str) -> str:
        """
        Construir prompt RAG com contexto
        
        Args:
            query: Pergunta do usuário
            context: Contexto dos documentos
            
        Returns:
            Prompt formatado
        """
        prompt = f"""Você é um assistente útil que responde perguntas baseado no contexto fornecido.

CONTEXTO:
{context}

PERGUNTA: {query}

INSTRUÇÕES:
- Responda a pergunta usando APENAS as informações do contexto fornecido
- Se a resposta não estiver no contexto, diga que não tem informações suficientes
- Seja preciso e conciso
- Cite os documentos relevantes quando apropriado

RESPOSTA:"""
        
        return prompt
    
    async def check_model_available(self) -> bool:
        """Verificar se o modelo está disponível no Ollama"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            return self.model in model_names
        except Exception:
            return False
    
    async def pull_model(self):
        """Baixar modelo do Ollama se não estiver disponível"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model},
                timeout=300.0  # Timeout maior para download
            )
            return response.json()
        except Exception as e:
            raise Exception(f"Erro ao baixar modelo: {e}")

