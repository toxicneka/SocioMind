import numpy as np
import faiss
from .llm_client import client

class SocioRAG:
    def __init__(self):
        self.index = None
        self.chunks = []
        
    async def build_index(self, text_path='socio.txt'):
        # Читаем и предобрабатываем текст
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Разбиваем на чанки по социотипам
        self.chunks = []
        current_chunk = []
        
        for line in text.split('\n'):
            if line.strip() and not line.startswith(' '):
                if current_chunk:
                    self.chunks.append('\n'.join(current_chunk))
                    current_chunk = []
            current_chunk.append(line)
        
        if current_chunk:
            self.chunks.append('\n'.join(current_chunk))
        
        # Создаем эмбеддинги
        embeddings = []
        for chunk in self.chunks:
            response = client.models.embed_content(
                model="models/text-embedding-004",
                contents=chunk
            )
            embedding = response.embeddings[0].values
            embeddings.append(embedding)
        
        # Создаем FAISS индекс
        embeddings = np.array(embeddings, dtype='float32')
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)
    
    def search(self, query, k=3):
        # Получаем эмбеддинг запроса
        response = client.models.embed_content(
            model="models/text-embedding-004",
            contents=query
        )
        query_embedding = np.array([response.embeddings[0].values], dtype='float32')
        
        # Ищем в индексе
        distances, indices = self.index.search(query_embedding, k)
        
        # Возвращаем релевантные чанки
        return [self.chunks[i] for i in indices[0]]

# Глобальный экземпляр RAG
socio_rag = SocioRAG()