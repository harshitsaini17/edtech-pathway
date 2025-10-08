"""
LLM-Integrated PDF Search Tools
===============================
Tools that can be called by LLM systems to search and extract content from PDF documents.
Integrates with the existing LLM.py infrastructure.

Features:
- LLM-callable search functions
- Function definitions for tool calling
- Integration with existing Azure LLM system
- Structured outputs for LLM consumption

Usage:
    from pdf_llm_tools import PDFSearchTools
    
    # Initialize with LLM
    tools = PDFSearchTools(llm_instance)
    
    # Register tools with LLM
    tools.register_with_llm()
"""

import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import os
from pdf_search_tool import PDFSearchTool, search_pdf_content

class PDFSearchTools:
    """
    LLM-integrated PDF search tools
    """
    
    def __init__(self, llm_instance=None, default_pdf_path: str = None):
        """
        Initialize PDF search tools
        
        Args:
            llm_instance: Instance of AdvancedAzureLLM
            default_pdf_path: Default PDF path to search in
        """
        self.llm = llm_instance
        self.default_pdf_path = default_pdf_path or self._find_default_pdf()
        
        # Tool definitions for LLM function calling
        self.tool_definitions = [
            {
                "name": "search_pdf_text",
                "description": "Search for specific text in a PDF document. Returns full pages if many matches found, or paragraphs if few matches.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The text to search for in the PDF"
                        },
                        "pdf_path": {
                            "type": "string",
                            "description": "Path to the PDF file (optional, uses default if not provided)"
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Whether to perform case-sensitive search",
                            "default": False
                        },
                        "fuzzy_match": {
                            "type": "boolean", 
                            "description": "Whether to allow partial word matches",
                            "default": True
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_pdf_by_topic",
                "description": "Search for educational topics or concepts in the PDF with enhanced academic context extraction.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The educational topic or concept to search for"
                        },
                        "include_examples": {
                            "type": "boolean",
                            "description": "Whether to include examples and problems related to the topic",
                            "default": True
                        },
                        "include_definitions": {
                            "type": "boolean",
                            "description": "Whether to prioritize definitions and explanations",
                            "default": True
                        },
                        "pdf_path": {
                            "type": "string",
                            "description": "Path to the PDF file (optional)"
                        }
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "get_pdf_page_content",
                "description": "Retrieve the full content of a specific page from the PDF.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_number": {
                            "type": "integer",
                            "description": "The page number to retrieve (1-indexed)"
                        },
                        "pdf_path": {
                            "type": "string",
                            "description": "Path to the PDF file (optional)"
                        }
                    },
                    "required": ["page_number"]
                }
            }
        ]
    
    def _find_default_pdf(self) -> Optional[str]:
        """Find default PDF in the doc folder"""
        doc_folder = os.path.join(os.getcwd(), "doc")
        if os.path.exists(doc_folder):
            pdf_files = [f for f in os.listdir(doc_folder) if f.endswith('.pdf')]
            if pdf_files:
                return os.path.join(doc_folder, pdf_files[0])  # Return the first PDF found
        return None
    
    def search_pdf_text(
        self,
        query: str,
        pdf_path: Optional[str] = None,
        case_sensitive: bool = False,
        fuzzy_match: bool = True,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        LLM-callable function to search PDF text
        """
        pdf_file = pdf_path or self.default_pdf_path
        
        if not pdf_file or not os.path.exists(pdf_file):
            return {
                "success": False,
                "error": "PDF file not found",
                "results": []
            }
        
        try:
            results = search_pdf_content(
                pdf_path=pdf_file,
                query=query,
                case_sensitive=case_sensitive,
                fuzzy_match=fuzzy_match,
                max_results=max_results
            )
            
            # Check if any results contain errors
            if results and "error" in results[0]:
                return {
                    "success": False,
                    "error": results[0]["error"],
                    "results": []
                }
            
            return {
                "success": True,
                "query": query,
                "total_results": len(results),
                "pdf_file": os.path.basename(pdf_file),
                "results": results
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def search_pdf_by_topic(
        self,
        topic: str,
        include_examples: bool = True,
        include_definitions: bool = True,
        pdf_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhanced topic search with academic context
        """
        pdf_file = pdf_path or self.default_pdf_path
        
        if not pdf_file or not os.path.exists(pdf_file):
            return {
                "success": False,
                "error": "PDF file not found",
                "results": []
            }
        
        # Create enhanced search queries for academic content
        search_queries = [topic]
        
        if include_definitions:
            search_queries.extend([
                f"definition of {topic}",
                f"{topic} is defined",
                f"what is {topic}"
            ])
        
        if include_examples:
            search_queries.extend([
                f"{topic} example",
                f"example of {topic}",
                f"{topic} problem"
            ])
        
        all_results = []
        seen_pages = set()
        
        try:
            with PDFSearchTool(pdf_file) as searcher:
                for query in search_queries:
                    results = searcher.search(query, max_results=3)
                    for result in results:
                        # Avoid duplicate pages
                        if result.page_number not in seen_pages:
                            all_results.append({
                                "query": result.query,
                                "page_number": result.page_number,
                                "match_type": result.match_type,
                                "content": result.content,
                                "context_info": result.context_info,
                                "match_count_on_page": result.match_count_on_page,
                                "total_matches": result.total_matches,
                                "confidence_score": result.confidence_score,
                                "search_category": self._categorize_search(query, topic)
                            })
                            seen_pages.add(result.page_number)
                    
                    if len(all_results) >= 8:  # Limit total results
                        break
            
            # Sort by confidence score
            all_results.sort(key=lambda x: x["confidence_score"], reverse=True)
            
            return {
                "success": True,
                "topic": topic,
                "total_results": len(all_results),
                "pdf_file": os.path.basename(pdf_file),
                "search_strategy": {
                    "included_definitions": include_definitions,
                    "included_examples": include_examples,
                    "queries_used": search_queries[:3]  # Show first 3 queries used
                },
                "results": all_results[:5]  # Return top 5 results
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def get_pdf_page_content(
        self,
        page_number: int,
        pdf_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get full content of a specific PDF page
        """
        pdf_file = pdf_path or self.default_pdf_path
        
        if not pdf_file or not os.path.exists(pdf_file):
            return {
                "success": False,
                "error": "PDF file not found",
                "content": ""
            }
        
        try:
            with PDFSearchTool(pdf_file) as searcher:
                if page_number < 1 or page_number > searcher.total_pages:
                    return {
                        "success": False,
                        "error": f"Page number {page_number} is out of range (1-{searcher.total_pages})",
                        "content": ""
                    }
                
                page = searcher.doc[page_number - 1]  # Convert to 0-indexed
                page_text = page.get_text()
                cleaned_content = searcher._clean_page_text(page_text)
                
                return {
                    "success": True,
                    "page_number": page_number,
                    "total_pages": searcher.total_pages,
                    "pdf_file": os.path.basename(pdf_file),
                    "content": cleaned_content,
                    "word_count": len(cleaned_content.split()),
                    "character_count": len(cleaned_content)
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }
    
    def _categorize_search(self, query: str, original_topic: str) -> str:
        """Categorize the type of search performed"""
        query_lower = query.lower()
        
        if "definition" in query_lower or "what is" in query_lower or "is defined" in query_lower:
            return "definition"
        elif "example" in query_lower or "problem" in query_lower:
            return "example"
        elif query.lower() == original_topic.lower():
            return "main_topic"
        else:
            return "related"
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for LLM function calling"""
        return self.tool_definitions
    
    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle LLM tool calls
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments passed to the tool
            
        Returns:
            Tool execution result
        """
        try:
            if tool_name == "search_pdf_text":
                return self.search_pdf_text(**arguments)
            elif tool_name == "search_pdf_by_topic":
                return self.search_pdf_by_topic(**arguments)
            elif tool_name == "get_pdf_page_content":
                return self.get_pdf_page_content(**arguments)
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}",
                    "results": []
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "results": []
            }

# Standalone functions for direct LLM integration
def llm_search_pdf_text(
    query: str,
    pdf_path: Optional[str] = None,
    **kwargs
) -> str:
    """
    Simple function for LLM to search PDF text and get formatted results
    """
    tools = PDFSearchTools(default_pdf_path=pdf_path)
    result = tools.search_pdf_text(query, pdf_path, **kwargs)
    
    if not result["success"]:
        return f"Search failed: {result['error']}"
    
    if not result["results"]:
        return f"No results found for '{query}'"
    
    formatted_output = []
    formatted_output.append(f"Found {result['total_results']} results for '{query}' in {result['pdf_file']}:\n")
    
    for i, res in enumerate(result["results"], 1):
        formatted_output.append(f"Result {i} (Page {res['page_number']}, {res['match_type']}):")
        formatted_output.append(f"Confidence: {res['confidence_score']:.2f}")
        formatted_output.append(f"Context: {res['context_info']}")
        formatted_output.append(f"Content:\n{res['content']}")
        formatted_output.append("-" * 50)
    
    return "\n".join(formatted_output)

def llm_search_topic(
    topic: str,
    pdf_path: Optional[str] = None,
    **kwargs
) -> str:
    """
    Simple function for LLM to search academic topics
    """
    tools = PDFSearchTools(default_pdf_path=pdf_path)
    result = tools.search_pdf_by_topic(topic, pdf_path=pdf_path, **kwargs)
    
    if not result["success"]:
        return f"Topic search failed: {result['error']}"
    
    if not result["results"]:
        return f"No results found for topic '{topic}'"
    
    formatted_output = []
    formatted_output.append(f"Found {result['total_results']} results for topic '{topic}' in {result['pdf_file']}:\n")
    formatted_output.append(f"Search strategy: {result['search_strategy']}\n")
    
    for i, res in enumerate(result["results"], 1):
        formatted_output.append(f"Result {i} (Page {res['page_number']}, {res['search_category']}):")
        formatted_output.append(f"Match type: {res['match_type']}")
        formatted_output.append(f"Confidence: {res['confidence_score']:.2f}")
        formatted_output.append(f"Content:\n{res['content']}")
        formatted_output.append("-" * 50)
    
    return "\n".join(formatted_output)

if __name__ == "__main__":
    # Example usage
    tools = PDFSearchTools()
    
    # Test search
    result = tools.search_pdf_text("Normal Distribution")
    print(json.dumps(result, indent=2))