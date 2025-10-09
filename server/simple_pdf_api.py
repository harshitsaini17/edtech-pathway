#!/usr/bin/env python3
"""
Simple API for PDF Page Extraction
Convenient functions for common use cases
"""

from pdf_page_extractor import PDFPageExtractor
from typing import Optional, List, Dict, Any


# Global extractor instance
_extractor = None


def get_extractor(pdf_directory: str = "./doc") -> PDFPageExtractor:
    """Get or create the global extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = PDFPageExtractor(pdf_directory=pdf_directory)
    return _extractor


# Simple API functions

def get_page(pdf_file: str, page_number: int) -> str:
    """
    Get page content as plain text
    
    Args:
        pdf_file: PDF filename
        page_number: Page number (1-indexed)
        
    Returns:
        Page text content
    """
    extractor = get_extractor()
    result = extractor.extract_page(pdf_file, page_number)
    return result['text']


def get_pages(pdf_file: str, page_numbers: List[int]) -> List[str]:
    """
    Get multiple pages as list of text strings
    
    Args:
        pdf_file: PDF filename
        page_numbers: List of page numbers (1-indexed)
        
    Returns:
        List of page text contents
    """
    extractor = get_extractor()
    results = extractor.extract_pages(pdf_file, page_numbers)
    return [r['text'] for r in results if 'text' in r]


def get_page_range(pdf_file: str, start: int, end: int) -> List[str]:
    """
    Get page range as list of text strings
    
    Args:
        pdf_file: PDF filename
        start: Start page (1-indexed, inclusive)
        end: End page (1-indexed, inclusive)
        
    Returns:
        List of page text contents
    """
    extractor = get_extractor()
    results = extractor.extract_page_range(pdf_file, start, end)
    return [r['text'] for r in results if 'text' in r]


def find_text(pdf_file: str, search_text: str, max_pages: Optional[int] = None) -> List[int]:
    """
    Find pages containing text
    
    Args:
        pdf_file: PDF filename
        search_text: Text to search for
        max_pages: Maximum pages to return
        
    Returns:
        List of page numbers
    """
    extractor = get_extractor()
    return extractor.find_pages_with_text(pdf_file, search_text, max_pages=max_pages)


def get_page_info(pdf_file: str, page_number: int) -> Dict[str, Any]:
    """
    Get detailed page information
    
    Args:
        pdf_file: PDF filename
        page_number: Page number (1-indexed)
        
    Returns:
        Dictionary with page metadata
    """
    extractor = get_extractor()
    return extractor.extract_page(pdf_file, page_number)


def count_pages(pdf_file: str) -> int:
    """
    Get total page count
    
    Args:
        pdf_file: PDF filename
        
    Returns:
        Total number of pages
    """
    extractor = get_extractor()
    return extractor.get_page_count(pdf_file)


def list_pdfs() -> List[str]:
    """
    List available PDF files
    
    Returns:
        List of PDF filenames
    """
    extractor = get_extractor()
    return extractor.list_pdfs()


# Demo
if __name__ == "__main__":
    print("="*80)
    print(" SIMPLE PDF PAGE API - DEMO ")
    print("="*80)
    
    # List PDFs
    print("\n[1] Available PDFs:")
    pdfs = list_pdfs()
    for pdf in pdfs:
        pages = count_pages(pdf)
        print(f"  • {pdf} ({pages} pages)")
    
    # Get single page
    print("\n[2] Get page 232 from book2.pdf:")
    text = get_page("book2.pdf", 232)
    print(f"  Length: {len(text)} chars")
    print(f"  Preview: {text[:200]}...")
    
    # Get multiple pages
    print("\n[3] Get pages 232, 233, 234:")
    texts = get_pages("book2.pdf", [232, 233, 234])
    for i, text in enumerate(texts, start=232):
        print(f"  Page {i}: {len(text)} chars")
    
    # Get page range
    print("\n[4] Get page range 232-234:")
    texts = get_page_range("book2.pdf", 232, 234)
    print(f"  Retrieved {len(texts)} pages")
    
    # Find text
    print("\n[5] Find pages with 'normal':")
    pages = find_text("book2.pdf", "normal", max_pages=5)
    print(f"  Found in pages: {pages}")
    
    # Get page info
    print("\n[6] Get detailed info for page 232:")
    info = get_page_info("book2.pdf", 232)
    print(f"  Page: {info['page_number']}/{info['total_pages']}")
    print(f"  Dimensions: {info['page_width']:.1f} x {info['page_height']:.1f}")
    print(f"  Text length: {info['text_length']} chars")
    
    print("\n" + "="*80)
    print("✅ DEMO COMPLETE")
    print("="*80)
    
    print("\n💡 Quick Usage Examples:")
    print("""
    # Import
    from simple_pdf_api import get_page, get_pages, find_text
    
    # Get single page
    text = get_page("book2.pdf", 232)
    
    # Get multiple pages
    texts = get_pages("book2.pdf", [232, 233, 234])
    
    # Find pages with text
    pages = find_text("book2.pdf", "probability")
    """)
