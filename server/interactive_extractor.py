#!/usr/bin/env python3
"""
Interactive Topic Extractor
Extract any specific topic from the book based on the clean heading structure
"""

import os
import json
import fitz
import re
from datetime import datetime
from typing import List, Dict, Optional

try:
    from LLM import AdvancedAzureLLM
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

class InteractiveTopicExtractor:
    """Interactive tool for extracting specific topics from the book"""
    
    def __init__(self, pdf_path: str, structure_file: str):
        self.pdf_path = pdf_path
        self.structure_file = structure_file
        self.book_structure = []
        self.load_structure()
    
    def load_structure(self):
        """Load the book structure from JSON file"""
        try:
            with open(self.structure_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.book_structure = data.get('headings', [])
            print(f"✅ Loaded {len(self.book_structure)} topics from structure file")
        except Exception as e:
            print(f"❌ Failed to load structure: {e}")
    
    def search_topics(self, query: str) -> List[Dict]:
        """Search for topics matching the query"""
        query_upper = query.upper()
        matches = []
        
        for topic in self.book_structure:
            title_upper = topic['title'].upper()
            if (query_upper in title_upper or 
                any(word in title_upper for word in query_upper.split())):
                matches.append(topic)
        
        return matches
    
    def list_all_topics(self):
        """List all available topics"""
        print("\n📚 AVAILABLE TOPICS IN THE BOOK:")
        print("="*50)
        
        current_chapter = 0
        for i, topic in enumerate(self.book_structure, 1):
            # Detect new chapters
            if topic['level'] == 1 and re.match(r'^\d+\s', topic['title']):
                chapter_num = int(topic['title'].split()[0])
                if chapter_num != current_chapter:
                    current_chapter = chapter_num
                    print(f"\n📖 CHAPTER {chapter_num}:")
            
            indent = "  " * (topic['level'] - 1)
            if topic['level'] == 1:
                print(f"{i:3d}. 📖 {topic['title']} (Page {topic['page']})")
            else:
                print(f"{i:3d}. {indent}📝 {topic['title']} (Page {topic['page']})")
        
        print(f"\nTotal: {len(self.book_structure)} topics available")
    
    def extract_topic_content(self, topic_index: int) -> Optional[str]:
        """Extract content for a specific topic by index"""
        if not (0 <= topic_index < len(self.book_structure)):
            return None
        
        topic = self.book_structure[topic_index]
        
        # Determine page range
        start_page = topic['page']
        end_page = start_page + 5  # Default to 5 pages
        
        # Try to find the next topic at same or higher level for better end page
        for next_topic in self.book_structure[topic_index + 1:]:
            if next_topic['level'] <= topic['level']:
                end_page = next_topic['page'] - 1
                break
        
        print(f"📄 Extracting content from pages {start_page}-{end_page}...")
        
        # Extract text from the page range
        content_parts = []
        
        try:
            with fitz.open(self.pdf_path) as doc:
                for page_num in range(start_page - 1, min(end_page, doc.page_count)):
                    page = doc[page_num]
                    page_text = page.get_text()
                    
                    if page_text.strip():
                        content_parts.append(f"--- Page {page_num + 1} ---\n{page_text.strip()}")
        
        except Exception as e:
            print(f"❌ Error extracting content: {e}")
            return None
        
        return "\n\n".join(content_parts)
    
    def generate_materials(self, topic_title: str, content: str):
        """Generate study materials using LLM"""
        if not LLM_AVAILABLE:
            print("⚠️  LLM not available for material generation")
            return None, None
        
        try:
            llm = AdvancedAzureLLM()
            
            # Generate theory notes
            theory_prompt = f"""Create comprehensive theory notes for the topic "{topic_title}" based on the following textbook content:

{content[:3000]}  # Limit content length

Please provide:
1. **Key Concepts and Definitions**
2. **Mathematical Foundations** (if applicable)
3. **Important Principles and Properties**
4. **Practical Applications** (if mentioned)
5. **Summary Points for Quick Review**

Format with clear headers and bullet points. Focus on making concepts clear and understandable."""

            theory_notes = llm.gpt_4_1_mini(
                theory_prompt,
                system_message="You are an expert instructor. Create clear, well-structured study notes that help students understand the concepts."
            )
            
            # Generate practice quiz
            quiz_prompt = f"""Create a practice quiz for the topic "{topic_title}" based on the following content:

{content[:3000]}

Generate:
**MULTIPLE CHOICE (3 questions)**
- 4 options each (A, B, C, D)
- Test understanding of key concepts

**SHORT ANSWER (2 questions)**  
- Test conceptual understanding
- Require 2-3 sentence explanations

**PROBLEMS (1-2 questions if applicable)**
- Test application of concepts

Include an **ANSWER KEY** with explanations.

Base all questions strictly on the provided content."""

            quiz = llm.gpt_4_1_mini(
                quiz_prompt,
                system_message="You are an expert quiz creator. Generate fair questions that test multiple cognitive levels based on the provided material."
            )
            
            return theory_notes, quiz
            
        except Exception as e:
            print(f"❌ Error generating materials: {e}")
            return None, None
    
    def save_extracted_content(self, topic: Dict, content: str, theory_notes: str = None, quiz: str = None):
        """Save all extracted content and generated materials"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = re.sub(r'[^\w\s-]', '', topic['title']).strip()
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        
        output_dir = "./output/extracted_topics"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save raw content
        content_file = os.path.join(output_dir, f"{safe_title}_content_{timestamp}.txt")
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(f"EXTRACTED CONTENT: {topic['title']}\n")
            f.write("="*60 + "\n")
            f.write(f"Page: {topic['page']}\n")
            f.write(f"Level: {topic['level']}\n")
            f.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            f.write(content)
        
        files_created = [content_file]
        
        # Save theory notes if available
        if theory_notes:
            theory_file = os.path.join(output_dir, f"{safe_title}_theory_{timestamp}.txt")
            with open(theory_file, 'w', encoding='utf-8') as f:
                f.write(f"THEORY NOTES: {topic['title']}\n")
                f.write("="*60 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                f.write(theory_notes)
            files_created.append(theory_file)
        
        # Save quiz if available
        if quiz:
            quiz_file = os.path.join(output_dir, f"{safe_title}_quiz_{timestamp}.txt")
            with open(quiz_file, 'w', encoding='utf-8') as f:
                f.write(f"PRACTICE QUIZ: {topic['title']}\n")
                f.write("="*60 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                f.write(quiz)
            files_created.append(quiz_file)
        
        return files_created
    
    def interactive_mode(self):
        """Run interactive topic extraction"""
        print("🎯 INTERACTIVE TOPIC EXTRACTOR")
        print("="*40)
        print("Choose a topic to extract from the book!")
        print("="*40)
        
        while True:
            print("\n📋 OPTIONS:")
            print("1. 📚 List all available topics")
            print("2. 🔍 Search for topics")
            print("3. 📖 Extract topic by number")
            print("4. 🚪 Exit")
            
            choice = input("\n👉 Enter your choice (1-4): ").strip()
            
            if choice == "1":
                self.list_all_topics()
                
            elif choice == "2":
                query = input("\n🔍 Enter search terms: ").strip()
                if query:
                    matches = self.search_topics(query)
                    if matches:
                        print(f"\n📋 Found {len(matches)} matching topics:")
                        for i, match in enumerate(matches, 1):
                            print(f"{i:2d}. {match['title']} (Page {match['page']})")
                    else:
                        print("❌ No matching topics found")
                        
            elif choice == "3":
                try:
                    topic_num = int(input(f"\n📖 Enter topic number (1-{len(self.book_structure)}): "))
                    topic_index = topic_num - 1
                    
                    if 0 <= topic_index < len(self.book_structure):
                        topic = self.book_structure[topic_index]
                        print(f"\n🎯 Extracting: {topic['title']}")
                        
                        # Extract content
                        content = self.extract_topic_content(topic_index)
                        
                        if content:
                            print(f"✅ Content extracted ({len(content)} characters)")
                            
                            # Generate materials if LLM available
                            theory_notes = None
                            quiz = None
                            
                            if LLM_AVAILABLE:
                                generate = input("\n🤖 Generate study materials? (y/n): ").strip().lower()
                                if generate == 'y':
                                    print("📚 Generating theory notes...")
                                    theory_notes, quiz = self.generate_materials(topic['title'], content)
                                    
                                    if theory_notes:
                                        print("✅ Theory notes generated")
                                    if quiz:
                                        print("✅ Practice quiz generated")
                            
                            # Save everything
                            files = self.save_extracted_content(topic, content, theory_notes, quiz)
                            
                            print(f"\n💾 Files saved:")
                            for file_path in files:
                                print(f"  📄 {os.path.basename(file_path)}")
                            
                            print(f"\n📁 All files saved to: {os.path.dirname(files[0])}")
                        
                        else:
                            print("❌ Failed to extract content")
                    else:
                        print("❌ Invalid topic number")
                        
                except ValueError:
                    print("❌ Please enter a valid number")
                    
            elif choice == "4":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-4.")

def main():
    """Main execution"""
    pdf_path = "./doc/book.pdf"
    
    # Find the latest structure file
    structure_files = [f for f in os.listdir("./output") if f.startswith("book_structure_clean_") and f.endswith(".json")]
    
    if not structure_files:
        print("❌ No book structure file found!")
        print("   Please run extract_clean_headings.py first to generate the book structure.")
        return
    
    # Use the latest structure file
    structure_file = os.path.join("./output", sorted(structure_files)[-1])
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print(f"📖 PDF: {pdf_path}")
    print(f"📊 Structure: {structure_file}")
    
    extractor = InteractiveTopicExtractor(pdf_path, structure_file)
    
    if not extractor.book_structure:
        print("❌ Failed to load book structure")
        return
    
    # Run interactive mode
    extractor.interactive_mode()

if __name__ == "__main__":
    main()
