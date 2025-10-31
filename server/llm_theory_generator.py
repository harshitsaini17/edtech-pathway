"""
LLM-Based Theory Generator from PDF Content
===========================================

Generates high-quality, contextual learning theory directly from PDF content.
"""

import fitz  # PyMuPDF
from typing import List, Dict, Any
from LLM import AdvancedAzureLLM


class LLMTheoryGenerator:
    """Generate educational theory content from PDF using LLM"""
    
    def __init__(self, pdf_path: str):
        """
        Initialize theory generator
        
        Args:
            pdf_path: Path to the PDF textbook
        """
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        
        try:
            self.llm = AdvancedAzureLLM()
            print("✅ LLM Theory Generator initialized successfully")
        except Exception as e:
            print(f"❌ LLM initialization failed: {e}")
            self.llm = None
    
    def extract_text_from_pages(self, page_numbers: List[int]) -> str:
        """
        Extract text from specific pages
        
        Args:
            page_numbers: List of page numbers to extract from
            
        Returns:
            Combined text from all pages
        """
        text_content = []
        
        for page_num in page_numbers:
            if 0 <= page_num < len(self.doc):
                page = self.doc[page_num]
                text = page.get_text()
                text_content.append(text)
        
        return "\n\n".join(text_content)
    
    def generate_theory_from_pdf(
        self,
        topic_title: str,
        page_numbers: List[int],
        difficulty_level: str = "intermediate",
        learning_objectives: List[str] = None,
        student_weak_areas: List[str] = None
    ) -> str:
        """
        Generate comprehensive theory content from PDF pages
        
        Args:
            topic_title: Title of the topic
            page_numbers: Pages to extract content from
            difficulty_level: beginner, intermediate, advanced
            learning_objectives: Learning objectives for this topic
            student_weak_areas: Areas where student is weak (for personalization)
            
        Returns:
            Generated theory content as markdown
        """
        if not self.llm:
            print("⚠️ LLM not available, using fallback")
            return self._generate_fallback_theory(topic_title, difficulty_level)
        
        # Extract PDF content
        pdf_content = self.extract_text_from_pages(page_numbers)
        
        if not pdf_content.strip():
            print(f"⚠️ No content found on pages {page_numbers}")
            return self._generate_fallback_theory(topic_title, difficulty_level)
        
        # Build personalization context
        personalization_note = ""
        if student_weak_areas:
            personalization_note = f"""
STUDENT CONTEXT (Personalization):
The student has struggled with: {', '.join(student_weak_areas)}
Please provide extra explanation and examples for these areas.
"""
        
        objectives_text = ""
        if learning_objectives:
            objectives_text = f"""
LEARNING OBJECTIVES:
{chr(10).join(f'- {obj}' for obj in learning_objectives)}
"""
        
        prompt = f"""You are an expert educational content creator. Generate comprehensive, well-structured learning material for students.

TOPIC: {topic_title}
DIFFICULTY LEVEL: {difficulty_level}
PAGES: {page_numbers}
{objectives_text}
{personalization_note}

SOURCE MATERIAL (from textbook):
{pdf_content[:6000]}

REQUIREMENTS:
1. Create a complete, well-structured learning module
2. Use ONLY information from the source material provided
3. Structure the content as follows:
   - Introduction (engaging hook + overview)
   - Key Concepts (clear definitions)
   - Detailed Explanation (with examples from the text)
   - Mathematical formulas (if present in source)
   - Real-world examples or applications
   - Practice problems or exercises
   - Summary and key takeaways
4. Difficulty level: {difficulty_level}
5. Format in clear Markdown
6. Include concrete examples from the source material
7. If formulas are present, explain them clearly
8. Make it engaging and easy to understand

OUTPUT FORMAT:
Generate complete markdown content suitable for student learning.
Include ## headers for sections.
Use bullet points, numbered lists, and **bold** for emphasis.
Include code blocks for formulas if applicable.

Generate the learning content now:"""
        
        try:
            response = self.llm.generate_response(
                prompt=prompt,
                max_tokens=3000,
                temperature=1.0
            )
            
            print(f"✅ Generated theory for '{topic_title}' ({len(response)} chars)")
            return response
            
        except Exception as e:
            print(f"❌ Error generating theory: {e}")
            return self._generate_fallback_theory(topic_title, difficulty_level)
    
    def _generate_fallback_theory(self, topic_title: str, difficulty_level: str) -> str:
        """Generate simple fallback theory when LLM is not available"""
        return f"""
# {topic_title}

## Introduction

This section covers the fundamental concepts of {topic_title}. 
This content is designed for {difficulty_level} level students.

## Key Concepts

The main concepts covered in this topic include the core principles and 
foundational ideas that are essential for understanding {topic_title}.

## Detailed Explanation

{topic_title} is an important concept that builds upon previous knowledge.
Understanding this topic requires careful study of the principles and their
applications in various contexts.

## Examples

Practical examples help illustrate how {topic_title} works in real scenarios.
Students should work through these examples to deepen their understanding.

## Practice

To master {topic_title}, practice with various problems and exercises.
Apply the concepts learned to solve real-world problems.

## Summary

This topic provides essential knowledge about {topic_title}. Review the
key concepts and practice regularly to build proficiency.
"""
    
    def generate_personalized_theory(
        self,
        topic_title: str,
        page_numbers: List[int],
        difficulty_level: str,
        quiz_performance: Dict[str, Any]
    ) -> str:
        """
        Generate theory with personalization based on quiz performance
        
        Args:
            topic_title: Topic to generate theory for
            page_numbers: Pages to use from PDF
            difficulty_level: Current difficulty level
            quiz_performance: Previous quiz results with weak areas
            
        Returns:
            Personalized theory content
        """
        weak_concepts = quiz_performance.get('weak_concepts', [])
        score = quiz_performance.get('score', 0)
        
        # Extract PDF content
        pdf_content = self.extract_text_from_pages(page_numbers)
        
        if not self.llm:
            return self._generate_fallback_theory(topic_title, difficulty_level)
        
        prompt = f"""You are an expert adaptive learning content creator. Generate PERSONALIZED learning content based on student's performance.

TOPIC: {topic_title}
DIFFICULTY: {difficulty_level}
PAGES: {page_numbers}

STUDENT PERFORMANCE:
- Previous Quiz Score: {score}%
- Weak Areas: {', '.join(weak_concepts) if weak_concepts else 'None'}

SOURCE MATERIAL:
{pdf_content[:6000]}

PERSONALIZATION REQUIREMENTS:
1. Start with a "📊 PERSONALIZED FOR YOU" section explaining:
   - Your performance level
   - What we'll focus on
   - Why this content is tailored for you

2. If student scored < 60%:
   - Provide MORE detailed explanations
   - Include EXTRA examples
   - Break down complex concepts into smaller steps
   - Add review sections for weak areas

3. If student scored 60-80%:
   - Standard detailed content
   - Focus extra attention on weak areas
   - Provide targeted examples for concepts they struggled with

4. If student scored > 80%:
   - More concise explanations
   - Focus on advanced aspects
   - Include challenging applications

5. Structure:
   - Personalized introduction
   - Review of relevant weak areas (if any)
   - Main content (from PDF)
   - Extra practice on weak concepts
   - Summary with personalized recommendations

6. Format in Markdown with clear sections

Generate personalized learning content now:"""
        
        try:
            response = self.llm.generate_response(
                prompt=prompt,
                max_tokens=3500,
                temperature=1.0
            )
            
            print(f"✅ Generated personalized theory for '{topic_title}'")
            return response
            
        except Exception as e:
            print(f"❌ Error generating personalized theory: {e}")
            return self._generate_fallback_theory(topic_title, difficulty_level)
    
    def __del__(self):
        """Close PDF document"""
        if hasattr(self, 'doc'):
            self.doc.close()


if __name__ == "__main__":
    # Test the theory generator
    print("Testing LLM Theory Generator...")
    
    generator = LLMTheoryGenerator("doc/book2.pdf")
    
    theory = generator.generate_theory_from_pdf(
        topic_title="Expected Value of Random Variables",
        page_numbers=[153, 154, 155],  # Example pages
        difficulty_level="intermediate",
        learning_objectives=[
            "Understand the definition of expected value",
            "Calculate expected values for discrete random variables",
            "Apply properties of expected value"
        ]
    )
    
    print("\n" + "="*80)
    print("GENERATED THEORY:")
    print("="*80)
    print(theory[:500] + "...")
