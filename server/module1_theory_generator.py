#!/usr/bin/env python3
"""
THEORY GENERATOR FOR MODULE 1: FOUNDATIONS OF DESCRIPTIVE STATISTICS
=====================================================================

This script generates easy-to-read, engaging theory for every topic in Module 1
by extracting content from the relevant PDF pages and using LLM to create 
user-friendly explanations.

Module 1 Topics (with their extracted pages):
1. Chapter 2 DESCRIPTIVE STATISTICS - Pages: [75, 76] 
2. 2.2 DESCRIBING DATA SETS - Pages: [77]
3. 2.2 Describing Data Sets - Pages: [83] 
4. 2.3 Summarizing Data Sets - Pages: [88, 89]
5. 2.3 SUMMARIZING DATA SETS - Pages: [112, 113]
6. 2.3.1 Sample Mean, Sample Median, and Sample Mode - Pages: [411]
7. 2.3.2 Sample Variance and Sample Standard Deviation - Pages: [542, 543]
8. 16.9 Find the (a) sample mean, and - Pages: [543]
"""

import fitz  # PyMuPDF
import json
import sys
import os
from datetime import datetime
from LLM import AdvancedAzureLLM

class Module1TheoryGenerator:
    """Generates engaging theories for Module 1 topics using extracted PDF content."""
    
    def __init__(self):
        self.pdf_path = "doc/book2.pdf"
        self.output_dir = "output"
        self.llm = AdvancedAzureLLM()
        
        # Module 1 topic mapping from detailed analysis
        self.module1_topics = {
            "Chapter 2 DESCRIPTIVE STATISTICS": {
                "pages": [75, 76],
                "description": "Introduction to descriptive statistics and data analysis"
            },
            "2.2 DESCRIBING DATA SETS": {
                "pages": [77],
                "description": "Methods for describing and presenting data sets"
            },
            "2.2 Describing Data Sets": {
                "pages": [83],
                "description": "Additional techniques for data set description"
            },
            "2.3 Summarizing Data Sets": {
                "pages": [88, 89],
                "description": "Statistical measures for summarizing data"
            },
            "2.3 SUMMARIZING DATA SETS": {
                "pages": [112, 113],
                "description": "Advanced summarization techniques"
            },
            "2.3.1 Sample Mean, Sample Median, and Sample Mode": {
                "pages": [411],
                "description": "Central tendency measures"
            },
            "2.3.2 Sample Variance and Sample Standard Deviation": {
                "pages": [542, 543],
                "description": "Measures of variability and spread"
            },
            "16.9 Find the (a) sample mean, and": {
                "pages": [543],
                "description": "Practical applications of sample mean calculations"
            }
        }
        
        self.theory_prompt_template = """
You are an expert statistics educator who creates engaging, easy-to-understand explanations. 
Your task is to generate brief theory content for a statistics topic using the provided PDF content.

TOPIC: {topic_title}
DESCRIPTION: {topic_description}

SOURCE CONTENT FROM PDF:
{pdf_content}

INSTRUCTIONS:
1. Create a brief, engaging theory explanation (200-400 words)
2. Make it easy to read and not boring - use conversational tone
3. Focus only on content that's relevant to the specific topic
4. Extract key concepts, formulas, and examples from the provided PDF content
5. Structure with clear headings and bullet points where appropriate
6. Include practical examples or applications when mentioned in the source
7. Don't add information that's not in the source material
8. Make it beginner-friendly but mathematically accurate

RESPONSE FORMAT:
# {topic_title}

## 🎯 What You'll Learn
[Brief overview of what this topic covers]

## 📚 Key Concepts
[Main concepts extracted from the PDF content]

## 🔢 Important Formulas
[Any formulas or calculations mentioned in the source]

## 💡 Real-World Applications
[Examples or applications mentioned in the source content]

## ⚡ Quick Summary
[2-3 bullet points summarizing the main takeaways]

Please generate the theory content based strictly on the provided PDF content.
"""
    
    def extract_pdf_content(self, page_numbers):
        """Extract text content from specific PDF pages."""
        try:
            doc = fitz.open(self.pdf_path)
            content = []
            
            for page_num in page_numbers:
                if page_num <= len(doc):
                    page = doc[page_num - 1]  # PyMuPDF uses 0-based indexing
                    text = page.get_text()
                    content.append(f"=== PAGE {page_num} ===\n{text}\n")
                    
            doc.close()
            return "\n".join(content)
            
        except Exception as e:
            print(f"❌ Error extracting PDF content: {e}")
            return ""
    
    def clean_pdf_content(self, raw_content):
        """Clean and prepare PDF content for LLM processing."""
        # Remove excessive whitespace and clean up formatting
        lines = raw_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('=== PAGE'):
                # Remove page numbers and headers that are just numbers
                if not line.isdigit() and len(line) > 2:
                    cleaned_lines.append(line)
        
        # Join lines and limit content length for LLM
        cleaned_content = ' '.join(cleaned_lines)
        
        # Truncate if too long (keep first 3000 characters to focus on main content)
        if len(cleaned_content) > 3000:
            cleaned_content = cleaned_content[:3000] + "... [content truncated]"
        
        return cleaned_content
    
    def generate_theory_for_topic(self, topic_title, topic_info):
        """Generate theory content for a single topic."""
        print(f"📖 Generating theory for: {topic_title}")
        print(f"   Pages: {topic_info['pages']}")
        
        # Extract PDF content
        raw_content = self.extract_pdf_content(topic_info['pages'])
        if not raw_content:
            print(f"   ❌ Failed to extract content from pages {topic_info['pages']}")
            return None
        
        # Clean content
        cleaned_content = self.clean_pdf_content(raw_content)
        print(f"   📄 Extracted {len(cleaned_content)} characters of content")
        
        # Generate theory using LLM
        prompt = self.theory_prompt_template.format(
            topic_title=topic_title,
            topic_description=topic_info['description'],
            pdf_content=cleaned_content
        )
        
        try:
            theory = self.llm.generate_response(prompt)
            print(f"   ✅ Generated {len(theory)} characters of theory")
            return theory
        except Exception as e:
            print(f"   ❌ Error generating theory: {e}")
            return None
    
    def generate_all_theories(self):
        """Generate theories for all Module 1 topics."""
        print("🚀 Starting Module 1 Theory Generation")
        print(f"📚 Processing {len(self.module1_topics)} topics")
        print("=" * 60)
        
        theories = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, (topic_title, topic_info) in enumerate(self.module1_topics.items(), 1):
            print(f"\n[{i}/{len(self.module1_topics)}] Processing: {topic_title}")
            
            theory = self.generate_theory_for_topic(topic_title, topic_info)
            if theory:
                theories[topic_title] = {
                    "theory": theory,
                    "pages": topic_info['pages'],
                    "description": topic_info['description']
                }
            else:
                print(f"   ⚠️ Skipping {topic_title} due to errors")
        
        # Save theories to files
        self.save_theories(theories, timestamp)
        
        return theories
    
    def save_theories(self, theories, timestamp):
        """Save generated theories to files."""
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save as JSON
        json_filename = f"{self.output_dir}/module1_theories_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(theories, f, indent=2, ensure_ascii=False)
        
        # Save as readable text file
        text_filename = f"{self.output_dir}/module1_theories_{timestamp}.txt"
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write("📚 MODULE 1: FOUNDATIONS OF DESCRIPTIVE STATISTICS\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Topics: {len(theories)}\n\n")
            
            for i, (topic_title, content) in enumerate(theories.items(), 1):
                f.write(f"\n{'=' * 80}\n")
                f.write(f"TOPIC {i}: {topic_title}\n")
                f.write(f"Pages: {content['pages']}\n")
                f.write(f"{'=' * 80}\n\n")
                f.write(content['theory'])
                f.write("\n\n")
        
        # Create individual topic files
        topic_dir = f"{self.output_dir}/module1_individual_theories_{timestamp}"
        os.makedirs(topic_dir, exist_ok=True)
        
        for i, (topic_title, content) in enumerate(theories.items(), 1):
            safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in topic_title)
            safe_filename = safe_filename.replace(' ', '_').lower()
            
            topic_filename = f"{topic_dir}/topic_{i:02d}_{safe_filename}.md"
            with open(topic_filename, 'w', encoding='utf-8') as f:
                f.write(content['theory'])
        
        print(f"\n✅ Results saved:")
        print(f"   📋 Complete theories: {text_filename}")
        print(f"   📊 JSON data: {json_filename}")
        print(f"   📁 Individual files: {topic_dir}")
    
    def create_theory_summary(self, theories):
        """Create a summary of all generated theories."""
        summary = []
        summary.append("📊 MODULE 1 THEORY GENERATION SUMMARY")
        summary.append("=" * 50)
        summary.append(f"Topics Processed: {len(theories)}")
        summary.append(f"Generation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append("\n📚 TOPICS OVERVIEW:")
        
        total_pages = 0
        for i, (topic_title, content) in enumerate(theories.items(), 1):
            pages = content['pages']
            total_pages += len(pages)
            summary.append(f"{i:2d}. {topic_title}")
            summary.append(f"    📄 Pages: {pages} ({len(pages)} pages)")
            summary.append(f"    📝 Theory Length: {len(content['theory'])} characters")
            summary.append("")
        
        summary.append(f"📈 STATISTICS:")
        summary.append(f"   Total Pages Processed: {total_pages}")
        summary.append(f"   Average Pages per Topic: {total_pages/len(theories):.1f}")
        summary.append(f"   Total Theory Content: {sum(len(content['theory']) for content in theories.values())} characters")
        
        return "\n".join(summary)

def main():
    """Main function to generate Module 1 theories."""
    try:
        generator = Module1TheoryGenerator()
        theories = generator.generate_all_theories()
        
        print("\n" + "=" * 60)
        print(generator.create_theory_summary(theories))
        print("=" * 60)
        print("🎉 Module 1 theory generation completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in theory generation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
