"""
Curriculum Creation Workflow
===========================
A comprehensive system that takes user queries, refines them using LLM,
and creates customized curricula from extracted book topics.

Workflow:
1. Take user query as input
2. Refine query using GPT-5 LLM
3. Load extracted topics from book
4. Split topics into manageable chunks if too large
5. Extract relevant topics from each chunk using LLM
6. Combine all relevant topics
7. Create final curriculum based on refined query and relevant topics

Usage:
    python curriculum_creator.py
"""

import json
import os
import sys
import math
from datetime import datetime
from typing import List, Dict, Any, Tuple
from LLM import AdvancedAzureLLM

class CurriculumCreator:
    def __init__(self):
        """Initialize the curriculum creator with LLM"""
        self.llm = AdvancedAzureLLM()
        self.max_topics_per_chunk = 50  # Maximum topics to process in one chunk
        self.output_dir = "curriculum_output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_user_query(self) -> str:
        """Get user's learning query/goal"""
        print("\n🎓 Curriculum Creator - Personalized Learning Path Generator")
        print("=" * 65)
        print("Tell me what you want to learn, and I'll create a custom curriculum for you!")
        print("\nExamples:")
        print("  • 'I want to learn probability and statistics for data science'")
        print("  • 'Teach me signal processing fundamentals for audio engineering'")  
        print("  • 'I need to understand linear systems for control engineering'")
        print("  • 'Help me learn random variables and distributions'")
        
        while True:
            user_query = input("\n💭 What would you like to learn? ").strip()
            if len(user_query) >= 10:
                return user_query
            else:
                print("❌ Please provide a more detailed description (at least 10 characters)")
    
    def refine_query_with_llm(self, user_query: str) -> Dict[str, str]:
        """Use GPT-5 to refine and analyze the user query"""
        print("\n🤖 Refining your query with GPT-5...")
        
        system_prompt = """
        You are an expert educational consultant and curriculum designer. Your task is to analyze and refine student learning queries to create better educational outcomes.

        Given a user's learning query, you should:
        1. REFINE the query to be more specific and educational
        2. IDENTIFY the key learning objectives
        3. SUGGEST the appropriate learning level (beginner/intermediate/advanced)
        4. DETERMINE the estimated learning duration
        5. LIST the prerequisite knowledge needed

        Respond in JSON format with these fields:
        - "refined_query": A more specific and educational version of the original query
        - "learning_objectives": List of 3-5 specific learning goals
        - "level": "beginner", "intermediate", or "advanced" 
        - "duration": Estimated time to complete (e.g., "4-6 weeks", "2-3 months")
        - "prerequisites": List of prerequisite topics/knowledge
        - "focus_areas": Key subject areas to emphasize
        """
        
        user_prompt = f"""
        Original user query: "{user_query}"
        
        Please analyze and refine this learning query according to the instructions.
        """
        
        try:
            response = self.llm.gpt_5(
                user_prompt, 
                system_message=system_prompt,
                temperature=0.7
            )
            
            # Parse JSON response
            refined_data = json.loads(response)
            print(f"✅ Query refined successfully!")
            
            # Display refined information
            print(f"\n📝 Refined Query: {refined_data['refined_query']}")
            print(f"🎯 Level: {refined_data['level'].title()}")
            print(f"⏱️ Duration: {refined_data['duration']}")
            print(f"🎓 Learning Objectives:")
            for i, obj in enumerate(refined_data['learning_objectives'], 1):
                print(f"   {i}. {obj}")
            
            return refined_data
            
        except Exception as e:
            print(f"❌ Error refining query: {e}")
            # Return basic refined data as fallback
            return {
                "refined_query": user_query,
                "learning_objectives": ["Master the requested topic"],
                "level": "intermediate", 
                "duration": "4-6 weeks",
                "prerequisites": ["Basic mathematics"],
                "focus_areas": ["Core concepts"]
            }
    
    def load_extracted_topics(self, topics_file_path: str = None) -> List[Dict]:
        """Load previously extracted topics from JSON file"""
        
        # If no file specified, look for the most recent extraction
        if not topics_file_path:
            output_dir = "output"
            if not os.path.exists(output_dir):
                raise FileNotFoundError("No output directory found. Please run topic extraction first.")
            
            # Find most recent optimized universal extraction
            json_files = [f for f in os.listdir(output_dir) if f.endswith('.json') and 'optimized_universal' in f]
            if not json_files:
                # Fallback to any recent extraction file
                json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
            
            if not json_files:
                raise FileNotFoundError("No topic extraction files found. Please run topic extraction first.")
            
            # Use the most recent file (sort by filename which includes timestamp)
            topics_file_path = os.path.join(output_dir, sorted(json_files)[-1])
        
        print(f"\n📚 Loading topics from: {os.path.basename(topics_file_path)}")
        
        try:
            with open(topics_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if 'topics' in data:
                topics = data['topics']
            elif 'metadata' in data and 'topics' in data:
                topics = data['topics']
            else:
                topics = data  # Assume the whole file is topics
            
            print(f"✅ Loaded {len(topics)} topics successfully!")
            return topics
            
        except FileNotFoundError:
            print(f"❌ Topics file not found: {topics_file_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing topics file: {e}")
            raise
    
    def split_topics_into_chunks(self, topics: List[Dict]) -> List[List[Dict]]:
        """Split topics into manageable chunks for LLM processing"""
        if len(topics) <= self.max_topics_per_chunk:
            return [topics]
        
        chunks = []
        num_chunks = math.ceil(len(topics) / self.max_topics_per_chunk)
        
        print(f"\n✂️ Splitting {len(topics)} topics into {num_chunks} chunks...")
        
        for i in range(0, len(topics), self.max_topics_per_chunk):
            chunk = topics[i:i + self.max_topics_per_chunk]
            chunks.append(chunk)
            print(f"   📦 Chunk {len(chunks)}: {len(chunk)} topics")
        
        return chunks
    
    def extract_relevant_topics_from_chunk(self, chunk: List[Dict], refined_query_data: Dict) -> List[Dict]:
        """Use LLM to extract relevant topics from a chunk"""
        
        # Prepare topics text
        topics_text = "\n".join([
            f"{i+1}. {topic['topic']} (Page {topic['page']})" 
            for i, topic in enumerate(chunk)
        ])
        
        system_prompt = f"""
        You are an expert curriculum designer. Your task is to identify topics that are relevant to a student's learning goals.

        Student's refined learning query: "{refined_query_data['refined_query']}"
        Learning level: {refined_query_data['level']}
        Focus areas: {', '.join(refined_query_data['focus_areas'])}
        Learning objectives: {', '.join(refined_query_data['learning_objectives'])}

        From the provided list of book topics, select only those that are DIRECTLY RELEVANT to the student's learning goals. 

        Criteria for relevance:
        1. The topic directly supports one or more learning objectives
        2. The topic is appropriate for the student's level
        3. The topic relates to the focus areas
        4. The topic would help achieve the refined learning query

        Return your response as a JSON array of objects, where each object has:
        - "topic": The exact topic text
        - "page": The page number
        - "relevance_score": A score from 1-10 (10 being most relevant)
        - "relevance_reason": Brief explanation of why this topic is relevant

        Only include topics with relevance_score >= 7.
        """
        
        user_prompt = f"""
        Here are the topics to analyze:

        {topics_text}

        Please identify which topics are relevant to the student's learning goals and return them in the specified JSON format.
        """
        
        try:
            response = self.llm.gpt_5(
                user_prompt,
                system_message=system_prompt,
                temperature=0.3  # Lower temperature for more consistent topic selection
            )
            
            relevant_topics = json.loads(response)
            return relevant_topics
            
        except Exception as e:
            print(f"❌ Error extracting relevant topics from chunk: {e}")
            return []
    
    def extract_all_relevant_topics(self, topics: List[Dict], refined_query_data: Dict) -> List[Dict]:
        """Extract relevant topics from all chunks and combine them"""
        
        print(f"\n🔍 Analyzing topics for relevance to your learning goals...")
        
        # Split into chunks
        chunks = self.split_topics_into_chunks(topics)
        
        all_relevant_topics = []
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n   📦 Processing chunk {i}/{len(chunks)}...")
            
            relevant_topics = self.extract_relevant_topics_from_chunk(chunk, refined_query_data)
            
            if relevant_topics:
                all_relevant_topics.extend(relevant_topics)
                print(f"   ✅ Found {len(relevant_topics)} relevant topics in chunk {i}")
            else:
                print(f"   ℹ️ No highly relevant topics found in chunk {i}")
        
        # Sort by relevance score
        all_relevant_topics.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        print(f"\n🎯 Total relevant topics found: {len(all_relevant_topics)}")
        
        # Show top 5 most relevant topics
        if all_relevant_topics:
            print(f"\n🏆 Top 5 most relevant topics:")
            for i, topic in enumerate(all_relevant_topics[:5], 1):
                print(f"   {i}. {topic['topic']} (Score: {topic.get('relevance_score', 'N/A')})")
        
        return all_relevant_topics
    
    def create_curriculum(self, refined_query_data: Dict, relevant_topics: List[Dict]) -> Dict:
        """Create final curriculum using refined query and relevant topics"""
        
        print(f"\n🏗️ Creating your personalized curriculum...")
        
        # Prepare relevant topics text
        topics_text = "\n".join([
            f"• {topic['topic']} (Page {topic['page']}, Relevance: {topic.get('relevance_score', 'N/A')})"
            for topic in relevant_topics
        ])
        
        system_prompt = f"""
        You are a world-class curriculum designer and educational expert. Create a comprehensive, well-structured learning curriculum based on the student's refined learning goals and relevant book topics.

        Student Profile:
        - Refined Learning Query: "{refined_query_data['refined_query']}"
        - Level: {refined_query_data['level']}
        - Duration: {refined_query_data['duration']}
        - Prerequisites: {', '.join(refined_query_data['prerequisites'])}
        - Learning Objectives: {', '.join(refined_query_data['learning_objectives'])}
        - Focus Areas: {', '.join(refined_query_data['focus_areas'])}

        Create a curriculum that:
        1. Is perfectly tailored to the student's level and goals
        2. Uses the relevant topics as learning materials
        3. Follows a logical learning progression
        4. Includes practical applications and assessments
        5. Provides a clear timeline and milestones

        Respond in JSON format with:
        - "curriculum_title": A compelling title for the curriculum
        - "description": Brief overview of what the student will learn
        - "modules": Array of learning modules, each with:
          - "module_number": Module number
          - "title": Module title
          - "duration": Estimated time for this module
          - "objectives": Specific learning objectives for this module
          - "topics": Array of relevant book topics to study
          - "activities": Suggested learning activities
          - "assessment": How to assess learning for this module
        - "prerequisites_check": List of things student should know before starting
        - "success_metrics": How to measure overall success
        - "next_steps": Suggestions for further learning after completing this curriculum
        """
        
        user_prompt = f"""
        Available relevant topics from the book:
        {topics_text}

        Please create a comprehensive curriculum using these topics and the student's learning profile.
        """
        
        try:
            response = self.llm.gpt_5(
                user_prompt,
                system_message=system_prompt, 
                temperature=0.7
            )
            
            curriculum = json.loads(response)
            print(f"✅ Curriculum created successfully!")
            
            return curriculum
            
        except Exception as e:
            print(f"❌ Error creating curriculum: {e}")
            # Return basic fallback curriculum
            return {
                "curriculum_title": f"Custom Learning Path: {refined_query_data['refined_query']}",
                "description": "A personalized curriculum based on your learning goals",
                "modules": [
                    {
                        "module_number": 1,
                        "title": "Foundation Concepts",
                        "duration": "1-2 weeks",
                        "objectives": ["Understand basic concepts"],
                        "topics": [t['topic'] for t in relevant_topics[:10]],
                        "activities": ["Read relevant sections", "Practice problems"],
                        "assessment": "Quiz on key concepts"
                    }
                ],
                "prerequisites_check": refined_query_data['prerequisites'],
                "success_metrics": ["Complete all modules", "Pass assessments"],
                "next_steps": ["Advanced topics", "Practical projects"]
            }
    
    def save_curriculum(self, curriculum: Dict, refined_query_data: Dict, relevant_topics: List[Dict]) -> str:
        """Save the complete curriculum and analysis to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create comprehensive output
        output_data = {
            "generation_info": {
                "timestamp": timestamp,
                "user_query": refined_query_data.get('original_query', ''),
                "refined_query": refined_query_data['refined_query'],
                "total_relevant_topics": len(relevant_topics)
            },
            "student_profile": refined_query_data,
            "curriculum": curriculum,
            "relevant_topics": relevant_topics
        }
        
        # Save JSON file
        json_file = os.path.join(self.output_dir, f"curriculum_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Save readable markdown file
        md_file = os.path.join(self.output_dir, f"curriculum_{timestamp}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# {curriculum['curriculum_title']}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 📋 Learning Profile\n\n")
            f.write(f"**Query:** {refined_query_data['refined_query']}\n\n")
            f.write(f"**Level:** {refined_query_data['level'].title()}\n\n")
            f.write(f"**Duration:** {refined_query_data['duration']}\n\n")
            
            f.write("### 🎯 Learning Objectives\n")
            for obj in refined_query_data['learning_objectives']:
                f.write(f"- {obj}\n")
            f.write("\n")
            
            f.write("### 📚 Prerequisites\n")
            for prereq in refined_query_data['prerequisites']:
                f.write(f"- {prereq}\n")
            f.write("\n")
            
            f.write("## 📖 Curriculum Overview\n\n")
            f.write(f"{curriculum['description']}\n\n")
            
            f.write("## 🎓 Learning Modules\n\n")
            for module in curriculum['modules']:
                f.write(f"### Module {module['module_number']}: {module['title']}\n\n")
                f.write(f"**Duration:** {module['duration']}\n\n")
                
                f.write("**Objectives:**\n")
                for obj in module['objectives']:
                    f.write(f"- {obj}\n")
                f.write("\n")
                
                f.write("**Topics to Study:**\n")
                for topic in module['topics']:
                    f.write(f"- {topic}\n")
                f.write("\n")
                
                f.write("**Activities:**\n")
                for activity in module['activities']:
                    f.write(f"- {activity}\n")
                f.write("\n")
                
                f.write(f"**Assessment:** {module['assessment']}\n\n")
            
            f.write("## 📊 Success Metrics\n\n")
            for metric in curriculum['success_metrics']:
                f.write(f"- {metric}\n")
            f.write("\n")
            
            f.write("## 🚀 Next Steps\n\n")
            for step in curriculum['next_steps']:
                f.write(f"- {step}\n")
            f.write("\n")
            
            f.write("## 📚 All Relevant Topics\n\n")
            for i, topic in enumerate(relevant_topics, 1):
                f.write(f"{i:2d}. {topic['topic']} (Page {topic['page']}, Score: {topic.get('relevance_score', 'N/A')})\n")
        
        print(f"\n💾 Curriculum saved:")
        print(f"   📄 JSON: {json_file}")
        print(f"   📋 Markdown: {md_file}")
        
        return md_file
    
    def display_curriculum_summary(self, curriculum: Dict):
        """Display a nice summary of the created curriculum"""
        
        print(f"\n🎉 Your Personalized Curriculum is Ready!")
        print("=" * 55)
        print(f"\n📚 {curriculum['curriculum_title']}")
        print(f"📝 {curriculum['description']}")
        
        print(f"\n📊 Curriculum Structure:")
        total_modules = len(curriculum['modules'])
        print(f"   📖 Modules: {total_modules}")
        
        for i, module in enumerate(curriculum['modules'], 1):
            print(f"   {i:2d}. {module['title']} ({module['duration']})")
        
        print(f"\n✅ Success Criteria:")
        for metric in curriculum['success_metrics']:
            print(f"   • {metric}")
        
        print(f"\n🚀 What's Next:")
        for step in curriculum['next_steps']:
            print(f"   • {step}")

def main():
    """Main workflow function"""
    try:
        # Initialize curriculum creator
        creator = CurriculumCreator()
        
        # Step 1: Get user query
        user_query = creator.get_user_query()
        
        # Step 2: Refine query with LLM
        refined_query_data = creator.refine_query_with_llm(user_query)
        refined_query_data['original_query'] = user_query  # Keep original
        
        # Step 3: Load extracted topics
        topics = creator.load_extracted_topics()
        
        # Step 4: Extract relevant topics (handles chunking internally)
        relevant_topics = creator.extract_all_relevant_topics(topics, refined_query_data)
        
        if not relevant_topics:
            print("\n❌ No relevant topics found for your query.")
            print("Try running the topic extractor first or refining your learning goals.")
            return
        
        # Step 5: Create final curriculum
        curriculum = creator.create_curriculum(refined_query_data, relevant_topics)
        
        # Step 6: Save and display results
        markdown_file = creator.save_curriculum(curriculum, refined_query_data, relevant_topics)
        creator.display_curriculum_summary(curriculum)
        
        print(f"\n🎓 Your complete curriculum is ready!")
        print(f"📁 Check the detailed curriculum at: {markdown_file}")
        
    except KeyboardInterrupt:
        print("\n\n👋 Curriculum creation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error in curriculum creation workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
