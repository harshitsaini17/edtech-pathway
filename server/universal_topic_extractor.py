"""
Universal Book Topic Extractor
=============================
Extracts headings, topics, and sub-topics from any PDF book.
Combines techniques from both technical and academic book structures.

Features:
- Works with both technical books (like book.pdf) and academic textbooks (like book2.pdf)
- Handles various numbering schemes (1.1, 1.1.1, Chapter 1, Section A, etc.)
- Filters out unwanted content fragments
- Supports Table of Contents extraction when available
- Adaptive pattern recognition for different book formats
- Clean output with hierarchical structure

Usage:
    python universal_topic_extractor.py <pdf_file_path>
    
Example:
    python universal_topic_extractor.py doc/book.pdf
    python universal_topic_extractor.py doc/book2.pdf
"""

import fitz  # PyMuPDF
import re
import sys
import os
from datetime import datetime
from typing import List, Dict, Set, Tuple

class UniversalTopicExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_filename = os.path.basename(pdf_path).replace('.pdf', '')
        self.doc = fitz.open(pdf_path)
        self.topics = []
        self.seen_topics = set()
        
        # Comprehensive regex patterns for different book styles
        self.patterns = {
            # Standard numbered sections (1.1, 1.1.1, 1.1.1.1)
            'numbered_sections': [
                r'\b(\d{1,2}\.\d{1,2}(?:\.\d{1,2})*(?:\.\d{1,2})*)\s+([A-Z][A-Za-z\s\-\(\)&,.:]+?)(?=\s*\n|\s*\(Page|\s*$)',
                r'^(\d{1,2}\.\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Za-z\s\-\(\)&,.:]+?)(?=\s*\n|\s*\(|\s*$)',
            ],
            
            # Chapter patterns
            'chapters': [
                r'\b(Chapter\s+\d{1,2})\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:]+?)(?=\s*\n|\s*\(Page|\s*$)',
                r'\b(CHAPTER\s+\d{1,2})\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:]+?)(?=\s*\n|\s*\(Page|\s*$)',
            ],
            
            # Section patterns
            'sections': [
                r'\b(Section\s+\d{1,2}(?:\.\d{1,2})*)\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:]+?)(?=\s*\n|\s*\(Page|\s*$)',
                r'\b(SECTION\s+\d{1,2}(?:\.\d{1,2})*)\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:]+?)(?=\s*\n|\s*\(Page|\s*$)',
            ],
            
            # Alphabetic sections (A.1, B.2, etc.)
            'alpha_sections': [
                r'\b([A-Z]\.\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Za-z\s\-\(\)&,.:]+?)(?=\s*\n|\s*\(Page|\s*$)',
            ],
            
            # Roman numeral sections
            'roman_sections': [
                r'\b([IVX]{1,6})\.\s+([A-Z][A-Za-z\s\-\(\)&,.:]+?)(?=\s*\n|\s*\(Page|\s*$)',
            ],
            
            # All caps headings (common in academic books)
            'caps_headings': [
                r'\b([A-Z][A-Z\s\-\(\)&,.:]{10,50})(?=\s*\n|\s*\(Page|\s*$)',
            ]
        }
        
        # Quality keywords for filtering meaningful topics
        self.quality_keywords = {
            'good': [
                'introduction', 'definition', 'theorem', 'proof', 'example', 'solution',
                'method', 'algorithm', 'analysis', 'theory', 'principle', 'law',
                'equation', 'formula', 'distribution', 'probability', 'statistics',
                'regression', 'correlation', 'variance', 'mean', 'deviation',
                'hypothesis', 'test', 'confidence', 'interval', 'estimation',
                'sampling', 'population', 'variable', 'function', 'derivative',
                'integral', 'limit', 'series', 'matrix', 'vector', 'system',
                'model', 'optimization', 'linear', 'nonlinear', 'differential',
                'applications', 'problems', 'exercises', 'summary', 'review',
                'appendix', 'references', 'bibliography', 'glossary', 'index'
            ],
            'bad': [
                'page', 'figure', 'table', 'graph', 'chart', 'diagram',
                'copyright', 'isbn', 'publisher', 'edition', 'printing',
                'acknowledgment', 'preface', 'foreword', 'dedication',
                'contents', 'this book', 'the author', 'we will', 'in this'
            ]
        }
    
    def extract_toc_topics(self) -> List[Tuple[str, int]]:
        """Extract topics from Table of Contents if available"""
        toc_topics = []
        try:
            toc = self.doc.get_toc()
            if toc:
                print(f"Found TOC with {len(toc)} entries")
                for level, title, page in toc:
                    if title and len(title.strip()) > 3:
                        clean_title = title.strip()
                        # Filter out common TOC noise
                        if not any(word in clean_title.lower() for word in ['contents', 'index', 'bibliography', 'preface']):
                            toc_topics.append((clean_title, page))
            return toc_topics
        except Exception as e:
            print(f"TOC extraction error: {e}")
            return []
    
    def is_quality_topic(self, text: str) -> bool:
        """Check if a topic is meaningful based on content and keywords"""
        text_lower = text.lower()
        
        # Length filters
        if len(text) < 5 or len(text) > 100:
            return False
        
        # Check for bad keywords
        if any(bad_word in text_lower for bad_word in self.quality_keywords['bad']):
            return False
        
        # Must contain at least some alphabetic characters
        if not re.search(r'[a-zA-Z]', text):
            return False
        
        # Filter out sentences (topics shouldn't be full sentences)
        if text.count('.') > 2 or text.count(',') > 3:
            return False
        
        # Filter out fragments with weird patterns
        if re.search(r'\d{4,}|\w{30,}|[^\w\s\-\(\)&,.:]{3,}', text):
            return False
        
        # Prefer topics with good keywords
        has_good_keywords = any(good_word in text_lower for good_word in self.quality_keywords['good'])
        
        # Accept if has good keywords or looks like a proper heading
        if has_good_keywords or re.match(r'^\d+\.\d+', text) or text.isupper():
            return True
        
        # Accept if it looks like a proper title (title case)
        words = text.split()
        if len(words) >= 2 and len(words) <= 10:
            title_case_words = sum(1 for word in words if word[0].isupper() and len(word) > 1)
            if title_case_words >= len(words) * 0.5:
                return True
        
        return False
    
    def clean_topic_text(self, text: str) -> str:
        """Clean and normalize topic text"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common suffixes
        text = re.sub(r'\s*\(Page\s+\d+\).*$', '', text)
        text = re.sub(r'\s*\.\.\.$', '', text)
        text = re.sub(r'\s*…$', '', text)
        
        # Clean up punctuation
        text = re.sub(r'\s+([,.;:])', r'\1', text)
        text = re.sub(r'([,.;:])\s*$', '', text)
        
        return text.strip()
    
    def extract_patterns_from_text(self, text: str, page_num: int) -> List[Tuple[str, str, int]]:
        """Extract topics using regex patterns"""
        found_topics = []
        
        for pattern_group, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) >= 2:
                        number = match.group(1).strip()
                        title = match.group(2).strip()
                    else:
                        number = ""
                        title = match.group(1).strip()
                    
                    # Clean the title
                    title = self.clean_topic_text(title)
                    
                    if title and self.is_quality_topic(title):
                        full_topic = f"{number} {title}".strip()
                        if full_topic not in self.seen_topics:
                            found_topics.append((full_topic, pattern_group, page_num))
                            self.seen_topics.add(full_topic)
        
        return found_topics
    
    def extract_topics_from_pdf(self) -> List[Dict]:
        """Main extraction method"""
        print(f"Extracting topics from: {self.pdf_path}")
        print(f"Total pages: {len(self.doc)}")
        
        # First, try TOC extraction
        toc_topics = self.extract_toc_topics()
        if toc_topics:
            print(f"Using TOC-based extraction with {len(toc_topics)} topics")
            for topic, page in toc_topics:
                if topic not in self.seen_topics:
                    self.topics.append({
                        'topic': topic,
                        'page': page,
                        'source': 'toc'
                    })
                    self.seen_topics.add(topic)
        
        # Pattern-based extraction from content
        pattern_topics_count = 0
        for page_num in range(len(self.doc)):
            try:
                page = self.doc[page_num]
                text = page.get_text()
                
                if text.strip():
                    found_topics = self.extract_patterns_from_text(text, page_num + 1)
                    for topic, source, page_n in found_topics:
                        self.topics.append({
                            'topic': topic,
                            'page': page_n,
                            'source': source
                        })
                        pattern_topics_count += 1
                
            except Exception as e:
                print(f"Error processing page {page_num + 1}: {e}")
                continue
        
        print(f"Pattern-based extraction found: {pattern_topics_count} topics")
        print(f"Total topics extracted: {len(self.topics)}")
        
        return self.topics
    
    def save_results(self):
        """Save extraction results to multiple formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory if it doesn't exist
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # JSON format
        json_file = os.path.join(output_dir, f"{self.pdf_filename}_universal_topics_{timestamp}.json")
        import json
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.topics, f, indent=2, ensure_ascii=False)
        
        # Simple text list
        list_file = os.path.join(output_dir, f"{self.pdf_filename}_universal_topics_list_{timestamp}.txt")
        with open(list_file, 'w', encoding='utf-8') as f:
            f.write(f"{self.pdf_filename.upper()} UNIVERSAL TOPICS - FOR CONTENT EXTRACTION\n")
            f.write("=" * 70 + "\n\n")
            
            for i, topic_data in enumerate(self.topics, 1):
                f.write(f"{i}. {topic_data['topic']} (Page {topic_data['page']})\n")
        
        # Structured markdown
        md_file = os.path.join(output_dir, f"{self.pdf_filename}_universal_topics_{timestamp}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# {self.pdf_filename.replace('_', ' ').title()} - Universal Topics\n\n")
            f.write(f"**Extraction Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Topics:** {len(self.topics)}\n")
            f.write(f"**Source File:** {self.pdf_path}\n\n")
            
            # Group by source
            sources = {}
            for topic_data in self.topics:
                source = topic_data['source']
                if source not in sources:
                    sources[source] = []
                sources[source].append(topic_data)
            
            for source, topics in sources.items():
                f.write(f"## {source.upper()} Topics ({len(topics)} items)\n\n")
                for topic_data in topics:
                    f.write(f"- **{topic_data['topic']}** (Page {topic_data['page']})\n")
                f.write("\n")
        
        print(f"\n✅ Results saved:")
        print(f"📄 JSON: {json_file}")
        print(f"📝 List: {list_file}")
        print(f"📋 Markdown: {md_file}")
        
        return {
            'json_file': json_file,
            'list_file': list_file,
            'md_file': md_file
        }

def main():
    if len(sys.argv) != 2:
        print("Usage: python universal_topic_extractor.py <pdf_file_path>")
        print("\nExamples:")
        print("  python universal_topic_extractor.py doc/book.pdf")
        print("  python universal_topic_extractor.py doc/book2.pdf")
        return
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        return
    
    try:
        extractor = UniversalTopicExtractor(pdf_path)
        topics = extractor.extract_topics_from_pdf()
        
        if topics:
            files = extractor.save_results()
            print(f"\n🎉 Successfully extracted {len(topics)} topics!")
            
            # Show sample topics
            print(f"\n📋 Sample topics:")
            for i, topic_data in enumerate(topics[:10], 1):
                print(f"  {i}. {topic_data['topic']} (Page {topic_data['page']})")
            
            if len(topics) > 10:
                print(f"  ... and {len(topics) - 10} more topics")
            
        else:
            print("❌ No topics found. The PDF might not have a recognizable structure.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
