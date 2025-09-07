"""
Universal Clean Topic Extractor
===============================
Enhanced version that extracts only high-quality headings, topics, and sub-topics 
from any PDF book while filtering out noise and irrelevant content.

Features:
- Works with both technical books and academic textbooks
- Intelligent quality filtering to remove fragments and noise
- Hierarchical topic organization
- Multiple output formats (JSON, text list, markdown)
- Adaptive pattern recognition for different book styles

Usage:
    python universal_clean_extractor.py <pdf_file_path>
"""

import fitz  # PyMuPDF
import re
import sys
import os
from datetime import datetime
from typing import List, Dict, Set, Tuple

class UniversalCleanExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_filename = os.path.basename(pdf_path).replace('.pdf', '')
        self.doc = fitz.open(pdf_path)
        self.topics = []
        self.seen_topics = set()
        
        # High-quality regex patterns for meaningful topics only
        self.patterns = [
            # Standard numbered sections (1.1, 1.1.1, etc.)
            r'\b(\d{1,2}\.\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Za-z\s\-\(\)&,.:\']+?)(?=\s*\n|\s*\(|\s*$)',
            
            # Chapter patterns
            r'\b(Chapter\s+\d{1,2})\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:\']+?)(?=\s*\n|\s*\(|\s*$)',
            r'\b(CHAPTER\s+\d{1,2})\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:\']+?)(?=\s*\n|\s*\(|\s*$)',
            
            # Section patterns  
            r'\b(Section\s+\d{1,2}(?:\.\d{1,2})*)\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:\']+?)(?=\s*\n|\s*\(|\s*$)',
            
            # Appendix patterns
            r'\b(Appendix\s+[A-Z])\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:\']+?)(?=\s*\n|\s*\(|\s*$)',
            
            # Starred sections (for optional/advanced topics)
            r'\*(\d{1,2}\.\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Za-z\s\-\(\)&,.:\']+?)(?=\s*\n|\s*\(|\s*$)',
        ]
        
        # Strong quality indicators
        self.strong_indicators = {
            'academic': [
                'introduction', 'definition', 'theorem', 'proof', 'example', 'solution',
                'method', 'algorithm', 'analysis', 'theory', 'principle', 'law',
                'distribution', 'probability', 'statistics', 'regression', 'correlation',
                'variance', 'hypothesis', 'test', 'confidence', 'estimation', 'sampling',
                'variables', 'function', 'applications', 'problems', 'exercises'
            ],
            'technical': [
                'systems', 'signals', 'transform', 'frequency', 'response', 'filter',
                'processing', 'control', 'stability', 'design', 'implementation',
                'optimization', 'linear', 'nonlinear', 'differential', 'integral'
            ],
            'structural': [
                'summary', 'review', 'conclusion', 'references', 'bibliography',
                'appendix', 'glossary', 'index', 'notation'
            ]
        }
        
        # Strict exclusion patterns
        self.exclusion_patterns = [
            r'^[^A-Z]',  # Must start with capital letter
            r'\d{4,}',   # Long numbers (likely page numbers, years, etc.)
            r'[^\w\s\-\(\)&,.:\']{2,}',  # Special characters clusters
            r'\w{40,}',  # Very long words (likely corrupted text)
            r'(page|figure|table|chart|graph|diagram)\s+\d+',  # References to figures/tables
            r'(copyright|isbn|publisher|edition|printing)',  # Publication info
            r'(www\.|http|\.com|\.org)',  # URLs
            r'^\d+\s*$',  # Just numbers
            r'^[A-Z]\s*$',  # Single letters
        ]
    
    def is_high_quality_topic(self, text: str) -> bool:
        """Strict quality check for topics"""
        text_lower = text.lower()
        
        # Basic filters
        if len(text) < 8 or len(text) > 80:
            return False
        
        # Check exclusion patterns
        for pattern in self.exclusion_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # Must have proper word structure
        words = text.split()
        if len(words) < 2 or len(words) > 12:
            return False
        
        # Check for quality indicators
        has_indicator = False
        for category, indicators in self.strong_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                has_indicator = True
                break
        
        # Must have quality indicator OR proper numbered structure
        has_numbers = re.match(r'^\d+\.\d+', text.strip())
        has_chapter = re.match(r'^(chapter|section|appendix)', text.lower().strip())
        
        return has_indicator or has_numbers or has_chapter
    
    def clean_topic_text(self, text: str) -> str:
        """Clean and normalize topic text"""
        # Remove extra whitespace and normalize
        text = ' '.join(text.split())
        
        # Remove common suffixes and artifacts
        text = re.sub(r'\s*\(Page\s+\d+\).*$', '', text, re.IGNORECASE)
        text = re.sub(r'\s*\.\.\.$', '', text)
        text = re.sub(r'\s*…$', '', text)
        text = re.sub(r'\s*\*$', '', text)
        
        # Clean punctuation
        text = re.sub(r'\s+([,.;:])', r'\1', text)
        text = re.sub(r'([,.;:])\s*$', '', text)
        
        # Ensure proper capitalization for numbered sections
        if re.match(r'^\d+\.\d+', text):
            parts = text.split(' ', 1)
            if len(parts) == 2:
                text = f"{parts[0]} {parts[1].title()}"
        
        return text.strip()
    
    def extract_toc_topics(self) -> List[Tuple[str, int]]:
        """Extract high-quality topics from Table of Contents"""
        toc_topics = []
        try:
            toc = self.doc.get_toc()
            if toc:
                print(f"Found TOC with {len(toc)} entries")
                for level, title, page in toc:
                    if title and len(title.strip()) > 5:
                        clean_title = self.clean_topic_text(title)
                        if clean_title and self.is_high_quality_topic(clean_title):
                            toc_topics.append((clean_title, page))
            return toc_topics
        except Exception as e:
            print(f"TOC extraction error: {e}")
            return []
    
    def extract_from_content(self) -> List[Tuple[str, int]]:
        """Extract topics using pattern matching on content"""
        content_topics = []
        
        for page_num in range(len(self.doc)):
            try:
                page = self.doc[page_num]
                text = page.get_text()
                
                if not text.strip():
                    continue
                
                # Try each pattern
                for pattern in self.patterns:
                    matches = re.finditer(pattern, text, re.MULTILINE)
                    for match in matches:
                        if len(match.groups()) >= 2:
                            number = match.group(1).strip()
                            title = match.group(2).strip()
                            full_topic = f"{number} {title}"
                        else:
                            full_topic = match.group(1).strip()
                        
                        # Clean and validate
                        clean_topic = self.clean_topic_text(full_topic)
                        if clean_topic and self.is_high_quality_topic(clean_topic):
                            if clean_topic not in self.seen_topics:
                                content_topics.append((clean_topic, page_num + 1))
                                self.seen_topics.add(clean_topic)
                
            except Exception as e:
                print(f"Error processing page {page_num + 1}: {e}")
                continue
        
        return content_topics
    
    def extract_topics(self) -> List[Dict]:
        """Main extraction method with intelligent fallback"""
        print(f"Extracting high-quality topics from: {self.pdf_path}")
        print(f"Total pages: {len(self.doc)}")
        
        # Try TOC first (usually highest quality)
        toc_topics = self.extract_toc_topics()
        toc_count = len(toc_topics)
        
        # Add TOC topics
        for topic, page in toc_topics:
            self.topics.append({
                'topic': topic,
                'page': page,
                'source': 'toc'
            })
            self.seen_topics.add(topic)
        
        # Extract from content
        content_topics = self.extract_from_content()
        content_count = len(content_topics)
        
        # Add content topics
        for topic, page in content_topics:
            self.topics.append({
                'topic': topic,
                'page': page,
                'source': 'content'
            })
        
        print(f"TOC topics: {toc_count}")
        print(f"Content topics: {content_count}")
        print(f"Total high-quality topics: {len(self.topics)}")
        
        # Sort by page number for better organization
        self.topics.sort(key=lambda x: x['page'])
        
        return self.topics
    
    def save_results(self):
        """Save extraction results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # JSON format
        json_file = os.path.join(output_dir, f"{self.pdf_filename}_clean_universal_{timestamp}.json")
        import json
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.topics, f, indent=2, ensure_ascii=False)
        
        # Clean list for easy use
        list_file = os.path.join(output_dir, f"{self.pdf_filename}_clean_universal_list_{timestamp}.txt")
        with open(list_file, 'w', encoding='utf-8') as f:
            f.write(f"{self.pdf_filename.upper()} - CLEAN UNIVERSAL TOPICS\n")
            f.write("=" * 60 + "\n\n")
            
            for i, topic_data in enumerate(self.topics, 1):
                f.write(f"{i}. {topic_data['topic']} (Page {topic_data['page']})\n")
        
        # Organized markdown
        md_file = os.path.join(output_dir, f"{self.pdf_filename}_clean_universal_{timestamp}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# {self.pdf_filename.replace('_', ' ').title()} - Clean Universal Topics\n\n")
            f.write(f"**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Topics:** {len(self.topics)}\n")
            f.write(f"**Source:** {self.pdf_path}\n\n")
            
            # Organize by chapters/sections
            current_chapter = ""
            chapter_topics = []
            
            for topic_data in self.topics:
                topic = topic_data['topic']
                
                # Detect chapter boundaries
                if re.match(r'^(Chapter|\d+\.0|\d+\s+[A-Z])', topic):
                    if current_chapter and chapter_topics:
                        f.write(f"## {current_chapter}\n\n")
                        for t in chapter_topics:
                            f.write(f"- **{t['topic']}** (Page {t['page']})\n")
                        f.write("\n")
                    current_chapter = topic
                    chapter_topics = [topic_data]
                else:
                    chapter_topics.append(topic_data)
            
            # Write last chapter
            if current_chapter and chapter_topics:
                f.write(f"## {current_chapter}\n\n")
                for t in chapter_topics:
                    f.write(f"- **{t['topic']}** (Page {t['page']})\n")
        
        print(f"\n✅ Clean results saved:")
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
        print("Usage: python universal_clean_extractor.py <pdf_file_path>")
        print("\nExamples:")
        print("  python universal_clean_extractor.py doc/book.pdf")
        print("  python universal_clean_extractor.py doc/book2.pdf")
        return
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return
    
    try:
        extractor = UniversalCleanExtractor(pdf_path)
        topics = extractor.extract_topics()
        
        if topics:
            files = extractor.save_results()
            print(f"\n🎉 Successfully extracted {len(topics)} high-quality topics!")
            
            # Show sample topics
            print(f"\n📋 Sample high-quality topics:")
            for i, topic_data in enumerate(topics[:15], 1):
                print(f"  {i:2d}. {topic_data['topic']} (Page {topic_data['page']})")
            
            if len(topics) > 15:
                print(f"  ... and {len(topics) - 15} more topics")
            
        else:
            print("❌ No high-quality topics found. The PDF might not have a recognizable structure.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
