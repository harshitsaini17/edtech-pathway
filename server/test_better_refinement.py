#!/usr/bin/env python3
"""
Quick test for better query refinement
"""
import sys
from curriculum_creator_fallback import CurriculumCreatorFallback

def test_refinement():
    creator = CurriculumCreatorFallback()
    
    test_queries = [
        "probability distributions",
        "linear algebra",
        "machine learning",
        "calculus",
        "statistics"
    ]
    
    print("🧪 Testing Improved Query Refinement")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n📝 Original: '{query}'")
        try:
            refined = creator.refine_query_with_llm(query)
            print(f"🤖 Refined:  '{refined}'")
            print(f"📏 Length:   {len(refined)} characters")
        except Exception as e:
            print(f"❌ Error: {e}")
        print("-" * 50)

if __name__ == "__main__":
    test_refinement()
