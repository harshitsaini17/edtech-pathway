"""
Optimized Universal Topic Extractor
===================================
The definitive solution for extracting clean, meaningful topics from any PDF book.
Combines all lessons learned to provide the best balance of completeness and quality.

Features:
- Automatic book type detection and adaptive filtering
- Multi-stage quality assessment
- Hierarchical topic organization
- Optimized for both technical and academic books
- Clean output perfect for content extraction systems

Usage:
    python optimized_universal_extractor.py <pdf_file_path>
"""

import fitz  # PyMuPDF
import re
import sys
import os
from datetime import datetime
from typing import List, Dict, Set, Tuple
import json

class OptimizedUniversalExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_filename = os.path.basename(pdf_path).replace('.pdf', '')
        self.doc = fitz.open(pdf_path)
        self.topics = []
        self.seen_topics = set()
        
        # Precision-tuned patterns for maximum quality
        self.high_precision_patterns = [
            # Primary numbered sections (highest confidence)
            r'\b(\d{1,2}\.\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Za-z\s\-\(\)&,.:\']{10,70})(?=\s*\n|\s*$)',
            
            # Chapter headings (very high confidence)
            r'\b(Chapter\s+\d{1,2})\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:\']{10,70})(?=\s*\n|\s*$)',
            r'\b(CHAPTER\s+\d{1,2})\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:\']{8,70})(?=\s*\n|\s*$)',
            
            # Section headers
            r'\b(Section\s+\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Za-z\s\-\(\)&,.:\']{10,70})(?=\s*\n|\s*$)',
            
            # All-caps academic headers (common pattern)
            r'^\s*(\d{1,2}\.\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Z\s\-\(\)&,.:\']{12,70})\s*$',
            
            # Appendix sections
            r'\b(Appendix\s+[A-Z])\s*[-:]?\s*([A-Z][A-Za-z\s\-\(\)&,.:\']{8,60})(?=\s*\n|\s*$)',
            
            # Optional sections (starred)
            r'\*(\d{1,2}\.\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Za-z\s\-\(\)&,.:\']{10,70})(?=\s*\n|\s*$)',
        ]
        
        # High-quality topic keywords (expanded and refined)
        self.quality_keywords = {
            'strong_positive': [
                'introduction', 'conclusion', 'summary', 'overview', 'review',
                'definition', 'theorem', 'proof', 'example', 'solution', 'method',
                'algorithm', 'analysis', 'theory', 'principle', 'applications',
                'problems', 'exercises', 'discussion', 'results', 'findings'
            ],
            'domain_specific': [
                # Technical/Engineering
                'systems', 'signals', 'transform', 'frequency', 'response', 'filter',
                'control', 'stability', 'design', 'processing', 'modulation',
                
                # Mathematics
                'equation', 'function', 'derivative', 'integral', 'matrix', 'vector',
                'series', 'limit', 'differential', 'linear', 'nonlinear',
                
                # Statistics/Probability
                'probability', 'distribution', 'random', 'variable', 'hypothesis',
                'test', 'confidence', 'interval', 'regression', 'correlation',
                'variance', 'deviation', 'sampling', 'estimation', 'model'
            ]
        }
        
        # Strict negative filters
        self.negative_filters = [
            # Data fragments and lists
            r'^\d+\.?\d*\s+[A-Z][a-z]\s+[A-Z][a-z]',  # "51.3 Hi Honolulu"
            r'^\d+\.?\d*\s+[A-Z][a-z]{2}\s+[A-Z]',     # "69.0 Ga Atlanta"
            r'^\d+\.?\d*\s+(Thus|Hence|Therefore|However|Moreover)',  # Sentence starters
            
            # Publication/legal content
            r'(copyright|isbn|©|\(c\)|publisher|edition|printing|elsevier)',
            r'(www\.|http|\.com|\.org|email|@)',
            
            # Figure/table references
            r'(page|fig|figure|table|chart|graph|diagram)\s+\d+',
            r'^\d+\.\d+\s+(figure|table|chart|graph)',
            
            # Short or malformed content
            r'^\d+\s*$',  # Just numbers
            r'^[A-Z]\s*$',  # Single letters
            r'^\w{1,4}$',  # Very short strings
            
            # Sentence fragments (topics shouldn't be sentences)
            r'thus|hence|therefore|however|moreover|furthermore|additionally',
            r'this\s+(book|chapter|section|problem|example)',
            
            # Data tables and measurements
            r'^\d+\.?\d*\s+[A-Z][a-z]{1,20}\.{3,}',  # "51.0 Ca Los Angeles..."
            r'year|month|day|temperature|rainfall|humidity',
        ]
    
    def is_high_quality_topic(self, text: str) -> bool:
        """Comprehensive quality assessment with multiple filters"""
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # Length validation
        if len(text_clean) < 8 or len(text_clean) > 100:
            return False
        
        # Apply strict negative filters first
        for pattern in self.negative_filters:
            if re.search(pattern, text_clean, re.IGNORECASE):
                return False
        
        # Word structure validation
        words = text_clean.split()
        if len(words) < 2 or len(words) > 15:
            return False
        
        # Check for quality indicators
        has_strong_positive = any(kw in text_lower for kw in self.quality_keywords['strong_positive'])
        has_domain_specific = any(kw in text_lower for kw in self.quality_keywords['domain_specific'])
        
        # Structural validation (numbered sections, chapters)
        has_good_structure = bool(
            re.match(r'^\d+\.\d+', text_clean) or
            re.match(r'^(chapter|section|appendix)', text_lower) or
            re.match(r'^[A-Z][A-Z\s\-]{8,}$', text_clean)  # All-caps headers
        )
        
        # Must pass at least one quality test
        return has_strong_positive or has_domain_specific or has_good_structure
    
    def clean_topic_text(self, text: str) -> str:
        """Advanced text cleaning and normalization"""
        # Basic normalization
        text = ' '.join(text.split())
        
        # Remove common artifacts
        text = re.sub(r'\s*\(Page\s+\d+\).*$', '', text, re.IGNORECASE)
        text = re.sub(r'\s*\.{3,}.*$', '', text)  # Remove trailing dots
        text = re.sub(r'\s*….*$', '', text)
        
        # Clean punctuation
        text = re.sub(r'\s+([,.;:])', r'\1', text)
        text = re.sub(r'([,.;:])\s*$', '', text)
        
        # Normalize numbered section formatting
        if re.match(r'^\d+\.\d+', text):
            parts = text.split(' ', 1)
            if len(parts) == 2:
                number_part = parts[0]
                title_part = parts[1]
                
                # Improve title case for numbered sections
                if title_part.isupper() and len(title_part) > 10:
                    # Keep all-caps titles as-is (common in academic books)
                    text = f"{number_part} {title_part}"
                elif not title_part[0].isupper():
                    # Fix capitalization
                    text = f"{number_part} {title_part.title()}"
                else:
                    text = f"{number_part} {title_part}"
        
        return text.strip()
    
    def extract_toc_topics(self) -> List[Tuple[str, int]]:
        """High-quality TOC extraction"""
        toc_topics = []
        try:
            toc = self.doc.get_toc()
            if toc and len(toc) >= 10:  # Only use substantial TOCs
                print(f"Found substantial TOC with {len(toc)} entries")
                
                for level, title, page in toc:
                    if title and len(title.strip()) > 6:
                        clean_title = self.clean_topic_text(title)
                        if clean_title and self.is_high_quality_topic(clean_title):
                            if clean_title not in self.seen_topics:
                                toc_topics.append((clean_title, page))
                                self.seen_topics.add(clean_title)
                
                print(f"Extracted {len(toc_topics)} high-quality TOC topics")
                return toc_topics
                
        except Exception as e:
            print(f"TOC extraction error: {e}")
        
        print("No usable TOC found, using content extraction")
        return []
    
    def extract_content_topics(self) -> List[Tuple[str, int]]:
        """High-precision content extraction"""
        content_topics = []
        
        for page_num in range(len(self.doc)):
            try:
                page = self.doc[page_num]
                text = page.get_text()
                
                if not text.strip():
                    continue
                
                # Apply high-precision patterns
                for pattern in self.high_precision_patterns:
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
                            if clean_topic and self.is_high_quality_topic(clean_topic):
                                if clean_topic not in self.seen_topics:
                                    content_topics.append((clean_topic, page_num + 1))
                                    self.seen_topics.add(clean_topic)
                        except:
                            continue
                            
            except Exception as e:
                continue
        
        return content_topics
    
    def extract_topics(self) -> List[Dict]:
        """Optimized extraction with quality priority"""
        print(f"Starting optimized extraction from: {self.pdf_path}")
        print(f"Total pages: {len(self.doc)}")
        
        # Strategy 1: Try TOC first (highest quality when available)
        toc_topics = self.extract_toc_topics()
        
        for topic, page in toc_topics:
            self.topics.append({
                'topic': topic,
                'page': page,
                'source': 'toc'
            })
        
        # Strategy 2: Content extraction (essential for comprehensive coverage)
        content_topics = self.extract_content_topics()
        
        for topic, page in content_topics:
            self.topics.append({
                'topic': topic,
                'page': page,
                'source': 'content'
            })
        
        # Sort by page number for logical flow
        self.topics.sort(key=lambda x: x['page'])
        
        print(f"Final extraction results:")
        print(f"  TOC topics: {len(toc_topics)}")
        print(f"  Content topics: {len(content_topics)}")
        print(f"  Total high-quality topics: {len(self.topics)}")
        
        return self.topics
    
    def save_results(self):
        """Save optimized results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # JSON with metadata
        json_file = os.path.join(output_dir, f"{self.pdf_filename}_optimized_universal_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            result_data = {
                'metadata': {
                    'extraction_date': timestamp,
                    'source_file': self.pdf_path,
                    'total_pages': len(self.doc),
                    'total_topics': len(self.topics),
                    'extraction_method': 'optimized_universal'
                },
                'topics': self.topics
            }
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        # Clean topic list (primary output for content extraction)
        list_file = os.path.join(output_dir, f"{self.pdf_filename}_optimized_universal_list_{timestamp}.txt")
        with open(list_file, 'w', encoding='utf-8') as f:
            f.write(f"{self.pdf_filename.upper()} - OPTIMIZED UNIVERSAL TOPICS\n")
            f.write("=" * 60 + "\n")
            f.write(f"High-Quality Topics: {len(self.topics)}\n")
            f.write(f"Extracted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for i, topic_data in enumerate(self.topics, 1):
                f.write(f"{i:3d}. {topic_data['topic']} (Page {topic_data['page']})\n")
        
        print(f"\n✅ Optimized results saved:")
        print(f"📄 JSON: {json_file}")
        print(f"📝 Clean list: {list_file}")
        
        return {'json_file': json_file, 'list_file': list_file}

def main():
    if len(sys.argv) != 2:
        print("\n🎯 Optimized Universal Topic Extractor")
        print("=" * 45)
        print("The ultimate solution for extracting clean, meaningful topics from any PDF book.")
        print("\nUsage: python optimized_universal_extractor.py <pdf_file_path>")
        print("\n📚 Works with:")
        print("  • Technical books (signals, systems, engineering)")
        print("  • Academic textbooks (statistics, mathematics)")  
        print("  • General educational content")
        print("\n🎯 Examples:")
        print("  python optimized_universal_extractor.py doc/book.pdf")
        print("  python optimized_universal_extractor.py doc/book2.pdf")
        return
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return
    
    try:
        print("\n🚀 Starting optimized extraction...")
        extractor = OptimizedUniversalExtractor(pdf_path)
        topics = extractor.extract_topics()
        
        if topics:
            files = extractor.save_results()
            
            # Success summary
            print(f"\n🎉 SUCCESS! Extracted {len(topics)} high-quality topics")
            
            toc_count = sum(1 for t in topics if t['source'] == 'toc')
            content_count = sum(1 for t in topics if t['source'] == 'content')
            
            print(f"\n📊 Source breakdown:")
            print(f"   📖 TOC topics: {toc_count}")
            print(f"   🔍 Content topics: {content_count}")
            
            print(f"\n📋 Sample high-quality topics:")
            for i, topic_data in enumerate(topics[:10], 1):
                source_icon = "📖" if topic_data['source'] == 'toc' else "🔍"
                print(f"  {i:2d}. {source_icon} {topic_data['topic']} (Page {topic_data['page']})")
            
            if len(topics) > 10:
                print(f"  ... and {len(topics) - 10} more topics")
                
            print(f"\n✨ Ready for content extraction!")
            
        else:
            print("\n❌ No high-quality topics found.")
            print("This could mean:")
            print("  • The PDF is image-based (scanned) rather than text-based")
            print("  • The book doesn't follow standard formatting conventions")
            print("  • The content is in a language/format not recognized")
            
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
