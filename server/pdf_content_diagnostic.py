#!/usr/bin/env python3
"""
PDF Content Diagnostic Tool
===========================
Verifies that we're extracting meaningful content from PDF pages for theory generation.
"""

import fitz
import json
import os

class PDFContentDiagnostic:
    def __init__(self):
        self.pdf_path = "doc/book2.pdf"
    
    def test_pdf_extraction(self, page_numbers=[75, 83, 88, 171, 185]):
        """Test PDF extraction for sample pages"""
        print("🔍 PDF Content Diagnostic Tool")
        print("=" * 50)
        
        if not os.path.exists(self.pdf_path):
            print(f"❌ PDF not found: {self.pdf_path}")
            return False
        
        try:
            doc = fitz.open(self.pdf_path)
            print(f"✅ PDF opened successfully: {len(doc)} pages")
            
            for page_num in page_numbers:
                print(f"\n📄 Testing Page {page_num}:")
                print("-" * 30)
                
                if page_num > len(doc):
                    print(f"❌ Page {page_num} exceeds document length")
                    continue
                
                page = doc[page_num - 1]  # 0-based indexing
                text = page.get_text()
                
                # Content analysis
                word_count = len(text.split())
                char_count = len(text)
                line_count = len(text.split('\n'))
                
                print(f"📊 Content Stats:")
                print(f"   Words: {word_count}")
                print(f"   Characters: {char_count}")
                print(f"   Lines: {line_count}")
                
                # Check for mathematical content
                math_indicators = ['=', '∑', 'σ', 'μ', 'x̄', '±', '≤', '≥', '√', 'Var', 'E[', 'variance', 'mean', 'standard deviation']
                math_found = [indicator for indicator in math_indicators if indicator in text]
                print(f"   Math indicators found: {len(math_found)} - {math_found[:5]}")
                
                # Check for examples
                examples = ['example', 'EXAMPLE', 'solution', 'SOLUTION', 'problem', 'PROBLEM']
                example_found = [ex for ex in examples if ex in text]
                print(f"   Example indicators: {example_found}")
                
                # Show sample content (first 300 chars)
                print(f"📝 Sample Content:")
                sample = text.strip()[:300].replace('\n', ' ')
                print(f"   \"{sample}...\"")
                
                # Check if content is meaningful (not just page numbers/headers)
                meaningful = word_count > 50 and any(word in text.lower() for word in ['statistics', 'probability', 'data', 'variable', 'distribution', 'sample', 'population'])
                print(f"   Meaningful content: {'✅' if meaningful else '❌'}")
                
            doc.close()
            return True
            
        except Exception as e:
            print(f"❌ Error testing PDF: {e}")
            return False
    
    def compare_with_curriculum_pages(self):
        """Check content from curriculum pages"""
        print(f"\n🎯 Testing Curriculum-Specific Pages")
        print("=" * 50)
        
        # Load latest curriculum
        output_dir = "output"
        curriculum_files = [f for f in os.listdir(output_dir) if 'curriculum' in f and f.endswith('.json')]
        
        if not curriculum_files:
            print("❌ No curriculum files found")
            return
        
        curriculum_files.sort(reverse=True)
        latest_curriculum = curriculum_files[0]
        
        with open(os.path.join(output_dir, latest_curriculum), 'r') as f:
            curriculum = json.load(f)
        
        print(f"📚 Using curriculum: {latest_curriculum}")
        
        # Extract all page numbers from curriculum
        all_pages = []
        for module in curriculum.get('modules', []):
            all_pages.extend(module.get('pages', []))
        
        unique_pages = sorted(set(all_pages))[:10]  # Test first 10 unique pages
        print(f"🔍 Testing {len(unique_pages)} curriculum pages: {unique_pages}")
        
        self.test_pdf_extraction(unique_pages)
    
    def test_actual_theory_generation_input(self):
        """Test what actually gets sent to LLM"""
        print(f"\n🤖 Testing Theory Generation Input")
        print("=" * 50)
        
        try:
            doc = fitz.open(self.pdf_path)
            test_pages = [75, 171, 185]  # Key theory pages
            
            for page_num in test_pages:
                page = doc[page_num - 1]
                text = page.get_text()
                
                # Simulate what gets sent to LLM
                cleaned_text = self.clean_content(text)
                
                print(f"\n📄 Page {page_num} - What LLM receives:")
                print(f"   Original length: {len(text)} chars")
                print(f"   Cleaned length: {len(cleaned_text)} chars")
                print(f"   First 500 chars: \"{cleaned_text[:500]}...\"")
                
                # Check if this is substantial content
                substantial = len(cleaned_text) > 1000 and len(cleaned_text.split()) > 150
                print(f"   Substantial content: {'✅' if substantial else '❌'}")
                
            doc.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def clean_content(self, text):
        """Simulate content cleaning for LLM"""
        # Basic cleaning
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip very short lines, page numbers, headers
            if len(line) < 3 or line.isdigit() or len(line.split()) < 2:
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

def main():
    diagnostic = PDFContentDiagnostic()
    
    # Test basic PDF extraction
    print("Phase 1: Basic PDF Extraction Test")
    diagnostic.test_pdf_extraction()
    
    # Test curriculum-specific pages
    print("\n" + "="*70)
    print("Phase 2: Curriculum Page Content Test")
    diagnostic.compare_with_curriculum_pages()
    
    # Test actual theory generation input
    print("\n" + "="*70)
    print("Phase 3: Theory Generation Input Test")
    diagnostic.test_actual_theory_generation_input()

if __name__ == "__main__":
    main()
