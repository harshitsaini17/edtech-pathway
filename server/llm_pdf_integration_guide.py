"""
LLM Integration Guide for PDF Search Tool
==========================================
How to integrate PDF search functionality with your existing LLM system.

QUICK START:
-----------
1. Import the integration module:
   from pdf_search_integration import search_pdf, get_pdf_page, search_topic

2. Use in your LLM system:
   result = search_pdf("Normal Distribution")
   page = get_pdf_page(232)

FEATURES:
---------
✅ Smart search: Returns full pages for multiple matches, paragraphs for single matches
✅ Automatic PDF detection: Uses book2.pdf (statistics) by default, falls back to book.pdf
✅ LLM-friendly output: Clean, structured responses
✅ Error handling: Graceful failure with meaningful error messages
✅ Ready for function calling: Tool definitions included

USAGE EXAMPLES:
--------------
"""

# Example 1: Basic text search
from pdf_search_integration import search_pdf

def example_basic_search():
    """Example of basic PDF search"""
    result = search_pdf("Normal Distribution", max_results=3)
    
    if result["success"]:
        print(f"Found {result['results_returned']} results:")
        for res in result["results"]:
            print(f"Page {res['page']}: {res['content'][:100]}...")
    else:
        print(f"Search failed: {result['error']}")

# Example 2: Get specific page content
from pdf_search_integration import get_pdf_page

def example_get_page():
    """Example of getting specific page content"""
    result = get_pdf_page(232)  # Page with Normal Distribution content
    
    if result["success"]:
        print(f"Page {result['page']} content:")
        print(result["content"][:300] + "...")
    else:
        print(f"Error: {result['error']}")

# Example 3: Topic search with academic context
from pdf_search_integration import search_topic

def example_topic_search():
    """Example of enhanced topic search"""
    result = search_topic(
        topic="probability",
        include_examples=True,
        include_definitions=True
    )
    
    if result["success"]:
        print(f"Found {result['total_results']} results for 'probability'")
        for res in result["results"][:2]:  # Show first 2 results
            print(f"Page {res['page_number']}: {res['content'][:150]}...")

# Example 4: Integration with your existing LLM class
"""
Add these methods to your AdvancedAzureLLM class:
"""

def add_pdf_search_to_llm():
    """
    Example of how to add PDF search to your existing LLM class
    """
    
    class AdvancedAzureLLMWithPDF:
        def __init__(self):
            # Your existing initialization code
            pass
        
        def search_pdf_content(self, query: str, max_results: int = 3):
            """Search PDF content and return formatted response"""
            from pdf_search_integration import search_pdf
            
            result = search_pdf(query, max_results=max_results)
            
            if not result["success"]:
                return f"PDF search failed: {result['error']}"
            
            if not result["results"]:
                return f"No results found for '{query}'"
            
            # Format for LLM consumption
            response = f"Found {result['results_returned']} results for '{query}':\n\n"
            
            for i, res in enumerate(result["results"], 1):
                response += f"{i}. Page {res['page']} ({res['type']}):\n"
                response += f"   {res['content'][:200]}...\n\n"
            
            return response
        
        def get_pdf_page_content(self, page_number: int):
            """Get full page content from PDF"""
            from pdf_search_integration import get_pdf_page
            
            result = get_pdf_page(page_number)
            
            if not result["success"]:
                return f"Error retrieving page {page_number}: {result['error']}"
            
            return f"Page {page_number} content:\n\n{result['content']}"

# Example 5: Function calling integration
from pdf_search_integration import PDF_SEARCH_TOOLS

def example_function_calling():
    """
    Example of how to integrate with function calling systems
    """
    
    # The PDF_SEARCH_TOOLS list contains tool definitions ready for use
    print("Available PDF search tools:")
    for tool in PDF_SEARCH_TOOLS:
        print(f"- {tool['name']}: {tool['description']}")
    
    # Example function call handler
    def handle_pdf_tool_call(tool_name: str, arguments: dict):
        """Handle PDF-related tool calls"""
        
        if tool_name == "search_pdf":
            from pdf_search_integration import search_pdf
            return search_pdf(**arguments)
        
        elif tool_name == "get_pdf_page":
            from pdf_search_integration import get_pdf_page
            return get_pdf_page(**arguments)
        
        elif tool_name == "search_topic":
            from pdf_search_integration import search_topic
            return search_topic(**arguments)
        
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

# Example 6: Simple text-based functions (easiest integration)
from pdf_search_integration import search_pdf_simple, get_pdf_page_simple

def example_simple_functions():
    """
    Simple text-based functions that return formatted strings
    Perfect for LLM systems that prefer text responses
    """
    
    # Simple search - returns formatted text
    search_result = search_pdf_simple("Normal Distribution")
    print("Search result:")
    print(search_result)
    
    print("\n" + "="*50 + "\n")
    
    # Simple page retrieval - returns formatted text
    page_content = get_pdf_page_simple(232)
    print("Page content:")
    print(page_content[:300] + "...")

# IMPLEMENTATION CHECKLIST:
"""
□ Install PyMuPDF: pip install PyMuPDF (already done in your venv)
□ Copy pdf_search_tool.py to your project
□ Copy pdf_llm_tools.py to your project  
□ Copy pdf_search_integration.py to your project
□ Test with: python3 pdf_search_integration.py
□ Integrate with your LLM class using examples above
□ Add tool definitions to your function calling system (if used)
"""

# FILE STRUCTURE:
"""
Your project should now have:
├── pdf_search_tool.py          # Core PDF search functionality
├── pdf_llm_tools.py           # LLM integration helpers
├── pdf_search_integration.py   # Simple integration interface
├── pdf_search_demo.py         # Demonstration script
└── doc/
    ├── book.pdf              # Secondary PDF
    └── book2.pdf             # Primary PDF (statistics book)
"""

if __name__ == "__main__":
    print("PDF Search Tool - LLM Integration Examples")
    print("="*50)
    
    print("\n1. Basic Search Example:")
    example_basic_search()
    
    print("\n2. Page Retrieval Example:")
    example_get_page()
    
    print("\n3. Topic Search Example:")
    example_topic_search()
    
    print("\n4. Simple Functions Example:")
    example_simple_functions()
    
    print("\n5. Available Tool Definitions:")
    example_function_calling()
    
    print("\n" + "="*50)
    print("Integration complete! Your LLM can now search PDF content.")
    print("Use the functions from pdf_search_integration.py in your LLM system.")