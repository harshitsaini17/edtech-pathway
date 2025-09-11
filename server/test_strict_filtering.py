#!/usr/bin/env python3
"""
Test Strict Two-Stage GPT Filtering
===================================
Tests the updated aggressive two-stage filtering to target 200-300 final topics from 2242
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from topic_extractor import AdvancedMultiStrategyExtractor
import json
from datetime import datetime

def test_strict_filtering():
    """Test the strict two-stage filtering on book2.pdf"""
    
    print("🎯 Testing STRICT Two-Stage GPT Filtering")
    print("=" * 60)
    print("Target: 200-300 final topics from ~2200 input topics")
    print()
    
    try:
        # Initialize extractor
        extractor = AdvancedMultiStrategyExtractor("doc/book2.pdf")
        
        print("📊 Step 1: Running multi-strategy extraction...")
        all_topics = extractor.extract_with_multiple_strategies()
        
        if not all_topics:
            print("❌ No topics extracted from initial strategies")
            return
            
        print(f"✅ Initial extraction: {len(all_topics)} topics")
        
        # Get topics before GPT filtering (after keyword filtering)
        print("\n📊 Step 2: Getting topics after keyword filtering...")
        
        # We need to simulate getting topics after keyword filtering but before GPT
        # Let's extract manually to see the intermediate step
        extractor_test = AdvancedMultiStrategyExtractor("doc/book2.pdf")
        
        # Get raw topics from all strategies
        raw_topics = []
        
        # Strategy 1: Content pattern (combining TOC and content extraction)
        toc_topics = extractor_test._extract_from_toc()
        for topic_candidate in toc_topics:
            topic = {
                'topic': topic_candidate.text,
                'page': topic_candidate.page,
                'confidence': topic_candidate.confidence,
                'extraction_method': 'content_pattern'
            }
            raw_topics.append(topic)
            
        content_topics = extractor_test._extract_from_content()
        for topic_candidate in content_topics:
            topic = {
                'topic': topic_candidate.text,
                'page': topic_candidate.page,
                'confidence': topic_candidate.confidence,
                'extraction_method': 'content_pattern'
            }
            raw_topics.append(topic)
        
        # Strategy 2: Formatting
        format_topics = extractor_test._extract_by_formatting()
        for topic_candidate in format_topics:
            topic = {
                'topic': topic_candidate.text,
                'page': topic_candidate.page,
                'confidence': topic_candidate.confidence,
                'extraction_method': 'formatting'
            }
            raw_topics.append(topic)
        
        # Strategy 3: Context
        context_topics = extractor_test._extract_with_context()
        for topic_candidate in context_topics:
            topic = {
                'topic': topic_candidate.text,
                'page': topic_candidate.page,
                'confidence': topic_candidate.confidence,
                'extraction_method': 'context'
            }
            raw_topics.append(topic)
        
        print(f"📄 Raw topics from all strategies: {len(raw_topics)}")
        
        # Apply keyword filtering
        print("\n📊 Step 3: Applying keyword filtering...")
        keyword_filtered = extractor_test._filter_by_keywords(raw_topics)
        print(f"🔧 After keyword filtering: {len(keyword_filtered)} topics")
        retention_after_keywords = len(keyword_filtered) / len(raw_topics) * 100
        print(f"📈 Keyword retention rate: {retention_after_keywords:.1f}%")
        
        # Now apply strict two-stage GPT filtering
        print(f"\n📊 Step 4: Applying STRICT two-stage GPT filtering...")
        print(f"🎯 Target: Get from {len(keyword_filtered)} → 200-300 topics")
        
        start_time = datetime.now()
        final_topics = extractor_test._filter_by_gpt_two_stage(keyword_filtered)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        # Results analysis
        print(f"\n🏆 STRICT FILTERING RESULTS:")
        print(f"   📊 Raw topics (all strategies): {len(raw_topics)}")
        print(f"   🔧 After keyword filtering: {len(keyword_filtered)} ({retention_after_keywords:.1f}%)")
        print(f"   🤖 After two-stage GPT: {len(final_topics)}")
        print(f"   ⏱️ Processing time: {processing_time:.1f} seconds")
        
        overall_retention = len(final_topics) / len(raw_topics) * 100
        gpt_retention = len(final_topics) / len(keyword_filtered) * 100
        
        print(f"\n📈 Retention Analysis:")
        print(f"   🔧 Keyword filtering: {retention_after_keywords:.1f}% retention")
        print(f"   🤖 Two-stage GPT: {gpt_retention:.1f}% retention")
        print(f"   🎯 Overall pipeline: {overall_retention:.1f}% retention")
        
        # Check if we hit our target
        if 200 <= len(final_topics) <= 300:
            print(f"✅ SUCCESS! Hit target range: {len(final_topics)} topics (200-300)")
        elif len(final_topics) < 200:
            print(f"⚠️ Under target: {len(final_topics)} topics (need 200+)")
            print("   💡 Consider making filtering less aggressive")
        else:
            print(f"⚠️ Over target: {len(final_topics)} topics (target <300)")
            print("   💡 Consider making filtering more aggressive")
            
        # Show sample final topics
        print(f"\n🎯 Sample Final Topics (showing first 15):")
        for i, topic in enumerate(final_topics[:15], 1):
            page = topic.get('page', '?')
            conf = topic.get('confidence', 0)
            method = topic.get('extraction_method', '?')
            stage1 = '✓' if topic.get('gpt_stage1_filtered', False) else '○'
            stage2 = '✓' if topic.get('gpt_stage2_filtered', False) else '○'
            print(f"   {i:2d}. \"{topic['topic'][:60]}...\" (p{page}, {conf:.2f}, {method}) [S1:{stage1}, S2:{stage2}]")
            
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/strict_filtering_test_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_metadata': {
                    'test_date': timestamp,
                    'processing_time_seconds': processing_time,
                    'raw_topics_count': len(raw_topics),
                    'keyword_filtered_count': len(keyword_filtered),
                    'final_topics_count': len(final_topics),
                    'keyword_retention_percent': retention_after_keywords,
                    'gpt_retention_percent': gpt_retention,
                    'overall_retention_percent': overall_retention,
                    'target_achieved': 200 <= len(final_topics) <= 300
                },
                'final_topics': final_topics
            }, f, indent=2, ensure_ascii=False)
            
        print(f"\n💾 Results saved to: {output_file}")
        
        return len(final_topics)
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    test_strict_filtering()
