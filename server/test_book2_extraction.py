#!/usr/bin/env python3
"""
Full Topic Extraction Test for book2.pdf
========================================
Tests the complete topic extraction pipeline with parallel GPT filtering
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from topic_extractor import AdvancedMultiStrategyExtractor
import json
from datetime import datetime

def test_book2_extraction():
    """Test complete topic extraction on book2.pdf"""
    
    print("📚 Full Topic Extraction Test - book2.pdf")
    print("=" * 60)
    
    pdf_path = "doc/book2.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    print(f"📖 Processing: {pdf_path}")
    print(f"🔄 Pipeline: Multi-strategy extraction → Keyword filtering → Parallel GPT filtering")
    print()
    
    try:
        # Initialize extractor
        extractor = AdvancedMultiStrategyExtractor(pdf_path)
        
        # Run the complete extraction pipeline
        start_time = datetime.now()
        print("🚀 Starting complete extraction pipeline...")
        
        # This will run all strategies + keyword filtering + parallel GPT filtering
        topics = extractor.extract_with_multiple_strategies()
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"\n🎯 Extraction Complete!")
        print(f"   ⏱️ Total processing time: {processing_time:.2f} seconds")
        print(f"   📊 Final topics extracted: {len(topics)}")
        
        if topics:
            # Analyze results
            gpt_filtered_count = sum(1 for topic in topics if topic.get('gpt_filtered', False))
            avg_confidence = sum(topic.get('confidence', 0) for topic in topics) / len(topics)
            
            # Group by extraction method
            method_counts = {}
            for topic in topics:
                method = topic.get('extraction_method', 'unknown')
                method_counts[method] = method_counts.get(method, 0) + 1
            
            # Group by page ranges
            page_ranges = {
                '1-50': 0, '51-100': 0, '101-150': 0, '151-200': 0, '201+': 0
            }
            for topic in topics:
                page = topic.get('page', 0)
                if page <= 50:
                    page_ranges['1-50'] += 1
                elif page <= 100:
                    page_ranges['51-100'] += 1
                elif page <= 150:
                    page_ranges['101-150'] += 1
                elif page <= 200:
                    page_ranges['151-200'] += 1
                else:
                    page_ranges['201+'] += 1
            
            print(f"\n📈 Analysis:")
            print(f"   🤖 Topics processed by parallel GPT: {gpt_filtered_count}")
            print(f"   📊 Average confidence: {avg_confidence:.3f}")
            print(f"   📄 Page distribution: {dict(page_ranges)}")
            
            print(f"\n🔧 Extraction methods:")
            for method, count in sorted(method_counts.items()):
                print(f"   {method}: {count} topics")
            
            # Show sample high-confidence topics
            high_confidence_topics = [t for t in topics if t.get('confidence', 0) > 0.8]
            print(f"\n✨ High-confidence topics ({len(high_confidence_topics)} total):")
            for i, topic in enumerate(high_confidence_topics[:15]):
                page = topic.get('page', '?')
                conf = topic.get('confidence', 0)
                method = topic.get('extraction_method', '?')
                gpt_status = '✓' if topic.get('gpt_filtered', False) else '○'
                print(f"   {i+1:2d}. \"{topic['topic'][:60]}...\" (p{page}, {conf:.2f}, {method}) [GPT:{gpt_status}]")
            
            if len(high_confidence_topics) > 15:
                print(f"   ... and {len(high_confidence_topics) - 15} more high-confidence topics")
            
            # Show some medium-confidence topics
            medium_confidence_topics = [t for t in topics if 0.5 <= t.get('confidence', 0) <= 0.8]
            if medium_confidence_topics:
                print(f"\n📋 Medium-confidence topics (showing first 10 of {len(medium_confidence_topics)}):")
                for i, topic in enumerate(medium_confidence_topics[:10]):
                    page = topic.get('page', '?')
                    conf = topic.get('confidence', 0)
                    gpt_status = '✓' if topic.get('gpt_filtered', False) else '○'
                    print(f"   {i+1:2d}. \"{topic['topic'][:50]}...\" (p{page}, {conf:.2f}) [GPT:{gpt_status}]")
            
            # Save results with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save detailed JSON
            json_file = f"output/book2_extraction_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'source_file': pdf_path,
                        'extraction_date': timestamp,
                        'processing_time_seconds': processing_time,
                        'total_topics': len(topics),
                        'gpt_filtered_count': gpt_filtered_count,
                        'average_confidence': avg_confidence,
                        'extraction_methods': method_counts,
                        'page_distribution': page_ranges
                    },
                    'topics': topics
                }, f, indent=2, ensure_ascii=False)
            
            # Save summary report
            report_file = f"output/book2_summary_{timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"Topic Extraction Summary - book2.pdf\\n")
                f.write(f"=" * 50 + "\\n\\n")
                f.write(f"Processing Date: {timestamp}\\n")
                f.write(f"Processing Time: {processing_time:.2f} seconds\\n")
                f.write(f"Total Topics: {len(topics)}\\n")
                f.write(f"GPT Filtered: {gpt_filtered_count}\\n")
                f.write(f"Average Confidence: {avg_confidence:.3f}\\n\\n")
                
                f.write(f"High-Confidence Topics (confidence > 0.8):\\n")
                f.write(f"-" * 40 + "\\n")
                for i, topic in enumerate(high_confidence_topics[:20], 1):
                    f.write(f"{i:2d}. {topic['topic']} (Page {topic.get('page', '?')})\\n")
                
                if len(high_confidence_topics) > 20:
                    f.write(f"... and {len(high_confidence_topics) - 20} more\\n")
            
            print(f"\n💾 Results saved:")
            print(f"   📄 Detailed JSON: {json_file}")
            print(f"   📋 Summary report: {report_file}")
            
            print(f"\n🎉 SUCCESS! Extracted {len(topics)} genuine educational topics from book2.pdf")
            
        else:
            print("❌ No topics were extracted")
            
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()

def test_sample_parallel_gpt():
    """Quick test of parallel GPT filtering with sample data"""
    
    print("🧪 Quick Parallel GPT Test")
    print("=" * 40)
    
    # Sample topics for testing parallel processing
    sample_topics = [
        {"topic": "Chapter 5: Signal Processing Fundamentals", "page": 101, "confidence": 0.9},
        {"topic": "5.1 Discrete-Time Signals", "page": 102, "confidence": 0.8},
        {"topic": "Example 5.3: Sampling Rate Conversion", "page": 108, "confidence": 0.6},
        {"topic": "5.2 Z-Transform Properties", "page": 115, "confidence": 0.8},
        {"topic": "Definition 5.1: Region of Convergence", "page": 118, "confidence": 0.9},
        {"topic": "Exercise 5.12", "page": 125, "confidence": 0.4},
        {"topic": "Theorem 5.2: Convolution Theorem", "page": 130, "confidence": 0.9},
        {"topic": "Figure 5.7: Frequency Response", "page": 135, "confidence": 0.3},
        {"topic": "5.3 Digital Filter Design", "page": 140, "confidence": 0.8},
        {"topic": "Problem Set 5", "page": 150, "confidence": 0.2}
    ]
    
    try:
        # Just test the GPT filtering component
        extractor = AdvancedMultiStrategyExtractor("doc/book2.pdf")
        
        print(f"📝 Testing parallel GPT filtering on {len(sample_topics)} sample topics...")
        
        start_time = datetime.now()
        filtered = extractor._filter_by_gpt_parallel(sample_topics)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"\\n📊 Results:")
        print(f"   ⏱️ Processing time: {processing_time:.2f} seconds") 
        print(f"   📥 Input topics: {len(sample_topics)}")
        print(f"   📤 Filtered topics: {len(filtered)}")
        print(f"   📈 Retention rate: {(len(filtered)/len(sample_topics))*100:.1f}%")
        
        print(f"\\n✅ Kept topics:")
        for i, topic in enumerate(filtered, 1):
            gpt_status = "✓" if topic.get('gpt_filtered', False) else "○"
            batch_id = topic.get('batch_id', '?')
            print(f"   {i}. \"{topic['topic']}\" (Page {topic['page']}) [GPT:{gpt_status}, Batch:{batch_id}]")
            
    except Exception as e:
        print(f"❌ Error in parallel GPT test: {e}")

if __name__ == "__main__":
    print("Choose test type:")
    print("1. Full extraction test on book2.pdf")
    print("2. Quick parallel GPT test with sample data")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_book2_extraction()
    elif choice == "2":
        test_sample_parallel_gpt()
    else:
        print("Invalid choice. Running full extraction test...")
        test_book2_extraction()
