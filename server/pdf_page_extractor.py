#!/usr/bin/env python3
"""
PDF Page Extractor Tool
Extract content from specific pages in PDF files
"""

import os
from typing import Optional, Union, List, Dict, Any
import fitz  # PyMuPDF


class PDFPageExtractor:
    """Tool to extract content from specific pages in PDF files"""
    
    def __init__(self, pdf_directory: str = "./doc"):
        """
        Initialize PDF Page Extractor
        
        Args:
            pdf_directory: Directory containing PDF files
        """
        self.pdf_directory = pdf_directory
        
    def list_pdfs(self) -> List[str]:
        """List all PDF files in the directory"""
        if not os.path.exists(self.pdf_directory):
            return []
        return [f for f in os.listdir(self.pdf_directory) if f.endswith('.pdf')]
    
    def get_page_count(self, pdf_file: str) -> int:
        """
        Get total number of pages in a PDF
        
        Args:
            pdf_file: Name of the PDF file
            
        Returns:
            Total number of pages
        """
        pdf_path = os.path.join(self.pdf_directory, pdf_file)
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
        
        return page_count
    
    def extract_page(self, pdf_file: str, page_number: int) -> Dict[str, Any]:
        """
        Extract content from a specific page
        
        Args:
            pdf_file: Name of the PDF file
            page_number: Page number to extract (1-indexed)
            
        Returns:
            Dictionary with page content and metadata
        """
        pdf_path = os.path.join(self.pdf_directory, pdf_file)
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Validate page number (1-indexed)
        if page_number < 1 or page_number > total_pages:
            doc.close()
            raise ValueError(f"Invalid page number {page_number}. PDF has {total_pages} pages (1-{total_pages})")
        
        # Get page (convert to 0-indexed)
        page = doc[page_number - 1]
        
        # Extract text
        text = page.get_text()
        
        # Get page dimensions
        rect = page.rect
        width = rect.width
        height = rect.height
        
        doc.close()
        
        return {
            "pdf_file": pdf_file,
            "page_number": page_number,
            "total_pages": total_pages,
            "text": text,
            "text_length": len(text),
            "page_width": width,
            "page_height": height,
            "has_content": bool(text.strip())
        }
    
    def extract_pages(self, pdf_file: str, page_numbers: List[int]) -> List[Dict[str, Any]]:
        """
        Extract content from multiple pages
        
        Args:
            pdf_file: Name of the PDF file
            page_numbers: List of page numbers to extract (1-indexed)
            
        Returns:
            List of dictionaries with page content and metadata
        """
        results = []
        
        for page_num in page_numbers:
            try:
                result = self.extract_page(pdf_file, page_num)
                results.append(result)
            except Exception as e:
                results.append({
                    "pdf_file": pdf_file,
                    "page_number": page_num,
                    "error": str(e),
                    "status": "failed"
                })
        
        return results
    
    def extract_page_range(self, pdf_file: str, start_page: int, end_page: int) -> List[Dict[str, Any]]:
        """
        Extract content from a range of pages
        
        Args:
            pdf_file: Name of the PDF file
            start_page: Starting page number (1-indexed, inclusive)
            end_page: Ending page number (1-indexed, inclusive)
            
        Returns:
            List of dictionaries with page content and metadata
        """
        page_numbers = list(range(start_page, end_page + 1))
        return self.extract_pages(pdf_file, page_numbers)
    
    def search_in_page(self, pdf_file: str, page_number: int, search_text: str, 
                       case_sensitive: bool = False) -> Dict[str, Any]:
        """
        Search for text in a specific page
        
        Args:
            pdf_file: Name of the PDF file
            page_number: Page number to search (1-indexed)
            search_text: Text to search for
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            Dictionary with search results
        """
        page_data = self.extract_page(pdf_file, page_number)
        
        text = page_data['text']
        search_in = text if case_sensitive else text.lower()
        search_for = search_text if case_sensitive else search_text.lower()
        
        # Find all occurrences
        occurrences = []
        start = 0
        while True:
            pos = search_in.find(search_for, start)
            if pos == -1:
                break
            occurrences.append(pos)
            start = pos + 1
        
        return {
            **page_data,
            "search_text": search_text,
            "found": len(occurrences) > 0,
            "occurrences": len(occurrences),
            "positions": occurrences,
            "case_sensitive": case_sensitive
        }
    
    def find_pages_with_text(self, pdf_file: str, search_text: str, 
                            case_sensitive: bool = False, 
                            max_pages: Optional[int] = None) -> List[int]:
        """
        Find all pages containing specific text
        
        Args:
            pdf_file: Name of the PDF file
            search_text: Text to search for
            case_sensitive: Whether search should be case sensitive
            max_pages: Maximum number of pages to return (None for all)
            
        Returns:
            List of page numbers containing the text
        """
        pdf_path = os.path.join(self.pdf_directory, pdf_file)
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        matching_pages = []
        
        search_for = search_text if case_sensitive else search_text.lower()
        
        for page_num in range(1, len(doc) + 1):
            page = doc[page_num - 1]
            text = page.get_text()
            search_in = text if case_sensitive else text.lower()
            
            if search_for in search_in:
                matching_pages.append(page_num)
                
                if max_pages and len(matching_pages) >= max_pages:
                    break
        
        doc.close()
        
        return matching_pages


def main():
    """Demo and test the PDF Page Extractor"""
    print("="*80)
    print(" PDF PAGE EXTRACTOR TOOL - DEMO ")
    print("="*80)
    
    # Initialize extractor
    extractor = PDFPageExtractor(pdf_directory="./doc")
    
    # List available PDFs
    print("\n[1] Available PDFs:")
    pdfs = extractor.list_pdfs()
    for i, pdf in enumerate(pdfs, 1):
        page_count = extractor.get_page_count(pdf)
        print(f"  {i}. {pdf} ({page_count} pages)")
    
    if not pdfs:
        print("  No PDFs found in ./doc directory")
        return
    
    # Use book2.pdf for demo
    pdf_file = "book2.pdf"
    
    print(f"\n[2] Extracting specific page from {pdf_file}")
    print("="*80)
    
    # Extract page 232 (where NORMAL RANDOM VARIABLES content is)
    page_data = extractor.extract_page(pdf_file, 232)
    
    print(f"\n📄 Page Information:")
    print(f"  PDF: {page_data['pdf_file']}")
    print(f"  Page: {page_data['page_number']} of {page_data['total_pages']}")
    print(f"  Text Length: {page_data['text_length']} characters")
    print(f"  Dimensions: {page_data['page_width']:.1f} x {page_data['page_height']:.1f}")
    print(f"  Has Content: {page_data['has_content']}")
    
    print(f"\n📝 Page Content (first 500 chars):")
    print("-"*80)
    print(page_data['text'][:500])
    if len(page_data['text']) > 500:
        print("...")
    
    # Extract multiple pages
    print(f"\n[3] Extracting multiple pages (232-234)")
    print("="*80)
    
    pages_data = extractor.extract_page_range(pdf_file, 232, 234)
    
    for page in pages_data:
        if 'error' not in page:
            print(f"\n📄 Page {page['page_number']}: {page['text_length']} characters")
            print(f"   Preview: {page['text'][:100]}...")
    
    # Search for text in a page
    print(f"\n[4] Searching for 'NORMAL RANDOM VARIABLES' in page 232")
    print("="*80)
    
    search_result = extractor.search_in_page(pdf_file, 232, "NORMAL RANDOM VARIABLES")
    
    print(f"\n🔍 Search Results:")
    print(f"  Search Text: '{search_result['search_text']}'")
    print(f"  Found: {search_result['found']}")
    print(f"  Occurrences: {search_result['occurrences']}")
    if search_result['found']:
        print(f"  Positions: {search_result['positions']}")
    
    # Find all pages with specific text
    print(f"\n[5] Finding all pages containing 'normal'")
    print("="*80)
    
    matching_pages = extractor.find_pages_with_text(pdf_file, "normal", max_pages=10)
    
    print(f"\n📚 Found in {len(matching_pages)} pages (showing first 10):")
    print(f"   Pages: {matching_pages}")
    
    print("\n" + "="*80)
    print("✅ DEMO COMPLETE")
    print("="*80)
    
    print("\n💡 Usage Examples:")
    print("""
    from pdf_page_extractor import PDFPageExtractor
    
    # Initialize
    extractor = PDFPageExtractor(pdf_directory="./doc")
    
    # Extract single page
    page_data = extractor.extract_page("book2.pdf", 232)
    print(page_data['text'])
    
    # Extract multiple pages
    pages = extractor.extract_pages("book2.pdf", [232, 233, 234])
    
    # Extract page range
    pages = extractor.extract_page_range("book2.pdf", 232, 240)
    
    # Search in page
    result = extractor.search_in_page("book2.pdf", 232, "normal")
    
    # Find pages with text
    pages = extractor.find_pages_with_text("book2.pdf", "probability")
    """)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
