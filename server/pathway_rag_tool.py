"""
RAG Tool using Pathway with ChromaDB for local vector storage
and Azure OpenAI embeddings
"""

import os
import time
import pathway as pw
from pathway.xpacks.llm import embedders, llms, parsers, splitters
from pathway.xpacks.llm.vector_store import VectorStoreServer
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import numpy as np
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from dataclasses import dataclass
import json

load_dotenv()


@dataclass
class RAGConfig:
    """Configuration for RAG system"""
    # Azure OpenAI Embeddings
    embeddings_api_key: str = os.getenv("AZURE_OPENAI_EMBEDDINGS_API_KEY")
    embeddings_endpoint: str = os.getenv("AZURE_OPENAI_EMBEDDINGS_ENDPOINT")
    embeddings_deployment: str = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME")
    embeddings_api_version: str = os.getenv("AZURE_OPENAI_EMBEDDINGS_API_VERSION", "2025-01-01-preview")
    
    # Azure OpenAI Chat
    chat_api_key: str = os.getenv("AZURE_OPENAI_API_KEY")
    chat_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT")
    chat_deployment: str = os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME_GPT_4_1_MINI")
    chat_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    
    # ChromaDB settings
    chroma_persist_directory: str = "./data/chroma_db"
    chroma_collection_name: str = "pathway_rag_collection"
    
    # Text processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    
    # Batch processing for embeddings
    embedding_batch_size: int = 50  # Number of chunks to embed at once
    batch_delay_seconds: float = 1.0  # Delay between batches to avoid rate limits


class ChromaDBVectorStore:
    """ChromaDB integration for local vector storage"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.client = chromadb.PersistentClient(
            path=config.chroma_persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=config.chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def document_exists(self, document_id: str) -> bool:
        """Check if a document with given ID exists in the collection"""
        try:
            result = self.collection.get(ids=[document_id])
            return len(result['ids']) > 0
        except Exception:
            return False
    
    def get_documents_by_source(self, source_identifier: str) -> List[str]:
        """Get all document IDs for a given source (e.g., filename)"""
        try:
            results = self.collection.get(
                where={"source_file": source_identifier}
            )
            return results['ids'] if results else []
        except Exception:
            return []
        
    def add_documents(self, documents: List[str], embeddings: List[List[float]], 
                     metadatas: Optional[List[Dict]] = None, ids: Optional[List[str]] = None):
        """Add documents with embeddings to ChromaDB"""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        if metadatas is None:
            metadatas = [{"source": "pathway"} for _ in range(len(documents))]
        
        # Filter out documents that already exist
        new_documents = []
        new_embeddings = []
        new_metadatas = []
        new_ids = []
        
        for doc, emb, meta, doc_id in zip(documents, embeddings, metadatas, ids):
            if not self.document_exists(doc_id):
                new_documents.append(doc)
                new_embeddings.append(emb)
                new_metadatas.append(meta)
                new_ids.append(doc_id)
        
        if new_documents:
            self.collection.add(
                documents=new_documents,
                embeddings=new_embeddings,
                metadatas=new_metadatas,
                ids=new_ids
            )
        
        return len(new_documents), len(documents) - len(new_documents)
        
    def query(self, query_embedding: List[float], n_results: int = 5) -> Dict[str, Any]:
        """Query ChromaDB with embedding"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results
    
    def delete_collection(self):
        """Delete the collection"""
        self.client.delete_collection(name=self.config.chroma_collection_name)
        
    def get_collection_count(self) -> int:
        """Get the number of documents in collection"""
        return self.collection.count()


class PathwayRAGTool:
    """RAG Tool using Pathway with ChromaDB and Azure OpenAI"""
    
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        
        # Initialize Azure OpenAI embeddings
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=self.config.embeddings_endpoint,
            api_key=self.config.embeddings_api_key,
            azure_deployment=self.config.embeddings_deployment,
            api_version=self.config.embeddings_api_version
        )
        
        # Initialize Azure OpenAI chat
        self.llm = AzureChatOpenAI(
            azure_endpoint=self.config.chat_endpoint,
            api_key=self.config.chat_api_key,
            azure_deployment=self.config.chat_deployment,
            api_version=self.config.chat_api_version,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Initialize ChromaDB
        self.vector_store = ChromaDBVectorStore(self.config)
        
        print(f"✓ Initialized Pathway RAG Tool")
        print(f"✓ ChromaDB collection: {self.config.chroma_collection_name}")
        print(f"✓ Documents in collection: {self.vector_store.get_collection_count()}")
        
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.config.chunk_size
            
            # If not the last chunk, try to break at a sentence or word boundary
            if end < text_length:
                # Look for sentence boundary
                period_pos = text.rfind('.', start, end)
                newline_pos = text.rfind('\n', start, end)
                space_pos = text.rfind(' ', start, end)
                
                # Choose the best boundary
                boundary = max(period_pos, newline_pos, space_pos)
                if boundary > start:
                    end = boundary + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.config.chunk_overlap
            
        return chunks
    
    def process_documents(self, documents: List[str], metadatas: Optional[List[Dict]] = None, source_file: Optional[str] = None):
        """Process and index documents using Pathway"""
        
        # Check if source file already exists in database
        if source_file:
            existing_docs = self.vector_store.get_documents_by_source(source_file)
            if existing_docs:
                print(f"⚠ Document '{source_file}' already exists in database with {len(existing_docs)} chunks")
                print(f"  Skipping to avoid duplicate embeddings.")
                return {
                    "status": "skipped",
                    "reason": "already_exists",
                    "existing_chunks": len(existing_docs),
                    "source_file": source_file
                }
        
        all_chunks = []
        all_metadatas = []
        all_ids = []
        
        # Track total chunk count across all documents for unique IDs
        global_chunk_idx = 0
        
        for idx, doc in enumerate(documents):
            chunks = self.chunk_text(doc)
            
            for chunk_idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                
                # Prepare metadata with source_file for tracking
                metadata = {
                    "source": f"doc_{idx}", 
                    "chunk": chunk_idx,
                    "chunk_total": len(chunks)
                }
                
                if source_file:
                    metadata["source_file"] = source_file
                    
                if metadatas and idx < len(metadatas):
                    metadata.update(metadatas[idx])
                    
                all_metadatas.append(metadata)
                
                # Generate unique ID based on source_file if available
                if source_file:
                    # Use hash of source_file and global chunk index for consistent IDs
                    import hashlib
                    file_hash = hashlib.md5(source_file.encode()).hexdigest()[:8]
                    doc_id = f"{file_hash}_chunk_{global_chunk_idx}"
                else:
                    # Use timestamp-based ID if no source file
                    import time
                    doc_id = f"doc_{idx}_chunk_{chunk_idx}_{int(time.time()*1000)}"
                    
                all_ids.append(doc_id)
                global_chunk_idx += 1
        
        print(f"Processing {len(all_chunks)} chunks from {len(documents)} documents...")
        
        # Generate embeddings in batches to avoid rate limits
        batch_size = self.config.embedding_batch_size
        batch_delay = self.config.batch_delay_seconds
        all_embeddings = []
        total_chunks = len(all_chunks)
        
        print(f"Generating embeddings in batches of {batch_size} (delay: {batch_delay}s)...")
        
        for i in range(0, total_chunks, batch_size):
            batch_end = min(i + batch_size, total_chunks)
            batch = all_chunks[i:batch_end]
            batch_num = (i // batch_size) + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size
            
            print(f"  Batch {batch_num}/{total_batches}: Processing {len(batch)} chunks...")
            
            try:
                batch_embeddings = self.embeddings.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)
                print(f"    ✓ Generated {len(batch_embeddings)} embeddings")
                
                # Small delay between batches to avoid rate limits
                if batch_end < total_chunks:
                    import time
                    time.sleep(batch_delay)
                    
            except Exception as e:
                if "429" in str(e) or "rate limit" in str(e).lower():
                    print(f"    ⚠ Rate limit hit! Waiting 60 seconds...")
                    import time
                    time.sleep(60)
                    
                    # Retry this batch
                    print(f"    ↻ Retrying batch {batch_num}...")
                    batch_embeddings = self.embeddings.embed_documents(batch)
                    all_embeddings.extend(batch_embeddings)
                    print(f"    ✓ Retry successful!")
                else:
                    raise
        
        print(f"✓ Generated embeddings for all {len(all_embeddings)} chunks")
        
        # Add to ChromaDB (will filter duplicates internally)
        added, skipped = self.vector_store.add_documents(
            documents=all_chunks,
            embeddings=all_embeddings,
            metadatas=all_metadatas,
            ids=all_ids
        )
        
        print(f"✓ Added {added} new chunks")
        if skipped > 0:
            print(f"⚠ Skipped {skipped} duplicate chunks")
        print(f"✓ Total documents in collection: {self.vector_store.get_collection_count()}")
        
        return {
            "status": "success",
            "added": added,
            "skipped": skipped,
            "total_chunks": len(all_chunks),
            "source_file": source_file
        }
    
    def process_documents_with_pages(self, page_texts: List[Dict], pdf_file: str, page_count: int):
        """Process PDF documents with page number tracking for each chunk
        
        Args:
            page_texts: List of dicts with 'text' and 'page_number' keys
            pdf_file: Name of the PDF file
            page_count: Total number of pages
            
        Returns:
            Dictionary with processing status
        """
        # Check if source file already exists in database
        existing_docs = self.vector_store.get_documents_by_source(pdf_file)
        if existing_docs:
            print(f"⚠ Document '{pdf_file}' already exists in database with {len(existing_docs)} chunks")
            print(f"  Skipping to avoid duplicate embeddings.")
            return {
                "status": "skipped",
                "reason": "already_exists",
                "existing_chunks": len(existing_docs),
                "source_file": pdf_file
            }
        
        all_chunks = []
        all_metadatas = []
        all_ids = []
        global_chunk_idx = 0
        
        # Process each page and create chunks with page number metadata
        for page_data in page_texts:
            page_text = page_data['text']
            page_num = page_data['page_number']
            
            # Chunk the page text
            chunks = self.chunk_text(page_text)
            
            for chunk_idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                
                # Prepare metadata with page number
                metadata = {
                    "source_file": pdf_file,
                    "filename": pdf_file,
                    "source": "pdf",
                    "page_number": page_num,  # Add page number for this chunk
                    "chunk": global_chunk_idx,
                    "page_chunk_index": chunk_idx,  # Chunk index within this page
                    "pages": page_count  # Total pages in document
                }
                
                all_metadatas.append(metadata)
                
                # Generate unique ID
                import hashlib
                file_hash = hashlib.md5(pdf_file.encode()).hexdigest()[:8]
                doc_id = f"{file_hash}_page{page_num}_chunk_{chunk_idx}_{global_chunk_idx}"
                
                all_ids.append(doc_id)
                global_chunk_idx += 1
        
        # Update chunk_total in all metadatas now that we know the total
        for metadata in all_metadatas:
            metadata['chunk_total'] = len(all_chunks)
        
        print(f"Processing {len(all_chunks)} chunks from {len(page_texts)} pages...")
        
        # Generate embeddings in batches
        batch_size = self.config.embedding_batch_size
        batch_delay = self.config.batch_delay_seconds
        all_embeddings = []
        
        total_batches = (len(all_chunks) + batch_size - 1) // batch_size
        print(f"Generating embeddings in batches of {batch_size} (delay: {batch_delay}s)...")
        
        for i in range(0, len(all_chunks), batch_size):
            batch_num = i // batch_size + 1
            batch = all_chunks[i:i+batch_size]
            print(f"  Batch {batch_num}/{total_batches}: Processing {len(batch)} chunks...")
            
            try:
                batch_embeddings = self.embeddings.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)
                print(f"    ✓ Generated {len(batch_embeddings)} embeddings")
                
                # Add delay between batches to avoid rate limits
                if i + batch_size < len(all_chunks):
                    time.sleep(batch_delay)
            except Exception as e:
                if "429" in str(e):
                    print(f"    ⚠ Rate limit hit, waiting 5 seconds...")
                    time.sleep(5)
                    print(f"    ↻ Retrying batch {batch_num}...")
                    batch_embeddings = self.embeddings.embed_documents(batch)
                    all_embeddings.extend(batch_embeddings)
                    print(f"    ✓ Retry successful!")
                else:
                    raise
        
        print(f"✓ Generated embeddings for all {len(all_embeddings)} chunks")
        
        # Add to ChromaDB
        added, skipped = self.vector_store.add_documents(
            documents=all_chunks,
            embeddings=all_embeddings,
            metadatas=all_metadatas,
            ids=all_ids
        )
        
        print(f"✓ Added {added} new chunks")
        if skipped > 0:
            print(f"⚠ Skipped {skipped} duplicate chunks")
        print(f"✓ Total documents in collection: {self.vector_store.get_collection_count()}")
        
        return {
            "status": "success",
            "added": added,
            "skipped": skipped,
            "total_chunks": len(all_chunks),
            "source_file": pdf_file
        }
        
    def process_pdf_directory(self, directory_path: str, pdf_pattern: Optional[str] = None):
        """Process all PDF files in a directory
        
        Args:
            directory_path: Path to directory containing PDFs
            pdf_pattern: Optional pattern to filter PDFs (e.g., 'book2.pdf' or '*.pdf')
        """
        import fitz  # PyMuPDF
        
        all_pdf_files = [f for f in os.listdir(directory_path) if f.endswith('.pdf')]
        
        # Filter by pattern if provided
        if pdf_pattern:
            if '*' in pdf_pattern:
                # Wildcard matching
                import fnmatch
                pdf_files = [f for f in all_pdf_files if fnmatch.fnmatch(f, pdf_pattern)]
            else:
                # Exact match
                pdf_files = [f for f in all_pdf_files if f == pdf_pattern]
        else:
            pdf_files = all_pdf_files
            
        print(f"Found {len(pdf_files)} PDF files in {directory_path}")
        
        results = []
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(directory_path, pdf_file)
            print(f"\n{'='*80}")
            print(f"Processing: {pdf_file}")
            print('='*80)
            
            try:
                # Check if this PDF is already in the database
                existing_docs = self.vector_store.get_documents_by_source(pdf_file)
                if existing_docs:
                    print(f"✓ PDF '{pdf_file}' already indexed with {len(existing_docs)} chunks")
                    print(f"  Skipping to avoid duplicate embeddings.")
                    results.append({
                        "filename": pdf_file,
                        "status": "skipped",
                        "reason": "already_exists",
                        "existing_chunks": len(existing_docs)
                    })
                    continue
                
                # Extract text from PDF page by page with page tracking
                doc = fitz.open(pdf_path)
                page_count = len(doc)
                page_texts = []
                
                for page_num, page in enumerate(doc, 1):
                    page_text = page.get_text()
                    if page_text.strip():
                        page_texts.append({
                            'text': page_text,
                            'page_number': page_num
                        })
                    if page_num % 10 == 0:
                        print(f"  Extracted {page_num}/{page_count} pages...")
                
                doc.close()
                
                if page_texts:
                    # Process the document with page number tracking
                    result = self.process_documents_with_pages(
                        page_texts=page_texts,
                        pdf_file=pdf_file,
                        page_count=page_count
                    )
                    result["filename"] = pdf_file
                    result["pages"] = page_count
                    results.append(result)
                    
                    if result["status"] == "success":
                        print(f"✓ Successfully processed {pdf_file} ({page_count} pages)")
                else:
                    print(f"⚠ No text extracted from {pdf_file}")
                    results.append({
                        "filename": pdf_file,
                        "status": "failed",
                        "reason": "no_text_extracted"
                    })
                    
            except Exception as e:
                print(f"✗ Error processing {pdf_file}: {str(e)}")
                results.append({
                    "filename": pdf_file,
                    "status": "error",
                    "error": str(e)
                })
        
        # Print summary
        print(f"\n{'='*80}")
        print("PROCESSING SUMMARY")
        print('='*80)
        
        success_count = sum(1 for r in results if r.get("status") == "success")
        skipped_count = sum(1 for r in results if r.get("status") == "skipped")
        error_count = sum(1 for r in results if r.get("status") in ["error", "failed"])
        
        print(f"✓ Successfully processed: {success_count} PDF(s)")
        print(f"⚠ Skipped (already exists): {skipped_count} PDF(s)")
        print(f"✗ Failed/Error: {error_count} PDF(s)")
        print(f"📊 Total documents in database: {self.vector_store.get_collection_count()}")
        
        return results
    
    def query(self, question: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Query the RAG system and return only top K chunks (no LLM generation)
        
        Args:
            question: The query question
            top_k: Number of top results to return (uses config default if not specified)
            
        Returns:
            Dictionary containing question, retrieved chunks, and metadata
        """
        if top_k is None:
            top_k = self.config.top_k_results
            
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(question)
        
        # Search ChromaDB
        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=top_k
        )
        
        # Extract relevant documents
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        
        # Calculate relevance scores (1 - distance for cosine similarity)
        relevance_scores = [1 - dist for dist in distances]
        
        # Prepare response with only retrieved chunks
        response = {
            "question": question,
            "top_k": top_k,
            "retrieved_chunks": [
                {
                    "chunk_id": idx + 1,
                    "text": doc,
                    "relevance_score": score,
                    "metadata": meta
                }
                for idx, (doc, score, meta) in enumerate(zip(documents, relevance_scores, metadatas))
            ],
            "total_retrieved": len(documents)
        }
        
        return response
    
    def query_with_llm(self, question: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Query the RAG system with LLM answer generation
        
        Args:
            question: The query question
            top_k: Number of top results to use as context
            
        Returns:
            Dictionary containing question, answer, and retrieved chunks
        """
        # Get retrieved chunks
        retrieval_result = self.query(question, top_k)
        
        if not retrieval_result['retrieved_chunks']:
            return {
                **retrieval_result,
                "answer": "No relevant information found in the knowledge base."
            }
        
        # Build context from retrieved chunks
        context = "\n\n".join([
            f"[Chunk {chunk['chunk_id']}]:\n{chunk['text']}"
            for chunk in retrieval_result['retrieved_chunks']
        ])
        
        # Generate answer using LLM
        prompt = f"""Based on the following context chunks from the knowledge base, please answer the question.

Context:
{context}

Question: {question}

Answer:"""
        
        llm_response = self.llm.invoke(prompt)
        
        return {
            **retrieval_result,
            "answer": llm_response.content
        }
    
    def chat(self, question: str, use_llm: bool = False, top_k: Optional[int] = None) -> str:
        """
        Simple chat interface - returns top K chunks by default
        
        Args:
            question: The query question
            use_llm: Whether to generate an answer using LLM (default: False)
            top_k: Number of top results to return
        """
        if use_llm:
            result = self.query_with_llm(question, top_k)
        else:
            result = self.query(question, top_k)
        
        print("\n" + "="*80)
        print(f"Question: {question}")
        print("="*80)
        
        if "answer" in result:
            print(f"\n📝 Generated Answer:\n{result['answer']}")
        
        print(f"\n{'─'*80}")
        print(f"📚 Top {result['top_k']} Retrieved Chunks:")
        print('─'*80)
        
        for chunk_data in result['retrieved_chunks']:
            print(f"\n[Chunk {chunk_data['chunk_id']}] Relevance Score: {chunk_data['relevance_score']:.3f}")
            
            metadata = chunk_data['metadata']
            if 'source_file' in metadata:
                print(f"Source File: {metadata['source_file']}")
            if 'pages' in metadata:
                print(f"Total Pages: {metadata['pages']}")
            if 'chunk' in metadata and 'chunk_total' in metadata:
                print(f"Chunk: {metadata['chunk'] + 1}/{metadata['chunk_total']}")
            
            print(f"\nText Preview:\n{chunk_data['text'][:300]}...")
        
        return result.get("answer", "Chunks retrieved successfully")
    
    def reset_database(self):
        """Reset the ChromaDB collection"""
        self.vector_store.delete_collection()
        self.vector_store = ChromaDBVectorStore(self.config)
        print("✓ Database reset successfully")


def main():
    """Example usage of the Pathway RAG Tool"""
    
    # Initialize RAG tool
    rag = PathwayRAGTool()
    
    # Example 1: Process PDF documents
    pdf_directory = "./doc"
    if os.path.exists(pdf_directory):
        print("\n" + "="*80)
        print("Processing PDF documents...")
        print("="*80)
        rag.process_pdf_directory(pdf_directory)
    
    # Example 2: Process text documents
    sample_documents = [
        """
        Pathway is a Python data processing framework for analytics and AI pipelines over data streams.
        It's designed for real-time data processing and can handle both batch and streaming data efficiently.
        """,
        """
        ChromaDB is an open-source embedding database that makes it easy to build LLM apps by making 
        knowledge, facts, and skills pluggable for LLMs. It provides a simple API for storing and 
        querying embeddings with metadata filtering.
        """,
        """
        Azure OpenAI Service provides REST API access to OpenAI's powerful language models including 
        GPT-4, GPT-3.5-Turbo, and Embeddings models. These models can be used for content generation,
        summarization, semantic search, and natural language to code translation.
        """
    ]
    
    print("\n" + "="*80)
    print("Processing sample documents...")
    print("="*80)
    rag.process_documents(sample_documents)
    
    # Example 3: Query the system
    print("\n" + "="*80)
    print("Testing RAG queries...")
    print("="*80)
    
    questions = [
        "What is Pathway?",
        "How does ChromaDB help with LLM applications?",
        "What models are available in Azure OpenAI?"
    ]
    
    for question in questions:
        rag.chat(question)
        print()


if __name__ == "__main__":
    main()
