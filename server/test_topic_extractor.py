#!/usr/bin/env python3

"""
Comprehensive Test Suite for AdvancedMultiStrategyExtractor
==========================================================
Tests all extraction methods, filtering mechanisms, and edge cases
"""

import unittest
import tempfile
import os
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict
import fitz  # PyMuPDF

# Import the modules to test
from topic_extractor import AdvancedMultiStrategyExtractor, TopicCandidate


class TestTopicCandidate(unittest.TestCase):
    """Test the TopicCandidate dataclass"""
    
    def test_topic_candidate_creation(self):
        """Test basic TopicCandidate creation"""
        candidate = TopicCandidate(
            text="Sample Topic",
            page=1,
            confidence=0.8,
            extraction_method="toc",
            context="test_context",
            position="header"
        )
        
        self.assertEqual(candidate.text, "Sample Topic")
        self.assertEqual(candidate.page, 1)
        self.assertEqual(candidate.confidence, 0.8)
        self.assertEqual(candidate.extraction_method, "toc")
        self.assertEqual(candidate.context, "test_context")
        self.assertEqual(candidate.position, "header")
        self.assertFalse(candidate.is_filtered)
        self.assertEqual(candidate.filter_reason, "")
    
    def test_topic_candidate_filtering(self):
        """Test TopicCandidate filtering attributes"""
        candidate = TopicCandidate(
            text="Test Topic",
            page=1,
            confidence=0.5,
            extraction_method="content",
            context="test",
            position="body",
            is_filtered=True,
            filter_reason="test_reason"
        )
        
        self.assertTrue(candidate.is_filtered)
        self.assertEqual(candidate.filter_reason, "test_reason")


class TestAdvancedMultiStrategyExtractor(unittest.TestCase):
    """Test the main extractor class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary PDF for testing
        self.test_pdf_path = self._create_test_pdf()
        self.extractor = AdvancedMultiStrategyExtractor(self.test_pdf_path)
    
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self, 'test_pdf_path') and os.path.exists(self.test_pdf_path):
            os.unlink(self.test_pdf_path)
        if hasattr(self.extractor, 'doc'):
            self.extractor.doc.close()
    
    def _create_test_pdf(self) -> str:
        """Create a simple test PDF"""
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        doc = fitz.open()
        
        # Add test content
        page1 = doc.new_page()
        page1.insert_text((50, 100), "1.1 Introduction to Probability", fontsize=16)
        page1.insert_text((50, 130), "This chapter covers basic probability concepts.")
        page1.insert_text((50, 160), "Example 1.1 Rolling a Die")
        page1.insert_text((50, 190), "Consider rolling a fair six-sided die.")
        
        page2 = doc.new_page()
        page2.insert_text((50, 100), "2.1 Random Variables", fontsize=16)
        page2.insert_text((50, 130), "Definition 2.1 A random variable is a function.")
        page2.insert_text((50, 160), "Figure 2.1 shows the distribution.")
        
        # Add a TOC
        doc.set_toc([
            [1, "Introduction to Probability", 1],
            [1, "Random Variables", 2],
            [2, "Definition of Random Variables", 2]
        ])
        
        doc.save(temp_pdf.name)
        doc.close()
        temp_pdf.close()
        
        return temp_pdf.name
    
    def test_extractor_initialization(self):
        """Test extractor initialization"""
        self.assertIsNotNone(self.extractor.doc)
        self.assertEqual(self.extractor.pdf_path, self.test_pdf_path)
        self.assertIsInstance(self.extractor.candidates, list)
        self.assertIsInstance(self.extractor.final_topics, list)
        self.assertIsInstance(self.extractor.example_keywords, list)
        self.assertIsInstance(self.extractor.concluding_keywords, list)
        self.assertIsInstance(self.extractor.exclusion_phrases, list)
    
    def test_extract_from_toc(self):
        """Test TOC extraction"""
        candidates = self.extractor._extract_from_toc()
        
        self.assertIsInstance(candidates, list)
        self.assertGreater(len(candidates), 0)
        
        # Check that TOC candidates have the right properties
        for candidate in candidates:
            self.assertIsInstance(candidate, TopicCandidate)
            self.assertEqual(candidate.extraction_method, 'toc')
            self.assertEqual(candidate.position, 'toc')
            self.assertEqual(candidate.confidence, 0.9)  # TOC has high confidence
    
    def test_extract_from_content(self):
        """Test content extraction"""
        candidates = self.extractor._extract_from_content()
        
        self.assertIsInstance(candidates, list)
        # Content extraction should find patterns in our test PDF
        
        for candidate in candidates:
            self.assertIsInstance(candidate, TopicCandidate)
            self.assertEqual(candidate.extraction_method, 'content_pattern')
            self.assertEqual(candidate.position, 'body')
    
    def test_extract_by_formatting(self):
        """Test formatting-based extraction"""
        candidates = self.extractor._extract_by_formatting()
        
        self.assertIsInstance(candidates, list)
        
        for candidate in candidates:
            self.assertIsInstance(candidate, TopicCandidate)
            self.assertEqual(candidate.extraction_method, 'formatting')
            self.assertEqual(candidate.position, 'header')
    
    def test_extract_with_context(self):
        """Test context-aware extraction"""
        candidates = self.extractor._extract_with_context()
        
        self.assertIsInstance(candidates, list)
        
        for candidate in candidates:
            self.assertIsInstance(candidate, TopicCandidate)
            self.assertEqual(candidate.extraction_method, 'context')
            self.assertEqual(candidate.position, 'body')
    
    def test_score_candidates(self):
        """Test candidate scoring"""
        # Create test candidates
        candidates = [
            TopicCandidate("Introduction", 1, 0.5, "test", "test", "header"),
            TopicCandidate("Probability Theory", 2, 0.6, "test", "test", "body"),
            TopicCandidate("Ex", 3, 0.4, "test", "test", "body"),  # Very short
            TopicCandidate("Definition of Random Variables", 4, 0.7, "test", "test", "header")
        ]
        
        scored = self.extractor._score_candidates(candidates)
        
        self.assertEqual(len(scored), 4)
        # Check that candidates are sorted by confidence
        confidences = [c.confidence for c in scored]
        self.assertEqual(confidences, sorted(confidences, reverse=True))
    
    def test_deduplicate_and_finalize(self):
        """Test deduplication and finalization"""
        candidates = [
            TopicCandidate("Same Topic", 1, 0.8, "toc", "test", "header"),
            TopicCandidate("Same Topic", 1, 0.7, "content", "test", "body"),  # Duplicate
            TopicCandidate("Different Topic", 2, 0.6, "toc", "test", "header"),
            TopicCandidate("Low Confidence", 3, 0.2, "content", "test", "body")  # Too low confidence
        ]
        
        final_topics = self.extractor._deduplicate_and_finalize(candidates)
        
        # Should remove duplicate and low confidence topic
        self.assertEqual(len(final_topics), 2)
        self.assertIsInstance(final_topics[0], dict)
        
        # Check topic structure
        topic = final_topics[0]
        self.assertIn('topic', topic)
        self.assertIn('page', topic)
        self.assertIn('confidence', topic)
        self.assertIn('extraction_method', topic)
        self.assertIn('context', topic)
        self.assertIn('position', topic)
    
    def test_filter_by_keywords(self):
        """Test keyword-based filtering"""
        topics = [
            {'topic': 'Introduction to Probability', 'page': 1, 'confidence': 0.8},
            {'topic': 'Example 1.1 Rolling a Die', 'page': 1, 'confidence': 0.7},  # Should be filtered
            {'topic': 'Definition of Variables', 'page': 2, 'confidence': 0.9},
            {'topic': 'However, this shows that', 'page': 2, 'confidence': 0.6},  # Should be filtered
            {'topic': 'Figure 2.1 Distribution', 'page': 2, 'confidence': 0.5}  # Should be filtered
        ]
        
        filtered = self.extractor._filter_by_keywords(topics)
        
        # Should keep only topics without problematic keywords
        self.assertEqual(len(filtered), 2)  # Introduction and Definition should remain
        remaining_topics = [t['topic'] for t in filtered]
        self.assertIn('Introduction to Probability', remaining_topics)
        self.assertIn('Definition of Variables', remaining_topics)
    
    def test_filter_by_negative_patterns(self):
        """Test negative pattern filtering"""
        topics = [
            {'topic': 'Probability Theory', 'page': 1, 'confidence': 0.8},
            {'topic': '51.3 Hi Honolulu', 'page': 2, 'confidence': 0.7},  # Should be filtered
            {'topic': 'Random Variables', 'page': 3, 'confidence': 0.9},
            {'topic': 'www.example.com', 'page': 4, 'confidence': 0.6},  # Should be filtered
            {'topic': 'A', 'page': 5, 'confidence': 0.5}  # Should be filtered (too short)
        ]
        
        filtered = self.extractor._filter_by_negative_patterns(topics)
        
        # Should remove topics matching negative patterns
        self.assertEqual(len(filtered), 2)  # Only Probability Theory and Random Variables
        remaining_topics = [t['topic'] for t in filtered]
        self.assertIn('Probability Theory', remaining_topics)
        self.assertIn('Random Variables', remaining_topics)
    
    def test_filter_by_quality(self):
        """Test quality-based filtering"""
        topics = [
            {'topic': 'Probability Theory and Applications', 'page': 1, 'confidence': 0.8},
            {'topic': 'ABC', 'page': 2, 'confidence': 0.7},  # Too short
            {'topic': '12345 67890', 'page': 3, 'confidence': 0.6},  # Mostly numbers
            {'topic': 'AAAAA AAAAA', 'page': 4, 'confidence': 0.5},  # Too repetitive
            {'topic': 'Statistics and Inference', 'page': 5, 'confidence': 0.9}
        ]
        
        filtered = self.extractor._filter_by_quality(topics)
        
        # Should keep only high-quality topics
        self.assertEqual(len(filtered), 2)
        remaining_topics = [t['topic'] for t in filtered]
        self.assertIn('Probability Theory and Applications', remaining_topics)
        self.assertIn('Statistics and Inference', remaining_topics)
    
    def test_clean_topic_text(self):
        """Test text cleaning functionality"""
        test_cases = [
            ("  Multiple   spaces  ", "Multiple spaces"),
            ("Topic with (Page 123)", "Topic with"),
            ("Topic with dots...and more", "Topic with dots"),
            ("Topic with ellipsis…", "Topic with ellipsis"),
            ("Topic , with punctuation .", "Topic, with punctuation"),
            ("", ""),
            (None, "")
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.extractor._clean_topic_text(input_text)
                self.assertEqual(result, expected)
    
    def test_is_valid_topic(self):
        """Test topic validation"""
        valid_topics = [
            "Introduction to Probability",
            "Random Variables and Distributions",
            "Statistical Inference Methods"
        ]
        
        invalid_topics = [
            "",  # Empty
            "AB",  # Too short
            "A" * 121,  # Too long
            "123",  # Just numbers
            "A",  # Single letter
            "Page 123",  # Page reference
            "www.example.com",  # URL
            "copyright 2023"  # Copyright
        ]
        
        for topic in valid_topics:
            with self.subTest(topic=topic):
                self.assertTrue(self.extractor._is_valid_topic(topic))
        
        for topic in invalid_topics:
            with self.subTest(topic=topic):
                self.assertFalse(self.extractor._is_valid_topic(topic))
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        # Test with high-value keywords
        conf1 = self.extractor._calculate_confidence(
            "Introduction to Probability Theory", "numbered_sections", "context"
        )
        self.assertGreater(conf1, 0.8)  # Should be boosted
        
        # Test without keywords
        conf2 = self.extractor._calculate_confidence(
            "Random Text", "content_markers", "context"
        )
        self.assertEqual(conf2, 0.6)  # Base confidence for content_markers
    
    def test_looks_like_header(self):
        """Test header detection"""
        headers = [
            "1.1 Introduction",
            "Chapter 5 Statistics",
            "PROBABILITY THEORY",
            "Example 2.3 Sampling",
            "Definition 1.1 Random Variable"
        ]
        
        non_headers = [
            "This is a regular sentence.",
            "some lowercase text",
            "Mixed Case But Not Header Pattern"
        ]
        
        for header in headers:
            with self.subTest(header=header):
                self.assertTrue(self.extractor._looks_like_header(header))
        
        for non_header in non_headers:
            with self.subTest(non_header=non_header):
                self.assertFalse(self.extractor._looks_like_header(non_header))
    
    def test_has_topic_indicators(self):
        """Test topic indicator detection"""
        indicator_lines = [
            "Example 1.1 shows that",
            "Definition: A random variable",
            "Theorem 3.2 states that",
            "Problem 5.1 asks us to"
        ]
        
        non_indicator_lines = [
            "This is just regular text",
            "Some random sentence",
            "No indicators here"
        ]
        
        for line in indicator_lines:
            with self.subTest(line=line):
                self.assertTrue(self.extractor._has_topic_indicators(line))
        
        for line in non_indicator_lines:
            with self.subTest(line=line):
                self.assertFalse(self.extractor._has_topic_indicators(line))
    
    def test_extract_topics_from_context(self):
        """Test context-based topic extraction"""
        context_text = """
        1.1 Introduction to Probability Theory
        This section covers basic concepts.
        EXAMPLE 2.3a Coin Flipping
        We examine the probability of heads.
        DEFINITION 3.1 Random Variable
        A function from sample space to real numbers.
        """
        
        topics = self.extractor._extract_topics_from_context(context_text)
        
        self.assertIsInstance(topics, list)
        self.assertGreater(len(topics), 0)
    
    @patch('topic_extractor.AdvancedAzureLLM')
    def test_filter_by_gpt_simplified_no_llm(self, mock_llm_class):
        """Test GPT filtering when LLM is not available"""
        # Mock LLM initialization failure
        mock_llm_class.side_effect = Exception("LLM not available")
        
        topics = [
            {'topic': 'Test Topic 1', 'page': 1, 'confidence': 0.8},
            {'topic': 'Test Topic 2', 'page': 2, 'confidence': 0.7}
        ]
        
        # Should return original topics when LLM fails
        filtered = self.extractor._filter_by_gpt_simplified(topics)
        self.assertEqual(len(filtered), len(topics))
    
    def test_save_results(self):
        """Test results saving functionality"""
        topics = [
            {'topic': 'Test Topic 1', 'page': 1, 'confidence': 0.8, 'extraction_method': 'toc'},
            {'topic': 'Test Topic 2', 'page': 2, 'confidence': 0.7, 'extraction_method': 'content'}
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory for testing
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                result = self.extractor.save_results(topics)
                
                self.assertIn('json_file', result)
                self.assertTrue(os.path.exists(result['json_file']))
                
                # Verify JSON content
                with open(result['json_file'], 'r') as f:
                    data = json.load(f)
                
                self.assertIn('metadata', data)
                self.assertIn('topics', data)
                self.assertIn('statistics', data)
                self.assertEqual(len(data['topics']), 2)
                
            finally:
                os.chdir(original_cwd)
    
    def test_extract_with_multiple_strategies_integration(self):
        """Integration test for the main extraction method"""
        # This test may take some time due to GPT filtering, so we'll mock it
        with patch.object(self.extractor, '_filter_by_gpt_simplified', return_value=[
            {'topic': 'Introduction to Probability', 'page': 1, 'confidence': 0.9, 'extraction_method': 'toc'},
            {'topic': 'Random Variables', 'page': 2, 'confidence': 0.8, 'extraction_method': 'content'}
        ]):
            topics = self.extractor.extract_with_multiple_strategies()
            
            self.assertIsInstance(topics, list)
            self.assertGreater(len(topics), 0)
            
            # Verify topic structure
            for topic in topics:
                self.assertIn('topic', topic)
                self.assertIn('page', topic)
                self.assertIn('confidence', topic)
                self.assertIn('extraction_method', topic)


class TestAsyncGPTFiltering(unittest.TestCase):
    """Test async GPT filtering methods"""
    
    def setUp(self):
        """Set up for async tests"""
        self.test_pdf_path = self._create_minimal_pdf()
        self.extractor = AdvancedMultiStrategyExtractor(self.test_pdf_path)
        
        # Mock LLM
        self.mock_llm = Mock()
        self.mock_llm.async_generate = Mock()
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_pdf_path):
            os.unlink(self.test_pdf_path)
        self.extractor.doc.close()
    
    def _create_minimal_pdf(self) -> str:
        """Create a minimal test PDF"""
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 100), "Test content")
        doc.save(temp_pdf.name)
        doc.close()
        temp_pdf.close()
        return temp_pdf.name
    
    def test_process_simplified_batch_success(self):
        """Test successful batch processing"""
        async def run_test():
            batch = [
                {'topic': 'Introduction to Statistics', 'page': 1},
                {'topic': 'Example 1.1 Coin Flip', 'page': 2},
                {'topic': 'Random Variables Theory', 'page': 3}
            ]
            
            # Mock successful GPT response
            self.mock_llm.async_generate.return_value = "[0, 2]"  # Keep indices 0 and 2
            
            result_topics, kept_count = await self.extractor._process_simplified_batch(
                batch, 0, self.mock_llm
            )
            
            self.assertEqual(kept_count, 2)
            self.assertEqual(len(result_topics), 2)
            
            # Check that correct topics were kept
            kept_topic_texts = [t['topic'] for t in result_topics]
            self.assertIn('Introduction to Statistics', kept_topic_texts)
            self.assertIn('Random Variables Theory', kept_topic_texts)
            self.assertNotIn('Example 1.1 Coin Flip', kept_topic_texts)
        
        asyncio.run(run_test())
    
    def test_process_simplified_batch_json_error(self):
        """Test batch processing with JSON parsing error"""
        async def run_test():
            batch = [
                {'topic': 'Test Topic 1', 'page': 1},
                {'topic': 'Test Topic 2', 'page': 2}
            ]
            
            # Mock invalid JSON response
            self.mock_llm.async_generate.return_value = "Invalid JSON response"
            
            result_topics, kept_count = await self.extractor._process_simplified_batch(
                batch, 0, self.mock_llm
            )
            
            # Should fallback to keeping all topics
            self.assertEqual(kept_count, 2)
            self.assertEqual(len(result_topics), 2)
        
        asyncio.run(run_test())
    
    def test_process_simplified_batch_exception(self):
        """Test batch processing with exception"""
        async def run_test():
            batch = [
                {'topic': 'Test Topic', 'page': 1}
            ]
            
            # Mock exception during processing
            self.mock_llm.async_generate.side_effect = Exception("GPT API error")
            
            result_topics, kept_count = await self.extractor._process_simplified_batch(
                batch, 0, self.mock_llm
            )
            
            # Should fallback to keeping all topics
            self.assertEqual(kept_count, 1)
            self.assertEqual(len(result_topics), 1)
        
        asyncio.run(run_test())


class TestExtractorEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_nonexistent_pdf(self):
        """Test handling of non-existent PDF file"""
        with self.assertRaises(Exception):
            AdvancedMultiStrategyExtractor("nonexistent_file.pdf")
    
    def test_empty_pdf(self):
        """Test handling of empty PDF"""
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        doc = fitz.open()
        doc.new_page()  # Empty page
        doc.save(temp_pdf.name)
        doc.close()
        temp_pdf.close()
        
        try:
            extractor = AdvancedMultiStrategyExtractor(temp_pdf.name)
            topics = extractor._extract_from_toc()  # Should handle empty TOC
            self.assertIsInstance(topics, list)
            extractor.doc.close()
        finally:
            os.unlink(temp_pdf.name)
    
    def test_pdf_with_no_toc(self):
        """Test PDF without table of contents"""
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 100), "Some content without TOC")
        doc.save(temp_pdf.name)
        doc.close()
        temp_pdf.close()
        
        try:
            extractor = AdvancedMultiStrategyExtractor(temp_pdf.name)
            candidates = extractor._extract_from_toc()
            self.assertIsInstance(candidates, list)
            # Should be empty or minimal since no TOC
            extractor.doc.close()
        finally:
            os.unlink(temp_pdf.name)


if __name__ == '__main__':
    # Configure test runner
    unittest.TestLoader.testMethodPrefix = 'test_'
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestTopicCandidate,
        TestAdvancedMultiStrategyExtractor,
        TestAsyncGPTFiltering,
        TestExtractorEdgeCases
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    print(f"{'='*60}")
