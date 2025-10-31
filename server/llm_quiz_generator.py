"""
LLM-Based Quiz Generator
========================

Generates high-quality, context-aware quiz questions using Azure OpenAI.
Questions are based on actual theory content and PDF text.
"""

import json
from typing import List, Dict, Any
from LLM import AdvancedAzureLLM


class LLMQuizGenerator:
    """Generate high-quality quiz questions using LLM"""
    
    def __init__(self):
        """Initialize the quiz generator with LLM"""
        try:
            self.llm = AdvancedAzureLLM()
            print("✅ LLM Quiz Generator initialized successfully")
        except Exception as e:
            print(f"❌ LLM initialization failed: {e}")
            self.llm = None
    
    def generate_quiz_from_multiple_theories(
        self,
        theories: List[Dict[str, Any]],
        module_name: str,
        difficulty_level: str = "intermediate",
        num_questions_per_topic: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions from multiple theory contents (entire module)
        
        Args:
            theories: List of theory dictionaries with 'topic' and 'theory' keys
            module_name: Name of the module
            difficulty_level: beginner, intermediate, advanced
            num_questions_per_topic: Questions to generate per topic
            
        Returns:
            List of quiz questions covering all topics
        """
        if not self.llm:
            print("⚠️ LLM not available, cannot generate quiz")
            return []
        
        # Combine all theories into one context
        combined_context = f"# {module_name}\n\n"
        for theory_dict in theories:
            topic = theory_dict.get('topic', 'Unknown Topic')
            theory = theory_dict.get('theory', '')
            combined_context += f"\n## {topic}\n\n{theory[:2000]}\n\n"
        
        total_questions = len(theories) * num_questions_per_topic
        
        prompt = f"""You are an expert educational assessment designer. Generate {total_questions} high-quality multiple-choice quiz questions based on the complete learning module provided below.

MODULE: {module_name}
DIFFICULTY LEVEL: {difficulty_level}
TOPICS COVERED: {len(theories)} topics
QUESTIONS PER TOPIC: {num_questions_per_topic}

COMPLETE MODULE CONTENT:
{combined_context[:8000]}

REQUIREMENTS:
1. Generate EXACTLY {total_questions} questions total
2. Distribute questions across all {len(theories)} topics covered
3. Each question must have 4 options (A, B, C, D)
4. Test understanding across the ENTIRE module, not just individual topics
5. Include questions that:
   - Test conceptual understanding of individual topics
   - Require comparing/contrasting concepts across topics
   - Apply concepts in integrated scenarios
   - Analyze relationships between topics in the module
6. Difficulty level: {difficulty_level}
7. Mix of difficulty within level:
   - 30% easier questions (definitions, recall)
   - 50% medium questions (application, analysis)
   - 20% harder questions (synthesis, evaluation)
8. Make sure questions reference specific content from the theories

OUTPUT FORMAT (JSON):
{{
  "questions": [
    {{
      "question": "Clear, specific question based on the module content",
      "options": {{
        "A": "First option",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
      }},
      "correct_answer": "B",
      "explanation": "Detailed explanation with reference to the theory",
      "concept": "Main concept from one of the topics",
      "difficulty": "easy/medium/hard",
      "topic_index": 0
    }}
  ]
}}

Generate {total_questions} comprehensive quiz questions now:"""
        
        try:
            response = self.llm.generate_response(
                prompt=prompt,
                max_tokens=3500,
                temperature=1.0
            )
            
            # Parse JSON response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            
            quiz_data = json.loads(response)
            questions = quiz_data.get('questions', [])
            
            # Format questions
            formatted_questions = []
            for q in questions:
                formatted_q = {
                    'question': q['question'],
                    'options': [
                        q['options'].get('A', ''),
                        q['options'].get('B', ''),
                        q['options'].get('C', ''),
                        q['options'].get('D', '')
                    ],
                    'correct_answer': q['correct_answer'],
                    'explanation': q.get('explanation', ''),
                    'concept': q.get('concept', module_name),
                    'difficulty': q.get('difficulty', 'medium'),
                    'topic_index': q.get('topic_index', 0)
                }
                formatted_questions.append(formatted_q)
            
            print(f"✅ Generated {len(formatted_questions)} questions from {len(theories)} topics")
            return formatted_questions
            
        except Exception as e:
            print(f"❌ Error generating quiz from multiple theories: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def generate_quiz_from_theory(
        self,
        theory_content: str,
        topic_title: str,
        difficulty_level: str = "intermediate",
        num_questions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions from theory content using LLM
        
        Args:
            theory_content: The theory text to generate questions from
            topic_title: Title of the topic
            difficulty_level: beginner, intermediate, advanced
            num_questions: Number of questions to generate
            
        Returns:
            List of quiz questions with options and correct answers
        """
        if not self.llm:
            print("⚠️ LLM not available, cannot generate quiz")
            return []
        
        prompt = f"""You are an expert educational assessment designer. Generate {num_questions} high-quality multiple-choice quiz questions based on the following learning content.

TOPIC: {topic_title}
DIFFICULTY LEVEL: {difficulty_level}

LEARNING CONTENT:
{theory_content[:3000]}

REQUIREMENTS:
1. Generate EXACTLY {num_questions} questions
2. Each question must have 4 options (A, B, C, D)
3. Questions should test understanding, not just memorization
4. Include a mix of:
   - Conceptual understanding (definitions, principles)
   - Application (how to use the concept)
   - Analysis (compare, contrast, evaluate)
5. Difficulty level: {difficulty_level}
6. Mark the correct answer clearly
7. Make sure wrong options are plausible but clearly incorrect

OUTPUT FORMAT (JSON):
{{
  "questions": [
    {{
      "question": "Clear, specific question text",
      "options": {{
        "A": "First option",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
      }},
      "correct_answer": "A",
      "explanation": "Brief explanation of why this is correct",
      "concept": "Main concept being tested",
      "difficulty": "easy/medium/hard"
    }}
  ]
}}

Generate the quiz questions now:"""
        
        try:
            response = self.llm.generate_response(
                prompt=prompt,
                max_tokens=2000,
                temperature=1.0
            )
            
            # Parse JSON response
            # Try to extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            
            quiz_data = json.loads(response)
            questions = quiz_data.get('questions', [])
            
            # Format questions
            formatted_questions = []
            for q in questions:
                formatted_q = {
                    'question': q['question'],
                    'options': [
                        q['options'].get('A', ''),
                        q['options'].get('B', ''),
                        q['options'].get('C', ''),
                        q['options'].get('D', '')
                    ],
                    'correct_answer': q['correct_answer'],
                    'explanation': q.get('explanation', ''),
                    'concept': q.get('concept', topic_title),
                    'difficulty': q.get('difficulty', 'medium')
                }
                formatted_questions.append(formatted_q)
            
            print(f"✅ Generated {len(formatted_questions)} high-quality quiz questions")
            return formatted_questions
            
        except Exception as e:
            print(f"❌ Error generating quiz: {e}")
            return []
    
    def generate_quiz_from_pdf_content(
        self,
        pdf_text: str,
        topic_title: str,
        page_numbers: List[int],
        difficulty_level: str = "intermediate",
        num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions directly from PDF content
        
        Args:
            pdf_text: Extracted text from PDF pages
            topic_title: Title of the topic
            page_numbers: Page numbers where content is from
            difficulty_level: beginner, intermediate, advanced
            num_questions: Number of questions to generate
            
        Returns:
            List of quiz questions
        """
        if not self.llm:
            print("⚠️ LLM not available, cannot generate quiz")
            return []
        
        prompt = f"""You are an expert educational assessment designer. Generate {num_questions} high-quality multiple-choice quiz questions based on the following textbook content.

TOPIC: {topic_title}
PAGES: {page_numbers}
DIFFICULTY LEVEL: {difficulty_level}

TEXTBOOK CONTENT:
{pdf_text[:4000]}

REQUIREMENTS:
1. Generate EXACTLY {num_questions} questions
2. Base questions ONLY on the provided content
3. Each question must have 4 options (A, B, C, D)
4. Test deep understanding, not surface-level facts
5. Include questions that:
   - Test conceptual understanding
   - Require application of concepts
   - Ask for analysis or evaluation
6. Difficulty: {difficulty_level}
7. Make distractors plausible but clearly wrong

OUTPUT FORMAT (JSON):
{{
  "questions": [
    {{
      "question": "Specific question based on the content",
      "options": {{
        "A": "First option",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
      }},
      "correct_answer": "B",
      "explanation": "Why this answer is correct with reference to content",
      "concept": "Main concept being tested",
      "difficulty": "easy/medium/hard",
      "page_reference": {page_numbers[0] if page_numbers else 0}
    }}
  ]
}}

Generate the quiz questions now:"""
        
        try:
            response = self.llm.generate_response(
                prompt=prompt,
                max_tokens=2500,
                temperature=1.0
            )
            
            # Parse JSON
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            
            quiz_data = json.loads(response)
            questions = quiz_data.get('questions', [])
            
            # Format questions
            formatted_questions = []
            for q in questions:
                formatted_q = {
                    'question': q['question'],
                    'options': [
                        q['options'].get('A', ''),
                        q['options'].get('B', ''),
                        q['options'].get('C', ''),
                        q['options'].get('D', '')
                    ],
                    'correct_answer': q['correct_answer'],
                    'explanation': q.get('explanation', ''),
                    'concept': q.get('concept', topic_title),
                    'difficulty': q.get('difficulty', 'medium'),
                    'page_reference': q.get('page_reference', 0)
                }
                formatted_questions.append(formatted_q)
            
            print(f"✅ Generated {len(formatted_questions)} PDF-based quiz questions")
            return formatted_questions
            
        except Exception as e:
            print(f"❌ Error generating quiz from PDF: {e}")
            return []
    
    def generate_adaptive_quiz(
        self,
        current_topic: str,
        previous_performance: Dict[str, Any],
        theory_content: str,
        difficulty_level: str = "intermediate"
    ) -> List[Dict[str, Any]]:
        """
        Generate adaptive quiz based on previous performance
        
        Args:
            current_topic: Current topic being studied
            previous_performance: Previous quiz results and weak areas
            theory_content: Theory content for current topic
            difficulty_level: Current difficulty level
            
        Returns:
            Adaptive quiz questions
        """
        weak_areas = previous_performance.get('weak_concepts', [])
        score = previous_performance.get('score', 0)
        
        # Adjust number of questions based on performance
        if score < 60:
            num_questions = 5  # More questions for struggling students
            focus = "Review and reinforce weak areas"
        elif score < 80:
            num_questions = 4  # Standard questions
            focus = "Strengthen understanding and test new concepts"
        else:
            num_questions = 3  # Fewer but harder questions
            focus = "Challenge with advanced concepts"
        
        prompt = f"""You are an expert adaptive learning system. Generate {num_questions} personalized quiz questions.

CURRENT TOPIC: {current_topic}
DIFFICULTY LEVEL: {difficulty_level}

STUDENT CONTEXT:
- Previous Score: {score}%
- Weak Areas: {', '.join(weak_areas) if weak_areas else 'None identified'}
- Focus: {focus}

LEARNING CONTENT:
{theory_content[:3000]}

REQUIREMENTS:
1. Generate {num_questions} questions adapted to student's level
2. If weak areas exist, include questions to assess if they've improved
3. Include questions on new material from current topic
4. Adjust difficulty based on previous performance
5. Each question: 4 options (A, B, C, D)

OUTPUT FORMAT (JSON):
{{
  "questions": [
    {{
      "question": "Question text",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "correct_answer": "C",
      "explanation": "Why this is correct",
      "concept": "Concept being tested",
      "difficulty": "easy/medium/hard",
      "is_remedial": false,
      "addresses_weak_area": "weak area name or null"
    }}
  ]
}}

Generate adaptive quiz now:"""
        
        try:
            response = self.llm.generate_response(
                prompt=prompt,
                max_tokens=2500,
                temperature=1.0
            )
            
            # Parse JSON
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            
            quiz_data = json.loads(response)
            questions = quiz_data.get('questions', [])
            
            formatted_questions = []
            for q in questions:
                formatted_q = {
                    'question': q['question'],
                    'options': [
                        q['options'].get('A', ''),
                        q['options'].get('B', ''),
                        q['options'].get('C', ''),
                        q['options'].get('D', '')
                    ],
                    'correct_answer': q['correct_answer'],
                    'explanation': q.get('explanation', ''),
                    'concept': q.get('concept', current_topic),
                    'difficulty': q.get('difficulty', 'medium'),
                    'is_remedial': q.get('is_remedial', False),
                    'addresses_weak_area': q.get('addresses_weak_area')
                }
                formatted_questions.append(formatted_q)
            
            print(f"✅ Generated {len(formatted_questions)} adaptive quiz questions")
            return formatted_questions
            
        except Exception as e:
            print(f"❌ Error generating adaptive quiz: {e}")
            return []


if __name__ == "__main__":
    # Test the quiz generator
    print("Testing LLM Quiz Generator...")
    
    generator = LLMQuizGenerator()
    
    # Test 1: Single theory
    print("\n" + "="*80)
    print("TEST 1: Single Theory Quiz Generation")
    print("="*80)
    
    sample_theory = """
    Expected Value (Expectation)
    
    The expected value of a random variable is a measure of the center of its distribution.
    For a discrete random variable X, the expected value E(X) is calculated as:
    
    E(X) = Σ x * P(X = x)
    
    where the sum is taken over all possible values of X.
    
    Properties of Expected Value:
    1. Linearity: E(aX + b) = aE(X) + b
    2. For independent variables: E(XY) = E(X)E(Y)
    3. The expected value is a weighted average of all possible values
    
    Example: For a fair six-sided die, E(X) = (1+2+3+4+5+6)/6 = 3.5
    """
    
    questions = generator.generate_quiz_from_theory(
        theory_content=sample_theory,
        topic_title="Expected Value",
        difficulty_level="intermediate",
        num_questions=3
    )
    
    print(f"\n✅ Generated {len(questions)} questions from single theory")
    if questions:
        print(f"\nSample Question:")
        print(f"Q: {questions[0]['question']}")
        print(f"Correct: {questions[0]['correct_answer']}")
    
    # Test 2: Multiple theories (entire module)
    print("\n" + "="*80)
    print("TEST 2: Multiple Theories Quiz Generation (Full Module)")
    print("="*80)
    
    sample_theories = [
        {
            'topic': 'Expected Value',
            'theory': sample_theory
        },
        {
            'topic': 'Variance',
            'theory': """
            Variance
            
            Variance measures the spread of a distribution. For a random variable X:
            
            Var(X) = E[(X - E(X))²] = E(X²) - [E(X)]²
            
            Properties:
            1. Var(aX + b) = a²Var(X)
            2. For independent X, Y: Var(X + Y) = Var(X) + Var(Y)
            3. Standard deviation: σ = √Var(X)
            
            Example: For die, E(X) = 3.5, Var(X) = 2.92
            """
        },
        {
            'topic': 'Covariance',
            'theory': """
            Covariance
            
            Covariance measures the joint variability of two random variables:
            
            Cov(X, Y) = E[(X - E(X))(Y - E(Y))] = E(XY) - E(X)E(Y)
            
            Properties:
            1. Cov(X, X) = Var(X)
            2. Cov(X, Y) = Cov(Y, X)
            3. If X, Y independent: Cov(X, Y) = 0
            
            Correlation: ρ(X,Y) = Cov(X,Y) / (σ_X × σ_Y)
            """
        }
    ]
    
    module_questions = generator.generate_quiz_from_multiple_theories(
        theories=sample_theories,
        module_name="Expectation and Variance",
        difficulty_level="intermediate",
        num_questions_per_topic=2
    )
    
    print(f"\n✅ Generated {len(module_questions)} questions from {len(sample_theories)} topics")
    if module_questions:
        print(f"\nSample Questions:")
        for i, q in enumerate(module_questions[:3], 1):
            print(f"\nQ{i}: {q['question']}")
            print(f"   Concept: {q['concept']}")
            print(f"   Difficulty: {q['difficulty']}")
            print(f"   Correct: {q['correct_answer']}")
