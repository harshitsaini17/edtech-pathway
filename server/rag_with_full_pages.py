#!/usr/bin/env python3
"""
Example: Integrate PDF Page Extractor with RAG Tool
Query RAG and retrieve full page content for results
"""

from pathway_rag_tool import PathwayRAGTool
from pdf_page_extractor import PDFPageExtractor
import json
from datetime import datetime


def query_and_get_full_pages(topic: str, top_k: int = 5):
    """
    Query RAG for a topic and retrieve full page content for matching chunks
    
    Args:
        topic: Topic to search for
        top_k: Number of top results to return
        
    Returns:
        List of results with full page content
    """
    print("="*80)
    print(f" QUERY RAG AND RETRIEVE FULL PAGE CONTENT ")
    print("="*80)
    
    # Initialize tools
    print("\n[1] Initializing tools...")
    rag = PathwayRAGTool()
    extractor = PDFPageExtractor(pdf_directory="./doc")
    
    print(f"   ✓ RAG Tool initialized")
    print(f"   ✓ Page Extractor initialized")
    print(f"   📊 Total chunks in database: {rag.vector_store.get_collection_count()}")
    
    # Query RAG
    print(f"\n[2] Querying RAG for: '{topic}' (top {top_k})")
    query_result = rag.query(topic, top_k=top_k)
    chunks = query_result.get('retrieved_chunks', [])
    
    print(f"   ✓ Found {len(chunks)} relevant chunks")
    
    # Get full page content for each chunk
    print(f"\n[3] Retrieving full page content for each chunk")
    print("="*80)
    
    results = []
    
    for i, chunk in enumerate(chunks, 1):
        metadata = chunk['metadata']
        page_number = metadata.get('page_number')
        source_file = metadata.get('source_file', metadata.get('filename'))
        
        print(f"\n{'─'*80}")
        print(f"Chunk #{i}")
        print(f"  Relevance Score: {chunk['relevance_score']:.4f}")
        print(f"  Source: {source_file}")
        print(f"  Page: {page_number}")
        print(f"  Chunk Text Length: {len(chunk['text'])} chars")
        
        # Extract full page content
        if page_number and source_file:
            try:
                page_data = extractor.extract_page(source_file, page_number)
                print(f"  ✓ Retrieved full page content: {page_data['text_length']} chars")
                
                # Combine RAG chunk info with full page content
                result = {
                    "chunk_number": i,
                    "relevance_score": chunk['relevance_score'],
                    "source_file": source_file,
                    "page_number": page_number,
                    "total_pages": page_data['total_pages'],
                    "chunk_metadata": metadata,
                    "chunk_text": chunk['text'],
                    "chunk_text_length": len(chunk['text']),
                    "full_page_content": page_data['text'],
                    "full_page_length": page_data['text_length'],
                    "page_dimensions": {
                        "width": page_data['page_width'],
                        "height": page_data['page_height']
                    }
                }
                
                results.append(result)
                
            except Exception as e:
                print(f"  ✗ Error retrieving page: {str(e)}")
                results.append({
                    "chunk_number": i,
                    "error": str(e),
                    "chunk_text": chunk['text'],
                    "metadata": metadata
                })
        else:
            print(f"  ⚠ No page number available for this chunk")
            results.append({
                "chunk_number": i,
                "warning": "No page number available",
                "chunk_text": chunk['text'],
                "metadata": metadata
            })
    
    return results


def display_results(results: list, show_full_content: bool = False):
    """Display results in a formatted way"""
    print("\n" + "="*80)
    print(" RESULTS SUMMARY ")
    print("="*80)
    
    for result in results:
        if 'error' in result or 'warning' in result:
            continue
            
        print(f"\n{'─'*80}")
        print(f"📄 Chunk #{result['chunk_number']} - Page {result['page_number']}")
        print(f"   Relevance: {result['relevance_score']:.4f}")
        print(f"   Source: {result['source_file']}")
        print(f"   Chunk Length: {result['chunk_text_length']} chars")
        print(f"   Full Page Length: {result['full_page_length']} chars")
        print(f"   Page Dimensions: {result['page_dimensions']['width']:.1f} x {result['page_dimensions']['height']:.1f}")
        
        if show_full_content:
            print(f"\n   📝 Chunk Content:")
            print(f"   {'-'*76}")
            for line in result['chunk_text'][:300].split('\n'):
                print(f"   {line}")
            if len(result['chunk_text']) > 300:
                print(f"   ...")
            
            print(f"\n   📖 Full Page Content:")
            print(f"   {'-'*76}")
            for line in result['full_page_content'][:500].split('\n'):
                print(f"   {line}")
            if len(result['full_page_content']) > 500:
                print(f"   ...")


def save_results(results: list, topic: str, output_dir: str = "./output"):
    """Save results to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rag_with_full_pages_{timestamp}.json"
    filepath = f"{output_dir}/{filename}"
    
    data = {
        "topic": topic,
        "timestamp": timestamp,
        "total_results": len(results),
        "results": results
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filepath


def main():
    """Main demo function"""
    print("="*80)
    print(" RAG + FULL PAGE CONTENT EXTRACTION ")
    print("="*80)
    
    # Query for a topic
    topic = "NORMAL RANDOM VARIABLES"
    top_k = 3  # Get top 3 results
    
    print(f"\n🔍 Query Topic: '{topic}'")
    print(f"📊 Top K Results: {top_k}")
    
    # Get results with full page content
    results = query_and_get_full_pages(topic, top_k=top_k)
    
    # Display results
    display_results(results, show_full_content=True)
    
    # Save results
    print("\n" + "="*80)
    print(" SAVING RESULTS ")
    print("="*80)
    
    filepath = save_results(results, topic)
    print(f"\n✓ Results saved to: {filepath}")
    
    print("\n" + "="*80)
    print("✅ COMPLETE")
    print("="*80)
    
    print("\n💡 Key Benefits:")
    print("   1. ✓ RAG retrieves most relevant chunks based on semantic search")
    print("   2. ✓ Page extractor provides full page context")
    print("   3. ✓ Combined view shows both focused chunk and surrounding content")
    print("   4. ✓ Page numbers enable easy reference to original PDF")
    
    print("\n📚 Use Cases:")
    print("   • Study material extraction with full context")
    print("   • Citation and reference verification")
    print("   • Content review and validation")
    print("   • Building comprehensive topic summaries")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
