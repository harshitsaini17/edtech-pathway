#!/usr/bin/env python3

"""
Enhanced Flexible Module Theory Generator with Multi-Phase Improvement
=====================================================================

Key Improvements:
1. Multi-phase generation: Initial → Verification → Enhancement
2. Previous theory loading for module consistency
3. Flexible content generation when PDF is incomplete
4. Iterative improvement loops for formulas and examples
5. Enhanced verification and quality assurance
6. Context-aware theory enhancement

Usage:
python enhanced_flexible_theory_generator.py
"""

import fitz
import json
import os
import re
import glob
from datetime import datetime
from typing import List, Dict, Any, Optional
from LLM import AdvancedAzureLLM
from topic_boundary_detector import TopicBoundaryDetector

class EnhancedFlexibleTheoryGenerator:
    """Enhanced theory generator with multi-phase improvement and consistency maintenance"""
    
    def __init__(self):
        self.pdf_path = "doc/book2.pdf"
        self.output_dir = "output"
        self.previous_theories_dir = os.path.join(self.output_dir, "previous_theories")
        self.llm = AdvancedAzureLLM()
        
        # Create directories
        os.makedirs(self.previous_theories_dir, exist_ok=True)
        
        # Initialize boundary detector
        print("🎯 Initializing Enhanced Theory Generation System...")
        self.boundary_detector = TopicBoundaryDetector(self.pdf_path)
        print("✅ Enhanced system ready")
        
        # Module context for consistency
        self.current_module_context = {}
        self.generated_theories = []

    def load_previous_theories(self, module_name: str) -> Dict[str, str]:
        """Load all previously generated theories for the current module"""
        previous_theories = {}
        
        # Create module-specific directory
        module_dir = os.path.join(self.previous_theories_dir, 
                                 re.sub(r'[^\w\s-]', '', module_name)[:30].replace(' ', '_'))
        
        if os.path.exists(module_dir):
            theory_files = glob.glob(os.path.join(module_dir, "*.md"))
            
            for file_path in theory_files:
                topic_name = os.path.basename(file_path).replace('.md', '')
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract just the theory content (after metadata)
                        if "---" in content:
                            theory_content = content.split("---", 2)[-1] if content.count("---") >= 2 else content
                        else:
                            theory_content = content
                        previous_theories[topic_name] = theory_content
                        print(f"📚 Loaded previous theory: {topic_name}")
                except Exception as e:
                    print(f"⚠️ Error loading {file_path}: {e}")
        
        return previous_theories

    def create_flexible_prompt_template(self, module_analysis: Dict, previous_theories: Dict) -> str:
        """Create a flexible prompt template that allows LLM freedom when PDF content is insufficient"""
        
        subject_area = module_analysis.get('primary_subject', 'general')
        has_previous = len(previous_theories) > 0
        
        consistency_section = ""
        if has_previous:
            consistency_section = f"""
CONSISTENCY REQUIREMENTS:
- Maintain consistency with previously generated theories in this module
- Use similar terminology, notation, and explanation style
- Reference connections to previous topics where relevant
- Previous theories count: {len(previous_theories)}

PREVIOUS THEORIES CONTEXT:
{self._create_previous_theories_summary(previous_theories)}
"""

        flexibility_section = """
CONTENT GENERATION FLEXIBILITY:
- PRIMARY: Use the provided PDF content as the foundation
- SECONDARY: If PDF content is incomplete or missing key elements, you may:
  * Generate additional explanations to complete the theory
  * Add missing mathematical derivations using standard methods
  * Include relevant examples that fit the topic context
  * Expand on concepts mentioned briefly in the PDF
- MAINTAIN: Consistency with PDF content and previous theories
- ENSURE: All generated content is academically accurate and relevant

BALANCE: ~70% PDF content, ~30% intelligent enhancement where needed
"""

        subject_specific_requirements = self._get_subject_specific_requirements(subject_area)

        template = f"""
You are creating comprehensive educational theory content for: "{{topic_title}}"

MODULE CONTEXT: {{module_title}} (Subject: {subject_area})

{consistency_section}

{flexibility_section}

{subject_specific_requirements}

PDF SOURCE CONTENT:
{{pdf_content}}

EXTRACTED ELEMENTS:
🔢 Formulas: {{formulas}}
💡 Examples: {{examples_count}} examples found
📖 Key Concepts: {{key_concepts}}
🧮 Definitions: {{definitions_count}}
🎯 Theorems: {{theorems_count}}

MANDATORY REQUIREMENTS:
1. **Use PDF examples and formulas** - reference them by exact numbers/notation
2. **Fill gaps intelligently** - add missing explanations or examples as needed
3. **Maintain consistency** - align with previous theories in terminology and style
4. **Include comprehensive pitfalls** using format:
   🚫 **Common Mistake**: [specific mistake]
   **Why it's wrong**: [detailed explanation]
   **Correct approach**: [proper method]

THEORY STRUCTURE (MANDATORY):
## 🎯 What You'll Learn
## 📖 Core Concepts  
## 🔢 Mathematical Framework
## 💡 Worked Examples
## 🚫 Common Pitfalls (minimum 3)
## 🏭 Real-World Applications
## 🧮 Key Formulas Summary

Generate a comprehensive theory that combines PDF content with intelligent enhancements.
"""
        
        return template

    def _create_previous_theories_summary(self, previous_theories: Dict) -> str:
        """Create a summary of previous theories for consistency"""
        if not previous_theories:
            return "No previous theories available."
        
        summary_parts = []
        for topic_name, content in list(previous_theories.items())[:3]:  # Limit to 3 most recent
            # Extract key concepts and terminology
            key_terms = re.findall(r'\*\*([^*]+)\*\*', content[:1000])
            formulas = re.findall(r'\$([^$]+)\$|\\\([^)]+\\\)|\\\[[^\]]+\\\]', content[:1000])
            
            summary_parts.append(f"""
- **{topic_name}**: 
  Key terms: {', '.join(key_terms[:5])}
  Formulas used: {len(formulas)} mathematical expressions
  Style: {'Formal mathematical' if len(formulas) > 3 else 'Conceptual focus'}
""")
        
        return '\n'.join(summary_parts)

    def _get_subject_specific_requirements(self, subject_area: str) -> str:
        """Get subject-specific requirements for theory generation"""
        
        requirements = {
            'mathematics': """
MATHEMATICAL FOCUS:
- Emphasize rigorous proofs and derivations
- Include step-by-step mathematical reasoning
- Show connections between concepts algebraically
- Provide geometric or analytical interpretations
- Include convergence, limits, and continuity where relevant
""",
            'statistics': """
STATISTICAL FOCUS:
- Emphasize probabilistic reasoning and interpretations
- Include both theoretical and practical perspectives
- Connect concepts to real-world data analysis scenarios
- Explain assumptions and their implications
- Include sampling considerations and inference logic
""",
            'engineering': """
ENGINEERING FOCUS:
- Emphasize practical applications and design considerations
- Include system-level thinking and trade-offs
- Connect theory to implementation challenges
- Provide design examples and case studies
- Include performance metrics and optimization aspects
""",
            'physics': """
PHYSICS FOCUS:
- Emphasize physical intuition and conceptual understanding
- Connect mathematical formalism to physical phenomena
- Include experimental perspectives and measurements
- Explain underlying physical principles
- Connect to observable natural phenomena
"""
        }
        
        return requirements.get(subject_area, """
GENERAL ACADEMIC FOCUS:
- Balance theoretical rigor with practical understanding
- Include both abstract concepts and concrete applications
- Explain the 'why' behind mathematical relationships
- Provide multiple perspectives on key concepts
- Connect to broader academic context
""")

    def enhanced_content_extraction(self, boundary_info: Dict) -> Dict:
        """Enhanced content extraction with better formula and example detection"""
        
        page_range = boundary_info['page_range']
        print(f"📚 Enhanced content extraction from pages {min(page_range)}-{max(page_range)}")
        
        try:
            doc = fitz.open(self.pdf_path)
            
            content_data = {
                'topic_title': boundary_info.get('topic_title', ''),
                'boundary_info': boundary_info,
                'pages_analyzed': page_range,
                'combined_text': '',
                'formulas': [],
                'examples': [],
                'definitions': [],
                'theorems': [],
                'key_terms': [],
                'statistics': {}
            }
            
            all_text_parts = []
            
            for page_num in page_range:
                if page_num <= len(doc):
                    page = doc[page_num - 1]
                    text = page.get_text()
                    
                    # Enhanced formula extraction
                    formulas = self._extract_enhanced_formulas(text)
                    
                    # Enhanced example extraction
                    examples = self._extract_enhanced_examples(text)
                    
                    # Extract definitions and theorems
                    definitions = re.findall(r'(DEFINITION\s+\d+\.\d+[^D]*?(?=DEFINITION|\n\n\n|$))', text, re.DOTALL | re.IGNORECASE)
                    theorems = re.findall(r'(THEOREM\s+\d+\.\d+[^T]*?(?=THEOREM|\n\n\n|$))', text, re.DOTALL | re.IGNORECASE)
                    
                    # Store page content
                    all_text_parts.append(text)
                    content_data['formulas'].extend(formulas)
                    content_data['examples'].extend(examples)
                    content_data['definitions'].extend(definitions)
                    content_data['theorems'].extend(theorems)
                    content_data['key_terms'].extend(self.extract_key_terms(text))
            
            doc.close()
            
            # Combine and deduplicate
            content_data['combined_text'] = '\n'.join(all_text_parts)
            content_data['formulas'] = list(set(content_data['formulas']))
            content_data['key_terms'] = list(set(content_data['key_terms']))
            
            # Calculate statistics
            total_words = len(content_data['combined_text'].split())
            content_data['statistics'] = {
                'total_words': total_words,
                'formula_count': len(content_data['formulas']),
                'example_count': len(content_data['examples']),
                'definition_count': len(content_data['definitions']),
                'theorem_count': len(content_data['theorems']),
                'avg_words_per_page': total_words / len(page_range) if page_range else 0
            }
            
            print(f"✅ Enhanced extraction complete:")
            print(f"   📊 {total_words} words, {len(content_data['formulas'])} formulas")
            print(f"   💡 {len(content_data['examples'])} examples, {len(content_data['definitions'])} definitions")
            
            return content_data
            
        except Exception as e:
            print(f"❌ Error in enhanced content extraction: {e}")
            return None

    def _extract_enhanced_formulas(self, text: str) -> List[str]:
        """Enhanced formula extraction with better pattern recognition"""
        
        patterns = [
            r'(?:E\[.*?\]|Var\(.*?\)|P\{.*?\})',  # Probability/statistics
            r'f\s*\([^)]*\)\s*=\s*[^,\n]+',      # Functions
            r'[σμλαβγδεζηθικλμνξοπρστυφχψω]\s*=\s*[^,\n]+',  # Greek letters
            r'\b\w+\s*=\s*\d+[^,\n]*',           # Simple equations
            r'∫.*?d[xyz]',                       # Integrals
            r'∑.*?=.*?(?=\s|$)',                 # Summations
            r'\$\$.*?\$\$',                      # LaTeX display math
            r'\$.*?\$',                          # LaTeX inline math
            r'\\begin\{equation\}.*?\\end\{equation\}',  # LaTeX equations
            r'\\begin\{align\}.*?\\end\{align\}',        # LaTeX align
            r'\\\[.*?\\\]',                      # LaTeX brackets
            r'\\\(.*?\\\)',                      # LaTeX parentheses
        ]
        
        formulas = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            formulas.extend([match.strip() for match in matches if len(match.strip()) > 2])
        
        # Clean and deduplicate
        cleaned_formulas = []
        for formula in formulas:
            # Remove excessive whitespace
            clean_formula = re.sub(r'\s+', ' ', formula).strip()
            if len(clean_formula) > 2 and clean_formula not in cleaned_formulas:
                cleaned_formulas.append(clean_formula)
        
        return cleaned_formulas[:20]  # Limit to prevent overflow

    def _extract_enhanced_examples(self, text: str) -> List[str]:
        """Enhanced example extraction with better context capture"""
        
        patterns = [
            r'(EXAMPLE\s+\d+\.\d+[a-z]?.*?(?=EXAMPLE|\n\n\n|$))',
            r'(Example\s+\d+\.\d+[a-z]?.*?(?=Example|\n\n\n|$))',
            r'(SOLUTION.*?(?=EXAMPLE|SOLUTION|\n\n\n|$))',
            r'(Solution.*?(?=Example|Solution|\n\n\n|$))',
        ]
        
        examples = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            examples.extend([match.strip() for match in matches if len(match.strip()) > 100])
        
        return examples[:10]  # Limit to prevent overflow

    def extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms with enhanced domain detection"""
        
        # Enhanced patterns for different domains
        patterns = {
            'general': [
                r'\b(?:theorem|definition|proof|lemma|corollary|proposition)\b',
                r'\b(?:analysis|method|algorithm|procedure|approach|technique)\b',
                r'\b(?:example|solution|result|conclusion|application)\b'
            ],
            'mathematics': [
                r'\b(?:function|equation|derivative|integral|limit|series|matrix|vector)\b',
                r'\b(?:continuous|differentiable|convergent|bounded|linear|nonlinear)\b',
                r'\b(?:domain|range|inverse|composition|transformation)\b'
            ],
            'statistics': [
                r'\b(?:probability|distribution|variance|expectation|sample|population)\b',
                r'\b(?:random|variable|hypothesis|inference|estimation|regression)\b',
                r'\b(?:normal|binomial|poisson|chi-square|t-test|confidence)\b'
            ],
            'engineering': [
                r'\b(?:system|signal|control|frequency|response|design|optimization)\b',
                r'\b(?:feedback|stability|transfer|function|filter|amplifier)\b',
                r'\b(?:linear|nonlinear|dynamic|static|steady|transient)\b'
            ]
        }
        
        key_terms = []
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, text, re.IGNORECASE)
                key_terms.extend([match.lower() for match in matches])
        
        # Return unique terms, prioritizing by frequency
        term_counts = {}
        for term in key_terms:
            term_counts[term] = term_counts.get(term, 0) + 1
        
        # Sort by frequency and return top terms
        sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
        return [term for term, count in sorted_terms[:15]]

    def multi_phase_theory_generation(self, topic_title: str, module_name: str, 
                                    start_page: Optional[int] = None) -> Dict:
        """
        Multi-phase theory generation with iterative improvement
        
        Phases:
        1. Content extraction and boundary detection
        2. Initial theory generation with flexibility
        3. Theory verification and assessment  
        4. Mathematical enhancement (formulas/examples)
        5. Final quality assurance and polish
        """
        
        print(f"\n🚀 MULTI-PHASE THEORY GENERATION")
        print(f"📚 Topic: {topic_title}")
        print(f"📖 Module: {module_name}")
        print("-" * 70)
        
        # Phase 1: Content Extraction
        print("📄 Phase 1: Content Extraction & Boundary Detection")
        boundary_info = self.detect_topic_boundaries(topic_title, start_page)
        if not boundary_info:
            print("❌ Failed to detect topic boundaries")
            return None
        
        content_data = self.enhanced_content_extraction(boundary_info)
        if not content_data:
            print("❌ Failed to extract content")
            return None
        
        # Phase 2: Initial Theory Generation
        print("🧠 Phase 2: Initial Theory Generation")
        previous_theories = self.load_previous_theories(module_name)
        
        # Analyze current module
        module_analysis = {'primary_subject': self._detect_subject_area(content_data)}
        
        # Create flexible prompt
        prompt_template = self.create_flexible_prompt_template(module_analysis, previous_theories)
        
        initial_prompt = prompt_template.format(
            topic_title=topic_title,
            module_title=module_name,
            pdf_content=content_data['combined_text'][:10000],
            formulas='\n'.join(content_data['formulas'][:10]),
            examples_count=content_data['statistics']['example_count'],
            key_concepts=', '.join(content_data['key_terms'][:10]),
            definitions_count=content_data['statistics']['definition_count'],
            theorems_count=content_data['statistics']['theorem_count']
        )
        
        initial_theory = self.llm.generate_response(initial_prompt)
        print(f"✅ Initial theory generated: {len(initial_theory)} characters")
        
        # Phase 3: Verification & Assessment
        print("🔍 Phase 3: Theory Verification & Assessment")
        verification_metrics = self._comprehensive_verification(initial_theory, content_data)
        
        print(f"   📊 Verification scores:")
        print(f"      🚫 Pitfalls: {verification_metrics['pitfall_count']}")
        print(f"      🔢 Formulas: {verification_metrics['formula_usage']}")
        print(f"      💡 Examples: {verification_metrics['example_references']}")
        print(f"      📈 Overall: {verification_metrics['overall_score']:.1f}")
        
        # Phase 4: Mathematical Enhancement
        print("🔢 Phase 4: Mathematical Enhancement")
        enhanced_theory = self._enhance_mathematical_content(
            initial_theory, content_data, verification_metrics
        )
        
        # Phase 5: Final Quality Assurance
        print("✨ Phase 5: Final Quality Assurance")
        final_theory = self._final_quality_polish(enhanced_theory, content_data, previous_theories)
        
        # Final verification
        final_verification = self._comprehensive_verification(final_theory, content_data)
        
        print(f"✅ Multi-phase generation complete!")
        print(f"   📈 Quality improvement: {final_verification['overall_score'] - verification_metrics['overall_score']:.1f}")
        
        return {
            'theory': final_theory,
            'boundary_info': boundary_info,
            'content_stats': content_data['statistics'],
            'initial_verification': verification_metrics,
            'final_verification': final_verification,
            'improvement_score': final_verification['overall_score'] - verification_metrics['overall_score'],
            'phases_completed': 5,
            'pages_used': boundary_info['page_range']
        }

    def _detect_subject_area(self, content_data: Dict) -> str:
        """Detect the primary subject area from content"""
        
        subject_keywords = {
            'statistics': ['probability', 'distribution', 'variance', 'sample', 'hypothesis', 'random'],
            'mathematics': ['function', 'equation', 'theorem', 'proof', 'derivative', 'integral'],
            'engineering': ['system', 'signal', 'control', 'design', 'frequency', 'response'],
            'physics': ['energy', 'force', 'wave', 'particle', 'field', 'momentum']
        }
        
        text_lower = content_data['combined_text'].lower()
        scores = {}
        
        for subject, keywords in subject_keywords.items():
            score = sum(text_lower.count(keyword) for keyword in keywords)
            scores[subject] = score
        
        return max(scores, key=scores.get) if scores else 'general'

    def _comprehensive_verification(self, theory_text: str, content_data: Dict) -> Dict:
        """Comprehensive theory verification with detailed metrics"""
        
        # Count pitfall callouts
        pitfall_count = theory_text.count('🚫')
        
        # Verify formula usage
        formula_usage = 0
        total_formulas = len(content_data['formulas'])
        for formula in content_data['formulas'][:10]:
            # Check if core part of formula appears in theory
            formula_core = re.sub(r'[^\w=+\-*/()αβγδεζηθικλμνξοπρστυφχψω]', '', formula)
            if len(formula_core) > 3 and formula_core in theory_text:
                formula_usage += 1
        
        # Check example references  
        example_references = 0
        for example in content_data['examples'][:5]:
            example_nums = re.findall(r'(?:EXAMPLE|Example)\s+(\d+\.\d+)', example, re.IGNORECASE)
            if example_nums:
                example_ref = f"Example {example_nums[0]}"
                if example_ref.lower() in theory_text.lower():
                    example_references += 1
        
        # Content coverage analysis
        theory_words = len(theory_text.split())
        expected_words = max(1500, content_data['statistics']['total_words'] // 5)
        coverage_ratio = min(100, (theory_words / expected_words) * 100)
        
        # Structure verification
        required_sections = ['🎯 What You\'ll Learn', '📖 Core Concepts', '🔢 Mathematical Framework',
                           '💡 Worked Examples', '🚫 Common Pitfalls', '🏭 Real-World Applications',
                           '🧮 Key Formulas Summary']
        section_count = sum(1 for section in required_sections if section in theory_text)
        structure_score = (section_count / len(required_sections)) * 100
        
        # Calculate overall score
        overall_score = (
            pitfall_count * 15 +           # Pitfall quality (weight: 15)
            formula_usage * 20 +           # Formula integration (weight: 20) 
            example_references * 25 +      # Example usage (weight: 25)
            coverage_ratio * 0.3 +         # Content coverage (weight: 0.3)
            structure_score * 0.4          # Structure completeness (weight: 0.4)
        )
        
        return {
            'pitfall_count': pitfall_count,
            'formula_usage': formula_usage,
            'formula_total': total_formulas,
            'example_references': example_references,
            'example_total': len(content_data['examples']),
            'coverage_ratio': coverage_ratio,
            'structure_score': structure_score,
            'theory_word_count': theory_words,
            'overall_score': overall_score
        }

    def _enhance_mathematical_content(self, theory: str, content_data: Dict, 
                                    verification_metrics: Dict) -> str:
        """Enhance mathematical content (formulas and examples) through targeted LLM refinement"""
        
        # Check if mathematical enhancement is needed
        formula_coverage = verification_metrics['formula_usage'] / max(verification_metrics['formula_total'], 1)
        example_coverage = verification_metrics['example_references'] / max(verification_metrics['example_total'], 1)
        
        needs_formula_enhancement = formula_coverage < 0.5
        needs_example_enhancement = example_coverage < 0.3
        
        if not (needs_formula_enhancement or needs_example_enhancement):
            print("   ✅ Mathematical content adequate, skipping enhancement")
            return theory
        
        enhancement_prompt = f"""
You are enhancing the mathematical content of an educational theory. 

CURRENT THEORY:
{theory}

ENHANCEMENT REQUIREMENTS:
"""
        
        if needs_formula_enhancement:
            available_formulas = '\n'.join(content_data['formulas'][:15])
            enhancement_prompt += f"""
🔢 FORMULA ENHANCEMENT NEEDED:
- Current formula usage: {verification_metrics['formula_usage']}/{verification_metrics['formula_total']}
- Available formulas from PDF:
{available_formulas}

Tasks:
1. Integrate more formulas from the available list into appropriate sections
2. Provide explanations for each formula's meaning and application
3. Show step-by-step derivations where appropriate
4. Connect formulas to worked examples
"""
        
        if needs_example_enhancement:
            available_examples = '\n'.join(content_data['examples'][:5])
            enhancement_prompt += f"""
💡 EXAMPLE ENHANCEMENT NEEDED:
- Current example usage: {verification_metrics['example_references']}/{verification_metrics['example_total']}
- Available examples from PDF:
{available_examples}

Tasks:
1. Reference specific examples by number (e.g., "Example 3.2a")
2. Provide step-by-step solutions for examples
3. Explain the reasoning behind each step
4. Connect examples to theoretical concepts
"""
        
        enhancement_prompt += """

INSTRUCTIONS:
1. Keep all existing content and structure
2. Enhance the Mathematical Framework and Worked Examples sections primarily
3. Maintain consistency with existing writing style
4. Add formulas/examples in appropriate locations, not as separate sections
5. Ensure all enhancements are mathematically accurate
6. Return the complete enhanced theory with improvements seamlessly integrated

Generate the enhanced theory now:
"""
        
        try:
            enhanced_theory = self.llm.generate_response(enhancement_prompt)
            print(f"   ✅ Mathematical content enhanced")
            return enhanced_theory
        except Exception as e:
            print(f"   ⚠️ Enhancement failed: {e}, using original theory")
            return theory

    def _final_quality_polish(self, theory: str, content_data: Dict, 
                            previous_theories: Dict) -> str:
        """Final quality polish focusing on consistency and completeness"""
        
        polish_prompt = f"""
You are performing final quality assurance on an educational theory. 

CURRENT THEORY:
{theory}

QUALITY ASSURANCE TASKS:

1. CONSISTENCY CHECK:
   - Ensure terminology is consistent throughout
   - Verify notation consistency in formulas
   - Check that examples connect properly to concepts

2. COMPLETENESS CHECK:
   - Ensure all required sections are present and substantial
   - Verify minimum 3 pitfall callouts with proper format
   - Confirm real-world applications are relevant and specific

3. STYLE POLISH:
   - Improve clarity and flow between sections
   - Ensure appropriate academic tone
   - Fix any grammatical or formatting issues

4. INTEGRATION CHECK:
   - Ensure PDF content and generated content blend seamlessly
   - Verify all mathematical notation is properly formatted
   - Confirm examples are explained step-by-step

CONSTRAINTS:
- Keep the same overall structure and length
- Maintain all technical accuracy
- Preserve all mathematical content
- Do not remove any substantial content

Return the polished theory:
"""
        
        try:
            polished_theory = self.llm.generate_response(polish_prompt)
            print(f"   ✅ Final quality polish complete")
            return polished_theory
        except Exception as e:
            print(f"   ⚠️ Final polish failed: {e}, using current theory")
            return theory

    def detect_topic_boundaries(self, topic_title: str, start_page: Optional[int] = None):
        """Detect topic boundaries using the existing boundary detector"""
        
        print(f"🔍 Detecting boundaries for: '{topic_title}'")
        
        if start_page:
            try:
                boundaries = self.boundary_detector.run_full_detection(
                    start_page=start_page,
                    end_page=start_page + 30
                )
                
                if boundaries:
                    topic_end = min(boundaries[0].end_page, start_page + 30)
                    return {
                        'topic_title': topic_title,
                        'start_page': start_page,
                        'end_page': topic_end,
                        'page_range': list(range(start_page, topic_end + 1)),
                        'confidence': boundaries[0].confidence,
                        'sections': boundaries
                    }
            except Exception as e:
                print(f"⚠️ Boundary detection error: {e}")
        
        # Fallback: search for topic in PDF
        try:
            doc = fitz.open(self.pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text().lower()
                if topic_title.lower() in text:
                    found_page = page_num + 1
                    doc.close()
                    return {
                        'topic_title': topic_title,
                        'start_page': found_page,
                        'end_page': min(found_page + 15, len(doc)),
                        'page_range': list(range(found_page, min(found_page + 16, len(doc) + 1))),
                        'confidence': 0.7,
                        'sections': []
                    }
            doc.close()
        except Exception as e:
            print(f"❌ Error searching for topic: {e}")
        
        # Final fallback
        return {
            'topic_title': topic_title,
            'start_page': 1,
            'end_page': 15,
            'page_range': list(range(1, 16)),
            'confidence': 0.3,
            'sections': []
        }

    def save_enhanced_theory(self, topic_title: str, module_name: str, theory_result: Dict):
        """Save enhanced theory with comprehensive metadata"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create module directory
        module_dir = os.path.join(self.previous_theories_dir, 
                                 re.sub(r'[^\w\s-]', '', module_name)[:30].replace(' ', '_'))
        os.makedirs(module_dir, exist_ok=True)
        
        # Save theory file
        safe_topic = re.sub(r'[^\w\s-]', '', topic_title)[:50].replace(' ', '_')
        theory_file = os.path.join(module_dir, f"{safe_topic}_{timestamp}.md")
        
        with open(theory_file, 'w', encoding='utf-8') as f:
            f.write(f"# {topic_title}\n\n")
            f.write(f"**Module**: {module_name}\n")
            f.write(f"**Generation Type**: Multi-Phase Enhanced\n")
            f.write(f"**Pages Used**: {min(theory_result['pages_used'])}-{max(theory_result['pages_used'])}\n")
            f.write(f"**Content Stats**: {theory_result['content_stats']['total_words']} words, {theory_result['content_stats']['formula_count']} formulas\n")
            f.write(f"**Quality Score**: {theory_result['final_verification']['overall_score']:.1f}\n")
            f.write(f"**Improvement**: +{theory_result['improvement_score']:.1f}\n")
            f.write(f"**Phases Completed**: {theory_result['phases_completed']}\n\n")
            f.write("---\n\n")
            f.write(theory_result['theory'])
        
        print(f"💾 Enhanced theory saved: {theory_file}")
        return theory_file

    def generate_module_theories_enhanced(self):
        """Main method for enhanced theory generation"""
        
        # Load curriculum modules
        modules = self.load_curriculum_modules()
        if not modules:
            print("❌ No curriculum modules found")
            return
        
        print(f"\n📚 ENHANCED THEORY GENERATOR")
        print("=" * 70)
        print("Features:")
        print(" 🚀 Multi-phase generation (5 phases)")
        print(" 🧠 Flexible content generation")
        print(" 📚 Previous theory consistency")
        print(" 🔢 Mathematical content enhancement") 
        print(" ✨ Iterative quality improvement")
        print(" 🎯 Comprehensive verification")
        print()
        
        # Display modules
        for i, module in enumerate(modules, 1):
            print(f"{i:2d}. {module['title']} ({len(module['topics'])} topics)")
        
        # User selection
        try:
            choice = input("\n🔢 Select module number (or 'all'): ").strip()
            if choice.lower() == 'all':
                selected_modules = modules
            else:
                module_idx = int(choice) - 1
                if 0 <= module_idx < len(modules):
                    selected_modules = [modules[module_idx]]
                else:
                    print("❌ Invalid selection")
                    return
        except ValueError:
            print("❌ Invalid input")
            return
        
        # Generate theories
        total_generated = 0
        total_improvement = 0
        
        for module in selected_modules:
            print(f"\n🎯 Processing Module: {module['title']}")
            print("=" * 50)
            
            module_name = module['title']
            topics = module['topics']
            pages = module.get('pages', [])
            
            for i, topic in enumerate(topics):
                start_page = pages[i] if i < len(pages) else None
                
                print(f"\n📝 Topic {i+1}/{len(topics)}: {topic}")
                
                theory_result = self.multi_phase_theory_generation(
                    topic_title=topic,
                    module_name=module_name,
                    start_page=start_page
                )
                
                if theory_result:
                    self.save_enhanced_theory(topic, module_name, theory_result)
                    total_generated += 1
                    total_improvement += theory_result['improvement_score']
                    
                    print(f"   ✅ Success! Quality: {theory_result['final_verification']['overall_score']:.1f}")
                    print(f"      Improvement: +{theory_result['improvement_score']:.1f}")
                else:
                    print(f"   ❌ Failed to generate theory for: {topic}")
        
        # Summary
        print(f"\n🎉 ENHANCED GENERATION COMPLETE!")
        print("=" * 50)
        print(f"📊 Total Theories Generated: {total_generated}")
        print(f"📈 Average Quality Improvement: {total_improvement/max(total_generated, 1):.1f}")
        print(f"🚀 Enhancement Features Used: All 5 phases")
        print(f"💾 Theories saved to: {self.previous_theories_dir}")

    def load_curriculum_modules(self):
        """Load curriculum modules from JSON files"""
        curriculum_files = [f for f in os.listdir(self.output_dir) 
                           if 'curriculum' in f and f.endswith('.json')]
        
        if not curriculum_files:
            return []
        
        latest_curriculum = sorted(curriculum_files, reverse=True)[0]
        
        with open(os.path.join(self.output_dir, latest_curriculum), 'r') as f:
            curriculum = json.load(f)
        
        print(f"📚 Loaded curriculum: {curriculum['title']}")
        return curriculum['modules']

def main():
    print("🚀 Enhanced Flexible Theory Generator")
    print("=" * 60)
    print("Multi-Phase Theory Generation with:")
    print(" 🧠 Intelligent content enhancement")
    print(" 📚 Previous theory consistency") 
    print(" 🔢 Mathematical content verification")
    print(" ✨ Iterative quality improvement")
    print(" 🎯 Comprehensive boundary detection")
    print()
    
    generator = EnhancedFlexibleTheoryGenerator()
    generator.generate_module_theories_enhanced()

if __name__ == "__main__":
    main()
