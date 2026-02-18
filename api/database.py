"""
Configuração do banco de dados PostgreSQL com SQLAlchemy
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Configurações do banco
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "raguser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ragpass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "ragdb")

# URL de conexão
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Criar engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Criar session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()


# Modelo de Documento
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    content = Column(Text)
    # Mapeamos embedding como TEXT apenas para leitura (o tipo real no Postgres é vector)
    # Isso evita problemas de adaptação de tipos com BYTEA e a extensão pgvector.
    embedding = Column(Text)
    # 'metadata' é um nome reservado na API declarativa do SQLAlchemy (Base.metadata)
    # Por isso, usamos o nome de atributo 'extra_metadata', mas mantemos o nome da coluna como 'metadata'
    extra_metadata = Column("metadata", JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_db():
    """Dependency para obter sessão do banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializar banco de dados (criar tabelas se não existirem)"""
    # As tabelas são criadas pelo init.sql do PostgreSQL
    # Esta função pode ser usada para verificações adicionais
    try:
        Base.metadata.create_all(bind=engine)
        print("Banco de dados inicializado com sucesso")
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")

