"""
Cliente MinIO para armazenamento de documentos
"""

from minio import Minio
from minio.error import S3Error
import os

# Configurações MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost")
MINIO_PORT = os.getenv("MINIO_PORT", "9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "documents")
MINIO_SECURE = False  # Para desenvolvimento local

# Cliente MinIO global
_minio_client = None


def get_minio_client() -> Minio:
    """Obter ou criar cliente MinIO"""
    global _minio_client
    
    if _minio_client is None:
        _minio_client = Minio(
            f"{MINIO_ENDPOINT}:{MINIO_PORT}",
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
    
    return _minio_client


def ensure_bucket_exists(client: Minio, bucket_name: str):
    """Garantir que o bucket existe, criando se necessário"""
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' criado com sucesso")
        else:
            print(f"Bucket '{bucket_name}' já existe")
    except S3Error as e:
        print(f"Erro ao criar/verificar bucket: {e}")
        raise


def upload_file(client: Minio, bucket_name: str, object_name: str, file_data: bytes, content_type: str = "application/octet-stream"):
    """Upload de arquivo para MinIO"""
    try:
        from io import BytesIO
        
        file_stream = BytesIO(file_data)
        client.put_object(
            bucket_name,
            object_name,
            file_stream,
            length=len(file_data),
            content_type=content_type
        )
        return True
    except S3Error as e:
        print(f"Erro ao fazer upload: {e}")
        raise


def download_file(client: Minio, bucket_name: str, object_name: str) -> bytes:
    """Download de arquivo do MinIO"""
    try:
        response = client.get_object(bucket_name, object_name)
        data = response.read()
        response.close()
        response.release_conn()
        return data
    except S3Error as e:
        print(f"Erro ao fazer download: {e}")
        raise

