"""
Serviço para processamento de documentos
"""

import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from minio_client import get_minio_client, upload_file
from embeddings_service import EmbeddingsService
import os

MINIO_BUCKET = os.getenv("MINIO_BUCKET", "documents")


class DocumentService:
    """Serviço para processar e armazenar documentos"""
    
    def __init__(self):
        self.minio_client = get_minio_client()
    
    async def process_document(
        self,
        filename: str,
        content: bytes,
        db: Session,
        embeddings_service: EmbeddingsService
    ) -> Dict[str, Any]:
        """
        Processar documento completo:
        1. Upload para MinIO
        2. Extrair conteúdo de texto
        3. Gerar embedding
        4. Salvar no PostgreSQL
        
        Args:
            filename: Nome do arquivo
            content: Conteúdo binário do arquivo
            db: Sessão do banco de dados
            embeddings_service: Serviço de embeddings
            
        Returns:
            Dicionário com informações do documento processado
        """
        # Gerar caminho único para o arquivo
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(filename)[1]
        file_path = f"{file_id}{file_ext}"
        
        # Upload para MinIO
        upload_file(
            self.minio_client,
            MINIO_BUCKET,
            file_path,
            content
        )
        
        # Extrair conteúdo de texto
        text_content = self._extract_text(content, filename)
        
        # Gerar embedding
        embedding = embeddings_service.generate_embedding(text_content)
        
        # Salvar no banco de dados
        from database import Document
        
        # Converter embedding numpy para formato string para PostgreSQL
        embedding_str = "[" + ",".join(map(str, embedding.tolist())) + "]"
        
        # Preparar metadados como JSON
        metadata = {
            "file_size": len(content),
            "file_type": file_ext,
        }
        metadata_json = json.dumps(metadata)

        # Inserir no banco usando SQL direto para usar tipo vector e jsonb
        insert_sql = text("""
            INSERT INTO documents (filename, file_path, content, embedding, metadata, created_at, updated_at)
            VALUES (
                :filename,
                :file_path,
                :content,
                CAST(:embedding AS vector),
                CAST(:metadata AS jsonb),
                :created_at,
                :updated_at
            )
            RETURNING id
        """)
        
        result = db.execute(
            insert_sql,
            {
                "filename": filename,
                "file_path": file_path,
                "content": text_content,
                "embedding": embedding_str,
                "metadata": metadata_json,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        )
        
        db.commit()
        
        document_id = result.fetchone()[0]
        
        return {
            "document_id": document_id,
            "filename": filename,
            "file_path": file_path,
            "content_length": len(text_content),
            "embedding_dimension": len(embedding)
        }
    
    def _extract_text(self, content: bytes, filename: str) -> str:
        """
        Extrair texto de diferentes formatos de arquivo
        
        Args:
            content: Conteúdo binário
            filename: Nome do arquivo (para determinar tipo)
            
        Returns:
            Texto extraído
        """
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext == '.txt':
            # Arquivo de texto simples
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                return content.decode('latin-1')
        
        elif file_ext == '.md':
            # Markdown
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                return content.decode('latin-1')
        
        elif file_ext == '.pdf':
            # PDF - requer biblioteca adicional
            try:
                import PyPDF2
                from io import BytesIO
                pdf_file = BytesIO(content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except ImportError:
                return "PDF requer PyPDF2. Instale com: pip install PyPDF2"
            except Exception as e:
                return f"Erro ao extrair PDF: {str(e)}"
        
        elif file_ext == '.docx':
            # DOCX - requer biblioteca adicional
            try:
                from docx import Document as DocxDocument
                from io import BytesIO
                docx_file = BytesIO(content)
                doc = DocxDocument(docx_file)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                return text
            except ImportError:
                return "DOCX requer python-docx. Instale com: pip install python-docx"
            except Exception as e:
                return f"Erro ao extrair DOCX: {str(e)}"
        
        else:
            # Tentar decodificar como texto genérico
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                return content.decode('latin-1', errors='ignore')

