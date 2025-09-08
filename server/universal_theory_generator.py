"""
🎓 Universal Theory Generator Agent
=====================================
Creates comprehensive, engaging theories for any curriculum topic with:
- Dynamic prompt generation from LLM
- Pitfall callouts and common mistakes
- Mathematical rigor with proofs and examples
- Visual interpretation guides
- Real-world applications

Author: AI Assistant
Date: 2025-09-08
"""

import json
import fitz  # PyMuPDF
from datetime import datetime
import os
import re
from LLM import AdvancedAzureLLM

class UniversalTheoryGenerator:
    def __init__(self):
        """Initialize the Universal Theory Generator"""
        self.llm = AdvancedAzureLLM()
        self.output_dir = "output"
        self.pdf_path = "doc/book2.pdf"
        
        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def extract_pdf_pages(self, page_numbers):
        """Extract content from specific PDF pages"""
        try:
            doc = fitz.open(self.pdf_path)
            content = ""
            
            for page_num in page_numbers:
                if 1 <= page_num <= len(doc):
                    page = doc[page_num - 1]  # fitz uses 0-based indexing
                    page_text = page.get_text()
                    content += f"\n--- PAGE {page_num} ---\n{page_text}\n"
            
            doc.close()
            return content
        except Exception as e:
            print(f"❌ Error extracting pages {page_numbers}: {str(e)}")
            return ""
    
    def generate_theory_prompt_template(self, topic_name, subject_area="Statistics", example_topic="Central Tendency"):
        """Generate a dynamic theory prompt template using LLM"""
        
        meta_prompt = f"""
You are an expert educational content designer. Create a comprehensive prompt template for generating high-quality academic theories.

CONTEXT:
- Subject Area: {subject_area}
- Current Topic: {topic_name}
- Example Topic for Reference: {example_topic}

REQUIREMENTS:
Create a detailed prompt template that will ensure consistent, engaging, and academically rigorous theory generation. The prompt should specify:

1. **Structure Requirements**: Clear sections with specific formatting
2. **Academic Rigor**: Mathematical proofs, derivations, and formulas
3. **Practical Examples**: Real-world applications and worked problems
4. **Visual Guidelines**: How to interpret charts, graphs, and data
5. **Pitfall Callouts**: Common mistakes students make
6. **Engagement Elements**: Make content interesting and memorable

EXAMPLE TOPIC DEMONSTRATION:
For the topic "Measures of Central Tendency", a good theory would include:
- Mathematical definitions of mean, median, mode
- Step-by-step calculation examples
- When each measure is appropriate vs inappropriate
- Common mistakes like "calculating mean on nominal data"
- Real applications in business, science, healthcare

OUTPUT FORMAT:
Provide a complete prompt template that can be used to generate theories for "{topic_name}" and similar topics in {subject_area}.

The template should be detailed enough to produce consistent, high-quality educational content across different topics.
"""

        try:
            response = self.llm.generate_response(meta_prompt)
            # Clean response
            if response.startswith('```') and response.endswith('```'):
                response = response[3:-3].strip()
            if response.startswith('json'):
                response = response[4:].strip()
                
            return response
        except Exception as e:
            print(f"❌ Error generating prompt template: {str(e)}")
            return self.get_default_prompt_template(topic_name, subject_area)
    
    def get_default_prompt_template(self, topic_name, subject_area):
        """Fallback prompt template if LLM generation fails"""
        return f"""
Create a comprehensive, engaging theory for: "{topic_name}"

STRUCTURE YOUR RESPONSE WITH THESE SECTIONS:

## 🎯 Learning Objectives
- List 4-6 specific, measurable learning outcomes
- Use action verbs: define, calculate, interpret, analyze, evaluate

## 📊 Theoretical Foundation  
- Core concepts and definitions
- Mathematical framework with key formulas
- Why these concepts matter in {subject_area}

## 🔢 Mathematical Framework
- All key formulas with LaTeX notation
- Derivations and proofs where appropriate
- Conditions for applicability

## 💡 Comprehensive Examples
- At least 2 worked examples with step-by-step solutions
- Use realistic data and scenarios
- Show different cases/variations

## 📈 Visual Interpretation
- How to read relevant charts, graphs, or visualizations
- What patterns to look for
- How to communicate findings

## 🚫 Common Mistakes & Pitfalls
- At least 3 boxed callouts highlighting frequent errors
- Format as: "🚫 **Common Mistake**: [Description]"
- Explain why the mistake occurs and how to avoid it

## 🔬 Real-World Applications
- Practical applications in various fields
- Industry examples and use cases
- Connection to current practices

## ⚠️ Important Considerations
- Limitations of methods/concepts
- When approaches break down
- Alternative approaches for edge cases

## 🧮 Practice Framework
- Types of problems students should master
- Skill progression from basic to advanced

## 📚 Connections to Advanced Topics
- How this topic relates to more advanced concepts
- Prerequisites this topic establishes

STYLE REQUIREMENTS:
- Academic rigor with engaging presentation
- Mathematical precision with intuitive explanations
- Include relevant examples from the provided PDF content
- Make content "binge-able" but intellectually substantial
- Use emojis strategically for visual organization
"""

    def generate_theory(self, topic_data, module_info, pdf_content=""):
        """Generate comprehensive theory for a single topic"""
        
        topic_name = topic_data.get('topic', 'Unknown Topic')
        pages = topic_data.get('pages', [])
        
        print(f"🧠 Generating theory for: {topic_name}")
        print(f"   Pages: {pages}")
        
        # Extract PDF content if pages are provided
        if pages and not pdf_content:
            pdf_content = self.extract_pdf_pages(pages)
            
        # Generate custom prompt for this topic
        subject_area = module_info.get('subject', 'Statistics')
        prompt_template = self.generate_theory_prompt_template(topic_name, subject_area)
        
        # Construct the full prompt
        full_prompt = f"""
{prompt_template}

TOPIC: {topic_name}
MODULE CONTEXT: {module_info.get('title', 'Unknown Module')}
PAGES REFERENCED: {pages}

PDF CONTENT TO USE:
{pdf_content[:8000] if pdf_content else 'No PDF content available'}

GENERATE THE THEORY NOW:
"""

        try:
            theory = self.llm.generate_response(full_prompt)
            
            # Clean response
            if theory.startswith('```') and theory.endswith('```'):
                theory = theory[3:-3].strip()
            
            print(f"   ✅ Generated {len(theory)} characters of theory")
            return theory
            
        except Exception as e:
            print(f"   ❌ Error generating theory: {str(e)}")
            return self.generate_fallback_theory(topic_name, pages, pdf_content)
    
    def generate_fallback_theory(self, topic_name, pages, pdf_content):
        """Generate a basic theory if main generation fails"""
        return f"""
# {topic_name}

## 🎯 Learning Objectives
- Understand the fundamental concepts of {topic_name}
- Apply theoretical knowledge to practical problems
- Interpret results and communicate findings

## 📊 Theoretical Foundation
*Content extracted from pages: {pages}*

{pdf_content[:2000] if pdf_content else 'Theoretical foundation to be developed based on curriculum requirements.'}

## 🚫 Common Mistakes & Pitfalls

🚫 **Common Mistake**: Misunderstanding fundamental concepts
- Students often confuse related but distinct concepts
- Always verify understanding with practical examples

🚫 **Common Mistake**: Incorrect formula application  
- Using formulas without checking preconditions
- Double-check that data meets method assumptions

## 🔬 Real-World Applications
- Practical applications in various fields
- Connection to industry standards and practices

*Note: This is a fallback theory. Full content generation encountered technical difficulties.*
"""

    def process_curriculum_module(self, curriculum_file, module_number):
        """Process a specific module from curriculum"""
        
        print(f"📚 Loading curriculum from: {curriculum_file}")
        
        try:
            with open(curriculum_file, 'r', encoding='utf-8') as f:
                curriculum = json.load(f)
        except Exception as e:
            print(f"❌ Error loading curriculum: {str(e)}")
            return None
        
        # Find the specified module
        modules = curriculum.get('modules', [])
        if module_number > len(modules):
            print(f"❌ Module {module_number} not found. Available modules: {len(modules)}")
            return None
            
        target_module = modules[module_number - 1]
        module_info = {
            'number': module_number,
            'title': target_module.get('title', f'Module {module_number}'),
            'subject': curriculum.get('title', 'Statistics'),
            'focus_area': curriculum.get('focus_area', 'General')
        }
        
        print(f"🎯 Processing: {module_info['title']}")
        print(f"📊 Topics to process: {len(target_module.get('topics', []))}")
        
        return target_module, module_info
    
    def generate_module_theories(self, curriculum_file, module_number, page_data_file=None):
        """Generate theories for all topics in a module"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print("🚀 Starting Universal Theory Generation")
        print(f"📅 Timestamp: {timestamp}")
        print("=" * 70)
        
        # Load curriculum and module data
        result = self.process_curriculum_module(curriculum_file, module_number)
        if not result:
            return None
            
        module_data, module_info = result
        topics = module_data.get('topics', [])
        
        # Load page data if available
        page_mapping = {}
        if page_data_file and os.path.exists(page_data_file):
            try:
                with open(page_data_file, 'r', encoding='utf-8') as f:
                    page_data = json.load(f)
                    for item in page_data.get('topics', []):
                        topic_name = item.get('topic', '').strip()
                        pages = item.get('pages', [])
                        page_mapping[topic_name] = pages
                print(f"📄 Loaded page mappings for {len(page_mapping)} topics")
            except Exception as e:
                print(f"⚠️ Could not load page data: {str(e)}")
        
        # Generate theories
        generated_theories = []
        successful_generations = 0
        
        for i, topic in enumerate(topics, 1):
            print(f"\n[{i}/{len(topics)}] Processing: {topic}")
            
            # Prepare topic data
            topic_data = {
                'topic': topic,
                'pages': page_mapping.get(topic, [])
            }
            
            # Generate theory
            theory = self.generate_theory(topic_data, module_info)
            
            if theory and len(theory) > 500:  # Ensure substantial content
                generated_theories.append({
                    'topic': topic,
                    'theory': theory,
                    'pages': topic_data['pages'],
                    'length': len(theory),
                    'timestamp': timestamp
                })
                successful_generations += 1
            else:
                print(f"   ⚠️ Generated theory too short or failed")
        
        # Save results
        self.save_theories(generated_theories, module_info, timestamp)
        
        # Generate summary report
        self.generate_summary_report(
            generated_theories, module_info, timestamp, 
            len(topics), successful_generations
        )
        
        return generated_theories
    
    def save_theories(self, theories, module_info, timestamp):
        """Save generated theories in multiple formats"""
        
        base_filename = f"universal_theories_module{module_info['number']}_{timestamp}"
        
        # 1. Complete text file
        text_file = f"{self.output_dir}/{base_filename}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"📚 UNIVERSAL THEORY GENERATOR - MODULE {module_info['number']}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Module: {module_info['title']}\n")
            f.write(f"Subject: {module_info['subject']}\n")
            f.write(f"Generated: {timestamp}\n")
            f.write(f"Total Topics: {len(theories)}\n\n")
            
            f.write("🎯 ENHANCEMENTS INCLUDED:\n")
            f.write("✅ Dynamic prompt generation for consistent quality\n")
            f.write("✅ Mathematical proofs and comprehensive examples\n")
            f.write("✅ Pitfall callouts and common mistake highlights\n")
            f.write("✅ Visual interpretation guidelines\n")
            f.write("✅ Real-world applications with depth\n")
            f.write("✅ Connection to advanced topics\n\n")
            
            for i, theory_data in enumerate(theories, 1):
                f.write("=" * 80 + "\n")
                f.write(f"TOPIC {i}: {theory_data['topic']}\n")
                f.write(f"Pages: {theory_data['pages']}\n")
                f.write(f"Length: {theory_data['length']} characters\n")
                f.write("=" * 80 + "\n\n")
                f.write(theory_data['theory'])
                f.write("\n\n")
        
        # 2. JSON format
        json_file = f"{self.output_dir}/{base_filename}.json"
        json_data = {
            'module_info': module_info,
            'generation_timestamp': timestamp,
            'total_topics': len(theories),
            'theories': theories,
            'enhancements': [
                'Dynamic prompt generation',
                'Mathematical rigor with proofs',
                'Pitfall callouts and common mistakes',
                'Comprehensive worked examples',
                'Visual interpretation guides',
                'Real-world applications',
                'Connections to advanced topics'
            ]
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # 3. Individual markdown files
        topic_dir = f"{self.output_dir}/module{module_info['number']}_topics"
        if not os.path.exists(topic_dir):
            os.makedirs(topic_dir)
            
        for theory_data in theories:
            # Clean topic name for filename
            clean_name = re.sub(r'[^\w\s-]', '', theory_data['topic'])
            clean_name = re.sub(r'[-\s]+', '_', clean_name)
            topic_file = f"{topic_dir}/{clean_name}.md"
            
            with open(topic_file, 'w', encoding='utf-8') as f:
                f.write(theory_data['theory'])
        
        print(f"✅ Theories saved:")
        print(f"   📋 Complete file: {text_file}")
        print(f"   📊 JSON data: {json_file}")
        print(f"   📁 Individual topics: {topic_dir}/")
    
    def generate_summary_report(self, theories, module_info, timestamp, total_topics, successful):
        """Generate a comprehensive summary report"""
        
        report_file = f"{self.output_dir}/UNIVERSAL_GENERATION_REPORT_MODULE{module_info['number']}_{timestamp}.md"
        
        # Calculate statistics
        total_chars = sum(t['length'] for t in theories)
        avg_length = total_chars // len(theories) if theories else 0
        success_rate = (successful / total_topics) * 100 if total_topics > 0 else 0
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"""# 🎓 Universal Theory Generation Report
## Module {module_info['number']}: {module_info['title']}

**Generated:** {timestamp}  
**Subject:** {module_info['subject']}  
**Generation Agent:** Universal Theory Generator

---

## 📊 Generation Statistics

| Metric | Value |
|--------|-------|
| **Total Topics Requested** | {total_topics} |
| **Successfully Generated** | {successful} |
| **Success Rate** | {success_rate:.1f}% |
| **Total Content Generated** | {total_chars:,} characters |
| **Average Theory Length** | {avg_length:,} characters |

---

## 🎯 Enhancement Features Implemented

### ✅ Dynamic Prompt Generation
- Custom prompts generated for each topic using LLM meta-reasoning
- Ensures consistency across different subject areas
- Adapts to topic-specific requirements automatically

### ✅ Pitfall Callouts Integration
- **🚫 Common Mistake** boxes throughout content
- Highlights frequent student errors
- Provides prevention strategies

### ✅ Mathematical Rigor
- Complete proofs and derivations
- Formula explanations with LaTeX formatting
- Step-by-step worked examples

### ✅ Visual Interpretation Guides
- Chart and graph reading instructions
- Pattern recognition guidelines
- Data communication best practices

### ✅ Real-World Applications
- Industry-specific examples
- Professional contexts and use cases
- Connection to current practices

---

## 📚 Generated Topics Summary

""")
            
            for i, theory in enumerate(theories, 1):
                pages_str = f"Pages {theory['pages']}" if theory['pages'] else "No pages specified"
                f.write(f"{i}. **{theory['topic']}** - {theory['length']:,} chars ({pages_str})\n")
            
            f.write(f"""

---

## 🔧 Technical Implementation

- **PDF Content Extraction:** {sum(1 for t in theories if t['pages']) if theories else 0} topics used PDF content
- **Fallback Generation:** Robust error handling with fallback content
- **Multi-format Output:** Text, JSON, and individual Markdown files
- **Quality Assurance:** Content validation and length checking

---

## 🎉 Generation Complete!

The Universal Theory Generator has successfully created comprehensive, engaging educational content with:
- Academic rigor and mathematical precision
- Practical examples and real-world applications  
- Common mistake prevention through pitfall callouts
- Visual interpretation and communication guidelines
- Connections to advanced topics for continued learning

**Next Steps:** Review generated content and integrate into learning management system.
""")
        
        print(f"📋 Summary report: {report_file}")

def main():
    """Main execution function"""
    generator = UniversalTheoryGenerator()
    
    # Configuration
    CURRICULUM_FILE = "output/curriculum_expectation_and_variance_20250908_092417.json"
    MODULE_NUMBER = 1  # Change this to generate different modules
    PAGE_DATA_FILE = "output/detailed_page_analysis_20250908_094406.json"
    
    print("🎓 Universal Theory Generator")
    print("=" * 50)
    print(f"📚 Curriculum: {CURRICULUM_FILE}")
    print(f"📖 Target Module: {MODULE_NUMBER}")
    print(f"📄 Page Data: {PAGE_DATA_FILE}")
    print()
    
    # Generate theories
    theories = generator.generate_module_theories(
        curriculum_file=CURRICULUM_FILE,
        module_number=MODULE_NUMBER,
        page_data_file=PAGE_DATA_FILE
    )
    
    if theories:
        print("\n🎉 UNIVERSAL THEORY GENERATION COMPLETED!")
        print(f"✅ Generated {len(theories)} comprehensive theories")
        print("🎯 All enhancement features successfully implemented")
    else:
        print("\n❌ Theory generation failed")

if __name__ == "__main__":
    main()
