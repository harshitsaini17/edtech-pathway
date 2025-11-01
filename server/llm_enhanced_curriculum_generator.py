#!/usr/bin/env python3

"""
Enhanced LLM Curriculum Generator with Focused Topic Selection
=============================================================

Fixes for identified issues:
1. Better topic relevance filtering (was 4/10, target 9/10)
2. Essential content inclusion verification  
3. Appropriate content depth allocation
4. Textbook section alignment
5. Learning objective precision

Usage:
python llm_enhanced_curriculum_generator.py
"""

import json
import os
import re
import sys
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple
from LLM import AdvancedAzureLLM

# Add utils to path
import sys
import os
# Add parent directory to path for utils imports
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)

try:
    from utils.topic_beautifier import TopicTitleBeautifier, beautify_curriculum_topics
except ImportError:
    print("⚠️ Warning: Could not import TopicTitleBeautifier")
    TopicTitleBeautifier = None
    beautify_curriculum_topics = lambda x: x  # Fallback no-op function

class EnhancedLLMCurriculumGenerator:
    def __init__(self):
        self.llm = None
        try:
            self.llm = AdvancedAzureLLM()
            print("✅ LLM initialized successfully")
        except Exception as e:
            print(f"⚠️ LLM not available, using fallback methods: {e}")
            
        self.topics = []
        self.textbook_structure = {}
        
        # Initialize topic beautifier
        if TopicTitleBeautifier:
            try:
                self.beautifier = TopicTitleBeautifier()
                print("✅ Topic beautifier initialized")
            except Exception as e:
                print(f"⚠️ Topic beautifier not available: {e}")
                self.beautifier = None
        else:
            self.beautifier = None
        
        # Enhanced learning domain mapping with specificity scores
        self.learning_domains = {
            'bernoulli_binomial': {
                'keywords': ['bernoulli', 'binomial', 'trial', 'success', 'failure', 'probability mass', 'pmf'],
                'essential_topics': ['binomial probability', 'bernoulli trial', 'probability mass function'],
                'specificity_weight': 10
            },
            'probability_distributions': {
                'keywords': ['distribution', 'random variable', 'probability', 'discrete', 'continuous'],
                'essential_topics': ['probability distribution', 'random variables'],
                'specificity_weight': 8
            },
            'expectation_variance': {
                'keywords': ['expectation', 'expected value', 'variance', 'covariance', 'moment'],
                'essential_topics': ['expectation', 'variance', 'properties of expectation'],
                'specificity_weight': 9
            },
            'statistics_foundations': {
                'keywords': ['statistics', 'sample', 'population', 'inference', 'hypothesis'],
                'essential_topics': ['statistical inference', 'sampling'],
                'specificity_weight': 6
            },
            'general_probability': {
                'keywords': ['probability', 'event', 'sample space', 'axiom'],
                'essential_topics': ['probability axioms', 'sample space'],
                'specificity_weight': 5
            }
        }

    def load_latest_topics(self) -> bool:
        """Load the most recent topic extraction results with enhanced validation"""
        output_dir = "output"
        if not os.path.exists(output_dir):
            print(f"❌ Output directory not found: {output_dir}")
            return False

        # Find the most recent topics file
        json_files = [f for f in os.listdir(output_dir) 
                     if f.startswith('topics_') and f.endswith('.json')]
        
        if not json_files:
            print("❌ No topic files found in output directory")
            return False

        latest_file = sorted(json_files, reverse=True)[0]
        filepath = os.path.join(output_dir, latest_file)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.topics = data.get('topics', [])
            print(f"📚 Loaded {len(self.topics)} topics from {latest_file}")
            
            # Build textbook structure mapping
            self._build_textbook_structure()
            return True
            
        except Exception as e:
            print(f"❌ Error loading topics: {e}")
            return False

    def _build_textbook_structure(self):
        """Build textbook chapter/section structure for better organization"""
        self.textbook_structure = {}
        
        for topic in self.topics:
            title = topic.get('title', topic.get('topic', ''))
            page = topic.get('page', 0)
            
            # Extract chapter/section information
            chapter_match = re.match(r'(?:Chapter\s+)?(\d+)(?:\.(\d+))?', title, re.IGNORECASE)
            if chapter_match:
                chapter = int(chapter_match.group(1))
                section = int(chapter_match.group(2)) if chapter_match.group(2) else 0
                
                if chapter not in self.textbook_structure:
                    self.textbook_structure[chapter] = {}
                if section not in self.textbook_structure[chapter]:
                    self.textbook_structure[chapter][section] = []
                    
                self.textbook_structure[chapter][section].append(topic)

    def enhanced_query_analysis(self, learning_query: str) -> Dict:
        """Enhanced query analysis with LLM and domain expertise"""
        
        if not self.llm:
            return self._fallback_query_analysis(learning_query)

        analysis_prompt = f"""
Analyze this learning query for curriculum creation: "{learning_query}"

Provide detailed analysis in this JSON format:
{{
    "refined_title": "Clear, specific curriculum title",
    "primary_domain": "Main subject area (e.g., bernoulli_binomial, probability_distributions)",
    "secondary_domains": ["Related areas"],
    "target_audience": "Specific learner type",
    "difficulty_level": "Beginner/Intermediate/Advanced", 
    "estimated_duration": "Hours needed",
    "key_concepts_required": ["Essential concepts that MUST be included"],
    "optional_concepts": ["Good to have concepts"],
    "prerequisite_concepts": ["Required background"],
    "learning_outcomes": ["Specific, measurable outcomes"],
    "specificity_score": 8.5,
    "focus_areas": {{
        "theory_weight": 0.6,
        "applications_weight": 0.4,
        "computational_weight": 0.3
    }}
}}

CRITICAL: For topics like "Bernoulli and Binomial", focus ONLY on those specific distributions, not general statistics.
"""

        try:
            response = self.llm.generate_response(analysis_prompt)
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                print(f"🎯 Enhanced query analysis complete")
                return analysis
        except Exception as e:
            print(f"⚠️ LLM analysis failed, using fallback: {e}")
            
        return self._fallback_query_analysis(learning_query)

    def _fallback_query_analysis(self, learning_query: str) -> Dict:
        """Improved fallback analysis with domain expertise"""
        query_lower = learning_query.lower()
        
        # Determine primary domain with specificity scoring
        domain_scores = {}
        for domain, info in self.learning_domains.items():
            score = 0
            for keyword in info['keywords']:
                if keyword in query_lower:
                    score += info['specificity_weight']
            domain_scores[domain] = score
        
        primary_domain = max(domain_scores, key=domain_scores.get) if domain_scores else 'general_probability'
        
        # Enhanced analysis based on domain
        if 'bernoulli' in query_lower or 'binomial' in query_lower:
            return {
                "refined_title": "Understanding Bernoulli and Binomial Distributions",
                "primary_domain": "bernoulli_binomial",
                "secondary_domains": ["probability_distributions", "expectation_variance"],
                "target_audience": "Undergraduate students in statistics/mathematics",
                "difficulty_level": "Beginner to Intermediate",
                "estimated_duration": "4-6 hours",
                "key_concepts_required": [
                    "Bernoulli trials", "Binomial probability mass function", 
                    "Parameter estimation", "Normal approximation"
                ],
                "specificity_score": 9.0,
                "focus_areas": {
                    "theory_weight": 0.7,
                    "applications_weight": 0.6,
                    "computational_weight": 0.5
                }
            }
        
        return {
            "refined_title": learning_query.title(),
            "primary_domain": primary_domain,
            "target_audience": "Undergraduate students",
            "difficulty_level": "Intermediate",
            "specificity_score": 6.0
        }

    def enhanced_topic_filtering(self, query_analysis: Dict) -> List[Dict]:
        """Enhanced topic filtering with relevance scoring"""
        
        if not self.llm:
            return self._fallback_topic_filtering(query_analysis)

        # Process topics in chunks for LLM analysis
        chunk_size = 30
        all_relevant_topics = []
        
        primary_domain = query_analysis.get('primary_domain', 'general')
        key_concepts = query_analysis.get('key_concepts_required', [])
        
        print(f"🔍 Filtering topics for domain: {primary_domain}")
        
        for i in range(0, len(self.topics), chunk_size):
            chunk = self.topics[i:i + chunk_size]
            
            # Create detailed topics summary for LLM
            topics_summary = []
            for topic in chunk:
                title = topic.get('title', topic.get('topic', ''))
                page = topic.get('page', 'N/A')
                topics_summary.append(f"- {title} (Page {page})")
            
            filtering_prompt = f"""
Filter these topics for relevance to: "{query_analysis.get('refined_title', '')}"

PRIMARY DOMAIN: {primary_domain}
REQUIRED CONCEPTS: {', '.join(key_concepts)}

TOPICS TO EVALUATE:
{chr(10).join(topics_summary)}

For each topic, provide relevance score (0-10) and reasoning:
- 9-10: Essential/Core content directly related to learning goal
- 7-8: Important supporting content  
- 5-6: Useful background/context
- 3-4: Tangentially related
- 0-2: Not relevant

Return as JSON array:
[
    {{"topic": "Topic Name", "page": 123, "relevance_score": 8, "reasoning": "Why it's relevant"}},
    ...
]

CRITICAL: For Bernoulli/Binomial focus, prioritize:
- Binomial probability mass functions
- Bernoulli trials and properties  
- Parameter estimation for these distributions
- Computing binomial probabilities
AVOID general statistics introductions unless specifically needed.
"""

            try:
                response = self.llm.generate_response(filtering_prompt)
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    filtered_topics = json.loads(json_match.group())
                    # Keep topics with relevance score >= 6
                    relevant_topics = [t for t in filtered_topics if t.get('relevance_score', 0) >= 6]
                    all_relevant_topics.extend(relevant_topics)
                    
            except Exception as e:
                print(f"⚠️ LLM filtering failed for chunk, using fallback: {e}")
                fallback_topics = self._fallback_topic_filtering_chunk(chunk, query_analysis)
                all_relevant_topics.extend(fallback_topics)

        print(f"✅ Selected {len(all_relevant_topics)} relevant topics")
        return all_relevant_topics

    def _fallback_topic_filtering(self, query_analysis: Dict) -> List[Dict]:
        """Enhanced fallback filtering with domain expertise"""
        primary_domain = query_analysis.get('primary_domain', 'general')
        query_title = query_analysis.get('refined_title', '').lower()
        
        relevant_topics = []
        
        for topic in self.topics:
            title = topic.get('title', topic.get('topic', '')).lower()
            score = 0
            
            # Domain-specific scoring
            if primary_domain in self.learning_domains:
                domain_info = self.learning_domains[primary_domain]
                for keyword in domain_info['keywords']:
                    if keyword in title:
                        score += domain_info['specificity_weight']
                
                # Bonus for essential topics
                for essential in domain_info['essential_topics']:
                    if essential.lower() in title:
                        score += 15
            
            # Special handling for specific domains
            if primary_domain == 'bernoulli_binomial':
                # High scores for exact matches
                if any(term in title for term in ['binomial', 'bernoulli']):
                    score += 20
                elif any(term in title for term in ['probability mass', 'pmf', 'trial']):
                    score += 15
                # Penalty for too general topics
                elif any(term in title for term in ['introduction', 'data collection', 'descriptive statistics']):
                    score -= 10
            
            if score >= 8:  # Threshold for relevance
                topic_copy = topic.copy()
                topic_copy['relevance_score'] = min(10, score / 5)  # Normalize score
                relevant_topics.append(topic_copy)
        
        return sorted(relevant_topics, key=lambda x: x.get('relevance_score', 0), reverse=True)

    def create_enhanced_curriculum(self, relevant_topics: List[Dict], query_analysis: Dict) -> Dict:
        """Create curriculum with enhanced module organization"""
        
        if not self.llm:
            return self._fallback_curriculum_creation(relevant_topics, query_analysis)

        curriculum_prompt = f"""
Create a well-structured curriculum from these relevant topics for: "{query_analysis.get('refined_title', '')}"

LEARNING ANALYSIS:
- Primary Domain: {query_analysis.get('primary_domain', '')}
- Target Audience: {query_analysis.get('target_audience', '')}
- Difficulty: {query_analysis.get('difficulty_level', '')}
- Duration: {query_analysis.get('estimated_duration', '')}

RELEVANT TOPICS:
{self._format_topics_for_llm(relevant_topics)}

Create curriculum with 4-6 modules, each with:
1. Logical learning progression (basic → advanced)
2. Appropriate time allocation 
3. Clear learning outcomes
4. 5-8 topics per module (avoid overloading)

Return as JSON:
{{
    "title": "Curriculum Title",
    "description": "Clear description",
    "learning_objectives": ["Specific learning objectives"],
    "target_audience": "Target audience",
    "prerequisites": ["Prerequisites"],
    "difficulty_level": "Level",
    "estimated_total_duration": "X hours",
    "modules": [
        {{
            "module_number": 1,
            "title": "Module Title", 
            "description": "Module description",
            "learning_outcomes": ["Specific outcomes"],
            "topics": ["Topic 1", "Topic 2", ...],
            "pages": [123, 124, ...],
            "estimated_duration": "X hours",
            "difficulty": "Level"
        }}
    ],
    "total_topics": 42,
    "quality_metrics": {{
        "topic_coverage_score": 8.5,
        "learning_progression_score": 9.0,
        "depth_appropriateness_score": 8.0
    }}
}}

CRITICAL REQUIREMENTS:
1. For Bernoulli/Binomial focus: Ensure core topics are in early modules
2. Avoid general statistics unless essential for understanding
3. Include practical computation/application modules
4. Ensure adequate time for each concept (not rushed)
"""

        try:
            response = self.llm.generate_response(curriculum_prompt)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                curriculum = json.loads(json_match.group())
                
                # Validate and enhance curriculum
                curriculum = self._validate_and_enhance_curriculum(curriculum, relevant_topics)
                print(f"✅ Enhanced curriculum created with {len(curriculum.get('modules', []))} modules")
                return curriculum
                
        except Exception as e:
            print(f"⚠️ LLM curriculum creation failed, using fallback: {e}")
            
        return self._fallback_curriculum_creation(relevant_topics, query_analysis)

    def _validate_and_enhance_curriculum(self, curriculum: Dict, topics: List[Dict]) -> Dict:
        """Validate and enhance curriculum structure"""
        
        # Ensure essential content coverage
        modules = curriculum.get('modules', [])
        primary_domain = curriculum.get('primary_domain', '')
        
        if primary_domain == 'bernoulli_binomial':
            # Check for essential Bernoulli/Binomial content
            essential_topics = [
                'binomial probability mass functions',
                'bernoulli distribution', 
                'computing binomial distribution',
                'hypothesis tests in bernoulli populations'
            ]
            
            covered_essentials = set()
            for module in modules:
                for topic in module.get('topics', []):
                    topic_lower = topic.lower()
                    for essential in essential_topics:
                        if essential in topic_lower:
                            covered_essentials.add(essential)
            
            # Add quality metrics
            coverage_score = len(covered_essentials) / len(essential_topics) * 10
            curriculum.setdefault('quality_metrics', {})['essential_coverage'] = coverage_score
            
            if coverage_score < 7.0:
                print(f"⚠️ Low essential content coverage: {coverage_score:.1f}/10")
        
        return curriculum

    def _format_topics_for_llm(self, topics: List[Dict]) -> str:
        """Format topics for LLM processing"""
        formatted = []
        for i, topic in enumerate(topics[:50], 1):  # Limit to prevent token overflow
            title = topic.get('topic', topic.get('title', ''))
            page = topic.get('page', 'N/A')
            score = topic.get('relevance_score', 0)
            formatted.append(f"{i}. {title} (Page {page}, Relevance: {score:.1f})")
        
        if len(topics) > 50:
            formatted.append(f"... and {len(topics) - 50} more topics")
        
        return '\n'.join(formatted)

    def _fallback_curriculum_creation(self, relevant_topics: List[Dict], query_analysis: Dict) -> Dict:
        """Enhanced fallback curriculum creation"""
        
        # Group topics by relevance and content type
        high_relevance = [t for t in relevant_topics if t.get('relevance_score', 0) >= 8.5]
        medium_relevance = [t for t in relevant_topics if 6.5 <= t.get('relevance_score', 0) < 8.5]
        
        title = query_analysis.get('refined_title', 'Statistics Curriculum')
        primary_domain = query_analysis.get('primary_domain', 'general')
        
        # Create modules based on content progression
        modules = []
        
        if primary_domain == 'bernoulli_binomial':
            modules = self._create_bernoulli_binomial_modules(high_relevance, medium_relevance)
        else:
            modules = self._create_general_modules(high_relevance, medium_relevance, query_analysis)
        
        return {
            "title": title,
            "description": f"A comprehensive curriculum covering {title.lower()}",
            "learning_objectives": query_analysis.get('learning_outcomes', [
                f"Understand fundamental concepts of {title.lower()}",
                f"Apply {title.lower()} to solve real-world problems"
            ]),
            "target_audience": query_analysis.get('target_audience', 'Undergraduate students'),
            "difficulty_level": query_analysis.get('difficulty_level', 'Intermediate'),
            "estimated_total_duration": query_analysis.get('estimated_duration', '4-6 hours'),
            "modules": modules,
            "total_topics": sum(len(m.get('topics', [])) for m in modules)
        }

    def _create_bernoulli_binomial_modules(self, high_rel: List[Dict], medium_rel: List[Dict]) -> List[Dict]:
        """Create specialized Bernoulli/Binomial curriculum modules"""
        
        modules = []
        
        # Module 1: Probability Foundations (only essential basics)
        foundation_topics = [t for t in medium_rel 
                           if any(term in t.get('topic', '').lower() 
                                 for term in ['random variables', 'probability', 'expectation'])
                           and not any(term in t.get('topic', '').lower()
                                     for term in ['introduction', 'data collection'])][:4]
        
        if foundation_topics:
            modules.append({
                "module_number": 1,
                "title": "Probability Foundations for Discrete Distributions",
                "description": "Essential probability concepts needed for Bernoulli and Binomial distributions",
                "topics": [t.get('topic', t.get('title', '')) for t in foundation_topics],
                "pages": [t.get('page', 0) for t in foundation_topics],
                "estimated_duration": "45 minutes",
                "difficulty": "Beginner"
            })
        
        # Module 2: Bernoulli Distribution (core focus)
        bernoulli_topics = [t for t in high_rel 
                          if 'bernoulli' in t.get('topic', '').lower()]
        
        if bernoulli_topics:
            modules.append({
                "module_number": len(modules) + 1,
                "title": "Bernoulli Distribution Theory and Applications", 
                "description": "Complete treatment of Bernoulli trials and distribution",
                "topics": [t.get('topic', t.get('title', '')) for t in bernoulli_topics],
                "pages": [t.get('page', 0) for t in bernoulli_topics],
                "estimated_duration": "60 minutes",
                "difficulty": "Intermediate"
            })
        
        # Module 3: Binomial Distribution (core focus)
        binomial_topics = [t for t in high_rel 
                         if 'binomial' in t.get('topic', '').lower()]
        
        if binomial_topics:
            modules.append({
                "module_number": len(modules) + 1,
                "title": "Binomial Distribution: Theory and Computation",
                "description": "Comprehensive coverage of binomial distribution properties and calculations",
                "topics": [t.get('topic', t.get('title', '')) for t in binomial_topics],
                "pages": [t.get('page', 0) for t in binomial_topics],
                "estimated_duration": "75 minutes", 
                "difficulty": "Intermediate"
            })
        
        # Module 4: Applications and Inference
        application_topics = [t for t in high_rel + medium_rel
                            if any(term in t.get('topic', '').lower()
                                  for term in ['hypothesis', 'test', 'estimation', 'inference'])][:5]
        
        if application_topics:
            modules.append({
                "module_number": len(modules) + 1,
                "title": "Statistical Inference with Bernoulli and Binomial Models",
                "description": "Hypothesis testing and parameter estimation applications",
                "topics": [t.get('topic', t.get('title', '')) for t in application_topics],
                "pages": [t.get('page', 0) for t in application_topics],
                "estimated_duration": "60 minutes",
                "difficulty": "Intermediate to Advanced"
            })
        
        return modules

    def _create_general_modules(self, high_rel: List[Dict], medium_rel: List[Dict], 
                               query_analysis: Dict) -> List[Dict]:
        """Create general curriculum modules"""
        
        # Simple module creation for general topics
        all_topics = high_rel + medium_rel
        topics_per_module = 6
        modules = []
        
        for i in range(0, len(all_topics), topics_per_module):
            module_topics = all_topics[i:i + topics_per_module]
            modules.append({
                "module_number": len(modules) + 1,
                "title": f"Module {len(modules) + 1}: Core Concepts",
                "description": f"Essential topics for {query_analysis.get('refined_title', 'the subject')}",
                "topics": [t.get('topic', t.get('title', '')) for t in module_topics],
                "pages": [t.get('page', 0) for t in module_topics],
                "estimated_duration": "60-75 minutes",
                "difficulty": query_analysis.get('difficulty_level', 'Intermediate')
            })
        
        return modules

    def generate_curriculum(self, learning_query: str) -> Dict:
        """Main method to generate enhanced curriculum"""
        
        print(f"\n🚀 ENHANCED CURRICULUM GENERATION")
        print("=" * 60)
        print(f"🎯 Learning Goal: {learning_query}")
        
        # Step 1: Load topics
        if not self.load_latest_topics():
            return None
        
        # Step 2: Enhanced query analysis
        print("\n🔍 Step 1: Enhanced Query Analysis")
        query_analysis = self.enhanced_query_analysis(learning_query)
        print(f"✅ Primary Domain: {query_analysis.get('primary_domain', 'Unknown')}")
        print(f"✅ Specificity Score: {query_analysis.get('specificity_score', 0):.1f}/10")
        
        # Step 3: Enhanced topic filtering
        print("\n🎯 Step 2: Enhanced Topic Filtering")
        relevant_topics = self.enhanced_topic_filtering(query_analysis)
        
        if not relevant_topics:
            print("❌ No relevant topics found")
            return None
        
        print(f"✅ Selected {len(relevant_topics)} highly relevant topics")
        
        # Step 4: Create enhanced curriculum
        print("\n📚 Step 3: Enhanced Curriculum Creation")
        curriculum = self.create_enhanced_curriculum(relevant_topics, query_analysis)
        
        if curriculum:
            # Beautify topic titles for better presentation
            print("\n✨ Beautifying topic titles...")
            curriculum = beautify_curriculum_topics(curriculum)
            
            # Save curriculum
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
            filename = f"output/enhanced_curriculum_{timestamp}.json"
            os.makedirs("output", exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(curriculum, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Enhanced curriculum saved: {filename}")
            
            # Display results
            self._display_curriculum_summary(curriculum)
            
        return curriculum

    def _display_curriculum_summary(self, curriculum: Dict):
        """Display curriculum summary with quality metrics"""
        
        print(f"\n📊 ENHANCED CURRICULUM SUMMARY")
        print("=" * 50)
        print(f"📚 Title: {curriculum.get('title', 'Untitled')}")
        print(f"🎯 Modules: {len(curriculum.get('modules', []))}")
        print(f"📄 Total Topics: {curriculum.get('total_topics', 0)}")
        print(f"⏱️ Duration: {curriculum.get('estimated_total_duration', 'Unknown')}")
        
        # Quality metrics
        quality = curriculum.get('quality_metrics', {})
        if quality:
            print(f"\n📈 Quality Metrics:")
            for metric, score in quality.items():
                print(f"   {metric}: {score:.1f}/10")
        
        print(f"\n📋 Module Breakdown:")
        for module in curriculum.get('modules', []):
            print(f"   {module.get('module_number', '?')}. {module.get('title', 'Untitled')}")
            print(f"      📄 Topics: {len(module.get('topics', []))}")
            print(f"      ⏱️ Duration: {module.get('estimated_duration', 'Unknown')}")

def main():
    """Main function for interactive use"""
    print("🚀 Enhanced LLM Curriculum Generator")
    print("=" * 50)
    print("Features:")
    print(" • Enhanced topic relevance filtering")
    print(" • Domain-specific curriculum creation")
    print(" • Quality metrics and validation")
    print(" • Textbook structure awareness")
    print()
    
    generator = EnhancedLLMCurriculumGenerator()
    
    # Example usage
    if len(generator.topics) == 0:
        print("💡 Example: Run the complete pathway generator first:")
        print("   python complete_pathway_generator.py")
        return
    
    learning_query = input("🎯 Enter your learning goal: ").strip()
    if learning_query:
        curriculum = generator.generate_curriculum(learning_query)
        if curriculum:
            print("\n🎉 Enhanced curriculum generation complete!")
        else:
            print("\n❌ Curriculum generation failed")

if __name__ == "__main__":
    main()
