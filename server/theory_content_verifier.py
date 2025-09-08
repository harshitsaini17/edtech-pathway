#!/usr/bin/env python3
"""
Theory Generation Content Verification Tool
==========================================
Verifies that theories are actually based on PDF content by checking content overlap
and specific examples/formulas from the source material.
"""

import fitz
import json
import os
import re
from LLM import AdvancedAzureLLM

class TheoryContentVerifier:
    def __init__(self):
        self.pdf_path = "doc/book2.pdf"
        self.llm = AdvancedAzureLLM()
    
    def extract_page_content(self, page_num):
        """Extract content from a specific page"""
        try:
            doc = fitz.open(self.pdf_path)
            page = doc[page_num - 1]
            content = page.get_text()
            doc.close()
            return content
        except Exception as e:
            print(f"Error extracting page {page_num}: {e}")
            return ""
    
    def test_theory_generation_with_content_verification(self):
        """Generate theory and verify it uses PDF content"""
        
        # Test page with rich content
        test_page = 171  # Expectation chapter
        pdf_content = self.extract_page_content(test_page)
        
        print("🔍 THEORY GENERATION VERIFICATION TEST")
        print("=" * 60)
        print(f"📄 Testing with Page {test_page} content")
        print(f"📊 PDF Content Length: {len(pdf_content)} characters")
        
        # Extract specific elements from PDF
        formulas = re.findall(r'E\[.*?\]|Var\(.*?\)|f\s*\(.*?\)|P\{.*?\}', pdf_content)
        examples = re.findall(r'EXAMPLE\s+\d+\.\d+[a-z]?.*?SOLUTION.*?(?=EXAMPLE|\n\n|\Z)', pdf_content, re.DOTALL)
        key_terms = re.findall(r'\b(expectation|expected value|variance|random variable|probability|distribution)\b', pdf_content, re.IGNORECASE)
        
        print(f"🔍 Found in PDF:")
        print(f"   Formulas: {len(formulas)} - {formulas[:3]}")
        print(f"   Examples: {len(examples)} complete examples")
        print(f"   Key terms: {len(set(key_terms))} unique terms")
        
        # Test 1: Generate theory WITH specific instruction to use PDF content
        explicit_prompt = f"""
        Generate a comprehensive theory section about Expectation based STRICTLY on this PDF content:
        
        PDF CONTENT:
        {pdf_content[:4000]}
        
        CRITICAL REQUIREMENTS:
        1. Use ONLY information from the provided PDF content
        2. Include the specific examples shown in the PDF
        3. Use the exact formulas and notation from the PDF
        4. Reference specific data/numbers mentioned in the PDF
        5. If the PDF mentions specific example numbers (like "EXAMPLE 4.3h"), include them
        
        Generate a theory that clearly demonstrates you used the PDF content.
        """
        
        print(f"\n🤖 Generating theory with explicit PDF usage instruction...")
        theory_explicit = self.llm.generate_response(explicit_prompt)
        
        # Test 2: Generate theory WITHOUT PDF content (control)
        generic_prompt = """
        Generate a comprehensive theory section about Expectation in probability theory.
        Include definitions, formulas, examples, and applications.
        Make it educational and thorough.
        """
        
        print(f"🤖 Generating control theory without PDF content...")
        theory_generic = self.llm.generate_response(generic_prompt)
        
        # Analysis
        print(f"\n📊 CONTENT ANALYSIS:")
        print("=" * 60)
        
        # Check for PDF-specific content in theories
        def analyze_theory_content(theory, name):
            print(f"\n{name}:")
            print(f"   Length: {len(theory)} characters")
            
            # Check for specific PDF formulas
            pdf_formula_matches = sum(1 for formula in formulas if formula in theory)
            print(f"   PDF formulas used: {pdf_formula_matches}/{len(formulas)}")
            
            # Check for specific example references
            example_refs = re.findall(r'EXAMPLE\s+\d+\.\d+[a-z]?', theory)
            print(f"   Specific example references: {len(example_refs)}")
            
            # Check for PDF-specific terms
            pdf_specific_terms = ['joint density', 'conditional density', 'fX|Y', 'f(x,y)']
            pdf_term_matches = sum(1 for term in pdf_specific_terms if term.lower() in theory.lower())
            print(f"   PDF-specific terms: {pdf_term_matches}/{len(pdf_specific_terms)}")
            
            # Generic vs specific content
            generic_phrases = ['in general', 'typically', 'usually', 'commonly', 'often']
            generic_count = sum(1 for phrase in generic_phrases if phrase in theory.lower())
            
            specific_phrases = ['as shown in', 'from the given', 'in this example', 'according to']  
            specific_count = sum(1 for phrase in specific_phrases if phrase in theory.lower())
            
            print(f"   Generic language: {generic_count} phrases")
            print(f"   Specific references: {specific_count} phrases")
            
            # Overall assessment
            pdf_utilization_score = (pdf_formula_matches * 3 + len(example_refs) * 2 + pdf_term_matches + specific_count) / max(1, len(formulas) + len(example_refs) + len(pdf_specific_terms) + 4) * 100
            print(f"   PDF Utilization Score: {pdf_utilization_score:.1f}%")
            
            return pdf_utilization_score
        
        score1 = analyze_theory_content(theory_explicit, "📖 Theory with PDF instruction")
        score2 = analyze_theory_content(theory_generic, "🎯 Control theory (no PDF)")
        
        print(f"\n🎯 VERIFICATION RESULTS:")
        print("=" * 60)
        
        if score1 > score2 + 20:
            print("✅ PDF content IS being utilized when explicitly instructed")
        elif score1 > score2:
            print("⚠️ PDF content is somewhat utilized but could be better")  
        else:
            print("❌ PDF content may NOT be properly utilized")
        
        print(f"\nPDF-instructed theory score: {score1:.1f}%")
        print(f"Generic theory score: {score2:.1f}%")
        
        # Save theories for manual inspection
        os.makedirs("output", exist_ok=True)
        
        with open("output/theory_verification_explicit.txt", "w") as f:
            f.write("THEORY GENERATED WITH PDF CONTENT INSTRUCTION\n")
            f.write("=" * 50 + "\n\n")
            f.write(theory_explicit)
            
        with open("output/theory_verification_generic.txt", "w") as f:
            f.write("CONTROL THEORY (NO PDF CONTENT)\n")
            f.write("=" * 50 + "\n\n")
            f.write(theory_generic)
        
        print(f"\n📁 Theories saved for manual review:")
        print(f"   📖 output/theory_verification_explicit.txt")
        print(f"   🎯 output/theory_verification_generic.txt")

def main():
    verifier = TheoryContentVerifier()
    verifier.test_theory_generation_with_content_verification()

if __name__ == "__main__":
    main()
