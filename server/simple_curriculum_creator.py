"""
Simple Curriculum Creator
=========================
A simpler version of the curriculum creator for testing and demonstration.
Works with extracted topics to create basic curricula.

Usage:
    python simple_curriculum_creator.py
"""

import json
import os
import sys
import math
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple

class SimpleCurriculumCreator:
    def __init__(self):
        """Initialize the simple curriculum creator"""
        self.max_topics_per_chunk = 50
        self.output_dir = "curriculum_output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_user_query(self) -> str:
        """Get user's learning query/goal"""
        print("\n🎓 Simple Curriculum Creator")
        print("=" * 35)
        print("Tell me what you want to learn!")
        print("\nExamples:")
        print("  • probability")
        print("  • statistics")  
        print("  • random variables")
        print("  • hypothesis testing")
        
        while True:
            user_query = input("\n💭 What would you like to learn? ").strip().lower()
            if len(user_query) >= 3:
                return user_query
            else:
                print("❌ Please provide a valid topic (at least 3 characters)")
    
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
    
    def find_relevant_topics(self, topics: List[Dict], user_query: str) -> List[Dict]:
        """Find topics relevant to user query using keyword matching"""
        
        print(f"\n🔍 Searching for topics related to '{user_query}'...")
        
        # Split user query into keywords
        query_keywords = user_query.lower().split()
        
        relevant_topics = []
        
        for topic in topics:
            topic_text = topic['topic'].lower()
            
            # Calculate relevance score based on keyword matches
            relevance_score = 0
            
            for keyword in query_keywords:
                if keyword in topic_text:
                    relevance_score += 2  # Exact match
                elif any(keyword in word for word in topic_text.split()):
                    relevance_score += 1  # Partial match
            
            # Add bonus for specific statistical terms
            bonus_keywords = {
                'expectation': ['expectation', 'expected', 'mean', 'average'],
                'probability': ['probability', 'prob', 'chance', 'likelihood'], 
                'statistics': ['statistics', 'statistical', 'stat', 'data'],
                'random': ['random', 'variable', 'distribution'],
                'variance': ['variance', 'deviation', 'spread'],
                'hypothesis': ['hypothesis', 'test', 'testing'],
                'regression': ['regression', 'correlation', 'linear'],
                'sampling': ['sampling', 'sample', 'population']
            }
            
            for query_key, bonus_words in bonus_keywords.items():
                if query_key in user_query:
                    for bonus_word in bonus_words:
                        if bonus_word in topic_text:
                            relevance_score += 1
            
            # Only include topics with some relevance
            if relevance_score > 0:
                relevant_topics.append({
                    'topic': topic['topic'],
                    'page': topic['page'],
                    'source': topic.get('source', 'content'),
                    'relevance_score': relevance_score,
                    'relevance_reason': f"Matched keywords related to '{user_query}'"
                })
        
        # Sort by relevance score
        relevant_topics.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        print(f"✅ Found {len(relevant_topics)} relevant topics!")
        
        # Show top topics
        if relevant_topics:
            print(f"\n🏆 Most relevant topics:")
            for i, topic in enumerate(relevant_topics[:10], 1):
                print(f"  {i:2d}. {topic['topic']} (Score: {topic['relevance_score']})")
        
        return relevant_topics
    
    def create_simple_curriculum(self, user_query: str, relevant_topics: List[Dict]) -> Dict:
        """Create a simple curriculum structure"""
        
        print(f"\n🏗️ Creating curriculum for '{user_query}'...")
        
        if not relevant_topics:
            return {
                "curriculum_title": f"Learning Path: {user_query.title()}",
                "description": f"No specific topics found for {user_query}. Consider a broader search.",
                "modules": [],
                "total_topics": 0
            }
        
        # Organize topics into modules based on relevance and content
        high_relevance = [t for t in relevant_topics if t['relevance_score'] >= 3]
        medium_relevance = [t for t in relevant_topics if 1 <= t['relevance_score'] < 3]
        
        modules = []
        
        # Module 1: Core Topics (high relevance)
        if high_relevance:
            modules.append({
                "module_number": 1,
                "title": f"Core {user_query.title()} Concepts",
                "duration": "2-3 weeks",
                "topic_count": len(high_relevance),
                "topics": [f"{t['topic']} (Page {t['page']})" for t in high_relevance[:15]],  # Limit to top 15
                "description": f"Fundamental concepts directly related to {user_query}"
            })
        
        # Module 2: Supporting Topics (medium relevance)  
        if medium_relevance:
            modules.append({
                "module_number": 2,
                "title": f"Advanced {user_query.title()} Topics",
                "duration": "2-4 weeks", 
                "topic_count": len(medium_relevance),
                "topics": [f"{t['topic']} (Page {t['page']})" for t in medium_relevance[:15]],  # Limit to top 15
                "description": f"Advanced and related topics to deepen your understanding of {user_query}"
            })
        
        curriculum = {
            "curriculum_title": f"Comprehensive {user_query.title()} Learning Path",
            "description": f"A structured curriculum covering {len(relevant_topics)} topics related to {user_query}",
            "modules": modules,
            "total_topics": len(relevant_topics),
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return curriculum
    
    def save_curriculum(self, curriculum: Dict, user_query: str, relevant_topics: List[Dict]) -> str:
        """Save curriculum to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_file = os.path.join(self.output_dir, f"simple_curriculum_{timestamp}.json")
        output_data = {
            "user_query": user_query,
            "curriculum": curriculum,
            "relevant_topics": relevant_topics
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Save readable markdown
        md_file = os.path.join(self.output_dir, f"simple_curriculum_{timestamp}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# {curriculum['curriculum_title']}\n\n")
            f.write(f"**Created:** {curriculum['created']}\n")
            f.write(f"**Query:** {user_query}\n")
            f.write(f"**Total Relevant Topics:** {curriculum['total_topics']}\n\n")
            
            f.write(f"## 📖 Description\n\n")
            f.write(f"{curriculum['description']}\n\n")
            
            f.write(f"## 📚 Learning Modules\n\n")
            
            for module in curriculum['modules']:
                f.write(f"### Module {module['module_number']}: {module['title']}\n\n")
                f.write(f"**Duration:** {module['duration']}\n")
                f.write(f"**Topic Count:** {module['topic_count']}\n")
                f.write(f"**Description:** {module['description']}\n\n")
                
                f.write("**Topics to Study:**\n")
                for topic in module['topics']:
                    f.write(f"- {topic}\n")
                f.write("\n")
            
            f.write(f"## 📋 All Relevant Topics ({len(relevant_topics)} total)\n\n")
            for i, topic in enumerate(relevant_topics, 1):
                f.write(f"{i:3d}. {topic['topic']} (Page {topic['page']}, Score: {topic['relevance_score']})\n")
        
        print(f"\n💾 Curriculum saved:")
        print(f"   📄 JSON: {json_file}")
        print(f"   📋 Markdown: {md_file}")
        
        return md_file
    
    def display_curriculum_summary(self, curriculum: Dict):
        """Display curriculum summary"""
        
        print(f"\n🎉 Your Curriculum is Ready!")
        print("=" * 35)
        print(f"\n📚 {curriculum['curriculum_title']}")
        print(f"📝 {curriculum['description']}")
        
        if curriculum['modules']:
            print(f"\n📊 Modules:")
            for module in curriculum['modules']:
                print(f"   📖 {module['title']}")
                print(f"      ⏱️ Duration: {module['duration']}")
                print(f"      📋 Topics: {module['topic_count']}")
                print()

def main():
    """Main workflow"""
    try:
        # Initialize creator
        creator = SimpleCurriculumCreator()
        
        # Get user query
        user_query = creator.get_user_query()
        
        # Load topics
        topics = creator.load_extracted_topics()
        
        # Find relevant topics
        relevant_topics = creator.find_relevant_topics(topics, user_query)
        
        if not relevant_topics:
            print("\n❌ No relevant topics found for your query.")
            print("Try a different search term or run topic extraction first.")
            return
        
        # Create curriculum
        curriculum = creator.create_simple_curriculum(user_query, relevant_topics)
        
        # Save and display
        markdown_file = creator.save_curriculum(curriculum, user_query, relevant_topics)
        creator.display_curriculum_summary(curriculum)
        
        print(f"\n🎓 Complete curriculum available at: {markdown_file}")
        
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
