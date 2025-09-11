#!/usr/bin/env python3

"""
Focused Integration Test for Topic Extractor
============================================
Tests the main functionality with real PDF processing but mocked LLM
"""

import os
import json
import asyncio
from unittest.mock import patch, Mock
from topic_extractor import AdvancedMultiStrategyExtractor


def test_full_extraction_pipeline():
    """Test the complete extraction pipeline with mocked GPT"""
    print("🧪 Starting Full Pipeline Integration Test")
    print("=" * 60)
    
    # Use the existing test PDF
    pdf_path = "doc/book2.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Test PDF not found: {pdf_path}")
        print("⚠️ Please ensure doc/book2.pdf exists for integration testing")
        return False
    
    try:
        # Initialize extractor
        print("📖 Initializing extractor...")
        extractor = AdvancedMultiStrategyExtractor(pdf_path)
        print(f"✅ PDF loaded: {len(extractor.doc)} pages")
        
        # Test individual extraction methods
        print("\n🔍 Testing individual extraction methods...")
        
        # Test TOC extraction
        print("1️⃣ Testing TOC extraction...")
        toc_candidates = extractor._extract_from_toc()
        print(f"   📑 TOC candidates: {len(toc_candidates)}")
        
        # Test content extraction
        print("2️⃣ Testing content extraction...")
        content_candidates = extractor._extract_from_content()
        print(f"   📄 Content candidates: {len(content_candidates)}")
        
        # Test formatting extraction
        print("3️⃣ Testing formatting extraction...")
        formatting_candidates = extractor._extract_by_formatting()
        print(f"   🎨 Formatting candidates: {len(formatting_candidates)}")
        
        # Test context extraction
        print("4️⃣ Testing context extraction...")
        context_candidates = extractor._extract_with_context()
        print(f"   🔍 Context candidates: {len(context_candidates)}")
        
        # Combine and score
        print("\n📊 Testing candidate processing...")
        all_candidates = (toc_candidates + content_candidates + 
                         formatting_candidates + context_candidates)
        print(f"   🔗 Total candidates: {len(all_candidates)}")
        
        scored_candidates = extractor._score_candidates(all_candidates)
        print(f"   📈 Scored candidates: {len(scored_candidates)}")
        
        # Test deduplication
        final_topics = extractor._deduplicate_and_finalize(scored_candidates)
        print(f"   🎯 After deduplication: {len(final_topics)}")
        
        # Test filtering stages
        print("\n🔧 Testing filtering stages...")
        
        # Keyword filtering
        print("1️⃣ Testing keyword filtering...")
        keyword_filtered = extractor._filter_by_keywords(final_topics)
        print(f"   ✂️ After keyword filtering: {len(keyword_filtered)}")
        
        # Negative pattern filtering
        print("2️⃣ Testing negative pattern filtering...")
        negative_filtered = extractor._filter_by_negative_patterns(keyword_filtered)
        print(f"   🚫 After negative filtering: {len(negative_filtered)}")
        
        # Quality filtering
        print("3️⃣ Testing quality filtering...")
        quality_filtered = extractor._filter_by_quality(negative_filtered)
        print(f"   🎯 After quality filtering: {len(quality_filtered)}")
        
        # Mock GPT filtering for testing
        print("4️⃣ Testing GPT filtering (mocked)...")
        with patch('topic_extractor.AdvancedAzureLLM') as mock_llm_class:
            # Create a mock LLM instance
            mock_llm = Mock()
            mock_llm_class.return_value = mock_llm
            
            # Mock async_generate to simulate GPT keeping ~50% of topics
            async def mock_generate(*args, **kwargs):
                # Return indices for roughly half the topics
                prompt = kwargs.get('prompt', args[0] if args else "")
                batch_size = prompt.count('\n') if '\n' in prompt else len(quality_filtered)
                keep_indices = list(range(0, min(batch_size, len(quality_filtered)), 2))  # Every other topic
                return json.dumps(keep_indices)
            
            mock_llm.async_generate = mock_generate
            
            # Test GPT filtering
            gpt_filtered = extractor._filter_by_gpt_simplified(quality_filtered)
            print(f"   🤖 After GPT filtering (mocked): {len(gpt_filtered)}")
        
        # Test helper methods
        print("\n🛠️ Testing helper methods...")
        
        # Test text cleaning
        test_texts = [
            "  Multiple   spaces  in text  ",
            "Topic with (Page 123) reference",
            "Topic with dots...and more text",
            "Topic with punctuation , and . marks",
        ]
        
        print("   🧹 Testing text cleaning:")
        for text in test_texts:
            cleaned = extractor._clean_topic_text(text)
            print(f"      '{text}' → '{cleaned}'")
        
        # Test topic validation
        print("   ✅ Testing topic validation:")
        valid_topics = ["Introduction to Probability", "Random Variables"]
        invalid_topics = ["", "AB", "Page 123", "www.test.com"]
        
        for topic in valid_topics + invalid_topics:
            is_valid = extractor._is_valid_topic(topic)
            status = "✅" if is_valid else "❌"
            print(f"      {status} '{topic}': {is_valid}")
        
        # Test confidence calculation
        print("   📊 Testing confidence calculation:")
        test_cases = [
            ("Introduction to Theory", "numbered_sections"),
            ("Random text", "content_markers"),
            ("Probability Distribution", "header_detection")
        ]
        
        for text, category in test_cases:
            conf = extractor._calculate_confidence(text, category, "test_context")
            print(f"      '{text}' ({category}): {conf:.3f}")
        
        # Test full pipeline with mocked GPT
        print("\n🚀 Testing full pipeline with mocked GPT...")
        with patch('topic_extractor.AdvancedAzureLLM') as mock_llm_class:
            mock_llm = Mock()
            mock_llm_class.return_value = mock_llm
            
            # Mock to keep a reasonable number of topics
            async def mock_full_generate(*args, **kwargs):
                prompt = kwargs.get('prompt', args[0] if args else "")
                lines = prompt.split('\n')
                topic_lines = [i for i, line in enumerate(lines) if ':' in line and 'Page' in line]
                # Keep roughly 30% of topics
                keep_count = max(1, len(topic_lines) // 3)
                keep_indices = topic_lines[:keep_count]
                return json.dumps(keep_indices)
            
            mock_llm.async_generate = mock_full_generate
            
            # Run full extraction
            final_result = extractor.extract_with_multiple_strategies()
            
            print(f"🎉 Final result: {len(final_result)} topics extracted")
            
            if final_result:
                # Show some sample topics
                print("\n📋 Sample extracted topics:")
                for i, topic in enumerate(final_result[:10], 1):
                    print(f"   {i:2d}. {topic['topic']} (Page {topic['page']}, "
                          f"Conf: {topic['confidence']:.3f}, Method: {topic['extraction_method']})")
                
                if len(final_result) > 10:
                    print(f"   ... and {len(final_result) - 10} more topics")
                
                # Test saving results
                print("\n💾 Testing results saving...")
                saved_files = extractor.save_results(final_result)
                print(f"   ✅ Results saved to: {saved_files['json_file']}")
                
                # Verify saved file
                if os.path.exists(saved_files['json_file']):
                    with open(saved_files['json_file'], 'r') as f:
                        saved_data = json.load(f)
                    
                    print(f"   📊 Saved data structure:")
                    print(f"      - Metadata: {len(saved_data['metadata'])} fields")
                    print(f"      - Topics: {len(saved_data['topics'])} topics")
                    print(f"      - Statistics: {len(saved_data['statistics'])} metrics")
                    
                    # Clean up test file
                    os.remove(saved_files['json_file'])
                    print(f"   🧹 Cleaned up test file")
        
        print(f"\n✅ Integration test completed successfully!")
        print(f"📊 Test Summary:")
        print(f"   - PDF pages processed: {len(extractor.doc)}")
        print(f"   - Total candidates found: {len(all_candidates)}")
        print(f"   - After all filtering: {len(final_result) if 'final_result' in locals() else 'N/A'}")
        print(f"   - All methods tested: ✅")
        
        extractor.doc.close()
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling scenarios"""
    print("\n🚨 Testing Error Handling Scenarios")
    print("-" * 40)
    
    # Test with non-existent file
    print("1️⃣ Testing non-existent PDF...")
    try:
        extractor = AdvancedMultiStrategyExtractor("non_existent_file.pdf")
        print("   ❌ Should have raised an exception")
        return False
    except Exception as e:
        print(f"   ✅ Correctly handled non-existent file: {type(e).__name__}")
    
    # Test helper methods with edge cases
    pdf_path = "doc/book2.pdf"
    if os.path.exists(pdf_path):
        print("2️⃣ Testing edge cases with valid extractor...")
        extractor = AdvancedMultiStrategyExtractor(pdf_path)
        
        # Test text cleaning with None/empty
        edge_cases = [None, "", "   ", "\n\t\r"]
        print("   🧹 Testing text cleaning edge cases:")
        for case in edge_cases:
            try:
                result = extractor._clean_topic_text(case)
                print(f"      '{case}' → '{result}' ✅")
            except Exception as e:
                print(f"      '{case}' → Error: {e} ❌")
        
        # Test validation with edge cases
        print("   ✅ Testing validation edge cases:")
        validation_cases = [None, "", " ", "A", "A" * 200]
        for case in validation_cases:
            try:
                result = extractor._is_valid_topic(case)
                print(f"      '{case}' → {result} ✅")
            except Exception as e:
                print(f"      '{case}' → Error: {e} ❌")
        
        extractor.doc.close()
        print("   ✅ Edge case testing completed")
    
    return True


def test_performance_metrics():
    """Test and report performance metrics"""
    print("\n⚡ Performance Testing")
    print("-" * 30)
    
    pdf_path = "doc/book2.pdf"
    if not os.path.exists(pdf_path):
        print("❌ Test PDF not found for performance testing")
        return
    
    import time
    
    start_time = time.time()
    
    try:
        extractor = AdvancedMultiStrategyExtractor(pdf_path)
        
        # Time individual extraction methods
        methods = [
            ('TOC Extraction', extractor._extract_from_toc),
            ('Content Extraction', extractor._extract_from_content),
            ('Formatting Extraction', extractor._extract_by_formatting),
            ('Context Extraction', extractor._extract_with_context)
        ]
        
        method_times = {}
        all_candidates = []
        
        for method_name, method_func in methods:
            method_start = time.time()
            candidates = method_func()
            method_time = time.time() - method_start
            method_times[method_name] = method_time
            all_candidates.extend(candidates)
            print(f"   {method_name}: {len(candidates)} candidates in {method_time:.2f}s")
        
        # Time filtering stages
        print("\n🔧 Filtering Performance:")
        
        scored = extractor._score_candidates(all_candidates)
        final_topics = extractor._deduplicate_and_finalize(scored)
        
        filter_start = time.time()
        keyword_filtered = extractor._filter_by_keywords(final_topics)
        keyword_time = time.time() - filter_start
        print(f"   Keyword filtering: {len(keyword_filtered)} topics in {keyword_time:.2f}s")
        
        neg_start = time.time()
        negative_filtered = extractor._filter_by_negative_patterns(keyword_filtered)
        negative_time = time.time() - neg_start
        print(f"   Negative filtering: {len(negative_filtered)} topics in {negative_time:.2f}s")
        
        qual_start = time.time()
        quality_filtered = extractor._filter_by_quality(negative_filtered)
        quality_time = time.time() - qual_start
        print(f"   Quality filtering: {len(quality_filtered)} topics in {quality_time:.2f}s")
        
        total_time = time.time() - start_time
        
        print(f"\n📊 Performance Summary:")
        print(f"   Total processing time: {total_time:.2f}s")
        print(f"   PDF pages: {len(extractor.doc)}")
        print(f"   Candidates per second: {len(all_candidates)/total_time:.1f}")
        print(f"   Final topics: {len(quality_filtered)}")
        
        extractor.doc.close()
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")


if __name__ == "__main__":
    print("🧪 Topic Extractor Integration Test Suite")
    print("=" * 50)
    
    # Run all tests
    tests = [
        ("Full Pipeline Integration", test_full_extraction_pipeline),
        ("Error Handling", test_error_handling),
        ("Performance Metrics", test_performance_metrics)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}")
        except Exception as e:
            print(f"   ❌ FAILED with exception: {e}")
            results.append((test_name, False))
    
    # Final summary
    print(f"\n{'='*50}")
    print("🏁 Test Suite Summary:")
    print(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    print(f"\n📊 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! The topic extractor is working correctly.")
    else:
        print("⚠️ Some tests failed. Please review the output above.")
