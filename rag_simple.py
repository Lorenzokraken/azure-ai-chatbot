# RAG Service Essenziale per KrakenGPT
# Implementazione minima per boost immediato ai modelli free

from sentence_transformers import SentenceTransformer
import numpy as np
import json
import sqlite3
from typing import List, Dict, Any
import logging

class SimpleRAG:
    def __init__(self):
        """Inizializza RAG con modello leggero e veloce"""
        print("🧠 Inizializzazione RAG Service...")
        
        # Modello piccolo e veloce - 384 dimensioni
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print(f"✅ Modello caricato: all-MiniLM-L6-v2 ({self.model.get_sentence_embedding_dimension()}D)")
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Chunking basilare per paragrafi - semplice ma efficace"""
        
        # Pulisci il testo
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = '\n'.join(line.strip() for line in text.split('\n'))
        
        # Dividi per paragrafi
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Se aggiungere questo paragrafo supera il limite
            if len(current_chunk + paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
            else:
                current_chunk += paragraph + "\n\n"
        
        # Aggiungi ultimo chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Fallback: se non ci sono paragrafi, chunking per caratteri
        if not chunks:
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                if chunk.strip():
                    chunks.append(chunk.strip())
        
        print(f"📝 Testo diviso in {len(chunks)} chunks")
        return chunks
    
    def add_document(self, project_id: int, filename: str, content: str) -> int:
        """Aggiungi documento e genera embeddings"""
        print(f"📄 Processando documento: {filename}")
        
        from db.db import DatabaseManager
        db = DatabaseManager()
        
        # Salva documento
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO rag_documents (project_id, filename, content)
                VALUES (?, ?, ?)
            ''', (project_id, filename, content))
            doc_id = cursor.lastrowid
            
            # Chunking
            chunks = self.chunk_text(content)
            
            if not chunks:
                print("⚠️ Nessun chunk generato dal documento")
                return doc_id
            
            print(f"🔄 Generazione embeddings per {len(chunks)} chunks...")
            
            # Genera embeddings per tutti i chunks
            embeddings = self.model.encode(chunks, show_progress_bar=True)
            
            # Salva chunks con embeddings
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                embedding_json = json.dumps(embedding.tolist())
                cursor.execute('''
                    INSERT INTO rag_chunks (document_id, content, embedding)
                    VALUES (?, ?, ?)
                ''', (doc_id, chunk, embedding_json))
            
            conn.commit()
            print(f"✅ Documento {filename} processato: {len(chunks)} chunks salvati")
            return doc_id
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Errore processamento {filename}: {e}")
            raise
        finally:
            conn.close()
    
    def search(self, query: str, project_id: int, top_k: int = 5) -> str:
        """Cerca chunks rilevanti e restituisci context per il prompt"""
        print(f"🔍 Ricerca RAG per: '{query[:50]}...'")
        
        from db.db import DatabaseManager
        db = DatabaseManager()
        
        # Genera embedding della query
        query_embedding = self.model.encode([query])[0]
        
        # Recupera tutti i chunks del progetto
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT rc.content, rc.embedding, rd.filename
                FROM rag_chunks rc
                JOIN rag_documents rd ON rc.document_id = rd.id
                WHERE rd.project_id = ?
            ''', (project_id,))
            
            results = cursor.fetchall()
            
            if not results:
                print("📭 Nessun documento trovato per questo progetto")
                return ""
            
            print(f"📊 Analizzando {len(results)} chunks...")
            
            # Calcola similarity per ogni chunk
            similarities = []
            for content, embedding_json, filename in results:
                try:
                    chunk_embedding = np.array(json.loads(embedding_json))
                    
                    # Cosine similarity
                    similarity = np.dot(query_embedding, chunk_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                    )
                    similarities.append((similarity, content, filename))
                except Exception as e:
                    print(f"⚠️ Errore calcolo similarity: {e}")
                    continue
            
            if not similarities:
                print("❌ Errore nel calcolo delle similarità")
                return ""
            
            # Ordina per similarity e prendi top_k
            similarities.sort(reverse=True, key=lambda x: x[0])
            top_chunks = similarities[:top_k]
            
            # Debug: mostra similarità per debug
            for i, (similarity, content, filename) in enumerate(top_chunks[:3]):  # Mostra top 3 per debug
                print(f"   📋 Chunk {i+1}: Similarità {similarity:.1%} - Preview: {content[:80]}...")
            
            # Filtra per threshold minimo (molto basso per test)
            relevant_chunks = [chunk for chunk in top_chunks if chunk[0] >= 0.05]  # Abbassato a 5%
            
            if not relevant_chunks:
                print(f"🔍 Nessun chunk sufficientemente rilevante (soglia: 5%)")
                return ""
            
            print(f"✅ Trovati {len(relevant_chunks)} chunks rilevanti")
            
            # Costruisci context formattato
            context_parts = []
            for i, (score, content, filename) in enumerate(relevant_chunks):
                score_percent = score * 100
                context_parts.append(f"[Fonte: {filename} - Rilevanza: {score_percent:.1f}%]\n{content}")
            
            context = "\n\n---\n\n".join(context_parts)
            
            print(f"📋 Context generato: {len(context)} caratteri")
            return context
            
        except Exception as e:
            print(f"❌ Errore durante la ricerca: {e}")
            return ""
        finally:
            conn.close()
    
    def get_project_stats(self, project_id: int) -> Dict[str, Any]:
        """Ottieni statistiche RAG per un progetto"""
        from db.db import DatabaseManager
        db = DatabaseManager()
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Conta documenti
            cursor.execute('''
                SELECT COUNT(*) FROM rag_documents WHERE project_id = ?
            ''', (project_id,))
            doc_count = cursor.fetchone()[0]
            
            # Conta chunks
            cursor.execute('''
                SELECT COUNT(*) FROM rag_chunks rc
                JOIN rag_documents rd ON rc.document_id = rd.id
                WHERE rd.project_id = ?
            ''', (project_id,))
            chunk_count = cursor.fetchone()[0]
            
            return {
                'documents': doc_count,
                'chunks': chunk_count,
                'status': 'active' if doc_count > 0 else 'empty'
            }
            
        except Exception as e:
            print(f"❌ Errore statistiche: {e}")
            return {'documents': 0, 'chunks': 0, 'status': 'error'}
        finally:
            conn.close()

# Istanza globale per l'app
rag = SimpleRAG()

# Test function per debugging
def test_rag():
    """Funzione di test per verificare il funzionamento"""
    print("🧪 Test RAG Service...")
    
    # Test embedding
    test_text = "Questo è un test per verificare il funzionamento degli embeddings"
    embedding = rag.model.encode([test_text])[0]
    print(f"✅ Test embedding: {len(embedding)} dimensioni")
    
    # Test chunking
    long_text = "Questo è il primo paragrafo.\n\nQuesto è il secondo paragrafo con più testo per testare il chunking automatico del sistema RAG.\n\nTerzo paragrafo finale."
    chunks = rag.chunk_text(long_text)
    print(f"✅ Test chunking: {len(chunks)} chunks generati")
    
    print("🎉 RAG Service funzionante!")

if __name__ == "__main__":
    test_rag()
