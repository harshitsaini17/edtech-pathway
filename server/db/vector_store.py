"""
Vector Store Implementation using ChromaDB
==========================================
Handles storage and retrieval of topic embeddings for semantic search
and RAG operations in the adaptive learning system.
"""

import os
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import numpy as np

from config.settings import settings


class VectorStore:
    """
    ChromaDB-based vector store for topic embeddings and metadata
    """
    
    def __init__(
        self,
        persist_directory: str = None,
        embedding_model_name: str = None
    ):
        """
        Initialize the vector store
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            embedding_model_name: Name of the sentence transformer model
        """
        self.persist_directory = persist_directory or settings.CHROMADB_PATH
        self.embedding_model_name = embedding_model_name or settings.EMBEDDING_MODEL
        
        # Ensure directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Create embedding function for ChromaDB
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model_name
        )
        
        # Initialize collections
        self.topics_collection = self._get_or_create_collection(
            settings.CHROMADB_COLLECTION_TOPICS
        )
        self.questions_collection = self._get_or_create_collection(
            settings.CHROMADB_COLLECTION_QUESTIONS
        )
        
        print(f"✅ VectorStore initialized with {self.embedding_model_name}")
        print(f"📁 Persisting to: {self.persist_directory}")
        
    def _get_or_create_collection(self, name: str):
        """Get or create a collection"""
        try:
            collection = self.client.get_collection(
                name=name,
                embedding_function=self.embedding_function
            )
            print(f"📚 Loaded existing collection: {name}")
        except:
            collection = self.client.create_collection(
                name=name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"✨ Created new collection: {name}")
        
        return collection
    
    def add_topics(
        self,
        topics: List[Dict[str, Any]],
        source_document: str = "unknown",
        batch_size: int = 100
    ) -> int:
        """
        Add topics to the vector store
        
        Args:
            topics: List of topic dictionaries with 'topic', 'page', etc.
            source_document: Source PDF/document name
            batch_size: Batch size for adding embeddings
            
        Returns:
            Number of topics added
        """
        if not topics:
            return 0
        
        added_count = 0
        
        # Process in batches
        for i in range(0, len(topics), batch_size):
            batch = topics[i:i + batch_size]
            
            ids = []
            documents = []
            metadatas = []
            
            for topic_data in batch:
                # Generate unique ID
                topic_id = str(uuid.uuid4())
                
                # Extract topic text
                topic_text = topic_data.get('topic', topic_data.get('title', ''))
                
                if not topic_text:
                    continue
                
                # Prepare document (the text to embed)
                doc_text = topic_text
                
                # Add context if available
                if 'content' in topic_data:
                    doc_text = f"{topic_text}\n\n{topic_data['content']}"
                elif 'clean_text' in topic_data:
                    doc_text = f"{topic_text}\n\n{topic_data['clean_text']}"
                
                # Prepare metadata
                metadata = {
                    'topic': topic_text,
                    'page': topic_data.get('page', 0),
                    'source_document': source_document,
                    'source_type': topic_data.get('source', 'unknown'),
                    'added_at': datetime.now().isoformat(),
                }
                
                # Add optional metadata
                if 'chapter' in topic_data:
                    metadata['chapter'] = str(topic_data['chapter'])
                if 'section' in topic_data:
                    metadata['section'] = str(topic_data['section'])
                if 'confidence' in topic_data:
                    metadata['confidence'] = float(topic_data['confidence'])
                if 'boundary_type' in topic_data:
                    metadata['boundary_type'] = str(topic_data['boundary_type'])
                
                ids.append(topic_id)
                documents.append(doc_text)
                metadatas.append(metadata)
            
            # Add to collection
            if ids:
                try:
                    self.topics_collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas
                    )
                    added_count += len(ids)
                except Exception as e:
                    print(f"⚠️ Error adding batch: {e}")
                    continue
        
        print(f"✅ Added {added_count} topics to vector store")
        return added_count
    
    def search_topics(
        self,
        query: str,
        n_results: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant topics using semantic similarity
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of matching topics with scores
        """
        try:
            results = self.topics_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_dict
            )
            
            # Format results
            formatted_results = []
            
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'topic': results['metadatas'][0][i].get('topic', ''),
                        'page': results['metadatas'][0][i].get('page', 0),
                        'source_document': results['metadatas'][0][i].get('source_document', ''),
                        'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i]
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching topics: {e}")
            return []
    
    def get_topic_by_id(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific topic by ID"""
        try:
            results = self.topics_collection.get(ids=[topic_id])
            
            if results['ids']:
                return {
                    'id': results['ids'][0],
                    'topic': results['metadatas'][0].get('topic', ''),
                    'content': results['documents'][0],
                    'metadata': results['metadatas'][0]
                }
            return None
            
        except Exception as e:
            print(f"❌ Error getting topic: {e}")
            return None
    
    def add_questions(
        self,
        questions: List[Dict[str, Any]],
        module_name: str = "unknown",
        batch_size: int = 100
    ) -> int:
        """
        Add quiz questions to the vector store
        
        Args:
            questions: List of question dictionaries
            module_name: Module/topic name
            batch_size: Batch size for adding
            
        Returns:
            Number of questions added
        """
        if not questions:
            return 0
        
        added_count = 0
        
        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]
            
            ids = []
            documents = []
            metadatas = []
            
            for question_data in batch:
                question_id = str(uuid.uuid4())
                
                # Extract question text
                question_text = question_data.get('question', '')
                if not question_text:
                    continue
                
                # Prepare document
                doc_text = question_text
                if 'context' in question_data:
                    doc_text = f"{question_text}\n\nContext: {question_data['context']}"
                
                # Prepare metadata
                metadata = {
                    'module_name': module_name,
                    'question_type': question_data.get('type', 'mcq'),
                    'difficulty': question_data.get('difficulty', 'medium'),
                    'topic': question_data.get('topic', ''),
                    'added_at': datetime.now().isoformat(),
                }
                
                # Add optional fields
                if 'correct_answer' in question_data:
                    metadata['has_answer'] = True
                if 'explanation' in question_data:
                    metadata['has_explanation'] = True
                
                ids.append(question_id)
                documents.append(doc_text)
                metadatas.append(metadata)
            
            # Add to collection
            if ids:
                try:
                    self.questions_collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas
                    )
                    added_count += len(ids)
                except Exception as e:
                    print(f"⚠️ Error adding question batch: {e}")
                    continue
        
        print(f"✅ Added {added_count} questions to vector store")
        return added_count
    
    def search_questions(
        self,
        query: str,
        n_results: int = 5,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant questions
        
        Args:
            query: Search query
            n_results: Number of results
            difficulty: Filter by difficulty
            question_type: Filter by type
            
        Returns:
            List of matching questions
        """
        filter_dict = {}
        if difficulty:
            filter_dict['difficulty'] = difficulty
        if question_type:
            filter_dict['question_type'] = question_type
        
        try:
            results = self.questions_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_dict if filter_dict else None
            )
            
            # Format results
            formatted_results = []
            
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'question': results['documents'][0][i],
                        'similarity_score': 1 - results['distances'][0][i],
                        'metadata': results['metadatas'][0][i]
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching questions: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collections"""
        topics_count = self.topics_collection.count()
        questions_count = self.questions_collection.count()
        
        return {
            'topics_count': topics_count,
            'questions_count': questions_count,
            'embedding_model': self.embedding_model_name,
            'embedding_dimension': settings.EMBEDDING_DIMENSION,
            'persist_directory': self.persist_directory
        }
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            self.client.delete_collection(name=collection_name)
            print(f"🗑️ Deleted collection: {collection_name}")
            return True
        except Exception as e:
            print(f"❌ Error deleting collection: {e}")
            return False
    
    def reset_all(self) -> bool:
        """Reset all collections (use with caution!)"""
        try:
            self.client.reset()
            print("🗑️ Reset all collections")
            
            # Recreate collections
            self.topics_collection = self._get_or_create_collection(
                settings.CHROMADB_COLLECTION_TOPICS
            )
            self.questions_collection = self._get_or_create_collection(
                settings.CHROMADB_COLLECTION_QUESTIONS
            )
            return True
        except Exception as e:
            print(f"❌ Error resetting: {e}")
            return False


# Singleton instance
_vector_store_instance = None


def get_vector_store() -> VectorStore:
    """Get or create the global vector store instance"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance


if __name__ == "__main__":
    # Test the vector store
    print("🧪 Testing VectorStore...")
    
    store = VectorStore()
    
    # Test adding topics
    sample_topics = [
        {
            'topic': 'Introduction to Probability',
            'page': 1,
            'content': 'Probability is the study of random events and their likelihood.'
        },
        {
            'topic': 'Random Variables',
            'page': 15,
            'content': 'A random variable is a variable whose value depends on outcomes of a random phenomenon.'
        },
        {
            'topic': 'Expected Value',
            'page': 30,
            'content': 'The expected value is the long-run average value of repetitions of the experiment.'
        }
    ]
    
    store.add_topics(sample_topics, source_document="test_book.pdf")
    
    # Test search
    print("\n🔍 Searching for 'probability theory'...")
    results = store.search_topics("probability theory", n_results=3)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['topic']} (Score: {result['similarity_score']:.3f})")
    
    # Get stats
    print("\n📊 Collection Stats:")
    stats = store.get_collection_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ VectorStore test complete!")
