#!/usr/bin/env python3
"""
Process PDFs with rate limiting and batch processing
Handles Azure OpenAI API rate limits gracefully
"""

import time
from pathway_rag_tool import PathwayRAGTool, RAGConfig
from langchain_openai import AzureOpenAIEmbeddings
import fitz  # PyMuPDF


def process_pdf_with_batching(pdf_path, batch_size=50, delay_between_batches=2):
    """
    Process a single PDF with batching to handle rate limits
    
    Args:
        pdf_path: Path to the PDF file
        batch_size: Number of chunks to process in each batch
        delay_between_batches: Seconds to wait between batches
    """
    print(f"\n{'='*80}")
    print(f"Processing: {pdf_path}")
    print('='*80)
    
    # Initialize RAG with smaller batch processing
    rag = PathwayRAGTool()
    
    # Check if already processed
    filename = pdf_path.split('/')[-1]
    existing_chunks = rag.vector_store.get_documents_by_source(filename)
    
    if existing_chunks:
        print(f"✓ {filename} already indexed with {len(existing_chunks)} chunks")
        print("  Skipping to avoid duplicates.")
        return {"status": "skipped", "filename": filename, "chunks": len(existing_chunks)}
    
    # Extract text from PDF
    print(f"Extracting text from {filename}...")
    doc = fitz.open(pdf_path)
    text = ""
    page_count = len(doc)
    
    for page_num, page in enumerate(doc, 1):
        text += page.get_text()
        if page_num % 50 == 0:
            print(f"  Extracted {page_num}/{page_count} pages...")
    
    doc.close()
    print(f"✓ Extracted text from {page_count} pages")
    
    if not text.strip():
        print(f"⚠ No text extracted from {filename}")
        return {"status": "failed", "filename": filename, "reason": "no_text"}
    
    # Chunk the text
    print(f"\nChunking text...")
    chunks = rag.chunk_text(text)
    print(f"✓ Created {len(chunks)} chunks")
    
    # Process in batches
    print(f"\nProcessing chunks in batches of {batch_size}...")
    total_added = 0
    
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        print(f"\n  Batch {batch_num}/{total_batches} ({len(batch_chunks)} chunks)...")
        
        try:
            # Generate embeddings for this batch
            embeddings = rag.embeddings.embed_documents(batch_chunks)
            
            # Prepare metadata and IDs
            batch_metadatas = []
            batch_ids = []
            
            import hashlib
            file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
            
            for chunk_idx in range(len(batch_chunks)):
                global_idx = i + chunk_idx
                
                metadata = {
                    "source": "pdf",
                    "source_file": filename,
                    "chunk": global_idx,
                    "chunk_total": len(chunks),
                    "pages": page_count
                }
                batch_metadatas.append(metadata)
                batch_ids.append(f"{file_hash}_chunk_{global_idx}")
            
            # Add to ChromaDB
            added, skipped = rag.vector_store.add_documents(
                documents=batch_chunks,
                embeddings=embeddings,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
            
            total_added += added
            print(f"    ✓ Added {added} chunks (skipped {skipped} duplicates)")
            
            # Wait between batches to avoid rate limiting
            if i + batch_size < len(chunks):
                print(f"    ⏳ Waiting {delay_between_batches}s before next batch...")
                time.sleep(delay_between_batches)
                
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                print(f"    ⚠ Rate limit hit! Waiting 60 seconds...")
                time.sleep(60)
                
                # Retry this batch
                print(f"    ↻ Retrying batch {batch_num}...")
                try:
                    embeddings = rag.embeddings.embed_documents(batch_chunks)
                    added, skipped = rag.vector_store.add_documents(
                        documents=batch_chunks,
                        embeddings=embeddings,
                        metadatas=batch_metadatas,
                        ids=batch_ids
                    )
                    total_added += added
                    print(f"    ✓ Added {added} chunks on retry")
                except Exception as retry_error:
                    print(f"    ✗ Retry failed: {str(retry_error)}")
                    raise
            else:
                print(f"    ✗ Error: {str(e)}")
                raise
    
    print(f"\n{'─'*80}")
    print(f"✓ Successfully processed {filename}")
    print(f"  Total chunks added: {total_added}")
    print(f"  Total in database: {rag.vector_store.get_collection_count()}")
    
    return {
        "status": "success",
        "filename": filename,
        "chunks_added": total_added,
        "total_chunks": len(chunks),
        "pages": page_count
    }


def process_books_directory(directory="./doc", batch_size=50, delay=2):
    """Process all PDFs in the directory with rate limiting"""
    import os
    
    print("="*80)
    print(" PDF PROCESSING WITH RATE LIMIT HANDLING ")
    print("="*80)
    print(f"\nSettings:")
    print(f"  - Batch size: {batch_size} chunks")
    print(f"  - Delay between batches: {delay}s")
    print(f"  - Directory: {directory}")
    
    pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"\n⚠ No PDF files found in {directory}")
        return
    
    print(f"\nFound {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        print(f"  - {pdf}")
    
    results = []
    
    for idx, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(directory, pdf_file)
        
        print(f"\n{'='*80}")
        print(f"Processing PDF {idx}/{len(pdf_files)}: {pdf_file}")
        print('='*80)
        
        try:
            result = process_pdf_with_batching(pdf_path, batch_size, delay)
            results.append(result)
            
            # Wait between PDFs
            if idx < len(pdf_files):
                print(f"\n⏳ Waiting 5s before next PDF...")
                time.sleep(5)
                
        except Exception as e:
            print(f"\n✗ Failed to process {pdf_file}: {str(e)}")
            results.append({
                "status": "error",
                "filename": pdf_file,
                "error": str(e)
            })
    
    # Summary
    print(f"\n{'='*80}")
    print(" PROCESSING SUMMARY ")
    print('='*80)
    
    success = [r for r in results if r['status'] == 'success']
    skipped = [r for r in results if r['status'] == 'skipped']
    failed = [r for r in results if r['status'] in ['error', 'failed']]
    
    print(f"\n✓ Successfully processed: {len(success)} PDF(s)")
    for r in success:
        print(f"    - {r['filename']}: {r['chunks_added']} chunks added")
    
    print(f"\n⊙ Skipped (already exists): {len(skipped)} PDF(s)")
    for r in skipped:
        print(f"    - {r['filename']}: {r.get('chunks', 0)} chunks")
    
    print(f"\n✗ Failed: {len(failed)} PDF(s)")
    for r in failed:
        print(f"    - {r['filename']}")
    
    print("\n" + "="*80)
    
    return results


def main():
    """Main function"""
    import sys
    
    # Parse command line arguments
    batch_size = 50  # Default batch size
    delay = 2  # Default delay
    
    if len(sys.argv) > 1:
        try:
            batch_size = int(sys.argv[1])
        except:
            pass
    
    if len(sys.argv) > 2:
        try:
            delay = int(sys.argv[2])
        except:
            pass
    
    try:
        print("\n📚 Starting PDF processing with rate limit handling...")
        print(f"💡 Tip: Adjust batch size and delay if you hit rate limits")
        print(f"   Usage: python3 process_pdfs_with_batching.py [batch_size] [delay]")
        print(f"   Example: python3 process_pdfs_with_batching.py 25 3")
        
        results = process_books_directory(batch_size=batch_size, delay=delay)
        
        print("\n✅ Processing complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
