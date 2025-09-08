#!/usr/bin/env python3
"""
Complete Learning Pathway Workflow
==================================

This script provides an end-to-end workflow for creating personalized learning paths:
1. Extract topics from PDF textbooks
2. Create curriculum based on user query
3. Extract specific pages for the curriculum
4. Generate a focused study PDF

Usage:
    python complete_workflow.py

Interactive workflow that guides users through the entire process.
"""

import os
import sys
import subprocess
from datetime import datetime
from typing import List, Dict


class CompleteWorkflow:
    """Complete workflow manager for learning pathway creation"""
    
    def __init__(self):
        self.doc_dir = "doc"
        self.output_dir = "output"
        
    def get_available_pdfs(self) -> List[str]:
        """Get list of available PDF files"""
        pdfs = []
        if os.path.exists(self.doc_dir):
            for file in os.listdir(self.doc_dir):
                if file.lower().endswith('.pdf'):
                    pdfs.append(file)
        return sorted(pdfs)
    
    def get_available_topics(self) -> List[str]:
        """Get list of available topic extraction files"""
        topics = []
        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                if file.endswith("_optimized_universal_") and file.endswith(".json"):
                    topics.append(file)
        return sorted(topics)
    
    def run_topic_extraction(self, pdf_file: str) -> bool:
        """Run topic extraction on PDF file"""
        pdf_path = os.path.join(self.doc_dir, pdf_file)
        print(f"\n🔍 Extracting topics from {pdf_file}...")
        
        try:
            result = subprocess.run(
                [sys.executable, "optimized_universal_extractor.py", pdf_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print("✅ Topic extraction completed successfully!")
                # Show last few lines of output
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines[-5:]:
                    if line.strip():
                        print(f"   {line}")
                return True
            else:
                print(f"❌ Topic extraction failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Topic extraction timed out")
            return False
        except Exception as e:
            print(f"❌ Error running topic extraction: {e}")
            return False
    
    def run_curriculum_creation(self, query: str) -> str:
        """Run curriculum creation with given query"""
        print(f"\n📚 Creating curriculum for: '{query}'...")
        
        try:
            result = subprocess.run(
                [sys.executable, "curriculum_creator_fallback.py"],
                input=query + "\n",
                capture_output=True,
                text=True,
                timeout=180  # 3 minute timeout
            )
            
            if result.returncode == 0:
                print("✅ Curriculum creation completed!")
                
                # Extract curriculum filename from output
                output_lines = result.stdout.strip().split('\n')
                curriculum_file = None
                
                for line in output_lines:
                    if "Curriculum saved to:" in line:
                        # Extract filename from path
                        path = line.split(":")[-1].strip()
                        curriculum_file = os.path.basename(path)
                        break
                
                # Show summary
                in_summary = False
                for line in output_lines:
                    if "Learning Path:" in line:
                        in_summary = True
                    if in_summary and ("✨" in line or "Curriculum ready" in line):
                        break
                    if in_summary:
                        print(f"   {line}")
                
                return curriculum_file
            else:
                print(f"❌ Curriculum creation failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ Curriculum creation timed out")
            return None
        except Exception as e:
            print(f"❌ Error running curriculum creation: {e}")
            return None
    
    def run_page_extraction(self, curriculum_file: str) -> str:
        """Run page extraction for curriculum"""
        print(f"\n📄 Extracting pages for curriculum: {curriculum_file}...")
        
        try:
            # Run page extractor with curriculum file selection (select option 1)
            result = subprocess.run(
                [sys.executable, "curriculum_page_extractor.py"],
                input="1\ny\n",  # Select curriculum 1, confirm extraction
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode == 0:
                print("✅ Page extraction completed!")
                
                # Extract PDF filename from output
                output_lines = result.stdout.strip().split('\n')
                pdf_file = None
                
                for line in output_lines:
                    if "Successfully created:" in line:
                        pdf_file = line.split(":")[-1].strip()
                        break
                
                # Show extraction summary
                in_summary = False
                for line in output_lines:
                    if "Curriculum Page Extraction Summary" in line:
                        in_summary = True
                    if in_summary and ("💾 Summary saved" in line):
                        print(f"   {line}")
                        break
                    if in_summary:
                        print(f"   {line}")
                
                return pdf_file
            else:
                print(f"❌ Page extraction failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ Page extraction timed out")
            return None
        except Exception as e:
            print(f"❌ Error running page extraction: {e}")
            return None
    
    def interactive_workflow(self):
        """Main interactive workflow"""
        print("🎓 Complete Learning Pathway Workflow")
        print("=" * 60)
        print("Create personalized learning paths from PDF textbooks!")
        print()
        
        # Check if topic extraction is needed
        available_pdfs = self.get_available_pdfs()
        available_topics = self.get_available_topics()
        
        if not available_pdfs:
            print("❌ No PDF files found in 'doc' directory")
            print("   Please add PDF textbooks to the 'doc' folder")
            return
        
        print(f"📚 Found {len(available_pdfs)} PDF file(s):")
        for i, pdf in enumerate(available_pdfs, 1):
            print(f"   {i}. {pdf}")
        print()
        
        # Step 1: Topic Extraction
        if not available_topics:
            print("🔍 No topic extractions found. Let's extract topics first!")
            print()
            
            # Select PDF
            try:
                pdf_choice = input("📖 Select PDF for topic extraction (number): ").strip()
                pdf_index = int(pdf_choice) - 1
                
                if 0 <= pdf_index < len(available_pdfs):
                    selected_pdf = available_pdfs[pdf_index]
                else:
                    print("❌ Invalid selection")
                    return
            except ValueError:
                print("❌ Please enter a valid number")
                return
            
            # Extract topics
            if not self.run_topic_extraction(selected_pdf):
                print("❌ Cannot proceed without topic extraction")
                return
        else:
            print(f"✅ Found {len(available_topics)} existing topic extraction(s)")
            for i, topics_file in enumerate(available_topics, 1):
                # Extract readable name
                name = topics_file.replace("_optimized_universal_", " ").replace(".json", "")
                print(f"   {i}. {name}")
            print()
            
            use_existing = input("🔄 Use existing topic extraction? (y/n): ").strip().lower()
            if use_existing != 'y':
                # Select PDF for new extraction
                try:
                    pdf_choice = input("📖 Select PDF for new topic extraction (number): ").strip()
                    pdf_index = int(pdf_choice) - 1
                    
                    if 0 <= pdf_index < len(available_pdfs):
                        selected_pdf = available_pdfs[pdf_index]
                    else:
                        print("❌ Invalid selection")
                        return
                except ValueError:
                    print("❌ Please enter a valid number")
                    return
                
                # Extract topics
                if not self.run_topic_extraction(selected_pdf):
                    print("❌ Cannot proceed without topic extraction")
                    return
        
        # Step 2: Curriculum Creation
        print("\n" + "=" * 40)
        print("📚 STEP 2: Curriculum Creation")
        print("=" * 40)
        
        learning_query = input("\n💭 What would you like to learn? ").strip()
        
        if not learning_query:
            print("❌ Please provide a learning topic")
            return
        
        curriculum_file = self.run_curriculum_creation(learning_query)
        if not curriculum_file:
            print("❌ Cannot proceed without curriculum")
            return
        
        # Step 3: Page Extraction
        print("\n" + "=" * 40)
        print("📄 STEP 3: Page Extraction")
        print("=" * 40)
        
        extract_pages = input("\n📄 Extract specific pages for this curriculum? (y/n): ").strip().lower()
        
        if extract_pages == 'y':
            pdf_file = self.run_page_extraction(curriculum_file)
            if pdf_file:
                print(f"\n🎉 COMPLETE! Your personalized learning materials are ready:")
                print(f"   📚 Curriculum: {curriculum_file}")
                print(f"   📄 Study PDF: {pdf_file}")
            else:
                print(f"\n⚠️ Curriculum created but page extraction failed:")
                print(f"   📚 Curriculum: {curriculum_file}")
        else:
            print(f"\n✅ Curriculum created successfully:")
            print(f"   📚 Curriculum: {curriculum_file}")
        
        print(f"\n📁 All files saved in: {self.output_dir}/")
        print("✨ Happy learning! 🚀")


def main():
    """Main function"""
    workflow = CompleteWorkflow()
    workflow.interactive_workflow()


if __name__ == "__main__":
    main()
