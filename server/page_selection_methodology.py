#!/usr/bin/env python3
"""
PAGE SELECTION METHODOLOGY SUMMARY
==================================

This document explains how our system intelligently selects pages for each topic
in the curriculum, providing complete transparency in the decision-making process.

Based on the detailed analysis from: detailed_page_analysis_20250908_094406.txt
"""

import json

def explain_page_selection_methodology():
    """Explains the sophisticated page selection system."""
    
    print("🔍 PAGE SELECTION METHODOLOGY")
    print("=" * 50)
    
    print("\n1. BASE PAGE SELECTION:")
    print("   • Each curriculum topic starts with a base page from book2.pdf")
    print("   • Base page is automatically given relevance score of 9 (high)")
    print("   • System ensures correct PDF source (book2.pdf, not book.pdf)")
    
    print("\n2. CONTINUATION PAGE ANALYSIS:")
    print("   • System analyzes up to 4 pages after the base page")
    print("   • Each page gets scored based on multiple criteria:")
    
    print("\n   📊 SCORING CRITERIA:")
    print("   • Mathematical Content: +3 points")
    print("     - Looks for: variance, expectation, σ, μ, formulas")
    print("   • Examples Present: +2 points")
    print("     - Identifies worked examples and problems")
    print("   • Definitions Present: +2 points")
    print("     - Detects formal definitions and theorems")
    print("   • Content Length: +1-2 points")
    print("     - Longer pages with substantial content get higher scores")
    
    print("\n3. SECTION BREAK DETECTION:")
    print("   • System stops adding pages when it detects:")
    print("     - New chapters starting")
    print("     - New sections beginning")
    print("     - Topic changes (indicated by headers)")
    print("   • This prevents including unrelated content")
    
    print("\n4. RELEVANCE THRESHOLD:")
    print("   • Pages must score ≥5 points to be included")
    print("   • Lower scoring pages are excluded to maintain quality")
    print("   • System provides detailed reasoning for each decision")
    
    print("\n📈 RESULTS ACHIEVED:")
    
    # Read the analysis results
    try:
        with open("output/detailed_page_analysis_20250908_094406.txt", "r") as f:
            content = f.read()
            
        # Count modules and topics
        module_count = content.count("📚 MODULE")
        topic_count = content.count("📖 Topic")
        
        # Extract page counts
        import re
        page_selections = re.findall(r'Selected Pages: \[([^\]]+)\] \((\d+) pages\)', content)
        total_pages = sum(int(count) for _, count in page_selections)
        
        print(f"   • Analyzed {topic_count} topics across {module_count} modules")
        print(f"   • Selected {total_pages} pages total")
        print(f"   • Average: {total_pages/topic_count:.1f} pages per topic")
        
        # Show examples of different selection patterns
        print(f"\n📋 SELECTION PATTERN EXAMPLES:")
        
        # Find examples of different patterns
        single_page = [p for p in page_selections if int(p[1]) == 1]
        multi_page = [p for p in page_selections if int(p[1]) >= 4]
        
        print(f"   • Single page topics: {len(single_page)} topics")
        print(f"   • Multi-page topics (4+ pages): {len(multi_page)} topics")
        print(f"   • This shows adaptive selection based on content complexity")
        
    except FileNotFoundError:
        print("   • Analysis file not found - run detailed_page_tracker.py first")
    
    print("\n🎯 KEY ADVANTAGES:")
    print("   • Intelligent continuation detection")
    print("   • Prevents content gaps mid-topic")
    print("   • Avoids including unrelated sections")
    print("   • Transparent scoring with detailed reasoning")
    print("   • Adaptive to content complexity")
    print("   • Quality-focused (only relevant pages included)")

def show_topic_examples():
    """Shows specific examples of page selection decisions."""
    
    print("\n" + "=" * 60)
    print("🔬 DETAILED SELECTION EXAMPLES")
    print("=" * 60)
    
    examples = [
        {
            "topic": "Chapter 4 RANDOM VARIABLES AND EXPECTATION",
            "base_page": 153,
            "selected": "[153, 154, 155, 156, 157] (5 pages)",
            "reasoning": "Base page + 4 high-relevance continuation pages (scores: 12, 11, 12, 10)",
            "why_stopped": "Maintained high relevance throughout sequence"
        },
        {
            "topic": "2.2 DESCRIBING DATA SETS", 
            "base_page": 77,
            "selected": "[77] (1 page)",
            "reasoning": "Base page only",
            "why_stopped": "Next page had section break detected: ['chapter']"
        },
        {
            "topic": "4.7 Covariance and Variance of Sums of Random Variables",
            "base_page": 185, 
            "selected": "[185, 186, 187, 188, 189] (5 pages)",
            "reasoning": "All continuation pages highly relevant (scores: 6, 19, 6, 21)",
            "why_stopped": "Next page would start new section"
        },
        {
            "topic": "2.5 Normal Data Sets",
            "base_page": 97,
            "selected": "[97] (1 page)", 
            "reasoning": "Base page with high relevance (14)",
            "why_stopped": "Next page had section break: ['chapter']"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n📖 EXAMPLE {i}: {example['topic']}")
        print(f"   Base Page: {example['base_page']}")
        print(f"   Selected: {example['selected']}")
        print(f"   Logic: {example['reasoning']}")
        print(f"   Stopped: {example['why_stopped']}")

def show_scoring_details():
    """Shows the detailed scoring system."""
    
    print("\n" + "=" * 60)
    print("🧮 DETAILED SCORING SYSTEM")
    print("=" * 60)
    
    print("\n📊 CONTENT ANALYSIS WEIGHTS:")
    scoring_weights = {
        "Mathematical Content": {
            "weight": 3,
            "detects": ["variance", "expectation", "σ", "μ", "equations", "formulas"],
            "importance": "Core statistical concepts for expectation/variance curriculum"
        },
        "Examples Present": {
            "weight": 2, 
            "detects": ["EXAMPLE", "SOLUTION", "worked problems", "calculations"],
            "importance": "Practical application and understanding"
        },
        "Definitions Present": {
            "weight": 2,
            "detects": ["DEFINITION", "THEOREM", "PROPOSITION", "formal statements"],
            "importance": "Theoretical foundation and precise understanding"
        },
        "Content Density": {
            "weight": "1-2",
            "detects": ["word count", "substantial text", "comprehensive coverage"],
            "importance": "Ensures meaningful content, not just headers"
        }
    }
    
    for criterion, details in scoring_weights.items():
        print(f"\n🎯 {criterion.upper()}:")
        print(f"   Weight: +{details['weight']} points")
        print(f"   Detects: {', '.join(details['detects'])}")
        print(f"   Why Important: {details['importance']}")
    
    print(f"\n⚖️ DECISION THRESHOLDS:")
    print(f"   • Include Page: Score ≥ 5 points")
    print(f"   • Base Page: Always included (auto-score: 9)")
    print(f"   • Section Break: Immediate stop regardless of score")
    print(f"   • Maximum Lookahead: 4 pages after base page")

if __name__ == "__main__":
    explain_page_selection_methodology()
    show_topic_examples()
    show_scoring_details()
    
    print(f"\n" + "=" * 60)
    print(f"📁 For complete analysis, see:")
    print(f"   • detailed_page_analysis_20250908_094406.txt")
    print(f"   • All 71 topics with full reasoning documented")
    print(f"   • 110 total pages selected across 9 modules")
    print(f"=" * 60)
