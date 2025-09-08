#!/usr/bin/env python3
"""
Enhanced Curriculum Page Extractor with Section-Based Extraction
===============================================================

This enhanced version extracts complete sections for each topic, including
theory continuation pages, and organizes extraction module by module.

Features:
- Module-wise page extraction
- Automatic detection of section continuation (theory + examples)
- Smart page range detection for complete topics
- Proper source PDF detection (book2.pdf priority)
- Individual module PDFs + combined curriculum PDF
"""

import os
import json
import fitz  # PyMuPDF
from datetime import datetime
from typing import List, Dict, Set, Tuple
import argparse


class EnhancedCurriculumPageExtractor:
    """Enhanced extractor with section-based page extraction"""
    
    def __init__(self):
        self.output_dir = "output"
        self.doc_dir = "doc"
        
    def get_available_curricula(self) -> List[str]:
        """Get list of available curriculum files"""
        curricula = []
        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                if file.startswith("curriculum_") and file.endswith(".json"):
                    curricula.append(file)
        return sorted(curricula)
    
    def load_curriculum(self, curriculum_file: str) -> Dict:
        """Load curriculum from JSON file"""
        file_path = os.path.join(self.output_dir, curriculum_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                curriculum = json.load(f)
            print(f"✅ Loaded curriculum: {curriculum.get('title', 'Unknown')}")
            return curriculum
        except Exception as e:
            print(f"❌ Error loading curriculum: {e}")
            return {}
    
    def find_source_pdf(self, curriculum_file: str) -> str:
        """Find the source PDF file with book2.pdf priority"""
        # Priority order: book2.pdf first, then others
        priority_names = ["book2.pdf", "book.pdf", "textbook.pdf", "document.pdf"]
        
        # Check doc directory for PDFs in priority order
        if os.path.exists(self.doc_dir):
            for pdf_name in priority_names:
                pdf_path = os.path.join(self.doc_dir, pdf_name)
                if os.path.exists(pdf_path):
                    print(f"📚 Using source PDF: {pdf_name}")
                    return pdf_path
            
            # If no priority PDFs found, check any PDF
            for filename in os.listdir(self.doc_dir):
                if filename.lower().endswith('.pdf'):
                    pdf_path = os.path.join(self.doc_dir, filename)
                    print(f"📚 Using source PDF: {filename}")
                    return pdf_path
        
        return None
    
    def detect_section_pages(self, source_doc: fitz.Document, start_page: int, 
                           topic_title: str, max_continuation: int = 4) -> List[int]:
        """
        Detect complete section pages starting from a topic page.
        Includes continuation pages with theory and examples.
        """
        if start_page < 1 or start_page > len(source_doc):
            return []
        
        section_pages = [start_page]
        current_page = start_page
        
        try:
            # Get text from the starting page to understand the topic
            start_page_obj = source_doc[start_page - 1]  # 0-based indexing
            start_text = start_page_obj.get_text().lower()
            
            # Look for continuation indicators in subsequent pages
            for i in range(1, max_continuation + 1):
                next_page_num = start_page + i
                
                if next_page_num > len(source_doc):
                    break
                
                try:
                    next_page_obj = source_doc[next_page_num - 1]
                    next_text = next_page_obj.get_text().lower()
                    
                    # Check if page likely continues the topic
                    is_continuation = self.is_topic_continuation(
                        start_text, next_text, topic_title, next_page_num
                    )
                    
                    if is_continuation:
                        section_pages.append(next_page_num)
                    else:
                        # Stop if we hit a clear section break
                        if self.is_section_break(next_text):
                            break
                            
                except Exception as e:
                    print(f"⚠️ Error analyzing page {next_page_num}: {e}")
                    break
            
        except Exception as e:
            print(f"⚠️ Error detecting section for page {start_page}: {e}")
        
        return sorted(section_pages)
    
    def is_topic_continuation(self, start_text: str, current_text: str, 
                            topic_title: str, page_num: int) -> bool:
        """Determine if a page is likely a continuation of the topic"""
        
        # Keywords indicating continuation
        continuation_indicators = [
            'example', 'theorem', 'proof', 'definition', 'proposition',
            'corollary', 'lemma', 'remark', 'note', 'solution', 'exercise',
            'problem', 'formula', 'equation', 'figure', 'table'
        ]
        
        # Keywords indicating new section/chapter
        section_break_indicators = [
            'chapter', 'section', '\\section', '\\chapter', 'introduction',
            'summary', 'conclusion', 'references', 'bibliography'
        ]
        
        # Extract key terms from topic title
        topic_words = topic_title.lower().split()
        topic_keywords = [word for word in topic_words if len(word) > 3]
        
        # Check for continuation indicators
        continuation_score = 0
        
        # 1. Contains continuation keywords
        for indicator in continuation_indicators:
            if indicator in current_text:
                continuation_score += 1
        
        # 2. Contains topic-related keywords
        for keyword in topic_keywords:
            if keyword in current_text:
                continuation_score += 2
        
        # 3. Mathematical content (common in statistics/probability)
        math_indicators = ['=', '∑', '∫', '≤', '≥', '±', 'var(', 'e(', 'σ', 'μ']
        for indicator in math_indicators:
            if indicator in current_text:
                continuation_score += 1
        
        # 4. Check for section breaks (negative score)
        for break_indicator in section_break_indicators:
            if current_text.startswith(break_indicator) or f"\\n{break_indicator}" in current_text:
                continuation_score -= 3
        
        # 5. Very short pages are likely not substantial content
        if len(current_text.strip()) < 100:
            continuation_score -= 2
        
        return continuation_score > 2
    
    def is_section_break(self, text: str) -> bool:
        """Check if page contains clear section break indicators"""
        section_breaks = [
            'chapter', '\\chapter', 'section', '\\section',
            'part', '\\part', 'appendix', '\\appendix'
        ]
        
        text_lines = text.lower().split('\\n')
        for line in text_lines[:3]:  # Check first few lines
            for break_word in section_breaks:
                if line.strip().startswith(break_word):
                    return True
        return False
    
    def extract_module_pages(self, source_doc: fitz.Document, module: Dict) -> Set[int]:
        """Extract complete pages for a single module"""
        module_pages = set()
        
        module_title = module.get('title', 'Unknown Module')
        topics = module.get('topics', [])
        pages = module.get('pages', [])
        
        print(f"   📖 Processing module: {module_title}")
        print(f"   📄 Topics: {len(topics)}, Base pages: {len(pages)}")
        
        # Process each topic in the module
        for i, topic in enumerate(topics):
            if i < len(pages):
                base_page = pages[i]
                
                if isinstance(base_page, int) and 1 <= base_page <= len(source_doc):
                    # Get complete section for this topic
                    section_pages = self.detect_section_pages(source_doc, base_page, topic)
                    module_pages.update(section_pages)
                    
                    if len(section_pages) > 1:
                        print(f"     🔍 {topic[:50]}... → Pages {section_pages[0]}-{section_pages[-1]} ({len(section_pages)} pages)")
                    else:
                        print(f"     🔍 {topic[:50]}... → Page {base_page}")
                elif isinstance(base_page, str) and base_page.isdigit():
                    base_page_num = int(base_page)
                    if 1 <= base_page_num <= len(source_doc):
                        section_pages = self.detect_section_pages(source_doc, base_page_num, topic)
                        module_pages.update(section_pages)
        
        print(f"   ✅ Module total: {len(module_pages)} pages")
        return module_pages
    
    def create_module_pdf(self, source_doc: fitz.Document, pages: Set[int], 
                         module: Dict, output_filename: str) -> bool:
        """Create PDF for a single module"""
        try:
            if not pages:
                return False
            
            sorted_pages = sorted(pages)
            output_doc = fitz.open()
            
            # Extract pages
            for page_num in sorted_pages:
                try:
                    output_doc.insert_pdf(source_doc, from_page=page_num-1, to_page=page_num-1)
                except Exception as e:
                    print(f"⚠️ Error extracting page {page_num}: {e}")
            
            # Add metadata
            metadata = {
                "title": f"Module: {module.get('title', 'Unknown')}",
                "subject": f"Pages for {module.get('title', 'Unknown')}",
                "creator": "Enhanced Curriculum Page Extractor",
                "producer": "PyMuPDF"
            }
            output_doc.set_metadata(metadata)
            
            # Save module PDF
            output_path = os.path.join(self.output_dir, output_filename)
            output_doc.save(output_path)
            output_doc.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating module PDF: {e}")
            return False
    
    def create_complete_curriculum_pdf(self, source_doc: fitz.Document, 
                                     all_pages: Set[int], curriculum: Dict, 
                                     output_filename: str) -> bool:
        """Create complete curriculum PDF with all modules"""
        try:
            if not all_pages:
                return False
            
            sorted_pages = sorted(all_pages)
            output_doc = fitz.open()
            
            print(f"📄 Creating complete curriculum PDF with {len(sorted_pages)} pages...")
            
            # Extract all pages
            for page_num in sorted_pages:
                try:
                    output_doc.insert_pdf(source_doc, from_page=page_num-1, to_page=page_num-1)
                except Exception as e:
                    print(f"⚠️ Error extracting page {page_num}: {e}")
            
            # Add bookmarks for modules
            toc = []
            page_offset = 0
            
            for module in curriculum.get('modules', []):
                module_title = module.get('title', f"Module {module.get('module_number', '?')}")
                module_pages = module.get('pages', [])
                
                # Find first page of this module in our sorted list
                for i, page in enumerate(module_pages):
                    if isinstance(page, int) and page in sorted_pages:
                        try:
                            bookmark_page = sorted_pages.index(page) + 1
                            toc.append([1, module_title, bookmark_page])
                            break
                        except ValueError:
                            continue
            
            if toc:
                output_doc.set_toc(toc)
            
            # Add metadata
            metadata = {
                "title": curriculum.get('title', 'Curriculum Pages'),
                "subject": f"Complete curriculum pages",
                "creator": "Enhanced Curriculum Page Extractor",
                "producer": "PyMuPDF"
            }
            output_doc.set_metadata(metadata)
            
            # Save complete PDF
            output_path = os.path.join(self.output_dir, output_filename)
            output_doc.save(output_path)
            output_doc.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating complete curriculum PDF: {e}")
            return False
    
    def enhanced_extraction_workflow(self):
        """Enhanced interactive workflow with module-wise extraction"""
        print("🎓 Enhanced Curriculum Page Extractor")
        print("=" * 60)
        print("Extract complete sections module-by-module with theory continuation")
        print()
        
        # Get available curricula
        curricula = self.get_available_curricula()
        
        if not curricula:
            print("❌ No curriculum files found in output directory.")
            print("   Please run the curriculum creator first.")
            return
        
        print(f"📚 Found {len(curricula)} available curricula:")
        for i, curriculum_file in enumerate(curricula, 1):
            # Extract a readable name
            name = curriculum_file.replace("curriculum_", "").replace(".json", "").replace("_", " ")
            print(f"   {i:2d}. {name}")
        
        print()
        
        # Select curriculum
        try:
            choice = input("🎯 Select curriculum (number): ").strip()
            curriculum_index = int(choice) - 1
            
            if 0 <= curriculum_index < len(curricula):
                selected_curriculum = curricula[curriculum_index]
            else:
                print("❌ Invalid selection")
                return
        except ValueError:
            print("❌ Please enter a valid number")
            return
        
        # Load curriculum
        curriculum = self.load_curriculum(selected_curriculum)
        if not curriculum:
            return
        
        # Find source PDF (prioritize book2.pdf)
        source_pdf = self.find_source_pdf(selected_curriculum)
        if not source_pdf:
            print("❌ Could not find source PDF file")
            print("   Please ensure book2.pdf is in the 'doc' directory")
            return
        
        # Open source PDF
        try:
            source_doc = fitz.open(source_pdf)
            print(f"📖 Source PDF: {os.path.basename(source_pdf)} ({len(source_doc)} pages)")
        except Exception as e:
            print(f"❌ Error opening source PDF: {e}")
            return
        
        # Choose extraction mode
        print("\n🔧 Extraction Options:")
        print("   1. Individual module PDFs + Complete curriculum PDF")
        print("   2. Complete curriculum PDF only")
        
        try:
            mode_choice = input("\n📋 Select extraction mode (1 or 2): ").strip()
            extract_individual = (mode_choice == "1")
        except:
            extract_individual = True
        
        # Generate base filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = selected_curriculum.replace("curriculum_", "").replace(".json", "")
        
        print(f"\\n🔄 Starting enhanced extraction...")
        
        # Process each module
        all_curriculum_pages = set()
        module_results = []
        
        for i, module in enumerate(curriculum.get('modules', []), 1):
            print(f"\\n📚 Processing Module {i}/{len(curriculum.get('modules', []))}")
            
            # Extract pages for this module
            module_pages = self.extract_module_pages(source_doc, module)
            all_curriculum_pages.update(module_pages)
            
            # Create individual module PDF if requested
            if extract_individual and module_pages:
                module_filename = f"module_{i:02d}_{base_name}_{timestamp}.pdf"
                success = self.create_module_pdf(source_doc, module_pages, module, module_filename)
                
                if success:
                    print(f"   ✅ Created: {module_filename}")
                    module_results.append({
                        'module': module,
                        'filename': module_filename,
                        'pages': len(module_pages)
                    })
                else:
                    print(f"   ❌ Failed to create: {module_filename}")
        
        # Create complete curriculum PDF
        complete_filename = f"complete_{base_name}_{timestamp}.pdf"
        print(f"\\n📖 Creating complete curriculum PDF...")
        
        success = self.create_complete_curriculum_pdf(
            source_doc, all_curriculum_pages, curriculum, complete_filename
        )
        
        source_doc.close()
        
        # Show results
        if success:
            print(f"\\n🎉 EXTRACTION COMPLETE!")
            print("=" * 50)
            print(f"📚 Curriculum: {curriculum.get('title', 'Unknown')}")
            print(f"📄 Total pages extracted: {len(all_curriculum_pages)}")
            print(f"📖 Complete PDF: {complete_filename}")
            
            if extract_individual:
                print(f"📁 Individual modules: {len(module_results)} files")
                for result in module_results:
                    module_title = result['module'].get('title', 'Unknown')
                    print(f"   • {result['filename']} ({result['pages']} pages)")
            
            # Create summary
            self.create_enhanced_summary(curriculum, all_curriculum_pages, 
                                       complete_filename, module_results)
        else:
            print("❌ Extraction failed")
    
    def create_enhanced_summary(self, curriculum: Dict, all_pages: Set[int], 
                              complete_filename: str, module_results: List[Dict]):
        """Create detailed summary of enhanced extraction"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_filename = f"enhanced_extraction_summary_{timestamp}.txt"
        
        summary_lines = [
            "📚 Enhanced Curriculum Page Extraction Summary",
            "=" * 60,
            "",
            f"📖 Curriculum: {curriculum.get('title', 'Unknown')}",
            f"📄 Total Topics: {curriculum.get('total_topics', 'Unknown')}",
            f"⏱️ Estimated Duration: {curriculum.get('estimated_total_duration', 'Unknown')}",
            f"🗓️ Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "📊 Extraction Results:",
            f"   • Total pages extracted: {len(all_pages)}",
            f"   • Complete curriculum PDF: {complete_filename}",
            f"   • Individual module PDFs: {len(module_results)}",
            "",
            f"📄 Page Numbers: {sorted(all_pages)}",
            "",
            "📚 Modules Extracted:",
        ]
        
        for i, result in enumerate(module_results, 1):
            module = result['module']
            module_title = module.get('title', f"Module {i}")
            topic_count = len(module.get('topics', []))
            duration = module.get('estimated_duration', 'Unknown')
            summary_lines.append(f"   {i:2d}. {module_title}")
            summary_lines.append(f"       📁 File: {result['filename']}")
            summary_lines.append(f"       📄 Pages: {result['pages']}")
            summary_lines.append(f"       📚 Topics: {topic_count} ({duration})")
            summary_lines.append("")
        
        summary_lines.extend([
            "🔧 Enhanced Features:",
            "   • Section continuation detection",
            "   • Theory and example pages included",
            "   • Module-wise organization",
            "   • Smart page range detection",
            "",
            "✨ Happy Learning! 🎓"
        ])
        
        # Save summary
        summary_path = os.path.join(self.output_dir, summary_filename)
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("\\n".join(summary_lines))
            print(f"💾 Summary saved to: {summary_filename}")
        except Exception as e:
            print(f"⚠️ Could not save summary: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Enhanced curriculum page extraction")
    parser.add_argument("--curriculum", help="Specific curriculum file to process")
    
    args = parser.parse_args()
    
    extractor = EnhancedCurriculumPageExtractor()
    
    if args.curriculum:
        # Non-interactive mode (could be implemented)
        print("Non-interactive mode not yet implemented")
    else:
        # Interactive mode
        extractor.enhanced_extraction_workflow()


if __name__ == "__main__":
    main()
