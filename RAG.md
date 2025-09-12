# 🧠 Piano per Implementazione RAG (Retrieval-Augmented Generation) Avanzato

## 📊 Analisi del Sistema RAG Attuale

### ❌ Limitazioni del Sistema Corrente

Il sistema attuale **NON è un vero RAG**, ma solo un semplice **context injection**:

1. **Context Statico**: Il campo `context` nella tabella `chats` contiene solo testo statico inserito manualmente
2. **Nessuna Elaborazione**: Il testo viene semplicemente aggiunto al prompt di sistema senza elaborazione
3. **Nessuna Indicizzazione**: Non esiste ricerca semantica o splitting dei documenti
4. **Nessun Retrieval**: Non c'è recupero automatico di informazioni rilevanti
5. **Nessun Embedding**: Non vengono generate rappresentazioni vettoriali del contenuto
6. **Storage Limitato**: Solo un campo TEXT in SQLite per chat

### 🔍 Comportamento Attuale

```javascript
// Nel frontend (App.js righe 504-507)
const context = currentChat?.context || "";
const systemMessageWithContext = context 
    ? `${systemMessage}\n\n--- CONTEXT ---\n${context}\n--- END CONTEXT ---`
    : systemMessage;
```

**Problema**: Il contesto viene semplicemente concatenato al prompt senza:
- Ricerca di rilevanza
- Splitting intelligente
- Ranking delle informazioni
- Gestione della dimensione del contesto

## 🎯 Piano per RAG Avanzato

### Fase 1: Infrastruttura Base (1-2 giorni)

#### 1.1 Database Vector Store
```sql
-- Nuove tabelle per RAG
CREATE TABLE document_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    project_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER,
    filename TEXT NOT NULL,
    content TEXT NOT NULL,
    content_type TEXT DEFAULT 'text/plain',
    metadata TEXT, -- JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (collection_id) REFERENCES document_collections (id) ON DELETE CASCADE
);

CREATE TABLE document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    chunk_index INTEGER,
    content TEXT NOT NULL,
    embedding BLOB, -- Vector embedding (serialized numpy array)
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX idx_chunks_document ON document_chunks (document_id);
```

#### 1.2 Dipendenze Python
```bash
pip install sentence-transformers numpy faiss-cpu pypdf2 python-docx tiktoken
```

#### 1.3 Embedding Service
```python
# rag/embedding_service.py
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from typing import List, Dict, Any
import pickle

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        return self.model.encode(texts, convert_to_numpy=True)
    
    def semantic_search(self, query: str, embeddings: np.ndarray, top_k: int = 5) -> List[int]:
        """Find most similar embeddings using FAISS"""
        query_embedding = self.model.encode([query])
        
        # Create FAISS index
        index = faiss.IndexFlatIP(self.dimension)  # Inner product for similarity
        faiss.normalize_L2(embeddings)  # Normalize for cosine similarity
        index.add(embeddings)
        
        # Search
        faiss.normalize_L2(query_embedding)
        scores, indices = index.search(query_embedding, top_k)
        
        return indices[0].tolist()
```

### Fase 2: Document Processing (2-3 giorni)

#### 2.1 Document Ingestion
```python
# rag/document_processor.py
import tiktoken
from typing import List, Dict, Any
import PyPDF2
import docx
import re

class DocumentProcessor:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def extract_text(self, file_path: str, content_type: str) -> str:
        """Extract text from various file formats"""
        if content_type == "application/pdf":
            return self._extract_pdf(file_path)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return self._extract_docx(file_path)
        elif content_type == "text/plain":
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """Split text into semantically coherent chunks"""
        # Clean text
        text = self._clean_text(text)
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Count tokens
            paragraph_tokens = len(self.tokenizer.encode(paragraph))
            current_tokens = len(self.tokenizer.encode(current_chunk))
            
            if current_tokens + paragraph_tokens > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'content': current_chunk.strip(),
                    'token_count': current_tokens
                })
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'token_count': len(self.tokenizer.encode(current_chunk))
            })
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()
```

#### 2.2 File Upload API
```python
# main.py - nuovi endpoint
from fastapi import UploadFile, File
from rag.document_processor import DocumentProcessor
from rag.embedding_service import EmbeddingService

@app.post("/api/collections/{collection_id}/upload")
async def upload_document(
    collection_id: int,
    file: UploadFile = File(...)
):
    """Upload and process a document"""
    processor = DocumentProcessor()
    embedding_service = EmbeddingService()
    
    # Save file temporarily
    file_path = f"temp/{file.filename}"
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    try:
        # Extract text
        text = processor.extract_text(file_path, file.content_type)
        
        # Create document record
        doc_id = db.create_document(collection_id, file.filename, text, file.content_type)
        
        # Chunk text
        chunks = processor.chunk_text(text)
        
        # Generate embeddings
        chunk_texts = [chunk['content'] for chunk in chunks]
        embeddings = embedding_service.generate_embeddings(chunk_texts)
        
        # Store chunks with embeddings
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db.create_chunk(
                doc_id, 
                i, 
                chunk['content'], 
                embedding.tobytes(), 
                chunk['token_count']
            )
        
        return {"message": "Document processed successfully", "chunks": len(chunks)}
    
    finally:
        # Clean up temp file
        os.remove(file_path)
```

### Fase 3: RAG Query Engine (2-3 giorni)

#### 3.1 Retrieval Service
```python
# rag/retrieval_service.py
from typing import List, Dict, Any, Optional
import numpy as np
from .embedding_service import EmbeddingService

class RetrievalService:
    def __init__(self, db_manager, embedding_service: EmbeddingService):
        self.db = db_manager
        self.embedding_service = embedding_service
    
    def retrieve_relevant_chunks(
        self, 
        query: str, 
        collection_ids: List[int] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Retrieve most relevant chunks for a query"""
        
        # Get all chunks from specified collections
        chunks = self.db.get_chunks_by_collections(collection_ids)
        
        if not chunks:
            return []
        
        # Extract embeddings and metadata
        embeddings = []
        chunk_metadata = []
        
        for chunk in chunks:
            embedding = np.frombuffer(chunk['embedding'], dtype=np.float32)
            embeddings.append(embedding)
            chunk_metadata.append({
                'id': chunk['id'],
                'content': chunk['content'],
                'document_id': chunk['document_id'],
                'token_count': chunk['token_count']
            })
        
        embeddings = np.array(embeddings)
        
        # Perform semantic search
        relevant_indices = self.embedding_service.semantic_search(
            query, embeddings, top_k
        )
        
        # Filter by similarity score if needed
        relevant_chunks = []
        for idx in relevant_indices:
            chunk_data = chunk_metadata[idx]
            
            # Calculate actual similarity score
            query_embedding = self.embedding_service.generate_embeddings([query])[0]
            chunk_embedding = embeddings[idx]
            similarity = np.dot(query_embedding, chunk_embedding)
            
            if similarity >= similarity_threshold:
                chunk_data['similarity_score'] = float(similarity)
                relevant_chunks.append(chunk_data)
        
        return relevant_chunks
    
    def build_rag_context(
        self, 
        query: str, 
        project_id: int,
        max_tokens: int = 2000
    ) -> str:
        """Build RAG context for a query within a project"""
        
        # Get collections for this project
        collections = self.db.get_collections_by_project(project_id)
        collection_ids = [c['id'] for c in collections]
        
        if not collection_ids:
            return ""
        
        # Retrieve relevant chunks
        relevant_chunks = self.retrieve_relevant_chunks(
            query, collection_ids, top_k=10
        )
        
        if not relevant_chunks:
            return ""
        
        # Build context string within token limit
        context_parts = []
        total_tokens = 0
        
        for chunk in relevant_chunks:
            chunk_tokens = chunk['token_count']
            
            if total_tokens + chunk_tokens > max_tokens:
                break
            
            context_parts.append(f"[Source: Document {chunk['document_id']}]\n{chunk['content']}")
            total_tokens += chunk_tokens
        
        if context_parts:
            return "\n\n---\n\n".join(context_parts)
        
        return ""
```

#### 3.2 Enhanced Chat Endpoint
```python
# main.py - modifica endpoint chat
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequestWithChat):
    retrieval_service = RetrievalService(db, EmbeddingService())
    
    # Extract user query from last message
    user_query = request.messages[-1].content if request.messages else ""
    
    # Get project context if chat_id is provided
    rag_context = ""
    if request.chat_id:
        chat = db.get_chat(request.chat_id)
        if chat and chat.get('project_id'):
            rag_context = retrieval_service.build_rag_context(
                user_query, chat['project_id']
            )
    
    # Enhance system message with RAG context
    if rag_context:
        enhanced_system_message = f"""You are KrakenGPT, a helpful AI assistant. Use the following context to inform your responses:

--- RETRIEVED CONTEXT ---
{rag_context}
--- END CONTEXT ---

Answer the user's question based on the context provided above. If the context doesn't contain relevant information, acknowledge this and provide a general response."""
        
        # Add enhanced system message to the beginning
        enhanced_messages = [
            {"role": "system", "content": enhanced_system_message}
        ] + [msg.dict() for msg in request.messages]
    else:
        enhanced_messages = [msg.dict() for msg in request.messages]
    
    # Continue with existing logic...
    payload = {
        "messages": enhanced_messages,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
        "stream": request.stream
    }
    
    # Rest of the existing endpoint logic...
```

### Fase 4: Frontend Integration (2-3 giorni)

#### 4.1 Document Management UI
```javascript
// Nuovo componente DocumentManager.js
import React, { useState, useEffect } from 'react';

const DocumentManager = ({ projectId, onDocumentUploaded }) => {
    const [collections, setCollections] = useState([]);
    const [selectedCollection, setSelectedCollection] = useState(null);
    const [uploading, setUploading] = useState(false);
    
    const handleFileUpload = async (file) => {
        if (!selectedCollection) return;
        
        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(
                `/api/collections/${selectedCollection.id}/upload`,
                {
                    method: 'POST',
                    body: formData
                }
            );
            
            if (response.ok) {
                const result = await response.json();
                onDocumentUploaded?.(result);
                alert(`Document uploaded and processed: ${result.chunks} chunks created`);
            }
        } catch (error) {
            console.error('Upload failed:', error);
            alert('Upload failed');
        } finally {
            setUploading(false);
        }
    };
    
    return (
        <div className="document-manager">
            <h3>📚 Document Management</h3>
            
            {/* Collection selector */}
            <div className="collection-selector">
                <select 
                    value={selectedCollection?.id || ''} 
                    onChange={(e) => setSelectedCollection(
                        collections.find(c => c.id === parseInt(e.target.value))
                    )}
                >
                    <option value="">Select Collection</option>
                    {collections.map(collection => (
                        <option key={collection.id} value={collection.id}>
                            {collection.name}
                        </option>
                    ))}
                </select>
            </div>
            
            {/* File upload */}
            <div className="file-upload">
                <input 
                    type="file" 
                    accept=".pdf,.docx,.txt"
                    onChange={(e) => handleFileUpload(e.target.files[0])}
                    disabled={!selectedCollection || uploading}
                />
                {uploading && <span>Processing...</span>}
            </div>
            
            {/* Collection documents */}
            {selectedCollection && (
                <DocumentList collectionId={selectedCollection.id} />
            )}
        </div>
    );
};
```

#### 4.2 RAG Context Indicator
```javascript
// Aggiunta ad App.js
const [ragContext, setRagContext] = useState("");

// Nella funzione sendMessage
const retrieveRAGContext = async (query, projectId) => {
    try {
        const response = await fetch('/api/rag/retrieve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, project_id: projectId })
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.context;
        }
    } catch (error) {
        console.error('RAG retrieval failed:', error);
    }
    return "";
};

// UI indicator
{ragContext && (
    <div className="rag-context-indicator">
        <span>🧠 RAG Context Active ({ragContext.split('\n\n').length} sources)</span>
    </div>
)}
```

### Fase 5: Advanced Features (3-4 giorni)

#### 5.1 Vector Database Migration
```python
# Opzione: Migrazione a Pinecone/Weaviate per scalabilità
import pinecone

class PineconeVectorStore:
    def __init__(self, api_key: str, environment: str):
        pinecone.init(api_key=api_key, environment=environment)
        self.index = pinecone.Index("krakengpt-rag")
    
    def upsert_embeddings(self, embeddings: List[Dict]):
        """Store embeddings in Pinecone"""
        self.index.upsert(embeddings)
    
    def query(self, query_embedding: List[float], top_k: int = 5):
        """Query similar embeddings"""
        return self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
```

#### 5.2 Hybrid Search
```python
# Combinazione di ricerca semantica + keyword search
from rank_bm25 import BM25Okapi

class HybridRetrieval:
    def __init__(self, embedding_service, chunks):
        self.embedding_service = embedding_service
        self.chunks = chunks
        
        # Prepare BM25 index
        tokenized_chunks = [chunk['content'].split() for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_chunks)
    
    def hybrid_search(self, query: str, alpha: float = 0.7):
        """Combine semantic and keyword search"""
        # Semantic search
        semantic_scores = self._semantic_search(query)
        
        # Keyword search
        keyword_scores = self.bm25.get_scores(query.split())
        
        # Combine scores
        combined_scores = []
        for i, (sem_score, kw_score) in enumerate(zip(semantic_scores, keyword_scores)):
            combined_score = alpha * sem_score + (1 - alpha) * kw_score
            combined_scores.append((i, combined_score))
        
        # Sort by combined score
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        
        return combined_scores[:10]  # Top 10 results
```

#### 5.3 Re-ranking with Cross-Encoder
```python
# Fine-tuning per relevance
from sentence_transformers import CrossEncoder

class ReRankingService:
    def __init__(self):
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-2-v2')
    
    def rerank_results(self, query: str, candidates: List[str]) -> List[int]:
        """Re-rank candidates based on query relevance"""
        pairs = [(query, candidate) for candidate in candidates]
        scores = self.reranker.predict(pairs)
        
        # Sort by relevance score
        ranked_indices = sorted(
            range(len(scores)), 
            key=lambda i: scores[i], 
            reverse=True
        )
        
        return ranked_indices
```

## 🚀 Roadmap di Implementazione

### Sprint 1 (Week 1): Infrastruttura Base
- [ ] Database schema per vector store
- [ ] Embedding service con Sentence Transformers
- [ ] Document processor per PDF/DOCX/TXT
- [ ] Basic chunking strategy

### Sprint 2 (Week 2): Core RAG
- [ ] Document upload API
- [ ] Chunk embedding e storage
- [ ] Basic retrieval service
- [ ] Enhanced chat endpoint con RAG

### Sprint 3 (Week 3): Frontend Integration  
- [ ] Document management UI
- [ ] Collection management
- [ ] RAG context indicators
- [ ] File upload progress

### Sprint 4 (Week 4): Advanced Features
- [ ] Hybrid search (semantic + keyword)
- [ ] Re-ranking con cross-encoder
- [ ] Vector database optimization
- [ ] Performance monitoring

### Sprint 5 (Week 5): Production Ready
- [ ] Error handling e retry logic
- [ ] Async processing per large documents
- [ ] RAG analytics dashboard  
- [ ] API rate limiting e caching

## 🔧 Configurazione Tecnica

### Environment Variables
```env
# RAG Configuration
RAG_ENABLED=true
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50
MAX_RAG_TOKENS=2000
SIMILARITY_THRESHOLD=0.7

# Optional: External Vector Store
PINECONE_API_KEY=your-key
PINECONE_ENVIRONMENT=us-west1-gcp
```

### Dependencies Update
```bash
# requirements.txt additions
sentence-transformers==2.2.2
faiss-cpu==1.7.4
PyPDF2==3.0.1
python-docx==0.8.11
tiktoken==0.5.1
rank-bm25==0.2.2
pinecone-client==2.2.4  # Optional
```

## 📊 Metriche di Successo

### Qualità RAG
- **Relevance Score**: > 0.8 per retrieved chunks
- **Context Utilization**: > 70% di risposte usano RAG context
- **Response Accuracy**: Miglioramento del 40% vs context statico

### Performance
- **Retrieval Time**: < 200ms per query
- **Embedding Generation**: < 100ms per chunk
- **Memory Usage**: < 1GB per 1000 documenti

### User Experience
- **Upload Success Rate**: > 99%
- **Search Response Time**: < 500ms end-to-end
- **User Satisfaction**: Rating > 4.5/5

## 🎯 Conclusioni

Questo piano trasforma il sistema da **semplice context injection** a **RAG avanzato** con:

1. **Semantic Search** per recupero intelligente
2. **Document Processing** automatico
3. **Vector Storage** efficiente  
4. **Hybrid Retrieval** per massima rilevanza
5. **Scalable Architecture** pronta per production

Il risultato sarà un sistema RAG completo che può competere con soluzioni enterprise, mantenendo la semplicità d'uso di KrakenGPT.

---

**🚀 Ready to implement RAG 2.0 in KrakenGPT!**