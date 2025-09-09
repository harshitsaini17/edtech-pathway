#!/usr/bin/env python3
"""
🎯 Enhanced Topic Boundary Detector - Demo with Specific Topics
===============================================================
Demonstrates precise topic boundary detection using both extracted topics and vector embeddings.

This version:
1. Uses previously extracted topics as starting points
2. Performs detailed boundary detection from topic start page onwards
3. Shows exactly where each topic's content ends

Usage:
    python topic_boundary_demo.py
"""

import os
import json
from datetime import datetime
from topic_boundary_detector import TopicBoundaryDetector

class TopicBoundaryDemo:
    """Demo class to show topic boundary detection with specific topics"""
    
    def __init__(self):
        self.pdf_path = "doc/book2.pdf"
        self.detector = None
        
    def find_latest_topic_file(self):
        """Find the latest topic extraction file"""
        output_dir = "output"
        if not os.path.exists(output_dir):
            return None
            
        topic_files = [f for f in os.listdir(output_dir) 
                      if ('optimized_universal' in f or 'curriculum' in f) and f.endswith('.json')]
        
        if not topic_files:
            return None
            
        topic_files.sort(reverse=True)
        return os.path.join(output_dir, topic_files[0])
        
    def load_specific_topics(self):
        """Load specific topics to demonstrate boundary detection"""
        topics_file = self.find_latest_topic_file()
        if not topics_file:
            print("❌ No topic extraction files found")
            return []
            
        try:
            with open(topics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different file formats
            topics = []
            
            if 'topics' in data:
                topics = data['topics']
            elif 'modules' in data:
                # Curriculum file - extract all topics from modules
                for module in data['modules']:
                    module_topics = module.get('topics', [])
                    for topic in module_topics:
                        # Ensure topic is in correct format
                        if isinstance(topic, str):
                            # Simple string topic - convert to dict
                            topics.append({'title': topic, 'page': 1})
                        elif isinstance(topic, dict):
                            topics.append(topic)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, str):
                        topics.append({'title': item, 'page': 1})
                    elif isinstance(item, dict):
                        topics.append(item)
            
            # Filter to get valid topics with page numbers
            valid_topics = []
            for topic in topics:
                if isinstance(topic, dict) and ('page' in topic or 'title' in topic or 'topic' in topic):
                    valid_topics.append(topic)
                    
            return valid_topics[:10]  # First 10 topics for demo
            
        except Exception as e:
            print(f"❌ Error loading topics: {e}")
            return []
            
    def detect_boundaries_for_topic(self, topic_info, page_range=5):
        """
        Detect precise boundaries for a specific topic
        
        Args:
            topic_info: Dictionary with topic information
            page_range: Number of pages to analyze after topic start
        """
        title = topic_info.get('title', topic_info.get('topic', 'Unknown Topic'))
        start_page = topic_info.get('page', 1)
        
        print(f"\n🎯 Analyzing Topic: {title}")
        print(f"📄 Starting from page: {start_page}")
        print("-" * 60)
        
        # Analyze from topic start page for specified range
        end_page = start_page + page_range - 1
        
        # Run boundary detection
        boundaries = self.detector.run_full_detection(start_page, end_page)
        
        if boundaries:
            print(f"\n📊 Found {len(boundaries)} topic sections:")
            for i, boundary in enumerate(boundaries, 1):
                print(f"   Section {i}: {boundary.topic_title}")
                print(f"   📄 Pages: {boundary.start_page}-{boundary.end_page}")
                print(f"   🎯 Confidence: {boundary.confidence:.3f}")
                
        return boundaries
        
    def run_comprehensive_demo(self):
        """Run a comprehensive demonstration"""
        print("🎯 Enhanced Topic Boundary Detection Demo")
        print("=" * 60)
        
        if not os.path.exists(self.pdf_path):
            print(f"❌ PDF file not found: {self.pdf_path}")
            return
            
        # Initialize detector
        self.detector = TopicBoundaryDetector(self.pdf_path)
        
        # Load topics
        topics = self.load_specific_topics()
        if not topics:
            print("❌ No topics found for demo")
            return
            
        print(f"📚 Loaded {len(topics)} topics for boundary detection demo")
        
        # Test the specific topic requested by user
        test_topic = "6.6 SAMPLING FROM A FINITE POPULATION"
        
        print(f"\n🚀 TESTING SPECIFIC TOPIC: {test_topic}")
        print("=" * 80)
        
        # Single topic test - create topic object
        demo_topics = [{"title": test_topic, "topic": test_topic}]
        
        for i, topic in enumerate(demo_topics, 1):
            print(f"\n🔍 TOPIC TEST {i}/1")
            boundaries = self.detect_boundaries_for_topic(topic, page_range=50)  # Increased range for specific topic
            
            if boundaries:
                # Show the actual end page detected for this topic
                topic_end = max(boundary.end_page for boundary in boundaries)
                topic_title = topic.get('title', topic.get('topic', 'Unknown'))
                
                print(f"\n✅ RESULT: Topic '{topic_title}' ends at page {topic_end}")
                
                # Show content summary of the detected boundaries
                print("\n📝 Content Summary:")
                for boundary in boundaries:
                    print(f"   Pages {boundary.start_page}-{boundary.end_page}: {boundary.content_summary[:100]}...")
                    
            print("\n" + "="*40)
            
        print("\n🎉 DEMO COMPLETE!")
        print("📁 Check output/ folder for detailed results and visualizations")


def main():
    """Main demo execution"""
    try:
        demo = TopicBoundaryDemo()
        demo.run_comprehensive_demo()
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("📦 Install with: pip install sentence-transformers scikit-learn matplotlib seaborn")
    except Exception as e:
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    main()
