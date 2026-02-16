"""
Serviço de geração de embeddings usando sentence-transformers
"""

from sentence_transformers import SentenceTransformer
import numpy as np
import os

# Modelo padrão: all-MiniLM-L6-v2 (384 dimensões, rápido e eficiente)
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingsService:
    """Serviço para gerar embeddings de texto"""
    
    def __init__(self, model_name: str = None):
        """
        Inicializar serviço de embeddings
        
        Args:
            model_name: Nome do modelo sentence-transformers a usar
        """
        self.model_name = model_name or os.getenv("EMBEDDINGS_MODEL", DEFAULT_MODEL)
        print(f"Carregando modelo de embeddings: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print(f"Modelo carregado. Dimensão dos embeddings: {self.model.get_sentence_embedding_dimension()}")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Gerar embedding para um texto
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Array numpy com o embedding
        """
        if not text or not text.strip():
            raise ValueError("Texto não pode ser vazio")
        
        # Gerar embedding
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
    
    def generate_embeddings_batch(self, texts: list) -> np.ndarray:
        """
        Gerar embeddings para múltiplos textos (mais eficiente)
        
        Args:
            texts: Lista de textos
            
        Returns:
            Array numpy com embeddings (shape: [len(texts), embedding_dim])
        """
        if not texts:
            return np.array([])
        
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Retornar dimensão dos embeddings"""
        return self.model.get_sentence_embedding_dimension()

