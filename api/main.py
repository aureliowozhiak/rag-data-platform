"""
FastAPI - API principal para RAG Data Platform
Fornece endpoints para upload, busca semântica e RAG
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from contextlib import asynccontextmanager

from database import get_db, init_db
from minio_client import get_minio_client, ensure_bucket_exists
from embeddings_service import EmbeddingsService
from rag_service import RAGService
from document_service import DocumentService

# Configurações
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "documents")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialização e limpeza da aplicação"""
    # Inicializar banco de dados
    init_db()
    
    # Garantir que o bucket MinIO existe
    minio_client = get_minio_client()
    ensure_bucket_exists(minio_client, MINIO_BUCKET)
    
    # Inicializar serviços
    app.state.embeddings_service = EmbeddingsService()
    app.state.rag_service = RAGService(OLLAMA_BASE_URL, OLLAMA_MODEL)
    app.state.document_service = DocumentService()
    
    yield
    
    # Cleanup (se necessário)
    pass


# Criar aplicação FastAPI
app = FastAPI(
    title="RAG Data Platform API",
    description="API para upload, busca semântica e RAG com documentos",
    version="1.0.0",
    lifespan=lifespan
)


# Modelos Pydantic
class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    threshold: float = 0.7


class SearchResult(BaseModel):
    id: int
    filename: str
    content: str
    similarity: float
    metadata: Optional[dict] = None


class RAGRequest(BaseModel):
    query: str
    limit: int = 3
    temperature: float = 0.7


class RAGResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    query: str


# Endpoints
@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "RAG Data Platform API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload",
            "search": "/search",
            "rag": "/rag",
            "documents": "/documents",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    db = next(get_db())
    try:
        # Verificar conexão com banco
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    finally:
        db.close()
    
    return {
        "status": "ok",
        "database": db_status,
        "services": {
            "embeddings": "ready",
            "rag": "ready"
        }
    }


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db = Depends(get_db)
):
    """
    Upload de documento
    - Salva o arquivo no MinIO
    - Extrai o conteúdo
    - Gera embeddings
    - Indexa no PostgreSQL com pgvector
    """
    try:
        # Validar tipo de arquivo
        allowed_extensions = {'.txt', '.pdf', '.md', '.docx'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de arquivo não suportado. Permitidos: {allowed_extensions}"
            )
        
        # Ler conteúdo do arquivo
        content = await file.read()
        
        # Processar documento através do serviço
        document_service = app.state.document_service
        result = await document_service.process_document(
            filename=file.filename,
            content=content,
            db=db,
            embeddings_service=app.state.embeddings_service
        )
        
        return JSONResponse(
            status_code=201,
            content={
                "message": "Documento processado com sucesso",
                "document_id": result["document_id"],
                "filename": result["filename"],
                "file_path": result["file_path"],
                "content_length": result["content_length"]
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=List[SearchResult])
async def semantic_search(
    request: SearchRequest,
    db = Depends(get_db)
):
    """
    Busca semântica usando embeddings
    - Gera embedding da query
    - Busca documentos similares no PostgreSQL usando pgvector
    - Retorna resultados ordenados por similaridade
    """
    try:
        embeddings_service = app.state.embeddings_service
        
        # Gerar embedding da query
        query_embedding = embeddings_service.generate_embedding(request.query)
        
        # Buscar documentos similares
        from database import Document
        from sqlalchemy import text
        
        # Query de busca vetorial usando cosine similarity
        query_sql = text("""
            SELECT 
                id,
                filename,
                content,
                metadata,
                1 - (embedding <=> :query_embedding::vector) as similarity
            FROM documents
            WHERE embedding IS NOT NULL
            AND 1 - (embedding <=> :query_embedding::vector) >= :threshold
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :limit
        """)
        
        result = db.execute(
            query_sql,
            {
                "query_embedding": str(query_embedding.tolist()),
                "threshold": request.threshold,
                "limit": request.limit
            }
        )
        
        results = []
        for row in result:
            results.append(SearchResult(
                id=row.id,
                filename=row.filename,
                content=row.content[:500] + "..." if len(row.content) > 500 else row.content,
                similarity=float(row.similarity),
                metadata=row.metadata if row.metadata else {}
            ))
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rag", response_model=RAGResponse)
async def rag_query(
    request: RAGRequest,
    db = Depends(get_db)
):
    """
    RAG (Retrieval Augmented Generation)
    - Busca documentos relevantes usando busca semântica
    - Constrói contexto com os documentos encontrados
    - Envia query + contexto para Ollama
    - Retorna resposta gerada com fontes
    """
    try:
        embeddings_service = app.state.embeddings_service
        rag_service = app.state.rag_service
        
        # Gerar embedding da query
        query_embedding = embeddings_service.generate_embedding(request.query)
        
        # Buscar documentos relevantes
        from database import Document
        from sqlalchemy import text
        
        query_sql = text("""
            SELECT 
                id,
                filename,
                content,
                metadata,
                1 - (embedding <=> :query_embedding::vector) as similarity
            FROM documents
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :limit
        """)
        
        result = db.execute(
            query_sql,
            {
                "query_embedding": str(query_embedding.tolist()),
                "limit": request.limit
            }
        )
        
        # Preparar contexto
        sources = []
        context_parts = []
        
        for row in result:
            sources.append(SearchResult(
                id=row.id,
                filename=row.filename,
                content=row.content[:500] + "..." if len(row.content) > 500 else row.content,
                similarity=float(row.similarity),
                metadata=row.metadata if row.metadata else {}
            ))
            context_parts.append(f"Documento: {row.filename}\nConteúdo: {row.content}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Gerar resposta usando RAG
        answer = await rag_service.generate_response(
            query=request.query,
            context=context,
            temperature=request.temperature
        )
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            query=request.query
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 10,
    db = Depends(get_db)
):
    """Listar documentos indexados"""
    try:
        from database import Document
        
        documents = db.query(Document).offset(skip).limit(limit).all()
        total = db.query(Document).count()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_path": doc.file_path,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "has_embedding": doc.embedding is not None
                }
                for doc in documents
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db = Depends(get_db)
):
    """Deletar documento"""
    try:
        from database import Document
        from minio_client import get_minio_client, MINIO_BUCKET
        
        # Buscar documento
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        
        # Deletar do MinIO
        from minio_client import get_minio_client
        minio_client = get_minio_client()
        try:
            minio_client.remove_object(MINIO_BUCKET, doc.file_path)
        except Exception as e:
            print(f"Erro ao deletar do MinIO: {e}")
        
        # Deletar do banco
        db.delete(doc)
        db.commit()
        
        return {"message": "Documento deletado com sucesso"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

