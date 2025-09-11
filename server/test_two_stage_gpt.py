#!/usr/bin/env python3
"""
Test Two-Stage GPT Filtering
============================
Tests the new two-stage GPT filtering process on book2.pdf
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from topic_extractor import AdvancedMultiStrategyExtractor
import json
from datetime import datetime

def test_two_stage_filtering():
    """Test the two-stage GPT filtering on book2.pdf"""
    
    print("🎯 Two-Stage GPT Filtering Test - book2.pdf")
    print("=" * 60)
    
    pdf_path = "doc/book2.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    print(f"📖 Processing: {pdf_path}")
    print(f"🔄 Pipeline: Multi-strategy → Keyword → Quality → Two-Stage GPT")
    print(f"    📚 Stage 1: Keep all educational content") 
    print(f"    📖 Stage 2: Keep only high-quality curriculum topics")
    print()
    
    try:
        # Initialize extractor
        extractor = AdvancedMultiStrategyExtractor(pdf_path)
        
        # Run the complete extraction pipeline with two-stage filtering
        start_time = datetime.now()
        print("🚀 Starting complete extraction with two-stage GPT filtering...")
        
        # This will run: multi-strategy → keyword → quality → two-stage GPT
        topics = extractor.extract_with_multiple_strategies()
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"\n🎉 TWO-STAGE EXTRACTION COMPLETE!")
        print(f"   ⏱️ Total processing time: {processing_time:.2f} seconds")
        print(f"   🏆 Final high-quality topics: {len(topics)}")
        
        if topics:
            # Analyze results
            stage1_count = sum(1 for topic in topics if topic.get('gpt_stage1_filtered', False))
            stage2_count = sum(1 for topic in topics if topic.get('gpt_stage2_filtered', False))
            avg_confidence = sum(topic.get('confidence', 0) for topic in topics) / len(topics)
            
            # Analyze by extraction method
            method_counts = {}
            for topic in topics:
                method = topic.get('extraction_method', 'unknown')
                method_counts[method] = method_counts.get(method, 0) + 1
            
            # Analyze by confidence ranges
            confidence_ranges = {
                'Very High (0.9+)': 0, 'High (0.8-0.9)': 0, 
                'Medium (0.6-0.8)': 0, 'Low (<0.6)': 0
            }
            for topic in topics:
                conf = topic.get('confidence', 0)
                if conf >= 0.9:
                    confidence_ranges['Very High (0.9+)'] += 1
                elif conf >= 0.8:
                    confidence_ranges['High (0.8-0.9)'] += 1
                elif conf >= 0.6:
                    confidence_ranges['Medium (0.6-0.8)'] += 1
                else:
                    confidence_ranges['Low (<0.6)'] += 1
            
            print(f"\n📊 DETAILED ANALYSIS:")
            print(f"   🤖 Stage 1 GPT processed: {stage1_count}")
            print(f"   🎯 Stage 2 GPT processed: {stage2_count}")
            print(f"   📊 Average confidence: {avg_confidence:.3f}")
            
            print(f"\n🔧 Extraction methods:")
            for method, count in sorted(method_counts.items()):
                print(f"   {method}: {count} topics")
                
            print(f"\n📈 Confidence distribution:")
            for range_name, count in confidence_ranges.items():
                print(f"   {range_name}: {count} topics")
            
            # Show top high-confidence topics
            high_confidence_topics = sorted(
                [t for t in topics if t.get('confidence', 0) > 0.8],
                key=lambda x: x.get('confidence', 0), 
                reverse=True
            )
            
            print(f"\n✨ TOP HIGH-CONFIDENCE TOPICS ({len(high_confidence_topics)} total):")
            for i, topic in enumerate(high_confidence_topics[:20]):
                page = topic.get('page', '?')
                conf = topic.get('confidence', 0)
                method = topic.get('extraction_method', '?')
                stage1 = '✓' if topic.get('gpt_stage1_filtered', False) else '○'
                stage2 = '✓' if topic.get('gpt_stage2_filtered', False) else '○'
                print(f"   {i+1:2d}. \"{topic['topic'][:70]}...\" (p{page}, {conf:.2f}, {method})")
                print(f"       [Stage1:{stage1}, Stage2:{stage2}]")
            
            if len(high_confidence_topics) > 20:
                print(f"   ... and {len(high_confidence_topics) - 20} more high-confidence topics")
            
            # Show some medium confidence topics  
            medium_topics = [t for t in topics if 0.6 <= t.get('confidence', 0) < 0.8]
            if medium_topics:
                print(f"\n📋 MEDIUM-CONFIDENCE TOPICS (showing first 10 of {len(medium_topics)}):")
                for i, topic in enumerate(medium_topics[:10]):
                    page = topic.get('page', '?')
                    conf = topic.get('confidence', 0)
                    stage1 = '✓' if topic.get('gpt_stage1_filtered', False) else '○'
                    stage2 = '✓' if topic.get('gpt_stage2_filtered', False) else '○'
                    print(f"   {i+1:2d}. \"{topic['topic'][:60]}...\" (p{page}, {conf:.2f}) [S1:{stage1}, S2:{stage2}]")
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save detailed JSON
            json_file = f"output/book2_two_stage_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'source_file': pdf_path,
                        'extraction_date': timestamp,
                        'processing_time_seconds': processing_time,
                        'total_topics': len(topics),
                        'stage1_gpt_count': stage1_count,
                        'stage2_gpt_count': stage2_count,
                        'average_confidence': avg_confidence,
                        'extraction_methods': method_counts,
                        'confidence_distribution': confidence_ranges,
                        'filtering_pipeline': 'multi_strategy → keyword → quality → two_stage_gpt'
                    },
                    'topics': topics
                }, f, indent=2, ensure_ascii=False)
            
            # Save summary report
            report_file = f"output/book2_two_stage_summary_{timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"Two-Stage GPT Filtering Results - book2.pdf\\n")
                f.write(f"=" * 50 + "\\n\\n")
                f.write(f"Processing Date: {timestamp}\\n")
                f.write(f"Processing Time: {processing_time:.2f} seconds\\n")
                f.write(f"Final Topics: {len(topics)}\\n")
                f.write(f"Average Confidence: {avg_confidence:.3f}\\n\\n")
                
                f.write(f"Two-Stage GPT Results:\\n")
                f.write(f"Stage 1 (Educational): {stage1_count} topics\\n")
                f.write(f"Stage 2 (Quality): {stage2_count} topics\\n\\n")
                
                f.write(f"Top High-Confidence Topics:\\n")
                f.write(f"-" * 40 + "\\n")
                for i, topic in enumerate(high_confidence_topics[:25], 1):
                    f.write(f"{i:2d}. {topic['topic']} (Page {topic.get('page', '?')}, {topic.get('confidence', 0):.2f})\\n")
                
                if len(high_confidence_topics) > 25:
                    f.write(f"... and {len(high_confidence_topics) - 25} more\\n")
            
            print(f"\n💾 Results saved:")
            print(f"   📄 Detailed JSON: {json_file}")
            print(f"   📋 Summary report: {report_file}")
            
            print(f"\n🎉 SUCCESS! Two-stage filtering extracted {len(topics)} high-quality topics")
            print(f"   📚 Stage 1: Kept educational content")
            print(f"   📖 Stage 2: Refined to curriculum-quality topics")
            
        else:
            print("❌ No topics survived the two-stage filtering")
            
    except Exception as e:
        print(f"❌ Error during two-stage extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_two_stage_filtering()
