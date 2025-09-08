#!/usr/bin/env python3
"""
Enhanced LLM-Powered Curriculum Generator
========================================

This script uses LLM to generate a well-structured, comprehensive curriculum
from extracted topics, ensuring proper organization, logical flow, and
educational best practices.

Features:
- LLM-driven curriculum organization
- Automatic module grouping and sequencing
- Duration estimation based on complexity
- Learning objective generation
- Prerequisite identification
- Quality validation and refinement
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import fitz  # PyMuPDF
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our LLM class
from LLM import AdvancedAzureLLM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedLLMCurriculumGenerator:
    """Enhanced curriculum generator using LLM for intelligent organization"""
    
    def __init__(self, pdf_path: str = "doc/book2.pdf"):
        """Initialize the enhanced curriculum generator"""
        self.pdf_path = pdf_path
        self.pdf_doc = None
        self.llm = AdvancedAzureLLM()
        
        # Ensure output directory exists
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Load extracted topics
        self.extracted_topics = self._load_extracted_topics()
        
        logger.info("Enhanced LLM Curriculum Generator initialized")
    
    def _load_extracted_topics(self) -> List[Dict]:
        """Load the extracted topics from the latest extraction file"""
        try:
            # Look for the latest topic extraction file (updated patterns)
            topic_files = list(self.output_dir.glob("*_topics_*.json")) + \
                         list(self.output_dir.glob("*_optimized_*.json")) + \
                         list(self.output_dir.glob("extracted_topics_*.json"))
            
            if not topic_files:
                raise FileNotFoundError("No extracted topics file found. Run topic extraction first.")
            
            # Get the most recent file
            latest_file = max(topic_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            logger.info(f"Loaded {len(data)} topics from {latest_file}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading extracted topics: {e}")
            return []
    
    def _open_pdf(self):
        """Open the PDF document"""
        if self.pdf_doc is None:
            try:
                self.pdf_doc = fitz.open(self.pdf_path)
                logger.info(f"Opened PDF: {self.pdf_path} ({len(self.pdf_doc)} pages)")
            except Exception as e:
                logger.error(f"Error opening PDF {self.pdf_path}: {e}")
                raise
    
    def _extract_page_content(self, page_num: int) -> str:
        """Extract text content from a specific page"""
        if self.pdf_doc is None:
            self._open_pdf()
        
        try:
            if 0 <= page_num < len(self.pdf_doc):
                page = self.pdf_doc[page_num]
                return page.get_text()
            return ""
        except Exception as e:
            logger.warning(f"Error extracting page {page_num}: {e}")
            return ""
    
    def _prepare_topics_for_llm(self) -> str:
        """Prepare topics data for LLM analysis"""
        topics_text = []
        
        for i, topic in enumerate(self.extracted_topics[:50], 1):  # Limit to first 50 for context
            page_info = f"Page {topic.get('page_number', 'N/A')}" if topic.get('page_number') else ""
            topics_text.append(f"{i}. {topic.get('title', 'Untitled')} ({page_info})")
        
        return "\n".join(topics_text)
    
    def generate_curriculum_structure(self) -> Dict[str, Any]:
        """Use LLM to generate a well-structured curriculum"""
        logger.info("🧠 Generating curriculum structure using LLM...")
        
        topics_text = self._prepare_topics_for_llm()
        
        curriculum_prompt = f"""
You are an expert educational curriculum designer specializing in statistics and probability. 

TASK: Create a comprehensive, well-structured learning curriculum for "Expectation and Variance in Statistics and Probability" using the provided topics.

AVAILABLE TOPICS:
{topics_text}

REQUIREMENTS:
1. **Logical Organization**: Group topics into modules that build upon each other
2. **Progressive Difficulty**: Arrange from foundational concepts to advanced applications
3. **Optimal Module Size**: 5-8 topics per module for manageable learning
4. **Clear Learning Path**: Each module should prepare students for the next
5. **Eliminate Redundancy**: Remove or consolidate duplicate/overlapping topics
6. **Educational Best Practices**: Follow proven curriculum design principles

OUTPUT STRUCTURE (JSON format):
{{
    "curriculum_title": "Comprehensive title for the learning path",
    "description": "Brief description of what students will learn",
    "target_audience": "Who this curriculum is designed for",
    "total_duration_hours": "Estimated total learning time",
    "modules": [
        {{
            "module_number": 1,
            "module_title": "Clear, descriptive module title",
            "module_description": "What students will learn in this module",
            "duration_hours": "Estimated time for this module",
            "learning_objectives": ["Specific, measurable learning objectives"],
            "topics": [
                {{
                    "topic_number": 1,
                    "topic_title": "Clean, specific topic title",
                    "page_reference": "Page number if available",
                    "complexity_level": "beginner/intermediate/advanced",
                    "estimated_time_minutes": "Time estimate for this topic"
                }}
            ],
            "prerequisites": ["What students need to know before this module"],
            "key_concepts": ["Main concepts covered in this module"]
        }}
    ],
    "learning_outcomes": ["Overall outcomes after completing the curriculum"],
    "assessment_suggestions": ["Ways to assess student understanding"]
}}

FOCUS ON:
- Statistics fundamentals (descriptive statistics, probability basics)
- Random variables and probability distributions
- Expectation: definition, properties, calculations
- Variance: definition, properties, relationships with expectation
- Covariance and correlation
- Applications in statistical inference
- Real-world applications and interpretations

Create a curriculum that would be suitable for undergraduate statistics students or professionals learning these concepts.
"""

        try:
            response = self.llm.get_response(curriculum_prompt)
            
            # Clean and parse the JSON response
            response_clean = self._clean_json_response(response)
            curriculum_data = json.loads(response_clean)
            
            logger.info(f"✅ Generated curriculum with {len(curriculum_data.get('modules', []))} modules")
            return curriculum_data
            
        except Exception as e:
            logger.error(f"Error generating curriculum structure: {e}")
            return self._create_fallback_curriculum()
    
    def _clean_json_response(self, response: str) -> str:
        """Clean the LLM response to extract valid JSON"""
        # Remove markdown code blocks if present
        if '```json' in response:
            start = response.find('```json') + 7
            end = response.rfind('```')
            response = response[start:end].strip()
        elif '```' in response:
            start = response.find('```') + 3
            end = response.rfind('```')
            response = response[start:end].strip()
        
        return response.strip()
    
    def _create_fallback_curriculum(self) -> Dict[str, Any]:
        """Create a fallback curriculum structure if LLM fails"""
        logger.warning("Using fallback curriculum structure")
        
        return {
            "curriculum_title": "Expectation and Variance in Statistics and Probability",
            "description": "A comprehensive learning path covering fundamental and advanced concepts of expectation and variance",
            "target_audience": "Undergraduate students and professionals",
            "total_duration_hours": 25,
            "modules": [
                {
                    "module_number": 1,
                    "module_title": "Foundations of Statistics",
                    "module_description": "Basic statistical concepts and data analysis",
                    "duration_hours": 3,
                    "learning_objectives": ["Understand descriptive statistics", "Learn data visualization"],
                    "topics": self.extracted_topics[:8],
                    "prerequisites": ["Basic mathematics"],
                    "key_concepts": ["Mean", "Median", "Variance", "Standard deviation"]
                }
            ],
            "learning_outcomes": ["Master expectation and variance concepts"],
            "assessment_suggestions": ["Quizzes", "Problem sets", "Projects"]
        }
    
    def enhance_with_page_analysis(self, curriculum: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance curriculum with detailed page content analysis"""
        logger.info("📚 Enhancing curriculum with page content analysis...")
        
        self._open_pdf()
        
        for module in curriculum.get('modules', []):
            for topic in module.get('topics', []):
                # Find matching topic in extracted data
                topic_title = topic.get('topic_title', '')
                
                # Find the corresponding extracted topic
                matching_topic = self._find_matching_topic(topic_title)
                if matching_topic and matching_topic.get('page_number'):
                    page_num = matching_topic['page_number']
                    
                    # Extract page content
                    page_content = self._extract_page_content(page_num - 1)  # Convert to 0-based
                    
                    # Analyze content complexity and add metadata
                    content_analysis = self._analyze_content_complexity(page_content)
                    topic.update({
                        'page_reference': page_num,
                        'content_length': len(page_content),
                        'has_mathematical_content': content_analysis['has_math'],
                        'complexity_indicators': content_analysis['indicators'],
                        'estimated_time_minutes': content_analysis['time_estimate']
                    })
        
        return curriculum
    
    def _find_matching_topic(self, topic_title: str) -> Dict:
        """Find matching topic in extracted data"""
        for topic in self.extracted_topics:
            if topic_title.lower() in topic.get('title', '').lower() or \
               topic.get('title', '').lower() in topic_title.lower():
                return topic
        return {}
    
    def _analyze_content_complexity(self, content: str) -> Dict[str, Any]:
        """Analyze page content to estimate complexity and time requirements"""
        # Simple heuristics for content analysis
        word_count = len(content.split())
        
        # Check for mathematical content
        math_indicators = ['formula', 'equation', 'theorem', 'proof', '∑', '∫', '∂', 'σ', 'μ']
        has_math = any(indicator in content.lower() for indicator in math_indicators)
        
        # Estimate reading time (average 200 words per minute, slower for math content)
        base_time = word_count / 200
        if has_math:
            base_time *= 1.5  # Math content takes longer
        
        # Convert to minutes and add buffer
        time_estimate = max(15, int(base_time * 60 + 10))
        
        return {
            'has_math': has_math,
            'indicators': {
                'word_count': word_count,
                'has_formulas': 'formula' in content.lower(),
                'has_examples': 'example' in content.lower(),
                'has_exercises': any(word in content.lower() for word in ['exercise', 'problem', 'solve'])
            },
            'time_estimate': time_estimate
        }
    
    def save_curriculum(self, curriculum: Dict[str, Any]) -> Tuple[str, str]:
        """Save the generated curriculum in multiple formats"""
        # JSON format
        json_filename = f"enhanced_curriculum_{self.timestamp}.json"
        json_path = self.output_dir / json_filename
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(curriculum, f, indent=2, ensure_ascii=False)
        
        # Human-readable format
        text_filename = f"enhanced_curriculum_{self.timestamp}.txt"
        text_path = self.output_dir / text_filename
        
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(self._format_curriculum_text(curriculum))
        
        logger.info(f"📄 Curriculum saved: {json_path}")
        logger.info(f"📄 Human-readable version: {text_path}")
        
        return str(json_path), str(text_path)
    
    def _format_curriculum_text(self, curriculum: Dict[str, Any]) -> str:
        """Format curriculum as human-readable text"""
        lines = []
        
        lines.append(f"🎯 {curriculum.get('curriculum_title', 'Learning Curriculum')}")
        lines.append("=" * 80)
        lines.append(f"📖 {curriculum.get('description', 'No description available')}")
        lines.append(f"👥 Target Audience: {curriculum.get('target_audience', 'General')}")
        lines.append(f"⏱ Total Duration: {curriculum.get('total_duration_hours', 'N/A')} hours")
        lines.append(f"📚 Modules: {len(curriculum.get('modules', []))}")
        lines.append("")
        
        # Modules
        for module in curriculum.get('modules', []):
            lines.append(f"📚 Module {module.get('module_number', 'N/A')}: {module.get('module_title', 'Untitled')}")
            lines.append(f"   ⏱ Duration: {module.get('duration_hours', 'N/A')} hours")
            lines.append(f"   📝 Description: {module.get('module_description', 'No description')}")
            lines.append(f"   📄 Topics ({len(module.get('topics', []))}):")
            
            for topic in module.get('topics', []):
                page_ref = f" (Page {topic.get('page_reference', 'N/A')})" if topic.get('page_reference') else ""
                time_est = f" [{topic.get('estimated_time_minutes', 'N/A')}min]" if topic.get('estimated_time_minutes') else ""
                lines.append(f"       {topic.get('topic_number', 'N/A')}. {topic.get('topic_title', 'Untitled')}{page_ref}{time_est}")
            
            if module.get('learning_objectives'):
                lines.append(f"   🎯 Learning Objectives:")
                for obj in module['learning_objectives']:
                    lines.append(f"       • {obj}")
            
            lines.append("")
        
        # Learning outcomes
        if curriculum.get('learning_outcomes'):
            lines.append("🏆 Overall Learning Outcomes:")
            for outcome in curriculum['learning_outcomes']:
                lines.append(f"   • {outcome}")
            lines.append("")
        
        # Assessment suggestions
        if curriculum.get('assessment_suggestions'):
            lines.append("📊 Assessment Suggestions:")
            for suggestion in curriculum['assessment_suggestions']:
                lines.append(f"   • {suggestion}")
        
        return "\n".join(lines)
    
    def validate_curriculum(self, curriculum: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and provide quality metrics for the curriculum"""
        validation_results = {
            'total_modules': len(curriculum.get('modules', [])),
            'total_topics': sum(len(module.get('topics', [])) for module in curriculum.get('modules', [])),
            'average_topics_per_module': 0,
            'modules_with_objectives': 0,
            'topics_with_page_refs': 0,
            'estimated_total_time': 0,
            'quality_score': 0
        }
        
        if validation_results['total_modules'] > 0:
            validation_results['average_topics_per_module'] = validation_results['total_topics'] / validation_results['total_modules']
        
        # Count modules with learning objectives
        for module in curriculum.get('modules', []):
            if module.get('learning_objectives'):
                validation_results['modules_with_objectives'] += 1
            
            # Count topics with page references and sum time estimates
            for topic in module.get('topics', []):
                if topic.get('page_reference'):
                    validation_results['topics_with_page_refs'] += 1
                if topic.get('estimated_time_minutes'):
                    validation_results['estimated_total_time'] += topic['estimated_time_minutes']
        
        # Calculate quality score (0-100)
        score_components = [
            min(validation_results['total_modules'] * 10, 50),  # Module count (up to 50 points)
            (validation_results['modules_with_objectives'] / max(validation_results['total_modules'], 1)) * 20,  # Objectives coverage
            (validation_results['topics_with_page_refs'] / max(validation_results['total_topics'], 1)) * 30,  # Page reference coverage
        ]
        validation_results['quality_score'] = sum(score_components)
        
        return validation_results
    
    def run_enhanced_generation(self) -> Tuple[Dict[str, Any], str, str]:
        """Run the complete enhanced curriculum generation process"""
        logger.info("🚀 Starting Enhanced LLM Curriculum Generation")
        logger.info("=" * 60)
        
        # Step 1: Generate curriculum structure using LLM
        curriculum = self.generate_curriculum_structure()
        
        # Step 2: Enhance with page analysis
        curriculum = self.enhance_with_page_analysis(curriculum)
        
        # Step 3: Validate curriculum quality
        validation = self.validate_curriculum(curriculum)
        
        # Step 4: Save results
        json_path, text_path = self.save_curriculum(curriculum)
        
        # Step 5: Print summary
        self._print_generation_summary(curriculum, validation)
        
        return curriculum, json_path, text_path
    
    def _print_generation_summary(self, curriculum: Dict[str, Any], validation: Dict[str, Any]):
        """Print generation summary"""
        print("\n" + "=" * 60)
        print("🎉 ENHANCED CURRICULUM GENERATION COMPLETED!")
        print("=" * 60)
        print(f"📚 Curriculum: {curriculum.get('curriculum_title', 'Untitled')}")
        print(f"📊 Modules: {validation['total_modules']}")
        print(f"📄 Topics: {validation['total_topics']}")
        print(f"⏱ Estimated Time: {validation['estimated_total_time']:.0f} minutes ({validation['estimated_total_time']/60:.1f} hours)")
        print(f"🎯 Quality Score: {validation['quality_score']:.1f}/100")
        print(f"📖 Page Coverage: {validation['topics_with_page_refs']}/{validation['total_topics']} topics")
        print("=" * 60)

def main():
    """Main execution function"""
    try:
        # Initialize the enhanced curriculum generator
        generator = EnhancedLLMCurriculumGenerator()
        
        # Run the enhanced generation process
        curriculum, json_path, text_path = generator.run_enhanced_generation()
        
        print(f"\n✅ Enhanced curriculum files generated:")
        print(f"   📋 JSON: {json_path}")
        print(f"   📄 Text: {text_path}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"❌ Generation failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
