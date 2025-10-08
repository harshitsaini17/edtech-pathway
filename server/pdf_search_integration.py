"""
PDF Search Integration for LLM
==============================
Simple, clean interface for LLM to search PDF documents.
Ready to use with existing LLM system.

Usage Examples:
    # Basic search
    result = search_pdf("Normal Distribution")
    
    # Search specific PDF
    result = search_pdf("probability", pdf_path="doc/book2.pdf")
    
    # Get specific page
    page_content = get_pdf_page(232)
"""

import os
import sys
from typing import Dict, List, Any, Optional
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_search_tool import PDFSearchTool
from pdf_llm_tools import PDFSearchTools

# Default PDF paths - prioritize statistics book
DEFAULT_PDF_PATHS = [
    "doc/book2.pdf",  # Statistics book
    "doc/book.pdf"    # Fallback book
]

def find_available_pdf() -> Optional[str]:
    """Find the first available PDF file"""
    for pdf_path in DEFAULT_PDF_PATHS:
        if os.path.exists(pdf_path):
            return pdf_path
    return None

def search_pdf(
    query: str, 
    pdf_path: Optional[str] = None,
    max_results: int = 3,
    case_sensitive: bool = False
) -> Dict[str, Any]:
    """
    Simple PDF search function for LLM to call
    
    Args:
        query: Text to search for
        pdf_path: Optional PDF file path
        max_results: Maximum number of results
        case_sensitive: Whether search is case sensitive
        
    Returns:
        Dictionary with search results
    """
    # Use provided path or find default
    pdf_file = pdf_path or find_available_pdf()
    
    if not pdf_file:
        return {
            "success": False,
            "error": "No PDF files found",
            "query": query,
            "results": []
        }
    
    try:
        with PDFSearchTool(pdf_file) as searcher:
            results = searcher.search(
                query=query,
                case_sensitive=case_sensitive,
                max_results=max_results
            )
            
            if not results:
                return {
                    "success": True,
                    "query": query,
                    "pdf_file": os.path.basename(pdf_file),
                    "message": f"No results found for '{query}'",
                    "results": []
                }
            
            # Format results for LLM consumption
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "page": result.page_number,
                    "type": result.match_type,
                    "content": result.content,
                    "context": result.context_info,
                    "confidence": round(result.confidence_score, 2),
                    "matches_on_page": result.match_count_on_page
                })
            
            return {
                "success": True,
                "query": query,
                "pdf_file": os.path.basename(pdf_file),
                "total_matches": results[0].total_matches if results else 0,
                "results_returned": len(results),
                "results": formatted_results
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "results": []
        }

def get_pdf_page(
    page_number: int,
    pdf_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get full content of a specific PDF page
    
    Args:
        page_number: Page number (1-indexed)
        pdf_path: Optional PDF file path
        
    Returns:
        Dictionary with page content
    """
    pdf_file = pdf_path or find_available_pdf()
    
    if not pdf_file:
        return {
            "success": False,
            "error": "No PDF files found",
            "page": page_number,
            "content": ""
        }
    
    try:
        with PDFSearchTool(pdf_file) as searcher:
            if page_number < 1 or page_number > searcher.total_pages:
                return {
                    "success": False,
                    "error": f"Page {page_number} out of range (1-{searcher.total_pages})",
                    "page": page_number,
                    "content": ""
                }
            
            page = searcher.doc[page_number - 1]
            content = searcher._clean_page_text(page.get_text())
            
            return {
                "success": True,
                "page": page_number,
                "total_pages": searcher.total_pages,
                "pdf_file": os.path.basename(pdf_file),
                "content": content,
                "word_count": len(content.split())
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "page": page_number,
            "content": ""
        }

def search_topic(
    topic: str,
    pdf_path: Optional[str] = None,
    include_examples: bool = True,
    include_definitions: bool = True
) -> Dict[str, Any]:
    """
    Enhanced search for educational topics
    
    Args:
        topic: Educational topic to search
        pdf_path: Optional PDF file path
        include_examples: Include examples in search
        include_definitions: Include definitions in search
        
    Returns:
        Dictionary with topic search results
    """
    pdf_file = pdf_path or find_available_pdf()
    
    if not pdf_file:
        return {
            "success": False,
            "error": "No PDF files found",
            "topic": topic,
            "results": []
        }
    
    try:
        tools = PDFSearchTools(default_pdf_path=pdf_file)
        result = tools.search_pdf_by_topic(
            topic=topic,
            include_examples=include_examples,
            include_definitions=include_definitions,
            pdf_path=pdf_file
        )
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "topic": topic,
            "results": []
        }

# Simple text-based functions for easy LLM integration
def search_pdf_simple(query: str, max_results: int = 3) -> str:
    """
    Simple text-based search for LLM
    Returns formatted string instead of dictionary
    """
    result = search_pdf(query, max_results=max_results)
    
    if not result["success"]:
        return f"Search failed: {result['error']}"
    
    if not result["results"]:
        return f"No results found for '{query}'"
    
    output = [f"Found {result['results_returned']} results for '{query}' in {result['pdf_file']}:\n"]
    
    for i, res in enumerate(result["results"], 1):
        output.append(f"Result {i} (Page {res['page']}):")
        output.append(f"Type: {res['type']} (Confidence: {res['confidence']})")
        output.append(f"Content: {res['content'][:300]}...")
        output.append("-" * 50)
    
    return "\n".join(output)

def get_pdf_page_simple(page_number: int) -> str:
    """
    Simple text-based page retrieval for LLM
    """
    result = get_pdf_page(page_number)
    
    if not result["success"]:
        return f"Error retrieving page {page_number}: {result['error']}"
    
    return f"Page {page_number} of {result['pdf_file']}:\n\n{result['content']}"

# Tool definitions for function calling systems
PDF_SEARCH_TOOLS = [
    {
        "name": "search_pdf",
        "description": "Search for text in PDF documents. Returns full pages for multiple matches or paragraphs for single matches.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text to search for in the PDF"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 3)",
                    "default": 3
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Whether to perform case-sensitive search (default: false)",
                    "default": False
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_pdf_page",
        "description": "Retrieve the full content of a specific page from the PDF",
        "parameters": {
            "type": "object",
            "properties": {
                "page_number": {
                    "type": "integer",
                    "description": "Page number to retrieve (1-indexed)"
                }
            },
            "required": ["page_number"]
        }
    },
    {
        "name": "search_topic",
        "description": "Search for educational topics with enhanced academic context",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Educational topic or concept to search for"
                },
                "include_examples": {
                    "type": "boolean",
                    "description": "Whether to include examples and problems (default: true)",
                    "default": True
                },
                "include_definitions": {
                    "type": "boolean",
                    "description": "Whether to prioritize definitions (default: true)",
                    "default": True
                }
            },
            "required": ["topic"]
        }
    }
]

if __name__ == "__main__":
    # Demo the simple functions
    print("=== PDF Search Integration Demo ===\n")
    
    # Test basic search
    print("1. Testing basic search for 'Normal Distribution':")
    result = search_pdf_simple("Normal Distribution", max_results=2)
    print(result[:500] + "..." if len(result) > 500 else result)
    
    print("\n" + "="*50 + "\n")
    
    # Test page retrieval
    print("2. Testing page retrieval (page 232):")
    page_content = get_pdf_page_simple(232)
    print(page_content[:400] + "..." if len(page_content) > 400 else page_content)
    
    print("\n" + "="*50 + "\n")
    
    # Test topic search
    print("3. Testing topic search for 'probability':")
    topic_result = search_topic("probability")
    if topic_result["success"] and topic_result["results"]:
        print(f"Found {len(topic_result['results'])} results for probability")
        first_result = topic_result["results"][0]
        print(f"First result: Page {first_result['page_number']}")
        print(f"Content preview: {first_result['content'][:200]}...")
    else:
        print(f"Topic search failed or no results: {topic_result.get('error', 'No results')}")