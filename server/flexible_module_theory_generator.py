#!/usr/bin/env python3
"""
Flexible Module Theory Generator
===============================
A universal theory generator that adapts to any module content by:
1. Analyzing the module topics and content
2. Using LLM to generate a custom prompt template
3. Applying that template to generate theories

This works for any subject: statistics, engineering, physics, mathematics, etc.

Usage:
    python flexible_module_theory_generator.py
"""

import fitz
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any
from LLM import AdvancedAzureLLM

class FlexibleModuleTheoryGenerator:
    """Generates theories for any module by dynamically creating appropriate prompts"""
    
    def __init__(self):
        self.pdf_path = "doc/book2.pdf"
        self.output_dir = "output"
        self.llm = AdvancedAzureLLM()
        
        # Example prompt template for consistency
        self.example_prompt_template = """
You are creating educational theory content for the topic: "{topic_title}"

CRITICAL REQUIREMENT: You MUST base your theory EXCLUSIVELY on the provided PDF content below. 
Do NOT use external knowledge. Extract and build from what is given.

PDF SOURCE CONTENT:
{pdf_content}

SPECIFIC PDF ELEMENTS TO USE:
Formulas found: {formulas}
Examples found: {examples_count} complete examples
Key concepts in PDF: {key_concepts}

MANDATORY REQUIREMENTS:
1. **Use the specific examples from the PDF** - reference them by their exact numbers
2. **Include the exact formulas from the PDF** - use the same notation and formatting
3. **Build explanations around what's actually in the PDF** - don't add external examples
4. **Include pitfall callouts** using this exact format:

🚫 **Common Mistake**: [Specific mistake from PDF context]
**Why it's wrong**: [Explanation]
**Correct approach**: [Right way]

THEORY STRUCTURE REQUIRED:
## 🎯 What You'll Learn
## 📖 Core Concepts  
## 🔢 Mathematical Framework
## 💡 Worked Examples
## 🚫 Common Pitfalls
## 🏭 Real-World Applications
## 🧮 Key Formulas Summary
"""
    
    def load_curriculum_modules(self):
        """Load available curriculum modules"""
        curriculum_files = [f for f in os.listdir(self.output_dir) 
                          if 'curriculum' in f and f.endswith('.json')]
        
        if not curriculum_files:
            print("❌ No curriculum files found")
            return []
        
        curriculum_files.sort(reverse=True)
        latest_curriculum = curriculum_files[0]
        
        with open(os.path.join(self.output_dir, latest_curriculum), 'r') as f:
            curriculum = json.load(f)
        
        print(f"📚 Loaded curriculum: {curriculum['title']}")
        return curriculum['modules']
    
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
                    
                    content_blocks.append({
                        'page': page_num,
                        'raw_text': text,
                        'word_count': len(text.split()),
                        'formulas': formulas,
                        'examples': examples,
                        'key_terms': self.extract_key_terms(text)
                    })
            
            doc.close()
            return content_blocks
            
        except Exception as e:
            print(f"❌ Error extracting PDF content: {e}")
            return []
    
    def extract_key_terms(self, text):
        """Extract domain-specific key terms"""
        # General academic terms
        general_patterns = [
            r'\b(?:theorem|definition|proof|lemma|corollary|proposition)\b',
            r'\b(?:analysis|method|algorithm|procedure|approach)\b',
            r'\b(?:example|solution|result|conclusion|application)\b'
        ]
        
        # Subject-specific terms (will be expanded dynamically)
        subject_patterns = [
            r'\b(?:probability|statistics|random|distribution|variance|expectation)\b',
            r'\b(?:function|equation|derivative|integral|limit|series)\b',
            r'\b(?:matrix|vector|linear|system|control|signal)\b',
            r'\b(?:energy|force|momentum|wave|frequency|amplitude)\b'
        ]
        
        key_terms = []
        for patterns in [general_patterns, subject_patterns]:
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                key_terms.extend([match.lower() for match in matches])
        
        return list(set(key_terms))[:10]  # Top 10 most relevant terms
    
    def analyze_module_content(self, module_data):
        """Analyze module content to understand its characteristics"""
        
        topics = module_data['topics']
        pages = module_data.get('pages', [])
        
        # Extract sample content for analysis
        sample_content = []
        if pages:
            sample_pages = pages[:3]  # Analyze first 3 pages
            content_blocks = self.extract_page_content(sample_pages)
            sample_content = content_blocks
        
        # Analyze content characteristics
        total_words = sum(block['word_count'] for block in sample_content) if sample_content else 0
        all_formulas = [formula for block in sample_content for formula in block['formulas']] if sample_content else []
        all_key_terms = [term for block in sample_content for term in block['key_terms']] if sample_content else []
        
        # Determine subject area
        subject_keywords = {
            'mathematics': ['function', 'equation', 'derivative', 'integral', 'theorem', 'proof'],
            'statistics': ['probability', 'distribution', 'variance', 'sample', 'population', 'hypothesis'],
            'engineering': ['system', 'signal', 'control', 'frequency', 'response', 'design'],
            'physics': ['energy', 'force', 'wave', 'particle', 'momentum', 'field']
        }
        
        subject_scores = {}
        for subject, keywords in subject_keywords.items():
            score = sum(1 for term in all_key_terms if any(kw in term for kw in keywords))
            subject_scores[subject] = score
        
        primary_subject = max(subject_scores, key=subject_scores.get) if subject_scores else 'general'
        
        return {
            'module_title': module_data['title'],
            'topic_count': len(topics),
            'sample_topics': topics[:3],
            'total_pages': len(pages),
            'content_words': total_words,
            'formula_count': len(all_formulas),
            'sample_formulas': all_formulas[:5],
            'key_terms': all_key_terms[:10],
            'primary_subject': primary_subject,
            'has_examples': any('example' in block['raw_text'].lower() for block in sample_content),
            'mathematical_content': len(all_formulas) > 0
        }
    
    def generate_custom_prompt_template(self, module_analysis):
        """Use LLM to generate a custom prompt template for this specific module"""
        
        analysis_summary = f"""
Module: {module_analysis['module_title']}
Subject Area: {module_analysis['primary_subject']}
Topics Count: {module_analysis['topic_count']}
Sample Topics: {', '.join(module_analysis['sample_topics'])}
Content Characteristics:
- Mathematical Content: {module_analysis['mathematical_content']}
- Has Examples: {module_analysis['has_examples']}
- Formula Count: {module_analysis['formula_count']}
- Key Terms: {', '.join(module_analysis['key_terms'])}
"""

        prompt_generation_request = f"""
You are an expert educational content designer. Create a custom prompt template for generating high-quality educational theories for this specific module:

{analysis_summary}

REFERENCE EXAMPLE (maintain this structure and quality):
{self.example_prompt_template}

REQUIREMENTS:
1. Analyze the module characteristics and adapt the prompt accordingly
2. Keep the same overall structure (🎯, 📖, 🔢, 💡, 🚫, 🏭, 🧮 sections)
3. Customize the content focus based on the subject area
4. Emphasize relevant elements (e.g., more math for statistics, more applications for engineering)
5. Include subject-specific pitfall categories
6. Maintain the 🚫 pitfall format exactly

CUSTOMIZATION GUIDELINES:
- For mathematics/statistics: Focus on proofs, derivations, mathematical rigor
- For engineering: Emphasize practical applications, design considerations
- For physics: Include conceptual understanding, real-world phenomena
- For general subjects: Balance theory and application

Generate a complete prompt template that will produce theories specifically suited to this module's content and subject area. Return ONLY the prompt template, no other text.
"""
        
        try:
            custom_template = self.llm.generate_response(prompt_generation_request)
            print(f"✅ Generated custom prompt template for {module_analysis['primary_subject']} content")
            return custom_template.strip()
            
        except Exception as e:
            print(f"⚠️ Error generating custom prompt, using default: {e}")
            return self.example_prompt_template
    
    def generate_theory_with_custom_prompt(self, topic_title, pages, custom_template):
        """Generate theory using the custom prompt template"""
        
        print(f"📚 Generating theory for: {topic_title}")
        print(f"📄 Using pages: {pages}")
        
        # Extract content
        content_blocks = self.extract_page_content(pages)
        if not content_blocks:
            print("❌ Failed to extract PDF content")
            return None
        
        # Prepare content data
        combined_text = '\n'.join([block['raw_text'] for block in content_blocks])
        all_formulas = [formula for block in content_blocks for formula in block['formulas']]
        all_examples = [ex for block in content_blocks for ex in block['examples']]
        all_key_terms = [term for block in content_blocks for term in block['key_terms']]
        
        # Fill in the custom template
        try:
            filled_prompt = custom_template.format(
                topic_title=topic_title,
                pdf_content=combined_text[:8000],
                formulas=', '.join(all_formulas[:10]) if all_formulas else 'None found',
                examples_count=len(all_examples),
                key_concepts=', '.join(set(all_key_terms)) if all_key_terms else 'General concepts'
            )
            
        except KeyError as e:
            print(f"⚠️ Template formatting error: {e}, using simplified version")
            # Fallback to basic formatting
            filled_prompt = f"""
Generate educational theory for: {topic_title}

Based on this PDF content:
{combined_text[:6000]}

Include: formulas, examples, explanations, and pitfall callouts with 🚫 format.
Use the exact content from the PDF pages provided.
"""
        
        # Generate theory
        try:
            theory = self.llm.generate_response(filled_prompt)
            print(f"✅ Generated theory: {len(theory)} characters")
            
            # Basic verification
            pitfall_count = theory.count('🚫')
            formula_mentions = sum(1 for formula in all_formulas[:5] if formula in theory)
            
            verification_score = (pitfall_count * 20) + (formula_mentions * 15)
            
            print(f"📊 Quality metrics:")
            print(f"   Pitfall callouts: {pitfall_count}")
            print(f"   Formula usage: {formula_mentions}")
            print(f"   Quality score: {verification_score}")
            
            return {
                'theory': theory,
                'verification': {
                    'pitfall_callouts': pitfall_count,
                    'formula_usage': formula_mentions,
                    'quality_score': verification_score
                }
            }
            
        except Exception as e:
            print(f"❌ Error generating theory: {e}")
            return None
    
    def select_and_generate_module_theories(self):
        """Interactive module selection and theory generation"""
        
        # Load available modules
        modules = self.load_curriculum_modules()
        if not modules:
            return
        
        print(f"\n📚 Available Modules:")
        print("-" * 60)
        
        for i, module in enumerate(modules, 1):
            print(f"{i:2d}. {module['title']}")
            print(f"    📄 Topics: {len(module['topics'])}")
            print(f"    📑 Pages: {len(module.get('pages', []))}")
            print()
        
        # User selection
        try:
            choice = input("🔢 Select module number (or 'all' for all modules): ").strip()
            
            if choice.lower() == 'all':
                selected_modules = modules
                print("📚 Generating theories for ALL modules")
            else:
                module_idx = int(choice) - 1
                if 0 <= module_idx < len(modules):
                    selected_modules = [modules[module_idx]]
                    print(f"📚 Selected: {modules[module_idx]['title']}")
                else:
                    print("❌ Invalid selection")
                    return
                    
        except ValueError:
            print("❌ Invalid input")
            return
        
        # Generate theories for selected modules
        all_results = []
        
        for module in selected_modules:
            print(f"\n🎯 Processing: {module['title']}")
            print("=" * 70)
            
            # Step 1: Analyze module content
            print("📊 Analyzing module content...")
            module_analysis = self.analyze_module_content(module)
            
            # Step 2: Generate custom prompt template
            print("🧠 Generating custom prompt template...")
            custom_template = self.generate_custom_prompt_template(module_analysis)
            
            # Step 3: Generate theories for each topic
            print("📝 Generating theories...")
            module_results = []
            
            topics = module['topics']
            pages = module.get('pages', [])
            
            for i, topic in enumerate(topics):
                topic_pages = [pages[i]] if i < len(pages) else []
                
                if topic_pages:
                    theory_result = self.generate_theory_with_custom_prompt(
                        topic, topic_pages, custom_template
                    )
                    
                    if theory_result:
                        module_results.append({
                            'topic': topic,
                            'pages': topic_pages,
                            'theory': theory_result['theory'],
                            'verification': theory_result['verification']
                        })
                        print(f"   ✅ {topic}")
                    else:
                        print(f"   ❌ Failed: {topic}")
                else:
                    print(f"   ⚠️ No pages: {topic}")
            
            all_results.append({
                'module': module['title'],
                'analysis': module_analysis,
                'custom_template': custom_template,
                'theories': module_results
            })
            
            print(f"📊 Module Summary: {len(module_results)} theories generated")
        
        # Save results
        self.save_flexible_results(all_results)
    
    def save_flexible_results(self, all_results):
        """Save the flexible generation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save individual theory files
        for module_result in all_results:
            module_name = re.sub(r'[^\w\s-]', '', module_result['module'])[:30].replace(' ', '_')
            
            for theory_data in module_result['theories']:
                safe_topic = re.sub(r'[^\w\s-]', '', theory_data['topic'])[:50].replace(' ', '_')
                theory_file = os.path.join(self.output_dir, f"flexible_theory_{module_name}_{safe_topic}_{timestamp}.md")
                
                with open(theory_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {theory_data['topic']}\n\n")
                    f.write(f"**Module**: {module_result['module']}\n")
                    f.write(f"**Pages Used**: {theory_data['pages']}\n")
                    f.write(f"**Quality Score**: {theory_data['verification']['quality_score']}\n")
                    f.write(f"**Pitfall Callouts**: {theory_data['verification']['pitfall_callouts']}\n\n")
                    f.write("---\n\n")
                    f.write(theory_data['theory'])
        
        # Save comprehensive summary
        summary_file = os.path.join(self.output_dir, f"flexible_generation_summary_{timestamp}.json")
        
        summary_data = {
            'generation_date': timestamp,
            'generator_type': 'flexible_module_theory_generator',
            'total_modules': len(all_results),
            'total_theories': sum(len(mr['theories']) for mr in all_results),
            'modules': []
        }
        
        for module_result in all_results:
            summary_data['modules'].append({
                'module_title': module_result['module'],
                'analysis': module_result['analysis'],
                'theory_count': len(module_result['theories']),
                'average_quality': sum(t['verification']['quality_score'] for t in module_result['theories']) / max(len(module_result['theories']), 1),
                'custom_template_used': len(module_result['custom_template']) > 500
            })
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        # Display results
        total_theories = sum(len(mr['theories']) for mr in all_results)
        avg_quality = sum(sum(t['verification']['quality_score'] for t in mr['theories']) 
                         for mr in all_results) / max(total_theories, 1)
        
        print(f"\n✅ FLEXIBLE GENERATION COMPLETE!")
        print("=" * 60)
        print(f"📊 Total Theories Generated: {total_theories}")
        print(f"📈 Average Quality Score: {avg_quality:.1f}")
        print(f"📁 Summary saved to: {summary_file}")
        print(f"📝 Individual theory files saved to output/")
        
        print(f"\n📋 Module Breakdown:")
        for module_result in all_results:
            theories_count = len(module_result['theories'])
            subject = module_result['analysis']['primary_subject']
            print(f"   📚 {module_result['module']}")
            print(f"      🎯 Subject: {subject}")
            print(f"      📄 Theories: {theories_count}")
            print(f"      ✨ Custom Template: {'Yes' if len(module_result['custom_template']) > 500 else 'No'}")

def main():
    print("🚀 Flexible Module Theory Generator")
    print("=" * 50)
    print("Adapts to any subject: Statistics, Engineering, Physics, Mathematics, etc.")
    print("Features:")
    print("  • Dynamic prompt generation based on content analysis")
    print("  • Subject-specific theory structures")
    print("  • PDF content extraction and utilization")
    print("  • Quality verification and scoring")
    
    generator = FlexibleModuleTheoryGenerator()
    generator.select_and_generate_module_theories()

if __name__ == "__main__":
    main()
