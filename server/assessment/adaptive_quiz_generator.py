"""
Adaptive Quiz Generator
========================
Generates context-aware assessment questions with varying difficulty levels.
Uses LLM + vector store for semantic content retrieval and intelligent question generation.
"""

import json
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict

from LLM import AdvancedAzureLLM
from db.vector_store import get_vector_store
from config.settings import settings


class QuestionType(str, Enum):
    """Question types supported by the quiz generator"""
    MCQ = "mcq"  # Multiple choice
    SHORT_ANSWER = "short_answer"
    TRUE_FALSE = "true_false"
    CODE = "code"  # Code problem/debugging
    NUMERICAL = "numerical"


class DifficultyLevel(str, Enum):
    """Difficulty levels for questions"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class Question:
    """Represents a quiz question"""
    id: str
    question: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    topic: str
    module_name: str
    options: Optional[List[str]] = None  # For MCQ
    correct_answer: Any = None
    explanation: str = ""
    context: str = ""  # Relevant content from theory
    points: int = 1
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class AdaptiveQuizGenerator:
    """
    Generates adaptive quizzes based on module content and student performance
    """
    
    def __init__(self):
        """Initialize the quiz generator"""
        self.llm = AdvancedAzureLLM()
        self.vector_store = get_vector_store()
        self.generated_questions = []
        
        print("✅ Adaptive Quiz Generator initialized")
    
    def generate_quiz(
        self,
        module_name: str,
        topics: List[str],
        num_questions: int = None,
        difficulty_distribution: Dict[str, float] = None,
        question_types: List[QuestionType] = None,
        student_weak_areas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete quiz for a module
        
        Args:
            module_name: Name of the module
            topics: List of topic names to cover
            num_questions: Number of questions (default from settings)
            difficulty_distribution: Distribution of difficulties (e.g., {"easy": 0.3, "medium": 0.5, "hard": 0.2})
            question_types: Types of questions to generate
            student_weak_areas: Topics where student needs more practice
            
        Returns:
            Complete quiz with questions and metadata
        """
        if num_questions is None:
            num_questions = settings.QUIZ_DEFAULT_QUESTIONS
        
        if difficulty_distribution is None:
            difficulty_distribution = {"easy": 0.3, "medium": 0.5, "hard": 0.2}
        
        if question_types is None:
            question_types = [QuestionType.MCQ, QuestionType.SHORT_ANSWER, QuestionType.TRUE_FALSE]
        
        print(f"\n📝 Generating quiz for: {module_name}")
        print(f"   Topics: {len(topics)}")
        print(f"   Questions: {num_questions}")
        print(f"   Difficulty: {difficulty_distribution}")
        
        questions = []
        
        # Calculate questions per difficulty
        num_easy = int(num_questions * difficulty_distribution.get("easy", 0.3))
        num_medium = int(num_questions * difficulty_distribution.get("medium", 0.5))
        num_hard = num_questions - num_easy - num_medium
        
        # Prioritize weak areas
        topics_to_cover = topics.copy()
        if student_weak_areas:
            # Give more weight to weak areas
            for weak_topic in student_weak_areas:
                if weak_topic in topics_to_cover:
                    topics_to_cover.append(weak_topic)  # Add again for higher probability
        
        # Generate questions by difficulty
        for difficulty, count in [
            (DifficultyLevel.EASY, num_easy),
            (DifficultyLevel.MEDIUM, num_medium),
            (DifficultyLevel.HARD, num_hard)
        ]:
            for i in range(count):
                # Select topic (round-robin with weak area bias)
                topic_idx = (len(questions) + i) % len(topics_to_cover)
                topic = topics_to_cover[topic_idx]
                
                # Select question type (distribute evenly)
                question_type = question_types[(len(questions) + i) % len(question_types)]
                
                # Generate question
                question = self._generate_single_question(
                    module_name=module_name,
                    topic=topic,
                    question_type=question_type,
                    difficulty=difficulty
                )
                
                if question:
                    questions.append(question)
        
        # Create quiz object
        quiz = {
            'quiz_id': self._generate_quiz_id(module_name),
            'module_name': module_name,
            'topics': topics,
            'num_questions': len(questions),
            'questions': [q.to_dict() for q in questions],
            'difficulty_distribution': difficulty_distribution,
            'generated_at': datetime.now().isoformat(),
            'metadata': {
                'question_types': [qt.value for qt in question_types],
                'weak_areas_targeted': student_weak_areas or []
            }
        }
        
        # Save quiz
        self._save_quiz(quiz)
        
        print(f"✅ Generated {len(questions)} questions")
        return quiz
    
    def _generate_single_question(
        self,
        module_name: str,
        topic: str,
        question_type: QuestionType,
        difficulty: DifficultyLevel
    ) -> Optional[Question]:
        """
        Generate a single question using RAG + LLM
        
        Args:
            module_name: Module name
            topic: Specific topic
            question_type: Type of question
            difficulty: Difficulty level
            
        Returns:
            Generated question or None
        """
        try:
            # Step 1: Retrieve relevant context from vector store
            context = self._retrieve_context(topic, n_results=3)
            
            if not context:
                print(f"⚠️  No context found for topic: {topic}")
                return None
            
            # Step 2: Generate question using LLM
            question_data = self._llm_generate_question(
                topic=topic,
                context=context,
                question_type=question_type,
                difficulty=difficulty
            )
            
            if not question_data:
                return None
            
            # Step 3: Create Question object
            question = Question(
                id=self._generate_question_id(),
                question=question_data.get('question', ''),
                question_type=question_type,
                difficulty=difficulty,
                topic=topic,
                module_name=module_name,
                options=question_data.get('options'),
                correct_answer=question_data.get('correct_answer'),
                explanation=question_data.get('explanation', ''),
                context=context[:500],  # Store first 500 chars of context
                points=self._calculate_points(difficulty),
                metadata={
                    'generation_method': 'rag_llm',
                    'context_length': len(context)
                }
            )
            
            return question
            
        except Exception as e:
            print(f"❌ Error generating question: {e}")
            return None
    
    def _retrieve_context(self, topic: str, n_results: int = 3) -> str:
        """
        Retrieve relevant context from vector store for question generation
        
        Args:
            topic: Topic to retrieve context for
            n_results: Number of results to retrieve
            
        Returns:
            Combined context string
        """
        # Search vector store for relevant content
        results = self.vector_store.search_topics(topic, n_results=n_results)
        
        if not results:
            return ""
        
        # Combine content from top results
        context_parts = []
        for result in results:
            content = result.get('content', '')
            if content:
                context_parts.append(content)
        
        return "\n\n".join(context_parts)
    
    def _llm_generate_question(
        self,
        topic: str,
        context: str,
        question_type: QuestionType,
        difficulty: DifficultyLevel
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM to generate a question based on context
        
        Args:
            topic: Topic name
            context: Retrieved context
            question_type: Type of question
            difficulty: Difficulty level
            
        Returns:
            Dictionary with question data
        """
        # Create prompt based on question type
        prompt = self._create_question_prompt(topic, context, question_type, difficulty)
        
        try:
            # Use GPT-5-mini for fast generation
            response = self.llm.gpt_5_mini(prompt)
            
            # Parse response
            question_data = self._parse_llm_response(response, question_type)
            
            return question_data
            
        except Exception as e:
            print(f"❌ LLM generation error: {e}")
            return None
    
    def _create_question_prompt(
        self,
        topic: str,
        context: str,
        question_type: QuestionType,
        difficulty: DifficultyLevel
    ) -> str:
        """Create LLM prompt for question generation"""
        
        base_prompt = f"""Generate a {difficulty.value} difficulty {question_type.value} question about "{topic}".

CONTEXT FROM TEXTBOOK:
{context}

REQUIREMENTS:
1. Question must be based strictly on the provided context
2. Difficulty level: {difficulty.value}
3. Question type: {question_type.value}
"""

        if question_type == QuestionType.MCQ:
            base_prompt += """
4. Provide exactly 4 options (A, B, C, D)
5. Only one option should be correct
6. Distractors should be plausible but clearly wrong
7. Include explanation for the correct answer

OUTPUT FORMAT (JSON):
{
  "question": "Your question here",
  "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
  "correct_answer": "A",
  "explanation": "Why this is correct..."
}
"""
        elif question_type == QuestionType.SHORT_ANSWER:
            base_prompt += """
4. Question should require 2-3 sentence answer
5. Provide model answer
6. Include grading rubric points

OUTPUT FORMAT (JSON):
{
  "question": "Your question here",
  "correct_answer": "Model answer here...",
  "explanation": "Key points to include in answer..."
}
"""
        elif question_type == QuestionType.TRUE_FALSE:
            base_prompt += """
4. Create a clear true/false statement
5. Include explanation

OUTPUT FORMAT (JSON):
{
  "question": "Statement to evaluate",
  "correct_answer": true/false,
  "explanation": "Why this is true/false..."
}
"""
        elif question_type == QuestionType.CODE:
            base_prompt += """
4. If applicable to the topic, create a code problem
5. Otherwise, create a problem-solving question
6. Provide solution

OUTPUT FORMAT (JSON):
{
  "question": "Problem statement or code challenge",
  "correct_answer": "Solution or code",
  "explanation": "Explanation of solution..."
}
"""
        elif question_type == QuestionType.NUMERICAL:
            base_prompt += """
4. Create a numerical problem
5. Provide numerical answer with units
6. Show solution steps

OUTPUT FORMAT (JSON):
{
  "question": "Problem with numerical answer",
  "correct_answer": "42.5 units",
  "explanation": "Solution steps..."
}
"""
        
        base_prompt += "\n\nGenerate ONLY the JSON, no additional text:"
        
        return base_prompt
    
    def _parse_llm_response(
        self,
        response: str,
        question_type: QuestionType
    ) -> Optional[Dict[str, Any]]:
        """Parse LLM response to extract question data"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                print("⚠️  No JSON found in LLM response")
                return None
            
            json_str = json_match.group(0)
            question_data = json.loads(json_str)
            
            # Validate required fields
            if 'question' not in question_data or 'correct_answer' not in question_data:
                print("⚠️  Missing required fields in question data")
                return None
            
            return question_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Response: {response[:200]}...")
            return None
        except Exception as e:
            print(f"❌ Parse error: {e}")
            return None
    
    def _calculate_points(self, difficulty: DifficultyLevel) -> int:
        """Calculate points based on difficulty"""
        points_map = {
            DifficultyLevel.EASY: 1,
            DifficultyLevel.MEDIUM: 2,
            DifficultyLevel.HARD: 3
        }
        return points_map.get(difficulty, 1)
    
    def _generate_quiz_id(self, module_name: str) -> str:
        """Generate unique quiz ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_module = re.sub(r'[^\w\s-]', '', module_name)[:30].replace(' ', '_')
        return f"quiz_{clean_module}_{timestamp}"
    
    def _generate_question_id(self) -> str:
        """Generate unique question ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        import random
        random_suffix = random.randint(1000, 9999)
        return f"q_{timestamp}_{random_suffix}"
    
    def _save_quiz(self, quiz: Dict[str, Any]):
        """Save generated quiz to file"""
        output_dir = "output/quizzes"
        os.makedirs(output_dir, exist_ok=True)
        
        quiz_id = quiz['quiz_id']
        filename = f"{output_dir}/{quiz_id}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(quiz, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Quiz saved: {filename}")


if __name__ == "__main__":
    # Test the quiz generator
    print("🧪 Testing Adaptive Quiz Generator...")
    
    generator = AdaptiveQuizGenerator()
    
    # Test quiz generation
    quiz = generator.generate_quiz(
        module_name="Introduction to Probability",
        topics=["Random Variables", "Expected Value", "Variance"],
        num_questions=5,
        difficulty_distribution={"easy": 0.4, "medium": 0.4, "hard": 0.2},
        question_types=[QuestionType.MCQ, QuestionType.SHORT_ANSWER]
    )
    
    print("\n📊 Generated Quiz:")
    print(f"Quiz ID: {quiz['quiz_id']}")
    print(f"Questions: {quiz['num_questions']}")
    print(f"\nSample Questions:")
    for i, q in enumerate(quiz['questions'][:3], 1):
        print(f"\n{i}. [{q['difficulty']}] {q['question'][:100]}...")
    
    print("\n✅ Quiz generator test complete!")
