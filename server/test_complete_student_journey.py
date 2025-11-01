"""
Complete Student Learning Journey Simulation
=============================================

Simulates a full student experience:
1. Extract topics from PDF
2. Generate personalized curriculum
3. Generate theory content for first module
4. Generate quiz questions
5. Simulate student taking quiz
6. Analyze performance and adapt
7. Generate personalized next module content
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import random

# Import all necessary components
from optimized_universal_extractor import OptimizedUniversalExtractor
from db.student_profile import StudentProfile, LearningStyle
from assessment.quiz_analyzer import QuizAnalyzer
from llm_quiz_generator import LLMQuizGenerator
from llm_theory_generator import LLMTheoryGenerator


def generate_quiz_from_all_theories(
    theories: List[Dict[str, Any]],
    module_name: str,
    difficulty_level: str = "intermediate",
    num_questions_per_topic: int = 3
) -> List[Dict[str, Any]]:
    """
    Generate quiz questions from ALL theories in a module using LLM
    
    This provides better context and allows for cross-topic questions.
    
    Args:
        theories: List of theory dictionaries with 'topic' and 'theory' keys
        module_name: Name of the module
        difficulty_level: Difficulty level
        num_questions_per_topic: Questions per topic
        
    Returns:
        List of quiz questions covering the entire module
    """
    generator = LLMQuizGenerator()
    questions = generator.generate_quiz_from_multiple_theories(
        theories=theories,
        module_name=module_name,
        difficulty_level=difficulty_level,
        num_questions_per_topic=num_questions_per_topic
    )
    return questions


def generate_theory_from_pdf(
    pdf_path: str,
    topic_title: str,
    page_numbers: List[int],
    difficulty_level: str = "intermediate",
    learning_objectives: List[str] = None,
    weak_areas: List[str] = None
) -> str:
    """
    Generate theory content from PDF using LLM
    
    Args:
        pdf_path: Path to PDF file
        topic_title: Title of the topic
        page_numbers: Pages to extract from
        difficulty_level: Difficulty level
        learning_objectives: Learning objectives
        weak_areas: Student's weak areas for personalization
        
    Returns:
        Generated theory content
    """
    generator = LLMTheoryGenerator(pdf_path)
    theory = generator.generate_theory_from_pdf(
        topic_title=topic_title,
        page_numbers=page_numbers,
        difficulty_level=difficulty_level,
        learning_objectives=learning_objectives,
        student_weak_areas=weak_areas
    )
    return theory


def generate_quiz_questions(topic_title: str, theory_content: str, num_questions: int = 3) -> List[Dict[str, Any]]:
    """
    Generate quiz questions for a topic
    
    Args:
        topic_title: Title of the topic
        theory_content: Theory content to generate questions from
        num_questions: Number of questions to generate
        
    Returns:
        List of quiz questions
    """
    # Sample quiz questions based on common patterns
    questions = []
    
    question_templates = [
        {
            'question': f'What is the definition of {topic_title}?',
            'options': ['Option A', 'Option B', 'Option C', 'Option D'],
            'correct_answer': 'A',
            'concept': topic_title,
            'difficulty': 'easy'
        },
        {
            'question': f'Which property is true for {topic_title}?',
            'options': ['Property A', 'Property B', 'Property C', 'Property D'],
            'correct_answer': 'B',
            'concept': topic_title,
            'difficulty': 'medium'
        },
        {
            'question': f'How would you apply {topic_title} in practice?',
            'options': ['Method A', 'Method B', 'Method C', 'Method D'],
            'correct_answer': 'C',
            'concept': topic_title,
            'difficulty': 'hard'
        }
    ]
    
    for i in range(min(num_questions, len(question_templates))):
        questions.append(question_templates[i])
    
    return questions


def generate_simple_theory(topic_title: str, difficulty_level: str = "beginner") -> str:
    """
    Generate simple theory content for a topic
    
    Args:
        topic_title: Title of the topic
        difficulty_level: Difficulty level (beginner/intermediate/advanced)
        
    Returns:
        Theory content as string
    """
    theory = f"""
# {topic_title}

## Introduction

This section covers the fundamental concepts of {topic_title}. 
This is designed for {difficulty_level} level students.

## Key Concepts

1. **Definition**: {topic_title} refers to the fundamental principles and 
   concepts that form the foundation of this topic area.

2. **Core Principles**: Understanding {topic_title} requires grasping 
   several key principles that govern how these concepts work in practice.

3. **Applications**: {topic_title} has wide-ranging applications across 
   various domains and practical scenarios.

## Detailed Explanation

{topic_title} is an important concept that builds upon previous knowledge.
The key aspects include:

- Understanding the theoretical foundations
- Recognizing practical applications
- Developing problem-solving skills
- Connecting concepts to real-world scenarios

## Examples

Example 1: Basic application of {topic_title}
Example 2: Intermediate application showing deeper understanding
Example 3: Advanced scenario demonstrating mastery

## Practice Problems

1. Define {topic_title} in your own words
2. Identify the key components
3. Apply the concept to solve a practical problem
4. Analyze how this relates to other topics

## Summary

{topic_title} is a critical concept that forms the foundation for more 
advanced topics. Understanding this material is essential for progressing 
in your learning journey.

## Next Steps

- Review the key concepts
- Practice with additional problems
- Connect this topic to related concepts
- Prepare for the assessment quiz
"""
    return theory


@dataclass
class QuizAttempt:
    """Records a quiz attempt"""
    quiz_id: str
    module_name: str
    topic: str
    questions: List[Dict[str, Any]]
    student_answers: List[str]
    correct_answers: List[str]
    score: float
    time_taken: int
    weak_concepts: List[str]
    strong_concepts: List[str]
    timestamp: str


@dataclass
class StudentJourneyRecord:
    """Complete record of student's learning journey"""
    student_id: str
    topic: str
    curriculum: Dict[str, Any]
    modules_completed: List[str]
    quiz_attempts: List[QuizAttempt]
    theories_studied: List[Dict[str, Any]]
    personalization_history: List[Dict[str, Any]]
    overall_progress: float
    current_level: str


class StudentSimulator:
    """Simulates a student going through the learning journey"""
    
    def __init__(self, student_id: str, knowledge_level: str = "beginner"):
        """
        Initialize student simulator
        
        Args:
            student_id: Student identifier
            knowledge_level: beginner, intermediate, advanced
        """
        self.student_id = student_id
        self.knowledge_level = knowledge_level
        
        # Student characteristics that affect performance
        self.mastery_probability = {
            "beginner": 0.4,      # 40% chance to answer correctly
            "intermediate": 0.7,  # 70% chance
            "advanced": 0.9       # 90% chance
        }
        
        self.weak_areas = []
        self.strong_areas = []
        
    def take_quiz(self, quiz_questions: List[Dict[str, Any]], topic: str) -> Dict[str, Any]:
        """
        Simulate student taking a quiz
        
        Args:
            quiz_questions: List of quiz questions
            topic: Current topic being tested
            
        Returns:
            Quiz results with answers and performance analysis
        """
        student_answers = []
        correct_answers = []
        correct_count = 0
        weak_concepts = []
        strong_concepts = []
        
        base_probability = self.mastery_probability[self.knowledge_level]
        
        for i, question in enumerate(quiz_questions):
            correct_answer = question.get('correct_answer', 'A')
            correct_answers.append(correct_answer)
            
            # Simulate answer based on student level and previous performance
            # Students tend to do worse on topics they've struggled with
            concept = question.get('concept', topic)
            
            # Adjust probability based on previous weak areas
            adjusted_probability = base_probability
            if concept in self.weak_areas:
                adjusted_probability *= 0.6  # 40% reduction if weak area
            elif concept in self.strong_areas:
                adjusted_probability = min(0.95, adjusted_probability * 1.2)
            
            # Simulate answer
            is_correct = random.random() < adjusted_probability
            
            if is_correct:
                student_answer = correct_answer
                correct_count += 1
                if concept not in strong_concepts:
                    strong_concepts.append(concept)
            else:
                # Choose a wrong answer
                options = ['A', 'B', 'C', 'D']
                options.remove(correct_answer)
                student_answer = random.choice(options)
                if concept not in weak_concepts:
                    weak_concepts.append(concept)
            
            student_answers.append(student_answer)
        
        score = (correct_count / len(quiz_questions)) * 100
        
        # Update student's weak and strong areas
        self.weak_areas.extend(weak_concepts)
        self.strong_areas.extend(strong_concepts)
        
        # Remove duplicates while preserving order
        self.weak_areas = list(dict.fromkeys(self.weak_areas))
        self.strong_areas = list(dict.fromkeys(self.strong_areas))
        
        return {
            'student_answers': student_answers,
            'correct_answers': correct_answers,
            'score': score,
            'correct_count': correct_count,
            'total_questions': len(quiz_questions),
            'weak_concepts': weak_concepts,
            'strong_concepts': strong_concepts,
            'time_taken': random.randint(300, 900)  # 5-15 minutes
        }


def generate_personalized_content(
    student_performance: Dict[str, Any],
    next_module: Dict[str, Any],
    previous_weak_areas: List[str]
) -> Dict[str, Any]:
    """
    Generate personalized content based on student's performance
    
    Args:
        student_performance: Results from previous quiz
        next_module: Next module to study
        previous_weak_areas: Topics student has struggled with
        
    Returns:
        Personalized learning content
    """
    score = student_performance['score']
    weak_concepts = student_performance['weak_concepts']
    
    personalization = {
        'score': score,
        'performance_level': 'excellent' if score >= 80 else 'good' if score >= 60 else 'needs_improvement',
        'recommendations': [],
        'focus_areas': [],
        'content_adjustments': {}
    }
    
    # Determine personalization strategy
    if score < 60:
        personalization['recommendations'].extend([
            "Review previous module concepts before proceeding",
            "Consider additional practice exercises",
            "Spend more time on foundational topics"
        ])
        personalization['focus_areas'].extend(weak_concepts)
        personalization['content_adjustments'] = {
            'difficulty': 'reduce',
            'examples': 'increase',
            'practice_problems': 'more_basic',
            'explanation_depth': 'detailed'
        }
        
    elif score < 80:
        personalization['recommendations'].extend([
            "Good progress! Focus on weak areas identified",
            "Practice more problems on challenging concepts",
            "Review quiz mistakes before moving forward"
        ])
        personalization['focus_areas'].extend(weak_concepts)
        personalization['content_adjustments'] = {
            'difficulty': 'maintain',
            'examples': 'targeted',
            'practice_problems': 'moderate',
            'explanation_depth': 'standard'
        }
        
    else:
        personalization['recommendations'].extend([
            "Excellent performance! Ready for advanced topics",
            "Consider exploring related advanced concepts",
            "You can move to the next module confidently"
        ])
        personalization['content_adjustments'] = {
            'difficulty': 'increase',
            'examples': 'concise',
            'practice_problems': 'challenging',
            'explanation_depth': 'concise'
        }
    
    # Add weak area remediation
    if weak_concepts:
        personalization['remediation_topics'] = weak_concepts
        personalization['recommendations'].append(
            f"Pay special attention to: {', '.join(weak_concepts[:3])}"
        )
    
    return personalization


def run_complete_student_journey():
    """Run complete student learning journey simulation"""
    
    print("=" * 80)
    print("🎓 COMPLETE STUDENT LEARNING JOURNEY SIMULATION")
    print("=" * 80)
    
    # Configuration
    pdf_path = "doc/book2.pdf"
    target_topic = "expectation and variance"
    student_id = "student_journey_001"
    student_level = "intermediate"  # beginner, intermediate, advanced
    
    output_dir = f"output/student_journey/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📋 Configuration:")
    print(f"   Student ID: {student_id}")
    print(f"   Knowledge Level: {student_level}")
    print(f"   Topic: {target_topic}")
    print(f"   PDF: {pdf_path}")
    print(f"   Output: {output_dir}")
    
    # Initialize journey record
    journey = StudentJourneyRecord(
        student_id=student_id,
        topic=target_topic,
        curriculum={},
        modules_completed=[],
        quiz_attempts=[],
        theories_studied=[],
        personalization_history=[],
        overall_progress=0.0,
        current_level=student_level
    )
    
    # =========================================================================
    # STAGE 1: EXTRACT TOPICS AND GENERATE CURRICULUM
    # =========================================================================
    print("\n" + "=" * 80)
    print("📚 STAGE 1: TOPIC EXTRACTION & CURRICULUM GENERATION")
    print("=" * 80)
    
    print("\n⏳ Extracting topics from PDF...")
    extractor = OptimizedUniversalExtractor(pdf_path=pdf_path)
    all_topics = extractor.extract_topics()
    
    # Filter for relevant topics
    relevant_topics = [
        t for t in all_topics 
        if any(keyword in t.get('title', '').lower() 
               for keyword in target_topic.lower().split())
    ]
    
    # If no relevant topics found, use all topics
    if not relevant_topics:
        relevant_topics = all_topics[:60]  # Use first 60 topics
    print(f"✅ Extracted {len(all_topics)} total topics")
    print(f"✅ Found {len(relevant_topics)} relevant topics")
    
    # Save topics
    topics_file = os.path.join(output_dir, "1_extracted_topics.json")
    with open(topics_file, 'w') as f:
        json.dump(relevant_topics, f, indent=2)
    print(f"💾 Saved to: {topics_file}")
    
    print("\n⏳ Generating personalized curriculum...")
    
    # Create a simple curriculum structure from topics
    curriculum = {
        'topic': target_topic,
        'modules': []
    }
    
    # Group topics into modules (split into 4 groups)
    topics_per_module = max(1, len(relevant_topics) // 4)
    for i in range(4):
        start_idx = i * topics_per_module
        end_idx = start_idx + topics_per_module if i < 3 else len(relevant_topics)
        module_topics = relevant_topics[start_idx:end_idx]
        
        if module_topics:
            module = {
                'module_name': f'Module {i+1}: {target_topic.title()} - Part {i+1}',
                'difficulty_level': ['beginner', 'intermediate', 'intermediate', 'advanced'][i],
                'estimated_hours': [3, 4, 5, 6][i],
                'topics': module_topics[:6],  # Max 6 topics per module
                'learning_objectives': [
                    f'Understand key concepts of {target_topic}',
                    f'Apply concepts in practice'
                ],
                'prerequisites': [] if i == 0 else [curriculum['modules'][i-1]['module_name']]
            }
            curriculum['modules'].append(module)
    
    journey.curriculum = curriculum
    
    print(f"✅ Generated {len(curriculum.get('modules', []))} learning modules")
    for i, module in enumerate(curriculum.get('modules', []), 1):
        print(f"   Module {i}: {module['module_name']} ({module['difficulty_level']}, {module['estimated_hours']}h)")
    
    # Save curriculum
    curriculum_file = os.path.join(output_dir, "2_curriculum.json")
    with open(curriculum_file, 'w') as f:
        json.dump(curriculum, f, indent=2)
    print(f"💾 Saved to: {curriculum_file}")
    
    # =========================================================================
    # STAGE 2: GENERATE THEORY FOR FIRST MODULE
    # =========================================================================
    print("\n" + "=" * 80)
    print("📖 STAGE 2: THEORY CONTENT GENERATION")
    print("=" * 80)
    
    first_module = curriculum['modules'][0]
    print(f"\n📚 Generating theory for: {first_module['module_name']}")
    print(f"   Topics: {len(first_module['topics'])}")
    print(f"   Difficulty: {first_module['difficulty_level']}")
    
    module_theories = []
    for topic_idx, topic in enumerate(first_module['topics'][:3], 1):  # First 3 topics
        topic_title = topic.get('title') or topic.get('topic', 'Unknown Topic')
        page_num = topic.get('page', 0)
        
        print(f"\n   ⏳ Generating LLM-based theory {topic_idx}/{min(3, len(first_module['topics']))}: {topic_title}")
        
        # Generate theory from PDF using LLM
        theory = generate_theory_from_pdf(
            pdf_path=pdf_path,
            topic_title=topic_title,
            page_numbers=[page_num, page_num + 1, page_num + 2],  # 3 pages of content
            difficulty_level=first_module['difficulty_level'],
            learning_objectives=first_module.get('learning_objectives', [])
        )
        
        theory_content = {
            'topic': topic_title,
            'module': first_module['module_name'],
            'theory': theory,
            'page_references': [topic.get('page', 0)]
        }
        module_theories.append(theory_content)
        
        print(f"   ✅ Generated theory ({len(theory)} characters)")
    
    journey.theories_studied.extend(module_theories)
    
    # Save theories
    theories_file = os.path.join(output_dir, "3_module1_theories.json")
    with open(theories_file, 'w') as f:
        json.dump(module_theories, f, indent=2)
    print(f"\n💾 Saved theories to: {theories_file}")
    
    # =========================================================================
    # STAGE 3: GENERATE QUIZ FOR FIRST MODULE
    # =========================================================================
    print("\n" + "=" * 80)
    print("❓ STAGE 3: QUIZ GENERATION")
    print("=" * 80)
    
    print(f"\n⏳ Generating LLM-based quiz for: {first_module['module_name']}")
    print(f"   Using ALL {len(module_theories)} theories for better context...")
    
    # Generate quiz from ALL theories using LLM (better context)
    quiz_questions = generate_quiz_from_all_theories(
        theories=module_theories,
        module_name=first_module['module_name'],
        difficulty_level=first_module['difficulty_level'],
        num_questions_per_topic=3
    )
    
    print(f"✅ Generated {len(quiz_questions)} quiz questions covering all topics")
    
    # Save quiz
    quiz_file = os.path.join(output_dir, "4_module1_quiz.json")
    with open(quiz_file, 'w') as f:
        json.dump(quiz_questions, f, indent=2)
    print(f"💾 Saved to: {quiz_file}")
    
    # =========================================================================
    # STAGE 4: SIMULATE STUDENT TAKING QUIZ
    # =========================================================================
    print("\n" + "=" * 80)
    print("🎯 STAGE 4: STUDENT TAKES QUIZ")
    print("=" * 80)
    
    print(f"\n👤 Student '{student_id}' (Level: {student_level}) taking quiz...")
    simulator = StudentSimulator(student_id, student_level)
    
    quiz_result = simulator.take_quiz(quiz_questions, first_module['module_name'])
    
    print(f"\n📊 Quiz Results:")
    print(f"   Score: {quiz_result['score']:.1f}% ({quiz_result['correct_count']}/{quiz_result['total_questions']})")
    print(f"   Time taken: {quiz_result['time_taken']} seconds")
    print(f"   Weak concepts: {', '.join(quiz_result['weak_concepts']) if quiz_result['weak_concepts'] else 'None'}")
    print(f"   Strong concepts: {', '.join(quiz_result['strong_concepts']) if quiz_result['strong_concepts'] else 'None'}")
    
    # Record quiz attempt
    quiz_attempt = QuizAttempt(
        quiz_id=f"quiz_{first_module['module_name']}_1",
        module_name=first_module['module_name'],
        topic=target_topic,
        questions=quiz_questions,
        student_answers=quiz_result['student_answers'],
        correct_answers=quiz_result['correct_answers'],
        score=quiz_result['score'],
        time_taken=quiz_result['time_taken'],
        weak_concepts=quiz_result['weak_concepts'],
        strong_concepts=quiz_result['strong_concepts'],
        timestamp=datetime.now().isoformat()
    )
    journey.quiz_attempts.append(quiz_attempt)
    
    # Save quiz results
    quiz_result_file = os.path.join(output_dir, "5_quiz_results.json")
    with open(quiz_result_file, 'w') as f:
        json.dump(asdict(quiz_attempt), f, indent=2)
    print(f"💾 Saved to: {quiz_result_file}")
    
    # =========================================================================
    # STAGE 5: ANALYZE PERFORMANCE AND GENERATE PERSONALIZED CONTENT
    # =========================================================================
    print("\n" + "=" * 80)
    print("🔍 STAGE 5: PERFORMANCE ANALYSIS & PERSONALIZATION")
    print("=" * 80)
    
    print("\n⏳ Analyzing student performance...")
    
    # Get next module
    next_module = curriculum['modules'][1] if len(curriculum['modules']) > 1 else None
    
    if next_module:
        personalization = generate_personalized_content(
            student_performance=quiz_result,
            next_module=next_module,
            previous_weak_areas=simulator.weak_areas
        )
        
        journey.personalization_history.append({
            'after_module': first_module['module_name'],
            'before_module': next_module['module_name'],
            'personalization': personalization,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"\n📈 Performance Analysis:")
        print(f"   Level: {personalization['performance_level'].upper()}")
        print(f"   \n   📋 Recommendations:")
        for rec in personalization['recommendations']:
            print(f"      • {rec}")
        
        if personalization.get('focus_areas'):
            print(f"   \n   🎯 Focus Areas for Next Module:")
            for area in personalization['focus_areas']:
                print(f"      • {area}")
        
        print(f"   \n   ⚙️  Content Adjustments:")
        for key, value in personalization['content_adjustments'].items():
            print(f"      • {key}: {value}")
        
        # Save personalization
        personalization_file = os.path.join(output_dir, "6_personalization.json")
        with open(personalization_file, 'w') as f:
            json.dump(personalization, f, indent=2)
        print(f"\n💾 Saved to: {personalization_file}")
        
        # =====================================================================
        # STAGE 6: GENERATE PERSONALIZED THEORY FOR NEXT MODULE
        # =====================================================================
        print("\n" + "=" * 80)
        print("📖 STAGE 6: PERSONALIZED NEXT MODULE CONTENT")
        print("=" * 80)
        
        print(f"\n📚 Generating personalized theory for: {next_module['module_name']}")
        print(f"   Adjusting for: {personalization['performance_level']} performance")
        
        next_module_theories = []
        for topic_idx, topic in enumerate(next_module['topics'][:2], 1):  # First 2 topics
            topic_title = topic.get('title') or topic.get('topic', 'Unknown Topic')
            page_num = topic.get('page', 0)
            
            print(f"\n   ⏳ Generating personalized LLM theory {topic_idx}/2: {topic_title}")
            
            # Adjust difficulty based on performance
            adjusted_difficulty = next_module['difficulty_level']
            if personalization['content_adjustments']['difficulty'] == 'reduce':
                adjusted_difficulty = 'beginner'
            elif personalization['content_adjustments']['difficulty'] == 'increase':
                adjusted_difficulty = 'advanced'
            
            # Generate personalized theory from PDF
            theory = generate_theory_from_pdf(
                pdf_path=pdf_path,
                topic_title=topic_title,
                page_numbers=[page_num, page_num + 1, page_num + 2],
                difficulty_level=adjusted_difficulty,
                learning_objectives=next_module.get('learning_objectives', []),
                weak_areas=quiz_result['weak_concepts']  # Pass weak areas for personalization
            )
            
            # Add personalization notes
            theory_with_notes = f"""
{'=' * 80}
PERSONALIZED CONTENT FOR {student_id}
{'=' * 80}

Performance Level: {personalization['performance_level'].upper()}
Adjustments Applied: {personalization['content_adjustments']}

{'=' * 80}

{theory}

{'=' * 80}
RECOMMENDED FOCUS:
{'=' * 80}

"""
            if personalization.get('focus_areas'):
                theory_with_notes += "Based on your quiz performance, pay special attention to:\n"
                for area in personalization['focus_areas']:
                    theory_with_notes += f"• {area}\n"
            
            theory_with_notes += "\n" + "=" * 80
            
            next_theory_content = {
                'topic': topic_title,
                'module': next_module['module_name'],
                'theory': theory_with_notes,
                'personalization': personalization,
                'page_references': [topic.get('page', 0)]
            }
            next_module_theories.append(next_theory_content)
            
            print(f"   ✅ Generated personalized theory ({len(theory_with_notes)} characters)")
        
        journey.theories_studied.extend(next_module_theories)
        
        # Save personalized theories
        next_theories_file = os.path.join(output_dir, "7_module2_personalized_theories.json")
        with open(next_theories_file, 'w') as f:
            json.dump(next_module_theories, f, indent=2)
        print(f"\n💾 Saved to: {next_theories_file}")
    
    # =========================================================================
    # STAGE 7: GENERATE FINAL JOURNEY REPORT
    # =========================================================================
    print("\n" + "=" * 80)
    print("📊 STAGE 7: COMPLETE JOURNEY REPORT")
    print("=" * 80)
    
    # Calculate overall progress
    modules_started = 2 if next_module else 1
    journey.overall_progress = (modules_started / len(curriculum['modules'])) * 100
    journey.modules_completed = [first_module['module_name']]
    
    journey_dict = asdict(journey)
    
    # Save complete journey
    journey_file = os.path.join(output_dir, "COMPLETE_JOURNEY.json")
    with open(journey_file, 'w') as f:
        json.dump(journey_dict, f, indent=2)
    
    print(f"\n🎓 Student Journey Summary:")
    print(f"   Student ID: {journey.student_id}")
    print(f"   Topic: {journey.topic}")
    print(f"   Modules completed: {len(journey.modules_completed)}")
    print(f"   Quiz attempts: {len(journey.quiz_attempts)}")
    print(f"   Theories studied: {len(journey.theories_studied)}")
    print(f"   Overall progress: {journey.overall_progress:.1f}%")
    print(f"   Current level: {journey.current_level}")
    
    print(f"\n💾 Complete journey saved to: {journey_file}")
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("✅ COMPLETE STUDENT JOURNEY SIMULATION FINISHED")
    print("=" * 80)
    
    print(f"\n📁 All outputs saved to: {output_dir}")
    print(f"\n📄 Generated files:")
    print(f"   1. 1_extracted_topics.json - Extracted topics from PDF")
    print(f"   2. 2_curriculum.json - Personalized curriculum")
    print(f"   3. 3_module1_theories.json - Theory content for Module 1")
    print(f"   4. 4_module1_quiz.json - Quiz questions")
    print(f"   5. 5_quiz_results.json - Student's quiz performance")
    print(f"   6. 6_personalization.json - Performance analysis & recommendations")
    print(f"   7. 7_module2_personalized_theories.json - Personalized Module 2 content")
    print(f"   8. COMPLETE_JOURNEY.json - Full learning journey record")
    
    print(f"\n🎯 Key Highlights:")
    print(f"   ✅ Extracted {len(relevant_topics)} relevant topics")
    print(f"   ✅ Generated {len(curriculum['modules'])} module curriculum")
    print(f"   ✅ Created {len(module_theories)} theory contents")
    print(f"   ✅ Generated {len(quiz_questions)} quiz questions")
    print(f"   ✅ Student scored {quiz_result['score']:.1f}%")
    print(f"   ✅ Personalized next module based on performance")
    print(f"   ✅ Complete learning journey documented")
    
    return journey_dict


if __name__ == "__main__":
    try:
        journey = run_complete_student_journey()
        print("\n" + "=" * 80)
        print("🎉 SUCCESS! Complete student learning journey simulated.")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Error during simulation: {str(e)}")
        import traceback
        traceback.print_exc()
