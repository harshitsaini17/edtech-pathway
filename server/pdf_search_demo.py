"""
PDF Search Tool Integration Demo
===============================
Demonstrates how to integrate the PDF search tools with the existing LLM system.
Shows both direct usage and LLM function calling integration.
"""

import json
import sys
import os
from typing import Dict, Any, List

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_search_tool import PDFSearchTool
from pdf_llm_tools import PDFSearchTools, llm_search_pdf_text, llm_search_topic
from LLM import AdvancedAzureLLM

def demo_basic_search():
    """Demonstrate basic PDF search functionality"""
    print("=" * 60)
    print("DEMO: Basic PDF Search")
    print("=" * 60)
    
    # Find PDF file
    doc_folder = "doc"
    pdf_files = [f for f in os.listdir(doc_folder) if f.endswith('.pdf')] if os.path.exists(doc_folder) else []
    
    if not pdf_files:
        print("No PDF files found in doc/ folder")
        return
    
    pdf_path = os.path.join(doc_folder, pdf_files[0])
    print(f"Using PDF: {pdf_path}")
    
    # Test searches
    test_queries = [
        "Normal Distribution",
        "probability",
        "statistics",
        "variance"
    ]
    
    with PDFSearchTool(pdf_path) as searcher:
        for query in test_queries:
            print(f"\n--- Searching for: '{query}' ---")
            results = searcher.search(query, max_results=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"\nResult {i}:")
                    print(f"  Page: {result.page_number}")
                    print(f"  Type: {result.match_type}")
                    print(f"  Matches on page: {result.match_count_on_page}")
                    print(f"  Confidence: {result.confidence_score:.2f}")
                    print(f"  Preview: {result.content[:200]}...")
            else:
                print("  No results found")

def demo_llm_integration():
    """Demonstrate LLM integration with PDF search tools"""
    print("\n" + "=" * 60)
    print("DEMO: LLM Integration")
    print("=" * 60)
    
    # Initialize PDF search tools
    tools = PDFSearchTools()
    
    if not tools.default_pdf_path:
        print("No PDF files found for LLM integration demo")
        return
    
    print(f"Using PDF: {tools.default_pdf_path}")
    
    # Test LLM-callable functions
    test_cases = [
        {
            "function": "search_pdf_text",
            "args": {"query": "Normal Distribution", "max_results": 2}
        },
        {
            "function": "search_pdf_by_topic", 
            "args": {"topic": "probability", "include_examples": True}
        },
        {
            "function": "get_pdf_page_content",
            "args": {"page_number": 100}  # Arbitrary page number
        }
    ]
    
    for case in test_cases:
        print(f"\n--- Testing: {case['function']} ---")
        
        try:
            if case['function'] == 'search_pdf_text':
                result = tools.search_pdf_text(**case['args'])
            elif case['function'] == 'search_pdf_by_topic':
                result = tools.search_pdf_by_topic(**case['args'])
            elif case['function'] == 'get_pdf_page_content':
                result = tools.get_pdf_page_content(**case['args'])
            
            print(f"Success: {result['success']}")
            if result['success']:
                if 'results' in result and result['results']:
                    print(f"Results found: {len(result['results'])}")
                    # Show first result preview
                    first_result = result['results'][0]
                    if 'content' in first_result:
                        print(f"First result preview: {first_result['content'][:150]}...")
                elif 'content' in result:
                    print(f"Content preview: {result['content'][:150]}...")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            print(f"Exception: {e}")

def demo_tool_definitions():
    """Show tool definitions for LLM function calling"""
    print("\n" + "=" * 60)
    print("DEMO: Tool Definitions for LLM")
    print("=" * 60)
    
    tools = PDFSearchTools()
    definitions = tools.get_tool_definitions()
    
    for i, tool_def in enumerate(definitions, 1):
        print(f"\n--- Tool {i}: {tool_def['name']} ---")
        print(f"Description: {tool_def['description']}")
        print("Parameters:")
        
        for param_name, param_info in tool_def['parameters']['properties'].items():
            required = param_name in tool_def['parameters'].get('required', [])
            print(f"  - {param_name} ({param_info['type']}){'*' if required else ''}: {param_info['description']}")

def demo_formatted_output():
    """Demonstrate formatted output functions"""
    print("\n" + "=" * 60)
    print("DEMO: Formatted Output for LLM")
    print("=" * 60)
    
    # Test the simple LLM-callable functions
    print("\n--- Testing llm_search_pdf_text ---")
    result = llm_search_pdf_text("Normal Distribution", max_results=1)
    print(result[:500] + "..." if len(result) > 500 else result)
    
    print("\n--- Testing llm_search_topic ---")
    result = llm_search_topic("probability", include_examples=True)
    print(result[:500] + "..." if len(result) > 500 else result)

def simulate_llm_conversation():
    """Simulate an LLM conversation using the PDF search tools"""
    print("\n" + "=" * 60)
    print("DEMO: Simulated LLM Conversation")
    print("=" * 60)
    
    tools = PDFSearchTools()
    
    # Simulate LLM queries
    conversation = [
        {
            "user_query": "What is the definition of Normal Distribution?",
            "tool_call": {
                "name": "search_pdf_by_topic",
                "args": {"topic": "Normal Distribution", "include_definitions": True, "include_examples": False}
            }
        },
        {
            "user_query": "Can you show me examples of probability problems?", 
            "tool_call": {
                "name": "search_pdf_by_topic",
                "args": {"topic": "probability", "include_examples": True, "include_definitions": False}
            }
        },
        {
            "user_query": "Search for 'variance' in the document",
            "tool_call": {
                "name": "search_pdf_text", 
                "args": {"query": "variance", "max_results": 2}
            }
        }
    ]
    
    for i, turn in enumerate(conversation, 1):
        print(f"\n--- Conversation Turn {i} ---")
        print(f"User: {turn['user_query']}")
        print(f"LLM Tool Call: {turn['tool_call']['name']}")
        
        # Execute tool call
        result = tools.handle_tool_call(
            turn['tool_call']['name'], 
            turn['tool_call']['args']
        )
        
        print(f"Tool Response Success: {result['success']}")
        if result['success'] and 'results' in result and result['results']:
            print(f"Found {len(result['results'])} results")
            # Show summary of first result
            first = result['results'][0]
            print(f"First result: Page {first.get('page_number', 'N/A')}, "
                  f"Type: {first.get('match_type', 'N/A')}")
            content_preview = first.get('content', '')[:100]
            print(f"Content preview: {content_preview}...")
        elif result['success'] and 'content' in result:
            content_preview = result['content'][:100]
            print(f"Content preview: {content_preview}...")
        else:
            print(f"Error or no results: {result.get('error', 'No results found')}")

def main():
    """Run all demonstrations"""
    print("PDF Search Tool Integration Demonstration")
    print("=" * 60)
    
    try:
        demo_basic_search()
        demo_llm_integration() 
        demo_tool_definitions()
        demo_formatted_output()
        simulate_llm_conversation()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nIntegration Summary:")
        print("1. Basic PDF search works with PyMuPDF")
        print("2. LLM-callable functions are available")
        print("3. Tool definitions ready for function calling")
        print("4. Formatted outputs ready for LLM consumption")
        print("5. Full conversation simulation works")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()