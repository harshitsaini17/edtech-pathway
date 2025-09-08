#!/usr/bin/env python3
"""
PDF Page Extractor for Curriculum Topics
=========================================

This module extracts specific pages from a PDF based on curriculum topics,
creating a focused study material containing only the relevant content.

Usage:
    python curriculum_page_extractor.py

Features:
- Load curriculum from JSON files
- Extract specific pages mentioned in curriculum topics
- Create a new PDF with only the required pages
- Maintain page order and structure
- Add bookmarks for easy navigation
"""

import os
import json
import fitz  # PyMuPDF
from datetime import datetime
from typing import List, Dict, Set, Tuple
import argparse


class CurriculumPageExtractor:
    """Extract PDF pages based on curriculum topics"""
    
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
    
    def extract_page_numbers(self, curriculum: Dict) -> Set[int]:
        """Extract all unique page numbers from curriculum"""
        page_numbers = set()
        
        # Extract from modules
        for module in curriculum.get('modules', []):
            if 'pages' in module:
                # Handle different page formats
                pages = module['pages']
                if isinstance(pages, list):
                    for page in pages:
                        if isinstance(page, int) and page > 0:
                            page_numbers.add(page)
                        elif isinstance(page, str) and page.isdigit():
                            page_numbers.add(int(page))
            
            # Also check topics for page information (backup)
            for i, topic in enumerate(module.get('topics', [])):
                if i < len(module.get('pages', [])):
                    page = module['pages'][i]
                    if isinstance(page, int) and page > 0:
                        page_numbers.add(page)
        
        # Remove invalid pages (like 'N/A' converted to 0)
        page_numbers.discard(0)
        
        return page_numbers
    
    def find_source_pdf(self, curriculum_file: str) -> str:
        """Find the source PDF file based on curriculum filename or doc directory"""
        # Try to infer from curriculum filename
        possible_names = []
        
        # Extract potential PDF name from curriculum filename
        if "book2" in curriculum_file.lower():
            possible_names.append("book2.pdf")
        elif "book" in curriculum_file.lower():
            possible_names.append("book.pdf")
        
        # Add common PDF names
        possible_names.extend(["book.pdf", "book2.pdf", "textbook.pdf", "document.pdf"])
        
        # Check doc directory for PDFs
        if os.path.exists(self.doc_dir):
            for filename in os.listdir(self.doc_dir):
                if filename.lower().endswith('.pdf'):
                    possible_names.append(filename)
        
        # Find the first existing PDF
        for pdf_name in possible_names:
            pdf_path = os.path.join(self.doc_dir, pdf_name)
            if os.path.exists(pdf_path):
                print(f"📚 Found source PDF: {pdf_name}")
                return pdf_path
        
        return None
    
    def extract_pages_to_pdf(self, source_pdf_path: str, page_numbers: Set[int], 
                           output_filename: str, curriculum: Dict) -> bool:
        """Extract specified pages to a new PDF"""
        try:
            # Open source PDF
            source_doc = fitz.open(source_pdf_path)
            total_pages = len(source_doc)
            
            print(f"📖 Source PDF has {total_pages} pages")
            
            # Filter valid page numbers
            valid_pages = {p for p in page_numbers if 1 <= p <= total_pages}
            invalid_pages = page_numbers - valid_pages
            
            if invalid_pages:
                print(f"⚠️ Invalid page numbers (will be skipped): {sorted(invalid_pages)}")
            
            if not valid_pages:
                print(f"❌ No valid pages to extract")
                return False
            
            # Sort pages for logical order
            sorted_pages = sorted(valid_pages)
            print(f"📄 Extracting {len(sorted_pages)} pages: {sorted_pages[:10]}{'...' if len(sorted_pages) > 10 else ''}")
            
            # Create new PDF
            output_doc = fitz.open()
            
            # Extract pages (PyMuPDF uses 0-based indexing)
            for page_num in sorted_pages:
                try:
                    source_page = source_doc[page_num - 1]  # Convert to 0-based
                    output_doc.insert_pdf(source_doc, from_page=page_num-1, to_page=page_num-1)
                except Exception as e:
                    print(f"⚠️ Error extracting page {page_num}: {e}")
            
            # Add metadata
            metadata = {
                "title": curriculum.get('title', 'Curriculum Pages'),
                "subject": f"Pages extracted for curriculum study",
                "creator": "Curriculum Page Extractor",
                "producer": "PyMuPDF",
                "creationDate": datetime.now().strftime("D:%Y%m%d%H%M%S"),
                "modDate": datetime.now().strftime("D:%Y%m%d%H%M%S")
            }
            output_doc.set_metadata(metadata)
            
            # Add bookmarks for modules (if possible)
            self.add_module_bookmarks(output_doc, curriculum, sorted_pages)
            
            # Save the output PDF
            output_path = os.path.join(self.output_dir, output_filename)
            output_doc.save(output_path)
            
            # Cleanup
            source_doc.close()
            output_doc.close()
            
            print(f"✅ Successfully created: {output_filename}")
            print(f"📊 Extracted {len(sorted_pages)} pages from {total_pages} total pages")
            return True
            
        except Exception as e:
            print(f"❌ Error creating PDF: {e}")
            return False
    
    def add_module_bookmarks(self, doc: fitz.Document, curriculum: Dict, sorted_pages: List[int]):
        """Add bookmarks for curriculum modules"""
        try:
            toc = []  # Table of contents
            
            for module in curriculum.get('modules', []):
                module_title = module.get('title', f"Module {module.get('module_number', '?')}")
                module_pages = module.get('pages', [])
                
                if module_pages:
                    # Find the first valid page for this module
                    first_module_page = None
                    for page in module_pages:
                        if isinstance(page, int) and page in sorted_pages:
                            # Find position in our extracted pages
                            try:
                                page_index = sorted_pages.index(page)
                                first_module_page = page_index
                                break
                            except ValueError:
                                continue
                    
                    if first_module_page is not None:
                        toc.append([1, module_title, first_module_page + 1])  # 1-based page number
            
            if toc:
                doc.set_toc(toc)
                print(f"📑 Added {len(toc)} module bookmarks")
                
        except Exception as e:
            print(f"⚠️ Could not add bookmarks: {e}")
    
    def create_extraction_summary(self, curriculum: Dict, extracted_pages: Set[int], 
                                output_filename: str) -> str:
        """Create a summary of the extraction"""
        summary_lines = [
            f"📚 Curriculum Page Extraction Summary",
            f"=" * 50,
            f"",
            f"📖 Curriculum: {curriculum.get('title', 'Unknown')}",
            f"📄 Total Topics: {curriculum.get('total_topics', 'Unknown')}",
            f"⏱️ Estimated Duration: {curriculum.get('estimated_total_duration', 'Unknown')}",
            f"",
            f"📊 Extraction Results:",
            f"   • Pages extracted: {len(extracted_pages)}",
            f"   • Output file: {output_filename}",
            f"   • Modules: {len(curriculum.get('modules', []))}",
            f"",
            f"📄 Page Numbers: {sorted(extracted_pages)}",
            f"",
            f"📚 Modules Included:",
        ]
        
        for i, module in enumerate(curriculum.get('modules', []), 1):
            module_title = module.get('title', f"Module {i}")
            topic_count = len(module.get('topics', []))
            duration = module.get('estimated_duration', 'Unknown')
            summary_lines.append(f"   {i:2d}. {module_title} ({topic_count} topics, {duration})")
        
        return "\n".join(summary_lines)
    
    def interactive_workflow(self):
        """Interactive workflow for curriculum page extraction"""
        print("🎓 Curriculum Page Extractor")
        print("=" * 50)
        print("Extract specific PDF pages for your selected curriculum topics")
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
        
        # Extract page numbers
        page_numbers = self.extract_page_numbers(curriculum)
        print(f"📄 Found {len(page_numbers)} unique pages to extract")
        
        if not page_numbers:
            print("❌ No valid page numbers found in curriculum")
            return
        
        # Find source PDF
        source_pdf = self.find_source_pdf(selected_curriculum)
        if not source_pdf:
            print("❌ Could not find source PDF file")
            print("   Please ensure PDF is in the 'doc' directory")
            return
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = selected_curriculum.replace("curriculum_", "").replace(".json", "")
        output_filename = f"pages_{base_name}_{timestamp}.pdf"
        
        print(f"💾 Output will be saved as: {output_filename}")
        
        # Confirm extraction
        confirm = input("\n🚀 Proceed with page extraction? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Extraction cancelled")
            return
        
        # Extract pages
        print(f"\n🔄 Extracting pages...")
        success = self.extract_pages_to_pdf(source_pdf, page_numbers, output_filename, curriculum)
        
        if success:
            # Create summary
            summary = self.create_extraction_summary(curriculum, page_numbers, output_filename)
            print(f"\n{summary}")
            
            # Save summary to file
            summary_filename = output_filename.replace(".pdf", "_summary.txt")
            summary_path = os.path.join(self.output_dir, summary_filename)
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"💾 Summary saved to: {summary_filename}")
        else:
            print("❌ Page extraction failed")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Extract PDF pages for curriculum topics")
    parser.add_argument("--curriculum", help="Specific curriculum file to process")
    parser.add_argument("--output", help="Output PDF filename")
    
    args = parser.parse_args()
    
    extractor = CurriculumPageExtractor()
    
    if args.curriculum and args.output:
        # Non-interactive mode
        curriculum = extractor.load_curriculum(args.curriculum)
        if curriculum:
            page_numbers = extractor.extract_page_numbers(curriculum)
            source_pdf = extractor.find_source_pdf(args.curriculum)
            if source_pdf and page_numbers:
                extractor.extract_pages_to_pdf(source_pdf, page_numbers, args.output, curriculum)
    else:
        # Interactive mode
        extractor.interactive_workflow()


if __name__ == "__main__":
    main()
