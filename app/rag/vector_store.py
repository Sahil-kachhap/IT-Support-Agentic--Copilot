import os
import time
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import JinaEmbeddings
from app.core.config import get_settings
from dotenv import load_dotenv
load_dotenv()

settings = get_settings()

_vectorstore = None

def get_embeddings():
    jina_key = os.getenv("JINA_API_KEY")
    embedding_model = JinaEmbeddings(model_name="jina-embeddings-v2-base-en", jina_api_key=jina_key)
    return embedding_model

def ensure_index():
    if not settings.pinecone_api_key:
        raise RuntimeError("PINECONE_API_KEY is missing")
    
    embedding_dimension = 768
    pinecone_client = Pinecone(api_key=settings.pinecone_api_key)
    names = [x["name"] for x in pinecone_client.list_indexes()]

    if settings.pinecone_index_name in names:
        index_info = pinecone_client.describe_index(settings.pinecone_index_name)
        current_dimesnion = getattr(index_info, "dimension", None)
        if current_dimesnion is None and isinstance(index_info, dict):
            current_dimesnion = index_info.get("dimension")

        if current_dimesnion is not None and current_dimesnion != embedding_dimension:
            pinecone_client.delete_index(name = settings.pinecone_index_name)
            while settings.pinecone_index_name in [x["name"] for x in pinecone_client.list_indexes()]:
                time.sleep(1)
    
    if settings.pinecone_index_name not in [x["name"] for x in pinecone_client.list_indexes()]:
        pinecone_client.create_index(
            name=settings.pinecone_index_name,
            dimension=embedding_dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        while not pinecone_client.describe_index(settings.pinecone_index_name).status["ready"]:
            time.sleep(1)
    
    return pinecone_client.Index(settings.pinecone_index_name)

def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        index = ensure_index()
        _vectorstore = PineconeVectorStore(
            index = index,
            embedding=get_embeddings(),
            namespace=settings.pinecone_namespace
        )
    return _vectorstore

def get_retriever():
    return get_vectorstore().as_retriever(search_kwargs={"k": settings.top_k})

def add_documents(chunks):
    store = get_vectorstore()
    return store.add_documents(chunks)
