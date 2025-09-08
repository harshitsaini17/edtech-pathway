#!/usr/bin/env python3
"""
PDF-Content-Based Theory Generator
=================================
Ensures theories are authentically derived from PDF content rather than generic LLM knowledge.
Forces the LLM to extract and use specific examples, formulas, and content from the PDF.

Key Features:
- Content extraction verification  
- Forced PDF utilization prompts
- Specific example and formula extraction
- Content authenticity scoring
- Pitfall callouts with 🚫 format
"""

import fitz
import json
import os
import re
from datetime import datetime
from LLM import AdvancedAzureLLM

class PDFContentBasedTheoryGenerator:
    """Generates theories that authentically use PDF content"""
    
    def __init__(self):
        self.pdf_path = "doc/book2.pdf"
        self.output_dir = "output"
        self.llm = AdvancedAzureLLM()
        
    def extract_page_content(self, page_numbers):
        """Extract comprehensive content from PDF pages"""
        try:
            doc = fitz.open(self.pdf_path)
            content_blocks = []
            
            for page_num in page_numbers:
                if page_num <= len(doc):
                    page = doc[page_num - 1]
                    text = page.get_text()
                    
                    # Extract specific elements
                    formulas = re.findall(r'(?:E\[.*?\]|Var\(.*?\)|P\{.*?\}|f\s*\([^)]*\)|σ\s*=|μ\s*=|\w+\s*=\s*[^,\n]+)', text)
                    examples = re.findall(r'(EXAMPLE\s+\d+\.\d+[a-z]?[^E]*?(?=EXAMPLE|\n\n\n|\Z))', text, re.DOTALL | re.IGNORECASE)
                    solutions = re.findall(r'(SOLUTION[^E]*?(?=EXAMPLE|\n\n\n|\Z))', text, re.DOTALL | re.IGNORECASE)
                    
                    content_blocks.append({
                        'page': page_num,
                        'raw_text': text,
                        'word_count': len(text.split()),
                        'formulas': formulas,
                        'examples': examples,
                        'solutions': solutions,
                        'key_terms': self.extract_key_terms(text)
                    })
            
            doc.close()
            return content_blocks
            
        except Exception as e:
            print(f"❌ Error extracting PDF content: {e}")
            return []
    
    def extract_key_terms(self, text):
        """Extract domain-specific key terms"""
        patterns = [
            r'\b(?:expectation|expected value|variance|covariance|standard deviation)\b',
            r'\b(?:random variable|probability|distribution|density|mass function)\b',
            r'\b(?:sample|population|mean|median|mode)\b',
            r'\b(?:independent|conditional|joint)\b'
        ]
        
        key_terms = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            key_terms.extend([match.lower() for match in matches])
        
        return list(set(key_terms))
    
    def create_pdf_enforced_prompt(self, topic_title, content_blocks):
        """Create a prompt that enforces PDF content usage"""
        
        # Consolidate PDF content
        all_formulas = []
        all_examples = []
        all_text = []
        
        for block in content_blocks:
            all_formulas.extend(block['formulas'])
            all_examples.extend(block['examples'])
            all_text.append(block['raw_text'])
        
        combined_text = '\n'.join(all_text)
        
        prompt = f"""
You are creating educational theory content for the topic: "{topic_title}"

CRITICAL REQUIREMENT: You MUST base your theory EXCLUSIVELY on the provided PDF content below. 
Do NOT use external knowledge. Extract and build from what is given.

PDF SOURCE CONTENT:
{combined_text[:8000]}

SPECIFIC PDF ELEMENTS TO USE:
Formulas found: {all_formulas[:10]}
Examples found: {len(all_examples)} complete examples
Key concepts in PDF: {', '.join(set([term for block in content_blocks for term in block['key_terms']]))}

MANDATORY REQUIREMENTS:
1. **Use the specific examples from the PDF** - reference them by their exact numbers (e.g., "EXAMPLE 4.3h")
2. **Include the exact formulas from the PDF** - use the same notation and formatting
3. **Build explanations around what's actually in the PDF** - don't add external examples
4. **Reference specific data/numbers** mentioned in the PDF content
5. **Include pitfall callouts** using this exact format:

🚫 **Common Mistake**: [Specific mistake from PDF context]
**Why it's wrong**: [Explanation]
**Correct approach**: [Right way]

THEORY STRUCTURE REQUIRED:
## 🎯 What You'll Learn
[Learning objectives based on PDF content]

## 📖 Core Concepts  
[Main concepts from the PDF, with specific examples and formulas]

## 🔢 Mathematical Framework
[Formulas and derivations exactly as shown in PDF]

## 💡 Worked Examples
[Use the specific examples from the PDF content - EXAMPLE X.Xx format]

## 🚫 Common Pitfalls
[At least 3 pitfall callouts based on what the PDF content suggests could go wrong]

## 🏭 Real-World Applications
[Only applications that can be inferred from the PDF content]

## 🧮 Key Formulas Summary
[List all formulas used, exactly as they appear in PDF]

Generate comprehensive theory content that clearly demonstrates you used the PDF material.
Be academic but engaging. Include proofs and derivations shown in the PDF.
"""
        return prompt
    
    def verify_pdf_usage(self, theory, content_blocks):
        """Verify that theory actually uses PDF content"""
        score = 0
        max_score = 0
        
        # Check formula usage
        all_formulas = [formula for block in content_blocks for formula in block['formulas']]
        formula_matches = sum(1 for formula in all_formulas[:10] if formula in theory)
        score += formula_matches * 3
        max_score += len(all_formulas[:10]) * 3
        
        # Check example references
        example_refs = re.findall(r'EXAMPLE\s+\d+\.\d+[a-z]?', theory, re.IGNORECASE)
        score += len(example_refs) * 5
        max_score += 10  # Expected at least 2 examples
        
        # Check for pitfall callouts
        pitfall_callouts = theory.count('🚫')
        score += pitfall_callouts * 2
        max_score += 6  # Expected 3 pitfalls
        
        # Check key terms usage
        all_key_terms = [term for block in content_blocks for term in block['key_terms']]
        term_matches = sum(1 for term in set(all_key_terms) if term in theory.lower())
        score += term_matches
        max_score += len(set(all_key_terms))
        
        # Check for specific PDF references
        specific_refs = ['as shown', 'from the given', 'in the example', 'according to']
        ref_matches = sum(1 for ref in specific_refs if ref in theory.lower())
        score += ref_matches
        max_score += len(specific_refs)
        
        authenticity_score = (score / max(max_score, 1)) * 100
        
        return {
            'authenticity_score': authenticity_score,
            'formula_matches': formula_matches,
            'example_references': len(example_refs),
            'pitfall_callouts': pitfall_callouts,
            'term_matches': term_matches,
            'specific_references': ref_matches
        }
    
    def generate_pdf_based_theory(self, topic_title, page_numbers):
        """Generate theory that authentically uses PDF content"""
        
        print(f"📚 Generating PDF-based theory for: {topic_title}")
        print(f"📄 Using pages: {page_numbers}")
        
        # Extract content
        content_blocks = self.extract_page_content(page_numbers)
        if not content_blocks:
            print("❌ Failed to extract PDF content")
            return None
        
        total_words = sum(block['word_count'] for block in content_blocks)
        total_formulas = sum(len(block['formulas']) for block in content_blocks)
        total_examples = sum(len(block['examples']) for block in content_blocks)
        
        print(f"📊 Extracted content: {total_words} words, {total_formulas} formulas, {total_examples} examples")
        
        # Create enforced prompt
        prompt = self.create_pdf_enforced_prompt(topic_title, content_blocks)
        
        # Generate theory
        try:
            theory = self.llm.generate_response(prompt)
            print(f"✅ Generated theory: {len(theory)} characters")
            
            # Verify authenticity
            verification = self.verify_pdf_usage(theory, content_blocks)
            print(f"🎯 Authenticity score: {verification['authenticity_score']:.1f}%")
            print(f"   Formula usage: {verification['formula_matches']}")
            print(f"   Example references: {verification['example_references']}")
            print(f"   Pitfall callouts: {verification['pitfall_callouts']}")
            
            return {
                'theory': theory,
                'verification': verification,
                'content_stats': {
                    'total_words': total_words,
                    'total_formulas': total_formulas,
                    'total_examples': total_examples
                }
            }
            
        except Exception as e:
            print(f"❌ Error generating theory: {e}")
            return None
    
    def generate_curriculum_theories(self, curriculum_file=None):
        """Generate PDF-based theories for all curriculum topics"""
        
        if not curriculum_file:
            # Find latest curriculum
            curriculum_files = [f for f in os.listdir(self.output_dir) 
                              if 'curriculum' in f and f.endswith('.json')]
            if not curriculum_files:
                print("❌ No curriculum files found")
                return
            
            curriculum_files.sort(reverse=True)
            curriculum_file = curriculum_files[0]
        
        curriculum_path = os.path.join(self.output_dir, curriculum_file)
        
        with open(curriculum_path, 'r') as f:
            curriculum = json.load(f)
        
        print(f"🎓 Generating PDF-based theories for curriculum: {curriculum_file}")
        print(f"📚 Curriculum: {curriculum['title']}")
        
        results = []
        
        for module in curriculum['modules']:
            print(f"\n📖 Processing {module['title']}")
            
            for i, topic in enumerate(module['topics']):
                pages = [module['pages'][i]] if i < len(module['pages']) else []
                
                if pages:
                    theory_result = self.generate_pdf_based_theory(topic, pages)
                    
                    if theory_result:
                        results.append({
                            'module': module['title'],
                            'topic': topic,
                            'pages': pages,
                            'theory': theory_result['theory'],
                            'verification': theory_result['verification']
                        })
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Individual theory files
        for result in results:
            safe_topic = re.sub(r'[^\w\s-]', '', result['topic'])[:50].replace(' ', '_')
            theory_file = os.path.join(self.output_dir, f"pdf_theory_{safe_topic}_{timestamp}.md")
            
            with open(theory_file, 'w', encoding='utf-8') as f:
                f.write(f"# {result['topic']}\n\n")
                f.write(f"**Pages Used**: {result['pages']}\n")
                f.write(f"**Authenticity Score**: {result['verification']['authenticity_score']:.1f}%\n\n")
                f.write(result['theory'])
        
        # Summary report
        summary_file = os.path.join(self.output_dir, f"pdf_theories_summary_{timestamp}.json")
        with open(summary_file, 'w') as f:
            json.dump({
                'curriculum_used': curriculum_file,
                'generation_date': timestamp,
                'total_theories': len(results),
                'average_authenticity': sum(r['verification']['authenticity_score'] for r in results) / len(results),
                'theories': results
            }, f, indent=2)
        
        print(f"\n✅ Generated {len(results)} PDF-based theories")
        print(f"📁 Summary saved to: {summary_file}")
        
        # Display quality metrics
        avg_score = sum(r['verification']['authenticity_score'] for r in results) / len(results)
        high_quality = sum(1 for r in results if r['verification']['authenticity_score'] > 70)
        
        print(f"\n📊 Quality Metrics:")
        print(f"   Average authenticity: {avg_score:.1f}%")
        print(f"   High-quality theories (>70%): {high_quality}/{len(results)}")

def main():
    generator = PDFContentBasedTheoryGenerator()
    
    # Test with a single topic first
    print("🧪 Testing with single topic...")
    test_result = generator.generate_pdf_based_theory("4.4 Expectation", [171, 175])
    
    if test_result and test_result['verification']['authenticity_score'] > 60:
        print("✅ Single topic test passed. Generating full curriculum...")
        generator.generate_curriculum_theories()
    else:
        print("❌ Single topic test failed. Check PDF content and prompts.")

if __name__ == "__main__":
    main()
