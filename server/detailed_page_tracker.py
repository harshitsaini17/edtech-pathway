#!/usr/bin/env python3
"""
Enhanced Page Tracker - Detailed Topic Page Analysis
===================================================

This version provides detailed tracking of page selection logic and saves
comprehensive page information for every topic.

Features:
- Detailed page selection reasoning for each topic
- Save page numbers and reasoning for every topic
- Visual representation of page selection process
- Export detailed topic-page mapping
"""

import os
import json
import fitz  # PyMuPDF
from datetime import datetime
from typing import List, Dict, Set, Tuple
import argparse


class DetailedTopicPageTracker:
    """Enhanced tracker with detailed page selection logging"""
    
    def __init__(self):
        self.output_dir = "output"
        self.doc_dir = "doc"
        self.topic_page_details = []  # Store detailed info for each topic
        
    def get_available_curricula(self) -> List[str]:
        """Get list of available curriculum files"""
        curricula = []
        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                if file.startswith("curriculum_") and file.endswith(".json"):
                    curricula.append(file)
        return sorted(curricula)
    
    def load_curriculum(self, curriculum_file: str) -> Dict:
        """Load curriculum from JSON file"""
        file_path = os.path.join(self.output_dir, curriculum_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                curriculum = json.load(f)
            print(f"✅ Loaded curriculum: {curriculum.get('title', 'Unknown')}")
            return curriculum
        except Exception as e:
            print(f"❌ Error loading curriculum: {e}")
            return {}
    
    def find_source_pdf(self, curriculum_file: str) -> str:
        """Find the source PDF file with book2.pdf priority"""
        priority_names = ["book2.pdf", "book.pdf", "textbook.pdf", "document.pdf"]
        
        if os.path.exists(self.doc_dir):
            for pdf_name in priority_names:
                pdf_path = os.path.join(self.doc_dir, pdf_name)
                if os.path.exists(pdf_path):
                    print(f"📚 Using source PDF: {pdf_name}")
                    return pdf_path
        return None
    
    def analyze_page_content(self, doc: fitz.Document, page_num: int) -> Dict:
        """Analyze page content and return detailed information"""
        if page_num < 1 or page_num > len(doc):
            return {"error": "Invalid page number"}
        
        try:
            page_obj = doc[page_num - 1]  # 0-based indexing
            text = page_obj.get_text()
            text_lower = text.lower()
            
            # Count different types of content
            content_analysis = {
                "page_number": page_num,
                "text_length": len(text),
                "line_count": len(text.split('\n')),
                "word_count": len(text.split()),
                "has_math": self.detect_mathematical_content(text_lower),
                "has_examples": self.detect_examples(text_lower),
                "has_definitions": self.detect_definitions(text_lower),
                "has_theorems": self.detect_theorems(text_lower),
                "section_indicators": self.detect_section_indicators(text_lower),
                "continuation_score": 0,
                "text_preview": text[:200].replace('\n', ' ').strip()
            }
            
            return content_analysis
            
        except Exception as e:
            return {"error": f"Error analyzing page {page_num}: {e}"}
    
    def detect_mathematical_content(self, text: str) -> bool:
        """Detect mathematical content in text"""
        math_indicators = ['=', '∑', '∫', '≤', '≥', '±', 'var(', 'e(', 'σ', 'μ', 
                          'variance', 'expectation', 'mean', 'standard deviation',
                          'probability', 'distribution', 'formula', 'equation']
        return any(indicator in text for indicator in math_indicators)
    
    def detect_examples(self, text: str) -> bool:
        """Detect example content"""
        example_indicators = ['example', 'e.g.', 'for instance', 'consider', 'suppose']
        return any(indicator in text for indicator in example_indicators)
    
    def detect_definitions(self, text: str) -> bool:
        """Detect definition content"""
        def_indicators = ['definition', 'define', 'is defined as', 'we define', 'let us define']
        return any(indicator in text for indicator in def_indicators)
    
    def detect_theorems(self, text: str) -> bool:
        """Detect theorem/proof content"""
        theorem_indicators = ['theorem', 'proof', 'proposition', 'corollary', 'lemma']
        return any(indicator in text for indicator in theorem_indicators)
    
    def detect_section_indicators(self, text: str) -> List[str]:
        """Detect section break indicators"""
        section_indicators = ['chapter', 'section', '\\section', '\\chapter', 
                             'introduction', 'summary', 'conclusion']
        found = []
        for indicator in section_indicators:
            if indicator in text:
                found.append(indicator)
        return found
    
    def calculate_topic_relevance(self, page_analysis: Dict, topic_title: str) -> int:
        """Calculate how relevant a page is to a specific topic"""
        score = 0
        topic_words = topic_title.lower().split()
        topic_keywords = [word for word in topic_words if len(word) > 3]
        
        # Base content score
        if page_analysis.get('has_math', False):
            score += 2
        if page_analysis.get('has_examples', False):
            score += 2
        if page_analysis.get('has_definitions', False):
            score += 3
        if page_analysis.get('has_theorems', False):
            score += 2
        
        # Topic keyword relevance
        text_preview = page_analysis.get('text_preview', '').lower()
        for keyword in topic_keywords:
            if keyword in text_preview:
                score += 3
        
        # Section break penalty
        if page_analysis.get('section_indicators', []):
            score -= 5
        
        # Length considerations
        word_count = page_analysis.get('word_count', 0)
        if word_count < 50:  # Very short pages
            score -= 3
        elif word_count > 200:  # Substantial content
            score += 1
        
        return max(0, score)
    
    def detailed_section_detection(self, doc: fitz.Document, start_page: int, 
                                  topic_title: str, max_continuation: int = 4) -> Dict:
        """Detailed section detection with full reasoning"""
        
        detection_result = {
            "topic_title": topic_title,
            "start_page": start_page,
            "selected_pages": [],
            "page_analyses": [],
            "selection_reasoning": [],
            "total_pages": 0
        }
        
        if start_page < 1 or start_page > len(doc):
            detection_result["error"] = "Invalid start page"
            return detection_result
        
        print(f"  🔍 Analyzing topic: {topic_title[:60]}...")
        print(f"      Starting from page: {start_page}")
        
        # Analyze starting page
        start_analysis = self.analyze_page_content(doc, start_page)
        start_relevance = self.calculate_topic_relevance(start_analysis, topic_title)
        
        detection_result["selected_pages"].append(start_page)
        detection_result["page_analyses"].append(start_analysis)
        detection_result["selection_reasoning"].append(f"Base page (relevance: {start_relevance})")
        
        print(f"      📄 Page {start_page}: Base page (score: {start_relevance})")
        
        # Check continuation pages
        for i in range(1, max_continuation + 1):
            next_page = start_page + i
            
            if next_page > len(doc):
                detection_result["selection_reasoning"].append(f"Page {next_page}: Beyond document end")
                break
            
            # Analyze next page
            page_analysis = self.analyze_page_content(doc, next_page)
            relevance_score = self.calculate_topic_relevance(page_analysis, topic_title)
            
            # Decision logic
            include_page = False
            reason = ""
            
            if relevance_score >= 5:
                include_page = True
                reason = f"High relevance (score: {relevance_score})"
            elif relevance_score >= 3 and not page_analysis.get('section_indicators', []):
                include_page = True
                reason = f"Moderate relevance, no section break (score: {relevance_score})"
            elif page_analysis.get('section_indicators', []):
                include_page = False
                reason = f"Section break detected: {page_analysis['section_indicators']}"
            else:
                include_page = False
                reason = f"Low relevance (score: {relevance_score})"
            
            # Log the decision
            status = "✅ INCLUDED" if include_page else "❌ EXCLUDED"
            print(f"      📄 Page {next_page}: {status} - {reason}")
            
            detection_result["page_analyses"].append(page_analysis)
            detection_result["selection_reasoning"].append(f"Page {next_page}: {reason}")
            
            if include_page:
                detection_result["selected_pages"].append(next_page)
            else:
                # Stop at first excluded page to avoid gaps
                break
        
        detection_result["total_pages"] = len(detection_result["selected_pages"])
        
        print(f"      ✅ Selected {detection_result['total_pages']} pages: {detection_result['selected_pages']}")
        
        return detection_result
    
    def process_curriculum_with_detailed_tracking(self, curriculum: Dict, doc: fitz.Document):
        """Process entire curriculum with detailed tracking"""
        
        print("\n🔍 DETAILED TOPIC PAGE ANALYSIS")
        print("=" * 60)
        
        self.topic_page_details = []
        all_selected_pages = set()
        
        for module_idx, module in enumerate(curriculum.get('modules', []), 1):
            module_title = module.get('title', f'Module {module_idx}')
            topics = module.get('topics', [])
            pages = module.get('pages', [])
            
            print(f"\n📚 MODULE {module_idx}: {module_title}")
            print("-" * 50)
            print(f"Topics: {len(topics)}, Base pages: {len(pages)}")
            
            module_details = {
                "module_number": module_idx,
                "module_title": module_title,
                "topics": []
            }
            
            # Process each topic
            for topic_idx, topic in enumerate(topics):
                if topic_idx < len(pages):
                    base_page = pages[topic_idx]
                    
                    if isinstance(base_page, (int, str)) and str(base_page).isdigit():
                        base_page_num = int(base_page)
                        
                        if 1 <= base_page_num <= len(doc):
                            # Detailed analysis for this topic
                            topic_analysis = self.detailed_section_detection(
                                doc, base_page_num, topic
                            )
                            
                            # Add to module details
                            topic_details = {
                                "topic_index": topic_idx + 1,
                                "topic_title": topic,
                                "base_page": base_page_num,
                                "selected_pages": topic_analysis["selected_pages"],
                                "page_count": topic_analysis["total_pages"],
                                "selection_reasoning": topic_analysis["selection_reasoning"],
                                "page_analyses": topic_analysis["page_analyses"]
                            }
                            
                            module_details["topics"].append(topic_details)
                            all_selected_pages.update(topic_analysis["selected_pages"])
                        else:
                            print(f"  ❌ Topic {topic_idx + 1}: Invalid page number {base_page_num}")
                    else:
                        print(f"  ❌ Topic {topic_idx + 1}: Invalid page format {base_page}")
            
            self.topic_page_details.append(module_details)
        
        print(f"\n📊 SUMMARY")
        print("-" * 30)
        print(f"Total unique pages selected: {len(all_selected_pages)}")
        print(f"Page range: {min(all_selected_pages)} - {max(all_selected_pages)}")
        
        return all_selected_pages
    
    def save_detailed_analysis(self, curriculum: Dict, timestamp: str):
        """Save comprehensive analysis to JSON and readable text files"""
        
        base_name = "detailed_page_analysis"
        
        # Save JSON version (machine readable)
        json_filename = f"{base_name}_{timestamp}.json"
        json_path = os.path.join(self.output_dir, json_filename)
        
        analysis_data = {
            "curriculum_title": curriculum.get('title', 'Unknown'),
            "analysis_date": datetime.now().isoformat(),
            "total_modules": len(self.topic_page_details),
            "modules": self.topic_page_details
        }
        
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Detailed JSON analysis saved: {json_filename}")
        except Exception as e:
            print(f"❌ Error saving JSON analysis: {e}")
        
        # Save readable text version (human readable)
        txt_filename = f"{base_name}_{timestamp}.txt"
        txt_path = os.path.join(self.output_dir, txt_filename)
        
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"📚 DETAILED TOPIC PAGE ANALYSIS\\n")
                f.write(f"{'=' * 60}\\n\\n")
                f.write(f"Curriculum: {curriculum.get('title', 'Unknown')}\\n")
                f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
                f.write(f"Total Modules: {len(self.topic_page_details)}\\n\\n")
                
                for module in self.topic_page_details:
                    f.write(f"📚 MODULE {module['module_number']}: {module['module_title']}\\n")
                    f.write(f"{'-' * 50}\\n")
                    
                    for topic in module['topics']:
                        f.write(f"\\n📖 Topic {topic['topic_index']}: {topic['topic_title']}\\n")
                        f.write(f"   Base Page: {topic['base_page']}\\n")
                        f.write(f"   Selected Pages: {topic['selected_pages']} ({topic['page_count']} pages)\\n")
                        f.write(f"   Selection Reasoning:\\n")
                        
                        for reason in topic['selection_reasoning']:
                            f.write(f"     • {reason}\\n")
                        
                        f.write(f"\\n   📄 Page Details:\\n")
                        for page_analysis in topic['page_analyses']:
                            page_num = page_analysis['page_number']
                            f.write(f"     Page {page_num}:\\n")
                            f.write(f"       • Words: {page_analysis.get('word_count', 0)}\\n")
                            f.write(f"       • Math content: {page_analysis.get('has_math', False)}\\n")
                            f.write(f"       • Examples: {page_analysis.get('has_examples', False)}\\n")
                            f.write(f"       • Definitions: {page_analysis.get('has_definitions', False)}\\n")
                            f.write(f"       • Preview: {page_analysis.get('text_preview', 'N/A')[:100]}...\\n")
                        
                        f.write(f"\\n")
                    
                    f.write(f"\\n")
            
            print(f"💾 Readable text analysis saved: {txt_filename}")
            
        except Exception as e:
            print(f"❌ Error saving text analysis: {e}")
    
    def interactive_detailed_analysis(self):
        """Interactive workflow for detailed page analysis"""
        print("🔍 DETAILED TOPIC PAGE ANALYZER")
        print("=" * 60)
        print("Analyze page selection logic and save detailed topic-page mapping")
        print()
        
        # Get available curricula
        curricula = self.get_available_curricula()
        
        if not curricula:
            print("❌ No curriculum files found in output directory.")
            return
        
        print(f"📚 Found {len(curricula)} available curricula:")
        for i, curriculum_file in enumerate(curricula, 1):
            name = curriculum_file.replace("curriculum_", "").replace(".json", "").replace("_", " ")
            print(f"   {i:2d}. {name}")
        
        # Select curriculum
        try:
            choice = input("\\n🎯 Select curriculum (number): ").strip()
            curriculum_index = int(choice) - 1
            
            if 0 <= curriculum_index < len(curricula):
                selected_curriculum = curricula[curriculum_index]
            else:
                print("❌ Invalid selection")
                return
        except ValueError:
            print("❌ Please enter a valid number")
            return
        
        # Load curriculum
        curriculum = self.load_curriculum(selected_curriculum)
        if not curriculum:
            return
        
        # Find source PDF
        source_pdf = self.find_source_pdf(selected_curriculum)
        if not source_pdf:
            print("❌ Could not find source PDF file")
            return
        
        # Open PDF
        try:
            doc = fitz.open(source_pdf)
            print(f"📖 Source PDF: {os.path.basename(source_pdf)} ({len(doc)} pages)")
        except Exception as e:
            print(f"❌ Error opening PDF: {e}")
            return
        
        # Process curriculum with detailed tracking
        all_pages = self.process_curriculum_with_detailed_tracking(curriculum, doc)
        
        # Save detailed analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_detailed_analysis(curriculum, timestamp)
        
        doc.close()
        
        print(f"\\n🎉 ANALYSIS COMPLETE!")
        print(f"📄 Total pages identified: {len(all_pages)}")
        print(f"📁 Detailed analysis saved with timestamp: {timestamp}")


def main():
    """Main function"""
    tracker = DetailedTopicPageTracker()
    tracker.interactive_detailed_analysis()


if __name__ == "__main__":
    main()
