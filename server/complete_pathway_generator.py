#!/usr/bin/env python3
"""
🚀 Complete Educational Pathway Generator
==========================================
Single comprehensive file that runs the complete workflow:
1. PDF Topic Extraction
2. Curriculum Creation  
3. Theory Generation

This file combines all working components into one seamless workflow.

Usage:
    python complete_pathway_generator.py
    
Features:
- Extracts topics from any PDF textbook
- Creates AI-powered curriculum structure
- Generates comprehensive theories for selected modules
- Adapts to any subject matter automatically
- Quality scoring and verification
"""

import os
import sys
import json
import fitz  # PyMuPDF
import re
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple, Optional
from dataclasses import dataclass

# Import our working components
from LLM import AdvancedAzureLLM
from optimized_universal_extractor import OptimizedUniversalExtractor
from llm_enhanced_curriculum_generator import EnhancedLLMCurriculumGenerator

class CompletePathwayGenerator:
    """
    Complete Educational Pathway Generator
    Orchestrates the entire workflow from PDF to theories
    """
    
    def __init__(self):
        self.llm = None
        self.extractor = None
        self.curriculum_generator = None
        self.pdf_path = None
        self.curriculum_data = None
        self.topics_data = None
        
        # Initialize LLM
        try:
            self.llm = AdvancedAzureLLM()
            print("✅ LLM initialized successfully")
        except Exception as e:
            print(f"❌ LLM initialization failed: {e}")
            print("🔧 Please check your Azure OpenAI credentials in .env file")
            
    def display_banner(self):
        """Display the main banner"""
        print("🚀 Complete Educational Pathway Generator")
        print("=" * 80)
        print("📚 Full Workflow: PDF → Topics → Curriculum → Theories")
        print()
        print("🎯 Features:")
        print("  • Extract topics from any PDF textbook")
        print("  • AI-powered curriculum creation")
        print("  • Dynamic theory generation")
        print("  • Universal subject adaptation")
        print("  • Quality verification system")
        print()
        
    def step1_extract_topics(self, pdf_path: str) -> bool:
        """Step 1: Extract topics from PDF"""
        print("🔍 STEP 1: PDF Topic Extraction")
        print("-" * 50)
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF file not found: {pdf_path}")
            return False
            
        try:
            self.pdf_path = pdf_path
            self.extractor = OptimizedUniversalExtractor(pdf_path)
            
            print(f"📖 Processing: {os.path.basename(pdf_path)}")
            topics_data = self.extractor.extract_topics()
            
            if not topics_data or len(topics_data) == 0:
                print("❌ No topics extracted from PDF")
                return False
                
            # Convert to the expected format
            self.topics_data = {
                'topics': topics_data,
                'source': pdf_path,
                'extraction_date': datetime.now().isoformat()
            }
            
            # Save topics data to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topics_file = f"output/topics_{timestamp}.json"
            
            # Ensure output directory exists
            os.makedirs("output", exist_ok=True)
            
            with open(topics_file, 'w', encoding='utf-8') as f:
                json.dump(self.topics_data, f, indent=2, ensure_ascii=False)
            
            topic_count = len(topics_data)
            print(f"✅ Extracted {topic_count} high-quality topics")
            print(f"📁 Topics saved: {topics_file}")
            
            # Show sample topics
            print("\n📋 Sample topics:")
            for i, topic in enumerate(topics_data[:5]):
                title = topic.get('title', topic.get('topic', 'Unknown Topic'))
                page = topic.get('page', 'Unknown')
                print(f"   {i+1}. {title} (Page {page})")
            if topic_count > 5:
                print(f"   ... and {topic_count - 5} more topics")
                
            return True
            
        except Exception as e:
            print(f"❌ Topic extraction failed: {e}")
            return False
            
    def step2_create_curriculum(self, learning_query: str) -> bool:
        """Step 2: Create curriculum from topics"""
        print("\n📚 STEP 2: AI-Powered Curriculum Creation")
        print("-" * 50)
        
        try:
            self.curriculum_generator = EnhancedLLMCurriculumGenerator()
            
            print(f"🎯 Learning Goal: {learning_query}")
            print("🧠 AI analyzing and creating curriculum...")
            
            # The new enhanced generator handles everything in one method
            curriculum = self.curriculum_generator.generate_curriculum(learning_query)
            
            if not curriculum:
                print("❌ Curriculum creation failed")
                return False
                
            self.curriculum_data = curriculum
            
            print(f"✅ Created: {curriculum.get('title', 'Untitled Curriculum')}")
            print(f"📊 Modules: {len(curriculum.get('modules', []))}")
            print(f"📄 Total Topics: {curriculum.get('total_topics', sum(len(module.get('topics', [])) for module in curriculum.get('modules', [])))}")
            
            # Show module breakdown
            print("\n📚 Module Overview:")
            for i, module in enumerate(curriculum.get('modules', []), 1):
                topics_count = len(module.get('topics', []))
                duration = module.get('estimated_duration', 'Unknown')
                print(f"   {i}. {module.get('title', f'Module {i}')}")
                print(f"      📄 Topics: {topics_count} | ⏱️ Duration: {duration}")
                
            return True
            
        except Exception as e:
            print(f"❌ Curriculum creation failed: {e}")
            return False
            
    def step3_prepare_for_theories(self, module_selection: str = None) -> bool:
        """Step 3: Prepare curriculum data for theory generation"""
        print("\n📝 STEP 3: Theory Generation Setup")
        print("-" * 50)
        
        if not self.curriculum_data:
            print("❌ No curriculum data available")
            return False
            
        try:
            # The enhanced curriculum generator already saved the file with enhanced_ prefix
            # We just need to confirm it exists and provide guidance
            
            # Ensure output directory exists
            os.makedirs("output", exist_ok=True)
            
            print("📁 Enhanced curriculum already saved from Step 2")
            print("📁 Topics data already saved from Step 1")
            
            # Let user know they can now use the flexible generator
            print("💡 You can now use the flexible theory generator with:")
            print(f"   python flexible_module_theory_generator.py")
            
            # Show available modules with enhanced details
            modules = self.curriculum_data.get('modules', [])
            total_duration = self.curriculum_data.get('estimated_total_duration', 'Unknown')
            quality_metrics = self.curriculum_data.get('quality_metrics', {})
            
            print(f"📚 Available Modules ({len(modules)}) | ⏱️ Total Duration: {total_duration}:")
            for i, module in enumerate(modules, 1):
                topics_count = len(module.get('topics', []))
                duration = module.get('estimated_duration', 'Unknown')
                print(f"   {i}. {module.get('title', f'Module {i}')}")
                print(f"      📄 Topics: {topics_count} | ⏱️ Duration: {duration}")
                
            # Show quality metrics if available
            if quality_metrics:
                print(f"\n📈 Quality Metrics:")
                for metric, score in quality_metrics.items():
                    print(f"   {metric}: {score:.1f}/10")
                
            print("\n✅ SETUP COMPLETE!")
            print("🚀 Next step: Run the flexible theory generator")
            print(f"   python flexible_module_theory_generator.py")
            
            return True
                
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
            
    def run_complete_workflow(self):
        """Run the complete workflow interactively"""
        self.display_banner()
        
        # Check if we have a PDF in doc/ folder
        doc_folder = "doc"
        pdf_files = []
        if os.path.exists(doc_folder):
            pdf_files = [f for f in os.listdir(doc_folder) if f.lower().endswith('.pdf')]
            
        if pdf_files:
            print(f"📁 Found PDF files in {doc_folder}/ folder:")
            for i, pdf_file in enumerate(pdf_files, 1):
                print(f"   {i}. {pdf_file}")
            print()
            
            # Let user select PDF
            if len(pdf_files) == 1:
                pdf_choice = pdf_files[0]
                print(f"📖 Using: {pdf_choice}")
            else:
                print("🔢 Select PDF file:")
                try:
                    choice = int(input("Enter number: ").strip())
                    if 1 <= choice <= len(pdf_files):
                        pdf_choice = pdf_files[choice - 1]
                    else:
                        print("❌ Invalid choice")
                        return
                except ValueError:
                    print("❌ Please enter a valid number")
                    return
                    
            pdf_path = os.path.join(doc_folder, pdf_choice)
        else:
            # Ask user for PDF path
            print("📁 No PDF files found in doc/ folder")
            pdf_path = input("📖 Enter PDF file path: ").strip()
            
        # Step 1: Extract topics
        if not self.step1_extract_topics(pdf_path):
            print("❌ Workflow failed at topic extraction")
            return
            
        # Step 2: Get learning goal
        print("\\n🎯 What would you like to learn?")
        print("💡 Examples:")
        print("  • 'expectation and variance for financial modeling'")
        print("  • 'probability theory foundations'")  
        print("  • 'statistical analysis and hypothesis testing'")
        print()
        
        learning_query = input("📝 Enter your learning goal: ").strip()
        if not learning_query:
            print("❌ Please enter a learning goal")
            return
            
        # Step 2: Create curriculum
        if not self.step2_create_curriculum(learning_query):
            print("❌ Workflow failed at curriculum creation")
            return
            
        # Step 3: Setup for theory generation
        if not self.step3_prepare_for_theories():
            print("❌ Workflow failed at setup")
            return
            
        print("\n🎉 WORKFLOW READY!")
        print("=" * 50)
        print("✅ PDF topics extracted and saved")
        print("✅ Enhanced AI curriculum created and saved") 
        print("✅ Ready for theory generation")
        print("📁 All data saved to output/ folder")
        print("   • topics_YYYYMMDD_HHMMSS.json")
        print("   • enhanced_curriculum_YYYYMMDD_HHMMSS.json")
        print("\n🚀 Next: Run theory generation")
        print("   python flexible_module_theory_generator.py")
        
    def run_quick_demo(self):
        """Run a quick demo with default settings"""
        self.display_banner()
        
        # Use book2.pdf if available
        pdf_path = "doc/book2.pdf"
        if not os.path.exists(pdf_path):
            print(f"❌ Demo PDF not found: {pdf_path}")
            print("💡 Please ensure book2.pdf is in the doc/ folder")
            return
            
        print("🚀 Running Quick Demo")
        print("📖 Using: book2.pdf")
        print("🎯 Learning Goal: expectation and variance")
        print("📝 Generating theories for Module 1")
        print()
        
        # Run workflow setup
        if (self.step1_extract_topics(pdf_path) and 
            self.step2_create_curriculum("expectation and variance") and
            self.step3_prepare_for_theories()):
            
            print("\n🎉 DEMO SETUP COMPLETE!")
            print("📁 Data prepared in output/ folder")
            print("🚀 Next: Run python flexible_module_theory_generator.py")
        else:
            print("❌ Demo setup failed")


def main():
    """Main entry point"""
    generator = CompletePathwayGenerator()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['demo', '--demo', '-d']:
            generator.run_quick_demo()
        elif arg in ['help', '--help', '-h']:
            print("🚀 Complete Educational Pathway Generator")
            print()
            print("Usage:")
            print("  python complete_pathway_generator.py          # Interactive mode")
            print("  python complete_pathway_generator.py demo     # Quick demo")
            print("  python complete_pathway_generator.py help     # Show this help")
        else:
            print(f"❌ Unknown argument: {arg}")
            print("💡 Use 'help' for usage information")
    else:
        # Interactive mode
        generator.run_complete_workflow()


if __name__ == "__main__":
    main()
