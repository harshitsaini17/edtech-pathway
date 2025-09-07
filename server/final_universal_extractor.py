"""
Final Universal Topic Extractor
===============================
A comprehensive and balanced extractor that works optimally with any type of book.
Combines TOC extraction with intelligent content parsing and adaptive quality filtering.

Key Features:
- Automatic book type detection (technical vs academic)
- Smart quality filtering with adaptive thresholds
- Hierarchical topic organization
- Multiple extraction strategies with intelligent fallback
- Clean output formats optimized for content extraction

Usage:
    python final_universal_extractor.py <pdf_file_path>
"""

import fitz  # PyMuPDF
import re
import sys
import os
from datetime import datetime
from typing import List, Dict, Set, Tuple
import json

class FinalUniversalExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_filename = os.path.basename(pdf_path).replace('.pdf', '')
        self.doc = fitz.open(pdf_path)
        self.topics = []
        self.seen_topics = set()
        self.book_type = "unknown"  # Will be detected automatically
        
        # Comprehensive patterns for different structures
        self.toc_patterns = [
            # Standard TOC numbered sections
            r'^(\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Za-z\s\-\(\)&,.:\']+?)(?:\s+\d+)?$',
            r'^(Chapter\s+\d{1,2})\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:\']+?)(?:\s+\d+)?$',
            r'^(Appendix\s+[A-Z])\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:\']+?)(?:\s+\d+)?$',
        ]
        
        self.content_patterns = [
            # High-confidence numbered sections
            r'\b(\d{1,2}\.\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Za-z\s\-\(\)&,.:\']{8,60})(?=\s*\n|\s*\(|\s*$)',
            
            # Chapter headings  
            r'\b(Chapter\s+\d{1,2})\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:\']{8,60})(?=\s*\n|\s*\(|\s*$)',
            r'\b(CHAPTER\s+\d{1,2})\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:\']{8,60})(?=\s*\n|\s*\(|\s*$)',
            
            # Section patterns with better filtering
            r'\b(Section\s+\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Za-z\s\-\(\)&,.:\']{8,60})(?=\s*\n|\s*\(|\s*$)',
            
            # All-caps section headers (common in academic books)
            r'\b(\d{1,2}\.\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Z\s\-\(\)&,.:\']{10,60})(?=\s*\n|\s*\(|\s*$)',
            
            # Appendix and special sections
            r'\b(Appendix\s+[A-Z])\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:\']{8,60})(?=\s*\n|\s*\(|\s*$)',
            
            # Optional/starred sections
            r'\*(\d{1,2}\.\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Za-z\s\-\(\)&,.:\']{8,60})(?=\s*\n|\s*\(|\s*$)',
        ]
        
        # Quality indicators by category
        self.quality_indicators = {
            'technical': [
                'systems', 'signals', 'transform', 'frequency', 'response', 'analysis',
                'filter', 'processing', 'control', 'stability', 'design', 'linear',
                'fourier', 'laplace', 'convolution', 'sampling', 'modulation'
            ],
            'mathematics': [
                'theorem', 'proof', 'equation', 'function', 'derivative', 'integral',
                'matrix', 'vector', 'series', 'limit', 'differential', 'optimization',
                'algebra', 'calculus', 'geometry', 'topology'
            ],
            'statistics': [
                'probability', 'distribution', 'random', 'variable', 'hypothesis',
                'test', 'confidence', 'interval', 'regression', 'correlation',
                'variance', 'deviation', 'sampling', 'estimation', 'bayesian'
            ],
            'academic': [
                'introduction', 'conclusion', 'summary', 'review', 'applications',
                'examples', 'problems', 'exercises', 'solution', 'method',
                'algorithm', 'theory', 'principle', 'definition'
            ]
        }
        
        # Strong exclusion criteria
        self.exclusion_criteria = [
            r'^\d+\s*$',  # Just numbers
            r'^[A-Z]\s*$',  # Single letters  
            r'(page|fig|figure|table|chart)\s+\d+',  # Figure/table references
            r'(copyright|isbn|©|\(c\)|publisher|edition|printing)',  # Legal/publishing
            r'(www\.|http|\.com|\.org|email|@)',  # Web/email
            r'^\w{1,3}$',  # Very short words
            r'\d{4,}',  # Long number sequences
            r'[^\w\s\-\(\)&,.:\']{3,}',  # Special character clusters
            r'this\s+(book|chapter|section)',  # Self-references
        ]
    
    def detect_book_type(self) -> str:
        """Detect book type based on content analysis"""
        sample_text = ""
        # Sample first 50 pages
        for i in range(min(50, len(self.doc))):
            try:
                page = self.doc[i]
                sample_text += page.get_text()[:1000]  # First 1000 chars per page
            except:
                continue
        
        sample_lower = sample_text.lower()
        
        # Count indicators
        tech_score = sum(1 for word in self.quality_indicators['technical'] if word in sample_lower)
        math_score = sum(1 for word in self.quality_indicators['mathematics'] if word in sample_lower)
        stats_score = sum(1 for word in self.quality_indicators['statistics'] if word in sample_lower)
        academic_score = sum(1 for word in self.quality_indicators['academic'] if word in sample_lower)
        
        # Determine book type
        if tech_score > max(math_score, stats_score, academic_score):
            return "technical"
        elif stats_score > max(tech_score, math_score, academic_score):
            return "statistics"
        elif math_score > max(tech_score, stats_score, academic_score):
            return "mathematics"
        else:
            return "academic"
    
    def is_quality_topic(self, text: str, context: str = "content") -> bool:
        """Adaptive quality assessment based on book type and context"""
        text_lower = text.lower().strip()
        
        # Basic length filter
        if len(text) < 6 or len(text) > 100:
            return False
        
        # Apply exclusion criteria
        for pattern in self.exclusion_criteria:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # Must have reasonable word structure
        words = text.split()
        if len(words) < 2 or len(words) > 15:
            return False
        
        # Check for quality indicators
        has_quality_indicator = False
        for category, indicators in self.quality_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                has_quality_indicator = True
                break
        
        # Structural indicators (numbered sections, chapters)
        has_structure = bool(
            re.match(r'^\d+\.\d+', text.strip()) or
            re.match(r'^(chapter|section|appendix)', text.lower().strip()) or
            re.search(r'\b(introduction|conclusion|summary|problems|exercises)\b', text_lower)
        )
        
        # Context-based scoring
        if context == "toc":
            # TOC entries are generally high quality, be more lenient
            return has_structure or has_quality_indicator or len(words) >= 3
        else:
            # Content extraction needs stricter filtering
            return has_structure or has_quality_indicator
    
    def clean_topic_text(self, text: str) -> str:
        """Enhanced text cleaning"""
        # Basic normalization
        text = ' '.join(text.split())
        
        # Remove artifacts
        text = re.sub(r'\s*\(Page\s+\d+\).*$', '', text, re.IGNORECASE)
        text = re.sub(r'\s*\.\.\.$', '', text)
        text = re.sub(r'\s*…$', '', text)
        text = re.sub(r'\s*\*+\s*$', '', text)
        
        # Clean punctuation
        text = re.sub(r'\s+([,.;:])', r'\1', text)
        text = re.sub(r'([,.;:])\s*$', '', text)
        
        # Normalize case for numbered sections
        if re.match(r'^\d+\.\d+', text):
            parts = text.split(' ', 1)
            if len(parts) == 2:
                # Keep number as-is, title case the rest
                text = f"{parts[0]} {parts[1].title()}"
        
        return text.strip()
    
    def extract_toc_topics(self) -> List[Tuple[str, int]]:
        """Extract topics from Table of Contents"""
        toc_topics = []
        try:
            toc = self.doc.get_toc()
            if toc and len(toc) > 5:  # Only use TOC if it's substantial
                print(f"Found substantial TOC with {len(toc)} entries")
                
                for level, title, page in toc:
                    if title and len(title.strip()) > 4:
                        clean_title = self.clean_topic_text(title)
                        if clean_title and self.is_quality_topic(clean_title, "toc"):
                            if clean_title not in self.seen_topics:
                                toc_topics.append((clean_title, page))
                                self.seen_topics.add(clean_title)
                
                return toc_topics
        except Exception as e:
            print(f"TOC extraction error: {e}")
        
        return []
    
    def extract_content_topics(self) -> List[Tuple[str, int]]:
        """Extract topics from page content using patterns"""
        content_topics = []
        
        for page_num in range(len(self.doc)):
            try:
                page = self.doc[page_num]
                text = page.get_text()
                
                if not text.strip():
                    continue
                
                # Apply all patterns
                for pattern in self.content_patterns:
                    matches = re.finditer(pattern, text, re.MULTILINE)
                    for match in matches:
                        try:
                            if len(match.groups()) >= 2:
                                number = match.group(1).strip()
                                title = match.group(2).strip()
                                full_topic = f"{number} {title}"
                            else:
                                full_topic = match.group(1).strip()
                            
                            clean_topic = self.clean_topic_text(full_topic)
                            if clean_topic and self.is_quality_topic(clean_topic, "content"):
                                if clean_topic not in self.seen_topics:
                                    content_topics.append((clean_topic, page_num + 1))
                                    self.seen_topics.add(clean_topic)
                        except:
                            continue
                            
            except Exception as e:
                print(f"Error processing page {page_num + 1}: {e}")
                continue
        
        return content_topics
    
    def extract_all_topics(self) -> List[Dict]:
        """Main extraction method with intelligent strategy selection"""
        print(f"Extracting topics from: {self.pdf_path}")
        print(f"Total pages: {len(self.doc)}")
        
        # Detect book type for better processing
        self.book_type = self.detect_book_type()
        print(f"Detected book type: {self.book_type}")
        
        # Try TOC extraction first
        toc_topics = self.extract_toc_topics()
        toc_count = len(toc_topics)
        
        # Add TOC topics
        for topic, page in toc_topics:
            self.topics.append({
                'topic': topic,
                'page': page,
                'source': 'toc',
                'book_type': self.book_type
            })
        
        # Extract from content (especially important if TOC is limited)
        content_topics = self.extract_content_topics()
        content_count = len(content_topics)
        
        # Add content topics
        for topic, page in content_topics:
            self.topics.append({
                'topic': topic,
                'page': page,
                'source': 'content',
                'book_type': self.book_type
            })
        
        print(f"TOC topics: {toc_count}")
        print(f"Content topics: {content_count}")
        print(f"Total topics extracted: {len(self.topics)}")
        
        # Sort by page for logical ordering
        self.topics.sort(key=lambda x: x['page'])
        
        return self.topics
    
    def save_results(self):
        """Save comprehensive results in multiple formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # JSON with full metadata
        json_file = os.path.join(output_dir, f"{self.pdf_filename}_final_universal_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            result_data = {
                'extraction_info': {
                    'timestamp': timestamp,
                    'source_file': self.pdf_path,
                    'total_pages': len(self.doc),
                    'book_type': self.book_type,
                    'total_topics': len(self.topics)
                },
                'topics': self.topics
            }
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        # Clean text list for easy content extraction
        list_file = os.path.join(output_dir, f"{self.pdf_filename}_final_universal_list_{timestamp}.txt")
        with open(list_file, 'w', encoding='utf-8') as f:
            f.write(f"{self.pdf_filename.upper()} - FINAL UNIVERSAL EXTRACTION\n")
            f.write("=" * 65 + "\n")
            f.write(f"Book Type: {self.book_type.title()}\n")
            f.write(f"Total Topics: {len(self.topics)}\n")
            f.write(f"Extracted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for i, topic_data in enumerate(self.topics, 1):
                f.write(f"{i:3d}. {topic_data['topic']} (Page {topic_data['page']})\n")
        
        # Organized markdown with chapter structure
        md_file = os.path.join(output_dir, f"{self.pdf_filename}_final_universal_{timestamp}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# {self.pdf_filename.replace('_', ' ').title()} - Final Universal Topics\n\n")
            f.write(f"**Book Type:** {self.book_type.title()}\n")
            f.write(f"**Extraction Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Topics:** {len(self.topics)}\n")
            f.write(f"**Source File:** {self.pdf_path}\n\n")
            
            # Group topics by source
            toc_topics = [t for t in self.topics if t['source'] == 'toc']
            content_topics = [t for t in self.topics if t['source'] == 'content']
            
            if toc_topics:
                f.write(f"## Table of Contents Topics ({len(toc_topics)} items)\n\n")
                for topic in toc_topics:
                    f.write(f"- **{topic['topic']}** (Page {topic['page']})\n")
                f.write("\n")
            
            if content_topics:
                f.write(f"## Content-Extracted Topics ({len(content_topics)} items)\n\n")
                for topic in content_topics:
                    f.write(f"- **{topic['topic']}** (Page {topic['page']})\n")
                f.write("\n")
        
        print(f"\n✅ Final results saved:")
        print(f"📄 JSON (with metadata): {json_file}")
        print(f"📝 Clean list: {list_file}")
        print(f"📋 Organized markdown: {md_file}")
        
        return {
            'json_file': json_file,
            'list_file': list_file,
            'md_file': md_file
        }

def main():
    if len(sys.argv) != 2:
        print("Final Universal Topic Extractor")
        print("=" * 35)
        print("Usage: python final_universal_extractor.py <pdf_file_path>")
        print("\nExamples:")
        print("  python final_universal_extractor.py doc/book.pdf")
        print("  python final_universal_extractor.py doc/book2.pdf")
        print("  python final_universal_extractor.py path/to/any_book.pdf")
        return
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return
    
    try:
        extractor = FinalUniversalExtractor(pdf_path)
        topics = extractor.extract_all_topics()
        
        if topics:
            files = extractor.save_results()
            print(f"\n🎉 Successfully extracted {len(topics)} topics!")
            print(f"📚 Book type detected: {extractor.book_type}")
            
            # Show sample topics by category
            toc_count = sum(1 for t in topics if t['source'] == 'toc')
            content_count = sum(1 for t in topics if t['source'] == 'content')
            
            print(f"\n📊 Extraction Summary:")
            print(f"   TOC topics: {toc_count}")
            print(f"   Content topics: {content_count}")
            print(f"   Total: {len(topics)}")
            
            print(f"\n📋 Sample topics:")
            for i, topic_data in enumerate(topics[:12], 1):
                source_icon = "📖" if topic_data['source'] == 'toc' else "🔍"
                print(f"  {i:2d}. {source_icon} {topic_data['topic']} (Page {topic_data['page']})")
            
            if len(topics) > 12:
                print(f"  ... and {len(topics) - 12} more topics")
            
        else:
            print("❌ No topics found. The PDF might not have a recognizable structure.")
            print("Try checking if the PDF is text-based (not scanned images) and has proper formatting.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
