#!/usr/bin/env python3
"""
Test Parallel GPT Filtering
===========================
Tests the parallel GPT filtering functionality with LLM.py integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from topic_extractor import AdvancedMultiStrategyExtractor
import json
from datetime import datetime
import asyncio

def test_parallel_gpt():
    """Test parallel GPT filtering with real async processing"""
    
    print("🚀 Testing Parallel GPT Filtering with LLM.py Integration")
    print("=" * 60)
    
    pdf_path = "doc/book2.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # Test with realistic sample topics - expanded for better parallel testing
    sample_topics = [
        {"topic": "Chapter 1: Introduction to Probability Theory", "page": 1, "confidence": 0.9, "extraction_method": "toc", "context": "chapter", "position": "toc"},
        {"topic": "1.1 Sample Spaces and Events", "page": 3, "confidence": 0.8, "extraction_method": "content_pattern", "context": "numbered_sections", "position": "header"},
        {"topic": "Example 1.3: Rolling a Six-Sided Die", "page": 8, "confidence": 0.7, "extraction_method": "content_pattern", "context": "content_markers", "position": "body"},
        {"topic": "1.2 Probability Measures", "page": 12, "confidence": 0.8, "extraction_method": "formatting", "context": "font_size_14.0_bold_True", "position": "header"},
        {"topic": "Definition 1.1: Probability Space", "page": 15, "confidence": 0.9, "extraction_method": "content_pattern", "context": "content_markers", "position": "body"},
        {"topic": "Exercise 1.5", "page": 18, "confidence": 0.5, "extraction_method": "content_pattern", "context": "content_markers", "position": "body"},
        {"topic": "Figure 1.2: Venn Diagram Illustration", "page": 20, "confidence": 0.4, "extraction_method": "context", "context": "contextual_analysis", "position": "body"},
        {"topic": "Theorem 1.3: Addition Rule for Probability", "page": 25, "confidence": 0.9, "extraction_method": "content_pattern", "context": "content_markers", "position": "body"},
        {"topic": "2.1 Random Variables", "page": 35, "confidence": 0.8, "extraction_method": "formatting", "context": "font_size_13.5_bold_True", "position": "header"},
        {"topic": "Problem Set 2.1", "page": 45, "confidence": 0.3, "extraction_method": "content_pattern", "context": "content_markers", "position": "body"},
        {"topic": "2.2 Probability Distribution Functions", "page": 48, "confidence": 0.8, "extraction_method": "formatting", "context": "font_size_13.5_bold_True", "position": "header"},
        {"topic": "Example 2.7: Bernoulli Distribution", "page": 52, "confidence": 0.6, "extraction_method": "content_pattern", "context": "content_markers", "position": "body"},
        {"topic": "Applications in Statistics", "page": 65, "confidence": 0.8, "extraction_method": "toc", "context": "table_of_contents", "position": "toc"},
        {"topic": "Chapter Summary and Review", "page": 70, "confidence": 0.7, "extraction_method": "formatting", "context": "font_size_12.0_bold_True", "position": "header"},
        {"topic": "Bibliography and References", "page": 75, "confidence": 0.3, "extraction_method": "formatting", "context": "font_size_12.0_bold_False", "position": "header"},
        {"topic": "3.1 Continuous Random Variables", "page": 80, "confidence": 0.8, "extraction_method": "content_pattern", "context": "numbered_sections", "position": "header"},
        {"topic": "The Normal Distribution", "page": 88, "confidence": 0.8, "extraction_method": "toc", "context": "table_of_contents", "position": "toc"},
        {"topic": "Homework Assignment 3", "page": 95, "confidence": 0.2, "extraction_method": "context", "context": "contextual_analysis", "position": "body"},
        {"topic": "Central Limit Theorem", "page": 102, "confidence": 0.9, "extraction_method": "toc", "context": "table_of_contents", "position": "toc"},
        {"topic": "Statistical Inference Methods", "page": 115, "confidence": 0.8, "extraction_method": "formatting", "context": "font_size_13.0_bold_True", "position": "header"},
        {"topic": "3.3 Hypothesis Testing", "page": 120, "confidence": 0.8, "extraction_method": "content_pattern", "context": "numbered_sections", "position": "header"},
        {"topic": "Example 3.12: T-Test Application", "page": 125, "confidence": 0.5, "extraction_method": "content_pattern", "context": "content_markers", "position": "body"},
        {"topic": "4.1 Regression Analysis", "page": 140, "confidence": 0.8, "extraction_method": "formatting", "context": "font_size_14.0_bold_True", "position": "header"},
        {"topic": "Linear Model Assumptions", "page": 155, "confidence": 0.7, "extraction_method": "context", "context": "contextual_analysis", "position": "body"},
        {"topic": "Problem 4.8", "page": 165, "confidence": 0.3, "extraction_method": "content_pattern", "context": "content_markers", "position": "body"},
        {"topic": "Multiple Regression Techniques", "page": 170, "confidence": 0.8, "extraction_method": "toc", "context": "table_of_contents", "position": "toc"},
        {"topic": "Model Validation Methods", "page": 185, "confidence": 0.7, "extraction_method": "formatting", "context": "font_size_13.0_bold_True", "position": "header"},
        {"topic": "Cross-Validation Techniques", "page": 195, "confidence": 0.8, "extraction_method": "context", "context": "contextual_analysis", "position": "body"},
        {"topic": "Appendix A: Statistical Tables", "page": 210, "confidence": 0.6, "extraction_method": "toc", "context": "table_of_contents", "position": "toc"},
        {"topic": "Index", "page": 220, "confidence": 0.2, "extraction_method": "formatting", "context": "font_size_12.0_bold_False", "position": "header"}
    ]
    
    try:
        extractor = AdvancedMultiStrategyExtractor(pdf_path)
        
        print(f"📝 Testing parallel GPT filtering with {len(sample_topics)} topics...")
        print(f"📊 Expected filtering: Examples, Problems, Figures, Homework should be removed")
        
        # Test the new parallel GPT filtering
        start_time = datetime.now()
        filtered_topics = extractor._filter_by_gpt_parallel(sample_topics)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        # Calculate detailed statistics
        original_count = len(sample_topics)
        filtered_count = len(filtered_topics)
        removed_count = original_count - filtered_count
        retention_rate = (filtered_count / original_count) * 100 if original_count > 0 else 0
        
        print(f"\n🎯 Parallel Processing Results:")
        print(f"   📥 Input topics: {original_count}")
        print(f"   📤 Topics kept: {filtered_count}")
        print(f"   🚫 Topics filtered out: {removed_count}")
        print(f"   ⏱️ Processing time: {processing_time:.2f} seconds")
        print(f"   📈 Retention rate: {retention_rate:.1f}%")
        print(f"   ⚡ Speed: {original_count/processing_time:.1f} topics/second")
        
        # Analyze which topics were kept vs filtered
        kept_topics = []
        batch_stats = {}
        
        print(f"\n✅ Topics KEPT by parallel GPT filtering:")
        for i, topic in enumerate(filtered_topics):
            gpt_status = "✓" if topic.get('gpt_filtered', False) else "✗"
            batch_id = topic.get('batch_id', 'N/A')
            
            # Track batch statistics
            if batch_id not in batch_stats:
                batch_stats[batch_id] = 0
            batch_stats[batch_id] += 1
            
            kept_topics.append(topic['topic'])
            print(f"   {i+1:2d}. \"{topic['topic']}\" (Page {topic['page']}) [GPT:{gpt_status}, Batch:{batch_id}]")
        
        # Show what was filtered out
        filtered_out = [topic for topic in sample_topics if topic['topic'] not in kept_topics]
        print(f"\n🚫 Topics FILTERED OUT by parallel GPT ({len(filtered_out)} topics):")
        for i, topic in enumerate(filtered_out):
            print(f"   {i+1:2d}. \"{topic['topic']}\" (Page {topic['page']}) - Likely reason: {_guess_filter_reason(topic['topic'])}")
        
        # Show batch processing statistics
        print(f"\n📊 Batch Processing Statistics:")
        for batch_id, count in sorted(batch_stats.items()):
            if batch_id != 'N/A':
                print(f"   Batch {batch_id}: {count} topics kept")
        
        # Test quality of filtering
        expected_filtered = ['Example', 'Problem', 'Exercise', 'Homework', 'Figure', 'Bibliography', 'Index']
        expected_kept = ['Chapter', 'Definition', 'Theorem', 'Distribution', 'Applications', 'Methods']
        
        correctly_filtered = sum(1 for topic in filtered_out if any(keyword in topic['topic'] for keyword in expected_filtered))
        correctly_kept = sum(1 for topic in filtered_topics if any(keyword in topic['topic'] for keyword in expected_kept))
        
        print(f"\n🎯 Filtering Quality Assessment:")
        print(f"   ✅ Correctly filtered examples/exercises: {correctly_filtered}/{len([t for t in sample_topics if any(kw in t['topic'] for kw in expected_filtered)])}")
        print(f"   ✅ Correctly kept educational content: {correctly_kept}/{len([t for t in sample_topics if any(kw in t['topic'] for kw in expected_kept)])}")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/parallel_gpt_test_{timestamp}.json"
        
        test_results = {
            'test_metadata': {
                'test_date': timestamp,
                'processing_time_seconds': processing_time,
                'input_count': original_count,
                'output_count': filtered_count,
                'removed_count': removed_count,
                'retention_rate': retention_rate,
                'processing_speed_topics_per_second': original_count/processing_time if processing_time > 0 else 0,
                'batch_statistics': batch_stats
            },
            'quality_metrics': {
                'correctly_filtered_examples': correctly_filtered,
                'correctly_kept_educational': correctly_kept,
                'expected_filtered_keywords': expected_filtered,
                'expected_kept_keywords': expected_kept
            },
            'input_topics': sample_topics,
            'filtered_topics': filtered_topics,
            'removed_topics': [{'topic': t['topic'], 'page': t['page'], 'reason': _guess_filter_reason(t['topic'])} for t in filtered_out]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed test results saved to: {output_file}")
        
        # Performance comparison note
        estimated_sequential_time = original_count * 0.5  # Assume 0.5 seconds per topic for sequential processing
        speedup_factor = estimated_sequential_time / processing_time if processing_time > 0 else 0
        
        print(f"\n⚡ Performance Analysis:")
        print(f"   🐌 Estimated sequential processing time: {estimated_sequential_time:.1f} seconds")
        print(f"   🚀 Actual parallel processing time: {processing_time:.2f} seconds")
        print(f"   📈 Estimated speedup factor: {speedup_factor:.1f}x faster")
        
        return filtered_topics
        
    except Exception as e:
        print(f"❌ Error during parallel testing: {e}")
        import traceback
        traceback.print_exc()
        return None

def _guess_filter_reason(topic_text: str) -> str:
    """Guess why a topic might have been filtered out"""
    topic_lower = topic_text.lower()
    
    if any(keyword in topic_lower for keyword in ['example', 'problem', 'exercise', 'homework']):
        return "Contains example/exercise keywords"
    elif any(keyword in topic_lower for keyword in ['figure', 'table', 'chart']):
        return "Figure/table reference"
    elif any(keyword in topic_lower for keyword in ['bibliography', 'references', 'index']):
        return "Non-educational content"
    elif len(topic_text.split()) <= 2:
        return "Too short/fragmentary"
    else:
        return "GPT determined not educational content"

def test_llm_connection():
    """Test if LLM connection is working"""
    print("\n🔧 Testing LLM Connection...")
    
    try:
        from LLM import AdvancedAzureLLM
        llm = AdvancedAzureLLM()
        
        # Test basic connection
        status = llm.get_system_status()
        print("📡 LLM System Status:")
        for system, info in status.items():
            print(f"   {system}: API Key {'✅' if info['api_key_configured'] else '❌'}, Endpoint {'✅' if info['endpoint_configured'] else '❌'}")
        
        # Test model switching
        llm.switch_model("gpt-5-mini")
        print("✅ Successfully switched to gpt-5-mini model")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Test LLM connection first
    if test_llm_connection():
        print("\n" + "="*60)
        test_parallel_gpt()
    else:
        print("❌ Cannot proceed with parallel GPT testing - LLM connection failed")
        print("💡 Please check your .env file and Azure OpenAI credentials")
