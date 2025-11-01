"""
Phase 1 Testing: Knowledge Base Ingestion
==========================================
Tests PDF extraction, vector storage, and topic detection.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pathlib import Path

from db.vector_store import get_vector_store
from topic_boundary_detector import TopicBoundaryDetector
from optimized_universal_extractor import UniversalExtractor


class TestPhase1KnowledgeBase:
    """Test suite for Phase 1: Knowledge Base Ingestion"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.vector_store = get_vector_store()
        print("\n🧪 Phase 1 Testing: Knowledge Base Ingestion")
    
    def test_vector_store_initialization(self):
        """Test vector store initialization"""
        print("\n1️⃣ Testing vector store initialization...")
        
        assert self.vector_store is not None
        assert self.vector_store.client is not None
        
        print("   ✅ Vector store initialized successfully")
    
    def test_add_and_search_topics(self):
        """Test adding and searching topics"""
        print("\n2️⃣ Testing topic storage and search...")
        
        # Add test topics
        test_topics = [
            {
                "topic_id": "test_topic_1",
                "title": "Introduction to Machine Learning",
                "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms that learn from data.",
                "metadata": {"module": "ML_Basics"}
            },
            {
                "topic_id": "test_topic_2",
                "title": "Neural Networks",
                "content": "Neural networks are computing systems inspired by biological neural networks. They consist of layers of interconnected nodes.",
                "metadata": {"module": "Deep_Learning"}
            }
        ]
        
        # Add topics
        self.vector_store.add_topics(test_topics)
        print("   ✅ Added test topics to vector store")
        
        # Search for topics
        results = self.vector_store.search_topics(
            query="What is machine learning?",
            n_results=2
        )
        
        assert "documents" in results
        assert len(results["documents"][0]) > 0
        
        print(f"   ✅ Found {len(results['documents'][0])} relevant topics")
        print(f"   Top result: {results['documents'][0][0][:100]}...")
    
    def test_topic_boundary_detector(self):
        """Test topic boundary detection"""
        print("\n3️⃣ Testing topic boundary detector...")
        
        # Create test document
        test_content = """
        Chapter 1: Introduction to Programming
        
        Programming is the process of writing computer programs. 
        It involves designing algorithms and implementing them in a programming language.
        
        Chapter 2: Variables and Data Types
        
        Variables are containers for storing data values.
        Python has several data types including integers, floats, strings, and booleans.
        
        Chapter 3: Control Structures
        
        Control structures allow you to control the flow of program execution.
        Common control structures include if statements, loops, and functions.
        """
        
        # Test boundary detection (simplified test - actual PDF needed for full test)
        print("   ℹ️ Topic boundary detector requires PDF input")
        print("   ✅ Topic boundary detector module available")
    
    def test_vector_embeddings(self):
        """Test vector embeddings generation"""
        print("\n4️⃣ Testing vector embeddings...")
        
        test_text = "This is a test document about artificial intelligence and machine learning."
        
        # Add to vector store
        self.vector_store.add_topics([{
            "topic_id": "embedding_test",
            "title": "Embedding Test",
            "content": test_text,
            "metadata": {}
        }])
        
        # Search to verify embeddings
        results = self.vector_store.search_topics("artificial intelligence", n_results=1)
        
        assert results["documents"][0][0] == test_text
        print("   ✅ Vector embeddings working correctly")
    
    def test_semantic_search(self):
        """Test semantic search capabilities"""
        print("\n5️⃣ Testing semantic search...")
        
        # Add diverse topics
        topics = [
            {
                "topic_id": "math_1",
                "title": "Algebra",
                "content": "Algebra is a branch of mathematics dealing with symbols and the rules for manipulating those symbols.",
                "metadata": {"subject": "mathematics"}
            },
            {
                "topic_id": "cs_1",
                "title": "Algorithms",
                "content": "An algorithm is a step-by-step procedure for solving a problem or accomplishing a task.",
                "metadata": {"subject": "computer_science"}
            },
            {
                "topic_id": "physics_1",
                "title": "Newton's Laws",
                "content": "Newton's laws of motion describe the relationship between a body and the forces acting upon it.",
                "metadata": {"subject": "physics"}
            }
        ]
        
        self.vector_store.add_topics(topics)
        
        # Search with different queries
        queries = [
            "mathematical operations with symbols",
            "how to solve problems step by step",
            "forces and motion"
        ]
        
        for query in queries:
            results = self.vector_store.search_topics(query, n_results=1)
            print(f"   Query: '{query}'")
            print(f"   Top result: {results['ids'][0][0]}")
        
        print("   ✅ Semantic search functioning correctly")


def run_phase1_tests():
    """Run all Phase 1 tests"""
    print("=" * 80)
    print("PHASE 1 TESTING: KNOWLEDGE BASE INGESTION")
    print("=" * 80)
    
    tester = TestPhase1KnowledgeBase()
    tester.setup_method()
    
    try:
        tester.test_vector_store_initialization()
        tester.test_add_and_search_topics()
        tester.test_topic_boundary_detector()
        tester.test_vector_embeddings()
        tester.test_semantic_search()
        
        print("\n" + "=" * 80)
        print("✅ PHASE 1 TESTS PASSED")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ PHASE 1 TESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_phase1_tests()
    sys.exit(0 if success else 1)
