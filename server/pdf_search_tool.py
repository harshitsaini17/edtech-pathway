"""
PDF Search Tool
===============
A comprehensive tool for searching text in PDF documents with intelligent context extraction.
Returns full pages when multiple matches are found, or specific paragraphs for single matches.

Features:
- Smart text search with fuzzy matching
- Context-aware result extraction
- Full page vs paragraph detection
- Page number and location tracking
- Optimized for educational content

Usage:
    from pdf_search_tool import PDFSearchTool
    
    searcher = PDFSearchTool("path/to/document.pdf")
    results = searcher.search("Normal Distribution")
"""

import fitz  # PyMuPDF
import re
import os
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class SearchResult:
    """Data class for search results"""
    query: str
    page_number: int
    match_type: str  # "paragraph" or "full_page"
    content: str
    context_info: str
    match_count_on_page: int
    total_matches: int
    confidence_score: float

class PDFSearchTool:
    """
    Advanced PDF search tool with intelligent context extraction
    """
    
    def __init__(self, pdf_path: str):
        """
        Initialize the PDF search tool
        
        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = pdf_path
        self.pdf_filename = os.path.basename(pdf_path).replace('.pdf', '')
        
        try:
            self.doc = fitz.open(pdf_path)
            self.total_pages = len(self.doc)
        except Exception as e:
            raise ValueError(f"Could not open PDF file: {e}")
    
    def search(
        self, 
        query: str, 
        case_sensitive: bool = False,
        fuzzy_match: bool = True,
        context_lines: int = 3,
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Search for text in the PDF document
        
        Args:
            query: Text to search for
            case_sensitive: Whether to perform case-sensitive search
            fuzzy_match: Whether to allow partial word matches
            context_lines: Number of lines to include around matches for paragraph extraction
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        if not query.strip():
            return []
        
        search_results = []
        total_matches = 0
        
        # First pass: count total matches across all pages
        for page_num in range(self.total_pages):
            page = self.doc[page_num]
            page_text = page.get_text()
            matches = self._find_matches(page_text, query, case_sensitive, fuzzy_match)
            total_matches += len(matches)
        
        # Second pass: extract content based on match density
        for page_num in range(self.total_pages):
            page = self.doc[page_num]
            page_text = page.get_text()
            matches = self._find_matches(page_text, query, case_sensitive, fuzzy_match)
            
            if not matches:
                continue
            
            match_count_on_page = len(matches)
            
            # Determine if we should return full page or paragraph
            if match_count_on_page > 2:  # Multiple matches - return full page
                result = SearchResult(
                    query=query,
                    page_number=page_num + 1,
                    match_type="full_page",
                    content=self._clean_page_text(page_text),
                    context_info=f"Page {page_num + 1} contains {match_count_on_page} matches of '{query}'",
                    match_count_on_page=match_count_on_page,
                    total_matches=total_matches,
                    confidence_score=self._calculate_confidence(matches, page_text)
                )
                search_results.append(result)
            else:  # Single or few matches - return paragraph
                for match in matches:
                    paragraph = self._extract_paragraph(page_text, match, context_lines)
                    result = SearchResult(
                        query=query,
                        page_number=page_num + 1,
                        match_type="paragraph",
                        content=paragraph,
                        context_info=f"Found in paragraph on page {page_num + 1}",
                        match_count_on_page=match_count_on_page,
                        total_matches=total_matches,
                        confidence_score=self._calculate_confidence([match], paragraph)
                    )
                    search_results.append(result)
            
            if len(search_results) >= max_results:
                break
        
        # Sort by confidence score and page number
        search_results.sort(key=lambda x: (x.confidence_score, x.page_number), reverse=True)
        
        return search_results[:max_results]
    
    def _find_matches(
        self, 
        text: str, 
        query: str, 
        case_sensitive: bool, 
        fuzzy_match: bool
    ) -> List[Tuple[int, int, str]]:
        """
        Find all matches of the query in the text
        
        Returns:
            List of tuples (start_pos, end_pos, matched_text)
        """
        matches = []
        
        if not case_sensitive:
            search_text = text.lower()
            search_query = query.lower()
        else:
            search_text = text
            search_query = query
        
        if fuzzy_match:
            # Create a flexible pattern that allows for minor variations
            pattern_parts = []
            for word in search_query.split():
                # Allow for minor character variations and optional word boundaries
                escaped_word = re.escape(word)
                pattern_parts.append(f"\\b{escaped_word}\\b")
            
            pattern = r'\s+'.join(pattern_parts)
            
            try:
                for match in re.finditer(pattern, search_text, re.IGNORECASE if not case_sensitive else 0):
                    original_match = text[match.start():match.end()]
                    matches.append((match.start(), match.end(), original_match))
            except re.error:
                # Fallback to simple string search if regex fails
                start = 0
                while True:
                    pos = search_text.find(search_query, start)
                    if pos == -1:
                        break
                    original_match = text[pos:pos + len(query)]
                    matches.append((pos, pos + len(query), original_match))
                    start = pos + 1
        else:
            # Exact string matching
            start = 0
            while True:
                pos = search_text.find(search_query, start)
                if pos == -1:
                    break
                original_match = text[pos:pos + len(query)]
                matches.append((pos, pos + len(query), original_match))
                start = pos + 1
        
        return matches
    
    def _extract_paragraph(
        self, 
        page_text: str, 
        match: Tuple[int, int, str], 
        context_lines: int
    ) -> str:
        """
        Extract paragraph around a match with context
        """
        start_pos, end_pos, _ = match
        
        # Split text into lines
        lines = page_text.split('\n')
        
        # Find the line containing the match
        current_pos = 0
        match_line_idx = -1
        
        for i, line in enumerate(lines):
            line_end = current_pos + len(line) + 1  # +1 for newline
            if current_pos <= start_pos < line_end:
                match_line_idx = i
                break
            current_pos = line_end
        
        if match_line_idx == -1:
            # Fallback: extract text around the match position
            context_start = max(0, start_pos - 200)
            context_end = min(len(page_text), end_pos + 200)
            return page_text[context_start:context_end].strip()
        
        # Extract context lines around the match
        start_line = max(0, match_line_idx - context_lines)
        end_line = min(len(lines), match_line_idx + context_lines + 1)
        
        paragraph_lines = lines[start_line:end_line]
        paragraph = '\n'.join(paragraph_lines).strip()
        
        # Clean up the paragraph
        paragraph = self._clean_text(paragraph)
        
        return paragraph
    
    def _clean_page_text(self, text: str) -> str:
        """Clean and format page text for better readability"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove page headers/footers (common patterns)
        text = re.sub(r'^.*Chapter \d+.*\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def _clean_text(self, text: str) -> str:
        """Clean text for better readability"""
        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove common artifacts
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)  # Page numbers
        text = re.sub(r'^\s*Chapter.*$', '', text, flags=re.MULTILINE)  # Chapter headers
        
        return text.strip()
    
    def _calculate_confidence(self, matches: List[Tuple[int, int, str]], context: str) -> float:
        """
        Calculate confidence score for search results
        
        Args:
            matches: List of matches found
            context: The text context containing the matches
            
        Returns:
            Confidence score between 0 and 1
        """
        if not matches:
            return 0.0
        
        base_score = 0.5
        
        # Boost score based on number of matches
        match_bonus = min(0.3, len(matches) * 0.1)
        
        # Boost score based on context quality (presence of educational indicators)
        educational_indicators = [
            'definition', 'theorem', 'example', 'proof', 'lemma',
            'section', 'chapter', 'figure', 'table', 'equation',
            'problem', 'solution', 'exercise', 'note'
        ]
        
        context_lower = context.lower()
        indicator_count = sum(1 for indicator in educational_indicators if indicator in context_lower)
        context_bonus = min(0.2, indicator_count * 0.05)
        
        # Penalty for very short context
        length_penalty = 0.0 if len(context) > 100 else 0.1
        
        final_score = base_score + match_bonus + context_bonus - length_penalty
        return min(1.0, max(0.0, final_score))
    
    def search_and_format(
        self, 
        query: str, 
        format_type: str = "json",
        **kwargs
    ) -> Union[str, Dict, List[Dict]]:
        """
        Search and return results in specified format
        
        Args:
            query: Search query
            format_type: "json", "text", or "dict"
            **kwargs: Additional arguments passed to search()
            
        Returns:
            Formatted search results
        """
        results = self.search(query, **kwargs)
        
        if format_type == "json":
            return json.dumps([{
                "query": r.query,
                "page_number": r.page_number,
                "match_type": r.match_type,
                "content": r.content,
                "context_info": r.context_info,
                "match_count_on_page": r.match_count_on_page,
                "total_matches": r.total_matches,
                "confidence_score": r.confidence_score
            } for r in results], indent=2)
        
        elif format_type == "text":
            formatted_results = []
            for r in results:
                formatted_results.append(
                    f"=== Search Result (Page {r.page_number}) ===\n"
                    f"Query: {r.query}\n"
                    f"Type: {r.match_type}\n"
                    f"Context: {r.context_info}\n"
                    f"Confidence: {r.confidence_score:.2f}\n"
                    f"Content:\n{r.content}\n"
                    f"{'='*50}\n"
                )
            return '\n'.join(formatted_results)
        
        elif format_type == "dict":
            return [{
                "query": r.query,
                "page_number": r.page_number,
                "match_type": r.match_type,
                "content": r.content,
                "context_info": r.context_info,
                "match_count_on_page": r.match_count_on_page,
                "total_matches": r.total_matches,
                "confidence_score": r.confidence_score
            } for r in results]
        
        else:
            raise ValueError(f"Unsupported format_type: {format_type}")
    
    def close(self):
        """Close the PDF document"""
        if hasattr(self, 'doc'):
            self.doc.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# LLM-callable function wrapper
def search_pdf_content(
    pdf_path: str,
    query: str,
    case_sensitive: bool = False,
    fuzzy_match: bool = True,
    max_results: int = 5
) -> List[Dict]:
    """
    LLM-callable function to search PDF content
    
    Args:
        pdf_path: Path to the PDF file
        query: Text to search for
        case_sensitive: Whether to perform case-sensitive search
        fuzzy_match: Whether to allow partial word matches
        max_results: Maximum number of results to return
        
    Returns:
        List of dictionaries containing search results
    """
    try:
        with PDFSearchTool(pdf_path) as searcher:
            results = searcher.search(
                query=query,
                case_sensitive=case_sensitive,
                fuzzy_match=fuzzy_match,
                max_results=max_results
            )
            
            return [{
                "query": r.query,
                "page_number": r.page_number,
                "match_type": r.match_type,
                "content": r.content,
                "context_info": r.context_info,
                "match_count_on_page": r.match_count_on_page,
                "total_matches": r.total_matches,
                "confidence_score": r.confidence_score
            } for r in results]
    
    except Exception as e:
        return [{
            "error": f"Search failed: {str(e)}",
            "query": query,
            "page_number": 0,
            "match_type": "error",
            "content": "",
            "context_info": f"Error occurred while searching for '{query}'",
            "match_count_on_page": 0,
            "total_matches": 0,
            "confidence_score": 0.0
        }]

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python pdf_search_tool.py <pdf_path> <search_query>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    query = sys.argv[2]
    
    try:
        with PDFSearchTool(pdf_path) as searcher:
            results = searcher.search(query)
            
            if not results:
                print(f"No results found for '{query}'")
                sys.exit(0)
            
            print(f"Found {len(results)} results for '{query}':")
            print("=" * 60)
            
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"Page: {result.page_number}")
                print(f"Type: {result.match_type}")
                print(f"Matches on page: {result.match_count_on_page}")
                print(f"Total matches: {result.total_matches}")
                print(f"Confidence: {result.confidence_score:.2f}")
                print(f"Context: {result.context_info}")
                print("\nContent:")
                print("-" * 40)
                print(result.content)
                print("-" * 40)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)