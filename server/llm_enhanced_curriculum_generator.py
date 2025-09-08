"""
LLM Enhanced Curriculum Generator
================================
Advanced curriculum creation using LLM-powered topic extraction and organization.
Inspired by curriculum_creator_fallback.py with enhanced LLM integration.

Features:
- LLM-powered query refinement and topic analysis
- Intelligent topic clustering and organization
- Academic-grade curriculum structuring
- Fallback mechanisms for reliability
- Clean, organized module creation

Usage:
    python llm_enhanced_curriculum_generator.py
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Set
from LLM import AdvancedAzureLLM

class LLMEnhancedCurriculumGenerator:
    def __init__(self):
        self.llm = None
        try:
            self.llm = AdvancedAzureLLM()
            print("✅ LLM initialized successfully")
        except Exception as e:
            print(f"⚠️ LLM not available, using fallback methods: {e}")
        
        self.topics = []
        self.learning_domains = {
            'probability': ['probability', 'random', 'chance', 'likelihood', 'distribution', 'stochastic'],
            'statistics': ['statistics', 'statistical', 'data', 'analysis', 'inference', 'hypothesis', 'test'],
            'expectation': ['expectation', 'expected', 'value', 'mean', 'average', 'moment'],
            'variance': ['variance', 'deviation', 'spread', 'variability', 'dispersion', 'covariance'],
            'regression': ['regression', 'correlation', 'linear', 'model', 'prediction', 'least squares'],
            'sampling': ['sampling', 'sample', 'population', 'estimation', 'estimator'],
            'distribution': ['distribution', 'normal', 'binomial', 'poisson', 'uniform', 'exponential'],
            'signal_processing': ['signal', 'signals', 'processing', 'fourier', 'transform', 'frequency'],
            'systems': ['systems', 'system', 'linear', 'control', 'response', 'stability'],
            'mathematics': ['theorem', 'proof', 'equation', 'function', 'derivative', 'integral'],
            'machine_learning': ['machine learning', 'neural', 'classification', 'clustering', 'training'],
            'data_analysis': ['data mining', 'visualization', 'exploratory', 'descriptive', 'predictive']
        }
    
    def load_latest_topics(self) -> bool:
        """Load the most recent topic extraction results"""
        output_dir = "output"
        
        if not os.path.exists(output_dir):
            print(f"❌ Output directory not found: {output_dir}")
            return False
        
        # Find the most recent optimized universal topics file
        json_files = [f for f in os.listdir(output_dir) 
                     if 'optimized_universal' in f and f.endswith('.json')]
        
        if not json_files:
            # Try other topic extraction files
            json_files = [f for f in os.listdir(output_dir) 
                         if ('topics' in f or 'extracted' in f) and f.endswith('.json')]
        
        if not json_files:
            print("❌ No topic extraction files found. Run topic extraction first.")
            return False
        
        # Sort by timestamp and get the latest
        json_files.sort(reverse=True)
        latest_file = json_files[0]
        file_path = os.path.join(output_dir, latest_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.topics = data.get('topics', data.get('extracted_topics', []))
            
            print(f"📚 Loaded {len(self.topics)} topics from: {latest_file}")
            return len(self.topics) > 0
            
        except Exception as e:
            print(f"❌ Error loading topics: {e}")
            return False
    
    def refine_query_with_llm(self, user_query: str) -> Dict[str, Any]:
        """Enhanced query refinement using LLM"""
        if not self.llm:
            return self.refine_query_fallback(user_query)
        
        try:
            prompt = f"""
            Analyze and enhance this learning query to create a comprehensive curriculum:
            
            User Query: "{user_query}"
            
            Return a JSON object with:
            {{
                "refined_title": "Clear, specific learning path title",
                "learning_objectives": ["obj1", "obj2", "obj3"],
                "target_audience": "Who this is for",
                "prerequisites": ["prereq1", "prereq2"] or [],
                "estimated_duration": "Total time estimate",
                "difficulty_level": "Beginner/Intermediate/Advanced",
                "key_concepts": ["concept1", "concept2", "concept3"]
            }}
            
            Make it academic yet accessible. Focus on {user_query}.
            Return only the JSON, no other text.
            """
            
            response = self.llm.generate_response(prompt)
            
            if response and response.strip():
                # Clean response
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                refined_data = json.loads(clean_response)
                if isinstance(refined_data, dict) and 'refined_title' in refined_data:
                    print(f"🤖 LLM enhanced query successfully")
                    return refined_data
            
            return self.refine_query_fallback(user_query)
                
        except Exception as e:
            print(f"⚠️ LLM query refinement failed: {e}")
            return self.refine_query_fallback(user_query)
    
    def refine_query_fallback(self, user_query: str) -> Dict[str, Any]:
        """Fallback query refinement"""
        query_lower = user_query.lower()
        
        # Detect domains
        detected_domains = []
        for domain, keywords in self.learning_domains.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_domains.append(domain.replace('_', ' ').title())
        
        difficulty = "Intermediate"
        if any(word in query_lower for word in ['basic', 'intro', 'fundamental', 'beginner']):
            difficulty = "Beginner"
        elif any(word in query_lower for word in ['advanced', 'deep', 'expert']):
            difficulty = "Advanced"
        
        return {
            "refined_title": f"Mastering {user_query.title()}",
            "learning_objectives": [
                f"Understand fundamental concepts in {user_query}",
                f"Apply {user_query} techniques to real-world problems",
                f"Analyze and interpret results using {user_query} methods"
            ],
            "target_audience": f"Students and professionals interested in {user_query}",
            "prerequisites": ["Basic mathematics", "Statistical concepts"] if 'statistic' in query_lower else [],
            "estimated_duration": "20-30 hours",
            "difficulty_level": difficulty,
            "key_concepts": detected_domains if detected_domains else [user_query.title()]
        }
    
    def extract_relevant_topics_with_llm(self, topics_chunk: List[Dict], query_data: Dict) -> List[Dict]:
        """Enhanced topic extraction using LLM"""
        if not self.llm:
            return self.extract_relevant_topics_fallback(topics_chunk, query_data['refined_title'])
        
        try:
            topic_list = "\n".join([f"- {t['topic']} (Page {t['page']})" for t in topics_chunk])
            key_concepts = ", ".join(query_data.get('key_concepts', []))
            
            prompt = f"""
            Learning Goal: {query_data['refined_title']}
            Key Concepts: {key_concepts}
            Target Level: {query_data.get('difficulty_level', 'Intermediate')}
            
            From these topics, select the most relevant ones:
            {topic_list}
            
            Return JSON array with topics that best support the learning goal:
            [
              {{
                "topic": "exact topic name",
                "page": page_number,
                "relevance_score": 1-10,
                "learning_category": "foundational/core/advanced/supplementary",
                "prerequisite_for": ["other topics it enables"],
                "concepts_covered": ["concept1", "concept2"]
              }}
            ]
            
            Prioritize topics that:
            1. Match the difficulty level
            2. Cover key concepts
            3. Build logical learning progression
            4. Provide practical applications
            
            Maximum 15 topics. Return only JSON.
            """
            
            response = self.llm.generate_response(prompt)
            
            if response and response.strip():
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                relevant_topics = json.loads(clean_response)
                if isinstance(relevant_topics, list) and len(relevant_topics) > 0:
                    print(f"🎯 LLM identified {len(relevant_topics)} relevant topics")
                    return relevant_topics
            
            return self.extract_relevant_topics_fallback(topics_chunk, query_data['refined_title'])
            
        except Exception as e:
            print(f"⚠️ LLM topic extraction failed: {e}")
            return self.extract_relevant_topics_fallback(topics_chunk, query_data['refined_title'])
    
    def extract_relevant_topics_fallback(self, topics_chunk: List[Dict], query: str) -> List[Dict]:
        """Fallback topic extraction using advanced pattern matching"""
        query_lower = query.lower()
        relevant_topics = []
        
        # Extract keywords from query
        query_keywords = set(re.findall(r'\b\w+\b', query_lower))
        
        for topic_data in topics_chunk:
            topic = topic_data['topic'].lower()
            topic_keywords = set(re.findall(r'\b\w+\b', topic))
            
            # Scoring algorithm
            keyword_score = len(query_keywords.intersection(topic_keywords)) * 2
            
            # Domain-specific scoring
            domain_score = 0
            for domain, keywords in self.learning_domains.items():
                if any(kw in query_lower for kw in keywords):
                    if any(kw in topic for kw in keywords):
                        domain_score += 3
            
            # Chapter/section importance
            structure_score = 0
            if re.search(r'chapter\s+\d+|section\s+\d+', topic, re.IGNORECASE):
                structure_score += 2
            
            # Length and detail bonus
            length_bonus = 1 if len(topic.split()) >= 4 else 0
            
            total_score = keyword_score + domain_score + structure_score + length_bonus
            
            if total_score >= 3:  # Higher threshold for quality
                # Categorize topic
                category = "core"
                if any(word in topic for word in ['introduction', 'basic', 'fundamental']):
                    category = "foundational"
                elif any(word in topic for word in ['advanced', 'complex', 'specialized']):
                    category = "advanced"
                elif any(word in topic for word in ['example', 'application', 'exercise']):
                    category = "supplementary"
                
                relevant_topics.append({
                    'topic': topic_data['topic'],
                    'page': topic_data['page'],
                    'relevance_score': min(total_score, 10),
                    'learning_category': category,
                    'prerequisite_for': [],
                    'concepts_covered': list(topic_keywords.intersection(query_keywords))[:3]
                })
        
        # Sort by relevance score
        relevant_topics.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant_topics[:15]  # Top 15 most relevant
    
    def create_curriculum_with_llm(self, relevant_topics: List[Dict], query_data: Dict) -> Dict:
        """Create comprehensive curriculum using LLM"""
        if not self.llm or len(relevant_topics) == 0:
            return self.create_curriculum_fallback(relevant_topics, query_data)
        
        try:
            # Prepare topic data
            topics_summary = "\n".join([
                f"- {t['topic']} (Page {t['page']}, Category: {t.get('learning_category', 'core')}, Score: {t.get('relevance_score', 5)})"
                for t in relevant_topics
            ])
            
            prompt = f"""
            Create a comprehensive academic curriculum for: "{query_data['refined_title']}"
            
            Learning Objectives: {', '.join(query_data.get('learning_objectives', []))}
            Difficulty Level: {query_data.get('difficulty_level', 'Intermediate')}
            Target Duration: {query_data.get('estimated_duration', '20-30 hours')}
            
            Available Topics:
            {topics_summary}
            
            Create a well-structured curriculum with this JSON format:
            {{
              "title": "{query_data['refined_title']}",
              "description": "Comprehensive description of the learning path",
              "learning_objectives": {json.dumps(query_data.get('learning_objectives', []))},
              "target_audience": "{query_data.get('target_audience', 'General learners')}",
              "prerequisites": {json.dumps(query_data.get('prerequisites', []))},
              "difficulty_level": "{query_data.get('difficulty_level', 'Intermediate')}",
              "estimated_total_duration": "{query_data.get('estimated_duration', '25 hours')}",
              "modules": [
                {{
                  "module_number": 1,
                  "title": "Module 1: Foundations",
                  "description": "Module description",
                  "learning_outcomes": ["outcome1", "outcome2"],
                  "topics": ["topic1", "topic2"],
                  "pages": [page1, page2],
                  "estimated_duration": "3 hours",
                  "difficulty": "Beginner"
                }}
              ],
              "total_topics": {len(relevant_topics)},
              "assessment_suggestions": ["suggestion1", "suggestion2"],
              "further_reading": ["resource1", "resource2"]
            }}
            
            Organization guidelines:
            1. Start with foundational concepts
            2. Progress logically to advanced topics
            3. Group related concepts into coherent modules
            4. Balance theory and application
            5. Include 4-7 modules total
            6. Each module should have 3-8 topics
            
            Return only the JSON, no other text.
            """
            
            response = self.llm.generate_response(prompt)
            
            if response and response.strip():
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                curriculum = json.loads(clean_response)
                if isinstance(curriculum, dict) and 'modules' in curriculum:
                    print(f"🏗️ LLM created curriculum with {len(curriculum['modules'])} modules")
                    return curriculum
            
            return self.create_curriculum_fallback(relevant_topics, query_data)
            
        except Exception as e:
            print(f"⚠️ LLM curriculum creation failed: {e}")
            return self.create_curriculum_fallback(relevant_topics, query_data)
    
    def create_curriculum_fallback(self, relevant_topics: List[Dict], query_data: Dict) -> Dict:
        """Enhanced fallback curriculum creation"""
        if not relevant_topics:
            return {
                "title": query_data.get('refined_title', 'Learning Path'),
                "description": "No specific topics found for curriculum creation.",
                "modules": [],
                "total_topics": 0
            }
        
        # Group topics by learning category
        categorized_topics = {
            'foundational': [],
            'core': [],
            'advanced': [],
            'supplementary': []
        }
        
        for topic in relevant_topics:
            category = topic.get('learning_category', 'core')
            categorized_topics[category].append(topic)
        
        # Create modules
        modules = []
        module_num = 1
        
        # Foundational module
        if categorized_topics['foundational']:
            modules.append({
                "module_number": module_num,
                "title": f"Module {module_num}: Foundations",
                "description": "Essential foundational concepts",
                "topics": [t['topic'] for t in categorized_topics['foundational']],
                "pages": [t['page'] for t in categorized_topics['foundational']],
                "estimated_duration": f"{len(categorized_topics['foundational']) * 45} minutes",
                "difficulty": "Beginner"
            })
            module_num += 1
        
        # Core concepts (split into multiple modules if needed)
        core_topics = categorized_topics['core']
        if core_topics:
            chunk_size = 6
            for i in range(0, len(core_topics), chunk_size):
                chunk = core_topics[i:i + chunk_size]
                modules.append({
                    "module_number": module_num,
                    "title": f"Module {module_num}: Core Concepts {'I' * ((i // chunk_size) + 1)}",
                    "description": "Essential concepts and methods",
                    "topics": [t['topic'] for t in chunk],
                    "pages": [t['page'] for t in chunk],
                    "estimated_duration": f"{len(chunk) * 45} minutes",
                    "difficulty": "Intermediate"
                })
                module_num += 1
        
        # Advanced module
        if categorized_topics['advanced']:
            modules.append({
                "module_number": module_num,
                "title": f"Module {module_num}: Advanced Topics",
                "description": "Advanced concepts and specialized applications",
                "topics": [t['topic'] for t in categorized_topics['advanced']],
                "pages": [t['page'] for t in categorized_topics['advanced']],
                "estimated_duration": f"{len(categorized_topics['advanced']) * 60} minutes",
                "difficulty": "Advanced"
            })
            module_num += 1
        
        # Supplementary module
        if categorized_topics['supplementary']:
            modules.append({
                "module_number": module_num,
                "title": f"Module {module_num}: Applications & Examples",
                "description": "Practical applications and worked examples",
                "topics": [t['topic'] for t in categorized_topics['supplementary']],
                "pages": [t['page'] for t in categorized_topics['supplementary']],
                "estimated_duration": f"{len(categorized_topics['supplementary']) * 30} minutes",
                "difficulty": "Applied"
            })
        
        return {
            "title": query_data.get('refined_title', 'Learning Path'),
            "description": f"Structured curriculum covering {len(relevant_topics)} topics",
            "learning_objectives": query_data.get('learning_objectives', []),
            "modules": modules,
            "total_topics": len(relevant_topics),
            "estimated_total_duration": query_data.get('estimated_duration', f"{len(relevant_topics) * 45} minutes")
        }
    
    def save_curriculum(self, curriculum: Dict, query: str) -> str:
        """Save curriculum to file with metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = re.sub(r'[^\w\s-]', '', query)[:30].replace(' ', '_')
        
        filename = f"llm_curriculum_{safe_query}_{timestamp}.json"
        filepath = os.path.join("output", filename)
        
        os.makedirs("output", exist_ok=True)
        
        # Add metadata
        curriculum['metadata'] = {
            'created_at': datetime.now().isoformat(),
            'generator': 'LLM Enhanced Curriculum Generator',
            'original_query': query,
            'version': '2.0'
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(curriculum, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def display_curriculum(self, curriculum: Dict):
        """Enhanced curriculum display"""
        print(f"\n🎯 {curriculum['title']}")
        print("=" * 80)
        print(f"📖 {curriculum['description']}")
        
        if 'learning_objectives' in curriculum and curriculum['learning_objectives']:
            print(f"\n🎯 Learning Objectives:")
            for i, obj in enumerate(curriculum['learning_objectives'], 1):
                print(f"   {i}. {obj}")
        
        if 'target_audience' in curriculum:
            print(f"\n👥 Target Audience: {curriculum['target_audience']}")
        
        if 'difficulty_level' in curriculum:
            print(f"📊 Difficulty Level: {curriculum['difficulty_level']}")
        
        print(f"📚 Total Topics: {curriculum['total_topics']}")
        print(f"⏱️ Estimated Duration: {curriculum.get('estimated_total_duration', 'N/A')}")
        
        modules = curriculum.get('modules', [])
        if not modules:
            print("❌ No modules found in curriculum")
            return
        
        print(f"\n📚 Learning Modules ({len(modules)}):")
        print("-" * 40)
        
        for module in modules:
            print(f"\n{module['title']}")
            if 'description' in module:
                print(f"   📝 {module['description']}")
            print(f"   ⏱️ Duration: {module.get('estimated_duration', 'N/A')}")
            if 'difficulty' in module:
                print(f"   📊 Level: {module['difficulty']}")
            print(f"   📄 Topics ({len(module['topics'])}):")
            
            for i, topic in enumerate(module['topics'], 1):
                page = module['pages'][i-1] if i-1 < len(module['pages']) else 'N/A'
                print(f"       {i:2d}. {topic} (Page {page})")
        
        if 'assessment_suggestions' in curriculum and curriculum['assessment_suggestions']:
            print(f"\n📝 Assessment Suggestions:")
            for suggestion in curriculum['assessment_suggestions']:
                print(f"   • {suggestion}")
        
        print("\n✨ Advanced curriculum ready for implementation!")
    
    def run_interactive(self):
        """Run the enhanced interactive curriculum creation workflow"""
        print("\n🎓 LLM Enhanced Curriculum Generator - AI-Powered Learning Path Creation")
        print("=" * 85)
        print("Describe your learning goals and I'll create a comprehensive, structured curriculum!")
        print("\n💡 Enhanced Features:")
        print("  • AI-powered topic selection and organization")
        print("  • Academic-grade curriculum structure") 
        print("  • Learning objective formulation")
        print("  • Difficulty progression planning")
        print("  • Assessment and resource recommendations")
        
        print("\n🎯 Example Queries:")
        print("  • 'I want to master expectation and variance for financial modeling'")
        print("  • 'Teach me advanced signal processing for audio applications'")
        print("  • 'Create a comprehensive statistics course for data science'")
        print("  • 'I need to understand probability theory for machine learning'")
        
        # Load topics
        if not self.load_latest_topics():
            return
        
        # Get user input
        user_query = input("\n🚀 What would you like to learn? ").strip()
        
        if not user_query:
            print("❌ Please provide a learning query.")
            return
        
        # Step 1: Enhanced query analysis
        print(f"\n🧠 AI analyzing and enhancing your learning request...")
        query_data = self.refine_query_with_llm(user_query)
        
        print(f"\n📝 Original Query: '{user_query}'")
        print(f"🎯 Enhanced Learning Path: '{query_data['refined_title']}'")
        print(f"👥 Target Audience: {query_data.get('target_audience', 'N/A')}")
        print(f"📊 Difficulty Level: {query_data.get('difficulty_level', 'N/A')}")
        
        # Step 2: Intelligent topic selection
        chunk_size = 40  # Smaller chunks for better LLM analysis
        all_relevant_topics = []
        
        print(f"\n🔍 AI analyzing {len(self.topics)} topics for curriculum relevance...")
        
        if len(self.topics) > chunk_size:
            num_chunks = (len(self.topics) + chunk_size - 1) // chunk_size
            print(f"⚡ Processing in {num_chunks} intelligent chunks...")
            
            for i in range(0, len(self.topics), chunk_size):
                chunk = self.topics[i:i + chunk_size]
                chunk_num = (i // chunk_size) + 1
                
                print(f"   🧠 AI analyzing chunk {chunk_num}/{num_chunks}...")
                
                relevant_topics = self.extract_relevant_topics_with_llm(chunk, query_data)
                
                if relevant_topics:
                    all_relevant_topics.extend(relevant_topics)
                    print(f"   ✅ Found {len(relevant_topics)} relevant topics")
        else:
            print("🧠 AI analyzing all topics comprehensively...")
            all_relevant_topics = self.extract_relevant_topics_with_llm(self.topics, query_data)
        
        # Remove duplicates and sort
        seen_topics = set()
        unique_topics = []
        for topic in all_relevant_topics:
            if topic['topic'] not in seen_topics:
                seen_topics.add(topic['topic'])
                unique_topics.append(topic)
        
        # Sort by relevance score
        unique_topics.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        print(f"\n🎯 AI selected {len(unique_topics)} highly relevant topics")
        
        if not unique_topics:
            print("❌ No relevant topics found for your query.")
            print("💡 Try refining your learning goals or running topic extraction first.")
            return
        
        # Step 3: AI curriculum creation
        print(f"\n🏗️ AI creating comprehensive curriculum structure...")
        curriculum = self.create_curriculum_with_llm(unique_topics, query_data)
        
        # Step 4: Save and display
        filepath = self.save_curriculum(curriculum, user_query)
        print(f"\n💾 Curriculum saved to: {filepath}")
        
        self.display_curriculum(curriculum)

def main():
    generator = LLMEnhancedCurriculumGenerator()
    generator.run_interactive()

if __name__ == "__main__":
    main()
