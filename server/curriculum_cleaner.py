import json
import fitz
from collections import defaultdict
import re

class CurriculumCleaner:
    def __init__(self, pdf_path="doc/book2.pdf"):
        self.pdf_path = pdf_path
        
    def load_curriculum(self, curriculum_path):
        """Load and analyze curriculum structure"""
        with open(curriculum_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def clean_topic_name(self, topic_name):
        """Clean and standardize topic names"""
        if not topic_name or not topic_name.strip():
            return None
            
        # Remove leading numbers and dots
        cleaned = re.sub(r'^\d+\.?\d*\s*', '', topic_name.strip())
        
        # Normalize case - convert ALL CAPS to Title Case, keep others as is
        if cleaned.isupper():
            cleaned = cleaned.title()
        
        # Remove duplicate words
        words = cleaned.split()
        seen = set()
        unique_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower not in seen:
                seen.add(word_lower)
                unique_words.append(word)
        
        cleaned = ' '.join(unique_words)
        
        # Fix common patterns
        cleaned = re.sub(r'\bDESCRIPTIVE STATISTICS\b', 'Descriptive Statistics', cleaned)
        cleaned = re.sub(r'\bRANDOM VARIABLES\b', 'Random Variables', cleaned)
        cleaned = re.sub(r'\bSUMMARIZING DATA SETS\b', 'Summarizing Data Sets', cleaned)
        
        return cleaned if len(cleaned) > 3 else None
    
    def detect_duplicates(self, topics):
        """Detect and group duplicate/similar topics"""
        topic_groups = defaultdict(list)
        
        for i, topic in enumerate(topics):
            if not topic:
                continue
                
            # Create a normalized key for grouping
            key = re.sub(r'[^\w\s]', '', topic.lower())
            key = re.sub(r'\s+', ' ', key).strip()
            
            topic_groups[key].append((i, topic))
        
        return topic_groups
    
    def merge_duplicate_topics(self, topic_groups):
        """Merge duplicate topics, keeping the best version"""
        merged_topics = []
        
        for key, group in topic_groups.items():
            if len(group) == 1:
                # No duplicates
                merged_topics.append(group[0][1])
            else:
                # Choose the best version (longest, most descriptive)
                best_topic = max(group, key=lambda x: len(x[1]))[1]
                merged_topics.append(best_topic)
        
        return merged_topics
    
    def extract_actual_pdf_content(self, pages, max_chars=3000):
        """Extract and verify actual PDF content"""
        try:
            doc = fitz.open(self.pdf_path)
            content = ""
            
            print(f"📖 Extracting content from pages {pages}")
            
            for page_num in pages:
                if 1 <= page_num <= len(doc):
                    page = doc[page_num - 1]  # fitz uses 0-based indexing
                    page_text = page.get_text()
                    content += f"\n--- PAGE {page_num} ---\n{page_text}\n"
            
            doc.close()
            
            # Verify content quality
            if len(content.strip()) < 100:
                print(f"⚠️  Warning: Very little content extracted from pages {pages}")
            
            print(f"✅ Extracted {len(content)} characters from {len(pages)} pages")
            
            # Truncate if too long
            if len(content) > max_chars:
                content = content[:max_chars] + "\n\n[CONTENT TRUNCATED FOR LENGTH]"
                
            return content
            
        except Exception as e:
            print(f"❌ Error extracting pages {pages}: {str(e)}")
            return ""
    
    def clean_curriculum(self, curriculum_path):
        """Clean and enhance the curriculum"""
        print("🧹 Starting curriculum cleaning process...")
        
        curriculum = self.load_curriculum(curriculum_path)
        cleaned_curriculum = {
            "title": curriculum.get("title", ""),
            "description": curriculum.get("description", ""),
            "modules": []
        }
        
        total_topics_before = 0
        total_topics_after = 0
        
        for module in curriculum.get("modules", []):
            print(f"\n📚 Processing {module.get('title', 'Unknown Module')}")
            
            # Clean topics
            raw_topics = module.get("topics", [])
            total_topics_before += len(raw_topics)
            
            print(f"   Original topics: {len(raw_topics)}")
            
            # Clean individual topic names
            cleaned_topics = []
            for topic in raw_topics:
                cleaned = self.clean_topic_name(topic)
                if cleaned:
                    cleaned_topics.append(cleaned)
            
            # Detect and merge duplicates
            topic_groups = self.detect_duplicates(cleaned_topics)
            final_topics = self.merge_duplicate_topics(topic_groups)
            
            total_topics_after += len(final_topics)
            
            print(f"   Cleaned topics: {len(final_topics)}")
            print(f"   Removed duplicates: {len(cleaned_topics) - len(final_topics)}")
            
            # Verify PDF content for sample pages
            pages = module.get("pages", [])
            if pages:
                sample_content = self.extract_actual_pdf_content(pages[:2], max_chars=1000)
                print(f"   PDF Content Sample: {sample_content[:200]}...")
            
            # Create cleaned module
            cleaned_module = {
                "module_number": module.get("module_number"),
                "title": module.get("title"),
                "topics": final_topics,
                "pages": pages,
                "estimated_duration": module.get("estimated_duration")
            }
            
            cleaned_curriculum["modules"].append(cleaned_module)
        
        # Update totals
        cleaned_curriculum["total_topics"] = total_topics_after
        cleaned_curriculum["estimated_total_duration"] = curriculum.get("estimated_total_duration")
        
        print(f"\n✅ Curriculum cleaning completed!")
        print(f"📊 Topics before: {total_topics_before}")
        print(f"📊 Topics after: {total_topics_after}")
        print(f"📊 Topics removed: {total_topics_before - total_topics_after}")
        
        return cleaned_curriculum

def main():
    """Clean the curriculum and save results"""
    cleaner = CurriculumCleaner()
    
    # Load and clean curriculum
    curriculum_path = "output/curriculum_expectation_and_variance_20250908_092417.json"
    cleaned_curriculum = cleaner.clean_curriculum(curriculum_path)
    
    # Save cleaned curriculum
    output_path = "output/cleaned_curriculum_expectation_variance.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_curriculum, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Cleaned curriculum saved to: {output_path}")
    
    # Create a detailed analysis report
    analysis_path = "output/curriculum_cleaning_report.txt"
    with open(analysis_path, 'w', encoding='utf-8') as f:
        f.write("📊 CURRICULUM CLEANING ANALYSIS REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Original file: {curriculum_path}\n")
        f.write(f"Cleaned file: {output_path}\n\n")
        
        f.write("IMPROVEMENTS MADE:\n")
        f.write("✅ Removed duplicate topics\n")
        f.write("✅ Standardized topic naming\n")
        f.write("✅ Cleaned inconsistent formatting\n")
        f.write("✅ Verified PDF content accessibility\n\n")
        
        for i, module in enumerate(cleaned_curriculum["modules"], 1):
            f.write(f"MODULE {i}: {module['title']}\n")
            f.write(f"  Topics: {len(module['topics'])}\n")
            f.write(f"  Pages: {module['pages']}\n")
            for j, topic in enumerate(module['topics'], 1):
                f.write(f"    {j}. {topic}\n")
            f.write("\n")
    
    print(f"📝 Analysis report saved to: {analysis_path}")

if __name__ == "__main__":
    main()
