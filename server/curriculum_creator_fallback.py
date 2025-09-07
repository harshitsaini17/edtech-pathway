"""
Curriculum Creator with Fallback
===============================
Creates personalized learning curricula with smart fallback when LLM is unavailable.
Uses pattern matching and keyword analysis as backup to LLM-based topic selection.

Features:
- User query refinement with fallback
- Topic chunking for large datasets  
- Pattern-based topic matching as LLM fallback
- Structured curriculum generation
- Learning path organization

Usage:
    python curriculum_creator_fallback.py
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Set
from LLM import AdvancedAzureLLM

class CurriculumCreatorFallback:
    def __init__(self):
        self.llm = None
        try:
            self.llm = AdvancedAzureLLM()
            print("✅ LLM initialized successfully")
        except Exception as e:
            print(f"⚠️ LLM not available, using fallback methods: {e}")
        
        self.topics = []
        self.learning_domains = {
            'probability': ['probability', 'random', 'chance', 'likelihood', 'distribution'],
            'statistics': ['statistics', 'statistical', 'data', 'analysis', 'inference', 'hypothesis', 'test'],
            'expectation': ['expectation', 'expected', 'value', 'mean', 'average'],
            'variance': ['variance', 'deviation', 'spread', 'variability'],
            'regression': ['regression', 'correlation', 'linear', 'model', 'prediction'],
            'sampling': ['sampling', 'sample', 'population', 'estimation'],
            'distribution': ['distribution', 'normal', 'binomial', 'poisson', 'uniform', 'exponential'],
            'signal_processing': ['signal', 'signals', 'processing', 'fourier', 'transform', 'frequency'],
            'systems': ['systems', 'system', 'linear', 'control', 'response', 'stability'],
            'mathematics': ['theorem', 'proof', 'equation', 'function', 'derivative', 'integral']
        }
    
    def load_latest_topics(self) -> bool:
        """Load the most recent topic extraction results"""
        output_dir = "output"
        
        if not os.path.exists(output_dir):
            print(f"❌ Output directory not found: {output_dir}")
            return False
        
        # Find the most recent optimized universal topics file
        json_files = [f for f in os.listdir(output_dir) if 'optimized_universal' in f and f.endswith('.json')]
        
        if not json_files:
            print("❌ No topic extraction files found. Run optimized_universal_extractor.py first.")
            return False
        
        # Sort by timestamp and get the latest
        json_files.sort(reverse=True)
        latest_file = json_files[0]
        file_path = os.path.join(output_dir, latest_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.topics = data.get('topics', [])
            
            print(f"📚 Loaded {len(self.topics)} topics from: {latest_file}")
            return len(self.topics) > 0
            
        except Exception as e:
            print(f"❌ Error loading topics: {e}")
            return False
    
    def refine_query_fallback(self, user_query: str) -> str:
        """Fallback query refinement using pattern matching"""
        query_lower = user_query.lower()
        
        # Detect learning domains
        detected_domains = []
        for domain, keywords in self.learning_domains.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_domains.append(domain)
        
        if not detected_domains:
            # Generic refinement
            refined = f"Learn fundamentals of {user_query}"
        else:
            # Domain-specific refinement
            domain_str = ', '.join(detected_domains)
            refined = f"Comprehensive study of {domain_str} with practical applications and theoretical foundations"
        
        print(f"🔧 Fallback refinement: '{user_query}' → '{refined}'")
        return refined
    
    def refine_query_with_llm(self, user_query: str) -> str:
        """Refine user query using LLM with fallback"""
        if not self.llm:
            return self.refine_query_fallback(user_query)
        
        try:
            prompt = f"""
            Refine this simple learning query by making it slightly more specific but keep it brief:
            
            User Query: "{user_query}"
            
            Add just enough context to make it clear (1-2 sentences max).
            Examples:
            - "calculus" → "Learn calculus fundamentals including limits, derivatives, and integrals"
            - "statistics" → "Learn statistical concepts including probability, inference, and data analysis"
            - "machine learning" → "Learn machine learning basics including algorithms and model building"
            
            Keep under 100 words. Return only the refined query.
            """
            
            refined_query = self.llm.gpt_5(prompt)
            
            if refined_query and len(refined_query.strip()) > 10:
                print(f"🤖 LLM refined: '{user_query}' → '{refined_query.strip()}'")
                return refined_query.strip()
            else:
                return self.refine_query_fallback(user_query)
                
        except Exception as e:
            print(f"⚠️ LLM refinement failed: {e}")
            return self.refine_query_fallback(user_query)
    
    def extract_relevant_topics_fallback(self, topics_chunk: List[Dict], query: str) -> List[Dict]:
        """Fallback topic extraction using keyword matching"""
        query_lower = query.lower()
        relevant_topics = []
        
        # Extract keywords from query
        query_keywords = set(re.findall(r'\b\w+\b', query_lower))
        
        for topic_data in topics_chunk:
            topic = topic_data['topic'].lower()
            
            # Score topic based on keyword matches
            topic_keywords = set(re.findall(r'\b\w+\b', topic))
            
            # Direct keyword overlap
            keyword_score = len(query_keywords.intersection(topic_keywords))
            
            # Domain-specific scoring
            domain_score = 0
            for domain, keywords in self.learning_domains.items():
                if any(kw in query_lower for kw in keywords):
                    if any(kw in topic for kw in keywords):
                        domain_score += 2
            
            # Length bonus for detailed topics
            length_bonus = 1 if len(topic.split()) >= 4 else 0
            
            total_score = keyword_score + domain_score + length_bonus
            
            if total_score >= 2:  # Threshold for relevance
                relevant_topics.append({
                    'topic': topic_data['topic'],
                    'page': topic_data['page'],
                    'relevance_score': total_score
                })
        
        # Sort by relevance score
        relevant_topics.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant_topics[:10]  # Top 10 most relevant
    
    def extract_relevant_topics_with_llm(self, topics_chunk: List[Dict], query: str) -> List[Dict]:
        """Extract relevant topics using LLM with fallback"""
        if not self.llm:
            return self.extract_relevant_topics_fallback(topics_chunk, query)
        
        try:
            topic_list = "\n".join([f"- {t['topic']} (Page {t['page']})" for t in topics_chunk])
            
            prompt = f"""
            Given this learning query: "{query}"
            
            From the following topics, identify the most relevant ones for learning:
            {topic_list}
            
            Return a JSON array of the most relevant topics (maximum 10) in this format:
            [
              {{"topic": "exact topic name", "page": page_number, "relevance_score": 1-10}}
            ]
            
            Only return the JSON array, no other text.
            """
            
            response = self.llm.gpt_5(prompt)
            
            if response and response.strip():
                # Remove markdown code blocks if present
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]  # Remove ```json
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]  # Remove ```
                clean_response = clean_response.strip()
                
                relevant_topics = json.loads(clean_response)
                if isinstance(relevant_topics, list) and len(relevant_topics) > 0:
                    return relevant_topics
            
            return self.extract_relevant_topics_fallback(topics_chunk, query)
            
        except Exception as e:
            print(f"⚠️ LLM topic extraction failed: {e}")
            return self.extract_relevant_topics_fallback(topics_chunk, query)
    
    def create_curriculum_fallback(self, relevant_topics: List[Dict], refined_query: str) -> Dict:
        """Fallback curriculum creation using pattern-based organization"""
        if not relevant_topics:
            return {
                "title": f"Learning Path: {refined_query}",
                "description": "No specific topics found. Consider running topic extraction first.",
                "modules": [],
                "total_topics": 0
            }
        
        # Group topics by patterns and create modules
        modules = []
        
        # Group by chapter/section patterns
        chapter_topics = {}
        standalone_topics = []
        
        for topic_data in relevant_topics:
            topic = topic_data['topic']
            
            # Try to identify chapter/section patterns
            chapter_match = re.search(r'(Chapter\s+\d+|Section\s+\d+|\d+\.\d+)', topic, re.IGNORECASE)
            
            if chapter_match:
                chapter_key = chapter_match.group(1)
                if chapter_key not in chapter_topics:
                    chapter_topics[chapter_key] = []
                chapter_topics[chapter_key].append(topic_data)
            else:
                standalone_topics.append(topic_data)
        
        # Create modules from grouped topics
        module_num = 1
        
        # Chapter-based modules
        for chapter, topics in chapter_topics.items():
            modules.append({
                "module_number": module_num,
                "title": f"Module {module_num}: {chapter}",
                "topics": [t['topic'] for t in topics],
                "pages": [t['page'] for t in topics],
                "estimated_duration": f"{len(topics) * 30} minutes"
            })
            module_num += 1
        
        # Standalone topics module
        if standalone_topics:
            modules.append({
                "module_number": module_num,
                "title": f"Module {module_num}: Supplementary Topics",
                "topics": [t['topic'] for t in standalone_topics],
                "pages": [t['page'] for t in standalone_topics],
                "estimated_duration": f"{len(standalone_topics) * 30} minutes"
            })
        
        return {
            "title": f"Learning Path: {refined_query}",
            "description": f"Curriculum generated from {len(relevant_topics)} relevant topics",
            "modules": modules,
            "total_topics": len(relevant_topics),
            "estimated_total_duration": f"{len(relevant_topics) * 30} minutes"
        }
    
    def create_curriculum_with_llm(self, relevant_topics: List[Dict], refined_query: str) -> Dict:
        """Create curriculum using LLM with fallback"""
        if not self.llm:
            return self.create_curriculum_fallback(relevant_topics, refined_query)
        
        try:
            topics_summary = "\n".join([
                f"- {t['topic']} (Page {t['page']}, Relevance: {t.get('relevance_score', 'N/A')})"
                for t in relevant_topics
            ])
            
            prompt = f"""
            Create a structured learning curriculum for: "{refined_query}"
            
            Based on these relevant topics:
            {topics_summary}
            
            Create a curriculum with the following JSON structure:
            {{
              "title": "Learning Path: [descriptive title]",
              "description": "[brief description of what will be learned]",
              "modules": [
                {{
                  "module_number": 1,
                  "title": "Module 1: [module name]",
                  "topics": ["topic1", "topic2"],
                  "pages": [page1, page2],
                  "estimated_duration": "[time estimate]"
                }}
              ],
              "total_topics": {len(relevant_topics)},
              "estimated_total_duration": "[total time estimate]"
            }}
            
            Organize topics logically from basic to advanced concepts.
            Return only the JSON, no other text.
            """
            
            response = self.llm.gpt_5(prompt)
            
            if response and response.strip():
                # Remove markdown code blocks if present
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]  # Remove ```json
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]  # Remove ```
                clean_response = clean_response.strip()
                
                curriculum = json.loads(clean_response)
                if isinstance(curriculum, dict) and 'modules' in curriculum:
                    return curriculum
            
            return self.create_curriculum_fallback(relevant_topics, refined_query)
            
        except Exception as e:
            print(f"⚠️ LLM curriculum creation failed: {e}")
            return self.create_curriculum_fallback(relevant_topics, refined_query)
    
    def save_curriculum(self, curriculum: Dict, query: str) -> str:
        """Save curriculum to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = re.sub(r'[^\w\s-]', '', query)[:30].replace(' ', '_')
        
        # JSON format
        filename = f"curriculum_{safe_query}_{timestamp}.json"
        filepath = os.path.join("output", filename)
        
        os.makedirs("output", exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(curriculum, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def display_curriculum(self, curriculum: Dict):
        """Display curriculum in a user-friendly format"""
        print(f"\n🎯 {curriculum['title']}")
        print("=" * 60)
        print(f"📖 {curriculum['description']}")
        print(f"📊 Total Topics: {curriculum['total_topics']}")
        print(f"⏱️ Estimated Duration: {curriculum.get('estimated_total_duration', 'N/A')}")
        
        modules = curriculum.get('modules', [])
        if not modules:
            print("❌ No modules found in curriculum")
            return
        
        print(f"\n📚 Learning Modules ({len(modules)}):")
        print("-" * 40)
        
        for module in modules:
            print(f"\n{module['title']}")
            print(f"   ⏱️ Duration: {module.get('estimated_duration', 'N/A')}")
            print(f"   📄 Topics ({len(module['topics'])}):")
            
            for i, topic in enumerate(module['topics'], 1):
                page = module['pages'][i-1] if i-1 < len(module['pages']) else 'N/A'
                print(f"      {i:2d}. {topic} (Page {page})")
        
        print("\n✨ Curriculum ready for learning!")
    
    def run_interactive(self):
        """Run the interactive curriculum creation workflow"""
        print("\n🎓 Curriculum Creator with Fallback - Personalized Learning Path Generator")
        print("=" * 80)
        print("Tell me what you want to learn, and I'll create a custom curriculum for you!")
        print("\n💡 Examples:")
        print("  • 'I want to learn probability and statistics for data science'")
        print("  • 'Teach me signal processing fundamentals for audio engineering'")
        print("  • 'I need to understand linear systems for control engineering'")
        print("  • 'Help me learn expectation and variance in statistics'")
        
        # Load topics
        if not self.load_latest_topics():
            return
        
        # Get user input
        user_query = input("\n💭 What would you like to learn? ").strip()
        
        if not user_query:
            print("❌ Please provide a learning query.")
            return
        
        # Step 1: Refine query
        print(f"\n🔧 Refining your query...")
        refined_query = self.refine_query_with_llm(user_query)
        
        print(f"📝 Original Query: '{user_query}'")
        print(f"🎯 Refined Query: '{refined_query}'")
        print()
        
        # Step 2: Process topics in chunks
        chunk_size = 50
        all_relevant_topics = []
        
        print(f"\n🔍 Analyzing {len(self.topics)} topics for relevance...")
        
        if len(self.topics) > chunk_size:
            num_chunks = (len(self.topics) + chunk_size - 1) // chunk_size
            print(f"✂️ Splitting topics into {num_chunks} chunks...")
            
            for i in range(0, len(self.topics), chunk_size):
                chunk = self.topics[i:i + chunk_size]
                chunk_num = (i // chunk_size) + 1
                
                print(f"   📦 Processing chunk {chunk_num}/{num_chunks} ({len(chunk)} topics)...")
                
                relevant_topics = self.extract_relevant_topics_with_llm(chunk, refined_query)
                
                if relevant_topics:
                    all_relevant_topics.extend(relevant_topics)
                    print(f"   ✅ Found {len(relevant_topics)} relevant topics in chunk {chunk_num}")
                else:
                    print(f"   ℹ️ No highly relevant topics found in chunk {chunk_num}")
        else:
            print("📦 Processing all topics in single batch...")
            all_relevant_topics = self.extract_relevant_topics_with_llm(self.topics, refined_query)
        
        print(f"\n🎯 Total relevant topics found: {len(all_relevant_topics)}")
        
        if not all_relevant_topics:
            print("❌ No relevant topics found for your query.")
            print("Try running the topic extractor first or refining your learning goals.")
            return
        
        # Step 3: Create curriculum
        print(f"\n🏗️ Creating personalized curriculum...")
        curriculum = self.create_curriculum_with_llm(all_relevant_topics, refined_query)
        
        # Step 4: Save and display
        filepath = self.save_curriculum(curriculum, user_query)
        print(f"💾 Curriculum saved to: {filepath}")
        
        self.display_curriculum(curriculum)

def main():
    creator = CurriculumCreatorFallback()
    creator.run_interactive()

if __name__ == "__main__":
    main()
