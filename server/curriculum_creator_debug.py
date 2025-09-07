"""
Curriculum Creator Debug Version
===============================
Debug version without fallback to identify LLM response issues.
Prints raw LLM responses and stores them for debugging.

Usage:
    python curriculum_creator_debug.py
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Set
from LLM import AdvancedAzureLLM

class CurriculumCreatorDebug:
    def __init__(self):
        self.llm = AdvancedAzureLLM()
        print("✅ LLM initialized successfully")
        
        self.topics = []
        self.debug_responses = []  # Store all LLM responses for debugging
        
        # Create debug directory
        self.debug_dir = "debug"
        os.makedirs(self.debug_dir, exist_ok=True)
    
    def save_debug_response(self, step: str, prompt: str, response: str, error: str = None):
        """Save LLM response for debugging"""
        debug_data = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "prompt": prompt,
            "response": response,
            "response_length": len(response) if response else 0,
            "error": error
        }
        
        self.debug_responses.append(debug_data)
        
        # Save to file immediately
        debug_file = os.path.join(self.debug_dir, f"llm_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n🐛 DEBUG - {step}:")
        print(f"   📝 Prompt length: {len(prompt)} characters")
        print(f"   📤 Response length: {len(response) if response else 0} characters")
        if response:
            print(f"   📤 Response preview: {response[:200]}...")
        if error:
            print(f"   ❌ Error: {error}")
    
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
    
    def refine_query_with_llm(self, user_query: str) -> str:
        """Refine user query using LLM - DEBUG VERSION"""
        print(f"\n🤖 Refining query with GPT-5...")
        
        prompt = f"""
        Refine this learning query to be more specific and educational:
        
        User Query: "{user_query}"
        
        Please expand it to include:
        - Specific learning objectives
        - Key concepts to cover
        - Practical applications
        
        Return only the refined query, no additional text.
        """
        
        try:
            print("📤 Sending query refinement request to LLM...")
            response = self.llm.gpt_5(prompt)
            
            self.save_debug_response("query_refinement", prompt, response)
            
            if not response or len(response.strip()) < 10:
                print("❌ Empty or too short LLM response for query refinement")
                return user_query
                
            print(f"✅ Query refined successfully")
            print(f"   Original: '{user_query}'")
            print(f"   Refined:  '{response.strip()[:100]}...'")
            
            return response.strip()
                
        except Exception as e:
            error_msg = str(e)
            self.save_debug_response("query_refinement", prompt, "", error_msg)
            print(f"❌ LLM query refinement failed: {e}")
            return user_query
    
    def extract_relevant_topics_with_llm(self, topics_chunk: List[Dict], query: str, chunk_num: int) -> List[Dict]:
        """Extract relevant topics using LLM - DEBUG VERSION"""
        print(f"\n🔍 Processing chunk {chunk_num} with LLM...")
        
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
        
        try:
            print(f"📤 Sending chunk {chunk_num} to LLM for topic extraction...")
            response = self.llm.gpt_5(prompt)
            
            self.save_debug_response(f"topic_extraction_chunk_{chunk_num}", prompt, response)
            
            if not response or len(response.strip()) == 0:
                print(f"❌ Empty LLM response for chunk {chunk_num}")
                return []
            
            print(f"📥 Raw LLM response for chunk {chunk_num}:")
            print(f"   Response: '{response}'")
            
            # Extract JSON from markdown code blocks if present
            json_text = response.strip()
            if json_text.startswith('```json'):
                # Remove markdown wrapper
                json_text = json_text.replace('```json', '').replace('```', '').strip()
                print(f"🔧 Removed markdown wrapper from response")
            elif json_text.startswith('```'):
                # Remove generic code block wrapper
                json_text = json_text.replace('```', '').strip()
                print(f"🔧 Removed generic code block wrapper from response")
            
            print(f"📄 Clean JSON text: '{json_text[:200]}...'")
            
            # Try to parse JSON
            try:
                relevant_topics = json.loads(json_text)
                if isinstance(relevant_topics, list):
                    print(f"✅ Successfully parsed {len(relevant_topics)} topics from chunk {chunk_num}")
                    return relevant_topics
                else:
                    print(f"❌ LLM response is not a list for chunk {chunk_num}")
                    return []
            except json.JSONDecodeError as json_error:
                print(f"❌ JSON parsing failed for chunk {chunk_num}: {json_error}")
                print(f"   Clean JSON text was: '{json_text}'")
                return []
            
        except Exception as e:
            error_msg = str(e)
            self.save_debug_response(f"topic_extraction_chunk_{chunk_num}", prompt, "", error_msg)
            print(f"❌ LLM topic extraction failed for chunk {chunk_num}: {e}")
            return []
    
    def create_curriculum_with_llm(self, relevant_topics: List[Dict], refined_query: str) -> Dict:
        """Create curriculum using LLM - DEBUG VERSION"""
        print(f"\n🏗️ Creating curriculum with LLM...")
        
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
        
        try:
            print("📤 Sending curriculum creation request to LLM...")
            response = self.llm.gpt_5(prompt)
            
            self.save_debug_response("curriculum_creation", prompt, response)
            
            if not response or len(response.strip()) == 0:
                print("❌ Empty LLM response for curriculum creation")
                return {"error": "Empty LLM response"}
            
            print(f"📥 Raw LLM response for curriculum:")
            print(f"   Response length: {len(response)} characters")
            print(f"   Response preview: '{response[:300]}...'")
            
            # Extract JSON from markdown code blocks if present
            json_text = response.strip()
            if json_text.startswith('```json'):
                # Remove markdown wrapper
                json_text = json_text.replace('```json', '').replace('```', '').strip()
                print(f"🔧 Removed markdown wrapper from curriculum response")
            elif json_text.startswith('```'):
                # Remove generic code block wrapper
                json_text = json_text.replace('```', '').strip()
                print(f"🔧 Removed generic code block wrapper from curriculum response")
            
            print(f"📄 Clean curriculum JSON text: '{json_text[:200]}...'")
            
            # Try to parse JSON
            try:
                curriculum = json.loads(json_text)
                if isinstance(curriculum, dict) and 'modules' in curriculum:
                    print(f"✅ Successfully created curriculum with {len(curriculum.get('modules', []))} modules")
                    return curriculum
                else:
                    print("❌ LLM response doesn't contain valid curriculum structure")
                    return {"error": "Invalid curriculum structure", "raw_response": response}
            except json.JSONDecodeError as json_error:
                print(f"❌ JSON parsing failed for curriculum: {json_error}")
                print(f"   Clean JSON text was: '{json_text}'")
                return {"error": f"JSON parsing failed: {json_error}", "raw_response": response}
            
        except Exception as e:
            error_msg = str(e)
            self.save_debug_response("curriculum_creation", prompt, "", error_msg)
            print(f"❌ LLM curriculum creation failed: {e}")
            return {"error": f"LLM error: {e}"}
    
    def save_curriculum(self, curriculum: Dict, query: str) -> str:
        """Save curriculum to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = re.sub(r'[^\w\s-]', '', query)[:30].replace(' ', '_')
        
        # JSON format
        filename = f"curriculum_debug_{safe_query}_{timestamp}.json"
        filepath = os.path.join("output", filename)
        
        os.makedirs("output", exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(curriculum, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def save_all_debug_data(self):
        """Save all debug responses to a single file"""
        if self.debug_responses:
            debug_file = os.path.join(self.debug_dir, f"all_llm_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(self.debug_responses, f, indent=2, ensure_ascii=False)
            print(f"💾 All debug data saved to: {debug_file}")
    
    def display_curriculum(self, curriculum: Dict):
        """Display curriculum in a user-friendly format"""
        if "error" in curriculum:
            print(f"\n❌ Curriculum Generation Failed")
            print(f"Error: {curriculum['error']}")
            if "raw_response" in curriculum:
                print(f"Raw LLM Response: {curriculum['raw_response'][:500]}...")
            return
        
        print(f"\n🎯 {curriculum.get('title', 'Generated Curriculum')}")
        print("=" * 60)
        print(f"📖 {curriculum.get('description', 'No description')}")
        print(f"📊 Total Topics: {curriculum.get('total_topics', 0)}")
        print(f"⏱️ Estimated Duration: {curriculum.get('estimated_total_duration', 'N/A')}")
        
        modules = curriculum.get('modules', [])
        if not modules:
            print("❌ No modules found in curriculum")
            return
        
        print(f"\n📚 Learning Modules ({len(modules)}):")
        print("-" * 40)
        
        for module in modules:
            print(f"\n{module.get('title', 'Untitled Module')}")
            print(f"   ⏱️ Duration: {module.get('estimated_duration', 'N/A')}")
            topics = module.get('topics', [])
            pages = module.get('pages', [])
            print(f"   📄 Topics ({len(topics)}):")
            
            for i, topic in enumerate(topics, 1):
                page = pages[i-1] if i-1 < len(pages) else 'N/A'
                print(f"      {i:2d}. {topic} (Page {page})")
        
        print("\n✨ Curriculum ready for learning!")
    
    def run_interactive(self):
        """Run the interactive curriculum creation workflow - DEBUG VERSION"""
        print("\n🐛 Curriculum Creator DEBUG VERSION - LLM Response Analysis")
        print("=" * 70)
        print("This version shows detailed LLM interactions for debugging.")
        
        # Load topics
        if not self.load_latest_topics():
            return
        
        # Get user input
        user_query = input("\n💭 What would you like to learn? ").strip()
        
        if not user_query:
            print("❌ Please provide a learning query.")
            return
        
        # Step 1: Refine query
        refined_query = self.refine_query_with_llm(user_query)
        
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
                
                print(f"\n   📦 Processing chunk {chunk_num}/{num_chunks} ({len(chunk)} topics)...")
                
                relevant_topics = self.extract_relevant_topics_with_llm(chunk, refined_query, chunk_num)
                
                if relevant_topics:
                    all_relevant_topics.extend(relevant_topics)
                    print(f"   ✅ Found {len(relevant_topics)} relevant topics in chunk {chunk_num}")
                else:
                    print(f"   ❌ No relevant topics found in chunk {chunk_num}")
        else:
            print("📦 Processing all topics in single batch...")
            all_relevant_topics = self.extract_relevant_topics_with_llm(self.topics, refined_query, 1)
        
        print(f"\n🎯 Total relevant topics found: {len(all_relevant_topics)}")
        
        if not all_relevant_topics:
            print("❌ No relevant topics found for your query.")
            self.save_all_debug_data()
            return
        
        # Step 3: Create curriculum
        curriculum = self.create_curriculum_with_llm(all_relevant_topics, refined_query)
        
        # Step 4: Save and display
        filepath = self.save_curriculum(curriculum, user_query)
        print(f"💾 Curriculum saved to: {filepath}")
        
        self.display_curriculum(curriculum)
        
        # Save all debug data
        self.save_all_debug_data()

def main():
    creator = CurriculumCreatorDebug()
    creator.run_interactive()

if __name__ == "__main__":
    main()
