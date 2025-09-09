#!/usr/bin/env python3
"""
Specific Topic Boundary Detection Test
=====================================
Test the boundary detection system on a specific topic "6.6 SAMPLING FROM A FINITE POPULATION"
by searching through the PDF to find where this topic actually appears.
"""

import fitz  # PyMuPDF
from topic_boundary_detector import TopicBoundaryDetector
import re

class SpecificTopicAnalyzer:
    def __init__(self, pdf_path="doc/book2.pdf"):
        self.pdf_path = pdf_path
        self.detector = TopicBoundaryDetector(pdf_path)
        
    def find_topic_location(self, topic_title):
        """Find where a specific topic appears in the PDF"""
        print(f"🔍 Searching for topic: '{topic_title}'")
        print("=" * 60)
        
        doc = fitz.open(self.pdf_path)
        matches = []
        
        # Search for the topic in the PDF
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Look for the topic title (case insensitive)
            if topic_title.lower() in text.lower():
                # Find the exact position and context
                lines = text.split('\n')
                for line_num, line in enumerate(lines):
                    if topic_title.lower() in line.lower():
                        matches.append({
                            'page': page_num + 1,
                            'line': line_num,
                            'content': line.strip(),
                            'context': lines[max(0, line_num-2):line_num+3]
                        })
        
        doc.close()
        
        if matches:
            print(f"✅ Found {len(matches)} matches for '{topic_title}':")
            for i, match in enumerate(matches):
                print(f"\n📍 Match {i+1}:")
                print(f"   📄 Page: {match['page']}")
                print(f"   📝 Line: '{match['content']}'")
                print(f"   📋 Context:")
                for ctx_line in match['context']:
                    if ctx_line.strip():
                        marker = "➡️ " if topic_title.lower() in ctx_line.lower() else "   "
                        print(f"      {marker}{ctx_line.strip()}")
        else:
            print(f"❌ Topic '{topic_title}' not found in PDF")
            
        return matches
    
    def analyze_topic_boundaries(self, topic_title, start_page=None, page_range=20):
        """Analyze boundaries for a specific topic"""
        
        if start_page:
            print(f"🎯 Using provided start page: {start_page}")
        else:
            # Find where the topic appears
            matches = self.find_topic_location(topic_title)
            
            if not matches:
                print(f"\n⚠️  Topic not found, analyzing from beginning...")
                start_page = 1
            else:
                # Use the first match as starting point
                start_page = matches[0]['page']
                print(f"\n🎯 Starting analysis from page {start_page} where topic was found")
        
        print(f"\n🚀 TOPIC BOUNDARY ANALYSIS")
        print("=" * 50)
        print(f"📖 Topic: {topic_title}")
        print(f"📄 Starting from page: {start_page}")
        print(f"📊 Analyzing {page_range} pages")
        
        # Special handling for 7.3 INTERVAL ESTIMATES
        if "7.3 INTERVAL ESTIMATES" in topic_title:
            print(f"🎯 Expected Structure:")
            print(f"   📄 Main topic starts: 309")
            print(f"   📄 Subtopic transitions: 314, 319, 321")  
            print(f"   📄 Topic ends: 322")
        
        print("-" * 50)
        
        # Create a topic object for the detector
        topic_obj = {
            'title': topic_title,
            'topic': topic_title,
            'start_page': start_page
        }
        
        # Run boundary detection starting from the found page
        boundaries = self.detector.run_full_detection(
            start_page=start_page,
            end_page=start_page + page_range - 1
        )
        
        if boundaries:
            print(f"\n✅ BOUNDARY DETECTION RESULTS")
            print("=" * 40)
            print(f"📊 Total Sections Detected: {len(boundaries)}")
            
            topic_end = max(boundary.end_page for boundary in boundaries)
            print(f"🎯 Topic '{topic_title}' appears to end at page {topic_end}")
            
            print(f"\n📋 Detailed Sections:")
            for i, boundary in enumerate(boundaries, 1):
                print(f"\n📖 Section {i}: {boundary.topic_title}")
                print(f"   📄 Pages: {boundary.start_page}-{boundary.end_page}")
                print(f"   🎯 Confidence: {boundary.confidence:.3f}")
                print(f"   🔍 Type: {boundary.boundary_type}")
                print(f"   📝 Content: {boundary.content_summary[:150]}...")
                
        else:
            print("❌ No boundaries detected")
            
        return boundaries

def main():
    """Main execution"""
    print("🎯 Specific Topic Boundary Detection Test")
    print("=" * 60)
    
    analyzer = SpecificTopicAnalyzer()
    
    # Test the specific topic starting from page 309
    topic = "7.3 INTERVAL ESTIMATES"
    boundaries = analyzer.analyze_topic_boundaries(topic, start_page=309, page_range=15)
    
    print(f"\n🎉 ANALYSIS COMPLETE!")
    print("📁 Check output/ folder for detailed results and visualizations")

if __name__ == "__main__":
    main()
