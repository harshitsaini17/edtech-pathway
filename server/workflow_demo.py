"""
Complete Workflow Demo
=====================
Demonstrates the complete curriculum creation workflow from PDF to personalized learning path.
"""

import subprocess
import sys
import os

def run_workflow_demo():
    """Run complete workflow demonstration"""
    print("🚀 Complete Curriculum Creation Workflow Demo")
    print("=" * 60)
    
    # Step 1: Extract topics from both books
    print("\n📚 Step 1: Extracting Topics from Books")
    print("-" * 40)
    
    books = [
        ("doc/book.pdf", "Technical Signals & Systems"),
        ("doc/book2.pdf", "Statistics & Probability")
    ]
    
    for book_path, book_type in books:
        if os.path.exists(book_path):
            print(f"\n🔍 Extracting from {book_type}...")
            try:
                result = subprocess.run([
                    sys.executable, "optimized_universal_extractor.py", book_path
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if "SUCCESS!" in line or "topics" in line.lower():
                            print(f"   ✅ {line}")
                else:
                    print(f"   ❌ Failed to extract from {book_path}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        else:
            print(f"   ❌ Book not found: {book_path}")
    
    # Step 2: Show available curriculum options
    print(f"\n🎯 Step 2: Available Learning Paths")
    print("-" * 40)
    
    sample_queries = [
        "expectation and variance in statistics",
        "signal processing and fourier transforms", 
        "probability distributions and random variables",
        "linear systems and control theory"
    ]
    
    print("Choose from these learning paths:")
    for i, query in enumerate(sample_queries, 1):
        print(f"   {i}. {query}")
    
    # Step 3: Create curriculum
    print(f"\n🏗️ Step 3: Creating Curriculum")
    print("-" * 40)
    print("To create a curriculum, run:")
    print("   python curriculum_creator_fallback.py")
    print("\nThe system will:")
    print("   ✅ Load extracted topics automatically")
    print("   ✅ Refine your query using LLM")
    print("   ✅ Find relevant topics with smart matching")
    print("   ✅ Generate a structured learning path")
    print("   ✅ Save curriculum as JSON for further use")
    
    # Step 4: Show output files
    print(f"\n📋 Step 4: Generated Files")
    print("-" * 40)
    
    output_dir = "output"
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        topic_files = [f for f in files if 'optimized_universal' in f and f.endswith('.json')]
        curriculum_files = [f for f in files if f.startswith('curriculum_') and f.endswith('.json')]
        
        print("📚 Topic Extraction Files:")
        for file in topic_files:
            print(f"   • {file}")
        
        if curriculum_files:
            print("\n🎓 Generated Curricula:")
            for file in curriculum_files:
                print(f"   • {file}")
        else:
            print("\n🎓 No curricula generated yet - run curriculum_creator_fallback.py")
    
    print(f"\n✨ Workflow Complete! Ready for personalized learning.")

if __name__ == "__main__":
    run_workflow_demo()
